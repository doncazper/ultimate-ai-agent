from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, FastAPI, Header, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, SecretStr, StrictBool, model_validator

from ultimate_ai_agent.api.route_registration import register_router_once
from ultimate_ai_agent.core.communications import (
    CommunicationsReceiptNotFound,
    CommunicationsService,
    build_default_communications_service,
)
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope
from ultimate_ai_agent.core.hygiene.envelopes import (
    ErrorCategory,
    ErrorEnvelope,
    Severity,
)
from ultimate_ai_agent.api.idempotency import (
    IDEMPOTENCY_KEY_HEADER,
    IDEMPOTENCY_REF_HEADER,
)
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityLeaseStore,
    authority_lease_kill_switch_engaged,
)
from ultimate_ai_agent.core.communications.matrix_harness import (
    MATRIX_HARNESS_LANES,
    DockerMatrixHarnessBackend,
    MatrixHarnessAuthorityDispatchAdapter,
    MatrixHarnessCommand,
    MatrixHarnessOperation,
    build_matrix_harness_dispatch_request,
    capture_exact_matrix_harness_approval,
    default_matrix_harness_backend_config,
    execute_matrix_harness_command,
)
from ultimate_ai_agent.core.communications.matrix_session import (
    MATRIX_SESSION_LANES,
    MatrixSessionCommand,
    MatrixSessionOperation,
    MatrixSessionTransientInput,
    capture_exact_matrix_session_approval,
    execute_matrix_session_command,
)
from ultimate_ai_agent.core.communications.matrix_sync import (
    build_default_matrix_sync_posture,
)
from ultimate_ai_agent.core.communications.matrix_crypto import (
    MatrixCryptoCommand,
    build_default_matrix_crypto_posture,
    build_matrix_crypto_proposal,
)
from ultimate_ai_agent.core.communications.matrix_messaging import (
    MATRIX_MESSAGING_LANES,
    MatrixBrokerTransientInput,
    MatrixMessagingCommand,
    MatrixMessagingOperation,
    build_default_matrix_messaging_posture,
    build_matrix_messaging_proposal,
)
from ultimate_ai_agent.core.communications.matrix_messaging.authority_surfaces import (
    capture_exact_matrix_messaging_approval,
    issue_exact_matrix_messaging_lease,
)
from ultimate_ai_agent.core.communications.matrix_messaging.contracts import (
    MatrixMessagingReadiness,
)
from ultimate_ai_agent.core.communications.matrix_messaging.outbox import (
    MatrixOutboxRecord,
)
from ultimate_ai_agent.core.communications.matrix_messaging.service import (
    MatrixMessagingRuntime,
    execute_matrix_messaging_command,
)
from ultimate_ai_agent.core.communications.matrix_rooms_media import (
    MATRIX_ROOMS_MEDIA_LANES,
    MatrixRoomsMediaCommand,
    MatrixRoomsMediaOperation,
    MatrixRoomsMediaReadiness,
    MatrixRoomsMediaRuntime,
    build_default_matrix_rooms_media_posture,
    build_matrix_rooms_media_proposal,
    capture_exact_matrix_rooms_media_approval,
    execute_matrix_rooms_media_command,
    issue_exact_matrix_rooms_media_lease,
)
from ultimate_ai_agent.core.communications.matrix_intelligence import (
    MATRIX_INTELLIGENCE_LANES,
    MatrixIntelligenceCommand,
    MatrixIntelligenceOperation,
    MatrixIntelligenceProposalDraft,
    MatrixIntelligenceReadiness,
    MatrixIntelligenceRuntime,
    MatrixIntelligenceRuntimeInput,
    MatrixIntelligenceStore,
    MatrixTransientRoomMessage,
    build_default_matrix_intelligence_posture,
    build_matrix_intelligence_command_proposal,
    capture_exact_matrix_intelligence_approval,
    execute_matrix_intelligence_command,
    issue_exact_matrix_intelligence_lease,
)
from ultimate_ai_agent.core.time import utc_now


router = APIRouter(prefix="/control-center/communications", tags=["control-center"])
_REGISTERED_ATTR = "_uaa_communications_routes_registered"
_SERVICE = build_default_communications_service()
_HARNESS_APPROVAL_AUTHORITY = LocalApprovalAuthority()
_SESSION_APPROVAL_AUTHORITY = LocalApprovalAuthority()
_MESSAGING_APPROVAL_AUTHORITY = LocalApprovalAuthority()
_ROOMS_MEDIA_APPROVAL_AUTHORITY = LocalApprovalAuthority()
_INTELLIGENCE_APPROVAL_AUTHORITY = LocalApprovalAuthority()
_INTELLIGENCE_STORE = MatrixIntelligenceStore()
_REPO_ROOT = Path(__file__).resolve().parents[3]
_REDACTIONS = [
    "communications_safe_refs_only",
    "raw_message_content_omitted",
    "provider_payload_omitted",
    "identity_and_credential_material_omitted",
]


class MatrixHarnessOperationRequest(BaseModel):
    command: MatrixHarnessCommand
    confirmed: StrictBool = False

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_confirmation(self) -> "MatrixHarnessOperationRequest":
        lane = MATRIX_HARNESS_LANES[self.command.operation]
        if self.confirmed and not lane.approval_required:
            raise ValueError("MATRIX_HARNESS_READ_CONFIRMATION_FORBIDDEN")
        return self


MatrixHarnessOperationHandler = Callable[
    [MatrixHarnessOperationRequest],
    object,
]


class MatrixSessionOperationRequest(BaseModel):
    command: MatrixSessionCommand
    endpoint_url: SecretStr | None = None
    discovery_origin: SecretStr | None = None
    callback_url: SecretStr | None = None
    confirmed: StrictBool = False

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_request(self) -> "MatrixSessionOperationRequest":
        lane = MATRIX_SESSION_LANES[self.command.operation]
        if self.confirmed and not lane.approval_required:
            raise ValueError("MATRIX_SESSION_READ_CONFIRMATION_FORBIDDEN")
        sso_operations = {
            MatrixSessionOperation.sso_launch,
            MatrixSessionOperation.sso_callback_consume,
        }
        if self.command.operation == MatrixSessionOperation.discovery_read:
            if (
                self.discovery_origin is None
                or self.endpoint_url is not None
                or self.callback_url is not None
            ):
                raise ValueError("MATRIX_SESSION_DISCOVERY_TRANSIENT_SCOPE_INVALID")
        elif (
            self.endpoint_url is None
            or self.discovery_origin is not None
            or (
                (self.command.operation in sso_operations)
                != (self.callback_url is not None)
            )
        ):
            raise ValueError("MATRIX_SESSION_ENDPOINT_TRANSIENT_SCOPE_INVALID")
        return self


MatrixSessionOperationHandler = Callable[[MatrixSessionOperationRequest], object]


class MatrixCryptoProposalRequest(BaseModel):
    command: MatrixCryptoCommand

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class MatrixMessagingTransientRequest(BaseModel):
    homeserver_url: SecretStr | None = None
    room_id: SecretStr | None = None
    event_id: SecretStr | None = None
    typing_active: StrictBool | None = None

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    def to_runtime_input(self) -> MatrixBrokerTransientInput:
        return MatrixBrokerTransientInput(
            homeserver_url=(
                self.homeserver_url.get_secret_value()
                if self.homeserver_url is not None
                else None
            ),
            room_id=(
                self.room_id.get_secret_value() if self.room_id is not None else None
            ),
            event_id=(
                self.event_id.get_secret_value() if self.event_id is not None else None
            ),
            typing_active=self.typing_active,
        )


class MatrixMessagingOperationRequest(BaseModel):
    command: MatrixMessagingCommand
    transient: MatrixMessagingTransientRequest | None = None
    outbox_record: MatrixOutboxRecord | None = None
    confirmed: StrictBool = False

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_exact_runtime_input(self) -> "MatrixMessagingOperationRequest":
        outbox_write = self.command.operation in {
            MatrixMessagingOperation.draft_write,
            MatrixMessagingOperation.outbox_enqueue,
        }
        if outbox_write != (self.outbox_record is not None):
            raise ValueError("MATRIX_MESSAGING_OUTBOX_RECORD_SCOPE_INVALID")
        transient_operation = self.command.operation in {
            MatrixMessagingOperation.typing,
            MatrixMessagingOperation.read_receipt,
        }
        if transient_operation != (self.transient is not None):
            raise ValueError("MATRIX_MESSAGING_TRANSIENT_SCOPE_INVALID")
        if self.transient is not None:
            if self.transient.homeserver_url is None or self.transient.room_id is None:
                raise ValueError("MATRIX_MESSAGING_HOMESERVER_TRANSIENT_REQUIRED")
            if self.command.operation == MatrixMessagingOperation.typing:
                if (
                    self.transient.typing_active is None
                    or self.transient.event_id is not None
                ):
                    raise ValueError("MATRIX_MESSAGING_TYPING_TRANSIENT_INVALID")
            elif (
                self.transient.event_id is None
                or self.transient.typing_active is not None
            ):
                raise ValueError("MATRIX_MESSAGING_RECEIPT_TRANSIENT_INVALID")
        return self


class MatrixMessagingProposalRequest(BaseModel):
    command: MatrixMessagingCommand

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


MatrixMessagingOperationHandler = Callable[
    [MatrixMessagingOperationRequest],
    object,
]


class MatrixRoomsMediaOperationRequest(BaseModel):
    command: MatrixRoomsMediaCommand
    confirmed: StrictBool = False

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class MatrixRoomsMediaProposalRequest(BaseModel):
    command: MatrixRoomsMediaCommand

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


MatrixRoomsMediaOperationHandler = Callable[[MatrixRoomsMediaOperationRequest], object]


class MatrixIntelligenceTransientMessageRequest(BaseModel):
    event_ref: str
    content: SecretStr

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class MatrixIntelligenceOperationRequest(BaseModel):
    command: MatrixIntelligenceCommand
    transient_messages: tuple[MatrixIntelligenceTransientMessageRequest, ...] = ()
    proposal_draft: MatrixIntelligenceProposalDraft | None = None
    confirmed: StrictBool = False

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_runtime_input(self) -> "MatrixIntelligenceOperationRequest":
        context = (
            self.command.operation == MatrixIntelligenceOperation.context_materialize
        )
        proposal = (
            self.command.operation == MatrixIntelligenceOperation.proposal_persist
        )
        if context != bool(self.transient_messages):
            raise ValueError("MATRIX_INTELLIGENCE_TRANSIENT_CONTEXT_SCOPE_INVALID")
        if proposal != (self.proposal_draft is not None):
            raise ValueError("MATRIX_INTELLIGENCE_PROPOSAL_DRAFT_SCOPE_INVALID")
        if (
            self.transient_messages
            and tuple(item.event_ref for item in self.transient_messages)
            != self.command.event_refs
        ):
            raise ValueError("MATRIX_INTELLIGENCE_TRANSIENT_EVENT_SCOPE_MISMATCH")
        return self

    def to_runtime_input(self) -> MatrixIntelligenceRuntimeInput:
        return MatrixIntelligenceRuntimeInput(
            messages=tuple(
                MatrixTransientRoomMessage(
                    event_ref=item.event_ref,
                    content=item.content.get_secret_value(),
                )
                for item in self.transient_messages
            ),
            proposal_draft=self.proposal_draft,
        )


class MatrixIntelligenceProposalRequest(BaseModel):
    command: MatrixIntelligenceCommand

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


MatrixIntelligenceOperationHandler = Callable[
    [MatrixIntelligenceOperationRequest], object
]


def _execute_matrix_harness_operation(
    payload: MatrixHarnessOperationRequest,
) -> object:
    store = AuthorityLeaseStore()
    backend = DockerMatrixHarnessBackend(
        default_matrix_harness_backend_config(_REPO_ROOT),
        kill_switch_engaged=authority_lease_kill_switch_engaged,
    )
    lane = MATRIX_HARNESS_LANES[payload.command.operation]
    approval_ref: str | None = None
    if lane.approval_required and payload.confirmed:
        adapter = MatrixHarnessAuthorityDispatchAdapter(
            operation=payload.command.operation,
            backend=backend,
            authority_leases_provider=lambda: store.list_leases(active_only=False),
        )
        approval_ref = capture_exact_matrix_harness_approval(
            build_matrix_harness_dispatch_request(
                payload.command,
                adapter=adapter,
            ),
            approval_authority=_HARNESS_APPROVAL_AUTHORITY,
            confirmed=True,
        )
    return execute_matrix_harness_command(
        payload.command,
        repo_root=_REPO_ROOT,
        authority_state_dir=store.state_dir,
        approval_ref=approval_ref,
        backend=backend,
        lease_store=store,
        approval_authority=_HARNESS_APPROVAL_AUTHORITY,
    )


_HARNESS_OPERATION_HANDLER: MatrixHarnessOperationHandler = (
    _execute_matrix_harness_operation
)


def _execute_matrix_session_operation(
    payload: MatrixSessionOperationRequest,
) -> object:
    store = AuthorityLeaseStore()
    lane = MATRIX_SESSION_LANES[payload.command.operation]
    approval_ref: str | None = None
    if lane.approval_required and payload.confirmed:
        approval_ref = capture_exact_matrix_session_approval(
            payload.command,
            approval_authority=_SESSION_APPROVAL_AUTHORITY,
            confirmed=True,
        )
    return execute_matrix_session_command(
        payload.command,
        repo_root=_REPO_ROOT,
        authority_state_dir=store.state_dir,
        transient_input=MatrixSessionTransientInput(
            endpoint_url=(
                payload.endpoint_url.get_secret_value()
                if payload.endpoint_url is not None
                else None
            ),
            discovery_origin=(
                payload.discovery_origin.get_secret_value()
                if payload.discovery_origin is not None
                else None
            ),
            callback_url=(
                payload.callback_url.get_secret_value()
                if payload.callback_url is not None
                else None
            ),
        ),
        approval_ref=approval_ref,
        lease_store=store,
        approval_authority=_SESSION_APPROVAL_AUTHORITY,
    )


_SESSION_OPERATION_HANDLER: MatrixSessionOperationHandler = (
    _execute_matrix_session_operation
)


def _blocked_matrix_messaging_readiness(
    command: MatrixMessagingCommand,
) -> MatrixMessagingReadiness:
    now = utc_now()
    return MatrixMessagingReadiness(
        readiness_ref=command.readiness_ref,
        request_fingerprint_ref=command.request_fingerprint_ref,
        adapter_ref=MATRIX_MESSAGING_LANES[command.operation].adapter_ref,
        status="blocked",
        observed_at=now,
        expires_at=min(command.start_deadline, now + timedelta(seconds=30)),
        kill_switch_engaged=False,
        safe_disable_active=False,
        broker_integrity_verified=False,
        keychain_available=False,
        crypto_store_available=False,
        reason_refs=("reason-ref:matrix-messaging:runtime-enrollment-required",),
    )


def _execute_matrix_messaging_operation(
    payload: MatrixMessagingOperationRequest,
) -> object:
    store = AuthorityLeaseStore()
    command = payload.command
    if payload.confirmed:
        issue_exact_matrix_messaging_lease(command, store=store, confirmed=True)
        approval_ref = capture_exact_matrix_messaging_approval(
            command,
            approval_authority=_MESSAGING_APPROVAL_AUTHORITY,
            confirmed=True,
        )
    else:
        approval_ref = None
    return execute_matrix_messaging_command(
        command,
        authority_state_dir=store.state_dir,
        runtime=MatrixMessagingRuntime.blocked(),
        readiness_provider=_blocked_matrix_messaging_readiness,
        approval_ref=approval_ref,
        lease_store=store,
        approval_authority=_MESSAGING_APPROVAL_AUTHORITY,
    )


_MATRIX_MESSAGING_OPERATION_HANDLER: MatrixMessagingOperationHandler = (
    _execute_matrix_messaging_operation
)


def _blocked_matrix_rooms_media_readiness(
    command: MatrixRoomsMediaCommand,
) -> MatrixRoomsMediaReadiness:
    now = utc_now()
    return MatrixRoomsMediaReadiness(
        readiness_ref=command.readiness_ref,
        request_fingerprint_ref=command.request_fingerprint_ref,
        adapter_ref=MATRIX_ROOMS_MEDIA_LANES[command.operation].adapter_ref,
        status="blocked",
        observed_at=now,
        expires_at=min(command.start_deadline, now + timedelta(seconds=30)),
        kill_switch_engaged=False,
        safe_disable_active=False,
        broker_integrity_verified=False,
        filesystem_root_verified=False,
        encrypted_index_available=False,
        reason_refs=("reason-ref:matrix-rooms-media:runtime-enrollment-required",),
    )


def _execute_matrix_rooms_media_operation(
    payload: MatrixRoomsMediaOperationRequest,
) -> object:
    store = AuthorityLeaseStore()
    command = payload.command
    if payload.confirmed:
        issue_exact_matrix_rooms_media_lease(command, store=store, confirmed=True)
        approval_ref = capture_exact_matrix_rooms_media_approval(
            command,
            approval_authority=_ROOMS_MEDIA_APPROVAL_AUTHORITY,
            confirmed=True,
        )
    else:
        approval_ref = None
    return execute_matrix_rooms_media_command(
        command,
        authority_state_dir=store.state_dir,
        runtime=MatrixRoomsMediaRuntime.blocked(),
        readiness_provider=_blocked_matrix_rooms_media_readiness,
        approval_ref=approval_ref,
        lease_store=store,
        approval_authority=_ROOMS_MEDIA_APPROVAL_AUTHORITY,
    )


_MATRIX_ROOMS_MEDIA_OPERATION_HANDLER: MatrixRoomsMediaOperationHandler = (
    _execute_matrix_rooms_media_operation
)


def _matrix_intelligence_readiness(
    command: MatrixIntelligenceCommand,
) -> MatrixIntelligenceReadiness:
    now = utc_now()
    return MatrixIntelligenceReadiness(
        readiness_ref=command.readiness_ref,
        request_fingerprint_ref=command.request_fingerprint_ref,
        adapter_ref=MATRIX_INTELLIGENCE_LANES[command.operation].adapter_ref,
        status=("blocked" if authority_lease_kill_switch_engaged() else "ready"),
        observed_at=now,
        expires_at=min(command.start_deadline, now + timedelta(seconds=30)),
        kill_switch_engaged=authority_lease_kill_switch_engaged(),
        safe_disable_active=False,
        local_store_available=True,
        transient_context_adapter_available=True,
        reason_refs=(
            ("reason-ref:matrix-intelligence:authority-kill-switch-engaged",)
            if authority_lease_kill_switch_engaged()
            else ()
        ),
    )


def _execute_matrix_intelligence_operation(
    payload: MatrixIntelligenceOperationRequest,
) -> object:
    lease_store = AuthorityLeaseStore()
    command = payload.command
    if payload.confirmed:
        issue_exact_matrix_intelligence_lease(
            command, store=lease_store, confirmed=True
        )
        approval_ref = capture_exact_matrix_intelligence_approval(
            command,
            approval_authority=_INTELLIGENCE_APPROVAL_AUTHORITY,
            confirmed=True,
        )
    else:
        approval_ref = None
    return execute_matrix_intelligence_command(
        command,
        authority_state_dir=lease_store.state_dir,
        runtime=MatrixIntelligenceRuntime.local(
            store=_INTELLIGENCE_STORE,
            runtime_input=payload.to_runtime_input(),
        ),
        readiness_provider=_matrix_intelligence_readiness,
        approval_ref=approval_ref,
        lease_store=lease_store,
        approval_authority=_INTELLIGENCE_APPROVAL_AUTHORITY,
    )


_MATRIX_INTELLIGENCE_OPERATION_HANDLER: MatrixIntelligenceOperationHandler = (
    _execute_matrix_intelligence_operation
)


def get_communications_service() -> CommunicationsService:
    return _SERVICE


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


def _envelope(*, operation: str, trace_id: str, data: object) -> ResultEnvelope:
    return ResultEnvelope(
        success=True,
        operation=operation,
        service="CommunicationsService",
        trace_id=trace_id,
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:communications:contract-inspection"}],
        redactions_applied=list(_REDACTIONS),
    )


def _run_harness_operation(
    operation: MatrixHarnessOperation,
    payload: MatrixHarnessOperationRequest,
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    if payload.command.operation != operation:
        raise HTTPException(
            status_code=422,
            detail="MATRIX_HARNESS_OPERATION_MISMATCH",
            headers={"Cache-Control": "no-store"},
        )
    try:
        result = _HARNESS_OPERATION_HANDLER(payload)
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=409,
            detail="MATRIX_HARNESS_OPERATION_BLOCKED",
            headers={"Cache-Control": "no-store"},
        ) from exc
    data = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
    operation_name = f"control_center_communications_harness_{operation.value}"
    status = getattr(getattr(result, "receipt", None), "status", None)
    if status is None or status == "succeeded":
        return _envelope(
            operation=operation_name,
            trace_id=payload.command.dispatch_ref,
            data=data,
        )
    return ResultEnvelope(
        success=False,
        operation=operation_name,
        service="CommunicationsService",
        trace_id=payload.command.dispatch_ref,
        data=data,
        error=ErrorEnvelope(
            code="MATRIX_HARNESS_OPERATION_NOT_SUCCEEDED",
            category=(
                ErrorCategory.authorization_error
                if status in {"denied", "cancelled_before_start"}
                else ErrorCategory.tool_error
            ),
            safe_message="The exact Matrix harness operation did not succeed.",
            severity=Severity.high,
            retryable=False,
            details_redacted=True,
            source="CommunicationsService",
        ),
        redactions_applied=list(_REDACTIONS),
    )


def _require_harness_idempotency_binding(
    payload: MatrixHarnessOperationRequest,
    idempotency_key: str | None,
    idempotency_ref: str | None,
) -> None:
    supplied = {
        value.strip()
        for value in (idempotency_key, idempotency_ref)
        if value is not None and value.strip()
    }
    if supplied != {payload.command.idempotency_ref}:
        raise HTTPException(
            status_code=409,
            detail="MATRIX_HARNESS_IDEMPOTENCY_MISMATCH",
            headers={"Cache-Control": "no-store"},
        )


def _require_session_idempotency_binding(
    payload: MatrixSessionOperationRequest,
    idempotency_key: str | None,
    idempotency_ref: str | None,
) -> None:
    supplied = {
        value.strip()
        for value in (idempotency_key, idempotency_ref)
        if value is not None and value.strip()
    }
    if supplied != {payload.command.idempotency_ref}:
        raise HTTPException(
            status_code=409,
            detail="MATRIX_SESSION_IDEMPOTENCY_MISMATCH",
            headers={"Cache-Control": "no-store"},
        )


def _require_messaging_idempotency_binding(
    payload: MatrixMessagingOperationRequest,
    idempotency_key: str | None,
    idempotency_ref: str | None,
) -> None:
    supplied = {
        value.strip()
        for value in (idempotency_key, idempotency_ref)
        if value is not None and value.strip()
    }
    if supplied != {payload.command.idempotency_ref}:
        raise HTTPException(
            status_code=409,
            detail="MATRIX_MESSAGING_IDEMPOTENCY_MISMATCH",
            headers={"Cache-Control": "no-store"},
        )


def _require_rooms_media_idempotency_binding(
    payload: MatrixRoomsMediaOperationRequest,
    idempotency_key: str | None,
    idempotency_ref: str | None,
) -> None:
    supplied = {
        value.strip()
        for value in (idempotency_key, idempotency_ref)
        if value is not None and value.strip()
    }
    if supplied != {payload.command.idempotency_ref}:
        raise HTTPException(
            status_code=409,
            detail="MATRIX_ROOMS_MEDIA_IDEMPOTENCY_MISMATCH",
            headers={"Cache-Control": "no-store"},
        )


def _require_matrix_intelligence_idempotency_binding(
    payload: MatrixIntelligenceOperationRequest,
    idempotency_key: str | None,
    idempotency_ref: str | None,
) -> None:
    supplied = {
        value.strip()
        for value in (idempotency_key, idempotency_ref)
        if value is not None and value.strip()
    }
    if supplied != {payload.command.idempotency_ref}:
        raise HTTPException(
            status_code=409,
            detail="MATRIX_INTELLIGENCE_IDEMPOTENCY_MISMATCH",
            headers={"Cache-Control": "no-store"},
        )


def _run_matrix_messaging_operation(
    operation: MatrixMessagingOperation,
    payload: MatrixMessagingOperationRequest,
    response: Response,
    idempotency_key: str | None,
    idempotency_ref: str | None,
) -> ResultEnvelope:
    _no_store(response)
    if payload.command.operation != operation:
        raise HTTPException(
            status_code=422,
            detail="MATRIX_MESSAGING_OPERATION_MISMATCH",
            headers={"Cache-Control": "no-store"},
        )
    _require_messaging_idempotency_binding(payload, idempotency_key, idempotency_ref)
    try:
        result = _MATRIX_MESSAGING_OPERATION_HANDLER(payload)
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=409,
            detail="MATRIX_MESSAGING_OPERATION_BLOCKED",
            headers={"Cache-Control": "no-store"},
        ) from exc
    data = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
    operation_name = f"control_center_communications_matrix_messaging_{operation.value}"
    status = getattr(getattr(result, "receipt", None), "status", None)
    if status is None or status == "succeeded":
        return _envelope(
            operation=operation_name,
            trace_id=payload.command.dispatch_ref,
            data=data,
        )
    return ResultEnvelope(
        success=False,
        operation=operation_name,
        service="CommunicationsService",
        trace_id=payload.command.dispatch_ref,
        data=data,
        error=ErrorEnvelope(
            code="MATRIX_MESSAGING_OPERATION_NOT_SUCCEEDED",
            category=(
                ErrorCategory.authorization_error
                if status in {"denied", "cancelled_before_start"}
                else ErrorCategory.tool_error
            ),
            safe_message="The exact Matrix messaging operation did not succeed.",
            severity=Severity.high,
            retryable=False,
            details_redacted=True,
            source="CommunicationsService",
        ),
        redactions_applied=list(_REDACTIONS),
    )


def _run_matrix_rooms_media_operation(
    operation: MatrixRoomsMediaOperation,
    payload: MatrixRoomsMediaOperationRequest,
    response: Response,
    idempotency_key: str | None,
    idempotency_ref: str | None,
) -> ResultEnvelope:
    _no_store(response)
    if payload.command.operation != operation:
        raise HTTPException(
            status_code=422,
            detail="MATRIX_ROOMS_MEDIA_OPERATION_MISMATCH",
            headers={"Cache-Control": "no-store"},
        )
    _require_rooms_media_idempotency_binding(payload, idempotency_key, idempotency_ref)
    try:
        result = _MATRIX_ROOMS_MEDIA_OPERATION_HANDLER(payload)
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=409,
            detail="MATRIX_ROOMS_MEDIA_OPERATION_BLOCKED",
            headers={"Cache-Control": "no-store"},
        ) from exc
    data = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
    operation_name = (
        f"control_center_communications_matrix_rooms_media_{operation.value}"
    )
    status = getattr(getattr(result, "receipt", None), "status", None)
    if status == "succeeded":
        return _envelope(
            operation=operation_name, trace_id=payload.command.dispatch_ref, data=data
        )
    return ResultEnvelope(
        success=False,
        operation=operation_name,
        service="CommunicationsService",
        trace_id=payload.command.dispatch_ref,
        data=data,
        error=ErrorEnvelope(
            code="MATRIX_ROOMS_MEDIA_OPERATION_NOT_SUCCEEDED",
            category=ErrorCategory.authorization_error,
            safe_message="The exact Matrix room, search, or media operation did not succeed.",
            severity=Severity.high,
            retryable=False,
            details_redacted=True,
            source="CommunicationsService",
        ),
        redactions_applied=list(_REDACTIONS),
    )


def _run_matrix_intelligence_operation(
    operation: MatrixIntelligenceOperation,
    payload: MatrixIntelligenceOperationRequest,
    response: Response,
    idempotency_key: str | None,
    idempotency_ref: str | None,
) -> ResultEnvelope:
    _no_store(response)
    if payload.command.operation != operation:
        raise HTTPException(
            status_code=422,
            detail="MATRIX_INTELLIGENCE_OPERATION_MISMATCH",
            headers={"Cache-Control": "no-store"},
        )
    _require_matrix_intelligence_idempotency_binding(
        payload, idempotency_key, idempotency_ref
    )
    try:
        result = _MATRIX_INTELLIGENCE_OPERATION_HANDLER(payload)
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=409,
            detail="MATRIX_INTELLIGENCE_OPERATION_BLOCKED",
            headers={"Cache-Control": "no-store"},
        ) from exc
    data = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
    operation_name = (
        f"control_center_communications_matrix_intelligence_{operation.value}"
    )
    status = getattr(getattr(result, "receipt", None), "status", None)
    if status == "succeeded":
        return _envelope(
            operation=operation_name,
            trace_id=payload.command.dispatch_ref,
            data=data,
        )
    return ResultEnvelope(
        success=False,
        operation=operation_name,
        service="CommunicationsService",
        trace_id=payload.command.dispatch_ref,
        data=data,
        error=ErrorEnvelope(
            code="MATRIX_INTELLIGENCE_OPERATION_NOT_SUCCEEDED",
            category=ErrorCategory.authorization_error,
            safe_message="The exact Matrix intelligence operation did not succeed.",
            severity=Severity.high,
            retryable=False,
            details_redacted=True,
            source="CommunicationsService",
        ),
        redactions_applied=[*_REDACTIONS, "transient_room_content_omitted"],
    )


def _run_session_operation(
    operation: MatrixSessionOperation,
    payload: MatrixSessionOperationRequest,
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    if payload.command.operation != operation:
        raise HTTPException(
            status_code=422,
            detail="MATRIX_SESSION_OPERATION_MISMATCH",
            headers={"Cache-Control": "no-store"},
        )
    try:
        result = _SESSION_OPERATION_HANDLER(payload)
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=409,
            detail="MATRIX_SESSION_OPERATION_BLOCKED",
            headers={"Cache-Control": "no-store"},
        ) from exc
    data = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
    operation_name = f"control_center_communications_matrix_{operation.value}"
    status = getattr(getattr(result, "receipt", None), "status", None)
    if status == "succeeded":
        return _envelope(
            operation=operation_name,
            trace_id=payload.command.dispatch_ref,
            data=data,
        )
    return ResultEnvelope(
        success=False,
        operation=operation_name,
        service="CommunicationsService",
        trace_id=payload.command.dispatch_ref,
        data=data,
        error=ErrorEnvelope(
            code="MATRIX_SESSION_OPERATION_NOT_SUCCEEDED",
            category=(
                ErrorCategory.authorization_error
                if status in {"denied", "cancelled_before_start"}
                else ErrorCategory.tool_error
            ),
            safe_message="The exact Matrix session operation did not succeed.",
            severity=Severity.high,
            retryable=False,
            details_redacted=True,
            source="CommunicationsService",
        ),
        redactions_applied=list(_REDACTIONS),
    )


@router.get(
    "/providers",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_providers",
)
def get_control_center_communications_providers(response: Response) -> ResultEnvelope:
    _no_store(response)
    descriptors = get_communications_service().inspect_provider_posture()
    return _envelope(
        operation="control_center_communications_providers",
        trace_id="communications-trace:providers",
        data=[descriptor.model_dump(mode="json") for descriptor in descriptors],
    )


@router.get(
    "/session-posture",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_session_posture",
)
def get_control_center_communications_session_posture(
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    posture = get_communications_service().inspect_session_posture()
    return _envelope(
        operation="control_center_communications_session_posture",
        trace_id=posture.session_ref,
        data=posture.model_dump(mode="json"),
    )


@router.get(
    "/matrix-sync/posture",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_matrix_sync_posture",
)
def get_control_center_communications_matrix_sync_posture(
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    posture = build_default_matrix_sync_posture()
    return _envelope(
        operation="control_center_communications_matrix_sync_posture",
        trace_id="communications-trace:matrix-sync-posture",
        data=posture.model_dump(mode="json"),
    )


@router.get(
    "/matrix-crypto/posture",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_matrix_crypto_posture",
)
def get_control_center_communications_matrix_crypto_posture(
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    posture = build_default_matrix_crypto_posture()
    return _envelope(
        operation="control_center_communications_matrix_crypto_posture",
        trace_id=posture.posture_ref,
        data=posture.model_dump(mode="json"),
    )


@router.post(
    "/matrix-crypto/proposal",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_matrix_crypto_proposal",
)
def post_control_center_communications_matrix_crypto_proposal(
    payload: MatrixCryptoProposalRequest,
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    proposal = build_matrix_crypto_proposal(payload.command)
    return _envelope(
        operation="control_center_communications_matrix_crypto_proposal",
        trace_id=proposal.proposal_ref,
        data=proposal.model_dump(mode="json"),
    )


@router.get(
    "/matrix-messaging/posture",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_matrix_messaging_posture",
)
def get_control_center_communications_matrix_messaging_posture(
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    posture = build_default_matrix_messaging_posture()
    return _envelope(
        operation="control_center_communications_matrix_messaging_posture",
        trace_id=posture.posture_ref,
        data=posture.model_dump(mode="json"),
    )


@router.post(
    "/matrix-messaging/proposal",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_matrix_messaging_proposal",
)
def post_control_center_communications_matrix_messaging_proposal(
    payload: MatrixMessagingProposalRequest,
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    proposal = build_matrix_messaging_proposal(payload.command)
    return _envelope(
        operation="control_center_communications_matrix_messaging_proposal",
        trace_id=proposal.proposal_ref,
        data=proposal.model_dump(mode="json"),
    )


@router.get(
    "/matrix-rooms-media/posture",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_matrix_rooms_media_posture",
)
def get_control_center_communications_matrix_rooms_media_posture(
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    posture = build_default_matrix_rooms_media_posture()
    return _envelope(
        operation="control_center_communications_matrix_rooms_media_posture",
        trace_id=posture.posture_ref,
        data=posture.model_dump(mode="json"),
    )


@router.post(
    "/matrix-rooms-media/proposal",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_matrix_rooms_media_proposal",
)
def post_control_center_communications_matrix_rooms_media_proposal(
    payload: MatrixRoomsMediaProposalRequest,
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    proposal = build_matrix_rooms_media_proposal(payload.command)
    return _envelope(
        operation="control_center_communications_matrix_rooms_media_proposal",
        trace_id=proposal.proposal_ref,
        data=proposal.model_dump(mode="json"),
    )


@router.get(
    "/matrix-intelligence/posture",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_matrix_intelligence_posture",
)
def get_control_center_communications_matrix_intelligence_posture(
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    posture = build_default_matrix_intelligence_posture()
    return _envelope(
        operation="control_center_communications_matrix_intelligence_posture",
        trace_id=posture.posture_ref,
        data=posture.model_dump(mode="json"),
    )


@router.post(
    "/matrix-intelligence/proposal",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_matrix_intelligence_proposal",
)
def post_control_center_communications_matrix_intelligence_proposal(
    payload: MatrixIntelligenceProposalRequest,
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    proposal = build_matrix_intelligence_command_proposal(payload.command)
    return _envelope(
        operation="control_center_communications_matrix_intelligence_proposal",
        trace_id=proposal.proposal_ref,
        data=proposal.model_dump(mode="json"),
    )


@router.get(
    "/rooms",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_rooms",
)
def get_control_center_communications_rooms(
    response: Response,
    limit: int = Query(default=25, ge=1, le=50),
) -> ResultEnvelope:
    _no_store(response)
    page = get_communications_service().list_rooms(limit=limit)
    return _envelope(
        operation="control_center_communications_rooms",
        trace_id="communications-trace:rooms",
        data=page.model_dump(mode="json"),
    )


@router.get(
    "/failed-sends",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_failed_sends",
)
def get_control_center_communications_failed_sends(
    response: Response,
    limit: int = Query(default=25, ge=1, le=50),
) -> ResultEnvelope:
    _no_store(response)
    page = get_communications_service().list_failed_sends(limit=limit)
    return _envelope(
        operation="control_center_communications_failed_sends",
        trace_id="communications-trace:failed-sends",
        data=page.model_dump(mode="json"),
    )


@router.get(
    "/security-posture",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_security_posture",
)
def get_control_center_communications_security_posture(
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    posture = get_communications_service().inspect_security_posture()
    return _envelope(
        operation="control_center_communications_security_posture",
        trace_id=posture.posture_ref,
        data=posture.model_dump(mode="json"),
    )


@router.get(
    "/receipts/{receipt_ref}",
    response_model=ResultEnvelope,
    operation_id="get_control_center_communications_receipt",
)
def get_control_center_communications_receipt(
    receipt_ref: str,
    response: Response,
) -> ResultEnvelope:
    _no_store(response)
    try:
        receipt = get_communications_service().lookup_receipt(receipt_ref)
    except CommunicationsReceiptNotFound as exc:
        raise HTTPException(
            status_code=404,
            detail="COMMUNICATIONS_RECEIPT_NOT_FOUND",
            headers={"Cache-Control": "no-store"},
        ) from exc
    return _envelope(
        operation="control_center_communications_receipt",
        trace_id=receipt.receipt_ref,
        data=receipt.model_dump(mode="json"),
    )


@router.post(
    "/harness/inspect",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_harness_inspect",
)
def post_control_center_communications_harness_inspect(
    payload: MatrixHarnessOperationRequest,
    response: Response,
) -> ResultEnvelope:
    return _run_harness_operation(MatrixHarnessOperation.inspect, payload, response)


@router.post(
    "/harness/smoke",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_harness_smoke",
)
def post_control_center_communications_harness_smoke(
    payload: MatrixHarnessOperationRequest,
    response: Response,
) -> ResultEnvelope:
    return _run_harness_operation(MatrixHarnessOperation.smoke, payload, response)


@router.post(
    "/harness/start",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_harness_start",
)
def post_control_center_communications_harness_start(
    payload: MatrixHarnessOperationRequest,
    response: Response,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias=IDEMPOTENCY_KEY_HEADER
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias=IDEMPOTENCY_REF_HEADER
    ),
) -> ResultEnvelope:
    _require_harness_idempotency_binding(
        payload, x_uaa_idempotency_key, x_uaa_idempotency_ref
    )
    return _run_harness_operation(MatrixHarnessOperation.start, payload, response)


@router.post(
    "/harness/fixture-seed",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_harness_fixture_seed",
)
def post_control_center_communications_harness_fixture_seed(
    payload: MatrixHarnessOperationRequest,
    response: Response,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias=IDEMPOTENCY_KEY_HEADER
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias=IDEMPOTENCY_REF_HEADER
    ),
) -> ResultEnvelope:
    _require_harness_idempotency_binding(
        payload, x_uaa_idempotency_key, x_uaa_idempotency_ref
    )
    return _run_harness_operation(
        MatrixHarnessOperation.fixture_seed,
        payload,
        response,
    )


@router.post(
    "/harness/stop",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_harness_stop",
)
def post_control_center_communications_harness_stop(
    payload: MatrixHarnessOperationRequest,
    response: Response,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias=IDEMPOTENCY_KEY_HEADER
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias=IDEMPOTENCY_REF_HEADER
    ),
) -> ResultEnvelope:
    _require_harness_idempotency_binding(
        payload, x_uaa_idempotency_key, x_uaa_idempotency_ref
    )
    return _run_harness_operation(MatrixHarnessOperation.stop, payload, response)


@router.post(
    "/harness/reset",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_harness_reset",
)
def post_control_center_communications_harness_reset(
    payload: MatrixHarnessOperationRequest,
    response: Response,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias=IDEMPOTENCY_KEY_HEADER
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias=IDEMPOTENCY_REF_HEADER
    ),
) -> ResultEnvelope:
    _require_harness_idempotency_binding(
        payload, x_uaa_idempotency_key, x_uaa_idempotency_ref
    )
    return _run_harness_operation(MatrixHarnessOperation.reset, payload, response)


@router.post(
    "/matrix/discovery-read",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_matrix_discovery_read",
)
def post_control_center_communications_matrix_discovery_read(
    payload: MatrixSessionOperationRequest,
    response: Response,
) -> ResultEnvelope:
    return _run_session_operation(
        MatrixSessionOperation.discovery_read, payload, response
    )


@router.post(
    "/matrix/auth-methods-read",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_matrix_auth_methods_read",
)
def post_control_center_communications_matrix_auth_methods_read(
    payload: MatrixSessionOperationRequest,
    response: Response,
) -> ResultEnvelope:
    return _run_session_operation(
        MatrixSessionOperation.auth_methods_read, payload, response
    )


def _run_mutating_session_route(
    operation: MatrixSessionOperation,
    payload: MatrixSessionOperationRequest,
    response: Response,
    idempotency_key: str | None,
    idempotency_ref: str | None,
) -> ResultEnvelope:
    _require_session_idempotency_binding(payload, idempotency_key, idempotency_ref)
    return _run_session_operation(operation, payload, response)


@router.post(
    "/matrix/credential-auth-create",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_matrix_credential_auth_create",
)
def post_control_center_communications_matrix_credential_auth_create(
    payload: MatrixSessionOperationRequest,
    response: Response,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias=IDEMPOTENCY_KEY_HEADER
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias=IDEMPOTENCY_REF_HEADER
    ),
) -> ResultEnvelope:
    return _run_mutating_session_route(
        MatrixSessionOperation.credential_auth_create,
        payload,
        response,
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )


@router.post(
    "/matrix/sso-launch",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_matrix_sso_launch",
)
def post_control_center_communications_matrix_sso_launch(
    payload: MatrixSessionOperationRequest,
    response: Response,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias=IDEMPOTENCY_KEY_HEADER
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias=IDEMPOTENCY_REF_HEADER
    ),
) -> ResultEnvelope:
    return _run_mutating_session_route(
        MatrixSessionOperation.sso_launch,
        payload,
        response,
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )


@router.post(
    "/matrix/sso-callback-consume",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_matrix_sso_callback_consume",
)
def post_control_center_communications_matrix_sso_callback_consume(
    payload: MatrixSessionOperationRequest,
    response: Response,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias=IDEMPOTENCY_KEY_HEADER
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias=IDEMPOTENCY_REF_HEADER
    ),
) -> ResultEnvelope:
    return _run_mutating_session_route(
        MatrixSessionOperation.sso_callback_consume,
        payload,
        response,
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )


@router.post(
    "/matrix/refresh",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_matrix_refresh",
)
def post_control_center_communications_matrix_refresh(
    payload: MatrixSessionOperationRequest,
    response: Response,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias=IDEMPOTENCY_KEY_HEADER
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias=IDEMPOTENCY_REF_HEADER
    ),
) -> ResultEnvelope:
    return _run_mutating_session_route(
        MatrixSessionOperation.refresh,
        payload,
        response,
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )


@router.post(
    "/matrix/logout",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_matrix_logout",
)
def post_control_center_communications_matrix_logout(
    payload: MatrixSessionOperationRequest,
    response: Response,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias=IDEMPOTENCY_KEY_HEADER
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias=IDEMPOTENCY_REF_HEADER
    ),
) -> ResultEnvelope:
    return _run_mutating_session_route(
        MatrixSessionOperation.logout,
        payload,
        response,
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )


@router.post(
    "/matrix/revoke-all",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_matrix_revoke_all",
)
def post_control_center_communications_matrix_revoke_all(
    payload: MatrixSessionOperationRequest,
    response: Response,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias=IDEMPOTENCY_KEY_HEADER
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias=IDEMPOTENCY_REF_HEADER
    ),
) -> ResultEnvelope:
    return _run_mutating_session_route(
        MatrixSessionOperation.revoke_all,
        payload,
        response,
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )


@router.post(
    "/matrix/credential-store-rotate",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_matrix_credential_store_rotate",
)
def post_control_center_communications_matrix_credential_store_rotate(
    payload: MatrixSessionOperationRequest,
    response: Response,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias=IDEMPOTENCY_KEY_HEADER
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias=IDEMPOTENCY_REF_HEADER
    ),
) -> ResultEnvelope:
    return _run_mutating_session_route(
        MatrixSessionOperation.credential_store_rotate,
        payload,
        response,
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )


@router.post(
    "/matrix/credential-delete",
    response_model=ResultEnvelope,
    operation_id="post_control_center_communications_matrix_credential_delete",
)
def post_control_center_communications_matrix_credential_delete(
    payload: MatrixSessionOperationRequest,
    response: Response,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias=IDEMPOTENCY_KEY_HEADER
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias=IDEMPOTENCY_REF_HEADER
    ),
) -> ResultEnvelope:
    return _run_mutating_session_route(
        MatrixSessionOperation.credential_delete,
        payload,
        response,
        x_uaa_idempotency_key,
        x_uaa_idempotency_ref,
    )


def _matrix_messaging_api_handler(
    operation: MatrixMessagingOperation,
) -> Callable[..., ResultEnvelope]:
    def handler(
        payload: MatrixMessagingOperationRequest,
        response: Response,
        x_uaa_idempotency_key: str | None = Header(
            default=None, alias=IDEMPOTENCY_KEY_HEADER
        ),
        x_uaa_idempotency_ref: str | None = Header(
            default=None, alias=IDEMPOTENCY_REF_HEADER
        ),
    ) -> ResultEnvelope:
        return _run_matrix_messaging_operation(
            operation,
            payload,
            response,
            x_uaa_idempotency_key,
            x_uaa_idempotency_ref,
        )

    handler.__name__ = (
        f"post_control_center_communications_matrix_messaging_{operation.value}"
    )
    return handler


for _messaging_operation in MatrixMessagingOperation:
    _messaging_slug = _messaging_operation.value.replace("_", "-")
    router.add_api_route(
        f"/matrix-messaging/{_messaging_slug}",
        _matrix_messaging_api_handler(_messaging_operation),
        methods=["POST"],
        response_model=ResultEnvelope,
        operation_id=(
            "post_control_center_communications_matrix_messaging_"
            f"{_messaging_operation.value}"
        ),
    )


def _matrix_rooms_media_api_handler(
    operation: MatrixRoomsMediaOperation,
) -> Callable[..., ResultEnvelope]:
    def handler(
        payload: MatrixRoomsMediaOperationRequest,
        response: Response,
        x_uaa_idempotency_key: str | None = Header(
            default=None, alias=IDEMPOTENCY_KEY_HEADER
        ),
        x_uaa_idempotency_ref: str | None = Header(
            default=None, alias=IDEMPOTENCY_REF_HEADER
        ),
    ) -> ResultEnvelope:
        return _run_matrix_rooms_media_operation(
            operation, payload, response, x_uaa_idempotency_key, x_uaa_idempotency_ref
        )

    handler.__name__ = (
        f"post_control_center_communications_matrix_rooms_media_{operation.value}"
    )
    return handler


for _rooms_media_operation in MatrixRoomsMediaOperation:
    _rooms_media_slug = _rooms_media_operation.value.replace("_", "-")
    router.add_api_route(
        f"/matrix-rooms-media/{_rooms_media_slug}",
        _matrix_rooms_media_api_handler(_rooms_media_operation),
        methods=["POST"],
        response_model=ResultEnvelope,
        operation_id=f"post_control_center_communications_matrix_rooms_media_{_rooms_media_operation.value}",
    )


def _matrix_intelligence_api_handler(
    operation: MatrixIntelligenceOperation,
) -> Callable[..., ResultEnvelope]:
    def handler(
        payload: MatrixIntelligenceOperationRequest,
        response: Response,
        x_uaa_idempotency_key: str | None = Header(
            default=None, alias=IDEMPOTENCY_KEY_HEADER
        ),
        x_uaa_idempotency_ref: str | None = Header(
            default=None, alias=IDEMPOTENCY_REF_HEADER
        ),
    ) -> ResultEnvelope:
        return _run_matrix_intelligence_operation(
            operation,
            payload,
            response,
            x_uaa_idempotency_key,
            x_uaa_idempotency_ref,
        )

    handler.__name__ = (
        f"post_control_center_communications_matrix_intelligence_{operation.value}"
    )
    return handler


for _intelligence_operation in MatrixIntelligenceOperation:
    _intelligence_slug = _intelligence_operation.value.replace("_", "-")
    router.add_api_route(
        f"/matrix-intelligence/{_intelligence_slug}",
        _matrix_intelligence_api_handler(_intelligence_operation),
        methods=["POST"],
        response_model=ResultEnvelope,
        operation_id=(
            "post_control_center_communications_matrix_intelligence_"
            f"{_intelligence_operation.value}"
        ),
    )


def register_communications_routes(app: FastAPI) -> None:
    register_router_once(app, router, state_attr=_REGISTERED_ATTR)
