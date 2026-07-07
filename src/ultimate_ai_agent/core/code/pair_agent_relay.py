from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)


CODING_PAIR_AGENT_RELAY_SCHEMA_VERSION = (
    "uaa-coding-pair-agent-relay-runner.v1"
)
CODING_PAIR_AGENT_RELAY_LANE_REF = (
    "coding-pair-agent-lane:coding_pair_agent_foreground_relay_runner"
)
CODING_PAIR_AGENT_RELAY_READINESS_REF = (
    "coding-pair-agent-relay-readiness:preview-blocked-v1"
)
CODING_PAIR_AGENT_RELAY_RUN_REF = "coding-pair-run:preview-readiness-v1"
CODING_PAIR_AGENT_RELAY_TASK_REF = "coding-task:pair-agent-preview-v1"
CODING_PAIR_AGENT_RELAY_DOC_REF = "docs-ref:coding-pair-agent-relay-runner"
CODING_PAIR_AGENT_RELAY_UNBLOCK_PROMPT_REF = (
    "prompt-ref:unblock-coding-pair-agent-foreground-relay-runner"
)
CODING_PAIR_AGENT_RELAY_VERIFIER_REF = "verifier-ref:coding-pair-agent-relay-runner"
CODING_PAIR_AGENT_RELAY_BACKEND_ROUTE_REF = (
    "GET /control-center/coding/multi-agent-review"
)
CODING_PAIR_AGENT_RELAY_CLI_REF = (
    "scripts/dev/uaa_coding.py inspect-pair-agent-relay"
)
CODING_PAIR_AGENT_RELAY_REQUIRED_BLOCKED_REFS = [
    "blocked-state:coding-pair-no-generic-agent-bus",
    "blocked-state:coding-pair-no-provider-sdk-call",
    "blocked-state:coding-pair-no-provider-model-call",
    "blocked-state:coding-pair-no-foreground-adapter-execution",
    "blocked-state:coding-pair-no-background-dispatch",
    "blocked-state:coding-pair-no-arbitrary-command-text",
    "blocked-state:coding-pair-no-shell-subprocess",
    "blocked-state:coding-pair-no-plugin-runtime-import",
    "blocked-state:coding-pair-no-browser-automation",
    "blocked-state:coding-pair-no-connector-write",
    "blocked-state:coding-pair-no-git-mutation",
    "blocked-state:coding-pair-no-automatic-patch-apply",
    "blocked-state:coding-pair-no-raw-transcript-persistence",
    "blocked-state:coding-pair-no-production-authority",
    "blocked-state:coding-pair-no-broad-autonomy",
]


PairAgentRelayStatus = Literal["preview_readiness_execution_blocked"]
PairAgentRunState = Literal[
    "created",
    "pending_approval",
    "approved",
    "agent_a_running",
    "waiting_agent_a",
    "agent_b_running",
    "waiting_agent_b",
    "approval_required",
    "user_stopped",
    "max_turns_reached",
    "timed_out",
    "blocked",
    "failed",
    "completed",
]
PairAgentSlotRole = Literal["agent_a", "agent_b"]
PairAgentSlotStatus = Literal["configured_preview", "blocked_execution"]
PairAgentArtifactKind = Literal[
    "outbound_turn_packet",
    "inbound_agent_response",
    "disagreement_summary",
    "candidate_action_list",
    "validation_plan",
    "final_synthesis",
    "blocked_state_report",
]
PairAgentReceiptKind = Literal[
    "run_created",
    "approval_bound",
    "adapter_started",
    "turn_completed",
    "output_redacted",
    "stop_condition_reached",
    "run_completed",
    "run_blocked",
    "run_failed",
]
PairAgentReceiptStatus = Literal["planned_ref", "blocked_ref", "preview_ref"]


ALLOWED_PAIR_AGENT_RELAY_TRANSITIONS: dict[PairAgentRunState, set[PairAgentRunState]] = {
    "created": {"pending_approval", "blocked", "user_stopped"},
    "pending_approval": {"approved", "approval_required", "blocked", "user_stopped"},
    "approved": {"agent_a_running", "blocked", "user_stopped", "timed_out"},
    "agent_a_running": {
        "waiting_agent_a",
        "blocked",
        "failed",
        "timed_out",
        "user_stopped",
    },
    "waiting_agent_a": {"agent_b_running", "blocked", "user_stopped", "timed_out"},
    "agent_b_running": {
        "waiting_agent_b",
        "blocked",
        "failed",
        "timed_out",
        "user_stopped",
    },
    "waiting_agent_b": {
        "agent_a_running",
        "approval_required",
        "completed",
        "max_turns_reached",
        "blocked",
        "user_stopped",
        "timed_out",
    },
    "approval_required": {"approved", "blocked", "user_stopped", "timed_out"},
    "user_stopped": set(),
    "max_turns_reached": set(),
    "timed_out": set(),
    "blocked": set(),
    "failed": set(),
    "completed": set(),
}


def validate_pair_agent_relay_transition(
    current_state: PairAgentRunState, next_state: PairAgentRunState
) -> PairAgentRunState:
    allowed = ALLOWED_PAIR_AGENT_RELAY_TRANSITIONS[current_state]
    if next_state not in allowed:
        raise ValueError(f"pair agent relay transition denied {current_state}->{next_state}")
    return next_state


class CodingPairAgentSlotReadModel(BaseModel):
    slot_ref: str = Field(..., min_length=1)
    slot_id: PairAgentSlotRole
    adapter_ref: str = Field(..., min_length=1)
    display_label: str = Field(..., min_length=1, max_length=120)
    status: PairAgentSlotStatus
    argv_template_refs: list[str] = Field(default_factory=list)
    allowed_workspace_refs: list[str] = Field(default_factory=list)
    allowed_mode_refs: list[str] = Field(default_factory=list)
    max_runtime_seconds: int = Field(..., ge=1, le=3600)
    max_output_bytes: int = Field(..., ge=256, le=20000)
    env_policy_ref: str = Field(..., min_length=1)
    disabled_reason_ref: str = Field(..., min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    arbitrary_command_text_allowed: bool = False
    local_agent_process_execution_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    provider_model_call_enabled: bool = False
    background_dispatch_enabled: bool = False
    raw_env_persisted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_slot(self) -> "CodingPairAgentSlotReadModel":
        for ref in [
            self.slot_ref,
            self.adapter_ref,
            self.env_policy_ref,
            self.disabled_reason_ref,
            *self.argv_template_refs,
            *self.allowed_workspace_refs,
            *self.allowed_mode_refs,
            *self.evidence_refs,
            *self.proof_refs,
            *self.blocked_authority_refs,
        ]:
            validate_task_ref(ref, "coding_pair_agent_slot_ref")
        for value in [self.slot_id, self.display_label, self.status]:
            validate_safe_task_text(value, "coding_pair_agent_slot_text")
        if not self.argv_template_refs:
            raise ValueError("pair agent slot needs argv template refs")
        if not self.allowed_workspace_refs:
            raise ValueError("pair agent slot needs workspace refs")
        if not self.blocked_authority_refs:
            raise ValueError("pair agent slot needs blocked authority refs")
        false_flags = {
            "arbitrary_command_text_allowed": self.arbitrary_command_text_allowed,
            "local_agent_process_execution_enabled": (
                self.local_agent_process_execution_enabled
            ),
            "provider_sdk_call_enabled": self.provider_sdk_call_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "background_dispatch_enabled": self.background_dispatch_enabled,
            "raw_env_persisted": self.raw_env_persisted,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
        }
        enabled = [name for name, value in false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding pair agent slot enabled {enabled[0]}")
        return self


class CodingPairAgentTurnPacketReadModel(BaseModel):
    turn_packet_ref: str = Field(..., min_length=1)
    turn_index: int = Field(..., ge=0, le=24)
    sender_slot_ref: str = Field(..., min_length=1)
    receiver_slot_ref: str = Field(..., min_length=1)
    outbound_artifact_ref: str = Field(..., min_length=1)
    inbound_artifact_ref: str = Field(..., min_length=1)
    state_before: PairAgentRunState
    state_after: PairAgentRunState
    output_limit_bytes: int = Field(..., ge=256, le=20000)
    timeout_seconds: int = Field(..., ge=1, le=3600)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    raw_payload_persisted: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_turn_packet(self) -> "CodingPairAgentTurnPacketReadModel":
        for ref in [
            self.turn_packet_ref,
            self.sender_slot_ref,
            self.receiver_slot_ref,
            self.outbound_artifact_ref,
            self.inbound_artifact_ref,
            *self.proof_refs,
            *self.evidence_refs,
        ]:
            validate_task_ref(ref, "coding_pair_turn_packet_ref")
        for value in [self.state_before, self.state_after]:
            validate_safe_task_text(value, "coding_pair_turn_packet_text")
        if self.raw_payload_persisted:
            raise ValueError("pair turn packet cannot persist raw payload")
        return self


class CodingPairAgentArtifactReadModel(BaseModel):
    artifact_ref: str = Field(..., min_length=1)
    artifact_kind: PairAgentArtifactKind
    status: Literal["preview_ref", "blocked_ref"]
    safe_summary: str = Field(..., min_length=1, max_length=420)
    digest_ref: str = Field(..., min_length=1)
    bounded_preview_ref: str = Field(..., min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(default_factory=list)
    raw_content_omitted: bool = True
    raw_prompt_omitted: bool = True
    raw_response_omitted: bool = True
    provider_payload_omitted: bool = True
    raw_log_omitted: bool = True
    raw_local_path_omitted: bool = True
    durable_evidence: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_artifact(self) -> "CodingPairAgentArtifactReadModel":
        for ref in [
            self.artifact_ref,
            self.digest_ref,
            self.bounded_preview_ref,
            *self.evidence_refs,
            *self.proof_refs,
            *self.redactions_applied,
        ]:
            validate_task_ref(ref, "coding_pair_artifact_ref")
        for value in [self.artifact_kind, self.status, self.safe_summary]:
            validate_safe_task_text(value, "coding_pair_artifact_text")
        required_true = {
            "raw_content_omitted": self.raw_content_omitted,
            "raw_prompt_omitted": self.raw_prompt_omitted,
            "raw_response_omitted": self.raw_response_omitted,
            "provider_payload_omitted": self.provider_payload_omitted,
            "raw_log_omitted": self.raw_log_omitted,
            "raw_local_path_omitted": self.raw_local_path_omitted,
        }
        missing = [name for name, value in required_true.items() if not value]
        if missing:
            raise ValueError(f"coding pair artifact missing omission {missing[0]}")
        if self.durable_evidence:
            raise ValueError("raw pair artifacts cannot be durable evidence")
        return self


class CodingPairAgentReceiptReadModel(BaseModel):
    receipt_ref: str = Field(..., min_length=1)
    receipt_kind: PairAgentReceiptKind
    status: PairAgentReceiptStatus
    safe_summary: str = Field(..., min_length=1, max_length=420)
    canonical_json_ref: str = Field(..., min_length=1)
    digest_ref: str = Field(..., min_length=1)
    verifier_ref: str = Field(..., min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    raw_content_included: bool = False
    portable_receipt_ready: bool = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> "CodingPairAgentReceiptReadModel":
        for ref in [
            self.receipt_ref,
            self.canonical_json_ref,
            self.digest_ref,
            self.verifier_ref,
            *self.evidence_refs,
            *self.proof_refs,
            *self.blocked_authority_refs,
        ]:
            validate_task_ref(ref, "coding_pair_receipt_ref")
        for value in [self.receipt_kind, self.status, self.safe_summary]:
            validate_safe_task_text(value, "coding_pair_receipt_text")
        if self.raw_content_included:
            raise ValueError("coding pair receipt cannot include raw content")
        if not self.portable_receipt_ready:
            raise ValueError("coding pair receipt must retain portable posture")
        return self


class CodingPairAgentRunContractReadModel(BaseModel):
    run_ref: str = CODING_PAIR_AGENT_RELAY_RUN_REF
    task_ref: str = CODING_PAIR_AGENT_RELAY_TASK_REF
    state: PairAgentRunState
    allowed_state_refs: list[str] = Field(default_factory=list)
    state_transition_refs: list[str] = Field(default_factory=list)
    agent_slots: list[CodingPairAgentSlotReadModel] = Field(default_factory=list)
    workspace_scope_refs: list[str] = Field(default_factory=list)
    repo_scope_ref: str = Field(..., min_length=1)
    max_turns: int = Field(..., ge=1, le=12)
    wall_clock_timeout_seconds: int = Field(..., ge=30, le=3600)
    per_turn_output_limit_bytes: int = Field(..., ge=512, le=20000)
    stop_condition_refs: list[str] = Field(default_factory=list)
    approval_binding_refs: list[str] = Field(default_factory=list)
    idempotency_ref: str = Field(..., min_length=1)
    turn_packets: list[CodingPairAgentTurnPacketReadModel] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    background_dispatch_enabled: bool = False
    unbounded_turns_enabled: bool = False
    unbounded_timeout_enabled: bool = False
    unbounded_output_enabled: bool = False
    arbitrary_command_text_allowed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_run_contract(self) -> "CodingPairAgentRunContractReadModel":
        for ref in [
            self.run_ref,
            self.task_ref,
            self.repo_scope_ref,
            self.idempotency_ref,
            *self.allowed_state_refs,
            *self.state_transition_refs,
            *self.workspace_scope_refs,
            *self.stop_condition_refs,
            *self.approval_binding_refs,
            *self.receipt_refs,
            *self.evidence_refs,
            *self.proof_refs,
            *self.blocked_authority_refs,
        ]:
            validate_task_ref(ref, "coding_pair_run_contract_ref")
        validate_safe_task_text(self.state, "coding_pair_run_state")
        if len(self.agent_slots) != 2:
            raise ValueError("pair run requires exactly two agent slots")
        slot_ids = {slot.slot_id for slot in self.agent_slots}
        if slot_ids != {"agent_a", "agent_b"}:
            raise ValueError("pair run requires agent_a and agent_b slots")
        slot_refs = {slot.slot_ref for slot in self.agent_slots}
        if len(slot_refs) != len(self.agent_slots):
            raise ValueError("pair run slot refs must be unique")
        if not self.workspace_scope_refs:
            raise ValueError("pair run requires workspace scope refs")
        if not self.stop_condition_refs:
            raise ValueError("pair run requires stop condition refs")
        false_flags = {
            "background_dispatch_enabled": self.background_dispatch_enabled,
            "unbounded_turns_enabled": self.unbounded_turns_enabled,
            "unbounded_timeout_enabled": self.unbounded_timeout_enabled,
            "unbounded_output_enabled": self.unbounded_output_enabled,
            "arbitrary_command_text_allowed": self.arbitrary_command_text_allowed,
        }
        enabled = [name for name, value in false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding pair run enabled {enabled[0]}")
        return self


class CodingPairAgentRelayReadModel(BaseModel):
    schema_version: Literal["uaa-coding-pair-agent-relay-runner.v1"] = (
        CODING_PAIR_AGENT_RELAY_SCHEMA_VERSION
    )
    readiness_ref: str = CODING_PAIR_AGENT_RELAY_READINESS_REF
    lane_ref: str = CODING_PAIR_AGENT_RELAY_LANE_REF
    canonical_lane_name: Literal["coding_pair_agent_foreground_relay_runner"] = (
        "coding_pair_agent_foreground_relay_runner"
    )
    status: PairAgentRelayStatus = "preview_readiness_execution_blocked"
    backend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_PAIR_AGENT_RELAY_BACKEND_ROUTE_REF]
    )
    frontend_route_refs: list[str] = Field(default_factory=lambda: ["/coding"])
    cli_inspection_refs: list[str] = Field(
        default_factory=lambda: [
            CODING_PAIR_AGENT_RELAY_CLI_REF,
            "scripts/dev/uaa_coding.py preview-pair-run",
            "scripts/dev/uaa_coding.py inspect-pair-run",
            "scripts/dev/uaa_coding.py inspect-pair-artifacts",
            "scripts/dev/uaa_coding.py inspect-pair-receipts",
            "scripts/dev/uaa_coding.py start-pair-run-readiness",
            "scripts/dev/uaa_coding.py stop-pair-run-readiness",
        ]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            CODING_PAIR_AGENT_RELAY_DOC_REF,
            "docs-ref:coding-multi-agent-review-blocker",
            "docs-ref:operator-shell-gap-map",
        ]
    )
    verifier_refs: list[str] = Field(
        default_factory=lambda: [CODING_PAIR_AGENT_RELAY_VERIFIER_REF]
    )
    unblock_prompt_refs: list[str] = Field(
        default_factory=lambda: [CODING_PAIR_AGENT_RELAY_UNBLOCK_PROMPT_REF]
    )
    full_strength_goal: str = Field(..., min_length=1, max_length=640)
    repo_safe_current_state: str = Field(..., min_length=1, max_length=640)
    safe_summary: str = Field(..., min_length=1, max_length=640)
    run_contract: CodingPairAgentRunContractReadModel
    artifacts: list[CodingPairAgentArtifactReadModel] = Field(default_factory=list)
    receipts: list[CodingPairAgentReceiptReadModel] = Field(default_factory=list)
    artifact_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=520)
    backend_owned: bool = True
    preview_only: bool = True
    readiness_only: bool = True
    safe_refs_only: bool = True
    execution_promoted: bool = False
    foreground_adapter_execution_enabled: bool = False
    local_agent_process_execution_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    provider_model_call_enabled: bool = False
    background_dispatch_enabled: bool = False
    generic_agent_bus_enabled: bool = False
    arbitrary_command_text_allowed: bool = False
    shell_subprocess_execution_enabled: bool = False
    plugin_runtime_import_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    git_mutation_enabled: bool = False
    automatic_patch_apply_enabled: bool = False
    raw_transcript_durable: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    provider_payload_persisted: bool = False
    raw_log_persisted: bool = False
    raw_local_path_persisted: bool = False
    production_authority_enabled: bool = False
    broad_autonomy_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_relay(self) -> "CodingPairAgentRelayReadModel":
        for ref in [
            self.readiness_ref,
            self.lane_ref,
            *self.artifact_refs,
            *self.receipt_refs,
            *self.evidence_refs,
            *self.proof_refs,
            *self.blocked_authority_refs,
            *self.promotion_path_refs,
            *self.redactions_applied,
            *self.docs_refs,
            *self.verifier_refs,
            *self.unblock_prompt_refs,
        ]:
            validate_task_ref(ref, "coding_pair_relay_ref")
        for value in (
            self.backend_route_refs
            + self.frontend_route_refs
            + self.cli_inspection_refs
            + [
                self.canonical_lane_name,
                self.status,
                self.full_strength_goal,
                self.repo_safe_current_state,
                self.safe_summary,
                self.next_safe_action,
            ]
        ):
            validate_safe_task_text(value, "coding_pair_relay_text")
        artifact_refs = {artifact.artifact_ref for artifact in self.artifacts}
        if set(self.artifact_refs) != artifact_refs:
            raise ValueError("pair relay artifact refs must match artifacts")
        receipt_refs = {receipt.receipt_ref for receipt in self.receipts}
        if set(self.receipt_refs) != receipt_refs:
            raise ValueError("pair relay receipt refs must match receipts")
        if not set(CODING_PAIR_AGENT_RELAY_REQUIRED_BLOCKED_REFS).issubset(
            self.blocked_authority_refs
        ):
            raise ValueError("pair relay missing required blocked refs")
        required_true = {
            "backend_owned": self.backend_owned,
            "preview_only": self.preview_only,
            "readiness_only": self.readiness_only,
            "safe_refs_only": self.safe_refs_only,
        }
        missing = [name for name, value in required_true.items() if not value]
        if missing:
            raise ValueError(f"coding pair relay missing {missing[0]}")
        false_flags = {
            "execution_promoted": self.execution_promoted,
            "foreground_adapter_execution_enabled": (
                self.foreground_adapter_execution_enabled
            ),
            "local_agent_process_execution_enabled": (
                self.local_agent_process_execution_enabled
            ),
            "provider_sdk_call_enabled": self.provider_sdk_call_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "background_dispatch_enabled": self.background_dispatch_enabled,
            "generic_agent_bus_enabled": self.generic_agent_bus_enabled,
            "arbitrary_command_text_allowed": self.arbitrary_command_text_allowed,
            "shell_subprocess_execution_enabled": self.shell_subprocess_execution_enabled,
            "plugin_runtime_import_enabled": self.plugin_runtime_import_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "git_mutation_enabled": self.git_mutation_enabled,
            "automatic_patch_apply_enabled": self.automatic_patch_apply_enabled,
            "raw_transcript_durable": self.raw_transcript_durable,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
            "provider_payload_persisted": self.provider_payload_persisted,
            "raw_log_persisted": self.raw_log_persisted,
            "raw_local_path_persisted": self.raw_local_path_persisted,
            "production_authority_enabled": self.production_authority_enabled,
            "broad_autonomy_enabled": self.broad_autonomy_enabled,
        }
        enabled = [name for name, value in false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding pair relay enabled {enabled[0]}")
        payload = self.model_dump(mode="json")
        validate_safe_task_payload(payload, "coding_pair_agent_relay")
        return self


def build_coding_pair_agent_relay_read_model() -> CodingPairAgentRelayReadModel:
    proof_refs = ["proof-ref:coding-pair-agent-relay:preview"]
    evidence_refs = ["evidence-ref:coding-pair-agent-relay:preview"]
    slot_blockers = [
        "blocked-state:coding-pair-no-foreground-adapter-execution",
        "blocked-state:coding-pair-no-arbitrary-command-text",
        "blocked-state:coding-pair-no-shell-subprocess",
        "blocked-state:coding-pair-no-background-dispatch",
    ]
    slots = [
        CodingPairAgentSlotReadModel(
            slot_ref="agent-slot-ref:coding-pair:agent-a",
            slot_id="agent_a",
            adapter_ref="adapter-ref:coding-pair:agent-a-configured-foreground",
            display_label="Agent A implementer slot",
            status="blocked_execution",
            argv_template_refs=["argv-template-ref:coding-pair:agent-a"],
            allowed_workspace_refs=["workspace-scope-ref:coding-pair:local-uaa"],
            allowed_mode_refs=["mode-ref:coding-pair:foreground-only"],
            max_runtime_seconds=300,
            max_output_bytes=12000,
            env_policy_ref="env-policy-ref:coding-pair:scrubbed-minimal",
            disabled_reason_ref=(
                "disabled-reason-ref:coding-pair:foreground-adapter-not-promoted"
            ),
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=slot_blockers,
        ),
        CodingPairAgentSlotReadModel(
            slot_ref="agent-slot-ref:coding-pair:agent-b",
            slot_id="agent_b",
            adapter_ref="adapter-ref:coding-pair:agent-b-configured-foreground",
            display_label="Agent B reviewer slot",
            status="blocked_execution",
            argv_template_refs=["argv-template-ref:coding-pair:agent-b"],
            allowed_workspace_refs=["workspace-scope-ref:coding-pair:local-uaa"],
            allowed_mode_refs=["mode-ref:coding-pair:foreground-only"],
            max_runtime_seconds=300,
            max_output_bytes=12000,
            env_policy_ref="env-policy-ref:coding-pair:scrubbed-minimal",
            disabled_reason_ref=(
                "disabled-reason-ref:coding-pair:foreground-adapter-not-promoted"
            ),
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=slot_blockers,
        ),
    ]
    artifacts = _pair_agent_artifacts(evidence_refs=evidence_refs, proof_refs=proof_refs)
    receipts = _pair_agent_receipts(evidence_refs=evidence_refs, proof_refs=proof_refs)
    artifact_refs = [artifact.artifact_ref for artifact in artifacts]
    receipt_refs = [receipt.receipt_ref for receipt in receipts]
    run_contract = CodingPairAgentRunContractReadModel(
        state="blocked",
        allowed_state_refs=[
            f"pair-run-state-ref:{state}"
            for state in ALLOWED_PAIR_AGENT_RELAY_TRANSITIONS
        ],
        state_transition_refs=[
            "state-transition-ref:coding-pair:created-to-pending-approval",
            "state-transition-ref:coding-pair:approved-to-agent-a-running",
            "state-transition-ref:coding-pair:waiting-agent-b-to-completed",
            "state-transition-ref:coding-pair:any-active-to-blocked",
        ],
        agent_slots=slots,
        workspace_scope_refs=["workspace-scope-ref:coding-pair:local-uaa"],
        repo_scope_ref="repo-scope-ref:coding-pair:local-uaa",
        max_turns=6,
        wall_clock_timeout_seconds=900,
        per_turn_output_limit_bytes=12000,
        stop_condition_refs=[
            "stop-condition-ref:coding-pair:max-turns",
            "stop-condition-ref:coding-pair:timeout",
            "stop-condition-ref:coding-pair:sentinel-complete",
            "stop-condition-ref:coding-pair:user-stop",
            "stop-condition-ref:coding-pair:policy-block",
            "stop-condition-ref:coding-pair:approval-required",
            "stop-condition-ref:coding-pair:adapter-failure",
            "stop-condition-ref:coding-pair:output-too-large",
            "stop-condition-ref:coding-pair:unsafe-output",
            "stop-condition-ref:coding-pair:scope-expansion",
        ],
        approval_binding_refs=[
            "approval-binding-ref:coding-pair:run-scope",
            "approval-binding-ref:coding-pair:agent-slots",
            "approval-binding-ref:coding-pair:turn-budget",
            "approval-binding-ref:coding-pair:timeout",
            "approval-binding-ref:coding-pair:policy-decision",
        ],
        idempotency_ref="idempotency-ref:coding-pair:preview-run",
        turn_packets=[
            CodingPairAgentTurnPacketReadModel(
                turn_packet_ref="turn-packet-ref:coding-pair:agent-a-to-agent-b",
                turn_index=0,
                sender_slot_ref="agent-slot-ref:coding-pair:agent-a",
                receiver_slot_ref="agent-slot-ref:coding-pair:agent-b",
                outbound_artifact_ref="artifact-ref:coding-pair:outbound-turn-packet",
                inbound_artifact_ref="artifact-ref:coding-pair:inbound-agent-response",
                state_before="created",
                state_after="blocked",
                output_limit_bytes=12000,
                timeout_seconds=300,
                proof_refs=proof_refs,
                evidence_refs=evidence_refs,
            )
        ],
        receipt_refs=receipt_refs,
        evidence_refs=evidence_refs,
        proof_refs=proof_refs,
        blocked_authority_refs=CODING_PAIR_AGENT_RELAY_REQUIRED_BLOCKED_REFS,
    )
    return CodingPairAgentRelayReadModel(
        full_strength_goal=(
            "Run two exact configured coding agents in a foreground relay with "
            "bounded turns, operator stop controls, approval binding, redacted "
            "receipts, evidence refs, and reviewable proposal artifacts."
        ),
        repo_safe_current_state=(
            "UAA exposes the pair-run contract, state machine, adapter registry "
            "posture, receipt refs, artifact refs, and unblock prompt. "
            "Foreground adapter launch remains blocked until an AuthorityLease-"
            "gated capability is implemented, approved, and proven."
        ),
        safe_summary=(
            "Pair Agents is preview/readiness only. Agent output would be "
            "untrusted proposal text, never authority."
        ),
        run_contract=run_contract,
        artifacts=artifacts,
        receipts=receipts,
        artifact_refs=artifact_refs,
        receipt_refs=receipt_refs,
        evidence_refs=evidence_refs,
        proof_refs=proof_refs,
        blocked_authority_refs=CODING_PAIR_AGENT_RELAY_REQUIRED_BLOCKED_REFS,
        promotion_path_refs=[
            "promotion-path:coding-pair:adapter-registry",
            "promotion-path:coding-pair:approval-binding",
            "promotion-path:coding-pair:foreground-runner",
            "promotion-path:coding-pair:redacted-receipts",
            "promotion-path:coding-pair:cli-api-ui-parity",
        ],
        redactions_applied=[
            "redaction-ref:safe-refs-only",
            "redaction-ref:raw-prompts-omitted",
            "redaction-ref:raw-responses-omitted",
            "redaction-ref:provider-payloads-omitted",
            "redaction-ref:raw-logs-omitted",
            "redaction-ref:raw-local-paths-omitted",
        ],
        next_safe_action=(
            "Run the unblock prompt only after configured foreground adapters, "
            "exact approval binding, output limits, idempotency, safe-disable, "
            "redacted receipts, CLI/API/UI parity, and focused tests are in scope."
        ),
    )


def _pair_agent_artifacts(
    *, evidence_refs: list[str], proof_refs: list[str]
) -> list[CodingPairAgentArtifactReadModel]:
    labels: list[tuple[PairAgentArtifactKind, str]] = [
        ("outbound_turn_packet", "Bounded outbound turn packet ref only."),
        ("inbound_agent_response", "Bounded inbound response ref only."),
        ("disagreement_summary", "Reviewable disagreement summary ref."),
        ("candidate_action_list", "Candidate action list ref, not authority."),
        ("validation_plan", "Validation plan ref, not command authority."),
        ("final_synthesis", "Final synthesis ref for operator review."),
        ("blocked_state_report", "Blocked-state report ref for next lane."),
    ]
    return [
        CodingPairAgentArtifactReadModel(
            artifact_ref=f"artifact-ref:coding-pair:{kind.replace('_', '-')}",
            artifact_kind=kind,
            status="preview_ref" if kind != "blocked_state_report" else "blocked_ref",
            safe_summary=summary,
            digest_ref=f"digest-ref:coding-pair:{kind.replace('_', '-')}",
            bounded_preview_ref=f"bounded-preview-ref:coding-pair:{kind.replace('_', '-')}",
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            redactions_applied=[
                "redaction-ref:safe-refs-only",
                "redaction-ref:raw-content-omitted",
            ],
        )
        for kind, summary in labels
    ]


def _pair_agent_receipts(
    *, evidence_refs: list[str], proof_refs: list[str]
) -> list[CodingPairAgentReceiptReadModel]:
    labels: list[tuple[PairAgentReceiptKind, PairAgentReceiptStatus, str]] = [
        ("run_created", "preview_ref", "Run-created receipt ref shape."),
        ("approval_bound", "planned_ref", "Approval-bound receipt ref shape."),
        ("adapter_started", "blocked_ref", "Adapter-start receipt remains blocked."),
        ("turn_completed", "planned_ref", "Turn-completed receipt ref shape."),
        ("output_redacted", "planned_ref", "Output-redacted receipt ref shape."),
        ("stop_condition_reached", "planned_ref", "Stop-condition receipt ref shape."),
        ("run_completed", "planned_ref", "Run-completed receipt ref shape."),
        ("run_blocked", "blocked_ref", "Run-blocked receipt ref shape."),
        ("run_failed", "planned_ref", "Run-failed receipt ref shape."),
    ]
    return [
        CodingPairAgentReceiptReadModel(
            receipt_ref=f"receipt-ref:coding-pair:{kind.replace('_', '-')}",
            receipt_kind=kind,
            status=status,
            safe_summary=summary,
            canonical_json_ref=f"canonical-json-ref:coding-pair:{kind.replace('_', '-')}",
            digest_ref=f"digest-ref:coding-pair:receipt:{kind.replace('_', '-')}",
            verifier_ref=CODING_PAIR_AGENT_RELAY_VERIFIER_REF,
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=CODING_PAIR_AGENT_RELAY_REQUIRED_BLOCKED_REFS
            if status == "blocked_ref"
            else [],
        )
        for kind, status, summary in labels
    ]
