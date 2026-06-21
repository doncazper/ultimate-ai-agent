import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.model_runtime import (
    LocalRuntimeHealthProbePlan,
    validate_local_runtime_health_probe_plan,
)


def test_health_probe_plan_is_plan_only_by_default() -> None:
    plan = LocalRuntimeHealthProbePlan(
        plan_ref="local_runtime_health_plan_demo",
        safe_summary="future metadata-only health plan",
    )

    assert validate_local_runtime_health_probe_plan(plan) is plan
    assert plan.probe_allowed_now is False
    assert plan.probe_performed is False
    assert plan.network_call_performed is False
    assert plan.command_executed is False
    assert plan.user_content_sent is False


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("probe_allowed_now", "probe"),
        ("probe_performed", "probe"),
        ("network_call_performed", "network"),
        ("command_executed", "command"),
        ("user_content_sent", "user content"),
    ],
)
def test_health_probe_plan_rejects_probe_or_execution_flags(field: str, message: str) -> None:
    plan = LocalRuntimeHealthProbePlan(
        plan_ref="local_runtime_health_plan_demo",
        safe_summary="future metadata-only health plan",
        **{field: True},
    )

    with pytest.raises(ValueError, match=message):
        validate_local_runtime_health_probe_plan(plan)


def test_health_probe_plan_forbids_raw_output_field() -> None:
    with pytest.raises(ValidationError):
        LocalRuntimeHealthProbePlan(
            plan_ref="local_runtime_health_plan_demo",
            safe_summary="future metadata-only health plan",
            raw_health_payload="not allowed",
        )
