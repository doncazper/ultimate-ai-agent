from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, FastAPI, Header, Query
from pydantic import ValidationError

from ultimate_ai_agent.api.route_registration import register_router_once
from ultimate_ai_agent.core.hygiene.envelopes import (
    ErrorCategory,
    ErrorEnvelope,
    ResultEnvelope,
    Severity,
)
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityLeaseApproveAndIssueRequest,
    AuthorityLeaseConflictError,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseRevokeRequest,
    AuthorityLeaseStore,
    AuthorityMissionPlanRequest,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    build_authority_lease_operator_approval_grant,
    validate_authority_lease_approval,
)
from ultimate_ai_agent.core.decision_router import prepare_turn
from ultimate_ai_agent.core.control_center.runtime_parity_loop import (
    build_runtime_parity_loop_read_model,
)
from ultimate_ai_agent.core.execution import (
    build_sample_staged_orchestration_read_model,
)
from ultimate_ai_agent.core.runtime_gateway import (
    RuntimeGateway,
    HermesChatRequest,
    HermesCliAdapter,
    RuntimeInvocationConflictError,
    RuntimeInvocationNotFoundError,
    RuntimeInvocationRequest,
    RuntimeInvocationStore,
    active_runtime_authority_leases,
    RuntimeCommandExecutionRequest,
    RuntimeLocalModelCallRequest,
    build_default_runtime_capabilities,
    build_hermes_context_pack_read_model,
    build_governed_product_pilot_authority_profile,
    build_runtime_interface_mode_read_model,
    build_runtime_approval_bridge_read_model_from_authority_catalog,
    build_runtime_capability_discovery_read_model_from_authority_catalog,
    build_runtime_context_budget_pressure_read_model,
    build_runtime_delegation_adapter_read_model,
    build_runtime_doctor_diagnostics_read_model,
    build_runtime_background_jobs_read_model,
    build_runtime_hardline_command_blocklist_read_model,
    build_runtime_managed_scope_policy_read_model,
    build_runtime_mcp_catalog_filtering_read_model,
    build_runtime_subagent_isolation_read_model,
    build_runtime_worktree_per_agent_read_model,
    build_runtime_lsp_diagnostics_read_model,
    build_runtime_preview_rail_read_model,
    build_runtime_slash_command_registry_read_model,
    build_runtime_interrupt_redirect_read_model,
    build_runtime_logging_profile_read_model,
    build_runtime_result_classification_read_model,
    build_runtime_voice_media_posture_read_model,
    build_runtime_messaging_gateway_posture_read_model,
    build_runtime_remote_execution_posture_read_model,
    build_runtime_plugin_metadata_posture_read_model,
    build_runtime_skill_marketplace_posture_read_model,
    build_runtime_profile_isolation_read_model_from_authority_catalog,
    build_runtime_prompt_stability_tiers_read_model,
    build_runtime_run_events_read_model_from_authority_catalog,
    build_runtime_session_continuity_read_model,
    build_runtime_session_search_read_model,
    build_runtime_session_lineage_read_model,
    build_runtime_streaming_progress_read_model_from_authority_catalog,
    build_runtime_tool_registry_availability_read_model_from_authority_catalog,
    build_runtime_usage_cost_analytics_read_model,
    build_runtime_virtual_provider_moa_read_model,
    build_runtime_action_signed_evidence,
    build_runtime_checkpoint_rollback_read_model,
    build_runtime_context_references_read_model,
    command_allowlist_catalog,
    verify_runtime_action_signed_evidence,
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
    return RuntimeInvocationStore(
        active_authority_leases=active_runtime_authority_leases()
    )


def _runtime_store() -> RuntimeInvocationStore:
    if _runtime_store_getter is None:
        return _default_runtime_store()
    return _runtime_store_getter()


def _authority_store() -> AuthorityLeaseStore:
    return AuthorityLeaseStore()


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


def _runtime_action_signed_evidence_payload(record) -> dict[str, object]:
    if record.receipt is None or record.action_inbox_envelope is None:
        return {
            "signed_evidence_available": False,
            "signed_evidence_unavailable_reason": (
                "runtime-action-evidence-unavailable-ref:receipt-or-action-envelope-missing"
            ),
        }
    try:
        envelope = build_runtime_action_signed_evidence(record)
    except ValueError:
        return {
            "signed_evidence_available": False,
            "signed_evidence_unavailable_reason": (
                "runtime-action-evidence-unavailable-ref:validation-failed"
            ),
        }
    verification = verify_runtime_action_signed_evidence(envelope)
    return {
        "signed_evidence_available": True,
        "signed_evidence_envelope": envelope.model_dump(mode="json"),
        "signed_evidence_verification": verification.model_dump(mode="json"),
        "signed_evidence_ref": envelope.signed_envelope_ref,
        "signed_evidence_verification_status": verification.verification_status,
    }


@router.get("/capabilities", response_model=ResultEnvelope)
def get_api_runtime_capabilities() -> ResultEnvelope:
    capabilities = build_default_runtime_capabilities()
    data = capabilities.model_dump(mode="json")
    data["chat_runtime_integration"] = {
        "backend_owned": True,
        "route_ref": "/api/runtime/local-model/call",
        "default_status": "disabled_by_default",
        "enabled_profile_required": "local-runtime",
        "model_output_authority": "untrusted_proposal_only",
        "raw_prompt_persisted": False,
        "raw_response_persisted": False,
        "remote_provider_authority": "blocked",
    }
    data["command_runtime_integration"] = {
        "backend_owned": True,
        "route_ref": "/api/runtime/command/run",
        "argv_only": True,
        "shell_strings_accepted": False,
        "default_status": "exact_allowlisted_readonly_status_only",
        "raw_output_persisted": False,
        "allowlist_catalog": [
            entry.model_dump(mode="json") for entry in command_allowlist_catalog()
        ],
        "blocked_command_authority": [
            "arbitrary_command_text",
            "shell_execution",
            "networked_commands",
            "unvalidated_approval_refs_as_authority",
            "raw_command_output_persistence",
        ],
    }
    return ResultEnvelope(
        success=True,
        operation="api_runtime_capabilities",
        service="GovernedRuntimeAPI",
        trace_id=capabilities.capabilities_ref,
        data=data,
        evidence=[{"evidence_ref": "evidence-ref:governed-runtime-capabilities"}],
        redactions_applied=capabilities.redactions_applied,
    )


@router.get("/governed-product-pilot-profile", response_model=ResultEnvelope)
def get_api_runtime_governed_product_pilot_profile() -> ResultEnvelope:
    profile = build_governed_product_pilot_authority_profile()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_governed_product_pilot_profile",
        service="GovernedRuntimeAPI",
        trace_id=profile.profile_ref,
        data=profile.model_dump(mode="json"),
        evidence=[{"evidence_ref": profile.portable_evidence_envelope.evidence_ref}],
        redactions_applied=profile.redactions_applied,
    )


@router.get("/delegation-adapter", response_model=ResultEnvelope)
def get_api_runtime_delegation_adapter() -> ResultEnvelope:
    read_model = build_runtime_delegation_adapter_read_model()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_delegation_adapter",
        service="GovernedRuntimeAPI",
        trace_id=read_model.adapter_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-delegation-adapter:phase-01"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/interface-mode", response_model=ResultEnvelope)
def get_api_runtime_interface_mode() -> ResultEnvelope:
    read_model = build_runtime_interface_mode_read_model()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_interface_mode",
        service="GovernedRuntimeAPI",
        trace_id=read_model.contract_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-interface-mode:v1"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/hermes/context-pack", response_model=ResultEnvelope)
def get_api_runtime_hermes_context_pack() -> ResultEnvelope:
    read_model = build_hermes_context_pack_read_model()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_hermes_context_pack",
        service="GovernedRuntimeAPI",
        trace_id=read_model.context_pack_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:hermes-context-pack:v1"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.post("/hermes/chat", response_model=ResultEnvelope)
def post_api_runtime_hermes_chat(
    request: HermesChatRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias="x-uaa-idempotency-key"
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias="x-uaa-idempotency-ref"
    ),
) -> ResultEnvelope:
    idempotency_ref = _idempotency_ref(x_uaa_idempotency_key, x_uaa_idempotency_ref)
    receipt = HermesCliAdapter().chat(
        request,
        idempotency_ref=idempotency_ref,
        active_authority_leases=active_runtime_authority_leases(),
    )
    return ResultEnvelope(
        success=receipt.status in {"receipt_recorded", "external_handoff_only"},
        operation="api_runtime_hermes_chat",
        service="GovernedRuntimeAPI",
        trace_id=receipt.receipt_ref,
        data={
            "receipt": receipt.model_dump(mode="json"),
            "execution_performed": receipt.execution_performed,
            "external_handoff_only": receipt.external_handoff_only,
            "raw_prompt_persisted": receipt.raw_prompt_persisted,
            "raw_response_persisted": receipt.raw_response_persisted,
            "raw_output_persisted": receipt.raw_output_persisted,
            "model_output_authority": receipt.model_output_authority,
            "memory_update_policy": receipt.memory_update_policy,
            "authority_decision_ref": receipt.authority_decision_ref,
            "authority_decision_outcome": receipt.authority_decision_outcome,
            "authority_lease_ref": receipt.authority_lease_ref,
            "authority_domain_ref": receipt.authority_domain_ref,
            "authority_capability_ref": receipt.authority_capability_ref,
            "authority_required_mode_ref": receipt.authority_required_mode_ref,
            "authority_audit_ref": receipt.authority_audit_ref,
            "authority_policy_receipt_ref": receipt.authority_policy_receipt_ref,
        },
        evidence=[{"evidence_ref": "evidence-ref:hermes-interface-mode-chat"}],
        redactions_applied=receipt.redactions_applied,
    )


@router.get("/capability-discovery", response_model=ResultEnvelope)
def get_api_runtime_capability_discovery() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_capability_discovery_read_model_from_authority_catalog(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_capability_discovery",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[
            {"evidence_ref": "evidence-ref:runtime-capability-discovery:phase-02"}
        ],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/tool-registry", response_model=ResultEnvelope)
def get_api_runtime_tool_registry() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_tool_registry_availability_read_model_from_authority_catalog(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_tool_registry",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-tool-registry:phase-10"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/virtual-provider-moa", response_model=ResultEnvelope)
def get_api_runtime_virtual_provider_moa() -> ResultEnvelope:
    read_model = build_runtime_virtual_provider_moa_read_model()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_virtual_provider_moa",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[
            {"evidence_ref": "evidence-ref:runtime-virtual-provider-moa:phase-20"}
        ],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/usage-cost-analytics", response_model=ResultEnvelope)
def get_api_runtime_usage_cost_analytics() -> ResultEnvelope:
    read_model = build_runtime_usage_cost_analytics_read_model()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_usage_cost_analytics",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[
            {"evidence_ref": "evidence-ref:runtime-usage-cost-analytics:phase-22"}
        ],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/prompt-stability-tiers", response_model=ResultEnvelope)
def get_api_runtime_prompt_stability_tiers() -> ResultEnvelope:
    read_model = build_runtime_prompt_stability_tiers_read_model()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_prompt_stability_tiers",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-prompt-stability:phase-23"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/context-budget-pressure", response_model=ResultEnvelope)
def get_api_runtime_context_budget_pressure() -> ResultEnvelope:
    read_model = build_runtime_context_budget_pressure_read_model()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_context_budget_pressure",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-context-budget:phase-24"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/hardline-command-blocklist", response_model=ResultEnvelope)
def get_api_runtime_hardline_command_blocklist() -> ResultEnvelope:
    read_model = build_runtime_hardline_command_blocklist_read_model()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_hardline_command_blocklist",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[
            {"evidence_ref": "evidence-ref:runtime-hardline-command-blocklist:phase-25"}
        ],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/managed-scope-policy", response_model=ResultEnvelope)
def get_api_runtime_managed_scope_policy() -> ResultEnvelope:
    read_model = build_runtime_managed_scope_policy_read_model()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_managed_scope_policy",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[
            {"evidence_ref": "evidence-ref:runtime-managed-scope-policy:phase-27"}
        ],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/doctor-diagnostics", response_model=ResultEnvelope)
def get_api_runtime_doctor_diagnostics() -> ResultEnvelope:
    read_model = build_runtime_doctor_diagnostics_read_model()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_doctor_diagnostics",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-doctor-diagnostics:phase-28"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/session-continuity", response_model=ResultEnvelope)
def get_api_runtime_session_continuity() -> ResultEnvelope:
    read_model = build_runtime_session_continuity_read_model()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_session_continuity",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-session-continuity:phase-29"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/mcp-catalog-filtering", response_model=ResultEnvelope)
def get_api_runtime_mcp_catalog_filtering() -> ResultEnvelope:
    read_model = build_runtime_mcp_catalog_filtering_read_model()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_mcp_catalog_filtering",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[
            {"evidence_ref": "evidence-ref:runtime-mcp-catalog-filtering:phase-30"}
        ],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/background-jobs", response_model=ResultEnvelope)
def get_api_runtime_background_jobs() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_background_jobs_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_background_jobs",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-background-jobs:phase-31"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/subagent-isolation", response_model=ResultEnvelope)
def get_api_runtime_subagent_isolation() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_subagent_isolation_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_subagent_isolation",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-subagent-isolation:phase-32"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/worktree-per-agent", response_model=ResultEnvelope)
def get_api_runtime_worktree_per_agent() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_worktree_per_agent_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_worktree_per_agent",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-worktree-per-agent:phase-33"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/lsp-diagnostics", response_model=ResultEnvelope)
def get_api_runtime_lsp_diagnostics() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_lsp_diagnostics_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_lsp_diagnostics",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-lsp-diagnostics:phase-34"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/preview-rail", response_model=ResultEnvelope)
def get_api_runtime_preview_rail() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_preview_rail_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_preview_rail",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-preview-rail:phase-35"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/slash-command-registry", response_model=ResultEnvelope)
def get_api_runtime_slash_command_registry() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_slash_command_registry_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_slash_command_registry",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[
            {"evidence_ref": "evidence-ref:runtime-slash-command-registry:phase-36"}
        ],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/interrupt-redirect", response_model=ResultEnvelope)
def get_api_runtime_interrupt_redirect() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_interrupt_redirect_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_interrupt_redirect",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-interrupt-redirect:phase-37"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/logging-profile", response_model=ResultEnvelope)
def get_api_runtime_logging_profile() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_logging_profile_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_logging_profile",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-logging-profile:phase-38"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/result-classification", response_model=ResultEnvelope)
def get_api_runtime_result_classification() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_result_classification_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_result_classification",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[
            {"evidence_ref": "evidence-ref:runtime-result-classification:phase-39"}
        ],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/voice-media-posture", response_model=ResultEnvelope)
def get_api_runtime_voice_media_posture() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_voice_media_posture_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_voice_media_posture",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[
            {"evidence_ref": "evidence-ref:runtime-voice-media-posture:phase-41"}
        ],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/messaging-gateway-posture", response_model=ResultEnvelope)
def get_api_runtime_messaging_gateway_posture() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_messaging_gateway_posture_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_messaging_gateway_posture",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[
            {"evidence_ref": "evidence-ref:runtime-messaging-gateway-posture:phase-42"}
        ],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/remote-execution-posture", response_model=ResultEnvelope)
def get_api_runtime_remote_execution_posture() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_remote_execution_posture_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_remote_execution_posture",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[
            {"evidence_ref": "evidence-ref:runtime-remote-execution-posture:phase-43"}
        ],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/plugin-metadata-posture", response_model=ResultEnvelope)
def get_api_runtime_plugin_metadata_posture() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_plugin_metadata_posture_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_plugin_metadata_posture",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[
            {"evidence_ref": "evidence-ref:runtime-plugin-metadata-posture:phase-44"}
        ],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/skill-marketplace-posture", response_model=ResultEnvelope)
def get_api_runtime_skill_marketplace_posture() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_skill_marketplace_posture_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_skill_marketplace_posture",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[
            {"evidence_ref": "evidence-ref:runtime-skill-marketplace-posture:phase-45"}
        ],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/session-search", response_model=ResultEnvelope)
def get_api_runtime_session_search(
    query_ref: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=25),
) -> ResultEnvelope:
    try:
        read_model = build_runtime_session_search_read_model(
            query_ref=query_ref,
            limit=limit,
        )
    except ValueError as exc:
        return ResultEnvelope(
            success=False,
            operation="api_runtime_session_search",
            service="GovernedRuntimeAPI",
            trace_id="query-ref:runtime-session-search:invalid",
            error=ErrorEnvelope(
                code="RUNTIME_SESSION_SEARCH_REF_DENIED",
                category=ErrorCategory.validation_error,
                safe_message="Session search accepts safe query refs only.",
                severity=Severity.medium,
                retryable=False,
                details_redacted=True,
                source="GovernedRuntimeAPI",
                metadata={"reason_ref": str(exc) or "invalid_query_ref"},
            ),
            redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
        )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_session_search",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-session-search:phase-12"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/session-lineage", response_model=ResultEnvelope)
def get_api_runtime_session_lineage() -> ResultEnvelope:
    read_model = build_runtime_session_lineage_read_model()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_session_lineage",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-session-lineage:phase-19"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/context-references", response_model=ResultEnvelope)
def get_api_runtime_context_references() -> ResultEnvelope:
    read_model = build_runtime_context_references_read_model()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_context_references",
        service="GovernedRuntimeAPI",
        trace_id=read_model.preview_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-context-references:phase-16"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/checkpoint-rollback", response_model=ResultEnvelope)
def get_api_runtime_checkpoint_rollback() -> ResultEnvelope:
    read_model = build_runtime_checkpoint_rollback_read_model()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_checkpoint_rollback",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:checkpoint-rollback:phase-18"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/run-events", response_model=ResultEnvelope)
def get_api_runtime_run_events() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_run_events_read_model_from_authority_catalog(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_run_events",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_hash_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-run-events:phase-03"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/authority-state", response_model=ResultEnvelope)
def get_api_runtime_authority_state() -> ResultEnvelope:
    read_model = _authority_store().build_state_read_model()
    return ResultEnvelope(
        success=True,
        operation="api_runtime_authority_state",
        service="GovernedRuntimeAPI",
        trace_id=read_model.contract_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:authority-state:v1"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.post("/authority-decisions/preview", response_model=ResultEnvelope)
def post_api_runtime_authority_decision_preview(
    request: AuthorityActionRequest,
) -> ResultEnvelope:
    preview = _authority_store().preview_decision(request)
    return ResultEnvelope(
        success=True,
        operation="api_runtime_authority_decision_preview",
        service="GovernedRuntimeAPI",
        trace_id=preview.preview_ref,
        data=preview.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:authority-decision-preview:v1"}],
        redactions_applied=list(preview.redactions_applied),
    )


@router.post("/authority-missions/plan", response_model=ResultEnvelope)
def post_api_runtime_authority_mission_plan(
    request: AuthorityMissionPlanRequest,
) -> ResultEnvelope:
    plan = _authority_store().plan_mission(request)
    return ResultEnvelope(
        success=True,
        operation="api_runtime_authority_mission_plan",
        service="GovernedRuntimeAPI",
        trace_id=plan.plan_ref,
        data=plan.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:authority-mission-plan:v1"}],
        redactions_applied=list(plan.redactions_applied),
    )


@router.post("/authority-leases", response_model=ResultEnvelope)
def post_api_runtime_authority_lease(
    request: AuthorityLeaseIssueRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias="x-uaa-idempotency-key",
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias="x-uaa-idempotency-ref",
    ),
) -> ResultEnvelope:
    idempotency_ref = _idempotency_ref(x_uaa_idempotency_key, x_uaa_idempotency_ref)
    try:
        lease, receipt = _authority_store().issue_lease(
            request,
            idempotency_ref=idempotency_ref,
            approval_validator=validate_authority_lease_approval,
        )
    except AuthorityLeaseConflictError:
        return ResultEnvelope(
            success=False,
            operation="api_runtime_authority_lease_issue",
            service="GovernedRuntimeAPI",
            trace_id=idempotency_ref,
            error=ErrorEnvelope(
                code="AUTHORITY_LEASE_IDEMPOTENCY_CONFLICT",
                category=ErrorCategory.conflict,
                safe_message="The authority lease idempotency ref already belongs to another operation.",
                severity=Severity.medium,
                retryable=False,
                details_redacted=True,
                source="GovernedRuntimeAPI",
            ),
            redactions_applied=list(receipt.redactions_applied)
            if "receipt" in locals()
            else ["safe_refs_only"],
        )
    return ResultEnvelope(
        success=receipt.status in {"issued", "replayed"},
        operation="api_runtime_authority_lease_issue",
        service="GovernedRuntimeAPI",
        trace_id=receipt.receipt_ref,
        data={
            "lease": lease.model_dump(mode="json") if lease is not None else None,
            "receipt": receipt.model_dump(mode="json"),
            "execution_performed": False,
            "unsupported_adapters_claimed_execution": False,
            "unknown_authority_default": "deny",
        },
        evidence=[{"evidence_ref": "evidence-ref:authority-lease-issue:v1"}],
        redactions_applied=list(receipt.redactions_applied),
    )


@router.post("/authority-leases/approve-and-issue", response_model=ResultEnvelope)
def post_api_runtime_authority_lease_approve_and_issue(
    request: AuthorityLeaseApproveAndIssueRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias="x-uaa-idempotency-key",
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias="x-uaa-idempotency-ref",
    ),
) -> ResultEnvelope:
    idempotency_ref = _idempotency_ref(x_uaa_idempotency_key, x_uaa_idempotency_ref)
    lease_request = request.lease_issue_request
    approval_requirement, approval_grant = (
        build_authority_lease_operator_approval_grant(
            lease_request,
            idempotency_ref=idempotency_ref,
            approved_by_actor_id=request.approved_by_actor_ref,
        )
    )
    if approval_grant is not None:
        lease_request = lease_request.model_copy(
            update={
                "approval_ref": approval_grant.approval_ref,
                "approval_grants": [approval_grant.model_dump(mode="json")],
            }
        )
    try:
        lease, receipt = _authority_store().issue_lease(
            lease_request,
            idempotency_ref=idempotency_ref,
            approval_validator=validate_authority_lease_approval,
        )
    except AuthorityLeaseConflictError:
        return ResultEnvelope(
            success=False,
            operation="api_runtime_authority_lease_approve_and_issue",
            service="GovernedRuntimeAPI",
            trace_id=idempotency_ref,
            error=ErrorEnvelope(
                code="AUTHORITY_LEASE_IDEMPOTENCY_CONFLICT",
                category=ErrorCategory.conflict,
                safe_message="The authority lease idempotency ref already belongs to another operation.",
                severity=Severity.medium,
                retryable=False,
                details_redacted=True,
                source="GovernedRuntimeAPI",
            ),
            redactions_applied=["safe_refs_only"],
        )
    return ResultEnvelope(
        success=receipt.status in {"issued", "replayed"},
        operation="api_runtime_authority_lease_approve_and_issue",
        service="GovernedRuntimeAPI",
        trace_id=receipt.receipt_ref,
        data={
            "lease": lease.model_dump(mode="json") if lease is not None else None,
            "receipt": receipt.model_dump(mode="json"),
            "approval_requirement": approval_requirement.model_dump(mode="json"),
            "approval_captured": approval_grant is not None,
            "approval_ref": approval_grant.approval_ref
            if approval_grant is not None
            else None,
            "approval_grant_payload_persisted": False,
            "execution_performed": False,
            "unsupported_adapters_claimed_execution": False,
            "unknown_authority_default": "deny",
        },
        evidence=[
            {"evidence_ref": "evidence-ref:authority-lease-approve-and-issue:v1"}
        ],
        redactions_applied=list(receipt.redactions_applied),
    )


@router.post("/authority-leases/revoke", response_model=ResultEnvelope)
def post_api_runtime_authority_lease_revoke(
    request: AuthorityLeaseRevokeRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None,
        alias="x-uaa-idempotency-key",
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None,
        alias="x-uaa-idempotency-ref",
    ),
) -> ResultEnvelope:
    idempotency_ref = _idempotency_ref(x_uaa_idempotency_key, x_uaa_idempotency_ref)
    try:
        lease, receipt = _authority_store().revoke_lease(
            request,
            idempotency_ref=idempotency_ref,
        )
    except AuthorityLeaseConflictError:
        return ResultEnvelope(
            success=False,
            operation="api_runtime_authority_lease_revoke",
            service="GovernedRuntimeAPI",
            trace_id=idempotency_ref,
            error=ErrorEnvelope(
                code="AUTHORITY_LEASE_IDEMPOTENCY_CONFLICT",
                category=ErrorCategory.conflict,
                safe_message="The authority lease idempotency ref already belongs to another operation.",
                severity=Severity.medium,
                retryable=False,
                details_redacted=True,
                source="GovernedRuntimeAPI",
            ),
            redactions_applied=["safe_refs_only"],
        )
    return ResultEnvelope(
        success=receipt.status in {"revoked", "replayed"},
        operation="api_runtime_authority_lease_revoke",
        service="GovernedRuntimeAPI",
        trace_id=receipt.receipt_ref,
        data={
            "lease": lease.model_dump(mode="json") if lease is not None else None,
            "receipt": receipt.model_dump(mode="json"),
            "execution_performed": False,
            "unsupported_adapters_claimed_execution": False,
            "unknown_authority_default": "deny",
        },
        evidence=[{"evidence_ref": "evidence-ref:authority-lease-revoke:v1"}],
        redactions_applied=list(receipt.redactions_applied),
    )


@router.get("/approval-bridge", response_model=ResultEnvelope)
def get_api_runtime_approval_bridge() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_approval_bridge_read_model_from_authority_catalog(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_approval_bridge",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_hash_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-approval-bridge:phase-04"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/streaming-progress", response_model=ResultEnvelope)
def get_api_runtime_streaming_progress() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_streaming_progress_read_model_from_authority_catalog(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_streaming_progress",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_hash_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-streaming-progress:phase-05"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/profiles", response_model=ResultEnvelope)
def get_api_runtime_profiles() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_runtime_profile_isolation_read_model_from_authority_catalog(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_profiles",
        service="GovernedRuntimeAPI",
        trace_id=read_model.snapshot_hash_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:runtime-profiles:phase-06"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/staged-orchestration", response_model=ResultEnvelope)
def get_api_runtime_staged_orchestration() -> ResultEnvelope:
    authority_state = _authority_store().build_state_read_model()
    read_model = build_sample_staged_orchestration_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_staged_orchestration",
        service="GovernedRuntimeAPI",
        trace_id=read_model.plan.plan_ref,
        data=read_model.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:staged-orchestration:api-read"}],
        redactions_applied=read_model.redactions_applied,
    )


@router.get("/prepared-turn", response_model=ResultEnvelope)
def get_api_runtime_prepared_turn(
    sample: str = Query(default="diy-desk", min_length=1, max_length=80),
) -> ResultEnvelope:
    try:
        prepared = prepare_turn(sample_id=sample)
    except ValueError:
        return ResultEnvelope(
            success=False,
            operation="api_runtime_prepared_turn",
            service="GovernedRuntimeAPI",
            trace_id="prepared-turn-ref:invalid-sample",
            error=ErrorEnvelope(
                code="PREPARED_TURN_SAMPLE_INVALID",
                category=ErrorCategory.validation_error,
                safe_message="The prepared-turn sample id is not available.",
                severity=Severity.low,
                retryable=False,
                details_redacted=True,
                source="GovernedRuntimeAPI",
            ),
            redactions_applied=[
                "redaction-ref:prepared-turn:raw-turn-text-omitted",
                "redaction-ref:prepared-turn:raw-model-output-omitted",
            ],
        )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_prepared_turn",
        service="GovernedRuntimeAPI",
        trace_id=prepared.prepared_turn_ref,
        data=prepared.model_dump(mode="json"),
        evidence=[{"evidence_ref": "evidence-ref:prepared-turn:api-read"}],
        redactions_applied=prepared.redactions_applied,
    )


@router.get("/parity-loop", response_model=ResultEnvelope)
def get_api_runtime_parity_loop() -> ResultEnvelope:
    store = _runtime_store()
    read_model = build_runtime_parity_loop_read_model(
        store.list_invocations(),
        entries=store.list_entries(),
    )
    return ResultEnvelope(
        success=True,
        operation="api_runtime_parity_loop",
        service="GovernedRuntimeAPI",
        trace_id=read_model["contract_ref"],
        data=read_model,
        evidence=[{"evidence_ref": "evidence-ref:runtime-parity-loop-final-hardening"}],
        redactions_applied=read_model["redactions_applied"],
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
            "model_call_enabled": False,
            "command_execution_enabled": False,
            "local_model_gateway_route_available": True,
            "command_gateway_route_available": True,
            "local_model_runtime_enabled_by_default": False,
            "model_output_is_proposal_only": True,
            "invocation_count": len(records),
            "invocations": records,
        },
        redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
    )


@router.post("/local-model/call", response_model=ResultEnvelope)
def post_api_runtime_local_model_call(
    request: RuntimeLocalModelCallRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias="x-uaa-idempotency-key"
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias="x-uaa-idempotency-ref"
    ),
) -> ResultEnvelope:
    idempotency_ref = _idempotency_ref(x_uaa_idempotency_key, x_uaa_idempotency_ref)
    try:
        result = RuntimeGateway(store=_runtime_store()).invoke_local_model(
            request,
            idempotency_ref=idempotency_ref,
        )
    except RuntimeInvocationConflictError:
        return ResultEnvelope(
            success=False,
            operation="api_runtime_local_model_call",
            service="GovernedRuntimeAPI",
            trace_id=idempotency_ref,
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
    receipt = result.record.receipt
    metadata = receipt.model_receipt_metadata if receipt else None
    return ResultEnvelope(
        success=result.error_category is None
        and result.record.status == "receipt_recorded",
        operation="api_runtime_local_model_call",
        service="GovernedRuntimeAPI",
        trace_id=result.record.invocation_ref,
        data={
            "record": result.record.model_dump(mode="json"),
            "replayed": result.replayed,
            "local_model_runtime_enabled": result.local_model_runtime_enabled,
            "execution_performed": bool(receipt and receipt.execution_performed),
            "adapter_execution_enabled": result.record.policy_decision.adapter_execution_enabled,
            "model_call_performed": bool(receipt and receipt.model_call_performed),
            "model_output_non_authoritative": True,
            "response_preview": result.response_preview
            if result.response_preview_returned
            else None,
            "response_preview_returned": result.response_preview_returned,
            "response_preview_persisted": False,
            "request_byte_count": result.request_byte_count,
            "response_byte_count": result.response_byte_count,
            "error_category": result.error_category,
            "receipt_ref": receipt.receipt_ref if receipt else None,
            "metadata_ref": metadata.endpoint_ref if metadata else None,
            "blocked_authority_refs": (
                receipt.blocked_authority_refs
                if receipt
                else result.record.policy_decision.blocked_authority_refs
            ),
            "blocked_runtime_authority": [
                "command_execution",
                "browser_automation",
                "connector_write",
                "plugin_runtime_import",
                "remote_provider_model_call",
                "production_authority",
            ],
        },
        evidence=[{"evidence_ref": "evidence-ref:governed-runtime-local-model-call"}],
        redactions_applied=[
            *GOVERNED_RUNTIME_REDACTIONS,
            "raw_prompt_omitted_from_response",
            "raw_response_not_persisted",
            "provider_payload_not_persisted",
        ],
    )


@router.post("/command/run", response_model=ResultEnvelope)
def post_api_runtime_command_run(
    request: RuntimeCommandExecutionRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias="x-uaa-idempotency-key"
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias="x-uaa-idempotency-ref"
    ),
) -> ResultEnvelope:
    idempotency_ref = _idempotency_ref(x_uaa_idempotency_key, x_uaa_idempotency_ref)
    try:
        result = RuntimeGateway(store=_runtime_store()).invoke_command(
            request,
            idempotency_ref=idempotency_ref,
        )
    except RuntimeInvocationConflictError:
        return ResultEnvelope(
            success=False,
            operation="api_runtime_command_run",
            service="GovernedRuntimeAPI",
            trace_id=idempotency_ref,
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
    receipt = result.record.receipt
    metadata = receipt.command_receipt_metadata if receipt else None
    return ResultEnvelope(
        success=(
            result.error_category is None
            and result.record.status == "receipt_recorded"
            and result.exit_code == 0
        ),
        operation="api_runtime_command_run",
        service="GovernedRuntimeAPI",
        trace_id=result.record.invocation_ref,
        data={
            "record": result.record.model_dump(mode="json"),
            "replayed": result.replayed,
            "execution_performed": bool(receipt and receipt.execution_performed),
            "adapter_execution_enabled": result.record.policy_decision.adapter_execution_enabled,
            "command_execution_enabled": result.command_execution_enabled,
            "command_execution_performed": bool(
                receipt and receipt.command_execution_performed
            ),
            "shell_strings_accepted": False,
            "raw_output_persisted": False,
            "output_summary": result.output_summary,
            "output_summary_returned": result.output_summary_returned,
            "output_persisted": False,
            "exit_code": result.exit_code,
            "timed_out": result.timed_out,
            "error_category": result.error_category,
            "receipt_ref": receipt.receipt_ref if receipt else None,
            "metadata_ref": metadata.redacted_output_ref if metadata else None,
            "blocked_authority_refs": (
                receipt.blocked_authority_refs
                if receipt
                else result.record.policy_decision.blocked_authority_refs
            ),
            "blocked_runtime_authority": [
                "arbitrary_command_text",
                "shell_execution",
                "networked_commands",
                "raw_command_output_persistence",
                "browser_automation",
                "connector_write",
                "plugin_runtime_import",
                "remote_provider_model_call",
                "production_authority",
            ],
        },
        evidence=[{"evidence_ref": "evidence-ref:governed-runtime-command-run"}],
        redactions_applied=[
            *GOVERNED_RUNTIME_REDACTIONS,
            "raw_command_output_not_persisted",
            "local_cwd_not_persisted",
            "environment_not_persisted",
        ],
    )


@router.post("/invocations", response_model=ResultEnvelope)
def post_api_runtime_invocations(
    request: RuntimeInvocationRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias="x-uaa-idempotency-key"
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias="x-uaa-idempotency-ref"
    ),
) -> ResultEnvelope:
    store = _runtime_store()
    try:
        result = store.create_invocation(
            request,
            idempotency_ref=_idempotency_ref(
                x_uaa_idempotency_key, x_uaa_idempotency_ref
            ),
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
        evidence=[
            {"evidence_ref": "evidence-ref:governed-runtime-invocation-recorded"}
        ],
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
            "receipt": record.receipt.model_dump(mode="json")
            if record.receipt
            else None,
            "receipt_available": record.receipt is not None,
            **_runtime_action_signed_evidence_payload(record),
            "execution_performed": bool(
                record.receipt and record.receipt.execution_performed
            ),
            "model_call_performed": bool(
                record.receipt and record.receipt.model_call_performed
            ),
            "command_execution_performed": bool(
                record.receipt and record.receipt.command_execution_performed
            ),
        },
        warnings=[] if record.receipt else ["RUNTIME_RECEIPT_NOT_RECORDED_YET"],
        redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
    )


@router.post("/invocations/{id}/approve", response_model=ResultEnvelope)
def post_api_runtime_invocations_id_approve(
    id: str,
    request: RuntimeApprovalBindingRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias="x-uaa-idempotency-key"
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias="x-uaa-idempotency-ref"
    ),
) -> ResultEnvelope:
    try:
        record = _runtime_store().bind_approval(
            id,
            request,
            idempotency_ref=_idempotency_ref(
                x_uaa_idempotency_key, x_uaa_idempotency_ref
            ),
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
            "action_inbox_execution_bridge": record.action_inbox_envelope is not None,
            "action_envelope_ref": (
                record.action_inbox_envelope.action_envelope_ref
                if record.action_inbox_envelope
                else None
            ),
            "approval_validated": (
                bool(record.action_inbox_envelope.approval_validated)
                if record.action_inbox_envelope
                else False
            ),
            "approval_status": (
                record.action_inbox_envelope.status
                if record.action_inbox_envelope
                else record.status
            ),
            "blocked_reason_refs": (
                record.action_inbox_envelope.blocked_reason_refs
                if record.action_inbox_envelope
                else []
            ),
            "execution_performed": False,
            "adapter_execution_enabled": record.policy_decision.adapter_execution_enabled,
            "command_execution_enabled": record.policy_decision.command_execution_enabled,
        },
        evidence=[{"evidence_ref": "evidence-ref:governed-runtime-approval-binding"}],
        redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
    )


@router.post("/invocations/{id}/execute", response_model=ResultEnvelope)
def post_api_runtime_invocations_id_execute(
    id: str,
    request: RuntimeExecuteRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias="x-uaa-idempotency-key"
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias="x-uaa-idempotency-ref"
    ),
) -> ResultEnvelope:
    idempotency_ref = _idempotency_ref(x_uaa_idempotency_key, x_uaa_idempotency_ref)
    if request.command_request is not None:
        try:
            command_request = RuntimeCommandExecutionRequest(**request.command_request)
            result = RuntimeGateway(store=_runtime_store()).execute_approved_command(
                id,
                command_request,
                request,
                idempotency_ref=idempotency_ref,
            )
        except RuntimeInvocationNotFoundError:
            return _not_found("api_runtime_invocation_execute", id)
        except RuntimeInvocationConflictError:
            return ResultEnvelope(
                success=False,
                operation="api_runtime_invocation_execute",
                service="GovernedRuntimeAPI",
                trace_id=idempotency_ref,
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
        except ValidationError:
            return ResultEnvelope(
                success=False,
                operation="api_runtime_invocation_execute",
                service="GovernedRuntimeAPI",
                trace_id=idempotency_ref,
                error=ErrorEnvelope(
                    code="RUNTIME_COMMAND_REQUEST_INVALID",
                    category=ErrorCategory.validation_error,
                    safe_message="The governed runtime command request failed safe validation.",
                    severity=Severity.medium,
                    retryable=False,
                    details_redacted=True,
                    source="GovernedRuntimeAPI",
                ),
                redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
            )
        receipt = result.record.receipt
        metadata = receipt.command_receipt_metadata if receipt else None
        execution_performed = bool(receipt and receipt.execution_performed)
        signed_evidence = _runtime_action_signed_evidence_payload(result.record)
        return ResultEnvelope(
            success=result.error_category is None and execution_performed,
            operation="api_runtime_invocation_execute",
            service="GovernedRuntimeAPI",
            trace_id=result.record.invocation_ref,
            data={
                "record": result.record.model_dump(mode="json"),
                "replayed": result.replayed,
                "execution_performed": execution_performed,
                "adapter_execution_enabled": (
                    result.record.policy_decision.adapter_execution_enabled
                ),
                "command_execution_enabled": result.command_execution_enabled,
                "command_execution_performed": bool(
                    receipt and receipt.command_execution_performed
                ),
                "approval_envelope_ref": (
                    result.record.action_inbox_envelope.action_envelope_ref
                    if result.record.action_inbox_envelope
                    else None
                ),
                "receipt_ref": receipt.receipt_ref if receipt else None,
                "signed_evidence_ref": signed_evidence.get("signed_evidence_ref"),
                "signed_evidence_available": signed_evidence.get(
                    "signed_evidence_available", False
                ),
                "signed_evidence_verification_status": signed_evidence.get(
                    "signed_evidence_verification_status"
                ),
                "evidence_refs": receipt.evidence_refs if receipt else [],
                "metadata_ref": metadata.redacted_output_ref if metadata else None,
                "output_summary": result.output_summary,
                "output_summary_returned": result.output_summary_returned,
                "output_persisted": False,
                "exit_code": result.exit_code,
                "timed_out": result.timed_out,
                "error_category": result.error_category,
                "blocked_reason": result.error_category,
                "blocked_runtime_authority": [
                    "arbitrary_command_text",
                    "shell_execution",
                    "networked_commands",
                    "raw_command_output_persistence",
                    "browser_automation",
                    "connector_write",
                    "plugin_runtime_import",
                    "remote_provider_model_call",
                    "production_authority",
                ],
            },
            evidence=[
                {"evidence_ref": "evidence-ref:governed-runtime-action-inbox-execute"}
            ],
            redactions_applied=[
                *GOVERNED_RUNTIME_REDACTIONS,
                "raw_command_output_not_persisted",
                "local_cwd_not_persisted",
                "environment_not_persisted",
            ],
        )
    try:
        record = _runtime_store().record_blocked_execute(
            id,
            safe_summary=request.safe_summary,
            idempotency_ref=idempotency_ref,
        )
    except RuntimeInvocationNotFoundError:
        return _not_found("api_runtime_invocation_execute", id)
    except RuntimeInvocationConflictError:
        return ResultEnvelope(
            success=False,
            operation="api_runtime_invocation_execute",
            service="GovernedRuntimeAPI",
            trace_id=idempotency_ref,
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
            "blocked_reason": "RUNTIME_ADAPTER_EXECUTION_REQUIRES_ACTIVE_AUTHORITY_LEASE_CAPABILITY",
            "authority_decision_outcome": record.policy_decision.authority_decision_outcome,
            "authority_required_mode": record.policy_decision.authority_required_mode,
            "authority_required_domain": record.policy_decision.authority_domain,
            "authority_required_capability": record.policy_decision.authority_capability,
            "authority_operator_message": record.policy_decision.authority_operator_message,
            "blocked_reason_refs": [
                "reason-ref:authority:no-active-lease-for-runtime-adapter",
                "blocked-state:runtime-adapter-execution:authority-lease-required",
                "blocked-state:runtime-adapter-execution:approval-binding-required",
            ],
            "next_safe_action": (
                "Select a trust mode that grants the required domain/capability, "
                "then use the approval-bound command execution path with receipts."
            ),
        },
        evidence=[{"evidence_ref": "evidence-ref:governed-runtime-execution-blocked"}],
        redactions_applied=list(GOVERNED_RUNTIME_REDACTIONS),
    )


@router.post("/safe-disable", response_model=ResultEnvelope)
def post_api_runtime_safe_disable(
    request: RuntimeSafeDisableRequest,
    x_uaa_idempotency_key: str | None = Header(
        default=None, alias="x-uaa-idempotency-key"
    ),
    x_uaa_idempotency_ref: str | None = Header(
        default=None, alias="x-uaa-idempotency-ref"
    ),
) -> ResultEnvelope:
    try:
        state = _runtime_store().safe_disable(
            request,
            idempotency_ref=_idempotency_ref(
                x_uaa_idempotency_key, x_uaa_idempotency_ref
            ),
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
