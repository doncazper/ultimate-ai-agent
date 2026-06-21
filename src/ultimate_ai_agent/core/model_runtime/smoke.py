from typing import Protocol

from ultimate_ai_agent.core.approvals import (
    ApprovalDecisionStatus,
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    ApprovalValidationDecision,
    ApprovalValidationRequest,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.model_runtime.smoke_policy import (
    DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT,
    SMOKE_ACTION,
    ManualLoopbackSmokeRequest,
    ManualLoopbackSmokeResult,
    smoke_endpoint_reason_codes,
)


class ManualLoopbackSmokeTransport(Protocol):
    def send_smoke(
        self,
        request: ManualLoopbackSmokeRequest,
        approval_decision: ApprovalValidationDecision | None = None,
    ) -> ManualLoopbackSmokeResult:
        ...


class FakeManualLoopbackSmokeTransport:
    def __init__(self, response_text: str = "UAA_LOCAL_SMOKE_OK", elapsed_ms: int = 3) -> None:
        self.response_text = response_text
        self.elapsed_ms = elapsed_ms

    def send_smoke(
        self,
        request: ManualLoopbackSmokeRequest,
        approval_decision: ApprovalValidationDecision | None = None,
    ) -> ManualLoopbackSmokeResult:
        decision = validate_manual_loopback_smoke_request(request, approval_decision)
        if not decision.allowed:
            return decision
        if contains_secret_like(self.response_text):
            return _result(
                request,
                allowed=False,
                success=False,
                status="blocked",
                reason_codes=["SMOKE_RESPONSE_SECRET_BLOCKED"],
                safe_message="Manual local loopback smoke response was blocked by secret hygiene.",
                response_preview=None,
                response_origin="fake_manual_loopback_smoke",
                elapsed_ms=self.elapsed_ms,
                redactions_applied=["response_preview"],
            )
        if request.expected_marker and request.expected_marker not in self.response_text:
            return _result(
                request,
                allowed=True,
                success=False,
                status="failed",
                reason_codes=["EXPECTED_MARKER_MISSING"],
                safe_message="Manual local loopback smoke response did not contain the expected marker.",
                response_preview=_safe_preview(self.response_text, request.policy.max_response_bytes),
                response_origin="fake_manual_loopback_smoke",
                elapsed_ms=self.elapsed_ms,
            )
        return _result(
            request,
            allowed=True,
            success=True,
            status="smoke_passed",
            reason_codes=["SMOKE_OK"],
            safe_message="Manual local loopback smoke completed; model output is not authoritative evidence.",
            response_preview=_safe_preview(self.response_text, request.policy.max_response_bytes),
            response_origin="fake_manual_loopback_smoke",
            elapsed_ms=self.elapsed_ms,
        )


def smoke_approval_request(request: ManualLoopbackSmokeRequest) -> ApprovalRequest:
    return ApprovalRequest(
        approval_request_id=f"areq_{request.smoke_request_id}",
        run_id=request.run_id,
        subject_type=ApprovalSubjectType.model_runtime_request,
        subject_id=request.smoke_request_id,
        actor_context=request.actor_context,
        requested_action=SMOKE_ACTION,
        purpose="Approve manual local loopback smoke test with fixed non-sensitive prompt.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=request.data_classification,
        resource_refs=[request.endpoint.endpoint_id, request.model_id],
        event_ref=request.event_ref if hasattr(request, "event_ref") else None,
        trace_id=request.smoke_request_id,
    )


def smoke_approval_validation_request(request: ManualLoopbackSmokeRequest) -> ApprovalValidationRequest:
    return smoke_approval_request(request).to_validation_request(request.approval_ref or "")


def validate_manual_loopback_smoke_request(
    request: ManualLoopbackSmokeRequest,
    approval_decision: ApprovalValidationDecision | None = None,
) -> ManualLoopbackSmokeResult:
    reasons: list[str] = []
    if not request.policy.enable_manual_smoke:
        reasons.append("MANUAL_SMOKE_DISABLED")
    if request.fixed_prompt != DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT:
        reasons.append("SMOKE_PROMPT_MUST_MATCH_FIXED_PROMPT")
    reasons.extend(smoke_endpoint_reason_codes(request.endpoint, request.policy))

    if request.policy.require_approval:
        reasons.extend(_approval_reasons(request, approval_decision))

    if reasons:
        return _result(
            request,
            allowed=False,
            success=False,
            status="blocked",
            reason_codes=sorted(set(reasons)),
            safe_message="Manual local loopback smoke is blocked by local/dev policy.",
            response_preview=None,
            response_origin="local_loopback_smoke_validation",
        )
    return _result(
        request,
        allowed=True,
        success=False,
        status="allowed",
        reason_codes=["MANUAL_LOOPBACK_SMOKE_ALLOWED", "APPROVAL_VALIDATED"],
        safe_message="Manual local loopback smoke is allowed by local/dev policy.",
        response_preview=None,
        response_origin="local_loopback_smoke_validation",
    )


def _approval_reasons(
    request: ManualLoopbackSmokeRequest,
    approval_decision: ApprovalValidationDecision | None,
) -> list[str]:
    if not request.approval_ref:
        return ["APPROVAL_REQUIRED"]
    if approval_decision is None:
        return ["APPROVAL_DECISION_REQUIRED"]
    if approval_decision.approval_ref != request.approval_ref:
        return ["APPROVAL_REF_MISMATCH"]
    if not approval_decision.allowed:
        return approval_decision.reason_codes or ["APPROVAL_NOT_ALLOWED"]
    if approval_decision.status != ApprovalDecisionStatus.approved:
        return approval_decision.reason_codes or ["APPROVAL_NOT_APPROVED"]
    if approval_decision.matched_grant_ref != request.approval_ref:
        return ["APPROVAL_MATCHED_GRANT_REQUIRED"]
    if "APPROVAL_VALIDATED" not in approval_decision.reason_codes:
        return ["APPROVAL_VALIDATION_EVIDENCE_REQUIRED"]
    return []


def _result(
    request: ManualLoopbackSmokeRequest,
    *,
    allowed: bool,
    success: bool,
    status: str,
    reason_codes: list[str],
    safe_message: str,
    response_preview: str | None,
    response_origin: str,
    elapsed_ms: int | None = None,
    redactions_applied: list[str] | None = None,
) -> ManualLoopbackSmokeResult:
    return ManualLoopbackSmokeResult(
        smoke_request_id=request.smoke_request_id,
        allowed=allowed,
        success=success,
        status=status,
        reason_codes=reason_codes,
        safe_message=safe_message,
        response_preview=response_preview,
        response_origin=response_origin,
        elapsed_ms=elapsed_ms,
        redactions_applied=redactions_applied or [],
        metadata={
            "truth_authority": False,
            "runtime_boundary": "local_loopback_smoke",
            "manual_only": True,
            "fixed_prompt_used": True,
            "prompt_content_omitted": True,
        },
    )


def _safe_preview(value: str, max_bytes: int) -> str:
    encoded = value.encode("utf-8")[:max_bytes]
    return encoded.decode("utf-8", errors="replace")
