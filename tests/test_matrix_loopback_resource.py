from __future__ import annotations

import os
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

import tests.matrix_loopback_resource as matrix_loopback_resource


def test_matrix_loopback_resource_lock_is_stable_and_uid_scoped() -> None:
    assert matrix_loopback_resource._LOCK_PATH.parent == Path("/tmp")
    assert matrix_loopback_resource._LOCK_PATH.name.endswith(f"-{os.getuid()}.lock")


def test_matrix_loopback_resource_serializes_distinct_process_temp_roots(
    tmp_path: Path,
) -> None:
    first_temp = tmp_path / "first-tmp"
    second_temp = tmp_path / "second-tmp"
    first_temp.mkdir()
    second_temp.mkdir()
    first_marker = tmp_path / "first-acquired"
    second_marker = tmp_path / "second-acquired"
    script = (
        "import sys,time\n"
        "from pathlib import Path\n"
        "from tests.matrix_loopback_resource import matrix_loopback_test_resource\n"
        "with matrix_loopback_test_resource():\n"
        "    Path(sys.argv[1]).write_text('acquired', encoding='utf-8')\n"
        "    time.sleep(float(sys.argv[2]))\n"
    )
    first_environment = dict(os.environ)
    first_environment["TMPDIR"] = os.fspath(first_temp)
    second_environment = dict(os.environ)
    second_environment["TMPDIR"] = os.fspath(second_temp)
    first = subprocess.Popen(
        [sys.executable, "-c", script, os.fspath(first_marker), "0.5"],
        cwd=Path(__file__).resolve().parents[1],
        env=first_environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    second: subprocess.Popen[bytes] | None = None
    try:
        deadline = time.monotonic() + 5
        while not first_marker.exists():
            if first.poll() is not None or time.monotonic() >= deadline:
                raise AssertionError("first lock owner did not start")
            time.sleep(0.01)
        second = subprocess.Popen(
            [sys.executable, "-c", script, os.fspath(second_marker), "0"],
            cwd=Path(__file__).resolve().parents[1],
            env=second_environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        time.sleep(0.1)
        assert not second_marker.exists()
        assert first.wait(timeout=5) == 0
        assert second.wait(timeout=5) == 0
        assert second_marker.read_text(encoding="utf-8") == "acquired"
    finally:
        for process in (first, second):
            if process is not None and process.poll() is None:
                process.terminate()
                process.wait(timeout=5)


def test_matrix_loopback_resource_uses_owner_only_regular_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock_path = tmp_path / "matrix-loopback.lock"
    monkeypatch.setattr(matrix_loopback_resource, "_LOCK_PATH", lock_path)

    with matrix_loopback_resource.matrix_loopback_test_resource():
        metadata = lock_path.stat()
        assert stat.S_ISREG(metadata.st_mode)
        assert metadata.st_uid == os.getuid()
        assert stat.S_IMODE(metadata.st_mode) == 0o600


def test_matrix_loopback_resource_rejects_symlink_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "target"
    target.write_text("", encoding="utf-8")
    lock_path = tmp_path / "matrix-loopback.lock"
    lock_path.symlink_to(target)
    monkeypatch.setattr(matrix_loopback_resource, "_LOCK_PATH", lock_path)

    with pytest.raises(
        RuntimeError,
        match="MATRIX_TEST_HARNESS_RESOURCE_LOCK_UNSAFE",
    ):
        with matrix_loopback_resource.matrix_loopback_test_resource():
            raise AssertionError("unsafe lock unexpectedly acquired")
