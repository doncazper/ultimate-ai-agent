from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

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
        ("status", "--porcelain"): "",
        ("remote", "get-url", "origin"): "https://invalid.example/repository.git",
        ("branch", "--show-current"): "feature",
    }
    monkeypatch.setattr(executor, "_git", lambda *args: values[args])
    monkeypatch.setattr(
        executor,
        "_live_advertised_heads",
        lambda: (("b" * 40, "refs/heads/main"), (SHA, "refs/heads/feature")),
    )
    with pytest.raises(ValueError, match="canonical UAA"):
        executor._preflight(SHA)
    values[("remote", "get-url", "origin")] = (
        "git@github.com:doncazper/ultimate-ai-agent.git"
    )
    base_sha, branch_binding_ref = executor._preflight(SHA)
    assert base_sha == "b" * 40
    assert branch_binding_ref.startswith(execution.BRANCH_BINDING_PREFIX)


@pytest.mark.parametrize(
    "raw",
    (
        b"not-a-sha\trefs/heads/main\n",
        (b"b" * 40) + b" refs/heads/main\n",
        (b"b" * 40) + b"\trefs/heads/main\n" + (b"c" * 40) + b"\trefs/heads/main\n",
        (b"b" * 40) + b"\trefs/heads/../unsafe\n",
        (b"b" * 40) + b"\trefs/heads/main\x00unsafe\n",
    ),
)
def test_remote_head_parser_rejects_malformed_or_unsafe_advertisements(
    raw: bytes,
) -> None:
    with pytest.raises(
        execution.RemoteHeadAttestationError,
        match="reason-ref:private-ci:remote-advertisement-invalid",
    ):
        execution._parse_advertised_heads(raw)


def test_private_preflight_ignores_stale_cached_remote_tracking_refs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = execution.IsolatedPrivateExecutor(tmp_path)
    requested_git_args: list[tuple[str, ...]] = []

    def fake_git(*args: str, **_kwargs: object) -> str:
        requested_git_args.append(args)
        values = {
            ("rev-parse", "HEAD"): SHA,
            ("status", "--porcelain"): "",
            ("remote", "get-url", "origin"): (
                "git@github.com:doncazper/ultimate-ai-agent.git"
            ),
            ("branch", "--show-current"): "feature",
        }
        return values[args]

    monkeypatch.setattr(executor, "_git", fake_git)
    monkeypatch.setattr(
        executor,
        "_live_advertised_heads",
        lambda: (
            ("b" * 40, "refs/heads/main"),
            ("c" * 40, "refs/heads/other"),
        ),
    )
    with pytest.raises(
        execution.RemoteHeadAttestationError,
        match="reason-ref:private-ci:exact-branch-head-not-advertised",
    ):
        executor._preflight(SHA)

    assert all(args[:2] != ("branch", "-r") for args in requested_git_args)
    assert ("rev-parse", "refs/remotes/origin/main") not in requested_git_args


def test_live_remote_attestation_requires_the_exact_current_branch_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = execution.IsolatedPrivateExecutor(tmp_path)
    main_sha = "b" * 40
    monkeypatch.setattr(
        executor,
        "_live_advertised_heads",
        lambda: (
            (main_sha, "refs/heads/main"),
            (SHA, "refs/heads/feature"),
        ),
    )

    observed_main, branch_binding_ref = executor._attest_live_remote_heads(
        SHA,
        branch_ref="refs/heads/feature",
    )
    assert observed_main == main_sha
    assert branch_binding_ref == execution._source_branch_binding_ref(
        branch_ref="refs/heads/feature",
        repository_sha=SHA,
        origin_main_sha=main_sha,
    )


def test_live_remote_head_query_fails_closed_when_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = execution.IsolatedPrivateExecutor(tmp_path)

    def unavailable(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise subprocess.TimeoutExpired(("git", "ls-remote"), 20)

    monkeypatch.setattr(execution.subprocess, "run", unavailable)

    with pytest.raises(
        execution.RemoteHeadAttestationError,
        match="reason-ref:private-ci:remote-attestation-unavailable",
    ):
        executor._live_advertised_heads()


def _run_git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return completed.stdout.strip()


def _local_remote_branch_fixture(tmp_path: Path) -> tuple[Path, Path, str, str]:
    remote = tmp_path / "remote.git"
    worktree = tmp_path / "source"
    remote.mkdir()
    _run_git(remote, "init", "--bare")
    worktree.mkdir()
    _run_git(worktree, "init", "-b", "main")
    _run_git(worktree, "config", "user.name", "CI Fixture")
    _run_git(worktree, "config", "user.email", "ci-fixture@invalid.example")
    (worktree / "tracked.txt").write_text("main\n", encoding="utf-8")
    _run_git(worktree, "add", "tracked.txt")
    _run_git(worktree, "commit", "-m", "main fixture")
    main_sha = _run_git(worktree, "rev-parse", "HEAD")
    _run_git(worktree, "remote", "add", "origin", str(remote))
    _run_git(worktree, "push", "-u", "origin", "main")
    _run_git(worktree, "switch", "-c", "codex/attestation-test")
    (worktree / "tracked.txt").write_text("feature\n", encoding="utf-8")
    _run_git(worktree, "add", "tracked.txt")
    _run_git(worktree, "commit", "-m", "feature fixture")
    feature_sha = _run_git(worktree, "rev-parse", "HEAD")
    _run_git(worktree, "push", "-u", "origin", "codex/attestation-test")
    return remote, worktree, main_sha, feature_sha


def test_real_git_remote_attestation_binds_exact_branch_and_main(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    remote, worktree, main_sha, feature_sha = _local_remote_branch_fixture(tmp_path)
    monkeypatch.setattr(execution, "ALLOWED_ORIGIN_URLS", frozenset({str(remote)}))

    base_sha, branch_binding_ref = execution.IsolatedPrivateExecutor(
        worktree
    )._preflight(feature_sha)

    assert base_sha == main_sha
    assert branch_binding_ref == execution._source_branch_binding_ref(
        branch_ref="refs/heads/codex/attestation-test",
        repository_sha=feature_sha,
        origin_main_sha=main_sha,
    )


def test_real_git_remote_descendant_does_not_attest_local_ancestor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    remote, worktree, main_sha, _feature_sha = _local_remote_branch_fixture(tmp_path)
    monkeypatch.setattr(execution, "ALLOWED_ORIGIN_URLS", frozenset({str(remote)}))
    _run_git(worktree, "reset", "--hard", main_sha)

    with pytest.raises(
        execution.RemoteHeadAttestationError,
        match="reason-ref:private-ci:exact-branch-head-not-advertised",
    ):
        execution.IsolatedPrivateExecutor(worktree)._preflight(main_sha)


def test_real_git_remote_unavailable_and_detached_states_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    remote, worktree, _main_sha, feature_sha = _local_remote_branch_fixture(tmp_path)
    monkeypatch.setattr(execution, "ALLOWED_ORIGIN_URLS", frozenset({str(remote)}))
    _run_git(worktree, "checkout", "--detach", feature_sha)
    with pytest.raises(
        execution.RemoteHeadAttestationError,
        match="reason-ref:private-ci:current-branch-required",
    ):
        execution.IsolatedPrivateExecutor(worktree)._preflight(feature_sha)

    _run_git(worktree, "switch", "codex/attestation-test")
    remote.rename(tmp_path / "remote-unavailable.git")
    with pytest.raises(
        execution.RemoteHeadAttestationError,
        match="reason-ref:private-ci:remote-attestation-unavailable",
    ):
        execution.IsolatedPrivateExecutor(worktree)._preflight(feature_sha)


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
    assert '("git", "ls-remote", "--heads", "origin")' in source
    assert 'self._git("rev-parse", "refs/remotes/origin/main")' not in source
    assert 'self._git("branch", "-r", "--contains"' not in source
    assert "PRIVATE_BASE_REF" in source
    assert '("git", "remote", "remove", "origin")' in source
    assert '"worktree", "add"' not in source


def test_private_dependency_setup_is_frozen_and_matches_github_policy() -> None:
    commands = execution._dependency_setup_commands()
    serialized = "\n".join(" ".join(command) for command in commands)

    assert f"uv=={execution.UV_VERSION}" in serialized
    assert "uv sync --frozen --extra dev --python python3.12" in serialized
    assert "--upgrade pip" not in serialized
    assert "pip install -e" not in serialized


@pytest.mark.skipif(os.name != "posix", reason="process-group proof is POSIX-specific")
def test_safe_subprocess_cleans_residual_child_after_success(tmp_path: Path) -> None:
    pid_path = tmp_path / "child.pid"
    parent = (
        "import pathlib,subprocess,sys;"
        "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);"
        "pathlib.Path(sys.argv[1]).write_text(str(child.pid),encoding='ascii')"
    )

    returncode, _duration_ms, _result_ref = execution._safe_subprocess(
        (sys.executable, "-c", parent, str(pid_path)),
        cwd=tmp_path,
        timeout=10,
    )

    assert returncode == 0
    child_pid = int(pid_path.read_text(encoding="ascii"))
    child_alive = True
    deadline = time.monotonic() + 3
    try:
        while time.monotonic() < deadline:
            try:
                os.kill(child_pid, 0)
            except ProcessLookupError:
                child_alive = False
                break
            time.sleep(0.05)
    finally:
        if child_alive:
            try:
                os.kill(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                child_alive = False
    assert child_alive is False


@pytest.mark.skipif(os.name != "posix", reason="signal proof is POSIX-specific")
@pytest.mark.parametrize("signal_number", (signal.SIGINT, signal.SIGTERM, signal.SIGHUP))
def test_safe_subprocess_real_signal_reaps_descendants(
    tmp_path: Path,
    signal_number: signal.Signals,
) -> None:
    descendant_pid_path = tmp_path / "descendant.pid"
    result_path = tmp_path / "result.txt"
    helper = (
        "import pathlib,sys;"
        "from scripts.verification.ci_fallback_execution import _safe_subprocess;"
        "child=(\"import pathlib,subprocess,sys,time;\""
        "+\"p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);\""
        "+\"pathlib.Path(sys.argv[1]).write_text(str(p.pid),encoding='ascii');\""
        "+\"time.sleep(60)\");"
        "rc,_,_=_safe_subprocess((sys.executable,'-c',child,sys.argv[1]),"
        "cwd=pathlib.Path(sys.argv[3]),timeout=60);"
        "pathlib.Path(sys.argv[2]).write_text(str(rc),encoding='ascii')"
    )
    process = subprocess.Popen(
        (
            sys.executable,
            "-c",
            helper,
            str(descendant_pid_path),
            str(result_path),
            str(tmp_path),
        ),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 10
    try:
        while not descendant_pid_path.exists():
            if process.poll() is not None:
                pytest.fail("signal helper exited before starting its descendant")
            if time.monotonic() >= deadline:
                pytest.fail("signal helper did not start within the bound")
            time.sleep(0.02)
        os.kill(process.pid, signal_number)
        assert process.wait(timeout=15) == 0
        assert result_path.read_text(encoding="ascii") == "130"
        descendant_pid = int(descendant_pid_path.read_text(encoding="ascii"))
        deadline = time.monotonic() + 3
        while True:
            try:
                os.kill(descendant_pid, 0)
            except ProcessLookupError:
                break
            if time.monotonic() >= deadline:
                pytest.fail("signalled process descendant was not reaped")
            time.sleep(0.05)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


@pytest.mark.parametrize(
    ("unit_ref", "command"),
    (
        (
            "pytest-shards",
            CommandSpec(
                "command:pytest.sharded-suite",
                (".venv/bin/python", "scripts/verification/run_pytest_shards.py"),
                (),
                "test",
                10,
            ),
        ),
        (
            "risk-frontend-typecheck",
            CommandSpec(
                "command:frontend.typecheck",
                ("npm", "run", "typecheck"),
                (),
                "frontend",
                10,
            ),
        ),
        (
            "risk-final-diff-audit",
            CommandSpec("command:test", ("true",), (), "audit", 10),
        ),
        (
            "diagnostic-pytest-shard-0",
            CommandSpec(
                "command:test",
                (".venv/bin/python", "scripts/verification/run_pytest_shards.py"),
                (),
                "test",
                10,
            ),
        ),
    ),
)
def test_private_execution_rejects_complete_and_non_command_units(
    unit_ref: str,
    command: CommandSpec,
) -> None:
    with pytest.raises(ValueError, match="authoritative GitHub"):
        execution.IsolatedPrivateExecutor._assert_private_command_allowed(
            unit_ref, command
        )


def test_private_execution_accepts_only_exact_shard_reproduction() -> None:
    command = execution.command_registry()["command:pytest.shard-3-reproduce"]
    execution.IsolatedPrivateExecutor._assert_private_command_allowed(
        "diagnostic-pytest-shard-3", command
    )


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
