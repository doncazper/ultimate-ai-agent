from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.dev import install_governed_browser_keychain_helper as installer
from tests.test_governed_browser_queue01_group01 import _binding
from ultimate_ai_agent.core.governed_browser import (
    GovernedBrowserKeychainError,
    MacOSGovernedBrowserKeychainAdapter,
    build_governed_browser_credential_registration,
)


def _write_fake_helper(path: Path, *, extra_response_field: bool = False) -> str:
    extra = ', "unexpected": true' if extra_response_field else ""
    source = f"""#!/usr/bin/python3
import json
import sys

request = json.loads(sys.stdin.buffer.read())
operation = request["operation"]
response = {{
    "schema_version": "uaa-governed-browser-keychain-helper-response.v1",
    "ok": True,
    "operation": operation,
    "adapter_ref": "adapter-ref:governed-browser-keychain:macos:v1",
    "helper_version": "test",
    "helper_version_ref": "helper-version-ref:governed-browser-keychain:v1",
    "helper_receipt_ref": "helper-receipt-ref:governed-browser-keychain:test",
    "credential_material_included": False,
    "credential_material_returned": False,
    "browser_session_started": False,
    "authentication_performed": False,
    "cookies_used": False,
    "network_call_performed": False,
    "external_mutation_performed": False,
    "execution_authority_granted": False{extra},
}}
if operation != "version":
    for name in (
        "origin_ref",
        "credential_handle_ref",
        "credential_generation_ref",
        "keychain_item_ref",
    ):
        response[name] = request[name]
if operation == "store":
    response.update({{"created": True, "present": True}})
elif operation == "probe":
    response["present"] = True
elif operation == "delete":
    response.update({{"present": False, "deleted_or_absent": True}})
sys.stdout.write(json.dumps(response, sort_keys=True))
"""
    path.write_text(source, encoding="utf-8")
    path.chmod(0o700)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _registration():  # type: ignore[no-untyped-def]
    base = _binding(suffix="registration")
    return build_governed_browser_credential_registration(
        origin_ref=base.origin_ref,
        credential_handle_ref="credential-handle-ref:governed-browser:founder-login",
        credential_generation_ref=(
            "credential-generation-ref:governed-browser:generation-01"
        ),
    )


def _opaque_material(seed: int, length: int = 32) -> bytearray:
    return bytearray((seed + index) % 256 for index in range(length))


def test_real_adapter_is_hash_pinned_bounded_and_never_returns_material(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = tmp_path / "helper"
    digest = _write_fake_helper(helper)
    monkeypatch.setattr(
        "ultimate_ai_agent.core.governed_browser.browser_keychain.sys.platform",
        "darwin",
    )
    adapter = MacOSGovernedBrowserKeychainAdapter(
        helper_path=helper,
        expected_helper_sha256=digest,
    )
    registration = _registration()

    readiness = adapter.readiness()
    material = _opaque_material(11)
    material_fingerprint = hashlib.sha256(material).hexdigest()
    stored = adapter.store(
        registration,
        request_ref="request-ref:governed-browser-keychain:test-store",
        credential_material=material,
    )
    probed = adapter.probe(
        registration,
        request_ref="request-ref:governed-browser-keychain:test-probe",
    )
    deleted = adapter.delete(
        registration,
        request_ref="request-ref:governed-browser-keychain:test-delete",
    )

    assert readiness.status == "ready"
    assert readiness.browser_session_authority_granted is False
    assert all(value == 0 for value in material)
    assert stored.created is True and stored.present is True
    assert probed.present is True
    assert deleted.present is False and deleted.deleted_or_absent is True
    payload = json.dumps(
        {
            "readiness": readiness.model_dump(mode="json"),
            "store": stored.model_dump(mode="json"),
            "probe": probed.model_dump(mode="json"),
            "delete": deleted.model_dump(mode="json"),
        },
        sort_keys=True,
    )
    assert material_fingerprint not in payload
    assert '"credential_material_included": false' in payload
    assert '"credential_material_returned": false' in payload
    assert '"browser_session_started": false' in payload
    assert '"network_call_performed": false' in payload


def test_adapter_rejects_tamper_symlink_invalid_response_and_immutable_buffer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ultimate_ai_agent.core.governed_browser.browser_keychain.sys.platform",
        "darwin",
    )
    helper = tmp_path / "helper"
    digest = _write_fake_helper(helper)
    registration = _registration()
    adapter = MacOSGovernedBrowserKeychainAdapter(
        helper_path=helper,
        expected_helper_sha256=digest,
    )
    helper.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    helper.chmod(0o700)
    with pytest.raises(
        GovernedBrowserKeychainError,
        match="FINGERPRINT_MISMATCH",
    ):
        adapter.probe(
            registration,
            request_ref="request-ref:governed-browser-keychain:tampered",
        )

    actual = tmp_path / "actual"
    actual_digest = _write_fake_helper(actual)
    symlink = tmp_path / "symlink"
    symlink.symlink_to(actual)
    symlink_adapter = MacOSGovernedBrowserKeychainAdapter(
        helper_path=symlink,
        expected_helper_sha256=actual_digest,
    )
    with pytest.raises(GovernedBrowserKeychainError, match="FILE_UNTRUSTED"):
        symlink_adapter.probe(
            registration,
            request_ref="request-ref:governed-browser-keychain:symlink",
        )

    invalid = tmp_path / "invalid"
    invalid_digest = _write_fake_helper(invalid, extra_response_field=True)
    invalid_adapter = MacOSGovernedBrowserKeychainAdapter(
        helper_path=invalid,
        expected_helper_sha256=invalid_digest,
    )
    with pytest.raises(GovernedBrowserKeychainError, match="RESPONSE_INVALID"):
        invalid_adapter.probe(
            registration,
            request_ref="request-ref:governed-browser-keychain:invalid-response",
        )

    clean = tmp_path / "clean"
    clean_digest = _write_fake_helper(clean)
    clean_adapter = MacOSGovernedBrowserKeychainAdapter(
        helper_path=clean,
        expected_helper_sha256=clean_digest,
    )
    with pytest.raises(TypeError, match="MUTABLE_BUFFER_REQUIRED"):
        clean_adapter.store(  # type: ignore[arg-type]
            registration,
            request_ref="request-ref:governed-browser-keychain:immutable",
            credential_material=bytes(range(16)),
        )
    short = bytearray(range(8))
    with pytest.raises(GovernedBrowserKeychainError, match="LENGTH_INVALID"):
        clean_adapter.store(
            registration,
            request_ref="request-ref:governed-browser-keychain:short",
            credential_material=short,
        )
    assert all(value == 0 for value in short)


def test_installer_metadata_is_content_free_exact_and_rejects_unmanaged_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(installer.platform, "machine", lambda: "arm64")
    digest = "a" * 64
    metadata = installer._build_metadata(digest)

    assert installer._managed_metadata_matches(metadata, digest)
    assert not installer._managed_metadata_matches(
        {**metadata, "unexpected": False},
        digest,
    )
    assert metadata["credential_material_included"] is False
    assert metadata["absolute_path_included"] is False
    assert metadata["browser_session_authority_granted"] is False
    assert metadata["authentication_authority_granted"] is False
    assert metadata["network_authority_granted"] is False
    assert metadata["external_mutation_authority_granted"] is False

    source = tmp_path / "source"
    source.write_bytes(b"source-helper")
    source.chmod(0o700)
    target = tmp_path / installer.HELPER_NAME
    target.write_bytes(b"unmanaged-helper")
    target.chmod(0o700)
    metadata_path = tmp_path / installer.METADATA_NAME
    metadata_path.write_text("{}\n", encoding="utf-8")
    metadata_path.chmod(0o600)
    with pytest.raises(RuntimeError, match="EXISTING_INSTALL_UNMANAGED"):
        installer._reconcile_existing_pair(
            source=source,
            target=target,
            metadata_path=metadata_path,
            expected_digest=hashlib.sha256(source.read_bytes()).hexdigest(),
            intended_metadata=metadata,
        )
