from __future__ import annotations

import hashlib
import json
from datetime import datetime
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
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    GOVERNED_RUNTIME_REDACTIONS,
    GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
)
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)
from ultimate_ai_agent.core.runtime_gateway.goal_runtime import (
    DurableCriterionVerifierBinding,
    DurableRunEvent,
    GoalLifecycleReadModel,
    GoalMutationSubmissionRecoveryReadModel,
    GoalRuntimeService,
    RunEventReplayReadModel,
    RunEventStreamSummary,
)


RUNTIME_RUN_EVENTS_CONTRACT_REF = "contract-ref:runtime-run-events:v1"
RUNTIME_RUN_EVENTS_ROUTE_REF = "GET /api/runtime/run-events"
RUNTIME_RUN_EVENTS_CLI_REF = "uaa runtime inspect-run-events"
RUNTIME_RUN_EVENTS_SAMPLE_RUN_REF = (
    "runtime-run-ref:hermes-agent:proposal:approval-wait-sample"
)
RUNTIME_RUN_EVENTS_SAMPLE_DURABLE_RUN_REF = (
    "durable-run-ref:runtime-delegation:approval-wait-sample"
)
RUNTIME_RUN_EVENTS_SNAPSHOT_REF = (
    "runtime-run-events-snapshot-ref:hermes-agent:proposal-read-model"
)
RUNTIME_RUN_EVENTS_AUTHORITY_STATE_ROUTE_REF = "GET /api/runtime/authority-state"
RUNTIME_RUN_EVENTS_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_RUN_EVENTS_AUTHORITY_MAPPING_REF = "lane-ref:runtime-run-events-read-model"
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}


class RuntimeExternalRunLifecycleState(str, Enum):
    proposed = "proposed"
    approval_wait = "approval_wait"
    queued = "queued"
    running = "running"
    stopping = "stopping"
    cancelled = "cancelled"
    failed = "failed"
    completed = "completed"
    blocked = "blocked"
    unknown_stale = "unknown_stale"


class RuntimeUaaDurableRunState(str, Enum):
    proposed = "proposed"
    approval_wait = "approval_wait"
    queued = "queued"
    running = "running"
    cancellation_requested = "cancellation_requested"
    cancelled = "cancelled"
    failed = "failed"
    completed = "completed"
    blocked = "blocked"
    stale_unknown = "stale_unknown"


class RuntimeRunControlPosture(str, Enum):
    read_model_only = "read_model_only"
    blocked = "blocked"
    approval_required_future_lane = "approval_required_future_lane"


class RuntimeRunEventKind(str, Enum):
    run_proposed = "run_proposed"
    approval_wait_entered = "approval_wait_entered"
    event_stream_preview = "event_stream_preview"
    stop_requested_preview = "stop_requested_preview"
    proof_bound = "proof_bound"
    goal_linked = "goal_linked"
    plan_linked = "plan_linked"
    run_started = "run_started"
    approval_resumed = "approval_resumed"
    worker_restart_recovered = "worker_restart_recovered"
    allowed_local_action_recorded = "allowed_local_action_recorded"
    receipt_recorded = "receipt_recorded"
    evidence_linked = "evidence_linked"
    completion_verified = "completion_verified"
    cancellation_requested = "cancellation_requested"
    cancelled = "cancelled"
    failed_retryable = "failed_retryable"
    failed_terminal = "failed_terminal"
    dead_lettered = "dead_lettered"


class RuntimeRunLifecycleMapping(BaseModel):
    runtime_state: RuntimeExternalRunLifecycleState
    uaa_durable_run_state: RuntimeUaaDurableRunState
    operator_label: str
    safe_summary: str
    receipt_required_before_claim: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_mapping(self) -> "RuntimeRunLifecycleMapping":
        validate_safe_execution_text(self.operator_label, "operator_label")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if not self.receipt_required_before_claim:
            raise ValueError("RUNTIME_RUN_EVENT_RECEIPT_REQUIRED_BEFORE_CLAIM")
        return self


class RuntimeRunEventRefGrammar(BaseModel):
    grammar_ref: str = "event-grammar-ref:runtime-run-events:v1"
    event_ref_prefix: str = "runtime-run-event-ref:"
    required_bindings: list[str] = Field(
        default_factory=lambda: [
            "runtime_run_ref",
            "uaa_durable_run_ref",
            "proof_ref",
            "redaction_status",
        ]
    )
    safe_summary: str = (
        "Runtime event refs bind a delegated runtime run to a UAA durable run, "
        "proof ref, and redaction status without storing runtime payloads."
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_grammar(self) -> "RuntimeRunEventRefGrammar":
        validate_execution_ref(self.grammar_ref, "grammar_ref")
        validate_safe_execution_text(self.event_ref_prefix, "event_ref_prefix")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        for binding in self.required_bindings:
            validate_safe_execution_text(binding, "required_bindings")
        return self


class RuntimeRunEventPreview(BaseModel):
    event_ref: str
    event_kind: RuntimeRunEventKind
    runtime_run_ref: str
    uaa_durable_run_ref: str
    proof_ref: str
    redaction_status: str = "redacted_safe_ref_only"
    safe_summary: str
    sequence: int | None = Field(default=None, ge=1)
    recorded_at: datetime | None = None
    predecessor_hash_ref: str | None = None
    event_hash_ref: str | None = None
    proof_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    criterion_verifier_bindings: list[DurableCriterionVerifierBinding] = Field(
        default_factory=list,
        max_length=32,
    )
    goal_ref: str | None = None
    plan_ref: str | None = None
    runtime_payload_persisted: bool = False
    raw_log_persisted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_event(self) -> "RuntimeRunEventPreview":
        for value, field_name in [
            (self.event_ref, "event_ref"),
            (self.runtime_run_ref, "runtime_run_ref"),
            (self.uaa_durable_run_ref, "uaa_durable_run_ref"),
            (self.proof_ref, "proof_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.predecessor_hash_ref, "predecessor_hash_ref"),
            (self.event_hash_ref, "event_hash_ref"),
            (self.goal_ref, "goal_ref"),
            (self.plan_ref, "plan_ref"),
        ]:
            if value is not None:
                validate_execution_ref(value, field_name)
        for field_name in ("proof_refs", "receipt_refs"):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        validate_safe_execution_text(self.redaction_status, "redaction_status")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if any(
            (
                self.runtime_payload_persisted,
                self.raw_log_persisted,
                self.raw_prompt_persisted,
                self.raw_response_persisted,
            )
        ):
            raise ValueError("RUNTIME_RUN_EVENT_RAW_PERSISTENCE_DENIED")
        return self


class RuntimeRunProposalReadModel(BaseModel):
    proposal_ref: str
    runtime_run_ref: str
    uaa_durable_run_ref: str
    runtime_state: RuntimeExternalRunLifecycleState
    uaa_durable_run_state: RuntimeUaaDurableRunState
    create_posture: RuntimeRunControlPosture = RuntimeRunControlPosture.blocked
    stop_posture: RuntimeRunControlPosture = RuntimeRunControlPosture.blocked
    approval_resolution_posture: RuntimeRunControlPosture = (
        RuntimeRunControlPosture.approval_required_future_lane
    )
    event_stream_posture: RuntimeRunControlPosture = (
        RuntimeRunControlPosture.read_model_only
    )
    create_run_enabled: bool = False
    stop_run_enabled: bool = False
    approval_resolution_enabled: bool = False
    live_event_stream_enabled: bool = False
    retry_recovery_enabled: bool = False
    cancellation_proof_required: bool = True
    event_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    safe_summary: str

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_proposal(self) -> "RuntimeRunProposalReadModel":
        for value, field_name in [
            (self.proposal_ref, "proposal_ref"),
            (self.runtime_run_ref, "runtime_run_ref"),
            (self.uaa_durable_run_ref, "uaa_durable_run_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "event_refs",
            "proof_refs",
            "receipt_refs",
            "blocked_authority_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.uaa_durable_run_state == RuntimeUaaDurableRunState.completed.value:
            raise ValueError("RUNTIME_RUN_EVENT_FAKE_COMPLETION_DENIED")
        denied_flags = {
            "create_run_enabled": self.create_run_enabled,
            "stop_run_enabled": self.stop_run_enabled,
            "approval_resolution_enabled": self.approval_resolution_enabled,
            "live_event_stream_enabled": self.live_event_stream_enabled,
            "retry_recovery_enabled": self.retry_recovery_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_RUN_EVENT_MUTATION_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        if not self.cancellation_proof_required:
            raise ValueError("RUNTIME_RUN_EVENT_CANCELLATION_PROOF_REQUIRED")
        return self


class RuntimeRunEventsReadModel(BaseModel):
    schema_version: str = "runtime_run_events.v1"
    contract_ref: str = RUNTIME_RUN_EVENTS_CONTRACT_REF
    snapshot_ref: str = RUNTIME_RUN_EVENTS_SNAPSHOT_REF
    snapshot_hash_ref: str
    route_ref: str = RUNTIME_RUN_EVENTS_ROUTE_REF
    cli_ref: str = RUNTIME_RUN_EVENTS_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    runtime_identity_ref: str = "runtime-identity-ref:hermes-agent:optional-target"
    adapter_ref: str = "runtime-delegation-adapter:hermes-agent"
    status: str = "durable_local_replay"
    authority_state_route_ref: str
    authority_state_cli_ref: str
    authority_state_mapping_ref: str
    authority_state_catalog_ref: str
    authority_state_decision_ref: str
    authority_state_decision_outcome: str
    authority_state_status: str
    authority_state_operator_message: str
    authority_state_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    lifecycle_mappings: list[RuntimeRunLifecycleMapping]
    event_ref_grammar: RuntimeRunEventRefGrammar = Field(
        default_factory=RuntimeRunEventRefGrammar
    )
    run_proposals: list[RuntimeRunProposalReadModel]
    event_previews: list[RuntimeRunEventPreview]
    goal_lifecycle: GoalLifecycleReadModel
    goal_mutation_submissions: GoalMutationSubmissionRecoveryReadModel
    stream_summaries: list[RunEventStreamSummary] = Field(default_factory=list)
    replay: RunEventReplayReadModel | None = None
    stream_count: int = 0
    retained_event_count: int = 0
    durable_event_source: bool = True
    cursor_replay_supported: bool = True
    bounded_retention_enabled: bool = True
    proposal_count: int
    approval_wait_count: int
    completed_run_count: int = 0
    create_run_route_enabled: bool = False
    stop_run_route_enabled: bool = False
    approval_resolution_route_enabled: bool = False
    live_event_stream_enabled: bool = False
    uaa_controls_authority: bool = True
    control_center_talks_directly_to_runtime: bool = False
    no_runtime_control_routes_registered: bool = True
    safe_refs_only: bool = True
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    raw_provider_payload_persisted: bool = False
    raw_runtime_payload_persisted: bool = False
    raw_log_persisted: bool = False
    raw_local_path_persisted: bool = False
    credential_material_persisted: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "Proof-backed goals and accepted local run events are persisted in "
        "bounded hash-chained journals with cursor replay; live transport and "
        "external runtime control remain blocked."
    )
    redactions_applied: list[str] = Field(
        default_factory=lambda: (
            list(GOVERNED_RUNTIME_REDACTIONS) + ["runtime_event_payload_omitted"]
        )
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeRunEventsReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.runtime_identity_ref, "runtime_identity_ref"),
            (self.adapter_ref, "adapter_ref"),
            (self.authority_state_mapping_ref, "authority_state_mapping_ref"),
            (self.authority_state_catalog_ref, "authority_state_catalog_ref"),
            (self.authority_state_decision_ref, "authority_state_decision_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.status, "status"),
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
            "proof_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        if self.authority_state_mapping_ref != RUNTIME_RUN_EVENTS_AUTHORITY_MAPPING_REF:
            raise ValueError("RUNTIME_RUN_EVENT_AUTHORITY_MAPPING_MISMATCH")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_RUN_EVENT_AUTHORITY_DECISION_INVALID")
        if self.proposal_count != len(self.run_proposals):
            raise ValueError("RUNTIME_RUN_EVENT_PROPOSAL_COUNT_DRIFT")
        expected_approval_wait = sum(
            1
            for event in self.event_previews
            if event.event_kind == RuntimeRunEventKind.approval_wait_entered.value
        )
        if self.approval_wait_count != expected_approval_wait:
            raise ValueError("RUNTIME_RUN_EVENT_APPROVAL_WAIT_COUNT_DRIFT")
        expected_completed = sum(
            stream.successful_receipt_recorded
            or stream.terminal_event_kind
            == RuntimeRunEventKind.completion_verified.value
            for stream in self.stream_summaries
        )
        if self.completed_run_count != expected_completed:
            raise ValueError("RUNTIME_RUN_EVENT_COMPLETION_COUNT_DRIFT")
        if self.stream_count != len(self.stream_summaries):
            raise ValueError("RUNTIME_RUN_EVENT_STREAM_COUNT_DRIFT")
        if self.retained_event_count != sum(
            stream.retained_event_count for stream in self.stream_summaries
        ):
            raise ValueError("RUNTIME_RUN_EVENT_RETAINED_COUNT_DRIFT")
        denied_flags = {
            "create_run_route_enabled": self.create_run_route_enabled,
            "stop_run_route_enabled": self.stop_run_route_enabled,
            "approval_resolution_route_enabled": self.approval_resolution_route_enabled,
            "live_event_stream_enabled": self.live_event_stream_enabled,
            "control_center_talks_directly_to_runtime": (
                self.control_center_talks_directly_to_runtime
            ),
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
            "raw_provider_payload_persisted": self.raw_provider_payload_persisted,
            "raw_runtime_payload_persisted": self.raw_runtime_payload_persisted,
            "raw_log_persisted": self.raw_log_persisted,
            "raw_local_path_persisted": self.raw_local_path_persisted,
            "credential_material_persisted": self.credential_material_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_RUN_EVENT_UNSAFE_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        if not self.uaa_controls_authority:
            raise ValueError("RUNTIME_RUN_EVENT_UAA_AUTHORITY_REQUIRED")
        if not self.no_runtime_control_routes_registered:
            raise ValueError("RUNTIME_RUN_EVENT_CONTROL_ROUTE_DENIED")
        if not self.safe_refs_only:
            raise ValueError("RUNTIME_RUN_EVENT_SAFE_REFS_REQUIRED")
        if not (
            self.durable_event_source
            and self.cursor_replay_supported
            and self.bounded_retention_enabled
        ):
            raise ValueError("RUNTIME_RUN_EVENT_DURABILITY_REQUIRED")
        return self


def _mapping(
    runtime_state: RuntimeExternalRunLifecycleState,
    uaa_state: RuntimeUaaDurableRunState,
    label: str,
    summary: str,
) -> RuntimeRunLifecycleMapping:
    return RuntimeRunLifecycleMapping(
        runtime_state=runtime_state,
        uaa_durable_run_state=uaa_state,
        operator_label=label,
        safe_summary=summary,
    )


def build_runtime_run_events_read_model(
    *,
    service: GoalRuntimeService | None = None,
    run_ref: str | None = None,
    after_sequence: int = 0,
    limit: int = 100,
) -> RuntimeRunEventsReadModel:
    authority_entry = _authority_entry(authority_decision_catalog=None)
    return build_runtime_run_events_read_model_from_authority_catalog(
        authority_decision_catalog=[authority_entry],
        service=service,
        run_ref=run_ref,
        after_sequence=after_sequence,
        limit=limit,
    )


def build_runtime_run_events_read_model_from_authority_catalog(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None = None,
    *,
    service: GoalRuntimeService | None = None,
    run_ref: str | None = None,
    after_sequence: int = 0,
    limit: int = 100,
) -> RuntimeRunEventsReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    runtime_service = service or GoalRuntimeService.from_env()
    (
        replay,
        durable_events,
        stream_summaries,
        goal_lifecycle,
        goal_mutation_submissions,
    ) = runtime_service.aggregate_read_snapshot(
        run_ref=run_ref,
        after_sequence=after_sequence,
        limit=limit,
    )
    events = [_durable_event_preview(event) for event in durable_events]
    mappings = [
        _mapping(
            RuntimeExternalRunLifecycleState.proposed,
            RuntimeUaaDurableRunState.proposed,
            "Proposed",
            "Runtime proposal is not submitted until exact approval and idempotency exist.",
        ),
        _mapping(
            RuntimeExternalRunLifecycleState.approval_wait,
            RuntimeUaaDurableRunState.approval_wait,
            "Approval wait",
            "Runtime wait state maps to a UAA durable approval wait without resolving it.",
        ),
        _mapping(
            RuntimeExternalRunLifecycleState.queued,
            RuntimeUaaDurableRunState.queued,
            "Queued",
            "Queued delegated work requires a receipt before UAA can claim it.",
        ),
        _mapping(
            RuntimeExternalRunLifecycleState.running,
            RuntimeUaaDurableRunState.running,
            "Running",
            "Running delegated work requires redacted event receipts before display.",
        ),
        _mapping(
            RuntimeExternalRunLifecycleState.stopping,
            RuntimeUaaDurableRunState.cancellation_requested,
            "Cancellation requested",
            "Stop posture requires cancellation proof before UAA can display a stopped result.",
        ),
        _mapping(
            RuntimeExternalRunLifecycleState.cancelled,
            RuntimeUaaDurableRunState.cancelled,
            "Cancelled",
            "Cancelled state requires cancellation receipt proof.",
        ),
        _mapping(
            RuntimeExternalRunLifecycleState.failed,
            RuntimeUaaDurableRunState.failed,
            "Failed",
            "Failed state requires redacted error refs and proof refs.",
        ),
        _mapping(
            RuntimeExternalRunLifecycleState.completed,
            RuntimeUaaDurableRunState.completed,
            "Completed",
            "Completed state cannot be claimed without run receipt and proof binding.",
        ),
        _mapping(
            RuntimeExternalRunLifecycleState.blocked,
            RuntimeUaaDurableRunState.blocked,
            "Blocked",
            "Blocked runtime state remains visible as proof-bound metadata.",
        ),
        _mapping(
            RuntimeExternalRunLifecycleState.unknown_stale,
            RuntimeUaaDurableRunState.stale_unknown,
            "Unknown stale",
            "Stale or unreachable runtime state degrades to blocked inspection.",
        ),
    ]
    return RuntimeRunEventsReadModel(
        snapshot_hash_ref=_snapshot_hash_ref(
            lifecycle_mappings=mappings,
            run_proposals=[],
            event_previews=events,
            authority_entry=authority_entry,
            goal_lifecycle=goal_lifecycle,
            goal_mutation_submissions=goal_mutation_submissions,
            stream_summaries=stream_summaries,
            replay=replay,
        ),
        authority_state_route_ref=RUNTIME_RUN_EVENTS_AUTHORITY_STATE_ROUTE_REF,
        authority_state_cli_ref=RUNTIME_RUN_EVENTS_AUTHORITY_STATE_CLI_REF,
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
        lifecycle_mappings=mappings,
        run_proposals=[],
        event_previews=events,
        goal_lifecycle=goal_lifecycle,
        goal_mutation_submissions=goal_mutation_submissions,
        stream_summaries=stream_summaries,
        replay=replay,
        stream_count=len(stream_summaries),
        retained_event_count=sum(
            stream.retained_event_count for stream in stream_summaries
        ),
        proposal_count=0,
        approval_wait_count=sum(
            event.event_kind == RuntimeRunEventKind.approval_wait_entered.value
            for event in events
        ),
        completed_run_count=sum(
            stream.successful_receipt_recorded
            or stream.terminal_event_kind
            == RuntimeRunEventKind.completion_verified.value
            for stream in stream_summaries
        ),
        blocked_authority_refs=[
            *GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
            "blocked-authority:runtime-run-create-route",
            "blocked-authority:runtime-run-stop-execution",
            "blocked-authority:runtime-run-approval-resolution",
            "blocked-authority:runtime-run-live-event-stream",
        ],
        proof_refs=[
            "proof-ref:runtime-run-events:lifecycle-mapping",
            "proof-ref:runtime-run-events:event-ref-grammar",
            "proof-ref:runtime-run-events:durable-hash-chain",
            "proof-ref:runtime-run-events:bounded-cursor-replay",
            "proof-ref:runtime-run-events:no-runtime-control-routes",
        ],
        next_safe_action_refs=[
            "next-safe-action-ref:runtime-run-events:inspect-durable-replay",
            "next-safe-action-ref:runtime-run-events:verify-goal-receipt-binding",
            "next-safe-action-ref:runtime-run-events:keep-live-transport-blocked",
        ],
    )


def _snapshot_hash_ref(
    *,
    lifecycle_mappings: list[RuntimeRunLifecycleMapping],
    run_proposals: list[RuntimeRunProposalReadModel],
    event_previews: list[RuntimeRunEventPreview],
    authority_entry: AuthorityDecisionCatalogEntry,
    goal_lifecycle: GoalLifecycleReadModel,
    goal_mutation_submissions: GoalMutationSubmissionRecoveryReadModel,
    stream_summaries: list[RunEventStreamSummary],
    replay: RunEventReplayReadModel | None,
) -> str:
    payload = {
        "contract_ref": RUNTIME_RUN_EVENTS_CONTRACT_REF,
        "snapshot_ref": RUNTIME_RUN_EVENTS_SNAPSHOT_REF,
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
        "lifecycle_mappings": [
            mapping.model_dump(mode="json") for mapping in lifecycle_mappings
        ],
        "run_proposals": [
            proposal.model_dump(mode="json") for proposal in run_proposals
        ],
        "event_previews": [event.model_dump(mode="json") for event in event_previews],
        "goal_lifecycle": goal_lifecycle.model_dump(mode="json"),
        "goal_mutation_submissions": goal_mutation_submissions.model_dump(mode="json"),
        "stream_summaries": [
            summary.model_dump(mode="json") for summary in stream_summaries
        ],
        "replay": replay.model_dump(mode="json") if replay is not None else None,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return f"snapshot-hash-ref:runtime-run-events:{digest[:16]}"


def _durable_event_preview(event: DurableRunEvent) -> RuntimeRunEventPreview:
    proof_ref = (
        event.proof_refs[0]
        if event.proof_refs
        else "proof-ref:runtime-run-events:redacted-event-presence"
    )
    return RuntimeRunEventPreview(
        event_ref=event.event_ref,
        event_kind=event.event_kind,
        runtime_run_ref=event.run_ref,
        uaa_durable_run_ref=event.run_ref,
        proof_ref=proof_ref,
        safe_summary=event.safe_summary,
        sequence=event.sequence,
        recorded_at=event.recorded_at,
        predecessor_hash_ref=event.predecessor_hash_ref,
        event_hash_ref=event.event_hash_ref,
        proof_refs=event.proof_refs,
        receipt_refs=event.receipt_refs,
        criterion_verifier_bindings=event.criterion_verifier_bindings,
        goal_ref=event.goal_ref,
        plan_ref=event.plan_ref,
    )


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None,
) -> AuthorityDecisionCatalogEntry:
    catalog = authority_decision_catalog or build_authority_decision_catalog()
    for entry in catalog:
        if entry.lane_ref == RUNTIME_RUN_EVENTS_AUTHORITY_MAPPING_REF:
            return entry
    raise ValueError("RUNTIME_RUN_EVENT_AUTHORITY_MAPPING_MISSING")


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))
