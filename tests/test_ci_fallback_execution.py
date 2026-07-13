from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts.verification import ci_fallback_execution as execution
from scripts.verification.ci_command_manifest import (
    PROFILE_REF,
    CommandSpec,
    build_plan,
    lane_registry,
)


SHA = "a" * 40
ROOT = Path(__file__).resolve().parents[1]


def test_private_preflight_requires_clean_pushed_canonical_origin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = execution.IsolatedPrivateExecutor(tmp_path)
    values = {
        ("rev-parse", "HEAD"): SHA,
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
    executor._preflight(SHA)


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
            stdout=(
                b""
                if tuple(args[:2]) == ("git", "ls-files")
                else "b" * 40 + "\n"
            ),
            stderr=b"" if tuple(args[:2]) == ("git", "ls-files") else "",
        ),
    )
    with pytest.raises(ValueError, match="SHA changed"):
        execution.IsolatedPrivateExecutor._validate_worktree(worktree, SHA)


def test_private_execution_uses_standalone_clone_not_shared_worktree() -> None:
    source = Path(execution.__file__).read_text(encoding="utf-8")
    assert '"clone"' in source
    assert '"--no-local"' in source
    assert '"refs/remotes/origin/main"' in source
    assert "PRIVATE_BASE_REF" in source
    assert '("git", "remote", "remove", "origin")' in source
    assert '"worktree", "add"' not in source


def test_private_lane_receipt_is_recomputed_and_exact_plan_bound(tmp_path: Path) -> None:
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
            {
                "command_ref": command_ref,
                "category": "release_lane",
                "status": "pass",
                "started_at": "2026-01-01T00:00:00Z",
                "completed_at": "2026-01-01T00:00:01Z",
                "duration_ms": 1000,
                "output_byte_count": 0,
                "output_digest": hashlib.sha256(b"").hexdigest(),
                "result_ref": f"result-ref:ci:{'d' * 64}",
                "redaction_status": "content_free_output_metadata_only",
            }
            for command_ref in lane.command_refs
        ],
        "github_gate_satisfied": False,
        "merge_gate_satisfied": False,
        "redaction_status": "content_free_refs_hashes_counts_and_durations_only",
    }
    payload["receipt_ref"] = "receipt-ref:ci-lane:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(payload), encoding="utf-8")
    receipt_path.chmod(0o600)

    receipt_ref = execution._read_lane_receipt(
        receipt_path,
        lane_ref=lane_ref,
        repository_sha=SHA,
        definition_ref=plan.definition_fingerprint,
        lock_fingerprints=plan.dependency_lock_fingerprints,
        shard_plan_fingerprint=plan.pytest_shard_plan_fingerprint,
        visual_scope=plan.frontend_visual_scope,
    )

    assert receipt_ref == payload["receipt_ref"]
    assert not receipt_path.exists()


def test_private_lane_receipt_rejects_incomplete_command_evidence(tmp_path: Path) -> None:
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
            repository_sha=SHA,
            definition_ref=plan.definition_fingerprint,
            lock_fingerprints=plan.dependency_lock_fingerprints,
            shard_plan_fingerprint=plan.pytest_shard_plan_fingerprint,
            visual_scope=plan.frontend_visual_scope,
        )
