from __future__ import annotations

import fcntl
import hashlib
import json
import os
import platform
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.dev import install_matrix_session_helper as installer


def _metadata(digest: str) -> dict[str, object]:
    return {
        "schema_version": "uaa-matrix-session-keychain-helper-install.v1",
        "helper_ref": "helper-ref:matrix-session-keychain:v1",
        "helper_version_ref": "helper-version-ref:matrix-session-keychain:v1",
        "helper_fingerprint_ref": f"helper-fingerprint-ref:sha256:{digest}",
        "platform_ref": "platform-ref:macos:test",
        "session_material_included": False,
        "absolute_path_included": False,
        "execution_authority_granted": False,
    }


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS helper proof")
def test_native_helper_builds_and_exposes_only_content_free_version_handshake(
    tmp_path: Path,
) -> None:
    scratch = tmp_path / "swift-scratch"
    subprocess.run(
        [
            "/usr/bin/swift",
            "build",
            "--package-path",
            os.fspath(installer.PACKAGE),
            "-c",
            "release",
            "--scratch-path",
            os.fspath(scratch),
        ],
        check=True,
        capture_output=True,
        timeout=120,
    )
    helper = scratch / "release" / installer.HELPER_NAME
    version = subprocess.run(
        [os.fspath(helper)],
        input=json.dumps(
            {
                "schema_version": "uaa-matrix-session-keychain-helper-request.v1",
                "operation": "version",
            }
        ).encode(),
        check=True,
        capture_output=True,
        timeout=5,
    )
    payload = json.loads(version.stdout)
    assert payload["ok"] is True
    assert payload["credential_material_included"] is False
    assert payload["execution_authority_granted"] is False

    blocked = subprocess.run(
        [os.fspath(helper)],
        input=json.dumps(
            {
                "schema_version": "uaa-matrix-session-keychain-helper-request.v1",
                "operation": "adapter_with_credential",
            }
        ).encode(),
        check=False,
        capture_output=True,
        timeout=5,
    )
    denied = json.loads(blocked.stdout)
    assert blocked.returncode == 2
    assert denied["error_code"] == "MATRIX_KEYCHAIN_CALLER_AUTH_REQUIRED"
    assert "credential_item_ref" not in denied
    assert "adapter_response_base64url" not in denied


def test_installer_stages_and_recovers_one_hash_bound_private_pair(
    tmp_path: Path,
) -> None:
    tmp_path.chmod(0o700)
    source = tmp_path / "source-helper"
    source.write_bytes(b"bounded-version-helper")
    source.chmod(0o700)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    target = tmp_path / installer.HELPER_NAME
    metadata_path = tmp_path / installer.METADATA_NAME

    installer._install_pair(
        source=source,
        target=target,
        metadata_path=metadata_path,
        expected_digest=digest,
        intended=_metadata(digest),
    )
    assert installer._digest(target) == digest
    assert installer._read_metadata(metadata_path) == _metadata(digest)
    assert stat.S_IMODE(os.lstat(target).st_mode) == 0o700
    assert stat.S_IMODE(os.lstat(metadata_path).st_mode) == 0o600
    assert os.fspath(tmp_path) not in json.dumps(_metadata(digest), sort_keys=True)


def test_installer_forward_recovers_only_a_matching_pending_pair(
    tmp_path: Path,
) -> None:
    tmp_path.chmod(0o700)
    pending = tmp_path / f".{installer.HELPER_NAME}.installing"
    pending.write_bytes(b"pending-helper")
    pending.chmod(0o700)
    digest = installer._digest(pending)
    metadata_path = tmp_path / installer.METADATA_NAME
    metadata_temp = metadata_path.with_suffix(".tmp")
    metadata_temp.write_text(
        json.dumps(_metadata(digest), sort_keys=True) + "\n", encoding="utf-8"
    )
    metadata_temp.chmod(0o600)

    installer._recover_install_temps(tmp_path)

    assert installer._digest(tmp_path / installer.HELPER_NAME) == digest
    assert installer._read_metadata(metadata_path) == _metadata(digest)
    assert not pending.exists()
    assert not metadata_temp.exists()


def test_installer_rejects_symlink_fifo_and_unmanaged_existing_targets(
    tmp_path: Path,
) -> None:
    tmp_path.chmod(0o700)
    source = tmp_path / "source-helper"
    source.write_bytes(b"helper")
    source.chmod(0o700)
    linked = tmp_path / "linked-helper"
    linked.symlink_to(source)
    with pytest.raises((OSError, RuntimeError)):
        installer._digest(linked)

    fifo = tmp_path / "helper-fifo"
    os.mkfifo(fifo, mode=0o600)
    with pytest.raises(RuntimeError, match="MATRIX_SESSION_HELPER_FILE_UNSAFE"):
        installer._digest(fifo)

    target = tmp_path / installer.HELPER_NAME
    target.write_bytes(b"unmanaged")
    target.chmod(0o700)
    with pytest.raises(
        RuntimeError, match="MATRIX_SESSION_HELPER_EXISTING_INSTALL_INCOMPLETE"
    ):
        installer._reconcile_existing(
            source=source,
            target=target,
            metadata_path=tmp_path / installer.METADATA_NAME,
            expected_digest=hashlib.sha256(source.read_bytes()).hexdigest(),
            intended=_metadata(hashlib.sha256(source.read_bytes()).hexdigest()),
        )


def test_installer_lock_is_exclusive_and_short_write_cleans_staging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tmp_path.chmod(0o700)
    lock_path = tmp_path / installer.INSTALL_LOCK_NAME
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        with pytest.raises(
            RuntimeError, match="MATRIX_SESSION_HELPER_INSTALL_IN_PROGRESS"
        ):
            with installer._install_lock(tmp_path):
                raise AssertionError("exclusive lock unexpectedly acquired")
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)

    metadata_path = tmp_path / installer.METADATA_NAME
    real_write = installer.os.write

    def short_write(fd: int, payload: bytes) -> int:
        real_write(fd, payload[:-1])
        return len(payload) - 1

    monkeypatch.setattr(installer.os, "write", short_write)
    with pytest.raises(
        RuntimeError, match="MATRIX_SESSION_HELPER_METADATA_SHORT_WRITE"
    ):
        installer._stage_json(metadata_path, _metadata("a" * 64))
    assert not metadata_path.with_suffix(".tmp").exists()


def test_installer_metadata_never_contains_session_material_or_paths() -> None:
    payload = installer._metadata("a" * 64)
    assert payload["session_material_included"] is False
    assert payload["absolute_path_included"] is False
    assert payload["execution_authority_granted"] is False
    assert str(Path.home()) not in json.dumps(payload, sort_keys=True)
    assert platform.system() not in json.dumps(payload, sort_keys=True)
