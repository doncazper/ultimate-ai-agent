from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.verification import run_local_verification_lane as local_lane
from scripts.verification.pytest_shard_artifacts import safe_test_ref


SHA = "a" * 40
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _isolate_diagnostic_retention(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        local_lane,
        "DEFAULT_DIAGNOSTIC_ROOT",
        tmp_path / "diagnostics",
    )


def test_local_lane_default_fence_is_owner_scoped() -> None:
    assert local_lane.DEFAULT_FENCE_ROOT == Path(
        f"/private/tmp/uaa-verification-execution-fence-v2-{os.getuid()}"
    )


def test_local_lane_script_bootstraps_repo_imports_from_make_environment() -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = "src"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/verification/run_local_verification_lane.py",
            "--help",
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0
    assert "Run one clean exact-SHA local lane" in result.stdout


def test_local_lane_uses_canonical_local_surface_and_fence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, object] = {}
    monkeypatch.setattr(local_lane, "_repository_sha", lambda: SHA)

    def fake_run_lane(lane_ref: str, **kwargs: object) -> dict[str, object]:
        observed["lane_ref"] = lane_ref
        observed.update(kwargs)
        return {"status": "pass"}

    monkeypatch.setattr(local_lane, "run_lane", fake_run_lane)
    fence_root = tmp_path / "fence"

    assert (
        local_lane.run_local_lane(
            "ci-control-center-frontend",
            fence_root=fence_root,
        )
        == 0
    )
    assert observed["lane_ref"] == "ci-control-center-frontend"
    assert observed["repository_sha"] == SHA
    assert observed["full_suite_lock_mode"] == "local"
    assert observed["verification_execution_fence_root"] == fence_root
    assert observed["emit_failure_diagnostic_ref"] is True
    temp_root = observed["temp_root"]
    assert isinstance(temp_root, Path)
    assert not temp_root.exists()


def test_local_lane_prints_only_safe_pytest_failure_refs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(local_lane, "_repository_sha", lambda: SHA)
    safe_failure_ref = safe_test_ref("tests/test_safe.py::test_failure")

    def fake_run_lane(_lane_ref: str, **_kwargs: object) -> dict[str, object]:
        return {
            "status": "fail",
            "command_results": [
                {
                    "failed_shard_refs": (
                        "pytest-shard-ref:6:failed",
                        "pytest-shard-ref:99:failed",
                        "unsafe-shard-detail",
                    ),
                    "failed_test_refs": (
                        safe_failure_ref,
                        "unsafe-local-detail",
                    ),
                }
            ],
        }

    monkeypatch.setattr(local_lane, "run_lane", fake_run_lane)

    assert (
        local_lane.run_local_lane(
            "ci-pytest-shards",
            fence_root=tmp_path / "fence",
        )
        == 1
    )
    output = capsys.readouterr().out
    assert "pytest-shard-ref:6:failed" in output
    assert "CI_SHARD_INDEX=6" in output
    assert safe_failure_ref in output
    assert "pytest-shard-ref:99:failed" not in output
    assert "unsafe-local-detail" not in output
    assert "diagnostic-ref:local-verification:" in output
    retained = tuple(
        path
        for path in (tmp_path / "diagnostics").iterdir()
        if len(path.name) == 64
    )
    assert len(retained) == 1
    assert retained[0].is_file()
    payload = json.loads(retained[0].read_text(encoding="utf-8"))
    assert payload["redaction_status"] == "content_free_failure_metadata_only"
    assert payload["command_results"] == []


def test_local_lane_does_not_retry_failed_diagnostic_retention(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(local_lane, "_repository_sha", lambda: SHA)
    monkeypatch.setattr(
        local_lane,
        "run_lane",
        lambda *_args, **_kwargs: {"status": "fail"},
    )
    attempts = 0

    def reject_retention(*_args: object, **_kwargs: object) -> str:
        nonlocal attempts
        attempts += 1
        raise local_lane.LocalVerificationLaneError(
            "diagnostic lock is unavailable"
        )

    monkeypatch.setattr(local_lane, "_retain_diagnostics", reject_retention)

    with pytest.raises(
        local_lane.LocalVerificationLaneError,
        match="diagnostic lock is unavailable",
    ):
        local_lane.run_local_lane(
            "ci-pytest-shards",
            fence_root=tmp_path / "fence",
        )

    assert attempts == 1


def test_local_diagnostics_drop_untrusted_output_and_receipt_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(local_lane, "_repository_sha", lambda: SHA)

    def fake_run_lane(_lane_ref: str, **_kwargs: object) -> dict[str, object]:
        return {
            "status": "secret-like-value",
            "raw_output": "secret-like-value",
            "command_results": [
                {
                    "command_ref": "command:test.safe",
                    "status": "fail",
                    "output_byte_count": 17,
                    "output_digest": "b" * 64,
                    "raw_output": "secret-like-value",
                    "failed_test_refs": ("unsafe-local-detail",),
                }
            ],
        }

    monkeypatch.setattr(local_lane, "run_lane", fake_run_lane)

    assert local_lane.run_local_lane(
        "ci-pytest-shards",
        fence_root=tmp_path / "fence",
    ) == 1
    retained = tuple(
        path
        for path in (tmp_path / "diagnostics").iterdir()
        if len(path.name) == 64
    )
    encoded = retained[0].read_text(encoding="utf-8")
    assert "secret-like-value" not in encoded
    assert "unsafe-local-detail" not in encoded
    payload = json.loads(encoded)
    assert payload["status"] == "blocked"
    assert payload["command_results"] == [
        {
            "command_ref": "command:test.safe",
            "output_byte_count": 17,
            "output_digest": "b" * 64,
            "status": "fail",
        }
    ]


def test_local_diagnostic_retention_serializes_shared_pruning(
    tmp_path: Path,
) -> None:
    root = tmp_path / "diagnostics"
    receipt = {
        "status": "fail",
        "command_results": [
            {
                "command_ref": "command:test.safe",
                "status": "fail",
                "output_byte_count": 1,
                "output_digest": "c" * 64,
            }
        ],
    }

    def retain(_index: int) -> str:
        return local_lane._retain_diagnostics(
            receipt,
            diagnostic_root=root,
            lane_ref="ci-pytest-shards",
            repository_sha=SHA,
        )

    with ThreadPoolExecutor(max_workers=4) as executor:
        refs = tuple(executor.map(retain, range(12)))

    assert len(refs) == 12
    retained = tuple(path for path in root.iterdir() if len(path.name) == 64)
    assert len(retained) == local_lane.MAX_RETAINED_DIAGNOSTIC_RUNS
    assert all(path.is_file() for path in retained)


def test_local_diagnostic_retention_preserves_current_token_under_clock_skew(
    tmp_path: Path,
) -> None:
    root = tmp_path / "diagnostics"
    root.mkdir(mode=0o700)
    future_time = 4_102_444_800
    for index in range(local_lane.MAX_RETAINED_DIAGNOSTIC_RUNS):
        stale = root / f"{index:064x}"
        stale.write_text("{}\n", encoding="ascii")
        stale.chmod(0o600)
        os.utime(stale, (future_time, future_time))

    diagnostic_ref = local_lane._retain_diagnostics(
        None,
        diagnostic_root=root,
        lane_ref="ci-pytest-shards",
        repository_sha=SHA,
    )

    token = diagnostic_ref.rsplit(":", 1)[-1]
    retained = tuple(path for path in root.iterdir() if len(path.name) == 64)
    assert len(retained) == local_lane.MAX_RETAINED_DIAGNOSTIC_RUNS
    assert (root / token).is_file()


def test_local_diagnostic_enumeration_ignores_disappearing_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "diagnostics"
    root.mkdir(mode=0o700)
    missing_name = "a" * 64
    original_listdir = local_lane.os.listdir
    original_stat = local_lane.os.stat

    def include_disappearing_entry(path: object):
        if isinstance(path, int):
            return [missing_name]
        return original_listdir(path)

    def report_disappearance(
        path: object,
        *,
        dir_fd: int | None = None,
        follow_symlinks: bool = True,
    ):
        if path == missing_name and dir_fd is not None:
            raise FileNotFoundError("entry disappeared")
        return original_stat(
            path,
            dir_fd=dir_fd,
            follow_symlinks=follow_symlinks,
        )

    monkeypatch.setattr(local_lane.os, "listdir", include_disappearing_entry)
    monkeypatch.setattr(local_lane.os, "stat", report_disappearance)

    assert local_lane._retained_diagnostic_entries(root) == ()


def test_local_diagnostic_enumeration_rejects_unstatable_existing_entry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "diagnostics"
    root.mkdir(mode=0o700)
    entry = root / ("a" * 64)
    entry.mkdir()
    original_stat = local_lane.os.stat

    def reject_entry(
        path: object,
        *,
        dir_fd: int | None = None,
        follow_symlinks: bool = True,
    ):
        if path == entry.name and dir_fd is not None:
            raise OSError("metadata unavailable")
        return original_stat(
            path,
            dir_fd=dir_fd,
            follow_symlinks=follow_symlinks,
        )

    monkeypatch.setattr(local_lane.os, "stat", reject_entry)

    with pytest.raises(
        local_lane.LocalVerificationLaneError,
        match="diagnostics cannot be bounded",
    ):
        local_lane._retained_diagnostic_entries(root)


def test_local_diagnostic_retention_rejects_non_enumerable_owner_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "diagnostics"
    root.mkdir(mode=0o700)
    root.chmod(0o300)

    try:
        with pytest.raises(
            local_lane.LocalVerificationLaneError,
            match="diagnostic boundary is unsafe",
        ):
            local_lane._retain_diagnostics(
                None,
                diagnostic_root=root,
                lane_ref="ci-pytest-shards",
                repository_sha=SHA,
            )
    finally:
        root.chmod(0o700)


def test_local_diagnostic_retention_lock_times_out_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "diagnostics"
    root.mkdir(mode=0o700)
    monkeypatch.setattr(local_lane, "DIAGNOSTIC_LOCK_TIMEOUT_SECONDS", 0.0)
    original_flock = local_lane.fcntl.flock

    def reject_lock(descriptor: int, operation: int) -> None:
        if operation & local_lane.fcntl.LOCK_NB:
            raise BlockingIOError("lock held")
        original_flock(descriptor, operation)

    monkeypatch.setattr(local_lane.fcntl, "flock", reject_lock)

    with local_lane._pinned_diagnostic_root(root) as descriptor:
        with pytest.raises(
            local_lane.LocalVerificationLaneError,
            match="diagnostic lock is unavailable",
        ):
            with local_lane._locked_diagnostic_root(descriptor):
                pytest.fail("unavailable diagnostic lock was acquired")


def test_local_diagnostic_creation_rejects_precreated_token_atomically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "diagnostics"
    original_open = local_lane.os.open
    substituted_token: str | None = None

    def precreate_token(path: object, flags: int, *args: object, **kwargs: object):
        nonlocal substituted_token
        if (
            isinstance(path, str)
            and len(path) == 64
            and flags & os.O_CREAT
            and flags & os.O_EXCL
            and kwargs.get("dir_fd") is not None
        ):
            substituted_token = path
            (root / path).write_text("replacement", encoding="ascii")
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(local_lane.os, "open", precreate_token)

    with pytest.raises(
        local_lane.LocalVerificationLaneError,
        match="diagnostics cannot be bounded",
    ):
        local_lane._retain_diagnostics(
            None,
            diagnostic_root=root,
            lane_ref="ci-pytest-shards",
            repository_sha=SHA,
        )

    assert substituted_token is not None
    assert (root / substituted_token).read_text(encoding="ascii") == "replacement"


def test_local_diagnostic_retention_rolls_back_when_enumeration_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "diagnostics"
    original_listdir = local_lane.os.listdir
    calls = 0

    def fail_first_enumeration(path: object):
        nonlocal calls
        if isinstance(path, int) and calls == 0:
            calls += 1
            raise OSError("enumeration unavailable")
        return original_listdir(path)

    monkeypatch.setattr(local_lane.os, "listdir", fail_first_enumeration)

    with pytest.raises(
        local_lane.LocalVerificationLaneError,
        match="diagnostics cannot be bounded",
    ):
        local_lane._retain_diagnostics(
            None,
            diagnostic_root=root,
            lane_ref="ci-pytest-shards",
            repository_sha=SHA,
        )

    retained = tuple(path for path in root.iterdir() if len(path.name) == 64)
    assert retained == ()


def test_local_diagnostic_retention_rolls_back_when_stale_cleanup_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "diagnostics"
    root.mkdir(mode=0o700)
    stale_paths = []
    for index in range(local_lane.MAX_RETAINED_DIAGNOSTIC_RUNS):
        stale = root / f"{index:064x}"
        stale.mkdir(mode=0o700)
        stale_paths.append(stale)
    original_rmtree = local_lane.shutil.rmtree

    def reject_stale_cleanup(
        path: object,
        *,
        dir_fd: int | None = None,
    ) -> None:
        if isinstance(path, str) and path in {item.name for item in stale_paths}:
            raise PermissionError("cleanup unavailable")
        original_rmtree(path, dir_fd=dir_fd)

    monkeypatch.setattr(local_lane.shutil, "rmtree", reject_stale_cleanup)

    with pytest.raises(
        local_lane.LocalVerificationLaneError,
        match="diagnostics cannot be bounded",
    ):
        local_lane._retain_diagnostics(
            None,
            diagnostic_root=root,
            lane_ref="ci-pytest-shards",
            repository_sha=SHA,
        )

    retained = tuple(path for path in root.iterdir() if len(path.name) == 64)
    assert set(retained) == set(stale_paths)
    for stale in stale_paths:
        original_rmtree(stale)


def test_local_diagnostic_cleanup_verifies_root_after_descendant_disappears(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "diagnostics"
    root.mkdir(mode=0o700)
    destination_name = "a" * 64
    (root / destination_name).mkdir(mode=0o700)

    def report_descendant_disappearance(
        _path: object,
        *,
        dir_fd: int | None = None,
    ) -> None:
        raise FileNotFoundError("descendant disappeared")

    monkeypatch.setattr(
        local_lane.shutil,
        "rmtree",
        report_descendant_disappearance,
    )

    with local_lane._pinned_diagnostic_root(root) as descriptor:
        with pytest.raises(
            local_lane.LocalVerificationLaneError,
            match="diagnostics cannot be bounded",
        ):
            local_lane._remove_diagnostic_entry_at(
                descriptor,
                destination_name,
            )

    assert (root / destination_name).is_dir()


def test_local_diagnostic_retention_rejects_root_path_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "diagnostics"
    moved_root = tmp_path / "moved-diagnostics"
    replacement = tmp_path / "replacement"
    replacement.mkdir(mode=0o700)
    sentinel = replacement / ("f" * 64)
    sentinel.mkdir(mode=0o700)
    original_write = local_lane._write_diagnostic_envelope

    def swap_root_after_write(*args: object, **kwargs: object):
        result = original_write(*args, **kwargs)
        root.rename(moved_root)
        root.symlink_to(replacement, target_is_directory=True)
        return result

    monkeypatch.setattr(
        local_lane,
        "_write_diagnostic_envelope",
        swap_root_after_write,
    )

    try:
        with pytest.raises(
            local_lane.LocalVerificationLaneError,
            match="diagnostic boundary is unsafe",
        ):
            local_lane._retain_diagnostics(
                None,
                diagnostic_root=root,
                lane_ref="ci-pytest-shards",
                repository_sha=SHA,
            )
    finally:
        if root.is_symlink():
            root.unlink()

    assert (
        tuple(
            path
            for path in moved_root.iterdir()
            if path.name != ".uaa-diagnostic-retention.lock"
        )
        == ()
    )
    assert sentinel.is_dir()


def test_local_diagnostic_retention_rejects_token_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "diagnostics"
    moved_name = "moved-original"
    replacement_name: str | None = None
    original_write = local_lane._write_diagnostic_envelope

    def substitute_token(*args: object, **kwargs: object):
        nonlocal replacement_name
        result = original_write(*args, **kwargs)
        token_paths = tuple(
            path
            for path in root.iterdir()
            if len(path.name) == 64 and path.is_file()
        )
        assert len(token_paths) == 1
        replacement_name = token_paths[0].name
        token_paths[0].rename(root / moved_name)
        (root / replacement_name).write_text("replacement", encoding="ascii")
        return result

    monkeypatch.setattr(
        local_lane,
        "_write_diagnostic_envelope",
        substitute_token,
    )

    with pytest.raises(
        local_lane.LocalVerificationLaneError,
        match="diagnostics cannot be bounded",
    ):
        local_lane._retain_diagnostics(
            None,
            diagnostic_root=root,
            lane_ref="ci-pytest-shards",
            repository_sha=SHA,
        )

    assert not (root / moved_name).exists()
    assert replacement_name is not None
    (root / replacement_name).unlink()


def test_local_diagnostic_retention_rejects_payload_tampering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "diagnostics"
    original_write = local_lane._write_diagnostic_envelope

    def tamper_with_payload(*args: object, **kwargs: object):
        encoded = original_write(*args, **kwargs)
        descriptor = args[0]
        assert isinstance(descriptor, int)
        os.lseek(descriptor, 0, os.SEEK_SET)
        os.write(descriptor, b"X")
        os.fsync(descriptor)
        return encoded

    monkeypatch.setattr(
        local_lane,
        "_write_diagnostic_envelope",
        tamper_with_payload,
    )

    with pytest.raises(
        local_lane.LocalVerificationLaneError,
        match="diagnostics cannot be bounded",
    ):
        local_lane._retain_diagnostics(
            None,
            diagnostic_root=root,
            lane_ref="ci-pytest-shards",
            repository_sha=SHA,
        )

    assert tuple(path for path in root.iterdir() if len(path.name) == 64) == ()


def test_local_diagnostic_retention_rolls_back_on_unexpected_unwind(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "diagnostics"

    def interrupt_after_creation(*_args: object, **_kwargs: object) -> bytes:
        raise KeyboardInterrupt("interrupt diagnostic retention")

    monkeypatch.setattr(
        local_lane,
        "_write_diagnostic_envelope",
        interrupt_after_creation,
    )

    with pytest.raises(KeyboardInterrupt, match="interrupt diagnostic retention"):
        local_lane._retain_diagnostics(
            None,
            diagnostic_root=root,
            lane_ref="ci-pytest-shards",
            repository_sha=SHA,
        )

    assert tuple(path for path in root.iterdir() if len(path.name) == 64) == ()


@pytest.mark.parametrize("terminal_status", ("timed_out", "cancelled"))
def test_local_diagnostic_retention_preserves_terminal_status(
    tmp_path: Path,
    terminal_status: str,
) -> None:
    root = tmp_path / "diagnostics"
    local_lane._retain_diagnostics(
        {
            "status": terminal_status,
            "command_results": [
                {
                    "command_ref": "command:test.safe",
                    "status": terminal_status,
                    "output_byte_count": 1,
                    "output_digest": "d" * 64,
                }
            ],
        },
        diagnostic_root=root,
        lane_ref="ci-pytest-shards",
        repository_sha=SHA,
    )

    retained = tuple(path for path in root.iterdir() if len(path.name) == 64)
    assert len(retained) == 1
    payload = json.loads(retained[0].read_text(encoding="utf-8"))
    assert payload["status"] == terminal_status


def test_local_pytest_profile_is_validated_and_published_atomically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(local_lane, "_repository_sha", lambda: SHA)

    def fake_run_lane(_lane_ref: str, **kwargs: object) -> dict[str, object]:
        temp_root = kwargs["temp_root"]
        assert isinstance(temp_root, Path)
        (temp_root / local_lane.PYTEST_FILE_TIMINGS_NAME).write_text(
            json.dumps(
                {
                    "schema_version": local_lane.TIMING_SCHEMA_VERSION,
                    "timings": {
                        "tests/test_safe.py": 1.25,
                    },
                }
            ),
            encoding="utf-8",
        )
        return {"status": "pass"}

    monkeypatch.setattr(local_lane, "run_lane", fake_run_lane)
    output = tmp_path / "profile.json"

    assert (
        local_lane.run_local_lane(
            "ci-pytest-shards",
            fence_root=tmp_path / "fence",
            profile_output=output,
        )
        == 0
    )
    assert json.loads(output.read_text(encoding="utf-8"))["timings"] == {
        "tests/test_safe.py": 1.25
    }


def test_local_pytest_profile_rejects_unsafe_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(local_lane, "_repository_sha", lambda: SHA)

    def fake_run_lane(_lane_ref: str, **kwargs: object) -> dict[str, object]:
        temp_root = kwargs["temp_root"]
        assert isinstance(temp_root, Path)
        (temp_root / local_lane.PYTEST_FILE_TIMINGS_NAME).write_text(
            json.dumps(
                {
                    "schema_version": local_lane.TIMING_SCHEMA_VERSION,
                    "timings": {
                        "../unsafe.py": 1.0,
                    },
                }
            ),
            encoding="utf-8",
        )
        return {"status": "pass"}

    monkeypatch.setattr(local_lane, "run_lane", fake_run_lane)

    with pytest.raises(
        local_lane.LocalVerificationLaneError,
        match="unsafe entries",
    ):
        local_lane.run_local_lane(
            "ci-pytest-shards",
            fence_root=tmp_path / "fence",
            profile_output=tmp_path / "profile.json",
        )


def test_local_lane_cli_redacts_internal_failures(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    unsafe = "unsafe-local-detail"

    def fail(*_args: object, **_kwargs: object) -> int:
        raise local_lane.LocalVerificationLaneError(unsafe)

    monkeypatch.setattr(local_lane, "run_local_lane", fail)

    assert (
        local_lane.main(
            [
                "--lane",
                "ci-pytest-shards",
            ]
        )
        == 1
    )
    output = capsys.readouterr().out
    assert "reason-ref:verification:exclusive-resource-unavailable" in output
    assert unsafe not in output
