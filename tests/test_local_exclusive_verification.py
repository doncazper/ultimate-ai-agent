from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import copy
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


def _diagnostic_entries(root: Path) -> list[dict[str, object]]:
    store = json.loads(
        (root / local_lane.DIAGNOSTIC_STORE_NAME).read_text(encoding="utf-8")
    )
    assert store["schema_version"] == "uaa_local_diagnostic_store.v1"
    entries = store["entries"]
    assert isinstance(entries, list)
    return entries


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
    retained = _diagnostic_entries(tmp_path / "diagnostics")
    assert len(retained) == 1
    payload = retained[0]["payload"]
    assert isinstance(payload, dict)
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
    retained = _diagnostic_entries(tmp_path / "diagnostics")
    encoded = json.dumps(retained[0]["payload"], sort_keys=True)
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
    retained = _diagnostic_entries(root)
    assert len(retained) == local_lane.MAX_RETAINED_DIAGNOSTIC_RUNS
    retained_tokens = {entry["token"] for entry in retained}
    assert retained_tokens.issubset({ref.rsplit(":", 1)[-1] for ref in refs})


def test_local_diagnostic_retention_uses_insertion_order_not_clock_time(
    tmp_path: Path,
) -> None:
    root = tmp_path / "diagnostics"
    refs = tuple(
        local_lane._retain_diagnostics(
            None,
            diagnostic_root=root,
            lane_ref="ci-pytest-shards",
            repository_sha=SHA,
        )
        for _index in range(local_lane.MAX_RETAINED_DIAGNOSTIC_RUNS + 2)
    )

    retained = _diagnostic_entries(root)
    assert len(retained) == local_lane.MAX_RETAINED_DIAGNOSTIC_RUNS
    assert [entry["token"] for entry in retained] == [
        ref.rsplit(":", 1)[-1]
        for ref in refs[-local_lane.MAX_RETAINED_DIAGNOSTIC_RUNS :]
    ]


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


def test_local_diagnostic_store_rejects_precreated_corrupt_state(
    tmp_path: Path,
) -> None:
    root = tmp_path / "diagnostics"
    root.mkdir(mode=0o700)
    store = root / local_lane.DIAGNOSTIC_STORE_NAME
    store.write_text("corrupt", encoding="ascii")
    store.chmod(0o600)

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

    assert store.read_text(encoding="ascii") == "corrupt"


@pytest.mark.parametrize(
    "tamper_case",
    (
        "extra-envelope-field",
        "unsafe-lane",
        "invalid-repository-sha",
        "invalid-terminal-status",
        "unsafe-command-ref",
        "boolean-byte-count",
        "invalid-output-digest",
        "unsafe-shard-ref",
        "unsafe-test-ref",
    ),
)
def test_local_diagnostic_store_rejects_every_untrusted_payload_field(
    tmp_path: Path,
    tamper_case: str,
) -> None:
    root = tmp_path / "diagnostics"
    root.mkdir(mode=0o700)
    payload: dict[str, object] = {
        "schema_version": "uaa_local_verification_diagnostic.v1",
        "lane_ref": "ci-pytest-shards",
        "repository_sha": SHA,
        "status": "fail",
        "command_results": [
            {
                "command_ref": "command:pytest.sharded-suite",
                "status": "fail",
                "output_byte_count": 1,
                "output_digest": "b" * 64,
                "failed_shard_refs": ["pytest-shard-ref:0:failed"],
                "failed_test_refs": [safe_test_ref("tests/test_safe.py::test_safe")],
            }
        ],
        "redaction_status": "content_free_failure_metadata_only",
    }
    tampered = copy.deepcopy(payload)
    result = tampered["command_results"][0]
    assert isinstance(result, dict)
    if tamper_case == "extra-envelope-field":
        tampered["raw_output"] = "not-allowed"
    elif tamper_case == "unsafe-lane":
        tampered["lane_ref"] = "ci-unknown"
    elif tamper_case == "invalid-repository-sha":
        tampered["repository_sha"] = "not-a-sha"
    elif tamper_case == "invalid-terminal-status":
        tampered["status"] = "pass"
    elif tamper_case == "unsafe-command-ref":
        result["command_ref"] = "rm -rf"
    elif tamper_case == "boolean-byte-count":
        result["output_byte_count"] = True
    elif tamper_case == "invalid-output-digest":
        result["output_digest"] = "not-a-digest"
    elif tamper_case == "unsafe-shard-ref":
        result["failed_shard_refs"] = ["pytest-shard-ref:99:failed"]
    elif tamper_case == "unsafe-test-ref":
        result["failed_test_refs"] = ["raw-secret-path"]
    store = root / local_lane.DIAGNOSTIC_STORE_NAME
    original_store = (
        json.dumps(
            {
                "schema_version": "uaa_local_diagnostic_store.v1",
                "entries": [{"token": "c" * 64, "payload": tampered}],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    store.write_bytes(original_store)
    store.chmod(0o600)

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

    assert store.read_bytes() == original_store


def test_local_diagnostic_store_restores_previous_bytes_when_write_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "diagnostics"
    local_lane._retain_diagnostics(
        None,
        diagnostic_root=root,
        lane_ref="ci-pytest-shards",
        repository_sha=SHA,
    )
    store = root / local_lane.DIAGNOSTIC_STORE_NAME
    original_store = store.read_bytes()
    original_replace = local_lane._replace_descriptor_bytes
    calls = 0

    def fail_first_write(descriptor: int, encoded: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            os.ftruncate(descriptor, 0)
            raise OSError("store write unavailable")
        original_replace(descriptor, encoded)

    monkeypatch.setattr(
        local_lane,
        "_replace_descriptor_bytes",
        fail_first_write,
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

    assert calls == 2
    assert store.read_bytes() == original_store


def test_local_diagnostic_store_never_deletes_legacy_named_entries(
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
    cleanup_attempted = False

    def reject_stale_cleanup(*_args: object, **_kwargs: object) -> None:
        nonlocal cleanup_attempted
        cleanup_attempted = True
        raise AssertionError("diagnostic journal must not prune path entries")

    monkeypatch.setattr(local_lane.shutil, "rmtree", reject_stale_cleanup)

    local_lane._retain_diagnostics(
        None,
        diagnostic_root=root,
        lane_ref="ci-pytest-shards",
        repository_sha=SHA,
    )

    assert cleanup_attempted is False
    assert all(stale.is_dir() for stale in stale_paths)
    assert len(_diagnostic_entries(root)) == 1


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
    original_write = local_lane._replace_descriptor_bytes
    swapped = False

    def swap_root_after_write(descriptor: int, encoded: bytes) -> None:
        nonlocal swapped
        original_write(descriptor, encoded)
        if not swapped:
            swapped = True
            root.rename(moved_root)
            root.symlink_to(replacement, target_is_directory=True)

    monkeypatch.setattr(
        local_lane,
        "_replace_descriptor_bytes",
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

    moved_store = moved_root / local_lane.DIAGNOSTIC_STORE_NAME
    assert moved_store.read_bytes() == b""
    assert sentinel.is_dir()


def test_local_diagnostic_store_rejects_named_inode_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "diagnostics"
    moved_name = "moved-original"
    original_write = local_lane._replace_descriptor_bytes
    substituted = False

    def substitute_store(descriptor: int, encoded: bytes) -> None:
        nonlocal substituted
        original_write(descriptor, encoded)
        if not substituted:
            substituted = True
            store = root / local_lane.DIAGNOSTIC_STORE_NAME
            store.rename(root / moved_name)
            store.write_text("replacement", encoding="ascii")
            store.chmod(0o600)

    monkeypatch.setattr(
        local_lane,
        "_replace_descriptor_bytes",
        substitute_store,
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

    assert (root / moved_name).read_bytes() == b""
    assert (
        root / local_lane.DIAGNOSTIC_STORE_NAME
    ).read_text(encoding="ascii") == "replacement"


def test_local_diagnostic_store_rejects_payload_tampering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "diagnostics"
    original_write = local_lane._replace_descriptor_bytes
    tampered = False

    def tamper_with_payload(descriptor: int, encoded: bytes) -> None:
        nonlocal tampered
        original_write(descriptor, encoded)
        if not tampered:
            tampered = True
            os.lseek(descriptor, 0, os.SEEK_SET)
            os.write(descriptor, b"X")
            os.fsync(descriptor)

    monkeypatch.setattr(
        local_lane,
        "_replace_descriptor_bytes",
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

    assert (root / local_lane.DIAGNOSTIC_STORE_NAME).read_bytes() == b""


def test_local_diagnostic_retention_rolls_back_on_unexpected_unwind(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "diagnostics"
    original_write = local_lane._replace_descriptor_bytes
    interrupted = False

    def interrupt_after_write(descriptor: int, encoded: bytes) -> None:
        nonlocal interrupted
        original_write(descriptor, encoded)
        if not interrupted:
            interrupted = True
            raise KeyboardInterrupt("interrupt diagnostic retention")

    monkeypatch.setattr(
        local_lane,
        "_replace_descriptor_bytes",
        interrupt_after_write,
    )

    with pytest.raises(KeyboardInterrupt, match="interrupt diagnostic retention"):
        local_lane._retain_diagnostics(
            None,
            diagnostic_root=root,
            lane_ref="ci-pytest-shards",
            repository_sha=SHA,
        )

    assert (root / local_lane.DIAGNOSTIC_STORE_NAME).read_bytes() == b""


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

    retained = _diagnostic_entries(root)
    assert len(retained) == 1
    payload = retained[0]["payload"]
    assert isinstance(payload, dict)
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
