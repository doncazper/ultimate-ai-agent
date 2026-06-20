from __future__ import annotations

from fastapi import APIRouter, FastAPI, Header, HTTPException, Query
from pydantic import ValidationError

from ultimate_ai_agent.core.hygiene.envelopes import ErrorCategory, ErrorEnvelope, ResultEnvelope, Severity
from ultimate_ai_agent.core.mattermost import (
    MattermostBridgeService,
    MattermostMessageEvent,
    MattermostRoleBindRequest,
    MattermostRoleSuggestionRequest,
    MattermostRoleUnbindRequest,
    mattermost_bridge_authority_error,
)

router = APIRouter(prefix="/integrations/mattermost", tags=["mattermost"])
_REGISTERED_ATTR = "_uaa_mattermost_routes_registered"


@router.get("/status", response_model=ResultEnvelope)
def get_mattermost_status() -> ResultEnvelope:
    status = MattermostBridgeService.from_env().status()
    return ResultEnvelope(
        success=True,
        operation="mattermost_status",
        service="MattermostBridgeAPI",
        trace_id=status.bridge_ref,
        data=status.model_dump(mode="json"),
        redactions_applied=["safe_refs_only", "raw_transcript_omitted"],
    )


@router.get("/roles/catalog", response_model=ResultEnvelope)
def get_mattermost_roles_catalog(authorization: str | None = Header(default=None)) -> ResultEnvelope:
    _require_mattermost_authority(authorization)
    roles = MattermostBridgeService.from_env().role_catalog()
    return ResultEnvelope(
        success=True,
        operation="mattermost_roles_catalog",
        service="MattermostBridgeAPI",
        trace_id="mattermost-roles:catalog",
        data={"roles": roles},
        redactions_applied=["safe_refs_only"],
    )


@router.post("/roles/suggest", response_model=ResultEnvelope)
def post_mattermost_roles_suggest(
    request: MattermostRoleSuggestionRequest,
    authorization: str | None = Header(default=None),
) -> ResultEnvelope:
    _require_mattermost_authority(authorization)
    suggestions = MattermostBridgeService.from_env().suggest_roles(request)
    return ResultEnvelope(
        success=all(suggestion.status.value != "blocked" for suggestion in suggestions),
        operation="mattermost_roles_suggest",
        service="MattermostBridgeAPI",
        trace_id=request.actor_ref,
        data={"suggestions": [suggestion.model_dump(mode="json") for suggestion in suggestions]},
        redactions_applied=["safe_refs_only", "prompt_preview_bounded"],
    )


@router.post("/roles/bind", response_model=ResultEnvelope)
def post_mattermost_roles_bind(
    request: MattermostRoleBindRequest,
    authorization: str | None = Header(default=None),
) -> ResultEnvelope:
    _require_mattermost_authority(authorization)
    try:
        binding = MattermostBridgeService.from_env().bind_roles(request)
    except (ValidationError, ValueError) as exc:
        return _mattermost_error("mattermost_roles_bind", request.channel_ref, "MATTERMOST_ROLE_BIND_REJECTED", exc)
    return ResultEnvelope(
        success=True,
        operation="mattermost_roles_bind",
        service="MattermostBridgeAPI",
        trace_id=binding.binding_id,
        data={"binding": binding.model_dump(mode="json")},
        redactions_applied=["safe_refs_only"],
    )


@router.post("/roles/unbind", response_model=ResultEnvelope)
def post_mattermost_roles_unbind(
    request: MattermostRoleUnbindRequest,
    authorization: str | None = Header(default=None),
) -> ResultEnvelope:
    _require_mattermost_authority(authorization)
    binding = MattermostBridgeService.from_env().unbind_roles(request)
    return ResultEnvelope(
        success=True,
        operation="mattermost_roles_unbind",
        service="MattermostBridgeAPI",
        trace_id=request.channel_ref,
        data={"binding": binding.model_dump(mode="json") if binding is not None else None},
        redactions_applied=["safe_refs_only"],
    )


@router.post("/events/message", response_model=ResultEnvelope)
def post_mattermost_message_event(
    event: MattermostMessageEvent,
    authorization: str | None = Header(default=None),
) -> ResultEnvelope:
    _require_mattermost_authority(authorization)
    try:
        decision = MattermostBridgeService.from_env().handle_message_event(event)
    except (ValidationError, ValueError) as exc:
        return _mattermost_error("mattermost_message_event", event.event_ref, "MATTERMOST_MESSAGE_EVENT_REJECTED", exc)
    return ResultEnvelope(
        success=decision.status.value not in {"blocked"},
        operation="mattermost_message_event",
        service="MattermostBridgeAPI",
        trace_id=decision.decision_ref,
        data=decision.model_dump(mode="json"),
        redactions_applied=["safe_refs_only", "raw_transcript_omitted"],
    )


@router.get("/audit", response_model=ResultEnvelope)
def get_mattermost_audit(
    limit: int = Query(default=100, ge=1, le=500),
    authorization: str | None = Header(default=None),
) -> ResultEnvelope:
    _require_mattermost_authority(authorization)
    events = MattermostBridgeService.from_env().audit_events(limit)
    return ResultEnvelope(
        success=True,
        operation="mattermost_audit",
        service="MattermostBridgeAPI",
        trace_id="mattermost-audit:local",
        data={"events": events},
        redactions_applied=["safe_refs_only", "raw_transcript_omitted"],
    )


@router.get("/receipts", response_model=ResultEnvelope)
def get_mattermost_receipts(
    limit: int = Query(default=100, ge=1, le=500),
    authorization: str | None = Header(default=None),
) -> ResultEnvelope:
    _require_mattermost_authority(authorization)
    receipts = MattermostBridgeService.from_env().receipts(limit)
    return ResultEnvelope(
        success=True,
        operation="mattermost_receipts",
        service="MattermostBridgeAPI",
        trace_id="mattermost-receipts:local",
        data={"receipts": receipts},
        redactions_applied=["safe_refs_only", "raw_transcript_omitted"],
    )


def register_mattermost_routes(app: FastAPI) -> None:
    if getattr(app.state, _REGISTERED_ATTR, False):
        return
    registered_paths = {getattr(route, "path", None) for route in app.router.routes}
    for route in router.routes:
        if getattr(route, "path", None) not in registered_paths:
            app.router.routes.append(route)
    setattr(app.state, _REGISTERED_ATTR, True)


def _require_mattermost_authority(authorization: str | None) -> None:
    error = mattermost_bridge_authority_error(authorization)
    if error is None:
        return
    status_code, detail = error
    raise HTTPException(status_code=status_code, detail=detail)


def _mattermost_error(operation: str, trace_id: str, code: str, exc: Exception) -> ResultEnvelope:
    return ResultEnvelope(
        success=False,
        operation=operation,
        service="MattermostBridgeAPI",
        trace_id=trace_id,
        error=ErrorEnvelope(
            code=code,
            category=ErrorCategory.validation_error,
            safe_message="Mattermost bridge request was rejected safely.",
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="MattermostBridgeAPI",
            metadata={"error_type": exc.__class__.__name__},
        ),
        redactions_applied=["safe_refs_only", "raw_transcript_omitted"],
    )
