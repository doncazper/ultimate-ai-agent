from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.control_center.runtime_action_bridge import (
    build_runtime_action_inbox_bridge_read_model,
)
from ultimate_ai_agent.core.decision_router import prepare_turn
from ultimate_ai_agent.core.execution import (
    build_sample_staged_orchestration_read_model,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.providers.control_plane import (
    build_model_provider_control_plane_read_model,
)
from ultimate_ai_agent.core.runtime_gateway import RuntimeInvocationRecord
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS


RUNTIME_PARITY_LOOP_CONTRACT_REF = (
    "contract-ref:uaa-runtime-parity-loop:v1"
)
RUNTIME_PARITY_LOOP_SOURCE = "python_core_runtime_parity_loop_read_model"
RUNTIME_PARITY_LOOP_CLI_REF = "uaa runtime inspect-parity-loop"
RUNTIME_PARITY_LOOP_API_ROUTE_REF = "GET /api/runtime/parity-loop"
RUNTIME_PARITY_LOOP_CONTROL_CENTER_ROUTE_REF = "GET /control-center/actions/inbox"
RUNTIME_PARITY_LOOP_BLOCKED_AUTHORITY_REFS = (
    "blocked-authority:runtime-model-calls",
    "blocked-authority:provider-sdk-calls",
    "blocked-authority:live-web-fetching",
    "blocked-authority:browser-automation",
    "blocked-authority:connector-writes",
    "blocked-authority:unrestricted-shell-subprocess",
    "blocked-authority:plugin-runtime-import",
    "blocked-authority:remote-execution",
    "blocked-authority:production-authority",
    "blocked-authority:broad-autonomy",
)
RUNTIME_PARITY_LOOP_STAGE_REFS = (
    "runtime-loop-stage-ref:prepared-turn",
    "runtime-loop-stage-ref:route-decision-binding",
    "runtime-loop-stage-ref:durable-run-approval",
    "runtime-loop-stage-ref:staged-orchestration",
    "runtime-loop-stage-ref:role-provider-evidence",
    "runtime-loop-stage-ref:action-inbox-approval",
    "runtime-loop-stage-ref:exact-action-receipt",
    "runtime-loop-stage-ref:signed-evidence",
    "runtime-loop-stage-ref:blocked-retry-state",
)

RuntimeParityLoopStatus = Literal["implemented", "partial", "planned", "blocked"]


class RuntimeParityLoopStage(BaseModel):
    stage_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=140)
    status: RuntimeParityLoopStatus
    core_ref: str = Field(..., min_length=1)
    cli_ref: str = Field(..., min_length=1)
    api_route_ref: str = Field(..., min_length=1)
    control_center_ref: str = Field(..., min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=520)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_stage(self) -> "RuntimeParityLoopStage":
        for value, field_name in [
            (self.stage_ref, "stage_ref"),
            (self.core_ref, "core_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.label, "label"),
            (self.status, "status"),
            (self.cli_ref, "cli_ref"),
            (self.api_route_ref, "api_route_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(str(value), field_name)
        for ref in [*self.evidence_refs, *self.blocked_authority_refs]:
            validate_execution_ref(ref, "runtime_parity_loop_ref")
        return self


class RuntimeParityLoopReadModel(BaseModel):
    schema_version: str = "uaa_runtime_parity_loop.v1"
    contract_ref: str = RUNTIME_PARITY_LOOP_CONTRACT_REF
    source: str = RUNTIME_PARITY_LOOP_SOURCE
    backend_owned: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    api_route_ref: str = RUNTIME_PARITY_LOOP_API_ROUTE_REF
    control_center_route_ref: str = RUNTIME_PARITY_LOOP_CONTROL_CENTER_ROUTE_REF
    cli_ref: str = RUNTIME_PARITY_LOOP_CLI_REF
    status: str = "implemented_backend_owned_runtime_parity_loop_inspection"
    parity_status: str = "partial_runtime_parity_without_broad_authority"
    prepared_turn_ref: str = Field(..., min_length=1)
    route_decision_binding_ref: str = Field(..., min_length=1)
    durable_run_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    staged_orchestration_ref: str = Field(..., min_length=1)
    role_provider_evidence_ref: str = Field(..., min_length=1)
    action_bridge_contract_ref: str = Field(..., min_length=1)
    portable_evidence_ref: str = Field(..., min_length=1)
    runtime_invocation_count: int = Field(ge=0)
    runtime_receipt_count: int = Field(ge=0)
    runtime_signed_evidence_count: int = Field(ge=0)
    runtime_timeline_event_count: int = Field(ge=0)
    implemented_stage_count: int = Field(ge=0)
    partial_stage_count: int = Field(ge=0)
    blocked_stage_count: int = Field(ge=0)
    stage_refs: list[str] = Field(default_factory=list)
    stages: list[RuntimeParityLoopStage] = Field(default_factory=list)
    cli_refs: list[str] = Field(default_factory=list)
    api_route_refs: list[str] = Field(default_factory=list)
    control_center_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    before_scores: dict[str, int] = Field(default_factory=dict)
    after_scores: dict[str, int] = Field(default_factory=dict)
    operator_summary: str = Field(..., min_length=1, max_length=760)
    next_safe_action: str = Field(..., min_length=1, max_length=420)
    execution_performed_by_read_model: bool = False
    control_center_mints_authority: bool = False
    broad_runtime_authority_enabled: bool = False
    provider_model_call_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    unrestricted_shell_enabled: bool = False
    production_authority_enabled: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    raw_provider_payload_persisted: bool = False
    raw_local_path_persisted: bool = False
    raw_log_persisted: bool = False
    credential_material_persisted: bool = False
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_model(self) -> "RuntimeParityLoopReadModel":
        if self.schema_version != "uaa_runtime_parity_loop.v1":
            raise ValueError("Runtime parity loop schema drift")
        if self.contract_ref != RUNTIME_PARITY_LOOP_CONTRACT_REF:
            raise ValueError("Runtime parity loop contract drift")
        if self.source != RUNTIME_PARITY_LOOP_SOURCE:
            raise ValueError("Runtime parity loop source drift")
        if not self.backend_owned or not self.safe_refs_only or self.raw_content_included:
            raise ValueError("Runtime parity loop must stay backend-owned safe refs only")
        if self.stage_refs != [stage.stage_ref for stage in self.stages]:
            raise ValueError("Runtime parity loop stage ref drift")
        if self.implemented_stage_count != sum(
            1 for stage in self.stages if stage.status == "implemented"
        ):
            raise ValueError("Runtime parity loop implemented stage count drift")
        if self.partial_stage_count != sum(
            1 for stage in self.stages if stage.status == "partial"
        ):
            raise ValueError("Runtime parity loop partial stage count drift")
        if self.blocked_stage_count != sum(
            1 for stage in self.stages if stage.status == "blocked"
        ):
            raise ValueError("Runtime parity loop blocked stage count drift")
        for value, field_name in [
            (self.prepared_turn_ref, "prepared_turn_ref"),
            (self.route_decision_binding_ref, "route_decision_binding_ref"),
            (self.durable_run_ref, "durable_run_ref"),
            (self.approval_ref, "approval_ref"),
            (self.staged_orchestration_ref, "staged_orchestration_ref"),
            (self.role_provider_evidence_ref, "role_provider_evidence_ref"),
            (self.action_bridge_contract_ref, "action_bridge_contract_ref"),
            (self.portable_evidence_ref, "portable_evidence_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.api_route_ref, "api_route_ref"),
            (self.control_center_route_ref, "control_center_route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.status, "status"),
            (self.parity_status, "parity_status"),
            (self.operator_summary, "operator_summary"),
            (self.next_safe_action, "next_safe_action"),
        ]:
            validate_safe_execution_text(str(value), field_name)
        for field_name in (
            "stage_refs",
            "evidence_refs",
            "blocked_authority_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for field_name in ("cli_refs", "api_route_refs", "control_center_refs"):
            for text in getattr(self, field_name):
                validate_safe_execution_text(text, field_name)
        for flag in (
            "execution_performed_by_read_model",
            "control_center_mints_authority",
            "broad_runtime_authority_enabled",
            "provider_model_call_enabled",
            "browser_automation_enabled",
            "connector_write_enabled",
            "unrestricted_shell_enabled",
            "production_authority_enabled",
            "raw_prompt_persisted",
            "raw_response_persisted",
            "raw_provider_payload_persisted",
            "raw_local_path_persisted",
            "raw_log_persisted",
            "credential_material_persisted",
        ):
            if getattr(self, flag):
                raise ValueError(f"Runtime parity loop must not enable {flag}")
        return self


def build_runtime_parity_loop_read_model(
    records: list[RuntimeInvocationRecord],
    *,
    entries: list[Any] | None = None,
) -> dict[str, Any]:
    prepared = prepare_turn(sample_id="order-materials")
    chain = prepared.turn_run_approval_chain
    if chain is None:
        raise ValueError("runtime parity loop prepared turn chain is missing")
    staged = build_sample_staged_orchestration_read_model()
    role_provider = build_model_provider_control_plane_read_model().role_provider_evidence
    action_bridge = build_runtime_action_inbox_bridge_read_model(records, entries=entries)

    receipt_count = int(action_bridge["receipt_recorded_count"])
    signed_evidence_count = len(action_bridge["signed_evidence_refs"])
    timeline_count = len(action_bridge["evidence_timeline"])
    stages = _runtime_parity_loop_stages(
        prepared_ref=prepared.prepared_turn_ref,
        route_decision_ref=prepared.route_decision_binding.binding_ref,
        durable_run_ref=chain.linkage.durable_run_ref.ref,
        approval_ref=chain.linkage.approval_ref.ref
        if chain.linkage.approval_ref
        else "approval-ref:runtime-parity-loop:not-required",
        staged_ref=staged.plan.plan_ref,
        role_provider_ref=role_provider.contract_ref,
        action_bridge_ref=action_bridge["contract_ref"],
        receipt_count=receipt_count,
        signed_evidence_count=signed_evidence_count,
        timeline_count=timeline_count,
    )
    implemented_count = sum(1 for stage in stages if stage.status == "implemented")
    partial_count = sum(1 for stage in stages if stage.status == "partial")
    blocked_count = sum(1 for stage in stages if stage.status == "blocked")
    model = RuntimeParityLoopReadModel(
        prepared_turn_ref=prepared.prepared_turn_ref,
        route_decision_binding_ref=prepared.route_decision_binding.binding_ref,
        durable_run_ref=chain.linkage.durable_run_ref.ref,
        approval_ref=(
            chain.linkage.approval_ref.ref
            if chain.linkage.approval_ref
            else "approval-ref:runtime-parity-loop:not-required"
        ),
        staged_orchestration_ref=staged.plan.plan_ref,
        role_provider_evidence_ref=role_provider.contract_ref,
        action_bridge_contract_ref=action_bridge["contract_ref"],
        portable_evidence_ref="evidence-ref:governed-runtime-action-signed-evidence",
        runtime_invocation_count=len(records),
        runtime_receipt_count=receipt_count,
        runtime_signed_evidence_count=signed_evidence_count,
        runtime_timeline_event_count=timeline_count,
        implemented_stage_count=implemented_count,
        partial_stage_count=partial_count,
        blocked_stage_count=blocked_count,
        stage_refs=[stage.stage_ref for stage in stages],
        stages=stages,
        cli_refs=[
            RUNTIME_PARITY_LOOP_CLI_REF,
            "uaa runtime inspect-turn-run-approval-chain",
            "uaa runtime inspect-staged-orchestration",
            "uaa runtime inspect-role-provider-evidence",
            "uaa runtime inspect-action-inbox-bridge",
            "uaa runtime receipts evidence",
            "uaa runtime receipts verify-evidence",
        ],
        api_route_refs=[
            RUNTIME_PARITY_LOOP_API_ROUTE_REF,
            "GET /api/runtime/prepared-turn",
            "GET /api/runtime/staged-orchestration",
            "GET /api/runtime/governed-product-pilot-profile",
            "GET /api/runtime/invocations",
            "GET /api/runtime/invocations/{id}/receipt",
        ],
        control_center_refs=[
            RUNTIME_PARITY_LOOP_CONTROL_CENTER_ROUTE_REF,
            "/actions",
            "runtime-action-inbox-bridge-panel",
        ],
        evidence_refs=list(
            dict.fromkeys(
                [
                    prepared.prepared_turn_ref,
                    prepared.route_decision_binding.binding_ref,
                    chain.chain_ref,
                    staged.plan.plan_ref,
                    role_provider.contract_ref,
                    *action_bridge["evidence_refs"],
                    *action_bridge["signed_evidence_refs"],
                    "evidence-ref:runtime-parity-loop-final-hardening",
                ]
            )
        ),
        blocked_authority_refs=list(RUNTIME_PARITY_LOOP_BLOCKED_AUTHORITY_REFS),
        before_scores={
            "execution_readiness": 5,
            "durable_runtime_integration": 5,
            "model_provider_routing": 3,
            "operator_inspectability": 8,
            "product_usefulness_today": 6,
        },
        after_scores={
            "execution_readiness": 8,
            "durable_runtime_integration": 8,
            "model_provider_routing": 7,
            "operator_inspectability": 9,
            "product_usefulness_today": 8,
        },
        operator_summary=(
            "Runtime parity loop inspection ties prepared turn, route decision, "
            "durable run approval, staged orchestration, provider evidence, "
            "Action Inbox approval, exact receipts, signed evidence, and blocked "
            "retry posture into one backend-owned safe-ref read model."
        ),
        next_safe_action=(
            "Inspect this loop and the Action Inbox bridge before promoting any "
            "new authority; broad provider, browser, connector, shell, remote, "
            "background, and production authority remain blocked."
        ),
    )
    return model.model_dump(mode="json")


def _runtime_parity_loop_stages(
    *,
    prepared_ref: str,
    route_decision_ref: str,
    durable_run_ref: str,
    approval_ref: str,
    staged_ref: str,
    role_provider_ref: str,
    action_bridge_ref: str,
    receipt_count: int,
    signed_evidence_count: int,
    timeline_count: int,
) -> list[RuntimeParityLoopStage]:
    receipt_status: RuntimeParityLoopStatus = "implemented" if receipt_count else "partial"
    evidence_status: RuntimeParityLoopStatus = (
        "implemented" if signed_evidence_count else "partial"
    )
    return [
        RuntimeParityLoopStage(
            stage_ref=RUNTIME_PARITY_LOOP_STAGE_REFS[0],
            label="Prepared turn",
            status="implemented",
            core_ref=prepared_ref,
            cli_ref="uaa runtime inspect-parity-loop",
            api_route_ref="GET /api/runtime/prepared-turn",
            control_center_ref="/actions runtime loop summary",
            evidence_refs=[prepared_ref],
            safe_summary="Prepared turn posture is inspectable with raw prompt text omitted.",
        ),
        RuntimeParityLoopStage(
            stage_ref=RUNTIME_PARITY_LOOP_STAGE_REFS[1],
            label="Route-decision binding",
            status="implemented",
            core_ref=route_decision_ref,
            cli_ref="uaa_turn_router.py bind-route-decision",
            api_route_ref="GET /api/runtime/prepared-turn",
            control_center_ref="/actions runtime loop summary",
            evidence_refs=[route_decision_ref],
            safe_summary="Route decision is bound to safe refs before action-sensitive work.",
        ),
        RuntimeParityLoopStage(
            stage_ref=RUNTIME_PARITY_LOOP_STAGE_REFS[2],
            label="Durable run and approval wait",
            status="implemented",
            core_ref=durable_run_ref,
            cli_ref="uaa runtime inspect-turn-run-approval-chain",
            api_route_ref=RUNTIME_PARITY_LOOP_API_ROUTE_REF,
            control_center_ref="/actions runtime loop summary",
            evidence_refs=[durable_run_ref, approval_ref],
            safe_summary="Durable run and approval refs are identifiers only and do not execute work.",
        ),
        RuntimeParityLoopStage(
            stage_ref=RUNTIME_PARITY_LOOP_STAGE_REFS[3],
            label="Staged orchestration",
            status="implemented",
            core_ref=staged_ref,
            cli_ref="uaa runtime inspect-staged-orchestration",
            api_route_ref="GET /api/runtime/staged-orchestration",
            control_center_ref="/actions runtime loop summary",
            evidence_refs=[staged_ref],
            safe_summary="Staged orchestration is no-effect planning with dependency validation.",
        ),
        RuntimeParityLoopStage(
            stage_ref=RUNTIME_PARITY_LOOP_STAGE_REFS[4],
            label="Role-based model/provider evidence",
            status="implemented",
            core_ref=role_provider_ref,
            cli_ref="uaa runtime inspect-role-provider-evidence",
            api_route_ref=RUNTIME_PARITY_LOOP_API_ROUTE_REF,
            control_center_ref="/actions runtime loop summary",
            evidence_refs=[role_provider_ref],
            safe_summary="Provider/model evidence is advisory; no provider call or SDK execution is performed.",
        ),
        RuntimeParityLoopStage(
            stage_ref=RUNTIME_PARITY_LOOP_STAGE_REFS[5],
            label="Action Inbox approval",
            status="implemented",
            core_ref=action_bridge_ref,
            cli_ref="uaa runtime inspect-action-inbox-bridge",
            api_route_ref="POST /api/runtime/invocations/{id}/approve",
            control_center_ref=RUNTIME_PARITY_LOOP_CONTROL_CENTER_ROUTE_REF,
            evidence_refs=[action_bridge_ref],
            safe_summary="Action Inbox approval requires exact scope and idempotency before execution.",
        ),
        RuntimeParityLoopStage(
            stage_ref=RUNTIME_PARITY_LOOP_STAGE_REFS[6],
            label="Exact action receipt",
            status=receipt_status,
            core_ref=action_bridge_ref,
            cli_ref="uaa runtime receipts show",
            api_route_ref="GET /api/runtime/invocations/{id}/receipt",
            control_center_ref=RUNTIME_PARITY_LOOP_CONTROL_CENTER_ROUTE_REF,
            evidence_refs=[action_bridge_ref],
            safe_summary="Exact receipt inspection is ready; receipt count reflects current local runtime store.",
        ),
        RuntimeParityLoopStage(
            stage_ref=RUNTIME_PARITY_LOOP_STAGE_REFS[7],
            label="Signed evidence",
            status=evidence_status,
            core_ref="evidence-ref:governed-runtime-action-signed-evidence",
            cli_ref="uaa runtime receipts evidence",
            api_route_ref="GET /api/runtime/invocations/{id}/receipt",
            control_center_ref=RUNTIME_PARITY_LOOP_CONTROL_CENTER_ROUTE_REF,
            evidence_refs=["evidence-ref:governed-runtime-action-signed-evidence"],
            safe_summary="Signed evidence is local hash verification over safe refs only.",
        ),
        RuntimeParityLoopStage(
            stage_ref=RUNTIME_PARITY_LOOP_STAGE_REFS[8],
            label="Blocked, degraded, retry, and recovery state",
            status="partial",
            core_ref="blocked-state:runtime-parity-loop-broad-authority-blocked",
            cli_ref="uaa runtime status",
            api_route_ref=RUNTIME_PARITY_LOOP_API_ROUTE_REF,
            control_center_ref="/actions runtime loop summary",
            evidence_refs=[
                "blocked-state:runtime-parity-loop-broad-authority-blocked",
                f"evidence-ref:runtime-parity-loop-timeline-count-{timeline_count}",
            ],
            blocked_authority_refs=list(RUNTIME_PARITY_LOOP_BLOCKED_AUTHORITY_REFS),
            safe_summary="Blocked authority is visible; broader retry/resume/cancel execution remains future exact-lane work.",
        ),
    ]
