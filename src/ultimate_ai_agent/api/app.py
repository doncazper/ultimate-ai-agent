from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from ultimate_ai_agent import __version__
from ultimate_ai_agent.core.contracts import (
    ExecutionContract,
    ContextPack,
    validate_execution_contract,
    validate_context_pack,
)
from ultimate_ai_agent.core.ledger import (
    EventLedgerEvent,
    RunState,
    DeterministicRunState,
    InvalidStateTransitionError,
    generate_receipt_from_events,
)
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope, ErrorEnvelope, ErrorCategory, Severity

# Import M2.5 contracts for API boundary
from ultimate_ai_agent.core.world_state import StructuredWorldState, validate_world_state_secrets
from ultimate_ai_agent.core.context_budget import ContextBudget, validate_context_budget
from ultimate_ai_agent.core.runtime import LocalRuntimeManifest, PrivacyRoutingPolicy, validate_runtime_safety
from ultimate_ai_agent.core.adapters import AgentRuntimeAdapterManifest, SDKAdapterBoundaryPolicy, validate_adapter_boundary_policy

app = FastAPI(
    title="Ultimate AI Agent API Boundary",
    version=__version__,
    description="The secure control boundary for the Ultimate AI Agent"
)

class HealthResponse(BaseModel):
    status: str
    version: str

class TransitionRequest(BaseModel):
    run_id: str
    current_state: RunState
    next_state: RunState

class ReceiptPreviewRequest(BaseModel):
    run_id: str
    events: List[EventLedgerEvent]

@app.get("/health", response_model=HealthResponse)
def get_health():
    return {"status": "healthy", "version": __version__}

@app.get("/version")
def get_version():
    return {"version": __version__}

@app.post("/contracts/validate", response_model=ResultEnvelope)
def post_validate_contract(contract: ExecutionContract):
    return validate_execution_contract(contract)

@app.post("/context-packs/validate", response_model=ResultEnvelope)
def post_validate_context_pack(pack: ContextPack):
    return validate_context_pack(pack)

@app.post("/events/validate", response_model=ResultEnvelope)
def post_validate_event(event: EventLedgerEvent):
    # Basic structural and type validation is done by Pydantic model payload validation.
    # Check for payload secrets just in case
    from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets
    if scan_payload_for_secrets(event.model_dump()):
        err = ErrorEnvelope(
            code="SECRET_EXPOSURE_BLOCKED",
            category=ErrorCategory.security_blocked,
            safe_message="Event validation failed: secrets detected in event payload",
            severity=Severity.critical,
            retryable=False,
            details_redacted=False,
            source="LedgerAPI"
        )
        return ResultEnvelope(
            success=False,
            operation="validate_event",
            service="LedgerAPI",
            trace_id=event.run_id,
            error=err
        )

    return ResultEnvelope(
        success=True,
        operation="validate_event",
        service="LedgerAPI",
        trace_id=event.run_id,
        data={"event_id": event.event_id, "status": "validated"}
    )

@app.post("/runs/state/transition/validate", response_model=ResultEnvelope)
def post_validate_transition(req: TransitionRequest):
    try:
        state = DeterministicRunState(run_id=req.run_id, current_state=req.current_state)
        state.transition_to(req.next_state)
        return ResultEnvelope(
            success=True,
            operation="validate_transition",
            service="LedgerAPI",
            trace_id=req.run_id,
            data={"run_id": req.run_id, "status": "valid", "new_state": req.next_state}
        )
    except InvalidStateTransitionError as e:
        err = ErrorEnvelope(
            code="INVALID_STATE_TRANSITION",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=False,
            source="LedgerAPI"
        )
        return ResultEnvelope(
            success=False,
            operation="validate_transition",
            service="LedgerAPI",
            trace_id=req.run_id,
            error=err
        )

@app.post("/receipts/preview", response_model=ResultEnvelope)
def post_preview_receipt(req: ReceiptPreviewRequest):
    try:
        receipt = generate_receipt_from_events(req.run_id, req.events)
        return ResultEnvelope(
            success=True,
            operation="preview_receipt",
            service="LedgerAPI",
            trace_id=req.run_id,
            data=receipt.model_dump()
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="RECEIPT_COMPILATION_FAILED",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=False,
            source="LedgerAPI"
        )
        return ResultEnvelope(
            success=False,
            operation="preview_receipt",
            service="LedgerAPI",
            trace_id=req.run_id,
            error=err
        )



class RuntimeValidateRequest(BaseModel):
    manifest: LocalRuntimeManifest
    policy: Optional[PrivacyRoutingPolicy] = None

class AdapterValidateRequest(BaseModel):
    manifest: AgentRuntimeAdapterManifest
    policy: SDKAdapterBoundaryPolicy

@app.post("/world-state/validate", response_model=ResultEnvelope)
def post_validate_world_state(state: StructuredWorldState):
    if not validate_world_state_secrets(state):
        err = ErrorEnvelope(
            code="WORLD_STATE_SECRET_EXPOSURE",
            category=ErrorCategory.security_blocked,
            safe_message="World State validation failed: secrets detected in payload",
            severity=Severity.critical,
            retryable=False,
            details_redacted=False,
            source="CoreAPI"
        )
        return ResultEnvelope(
            success=False,
            operation="validate_world_state",
            service="CoreAPI",
            trace_id=state.run_id,
            error=err
        )
    return ResultEnvelope(
        success=True,
        operation="validate_world_state",
        service="CoreAPI",
        trace_id=state.run_id,
        data={"world_state_id": state.world_state_id, "status": "validated"}
    )

@app.post("/context-budget/validate", response_model=ResultEnvelope)
def post_validate_budget(budget: ContextBudget):
    try:
        validate_context_budget(budget)
        return ResultEnvelope(
            success=True,
            operation="validate_context_budget",
            service="CoreAPI",
            trace_id="system",
            data={"status": "validated", "available_history_tokens": budget.available_history_tokens}
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="CONTEXT_BUDGET_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=False,
            source="CoreAPI"
        )
        return ResultEnvelope(
            success=False,
            operation="validate_context_budget",
            service="CoreAPI",
            trace_id="system",
            error=err
        )

@app.post("/local-runtime/validate", response_model=ResultEnvelope)
def post_validate_local_runtime(req: RuntimeValidateRequest):
    try:
        policy = req.policy or PrivacyRoutingPolicy(policy_id="default_policy", allowed_modes=["local_only"])
        validate_runtime_safety(req.manifest, policy)
        return ResultEnvelope(
            success=True,
            operation="validate_local_runtime",
            service="CoreAPI",
            trace_id="system",
            data={"runtime_id": req.manifest.runtime_id, "status": "validated"}
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="LOCAL_RUNTIME_UNSAFE",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=False,
            source="CoreAPI"
        )
        return ResultEnvelope(
            success=False,
            operation="validate_local_runtime",
            service="CoreAPI",
            trace_id="system",
            error=err
        )

@app.post("/adapter-manifest/validate", response_model=ResultEnvelope)
def post_validate_adapter_manifest(req: AdapterValidateRequest):
    try:
        validate_adapter_boundary_policy(req.manifest, req.policy)
        return ResultEnvelope(
            success=True,
            operation="validate_adapter_manifest",
            service="CoreAPI",
            trace_id="system",
            data={"adapter_id": req.manifest.adapter_id, "status": "validated"}
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="ADAPTER_POLICY_VIOLATION",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.critical,
            retryable=False,
            details_redacted=False,
            source="CoreAPI"
        )
        return ResultEnvelope(
            success=False,
            operation="validate_adapter_manifest",
            service="CoreAPI",
            trace_id="system",
            error=err
        )

