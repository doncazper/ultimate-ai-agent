from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.model_runtime.enums import LocalModelRuntimeStatus
from ultimate_ai_agent.core.model_runtime.redaction import assert_secret_clean


class _LocalRuntimeHealthPlanModel(BaseModel):
    model_config = ConfigDict(use_enum_values=False, extra="forbid", protected_namespaces=())


class LocalRuntimeHealthProbePlan(_LocalRuntimeHealthPlanModel):
    plan_ref: str = Field(..., min_length=1)
    status: LocalModelRuntimeStatus = LocalModelRuntimeStatus.planned_disabled
    safe_summary: str = Field(..., min_length=1)
    probe_allowed_now: bool = False
    probe_performed: bool = False
    network_call_performed: bool = False
    command_executed: bool = False
    user_content_sent: bool = False
    no_model_called: bool = True
    no_endpoint_contacted: bool = True
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def validate_local_runtime_health_probe_plan(plan: LocalRuntimeHealthProbePlan) -> LocalRuntimeHealthProbePlan:
    assert_secret_clean(plan.plan_ref, field_name="plan_ref")
    assert_secret_clean(plan.safe_summary, field_name="safe_summary")
    for value in plan.metadata_refs:
        assert_secret_clean(value, field_name="metadata_refs")
    _assert_safe_metadata(plan.metadata)
    if plan.status != LocalModelRuntimeStatus.planned_disabled:
        raise ValueError("local runtime health plan must remain planned-disabled")
    if plan.probe_allowed_now:
        raise ValueError("local runtime health probe is not allowed now in M22")
    if plan.probe_performed:
        raise ValueError("local runtime health probe must not be performed in M22")
    if plan.network_call_performed:
        raise ValueError("local runtime health plan must not perform network calls")
    if plan.command_executed:
        raise ValueError("local runtime health plan must not execute commands")
    if plan.user_content_sent:
        raise ValueError("local runtime health plan must not send user content")
    if not plan.no_model_called:
        raise ValueError("local runtime health plan must record that no model was called")
    if not plan.no_endpoint_contacted:
        raise ValueError("local runtime health plan must record that no endpoint was contacted")
    return plan


def _assert_safe_metadata(metadata: dict[str, Any]) -> None:
    for key, value in metadata.items():
        if _is_secret_metadata_key(str(key)):
            raise ValueError("metadata contains secret-like content.")
        assert_secret_clean(str(key), field_name="metadata")
        if isinstance(value, dict):
            _assert_safe_metadata(value)
        elif isinstance(value, list):
            for item in value:
                assert_secret_clean(str(item), field_name="metadata")
        else:
            assert_secret_clean(str(value), field_name="metadata")


def _is_secret_metadata_key(key: str) -> bool:
    lowered = key.lower()
    return any(
        fragment in lowered
        for fragment in [
            "secret",
            "credential",
            "password",
            "authorization",
            "access_" + "token",
            "refresh_" + "token",
            "admin_" + "token",
            "session_" + "token",
            "api_" + "key",
        ]
    )
