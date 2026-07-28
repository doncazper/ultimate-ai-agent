from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.verification import pytest_shard_processes as shard_processes
from scripts.verification import run_ci_lane as runner
from scripts.verification.ci_command_manifest import (
    CI_JOB_GRAPH,
    DECLARED_RUNNER_PROFILE_ENV,
    CommandSpec,
    LaneSpec,
    build_plan,
)
from scripts.verification.pytest_shard_artifacts import safe_test_ref
from scripts.verification.pytest_shard_plan import CANONICAL_PYTEST_SHARD_COUNT
from scripts.verification.verification_contracts import (
    VerificationTerminalStatus,
    verification_receipt_fingerprint,
)
from scripts.verification.verification_execution_identity import (
    VerificationExecutionFence,
    VerificationExecutionFenceDisposition,
    build_verification_execution_identity,
)
from scripts.verification.verification_github_transport import (
    build_github_job_output_envelope,
    decode_github_job_output,
    encode_github_job_output,
)
from scripts.verification.verification_receipt_store import VerificationReceiptStore


ROOT = Path(__file__).resolve().parents[1]
SHA = subprocess.run(
    ("git", "rev-parse", "HEAD"),
    cwd=ROOT,
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()


class _FakeFullSuiteLock:
    def __init__(self, **_kwargs: object) -> None:
        pass

    def __enter__(self) -> _FakeFullSuiteLock:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def ensure_start_available(self) -> None:
        pass

    def record_start(self) -> None:
        pass


@pytest.fixture(autouse=True)
def _isolate_matrix_loopback_prestart_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "assert_matrix_loopback_test_resource_available",
        lambda: None,
    )
    monkeypatch.setattr(
        runner,
        "validate_lane_environment",
        lambda *_args, **_kwargs: ("preflight-ref:test-ready",),
    )


def _write_pytest_performance_report(
    path: Path,
    *,
    failed_index: int | None = None,
    timed_out: bool = False,
    plan_ref: str = "pytest-shard-plan-ref:sha256:" + "a" * 64,
    run_status: str | None = None,
    failed_test_refs: tuple[str, ...] = (),
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "uaa_pytest_performance_report.v1",
                "plan_fingerprint_ref": plan_ref,
                "run_status": run_status
                or (
                    "timeout"
                    if timed_out
                    else "failed"
                    if failed_index is not None
                    else "green"
                ),
                "shards": [
                    {
                        "shard_index": index,
                        "return_code": 1 if index == failed_index else 0,
                        "timed_out": timed_out and index == failed_index,
                        "failed_test_refs": (
                            list(failed_test_refs) if index == failed_index else []
                        ),
                    }
                    for index in range(CANONICAL_PYTEST_SHARD_COUNT)
                ],
            }
        ),
        encoding="utf-8",
    )


def test_safe_env_preserves_valid_declared_runner_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    declared_profile = "github-hosted-macos-15-python-3.12.10-node-22.23.1"
    monkeypatch.setenv(DECLARED_RUNNER_PROFILE_ENV, declared_profile)

    env = runner._safe_env(
        CommandSpec("command:test", ("true",), (), "test", 10),
        tmp_path,
        base_sha="a" * 40,
    )

    assert env[DECLARED_RUNNER_PROFILE_ENV] == declared_profile


def test_safe_env_rejects_invalid_declared_runner_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(DECLARED_RUNNER_PROFILE_ENV, "unsafe profile\nvalue")

    with pytest.raises(ValueError, match="declared runner profile"):
        runner._safe_env(
            CommandSpec("command:test", ("true",), (), "test", 10),
            tmp_path,
        )


def test_safe_env_rejects_command_override_of_declared_runner_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        DECLARED_RUNNER_PROFILE_ENV,
        "github-hosted-macos-15-python-3.12.10-node-22.23.1",
    )
    command = CommandSpec(
        "command:test",
        ("true",),
        ((DECLARED_RUNNER_PROFILE_ENV, "github-hosted-macos-15-overridden"),),
        "test",
        10,
    )

    with pytest.raises(ValueError, match="cannot override declared runner profile"):
        runner._safe_env(command, tmp_path)


def _patch_lane(
    monkeypatch: pytest.MonkeyPatch,
    commands: tuple[CommandSpec, ...],
    *,
    optional: tuple[str, ...] = (),
    lane_ref: str = "test-lane",
) -> None:
    registry = {command.command_ref: command for command in commands}
    lane = LaneSpec(
        lane_ref,
        "Test Lane",
        tuple(registry),
        optional_command_refs=optional,
    )
    plan = build_plan(
        ROOT,
        SHA,
        lane_refs=("docs",),
        verify_repository_state=False,
    )
    monkeypatch.setattr(runner, "_git_head", lambda _repo: SHA)
    monkeypatch.setattr(runner, "command_registry", lambda: registry)
    monkeypatch.setattr(runner, "lane_registry", lambda: {lane_ref: lane})
    monkeypatch.setattr(runner, "build_plan", lambda *_args, **_kwargs: plan)


def test_lane_runner_emits_content_free_hash_bound_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pass",
        (sys.executable, "-c", "print('private-output-that-must-not-persist')"),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,))

    receipt_file = tmp_path / "temp" / "receipts" / "lane.json"
    receipt = runner.run_lane(
        "test-lane",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
        receipt_file=receipt_file,
    )

    assert receipt["status"] == "pass"
    assert "execution_surface_ref" not in receipt
    assert receipt["github_gate_satisfied"] is False
    assert receipt["merge_gate_satisfied"] is False
    serialized = json.dumps(receipt, sort_keys=True)
    assert "private-output-that-must-not-persist" not in serialized
    assert str(tmp_path) not in serialized
    assert receipt["command_results"][0]["output_byte_count"] > 0
    assert len(receipt["command_results"][0]["output_digest"]) == 64
    assert (
        json.loads(receipt_file.read_text(encoding="utf-8"))["receipt_ref"]
        == receipt["receipt_ref"]
    )


def test_lane_runner_binds_exact_comparison_base_to_plan_command_and_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_sha = "b" * 40
    command = CommandSpec(
        "command:test.base-binding",
        (
            sys.executable,
            "-c",
            (
                "import os,sys; "
                "raise SystemExit(0 if os.environ.get('UAA_VERIFICATION_BASE_SHA') "
                "== sys.argv[1] else 2)"
            ),
            "{base_sha}",
        ),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,))
    original_build_plan = runner.build_plan
    observed_bases: list[str | None] = []

    def capture_build_plan(*args: object, **kwargs: object):
        observed_bases.append(kwargs.get("base_sha"))
        return original_build_plan(*args, **kwargs)

    monkeypatch.setattr(runner, "build_plan", capture_build_plan)

    receipt = runner.run_lane(
        "test-lane",
        repository_sha=SHA,
        base_sha=base_sha,
        temp_root=tmp_path / "temp",
    )

    assert receipt["status"] == "pass"
    assert observed_bases == [base_sha]


def test_typed_lane_evidence_is_content_bound_and_partial_run_is_blocked() -> None:
    plan = build_plan(ROOT, SHA, verify_repository_state=False)
    command_results = [
        {
            "command_ref": command_ref,
            "status": "pass",
            "duration_ms": 1,
            "output_byte_count": 0,
            "output_digest": "a" * 64,
            "result_ref": (
                "result-ref:ci:" + hashlib.sha256(str(index).encode()).hexdigest()
            ),
        }
        for index, command_ref in enumerate(
            ("command:ci.ruff", "command:ci.github-hosted-contract"), start=1
        )
    ]
    legacy_receipt = {
        "receipt_ref": f"receipt-ref:ci-lane:{'d' * 64}",
        "status": "pass",
        "started_at": "2026-07-15T00:00:00Z",
        "completed_at": "2026-07-15T00:00:01Z",
        "duration_ms": 1_000,
    }

    receipt, run = runner._build_typed_lane_evidence(
        lane_ref="ci-lint",
        legacy_receipt=legacy_receipt,
        full_plan=plan,
        results=command_results,
        execution_surface_ref="surface-ref:github",
        pytest_collection=None,
        pre_execution_identity_ref=runner.build_verification_execution_identity(
            plan,
            next(unit for unit in CI_JOB_GRAPH if unit.lane_ref == "ci-lint"),
            execution_surface_ref="surface-ref:github",
        ).identity_ref,
    )

    assert receipt.status is VerificationTerminalStatus.PASSED
    assert receipt.schema_version == "uaa_verification_receipt.v4"
    assert receipt.execution_identity_ref is not None
    assert receipt.observed_platform_fingerprint is not None
    assert receipt.receipt_ref.endswith(receipt.receipt_fingerprint or "missing")
    with pytest.raises(ValueError, match="fingerprint"):
        replace(receipt, observed_platform_fingerprint="c" * 64).validate()
    with pytest.raises(ValueError, match="requires observed platform proof"):
        replace(receipt, observed_platform_fingerprint=None).validate()
    assert run.status is VerificationTerminalStatus.BLOCKED
    assert run.schema_version == "uaa_verification_run.v3"
    assert run.required_unit_refs == plan.selected_unit_refs
    assert receipt.unit_ref not in run.missing_unit_refs
    assert run.receipt_refs == (receipt.receipt_ref,)
    serialized = json.dumps(
        {"receipt": asdict(receipt), "run": asdict(run)}, sort_keys=True
    )
    assert "/Users/" not in serialized
    assert "raw_output" not in serialized


def test_lane_runner_publishes_typed_v4_proof_to_immutable_store(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = build_plan(ROOT, SHA, verify_repository_state=False)
    plan_build_events: list[str] = []

    def fake_build_plan(*_args: object, **_kwargs: object):
        plan_build_events.append("plan")
        return plan

    monkeypatch.setattr(runner, "build_plan", fake_build_plan)

    def fake_run_command(
        command: CommandSpec,
        **_kwargs: object,
    ) -> dict[str, object]:
        assert len(plan_build_events) == 2
        return {
            "command_ref": command.command_ref,
            "category": command.category,
            "status": "pass",
            "started_at": "2026-07-15T00:00:00Z",
            "completed_at": "2026-07-15T00:00:01Z",
            "duration_ms": 1,
            "output_byte_count": 0,
            "output_digest": "a" * 64,
            "result_ref": (
                "result-ref:ci:"
                + hashlib.sha256(command.command_ref.encode()).hexdigest()
            ),
            "redaction_status": "content_free_output_metadata_only",
        }

    monkeypatch.setattr(runner, "_run_command", fake_run_command)
    store_root = tmp_path / "proof-store"
    summary_file = tmp_path / "summary.md"

    receipt = runner.run_lane(
        "ci-lint",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
        verification_store_root=store_root,
        summary_file=summary_file,
    )

    store = VerificationReceiptStore(store_root)
    receipt_digests = tuple(
        path.stem for path in (store_root / "receipts").glob("*.json")
    )
    run_digests = tuple(path.stem for path in (store_root / "runs").glob("*.json"))
    assert receipt["status"] == "pass"
    assert len(receipt_digests) == len(run_digests) == 1
    stored_receipt = store.get_receipt(receipt_digests[0])
    assert stored_receipt.schema_version == "uaa_verification_receipt.v4"
    assert stored_receipt.observed_platform_fingerprint is not None
    assert store.get_run_manifest(run_digests[0]).schema_version == (
        "uaa_verification_run.v3"
    )
    assert "Stored typed proof: verification-artifact:receipt:" in (
        summary_file.read_text(encoding="utf-8")
    )
    assert plan_build_events == ["plan", "plan", "plan"]


def test_typescript_terminal_status_cannot_change_prestart_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = build_plan(ROOT, SHA, verify_repository_state=False)
    unit = next(
        unit for unit in CI_JOB_GRAPH if unit.lane_ref == "ci-control-center-frontend"
    )
    declared = SimpleNamespace(
        declared_project_fingerprint=plan.typescript_project_fingerprint
    )
    runtime = SimpleNamespace(
        resolved_runtime_fingerprint="e" * 64,
        typescript_version="7.0.2",
    )
    monkeypatch.setattr(
        runner, "build_declared_typescript_binding", lambda _root: declared
    )
    monkeypatch.setattr(
        runner,
        "resolve_typescript_runtime_binding",
        lambda _root, _declared: runtime,
    )
    pre_identity_ref = runner.build_verification_execution_identity(
        plan,
        unit,
        execution_surface_ref="surface-ref:github",
        typescript_runtime_fingerprint=runtime.resolved_runtime_fingerprint,
        typescript_version_ref="typescript-version:7.0.2",
    ).identity_ref

    def build(status: str):
        result_ref = "result-ref:ci:" + hashlib.sha256(status.encode()).hexdigest()
        return runner._build_typed_lane_evidence(
            lane_ref="ci-control-center-frontend",
            legacy_receipt={
                "receipt_ref": f"receipt-ref:ci-lane:{'f' * 64}",
                "status": "pass" if status == "pass" else "fail",
                "started_at": "2026-07-15T00:00:00Z",
                "completed_at": "2026-07-15T00:00:01Z",
                "duration_ms": 1_000,
            },
            full_plan=plan,
            results=(
                [
                    {
                        "command_ref": "command:frontend.check",
                        "status": status,
                        "duration_ms": 1,
                        "output_byte_count": 0,
                        "output_digest": "a" * 64,
                        "result_ref": result_ref,
                    }
                ]
            ),
            execution_surface_ref="surface-ref:github",
            pytest_collection=None,
            frontend_collection={
                "collection_digest_ref": "sha256:" + "d" * 64,
                "collected_test_count": 3,
                "result_status": "passed",
            },
            pre_typescript_runtime=runtime,
            pre_execution_identity_ref=pre_identity_ref,
        )[0]

    passed = build("pass")
    failed = build("fail")

    assert passed.execution_identity_ref == failed.execution_identity_ref
    assert passed.typescript_binding_posture == "resolved"
    assert failed.typescript_binding_posture == "resolved"
    assert failed.status is VerificationTerminalStatus.FAILED
    with pytest.raises(ValueError, match="pre-start runtime binding"):
        replace(
            failed,
            typescript_binding_posture="unavailable",
            typescript_project_fingerprint=None,
            typescript_runtime_fingerprint=None,
            typescript_version_ref=None,
        ).validate()


def test_direct_frontend_lane_without_durable_fence_fails_before_plan_or_spawn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runner, "_git_head", lambda _repo: SHA)
    monkeypatch.setattr(
        runner,
        "build_plan",
        lambda *_args, **_kwargs: pytest.fail(
            "unfenced frontend verification must fail before planning"
        ),
    )
    monkeypatch.setattr(
        runner,
        "_run_command",
        lambda *_args, **_kwargs: pytest.fail(
            "unfenced frontend verification must not spawn"
        ),
    )

    with pytest.raises(ValueError, match="requires a durable execution fence"):
        runner.run_lane(
            "ci-control-center-frontend",
            repository_sha=SHA,
            temp_root=tmp_path / "temp",
        )


def test_frontend_release_receipt_reuses_exact_dependency_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = build_plan(ROOT, SHA, verify_repository_state=False)
    control_unit = next(
        unit for unit in CI_JOB_GRAPH if unit.lane_ref == "ci-control-center-frontend"
    )
    release_unit = next(
        unit for unit in CI_JOB_GRAPH if unit.lane_ref == "frontend"
    )
    declared = SimpleNamespace(
        declared_project_fingerprint=plan.typescript_project_fingerprint
    )
    runtime = SimpleNamespace(
        resolved_runtime_fingerprint="e" * 64,
        typescript_version="7.0.2",
    )
    monkeypatch.setattr(
        runner, "build_declared_typescript_binding", lambda _root: declared
    )
    monkeypatch.setattr(
        runner,
        "resolve_typescript_runtime_binding",
        lambda _root, _declared: runtime,
    )
    control_identity = runner.build_verification_execution_identity(
        plan,
        control_unit,
        execution_surface_ref="surface-ref:github",
        typescript_runtime_fingerprint=runtime.resolved_runtime_fingerprint,
        typescript_version_ref="typescript-version:7.0.2",
    ).identity_ref
    control_result_ref = "result-ref:ci:" + hashlib.sha256(b"frontend").hexdigest()
    control_receipt = runner._build_typed_lane_evidence(
        lane_ref="ci-control-center-frontend",
        legacy_receipt={
            "receipt_ref": f"receipt-ref:ci-lane:{'a' * 64}",
            "status": "pass",
            "started_at": "2026-07-15T00:00:00Z",
            "completed_at": "2026-07-15T00:00:01Z",
            "duration_ms": 1_000,
        },
        full_plan=plan,
        results=[
            {
                "command_ref": "command:frontend.check",
                "status": "pass",
                "duration_ms": 1_000,
                "output_byte_count": 0,
                "output_digest": "a" * 64,
                "result_ref": control_result_ref,
            }
        ],
        execution_surface_ref="surface-ref:github",
        pytest_collection=None,
        frontend_collection={
            "collection_digest_ref": "sha256:" + "d" * 64,
            "collected_test_count": 3,
            "result_status": "passed",
        },
        pre_typescript_runtime=runtime,
        pre_execution_identity_ref=control_identity,
    )[0]
    release_identity = runner.build_verification_execution_identity(
        plan,
        release_unit,
        execution_surface_ref="surface-ref:github",
        typescript_runtime_fingerprint=runtime.resolved_runtime_fingerprint,
        typescript_version_ref="typescript-version:7.0.2",
    ).identity_ref
    executed_results = [
        {
            "command_ref": command_ref,
            "status": "pass",
            "duration_ms": 500,
            "output_byte_count": 0,
            "output_digest": hashlib.sha256(command_ref.encode()).hexdigest(),
            "result_ref": (
                "result-ref:ci:" + hashlib.sha256(command_ref.encode()).hexdigest()
            ),
        }
        for command_ref in (
            "command:frontend.safety",
            "command:frontend.browser-smoke",
        )
    ]
    release_receipt = runner._build_typed_lane_evidence(
        lane_ref="frontend",
        legacy_receipt={
            "receipt_ref": f"receipt-ref:ci-lane:{'b' * 64}",
            "status": "pass",
            "started_at": "2026-07-15T00:00:02Z",
            "completed_at": "2026-07-15T00:00:03Z",
            "duration_ms": 1_000,
        },
        full_plan=plan,
        results=[
            {
                "command_ref": "command:frontend.check",
                "status": "reused_exact_receipt",
                "duration_ms": 0,
                "result_ref": control_receipt.receipt_ref,
            },
            *executed_results,
        ],
        execution_surface_ref="surface-ref:github",
        pytest_collection=None,
        reused_receipts_by_command={
            "command:frontend.check": control_receipt,
        },
        pre_execution_identity_ref=release_identity,
    )[0]

    assert release_receipt.status is VerificationTerminalStatus.PASSED
    assert release_receipt.reused_command_receipt_bindings == (
        ("command:frontend.check", control_receipt.receipt_ref),
    )
    assert release_receipt.observed_test_collection_fingerprint == "d" * 64
    assert release_receipt.typescript_runtime_fingerprint == "e" * 64


def test_frontend_release_lane_consumes_the_exact_dependency_envelope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = build_plan(ROOT, SHA, verify_repository_state=False)
    control_unit = next(
        unit for unit in CI_JOB_GRAPH if unit.lane_ref == "ci-control-center-frontend"
    )
    runtime = SimpleNamespace(
        resolved_runtime_fingerprint="e" * 64,
        typescript_version="7.0.2",
    )
    monkeypatch.setattr(
        runner,
        "build_declared_typescript_binding",
        lambda _root: SimpleNamespace(
            declared_project_fingerprint=plan.typescript_project_fingerprint
        ),
    )
    monkeypatch.setattr(
        runner,
        "resolve_typescript_runtime_binding",
        lambda _root, _declared: runtime,
    )
    control_identity = runner.build_verification_execution_identity(
        plan,
        control_unit,
        execution_surface_ref="surface-ref:github",
        typescript_runtime_fingerprint=runtime.resolved_runtime_fingerprint,
        typescript_version_ref="typescript-version:7.0.2",
    ).identity_ref
    control_receipt = runner._build_typed_lane_evidence(
        lane_ref="ci-control-center-frontend",
        legacy_receipt={
            "receipt_ref": f"receipt-ref:ci-lane:{'a' * 64}",
            "status": "pass",
            "started_at": "2026-07-15T00:00:00Z",
            "completed_at": "2026-07-15T00:00:01Z",
            "duration_ms": 1_000,
        },
        full_plan=plan,
        results=[
            {
                "command_ref": "command:frontend.check",
                "status": "pass",
                "duration_ms": 1_000,
                "output_byte_count": 0,
                "output_digest": "a" * 64,
                "result_ref": (
                    "result-ref:ci:" + hashlib.sha256(b"frontend").hexdigest()
                ),
            }
        ],
        execution_surface_ref="surface-ref:github",
        pytest_collection=None,
        frontend_collection={
            "collection_digest_ref": "sha256:" + "d" * 64,
            "collected_test_count": 3,
            "result_status": "passed",
        },
        pre_typescript_runtime=runtime,
        pre_execution_identity_ref=control_identity,
    )[0]
    encoded = encode_github_job_output(
        build_github_job_output_envelope(plan, control_receipt)
    )
    monkeypatch.setattr(runner, "build_plan", lambda *_args, **_kwargs: plan)
    monkeypatch.setattr(
        runner,
        "resolve_typescript_runtime_binding",
        lambda *_args, **_kwargs: pytest.fail(
            "exact dependency reuse must not probe the TypeScript runtime"
        ),
    )

    def fake_run_command(
        command: CommandSpec,
        **_kwargs: object,
    ) -> dict[str, object]:
        return {
            "command_ref": command.command_ref,
            "category": command.category,
            "status": "pass",
            "started_at": "2026-07-15T00:00:02Z",
            "completed_at": "2026-07-15T00:00:03Z",
            "duration_ms": 1,
            "output_byte_count": 0,
            "output_digest": hashlib.sha256(command.command_ref.encode()).hexdigest(),
            "result_ref": (
                "result-ref:ci:"
                + hashlib.sha256(command.command_ref.encode()).hexdigest()
            ),
            "redaction_status": "content_free_output_metadata_only",
        }

    monkeypatch.setattr(runner, "_run_command", fake_run_command)
    receipt = runner.run_lane(
        "frontend",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
        dependency_envelopes=(encoded,),
    )

    assert receipt["status"] == "pass"
    assert receipt["command_results"][0] == {
        "command_ref": "command:frontend.check",
        "category": "frontend",
        "status": "reused_exact_receipt",
        "duration_ms": 0,
        "result_ref": control_receipt.receipt_ref,
        "redaction_status": "content_free_output_metadata_only",
    }

    tampered = replace(
        control_receipt,
        proof_equivalence_ref="proof-equivalence-ref:wrong-source-unit",
        receipt_ref=f"receipt:verification:{'0' * 64}",
        receipt_fingerprint="0" * 64,
    )
    tampered_fingerprint = verification_receipt_fingerprint(tampered)
    tampered = replace(
        tampered,
        receipt_ref=f"receipt:verification:{tampered_fingerprint}",
        receipt_fingerprint=tampered_fingerprint,
    )
    tampered_envelope = encode_github_job_output(
        build_github_job_output_envelope(plan, tampered)
    )
    with pytest.raises(ValueError, match="exact plan"):
        runner.run_lane(
            "frontend",
            repository_sha=SHA,
            temp_root=tmp_path / "tampered-temp",
            dependency_envelopes=(tampered_envelope,),
        )


def test_failed_multicommand_lane_emits_exact_executed_prefix() -> None:
    plan = build_plan(ROOT, SHA, verify_repository_state=False)
    unit = next(unit for unit in CI_JOB_GRAPH if unit.lane_ref == "ci-lint")
    result_ref = "result-ref:ci:" + hashlib.sha256(b"failed-ruff").hexdigest()
    pre_identity_ref = runner.build_verification_execution_identity(
        plan,
        unit,
        execution_surface_ref="surface-ref:github",
    ).identity_ref

    receipt, run = runner._build_typed_lane_evidence(
        lane_ref="ci-lint",
        legacy_receipt={
            "receipt_ref": f"receipt-ref:ci-lane:{'d' * 64}",
            "status": "fail",
            "started_at": "2026-07-15T00:00:00Z",
            "completed_at": "2026-07-15T00:00:01Z",
            "duration_ms": 1_000,
        },
        full_plan=plan,
        results=[
            {
                "command_ref": "command:ci.ruff",
                "status": "fail",
                "duration_ms": 1,
                "output_byte_count": 0,
                "output_digest": "a" * 64,
                "result_ref": result_ref,
            }
        ],
        execution_surface_ref="surface-ref:github",
        pytest_collection=None,
        pre_execution_identity_ref=pre_identity_ref,
    )

    assert receipt.schema_version == "uaa_verification_receipt.v4"
    assert receipt.status is VerificationTerminalStatus.FAILED
    assert receipt.command_refs == ("command:ci.ruff",)
    assert receipt.executed_command_result_bindings == (
        ("command:ci.ruff", result_ref),
    )
    assert run.status is VerificationTerminalStatus.FAILED


def test_terminal_dependency_receipts_are_canonicalized_by_declared_dag_order() -> None:
    required = ("unit-a", "unit-b", "unit-c")
    receipts = {
        "unit-c": object(),
        "unit-a": object(),
        "unit-b": object(),
    }

    canonical = runner._canonicalize_terminal_dependency_receipts(
        required,
        receipts,
    )

    assert tuple(canonical) == required
    assert canonical["unit-a"] is receipts["unit-a"]
    assert canonical["unit-b"] is receipts["unit-b"]
    assert canonical["unit-c"] is receipts["unit-c"]


@pytest.mark.parametrize(
    "receipts",
    (
        {"unit-a": object(), "unit-b": object()},
        {
            "unit-a": object(),
            "unit-b": object(),
            "unit-c": object(),
            "unit-extra": object(),
        },
    ),
)
def test_terminal_dependency_receipts_reject_incomplete_or_extra_units(
    receipts: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match="terminal dependency evidence is incomplete"):
        runner._canonicalize_terminal_dependency_receipts(
            ("unit-a", "unit-b", "unit-c"),
            receipts,
        )


def test_not_affected_visual_scope_is_bound_and_never_claimed_executed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = build_plan(
        ROOT,
        SHA,
        frontend_visual_scope="not_affected",
        verify_repository_state=False,
    )
    observed_scopes: list[str | None] = []

    def fake_build_plan(*_args: object, **kwargs: object):
        observed_scopes.append(kwargs.get("frontend_visual_scope"))
        return plan

    def fake_run_command(
        command: CommandSpec,
        **_kwargs: object,
    ) -> dict[str, object]:
        return {
            "command_ref": command.command_ref,
            "category": command.category,
            "status": "pass",
            "started_at": "2026-07-15T00:00:00Z",
            "completed_at": "2026-07-15T00:00:01Z",
            "duration_ms": 1,
            "output_byte_count": 0,
            "output_digest": "a" * 64,
            "result_ref": (
                "result-ref:ci:"
                + hashlib.sha256(command.command_ref.encode()).hexdigest()
            ),
            "redaction_status": "content_free_output_metadata_only",
        }

    monkeypatch.setattr(runner, "build_plan", fake_build_plan)
    monkeypatch.setattr(runner, "_run_command", fake_run_command)
    store_root = tmp_path / "proof-store"

    runner.run_lane(
        "visual-regression",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
        visual_scope="not_affected",
        verification_store_root=store_root,
    )

    store = VerificationReceiptStore(store_root)
    receipt_digest = next((store_root / "receipts").glob("*.json")).stem
    typed = store.get_receipt(receipt_digest)
    assert observed_scopes == ["not_affected", "not_affected", "not_affected"]
    assert typed.schema_version == "uaa_verification_receipt.v4"
    assert typed.status is VerificationTerminalStatus.BLOCKED
    assert tuple(
        command_ref for command_ref, _result_ref in typed.executed_command_result_bindings
    ) == ("command:frontend.visual-regression-contract",)
    assert tuple(
        (command_ref, reason_ref)
        for command_ref, _result_ref, reason_ref in (
            typed.nonexecuted_command_result_bindings
        )
    ) == (
        (
            "command:frontend.visual-regression",
            "reason-ref:visual-regression:not-affected",
        ),
    )


def test_typed_frontend_release_rejects_synthetic_dependency_reuse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = build_plan(ROOT, SHA, verify_repository_state=False)
    monkeypatch.setattr(runner, "build_plan", lambda *_args, **_kwargs: plan)
    monkeypatch.setattr(
        runner,
        "resolve_typescript_runtime_binding",
        lambda *_args, **_kwargs: pytest.fail(
            "synthetic TypeScript dependency reuse must not probe runtime"
        ),
    )

    store_root = tmp_path / "proof-store"
    with pytest.raises(
        ValueError,
        match="synthetic dependency satisfaction is forbidden",
    ):
        runner.run_lane(
            "frontend",
            repository_sha=SHA,
            temp_root=tmp_path / "temp",
            verification_store_root=store_root,
        )
    assert not store_root.exists()


def test_preflight_failure_blocks_before_attempt_or_fence_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = build_plan(
        ROOT,
        SHA,
        lane_refs=("ci-pytest-shards",),
        verify_repository_state=False,
    )
    monkeypatch.setattr(runner, "_git_head", lambda _repo: SHA)
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(runner, "build_plan", lambda *_args, **_kwargs: plan)

    def block_preflight(*_args: object, **_kwargs: object) -> None:
        raise runner.VerificationEnvironmentPreflightError(
            "reason-ref:verification-preflight:test-blocked"
        )

    monkeypatch.setattr(runner, "validate_lane_environment", block_preflight)
    fence_root = tmp_path / "execution-fence"
    store_root = tmp_path / "proof-store"

    with pytest.raises(
        runner.VerificationEnvironmentPreflightError,
        match="test-blocked",
    ):
        runner.run_lane(
            "ci-pytest-shards",
            repository_sha=SHA,
            temp_root=tmp_path / "temp",
            verification_store_root=store_root,
            verification_execution_fence_root=fence_root,
        )

    assert not fence_root.exists()
    assert not store_root.exists()


def test_typed_plan_mutation_before_popen_blocks_suite_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lane_plan = build_plan(
        ROOT,
        SHA,
        lane_refs=("ci-pytest-shards",),
        verify_repository_state=False,
    )
    full_plan = build_plan(ROOT, SHA, verify_repository_state=False)
    changed_plan = replace(full_plan, platform_fingerprint="c" * 64)
    plans = iter((lane_plan, full_plan, changed_plan))
    monkeypatch.setattr(runner, "build_plan", lambda *_args, **_kwargs: next(plans))
    events: list[str] = []

    class FakeFullSuiteLock:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def ensure_start_available(self) -> None:
            events.append("validated-lock")

        def record_start(self) -> None:
            events.append("recorded-start")

    monkeypatch.setattr(runner, "FullSuiteLock", FakeFullSuiteLock)
    monkeypatch.setattr(runner, "_git_head", lambda _repo: SHA)
    monkeypatch.setattr(
        runner.subprocess,
        "Popen",
        lambda *_args, **_kwargs: events.append("popen"),
    )

    with pytest.raises(ValueError, match="plan changed before command start"):
        runner.run_lane(
            "ci-pytest-shards",
            repository_sha=SHA,
            temp_root=tmp_path / "temp",
            verification_store_root=tmp_path / "proof-store",
            verification_execution_fence_root=tmp_path / "execution-fence",
        )

    assert events == ["validated-lock"]


def test_attempt_ledger_failure_after_spawn_leaves_recovery_fence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lane_plan = build_plan(
        ROOT,
        SHA,
        lane_refs=("ci-pytest-shards",),
        verify_repository_state=False,
    )
    full_plan = build_plan(ROOT, SHA, verify_repository_state=False)
    monkeypatch.setattr(
        runner,
        "build_plan",
        lambda *_args, **kwargs: lane_plan if kwargs.get("lane_refs") else full_plan,
    )
    monkeypatch.setattr(runner, "_git_head", lambda _repo: SHA)
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda _name: object())
    events: list[str] = []

    class FailingFullSuiteLock(_FakeFullSuiteLock):
        def record_start(self) -> None:
            events.append("attempt-record-failed")
            raise RuntimeError("attempt record unavailable")

    def fake_run_command(
        _command: CommandSpec,
        *,
        validate_start=None,
        before_start=None,
        after_spawn=None,
        **_kwargs: object,
    ) -> dict[str, object]:
        assert validate_start is not None
        assert before_start is not None
        assert after_spawn is not None
        validate_start()
        before_start()
        events.append("spawned")
        after_spawn()
        raise AssertionError("attempt record failure must stop command handling")

    monkeypatch.setattr(runner, "FullSuiteLock", FailingFullSuiteLock)
    monkeypatch.setattr(runner, "_run_command", fake_run_command)
    fence_root = tmp_path / "execution-fence"

    with pytest.raises(RuntimeError, match="attempt record unavailable"):
        runner.run_lane(
            "ci-pytest-shards",
            repository_sha=SHA,
            temp_root=tmp_path / "temp",
            verification_store_root=tmp_path / "proof-store",
            verification_execution_fence_root=fence_root,
        )

    assert events == ["spawned", "attempt-record-failed"]
    unit = next(unit for unit in CI_JOB_GRAPH if unit.unit_ref == "pytest-shards")
    identity = build_verification_execution_identity(
        full_plan,
        unit,
        execution_surface_ref="surface-ref:github",
    )
    assert VerificationExecutionFence(fence_root).begin(identity).disposition is (
        VerificationExecutionFenceDisposition.RECOVERY_REQUIRED
    )


def test_run_command_spawn_failure_releases_prestart_reservation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.spawn-failure-rollback",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    events: list[str] = []

    def fail_spawn(*_args: object, **_kwargs: object) -> None:
        events.append("spawn-failed")
        raise RuntimeError("spawn unavailable")

    monkeypatch.setattr(runner, "spawn_owned_process_group", fail_spawn)

    with pytest.raises(RuntimeError, match="spawn unavailable"):
        runner._run_command(
            command,
            repository_sha=SHA,
            temp_root=tmp_path,
            before_start=lambda: events.append("reserved"),
            after_spawn=lambda: events.append("recorded"),
            on_spawn_failure=lambda: events.append("released"),
        )

    assert events == ["reserved", "spawn-failed", "released"]


def test_run_command_cancellation_before_spawn_releases_prestart_reservation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pre-spawn-cancellation",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    events: list[str] = []

    def cancel_after_reservation() -> None:
        events.append("reserved")
        handler = signal.getsignal(signal.SIGTERM)
        assert callable(handler)
        handler(signal.SIGTERM, None)

    monkeypatch.setattr(
        runner,
        "spawn_owned_process_group",
        lambda *_args, **_kwargs: pytest.fail("command must not spawn"),
    )

    result = runner._run_command(
        command,
        repository_sha=SHA,
        temp_root=tmp_path,
        before_start=cancel_after_reservation,
        after_spawn=lambda: events.append("recorded"),
        on_spawn_failure=lambda: events.append("released"),
    )

    assert result["status"] == "cancelled"
    assert events == ["reserved", "released"]


def test_run_command_emits_digest_ref_without_retaining_failure_output(
    tmp_path: Path,
) -> None:
    command = CommandSpec(
        "command:test.retained-failure-output",
        (
            sys.executable,
            "-c",
            "print('local diagnostic only'); raise SystemExit(7)",
        ),
        (),
        "test",
        10,
    )

    result = runner._run_command(
        command,
        repository_sha=SHA,
        temp_root=tmp_path,
        emit_failure_diagnostic_ref=True,
    )

    retained = tmp_path / "uaa_command_failure_output.log"
    assert result["status"] == "fail"
    assert str(result["diagnostic_digest_ref"]).startswith(
        "diagnostic-output-ref:sha256:"
    )
    assert not retained.exists()
    assert not tuple(tmp_path.glob("uaa-ci-transient-*"))


def test_exclusive_typed_lane_publishes_terminal_execution_fence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lane_plan = build_plan(
        ROOT,
        SHA,
        lane_refs=("ci-pytest-shards",),
        verify_repository_state=False,
    )
    full_plan = build_plan(ROOT, SHA, verify_repository_state=False)
    monkeypatch.setattr(
        runner,
        "build_plan",
        lambda *_args, **kwargs: lane_plan if kwargs.get("lane_refs") else full_plan,
    )
    monkeypatch.setattr(runner, "_git_head", lambda _repo: SHA)
    monkeypatch.setattr(runner, "FullSuiteLock", _FakeFullSuiteLock)
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(
        runner,
        "expected_pytest_shard_plan_ref",
        lambda: "pytest-shard-plan-ref:sha256:" + "a" * 64,
    )
    monkeypatch.setattr(
        runner,
        "load_aggregate_evidence",
        lambda *_args, **_kwargs: {
            "collection_digest_ref": "sha256:" + "b" * 64,
            "collected_test_count": 17,
        },
    )
    starts: list[str] = []

    def fake_run_command(
        command: CommandSpec,
        *,
        validate_start=None,
        before_start=None,
        **_kwargs: object,
    ) -> dict[str, object]:
        assert validate_start is not None
        assert before_start is not None
        validate_start()
        before_start()
        starts.append(command.command_ref)
        return {
            "command_ref": command.command_ref,
            "category": command.category,
            "status": "pass",
            "started_at": "2026-07-15T00:00:00Z",
            "completed_at": "2026-07-15T00:00:01Z",
            "duration_ms": 1_000,
            "output_byte_count": 0,
            "output_digest": "c" * 64,
            "result_ref": "result-ref:ci:"
            + hashlib.sha256(command.command_ref.encode()).hexdigest(),
            "redaction_status": "content_free_output_metadata_only",
        }

    monkeypatch.setattr(runner, "_run_command", fake_run_command)
    fence_root = tmp_path / "execution-fence"
    runner.run_lane(
        "ci-pytest-shards",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
        verification_store_root=tmp_path / "proof-store",
        verification_execution_fence_root=fence_root,
    )

    unit = next(unit for unit in CI_JOB_GRAPH if unit.unit_ref == "pytest-shards")
    identity = build_verification_execution_identity(
        full_plan,
        unit,
        execution_surface_ref="surface-ref:github",
    )
    decision = VerificationExecutionFence(fence_root).begin(identity)
    assert (
        decision.disposition
        is VerificationExecutionFenceDisposition.TERMINAL_PROOF_REUSED
    )
    assert decision.terminal_proof is not None
    assert decision.terminal_proof.status is VerificationTerminalStatus.PASSED
    assert starts == ["command:pytest.sharded-suite"]


def test_local_exclusive_lane_uses_same_resource_fence_without_output_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lane_plan = build_plan(
        ROOT,
        SHA,
        lane_refs=("ci-pytest-shards",),
        verify_repository_state=False,
    )
    full_plan = build_plan(ROOT, SHA, verify_repository_state=False)
    monkeypatch.setattr(
        runner,
        "build_plan",
        lambda *_args, **kwargs: lane_plan if kwargs.get("lane_refs") else full_plan,
    )
    monkeypatch.setattr(runner, "_git_head", lambda _repo: SHA)
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(
        runner,
        "expected_pytest_shard_plan_ref",
        lambda: "pytest-shard-plan-ref:sha256:" + "a" * 64,
    )
    monkeypatch.setattr(
        runner,
        "load_aggregate_evidence",
        lambda *_args, **_kwargs: {
            "collection_digest_ref": "sha256:" + "b" * 64,
            "collected_test_count": 17,
        },
    )
    lock_scopes: list[str] = []

    class LocalFullSuiteLock(_FakeFullSuiteLock):
        def __init__(self, **kwargs: object) -> None:
            lock_scopes.append(str(kwargs.get("attempt_scope")))

    monkeypatch.setattr(runner, "FullSuiteLock", LocalFullSuiteLock)

    def fake_run_command(
        command: CommandSpec,
        *,
        validate_start=None,
        before_start=None,
        **_kwargs: object,
    ) -> dict[str, object]:
        assert validate_start is not None
        assert before_start is not None
        validate_start()
        before_start()
        return {
            "command_ref": command.command_ref,
            "category": command.category,
            "status": "pass",
            "started_at": "2026-07-15T00:00:00Z",
            "completed_at": "2026-07-15T00:00:01Z",
            "duration_ms": 1_000,
            "output_byte_count": 0,
            "output_digest": "c" * 64,
            "result_ref": "result-ref:ci:"
            + hashlib.sha256(command.command_ref.encode()).hexdigest(),
            "redaction_status": "content_free_output_metadata_only",
        }

    monkeypatch.setattr(runner, "_run_command", fake_run_command)
    fence_root = tmp_path / "execution-fence"

    runner.run_lane(
        "ci-pytest-shards",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
        verification_execution_fence_root=fence_root,
        full_suite_lock_mode="local",
    )

    unit = next(unit for unit in CI_JOB_GRAPH if unit.unit_ref == "pytest-shards")
    local_identity = build_verification_execution_identity(
        full_plan,
        unit,
        execution_surface_ref="surface-ref:local",
    )
    decision = VerificationExecutionFence(fence_root).begin(local_identity)
    assert lock_scopes == ["local"]
    assert (
        decision.disposition
        is VerificationExecutionFenceDisposition.TERMINAL_PROOF_REUSED
    )


def test_local_frontend_lane_uses_typescript_resource_attempt_and_fence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lane_plan = build_plan(
        ROOT,
        SHA,
        lane_refs=("ci-control-center-frontend",),
        verify_repository_state=False,
    )
    full_plan = build_plan(ROOT, SHA, verify_repository_state=False)
    monkeypatch.setattr(
        runner,
        "build_plan",
        lambda *_args, **kwargs: lane_plan if kwargs.get("lane_refs") else full_plan,
    )
    monkeypatch.setattr(runner, "_git_head", lambda _repo: SHA)
    declared = SimpleNamespace(
        declared_project_fingerprint=full_plan.typescript_project_fingerprint
    )
    runtime = SimpleNamespace(
        resolved_runtime_fingerprint="e" * 64,
        typescript_version="7.0.2",
    )
    monkeypatch.setattr(
        runner,
        "build_declared_typescript_binding",
        lambda _root: declared,
    )
    monkeypatch.setattr(
        runner,
        "resolve_typescript_runtime_binding",
        lambda _root, _declared: runtime,
    )
    monkeypatch.setattr(
        runner,
        "consume_frontend_collection_evidence",
        lambda _path: {
            "collection_digest_ref": "sha256:" + "d" * 64,
            "collected_test_count": 3,
            "result_status": "passed",
        },
    )
    lock_attempts: list[tuple[str, object]] = []

    class LocalFrontendLock(_FakeFullSuiteLock):
        def __init__(self, **kwargs: object) -> None:
            lock_attempts.append(
                (
                    str(kwargs.get("attempt_scope")),
                    kwargs.get("resource_attempt_fingerprint"),
                )
            )

    monkeypatch.setattr(runner, "FullSuiteLock", LocalFrontendLock)

    def fake_run_command(
        command: CommandSpec,
        *,
        validate_start=None,
        before_start=None,
        **_kwargs: object,
    ) -> dict[str, object]:
        assert validate_start is not None
        assert before_start is not None
        validate_start()
        before_start()
        return {
            "command_ref": command.command_ref,
            "category": command.category,
            "status": "pass",
            "started_at": "2026-07-15T00:00:00Z",
            "completed_at": "2026-07-15T00:00:01Z",
            "duration_ms": 1_000,
            "output_byte_count": 0,
            "output_digest": "c" * 64,
            "result_ref": "result-ref:ci:"
            + hashlib.sha256(command.command_ref.encode()).hexdigest(),
            "redaction_status": "content_free_output_metadata_only",
        }

    monkeypatch.setattr(runner, "_run_command", fake_run_command)
    fence_root = tmp_path / "execution-fence"

    receipt = runner.run_lane(
        "ci-control-center-frontend",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
        verification_execution_fence_root=fence_root,
        full_suite_lock_mode="local",
    )

    unit = next(
        unit for unit in CI_JOB_GRAPH if unit.unit_ref == "control-center-frontend"
    )
    local_identity = build_verification_execution_identity(
        full_plan,
        unit,
        execution_surface_ref="surface-ref:local",
        typescript_runtime_fingerprint=runtime.resolved_runtime_fingerprint,
        typescript_version_ref="typescript-version:7.0.2",
    )
    decision = VerificationExecutionFence(fence_root).begin(local_identity)
    assert receipt["status"] == "pass"
    assert lock_attempts == [
        ("local", local_identity.exclusive_resource_attempt_fingerprint)
    ]
    assert (
        decision.disposition
        is VerificationExecutionFenceDisposition.TERMINAL_PROOF_REUSED
    )


def test_exclusive_typed_lane_timeout_is_not_persisted_as_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lane_plan = build_plan(
        ROOT,
        SHA,
        lane_refs=("ci-pytest-shards",),
        verify_repository_state=False,
    )
    full_plan = build_plan(ROOT, SHA, verify_repository_state=False)
    monkeypatch.setattr(
        runner,
        "build_plan",
        lambda *_args, **kwargs: lane_plan if kwargs.get("lane_refs") else full_plan,
    )
    monkeypatch.setattr(runner, "_git_head", lambda _repo: SHA)
    monkeypatch.setattr(runner, "FullSuiteLock", _FakeFullSuiteLock)
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(
        runner,
        "expected_pytest_shard_plan_ref",
        lambda: "pytest-shard-plan-ref:sha256:" + "a" * 64,
    )

    def fake_run_command(
        command: CommandSpec,
        *,
        validate_start=None,
        before_start=None,
        **_kwargs: object,
    ) -> dict[str, object]:
        assert validate_start is not None
        assert before_start is not None
        validate_start()
        before_start()
        return {
            "command_ref": command.command_ref,
            "category": command.category,
            "status": "timed_out",
            "started_at": "2026-07-15T00:00:00Z",
            "completed_at": "2026-07-15T00:10:00Z",
            "duration_ms": 600_000,
            "output_byte_count": 0,
            "output_digest": "c" * 64,
            "result_ref": "result-ref:ci:"
            + hashlib.sha256(command.command_ref.encode()).hexdigest(),
            "redaction_status": "content_free_output_metadata_only",
        }

    monkeypatch.setattr(runner, "_run_command", fake_run_command)
    fence_root = tmp_path / "execution-fence"
    receipt = runner.run_lane(
        "ci-pytest-shards",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
        verification_store_root=tmp_path / "proof-store",
        verification_execution_fence_root=fence_root,
    )

    assert receipt["status"] == "fail"
    assert receipt["command_results"][0]["status"] == "timed_out"
    unit = next(unit for unit in CI_JOB_GRAPH if unit.unit_ref == "pytest-shards")
    identity = build_verification_execution_identity(
        full_plan,
        unit,
        execution_surface_ref="surface-ref:github",
    )
    decision = VerificationExecutionFence(fence_root).begin(identity)
    assert (
        decision.disposition
        is VerificationExecutionFenceDisposition.TERMINAL_PROOF_REUSED
    )
    assert decision.terminal_proof is not None
    assert decision.terminal_proof.failure_reason_ref == (
        "reason-ref:verification:infrastructure-failure"
    )
    assert decision.terminal_proof.deterministic_failure is False


@pytest.mark.skipif(os.name != "posix", reason="process-group proof is POSIX-only")
def test_run_command_timeout_reaps_leader_descendant_and_process_group(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    leader_pid_path = tmp_path / "leader.pid"
    descendant_pid_path = tmp_path / "descendant.pid"
    descendant_ready_path = tmp_path / "descendant.ready"
    parent_ready_path = tmp_path / "parent.ready"
    descendant = (
        "import pathlib,signal,sys,time;"
        "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
        "pathlib.Path(sys.argv[1]).write_text('ready',encoding='ascii');"
        "time.sleep(10)"
    )
    parent = (
        "import os,pathlib,subprocess,sys,time;"
        "leader=pathlib.Path(sys.argv[1]);"
        "descendant_pid=pathlib.Path(sys.argv[2]);"
        "descendant_ready=pathlib.Path(sys.argv[3]);"
        "parent_ready=pathlib.Path(sys.argv[4]);"
        "leader.write_text(str(os.getpid()),encoding='ascii');"
        "child=subprocess.Popen([sys.executable,'-c',sys.argv[5],sys.argv[3]]);"
        "descendant_pid.write_text(str(child.pid),encoding='ascii');"
        "deadline=time.monotonic()+5;"
        "\nwhile not descendant_ready.exists():\n"
        "    if child.poll() is not None: raise SystemExit(91)\n"
        "    if time.monotonic() >= deadline: raise SystemExit(92)\n"
        "    time.sleep(0.01)\n"
        "parent_ready.write_text('ready',encoding='ascii');"
        "time.sleep(10)"
    )
    command = CommandSpec(
        "command:test.real-timeout-process-tree",
        (
            sys.executable,
            "-c",
            parent,
            str(leader_pid_path),
            str(descendant_pid_path),
            str(descendant_ready_path),
            str(parent_ready_path),
            descendant,
        ),
        (),
        "test",
        2,
    )
    monkeypatch.setattr(runner, "TERMINATION_GRACE_SECONDS", 0.2)

    result = runner._run_command(
        command,
        repository_sha=SHA,
        temp_root=tmp_path,
    )

    assert result["status"] == "timed_out"
    assert parent_ready_path.read_text(encoding="ascii") == "ready"
    assert descendant_ready_path.read_text(encoding="ascii") == "ready"
    leader_pid = int(leader_pid_path.read_text(encoding="ascii"))
    descendant_pid = int(descendant_pid_path.read_text(encoding="ascii"))
    deadline = time.monotonic() + 3
    while True:
        live_refs: list[str] = []
        for ref, pid in (("leader", leader_pid), ("descendant", descendant_pid)):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                continue
            except PermissionError:
                live_refs.append(ref)
                continue
            live_refs.append(ref)
        if shard_processes._owned_live_process_group_members(leader_pid):
            live_refs.append("process-group")
        if not live_refs:
            break
        if time.monotonic() >= deadline:
            pytest.fail(f"timed-out process tree survived: {','.join(live_refs)}")
        time.sleep(0.02)
    serialized = json.dumps(result, sort_keys=True)
    assert str(tmp_path) not in serialized
    assert "ready" not in serialized


@pytest.mark.skipif(os.name != "posix", reason="process-group proof is POSIX-only")
def test_run_command_success_reaps_residual_descendant_before_return(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    descendant_pid_path = tmp_path / "descendant.pid"
    descendant_ready_path = tmp_path / "descendant.ready"
    parent = (
        "import pathlib,subprocess,sys,time;"
        "pid_path=pathlib.Path(sys.argv[1]);"
        "ready_path=pathlib.Path(sys.argv[2]);"
        "child=subprocess.Popen([sys.executable,'-c',"
        '"import pathlib,sys,time;pathlib.Path(sys.argv[1]).write_text('
        "'ready',encoding='ascii');time.sleep(10)\",sys.argv[2]]);"
        "pid_path.write_text(str(child.pid),encoding='ascii');"
        "deadline=time.monotonic()+5;"
        "\nwhile not ready_path.exists():\n"
        "    if child.poll() is not None: raise SystemExit(91)\n"
        "    if time.monotonic() >= deadline: raise SystemExit(92)\n"
        "    time.sleep(0.01)\n"
    )
    command = CommandSpec(
        "command:test.real-success-process-tree",
        (
            sys.executable,
            "-c",
            parent,
            str(descendant_pid_path),
            str(descendant_ready_path),
        ),
        (),
        "test",
        10,
    )
    monkeypatch.setattr(runner, "TERMINATION_GRACE_SECONDS", 0.2)
    descendant_pid: int | None = None

    try:
        result = runner._run_command(
            command,
            repository_sha=SHA,
            temp_root=tmp_path,
        )

        assert result["status"] == "pass"
        descendant_pid = int(descendant_pid_path.read_text(encoding="ascii"))
        assert descendant_ready_path.read_text(encoding="ascii") == "ready"
        serialized = json.dumps(result, sort_keys=True)
        assert str(tmp_path) not in serialized
        assert "ready" not in serialized
        deadline = time.monotonic() + 3
        while True:
            try:
                os.kill(descendant_pid, 0)
            except ProcessLookupError:
                break
            if time.monotonic() >= deadline:
                pytest.fail("successful command residual descendant survived")
            time.sleep(0.02)
    finally:
        if descendant_pid is not None:
            try:
                os.kill(descendant_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


@pytest.mark.skipif(os.name != "posix", reason="signal proof is POSIX-only")
def test_run_command_repeated_signal_cleans_process_group_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ready_path = tmp_path / "command.ready"
    output_marker = b"cancelled-output-metadata-proof\n"
    command = CommandSpec(
        "command:test.repeated-signal-cleanup",
        (
            sys.executable,
            "-c",
            (
                "import pathlib,sys,time;"
                "print('cancelled-output-metadata-proof',flush=True);"
                "pathlib.Path(sys.argv[1]).write_text('ready',encoding='ascii');"
                "time.sleep(10)"
            ),
            str(ready_path),
        ),
        (),
        "test",
        10,
    )
    original_stop_processes = runner.stop_processes
    cleanup_calls = 0

    def count_cleanup(processes: object, grace_seconds: float) -> None:
        nonlocal cleanup_calls
        cleanup_calls += 1
        original_stop_processes(processes, grace_seconds)  # type: ignore[arg-type]

    def send_signals() -> None:
        deadline = time.monotonic() + 5
        while not ready_path.exists():
            if time.monotonic() >= deadline:
                return
            time.sleep(0.01)
        os.kill(os.getpid(), signal.SIGTERM)
        os.kill(os.getpid(), signal.SIGHUP)

    monkeypatch.setattr(runner, "TERMINATION_GRACE_SECONDS", 0.2)
    monkeypatch.setattr(runner, "stop_processes", count_cleanup)
    sender = threading.Thread(target=send_signals)
    sender.start()
    try:
        result = runner._run_command(
            command,
            repository_sha=SHA,
            temp_root=tmp_path,
        )
    finally:
        sender.join(timeout=5)

    assert sender.is_alive() is False
    assert result["status"] == "cancelled"
    assert cleanup_calls == 1
    assert result["output_byte_count"] == len(output_marker)
    assert result["output_digest"] == hashlib.sha256(output_marker).hexdigest()
    assert not tuple(tmp_path.glob("uaa-ci-transient-*"))


@pytest.mark.skipif(os.name != "posix", reason="signal proof is POSIX-only")
def test_run_command_preserves_spawn_cleanup_failure_over_pending_signal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.spawn-cleanup-priority",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )

    def fail_spawn(*_args: object, **_kwargs: object) -> None:
        handler = signal.getsignal(signal.SIGTERM)
        assert callable(handler)
        handler(signal.SIGTERM, None)
        raise shard_processes.ProcessCleanupError("cleanup-unproven")

    monkeypatch.setattr(runner, "spawn_owned_process_group", fail_spawn)

    with pytest.raises(
        shard_processes.ProcessCleanupError,
        match="cleanup-unproven",
    ):
        runner._run_command(
            command,
            repository_sha=SHA,
            temp_root=tmp_path,
        )


def test_github_output_is_exact_v4_non_authoritative_envelope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lane_plan = build_plan(
        ROOT,
        SHA,
        lane_refs=("ci-lint",),
        verify_repository_state=False,
    )
    full_plan = build_plan(ROOT, SHA, verify_repository_state=False)
    monkeypatch.setattr(
        runner,
        "build_plan",
        lambda *_args, **kwargs: lane_plan if kwargs.get("lane_refs") else full_plan,
    )
    monkeypatch.setattr(runner, "_git_head", lambda _repo: SHA)

    def fake_run_command(command: CommandSpec, **_kwargs: object) -> dict[str, object]:
        digest = hashlib.sha256(command.command_ref.encode()).hexdigest()
        return {
            "command_ref": command.command_ref,
            "category": command.category,
            "status": "pass",
            "started_at": "2026-07-15T00:00:00Z",
            "completed_at": "2026-07-15T00:00:01Z",
            "duration_ms": 1_000,
            "output_byte_count": 0,
            "output_digest": digest,
            "result_ref": "result-ref:ci:" + digest,
            "redaction_status": "content_free_output_metadata_only",
        }

    monkeypatch.setattr(runner, "_run_command", fake_run_command)
    output_file = tmp_path / "github-output"
    output_file.touch(mode=0o600)
    runner.run_lane(
        "ci-lint",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
        github_output_file=output_file,
    )

    key, encoded = output_file.read_text(encoding="ascii").strip().split("=", 1)
    assert key == runner.GITHUB_OUTPUT_KEY
    envelope = decode_github_job_output(encoded)
    assert envelope.repository_sha == SHA
    assert envelope.receipt.unit_ref == "lint"
    assert envelope.final_run_manifest is None
    assert envelope.construction_posture == "repository_constructed_non_authoritative"


def test_receipt_writer_rejects_outside_parent_before_creating_it(
    tmp_path: Path,
) -> None:
    temp_root = runner._safe_temp_root(tmp_path / "temp")
    outside = tmp_path / "outside" / "receipt.json"

    with pytest.raises(ValueError, match="inside the temp root"):
        runner._write_receipt(outside, {"safe": True}, temp_root)

    assert not outside.parent.exists()


def test_receipt_writer_rejects_symlinked_parent(tmp_path: Path) -> None:
    temp_root = runner._safe_temp_root(tmp_path / "temp")
    outside = tmp_path / "outside"
    outside.mkdir()
    (temp_root / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="inside the temp root"):
        runner._write_receipt(
            temp_root / "linked" / "receipt.json",
            {"safe": True},
            temp_root,
        )

    assert not (outside / "receipt.json").exists()


def test_lane_runner_stops_after_deterministic_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands = (
        CommandSpec(
            "command:test.fail",
            (sys.executable, "-c", "raise SystemExit(3)"),
            (),
            "test",
            10,
        ),
        CommandSpec(
            "command:test.must-not-start",
            (sys.executable, "-c", "raise SystemExit(0)"),
            (),
            "test",
            10,
        ),
    )
    _patch_lane(monkeypatch, commands)

    receipt = runner.run_lane(
        "test-lane",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
    )

    assert receipt["status"] == "fail"
    assert [item["command_ref"] for item in receipt["command_results"]] == [
        "command:test.fail"
    ]


def test_pytest_shard_evidence_retains_only_reproducible_failed_refs(
    tmp_path: Path,
) -> None:
    report = tmp_path / runner.PYTEST_PERFORMANCE_REPORT_NAME
    _write_pytest_performance_report(report, failed_index=3)

    evidence = runner._pytest_shard_evidence(
        tmp_path,
        expected_plan_ref="pytest-shard-plan-ref:sha256:" + "a" * 64,
        command_status="fail",
    )

    assert evidence == {
        "pytest_shard_evidence_status": "available",
        "pytest_shard_plan_fingerprint_ref": (
            "pytest-shard-plan-ref:sha256:" + "a" * 64
        ),
        "pytest_shard_count": CANONICAL_PYTEST_SHARD_COUNT,
        "failed_shard_count": 1,
        "failed_shard_refs": ("pytest-shard-ref:3:failed",),
    }
    serialized = json.dumps(evidence, sort_keys=True)
    assert str(tmp_path) not in serialized
    assert "raw" not in serialized


def test_pytest_shard_evidence_marks_timeout_without_raw_output(
    tmp_path: Path,
) -> None:
    report = tmp_path / runner.PYTEST_PERFORMANCE_REPORT_NAME
    _write_pytest_performance_report(report, failed_index=6, timed_out=True)

    evidence = runner._pytest_shard_evidence(
        tmp_path,
        expected_plan_ref="pytest-shard-plan-ref:sha256:" + "a" * 64,
        command_status="fail",
    )

    assert evidence["failed_shard_refs"] == ("pytest-shard-ref:6:timed-out",)


def test_pytest_shard_evidence_retains_bounded_safe_test_refs(
    tmp_path: Path,
) -> None:
    report = tmp_path / runner.PYTEST_PERFORMANCE_REPORT_NAME
    safe_ref = safe_test_ref("tests/test_module.py::test_case")
    _write_pytest_performance_report(
        report,
        failed_index=2,
        failed_test_refs=(safe_ref,),
    )

    evidence = runner._pytest_shard_evidence(
        tmp_path,
        expected_plan_ref="pytest-shard-plan-ref:sha256:" + "a" * 64,
        command_status="fail",
    )

    assert evidence["failed_test_refs"] == (safe_ref,)
    assert runner._pytest_shard_summary_lines(evidence)[-1] == (
        f"Diagnostic test ref: {safe_ref}"
    )
    assert evidence["failed_test_ref_posture"] == (
        "diagnostic_untrusted_code_metadata_only"
    )


def test_pytest_shard_summary_includes_bounded_collection_rejection_reason() -> None:
    reason_ref = "reason-ref:ci:pytest-collection-evidence-unavailable"

    lines = runner._pytest_shard_summary_lines(
        {
            "pytest_shard_evidence_status": "unavailable",
            "pytest_collection_evidence_status": "rejected",
            "pytest_collection_evidence_reason_ref": reason_ref,
        }
    )

    assert lines[-1] == f"Pytest collection evidence reason: {reason_ref}"


@pytest.mark.parametrize(
    "failed_test_refs",
    [
        ("unsafe raw node id",),
        (
            safe_test_ref("tests/test_module.py::test_case"),
            safe_test_ref("tests/test_module.py::test_case"),
        ),
        ("pytest-test-ref:test-module:test-case:123456789abc",),
    ],
)
def test_pytest_shard_evidence_rejects_unsafe_or_duplicate_test_refs(
    tmp_path: Path,
    failed_test_refs: tuple[str, ...],
) -> None:
    report = tmp_path / runner.PYTEST_PERFORMANCE_REPORT_NAME
    _write_pytest_performance_report(
        report,
        failed_index=2,
        failed_test_refs=failed_test_refs,
    )

    evidence = runner._pytest_shard_evidence(
        tmp_path,
        expected_plan_ref="pytest-shard-plan-ref:sha256:" + "a" * 64,
        command_status="fail",
    )

    assert evidence["pytest_shard_evidence_status"] == "rejected"


def test_pytest_shard_evidence_rejects_successful_timeout_row(tmp_path: Path) -> None:
    report = tmp_path / runner.PYTEST_PERFORMANCE_REPORT_NAME
    _write_pytest_performance_report(report, failed_index=2, timed_out=True)
    payload = json.loads(report.read_text(encoding="utf-8"))
    payload["shards"][2]["return_code"] = 0
    report.write_text(json.dumps(payload), encoding="utf-8")

    evidence = runner._pytest_shard_evidence(
        tmp_path,
        expected_plan_ref="pytest-shard-plan-ref:sha256:" + "a" * 64,
        command_status="fail",
    )

    assert evidence["pytest_shard_evidence_status"] == "rejected"


def test_pytest_shard_evidence_rejects_symlink_and_malformed_report(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside.json"
    _write_pytest_performance_report(outside, failed_index=1)
    report = tmp_path / runner.PYTEST_PERFORMANCE_REPORT_NAME
    report.symlink_to(outside)

    symlink_evidence = runner._pytest_shard_evidence(
        tmp_path,
        expected_plan_ref="pytest-shard-plan-ref:sha256:" + "a" * 64,
        command_status="fail",
    )
    assert symlink_evidence["pytest_shard_evidence_status"] == "rejected"
    assert "unsafe" in symlink_evidence["pytest_shard_evidence_reason_ref"]

    report.unlink()
    report.write_text('{"schema_version":"wrong"}', encoding="utf-8")
    malformed_evidence = runner._pytest_shard_evidence(
        tmp_path,
        expected_plan_ref="pytest-shard-plan-ref:sha256:" + "a" * 64,
        command_status="fail",
    )
    assert malformed_evidence["pytest_shard_evidence_status"] == "rejected"
    assert "invalid" in malformed_evidence["pytest_shard_evidence_reason_ref"]


def test_pytest_lane_receipt_and_summary_retain_safe_failed_shard_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pytest-shards",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,), lane_ref="ci-pytest-shards")

    def fake_run_command(
        _command: CommandSpec,
        *,
        temp_root: Path,
        **_kwargs: object,
    ) -> dict[str, object]:
        _write_pytest_performance_report(
            temp_root / runner.PYTEST_PERFORMANCE_REPORT_NAME,
            failed_index=2,
        )
        return {
            "command_ref": "command:test.pytest-shards",
            "category": "test",
            "status": "fail",
            "duration_ms": 1,
            "result_ref": "result-ref:ci:test",
            "redaction_status": "content_free_output_metadata_only",
        }

    monkeypatch.setattr(runner, "FullSuiteLock", _FakeFullSuiteLock)
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(
        runner,
        "expected_pytest_shard_plan_ref",
        lambda: "pytest-shard-plan-ref:sha256:" + "a" * 64,
    )
    monkeypatch.setattr(runner, "_run_command", fake_run_command)
    summary_file = tmp_path / "summary.md"

    receipt = runner.run_lane(
        "ci-pytest-shards",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
        summary_file=summary_file,
    )

    result = receipt["command_results"][0]
    assert result["failed_shard_refs"] == ("pytest-shard-ref:2:failed",)
    summary = summary_file.read_text(encoding="utf-8")
    assert "pytest-shard-ref:2:failed" in summary
    assert "make ci-reproduce-shard CI_SHARD_INDEX=2" in summary
    assert str(tmp_path) not in json.dumps(receipt, sort_keys=True)


def test_diagnostic_reproduction_lane_is_non_gating_and_rejects_typed_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lane_ref = "ci-pytest-shard-1-reproduce"
    command_ref = "command:pytest.shard-1-reproduce"
    command = CommandSpec(
        command_ref,
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    plan = build_plan(
        ROOT,
        SHA,
        lane_refs=(lane_ref,),
        verify_repository_state=False,
    )
    monkeypatch.setattr(runner, "_git_head", lambda _repo: SHA)
    monkeypatch.setattr(runner, "command_registry", lambda: {command_ref: command})
    monkeypatch.setattr(
        runner,
        "lane_registry",
        lambda: {lane_ref: LaneSpec(lane_ref, "Diagnostic", (command_ref,))},
    )
    monkeypatch.setattr(runner, "build_plan", lambda *_args, **_kwargs: plan)
    lock_kwargs: list[dict[str, object]] = []

    class _CapturingDiagnosticLock(_FakeFullSuiteLock):
        def __init__(self, **kwargs: object) -> None:
            lock_kwargs.append(kwargs)

    monkeypatch.setattr(runner, "FullSuiteLock", _CapturingDiagnosticLock)

    receipt = runner.run_lane(
        lane_ref,
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
        full_suite_lock_mode="private",
    )

    assert receipt["status"] == "pass"
    assert receipt["execution_surface_ref"] == "surface-ref:local"
    assert receipt["github_gate_satisfied"] is False
    assert receipt["merge_gate_satisfied"] is False
    assert lock_kwargs == [
        {
            "path": runner.PYTEST_DIAGNOSTIC_LOCK_PATH,
            "wait_seconds": 0,
            "shared_across_accounts": False,
        }
    ]

    with pytest.raises(ValueError, match="local/private only"):
        runner.run_lane(
            lane_ref,
            repository_sha=SHA,
            temp_root=tmp_path / "github-temp",
            execution_surface="github",
        )

    with pytest.raises(ValueError, match="cannot emit typed gating evidence"):
        runner.run_lane(
            lane_ref,
            repository_sha=SHA,
            temp_root=tmp_path / "typed-temp",
            verification_receipt_file=tmp_path / "typed-temp" / "receipt.json",
            full_suite_lock_mode="private",
        )


def test_typed_non_diagnostic_lane_rejects_execution_surface_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pass",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,))

    with pytest.raises(ValueError, match="limited to diagnostic reproduction"):
        runner.run_lane(
            "test-lane",
            repository_sha=SHA,
            temp_root=tmp_path / "temp",
            verification_receipt_file=tmp_path / "temp" / "receipt.json",
            verification_run_manifest_file=tmp_path / "temp" / "run.json",
            full_suite_lock_mode="private",
            execution_surface="github",
        )


def test_private_non_diagnostic_lane_is_denied_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pass",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,))
    started: list[bool] = []
    monkeypatch.setattr(
        runner,
        "_run_command",
        lambda *_args, **_kwargs: started.append(True),
    )

    with pytest.raises(
        runner.PrivateNonDiagnosticExecutionError,
        match="exact diagnostic shard reproduction",
    ):
        runner.run_lane(
            "test-lane",
            repository_sha=SHA,
            temp_root=tmp_path / "temp",
            full_suite_lock_mode="private",
        )

    assert started == []


def test_cli_redacts_private_non_diagnostic_lane_denial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    unsafe_detail = f"private execution attempted from {tmp_path}"

    def _raise_denied(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise runner.PrivateNonDiagnosticExecutionError(unsafe_detail)

    monkeypatch.setattr(runner, "run_lane", _raise_denied)

    exit_code = runner.main(
        [
            "--lane",
            "ci-pytest-shards",
            "--sha",
            SHA,
            "--temp-root",
            str(tmp_path / "temp"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert runner.PRIVATE_NON_DIAGNOSTIC_REASON_REF in captured.err
    assert unsafe_detail not in captured.err


def test_main_prints_safe_failed_shard_reproduction_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    receipt = {
        "lane_ref": "ci-pytest-shards",
        "status": "fail",
        "repository_sha": SHA,
        "plan": {"definition_fingerprint": "manifest-ref:safe"},
        "command_results": [
            {
                "command_ref": "command:pytest.sharded-suite",
                "status": "fail",
                "pytest_shard_evidence_status": "available",
                "failed_shard_refs": ("pytest-shard-ref:4:failed",),
            }
        ],
    }
    monkeypatch.setattr(runner, "run_lane", lambda *_args, **_kwargs: receipt)

    exit_code = runner.main(
        [
            "--lane",
            "ci-pytest-shards",
            "--sha",
            SHA,
            "--temp-root",
            str(tmp_path / "temp"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pytest-shard-ref:4:failed" in captured.out
    assert "make ci-reproduce-shard CI_SHARD_INDEX=4" in captured.out
    assert str(tmp_path) not in captured.out


def test_pytest_shard_evidence_rejects_stale_or_contradictory_report(
    tmp_path: Path,
) -> None:
    report = tmp_path / runner.PYTEST_PERFORMANCE_REPORT_NAME
    _write_pytest_performance_report(
        report,
        plan_ref="pytest-shard-plan-ref:sha256:" + "b" * 64,
    )
    stale = runner._pytest_shard_evidence(
        tmp_path,
        expected_plan_ref="pytest-shard-plan-ref:sha256:" + "a" * 64,
        command_status="pass",
    )
    assert stale["pytest_shard_evidence_status"] == "rejected"

    report.unlink()
    _write_pytest_performance_report(report, failed_index=2)
    contradictory = runner._pytest_shard_evidence(
        tmp_path,
        expected_plan_ref="pytest-shard-plan-ref:sha256:" + "a" * 64,
        command_status="pass",
    )
    assert contradictory["pytest_shard_evidence_status"] == "rejected"
    assert "inconsistent" in contradictory["pytest_shard_evidence_reason_ref"]


def test_pytest_lane_rejects_preexisting_performance_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pytest-shards",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,), lane_ref="ci-pytest-shards")
    temp_root = tmp_path / "temp"
    temp_root.mkdir()
    _write_pytest_performance_report(temp_root / runner.PYTEST_PERFORMANCE_REPORT_NAME)
    monkeypatch.setattr(runner, "FullSuiteLock", _FakeFullSuiteLock)
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda _name: object())
    started: list[bool] = []
    monkeypatch.setattr(
        runner,
        "_run_command",
        lambda *_args, **_kwargs: started.append(True),
    )

    with pytest.raises(ValueError, match="must not predate"):
        runner.run_lane(
            "ci-pytest-shards",
            repository_sha=SHA,
            temp_root=temp_root,
        )
    assert started == []


def test_full_suite_attempt_is_fenced_before_process_spawn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.spawn-failure",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    starts: list[bool] = []
    validations: list[bool] = []
    monkeypatch.setattr(
        runner.subprocess,
        "Popen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("spawn failed")),
    )

    with pytest.raises(OSError, match="spawn failed"):
        runner._run_command(
            command,
            repository_sha=SHA,
            temp_root=tmp_path,
            validate_start=lambda: validations.append(True),
            before_start=lambda: starts.append(True),
        )

    assert validations == [True]
    assert starts == [True]


def test_pytest_lane_rejects_missing_runtime_before_attempt_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pass",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,), lane_ref="ci-pytest-shards")
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda _name: None)

    with pytest.raises(
        runner.PytestRuntimeUnavailableError,
        match="pytest runtime is unavailable",
    ):
        runner.run_lane(
            "ci-pytest-shards",
            repository_sha=SHA,
            temp_root=tmp_path / "temp",
        )


def test_cli_redacts_missing_pytest_runtime_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    unsafe_detail = f"pytest missing from {tmp_path}"

    def _raise_unavailable(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise runner.PytestRuntimeUnavailableError(unsafe_detail)

    monkeypatch.setattr(runner, "run_lane", _raise_unavailable)

    exit_code = runner.main(
        [
            "--lane",
            "ci-pytest-shards",
            "--sha",
            SHA,
            "--temp-root",
            str(tmp_path / "temp"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == (
        "UAA CI lane blocked: reason-ref:ci:pytest-runtime-unavailable"
    )
    assert "Traceback" not in captured.err
    assert unsafe_detail not in captured.err
    assert str(tmp_path) not in captured.err


def test_full_pytest_lane_denies_busy_matrix_loopback_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pass",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,), lane_ref="ci-pytest-shards")
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda _name: object())
    events: list[str] = []

    class FakeFullSuiteLock:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def __enter__(self) -> FakeFullSuiteLock:
            events.append("lock-held")
            return self

        def __exit__(self, *_args: object) -> None:
            events.append("lock-released")

        def ensure_start_available(self) -> None:
            events.append("attempt-available")

        def record_start(self) -> None:
            events.append("attempt-recorded")

    def deny_resource() -> None:
        events.append("resource-denied")
        raise runner.MatrixLoopbackTestResourceUnavailableError("busy")

    monkeypatch.setattr(runner, "FullSuiteLock", FakeFullSuiteLock)
    monkeypatch.setattr(
        runner,
        "assert_matrix_loopback_test_resource_available",
        deny_resource,
    )

    with pytest.raises(runner.MatrixLoopbackTestResourceUnavailableError):
        runner.run_lane(
            "ci-pytest-shards",
            repository_sha=SHA,
            temp_root=tmp_path / "temp",
        )

    assert events == [
        "lock-held",
        "attempt-available",
        "resource-denied",
        "lock-released",
    ]


def test_cli_redacts_busy_matrix_loopback_resource(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    unsafe_detail = f"loopback resource busy near {tmp_path}"

    def _raise_unavailable(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise runner.MatrixLoopbackTestResourceUnavailableError(unsafe_detail)

    monkeypatch.setattr(runner, "run_lane", _raise_unavailable)

    exit_code = runner.main(
        [
            "--lane",
            "ci-pytest-shards",
            "--sha",
            SHA,
            "--temp-root",
            str(tmp_path / "temp"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == (
        "UAA CI lane blocked: "
        "reason-ref:ci:pytest-loopback-resource-unavailable"
    )
    assert "Traceback" not in captured.err
    assert unsafe_detail not in captured.err
    assert str(tmp_path) not in captured.err


def test_post_prestart_resource_collision_remains_a_code_failure() -> None:
    assert runner._execution_failure_reason_ref([{"status": "fail"}]) == (
        "reason-ref:verification:deterministic-code-failure"
    )


def test_cli_redacts_unexpected_lane_execution_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    unsafe_detail = f"executable missing from {tmp_path}"

    def _raise_spawn_failure(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise FileNotFoundError(unsafe_detail)

    monkeypatch.setattr(runner, "run_lane", _raise_spawn_failure)

    exit_code = runner.main(
        [
            "--lane",
            "ci-manifest-attestation",
            "--sha",
            SHA,
            "--temp-root",
            str(tmp_path / "temp"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == (
        "UAA CI lane blocked: reason-ref:ci:lane-execution-failed"
    )
    assert "Traceback" not in captured.err
    assert unsafe_detail not in captured.err
    assert str(tmp_path) not in captured.err


def test_cli_redacts_full_suite_lock_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    unsafe_detail = f"lock unavailable at {tmp_path}"

    def _raise_unavailable(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise runner.FullSuiteLockUnavailableError(unsafe_detail)

    monkeypatch.setattr(runner, "run_lane", _raise_unavailable)

    exit_code = runner.main(
        [
            "--lane",
            "ci-pytest-shards",
            "--sha",
            SHA,
            "--temp-root",
            str(tmp_path / "temp"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == (
        "UAA CI lane blocked: reason-ref:ci:full-suite-capacity-unavailable"
    )
    assert "Traceback" not in captured.err
    assert unsafe_detail not in captured.err
    assert str(tmp_path) not in captured.err


def test_cli_redacts_duplicate_full_suite_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    unsafe_detail = f"duplicate attempt recorded at {tmp_path}"

    def _raise_duplicate(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise runner.FullSuiteAttemptAlreadyRecordedError(unsafe_detail)

    monkeypatch.setattr(runner, "run_lane", _raise_duplicate)

    exit_code = runner.main(
        [
            "--lane",
            "ci-pytest-shards",
            "--sha",
            SHA,
            "--temp-root",
            str(tmp_path / "temp"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == (
        "UAA CI lane blocked: reason-ref:ci:full-suite-attempt-recorded"
    )
    assert "Traceback" not in captured.err
    assert unsafe_detail not in captured.err
    assert str(tmp_path) not in captured.err


def test_visual_optional_command_is_skipped_only_for_exact_not_affected_posture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands = (
        CommandSpec(
            "command:frontend.visual-regression",
            (sys.executable, "-c", "raise SystemExit(9)"),
            (),
            "frontend",
            10,
        ),
        CommandSpec(
            "command:test.contract",
            (sys.executable, "-c", "raise SystemExit(0)"),
            (),
            "test",
            10,
        ),
    )
    _patch_lane(
        monkeypatch,
        commands,
        optional=("command:frontend.visual-regression",),
    )

    receipt = runner.run_lane(
        "test-lane",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
        visual_scope="not_affected",
    )

    assert receipt["status"] == "pass"
    assert receipt["command_results"][0]["status"] == "not_applicable"
    assert receipt["command_results"][1]["status"] == "pass"


def test_summary_rejects_symlink_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pass",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,))
    target = tmp_path / "target"
    target.write_text("safe", encoding="utf-8")
    summary = tmp_path / "summary"
    summary.symlink_to(target)

    with pytest.raises(ValueError, match="regular non-symlink"):
        runner.run_lane(
            "test-lane",
            repository_sha=SHA,
            temp_root=tmp_path / "temp",
            summary_file=summary,
        )


def test_summary_rejects_hardlink_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pass",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,))
    target = tmp_path / "target"
    target.write_text("safe", encoding="utf-8")
    summary = tmp_path / "summary"
    summary.hardlink_to(target)
    with pytest.raises(ValueError, match="remain regular"):
        runner.run_lane(
            "test-lane",
            repository_sha=SHA,
            temp_root=tmp_path / "temp",
            summary_file=summary,
        )


def test_pytest_lane_uses_host_lock_with_exact_sha_and_execution_plane(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = CommandSpec(
        "command:test.pass",
        (sys.executable, "-c", "raise SystemExit(0)"),
        (),
        "test",
        10,
    )
    _patch_lane(monkeypatch, (command,), lane_ref="ci-pytest-shards")
    captured: list[dict[str, object]] = []

    class FakeLock:
        def __init__(self, **kwargs: object) -> None:
            captured.append(kwargs)

        def __enter__(self) -> None:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def record_start(self) -> None:
            captured[-1]["started"] = True

        def ensure_start_available(self) -> None:
            captured[-1]["start_available"] = True

    monkeypatch.setattr(runner, "FullSuiteLock", FakeLock)
    receipt = runner.run_lane(
        "ci-pytest-shards",
        repository_sha=SHA,
        temp_root=tmp_path / "temp",
    )
    assert receipt["status"] == "pass"
    resource_attempt_fingerprint = captured[0].pop(
        "resource_attempt_fingerprint"
    )
    assert isinstance(resource_attempt_fingerprint, str)
    assert len(resource_attempt_fingerprint) == 64
    int(resource_attempt_fingerprint, 16)
    assert captured == [
        {
            "wait_seconds": runner.GITHUB_FULL_SUITE_LOCK_WAIT_SECONDS,
            "repository_sha": SHA,
            "attempt_scope": "github",
            "start_available": True,
            "started": True,
        }
    ]
