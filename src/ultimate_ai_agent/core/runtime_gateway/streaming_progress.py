from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
from ultimate_ai_agent.core.runtime_gateway.run_events import (
    RUNTIME_RUN_EVENTS_SAMPLE_DURABLE_RUN_REF,
    RUNTIME_RUN_EVENTS_SAMPLE_RUN_REF,
)


RUNTIME_STREAMING_PROGRESS_CONTRACT_REF = (
    "contract-ref:runtime-streaming-progress:v1"
)
RUNTIME_STREAMING_PROGRESS_ROUTE_REF = "GET /api/runtime/streaming-progress"
RUNTIME_STREAMING_PROGRESS_CLI_REF = "uaa runtime inspect-streaming-progress"
RUNTIME_STREAMING_PROGRESS_PROOF_REF = (
    "proof-ref:runtime-streaming-progress:phase-05"
)


class RuntimeStreamingProgressEventKind(str, Enum):
    token = "token"
    tool_started = "tool_started"
    tool_completed = "tool_completed"
    warning = "warning"
    approval_wait = "approval_wait"
    stopped = "stopped"
    failed = "failed"
    completed = "completed"


class RuntimeStreamingProgressStreamState(str, Enum):
    fixture_preview = "fixture_preview"
    locally_stored_preview = "locally_stored_preview"
    stale_disconnected = "stale_disconnected"
    live_transport_blocked = "live_transport_blocked"


class RuntimeStreamingProgressEventPreview(BaseModel):
    event_ref: str
    sequence: int
    event_kind: RuntimeStreamingProgressEventKind
    runtime_run_ref: str
    uaa_durable_run_ref: str
    tool_call_ref: str | None = None
    proof_ref: str
    event_hash_ref: str
    redaction_status: str = "redacted_summary_only"
    preview_limit_bytes: int = 512
    safe_summary: str
    runtime_payload_persisted: bool = False
    raw_tool_payload_persisted: bool = False
    raw_token_persisted: bool = False
    raw_log_persisted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_event_preview(self) -> "RuntimeStreamingProgressEventPreview":
        for value, field_name in [
            (self.event_ref, "event_ref"),
            (self.runtime_run_ref, "runtime_run_ref"),
            (self.uaa_durable_run_ref, "uaa_durable_run_ref"),
            (self.proof_ref, "proof_ref"),
            (self.event_hash_ref, "event_hash_ref"),
        ]:
            validate_execution_ref(value, field_name)
        if self.tool_call_ref is not None:
            validate_execution_ref(self.tool_call_ref, "tool_call_ref")
        if self.sequence < 0:
            raise ValueError("RUNTIME_STREAMING_PROGRESS_SEQUENCE_INVALID")
        if self.preview_limit_bytes <= 0 or self.preview_limit_bytes > 2048:
            raise ValueError("RUNTIME_STREAMING_PROGRESS_PREVIEW_LIMIT_INVALID")
        validate_safe_execution_text(self.redaction_status, "redaction_status")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        denied_flags = {
            "runtime_payload_persisted": self.runtime_payload_persisted,
            "raw_tool_payload_persisted": self.raw_tool_payload_persisted,
            "raw_token_persisted": self.raw_token_persisted,
            "raw_log_persisted": self.raw_log_persisted,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_STREAMING_PROGRESS_RAW_PERSISTENCE_DENIED: "
                + ", ".join(enabled)
            )
        return self


class RuntimeStreamingProgressReadModel(BaseModel):
    schema_version: str = "runtime_streaming_progress.v1"
    contract_ref: str = RUNTIME_STREAMING_PROGRESS_CONTRACT_REF
    route_ref: str = RUNTIME_STREAMING_PROGRESS_ROUTE_REF
    cli_ref: str = RUNTIME_STREAMING_PROGRESS_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    runtime_identity_ref: str = "runtime-identity-ref:hermes-agent:optional-target"
    runtime_run_ref: str = RUNTIME_RUN_EVENTS_SAMPLE_RUN_REF
    uaa_durable_run_ref: str = RUNTIME_RUN_EVENTS_SAMPLE_DURABLE_RUN_REF
    status: str = "read_model_event_preview_only"
    stream_state: RuntimeStreamingProgressStreamState = (
        RuntimeStreamingProgressStreamState.stale_disconnected
    )
    event_previews: list[RuntimeStreamingProgressEventPreview]
    event_count: int
    stale_stream: bool = True
    live_subscription_enabled: bool = False
    sse_transport_enabled: bool = False
    websocket_transport_enabled: bool = False
    reconnect_enabled: bool = False
    event_ingest_enabled: bool = False
    bounded_retention_required: bool = True
    event_hashes_required: bool = True
    uaa_controls_authority: bool = True
    control_center_talks_directly_to_runtime: bool = False
    safe_refs_only: bool = True
    raw_runtime_payload_persisted: bool = False
    raw_tool_payload_persisted: bool = False
    raw_token_persisted: bool = False
    raw_log_persisted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "Runtime streaming progress is represented as redacted ordered event "
        "previews only; no live SSE, WebSocket, or direct runtime subscription is enabled."
    )
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + ["runtime_stream_payload_omitted", "tool_payload_omitted"]
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeStreamingProgressReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.runtime_identity_ref, "runtime_identity_ref"),
            (self.runtime_run_ref, "runtime_run_ref"),
            (self.uaa_durable_run_ref, "uaa_durable_run_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.status, "status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "proof_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        if self.event_count != len(self.event_previews):
            raise ValueError("RUNTIME_STREAMING_PROGRESS_EVENT_COUNT_DRIFT")
        sequences = [event.sequence for event in self.event_previews]
        if sequences != sorted(sequences) or len(sequences) != len(set(sequences)):
            raise ValueError("RUNTIME_STREAMING_PROGRESS_EVENT_ORDER_INVALID")
        if not self.stale_stream:
            raise ValueError("RUNTIME_STREAMING_PROGRESS_STALE_LABEL_REQUIRED")
        if not self.bounded_retention_required or not self.event_hashes_required:
            raise ValueError("RUNTIME_STREAMING_PROGRESS_RETENTION_HASH_REQUIRED")
        denied_flags = {
            "live_subscription_enabled": self.live_subscription_enabled,
            "sse_transport_enabled": self.sse_transport_enabled,
            "websocket_transport_enabled": self.websocket_transport_enabled,
            "reconnect_enabled": self.reconnect_enabled,
            "event_ingest_enabled": self.event_ingest_enabled,
            "control_center_talks_directly_to_runtime": (
                self.control_center_talks_directly_to_runtime
            ),
            "raw_runtime_payload_persisted": self.raw_runtime_payload_persisted,
            "raw_tool_payload_persisted": self.raw_tool_payload_persisted,
            "raw_token_persisted": self.raw_token_persisted,
            "raw_log_persisted": self.raw_log_persisted,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_STREAMING_PROGRESS_LIVE_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.uaa_controls_authority:
            raise ValueError("RUNTIME_STREAMING_PROGRESS_UAA_AUTHORITY_REQUIRED")
        if not self.safe_refs_only:
            raise ValueError("RUNTIME_STREAMING_PROGRESS_SAFE_REFS_REQUIRED")
        return self


def build_runtime_streaming_progress_read_model() -> RuntimeStreamingProgressReadModel:
    blocked_refs = [
        *GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
        "blocked-authority:runtime-streaming-progress-live-sse",
        "blocked-authority:runtime-streaming-progress-websocket",
        "blocked-authority:runtime-streaming-progress-direct-runtime-subscription",
        "blocked-authority:runtime-streaming-progress-raw-tool-payload",
    ]
    events = [
        RuntimeStreamingProgressEventPreview(
            event_ref="runtime-run-event-ref:hermes-agent:stream-fragment-preview",
            sequence=0,
            event_kind=RuntimeStreamingProgressEventKind.token,
            runtime_run_ref=RUNTIME_RUN_EVENTS_SAMPLE_RUN_REF,
            uaa_durable_run_ref=RUNTIME_RUN_EVENTS_SAMPLE_DURABLE_RUN_REF,
            proof_ref="proof-ref:runtime-streaming-progress:fragment-preview",
            event_hash_ref="event-hash-ref:runtime-streaming-progress:fragment-preview",
            safe_summary="Redacted stream fragment progress preview; content omitted.",
        ),
        RuntimeStreamingProgressEventPreview(
            event_ref="runtime-run-event-ref:hermes-agent:tool-started",
            sequence=1,
            event_kind=RuntimeStreamingProgressEventKind.tool_started,
            runtime_run_ref=RUNTIME_RUN_EVENTS_SAMPLE_RUN_REF,
            uaa_durable_run_ref=RUNTIME_RUN_EVENTS_SAMPLE_DURABLE_RUN_REF,
            tool_call_ref="tool-call-ref:runtime-streaming-progress:sample",
            proof_ref="proof-ref:runtime-streaming-progress:tool-started",
            event_hash_ref="event-hash-ref:runtime-streaming-progress:tool-started",
            safe_summary="Tool-start progress preview uses a tool call ref only.",
        ),
        RuntimeStreamingProgressEventPreview(
            event_ref="runtime-run-event-ref:hermes-agent:tool-completed",
            sequence=2,
            event_kind=RuntimeStreamingProgressEventKind.tool_completed,
            runtime_run_ref=RUNTIME_RUN_EVENTS_SAMPLE_RUN_REF,
            uaa_durable_run_ref=RUNTIME_RUN_EVENTS_SAMPLE_DURABLE_RUN_REF,
            tool_call_ref="tool-call-ref:runtime-streaming-progress:sample",
            proof_ref="proof-ref:runtime-streaming-progress:tool-completed",
            event_hash_ref="event-hash-ref:runtime-streaming-progress:tool-completed",
            safe_summary="Tool-completed progress preview omits raw tool output.",
        ),
        RuntimeStreamingProgressEventPreview(
            event_ref="runtime-run-event-ref:hermes-agent:approval-wait",
            sequence=3,
            event_kind=RuntimeStreamingProgressEventKind.approval_wait,
            runtime_run_ref=RUNTIME_RUN_EVENTS_SAMPLE_RUN_REF,
            uaa_durable_run_ref=RUNTIME_RUN_EVENTS_SAMPLE_DURABLE_RUN_REF,
            proof_ref="proof-ref:runtime-streaming-progress:approval-wait",
            event_hash_ref="event-hash-ref:runtime-streaming-progress:approval-wait",
            safe_summary="Approval-wait progress preview links back to UAA review refs.",
        ),
        RuntimeStreamingProgressEventPreview(
            event_ref="runtime-run-event-ref:hermes-agent:warning-stale",
            sequence=4,
            event_kind=RuntimeStreamingProgressEventKind.warning,
            runtime_run_ref=RUNTIME_RUN_EVENTS_SAMPLE_RUN_REF,
            uaa_durable_run_ref=RUNTIME_RUN_EVENTS_SAMPLE_DURABLE_RUN_REF,
            proof_ref="proof-ref:runtime-streaming-progress:stale-stream",
            event_hash_ref="event-hash-ref:runtime-streaming-progress:stale-stream",
            safe_summary="Stream is stale/disconnected; live reconnect is blocked.",
        ),
    ]
    return RuntimeStreamingProgressReadModel(
        event_previews=events,
        event_count=len(events),
        blocked_authority_refs=blocked_refs,
        proof_refs=[
            RUNTIME_STREAMING_PROGRESS_PROOF_REF,
            "proof-ref:runtime-streaming-progress:fragment-preview",
            "proof-ref:runtime-streaming-progress:tool-started",
            "proof-ref:runtime-streaming-progress:tool-completed",
            "proof-ref:runtime-streaming-progress:approval-wait",
            "proof-ref:runtime-streaming-progress:stale-stream",
            "proof-ref:runtime-streaming-progress:redaction",
            "proof-ref:runtime-streaming-progress:event-order",
            "proof-ref:runtime-streaming-progress:stale-label",
        ],
        next_safe_action_refs=[
            "next-safe-action-ref:runtime-streaming-progress:add-approved-loopback-transport",
            "next-safe-action-ref:runtime-streaming-progress:define-bounded-retention",
            "next-safe-action-ref:runtime-streaming-progress:add-event-hash-verifier",
            "next-safe-action-ref:runtime-streaming-progress:bind-proof-refs",
        ],
    )
