from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, FastAPI, Header

from ultimate_ai_agent.api.route_registration import register_router_once
from ultimate_ai_agent.core.hygiene.envelopes import (
    ErrorCategory,
    ErrorEnvelope,
    ResultEnvelope,
    Severity,
)
from ultimate_ai_agent.core.runtime_gateway import (
    RuntimeInvocationConflictError,
    RuntimeInvocationNotFoundError,
    RuntimeInvocationRequest,
    RuntimeInvocationStore,
    build_default_runtime_capabilities,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    GOVERNED_RUNTIME_REDACTIONS,
    RuntimeApprovalBindingRequest,
    RuntimeExecuteRequest,
    RuntimeSafeDisableRequest,
)


router = APIRouter(prefix="/api/runtime", tags=["governed-runtime"])
_REGISTERED_ATTR = "_uaa_governed_runtime_routes_registered"
_RuntimeStoreGetter = Callable[[], RuntimeInvocationStore]
_runtime_store_getter: _RuntimeStoreGetter | None = None


def _default_runtime_store() -> RuntimeInvocationStore:
    return RuntimeInvocationStore()


def _runtime_store() -> RuntimeInvocationStore:
    if _runtime_store_getter is None:
        return _default_runtime_store()
    return _runtime_store_getter()


def _idempotency_ref(
    key: str | None,
    ref: str | None,
) -> str:
    candidate = (ref or key or "").strip()
    if candidate:
        return candidate
    return "idempotency-ref:governed-runtime-missing"


def _not_found(operation: str, invocation_ref: str) -> ResultEnvelope:
    return ResultEnvelope(
        success=False,
        operation=operation,
        service="GovernedRuntimeAPI",
        trace_id=invocation_ref,
        error=ErrorEnvelope(
            code="RUNTIME_INVOCATION_NOT_FOUND",
            category=ErrorCategory.not_found,
            safe_message="The governed runtime invocation ref was not found.",
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="GovernedRuntimeAPI",
        ),
        redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
    )


@router.get("/capabilities", response_model=ResultEnvelope)
def get_api_runtime_capabilities() -> ResultEnvelope:
    capabilities = build_default_runtime_capabilities()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_capabilities",
        service="GovernedRuntimeAPI",
        trace_id=capabilities.capabilities_ref,
        data=capabilities.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:governed-runtime-capabilities"}],
        redactions_applied=capabilities.redactions_applied,
    )


@router.get("/invocations", response_model=ResultEnvelope)
def get_api_runtime_invocations() -> ResultEnvelope:
    store = _runtime_store()
    records = [record.model_dump(mode="json") for record in store.list_invocations()]
    return ResultEnvelope(
        success=True,
        operation="api_runtime_invocations",
        service="GovernedRuntimeAPI",
        trace_id=store.capabilities_storage_ref(),
        data={
            "schema_version": "governed_runtime_invocation_index.v1",
            "source": "python_core_runtime_gateway_store",
            "backend_owned": True,
            "safe_refs_only": True,
            "adapter_execution_enabled": False,
            "invocation_count": len(records),
            "invocations": records,
        },
        redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
    )


@router.post("/invocations", response_model=ResultEnvelope)
def post_api_runtime_invocations(
    request: RuntimeInvocationRequest,
    x_uaa_idempotency_key: str | None = Header(default=None, alias="x-uaa-idempotency-key"),
    x_uaa_idempotency_ref: str | None = Header(default=None, alias="x-uaa-idempotency-ref"),
) -> ResultEnvelope:
    store = _runtime_store()
    try:
        result = store.create_invocation(
            request,
            idempotency_ref=_idempotency_ref(x_uaa_idempotency_key, x_uaa_idempotency_ref),
        )
    except RuntimeInvocationConflictError:
        return ResultEnvelope(
            success=False,
            operation="api_runtime_invocation_create",
            service="GovernedRuntimeAPI",
            trace_id=_idempotency_ref(x_uaa_idempotency_key, x_uaa_idempotency_ref),
            error=ErrorEnvelope(
                code="RUNTIME_INVOCATION_IDEMPOTENCY_CONFLICT",
                category=ErrorCategory.conflict,
                safe_message="The governed runtime idempotency ref already has a different payload fingerprint.",
                severity=Severity.medium,
                retryable=False,
                details_redacted=True,
                source="GovernedRuntimeAPI",
            ),
            redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
        )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_invocation_create",
        service="GovernedRuntimeAPI",
        trace_id=result.record.invocation_ref,
        data={
            "record": result.record.model_dump(mode="json"),
            "replayed": result.replayed,
            "execution_performed": False,
            "adapter_execution_enabled": False,
        },
        evidence=[{"evidence_ref": "evidence-ref:governed-runtime-invocation-recorded"}],
        redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
    )


@router.get("/invocations/{id}", response_model=ResultEnvelope)
def get_api_runtime_invocations_id(id: str) -> ResultEnvelope:
    try:
        record = _runtime_store().get_invocation(id)
    except RuntimeInvocationNotFoundError:
        return _not_found("api_runtime_invocation_detail", id)
    return ResultEnvelope(
        success=True,
        operation="api_runtime_invocation_detail",
        service="GovernedRuntimeAPI",
        trace_id=record.invocation_ref,
        data=record.model_dump(mode="json"),
        redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
    )


@router.get("/invocations/{id}/receipt", response_model=ResultEnvelope)
def get_api_runtime_invocations_id_receipt(id: str) -> ResultEnvelope:
    try:
        record = _runtime_store().get_invocation(id)
    except RuntimeInvocationNotFoundError:
        return _not_found("api_runtime_invocation_receipt", id)
    return ResultEnvelope(
        success=record.receipt is not None,
        operation="api_runtime_invocation_receipt",
        service="GovernedRuntimeAPI",
        trace_id=record.invocation_ref,
        data={
            "receipt": record.receipt.model_dump(mode="json") if record.receipt else None,
            "receipt_available": record.receipt is not None,
            "execution_performed": False,
        },
        warnings=[] if record.receipt else ["RUNTIME_RECEIPT_NOT_RECORDED_YET"],
        redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
    )


@router.post("/invocations/{id}/approve", response_model=ResultEnvelope)
def post_api_runtime_invocations_id_approve(
    id: str,
    request: RuntimeApprovalBindingRequest,
    x_uaa_idempotency_key: str | None = Header(default=None, alias="x-uaa-idempotency-key"),
    x_uaa_idempotency_ref: str | None = Header(default=None, alias="x-uaa-idempotency-ref"),
) -> ResultEnvelope:
    try:
        record = _runtime_store().bind_approval(
            id,
            request,
            idempotency_ref=_idempotency_ref(x_uaa_idempotency_key, x_uaa_idempotency_ref),
        )
    except RuntimeInvocationNotFoundError:
        return _not_found("api_runtime_invocation_approve", id)
    except RuntimeInvocationConflictError:
        return ResultEnvelope(
            success=False,
            operation="api_runtime_invocation_approve",
            service="GovernedRuntimeAPI",
            trace_id=_idempotency_ref(x_uaa_idempotency_key, x_uaa_idempotency_ref),
            error=ErrorEnvelope(
                code="RUNTIME_INVOCATION_IDEMPOTENCY_CONFLICT",
                category=ErrorCategory.conflict,
                safe_message="The governed runtime idempotency ref already has a different payload fingerprint.",
                severity=Severity.medium,
                retryable=False,
                details_redacted=True,
                source="GovernedRuntimeAPI",
            ),
            redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
        )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_invocation_approve",
        service="GovernedRuntimeAPI",
        trace_id=record.invocation_ref,
        data={
            "record": record.model_dump(mode="json"),
            "approval_ref_is_identifier_only": True,
            "execution_performed": False,
            "adapter_execution_enabled": False,
        },
        evidence=[{"evidence_ref": "evidence-ref:governed-runtime-approval-binding"}],
        redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
    )


@router.post("/invocations/{id}/execute", response_model=ResultEnvelope)
def post_api_runtime_invocations_id_execute(
    id: str,
    request: RuntimeExecuteRequest,
    x_uaa_idempotency_key: str | None = Header(default=None, alias="x-uaa-idempotency-key"),
    x_uaa_idempotency_ref: str | None = Header(default=None, alias="x-uaa-idempotency-ref"),
) -> ResultEnvelope:
    try:
        record = _runtime_store().record_blocked_execute(
            id,
            safe_summary=request.safe_summary,
            idempotency_ref=_idempotency_ref(x_uaa_idempotency_key, x_uaa_idempotency_ref),
        )
    except RuntimeInvocationNotFoundError:
        return _not_found("api_runtime_invocation_execute", id)
    except RuntimeInvocationConflictError:
        return ResultEnvelope(
            success=False,
            operation="api_runtime_invocation_execute",
            service="GovernedRuntimeAPI",
            trace_id=_idempotency_ref(x_uaa_idempotency_key, x_uaa_idempotency_ref),
            error=ErrorEnvelope(
                code="RUNTIME_INVOCATION_IDEMPOTENCY_CONFLICT",
                category=ErrorCategory.conflict,
                safe_message="The governed runtime idempotency ref already has a different payload fingerprint.",
                severity=Severity.medium,
                retryable=False,
                details_redacted=True,
                source="GovernedRuntimeAPI",
            ),
            redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
        )
    return ResultEnvelope(
        success=False,
        operation="api_runtime_invocation_execute",
        service="GovernedRuntimeAPI",
        trace_id=record.invocation_ref,
        data={
            "record": record.model_dump(mode="json"),
            "execution_performed": False,
            "adapter_execution_enabled": False,
            "blocked_reason": "RUNTIME_ADAPTER_EXECUTION_BLOCKED_IN_PHASE_02",
        },
        evidence=[{"evidence_ref": "evidence-ref:governed-runtime-execution-blocked"}],
        redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
    )


@router.post("/safe-disable", response_model=ResultEnvelope)
def post_api_runtime_safe_disable(
    request: RuntimeSafeDisableRequest,
    x_uaa_idempotency_key: str | None = Header(default=None, alias="x-uaa-idempotency-key"),
    x_uaa_idempotency_ref: str | None = Header(default=None, alias="x-uaa-idempotency-ref"),
) -> ResultEnvelope:
    try:
        state = _runtime_store().safe_disable(
            request,
            idempotency_ref=_idempotency_ref(x_uaa_idempotency_key, x_uaa_idempotency_ref),
        )
    except RuntimeInvocationConflictError:
        return ResultEnvelope(
            success=False,
            operation="api_runtime_safe_disable",
            service="GovernedRuntimeAPI",
            trace_id=_idempotency_ref(x_uaa_idempotency_key, x_uaa_idempotency_ref),
            error=ErrorEnvelope(
                code="RUNTIME_INVOCATION_IDEMPOTENCY_CONFLICT",
                category=ErrorCategory.conflict,
                safe_message="The governed runtime idempotency ref already has a different payload fingerprint.",
                severity=Severity.medium,
                retryable=False,
                details_redacted=True,
                source="GovernedRuntimeAPI",
            ),
            redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
        )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_safe_disable",
        service="GovernedRuntimeAPI",
        trace_id=state.safe_disable_ref,
        data={
            "safe_disable": state.model_dump(mode="json"),
            "adapter_execution_enabled": False,
            "execution_performed": False,
        },
        evidence=[{"evidence_ref": "evidence-ref:governed-runtime-safe-disable"}],
        rollback_ref=state.safe_disable_posture_ref,
        redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
    )


def register_governed_runtime_routes(
    app: FastAPI,
    *,
    runtime_store_getter: _RuntimeStoreGetter | None = None,
) -> None:
    global _runtime_store_getter
    _runtime_store_getter = runtime_store_getter
    register_router_once(app, router, state_attr=_REGISTERED_ATTR)
