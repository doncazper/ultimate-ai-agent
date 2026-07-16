from __future__ import annotations

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
