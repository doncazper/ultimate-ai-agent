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


RUNTIME_SLASH_COMMAND_REGISTRY_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-slash-command-registry:v1"
)
RUNTIME_SLASH_COMMAND_REGISTRY_ROUTE_REF = "GET /api/runtime/slash-command-registry"
RUNTIME_SLASH_COMMAND_REGISTRY_CLI_REF = "uaa runtime inspect-slash-command-registry"
RUNTIME_SLASH_COMMAND_REGISTRY_SNAPSHOT_REF = (
    "slash-command-registry-snapshot-ref:runtime:metadata"
)
RUNTIME_SLASH_COMMAND_REGISTRY_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-36:slash-command-registry"
)
RUNTIME_SLASH_COMMAND_REGISTRY_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-36:slash-command-registry"
)
RUNTIME_SLASH_COMMAND_REGISTRY_AUTHORITY_STATE_ROUTE_REF = (
    "GET /api/runtime/authority-state"
)
RUNTIME_SLASH_COMMAND_REGISTRY_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_SLASH_COMMAND_REGISTRY_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-slash-command-registry-metadata"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}

RUNTIME_SLASH_COMMAND_REGISTRY_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:slash-command-registry-no-chat-execution",
    "blocked-authority:slash-command-registry-no-runtime-invocation",
    "blocked-authority:slash-command-registry-no-state-mutation",
    "blocked-authority:slash-command-registry-no-shell-execution",
    "blocked-authority:slash-command-registry-no-provider-call",
    "blocked-authority:slash-command-registry-no-browser-automation",
    "blocked-authority:slash-command-registry-no-connector-write",
    "blocked-authority:slash-command-registry-no-control-center-authority-mint",
    "blocked-authority:slash-command-registry-no-raw-prompt-persistence",
    "blocked-authority:slash-command-registry-no-raw-response-persistence",
)


class RuntimeSlashCommandStatus(str, Enum):
    metadata_ready = "metadata_ready"
    disabled_requires_exact_lane = "disabled_requires_exact_lane"
    blocked_high_authority = "blocked_high_authority"


class RuntimeSlashCommandAuthorityClass(str, Enum):
    read_only_metadata = "read_only_metadata"
    proposal_only = "proposal_only"
    approval_required_future_lane = "approval_required_future_lane"
    blocked_high_authority = "blocked_high_authority"


class RuntimeSlashCommandSideEffectClass(str, Enum):
    none = "none"
    proposal_only = "proposal_only"
    command_execution = "command_execution"
    model_call = "model_call"
    local_mutation = "local_mutation"
    runtime_invocation = "runtime_invocation"


class RuntimeSlashCommandRegistryEntry(BaseModel):
    command_ref: str
    display_label: str
    trigger_label: str
    command_status: RuntimeSlashCommandStatus
    authority_class: RuntimeSlashCommandAuthorityClass
    side_effect_class: RuntimeSlashCommandSideEffectClass
    docs_ref: str
    approval_policy_ref: str
    idempotency_policy_ref: str
    receipt_plan_ref: str
    proof_ref: str
    safe_summary: str
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    visible_in_control_center: bool = True
    registered_metadata_only: bool = True
    chat_trigger_enabled: bool = False
    runtime_invocation_enabled: bool = False
    state_mutation_enabled: bool = False
    shell_execution_enabled: bool = False
    provider_call_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    control_center_mints_authority: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_entry(self) -> "RuntimeSlashCommandRegistryEntry":
        for value, field_name in [
            (self.command_ref, "command_ref"),
            (self.docs_ref, "docs_ref"),
            (self.approval_policy_ref, "approval_policy_ref"),
            (self.idempotency_policy_ref, "idempotency_policy_ref"),
            (self.receipt_plan_ref, "receipt_plan_ref"),
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
            (self.display_label, "display_label"),
            (self.trigger_label, "trigger_label"),
            (str(self.command_status), "command_status"),
            (str(self.authority_class), "authority_class"),
            (str(self.side_effect_class), "side_effect_class"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "chat_trigger_enabled": self.chat_trigger_enabled,
            "runtime_invocation_enabled": self.runtime_invocation_enabled,
            "state_mutation_enabled": self.state_mutation_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "control_center_mints_authority": self.control_center_mints_authority,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_SLASH_COMMAND_ENTRY_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.visible_in_control_center or not self.registered_metadata_only:
            raise ValueError("RUNTIME_SLASH_COMMAND_METADATA_VISIBILITY_REQUIRED")
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_SLASH_COMMAND_BLOCKERS_REQUIRED")
        return self


class RuntimeSlashCommandRegistryReadModel(BaseModel):
    schema_version: str = "runtime_slash_command_registry.v1"
    contract_ref: str = RUNTIME_SLASH_COMMAND_REGISTRY_CONTRACT_REF
    status: str = "metadata_registry_all_commands_disabled"
    snapshot_ref: str = RUNTIME_SLASH_COMMAND_REGISTRY_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:slash-command-registry:pending"
    route_ref: str = RUNTIME_SLASH_COMMAND_REGISTRY_ROUTE_REF
    cli_ref: str = RUNTIME_SLASH_COMMAND_REGISTRY_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    authority_state_route_ref: str = (
        RUNTIME_SLASH_COMMAND_REGISTRY_AUTHORITY_STATE_ROUTE_REF
    )
    authority_state_cli_ref: str = (
        RUNTIME_SLASH_COMMAND_REGISTRY_AUTHORITY_STATE_CLI_REF
    )
    authority_state_mapping_ref: str
    authority_state_catalog_ref: str
    authority_state_decision_ref: str
    authority_state_decision_outcome: str
    authority_state_status: str
    authority_state_operator_message: str
    authority_state_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "Slash command registry exposes documented command metadata and "
        "authority labels only; command execution and runtime invocation "
        "remain blocked."
    )
    commands: list[RuntimeSlashCommandRegistryEntry] = Field(default_factory=list)
    command_count: int = 0
    metadata_ready_count: int = 0
    disabled_count: int = 0
    blocked_count: int = 0
    command_contract_visible: bool = True
    side_effect_class_visible: bool = True
    approval_policy_visible: bool = True
    idempotency_policy_visible: bool = True
    receipt_plan_visible: bool = True
    cli_api_alignment_visible: bool = True
    chat_trigger_enabled: bool = False
    runtime_invocation_enabled: bool = False
    state_mutation_enabled: bool = False
    shell_execution_enabled: bool = False
    provider_call_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    control_center_mints_authority: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + [
            "raw_prompts_omitted",
            "raw_responses_omitted",
            "provider_payloads_omitted",
            "runtime_payloads_omitted",
            "command_execution_outputs_omitted",
        ]
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeSlashCommandRegistryReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.authority_state_mapping_ref, "authority_state_mapping_ref"),
            (self.authority_state_catalog_ref, "authority_state_catalog_ref"),
            (self.authority_state_decision_ref, "authority_state_decision_ref"),
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
            "blocked_authority_refs",
            "promotion_path_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
            "authority_state_reason_refs",
            "unsupported_adapter_refs",
            "redactions_applied",
        ):
            for value in getattr(self, field_name):
                if field_name == "redactions_applied":
                    validate_safe_execution_text(value, field_name)
                else:
                    validate_execution_ref(value, field_name)
        if (
            self.authority_state_mapping_ref
            != RUNTIME_SLASH_COMMAND_REGISTRY_AUTHORITY_MAPPING_REF
        ):
            raise ValueError("RUNTIME_SLASH_COMMAND_AUTHORITY_MAPPING_UNKNOWN")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_SLASH_COMMAND_AUTHORITY_OUTCOME_UNKNOWN")
        if self.command_count != len(self.commands):
            raise ValueError("RUNTIME_SLASH_COMMAND_COUNT_DRIFT")
        status_counts = {
            RuntimeSlashCommandStatus.metadata_ready.value: self.metadata_ready_count,
            RuntimeSlashCommandStatus.disabled_requires_exact_lane.value: (
                self.disabled_count
            ),
            RuntimeSlashCommandStatus.blocked_high_authority.value: self.blocked_count,
        }
        for status, expected in status_counts.items():
            actual = sum(1 for command in self.commands if command.command_status == status)
            if actual != expected:
                raise ValueError("RUNTIME_SLASH_COMMAND_STATUS_COUNT_DRIFT")
        visibility_flags = {
            "command_contract_visible": self.command_contract_visible,
            "side_effect_class_visible": self.side_effect_class_visible,
            "approval_policy_visible": self.approval_policy_visible,
            "idempotency_policy_visible": self.idempotency_policy_visible,
            "receipt_plan_visible": self.receipt_plan_visible,
            "cli_api_alignment_visible": self.cli_api_alignment_visible,
        }
        missing = [name for name, value in visibility_flags.items() if not value]
        if missing:
            raise ValueError(
                "RUNTIME_SLASH_COMMAND_VISIBILITY_REQUIRED: "
                + ", ".join(missing)
            )
        denied_flags = {
            "chat_trigger_enabled": self.chat_trigger_enabled,
            "runtime_invocation_enabled": self.runtime_invocation_enabled,
            "state_mutation_enabled": self.state_mutation_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "control_center_mints_authority": self.control_center_mints_authority,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_SLASH_COMMAND_REGISTRY_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        for ref in RUNTIME_SLASH_COMMAND_REGISTRY_BLOCKED_AUTHORITY_REFS:
            if ref not in self.blocked_authority_refs:
                raise ValueError("RUNTIME_SLASH_COMMAND_BLOCKER_MISSING")
        if RUNTIME_SLASH_COMMAND_REGISTRY_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_SLASH_COMMAND_PROOF_REF_REQUIRED")
        if RUNTIME_SLASH_COMMAND_REGISTRY_VERIFIER_REF not in self.verifier_refs:
            raise ValueError("RUNTIME_SLASH_COMMAND_VERIFIER_REF_REQUIRED")
        return self


def _snapshot_hash_ref(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(encoded).hexdigest()[:24]
    return f"snapshot-hash-ref:slash-command-registry:{digest}"


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _command(
    slug: str,
    *,
    display_label: str,
    trigger_label: str,
    command_status: RuntimeSlashCommandStatus,
    authority_class: RuntimeSlashCommandAuthorityClass,
    side_effect_class: RuntimeSlashCommandSideEffectClass,
    safe_summary: str,
) -> RuntimeSlashCommandRegistryEntry:
    return RuntimeSlashCommandRegistryEntry(
        command_ref=f"slash-command-ref:{slug}",
        display_label=display_label,
        trigger_label=trigger_label,
        command_status=command_status,
        authority_class=authority_class,
        side_effect_class=side_effect_class,
        docs_ref=f"docs-ref:runtime-slash-command-registry:{slug}",
        approval_policy_ref=f"approval-policy-ref:slash-command:{slug}",
        idempotency_policy_ref=f"idempotency-policy-ref:slash-command:{slug}",
        receipt_plan_ref=f"receipt-plan-ref:slash-command:{slug}",
        proof_ref=RUNTIME_SLASH_COMMAND_REGISTRY_PROOF_REF,
        safe_summary=safe_summary,
        blocked_authority_refs=list(
            RUNTIME_SLASH_COMMAND_REGISTRY_BLOCKED_AUTHORITY_REFS
        ),
        promotion_path_refs=[f"promotion-path-ref:slash-command:{slug}:contract"],
        next_safe_action_refs=[f"next-safe-action-ref:slash-command:{slug}:review"],
    )


def build_runtime_slash_command_registry_read_model(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None = None,
) -> RuntimeSlashCommandRegistryReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    commands = [
        _command(
            "explain-repo",
            display_label="Explain repo",
            trigger_label="/explain",
            command_status=RuntimeSlashCommandStatus.metadata_ready,
            authority_class=RuntimeSlashCommandAuthorityClass.read_only_metadata,
            side_effect_class=RuntimeSlashCommandSideEffectClass.none,
            safe_summary=(
                "Registry metadata for a future explain command; chat execution "
                "is not enabled by this posture."
            ),
        ),
        _command(
            "plan-task",
            display_label="Plan task",
            trigger_label="/plan",
            command_status=RuntimeSlashCommandStatus.metadata_ready,
            authority_class=RuntimeSlashCommandAuthorityClass.proposal_only,
            side_effect_class=RuntimeSlashCommandSideEffectClass.proposal_only,
            safe_summary=(
                "Registry metadata for proposal-only planning; no runtime is "
                "invoked and no plan is executed."
            ),
        ),
        _command(
            "open-proof",
            display_label="Open proof",
            trigger_label="/proof",
            command_status=RuntimeSlashCommandStatus.metadata_ready,
            authority_class=RuntimeSlashCommandAuthorityClass.read_only_metadata,
            side_effect_class=RuntimeSlashCommandSideEffectClass.none,
            safe_summary=(
                "Registry metadata for proof navigation; this route does not "
                "open or mutate proof records."
            ),
        ),
        _command(
            "run-tests",
            display_label="Run tests",
            trigger_label="/run-tests",
            command_status=RuntimeSlashCommandStatus.disabled_requires_exact_lane,
            authority_class=(
                RuntimeSlashCommandAuthorityClass.approval_required_future_lane
            ),
            side_effect_class=RuntimeSlashCommandSideEffectClass.command_execution,
            safe_summary=(
                "Test execution command remains disabled until bound to an "
                "exact allowlisted command lane with approval and receipt."
            ),
        ),
        _command(
            "ask-agent",
            display_label="Ask agent",
            trigger_label="/ask-agent",
            command_status=RuntimeSlashCommandStatus.disabled_requires_exact_lane,
            authority_class=(
                RuntimeSlashCommandAuthorityClass.approval_required_future_lane
            ),
            side_effect_class=RuntimeSlashCommandSideEffectClass.model_call,
            safe_summary=(
                "Delegated agent command remains disabled until runtime and "
                "provider boundaries are exact-scoped."
            ),
        ),
        _command(
            "apply-patch",
            display_label="Apply patch",
            trigger_label="/apply-patch",
            command_status=RuntimeSlashCommandStatus.blocked_high_authority,
            authority_class=RuntimeSlashCommandAuthorityClass.blocked_high_authority,
            side_effect_class=RuntimeSlashCommandSideEffectClass.local_mutation,
            safe_summary=(
                "Patch application command is high-authority and remains blocked "
                "without exact patch, approval, checkpoint, receipt, and rollback."
            ),
        ),
    ]
    payload_for_hash: dict[str, object] = {
        "commands": [command.model_dump(mode="json") for command in commands],
        "blocked": list(RUNTIME_SLASH_COMMAND_REGISTRY_BLOCKED_AUTHORITY_REFS),
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
    }
    return RuntimeSlashCommandRegistryReadModel(
        snapshot_hash_ref=_snapshot_hash_ref(payload_for_hash),
        authority_state_mapping_ref=authority_entry.lane_ref,
        authority_state_catalog_ref=authority_entry.catalog_ref,
        authority_state_decision_ref=authority_entry.decision.decision_ref,
        authority_state_decision_outcome=_authority_value(
            authority_entry.decision.outcome
        ),
        authority_state_status=authority_entry.status,
        authority_state_operator_message=authority_entry.decision.operator_message,
        authority_state_reason_refs=list(authority_entry.decision.reason_refs),
        unsupported_adapter_refs=list(authority_entry.unsupported_adapter_refs),
        commands=commands,
        command_count=len(commands),
        metadata_ready_count=sum(
            1
            for command in commands
            if command.command_status == RuntimeSlashCommandStatus.metadata_ready.value
        ),
        disabled_count=sum(
            1
            for command in commands
            if command.command_status
            == RuntimeSlashCommandStatus.disabled_requires_exact_lane.value
        ),
        blocked_count=sum(
            1
            for command in commands
            if command.command_status
            == RuntimeSlashCommandStatus.blocked_high_authority.value
        ),
        blocked_authority_refs=list(
            RUNTIME_SLASH_COMMAND_REGISTRY_BLOCKED_AUTHORITY_REFS
        ),
        promotion_path_refs=[
            "promotion-path-ref:slash-command-registry:command-contract",
            "promotion-path-ref:slash-command-registry:side-effect-class",
            "promotion-path-ref:slash-command-registry:approval-policy",
            "promotion-path-ref:slash-command-registry:idempotency",
            "promotion-path-ref:slash-command-registry:receipt",
            "promotion-path-ref:slash-command-registry:tests",
        ],
        proof_refs=[
            RUNTIME_SLASH_COMMAND_REGISTRY_PROOF_REF,
            "proof-ref:slash-command-registry:metadata-only",
            "proof-ref:slash-command-registry:execution-blocked",
        ],
        verifier_refs=[RUNTIME_SLASH_COMMAND_REGISTRY_VERIFIER_REF],
        next_safe_action_refs=[
            "next-safe-action-ref:slash-command-registry:bind-command-contract",
            "next-safe-action-ref:slash-command-registry:define-chat-parser",
            "next-safe-action-ref:slash-command-registry:keep-execution-blocked",
        ],
    )


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None,
) -> AuthorityDecisionCatalogEntry:
    catalog = authority_decision_catalog or build_authority_decision_catalog()
    entries = {entry.lane_ref: entry for entry in catalog}
    if RUNTIME_SLASH_COMMAND_REGISTRY_AUTHORITY_MAPPING_REF not in entries:
        raise ValueError("RUNTIME_SLASH_COMMAND_AUTHORITY_CATALOG_MISSING")
    return entries[RUNTIME_SLASH_COMMAND_REGISTRY_AUTHORITY_MAPPING_REF]
