from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ultimate_ai_agent.core.approvals import ApprovalGrant, ApprovalRequest
from ultimate_ai_agent.core.execution.approval_queue import (
    RunAttachedApprovalQueueReadModel,
    build_run_attached_approval_queue_read_model,
)
from ultimate_ai_agent.core.execution.background_coworker import (
    BackgroundCoworkerReadModel,
    build_background_coworker_read_model,
)
from ultimate_ai_agent.core.execution.connector_delivery import (
    ConnectorDeliveryReadModel,
    ConnectorDeliveryReviewQueueReadModel,
    build_connector_delivery_read_model,
    build_connector_delivery_review_queue,
)
from ultimate_ai_agent.core.execution.read_models import (
    DurableRunLifecycleReadModel,
    RunProgressReadModel,
    build_durable_run_lifecycle_read_model,
    build_run_progress_read_model,
)
from ultimate_ai_agent.core.execution.run_storage import (
    AppendFirstRunStorage,
    DurableRunStorageEntryKind,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_payload,
    validate_safe_execution_text,
)


RUN_OBSERVABILITY_READ_MODEL_SCHEMA_VERSION = "run_observability_read_model.v1"
RUN_OBSERVABILITY_SOURCE = "python_core_run_observability_read_model"
RUN_OBSERVABILITY_CONTRACT_REF = "contract-ref:run-observability-surface:v1"
RUN_OBSERVABILITY_ROUTE_REF = "GET /control-center/runs/observability"
RUN_OBSERVABILITY_CLI_REF = (
    "python -m ultimate_ai_agent.core.task_decomposition.cli "
    "inspect-run-observability"
)
RUN_OBSERVABILITY_STATE_NOT_FOUND_REF = (
    "task-decomposition-run:observability:state-not-found"
)
RUN_OBSERVABILITY_BLOCKED_AUTHORITY_REFS = (
    "blocked-state:run-observability:no-cancel-control",
    "blocked-state:run-observability:no-resume-control",
    "blocked-state:run-observability:no-live-stream-runtime",
    "blocked-state:run-observability:no-background-worker",
    "blocked-state:run-observability:no-provider-model-call",
    "blocked-state:run-observability:no-tool-execution",
    "blocked-state:run-observability:no-connector-write-or-send",
    "blocked-state:run-observability:no-autonomous-execution",
    "blocked-state:run-observability:no-raw-payload-persistence",
)

RunObservabilityStatus = Literal[
    "implemented_read_only",
    "state_not_found_no_write",
]


def _stable_ref(prefix: str, *parts: str) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(payload).hexdigest()[:24]}"


def _sorted_unique(refs: Iterable[str | None]) -> list[str]:
    safe_refs: list[str] = []
    for ref in refs:
        if not ref:
            continue
        validate_execution_ref(ref, "run_observability_ref")
        safe_refs.append(ref)
    return sorted(dict.fromkeys(safe_refs))


def _latest_run_ref(storage: AppendFirstRunStorage) -> str | None:
    for entry in reversed(storage.list_entries()):
        if (
            entry.kind == DurableRunStorageEntryKind.run_record
            and entry.record_snapshot is not None
        ):
            return entry.run_id
    return None


class RunObservabilityReadModel(BaseModel):
    schema_version: str = RUN_OBSERVABILITY_READ_MODEL_SCHEMA_VERSION
    contract_ref: str = RUN_OBSERVABILITY_CONTRACT_REF
    source: str = RUN_OBSERVABILITY_SOURCE
    backend_owned: bool = True
    status: RunObservabilityStatus
    run_ref: str = Field(..., min_length=1)
    selected_run_ref: str | None = None
    route_ref: str = RUN_OBSERVABILITY_ROUTE_REF
    route_refs: list[str] = Field(
        default_factory=lambda: [
            RUN_OBSERVABILITY_ROUTE_REF,
            "GET /task-decomposition/runs/{run_id}/lifecycle",
            "GET /task-decomposition/runs/{run_id}/approvals",
            "GET /control-center/approvals/queue",
            "GET /control-center/evidence/timeline",
        ]
    )
    cli_ref: str = RUN_OBSERVABILITY_CLI_REF
    lifecycle: DurableRunLifecycleReadModel | None = None
    progress: RunProgressReadModel | None = None
    approval_queue: RunAttachedApprovalQueueReadModel
    coworker_workers: BackgroundCoworkerReadModel
    connector_deliveries: ConnectorDeliveryReadModel
    connector_delivery_review_queue: ConnectorDeliveryReviewQueueReadModel
    run_refs: list[str] = Field(default_factory=list)
    lifecycle_event_refs: list[str] = Field(default_factory=list)
    progress_event_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    coworker_handoff_refs: list[str] = Field(default_factory=list)
    connector_delivery_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(RUN_OBSERVABILITY_BLOCKED_AUTHORITY_REFS)
    )
    event_count: int = Field(default=0, ge=0)
    progress_event_count: int = Field(default=0, ge=0)
    approval_item_count: int = Field(default=0, ge=0)
    coworker_event_count: int = Field(default=0, ge=0)
    connector_delivery_count: int = Field(default=0, ge=0)
    connector_delivery_review_count: int = Field(default=0, ge=0)
    safe_summary: str = (
        "Run observability joins durable run lifecycle, ordered events, "
        "approvals, progress metadata, coworker refs, connector delivery refs, "
        "receipts, and evidence as read-only safe refs."
    )
    next_safe_action: str = "inspect_run_observability_refs_only"
    cancel_control_status: str = "blocked_no_cancel_route"
    resume_control_status: str = "blocked_no_resume_route"
    streaming_status: str = "blocked_no_live_stream_runtime"
    background_worker_status: str = "planned_blocked_no_worker_runtime"
    provider_model_status: str = "blocked_no_provider_model_authority"
    tool_execution_status: str = "blocked_no_tool_execution_authority"
    connector_execution_status: str = "blocked_no_connector_write_or_send"
    autonomous_execution_status: str = "blocked_no_autonomous_execution"
    proof_detail_status: str = "evidence_surface_projection_no_competing_proof_system"
    safe_refs_only: bool = True
    redacted_summaries_only: bool = True
    raw_payloads_persisted: bool = False
    prompt_content_stored: bool = False
    response_content_stored: bool = False
    provider_payload_content_stored: bool = False
    approval_refs_are_identifiers_only: bool = True
    approval_ref_grants_authority: bool = False
    control_center_presentation_only: bool = True
    ui_mutation_controls_enabled: bool = False
    cancel_resume_controls_enabled: bool = False
    live_streaming_runtime_enabled: bool = False
    provider_model_calls_enabled: bool = False
    tool_execution_enabled: bool = False
    connector_writes_enabled: bool = False
    connector_sends_enabled: bool = False
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    autonomous_execution_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> Any:
        for text, field_name in [
            (self.schema_version, "schema_version"),
            (self.source, "source"),
            (self.status, "status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.safe_summary, "safe_summary"),
            (self.next_safe_action, "next_safe_action"),
            (self.cancel_control_status, "cancel_control_status"),
            (self.resume_control_status, "resume_control_status"),
            (self.streaming_status, "streaming_status"),
            (self.background_worker_status, "background_worker_status"),
            (self.provider_model_status, "provider_model_status"),
            (self.tool_execution_status, "tool_execution_status"),
            (self.connector_execution_status, "connector_execution_status"),
            (self.autonomous_execution_status, "autonomous_execution_status"),
            (self.proof_detail_status, "proof_detail_status"),
        ]:
            validate_safe_execution_text(str(text), field_name)
        for ref in [
            self.contract_ref,
            self.run_ref,
            *(ref for ref in [self.selected_run_ref] if ref),
            *self.run_refs,
            *self.lifecycle_event_refs,
            *self.progress_event_refs,
            *self.approval_refs,
            *self.coworker_handoff_refs,
            *self.connector_delivery_refs,
            *self.receipt_refs,
            *self.evidence_refs,
            *self.proof_refs,
            *self.blocked_authority_refs,
        ]:
            validate_execution_ref(ref, "run_observability_ref")
        validate_safe_execution_payload(
            self.model_dump(
                mode="json",
                exclude={
                    "lifecycle",
                    "progress",
                    "approval_queue",
                    "coworker_workers",
                    "connector_deliveries",
                    "connector_delivery_review_queue",
                },
            ),
            "run_observability_read_model",
        )
        for field_name in [
            "backend_owned",
            "safe_refs_only",
            "redacted_summaries_only",
            "approval_refs_are_identifiers_only",
            "control_center_presentation_only",
        ]:
            if not getattr(self, field_name):
                raise ValueError(f"RUN_OBSERVABILITY_INVARIANT_FAILED:{field_name}")
        for field_name in [
            "raw_payloads_persisted",
            "prompt_content_stored",
            "response_content_stored",
            "provider_payload_content_stored",
            "approval_ref_grants_authority",
            "ui_mutation_controls_enabled",
            "cancel_resume_controls_enabled",
            "live_streaming_runtime_enabled",
            "provider_model_calls_enabled",
            "tool_execution_enabled",
            "connector_writes_enabled",
            "connector_sends_enabled",
            "background_worker_enabled",
            "scheduler_enabled",
            "autonomous_execution_enabled",
            "production_authority_enabled",
        ]:
            if getattr(self, field_name):
                raise ValueError(f"RUN_OBSERVABILITY_AUTHORITY_DENIED:{field_name}")
        if self.lifecycle is None and self.status != "state_not_found_no_write":
            raise ValueError("RUN_OBSERVABILITY_LIFECYCLE_REQUIRED")
        if self.lifecycle is not None and self.status != "implemented_read_only":
            raise ValueError("RUN_OBSERVABILITY_STATUS_MISMATCH")
        return self


def build_run_observability_read_model(
    storage: AppendFirstRunStorage,
    *,
    run_ref: str | None = None,
    approval_requests: Iterable[ApprovalRequest] = (),
    approval_grants: Iterable[ApprovalGrant] = (),
    lifecycle_limit: int = 50,
    related_limit: int = 50,
) -> RunObservabilityReadModel:
    if run_ref is not None:
        validate_execution_ref(run_ref, "run_ref")
    selected_run_ref = run_ref or _latest_run_ref(storage)
    effective_run_ref = selected_run_ref or RUN_OBSERVABILITY_STATE_NOT_FOUND_REF
    lifecycle = (
        build_durable_run_lifecycle_read_model(
            storage,
            effective_run_ref,
            include_receipts=False,
            limit=lifecycle_limit,
        )
        if selected_run_ref
        else None
    )
    progress: RunProgressReadModel | None = None
    if lifecycle is not None:
        try:
            progress = build_run_progress_read_model(
                storage,
                effective_run_ref,
                limit=lifecycle_limit,
            )
        except ValidationError:
            progress = None
    approval_queue = build_run_attached_approval_queue_read_model(
        approval_requests=approval_requests,
        approval_grants=approval_grants,
        durable_run_storage=storage,
        run_ref=selected_run_ref,
        limit=related_limit,
    )
    coworker_workers = build_background_coworker_read_model(
        storage,
        run_ref=selected_run_ref,
        limit=related_limit,
    )
    connector_deliveries = build_connector_delivery_read_model(
        storage,
        run_ref=selected_run_ref,
        limit=related_limit,
    )
    connector_delivery_review_queue = build_connector_delivery_review_queue(
        storage,
        run_ref=selected_run_ref,
        limit=related_limit,
    )
    lifecycle_events = lifecycle.events if lifecycle is not None else []
    progress_events = progress.events if progress is not None else []
    coworker_events = coworker_workers.events
    connector_events = connector_deliveries.events
    connector_items = connector_deliveries.delivery_statuses
    connector_review_items = connector_delivery_review_queue.queue_items
    approval_refs = _sorted_unique(
        [
            *(lifecycle.approval_refs if lifecycle is not None else []),
            *approval_queue.unified_review.pending_approval_refs,
            *approval_queue.unified_review.approval_history_refs,
            *connector_delivery_review_queue.outbound_approval_refs,
        ]
    )
    receipt_refs = _sorted_unique(
        [
            *(lifecycle.receipt_refs if lifecycle is not None else []),
            *(progress.receipt_refs if progress is not None else []),
            *approval_queue.unified_review.receipt_refs,
            *connector_delivery_review_queue.receipt_refs,
            *(ref for event in connector_events for ref in event.expected_receipt_refs),
            *(ref for event in connector_events for ref in event.failure_receipt_refs),
            *(ref for event in coworker_events for ref in event.receipt_refs),
        ]
    )
    evidence_refs = _sorted_unique(
        [
            *(lifecycle.evidence_refs if lifecycle is not None else []),
            *(progress.evidence_refs if progress is not None else []),
            *approval_queue.unified_review.evidence_refs,
            *connector_delivery_review_queue.evidence_refs,
            *(ref for event in connector_events for ref in event.evidence_refs),
            *(ref for event in coworker_events for ref in event.evidence_refs),
        ]
    )
    blocked_refs = _sorted_unique(
        [
            *RUN_OBSERVABILITY_BLOCKED_AUTHORITY_REFS,
            *(progress.blocked_state_refs if progress is not None else []),
            *approval_queue.unified_review.blocked_authority_refs,
            *connector_delivery_review_queue.blocked_authority_refs,
            *(ref for event in coworker_events for ref in event.blocked_authority_refs),
        ]
    )
    return RunObservabilityReadModel(
        status="implemented_read_only" if lifecycle is not None else "state_not_found_no_write",
        run_ref=effective_run_ref,
        selected_run_ref=selected_run_ref,
        lifecycle=lifecycle,
        progress=progress,
        approval_queue=approval_queue,
        coworker_workers=coworker_workers,
        connector_deliveries=connector_deliveries,
        connector_delivery_review_queue=connector_delivery_review_queue,
        run_refs=_sorted_unique(
            [
                effective_run_ref,
                *(approval_queue.unified_review.run_refs),
                *(connector_delivery_review_queue.run_refs),
                *(item.run_ref for item in connector_items),
                *(event.run_ref for event in coworker_events),
                *(event.parent_run_ref for event in coworker_events),
                *(event.child_run_ref for event in coworker_events),
            ]
        ),
        lifecycle_event_refs=_sorted_unique(event.storage_entry_ref for event in lifecycle_events),
        progress_event_refs=_sorted_unique(event.durable_run_event_ref for event in progress_events),
        approval_refs=approval_refs,
        coworker_handoff_refs=_sorted_unique(
            [
                *approval_queue.unified_review.coworker_handoff_refs,
                *(event.handoff_ref for event in coworker_events),
                *(event.worker_ref for event in coworker_events),
            ]
        ),
        connector_delivery_refs=_sorted_unique(
            [
                *approval_queue.unified_review.connector_delivery_refs,
                *(item.delivery_ref for item in connector_items),
                *(item.delivery_ref for item in connector_review_items),
            ]
        ),
        receipt_refs=receipt_refs,
        evidence_refs=evidence_refs,
        proof_refs=_sorted_unique(
            [
                *approval_queue.unified_review.proof_refs,
                *connector_delivery_review_queue.proof_refs,
                _stable_ref("proof-ref", RUN_OBSERVABILITY_CONTRACT_REF, effective_run_ref),
            ]
        ),
        blocked_authority_refs=blocked_refs,
        event_count=lifecycle.event_count if lifecycle is not None else 0,
        progress_event_count=progress.event_count if progress is not None else 0,
        approval_item_count=approval_queue.summary.queue_item_count,
        coworker_event_count=coworker_workers.event_count,
        connector_delivery_count=connector_deliveries.delivery_count,
        connector_delivery_review_count=connector_delivery_review_queue.delivery_count,
    )
