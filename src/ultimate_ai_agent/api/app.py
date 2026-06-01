from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic import ValidationError
from datetime import datetime
from ultimate_ai_agent.core.time import utc_now
from typing import List, Optional

from ultimate_ai_agent import __version__
from ultimate_ai_agent.api.contracts import ApiManifest
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.api.openapi import configure_openapi_contract
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
from ultimate_ai_agent.core.approvals import (
    ApprovalGrant,
    ApprovalReceipt,
    ApprovalRequest,
    ApprovalValidationRequest,
    LocalApprovalAuthority,
)

# Import M2.5 contracts for API boundary
from ultimate_ai_agent.core.world_state import StructuredWorldState, validate_world_state_secrets
from ultimate_ai_agent.core.context_budget import ContextBudget, validate_context_budget
from ultimate_ai_agent.core.runtime import LocalRuntimeManifest, PrivacyRoutingPolicy, validate_runtime_safety
from ultimate_ai_agent.core.adapters import AgentRuntimeAdapterManifest, SDKAdapterBoundaryPolicy, validate_adapter_boundary_policy

# Import M3 contracts for API boundary
from ultimate_ai_agent.core.consent import ConsentGrant, ConsentQuery, ConsentLedger, validate_consent_grant
from ultimate_ai_agent.core.tools import ToolManifest, ToolRequest, ToolBroker, ToolRegistry, CapabilityFirewallPolicy, validate_tool_manifest
from ultimate_ai_agent.core.secrets import (
    CredentialReference,
    SecretAccessRequest,
    SecretBroker,
    validate_credential_reference,
)
from ultimate_ai_agent.core.providers import (
    ProviderCapability,
    ProviderDomain,
    ProviderManifest,
    ProviderRegistry,
    ProviderResolver,
    ProviderResultEnvelope,
    ProviderSelectionPolicy,
    validate_provider_manifest,
    validate_provider_result_envelope,
)
from ultimate_ai_agent.core.memory import (
    MemoryReadRequest,
    MemoryRecord,
    MemoryStore,
    MemoryWriteRequest,
    validate_memory_record,
)
from ultimate_ai_agent.core.files import (
    FileKind,
    FileReadRequest,
    FileRef,
    FileSensitivity,
    FileWriteProposal,
    LocalFileManager,
)
from ultimate_ai_agent.core.truth import (
    EvidenceItem,
    EvidenceManifest,
    FreshnessPolicy,
    GroundingPolicy,
    SourceConflictReport,
    TruthRouteRequest,
    TruthSourceManifest,
    TruthSourceRouter,
    classify_freshness,
    enforce_freshness_policy,
    validate_evidence_manifest,
    validate_truth_source_manifest,
)
from ultimate_ai_agent.core.kernel import MinimumKernelRunner
from ultimate_ai_agent.core.gate import (
    FoundationGateReport,
    ShadowReplayScenario,
    validate_foundation_gate_report,
    validate_shadow_replay_scenario,
)
from ultimate_ai_agent.core.costs import (
    CostBudget,
    CostEstimate,
    CostGovernor,
    validate_cost_budget,
)
from ultimate_ai_agent.core.model_router import (
    ModelCapabilityProfile,
    ModelRouteRequest,
    ModelRouter,
    validate_model_capability_profile,
)
from ultimate_ai_agent.core.model_runtime import (
    LocalLoopbackModelRuntimeAdapter,
    LoopbackRuntimeEndpoint,
    LoopbackRuntimePolicy,
    ModelRuntimeAdapterManifest,
    ModelRuntimeRequest,
    ModelRuntimeResponse,
    SimulatedModelRuntimeAdapter,
    validate_runtime_manifest,
    validate_runtime_request,
    validate_runtime_response,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like

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

class CostEstimatePreviewRequest(BaseModel):
    request: ModelRouteRequest
    profile: ModelCapabilityProfile

class CostEvaluateRequest(BaseModel):
    estimate: CostEstimate
    budgets: List[CostBudget]

class ModelRuntimeRequestValidatePayload(BaseModel):
    request: dict
    manifest: dict

class ModelRuntimeResponseValidatePayload(BaseModel):
    response: dict

class ModelRuntimeSimulatePayload(BaseModel):
    request: dict
    manifest: dict

class LocalLoopbackEndpointValidatePayload(BaseModel):
    endpoint: dict
    policy: Optional[dict] = None

class LocalLoopbackExecutionValidatePayload(BaseModel):
    request: dict
    manifest: dict
    endpoint: dict
    policy: Optional[dict] = None
    approval_decision: Optional[dict] = None

class ApprovalValidatePayload(BaseModel):
    validation_request: dict
    grants: List[dict] = []

def sanitize_validation_errors(errors: list[dict]) -> list[dict]:
    sanitized = []
    for error in errors:
        sanitized_error = {
            "type": error.get("type", "validation_error"),
            "loc": [_sanitize_validation_location(part) for part in error.get("loc", [])],
            "msg": error.get("msg", "Validation failed."),
        }
        if contains_secret_like(sanitized_error["msg"]):
            sanitized_error["msg"] = "Validation failed."
        sanitized.append(sanitized_error)
    return sanitized

def _sanitize_validation_location(part: object) -> str:
    text = str(part)
    sensitive_keys = {"api_key", "client_secret", "auth_token", "password", "private_key", "token", "secret"}
    normalized = text.lower().replace("-", "_")
    if normalized in sensitive_keys or contains_secret_like(text):
        return "[redacted]"
    return text

def safe_request_validation_error_response(request: Request, exc: RequestValidationError) -> JSONResponse:
    envelope = ResultEnvelope(
        success=False,
        operation="request_validation",
        service="API",
        trace_id="system",
        error=ErrorEnvelope(
            code="REQUEST_VALIDATION_FAILED",
            category=ErrorCategory.validation_error,
            safe_message="Request validation failed.",
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="FastAPI",
            caused_by=["RequestValidationError"],
            metadata={
                "path": request.url.path,
                "error_count": len(exc.errors()),
                "validation_errors": sanitize_validation_errors(exc.errors()),
            },
        ),
        redactions_applied=["validation_input"],
    )
    return JSONResponse(status_code=422, content=envelope.model_dump(mode="json"))

@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    return safe_request_validation_error_response(request, exc)

@app.get("/health", response_model=HealthResponse)
def get_health():
    return {"status": "healthy", "version": __version__}

@app.get("/version")
def get_version():
    return {"version": __version__}

@app.get("/api/manifest", response_model=ApiManifest)
def get_api_manifest():
    return build_api_manifest(app)

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

@app.post("/models/profiles/validate", response_model=ResultEnvelope)
def post_validate_model_profile(profile: ModelCapabilityProfile):
    try:
        validate_model_capability_profile(profile)
        return ResultEnvelope(
            success=True,
            operation="validate_model_profile",
            service="ModelRouterAPI",
            trace_id=profile.model_profile_id,
            data={"model_profile_id": profile.model_profile_id, "status": "validated"},
        )
    except Exception as e:
        return ResultEnvelope(
            success=False,
            operation="validate_model_profile",
            service="ModelRouterAPI",
            trace_id=profile.model_profile_id,
            error=ErrorEnvelope(
                code="MODEL_PROFILE_INVALID",
                category=ErrorCategory.validation_error,
                safe_message=str(e),
                severity=Severity.medium,
                retryable=False,
                details_redacted=True,
                source="ModelRouterAPI",
            ),
        )

@app.post("/models/route/preview", response_model=ResultEnvelope)
def post_preview_model_route(request: ModelRouteRequest):
    decision = ModelRouter().route(request)
    return ResultEnvelope(
        success=True,
        operation="preview_model_route",
        service="ModelRouterAPI",
        trace_id=request.run_id,
        data=decision.model_dump(mode="json"),
    )

def _model_runtime_validation_error(operation: str, trace_id: str, exc: Exception) -> ResultEnvelope:
    return ResultEnvelope(
        success=False,
        operation=operation,
        service="ModelRuntimeAPI",
        trace_id=trace_id,
        error=ErrorEnvelope(
            code="MODEL_RUNTIME_VALIDATION_FAILED",
            category=ErrorCategory.validation_error,
            safe_message="Model runtime payload validation failed.",
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="ModelRuntimeAPI",
            caused_by=[type(exc).__name__],
        ),
        redactions_applied=["invalid_payload"],
    )

def _approval_validation_error(operation: str, trace_id: str, exc: Exception) -> ResultEnvelope:
    return ResultEnvelope(
        success=False,
        operation=operation,
        service="ApprovalAPI",
        trace_id=trace_id,
        error=ErrorEnvelope(
            code="APPROVAL_VALIDATION_FAILED",
            category=ErrorCategory.validation_error,
            safe_message="Approval payload validation failed.",
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="ApprovalAPI",
            caused_by=[type(exc).__name__],
        ),
        redactions_applied=["invalid_payload"],
    )

@app.post("/approvals/requests/validate", response_model=ResultEnvelope)
def post_validate_approval_request(payload: dict):
    try:
        request = ApprovalRequest(**payload)
    except (ValidationError, ValueError) as exc:
        return _approval_validation_error("validate_approval_request", "system", exc)
    return ResultEnvelope(
        success=True,
        operation="validate_approval_request",
        service="ApprovalAPI",
        trace_id=request.trace_id or request.run_id,
        data={"approval_request_id": request.approval_request_id, "status": "validated"},
    )

@app.post("/approvals/grants/validate", response_model=ResultEnvelope)
def post_validate_approval_grant(payload: dict):
    try:
        grant = ApprovalGrant(**payload)
    except (ValidationError, ValueError) as exc:
        return _approval_validation_error("validate_approval_grant", "system", exc)
    return ResultEnvelope(
        success=True,
        operation="validate_approval_grant",
        service="ApprovalAPI",
        trace_id=grant.trace_id or grant.run_id,
        data={"approval_ref": grant.approval_ref, "status": "validated"},
    )

@app.post("/approvals/validate", response_model=ResultEnvelope)
def post_validate_approval(payload: ApprovalValidatePayload):
    try:
        validation_request = ApprovalValidationRequest(**payload.validation_request)
        authority = LocalApprovalAuthority()
        for grant_payload in payload.grants:
            grant = ApprovalGrant(**grant_payload)
            authority._grants[grant.approval_ref] = grant
        decision = authority.validate(validation_request)
    except (ValidationError, ValueError) as exc:
        return _approval_validation_error("validate_approval", "system", exc)
    return ResultEnvelope(
        success=True,
        operation="validate_approval",
        service="ApprovalAPI",
        trace_id=validation_request.event_ref or validation_request.run_id,
        data=decision.model_dump(mode="json"),
    )

@app.post("/approvals/receipts/validate", response_model=ResultEnvelope)
def post_validate_approval_receipt(payload: dict):
    try:
        receipt = ApprovalReceipt(**payload)
    except (ValidationError, ValueError) as exc:
        return _approval_validation_error("validate_approval_receipt", "system", exc)
    return ResultEnvelope(
        success=True,
        operation="validate_approval_receipt",
        service="ApprovalAPI",
        trace_id=receipt.event_ref or receipt.run_id,
        data={"receipt_id": receipt.receipt_id, "status": "validated"},
    )

@app.post("/model-runtime/manifests/validate", response_model=ResultEnvelope)
def post_validate_model_runtime_manifest(manifest: dict):
    try:
        manifest = ModelRuntimeAdapterManifest(**manifest)
    except (ValidationError, ValueError) as exc:
        return _model_runtime_validation_error("validate_model_runtime_manifest", "system", exc)
    return validate_runtime_manifest(manifest)

@app.post("/model-runtime/requests/validate", response_model=ResultEnvelope)
def post_validate_model_runtime_request(payload: ModelRuntimeRequestValidatePayload):
    try:
        request = ModelRuntimeRequest(**payload.request)
        manifest = ModelRuntimeAdapterManifest(**payload.manifest)
    except (ValidationError, ValueError) as exc:
        return _model_runtime_validation_error("validate_model_runtime_request", "system", exc)
    return validate_runtime_request(request, manifest)

@app.post("/model-runtime/responses/validate", response_model=ResultEnvelope)
def post_validate_model_runtime_response(payload: ModelRuntimeResponseValidatePayload):
    try:
        response = ModelRuntimeResponse(**payload.response)
    except (ValidationError, ValueError) as exc:
        return _model_runtime_validation_error("validate_model_runtime_response", "system", exc)
    return validate_runtime_response(response)

@app.post("/model-runtime/simulate", response_model=ResultEnvelope)
def post_simulate_model_runtime(payload: ModelRuntimeSimulatePayload):
    try:
        request = ModelRuntimeRequest(**payload.request)
        manifest = ModelRuntimeAdapterManifest(**payload.manifest)
    except (ValidationError, ValueError) as exc:
        return _model_runtime_validation_error("simulate_model_runtime", "system", exc)
    response = SimulatedModelRuntimeAdapter().simulate_response(request, manifest)
    return ResultEnvelope(
        success=response.status in {"simulated_success", "simulated_refusal"},
        operation="simulate_model_runtime",
        service="ModelRuntimeAPI",
        trace_id=request.trace_id or request.run_id,
        data=response.model_dump(mode="json"),
    )

@app.post("/model-runtime/local/endpoints/validate", response_model=ResultEnvelope)
def post_validate_local_loopback_endpoint(payload: LocalLoopbackEndpointValidatePayload):
    try:
        endpoint = LoopbackRuntimeEndpoint(**payload.endpoint)
        policy = LoopbackRuntimePolicy(**(payload.policy or {"policy_id": "api_default"}))
    except (ValidationError, ValueError) as exc:
        return _model_runtime_validation_error("validate_local_loopback_endpoint", "system", exc)
    decision = LocalLoopbackModelRuntimeAdapter().validate_endpoint(endpoint, policy)
    return ResultEnvelope(
        success=decision.allowed,
        operation="validate_local_loopback_endpoint",
        service="ModelRuntimeAPI",
        trace_id=endpoint.endpoint_id,
        data=decision.model_dump(mode="json"),
    )

@app.post("/model-runtime/local/execution/validate", response_model=ResultEnvelope)
def post_validate_local_loopback_execution(payload: LocalLoopbackExecutionValidatePayload):
    try:
        request = ModelRuntimeRequest(**payload.request)
        manifest = ModelRuntimeAdapterManifest(**payload.manifest)
        endpoint = LoopbackRuntimeEndpoint(**payload.endpoint)
        policy = LoopbackRuntimePolicy(**(payload.policy or {"policy_id": "api_default"}))
        approval_decision = None
        if payload.approval_decision is not None:
            from ultimate_ai_agent.core.approvals import ApprovalValidationDecision

            approval_decision = ApprovalValidationDecision(**payload.approval_decision)
    except (ValidationError, ValueError) as exc:
        return _model_runtime_validation_error("validate_local_loopback_execution", "system", exc)
    decision = LocalLoopbackModelRuntimeAdapter().validate_execution(request, manifest, endpoint, policy, approval_decision)
    return ResultEnvelope(
        success=decision.allowed,
        operation="validate_local_loopback_execution",
        service="ModelRuntimeAPI",
        trace_id=request.trace_id or request.run_id,
        data=decision.model_dump(mode="json"),
    )

@app.post("/model-runtime/local/simulate-fallback", response_model=ResultEnvelope)
def post_local_loopback_simulated_fallback(payload: LocalLoopbackExecutionValidatePayload):
    try:
        request = ModelRuntimeRequest(**payload.request)
        manifest = ModelRuntimeAdapterManifest(**payload.manifest)
    except (ValidationError, ValueError) as exc:
        return _model_runtime_validation_error("simulate_local_loopback_fallback", "system", exc)
    response = LocalLoopbackModelRuntimeAdapter().fallback_simulated(request, manifest)
    return ResultEnvelope(
        success=True,
        operation="simulate_local_loopback_fallback",
        service="ModelRuntimeAPI",
        trace_id=request.trace_id or request.run_id,
        data=response.model_dump(mode="json"),
    )

@app.post("/costs/budgets/validate", response_model=ResultEnvelope)
def post_validate_cost_budget(budget: CostBudget):
    try:
        validate_cost_budget(budget)
        return ResultEnvelope(
            success=True,
            operation="validate_cost_budget",
            service="CostGovernorAPI",
            trace_id=budget.budget_id,
            data={"budget_id": budget.budget_id, "status": "validated"},
        )
    except Exception as e:
        return ResultEnvelope(
            success=False,
            operation="validate_cost_budget",
            service="CostGovernorAPI",
            trace_id=budget.budget_id,
            error=ErrorEnvelope(
                code="COST_BUDGET_INVALID",
                category=ErrorCategory.validation_error,
                safe_message=str(e),
                severity=Severity.medium,
                retryable=False,
                details_redacted=True,
                source="CostGovernorAPI",
            ),
        )

@app.post("/costs/estimate/preview", response_model=ResultEnvelope)
def post_preview_cost_estimate(payload: CostEstimatePreviewRequest):
    estimate = CostGovernor().estimate_route_cost(payload.request, payload.profile)
    return ResultEnvelope(
        success=True,
        operation="preview_cost_estimate",
        service="CostGovernorAPI",
        trace_id=payload.request.run_id,
        data=estimate.model_dump(mode="json"),
    )

@app.post("/costs/evaluate", response_model=ResultEnvelope)
def post_evaluate_cost(payload: CostEvaluateRequest):
    decision = CostGovernor().evaluate(payload.estimate, payload.budgets)
    return ResultEnvelope(
        success=True,
        operation="evaluate_cost",
        service="CostGovernorAPI",
        trace_id=payload.estimate.estimate_id,
        data=decision.model_dump(mode="json"),
    )

class ConsentEvaluateRequest(BaseModel):
    query: ConsentQuery
    grants: List[ConsentGrant]

class ToolEvaluateRequest(BaseModel):
    request: ToolRequest
    grants: List[ConsentGrant]
    tool: ToolManifest
    execution_contract: Optional[ExecutionContract] = None
    context_pack: Optional[ContextPack] = None
    firewall_policy: Optional[CapabilityFirewallPolicy] = None

class ToolDryRunRequest(BaseModel):
    request: ToolRequest
    tool: ToolManifest

class SecretAccessEvaluateRequest(BaseModel):
    reference: CredentialReference
    access_request: SecretAccessRequest
    secret_value: Optional[str] = None

class ProviderResolveRequest(BaseModel):
    domain: ProviderDomain
    capability: ProviderCapability
    policy: ProviderSelectionPolicy
    providers: List[ProviderManifest]
    credential_availability: Optional[dict[str, bool]] = None

class FileRefValidateRequest(BaseModel):
    file_ref: str
    path: str
    kind: FileKind
    sensitivity: FileSensitivity

class FileReadPreviewAPIRequest(BaseModel):
    workspace_root: str
    request: FileReadRequest

class FileWriteAPIRequest(BaseModel):
    workspace_root: str
    proposal: FileWriteProposal

class TruthFreshnessCheckRequest(BaseModel):
    evidence_item: EvidenceItem
    policy: FreshnessPolicy
    current_time: Optional[datetime] = None


@app.post("/gate/reports/validate", response_model=ResultEnvelope)
def post_validate_foundation_gate_report(report: FoundationGateReport):
    return validate_foundation_gate_report(report)


@app.post("/gate/shadow-replay/validate", response_model=ResultEnvelope)
def post_validate_shadow_replay_scenario(scenario: ShadowReplayScenario):
    return validate_shadow_replay_scenario(scenario)

@app.post("/consent/grants/validate", response_model=ResultEnvelope)
def post_validate_consent_grant(grant: ConsentGrant):
    try:
        validate_consent_grant(grant)
        return ResultEnvelope(
            success=True,
            operation="validate_consent_grant",
            service="ConsentAPI",
            trace_id="system",
            data={"consent_id": grant.consent_id, "status": "validated"}
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="CONSENT_GRANT_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=False,
            source="ConsentAPI"
        )
        return ResultEnvelope(
            success=False,
            operation="validate_consent_grant",
            service="ConsentAPI",
            trace_id="system",
            error=err
        )

@app.post("/consent/evaluate", response_model=ResultEnvelope)
def post_evaluate_consent(req: ConsentEvaluateRequest):
    try:
        ledger = ConsentLedger()
        for g in req.grants:
            ledger.add_grant(g)
        decision = ledger.evaluate(req.query)
        return ResultEnvelope(
            success=True,
            operation="evaluate_consent",
            service="ConsentAPI",
            trace_id=req.query.audit_ref.trace_id if req.query.audit_ref else "system",
            data=decision.model_dump()
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="CONSENT_EVALUATION_FAILED",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=False,
            source="ConsentAPI"
        )
        return ResultEnvelope(
            success=False,
            operation="evaluate_consent",
            service="ConsentAPI",
            trace_id=req.query.audit_ref.trace_id if req.query.audit_ref else "system",
            error=err
        )

@app.post("/tools/manifests/validate", response_model=ResultEnvelope)
def post_validate_tool_manifest(manifest: ToolManifest):
    try:
        validate_tool_manifest(manifest)
        return ResultEnvelope(
            success=True,
            operation="validate_tool_manifest",
            service="ToolBrokerAPI",
            trace_id="system",
            data={"tool_id": manifest.tool_id, "status": "validated"}
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="TOOL_MANIFEST_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=False,
            source="ToolBrokerAPI"
        )
        return ResultEnvelope(
            success=False,
            operation="validate_tool_manifest",
            service="ToolBrokerAPI",
            trace_id="system",
            error=err
        )

@app.post("/tools/requests/evaluate", response_model=ResultEnvelope)
def post_evaluate_tool_request(req: ToolEvaluateRequest):
    try:
        registry = ToolRegistry()
        registry.register_tool(req.tool)
        
        firewall = req.firewall_policy or CapabilityFirewallPolicy()
        broker = ToolBroker(registry=registry, firewall_policy=firewall)
        
        ledger = ConsentLedger()
        for g in req.grants:
            ledger.add_grant(g)
            
        decision = broker.evaluate_request(
            request=req.request,
            consent_ledger=ledger,
            execution_contract=req.execution_contract,
            context_pack=req.context_pack,
        )
        return ResultEnvelope(
            success=True,
            operation="evaluate_tool_request",
            service="ToolBrokerAPI",
            trace_id=req.request.run_id,
            data=decision.model_dump()
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="TOOL_EVALUATION_FAILED",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=False,
            source="ToolBrokerAPI"
        )
        return ResultEnvelope(
            success=False,
            operation="evaluate_tool_request",
            service="ToolBrokerAPI",
            trace_id=req.request.run_id,
            error=err
        )

@app.post("/tools/requests/dry-run", response_model=ResultEnvelope)
def post_tool_dry_run(req: ToolDryRunRequest):
    try:
        registry = ToolRegistry()
        registry.register_tool(req.tool)
        
        broker = ToolBroker(registry=registry, firewall_policy=CapabilityFirewallPolicy())
        plan = broker.dry_run(req.request)
        return ResultEnvelope(
            success=True,
            operation="tool_dry_run",
            service="ToolBrokerAPI",
            trace_id=req.request.run_id,
            data=plan.model_dump()
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="TOOL_DRY_RUN_FAILED",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=False,
            source="ToolBrokerAPI"
        )
        return ResultEnvelope(
            success=False,
            operation="tool_dry_run",
            service="ToolBrokerAPI",
            trace_id=req.request.run_id,
            error=err
        )

@app.post("/secrets/credentials/validate", response_model=ResultEnvelope)
def post_validate_credential_reference(reference: CredentialReference):
    try:
        validate_credential_reference(reference)
        return ResultEnvelope(
            success=True,
            operation="validate_credential_reference",
            service="SecretBrokerAPI",
            trace_id="system",
            data={"credential_ref": reference.credential_ref, "status": "validated"}
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="CREDENTIAL_REFERENCE_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="SecretBrokerAPI"
        )
        return ResultEnvelope(
            success=False,
            operation="validate_credential_reference",
            service="SecretBrokerAPI",
            trace_id="system",
            error=err
        )

@app.post("/secrets/access/evaluate", response_model=ResultEnvelope)
def post_evaluate_secret_access(req: SecretAccessEvaluateRequest):
    broker = SecretBroker()
    broker.register_credential(req.reference, secret_value=req.secret_value)
    decision = broker.request_secret(req.access_request)
    return ResultEnvelope(
        success=True,
        operation="evaluate_secret_access",
        service="SecretBrokerAPI",
        trace_id=req.access_request.event_ref or "system",
        data=decision.model_dump()
    )

@app.post("/providers/manifests/validate", response_model=ResultEnvelope)
def post_validate_provider_manifest(manifest: ProviderManifest):
    try:
        validate_provider_manifest(manifest)
        return ResultEnvelope(
            success=True,
            operation="validate_provider_manifest",
            service="ProviderRegistryAPI",
            trace_id="system",
            data={"provider_id": manifest.provider_id, "status": "validated"}
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="PROVIDER_MANIFEST_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="ProviderRegistryAPI"
        )
        return ResultEnvelope(
            success=False,
            operation="validate_provider_manifest",
            service="ProviderRegistryAPI",
            trace_id="system",
            error=err
        )

@app.post("/providers/resolve", response_model=ResultEnvelope)
def post_resolve_provider(req: ProviderResolveRequest):
    registry = ProviderRegistry()
    for provider in req.providers:
        registry.register_provider(provider)
    decision = ProviderResolver(registry).resolve(
        domain=req.domain,
        capability=req.capability,
        policy=req.policy,
        credential_availability=req.credential_availability,
    )
    return ResultEnvelope(
        success=True,
        operation="resolve_provider",
        service="ProviderRegistryAPI",
        trace_id="system",
        data=decision.model_dump()
    )

@app.post("/providers/results/validate", response_model=ResultEnvelope)
def post_validate_provider_result(envelope: ProviderResultEnvelope):
    if not validate_provider_result_envelope(envelope):
        err = ErrorEnvelope(
            code="PROVIDER_RESULT_SECRET_EXPOSURE",
            category=ErrorCategory.security_blocked,
            safe_message="Provider result validation failed: secrets detected in payload",
            severity=Severity.critical,
            retryable=False,
            details_redacted=True,
            source="ProviderRegistryAPI"
        )
        return ResultEnvelope(
            success=False,
            operation="validate_provider_result",
            service="ProviderRegistryAPI",
            trace_id=envelope.event_ref or "system",
            error=err
        )
    return ResultEnvelope(
        success=True,
        operation="validate_provider_result",
        service="ProviderRegistryAPI",
        trace_id=envelope.event_ref or "system",
        data={"result_id": envelope.result_id, "status": "validated"}
    )

@app.post("/memory/records/validate", response_model=ResultEnvelope)
def post_validate_memory_record(record: MemoryRecord):
    try:
        validate_memory_record(record)
        return ResultEnvelope(
            success=True,
            operation="validate_memory_record",
            service="MemoryAPI",
            trace_id=record.event_ref or "system",
            data={"memory_id": record.memory_id, "status": "validated"},
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="MEMORY_RECORD_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="MemoryAPI",
        )
        return ResultEnvelope(
            success=False,
            operation="validate_memory_record",
            service="MemoryAPI",
            trace_id=record.event_ref or "system",
            error=err,
        )

@app.post("/memory/write/evaluate", response_model=ResultEnvelope)
def post_evaluate_memory_write(request: MemoryWriteRequest):
    store = MemoryStore()
    decision = store.write_memory(request)
    return ResultEnvelope(
        success=True,
        operation="evaluate_memory_write",
        service="MemoryAPI",
        trace_id=request.run_id,
        data=decision.model_dump(),
    )

@app.post("/memory/query/preview", response_model=ResultEnvelope)
def post_preview_memory_query(request: MemoryReadRequest):
    store = MemoryStore()
    decision = store.search(request)
    return ResultEnvelope(
        success=True,
        operation="preview_memory_query",
        service="MemoryAPI",
        trace_id=request.run_id,
        data=decision.model_dump(),
    )

@app.post("/files/refs/validate", response_model=ResultEnvelope)
def post_validate_file_ref(req: FileRefValidateRequest):
    try:
        file_ref = FileRef(
            file_ref=req.file_ref,
            path=req.path,
            kind=req.kind,
            sensitivity=req.sensitivity,
        )
        return ResultEnvelope(
            success=True,
            operation="validate_file_ref",
            service="FileManagerAPI",
            trace_id="system",
            data={"file_ref": file_ref.file_ref, "status": "validated"},
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="FILE_REF_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="FileManagerAPI",
        )
        return ResultEnvelope(
            success=False,
            operation="validate_file_ref",
            service="FileManagerAPI",
            trace_id="system",
            error=err,
        )

@app.post("/files/read/preview", response_model=ResultEnvelope)
def post_preview_file_read(req: FileReadPreviewAPIRequest):
    try:
        preview = LocalFileManager(req.workspace_root).read_preview(req.request)
        return ResultEnvelope(
            success=True,
            operation="preview_file_read",
            service="FileManagerAPI",
            trace_id=req.request.run_id,
            data=preview.model_dump(),
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="FILE_READ_PREVIEW_FAILED",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="FileManagerAPI",
        )
        return ResultEnvelope(
            success=False,
            operation="preview_file_read",
            service="FileManagerAPI",
            trace_id=req.request.run_id,
            error=err,
        )

@app.post("/files/write/propose", response_model=ResultEnvelope)
def post_propose_file_write(req: FileWriteAPIRequest):
    decision = LocalFileManager(req.workspace_root).propose_write(req.proposal)
    return ResultEnvelope(
        success=True,
        operation="propose_file_write",
        service="FileManagerAPI",
        trace_id=req.proposal.run_id,
        data=decision.model_dump(),
    )

@app.post("/files/diff/preview", response_model=ResultEnvelope)
def post_preview_file_diff(req: FileWriteAPIRequest):
    try:
        diff = LocalFileManager(req.workspace_root).diff_preview(req.proposal)
        return ResultEnvelope(
            success=True,
            operation="preview_file_diff",
            service="FileManagerAPI",
            trace_id=req.proposal.run_id,
            data={"diff": diff},
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="FILE_DIFF_PREVIEW_FAILED",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="FileManagerAPI",
        )
        return ResultEnvelope(
            success=False,
            operation="preview_file_diff",
            service="FileManagerAPI",
            trace_id=req.proposal.run_id,
            error=err,
        )

@app.post("/truth/sources/validate", response_model=ResultEnvelope)
def post_validate_truth_source(source: TruthSourceManifest):
    try:
        validate_truth_source_manifest(source)
        return ResultEnvelope(
            success=True,
            operation="validate_truth_source",
            service="TruthSourceAPI",
            trace_id=source.event_ref or "system",
            data={"source_id": source.source_id, "status": "validated"},
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="TRUTH_SOURCE_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="TruthSourceAPI",
        )
        return ResultEnvelope(
            success=False,
            operation="validate_truth_source",
            service="TruthSourceAPI",
            trace_id=source.event_ref or "system",
            error=err,
            redactions_applied=["secret_value"],
        )

@app.post("/truth/grounding-policy/validate", response_model=ResultEnvelope)
def post_validate_grounding_policy(policy: GroundingPolicy):
    return ResultEnvelope(
        success=True,
        operation="validate_grounding_policy",
        service="TruthSourceAPI",
        trace_id="system",
        data={"policy_id": policy.policy_id, "status": "validated"},
    )

@app.post("/truth/evidence/validate", response_model=ResultEnvelope)
def post_validate_evidence_manifest(manifest: EvidenceManifest):
    try:
        validate_evidence_manifest(manifest)
        return ResultEnvelope(
            success=True,
            operation="validate_evidence_manifest",
            service="TruthSourceAPI",
            trace_id=manifest.trace_id or manifest.run_id,
            data={"manifest_id": manifest.manifest_id, "status": "validated"},
        )
    except Exception as e:
        err = ErrorEnvelope(
            code="EVIDENCE_MANIFEST_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=str(e),
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="TruthSourceAPI",
        )
        return ResultEnvelope(
            success=False,
            operation="validate_evidence_manifest",
            service="TruthSourceAPI",
            trace_id=manifest.trace_id or manifest.run_id,
            error=err,
            redactions_applied=["secret_value"],
        )

@app.post("/truth/route", response_model=ResultEnvelope)
def post_route_truth_source(request: TruthRouteRequest):
    decision = TruthSourceRouter().route(request)
    return ResultEnvelope(
        success=True,
        operation="route_truth_source",
        service="TruthSourceAPI",
        trace_id=request.run_id,
        data=decision.model_dump(),
    )

@app.post("/truth/freshness/check", response_model=ResultEnvelope)
def post_check_truth_freshness(request: TruthFreshnessCheckRequest):
    now = request.current_time or utc_now()
    status = classify_freshness(request.evidence_item, request.policy, now)
    allowed, reason = enforce_freshness_policy(request.evidence_item, request.policy, now)
    return ResultEnvelope(
        success=True,
        operation="check_truth_freshness",
        service="TruthSourceAPI",
        trace_id=request.evidence_item.event_ref or "system",
        data={
            "evidence_id": request.evidence_item.evidence_id,
            "freshness_status": status,
            "allowed": allowed,
            "reason": reason,
        },
    )

@app.post("/truth/conflicts/validate", response_model=ResultEnvelope)
def post_validate_source_conflict(conflict: SourceConflictReport):
    return ResultEnvelope(
        success=True,
        operation="validate_source_conflict",
        service="TruthSourceAPI",
        trace_id="system",
        data={"conflict_id": conflict.conflict_id, "status": "validated"},
    )

@app.post("/kernel/tasks/run", response_model=ResultEnvelope)
def post_run_kernel_task(payload: dict):
    result = MinimumKernelRunner().run_payload(payload)
    if result.success:
        return ResultEnvelope(
            success=True,
            operation="run_kernel_task",
            service="MinimumKernelAPI",
            trace_id=result.run_id,
            data=result.model_dump(),
        )

    return ResultEnvelope(
        success=False,
        operation="run_kernel_task",
        service="MinimumKernelAPI",
        trace_id=result.run_id,
        data=result.model_dump(),
        error=ErrorEnvelope(
            code=result.errors[0] if result.errors else "KERNEL_TASK_FAILED",
            category=ErrorCategory.validation_error,
            safe_message=result.safe_message,
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="MinimumKernelAPI",
        ),
        redactions_applied=result.redactions_applied,
    )


configure_openapi_contract(app)
