from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityDecisionCatalogEntry,
    build_authority_decision_catalog,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)


RUNTIME_INTERRUPT_REDIRECT_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-interrupt-redirect:v1"
)
RUNTIME_INTERRUPT_REDIRECT_ROUTE_REF = "GET /api/runtime/interrupt-redirect"
RUNTIME_INTERRUPT_REDIRECT_CLI_REF = "uaa runtime inspect-interrupt-redirect"
RUNTIME_INTERRUPT_REDIRECT_SNAPSHOT_REF = (
    "interrupt-redirect-snapshot-ref:runtime:control-posture"
)
RUNTIME_INTERRUPT_REDIRECT_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-37:interrupt-redirect"
)
RUNTIME_INTERRUPT_REDIRECT_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-37:interrupt-redirect"
)
RUNTIME_INTERRUPT_REDIRECT_AUTHORITY_STATE_ROUTE_REF = (
    "GET /api/runtime/authority-state"
)
RUNTIME_INTERRUPT_REDIRECT_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_INTERRUPT_REDIRECT_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-interrupt-redirect-proposals"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}

RUNTIME_INTERRUPT_REDIRECT_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:interrupt-redirect-no-live-stop-post",
    "blocked-authority:interrupt-redirect-no-process-kill",
    "blocked-authority:interrupt-redirect-no-runtime-mutation",
    "blocked-authority:interrupt-redirect-no-background-autonomy",
    "blocked-authority:interrupt-redirect-no-unscoped-approval-reuse",
    "blocked-authority:interrupt-redirect-no-shell-execution",
    "blocked-authority:interrupt-redirect-no-provider-call",
    "blocked-authority:interrupt-redirect-no-browser-automation",
    "blocked-authority:interrupt-redirect-no-connector-write",
    "blocked-authority:interrupt-redirect-no-control-center-authority-mint",
    "blocked-authority:interrupt-redirect-no-raw-runtime-payload-persistence",
    "blocked-authority:interrupt-redirect-no-raw-log-persistence",
)


class RuntimeRunControlActionKind(str, Enum):
    pause = "pause"
    stop = "stop"
    redirect = "redirect"
    revise = "revise"
    recover = "recover"


class RuntimeRunControlActionStatus(str, Enum):
    read_only_proposal = "read_only_proposal"
    blocked_until_exact_lane = "blocked_until_exact_lane"
    approval_required_future_lane = "approval_required_future_lane"


class RuntimeRunControlSideEffectClass(str, Enum):
    none = "none"
    runtime_control_mutation = "runtime_control_mutation"
    operator_instruction_update = "operator_instruction_update"
    recovery_state_transition = "recovery_state_transition"


class RuntimeRunControlProposal(BaseModel):
    action_ref: str
    action_kind: RuntimeRunControlActionKind
    display_label: str
    action_status: RuntimeRunControlActionStatus
    side_effect_class: RuntimeRunControlSideEffectClass
    approval_scope_ref: str
    idempotency_ref: str
    receipt_plan_ref: str
    recovery_state_ref: str
    proof_ref: str
    safe_summary: str
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    visible_in_control_center: bool = True
    proposal_only: bool = True
    live_stop_post_enabled: bool = False
    process_kill_enabled: bool = False
    runtime_mutation_enabled: bool = False
    background_autonomy_enabled: bool = False
    shell_execution_enabled: bool = False
    provider_call_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    control_center_mints_authority: bool = False
    raw_runtime_payload_persisted: bool = False
    raw_log_persisted: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_proposal(self) -> "RuntimeRunControlProposal":
        for value, field_name in [
            (self.action_ref, "action_ref"),
            (self.approval_scope_ref, "approval_scope_ref"),
            (self.idempotency_ref, "idempotency_ref"),
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.recovery_state_ref, "recovery_state_ref"),
            (self.proof_ref, "proof_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "promotion_path_refs",
            "next_safe_action_refs",
        ):
            for value in getattr(self, field_name):
                validate_execution_ref(value, field_name)
        for value, field_name in [
            (str(self.action_kind), "action_kind"),
            (self.display_label, "display_label"),
            (str(self.action_status), "action_status"),
            (str(self.side_effect_class), "side_effect_class"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "live_stop_post_enabled": self.live_stop_post_enabled,
            "process_kill_enabled": self.process_kill_enabled,
            "runtime_mutation_enabled": self.runtime_mutation_enabled,
            "background_autonomy_enabled": self.background_autonomy_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "control_center_mints_authority": self.control_center_mints_authority,
            "raw_runtime_payload_persisted": self.raw_runtime_payload_persisted,
            "raw_log_persisted": self.raw_log_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_INTERRUPT_REDIRECT_ACTION_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.visible_in_control_center or not self.proposal_only:
            raise ValueError("RUNTIME_INTERRUPT_REDIRECT_PROPOSAL_VISIBILITY_REQUIRED")
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_INTERRUPT_REDIRECT_ACTION_BLOCKERS_REQUIRED")
        return self


class RuntimeInterruptRedirectReadModel(BaseModel):
    schema_version: str = "runtime_interrupt_redirect.v1"
    contract_ref: str = RUNTIME_INTERRUPT_REDIRECT_CONTRACT_REF
    status: str = "run_control_proposal_only"
    snapshot_ref: str = RUNTIME_INTERRUPT_REDIRECT_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:interrupt-redirect:pending"
    route_ref: str = RUNTIME_INTERRUPT_REDIRECT_ROUTE_REF
    cli_ref: str = RUNTIME_INTERRUPT_REDIRECT_CLI_REF
    authority_state_route_ref: str = (
        RUNTIME_INTERRUPT_REDIRECT_AUTHORITY_STATE_ROUTE_REF
    )
    authority_state_cli_ref: str = RUNTIME_INTERRUPT_REDIRECT_AUTHORITY_STATE_CLI_REF
    authority_state_mapping_ref: str
    authority_state_catalog_ref: str
    authority_state_decision_ref: str
    authority_state_decision_outcome: str
    authority_state_status: str
    authority_state_operator_message: str
    authority_state_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    safe_summary: str = (
        "Interrupt, pause, stop, redirect, revise, and recovery controls are "
        "visible as proposal or blocked posture only; UAA does not issue live "
        "runtime stop or process-kill mutations."
    )
    proposals: list[RuntimeRunControlProposal] = Field(default_factory=list)
    proposal_count: int = 0
    read_only_proposal_count: int = 0
    approval_required_future_lane_count: int = 0
    blocked_count: int = 0
    run_ownership_visible: bool = True
    stop_scope_visible: bool = True
    idempotency_visible: bool = True
    cancellation_receipt_visible: bool = True
    recovery_state_visible: bool = True
    proof_link_visible: bool = True
    live_stop_post_enabled: bool = False
    process_kill_enabled: bool = False
    runtime_mutation_enabled: bool = False
    background_autonomy_enabled: bool = False
    shell_execution_enabled: bool = False
    provider_call_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    control_center_mints_authority: bool = False
    raw_runtime_payload_persisted: bool = False
    raw_log_persisted: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + [
            "raw_runtime_payloads_omitted",
            "raw_logs_omitted",
            "process_identifiers_omitted",
            "operator_instruction_text_omitted",
        ]
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeInterruptRedirectReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.authority_state_mapping_ref, "authority_state_mapping_ref"),
            (self.authority_state_catalog_ref, "authority_state_catalog_ref"),
            (self.authority_state_decision_ref, "authority_state_decision_ref"),
            (self.control_center_ref, "control_center_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.authority_state_route_ref, "authority_state_route_ref"),
            (self.authority_state_cli_ref, "authority_state_cli_ref"),
            (
                self.authority_state_decision_outcome,
                "authority_state_decision_outcome",
            ),
            (self.authority_state_status, "authority_state_status"),
            (
                self.authority_state_operator_message,
                "authority_state_operator_message",
            ),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for field_name in (
            "authority_state_reason_refs",
            "unsupported_adapter_refs",
            "blocked_authority_refs",
            "promotion_path_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
        ):
            for value in getattr(self, field_name):
                validate_execution_ref(value, field_name)
        if (
            self.authority_state_mapping_ref
            != RUNTIME_INTERRUPT_REDIRECT_AUTHORITY_MAPPING_REF
        ):
            raise ValueError("RUNTIME_INTERRUPT_REDIRECT_AUTHORITY_MAPPING_STALE")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_INTERRUPT_REDIRECT_AUTHORITY_OUTCOME_UNKNOWN")
        for value in self.redactions_applied:
            validate_safe_execution_text(value, "redactions_applied")
        denied_flags = {
            "live_stop_post_enabled": self.live_stop_post_enabled,
            "process_kill_enabled": self.process_kill_enabled,
            "runtime_mutation_enabled": self.runtime_mutation_enabled,
            "background_autonomy_enabled": self.background_autonomy_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "control_center_mints_authority": self.control_center_mints_authority,
            "raw_runtime_payload_persisted": self.raw_runtime_payload_persisted,
            "raw_log_persisted": self.raw_log_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_INTERRUPT_REDIRECT_READ_MODEL_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if set(RUNTIME_INTERRUPT_REDIRECT_BLOCKED_AUTHORITY_REFS) - set(
            self.blocked_authority_refs
        ):
            raise ValueError("RUNTIME_INTERRUPT_REDIRECT_BLOCKERS_REQUIRED")
        if self.proposal_count != len(self.proposals):
            raise ValueError("RUNTIME_INTERRUPT_REDIRECT_PROPOSAL_COUNT_MISMATCH")
        return self


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _proposal(
    *,
    action_kind: RuntimeRunControlActionKind,
    display_label: str,
    action_status: RuntimeRunControlActionStatus,
    side_effect_class: RuntimeRunControlSideEffectClass,
    summary: str,
) -> RuntimeRunControlProposal:
    action_token = action_kind.value.replace("_", "-")
    return RuntimeRunControlProposal(
        action_ref=f"run-control-action-ref:runtime:{action_token}",
        action_kind=action_kind,
        display_label=display_label,
        action_status=action_status,
        side_effect_class=side_effect_class,
        approval_scope_ref=f"approval-scope-ref:runtime-run-control:{action_token}",
        idempotency_ref=f"idempotency-ref:runtime-run-control:{action_token}",
        receipt_plan_ref=f"receipt-plan-ref:runtime-run-control:{action_token}",
        recovery_state_ref=f"recovery-state-ref:runtime-run-control:{action_token}",
        proof_ref=f"proof-ref:runtime-run-control:{action_token}",
        safe_summary=summary,
        blocked_authority_refs=list(RUNTIME_INTERRUPT_REDIRECT_BLOCKED_AUTHORITY_REFS),
        promotion_path_refs=[
            f"promotion-path-ref:runtime-run-control:{action_token}:approval-binding",
            f"promotion-path-ref:runtime-run-control:{action_token}:cancellation-receipt",
        ],
        next_safe_action_refs=[
            f"next-safe-action-ref:runtime-run-control:{action_token}:exact-lane-design"
        ],
    )


def build_runtime_interrupt_redirect_read_model(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None = None,
) -> RuntimeInterruptRedirectReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    proposals = [
        _proposal(
            action_kind=RuntimeRunControlActionKind.pause,
            display_label="Pause current work",
            action_status=RuntimeRunControlActionStatus.approval_required_future_lane,
            side_effect_class=RuntimeRunControlSideEffectClass.runtime_control_mutation,
            summary=(
                "Pause is planned as an approval-bound cancellation checkpoint; "
                "this read model does not pause a live runtime."
            ),
        ),
        _proposal(
            action_kind=RuntimeRunControlActionKind.stop,
            display_label="Stop current work",
            action_status=RuntimeRunControlActionStatus.blocked_until_exact_lane,
            side_effect_class=RuntimeRunControlSideEffectClass.runtime_control_mutation,
            summary=(
                "Stop remains blocked until UAA can prove run ownership, "
                "idempotency, cancellation receipt, and recovery state."
            ),
        ),
        _proposal(
            action_kind=RuntimeRunControlActionKind.redirect,
            display_label="Redirect work",
            action_status=RuntimeRunControlActionStatus.read_only_proposal,
            side_effect_class=RuntimeRunControlSideEffectClass.operator_instruction_update,
            summary=(
                "Redirect is represented as a safe proposal artifact; no "
                "runtime instruction is sent from this lane."
            ),
        ),
        _proposal(
            action_kind=RuntimeRunControlActionKind.revise,
            display_label="Revise task",
            action_status=RuntimeRunControlActionStatus.read_only_proposal,
            side_effect_class=RuntimeRunControlSideEffectClass.operator_instruction_update,
            summary=(
                "Revise captures the intended future contract for operator "
                "edits without persisting raw instruction text."
            ),
        ),
        _proposal(
            action_kind=RuntimeRunControlActionKind.recover,
            display_label="Recover safely",
            action_status=RuntimeRunControlActionStatus.approval_required_future_lane,
            side_effect_class=RuntimeRunControlSideEffectClass.recovery_state_transition,
            summary=(
                "Recover is a future approval-bound lane for resuming from a "
                "known checkpoint or blocked state."
            ),
        ),
    ]
    payload = {
        "contract_ref": RUNTIME_INTERRUPT_REDIRECT_CONTRACT_REF,
        "snapshot_ref": RUNTIME_INTERRUPT_REDIRECT_SNAPSHOT_REF,
        "route_ref": RUNTIME_INTERRUPT_REDIRECT_ROUTE_REF,
        "cli_ref": RUNTIME_INTERRUPT_REDIRECT_CLI_REF,
        "authority_state_mapping_ref": authority_entry.lane_ref,
        "authority_state_catalog_ref": authority_entry.catalog_ref,
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
        "authority_state_status": authority_entry.status,
        "authority_state_operator_message": authority_entry.decision.operator_message,
        "authority_state_reason_refs": list(authority_entry.decision.reason_refs),
        "unsupported_adapter_refs": list(authority_entry.unsupported_adapter_refs),
        "proposals": proposals,
        "proposal_count": len(proposals),
        "read_only_proposal_count": sum(
            proposal.action_status == RuntimeRunControlActionStatus.read_only_proposal
            for proposal in proposals
        ),
        "approval_required_future_lane_count": sum(
            proposal.action_status
            == RuntimeRunControlActionStatus.approval_required_future_lane
            for proposal in proposals
        ),
        "blocked_count": sum(
            proposal.action_status
            == RuntimeRunControlActionStatus.blocked_until_exact_lane
            for proposal in proposals
        ),
        "blocked_authority_refs": list(RUNTIME_INTERRUPT_REDIRECT_BLOCKED_AUTHORITY_REFS),
        "promotion_path_refs": [
            "promotion-path-ref:interrupt-redirect:run-ownership",
            "promotion-path-ref:interrupt-redirect:stop-scope",
            "promotion-path-ref:interrupt-redirect:idempotency",
            "promotion-path-ref:interrupt-redirect:cancellation-receipt",
            "promotion-path-ref:interrupt-redirect:event-proof",
            "promotion-path-ref:interrupt-redirect:recovery-state",
        ],
        "proof_refs": [RUNTIME_INTERRUPT_REDIRECT_PROOF_REF],
        "verifier_refs": [RUNTIME_INTERRUPT_REDIRECT_VERIFIER_REF],
        "next_safe_action_refs": [
            "next-safe-action-ref:interrupt-redirect:approval-bound-stop-contract",
            "next-safe-action-ref:interrupt-redirect:recovery-state-machine",
        ],
    }
    snapshot_material = {
        "contract_ref": payload["contract_ref"],
        "route_ref": payload["route_ref"],
        "proposal_refs": [proposal.action_ref for proposal in proposals],
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
        "blocked_authority_refs": payload["blocked_authority_refs"],
    }
    payload["snapshot_hash_ref"] = (
        "snapshot-hash-ref:interrupt-redirect:"
        + hashlib.sha256(
            json.dumps(snapshot_material, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
    )
    return RuntimeInterruptRedirectReadModel(**payload)


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None,
) -> AuthorityDecisionCatalogEntry:
    catalog = authority_decision_catalog or build_authority_decision_catalog()
    for entry in catalog:
        if entry.lane_ref == RUNTIME_INTERRUPT_REDIRECT_AUTHORITY_MAPPING_REF:
            return entry
    raise ValueError("RUNTIME_INTERRUPT_REDIRECT_AUTHORITY_MAPPING_MISSING")
