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
