from typing import Any
import pytest

from ultimate_ai_agent.core.evals import (
    AgentEvalCase,
    AgentEvalCaseObservation,
    AgentEvalHarnessPolicy,
    AgentEvalRegressionRunRequest,
    AgentEvalRegressionStatus,
    AgentEvalSuite,
    build_agent_eval_regression_report,
    validate_agent_eval_harness_policy,
    validate_agent_eval_regression_request,
)


def _case(**overrides: Any) -> Any:
    data = {
        "case_ref": "eval-case:m56-safe-context",
        "suite_ref": "eval-suite:m56-regression",
        "scenario_ref": "scenario:m56-safe-context-proposal",
        "expected_outcome_ref": "outcome:review-only-context-proposal",
        "redacted_input_summary": "Redacted review packet should produce proposal-only output.",
        "invariant_refs": [
            "invariant:no-model-call",
            "invariant:no-tool-execution",
            "invariant:no-context-injection",
        ],
        "evidence_refs": ["evidence:m56-reviewed-contract"],
    }
    data.update(overrides)
    return AgentEvalCase(**data)


def _suite(*cases: AgentEvalCase, **overrides: Any) -> Any:
    data = {
        "suite_ref": "eval-suite:m56-regression",
        "baseline_ref": "baseline:v0.59.0",
        "case_refs": [case.case_ref for case in cases] or ["eval-case:m56-safe-context"],
        "cases": list(cases) or [_case()],
        "deterministic_seed_ref": "seed:m56-static",
    }
    data.update(overrides)
    return AgentEvalSuite(**data)


def _request(**overrides: Any) -> Any:
    data = {
        "request_ref": "eval-request:m56-regression",
        "run_ref": "eval-run:m56-regression",
        "suite_ref": "eval-suite:m56-regression",
        "case_refs": ["eval-case:m56-safe-context"],
        "baseline_ref": "baseline:v0.59.0",
    }
    data.update(overrides)
    return AgentEvalRegressionRunRequest(**data)


def _observation(**overrides: Any) -> Any:
    data = {
        "case_ref": "eval-case:m56-safe-context",
        "observed_outcome_ref": "outcome:review-only-context-proposal",
        "safe_observation_summary": "Observed proposal-only behavior from explicit safe evidence refs.",
        "evidence_refs": ["evidence:m56-observed-contract"],
    }
    data.update(overrides)
    return AgentEvalCaseObservation(**data)


def test_agent_eval_regression_report_is_deterministic_and_no_effect() -> None:
    report = build_agent_eval_regression_report(
        _request(),
        _suite(_case()),
        [_observation()],
    )

    assert report.status == AgentEvalRegressionStatus.passed
    assert report.total_cases == 1
    assert report.passed_cases == 1
    assert report.failed_cases == 0
    assert report.receipt_plan is not None
    assert report.receipt_plan.evaluation_performed is False
    assert report.receipt_plan.side_effects_performed == []
    assert report.model_call_performed is False
    assert report.tool_execution_performed is False
    assert report.network_call_performed is False
    assert report.memory_write_performed is False
    assert report.context_injection_performed is False
    assert report.results[0].reason_codes == ["M56_EXPECTED_OUTCOME_MATCHED"]
    assert "raw prompt body" not in str(report.model_dump())


def test_agent_eval_regression_report_marks_mismatch_as_regression_without_execution() -> None:
    report = build_agent_eval_regression_report(
        _request(),
        _suite(_case()),
        [_observation(observed_outcome_ref="outcome:unexpected-authority")],
    )

    assert report.status == AgentEvalRegressionStatus.failed
    assert report.passed_cases == 0
    assert report.failed_cases == 1
    assert report.results[0].reason_codes == ["M56_EXPECTED_OUTCOME_MISMATCH"]
    assert report.receipt_plan is not None
    assert report.receipt_plan.evaluation_performed is False


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("model_call_requested", "MODEL_CALL_DENIED"),
        ("provider_call_requested", "PROVIDER_CALL_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
        ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
        ("network_access_requested", "NETWORK_ACCESS_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("raw_prompt_capture_requested", "RAW_PROMPT_CAPTURE_DENIED"),
        ("raw_provider_payload_capture_requested", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
    ],
)
def test_agent_eval_regression_request_denies_execution_and_raw_capture_flags(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_agent_eval_regression_request(_request(**{field: True}))


def test_agent_eval_regression_revalidates_model_copy_mutated_request() -> None:
    request = _request().model_copy(
        update={
            "model_call_requested": True,
            "contains_raw_prompt": True,
        }
    )

    with pytest.raises(ValueError, match="MODEL_CALL_DENIED"):
        build_agent_eval_regression_report(request, _suite(_case()), [_observation()])


def test_agent_eval_regression_denies_duplicate_and_missing_bindings() -> None:
    duplicate_suite = _suite(
        _case(),
        _case(scenario_ref="scenario:m56-duplicate"),
        case_refs=["eval-case:m56-safe-context", "eval-case:m56-safe-context"],
    )
    with pytest.raises(ValueError, match="EVAL_CASE_REF_DUPLICATE"):
        build_agent_eval_regression_report(_request(), duplicate_suite, [_observation()])

    with pytest.raises(ValueError, match="EVAL_OBSERVATION_MISSING"):
        build_agent_eval_regression_report(_request(), _suite(_case()), [])


def test_agent_eval_regression_denies_secret_like_case_content() -> None:
    unsafe_case = _case(redacted_input_summary="api_key='abcde12345678901234'")

    with pytest.raises(ValueError, match="SECRET_LIKE_EVAL_CONTENT_DENIED"):
        build_agent_eval_regression_report(_request(), _suite(unsafe_case), [_observation()])


def test_agent_eval_harness_policy_denies_runtime_authority_flags() -> None:
    policy = AgentEvalHarnessPolicy(
        model_call_enabled=True,
        tool_execution_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="MODEL_CALL_DENIED"):
        validate_agent_eval_harness_policy(policy)
