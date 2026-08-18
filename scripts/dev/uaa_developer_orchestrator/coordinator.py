from __future__ import annotations

import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.time import utc_now


DEVELOPER_COORDINATOR_CONTRACT_REF = "contract-ref:local-developer-work-coordinator:v1"
DEVELOPER_COORDINATOR_REF = "developer-work-coordinator:local-only"
DEVELOPER_COORDINATOR_CLI_REF = "scripts/dev/uaa_developer_queue.py"
DEVELOPER_COORDINATOR_STATE_DIR_ENV = "UAA_DEVELOPER_COORDINATOR_STATE_DIR"
DEVELOPER_COORDINATOR_STATE_FILE = "developer_work_queue.json"
DEVELOPER_COORDINATOR_RECEIPTS_FILE = "developer_work_queue_receipts.jsonl"
DEVELOPER_COORDINATOR_PENDING_TRANSACTION_FILE = (
    "developer_work_queue_pending_transaction.json"
)
DEVELOPER_COORDINATOR_LOCK_FILE = "developer_work_queue.lock"
DEVELOPER_COORDINATOR_GLOBAL_WIP_LIMIT = 3
DEVELOPER_COORDINATOR_GLOBAL_EXCLUSIVE_WIP_LIMIT = 1
DEVELOPER_COORDINATOR_WIP_LANE_LIMIT = 1
DEVELOPER_COORDINATOR_NODE_WIP_LIMIT = 2

DeveloperWorkPriority = Literal["p0", "p1", "p2", "p3"]
DeveloperWorkState = Literal[
    "queued",
    "claimed",
    "blocked",
    "review",
    "completed",
    "canceled",
]
DeveloperWorkConcurrency = Literal["parallel_safe", "exclusive"]
DeveloperWorkWipLane = Literal[
    "shared_core",
    "product_surface",
    "verification_read_only",
]
DeveloperWorktreePosture = Literal["isolated_required"]
DeveloperSolThinkingLevel = Literal["medium", "high", "xhigh"]
DeveloperScopeDispositionKind = Literal[
    "must_fix_now",
    "defer_safely",
    "dismiss_with_evidence",
]
DeveloperWorkEventKind = Literal[
    "initialized",
    "node_registered",
    "node_heartbeat",
    "task_added",
    "task_claimed",
    "task_heartbeat",
    "task_released",
    "task_blocked",
    "task_unblocked",
    "scope_disposition_recorded",
    "task_completed",
    "task_canceled",
    "task_archive_ready",
]
DeveloperNodeReadiness = Literal["ready", "degraded", "offline"]
DeveloperNodeCapability = Literal[
    "queue_claim",
    "local_worktree",
    "local_verification",
    "github_merge",
]


class DeveloperWorkQueueError(RuntimeError):
    pass


class DeveloperWorkQueueConflictError(DeveloperWorkQueueError):
    pass


class DeveloperWorkQueueClaimError(DeveloperWorkQueueError):
    pass


def _hash_ref(prefix: str, value: object) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return (
        f"{prefix}:sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:24]}"
    )


def developer_coordinator_state_dir() -> Path:
    value = os.environ.get(DEVELOPER_COORDINATOR_STATE_DIR_ENV, "").strip()
    if value:
        return Path(value).expanduser()
    return (
        Path.home()
        / ".local"
        / "state"
        / "ultimate-ai-agent"
        / "developer_work_coordinator"
    )


def _validate_refs(values: list[str], field_name: str) -> None:
    for value in values:
        validate_task_ref(value, field_name)


class DeveloperWorkTaskDraft(BaseModel):
    task_ref: str = Field(..., min_length=1)
    queue_order: int = Field(default=100000, ge=0)
    title: str = Field(..., min_length=1, max_length=140)
    safe_summary: str = Field(..., min_length=1, max_length=640)
    priority: DeveloperWorkPriority
    concurrency: DeveloperWorkConcurrency = "parallel_safe"
    wip_lane: DeveloperWorkWipLane = "shared_core"
    canonical_task_ref: str = Field(..., min_length=1)
    canonical_source_ref: str = Field(..., min_length=1)
    canonical_source_fingerprint_ref: str = Field(..., min_length=1)
    scope_contract_ref: str = Field(..., min_length=1)
    in_scope_refs: list[str] = Field(default_factory=list)
    out_of_scope_refs: list[str] = Field(default_factory=list)
    sol_thinking_level: DeveloperSolThinkingLevel
    branch_ref: str = Field(..., min_length=1)
    worktree_ref: str = Field(..., min_length=1)
    worktree_posture: DeveloperWorktreePosture = "isolated_required"
    workstream_ref: str = Field(..., min_length=1)
    acceptance_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    merge_gate_refs: list[str] = Field(default_factory=list)
    depends_on_task_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=360)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_draft(self) -> "DeveloperWorkTaskDraft":
        if not self.task_ref.startswith("dev-task:"):
            raise ValueError("developer work task ref must begin dev-task:")
        _validate_refs(
            [
                self.task_ref,
                self.canonical_task_ref,
                self.canonical_source_ref,
                self.canonical_source_fingerprint_ref,
                self.scope_contract_ref,
                self.workstream_ref,
                *self.in_scope_refs,
                *self.out_of_scope_refs,
                *self.acceptance_refs,
                *self.verifier_refs,
                *self.merge_gate_refs,
                *self.depends_on_task_refs,
                self.branch_ref,
                self.worktree_ref,
            ],
            "developer_work_task_ref",
        )
        for value in [
            self.title,
            self.safe_summary,
            self.priority,
            self.concurrency,
            self.wip_lane,
            self.worktree_posture,
            self.sol_thinking_level,
            self.next_safe_action,
        ]:
            validate_safe_task_text(value, "developer_work_task_text")
        if not self.acceptance_refs:
            raise ValueError("developer work task requires acceptance refs")
        if not self.verifier_refs:
            raise ValueError("developer work task requires verifier refs")
        if not self.merge_gate_refs:
            raise ValueError("developer work task requires merge gate refs")
        if not self.in_scope_refs or not self.out_of_scope_refs:
            raise ValueError("developer work task requires explicit scope boundaries")
        if self.task_ref in self.depends_on_task_refs:
            raise ValueError("developer work task cannot depend on itself")
        if len(self.depends_on_task_refs) != len(set(self.depends_on_task_refs)):
            raise ValueError("developer work task dependencies must be unique")
        return self


class DeveloperWorkNode(BaseModel):
    """A trusted developer machine declaration containing safe refs only."""

    node_ref: str
    transport_ref: str
    readiness: DeveloperNodeReadiness = "ready"
    capabilities: list[DeveloperNodeCapability] = Field(default_factory=list)
    heartbeat_generation: int = Field(default=0, ge=0)
    latest_heartbeat_ref: str | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_node(self) -> "DeveloperWorkNode":
        _validate_refs(
            [
                self.node_ref,
                self.transport_ref,
                *(
                    [self.latest_heartbeat_ref]
                    if self.latest_heartbeat_ref is not None
                    else []
                ),
            ],
            "developer_work_node_ref",
        )
        if not self.capabilities:
            raise ValueError("developer work node requires capabilities")
        if "queue_claim" not in self.capabilities:
            raise ValueError("developer work node requires queue claim capability")
        if len(self.capabilities) != len(set(self.capabilities)):
            raise ValueError("developer work node capabilities must be unique")
        validate_safe_task_text(self.readiness, "developer_work_node_readiness")
        return self


class DeveloperScopeDisposition(BaseModel):
    finding_ref: str
    classification: DeveloperScopeDispositionKind
    safe_summary: str
    evidence_refs: list[str] = Field(default_factory=list)
    deferred_follow_up_ref: str | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_disposition(self) -> "DeveloperScopeDisposition":
        _validate_refs(
            [
                self.finding_ref,
                *self.evidence_refs,
                *(
                    [self.deferred_follow_up_ref]
                    if self.deferred_follow_up_ref is not None
                    else []
                ),
            ],
            "developer_scope_disposition_ref",
        )
        for value in [self.classification, self.safe_summary]:
            validate_safe_task_text(value, "developer_scope_disposition_text")
        if (
            self.classification == "defer_safely"
            and self.deferred_follow_up_ref is None
        ):
            raise ValueError("safe deferral requires a durable follow-up ref")
        if (
            self.classification in {"must_fix_now", "dismiss_with_evidence"}
            and not self.evidence_refs
        ):
            raise ValueError("scope disposition requires evidence refs")
        return self


class DeveloperWorkTask(DeveloperWorkTaskDraft):
    state: DeveloperWorkState = "queued"
    owner_node_ref: str | None = None
    claim_ref: str | None = None
    claim_generation: int = Field(default=0, ge=0)
    latest_heartbeat_ref: str | None = None
    blocker_refs: list[str] = Field(default_factory=list)
    completion_evidence_refs: list[str] = Field(default_factory=list)
    cancellation_reason_ref: str | None = None
    terminal_scope_packet_ref: str | None = None
    latest_receipt_ref: str | None = None
    scope_dispositions: list[DeveloperScopeDisposition] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_task(self) -> "DeveloperWorkTask":
        if self.owner_node_ref is not None:
            validate_task_ref(self.owner_node_ref, "developer_work_owner_node_ref")
        _validate_refs(
            [
                *([self.claim_ref] if self.claim_ref is not None else []),
                *(
                    [self.latest_heartbeat_ref]
                    if self.latest_heartbeat_ref is not None
                    else []
                ),
                *self.blocker_refs,
                *self.completion_evidence_refs,
                *(
                    [self.cancellation_reason_ref]
                    if self.cancellation_reason_ref is not None
                    else []
                ),
                *(
                    [self.terminal_scope_packet_ref]
                    if self.terminal_scope_packet_ref is not None
                    else []
                ),
                *(
                    [self.latest_receipt_ref]
                    if self.latest_receipt_ref is not None
                    else []
                ),
            ],
            "developer_work_task_state_ref",
        )
        claimed = self.state == "claimed"
        if claimed != (self.owner_node_ref is not None and self.claim_ref is not None):
            raise ValueError("developer work claim state binding invalid")
        if self.state != "claimed" and (
            self.owner_node_ref is not None or self.claim_ref is not None
        ):
            raise ValueError("developer work non-claimed task cannot retain claim")
        if self.state == "blocked" and not self.blocker_refs:
            raise ValueError("blocked developer work task requires blocker refs")
        if self.state == "completed" and not self.completion_evidence_refs:
            raise ValueError("completed developer work task requires evidence refs")
        if (self.state == "canceled") != (self.cancellation_reason_ref is not None):
            raise ValueError("canceled developer work task requires one reason ref")
        if self.terminal_scope_packet_ref is not None and self.state not in {
            "completed",
            "canceled",
        }:
            raise ValueError(
                "terminal scope packet requires a terminal developer work task"
            )
        findings = [item.finding_ref for item in self.scope_dispositions]
        if len(findings) != len(set(findings)):
            raise ValueError("developer scope findings must be unique")
        return self


class DeveloperWorkQueueSnapshot(BaseModel):
    schema_version: Literal["uaa-local-developer-work-queue.v1"] = (
        "uaa-local-developer-work-queue.v1"
    )
    contract_ref: str = DEVELOPER_COORDINATOR_CONTRACT_REF
    coordinator_ref: str = DEVELOPER_COORDINATOR_REF
    revision: int = Field(default=0, ge=0)
    nodes: list[DeveloperWorkNode] = Field(default_factory=list)
    tasks: list[DeveloperWorkTask] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_snapshot(self) -> "DeveloperWorkQueueSnapshot":
        _validate_refs(
            [self.contract_ref, self.coordinator_ref],
            "developer_work_snapshot_ref",
        )
        task_refs = [task.task_ref for task in self.tasks]
        if len(task_refs) != len(set(task_refs)):
            raise ValueError("developer work queue task refs must be unique")
        node_refs = [node.node_ref for node in self.nodes]
        if len(node_refs) != len(set(node_refs)):
            raise ValueError("developer work queue node refs must be unique")
        known = set(task_refs)
        for task in self.tasks:
            if not set(task.depends_on_task_refs).issubset(known):
                raise ValueError("developer work task dependency missing")
        if _has_dependency_cycle(self.tasks):
            raise ValueError("developer work queue dependency cycle")
        active_tasks = [
            task for task in self.tasks if task.state not in {"completed", "canceled"}
        ]
        branch_refs = [task.branch_ref for task in active_tasks]
        if len(branch_refs) != len(set(branch_refs)):
            raise ValueError("active developer work branch refs must be unique")
        worktree_refs = [task.worktree_ref for task in active_tasks]
        if len(worktree_refs) != len(set(worktree_refs)):
            raise ValueError("active developer work worktree refs must be unique")
        exclusive_claims = [
            task
            for task in self.tasks
            if task.state == "claimed" and task.concurrency == "exclusive"
        ]
        claimed_tasks = [task for task in self.tasks if task.state == "claimed"]
        if len(claimed_tasks) > DEVELOPER_COORDINATOR_GLOBAL_WIP_LIMIT:
            raise ValueError("developer work global WIP limit exceeded")
        if len(exclusive_claims) > DEVELOPER_COORDINATOR_GLOBAL_EXCLUSIVE_WIP_LIMIT:
            raise ValueError("developer work exclusive WIP limit exceeded")
        claimed_lanes = [task.wip_lane for task in claimed_tasks]
        if len(claimed_lanes) != len(set(claimed_lanes)):
            raise ValueError("developer work WIP lane limit exceeded")
        validate_safe_task_payload(
            self.model_dump(mode="json"), "developer_work_snapshot"
        )
        return self


class DeveloperWorkQueueReceipt(BaseModel):
    schema_version: Literal["uaa-local-developer-work-queue-receipt.v1"] = (
        "uaa-local-developer-work-queue-receipt.v1"
    )
    receipt_ref: str
    event_kind: DeveloperWorkEventKind
    task_ref: str | None = None
    node_ref: str | None = None
    idempotency_ref: str
    payload_fingerprint_ref: str
    revision: int = Field(..., ge=0)
    occurred_at_ref: str
    safe_summary: str
    replayed: bool = False
    git_command_executed: bool = False
    shell_command_executed: bool = False
    remote_dispatch_performed: bool = False
    provider_call_performed: bool = False
    product_runtime_authority_granted: bool = False
    raw_paths_included: bool = False
    raw_content_included: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> "DeveloperWorkQueueReceipt":
        _validate_refs(
            [
                self.receipt_ref,
                self.idempotency_ref,
                self.payload_fingerprint_ref,
                self.occurred_at_ref,
                *([self.task_ref] if self.task_ref is not None else []),
                *([self.node_ref] if self.node_ref is not None else []),
            ],
            "developer_work_receipt_ref",
        )
        for value in [self.event_kind, self.safe_summary]:
            validate_safe_task_text(value, "developer_work_receipt_text")
        forbidden = {
            "git_command_executed": self.git_command_executed,
            "shell_command_executed": self.shell_command_executed,
            "remote_dispatch_performed": self.remote_dispatch_performed,
            "provider_call_performed": self.provider_call_performed,
            "product_runtime_authority_granted": self.product_runtime_authority_granted,
            "raw_paths_included": self.raw_paths_included,
            "raw_content_included": self.raw_content_included,
        }
        enabled = [name for name, value in forbidden.items() if value]
        if enabled:
            raise ValueError(f"developer work receipt enabled {enabled[0]}")
        return self


class DeveloperWorkQueuePendingTransaction(BaseModel):
    schema_version: Literal["uaa-local-developer-work-queue-transaction.v1"] = (
        "uaa-local-developer-work-queue-transaction.v1"
    )
    snapshot: DeveloperWorkQueueSnapshot
    receipt: DeveloperWorkQueueReceipt

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_transaction(self) -> "DeveloperWorkQueuePendingTransaction":
        if self.snapshot.revision != self.receipt.revision:
            raise ValueError("developer work transaction revision mismatch")
        return self


class DeveloperWorkQueueTaskView(BaseModel):
    task_ref: str
    queue_order: int
    canonical_task_ref: str
    canonical_source_ref: str
    canonical_source_fingerprint_ref: str
    scope_contract_ref: str
    in_scope_refs: list[str] = Field(default_factory=list)
    out_of_scope_refs: list[str] = Field(default_factory=list)
    sol_thinking_level: DeveloperSolThinkingLevel
    title: str
    priority: DeveloperWorkPriority
    state: DeveloperWorkState
    concurrency: DeveloperWorkConcurrency
    wip_lane: DeveloperWorkWipLane
    owner_node_ref: str | None
    branch_ref: str
    worktree_ref: str
    worktree_posture: DeveloperWorktreePosture
    dependency_ready: bool
    safe_summary: str
    next_safe_action: str
    blocker_refs: list[str] = Field(default_factory=list)
    completion_evidence_refs: list[str] = Field(default_factory=list)
    cancellation_reason_ref: str | None = None
    terminal_scope_packet_ref: str | None = None
    archive_ready: bool = False
    acceptance_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    merge_gate_refs: list[str] = Field(default_factory=list)
    scope_dispositions: list[DeveloperScopeDisposition] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class DeveloperWorkCoordinatorReadModel(BaseModel):
    schema_version: Literal["uaa-local-developer-work-coordinator-read-model.v1"] = (
        "uaa-local-developer-work-coordinator-read-model.v1"
    )
    contract_ref: str = DEVELOPER_COORDINATOR_CONTRACT_REF
    coordinator_ref: str = DEVELOPER_COORDINATOR_REF
    cli_ref: str = DEVELOPER_COORDINATOR_CLI_REF
    source_label: str = "local_developer_work_coordinator"
    status: Literal["local_only_durable_coordination"] = (
        "local_only_durable_coordination"
    )
    revision: int = Field(..., ge=0)
    nodes: list[DeveloperWorkNode] = Field(default_factory=list)
    tasks: list[DeveloperWorkQueueTaskView] = Field(default_factory=list)
    next_task_by_node_ref: dict[str, str | None] = Field(default_factory=dict)
    global_exclusive_wip_limit: Literal[1] = (
        DEVELOPER_COORDINATOR_GLOBAL_EXCLUSIVE_WIP_LIMIT
    )
    global_wip_limit: Literal[3] = DEVELOPER_COORDINATOR_GLOBAL_WIP_LIMIT
    wip_lane_limit: Literal[1] = DEVELOPER_COORDINATOR_WIP_LANE_LIMIT
    node_wip_limit: int = DEVELOPER_COORDINATOR_NODE_WIP_LIMIT
    active_exclusive_task_ref: str | None = None
    active_task_by_wip_lane: dict[str, str | None] = Field(default_factory=dict)
    archive_ready_task_refs: list[str] = Field(default_factory=list)
    safe_summary: str
    coordination_transport_posture: str
    next_safe_action: str
    queue_mutation_requires_explicit_confirmation: bool = True
    queue_mutation_requires_idempotency: bool = True
    shell_execution_enabled: bool = False
    git_execution_enabled: bool = False
    remote_dispatch_enabled: bool = False
    provider_execution_enabled: bool = False
    product_runtime_authority_granted: bool = False
    raw_paths_included: bool = False
    raw_content_included: bool = False
    redactions_applied: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "DeveloperWorkCoordinatorReadModel":
        _validate_refs(
            [
                self.contract_ref,
                self.coordinator_ref,
                *(
                    [self.active_exclusive_task_ref]
                    if self.active_exclusive_task_ref is not None
                    else []
                ),
                *self.archive_ready_task_refs,
                *(
                    task_ref
                    for task_ref in self.active_task_by_wip_lane.values()
                    if task_ref is not None
                ),
                *self.next_task_by_node_ref.keys(),
                *(
                    task_ref
                    for task_ref in self.next_task_by_node_ref.values()
                    if task_ref is not None
                ),
                *self.redactions_applied,
            ],
            "developer_work_read_model_ref",
        )
        for value in [
            self.cli_ref,
            self.source_label,
            self.status,
            self.safe_summary,
            self.coordination_transport_posture,
            self.next_safe_action,
        ]:
            validate_safe_task_text(value, "developer_work_read_model_text")
        for lane in self.active_task_by_wip_lane:
            validate_safe_task_text(lane, "developer_work_wip_lane")
        if not self.queue_mutation_requires_explicit_confirmation:
            raise ValueError("developer work queue confirmation posture missing")
        if not self.queue_mutation_requires_idempotency:
            raise ValueError("developer work queue idempotency posture missing")
        forbidden = {
            "shell_execution_enabled": self.shell_execution_enabled,
            "git_execution_enabled": self.git_execution_enabled,
            "remote_dispatch_enabled": self.remote_dispatch_enabled,
            "provider_execution_enabled": self.provider_execution_enabled,
            "product_runtime_authority_granted": self.product_runtime_authority_granted,
            "raw_paths_included": self.raw_paths_included,
            "raw_content_included": self.raw_content_included,
        }
        enabled = [name for name, value in forbidden.items() if value]
        if enabled:
            raise ValueError(f"developer work read model enabled {enabled[0]}")
        return self


def _has_dependency_cycle(tasks: list[DeveloperWorkTask]) -> bool:
    dependencies = {task.task_ref: set(task.depends_on_task_refs) for task in tasks}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_ref: str) -> bool:
        if task_ref in visited:
            return False
        if task_ref in visiting:
            return True
        visiting.add(task_ref)
        cycle = any(visit(dependency) for dependency in dependencies[task_ref])
        visiting.remove(task_ref)
        visited.add(task_ref)
        return cycle

    return any(visit(task_ref) for task_ref in dependencies)


def _priority_rank(priority: DeveloperWorkPriority) -> int:
    return {"p0": 0, "p1": 1, "p2": 2, "p3": 3}[priority]


class DeveloperWorkCoordinator:
    """Durable developer task claims and node heartbeats; it never runs agents."""

    def __init__(self, state_dir: Path | None = None) -> None:
        self.state_dir = state_dir or developer_coordinator_state_dir()
        self.state_path = self.state_dir / DEVELOPER_COORDINATOR_STATE_FILE
        self.receipts_path = self.state_dir / DEVELOPER_COORDINATOR_RECEIPTS_FILE
        self.pending_transaction_path = (
            self.state_dir / DEVELOPER_COORDINATOR_PENDING_TRANSACTION_FILE
        )
        self.lock_path = self.state_dir / DEVELOPER_COORDINATOR_LOCK_FILE

    def initialize(self, *, idempotency_ref: str) -> DeveloperWorkQueueReceipt:
        validate_task_ref(idempotency_ref, "developer_work_initialize_idempotency_ref")
        with self._locked():
            snapshot = self._load_snapshot()
            payload = {
                "event_kind": "initialized",
                "coordinator_ref": DEVELOPER_COORDINATOR_REF,
            }
            replay = self._replay(idempotency_ref=idempotency_ref, payload=payload)
            if replay is not None:
                return replay
            receipt = self._receipt(
                event_kind="initialized",
                idempotency_ref=idempotency_ref,
                payload=payload,
                revision=snapshot.revision,
                safe_summary="Local developer work coordinator initialized with no task execution.",
            )
            self._commit_mutation(snapshot, receipt)
            return receipt

    def register_node(
        self,
        node: DeveloperWorkNode,
        *,
        idempotency_ref: str,
    ) -> DeveloperWorkQueueReceipt:
        """Register one reviewed developer machine before it may claim work."""

        validate_task_ref(
            idempotency_ref, "developer_work_register_node_idempotency_ref"
        )
        if node.heartbeat_generation != 0 or node.latest_heartbeat_ref is not None:
            raise ValueError(
                "developer work node registration cannot preseed heartbeat"
            )
        with self._locked():
            snapshot = self._load_snapshot()
            payload = {
                "event_kind": "node_registered",
                "node": node.model_dump(mode="json"),
            }
            replay = self._replay(idempotency_ref=idempotency_ref, payload=payload)
            if replay is not None:
                return replay
            if any(candidate.node_ref == node.node_ref for candidate in snapshot.nodes):
                raise DeveloperWorkQueueConflictError(
                    "DEVELOPER_WORK_NODE_REF_CONFLICT"
                )
            next_snapshot = snapshot.model_copy(
                update={
                    "revision": snapshot.revision + 1,
                    "nodes": [*snapshot.nodes, node],
                }
            )
            receipt = self._receipt(
                event_kind="node_registered",
                node_ref=node.node_ref,
                idempotency_ref=idempotency_ref,
                payload=payload,
                revision=next_snapshot.revision,
                safe_summary=(
                    "Developer node registered with reviewed safe refs and capabilities; "
                    "no remote worker was started."
                ),
            )
            self._commit_mutation(next_snapshot, receipt)
            return receipt

    def node_heartbeat(
        self,
        *,
        node_ref: str,
        idempotency_ref: str,
    ) -> DeveloperWorkQueueReceipt:
        """Record liveness for an idle or active registered node."""

        validate_task_ref(node_ref, "developer_work_node_heartbeat_node_ref")
        validate_task_ref(
            idempotency_ref, "developer_work_node_heartbeat_idempotency_ref"
        )
        with self._locked():
            snapshot = self._load_snapshot()
            node = self._find_node(snapshot, node_ref)
            payload = {"event_kind": "node_heartbeat", "node_ref": node_ref}
            replay = self._replay(idempotency_ref=idempotency_ref, payload=payload)
            if replay is not None:
                return replay
            if node.readiness != "ready":
                raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_NODE_NOT_READY")
            updated = node.model_copy(
                update={
                    "heartbeat_generation": node.heartbeat_generation + 1,
                    "latest_heartbeat_ref": _hash_ref(
                        "developer-node-heartbeat-ref",
                        {
                            "node_ref": node_ref,
                            "generation": node.heartbeat_generation + 1,
                            "revision": snapshot.revision + 1,
                        },
                    ),
                }
            )
            next_snapshot = snapshot.model_copy(
                update={
                    "revision": snapshot.revision + 1,
                    "nodes": self._replace_node(snapshot, updated),
                }
            )
            receipt = self._receipt(
                event_kind="node_heartbeat",
                node_ref=node_ref,
                idempotency_ref=idempotency_ref,
                payload=payload,
                revision=next_snapshot.revision,
                safe_summary=(
                    "Developer node heartbeat recorded. This proves ledger liveness only "
                    "and does not start, stop, or control a remote worker."
                ),
            )
            self._commit_mutation(next_snapshot, receipt)
            return receipt

    def add_task(
        self,
        draft: DeveloperWorkTaskDraft,
        *,
        idempotency_ref: str,
    ) -> DeveloperWorkQueueReceipt:
        validate_task_ref(idempotency_ref, "developer_work_add_idempotency_ref")
        with self._locked():
            snapshot = self._load_snapshot()
            payload = {
                "event_kind": "task_added",
                "draft": draft.model_dump(mode="json"),
            }
            replay = self._replay(idempotency_ref=idempotency_ref, payload=payload)
            if replay is not None:
                return replay
            if any(task.task_ref == draft.task_ref for task in snapshot.tasks):
                raise DeveloperWorkQueueConflictError(
                    "DEVELOPER_WORK_TASK_REF_CONFLICT"
                )
            missing_dependencies = set(draft.depends_on_task_refs) - {
                task.task_ref for task in snapshot.tasks
            }
            if missing_dependencies:
                raise DeveloperWorkQueueConflictError(
                    "DEVELOPER_WORK_TASK_DEPENDENCY_MISSING"
                )
            if any(
                task.state not in {"completed", "canceled"}
                and task.branch_ref == draft.branch_ref
                for task in snapshot.tasks
            ):
                raise DeveloperWorkQueueConflictError(
                    "DEVELOPER_WORK_BRANCH_REF_CONFLICT"
                )
            if any(
                task.state not in {"completed", "canceled"}
                and task.worktree_ref == draft.worktree_ref
                for task in snapshot.tasks
            ):
                raise DeveloperWorkQueueConflictError(
                    "DEVELOPER_WORK_WORKTREE_REF_CONFLICT"
                )
            task = DeveloperWorkTask(**draft.model_dump(mode="json"))
            next_snapshot = snapshot.model_copy(
                update={
                    "revision": snapshot.revision + 1,
                    "tasks": [*snapshot.tasks, task],
                }
            )
            receipt = self._receipt(
                event_kind="task_added",
                task_ref=task.task_ref,
                idempotency_ref=idempotency_ref,
                payload=payload,
                revision=next_snapshot.revision,
                safe_summary="Developer task recorded with safe refs; no branch, shell, Git, or agent execution occurred.",
            )
            updated_task = task.model_copy(
                update={"latest_receipt_ref": receipt.receipt_ref}
            )
            next_snapshot = next_snapshot.model_copy(
                update={"tasks": [*snapshot.tasks, updated_task]}
            )
            self._commit_mutation(next_snapshot, receipt)
            return receipt

    def claim_next(
        self,
        *,
        node_ref: str,
        idempotency_ref: str,
    ) -> DeveloperWorkQueueReceipt:
        validate_task_ref(node_ref, "developer_work_claim_node_ref")
        validate_task_ref(idempotency_ref, "developer_work_claim_idempotency_ref")
        with self._locked():
            snapshot = self._load_snapshot()
            replay = self._replay_claim_next(
                idempotency_ref=idempotency_ref,
                node_ref=node_ref,
            )
            if replay is not None:
                return replay
            task = self._next_claimable(snapshot, node_ref=node_ref)
            if task is None:
                raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_NO_CLAIMABLE_TASK")
            return self._claim_locked(
                snapshot=snapshot,
                task_ref=task.task_ref,
                node_ref=node_ref,
                idempotency_ref=idempotency_ref,
            )

    def claim_task(
        self,
        *,
        task_ref: str,
        node_ref: str,
        idempotency_ref: str,
    ) -> DeveloperWorkQueueReceipt:
        validate_task_ref(task_ref, "developer_work_claim_task_ref")
        validate_task_ref(node_ref, "developer_work_claim_node_ref")
        validate_task_ref(idempotency_ref, "developer_work_claim_idempotency_ref")
        with self._locked():
            snapshot = self._load_snapshot()
            return self._claim_locked(
                snapshot=snapshot,
                task_ref=task_ref,
                node_ref=node_ref,
                idempotency_ref=idempotency_ref,
            )

    def heartbeat(
        self,
        *,
        task_ref: str,
        node_ref: str,
        idempotency_ref: str,
    ) -> DeveloperWorkQueueReceipt:
        return self._transition_claimed_task(
            event_kind="task_heartbeat",
            task_ref=task_ref,
            node_ref=node_ref,
            idempotency_ref=idempotency_ref,
            safe_summary="Developer task heartbeat recorded; no task execution occurred.",
        )

    def release(
        self,
        *,
        task_ref: str,
        node_ref: str,
        idempotency_ref: str,
    ) -> DeveloperWorkQueueReceipt:
        return self._transition_claimed_task(
            event_kind="task_released",
            task_ref=task_ref,
            node_ref=node_ref,
            idempotency_ref=idempotency_ref,
            safe_summary="Developer task claim released back to the durable queue; no task execution occurred.",
        )

    def complete(
        self,
        *,
        task_ref: str,
        node_ref: str,
        evidence_refs: list[str],
        idempotency_ref: str,
    ) -> DeveloperWorkQueueReceipt:
        _validate_refs(evidence_refs, "developer_work_completion_evidence_ref")
        if not evidence_refs:
            raise ValueError("developer work completion requires evidence refs")
        return self._transition_claimed_task(
            event_kind="task_completed",
            task_ref=task_ref,
            node_ref=node_ref,
            idempotency_ref=idempotency_ref,
            evidence_refs=evidence_refs,
            safe_summary="Developer task marked completed with safe evidence refs; no shell, Git, remote dispatch, or product authority was performed by the coordinator.",
        )

    def cancel(
        self,
        *,
        task_ref: str,
        cancellation_reason_ref: str,
        idempotency_ref: str,
    ) -> DeveloperWorkQueueReceipt:
        """Cancel one unclaimed task with an exact durable reason ref."""

        validate_task_ref(task_ref, "developer_work_cancel_task_ref")
        validate_task_ref(
            cancellation_reason_ref,
            "developer_work_cancellation_reason_ref",
        )
        validate_task_ref(idempotency_ref, "developer_work_cancel_idempotency_ref")
        with self._locked():
            snapshot = self._load_snapshot()
            task = self._find_task(snapshot, task_ref)
            payload = {
                "event_kind": "task_canceled",
                "task_ref": task_ref,
                "cancellation_reason_ref": cancellation_reason_ref,
            }
            replay = self._replay(idempotency_ref=idempotency_ref, payload=payload)
            if replay is not None:
                return replay
            if task.state == "claimed":
                raise DeveloperWorkQueueClaimError(
                    "DEVELOPER_WORK_CLAIM_RELEASE_REQUIRED"
                )
            if task.state in {"completed", "canceled"}:
                raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_TERMINAL_TASK")
            updated = task.model_copy(
                update={
                    "state": "canceled",
                    "owner_node_ref": None,
                    "claim_ref": None,
                    "latest_heartbeat_ref": None,
                    "blocker_refs": [],
                    "cancellation_reason_ref": cancellation_reason_ref,
                }
            )
            next_snapshot = snapshot.model_copy(
                update={
                    "revision": snapshot.revision + 1,
                    "tasks": self._replace_task(snapshot, updated),
                }
            )
            receipt = self._receipt(
                event_kind="task_canceled",
                task_ref=task_ref,
                idempotency_ref=idempotency_ref,
                payload=payload,
                revision=next_snapshot.revision,
                safe_summary=(
                    "Unclaimed developer task canceled with one exact safe reason ref; "
                    "no task, shell, Git, remote dispatch, or archive action occurred."
                ),
            )
            updated = updated.model_copy(
                update={"latest_receipt_ref": receipt.receipt_ref}
            )
            self._commit_mutation(
                next_snapshot.model_copy(
                    update={"tasks": self._replace_task(next_snapshot, updated)}
                ),
                receipt,
            )
            return receipt

    def record_terminal_scope_packet(
        self,
        *,
        task_ref: str,
        terminal_scope_packet_ref: str,
        idempotency_ref: str,
    ) -> DeveloperWorkQueueReceipt:
        """Bind terminal scope/deferral evidence before a Codex task may be archived."""

        validate_task_ref(task_ref, "developer_work_terminal_packet_task_ref")
        validate_task_ref(
            terminal_scope_packet_ref,
            "developer_work_terminal_scope_packet_ref",
        )
        validate_task_ref(
            idempotency_ref,
            "developer_work_terminal_packet_idempotency_ref",
        )
        with self._locked():
            snapshot = self._load_snapshot()
            task = self._find_task(snapshot, task_ref)
            payload = {
                "event_kind": "task_archive_ready",
                "task_ref": task_ref,
                "terminal_scope_packet_ref": terminal_scope_packet_ref,
            }
            replay = self._replay(idempotency_ref=idempotency_ref, payload=payload)
            if replay is not None:
                return replay
            if task.state not in {"completed", "canceled"}:
                raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_TASK_NOT_TERMINAL")
            if task.state == "completed" and not task.completion_evidence_refs:
                raise DeveloperWorkQueueClaimError(
                    "DEVELOPER_WORK_COMPLETION_EVIDENCE_REQUIRED"
                )
            if task.terminal_scope_packet_ref is not None:
                raise DeveloperWorkQueueConflictError(
                    "DEVELOPER_WORK_TERMINAL_PACKET_CONFLICT"
                )
            updated = task.model_copy(
                update={"terminal_scope_packet_ref": terminal_scope_packet_ref}
            )
            next_snapshot = snapshot.model_copy(
                update={
                    "revision": snapshot.revision + 1,
                    "tasks": self._replace_task(snapshot, updated),
                }
            )
            receipt = self._receipt(
                event_kind="task_archive_ready",
                task_ref=task_ref,
                idempotency_ref=idempotency_ref,
                payload=payload,
                revision=next_snapshot.revision,
                safe_summary=(
                    "Terminal scope and deferral packet recorded. The task is archive-ready "
                    "only as a Codex thread-management decision; no thread was archived here."
                ),
            )
            updated = updated.model_copy(
                update={"latest_receipt_ref": receipt.receipt_ref}
            )
            self._commit_mutation(
                next_snapshot.model_copy(
                    update={"tasks": self._replace_task(next_snapshot, updated)}
                ),
                receipt,
            )
            return receipt

    def block(
        self,
        *,
        task_ref: str,
        blocker_refs: list[str],
        idempotency_ref: str,
    ) -> DeveloperWorkQueueReceipt:
        validate_task_ref(task_ref, "developer_work_block_task_ref")
        validate_task_ref(idempotency_ref, "developer_work_block_idempotency_ref")
        _validate_refs(blocker_refs, "developer_work_blocker_ref")
        if not blocker_refs:
            raise ValueError("developer work block requires blocker refs")
        with self._locked():
            snapshot = self._load_snapshot()
            task = self._find_task(snapshot, task_ref)
            if task.state in {"completed", "canceled"}:
                raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_TERMINAL_TASK")
            payload = {
                "event_kind": "task_blocked",
                "task_ref": task_ref,
                "blocker_refs": blocker_refs,
            }
            replay = self._replay(idempotency_ref=idempotency_ref, payload=payload)
            if replay is not None:
                return replay
            next_snapshot = snapshot.model_copy(
                update={
                    "revision": snapshot.revision + 1,
                    "tasks": self._replace_task(
                        snapshot,
                        task.model_copy(
                            update={
                                "state": "blocked",
                                "owner_node_ref": None,
                                "claim_ref": None,
                                "latest_heartbeat_ref": None,
                                "blocker_refs": list(dict.fromkeys(blocker_refs)),
                            }
                        ),
                    ),
                }
            )
            receipt = self._receipt(
                event_kind="task_blocked",
                task_ref=task_ref,
                idempotency_ref=idempotency_ref,
                payload=payload,
                revision=next_snapshot.revision,
                safe_summary="Developer task blocked with safe reason refs; no task execution occurred.",
            )
            updated = self._find_task(next_snapshot, task_ref).model_copy(
                update={"latest_receipt_ref": receipt.receipt_ref}
            )
            self._commit_mutation(
                next_snapshot.model_copy(
                    update={"tasks": self._replace_task(next_snapshot, updated)}
                ),
                receipt,
            )
            return receipt

    def unblock(
        self,
        *,
        task_ref: str,
        idempotency_ref: str,
    ) -> DeveloperWorkQueueReceipt:
        """Return a reviewed blocked task to the queue; no task is executed."""

        validate_task_ref(task_ref, "developer_work_unblock_task_ref")
        validate_task_ref(idempotency_ref, "developer_work_unblock_idempotency_ref")
        with self._locked():
            snapshot = self._load_snapshot()
            task = self._find_task(snapshot, task_ref)
            payload = {"event_kind": "task_unblocked", "task_ref": task_ref}
            replay = self._replay(idempotency_ref=idempotency_ref, payload=payload)
            if replay is not None:
                return replay
            if task.state != "blocked":
                raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_TASK_NOT_BLOCKED")
            updated = task.model_copy(update={"state": "queued", "blocker_refs": []})
            next_snapshot = snapshot.model_copy(
                update={
                    "revision": snapshot.revision + 1,
                    "tasks": self._replace_task(snapshot, updated),
                }
            )
            receipt = self._receipt(
                event_kind="task_unblocked",
                task_ref=task_ref,
                idempotency_ref=idempotency_ref,
                payload=payload,
                revision=next_snapshot.revision,
                safe_summary=(
                    "Developer task returned to the queue after explicit blocker review; "
                    "no shell, Git, remote dispatch, or task execution occurred."
                ),
            )
            updated = updated.model_copy(
                update={"latest_receipt_ref": receipt.receipt_ref}
            )
            self._commit_mutation(
                next_snapshot.model_copy(
                    update={"tasks": self._replace_task(next_snapshot, updated)}
                ),
                receipt,
            )
            return receipt

    def record_scope_disposition(
        self,
        *,
        task_ref: str,
        disposition: DeveloperScopeDisposition,
        idempotency_ref: str,
    ) -> DeveloperWorkQueueReceipt:
        """Record an evidence-gated in-scope fix, safe deferral, or dismissal."""

        validate_task_ref(task_ref, "developer_scope_task_ref")
        validate_task_ref(idempotency_ref, "developer_scope_idempotency_ref")
        with self._locked():
            snapshot = self._load_snapshot()
            task = self._find_task(snapshot, task_ref)
            payload = {
                "event_kind": "scope_disposition_recorded",
                "task_ref": task_ref,
                "disposition": disposition.model_dump(mode="json"),
            }
            replay = self._replay(idempotency_ref=idempotency_ref, payload=payload)
            if replay is not None:
                return replay
            if task.state in {"completed", "canceled"}:
                raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_TERMINAL_TASK")
            if any(
                item.finding_ref == disposition.finding_ref
                for item in task.scope_dispositions
            ):
                raise DeveloperWorkQueueConflictError(
                    "DEVELOPER_SCOPE_FINDING_CONFLICT"
                )
            updated = task.model_copy(
                update={"scope_dispositions": [*task.scope_dispositions, disposition]}
            )
            next_snapshot = snapshot.model_copy(
                update={
                    "revision": snapshot.revision + 1,
                    "tasks": self._replace_task(snapshot, updated),
                }
            )
            receipt = self._receipt(
                event_kind="scope_disposition_recorded",
                task_ref=task_ref,
                idempotency_ref=idempotency_ref,
                payload=payload,
                revision=next_snapshot.revision,
                safe_summary=(
                    "Developer scope finding classified with evidence and no automatic "
                    "scope expansion, task execution, Git, or remote dispatch."
                ),
            )
            updated = updated.model_copy(
                update={"latest_receipt_ref": receipt.receipt_ref}
            )
            self._commit_mutation(
                next_snapshot.model_copy(
                    update={"tasks": self._replace_task(next_snapshot, updated)}
                ),
                receipt,
            )
            return receipt

    def inspect(
        self, *, node_refs: list[str] | None = None
    ) -> DeveloperWorkCoordinatorReadModel:
        next_nodes = node_refs or ["node-ref:mac", "node-ref:beast"]
        _validate_refs(next_nodes, "developer_work_inspect_node_ref")
        if len(next_nodes) != len(set(next_nodes)):
            raise ValueError("developer work inspect node refs must be unique")
        with self._locked():
            snapshot = self._load_snapshot()
        known_by_ref = {task.task_ref: task for task in snapshot.tasks}
        active_exclusive = next(
            (
                task.task_ref
                for task in snapshot.tasks
                if task.state == "claimed" and task.concurrency == "exclusive"
            ),
            None,
        )
        return DeveloperWorkCoordinatorReadModel(
            revision=snapshot.revision,
            nodes=sorted(snapshot.nodes, key=lambda node: node.node_ref),
            tasks=[
                DeveloperWorkQueueTaskView(
                    task_ref=task.task_ref,
                    queue_order=task.queue_order,
                    canonical_task_ref=task.canonical_task_ref,
                    canonical_source_ref=task.canonical_source_ref,
                    canonical_source_fingerprint_ref=task.canonical_source_fingerprint_ref,
                    scope_contract_ref=task.scope_contract_ref,
                    in_scope_refs=task.in_scope_refs,
                    out_of_scope_refs=task.out_of_scope_refs,
                    sol_thinking_level=task.sol_thinking_level,
                    title=task.title,
                    priority=task.priority,
                    state=task.state,
                    concurrency=task.concurrency,
                    wip_lane=task.wip_lane,
                    owner_node_ref=task.owner_node_ref,
                    branch_ref=task.branch_ref,
                    worktree_ref=task.worktree_ref,
                    worktree_posture=task.worktree_posture,
                    dependency_ready=all(
                        known_by_ref[dependency].state == "completed"
                        for dependency in task.depends_on_task_refs
                    ),
                    safe_summary=task.safe_summary,
                    next_safe_action=task.next_safe_action,
                    blocker_refs=task.blocker_refs,
                    completion_evidence_refs=task.completion_evidence_refs,
                    cancellation_reason_ref=task.cancellation_reason_ref,
                    terminal_scope_packet_ref=task.terminal_scope_packet_ref,
                    archive_ready=self._archive_ready(task),
                    acceptance_refs=task.acceptance_refs,
                    verifier_refs=task.verifier_refs,
                    merge_gate_refs=task.merge_gate_refs,
                    scope_dispositions=task.scope_dispositions,
                )
                for task in sorted(
                    snapshot.tasks,
                    key=lambda task: (
                        task.queue_order,
                        _priority_rank(task.priority),
                        task.task_ref,
                    ),
                )
            ],
            next_task_by_node_ref={
                node_ref: (
                    task.task_ref
                    if (task := self._next_claimable(snapshot, node_ref=node_ref))
                    is not None
                    else None
                )
                for node_ref in next_nodes
            },
            active_exclusive_task_ref=active_exclusive,
            active_task_by_wip_lane={
                lane: next(
                    (
                        task.task_ref
                        for task in snapshot.tasks
                        if task.state == "claimed" and task.wip_lane == lane
                    ),
                    None,
                )
                for lane in (
                    "shared_core",
                    "product_surface",
                    "verification_read_only",
                )
            },
            archive_ready_task_refs=[
                task.task_ref
                for task in sorted(snapshot.tasks, key=lambda task: task.task_ref)
                if self._archive_ready(task)
            ],
            safe_summary=(
                "Durable local developer task coordination for explicit branch and "
                "verification handoffs. Registered nodes provide receipt-backed liveness; "
                "agent launch remains outside this queue."
            ),
            coordination_transport_posture=(
                "One shared explicitly configured local state directory is required "
                "for Mac/Beast coordination. Network transport, remote dispatch, and "
                "automatic worker launch are not implemented in v1."
            ),
            next_safe_action=(
                "Initialize and register each node, record exact safe-ref tasks, and let "
                "a ready node claim bounded work with an idempotency ref. Record focused "
                "verification evidence before review."
            ),
            redactions_applied=[
                "redaction-ref:safe-refs-only",
                "redaction-ref:raw-paths-omitted",
                "redaction-ref:raw-content-omitted",
            ],
        )

    def _claim_locked(
        self,
        *,
        snapshot: DeveloperWorkQueueSnapshot,
        task_ref: str,
        node_ref: str,
        idempotency_ref: str,
    ) -> DeveloperWorkQueueReceipt:
        task = self._find_task(snapshot, task_ref)
        payload = {
            "event_kind": "task_claimed",
            "task_ref": task_ref,
            "node_ref": node_ref,
        }
        replay = self._replay(idempotency_ref=idempotency_ref, payload=payload)
        if replay is not None:
            return replay
        if task.state == "claimed" and task.owner_node_ref == node_ref:
            raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_TASK_ALREADY_CLAIMED")
        if task.state != "queued":
            raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_TASK_NOT_QUEUED")
        node = self._find_node(snapshot, node_ref)
        if (
            node.readiness != "ready"
            or "queue_claim" not in node.capabilities
            or node.heartbeat_generation < 1
            or node.latest_heartbeat_ref is None
        ):
            raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_NODE_NOT_READY")
        if not self._dependencies_complete(snapshot, task):
            raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_DEPENDENCIES_INCOMPLETE")
        if (
            self._node_claim_count(snapshot, node_ref)
            >= DEVELOPER_COORDINATOR_NODE_WIP_LIMIT
        ):
            raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_NODE_WIP_LIMIT")
        if self._global_claim_count(snapshot) >= DEVELOPER_COORDINATOR_GLOBAL_WIP_LIMIT:
            raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_GLOBAL_WIP_LIMIT")
        if any(
            candidate.state == "claimed" and candidate.wip_lane == task.wip_lane
            for candidate in snapshot.tasks
        ):
            raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_WIP_LANE_LIMIT")
        if task.concurrency == "exclusive" and any(
            candidate.state == "claimed" and candidate.concurrency == "exclusive"
            for candidate in snapshot.tasks
        ):
            raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_EXCLUSIVE_WIP_LIMIT")
        claim_generation = task.claim_generation + 1
        claim_ref = _hash_ref(
            "developer-work-claim-ref",
            {
                "task_ref": task_ref,
                "node_ref": node_ref,
                "generation": claim_generation,
            },
        )
        updated = task.model_copy(
            update={
                "state": "claimed",
                "owner_node_ref": node_ref,
                "claim_ref": claim_ref,
                "claim_generation": claim_generation,
                "latest_heartbeat_ref": _hash_ref(
                    "developer-work-heartbeat-ref",
                    {"claim_ref": claim_ref, "generation": 0},
                ),
                "blocker_refs": [],
            }
        )
        next_snapshot = snapshot.model_copy(
            update={
                "revision": snapshot.revision + 1,
                "tasks": self._replace_task(snapshot, updated),
            }
        )
        receipt = self._receipt(
            event_kind="task_claimed",
            task_ref=task_ref,
            node_ref=node_ref,
            idempotency_ref=idempotency_ref,
            payload=payload,
            revision=next_snapshot.revision,
            safe_summary="Developer task claimed by one named node with a bounded WIP slot; no execution occurred.",
        )
        self._commit_mutation(
            next_snapshot.model_copy(
                update={
                    "tasks": self._replace_task(
                        next_snapshot,
                        updated.model_copy(
                            update={"latest_receipt_ref": receipt.receipt_ref}
                        ),
                    )
                }
            ),
            receipt,
        )
        return receipt

    def _transition_claimed_task(
        self,
        *,
        event_kind: Literal["task_heartbeat", "task_released", "task_completed"],
        task_ref: str,
        node_ref: str,
        idempotency_ref: str,
        evidence_refs: list[str] | None = None,
        safe_summary: str,
    ) -> DeveloperWorkQueueReceipt:
        validate_task_ref(task_ref, "developer_work_transition_task_ref")
        validate_task_ref(node_ref, "developer_work_transition_node_ref")
        validate_task_ref(idempotency_ref, "developer_work_transition_idempotency_ref")
        with self._locked():
            snapshot = self._load_snapshot()
            task = self._find_task(snapshot, task_ref)
            payload = {
                "event_kind": event_kind,
                "task_ref": task_ref,
                "node_ref": node_ref,
                "evidence_refs": evidence_refs or [],
            }
            replay = self._replay(idempotency_ref=idempotency_ref, payload=payload)
            if replay is not None:
                return replay
            if task.state != "claimed" or task.owner_node_ref != node_ref:
                raise DeveloperWorkQueueClaimError(
                    "DEVELOPER_WORK_CLAIM_OWNERSHIP_REQUIRED"
                )
            if event_kind == "task_completed" and any(
                item.classification == "must_fix_now" and not item.evidence_refs
                for item in task.scope_dispositions
            ):
                raise DeveloperWorkQueueClaimError(
                    "DEVELOPER_SCOPE_FIX_EVIDENCE_REQUIRED"
                )
            if event_kind == "task_heartbeat":
                updated = task.model_copy(
                    update={
                        "latest_heartbeat_ref": _hash_ref(
                            "developer-work-heartbeat-ref",
                            {
                                "claim_ref": task.claim_ref,
                                "generation": task.claim_generation,
                                "revision": snapshot.revision + 1,
                            },
                        )
                    }
                )
            elif event_kind == "task_released":
                updated = task.model_copy(
                    update={
                        "state": "queued",
                        "owner_node_ref": None,
                        "claim_ref": None,
                        "latest_heartbeat_ref": None,
                    }
                )
            else:
                updated = task.model_copy(
                    update={
                        "state": "completed",
                        "owner_node_ref": None,
                        "claim_ref": None,
                        "latest_heartbeat_ref": None,
                        "completion_evidence_refs": list(
                            dict.fromkeys(evidence_refs or [])
                        ),
                    }
                )
            next_snapshot = snapshot.model_copy(
                update={
                    "revision": snapshot.revision + 1,
                    "tasks": self._replace_task(snapshot, updated),
                }
            )
            receipt = self._receipt(
                event_kind=event_kind,
                task_ref=task_ref,
                node_ref=node_ref,
                idempotency_ref=idempotency_ref,
                payload=payload,
                revision=next_snapshot.revision,
                safe_summary=safe_summary,
            )
            self._commit_mutation(
                next_snapshot.model_copy(
                    update={
                        "tasks": self._replace_task(
                            next_snapshot,
                            updated.model_copy(
                                update={"latest_receipt_ref": receipt.receipt_ref}
                            ),
                        )
                    }
                ),
                receipt,
            )
            return receipt

    def _next_claimable(
        self,
        snapshot: DeveloperWorkQueueSnapshot,
        *,
        node_ref: str,
    ) -> DeveloperWorkTask | None:
        node = next(
            (
                candidate
                for candidate in snapshot.nodes
                if candidate.node_ref == node_ref
            ),
            None,
        )
        if (
            node is None
            or node.readiness != "ready"
            or "queue_claim" not in node.capabilities
            or node.heartbeat_generation < 1
            or node.latest_heartbeat_ref is None
        ):
            return None
        if (
            self._node_claim_count(snapshot, node_ref)
            >= DEVELOPER_COORDINATOR_NODE_WIP_LIMIT
        ):
            return None
        if self._global_claim_count(snapshot) >= DEVELOPER_COORDINATOR_GLOBAL_WIP_LIMIT:
            return None
        exclusive_active = any(
            task.state == "claimed" and task.concurrency == "exclusive"
            for task in snapshot.tasks
        )
        active_lanes = {
            task.wip_lane for task in snapshot.tasks if task.state == "claimed"
        }
        candidates = sorted(
            snapshot.tasks,
            key=lambda task: (
                task.queue_order,
                _priority_rank(task.priority),
                task.task_ref,
            ),
        )
        for task in candidates:
            if task.state != "queued" or not self._dependencies_complete(
                snapshot, task
            ):
                continue
            if task.concurrency == "exclusive" and exclusive_active:
                continue
            if task.wip_lane in active_lanes:
                continue
            return task
        return None

    @staticmethod
    def _dependencies_complete(
        snapshot: DeveloperWorkQueueSnapshot,
        task: DeveloperWorkTask,
    ) -> bool:
        by_ref = {candidate.task_ref: candidate for candidate in snapshot.tasks}
        return all(
            by_ref[ref].state == "completed" for ref in task.depends_on_task_refs
        )

    @staticmethod
    def _archive_ready(task: DeveloperWorkTask) -> bool:
        return (
            task.state in {"completed", "canceled"}
            and task.terminal_scope_packet_ref is not None
            and (task.state == "canceled" or bool(task.completion_evidence_refs))
        )

    @staticmethod
    def _node_claim_count(snapshot: DeveloperWorkQueueSnapshot, node_ref: str) -> int:
        return sum(
            1
            for task in snapshot.tasks
            if task.state == "claimed" and task.owner_node_ref == node_ref
        )

    @staticmethod
    def _global_claim_count(snapshot: DeveloperWorkQueueSnapshot) -> int:
        return sum(1 for task in snapshot.tasks if task.state == "claimed")

    @staticmethod
    def _find_task(
        snapshot: DeveloperWorkQueueSnapshot, task_ref: str
    ) -> DeveloperWorkTask:
        for task in snapshot.tasks:
            if task.task_ref == task_ref:
                return task
        raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_TASK_NOT_FOUND")

    @staticmethod
    def _find_node(
        snapshot: DeveloperWorkQueueSnapshot, node_ref: str
    ) -> DeveloperWorkNode:
        for node in snapshot.nodes:
            if node.node_ref == node_ref:
                return node
        raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_NODE_NOT_REGISTERED")

    @staticmethod
    def _replace_task(
        snapshot: DeveloperWorkQueueSnapshot,
        replacement: DeveloperWorkTask,
    ) -> list[DeveloperWorkTask]:
        return [
            replacement if task.task_ref == replacement.task_ref else task
            for task in snapshot.tasks
        ]

    @staticmethod
    def _replace_node(
        snapshot: DeveloperWorkQueueSnapshot,
        replacement: DeveloperWorkNode,
    ) -> list[DeveloperWorkNode]:
        return [
            replacement if node.node_ref == replacement.node_ref else node
            for node in snapshot.nodes
        ]

    def _receipt(
        self,
        *,
        event_kind: DeveloperWorkEventKind,
        idempotency_ref: str,
        payload: dict[str, object],
        revision: int,
        safe_summary: str,
        task_ref: str | None = None,
        node_ref: str | None = None,
    ) -> DeveloperWorkQueueReceipt:
        payload_fingerprint_ref = _hash_ref("developer-work-payload-ref", payload)
        return DeveloperWorkQueueReceipt(
            receipt_ref=_hash_ref(
                "developer-work-receipt-ref",
                {
                    "event_kind": event_kind,
                    "idempotency_ref": idempotency_ref,
                    "payload": payload,
                },
            ),
            event_kind=event_kind,
            task_ref=task_ref,
            node_ref=node_ref,
            idempotency_ref=idempotency_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            revision=revision,
            occurred_at_ref=_hash_ref("time-ref", utc_now().isoformat()),
            safe_summary=safe_summary,
        )

    def _load_snapshot(self) -> DeveloperWorkQueueSnapshot:
        if not self.state_path.exists():
            return DeveloperWorkQueueSnapshot()
        return DeveloperWorkQueueSnapshot.model_validate_json(
            self.state_path.read_text(encoding="utf-8")
        )

    def _commit_mutation(
        self,
        snapshot: DeveloperWorkQueueSnapshot,
        receipt: DeveloperWorkQueueReceipt,
    ) -> None:
        """Durably prepare and recover one snapshot/receipt transaction."""

        validated_snapshot = DeveloperWorkQueueSnapshot.model_validate(
            snapshot.model_dump(mode="json")
        )
        transaction = DeveloperWorkQueuePendingTransaction(
            snapshot=validated_snapshot,
            receipt=receipt,
        )
        self._write_pending_transaction(transaction)
        self._write_snapshot(validated_snapshot)
        self._append_receipt(receipt)
        self._clear_pending_transaction()

    def _write_snapshot(self, snapshot: DeveloperWorkQueueSnapshot) -> None:
        validated = DeveloperWorkQueueSnapshot.model_validate(
            snapshot.model_dump(mode="json")
        )
        self._atomic_write_text(
            self.state_path,
            json.dumps(validated.model_dump(mode="json"), indent=2, sort_keys=True)
            + "\n",
        )

    def _append_receipt(self, receipt: DeveloperWorkQueueReceipt) -> None:
        receipts = self._load_receipts()
        for existing in receipts:
            if existing.receipt_ref == receipt.receipt_ref:
                if existing.model_dump(mode="json") != receipt.model_dump(mode="json"):
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_RECEIPT_REF_CONFLICT"
                    )
                return
            if existing.idempotency_ref == receipt.idempotency_ref:
                raise DeveloperWorkQueueConflictError(
                    "DEVELOPER_WORK_IDEMPOTENCY_CONFLICT"
                )
        lines = [
            json.dumps(item.model_dump(mode="json"), sort_keys=True)
            for item in [*receipts, receipt]
        ]
        self._atomic_write_text(self.receipts_path, "\n".join(lines) + "\n")

    def _load_receipts(self) -> list[DeveloperWorkQueueReceipt]:
        if not self.receipts_path.exists():
            return []
        receipts: list[DeveloperWorkQueueReceipt] = []
        for line in self.receipts_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                receipts.append(DeveloperWorkQueueReceipt.model_validate_json(line))
        return receipts

    def _write_pending_transaction(
        self,
        transaction: DeveloperWorkQueuePendingTransaction,
    ) -> None:
        self._atomic_write_text(
            self.pending_transaction_path,
            json.dumps(transaction.model_dump(mode="json"), indent=2, sort_keys=True)
            + "\n",
        )

    def _recover_pending_transaction(self) -> None:
        if not self.pending_transaction_path.exists():
            return
        try:
            transaction = DeveloperWorkQueuePendingTransaction.model_validate_json(
                self.pending_transaction_path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as error:
            raise DeveloperWorkQueueError(
                "DEVELOPER_WORK_PENDING_TRANSACTION_INVALID"
            ) from error
        self._write_snapshot(transaction.snapshot)
        self._append_receipt(transaction.receipt)
        self._clear_pending_transaction()

    def _clear_pending_transaction(self) -> None:
        if self.pending_transaction_path.exists():
            self.pending_transaction_path.unlink()
            self._fsync_state_dir()

    def _atomic_write_text(self, path: Path, payload: str) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        temporary_path = self.state_dir / f".{path.name}.tmp"
        with temporary_path.open("w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        self._fsync_state_dir()

    def _fsync_state_dir(self) -> None:
        directory_fd = os.open(self.state_dir, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)

    def _replay(
        self,
        *,
        idempotency_ref: str,
        payload: dict[str, object],
    ) -> DeveloperWorkQueueReceipt | None:
        expected_fingerprint = _hash_ref("developer-work-payload-ref", payload)
        for receipt in self._load_receipts():
            if receipt.idempotency_ref != idempotency_ref:
                continue
            if receipt.payload_fingerprint_ref != expected_fingerprint:
                raise DeveloperWorkQueueConflictError(
                    "DEVELOPER_WORK_IDEMPOTENCY_CONFLICT"
                )
            return receipt.model_copy(update={"replayed": True})
        return None

    def _replay_claim_next(
        self,
        *,
        idempotency_ref: str,
        node_ref: str,
    ) -> DeveloperWorkQueueReceipt | None:
        """Replay a claim-next receipt before selecting a different later task."""

        for receipt in self._load_receipts():
            if receipt.idempotency_ref != idempotency_ref:
                continue
            if receipt.event_kind != "task_claimed" or receipt.node_ref != node_ref:
                raise DeveloperWorkQueueConflictError(
                    "DEVELOPER_WORK_IDEMPOTENCY_CONFLICT"
                )
            return receipt.model_copy(update={"replayed": True})
        return None

    @contextmanager
    def _locked(self) -> Iterator[None]:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+", encoding="utf-8") as handle:
            try:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                self._recover_pending_transaction()
                yield
            finally:
                try:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass
