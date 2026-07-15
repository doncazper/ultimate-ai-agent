from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import pytest
from pydantic import ValidationError

from scripts import run_agent_capability_evaluation as runner
from scripts.verify_capability_maturity_uplift import (
    CapabilityMaturityVerificationError,
    verify_report,
)
from ultimate_ai_agent.core.evals import (
    CAPABILITY_COMPONENT_IDS,
    CapabilityEvaluationStatus,
    CapabilityMaturityDecisionStatus,
    CapabilityMaturityEvidenceStatus,
    CapabilityMaturityGraduationDecision,
    CapabilityScenarioObservation,
    build_agent_capability_evaluation_report,
    build_capability_maturity_read_model,
    capability_maturity_decision_ref,
    capability_maturity_report_digest,
)


def _observation(
    component_id: str,
    index: int,
    *,
    status: CapabilityEvaluationStatus = CapabilityEvaluationStatus.passed,
    structured_metrics: bool = False,
) -> CapabilityScenarioObservation:
    return CapabilityScenarioObservation(
        scenario_ref=f"scenario:test:{index}",
        component_id=component_id,
        expected_status=status,
        observed_status=status,
        evidence_refs=(f"evidence-ref:test:{index}",),
        verifier_refs=(f"verifier-ref:test:{index}",),
        execution_fingerprint_ref=f"fingerprint-ref:test:{index}",
        duration_ms=1,
        task_completed=(
            status == CapabilityEvaluationStatus.passed if structured_metrics else None
        ),
        completion_claimed=(
            status == CapabilityEvaluationStatus.passed if structured_metrics else None
        ),
        operator_interventions=0 if structured_metrics else None,
        unsupported_claim_count=0 if structured_metrics else None,
        policy_violation_refs=() if structured_metrics else None,
        evidence_complete=True if structured_metrics else None,
        recovery_expected=index == 0,
        recovery_succeeded=True if index == 0 and structured_metrics else None,
        replay_expected=index == 1,
        replay_succeeded=True if index == 1 and structured_metrics else None,
    )


def _observations(
    *, structured_metrics: bool = False
) -> tuple[CapabilityScenarioObservation, ...]:
    return tuple(
        _observation(component_id, index, structured_metrics=structured_metrics)
        for index, component_id in enumerate(CAPABILITY_COMPONENT_IDS)
    )


def test_report_separates_verifier_outcomes_from_unmeasured_task_completion() -> None:
    observations = list(_observations())
    observations[-1] = _observation(
        CAPABILITY_COMPONENT_IDS[-1],
        len(CAPABILITY_COMPONENT_IDS) - 1,
        status=CapabilityEvaluationStatus.blocked,
    )
    report = build_agent_capability_evaluation_report(
        report_ref="evaluation-report:test:complete",
        benchmark_ref="benchmark-ref:test:complete",
        registry_fingerprint_ref="fingerprint-ref:test:registry",
        observations=tuple(observations),
    )

    assert report.status == CapabilityEvaluationStatus.passed
    assert report.safe_outcome_adherence_rate == 1.0
    assert report.verification_pass_rate == 1.0
    assert report.passed_unblocked_verifier_count == 15
    assert report.passed_unblocked_verifier_rate == 0.9375
    assert report.task_completion_count is None
    assert report.task_completion_rate is None
    assert report.task_completion_posture == "not_measured"
    assert report.blocked_safe_outcome_count == 1
    assert report.correctness_rate is None
    assert report.recovery_success_rate is None
    assert report.evidence_completeness_rate is None
    assert report.replay_correctness_rate is None
    assert report.operator_intervention_count is None
    assert report.false_completion_count is None
    assert report.authority_policy_violation_count is None
    assert report.authority_granted is False


def test_report_aggregates_only_explicit_structured_metrics() -> None:
    report = build_agent_capability_evaluation_report(
        report_ref="evaluation-report:test:measured",
        benchmark_ref="benchmark-ref:test:measured",
        registry_fingerprint_ref="fingerprint-ref:test:registry",
        observations=_observations(structured_metrics=True),
    )

    assert report.correctness_rate == 1.0
    assert report.recovery_success_rate == 1.0
    assert report.evidence_completeness_rate == 1.0
    assert report.replay_correctness_rate == 1.0
    assert report.operator_intervention_count == 0
    assert report.false_completion_count == 0
    assert report.authority_policy_violation_count == 0
    assert report.correctness_posture == "measured"
    assert report.task_completion_count == len(CAPABILITY_COMPONENT_IDS)
    assert report.task_completion_rate == 1.0
    assert report.task_completion_posture == "measured"


def test_false_completion_is_measurable_and_fails_the_report() -> None:
    observations = list(_observations(structured_metrics=True))
    observations[0] = observations[0].model_copy(
        update={"task_completed": False, "completion_claimed": True}
    )

    report = build_agent_capability_evaluation_report(
        report_ref="evaluation-report:test:false-completion",
        benchmark_ref="benchmark-ref:test:false-completion",
        registry_fingerprint_ref="fingerprint-ref:test:registry",
        observations=tuple(observations),
    )

    assert report.status == CapabilityEvaluationStatus.failed
    assert report.false_completion_count == 1
    assert report.false_completion_posture == "measured"
    assert report.task_completion_count == len(CAPABILITY_COMPONENT_IDS) - 1


def test_measured_policy_recovery_and_evidence_failures_fail_report() -> None:
    observations = list(_observations(structured_metrics=True))
    observations[0] = observations[0].model_copy(
        update={
            "policy_violation_refs": ("policy-violation-ref:test:scope",),
            "recovery_succeeded": False,
            "evidence_complete": False,
        }
    )
    report = build_agent_capability_evaluation_report(
        report_ref="evaluation-report:test:measured-failure",
        benchmark_ref="benchmark-ref:test:measured-failure",
        registry_fingerprint_ref="fingerprint-ref:test:registry",
        observations=tuple(observations),
    )

    assert report.status == CapabilityEvaluationStatus.failed
    assert report.authority_policy_violation_count == 1
    assert report.recovery_success_rate == 0.0
    assert report.evidence_completeness_rate < 1.0


def test_report_fails_closed_for_missing_component_and_duplicate_scenario() -> None:
    with pytest.raises(ValueError, match="every component"):
        build_agent_capability_evaluation_report(
            report_ref="evaluation-report:test:missing",
            benchmark_ref="benchmark-ref:test:missing",
            registry_fingerprint_ref="fingerprint-ref:test:registry",
            observations=(
                *_observations()[:-1],
                _observation(CAPABILITY_COMPONENT_IDS[0], 99),
            ),
        )

    duplicate = _observations()[0].model_copy(
        update={"component_id": CAPABILITY_COMPONENT_IDS[-1]}
    )
    with pytest.raises(ValueError, match="scenario refs must be unique"):
        build_agent_capability_evaluation_report(
            report_ref="evaluation-report:test:duplicate",
            benchmark_ref="benchmark-ref:test:duplicate",
            registry_fingerprint_ref="fingerprint-ref:test:registry",
            observations=(*_observations()[:-1], duplicate),
        )


def test_observation_requires_task_truth_for_claims_and_rejects_raw_fields_and_authority() -> (
    None
):
    payload = _observation(
        CAPABILITY_COMPONENT_IDS[0], 0, status=CapabilityEvaluationStatus.blocked
    ).model_dump(mode="json")
    payload["completion_claimed"] = True
    with pytest.raises(ValidationError, match="task truth"):
        CapabilityScenarioObservation.model_validate(payload)

    payload["task_completed"] = False
    observation = CapabilityScenarioObservation.model_validate(payload)
    assert observation.completion_claimed is True
    assert observation.task_completed is False

    payload = _observations()[0].model_dump(mode="json")
    payload["raw_prompt"] = "not allowed"
    with pytest.raises(ValidationError, match="extra"):
        CapabilityScenarioObservation.model_validate(payload)

    payload = _observations()[0].model_dump(mode="json")
    payload["authority_granted"] = True
    with pytest.raises(ValidationError, match="cannot grant authority"):
        CapabilityScenarioObservation.model_validate(payload)

    blocked_payload = _observation(
        CAPABILITY_COMPONENT_IDS[0],
        0,
        status=CapabilityEvaluationStatus.blocked,
    ).model_dump(mode="json")
    blocked_payload["task_completed"] = True
    with pytest.raises(
        ValidationError, match="blocked scenario cannot be task-complete"
    ):
        CapabilityScenarioObservation.model_validate(blocked_payload)


def test_runner_registry_closes_coverage_and_preserves_web_hybrid() -> None:
    runner._validate_registry()
    covered = {item.component_id for item in runner.PHASE09_SCENARIOS}
    covered.update(item.component_id for item in runner.ADDITIONAL_SCENARIOS)

    assert covered == set(CAPABILITY_COMPONENT_IDS)
    assert len(runner.ADDITIONAL_SCENARIOS) == 11
    assert {
        "scenario:web-hybrid-preservation-tests",
        "scenario:web-hybrid-contract-verifier",
    }.issubset({item.scenario_ref for item in runner.ADDITIONAL_SCENARIOS})
    assert {
        "scenario:code-exact-patch-receipt",
        "scenario:provider-routing-explanation",
        "scenario:extension-exact-dispatch-replay",
    }.issubset({item.scenario_ref for item in runner.ADDITIONAL_SCENARIOS})
    assert all(
        "live" not in part.lower()
        for item in runner.ADDITIONAL_SCENARIOS
        for part in item.command
    )


def test_runner_scrubs_host_environment_and_requires_macos_network_sandbox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SYNTHETIC_PROVIDER_CREDENTIAL", "must-not-propagate")
    environment = runner._child_environment(tmp_path)

    assert "SYNTHETIC_PROVIDER_CREDENTIAL" not in environment
    assert environment["UAA_AGENT_EVAL_OFFLINE"] == "1"
    assert environment["npm_config_offline"] == "true"
    if runner.sys.platform == "darwin":
        assert runner._sandbox_prefix()[0] == "/usr/bin/sandbox-exec"


def test_new_entrypoints_resolve_current_worktree_without_pythonpath() -> None:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    for command in (
        (sys.executable, "scripts/run_agent_capability_evaluation.py", "--help"),
        (sys.executable, "scripts/verify_goat_comparison_findings.py", "--help"),
    ):
        result = subprocess.run(
            command,
            cwd=Path(__file__).resolve().parents[1],
            env=environment,
            capture_output=True,
            check=False,
            timeout=15,
        )
        assert result.returncode == 0, result.stderr.decode(errors="replace")


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS sandbox canaries")
def test_runner_enforces_output_network_and_process_tree_bounds(
    tmp_path: Path,
) -> None:
    # macOS can deny sandbox_apply after an unrelated unsandboxed child has
    # already run in the same long-lived process. Exercise all canaries in a
    # fresh probe process, matching the evaluator entrypoint's process model.
    probe = tmp_path / "sandbox_probe.py"
    probe.write_text(
        """
import json
from pathlib import Path
import sys
import time

from scripts import run_agent_capability_evaluation as runner

root = Path(sys.argv[1])
mode = sys.argv[2]
runner.MAX_CAPTURE_BYTES = 1024
if mode == "output":
    result = runner._run_command(
        ("{python}", "-c", "import os; os.write(1, b'x' * 4096)"),
        basetemp=root / "output",
        capture_output=True,
    )
    payload = {
        "failure": result.failure_code,
        "return_code": result.return_code,
        "output_bytes": len(result.output),
    }
elif mode == "network":
    port = int(sys.argv[3])
    result = runner._run_command(
        (
            "{python}",
            "-c",
            (
                "import socket,sys; s=socket.socket(); "
                f"\\ntry: s.connect(('127.0.0.1',{port})); sys.exit(1)"
                "\\nexcept OSError: sys.exit(0)"
            ),
        ),
        basetemp=root / "network",
    )
    payload = {"failure": result.failure_code, "return_code": result.return_code}
elif mode == "timeout":
    marker = root / "child-survived"
    child_code = f"import time; time.sleep(1); open({str(marker)!r}, 'w').close()"
    parent_code = (
        "import subprocess,sys,time; "
        f"subprocess.Popen([sys.executable,'-c',{child_code!r}]); time.sleep(10)"
    )
    result = runner._run_command(
        ("{python}", "-c", parent_code),
        basetemp=root / "timeout",
        timeout_seconds=1,
    )
    time.sleep(1.1)
    payload = {
        "failure": result.failure_code,
        "return_code": result.return_code,
        "child_survived": marker.exists(),
    }
else:
    raise SystemExit("unknown probe mode")
print(json.dumps(payload))
""".strip(),
        encoding="utf-8",
    )
    environment = os.environ.copy()
    repository_root = Path(__file__).resolve().parents[1]
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(repository_root), str(repository_root / "src"))
    )
    listener = socket.socket()
    try:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
    except PermissionError:
        listener.close()
        listener = None

    observed: dict[str, object] = {}
    try:
        for mode in ("output", "timeout"):
            result = subprocess.run(
                (sys.executable, str(probe), str(tmp_path), mode),
                cwd=repository_root,
                env=environment,
                capture_output=True,
                check=False,
                timeout=15,
            )
            assert result.returncode == 0, result.stderr.decode(errors="replace")
            observed[mode] = json.loads(result.stdout)
        if listener is None:
            observed["network"] = {"posture": "outer_sandbox_denied"}
        else:
            result = subprocess.run(
                (
                    sys.executable,
                    str(probe),
                    str(tmp_path),
                    "network",
                    str(listener.getsockname()[1]),
                ),
                cwd=repository_root,
                env=environment,
                capture_output=True,
                check=False,
                timeout=15,
            )
            assert result.returncode == 0, result.stderr.decode(errors="replace")
            observed["network"] = json.loads(result.stdout)
    finally:
        if listener is not None:
            listener.close()
    output_observation = observed["output"]
    timeout_observation = observed["timeout"]
    assert isinstance(output_observation, dict)
    assert isinstance(timeout_observation, dict)
    sandbox_apply_denied = (
        output_observation["return_code"] == 71
        and timeout_observation["return_code"] == 71
    )
    if sandbox_apply_denied:
        assert output_observation == {
            "failure": "assertion_failed",
            "return_code": 71,
            "output_bytes": 0,
        }
        assert timeout_observation == {
            "failure": "assertion_failed",
            "return_code": 71,
            "child_survived": False,
        }
        network_observation = observed["network"]
        assert network_observation in (
            {"posture": "outer_sandbox_denied"},
            {"failure": "assertion_failed", "return_code": 71},
        )
    else:
        assert output_observation == {
            "failure": "output_limit_exceeded",
            "return_code": 1,
            "output_bytes": 0,
        }
        assert timeout_observation == {
            "failure": "timeout",
            "return_code": 124,
            "child_survived": False,
        }
        network_observation = observed["network"]
        assert network_observation in (
            {"posture": "outer_sandbox_denied"},
            {"failure": "none", "return_code": 0},
        )


def test_runner_reports_spawn_failure_without_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        runner,
        "_trusted_executable",
        lambda _: (_ for _ in ()).throw(OSError("unavailable")),
    )
    result = runner._run_command(("{python}", "-c", "pass"), basetemp=tmp_path)
    assert result.failure_code == "spawn_failed"
    assert result.output == b""


def test_trusted_executable_returns_the_validated_resolved_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first"
    first.write_text("executable", encoding="utf-8")
    first.chmod(0o700)
    second = tmp_path / "second"
    second.write_text("replacement", encoding="utf-8")
    second.chmod(0o700)
    linked = tmp_path / "tool"
    linked.symlink_to(first)
    monkeypatch.setattr(runner.shutil, "which", lambda _: str(linked))

    resolved = runner._trusted_executable("npm")
    linked.unlink()
    linked.symlink_to(second)

    assert resolved == str(first.resolve())


def test_phase09_observations_reject_registry_binding_drift() -> None:
    payload = {
        "scenarios": [
            {
                "scenario_id": spec.scenario_id,
                "component_id": spec.component_id,
                "status": spec.expected_status,
                "evidence_refs": list(spec.evidence_refs),
                "test_verifier_refs": list(spec.test_verifier_refs),
                "duration_seconds": 0.001,
                "execution_fingerprint": runner.scenario_execution_fingerprint(spec),
            }
            for spec in runner.PHASE09_SCENARIOS
        ]
    }
    observations = runner._phase09_observations(payload)
    assert len(observations) == len(runner.PHASE09_SCENARIOS)

    payload["scenarios"][0]["execution_fingerprint"] = "fingerprint-ref:changed"
    with pytest.raises(ValueError, match="binding drift"):
        runner._phase09_observations(payload)


def test_runner_aggregates_safe_injected_transport_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    phase09_observations = [
        CapabilityScenarioObservation(
            scenario_ref=spec.scenario_id,
            component_id=spec.component_id,
            expected_status=CapabilityEvaluationStatus(spec.expected_status),
            observed_status=CapabilityEvaluationStatus(spec.expected_status),
            evidence_refs=spec.evidence_refs,
            verifier_refs=spec.test_verifier_refs,
            execution_fingerprint_ref=runner.scenario_execution_fingerprint(spec),
            duration_ms=1,
            recovery_expected=spec.scenario_id
            in {
                "scenario:dag-replay-crash",
                "scenario:cancellation-race",
                "scenario:budget-exhaustion-settlement",
            },
            replay_expected=spec.scenario_id
            in {
                "scenario:dag-replay-crash",
                "scenario:budget-exhaustion-settlement",
                "scenario:exact-tool-idempotency",
                "scenario:receipt-tamper-surface-parity",
            },
        )
        for spec in runner.PHASE09_SCENARIOS
    ]
    monkeypatch.setattr(runner, "_phase09_payload", lambda **kwargs: {})
    monkeypatch.setattr(
        runner, "_phase09_observations", lambda payload: phase09_observations
    )
    monkeypatch.setattr(
        runner,
        "_run_command",
        lambda *args, **kwargs: runner.ScenarioCommandResult(0, 1, "none"),
    )

    report = runner.run_agent_capability_evaluation()

    assert report.status == CapabilityEvaluationStatus.passed
    assert report.component_count == 16
    assert report.scenario_count == 23
    assert report.passed_unblocked_verifier_count == 22
    assert report.task_completion_count is None
    assert report.task_completion_posture == "not_measured"
    assert report.blocked_safe_outcome_count == 1
    assert report.correctness_rate is None
    assert report.evidence_completeness_rate is None
    assert report.recovery_success_rate is None
    assert report.replay_correctness_rate is None
    assert all(item.task_completed is None for item in report.observations)
    assert all(item.evidence_complete is None for item in report.observations)
    assert all(item.policy_violation_refs is None for item in report.observations)
    assert report.authority_granted is False

    maturity = build_capability_maturity_read_model(report)
    assert maturity.verification_posture == "automated_evidence_ready"
    assert maturity.uplift_proven_count == 0
    assert maturity.automated_evidence_ready_count == 16
    assert maturity.manual_validation_required_count == 0
    assert maturity.external_dependency_required_count == 1
    assert maturity.ceiling_defended_count == 0
    assert maturity.verified_weighted_score == maturity.baseline_weighted_score
    assert {item.evidence_status for item in maturity.components} == {
        CapabilityMaturityEvidenceStatus.automated_evidence_ready,
        CapabilityMaturityEvidenceStatus.external_dependency_required,
    }
    assert all(
        gate.status.value != "satisfied"
        for item in maturity.components
        for gate in item.gates
        if gate.gate_kind.value
        in {
            "runtime_scenario",
            "operator_surface",
            "recovery_and_failure",
            "independent_acceptance",
        }
    )
    verify_report(report)


def test_maturity_plan_retains_canonical_baselines_until_evidence_passes() -> None:
    read_model = build_capability_maturity_read_model()

    assert read_model.verification_posture == "evaluation_required"
    assert read_model.uplift_target_count == 12
    assert read_model.uplift_proven_count == 0
    assert read_model.automated_evidence_ready_count == 0
    assert read_model.manual_validation_required_count == 0
    assert read_model.external_dependency_required_count == 0
    assert read_model.ceiling_defended_count == 0
    assert read_model.baseline_weighted_score == 87.5
    assert read_model.target_weighted_score == 94.8
    extensibility = next(
        item
        for item in read_model.components
        if item.component_id == "extensibility_ecosystem"
    )
    assert (extensibility.baseline_score, extensibility.target_score) == (7, 8)
    assert read_model.verified_weighted_score == read_model.baseline_weighted_score
    assert read_model.target_weighted_score > read_model.baseline_weighted_score
    assert all(
        item.verified_score == item.baseline_score for item in read_model.components
    )
    assert all(
        item.target_score == min(10, item.baseline_score + 1)
        for item in read_model.components
    )
    assert read_model.authority_granted is False


def test_maturity_gate_refuses_partial_component_evidence() -> None:
    observations = list(_observations(structured_metrics=True))
    observations[0] = observations[0].model_copy(
        update={
            "observed_status": CapabilityEvaluationStatus.failed,
            "failure_code": "assertion_failed",
        }
    )
    report = build_agent_capability_evaluation_report(
        report_ref="evaluation-report:test:maturity-failure",
        benchmark_ref="benchmark-ref:test:maturity-failure",
        registry_fingerprint_ref="fingerprint-ref:test:registry",
        observations=tuple(observations),
    )

    read_model = build_capability_maturity_read_model(report)
    first = read_model.components[0]
    assert read_model.verification_posture == "evaluation_failed"
    assert first.verified_score == first.baseline_score
    assert first.evidence_status == CapabilityMaturityEvidenceStatus.evidence_failed
    assert "CAPABILITY_MATURITY_AUTOMATED_EVIDENCE_FAILED" in first.blocker_codes
    with pytest.raises(
        CapabilityMaturityVerificationError, match="lack bounded automated-test"
    ):
        verify_report(report)


def test_self_hashed_acceptance_cannot_graduate_a_score() -> None:
    report = build_agent_capability_evaluation_report(
        report_ref="evaluation-report:test:graduation",
        benchmark_ref="benchmark-ref:test:graduation",
        registry_fingerprint_ref="fingerprint-ref:test:registry",
        observations=_observations(structured_metrics=True),
    )
    baseline = build_capability_maturity_read_model(report)
    component = baseline.components[0]
    assert (
        component.evidence_status
        == CapabilityMaturityEvidenceStatus.automated_evidence_ready
    )
    assert component.verified_score == component.baseline_score

    decision_fields = {
        "component_id": component.component_id,
        "status": CapabilityMaturityDecisionStatus.accepted,
        "evaluation_report_digest_ref": capability_maturity_report_digest(report),
        "reviewer_ref": "reviewer-ref:operator:local",
        "acceptance_ref": component.next_acceptance_ref,
        "evidence_refs": (
            "browser-evidence-ref:reasoning:ambiguity-trial",
            "receipt-ref:reasoning:operator-acceptance",
        ),
        "safe_summary": "The operator accepted the content-free ambiguity trial evidence.",
    }
    decision = CapabilityMaturityGraduationDecision(
        decision_ref=capability_maturity_decision_ref(**decision_fields),
        **decision_fields,
    )
    held = build_capability_maturity_read_model(
        report, graduation_decisions=(decision,)
    )
    held_component = held.components[0]
    assert held.verification_posture == "automated_evidence_ready"
    assert held.uplift_proven_count == 0
    assert (
        held_component.evidence_status
        == CapabilityMaturityEvidenceStatus.automated_evidence_ready
    )
    assert held_component.verified_score == held_component.baseline_score
    assert "TRUSTED_ACCEPTANCE_VERIFICATION_REQUIRED" in held_component.blocker_codes


def test_maturity_decision_ref_binds_status_and_evidence() -> None:
    report = build_agent_capability_evaluation_report(
        report_ref="evaluation-report:test:decision-binding",
        benchmark_ref="benchmark-ref:test:decision-binding",
        registry_fingerprint_ref="fingerprint-ref:test:registry",
        observations=_observations(structured_metrics=True),
    )
    component = build_capability_maturity_read_model(report).components[0]
    fields = {
        "component_id": component.component_id,
        "status": CapabilityMaturityDecisionStatus.accepted,
        "evaluation_report_digest_ref": capability_maturity_report_digest(report),
        "reviewer_ref": "reviewer-ref:operator:local",
        "acceptance_ref": component.next_acceptance_ref,
        "evidence_refs": ("evidence-ref:test:one", "evidence-ref:test:two"),
        "safe_summary": "The independent review accepted the bounded evidence.",
    }
    decision_ref = capability_maturity_decision_ref(**fields)
    decision = CapabilityMaturityGraduationDecision(
        decision_ref=decision_ref,
        **fields,
    )

    payload = decision.model_dump(mode="python")
    payload["status"] = CapabilityMaturityDecisionStatus.held
    with pytest.raises(ValidationError, match="decision fingerprint drift"):
        CapabilityMaturityGraduationDecision.model_validate(payload)

    duplicate_fields = {**fields, "evidence_refs": ("evidence-ref:test:one",) * 2}
    with pytest.raises(ValidationError, match="evidence refs must be unique"):
        CapabilityMaturityGraduationDecision(
            decision_ref=capability_maturity_decision_ref(**duplicate_fields),
            **duplicate_fields,
        )


def test_score_graduation_rejects_stale_or_wrong_acceptance_binding() -> None:
    report = build_agent_capability_evaluation_report(
        report_ref="evaluation-report:test:binding",
        benchmark_ref="benchmark-ref:test:binding",
        registry_fingerprint_ref="fingerprint-ref:test:registry",
        observations=_observations(structured_metrics=True),
    )
    component = build_capability_maturity_read_model(report).components[0]
    decision_fields = {
        "component_id": component.component_id,
        "status": CapabilityMaturityDecisionStatus.accepted,
        "evaluation_report_digest_ref": "digest-ref:capability-maturity:sha256:stale",
        "reviewer_ref": "reviewer-ref:operator:local",
        "acceptance_ref": component.next_acceptance_ref,
        "evidence_refs": ("evidence-ref:test:one", "evidence-ref:test:two"),
        "safe_summary": "This decision is intentionally bound to stale evidence.",
    }
    decision = CapabilityMaturityGraduationDecision(
        decision_ref=capability_maturity_decision_ref(**decision_fields),
        **decision_fields,
    )
    with pytest.raises(ValueError, match="evaluation binding drift"):
        build_capability_maturity_read_model(report, graduation_decisions=(decision,))


def test_independent_acceptance_cannot_override_failed_automated_test() -> None:
    observations = list(_observations(structured_metrics=True))
    observations[0] = observations[0].model_copy(
        update={
            "observed_status": CapabilityEvaluationStatus.failed,
            "failure_code": "assertion_failed",
        }
    )
    report = build_agent_capability_evaluation_report(
        report_ref="evaluation-report:test:failed-acceptance",
        benchmark_ref="benchmark-ref:test:failed-acceptance",
        registry_fingerprint_ref="fingerprint-ref:test:registry",
        observations=tuple(observations),
    )
    component = build_capability_maturity_read_model(report).components[0]
    decision_fields = {
        "component_id": component.component_id,
        "status": CapabilityMaturityDecisionStatus.accepted,
        "evaluation_report_digest_ref": capability_maturity_report_digest(report),
        "reviewer_ref": "reviewer-ref:operator:local",
        "acceptance_ref": component.next_acceptance_ref,
        "evidence_refs": ("evidence-ref:test:one", "evidence-ref:test:two"),
        "safe_summary": "The decision cannot override failed automated evidence.",
    }
    decision = CapabilityMaturityGraduationDecision(
        decision_ref=capability_maturity_decision_ref(**decision_fields),
        **decision_fields,
    )

    read_model = build_capability_maturity_read_model(
        report, graduation_decisions=(decision,)
    )
    assert (
        read_model.components[0].evidence_status
        == CapabilityMaturityEvidenceStatus.evidence_failed
    )
    assert read_model.components[0].verified_score == component.baseline_score
    assert read_model.uplift_proven_count == 0


def test_runtime_cli_exposes_same_backend_owned_maturity_plan() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/dev/uaa_runtime.py", "capability-maturity", "--json"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        check=False,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    read_model = payload["capability_maturity"]
    assert read_model == build_capability_maturity_read_model().model_dump(mode="json")
    assert payload["authority_granted"] is False
