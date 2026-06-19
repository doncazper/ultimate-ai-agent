from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from pydantic import ValidationError
from datetime import datetime
import os
from pathlib import Path
from ultimate_ai_agent.core.time import utc_now
from typing import Any, List, Optional

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
    LegacyMemoryWriteRequest as MemoryWriteRequest,
    MemoryReadRequest,
    MemoryRecord,
    MemoryStore,
    validate_memory_record,
)
from ultimate_ai_agent.core.files import (
    FileKind,
    FileOperationStatus,
    FileReadRequest,
    FileRef,
    FileSensitivity,
    FileWriteDecision,
    LocalFileManager,
)
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
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
    ManualLoopbackSmokeRequest,
    ModelRuntimeAdapterManifest,
    ModelRuntimeRequest,
    ModelRuntimeResponse,
    SimulatedModelRuntimeAdapter,
    validate_manual_loopback_smoke_request,
    validate_runtime_manifest,
    validate_runtime_request,
    validate_runtime_response,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.remote_workers import (
    RemoteDryRunBuilder,
    RemoteExecutionPolicy,
    RemoteJobEnvelope,
    RemoteNode,
    RemoteTransportDescriptor,
    default_remote_node_registry,
    default_remote_transport_registry,
    evaluate_remote_job_policy,
)
from ultimate_ai_agent.core.runtime_readiness import (
    build_matrix,
    build_readiness_report,
    validate_manual_smoke_report,
)
from ultimate_ai_agent.core.control_center import (
    ControlCenterActionPreviewRequest,
    build_control_center_dashboard,
    build_control_center_manifest,
    preview_control_center_action,
)
from ultimate_ai_agent.core.file_review import (
    FileReviewApprovalCaptureRequest,
    FileReviewApprovalStore,
    capture_file_review_approval_request,
)
from ultimate_ai_agent.core.openwebui_bridge import (
    OpenWebUILocalChatCompletionRequest,
    build_openwebui_local_chat_completion_response,
    build_openwebui_local_models_response,
    openwebui_test_gateway_authorized,
    openwebui_test_gateway_enabled,
)
from ultimate_ai_agent.core.local_model_management import (
    M164ChatCompletionRequest,
    build_m164_chat_completion_response,
    build_m164_gateway_model_from_env,
    build_m164_local_models_response,
    llama_cpp_backend_api_key,
    llama_cpp_gateway_authorized,
    llama_cpp_gateway_enabled,
)
from ultimate_ai_agent.core.task_decomposition.runtime import (
    TaskCapabilityApprovalRequestPayload,
    TaskDecompositionApprovalGrantRequest,
    TaskDecompositionApprovalRevokeRequest,
    TaskDecompositionRegisterRequest,
    TaskDecompositionRequest,
    TaskDecompositionRunRequest,
    TaskDecompositionService,
    TaskPlanExecutionRequest,
    TaskPlanValidationRequest,
)
from ultimate_ai_agent.core.task_decomposition import api_safety as task_decomposition_api_safety

app = FastAPI(
    title="Ultimate AI Agent API Boundary",
    version=__version__,
    description="The secure control boundary for the Ultimate AI Agent"
)

_file_review_approval_store = FileReviewApprovalStore()
_task_decomposition_service = TaskDecompositionService.from_env()

FILE_API_DEFAULT_SAFE_ROOT_REF = "local_dev_workspace"
FILE_API_SAFE_ROOT_ENV = "UAA_FILE_API_SAFE_ROOT"
TASK_DECOMPOSITION_API_ENV = task_decomposition_api_safety.TASK_DECOMPOSITION_API_ENV
TASK_DECOMPOSITION_API_BEARER_ENV = task_decomposition_api_safety.TASK_DECOMPOSITION_API_BEARER_ENV

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

class LocalLoopbackSmokeValidatePayload(BaseModel):
    request: dict
    approval_decision: Optional[dict] = None

class V1ChatMessageAPIRequest(BaseModel):
    role: str
    content: str | None = None

    model_config = ConfigDict(extra="forbid")

class V1ChatCompletionAPIRequest(BaseModel):
    model: str
    messages: list[V1ChatMessageAPIRequest] = Field(..., min_length=1)
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = Field(default=None, ge=1, le=8192)
    tools: list[dict[str, Any]] | None = None
    tool_choice: Any = None
    functions: list[dict[str, Any]] | None = None
    function_call: Any = None

    model_config = ConfigDict(extra="forbid")

class RemoteNodeValidatePayload(BaseModel):
    node: dict

    model_config = ConfigDict(extra="forbid")

class RemoteTransportValidatePayload(BaseModel):
    transport: dict

    model_config = ConfigDict(extra="forbid")

class RemotePolicyValidatePayload(BaseModel):
    policy: dict

    model_config = ConfigDict(extra="forbid")

class RemoteJobValidatePayload(BaseModel):
    job: dict

    model_config = ConfigDict(extra="forbid")

class RemoteDryRunPayload(BaseModel):
    job: dict
    policy: Optional[dict] = None

    model_config = ConfigDict(extra="forbid")

class RuntimeSmokeReportValidatePayload(BaseModel):
    report: dict

    model_config = ConfigDict(extra="forbid")

class ApprovalValidatePayload(BaseModel):
    validation_request: dict
    grants: List[dict] = Field(default_factory=list)

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
    sensitive_keys = {
        "api_key",
        "auth_token",
        "client_secret",
        "credential_value",
        "password",
        "private_key",
        "raw_secret",
        "secret",
        "secret_value",
        "token",
    }
    normalized = text.lower().replace("-", "_")
    if normalized in sensitive_keys or contains_secret_like(text):
        return "[redacted]"
    return text


def safe_exception_message(code: str) -> str:
    return f"{code} failed safely; details are redacted."


def _file_api_safe_roots() -> dict[str, Path]:
    return {
        FILE_API_DEFAULT_SAFE_ROOT_REF: Path(os.environ.get(FILE_API_SAFE_ROOT_ENV, ".")).resolve(),
    }


def _file_manager_for_safe_root(safe_root_ref: str) -> LocalFileManager:
    if contains_secret_like(safe_root_ref) or "/" in safe_root_ref or "\\" in safe_root_ref:
        raise ValueError("FILE_SAFE_ROOT_REF_UNSAFE")
    safe_roots = _file_api_safe_roots()
    if safe_root_ref not in safe_roots:
        raise ValueError("FILE_SAFE_ROOT_REF_UNKNOWN")
    return LocalFileManager(safe_roots[safe_root_ref])


def _review_file_write_api_proposal(safe_root_ref: str, proposal: "FileWriteAPIProposal") -> FileWriteDecision:
    reason_codes: list[str] = []
    redactions = ["raw_content_omitted", "content_ref_only"]
    try:
        manager = _file_manager_for_safe_root(safe_root_ref)
        manager.validate_path(proposal.target_path)
    except ValueError:
        reason_codes.append("FILE_SAFE_ROOT_OR_PATH_BLOCKED")
    if not proposal.idempotency_key:
        reason_codes.append("IDEMPOTENCY_KEY_REQUIRED")
    if contains_secret_like(proposal.target_path) or contains_secret_like(proposal.new_content_ref):
        reason_codes.append("FILE_API_REF_UNSAFE")
    if proposal.sensitivity == FileSensitivity.credential_secret:
        reason_codes.append("CREDENTIAL_SECRET_FILE_REJECTED")

    allowed = not reason_codes
    return FileWriteDecision(
        decision_id=f"fwd_api_{proposal.proposal_id}",
        proposal_id=proposal.proposal_id,
        allowed=allowed,
        status=FileOperationStatus.proposed if allowed else FileOperationStatus.blocked,
        reason_codes=["WRITE_PROPOSAL_REF_ACCEPTED"] if allowed else reason_codes,
        safe_message="File write proposal ref is safe for review; raw content is omitted."
        if allowed
        else "The file write proposal ref was blocked.",
        diff_ref=f"diff_ref:{proposal.proposal_id}" if allowed else None,
        redactions_applied=redactions,
        event_ref=proposal.event_ref,
    )


def _require_task_decomposition_local_authority(authorization: str | None) -> None:
    error = task_decomposition_api_safety.task_decomposition_authority_error(authorization)
    if error is not None:
        status_code, detail = error
        raise HTTPException(status_code=status_code, detail=detail)


def _safe_task_decomposition_payload(payload: object, *, redact_read_refs: bool = False) -> object:
    return task_decomposition_api_safety.sanitize_task_decomposition_api_payload(
        payload,
        redact_read_refs=redact_read_refs,
    )


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

def _require_openwebui_local_test_gateway(authorization: str | None) -> None:
    if not openwebui_test_gateway_enabled():
        raise HTTPException(
            status_code=403,
            detail="M151 local OpenWebUI test gateway is disabled. Set UAA_OPENWEBUI_TEST_GATEWAY_ENABLED=1 for local smoke testing.",
        )
    if not openwebui_test_gateway_authorized(authorization):
        raise HTTPException(
            status_code=401,
            detail="M151 local OpenWebUI test gateway requires the local test bearer value.",
        )

def _require_m164_llama_cpp_gateway(authorization: str | None) -> None:
    if not llama_cpp_gateway_enabled():
        raise HTTPException(
            status_code=403,
            detail="M164 llama.cpp gateway is disabled. Set UAA_LLAMA_CPP_GATEWAY_ENABLED=1 for local runtime use.",
        )
    if not llama_cpp_gateway_authorized(authorization):
        raise HTTPException(
            status_code=401,
            detail="M164 llama.cpp gateway requires the configured local bearer value.",
        )

@app.get("/v1/models")
def get_v1_models(authorization: str | None = Header(default=None)):
    if llama_cpp_gateway_enabled():
        _require_m164_llama_cpp_gateway(authorization)
        return build_m164_local_models_response(build_m164_gateway_model_from_env())
    _require_openwebui_local_test_gateway(authorization)
    return build_openwebui_local_models_response()

@app.post("/v1/chat/completions")
def post_v1_chat_completions(
    request: V1ChatCompletionAPIRequest,
    authorization: str | None = Header(default=None),
):
    payload = request.model_dump(mode="json", exclude_none=True)
    if llama_cpp_gateway_enabled():
        _require_m164_llama_cpp_gateway(authorization)
        try:
            return build_m164_chat_completion_response(
                M164ChatCompletionRequest(**payload),
                gateway_model=build_m164_gateway_model_from_env(),
                api_key=llama_cpp_backend_api_key(),
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail="M164 llama.cpp gateway request failed safe validation.",
            ) from exc
    _require_openwebui_local_test_gateway(authorization)
    try:
        local_request = OpenWebUILocalChatCompletionRequest(**payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="M151 local OpenWebUI test gateway request failed safe validation.",
        ) from exc
    return build_openwebui_local_chat_completion_response(local_request)

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
    except InvalidStateTransitionError:
        err = ErrorEnvelope(
            code="INVALID_STATE_TRANSITION",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    except Exception:
        err = ErrorEnvelope(
            code="RECEIPT_COMPILATION_FAILED",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    except Exception:
        err = ErrorEnvelope(
            code="CONTEXT_BUDGET_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    except Exception:
        err = ErrorEnvelope(
            code="LOCAL_RUNTIME_UNSAFE",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    except Exception:
        err = ErrorEnvelope(
            code="ADAPTER_POLICY_VIOLATION",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    except Exception:
        return ResultEnvelope(
            success=False,
            operation="validate_model_profile",
            service="ModelRouterAPI",
            trace_id=profile.model_profile_id,
            error=ErrorEnvelope(
                code="MODEL_PROFILE_INVALID",
                category=ErrorCategory.validation_error,
                safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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

def _remote_worker_validation_error(operation: str, trace_id: str, exc: Exception) -> ResultEnvelope:
    reason_codes = _remote_worker_error_reason_codes(exc)
    return ResultEnvelope(
        success=False,
        operation=operation,
        service="RemoteWorkersAPI",
        trace_id=trace_id,
        error=ErrorEnvelope(
            code="REMOTE_WORKER_VALIDATION_FAILED",
            category=ErrorCategory.validation_error,
            safe_message="Remote worker payload validation failed.",
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="RemoteWorkersAPI",
            caused_by=[type(exc).__name__],
            metadata={"reason_codes": reason_codes} if reason_codes else {},
        ),
        redactions_applied=["invalid_payload"],
    )

def _remote_worker_error_reason_codes(exc: Exception) -> List[str]:
    message = str(exc)
    known_codes = [
        "REMOTE_TAILNET_NOT_SUPPORTED_IN_M10_5",
        "REMOTE_PERSONAL_DATA_NOT_SUPPORTED_IN_M10_5",
        "REMOTE_DISPATCH_CANNOT_BE_ENABLED",
        "REMOTE_SUBAGENTS_CANNOT_BE_ENABLED",
        "REMOTE_APPROVALS_CANNOT_BE_ENABLED",
        "REMOTE_NETWORK_CANNOT_BE_ENABLED",
        "REMOTE_WRITE_CANNOT_BE_ENABLED",
        "REMOTE_SEND_CANNOT_BE_ENABLED",
        "REMOTE_CRITICAL_CANNOT_BE_ENABLED",
    ]
    return [code for code in known_codes if code in message]

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

def _task_decomposition_error(operation: str, trace_id: str, code: str, exc: Exception | None = None) -> ResultEnvelope:
    return ResultEnvelope(
        success=False,
        operation=operation,
        service="TaskDecompositionAPI",
        trace_id=trace_id,
        error=ErrorEnvelope(
            code=code,
            category=ErrorCategory.validation_error,
            safe_message="Task decomposition request failed safely.",
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="TaskDecompositionAPI",
            caused_by=[type(exc).__name__] if exc is not None else [],
        ),
        redactions_applied=["task_decomposition_payload"],
    )


def _task_decomposition_public_error_code(exc: Exception, default: str) -> str:
    known_codes = {
        "TASK_DECOMPOSITION_INLINE_APPROVAL_GRANTS_DENIED",
        "TASK_DECOMPOSITION_RATE_LIMIT_EXCEEDED",
    }
    message = str(exc)
    return message if message in known_codes else default


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
            authority.load_grant_for_validation(grant)
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


@app.get("/task-decomposition/status", response_model=ResultEnvelope)
def get_task_decomposition_status(authorization: str | None = Header(default=None)):
    _require_task_decomposition_local_authority(authorization)
    status = _task_decomposition_service.status()
    return ResultEnvelope(
        success=True,
        operation="task_decomposition_status",
        service="TaskDecompositionAPI",
        trace_id="system",
        data=_safe_task_decomposition_payload(status),
    )


@app.get("/task-decomposition/catalog", response_model=ResultEnvelope)
def get_task_decomposition_catalog(authorization: str | None = Header(default=None)):
    _require_task_decomposition_local_authority(authorization)
    return ResultEnvelope(
        success=True,
        operation="task_decomposition_catalog",
        service="TaskDecompositionAPI",
        trace_id="system",
        data=_safe_task_decomposition_payload({"capabilities": _task_decomposition_service.catalog()}),
    )


@app.get("/task-decomposition/registry/export", response_model=ResultEnvelope)
def get_task_decomposition_registry_export(authorization: str | None = Header(default=None)):
    _require_task_decomposition_local_authority(authorization)
    return ResultEnvelope(
        success=True,
        operation="task_decomposition_registry_export",
        service="TaskDecompositionAPI",
        trace_id="system",
        data=_safe_task_decomposition_payload(_task_decomposition_service.export_registry_document()),
    )


@app.post("/task-decomposition/examples/init", response_model=ResultEnvelope)
def post_task_decomposition_init_examples(authorization: str | None = Header(default=None)):
    _require_task_decomposition_local_authority(authorization)
    return ResultEnvelope(
        success=True,
        operation="task_decomposition_init_examples",
        service="TaskDecompositionAPI",
        trace_id="system",
        data={"capabilities": _task_decomposition_service.ensure_examples()},
    )


@app.post("/task-decomposition/capabilities/register", response_model=ResultEnvelope)
def post_task_decomposition_register_capability(
    request: TaskDecompositionRegisterRequest,
    authorization: str | None = Header(default=None),
):
    _require_task_decomposition_local_authority(authorization)
    try:
        contract = _task_decomposition_service.register(request)
    except (ValidationError, ValueError, KeyError) as exc:
        return _task_decomposition_error(
            "task_decomposition_register_capability",
            "system",
            "TASK_DECOMPOSITION_REGISTER_FAILED",
            exc,
        )
    return ResultEnvelope(
        success=True,
        operation="task_decomposition_register_capability",
        service="TaskDecompositionAPI",
        trace_id=contract.card.id,
        data={"capability": contract.model_dump(mode="json")},
    )


@app.post("/task-decomposition/classify", response_model=ResultEnvelope)
def post_task_decomposition_classify(
    request: TaskDecompositionRequest,
    authorization: str | None = Header(default=None),
):
    _require_task_decomposition_local_authority(authorization)
    intent = _task_decomposition_service.classify(request)
    return ResultEnvelope(
        success=True,
        operation="task_decomposition_classify",
        service="TaskDecompositionAPI",
        trace_id="system",
        data=_safe_task_decomposition_payload({"intent": intent}),
    )


@app.post("/task-decomposition/decompose", response_model=ResultEnvelope)
def post_task_decomposition_decompose(
    request: TaskDecompositionRequest,
    authorization: str | None = Header(default=None),
):
    _require_task_decomposition_local_authority(authorization)
    result = _task_decomposition_service.decompose(request)
    return ResultEnvelope(
        success=result.validation.valid,
        operation="task_decomposition_decompose",
        service="TaskDecompositionAPI",
        trace_id=result.plan.plan_id,
        data=_safe_task_decomposition_payload(result),
    )


@app.post("/task-decomposition/plans/validate", response_model=ResultEnvelope)
def post_task_decomposition_validate_plan(
    request: TaskPlanValidationRequest,
    authorization: str | None = Header(default=None),
):
    _require_task_decomposition_local_authority(authorization)
    validation = _task_decomposition_service.validate_plan(request)
    return ResultEnvelope(
        success=validation.valid,
        operation="task_decomposition_validate_plan",
        service="TaskDecompositionAPI",
        trace_id=request.plan.plan_id,
        data=_safe_task_decomposition_payload(validation),
    )


@app.post("/task-decomposition/approval-requests", response_model=ResultEnvelope)
def post_task_decomposition_approval_request(
    request: TaskCapabilityApprovalRequestPayload,
    authorization: str | None = Header(default=None),
):
    _require_task_decomposition_local_authority(authorization)
    try:
        approval = _task_decomposition_service.build_approval_request(request)
    except (ValidationError, ValueError, KeyError) as exc:
        return _task_decomposition_error(
            "task_decomposition_approval_request",
            request.run_id,
            "TASK_DECOMPOSITION_APPROVAL_REQUEST_FAILED",
            exc,
        )
    return ResultEnvelope(
        success=True,
        operation="task_decomposition_approval_request",
        service="TaskDecompositionAPI",
        trace_id=request.run_id,
        data=approval.model_dump(mode="json"),
    )


@app.get("/task-decomposition/approvals", response_model=ResultEnvelope)
def get_task_decomposition_approvals(authorization: str | None = Header(default=None)):
    _require_task_decomposition_local_authority(authorization)
    return ResultEnvelope(
        success=True,
        operation="task_decomposition_approvals",
        service="TaskDecompositionAPI",
        trace_id="system",
        data=_safe_task_decomposition_payload(
            _task_decomposition_service.approval_queue(),
            redact_read_refs=True,
        ),
    )


@app.post("/task-decomposition/approvals/grants/capture", response_model=ResultEnvelope)
def post_task_decomposition_capture_approval_grant(
    request: TaskDecompositionApprovalGrantRequest,
    authorization: str | None = Header(default=None),
):
    _require_task_decomposition_local_authority(authorization)
    try:
        grant = _task_decomposition_service.grant_approval(request)
    except (ValidationError, ValueError, KeyError) as exc:
        return _task_decomposition_error(
            "task_decomposition_capture_approval_grant",
            request.approval_request_id,
            "TASK_DECOMPOSITION_APPROVAL_GRANT_FAILED",
            exc,
        )
    return ResultEnvelope(
        success=True,
        operation="task_decomposition_capture_approval_grant",
        service="TaskDecompositionAPI",
        trace_id=grant.run_id,
        data=grant.model_dump(mode="json"),
    )


@app.post("/task-decomposition/approvals/revoke", response_model=ResultEnvelope)
def post_task_decomposition_revoke_approval(
    request: TaskDecompositionApprovalRevokeRequest,
    authorization: str | None = Header(default=None),
):
    _require_task_decomposition_local_authority(authorization)
    try:
        grant = _task_decomposition_service.revoke_approval(request)
    except (ValidationError, ValueError, KeyError) as exc:
        return _task_decomposition_error(
            "task_decomposition_revoke_approval",
            request.approval_ref,
            "TASK_DECOMPOSITION_APPROVAL_REVOKE_FAILED",
            exc,
        )
    return ResultEnvelope(
        success=True,
        operation="task_decomposition_revoke_approval",
        service="TaskDecompositionAPI",
        trace_id=grant.run_id,
        data=grant.model_dump(mode="json"),
    )


@app.get("/task-decomposition/audit", response_model=ResultEnvelope)
def get_task_decomposition_audit(limit: int = 100, authorization: str | None = Header(default=None)):
    _require_task_decomposition_local_authority(authorization)
    bounded_limit = min(max(limit, 1), 500)
    return ResultEnvelope(
        success=True,
        operation="task_decomposition_audit",
        service="TaskDecompositionAPI",
        trace_id="system",
        data=_safe_task_decomposition_payload(
            {"events": _task_decomposition_service.audit_events(bounded_limit)},
            redact_read_refs=True,
        ),
    )


@app.get("/task-decomposition/metrics", response_model=ResultEnvelope)
def get_task_decomposition_metrics(authorization: str | None = Header(default=None)):
    _require_task_decomposition_local_authority(authorization)
    return ResultEnvelope(
        success=True,
        operation="task_decomposition_metrics",
        service="TaskDecompositionAPI",
        trace_id="system",
        data=_safe_task_decomposition_payload(_task_decomposition_service.metrics(), redact_read_refs=True),
    )


@app.post("/task-decomposition/plans/execute", response_model=ResultEnvelope)
async def post_task_decomposition_execute_plan(
    request: TaskPlanExecutionRequest,
    authorization: str | None = Header(default=None),
):
    _require_task_decomposition_local_authority(authorization)
    try:
        result = await _task_decomposition_service.execute_plan(request)
    except ValueError as exc:
        return _task_decomposition_error(
            "task_decomposition_execute_plan",
            request.plan.plan_id,
            _task_decomposition_public_error_code(exc, "TASK_DECOMPOSITION_EXECUTE_PLAN_FAILED"),
            exc,
        )
    return ResultEnvelope(
        success=result.status == "succeeded",
        operation="task_decomposition_execute_plan",
        service="TaskDecompositionAPI",
        trace_id=request.plan.plan_id,
        data=_safe_task_decomposition_payload(result),
    )


@app.post("/task-decomposition/run", response_model=ResultEnvelope)
async def post_task_decomposition_run(
    request: TaskDecompositionRunRequest,
    authorization: str | None = Header(default=None),
):
    _require_task_decomposition_local_authority(authorization)
    try:
        result = await _task_decomposition_service.run(request)
    except ValueError as exc:
        return _task_decomposition_error(
            "task_decomposition_run",
            "task-decomposition-run:local",
            _task_decomposition_public_error_code(exc, "TASK_DECOMPOSITION_RUN_FAILED"),
            exc,
        )
    succeeded = result.execution is not None and result.execution.status == "succeeded"
    return ResultEnvelope(
        success=succeeded,
        operation="task_decomposition_run",
        service="TaskDecompositionAPI",
        trace_id=result.plan.plan_id,
        data=_safe_task_decomposition_payload(result),
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

@app.post("/model-runtime/local/smoke/validate", response_model=ResultEnvelope)
def post_validate_local_loopback_smoke(payload: LocalLoopbackSmokeValidatePayload):
    try:
        request = ManualLoopbackSmokeRequest(**payload.request)
        approval_decision = None
        if payload.approval_decision is not None:
            from ultimate_ai_agent.core.approvals import ApprovalValidationDecision

            approval_decision = ApprovalValidationDecision(**payload.approval_decision)
    except (ValidationError, ValueError) as exc:
        return _model_runtime_validation_error("validate_local_loopback_smoke", "system", exc)
    decision = validate_manual_loopback_smoke_request(request, approval_decision)
    return ResultEnvelope(
        success=decision.allowed,
        operation="validate_local_loopback_smoke",
        service="ModelRuntimeAPI",
        trace_id=request.smoke_request_id,
        data=decision.model_dump(mode="json"),
    )

@app.post("/remote-workers/nodes/validate", response_model=ResultEnvelope)
def post_validate_remote_worker_node(payload: RemoteNodeValidatePayload):
    try:
        node = RemoteNode(**payload.node)
    except (ValidationError, ValueError) as exc:
        return _remote_worker_validation_error("validate_remote_worker_node", "system", exc)
    return ResultEnvelope(
        success=True,
        operation="validate_remote_worker_node",
        service="RemoteWorkersAPI",
        trace_id=node.node_id,
        data={"node": node.model_dump(mode="json"), "live_worker_enabled": False},
    )

@app.post("/remote-workers/transports/validate", response_model=ResultEnvelope)
def post_validate_remote_worker_transport(payload: RemoteTransportValidatePayload):
    try:
        descriptor = RemoteTransportDescriptor(**payload.transport)
        registry = default_remote_transport_registry()
        registry.register_transport(descriptor)
        decision = registry.validate_transport(descriptor.transport_id)
    except (ValidationError, ValueError) as exc:
        return _remote_worker_validation_error("validate_remote_worker_transport", "system", exc)
    return ResultEnvelope(
        success=decision.allowed,
        operation="validate_remote_worker_transport",
        service="RemoteWorkersAPI",
        trace_id=descriptor.transport_id,
        data=decision.model_dump(mode="json"),
    )

@app.post("/remote-workers/policy/validate", response_model=ResultEnvelope)
def post_validate_remote_worker_policy(payload: RemotePolicyValidatePayload):
    try:
        policy = RemoteExecutionPolicy(**payload.policy)
    except (ValidationError, ValueError) as exc:
        return _remote_worker_validation_error("validate_remote_worker_policy", "system", exc)
    return ResultEnvelope(
        success=True,
        operation="validate_remote_worker_policy",
        service="RemoteWorkersAPI",
        trace_id=policy.policy_id,
        data=policy.model_dump(mode="json"),
    )

@app.post("/remote-workers/jobs/validate", response_model=ResultEnvelope)
def post_validate_remote_worker_job(payload: RemoteJobValidatePayload):
    try:
        job = RemoteJobEnvelope(**payload.job)
    except (ValidationError, ValueError) as exc:
        return _remote_worker_validation_error("validate_remote_worker_job", "system", exc)
    policy = RemoteExecutionPolicy(
        policy_id="api_remote_validation_policy",
        remote_workers_enabled=True,
        remote_transports_enabled=True,
        remote_accept_jobs=True,
    )
    decision = evaluate_remote_job_policy(job, default_remote_node_registry(), default_remote_transport_registry(), policy)
    return ResultEnvelope(
        success=decision.allowed,
        operation="validate_remote_worker_job",
        service="RemoteWorkersAPI",
        trace_id=job.correlation_id,
        data=decision.model_dump(mode="json"),
    )

@app.post("/remote-workers/dry-run", response_model=ResultEnvelope)
def post_remote_worker_dry_run(payload: RemoteDryRunPayload):
    try:
        job = RemoteJobEnvelope(**payload.job)
        policy = (
            RemoteExecutionPolicy(**payload.policy)
            if payload.policy is not None
            else RemoteExecutionPolicy(
                policy_id="api_remote_dry_run_policy",
                remote_workers_enabled=True,
                remote_transports_enabled=True,
                remote_accept_jobs=True,
            )
        )
    except (ValidationError, ValueError) as exc:
        return _remote_worker_validation_error("remote_worker_dry_run", "system", exc)
    result = RemoteDryRunBuilder().dry_run(job, default_remote_node_registry(), default_remote_transport_registry(), policy)
    return ResultEnvelope(
        success=result.status == "simulated_result",
        operation="remote_worker_dry_run",
        service="RemoteWorkersAPI",
        trace_id=job.correlation_id,
        data=result.model_dump(mode="json"),
    )

@app.get("/remote-workers/status", response_model=ResultEnvelope)
def get_remote_workers_status():
    nodes = default_remote_node_registry()
    transports = default_remote_transport_registry()
    return ResultEnvelope(
        success=True,
        operation="remote_workers_status",
        service="RemoteWorkersAPI",
        trace_id="system",
        data={
            "nodes": nodes.status_summary(),
            "transports": transports.status_summary(),
            "live_network_enabled": False,
            "dispatch_enabled": False,
            "remote_approvals_enabled": False,
            "foundation_only": True,
        },
    )

@app.get("/remote-workers/tailnet/status", response_model=ResultEnvelope)
def get_remote_workers_tailnet_status():
    return ResultEnvelope(
        success=True,
        operation="remote_workers_tailnet_status",
        service="RemoteWorkersAPI",
        trace_id="system",
        data={
            "status": "planned",
            "live_network_enabled": False,
            "dispatch_enabled": False,
            "foundation_only": True,
        },
    )

@app.get("/remote-workers/mesh/status", response_model=ResultEnvelope)
def get_remote_workers_mesh_status():
    return ResultEnvelope(
        success=True,
        operation="remote_workers_mesh_status",
        service="RemoteWorkersAPI",
        trace_id="system",
        data={
            "status": "planned",
            "live_mesh_enabled": False,
            "headscale_integrated": False,
            "tailscale_integrated": False,
            "wireguard_integrated": False,
            "preferred_planned_providers": ["headscale_planned", "generic_wireguard_planned", "manual_lan_planned"],
            "proprietary_control_plane_allowed": False,
            "dispatch_enabled": False,
            "foundation_only": True,
        },
    )

@app.get("/runtime/readiness", response_model=ResultEnvelope)
def get_runtime_readiness():
    report = build_readiness_report()
    return ResultEnvelope(
        success=True,
        operation="runtime_readiness",
        service="RuntimeReadinessAPI",
        trace_id=report.report_id,
        data=report.model_dump(mode="json"),
    )

@app.get("/runtime/capability-matrix", response_model=ResultEnvelope)
def get_runtime_capability_matrix():
    matrix = build_matrix()
    return ResultEnvelope(
        success=True,
        operation="runtime_capability_matrix",
        service="RuntimeReadinessAPI",
        trace_id=matrix.matrix_id,
        data=matrix.model_dump(mode="json"),
    )

@app.post("/runtime/smoke-reports/validate", response_model=ResultEnvelope)
def post_validate_runtime_smoke_report(payload: RuntimeSmokeReportValidatePayload):
    validation = validate_manual_smoke_report(payload.report)
    return ResultEnvelope(
        success=validation.allowed,
        operation="validate_runtime_smoke_report",
        service="RuntimeReadinessAPI",
        trace_id=validation.report_id or "system",
        data=validation.model_dump(mode="json"),
    )


@app.get("/control-center/manifest", response_model=ResultEnvelope)
def get_control_center_manifest():
    manifest = build_control_center_manifest()
    return ResultEnvelope(
        success=True,
        operation="control_center_manifest",
        service="ControlCenterAPI",
        trace_id="system",
        data=manifest.model_dump(mode="json"),
    )


@app.get("/control-center/dashboard", response_model=ResultEnvelope)
def get_control_center_dashboard():
    api_manifest = build_api_manifest(app)
    dashboard = build_control_center_dashboard(
        api_route_count=api_manifest.route_count,
        foundation_gate_status="not_run_by_endpoint",
    )
    return ResultEnvelope(
        success=True,
        operation="control_center_dashboard",
        service="ControlCenterAPI",
        trace_id="system",
        data=dashboard.model_dump(mode="json"),
    )


@app.get("/control-center/status", response_model=ResultEnvelope)
def get_control_center_status():
    dashboard = build_control_center_dashboard()
    return ResultEnvelope(
        success=True,
        operation="control_center_status",
        service="ControlCenterAPI",
        trace_id="system",
        data=dashboard.system_status.model_dump(mode="json"),
    )


@app.get("/control-center/routes", response_model=ResultEnvelope)
def get_control_center_routes():
    api_manifest = build_api_manifest(app)
    control_center_routes = [
        route.model_dump(mode="json")
        for route in api_manifest.routes
        if route.path.startswith("/control-center")
    ]
    return ResultEnvelope(
        success=True,
        operation="control_center_routes",
        service="ControlCenterAPI",
        trace_id="system",
        data={
            "route_count": len(control_center_routes),
            "routes": control_center_routes,
            "read_only_preview_only": True,
        },
    )


@app.get("/control-center/approvals/summary", response_model=ResultEnvelope)
def get_control_center_approvals_summary():
    dashboard = build_control_center_dashboard()
    return ResultEnvelope(
        success=True,
        operation="control_center_approvals_summary",
        service="ControlCenterAPI",
        trace_id="system",
        data=dashboard.approval_summary.model_dump(mode="json"),
    )


@app.get("/control-center/runtime-readiness/summary", response_model=ResultEnvelope)
def get_control_center_runtime_readiness_summary():
    dashboard = build_control_center_dashboard()
    return ResultEnvelope(
        success=True,
        operation="control_center_runtime_readiness_summary",
        service="ControlCenterAPI",
        trace_id="system",
        data=dashboard.runtime_readiness_summary.model_dump(mode="json"),
    )


@app.get("/control-center/foundation-gate/summary", response_model=ResultEnvelope)
def get_control_center_foundation_gate_summary():
    dashboard = build_control_center_dashboard(foundation_gate_status="not_run_by_endpoint")
    return ResultEnvelope(
        success=True,
        operation="control_center_foundation_gate_summary",
        service="ControlCenterAPI",
        trace_id="system",
        data=dashboard.foundation_gate_summary.model_dump(mode="json"),
    )


@app.post("/control-center/actions/preview", response_model=ResultEnvelope)
def post_control_center_action_preview(request: ControlCenterActionPreviewRequest):
    decision = preview_control_center_action(request)
    return ResultEnvelope(
        success=decision.allowed,
        operation="control_center_action_preview",
        service="ControlCenterAPI",
        trace_id=request.request_id,
        data=decision.model_dump(mode="json"),
        redactions_applied=decision.metadata.get("redactions_applied", []),
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
    except Exception:
        return ResultEnvelope(
            success=False,
            operation="validate_cost_budget",
            service="CostGovernorAPI",
            trace_id=budget.budget_id,
            error=ErrorEnvelope(
                code="COST_BUDGET_INVALID",
                category=ErrorCategory.validation_error,
                safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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

    model_config = ConfigDict(extra="forbid")

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
    safe_root_ref: str = FILE_API_DEFAULT_SAFE_ROOT_REF
    request: FileReadRequest

    model_config = ConfigDict(extra="forbid")

class FileWriteAPIProposal(BaseModel):
    proposal_id: str
    run_id: str
    actor_context: ActorContext
    target_path: str
    purpose: str
    new_content_ref: str
    file_kind: FileKind
    sensitivity: FileSensitivity
    idempotency_key: Optional[str] = None
    approval_ref: Optional[str] = None
    event_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

class FileWriteAPIRequest(BaseModel):
    safe_root_ref: str = FILE_API_DEFAULT_SAFE_ROOT_REF
    proposal: FileWriteAPIProposal

    model_config = ConfigDict(extra="forbid")

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
    except Exception:
        err = ErrorEnvelope(
            code="CONSENT_GRANT_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    except Exception:
        err = ErrorEnvelope(
            code="CONSENT_EVALUATION_FAILED",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    except Exception:
        err = ErrorEnvelope(
            code="TOOL_MANIFEST_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    except Exception:
        err = ErrorEnvelope(
            code="TOOL_EVALUATION_FAILED",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    except Exception:
        err = ErrorEnvelope(
            code="TOOL_DRY_RUN_FAILED",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    except Exception:
        err = ErrorEnvelope(
            code="CREDENTIAL_REFERENCE_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    try:
        broker = SecretBroker()
        broker.register_credential(req.reference)
        decision = broker.request_secret(req.access_request)
        return ResultEnvelope(
            success=True,
            operation="evaluate_secret_access",
            service="SecretBrokerAPI",
            trace_id=req.access_request.event_ref or "system",
            data=decision.model_dump(),
            redactions_applied=["secret_value"],
        )
    except Exception:
        err = ErrorEnvelope(
            code="SECRET_ACCESS_EVALUATION_FAILED",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="SecretBrokerAPI",
        )
        return ResultEnvelope(
            success=False,
            operation="evaluate_secret_access",
            service="SecretBrokerAPI",
            trace_id="system",
            error=err,
            redactions_applied=["secret_value"],
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
    except Exception:
        err = ErrorEnvelope(
            code="PROVIDER_MANIFEST_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    except Exception:
        err = ErrorEnvelope(
            code="MEMORY_RECORD_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    except Exception:
        err = ErrorEnvelope(
            code="FILE_REF_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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

@app.post("/files/review/approvals/capture", response_model=ResultEnvelope)
def post_files_review_approvals_capture(request: FileReviewApprovalCaptureRequest):
    decision = capture_file_review_approval_request(request, store=_file_review_approval_store)
    if decision.status.value == "rejected":
        err = ErrorEnvelope(
            code="FILE_REVIEW_APPROVAL_CAPTURE_REJECTED",
            category=ErrorCategory.policy_denied,
            safe_message=decision.safe_message,
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="FileReviewAPI",
            metadata={"reason_codes": decision.reason_codes},
        )
        return ResultEnvelope(
            success=False,
            operation="capture_file_review_approval",
            service="FileReviewAPI",
            trace_id=request.review_packet_ref,
            data=decision.model_dump(mode="json"),
            error=err,
            redactions_applied=["raw_content_omitted", "safe_refs_only"],
        )
    return ResultEnvelope(
        success=True,
        operation="capture_file_review_approval",
        service="FileReviewAPI",
        trace_id=request.review_packet_ref,
        data=decision.model_dump(mode="json"),
        redactions_applied=["raw_content_omitted", "safe_refs_only"],
    )

@app.post("/files/read/preview", response_model=ResultEnvelope)
def post_preview_file_read(req: FileReadPreviewAPIRequest):
    try:
        requested_ref = req.request.path or req.request.file_ref or ""
        if contains_secret_like(requested_ref):
            raise ValueError("FILE_PREVIEW_REF_UNSAFE")
        preview = _file_manager_for_safe_root(req.safe_root_ref).read_preview(req.request)
        redactions = list(dict.fromkeys([*preview.redactions_applied, "raw_content_omitted"]))
        preview = preview.model_copy(
            update={
                "content_hash": "redacted",
                "text_preview": "",
                "redactions_applied": redactions,
                "truncated": False,
            }
        )
        return ResultEnvelope(
            success=True,
            operation="preview_file_read",
            service="FileManagerAPI",
            trace_id=req.request.run_id,
            data=preview.model_dump(),
        )
    except Exception:
        err = ErrorEnvelope(
            code="FILE_READ_PREVIEW_FAILED",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    decision = _review_file_write_api_proposal(req.safe_root_ref, req.proposal)
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
        decision = _review_file_write_api_proposal(req.safe_root_ref, req.proposal)
        return ResultEnvelope(
            success=decision.allowed,
            operation="preview_file_diff",
            service="FileManagerAPI",
            trace_id=req.proposal.run_id,
            data={
                "diff_ref": decision.diff_ref,
                "diff_summary": "Redacted file diff preview: raw_diff_omitted=True, content_ref_only=True.",
                "raw_diff_omitted": True,
            },
        )
    except Exception:
        err = ErrorEnvelope(
            code="FILE_DIFF_PREVIEW_FAILED",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    except Exception:
        err = ErrorEnvelope(
            code="TRUTH_SOURCE_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    except Exception:
        err = ErrorEnvelope(
            code="EVIDENCE_MANIFEST_INVALID",
            category=ErrorCategory.validation_error,
            safe_message=safe_exception_message("REQUEST_PROCESSING_FAILED"),
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
    safe_payload = dict(payload)
    if safe_payload.get("task_type") in {"create_dev_file", "update_dev_file"}:
        safe_payload["dry_run"] = True
    if safe_payload.get("task_type") == "rollback_dev_file":
        return ResultEnvelope(
            success=False,
            operation="run_kernel_task",
            service="MinimumKernelAPI",
            trace_id=str(safe_payload.get("run_id") or "system"),
            error=ErrorEnvelope(
                code="KERNEL_API_MUTATION_BLOCKED",
                category=ErrorCategory.security_blocked,
                safe_message="Kernel API mutation is blocked; use an explicitly reviewed authority path.",
                severity=Severity.high,
                retryable=False,
                details_redacted=True,
                source="MinimumKernelAPI",
            ),
        )
    result = MinimumKernelRunner().run_payload(safe_payload)
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
