from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.verification import ci_fallback_execution as execution
from scripts.verification import ci_fallback_contracts as contracts
from scripts.verification.ci_command_manifest import (
    PROFILE_REF,
    CommandSpec,
    VerificationPlan,
    build_plan,
    lane_registry,
)


SHA = "a" * 40
ROOT = Path(__file__).resolve().parents[1]


def _pass_command_result(command_ref: str, category: str) -> dict[str, object]:
    duration_ms = 1000
    output_digest = hashlib.sha256(b"").hexdigest()
    result_ref = (
        "result-ref:ci:"
        + hashlib.sha256(
            "|".join((command_ref, SHA, "0", output_digest, str(duration_ms))).encode()
        ).hexdigest()
    )
    return {
        "command_ref": command_ref,
        "category": category,
        "status": "pass",
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:01Z",
        "duration_ms": duration_ms,
        "output_byte_count": 0,
        "output_digest": output_digest,
        "result_ref": result_ref,
        "redaction_status": "content_free_output_metadata_only",
    }


def _lane_receipt_payload(
    lane_ref: str, plan: VerificationPlan, command_results: list[dict[str, object]]
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "uaa_ci_lane_receipt.v1",
        "profile_ref": PROFILE_REF,
        "repository_sha": SHA,
        "lane_ref": lane_ref,
        "plan": asdict(plan),
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:01Z",
        "duration_ms": 1000,
        "status": "pass",
        "command_results": command_results,
        "github_gate_satisfied": False,
        "merge_gate_satisfied": False,
        "redaction_status": "content_free_refs_hashes_counts_and_durations_only",
    }
    payload["receipt_ref"] = (
        "receipt-ref:ci-lane:"
        + hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    return payload


def _write_receipt(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")
    path.chmod(0o600)


def test_pytest_shard_evidence_validation_is_exact_and_fail_closed() -> None:
    plan_ref = "pytest-shard-plan-ref:sha256:" + "b" * 64
    result = {
        **_pass_command_result("command:pytest.sharded-suite", "test"),
        "pytest_shard_evidence_status": "available",
        "pytest_shard_plan_fingerprint_ref": plan_ref,
        "pytest_shard_count": 8,
        "failed_shard_count": 0,
        "failed_shard_refs": [],
    }

    assert contracts.has_valid_command_result_evidence(
        result,
        lane_ref="ci-pytest-shards",
        repository_sha=SHA,
        expected_category="test",
        expected_pytest_plan_ref=plan_ref,
        satisfied_by_dependency=False,
    )
    for unsafe_update in (
        {"status": "fail"},
        {"category": "wrong"},
        {"started_at": "not-a-timestamp"},
        {"duration_ms": -1},
        {"output_digest": "0" * 63},
        {"result_ref": f"result-ref:ci:{'e' * 64}"},
        {
            "pytest_shard_plan_fingerprint_ref": "pytest-shard-plan-ref:sha256:"
            + "c" * 64
        },
        {"failed_shard_count": 1},
        {"failed_shard_refs": ["pytest-shard-ref:0:failed"]},
        {"raw_log": "denied"},
    ):
        assert not contracts.has_valid_command_result_evidence(
            {**result, **unsafe_update},
            lane_ref="ci-pytest-shards",
            repository_sha=SHA,
            expected_category="test",
            expected_pytest_plan_ref=plan_ref,
            satisfied_by_dependency=False,
        )
    assert not contracts.has_valid_command_result_evidence(
        result,
        lane_ref="docs",
        repository_sha=SHA,
        expected_category="test",
        expected_pytest_plan_ref=plan_ref,
        satisfied_by_dependency=False,
    )


def test_private_preflight_requires_clean_pushed_canonical_origin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = execution.IsolatedPrivateExecutor(tmp_path)
    values = {
        ("rev-parse", "HEAD"): SHA,
        ("rev-parse", "refs/remotes/origin/main"): "b" * 40,
        ("status", "--porcelain"): "",
        ("remote", "get-url", "origin"): "https://invalid.example/repository.git",
        ("branch", "-r", "--contains", SHA): "origin/feature",
    }
    monkeypatch.setattr(executor, "_git", lambda *args: values[args])
    monkeypatch.setattr(execution, "private_verification_plan", lambda *_args: object())
    with pytest.raises(ValueError, match="canonical UAA"):
        executor._preflight(SHA)
    values[("remote", "get-url", "origin")] = (
        "git@github.com:doncazper/ultimate-ai-agent.git"
    )
    assert executor._preflight(SHA) == "b" * 40


def test_private_worktree_rejects_symlinked_selected_command_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worktree = tmp_path / "worktree"
    for ref in (
        "pyproject.toml",
        "uv.lock",
        "apps/control-center/package-lock.json",
        "scripts/verification/run_ci_lane.py",
    ):
        target = worktree / ref
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("safe", encoding="utf-8")
    unsafe_target = worktree / "safe-target.py"
    unsafe_target.write_text("safe", encoding="utf-8")
    unsafe_command = worktree / "scripts/unsafe.py"
    unsafe_command.symlink_to(unsafe_target)
    monkeypatch.setattr(
        execution,
        "command_registry",
        lambda: {
            "command:test": CommandSpec(
                "command:test",
                (".venv/bin/python", "scripts/unsafe.py"),
                (),
                "test",
                10,
            )
        },
    )
    with pytest.raises(ValueError, match="command repository path"):
        execution.IsolatedPrivateExecutor._validate_worktree(worktree, SHA)


def test_private_worktree_binds_exact_detached_sha(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worktree = tmp_path / "worktree"
    for ref in (
        "pyproject.toml",
        "uv.lock",
        "apps/control-center/package-lock.json",
        "scripts/verification/run_ci_lane.py",
    ):
        target = worktree / ref
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("safe", encoding="utf-8")
    monkeypatch.setattr(execution, "command_registry", lambda: {})
    monkeypatch.setattr(
        execution.subprocess,
        "run",
        lambda args, **_kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=(b"" if tuple(args[:2]) == ("git", "ls-files") else "b" * 40 + "\n"),
            stderr=b"" if tuple(args[:2]) == ("git", "ls-files") else "",
        ),
    )
    with pytest.raises(ValueError, match="SHA changed"):
        execution.IsolatedPrivateExecutor._validate_worktree(worktree, SHA)


def test_private_execution_uses_standalone_clone_not_shared_worktree() -> None:
    source = Path(execution.__file__).read_text(encoding="utf-8")
    assert '"clone"' in source
    assert '"--no-local"' in source
    assert 'self._git("rev-parse", "refs/remotes/origin/main")' in source
    assert "origin_main_sha" in source
    assert "PRIVATE_BASE_REF" in source
    assert '("git", "remote", "remove", "origin")' in source
    assert '"worktree", "add"' not in source


@pytest.mark.parametrize(("returncode", "expected"), ((0, False), (1, True), (2, True)))
def test_private_affected_preflight_frontend_dependency_is_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    returncode: int,
    expected: bool,
) -> None:
    monkeypatch.setattr(
        execution.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=returncode
        ),
    )

    assert (
        execution.IsolatedPrivateExecutor._affected_preflight_requires_frontend(
            tmp_path
        )
        is expected
    )


def test_private_frontend_dependencies_are_installed_before_affected_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    def fake_subprocess(argv, **_kwargs):
        events.append(" ".join(argv))
        return 0, 1, "result-ref:ci:test"

    def fake_lane(lane_ref: str, **_kwargs):
        events.append(f"lane:{lane_ref}")
        return True

    monkeypatch.setattr(execution, "_safe_subprocess", fake_subprocess)
    monkeypatch.setattr(
        execution.IsolatedPrivateExecutor,
        "_affected_preflight_requires_frontend",
        staticmethod(lambda _worktree: True),
    )
    monkeypatch.setattr(
        execution.IsolatedPrivateExecutor, "_run_lane", staticmethod(fake_lane)
    )
    monkeypatch.setattr(
        execution,
        "CI_JOB_GRAPH",
        (SimpleNamespace(lane_ref="ci-affected-preflight"),),
    )
    monkeypatch.setattr(execution.shutil, "which", lambda *_args, **_kwargs: None)
    plan = SimpleNamespace(
        definition_fingerprint="a" * 64,
        dependency_lock_fingerprints=(),
        pytest_shard_plan_fingerprint="b" * 64,
    )

    status = execution.IsolatedPrivateExecutor._run_graph(
        SHA,
        tmp_path,
        tmp_path,
        {"PATH": "/usr/bin"},
        [],
        [],
        plan,
    )

    assert status == "pass"
    assert events[:2] == ["npm ci", "lane:ci-affected-preflight"]
    assert events.count("lane:ci-affected-preflight") == 1


def test_private_lane_refs_include_affected_preflight_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert execution.PRIVATE_LANE_REFS.count("ci-affected-preflight") == 1
    observed: dict[str, object] = {}

    def fake_build_plan(
        repo: Path,
        repository_sha: str,
        *,
        lane_refs: tuple[str, ...],
    ) -> object:
        observed.update(
            repo=repo,
            repository_sha=repository_sha,
            lane_refs=lane_refs,
        )
        return object()

    monkeypatch.setattr(execution, "build_plan", fake_build_plan)
    plan = execution.private_verification_plan(ROOT, SHA)
    assert plan is not None
    assert observed["lane_refs"] == execution.PRIVATE_LANE_REFS


def test_private_and_lane_environments_share_playwright_browser_directory(
    tmp_path: Path,
) -> None:
    from scripts.verification import run_ci_lane

    private_env = execution._minimal_env(tmp_path)
    lane_temp = tmp_path / "lane-temp"
    command = CommandSpec("command:test", ("true",), (), "test", 10)
    lane_env = run_ci_lane._safe_env(command, lane_temp)

    assert (
        private_env["PLAYWRIGHT_BROWSERS_PATH"] == lane_env["PLAYWRIGHT_BROWSERS_PATH"]
    )


def test_private_lane_receipt_is_recomputed_and_exact_plan_bound(
    tmp_path: Path,
) -> None:
    lane_ref = "docs"
    plan = build_plan(
        ROOT,
        SHA,
        lane_refs=(lane_ref,),
        frontend_visual_scope="unknown_fail_closed",
        verify_repository_state=False,
    )
    lane = lane_registry()[lane_ref]
    payload: dict[str, object] = {
        "schema_version": "uaa_ci_lane_receipt.v1",
        "profile_ref": PROFILE_REF,
        "repository_sha": SHA,
        "lane_ref": lane_ref,
        "plan": asdict(plan),
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:01Z",
        "duration_ms": 1000,
        "status": "pass",
        "command_results": [
            _pass_command_result(
                command_ref, execution.command_registry()[command_ref].category
            )
            for command_ref in lane.command_refs
        ],
        "github_gate_satisfied": False,
        "merge_gate_satisfied": False,
        "redaction_status": "content_free_refs_hashes_counts_and_durations_only",
    }
    payload["receipt_ref"] = (
        "receipt-ref:ci-lane:"
        + hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(payload), encoding="utf-8")
    receipt_path.chmod(0o600)

    receipt_ref = execution._read_lane_receipt(
        receipt_path,
        lane_ref=lane_ref,
        expected_plan=plan,
    )

    assert receipt_ref == payload["receipt_ref"]
    assert not receipt_path.exists()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("repository_sha", "b" * 40),
        ("schema_version", "wrong"),
        ("profile_ref", "profile-ref:wrong"),
        ("redaction_status", "unsafe"),
    ],
)
def test_private_lane_receipt_rejects_self_consistent_wrong_plan(
    tmp_path: Path, field: str, value: str
) -> None:
    lane_ref = "docs"
    plan = build_plan(ROOT, SHA, lane_refs=(lane_ref,), verify_repository_state=False)
    lane = lane_registry()[lane_ref]
    results = [
        _pass_command_result(ref, execution.command_registry()[ref].category)
        for ref in lane.command_refs
    ]
    payload = _lane_receipt_payload(lane_ref, plan, results)
    assert isinstance(payload["plan"], dict)
    payload["plan"][field] = value
    payload["receipt_ref"] = (
        "receipt-ref:ci-lane:"
        + hashlib.sha256(
            json.dumps(
                {key: item for key, item in payload.items() if key != "receipt_ref"},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
    )
    receipt_path = tmp_path / "receipt.json"
    _write_receipt(receipt_path, payload)

    with pytest.raises(ValueError, match="exact plan"):
        execution._read_lane_receipt(
            receipt_path,
            lane_ref=lane_ref,
            expected_plan=plan,
        )


def test_private_pytest_lane_accepts_exact_safe_shard_evidence(tmp_path: Path) -> None:
    lane_ref = "ci-pytest-shards"
    plan = build_plan(
        ROOT,
        SHA,
        lane_refs=(lane_ref,),
        verify_repository_state=False,
    )
    lane = lane_registry()[lane_ref]
    expected_plan_ref = execution.expected_pytest_shard_plan_ref()
    payload: dict[str, object] = {
        "schema_version": "uaa_ci_lane_receipt.v1",
        "profile_ref": PROFILE_REF,
        "repository_sha": SHA,
        "lane_ref": lane_ref,
        "plan": asdict(plan),
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:01Z",
        "duration_ms": 1000,
        "status": "pass",
        "command_results": [
            {
                **_pass_command_result(lane.command_refs[0], "test"),
                "pytest_shard_evidence_status": "available",
                "pytest_shard_plan_fingerprint_ref": expected_plan_ref,
                "pytest_shard_count": 8,
                "failed_shard_count": 0,
                "failed_shard_refs": [],
            }
        ],
        "github_gate_satisfied": False,
        "merge_gate_satisfied": False,
        "redaction_status": "content_free_refs_hashes_counts_and_durations_only",
    }
    payload["receipt_ref"] = (
        "receipt-ref:ci-lane:"
        + hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(payload), encoding="utf-8")
    receipt_path.chmod(0o600)

    assert (
        execution._read_lane_receipt(
            receipt_path,
            lane_ref=lane_ref,
            expected_plan=plan,
        )
        == payload["receipt_ref"]
    )


def test_private_lane_receipt_rejects_incomplete_command_evidence(
    tmp_path: Path,
) -> None:
    lane_ref = "docs"
    plan = build_plan(
        ROOT,
        SHA,
        lane_refs=(lane_ref,),
        verify_repository_state=False,
    )
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(
        json.dumps(
            {
                "schema_version": "uaa_ci_lane_receipt.v1",
                "profile_ref": PROFILE_REF,
                "repository_sha": SHA,
                "lane_ref": lane_ref,
                "plan": asdict(plan),
                "started_at": "2026-01-01T00:00:00Z",
                "completed_at": "2026-01-01T00:00:01Z",
                "duration_ms": 1000,
                "status": "pass",
                "command_results": [],
                "github_gate_satisfied": False,
                "merge_gate_satisfied": False,
                "redaction_status": "content_free_refs_hashes_counts_and_durations_only",
                "receipt_ref": f"receipt-ref:ci-lane:{'0' * 64}",
            }
        ),
        encoding="utf-8",
    )
    receipt_path.chmod(0o600)

    with pytest.raises(ValueError, match="command membership"):
        execution._read_lane_receipt(
            receipt_path,
            lane_ref=lane_ref,
            expected_plan=plan,
        )
