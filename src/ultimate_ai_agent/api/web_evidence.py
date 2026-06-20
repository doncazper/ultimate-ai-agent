from __future__ import annotations

from fastapi import APIRouter, FastAPI
from pydantic import ValidationError

from ultimate_ai_agent.core.hygiene.envelopes import ErrorCategory, ErrorEnvelope, ResultEnvelope, Severity
from ultimate_ai_agent.core.network.governed_web_evidence import (
    GovernedWebEvidenceRequest,
    build_governed_web_evidence_status,
    fetch_governed_web_evidence,
    governed_web_evidence_policy_from_env,
)


router = APIRouter(prefix="/web-evidence", tags=["web-evidence"])
_REGISTERED_ATTR = "_uaa_governed_web_evidence_routes_registered"


@router.get("/status", response_model=ResultEnvelope)
def get_governed_web_evidence_status() -> ResultEnvelope:
    status = build_governed_web_evidence_status()
    return ResultEnvelope(
        success=True,
        operation="governed_web_evidence_status",
        service="GovernedWebEvidenceAPI",
        trace_id=status.capability_ref,
        data=status.model_dump(mode="json"),
        redactions_applied=["safe_refs_only", "raw_page_omitted"],
    )


@router.post("/request", response_model=ResultEnvelope)
def post_governed_web_evidence_request(request: GovernedWebEvidenceRequest) -> ResultEnvelope:
    try:
        policy = governed_web_evidence_policy_from_env()
        result = fetch_governed_web_evidence(request, policy=policy)
    except (ValidationError, ValueError):
        return _error_envelope(
            request_ref=getattr(request, "request_ref", "web-evidence-request:blocked"),
            run_id=getattr(request, "run_id", "web-evidence-run:local"),
            code="GOVERNED_WEB_EVIDENCE_REQUEST_REJECTED",
        )
    if not result.allowed:
        return ResultEnvelope(
            success=False,
            operation="governed_web_evidence_request",
            service="GovernedWebEvidenceAPI",
            run_id=result.run_id,
            trace_id=result.request_ref,
            data=result.model_dump(mode="json"),
            error=ErrorEnvelope(
                code=result.reason_codes[0] if result.reason_codes else "GOVERNED_WEB_EVIDENCE_BLOCKED",
                category=ErrorCategory.security_blocked,
                safe_message="Governed web evidence request was blocked safely.",
                severity=Severity.medium,
                retryable=False,
                details_redacted=True,
                source="GovernedWebEvidenceAPI",
                metadata={"reason_codes": result.reason_codes},
            ),
            redactions_applied=["raw_page_omitted", "raw_headers_omitted", "safe_refs_only"],
        )
    return ResultEnvelope(
        success=True,
        operation="governed_web_evidence_request",
        service="GovernedWebEvidenceAPI",
        run_id=result.run_id,
        trace_id=result.request_ref,
        data=result.model_dump(mode="json"),
        redactions_applied=["raw_page_omitted", "raw_headers_omitted", "safe_refs_only"],
    )


def register_governed_web_evidence_routes(app: FastAPI) -> None:
    if getattr(app.state, _REGISTERED_ATTR, False):
        return
    registered_paths = {getattr(route, "path", None) for route in app.router.routes}
    for route in router.routes:
        if getattr(route, "path", None) not in registered_paths:
            app.router.routes.append(route)
    setattr(app.state, _REGISTERED_ATTR, True)


def _error_envelope(*, request_ref: str, run_id: str, code: str) -> ResultEnvelope:
    return ResultEnvelope(
        success=False,
        operation="governed_web_evidence_request",
        service="GovernedWebEvidenceAPI",
        run_id=run_id,
        trace_id=request_ref,
        error=ErrorEnvelope(
            code=code,
            category=ErrorCategory.validation_error,
            safe_message="Governed web evidence request was rejected safely.",
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="GovernedWebEvidenceAPI",
        ),
        redactions_applied=["raw_page_omitted", "raw_headers_omitted", "safe_refs_only"],
    )
