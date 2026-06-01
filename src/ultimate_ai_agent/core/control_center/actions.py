from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.control_center.enums import (
    ControlCenterActionDecisionStatus,
    ControlCenterActionKind,
    ControlCenterRiskLevel,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.time import utc_now


class ControlCenterActionPreviewRequest(BaseModel):
    request_id: str = Field(..., min_length=1)
    actor_context: dict[str, Any]
    action_kind: ControlCenterActionKind
    target_ref: str = Field(..., min_length=1, max_length=256)
    purpose: str = Field(..., min_length=1, max_length=256)
    risk_level: ControlCenterRiskLevel
    data_classification: str = Field(..., min_length=1)
    approval_ref: str | None = None
    consent_refs: list[str] = Field(default_factory=list)
    idempotency_key: str | None = None
    created_at: str = Field(default_factory=lambda: utc_now().replace(microsecond=0).isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class ControlCenterActionPreviewDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: f"control_center_preview_{utc_now().timestamp():.0f}")
    request_id: str = Field(..., min_length=1)
    allowed: bool
    status: ControlCenterActionDecisionStatus
    reason_codes: list[str]
    safe_message: str
    required_next_action: str | None = None
    preview_summary: str = "Preview only; no action was executed."
    event_ref: str | None = None
    created_at: str = Field(default_factory=lambda: utc_now().replace(microsecond=0).isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


def preview_control_center_action(
    request: ControlCenterActionPreviewRequest | Mapping[str, Any],
) -> ControlCenterActionPreviewDecision:
    parsed = request if isinstance(request, ControlCenterActionPreviewRequest) else ControlCenterActionPreviewRequest(**dict(request))
    payload = parsed.model_dump(mode="json")
    reasons: list[str] = []
    redactions: list[str] = []
    text = _flatten_text(payload).lower()
    target = parsed.target_ref.lower()

    if contains_secret_like(payload):
        reasons.append("SECRET_LIKE_VALUE_REJECTED")
        redactions.append("unsafe_values")
    if parsed.action_kind == ControlCenterActionKind.disabled_execute.value:
        reasons.append("EXECUTION_ACTION_BLOCKED")
    if any(marker in target or marker in text for marker in ["runtime/execute", "runtime/run", "model-runtime/execute"]):
        reasons.append("RUNTIME_EXECUTION_BLOCKED")
    if any(marker in text for marker in ["provider invocation", "provider call", "model execution", "model call"]):
        reasons.append("MODEL_OR_PROVIDER_EXECUTION_BLOCKED")
    if any(marker in target or marker in text for marker in ["remote-workers/dispatch", "remote dispatch", "remote execution"]):
        reasons.append("REMOTE_EXECUTION_BLOCKED")
    if any(marker in target or marker in text for marker in ["plugins/enable", "plugin enable", "plugin enabled"]):
        reasons.append("PLUGIN_ENABLEMENT_BLOCKED")
    if any(marker in target or marker in text for marker in ["mobile/sensors", "sensor enabled", "camera", "microphone", "location sensor"]):
        reasons.append("MOBILE_SENSOR_BLOCKED")
    if any(marker in text for marker in ["credential use", "use credential", "secret access", "api key"]):
        reasons.append("CREDENTIAL_USE_BLOCKED")
    if any(marker in text for marker in ["mutate file", "write file", "delete file", "external action"]):
        reasons.append("MUTATION_BLOCKED")
    if parsed.approval_ref:
        reasons.append("ARBITRARY_APPROVAL_REF_NOT_AUTHORITY")

    deduped = _dedupe(reasons)
    if deduped:
        return ControlCenterActionPreviewDecision(
            request_id=parsed.request_id,
            allowed=False,
            status=ControlCenterActionDecisionStatus.blocked,
            reason_codes=deduped,
            safe_message="Control Center preview was blocked by read-only policy.",
            metadata={"redactions_applied": _dedupe(redactions), "executed": False},
        )
    if parsed.risk_level in {ControlCenterRiskLevel.high.value, ControlCenterRiskLevel.critical.value}:
        return ControlCenterActionPreviewDecision(
            request_id=parsed.request_id,
            allowed=False,
            status=ControlCenterActionDecisionStatus.approval_required,
            reason_codes=["APPROVAL_REQUIRED_FOR_HIGH_RISK_PREVIEW"],
            safe_message="High-risk previews require explicit approval before future execution-capable milestones.",
            required_next_action="request_approval_for_future_milestone",
            metadata={"executed": False},
        )
    return ControlCenterActionPreviewDecision(
        request_id=parsed.request_id,
        allowed=True,
        status=ControlCenterActionDecisionStatus.allowed_preview,
        reason_codes=["CONTROL_CENTER_PREVIEW_ALLOWED"],
        safe_message="Control Center preview is allowed. No action was executed.",
        metadata={"executed": False},
    )


def _flatten_text(value: Any) -> str:
    if isinstance(value, Mapping):
        return " ".join(f"{key} {_flatten_text(item)}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    return str(value)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output
