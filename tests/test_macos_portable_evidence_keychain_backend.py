from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.dev import install_portable_evidence_keychain_helper as installer
from ultimate_ai_agent.core.evidence_signing import macos_keychain
from ultimate_ai_agent.core.evidence_signing.macos_keychain import (
    MacOSKeychainPortableEvidenceSigningBackend,
    MacOSKeychainSigningBackendError,
    load_installed_macos_keychain_signing_backend,
)
from ultimate_ai_agent.core.evidence_signing.portable import (
    PORTABLE_EVIDENCE_SIGNING_DOMAIN,
)


@pytest.fixture(autouse=True)
def _macos_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(macos_keychain.sys, "platform", "darwin")


_FAKE_HELPER = r"""#!/usr/bin/python3
import base64
import hashlib
import json
import sys

request = json.loads(sys.stdin.buffer.read())
operation = request["operation"]
public = bytes(range(32))
signature = bytes(range(64))
encode = lambda value: base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")
response = {
    "schema_version": "uaa-portable-evidence-keychain-helper-response.v1",
    "ok": True,
    "operation": operation,
    "adapter_ref": "adapter-ref:portable-evidence-signing:macos-keychain:v1",
    "helper_version": "1.0.0",
    "helper_version_ref": "helper-version-ref:portable-evidence-keychain:v1",
    "key_ref": request.get("key_ref"),
    "key_version_ref": request.get("key_version_ref"),
    "public_key_base64url": encode(public) if operation in {"create", "probe"} else None,
    "public_key_fingerprint_ref": (
        "portable-evidence-public-key-fingerprint-ref:sha256:" + hashlib.sha256(public).hexdigest()
        if operation in {"create", "probe"} else None
    ),
    "signature_base64url": encode(signature) if operation == "sign" else None,
    "signature_ref": (
        "portable-evidence-signature-ref:sha256:" + hashlib.sha256(json.dumps(signature.hex(), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if operation == "sign" else None
    ),
    "helper_receipt_ref": "helper-receipt-ref:portable-evidence:test",
    "created": (True if operation == "create" else False) if operation in {"create", "probe"} else None,
    "deleted_or_absent": True if operation == "delete" else None,
    "error_code": None,
}
print(json.dumps({key: value for key, value in response.items() if value is not None}, sort_keys=True))
"""


def _backend(tmp_path: Path):  # type: ignore[no-untyped-def]
    tmp_path.mkdir(parents=True, exist_ok=True)
    helper = tmp_path / "uaa-portable-evidence-keychain-helper"
    helper.write_text(_FAKE_HELPER, encoding="utf-8")
    helper.chmod(0o700)
    digest = hashlib.sha256(helper.read_bytes()).hexdigest()
    return helper, MacOSKeychainPortableEvidenceSigningBackend(
        helper_path=helper,
        expected_helper_sha256=digest,
    )


def test_pinned_helper_readiness_and_strict_results(tmp_path: Path) -> None:
    _helper, backend = _backend(tmp_path)

    readiness = backend.readiness()
    created = backend.create_key(
        key_ref="signing-key-ref:portable-evidence:operator",
        key_version_ref="signing-key-version-ref:portable-evidence:operator:1",
        request_ref="request-ref:portable-evidence-key:create:1",
    )
    signed = backend.sign(
        key_ref=created.key_ref,
        key_version_ref=created.key_version_ref,
        request_ref="request-ref:portable-evidence:sign:1",
        payload=PORTABLE_EVIDENCE_SIGNING_DOMAIN + b"{}",
    )
    deleted = backend.delete_key(
        key_ref=created.key_ref,
        key_version_ref=created.key_version_ref,
        request_ref="request-ref:portable-evidence:key-delete:1",
    )

    assert readiness.status == "ready"
    assert readiness.secure_enclave_claimed is False
    assert created.private_key_included is False
    assert signed.signature_ref.startswith("portable-evidence-signature-ref:sha256:")
    assert deleted.deleted_or_absent is True


def test_backend_rejects_cross_protocol_payload_before_helper_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _helper, backend = _backend(tmp_path)
    invoked = False

    def unexpected_run(*args: object, **kwargs: object) -> object:
        nonlocal invoked
        invoked = True
        raise AssertionError("helper must not receive cross-protocol payload")

    monkeypatch.setattr(macos_keychain.subprocess, "run", unexpected_run)

    with pytest.raises(
        MacOSKeychainSigningBackendError,
        match="PORTABLE_EVIDENCE_HELPER_SIGNING_DOMAIN_REQUIRED",
    ):
        backend.sign(
            key_ref="signing-key-ref:portable-evidence:operator",
            key_version_ref="signing-key-version-ref:portable-evidence:operator:1",
            request_ref="request-ref:portable-evidence:cross-protocol-denied",
            payload=b"cross-protocol-payload",
        )
    assert invoked is False


def test_helper_hash_and_permissions_fail_closed(tmp_path: Path) -> None:
    helper, backend = _backend(tmp_path)
    helper.write_text(_FAKE_HELPER + "\n# changed", encoding="utf-8")
    assert backend.readiness().status == "helper_untrusted"

    helper, backend = _backend(tmp_path / "second")
    helper.chmod(0o722)
    assert backend.readiness().status == "helper_untrusted"


def test_helper_binding_mismatch_and_untrusted_output_are_redacted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _helper, backend = _backend(tmp_path)

    class Result:
        returncode = 0
        stderr = b"private-error-sentinel"
        stdout = b'{"private_key":"private-input-sentinel"}'

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: Result())
    with pytest.raises(
        MacOSKeychainSigningBackendError,
        match="PORTABLE_EVIDENCE_HELPER_RESPONSE_INVALID",
    ) as raised:
        backend.create_key(
            key_ref="signing-key-ref:portable-evidence:operator",
            key_version_ref="signing-key-version-ref:portable-evidence:operator:1",
            request_ref="request-ref:portable-evidence-key:create:1",
        )

    assert "private-input-sentinel" not in str(raised.value)
    assert "private-error-sentinel" not in str(raised.value)


def test_helper_symlink_is_rejected(tmp_path: Path) -> None:
    helper, _backend_instance = _backend(tmp_path)
    linked = tmp_path / "linked-helper"
    linked.symlink_to(helper)
    digest = hashlib.sha256(helper.read_bytes()).hexdigest()
    backend = MacOSKeychainPortableEvidenceSigningBackend(
        helper_path=linked,
        expected_helper_sha256=digest,
    )

    assert backend.readiness().status == "helper_untrusted"


def test_installed_metadata_loads_only_pinned_helper_without_path_persistence(
    tmp_path: Path,
) -> None:
    helper, _backend_instance = _backend(tmp_path)
    digest = hashlib.sha256(helper.read_bytes()).hexdigest()
    metadata = tmp_path / "portable-evidence-keychain-helper.json"
    metadata.write_text(
        json.dumps(
            {
                "schema_version": "uaa-portable-evidence-keychain-helper-install.v1",
                "helper_ref": "helper-ref:portable-evidence-keychain:v1",
                "helper_version_ref": "helper-version-ref:portable-evidence-keychain:v1",
                "helper_fingerprint_ref": f"helper-fingerprint-ref:sha256:{digest}",
                "platform_ref": "platform-ref:macos:test",
                "private_key_included": False,
                "absolute_path_included": False,
                "execution_authority_granted": False,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    metadata.chmod(0o600)

    loaded = load_installed_macos_keychain_signing_backend(tmp_path)

    assert loaded.readiness().status == "ready"
    assert str(tmp_path) not in metadata.read_text(encoding="utf-8")


def test_non_macos_readiness_and_direct_operations_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _helper, backend = _backend(tmp_path)
    monkeypatch.setattr(macos_keychain.sys, "platform", "linux")
    invoked = False

    def unexpected_run(*args: object, **kwargs: object) -> object:
        nonlocal invoked
        invoked = True
        raise AssertionError("helper must not execute off macOS")

    monkeypatch.setattr(macos_keychain.subprocess, "run", unexpected_run)

    assert backend.readiness().status == "unsupported_platform"
    with pytest.raises(
        MacOSKeychainSigningBackendError,
        match="PORTABLE_EVIDENCE_SIGNING_UNSUPPORTED_PLATFORM",
    ):
        backend.create_key(
            key_ref="signing-key-ref:portable-evidence:operator",
            key_version_ref="signing-key-version-ref:portable-evidence:operator:1",
            request_ref="request-ref:portable-evidence-key:create:off-platform",
        )
    assert invoked is False


def test_installer_denies_custom_roots_and_unmanaged_existing_targets(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        RuntimeError,
        match="PORTABLE_EVIDENCE_HELPER_CUSTOM_INSTALL_ROOT_DENIED",
    ):
        installer.install(install_root=tmp_path)

    target = tmp_path / installer.HELPER_NAME
    target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    target.chmod(0o700)
    with pytest.raises(
        RuntimeError,
        match="PORTABLE_EVIDENCE_HELPER_EXISTING_INSTALL_INCOMPLETE",
    ):
        installer._validate_existing_install(
            target=target,
            metadata_path=tmp_path / installer.METADATA_NAME,
        )
