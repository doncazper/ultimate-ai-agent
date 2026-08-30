from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
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
REPO_ROOT = Path(__file__).resolve().parents[3]
FULL_MERGE_COMMIT_REF_RE = re.compile(r"^merge-commit-ref:([0-9a-f]{40})$")
MERGE_EVIDENCE_TARGET_REF = "refs/remotes/origin/main"
MERGE_GATED_BLOCKER_PR_RE = re.compile(r"(?:^|[/:_-])pr([0-9]+)(?:[/:_-]|$)")
DEVELOPER_WORK_TASK_AMENDMENT_ACTION = "amend_developer_queue_contract"
DEVELOPER_QUEUE_ADMISSION_ACTION = "admit_developer_queue_contracts"
DEVELOPER_WORK_COMPLETED_MIGRATION_ACTION = "migrate_completed_developer_queue_contract"
DEVELOPER_QUEUE_RECONCILIATION_ACTION = "reconcile_developer_queue_contracts"

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
    "tasks_admitted",
    "task_amended",
    "task_contract_migrated",
    "queue_contracts_reconciled",
    "queue_contracts_invalidated",
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


def _actor_scope_binding(actor_context: ActorContext) -> dict[str, object]:
    """Bind stable actor authority fields without transient construction time."""

    return actor_context.model_dump(mode="json", exclude={"created_at"})


def build_developer_work_task_amendment_approval_request(
    draft: "DeveloperWorkTaskDraft",
    *,
    expected_current_fingerprint_ref: str,
    expected_current_task_revision_ref: str,
    idempotency_ref: str,
    actor_context: ActorContext,
) -> ApprovalRequest:
    """Build the exact local approval scope for one queued-contract amendment."""

    validate_task_ref(
        expected_current_fingerprint_ref,
        "developer_work_amend_expected_fingerprint_ref",
    )
    validate_task_ref(
        expected_current_task_revision_ref,
        "developer_work_amend_expected_task_revision_ref",
    )
    validate_task_ref(idempotency_ref, "developer_work_amend_idempotency_ref")
    scope_ref = _hash_ref(
        "developer-work-amendment-scope-ref",
        {
            "task_ref": draft.task_ref,
            "expected_current_fingerprint_ref": expected_current_fingerprint_ref,
            "expected_current_task_revision_ref": (expected_current_task_revision_ref),
            "replacement_fingerprint_ref": draft.canonical_source_fingerprint_ref,
            "replacement_contract": draft.model_dump(mode="json"),
            "idempotency_ref": idempotency_ref,
            "actor_context": _actor_scope_binding(actor_context),
        },
    )
    return ApprovalRequest(
        approval_request_id=_hash_ref(
            "approval-request-ref",
            {"action": DEVELOPER_WORK_TASK_AMENDMENT_ACTION, "scope_ref": scope_ref},
        ),
        run_id=idempotency_ref,
        subject_type=ApprovalSubjectType.external_action,
        subject_id=draft.task_ref,
        actor_context=actor_context,
        requested_action=DEVELOPER_WORK_TASK_AMENDMENT_ACTION,
        purpose="Amend one pristine queued developer contract under exact local scope.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="local_developer_work_coordinator",
            reason="The authoritative local developer queue is project-private state.",
            allowed_sinks=["local_developer_work_coordinator"],
            forbidden_sinks=["provider", "public_network"],
            requires_redaction=True,
        ),
        resource_refs=[
            scope_ref,
            draft.task_ref,
            expected_current_fingerprint_ref,
            expected_current_task_revision_ref,
            draft.canonical_source_fingerprint_ref,
        ],
    )


def build_developer_queue_admission_approval_request(
    drafts: list["DeveloperWorkTaskDraft"],
    *,
    expected_snapshot_revision: int,
    idempotency_ref: str,
    actor_context: ActorContext,
) -> ApprovalRequest:
    """Build exact approval for one atomic canonical Queue V2 admission."""

    if expected_snapshot_revision < 0:
        raise ValueError("developer queue admission revision is invalid")
    if not drafts:
        raise ValueError("developer queue admission requires at least one task")
    validate_task_ref(idempotency_ref, "developer_queue_admission_idempotency_ref")
    task_refs = [draft.task_ref for draft in drafts]
    if len(task_refs) != len(set(task_refs)):
        raise ValueError("developer queue admission task refs must be unique")
    scope_ref = _hash_ref(
        "developer-queue-admission-scope-ref",
        {
            "drafts": [draft.model_dump(mode="json") for draft in drafts],
            "expected_snapshot_revision": expected_snapshot_revision,
            "idempotency_ref": idempotency_ref,
            "actor_context": _actor_scope_binding(actor_context),
        },
    )
    return ApprovalRequest(
        approval_request_id=_hash_ref(
            "approval-request-ref",
            {"action": DEVELOPER_QUEUE_ADMISSION_ACTION, "scope_ref": scope_ref},
        ),
        run_id=idempotency_ref,
        subject_type=ApprovalSubjectType.external_action,
        subject_id=DEVELOPER_COORDINATOR_REF,
        actor_context=actor_context,
        requested_action=DEVELOPER_QUEUE_ADMISSION_ACTION,
        purpose="Admit exact canonical Queue V2 contracts to the local ledger.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="local_developer_work_coordinator",
            reason="The authoritative local developer queue is project-private state.",
            allowed_sinks=["local_developer_work_coordinator"],
            forbidden_sinks=["provider", "public_network"],
            requires_redaction=True,
        ),
        resource_refs=[scope_ref, DEVELOPER_COORDINATOR_REF, *task_refs],
    )


def build_developer_work_completed_migration_approval_request(
    draft: "DeveloperWorkTaskDraft",
    *,
    expected_current_fingerprint_ref: str,
    expected_current_task_revision_ref: str,
    migration_evidence_ref: str,
    idempotency_ref: str,
    actor_context: ActorContext,
) -> ApprovalRequest:
    """Build exact approval for one completed canonical-contract migration."""

    for value, field_name in [
        (expected_current_fingerprint_ref, "completed_migration_fingerprint_ref"),
        (expected_current_task_revision_ref, "completed_migration_task_revision_ref"),
        (migration_evidence_ref, "completed_migration_evidence_ref"),
        (idempotency_ref, "completed_migration_idempotency_ref"),
    ]:
        validate_task_ref(value, field_name)
    scope_ref = _hash_ref(
        "developer-work-completed-migration-scope-ref",
        {
            "task_ref": draft.task_ref,
            "expected_current_fingerprint_ref": expected_current_fingerprint_ref,
            "expected_current_task_revision_ref": expected_current_task_revision_ref,
            "replacement_contract": draft.model_dump(mode="json"),
            "migration_evidence_ref": migration_evidence_ref,
            "idempotency_ref": idempotency_ref,
            "actor_context": _actor_scope_binding(actor_context),
        },
    )
    return ApprovalRequest(
        approval_request_id=_hash_ref(
            "approval-request-ref",
            {
                "action": DEVELOPER_WORK_COMPLETED_MIGRATION_ACTION,
                "scope_ref": scope_ref,
            },
        ),
        run_id=idempotency_ref,
        subject_type=ApprovalSubjectType.external_action,
        subject_id=draft.task_ref,
        actor_context=actor_context,
        requested_action=DEVELOPER_WORK_COMPLETED_MIGRATION_ACTION,
        purpose="Migrate one completed canonical contract under exact evidence.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="local_developer_work_coordinator",
            reason="Completed canonical queue evidence is project-private state.",
            allowed_sinks=["local_developer_work_coordinator"],
            forbidden_sinks=["provider", "public_network"],
            requires_redaction=True,
        ),
        resource_refs=[
            scope_ref,
            draft.task_ref,
            expected_current_fingerprint_ref,
            expected_current_task_revision_ref,
            migration_evidence_ref,
        ],
    )


def developer_work_task_revision_ref(task: "DeveloperWorkTask") -> str:
    """Fingerprint the exact durable task state used by an amendment preview."""

    return _hash_ref("developer-work-task-revision-ref", task.model_dump(mode="json"))


def build_developer_queue_reconciliation_approval_request(
    *,
    canonical_contract_refs: dict[str, str],
    task_revision_refs: dict[str, str],
    legacy_transition_refs: dict[str, str],
    legacy_source_refs: dict[str, list[str]],
    expected_snapshot_revision: int,
    idempotency_ref: str,
    actor_context: ActorContext,
) -> ApprovalRequest:
    """Build exact approval for one durable canonical queue reconciliation."""

    if expected_snapshot_revision < 0:
        raise ValueError("developer queue reconciliation revision is invalid")
    validate_task_ref(idempotency_ref, "developer_queue_reconcile_idempotency_ref")
    payload = {
        "canonical_contract_refs": canonical_contract_refs,
        "task_revision_refs": task_revision_refs,
        "legacy_transition_refs": legacy_transition_refs,
        "legacy_source_refs": legacy_source_refs,
        "expected_snapshot_revision": expected_snapshot_revision,
        "idempotency_ref": idempotency_ref,
        "actor_context": _actor_scope_binding(actor_context),
    }
    scope_ref = _hash_ref("developer-queue-reconciliation-scope-ref", payload)
    return ApprovalRequest(
        approval_request_id=_hash_ref(
            "approval-request-ref",
            {"action": DEVELOPER_QUEUE_RECONCILIATION_ACTION, "scope_ref": scope_ref},
        ),
        run_id=idempotency_ref,
        subject_type=ApprovalSubjectType.external_action,
        subject_id=DEVELOPER_COORDINATOR_REF,
        actor_context=actor_context,
        requested_action=DEVELOPER_QUEUE_RECONCILIATION_ACTION,
        purpose="Reconcile exact canonical queue contracts for local claim readiness.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="local_developer_work_coordinator",
            reason="Canonical developer queue claim readiness is project-private state.",
            allowed_sinks=["local_developer_work_coordinator"],
            forbidden_sinks=["provider", "public_network"],
            requires_redaction=True,
        ),
        resource_refs=[scope_ref, DEVELOPER_COORDINATOR_REF],
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


def _validate_unblock_evidence(*, expected_blocker_ref: str, evidence_ref: str) -> None:
    merge_gated = "merge" in expected_blocker_ref and "pending" in expected_blocker_ref
    match = FULL_MERGE_COMMIT_REF_RE.fullmatch(evidence_ref)
    if merge_gated and match is None:
        raise DeveloperWorkQueueClaimError(
            "DEVELOPER_WORK_UNBLOCK_MERGE_COMMIT_EVIDENCE_REQUIRED"
        )
    if match is None:
        return
    pull_request_match = MERGE_GATED_BLOCKER_PR_RE.search(expected_blocker_ref)
    if merge_gated and pull_request_match is None:
        raise DeveloperWorkQueueClaimError(
            "DEVELOPER_WORK_UNBLOCK_MERGE_SUBJECT_REQUIRED"
        )
    revision = match.group(1)
    object_check = subprocess.run(
        ["git", "cat-file", "-e", f"{revision}^{{commit}}"],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    ancestry_check = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            revision,
            MERGE_EVIDENCE_TARGET_REF,
        ],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    message_check = subprocess.run(
        ["git", "log", "-1", "--format=%B", revision],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    expected_pr_marker = (
        None
        if pull_request_match is None
        else re.compile(
            rf"(?:\(#{pull_request_match.group(1)}\)\s*$|^Merge pull request #{pull_request_match.group(1)}\b)",
            re.MULTILINE,
        )
    )
    if (
        object_check.returncode != 0
        or ancestry_check.returncode != 0
        or message_check.returncode != 0
        or (
            expected_pr_marker is not None
            and expected_pr_marker.search(message_check.stdout) is None
        )
    ):
        raise DeveloperWorkQueueClaimError(
            "DEVELOPER_WORK_UNBLOCK_MERGE_COMMIT_EVIDENCE_INVALID"
        )


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
    canonical_source_refs: list[str] = Field(default_factory=list)
    canonical_item_contract_ref: str | None = None
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
                *self.canonical_source_refs,
                *(
                    [self.canonical_item_contract_ref]
                    if self.canonical_item_contract_ref is not None
                    else []
                ),
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
    dependency_contract_refs: dict[str, str] = Field(default_factory=dict)
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
                *self.dependency_contract_refs.keys(),
                *self.dependency_contract_refs.values(),
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
        if not set(self.dependency_contract_refs).issubset(
            set(self.depends_on_task_refs)
        ):
            raise ValueError("developer dependency contract ref is not a dependency")
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
    canonical_queue_contract_refs: dict[str, str] = Field(default_factory=dict)
    canonical_queue_task_revision_refs: dict[str, str] = Field(default_factory=dict)
    canonical_queue_legacy_transition_refs: dict[str, str] = Field(default_factory=dict)
    canonical_queue_legacy_source_refs: dict[str, list[str]] = Field(
        default_factory=dict
    )
    canonical_queue_reconciliation_ref: str | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_snapshot(self) -> "DeveloperWorkQueueSnapshot":
        _validate_refs(
            [
                self.contract_ref,
                self.coordinator_ref,
                *self.canonical_queue_contract_refs.keys(),
                *self.canonical_queue_contract_refs.values(),
                *self.canonical_queue_task_revision_refs.keys(),
                *self.canonical_queue_task_revision_refs.values(),
                *self.canonical_queue_legacy_transition_refs.keys(),
                *self.canonical_queue_legacy_transition_refs.values(),
                *self.canonical_queue_legacy_source_refs.keys(),
                *(
                    source_ref
                    for source_refs in self.canonical_queue_legacy_source_refs.values()
                    for source_ref in source_refs
                ),
                *(
                    [self.canonical_queue_reconciliation_ref]
                    if self.canonical_queue_reconciliation_ref is not None
                    else []
                ),
            ],
            "developer_work_snapshot_ref",
        )
        task_refs = [task.task_ref for task in self.tasks]
        if len(task_refs) != len(set(task_refs)):
            raise ValueError("developer work queue task refs must be unique")
        node_refs = [node.node_ref for node in self.nodes]
        if len(node_refs) != len(set(node_refs)):
            raise ValueError("developer work queue node refs must be unique")
        known = set(task_refs)
        reconciliation_key_sets = {
            frozenset(self.canonical_queue_contract_refs),
            frozenset(self.canonical_queue_task_revision_refs),
        }
        if len(reconciliation_key_sets) != 1:
            raise ValueError("developer queue reconciliation key sets differ")
        if not set(self.canonical_queue_legacy_transition_refs).issubset(
            set(self.canonical_queue_contract_refs)
        ):
            raise ValueError("developer queue legacy reconciliation ref is orphaned")
        if set(self.canonical_queue_legacy_source_refs) != set(
            self.canonical_queue_legacy_transition_refs
        ):
            raise ValueError("developer queue legacy source reconciliation differs")
        if not set(self.canonical_queue_contract_refs).issubset(known):
            raise ValueError("developer queue reconciliation task is missing")
        if self.canonical_queue_contract_refs and (
            self.canonical_queue_reconciliation_ref is None
        ):
            raise ValueError("developer queue reconciliation ref is missing")
        if self.canonical_queue_reconciliation_ref is not None and not (
            self.canonical_queue_contract_refs
        ):
            raise ValueError("developer queue reconciliation ref is orphaned")
        if self.canonical_queue_reconciliation_ref is not None:
            expected_reconciliation_ref = _hash_ref(
                "developer-queue-reconciliation-ref",
                {
                    "canonical_contract_refs": self.canonical_queue_contract_refs,
                    "task_revision_refs": self.canonical_queue_task_revision_refs,
                    "legacy_transition_refs": (
                        self.canonical_queue_legacy_transition_refs
                    ),
                    "legacy_source_refs": self.canonical_queue_legacy_source_refs,
                },
            )
            if self.canonical_queue_reconciliation_ref != expected_reconciliation_ref:
                raise ValueError("developer queue reconciliation ref is not bound")
            canonical_tasks = {
                task.task_ref: task
                for task in self.tasks
                if (
                    task.task_ref.startswith("dev-task:queue-v2-")
                    or task.canonical_task_ref.startswith(
                        "canonical-task-ref:queue-v2/"
                    )
                    or task.canonical_source_ref.startswith(
                        "repo-ref:developer-queue-v2/"
                    )
                )
            }
            if set(self.canonical_queue_contract_refs) != set(canonical_tasks):
                raise ValueError("developer queue reconciliation is incomplete")
            expected_legacy_refs = {
                task_ref
                for task_ref, task in canonical_tasks.items()
                if task.canonical_item_contract_ref is None
            }
            if set(self.canonical_queue_legacy_transition_refs) != (
                expected_legacy_refs
            ):
                raise ValueError("developer queue legacy reconciliation is incomplete")
            from uaa_developer_orchestrator.queue_record import (
                queue_record_canonical_item_contract_ref,
                queue_record_legacy_source_acceptance_ref_from_values,
            )

            for (
                task_ref,
                transition_ref,
            ) in self.canonical_queue_legacy_transition_refs.items():
                task = canonical_tasks[task_ref]
                source_refs = self.canonical_queue_legacy_source_refs[task_ref]
                item_id = task.canonical_task_ref.rsplit("/", maxsplit=1)[-1]
                expected_transition_ref = (
                    queue_record_legacy_source_acceptance_ref_from_values(
                        item_id=item_id,
                        task_ref=task_ref,
                        source_refs=source_refs,
                        legacy_fingerprint_ref=(task.canonical_source_fingerprint_ref),
                    )
                )
                expected_contract_ref = queue_record_canonical_item_contract_ref(
                    task.model_copy(update={"canonical_source_refs": source_refs})
                )
                if (
                    transition_ref != expected_transition_ref
                    or self.canonical_queue_contract_refs[task_ref]
                    != expected_contract_ref
                ):
                    raise ValueError(
                        "developer queue legacy reconciliation binding is invalid"
                    )
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
    approval_ref: str | None = None
    approval_scope_ref: str | None = None
    approving_actor_ref: str | None = None
    prior_fingerprint_ref: str | None = None
    prior_task_revision_ref: str | None = None
    migration_evidence_ref: str | None = None
    migration_replacement_draft: DeveloperWorkTaskDraft | None = None
    migration_result_task: DeveloperWorkTask | None = None
    migration_result_task_revision_ref: str | None = None
    migration_contract_evidence_ref: str | None = None
    admission_snapshot_revision: int | None = Field(default=None, ge=0)
    admission_drafts: list[DeveloperWorkTaskDraft] = Field(default_factory=list)
    admission_evidence_ref: str | None = None
    reconciliation_ref: str | None = None
    reconciliation_snapshot_revision: int | None = Field(default=None, ge=0)
    reconciliation_contract_refs: dict[str, str] = Field(default_factory=dict)
    reconciliation_task_revision_refs: dict[str, str] = Field(default_factory=dict)
    reconciliation_legacy_transition_refs: dict[str, str] = Field(default_factory=dict)
    reconciliation_legacy_source_refs: dict[str, list[str]] = Field(
        default_factory=dict
    )
    reconciliation_evidence_ref: str | None = None
    approval_proof_ref: str | None = None

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
                *([self.approval_ref] if self.approval_ref is not None else []),
                *(
                    [self.approval_scope_ref]
                    if self.approval_scope_ref is not None
                    else []
                ),
                *(
                    [self.approving_actor_ref]
                    if self.approving_actor_ref is not None
                    else []
                ),
                *(
                    [self.prior_fingerprint_ref]
                    if self.prior_fingerprint_ref is not None
                    else []
                ),
                *(
                    [self.prior_task_revision_ref]
                    if self.prior_task_revision_ref is not None
                    else []
                ),
                *(
                    [self.migration_evidence_ref]
                    if self.migration_evidence_ref is not None
                    else []
                ),
                *(
                    [self.migration_result_task_revision_ref]
                    if self.migration_result_task_revision_ref is not None
                    else []
                ),
                *(
                    [self.migration_contract_evidence_ref]
                    if self.migration_contract_evidence_ref is not None
                    else []
                ),
                *(
                    [self.admission_evidence_ref]
                    if self.admission_evidence_ref is not None
                    else []
                ),
                *(
                    [self.reconciliation_ref]
                    if self.reconciliation_ref is not None
                    else []
                ),
                *self.reconciliation_contract_refs.keys(),
                *self.reconciliation_contract_refs.values(),
                *self.reconciliation_task_revision_refs.keys(),
                *self.reconciliation_task_revision_refs.values(),
                *self.reconciliation_legacy_transition_refs.keys(),
                *self.reconciliation_legacy_transition_refs.values(),
                *self.reconciliation_legacy_source_refs.keys(),
                *(
                    source_ref
                    for source_refs in self.reconciliation_legacy_source_refs.values()
                    for source_ref in source_refs
                ),
                *(
                    [self.reconciliation_evidence_ref]
                    if self.reconciliation_evidence_ref is not None
                    else []
                ),
                *(
                    [self.approval_proof_ref]
                    if self.approval_proof_ref is not None
                    else []
                ),
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
        reconciliation_event = self.event_kind in {
            "queue_contracts_reconciled",
            "queue_contracts_invalidated",
        }
        if self.event_kind != "task_contract_migrated" and any(
            [
                self.migration_replacement_draft is not None,
                self.migration_result_task is not None,
                self.migration_result_task_revision_ref is not None,
                self.migration_contract_evidence_ref is not None,
            ]
        ):
            raise ValueError("developer queue migration contract evidence is orphaned")
        if reconciliation_event:
            if (
                self.admission_snapshot_revision is not None
                or self.admission_drafts
                or self.admission_evidence_ref is not None
            ):
                raise ValueError("developer queue admission evidence is orphaned")
            if self.reconciliation_snapshot_revision is None:
                raise ValueError(
                    "developer queue reconciliation evidence is incomplete"
                )
            if not self.reconciliation_contract_refs or set(
                self.reconciliation_contract_refs
            ) != set(self.reconciliation_task_revision_refs):
                raise ValueError(
                    "developer queue reconciliation evidence is incomplete"
                )
            if set(self.reconciliation_legacy_transition_refs) != set(
                self.reconciliation_legacy_source_refs
            ):
                raise ValueError(
                    "developer queue reconciliation evidence is incomplete"
                )
            if self.event_kind == "queue_contracts_reconciled" and (
                self.reconciliation_ref is None
            ):
                raise ValueError("developer queue reconciliation result ref is missing")
            if self.event_kind == "queue_contracts_invalidated" and (
                self.reconciliation_ref is not None
            ):
                raise ValueError("developer queue invalidation retained a result ref")
            evidence = {
                "canonical_contract_refs": self.reconciliation_contract_refs,
                "task_revision_refs": self.reconciliation_task_revision_refs,
                "legacy_transition_refs": (self.reconciliation_legacy_transition_refs),
                "legacy_source_refs": self.reconciliation_legacy_source_refs,
                "expected_snapshot_revision": (self.reconciliation_snapshot_revision),
                "reconciliation_ref": self.reconciliation_ref,
            }
            if self.reconciliation_evidence_ref != _hash_ref(
                "developer-queue-reconciliation-evidence-ref", evidence
            ):
                raise ValueError("developer queue reconciliation evidence is not bound")
            proof_values = {
                "approval_ref": self.approval_ref,
                "approval_scope_ref": self.approval_scope_ref,
                "approving_actor_ref": self.approving_actor_ref,
                "reconciliation_evidence_ref": self.reconciliation_evidence_ref,
            }
        else:
            orphaned_reconciliation_evidence = any(
                [
                    self.reconciliation_ref is not None,
                    self.reconciliation_snapshot_revision is not None,
                    bool(self.reconciliation_contract_refs),
                    bool(self.reconciliation_task_revision_refs),
                    bool(self.reconciliation_legacy_transition_refs),
                    bool(self.reconciliation_legacy_source_refs),
                    self.reconciliation_evidence_ref is not None,
                ]
            )
            if orphaned_reconciliation_evidence:
                raise ValueError("developer queue reconciliation evidence is orphaned")
            if self.event_kind == "tasks_admitted":
                if any(
                    value is not None
                    for value in [
                        self.prior_fingerprint_ref,
                        self.prior_task_revision_ref,
                        self.migration_evidence_ref,
                    ]
                ):
                    raise ValueError(
                        "developer queue admission receipt evidence is orphaned"
                    )
                admission_evidence_present = (
                    self.admission_snapshot_revision is not None
                    or bool(self.admission_drafts)
                    or self.admission_evidence_ref is not None
                )
                if admission_evidence_present and (
                    self.admission_snapshot_revision is None
                    or not self.admission_drafts
                    or self.admission_evidence_ref is None
                ):
                    raise ValueError(
                        "developer queue admission receipt evidence is incomplete"
                    )
                if self.admission_evidence_ref is not None:
                    admission_evidence = {
                        "drafts": [
                            draft.model_dump(mode="json")
                            for draft in self.admission_drafts
                        ],
                        "expected_snapshot_revision": (
                            self.admission_snapshot_revision
                        ),
                    }
                    if self.admission_evidence_ref != _hash_ref(
                        "developer-queue-admission-evidence-ref",
                        admission_evidence,
                    ):
                        raise ValueError(
                            "developer queue admission evidence is not bound"
                        )
                proof_values = {
                    "approval_ref": self.approval_ref,
                    "approval_scope_ref": self.approval_scope_ref,
                    "approving_actor_ref": self.approving_actor_ref,
                    **(
                        {"admission_evidence_ref": self.admission_evidence_ref}
                        if self.admission_evidence_ref is not None
                        else {}
                    ),
                }
            elif self.event_kind == "task_contract_migrated":
                if (
                    self.admission_snapshot_revision is not None
                    or self.admission_drafts
                    or self.admission_evidence_ref is not None
                ):
                    raise ValueError("developer queue admission evidence is orphaned")
                migration_contract_evidence_present = any(
                    [
                        self.migration_replacement_draft is not None,
                        self.migration_result_task is not None,
                        self.migration_result_task_revision_ref is not None,
                        self.migration_contract_evidence_ref is not None,
                    ]
                )
                if migration_contract_evidence_present and (
                    self.migration_replacement_draft is None
                    or self.migration_result_task is None
                    or self.migration_result_task_revision_ref is None
                    or self.migration_contract_evidence_ref is None
                ):
                    raise ValueError(
                        "developer queue migration contract evidence is incomplete"
                    )
                if self.migration_contract_evidence_ref is not None:
                    migration_contract_evidence = {
                        "replacement_draft": (
                            self.migration_replacement_draft.model_dump(mode="json")
                        ),
                        "result_task": self.migration_result_task.model_dump(
                            mode="json"
                        ),
                        "result_task_revision_ref": (
                            self.migration_result_task_revision_ref
                        ),
                    }
                    if self.migration_result_task_revision_ref != (
                        developer_work_task_revision_ref(self.migration_result_task)
                    ):
                        raise ValueError(
                            "developer queue migration result revision is not bound"
                        )
                    if self.migration_contract_evidence_ref != _hash_ref(
                        "developer-queue-migration-contract-evidence-ref",
                        migration_contract_evidence,
                    ):
                        raise ValueError(
                            "developer queue migration contract evidence is not bound"
                        )
                proof_values = {
                    "approval_ref": self.approval_ref,
                    "approval_scope_ref": self.approval_scope_ref,
                    "approving_actor_ref": self.approving_actor_ref,
                    "prior_fingerprint_ref": self.prior_fingerprint_ref,
                    "prior_task_revision_ref": self.prior_task_revision_ref,
                    "migration_evidence_ref": self.migration_evidence_ref,
                    **(
                        {
                            "migration_contract_evidence_ref": (
                                self.migration_contract_evidence_ref
                            )
                        }
                        if self.migration_contract_evidence_ref is not None
                        else {}
                    ),
                }
            else:
                if (
                    self.admission_snapshot_revision is not None
                    or self.admission_drafts
                    or self.admission_evidence_ref is not None
                ):
                    raise ValueError("developer queue admission evidence is orphaned")
                if self.migration_evidence_ref is not None:
                    raise ValueError("developer work migration evidence is orphaned")
                if any(
                    [
                        self.migration_replacement_draft is not None,
                        self.migration_result_task is not None,
                        self.migration_result_task_revision_ref is not None,
                        self.migration_contract_evidence_ref is not None,
                    ]
                ):
                    raise ValueError(
                        "developer queue migration contract evidence is orphaned"
                    )
                proof_values = {
                    "approval_ref": self.approval_ref,
                    "approval_scope_ref": self.approval_scope_ref,
                    "approving_actor_ref": self.approving_actor_ref,
                    "prior_fingerprint_ref": self.prior_fingerprint_ref,
                    "prior_task_revision_ref": self.prior_task_revision_ref,
                }
        populated_proof_values = [
            value for value in proof_values.values() if value is not None
        ]
        if self.event_kind == "task_amended" and len(populated_proof_values) != len(
            proof_values
        ):
            raise ValueError(
                "developer work amendment receipt approval proof is required"
            )
        if self.event_kind in {"tasks_admitted", "task_contract_migrated"} and len(
            populated_proof_values
        ) != len(proof_values):
            raise ValueError(
                "developer queue mutation receipt approval proof is required"
            )
        if reconciliation_event and len(populated_proof_values) != len(proof_values):
            raise ValueError(
                "developer queue reconciliation receipt approval proof is required"
            )
        if populated_proof_values and len(populated_proof_values) != len(proof_values):
            raise ValueError("developer work receipt approval proof is incomplete")
        if populated_proof_values:
            expected_proof_ref = _hash_ref(
                "developer-work-approval-proof-ref", proof_values
            )
            if self.approval_proof_ref != expected_proof_ref:
                raise ValueError("developer work receipt approval proof is not bound")
        elif self.approval_proof_ref is not None:
            raise ValueError("developer work receipt approval proof is orphaned")
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
    canonical_source_refs: list[str] = Field(default_factory=list)
    canonical_item_contract_ref: str | None = None
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
    workstream_ref: str
    depends_on_task_refs: list[str] = Field(default_factory=list)
    dependency_contract_refs: dict[str, str] = Field(default_factory=dict)
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
    canonical_queue_reconciliation_ref: str | None = None
    canonical_queue_reconciled_task_refs: list[str] = Field(default_factory=list)
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
                    [self.canonical_queue_reconciliation_ref]
                    if self.canonical_queue_reconciliation_ref is not None
                    else []
                ),
                *self.canonical_queue_reconciled_task_refs,
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
            self._validate_canonical_queue_draft(draft)
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
            self._validate_canonical_dependencies_for_admission(snapshot, draft)
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
            dependency_contract_refs = {
                dependency_ref: self._durable_task_contract_ref(
                    self._find_task(snapshot, dependency_ref)
                )
                for dependency_ref in draft.depends_on_task_refs
            }
            task = DeveloperWorkTask(
                **draft.model_dump(mode="json"),
                dependency_contract_refs=dependency_contract_refs,
            )
            next_snapshot = snapshot.model_copy(
                update={
                    "revision": snapshot.revision + 1,
                    "tasks": [*snapshot.tasks, task],
                    **(
                        {
                            "canonical_queue_contract_refs": {},
                            "canonical_queue_task_revision_refs": {},
                            "canonical_queue_legacy_transition_refs": {},
                            "canonical_queue_legacy_source_refs": {},
                            "canonical_queue_reconciliation_ref": None,
                        }
                        if self._is_canonical_queue_task(task)
                        else {}
                    ),
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

    def admit_canonical_queue_tasks(
        self,
        drafts: list[DeveloperWorkTaskDraft],
        *,
        expected_snapshot_revision: int,
        idempotency_ref: str,
        approval_authority: LocalApprovalAuthority,
        approval_ref: str,
        actor_context: ActorContext,
    ) -> DeveloperWorkQueueReceipt:
        """Atomically admit exact canonical drafts under one exact local approval."""

        validate_task_ref(idempotency_ref, "developer_queue_admission_idempotency_ref")
        validate_task_ref(approval_ref, "developer_queue_admission_approval_ref")
        approval_request = build_developer_queue_admission_approval_request(
            drafts,
            expected_snapshot_revision=expected_snapshot_revision,
            idempotency_ref=idempotency_ref,
            actor_context=actor_context,
        )
        approval_scope_ref = approval_request.resource_refs[0]
        with approval_authority.hold_validation_lock():
            with self._locked():
                snapshot = self._load_snapshot()
                payload = {
                    "event_kind": "tasks_admitted",
                    "drafts": [draft.model_dump(mode="json") for draft in drafts],
                    "expected_snapshot_revision": expected_snapshot_revision,
                    "approval_ref": approval_ref,
                    "approval_scope_ref": approval_scope_ref,
                }
                replay = self._replay(
                    idempotency_ref=idempotency_ref,
                    payload=payload,
                )
                if replay is not None:
                    return replay
                if snapshot.revision != expected_snapshot_revision:
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_QUEUE_ADMISSION_REVISION_CONFLICT"
                    )
                approval = approval_authority.validate_for_request(
                    approval_request, approval_ref
                )
                approval_grant = approval_authority.get_grant(approval_ref)
                if not approval.allowed or approval_grant is None:
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_QUEUE_ADMISSION_APPROVAL_INVALID"
                    )
                working_snapshot = snapshot
                admitted: list[DeveloperWorkTask] = []
                for draft in drafts:
                    self._validate_canonical_queue_draft(draft)
                    if not self._is_canonical_queue_task(draft):
                        raise DeveloperWorkQueueConflictError(
                            "DEVELOPER_QUEUE_ADMISSION_NONCANONICAL_TASK"
                        )
                    if any(
                        task.task_ref == draft.task_ref
                        for task in working_snapshot.tasks
                    ):
                        raise DeveloperWorkQueueConflictError(
                            "DEVELOPER_WORK_TASK_REF_CONFLICT"
                        )
                    missing_dependencies = set(draft.depends_on_task_refs) - {
                        task.task_ref for task in working_snapshot.tasks
                    }
                    if missing_dependencies:
                        raise DeveloperWorkQueueConflictError(
                            "DEVELOPER_WORK_TASK_DEPENDENCY_MISSING"
                        )
                    self._validate_canonical_dependencies_for_admission(
                        working_snapshot, draft
                    )
                    if any(
                        task.state not in {"completed", "canceled"}
                        and task.branch_ref == draft.branch_ref
                        for task in working_snapshot.tasks
                    ):
                        raise DeveloperWorkQueueConflictError(
                            "DEVELOPER_WORK_BRANCH_REF_CONFLICT"
                        )
                    if any(
                        task.state not in {"completed", "canceled"}
                        and task.worktree_ref == draft.worktree_ref
                        for task in working_snapshot.tasks
                    ):
                        raise DeveloperWorkQueueConflictError(
                            "DEVELOPER_WORK_WORKTREE_REF_CONFLICT"
                        )
                    dependency_contract_refs = {
                        dependency_ref: self._durable_task_contract_ref(
                            self._find_task(working_snapshot, dependency_ref)
                        )
                        for dependency_ref in draft.depends_on_task_refs
                    }
                    task = DeveloperWorkTask(
                        **draft.model_dump(mode="json"),
                        dependency_contract_refs=dependency_contract_refs,
                    )
                    admitted.append(task)
                    working_snapshot = working_snapshot.model_copy(
                        update={"tasks": [*working_snapshot.tasks, task]}
                    )
                next_snapshot = working_snapshot.model_copy(
                    update={
                        "revision": snapshot.revision + 1,
                        "canonical_queue_contract_refs": {},
                        "canonical_queue_task_revision_refs": {},
                        "canonical_queue_legacy_transition_refs": {},
                        "canonical_queue_legacy_source_refs": {},
                        "canonical_queue_reconciliation_ref": None,
                    }
                )
                receipt = self._receipt(
                    event_kind="tasks_admitted",
                    idempotency_ref=idempotency_ref,
                    payload=payload,
                    revision=next_snapshot.revision,
                    safe_summary=(
                        "Exact canonical Queue V2 contracts were atomically admitted "
                        "under local approval; no work was claimed or dispatched."
                    ),
                    approval_ref=approval_ref,
                    approval_scope_ref=approval_scope_ref,
                    approving_actor_ref=_hash_ref(
                        "actor-ref", approval_grant.approved_by_actor_id
                    ),
                    admission_snapshot_revision=expected_snapshot_revision,
                    admission_drafts=drafts,
                )
                admitted_refs = {task.task_ref for task in admitted}
                next_snapshot = next_snapshot.model_copy(
                    update={
                        "tasks": [
                            task.model_copy(
                                update={"latest_receipt_ref": receipt.receipt_ref}
                            )
                            if task.task_ref in admitted_refs
                            else task
                            for task in next_snapshot.tasks
                        ]
                    }
                )
                self._commit_mutation(next_snapshot, receipt)
                return receipt

    def amend_queued_task(
        self,
        draft: DeveloperWorkTaskDraft,
        *,
        expected_current_fingerprint_ref: str,
        expected_current_task_revision_ref: str,
        idempotency_ref: str,
        approval_authority: LocalApprovalAuthority,
        approval_ref: str,
        actor_context: ActorContext,
    ) -> DeveloperWorkQueueReceipt:
        """Replace one never-claimed queued draft under exact source and approval."""

        validate_task_ref(
            expected_current_fingerprint_ref,
            "developer_work_amend_expected_fingerprint_ref",
        )
        validate_task_ref(
            expected_current_task_revision_ref,
            "developer_work_amend_expected_task_revision_ref",
        )
        validate_task_ref(idempotency_ref, "developer_work_amend_idempotency_ref")
        validate_task_ref(approval_ref, "developer_work_amend_approval_ref")
        approval_request = build_developer_work_task_amendment_approval_request(
            draft,
            expected_current_fingerprint_ref=expected_current_fingerprint_ref,
            expected_current_task_revision_ref=expected_current_task_revision_ref,
            idempotency_ref=idempotency_ref,
            actor_context=actor_context,
        )
        approval_scope_ref = approval_request.resource_refs[0]
        with approval_authority.hold_validation_lock():
            with self._locked():
                snapshot = self._load_snapshot()
                payload = {
                    "event_kind": "task_amended",
                    "expected_current_fingerprint_ref": (
                        expected_current_fingerprint_ref
                    ),
                    "expected_current_task_revision_ref": (
                        expected_current_task_revision_ref
                    ),
                    "approval_ref": approval_ref,
                    "approval_scope_ref": approval_scope_ref,
                    "draft": draft.model_dump(mode="json"),
                }
                replay = self._replay(
                    idempotency_ref=idempotency_ref,
                    payload=payload,
                )
                if replay is not None:
                    return replay
                self._validate_canonical_queue_draft(draft)
                approval = approval_authority.validate_for_request(
                    approval_request,
                    approval_ref,
                )
                if not approval.allowed:
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_TASK_AMENDMENT_APPROVAL_INVALID"
                    )
                approval_grant = approval_authority.get_grant(approval_ref)
                if approval_grant is None:
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_TASK_AMENDMENT_APPROVAL_INVALID"
                    )
                task = self._find_task(snapshot, draft.task_ref)
                if (
                    developer_work_task_revision_ref(task)
                    != expected_current_task_revision_ref
                ):
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_TASK_AMENDMENT_REVISION_CONFLICT"
                    )
                pristine_queued = (
                    task.state == "queued"
                    and task.claim_generation == 0
                    and task.latest_heartbeat_ref is None
                    and not task.blocker_refs
                    and not task.completion_evidence_refs
                    and task.cancellation_reason_ref is None
                    and task.terminal_scope_packet_ref is None
                    and not task.scope_dispositions
                )
                if not pristine_queued:
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_TASK_AMENDMENT_STATE_INVALID"
                    )
                if (
                    task.canonical_source_fingerprint_ref
                    != expected_current_fingerprint_ref
                ):
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_TASK_AMENDMENT_FINGERPRINT_CONFLICT"
                    )
                immutable_fields = (
                    "task_ref",
                    "queue_order",
                    "canonical_task_ref",
                    "canonical_source_ref",
                    "scope_contract_ref",
                    "branch_ref",
                    "worktree_ref",
                    "workstream_ref",
                )
                if any(
                    getattr(task, field) != getattr(draft, field)
                    for field in immutable_fields
                ):
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_TASK_AMENDMENT_IDENTITY_CONFLICT"
                    )
                if task.canonical_source_fingerprint_ref == (
                    draft.canonical_source_fingerprint_ref
                ):
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_TASK_AMENDMENT_NO_CHANGE"
                    )
                missing_dependencies = set(draft.depends_on_task_refs) - {
                    item.task_ref for item in snapshot.tasks
                }
                if missing_dependencies:
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_TASK_DEPENDENCY_MISSING"
                    )
                self._validate_canonical_dependencies_for_admission(snapshot, draft)
                dependency_contract_refs = {
                    dependency_ref: self._durable_task_contract_ref(
                        self._find_task(snapshot, dependency_ref)
                    )
                    for dependency_ref in draft.depends_on_task_refs
                }
                replacement = DeveloperWorkTask(
                    **draft.model_dump(mode="json"),
                    dependency_contract_refs=dependency_contract_refs,
                )
                next_snapshot = snapshot.model_copy(
                    update={
                        "revision": snapshot.revision + 1,
                        "tasks": self._replace_task(snapshot, replacement),
                        "canonical_queue_contract_refs": {},
                        "canonical_queue_task_revision_refs": {},
                        "canonical_queue_legacy_transition_refs": {},
                        "canonical_queue_legacy_source_refs": {},
                        "canonical_queue_reconciliation_ref": None,
                    }
                )
                receipt = self._receipt(
                    event_kind="task_amended",
                    task_ref=task.task_ref,
                    idempotency_ref=idempotency_ref,
                    payload=payload,
                    revision=next_snapshot.revision,
                    safe_summary=(
                        "A never-claimed queued task contract was amended under exact "
                        "local approval and its prior fingerprint; no work was claimed "
                        "or dispatched."
                    ),
                    approval_ref=approval_ref,
                    approval_scope_ref=approval_scope_ref,
                    approving_actor_ref=_hash_ref(
                        "actor-ref", approval_grant.approved_by_actor_id
                    ),
                    prior_fingerprint_ref=expected_current_fingerprint_ref,
                    prior_task_revision_ref=expected_current_task_revision_ref,
                )
                replacement = replacement.model_copy(
                    update={"latest_receipt_ref": receipt.receipt_ref}
                )
                next_snapshot = next_snapshot.model_copy(
                    update={"tasks": self._replace_task(next_snapshot, replacement)}
                )
                self._commit_mutation(next_snapshot, receipt)
                return receipt

    def migrate_completed_canonical_task(
        self,
        draft: DeveloperWorkTaskDraft,
        *,
        expected_current_fingerprint_ref: str,
        expected_current_task_revision_ref: str,
        migration_evidence_ref: str,
        idempotency_ref: str,
        approval_authority: LocalApprovalAuthority,
        approval_ref: str,
        actor_context: ActorContext,
    ) -> DeveloperWorkQueueReceipt:
        """Migrate one inactive source-aware contract while preserving lifecycle evidence."""

        approval_request = build_developer_work_completed_migration_approval_request(
            draft,
            expected_current_fingerprint_ref=(expected_current_fingerprint_ref),
            expected_current_task_revision_ref=(expected_current_task_revision_ref),
            migration_evidence_ref=migration_evidence_ref,
            idempotency_ref=idempotency_ref,
            actor_context=actor_context,
        )
        validate_task_ref(approval_ref, "completed_migration_approval_ref")
        approval_scope_ref = approval_request.resource_refs[0]
        with approval_authority.hold_validation_lock():
            with self._locked():
                snapshot = self._load_snapshot()
                payload = {
                    "event_kind": "task_contract_migrated",
                    "expected_current_fingerprint_ref": (
                        expected_current_fingerprint_ref
                    ),
                    "expected_current_task_revision_ref": (
                        expected_current_task_revision_ref
                    ),
                    "migration_evidence_ref": migration_evidence_ref,
                    "approval_ref": approval_ref,
                    "approval_scope_ref": approval_scope_ref,
                    "draft": draft.model_dump(mode="json"),
                }
                replay = self._replay(
                    idempotency_ref=idempotency_ref,
                    payload=payload,
                )
                if replay is not None:
                    return replay
                self._validate_canonical_queue_draft(draft)
                approval = approval_authority.validate_for_request(
                    approval_request, approval_ref
                )
                approval_grant = approval_authority.get_grant(approval_ref)
                if not approval.allowed or approval_grant is None:
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_COMPLETED_MIGRATION_APPROVAL_INVALID"
                    )
                task = self._find_task(snapshot, draft.task_ref)
                if (
                    developer_work_task_revision_ref(task)
                    != expected_current_task_revision_ref
                ):
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_COMPLETED_MIGRATION_REVISION_CONFLICT"
                    )
                if task.state == "claimed":
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_COMPLETED_MIGRATION_STATE_INVALID"
                    )
                if (
                    task.canonical_item_contract_ref is None
                    or draft.canonical_item_contract_ref is None
                ):
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_COMPLETED_MIGRATION_SOURCE_AWARE_REQUIRED"
                    )
                if (
                    task.canonical_source_fingerprint_ref
                    != expected_current_fingerprint_ref
                ):
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_COMPLETED_MIGRATION_FINGERPRINT_CONFLICT"
                    )
                immutable_fields = (
                    "task_ref",
                    "queue_order",
                    "canonical_task_ref",
                    "canonical_source_ref",
                    "scope_contract_ref",
                    "branch_ref",
                    "worktree_ref",
                    "workstream_ref",
                )
                if any(
                    getattr(task, field) != getattr(draft, field)
                    for field in immutable_fields
                ):
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_COMPLETED_MIGRATION_IDENTITY_CONFLICT"
                    )
                if (
                    task.canonical_item_contract_ref
                    == draft.canonical_item_contract_ref
                ):
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_COMPLETED_MIGRATION_NO_CHANGE"
                    )
                if any(
                    dependent.state in {"claimed", "review"}
                    and task.task_ref in dependent.depends_on_task_refs
                    for dependent in snapshot.tasks
                ):
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_CONTRACT_MIGRATION_ACTIVE_DEPENDENT"
                    )
                missing_dependencies = set(draft.depends_on_task_refs) - {
                    item.task_ref for item in snapshot.tasks
                }
                if missing_dependencies:
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_TASK_DEPENDENCY_MISSING"
                    )
                self._validate_canonical_dependencies_for_admission(snapshot, draft)
                if task.state == "completed" and any(
                    self._find_task(snapshot, dependency_ref).state != "completed"
                    for dependency_ref in draft.depends_on_task_refs
                ):
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_COMPLETED_MIGRATION_DEPENDENCY_INCOMPLETE"
                    )
                dependency_contract_refs = {
                    dependency_ref: self._durable_task_contract_ref(
                        self._find_task(snapshot, dependency_ref)
                    )
                    for dependency_ref in draft.depends_on_task_refs
                }
                replacement = task.model_copy(
                    update={
                        **draft.model_dump(mode="json"),
                        "dependency_contract_refs": dependency_contract_refs,
                    }
                )
                next_snapshot = snapshot.model_copy(
                    update={
                        "revision": snapshot.revision + 1,
                        "tasks": self._replace_task(snapshot, replacement),
                        "canonical_queue_contract_refs": {},
                        "canonical_queue_task_revision_refs": {},
                        "canonical_queue_legacy_transition_refs": {},
                        "canonical_queue_legacy_source_refs": {},
                        "canonical_queue_reconciliation_ref": None,
                    }
                )
                receipt = self._receipt(
                    event_kind="task_contract_migrated",
                    task_ref=task.task_ref,
                    idempotency_ref=idempotency_ref,
                    payload=payload,
                    revision=next_snapshot.revision,
                    safe_summary=(
                        "One inactive source-aware canonical contract was migrated "
                        "under exact approval while lifecycle evidence was preserved."
                    ),
                    approval_ref=approval_ref,
                    approval_scope_ref=approval_scope_ref,
                    approving_actor_ref=_hash_ref(
                        "actor-ref", approval_grant.approved_by_actor_id
                    ),
                    prior_fingerprint_ref=expected_current_fingerprint_ref,
                    prior_task_revision_ref=expected_current_task_revision_ref,
                    migration_evidence_ref=migration_evidence_ref,
                    migration_replacement_draft=draft,
                    migration_result_task=replacement,
                    migration_result_task_revision_ref=(
                        developer_work_task_revision_ref(replacement)
                    ),
                )
                replacement = replacement.model_copy(
                    update={"latest_receipt_ref": receipt.receipt_ref}
                )
                self._commit_mutation(
                    next_snapshot.model_copy(
                        update={"tasks": self._replace_task(next_snapshot, replacement)}
                    ),
                    receipt,
                )
                return receipt

    def current_task_revision_ref(self, task_ref: str) -> str:
        """Return a non-mutating revision binding for one exact durable task."""

        validate_task_ref(task_ref, "developer_work_task_revision_task_ref")
        with self._locked():
            task = self._find_task(self._load_snapshot(), task_ref)
            return developer_work_task_revision_ref(task)

    def admission_receipt_for_idempotency(
        self, idempotency_ref: str
    ) -> DeveloperWorkQueueReceipt | None:
        """Return exact durable admission evidence for uncertainty-safe replay."""

        validate_task_ref(idempotency_ref, "developer_queue_admission_idempotency_ref")
        with self._locked():
            for receipt in self._load_receipts():
                if receipt.idempotency_ref != idempotency_ref:
                    continue
                if receipt.event_kind != "tasks_admitted":
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_IDEMPOTENCY_CONFLICT"
                    )
                self._require_mutation_replay_evidence(receipt)
                return receipt
        return None

    def reconciliation_receipt_for_idempotency(
        self, idempotency_ref: str
    ) -> DeveloperWorkQueueReceipt | None:
        """Return prior exact reconciliation evidence for uncertainty-safe replay."""

        validate_task_ref(idempotency_ref, "developer_queue_reconcile_idempotency_ref")
        with self._locked():
            for receipt in self._load_receipts():
                if receipt.idempotency_ref != idempotency_ref:
                    continue
                if receipt.event_kind not in {
                    "queue_contracts_reconciled",
                    "queue_contracts_invalidated",
                }:
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_WORK_IDEMPOTENCY_CONFLICT"
                    )
                return receipt
        return None

    def reconcile_canonical_queue_contracts(
        self,
        *,
        canonical_contract_refs: dict[str, str],
        task_revision_refs: dict[str, str],
        legacy_transition_refs: dict[str, str],
        legacy_source_refs: dict[str, list[str]],
        expected_snapshot_revision: int,
        idempotency_ref: str,
        approval_authority: LocalApprovalAuthority,
        approval_ref: str,
        actor_context: ActorContext,
    ) -> DeveloperWorkQueueReceipt:
        """Bind claim readiness to one explicit durable Queue V2 reconciliation."""

        validate_task_ref(idempotency_ref, "developer_queue_reconcile_idempotency_ref")
        validate_task_ref(approval_ref, "developer_queue_reconcile_approval_ref")
        _validate_refs(
            [
                *canonical_contract_refs.keys(),
                *canonical_contract_refs.values(),
                *task_revision_refs.keys(),
                *task_revision_refs.values(),
                *legacy_transition_refs.keys(),
                *legacy_transition_refs.values(),
                *legacy_source_refs.keys(),
                *(
                    source_ref
                    for source_values in legacy_source_refs.values()
                    for source_ref in source_values
                ),
            ],
            "developer_queue_reconcile_ref",
        )
        approval_request = build_developer_queue_reconciliation_approval_request(
            canonical_contract_refs=canonical_contract_refs,
            task_revision_refs=task_revision_refs,
            legacy_transition_refs=legacy_transition_refs,
            legacy_source_refs=legacy_source_refs,
            expected_snapshot_revision=expected_snapshot_revision,
            idempotency_ref=idempotency_ref,
            actor_context=actor_context,
        )
        approval_scope_ref = approval_request.resource_refs[0]
        with approval_authority.hold_validation_lock():
            with self._locked():
                snapshot = self._load_snapshot()
                payload = {
                    "event_kind": "queue_contracts_reconciled",
                    "canonical_contract_refs": canonical_contract_refs,
                    "task_revision_refs": task_revision_refs,
                    "legacy_transition_refs": legacy_transition_refs,
                    "legacy_source_refs": legacy_source_refs,
                    "expected_snapshot_revision": expected_snapshot_revision,
                    "approval_ref": approval_ref,
                    "approval_scope_ref": approval_scope_ref,
                }
                replay = self._replay(idempotency_ref=idempotency_ref, payload=payload)
                if replay is not None:
                    return replay
                if snapshot.revision != expected_snapshot_revision:
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_QUEUE_RECONCILIATION_REVISION_CONFLICT"
                    )
                approval = approval_authority.validate_for_request(
                    approval_request, approval_ref
                )
                approval_grant = approval_authority.get_grant(approval_ref)
                if not approval.allowed or approval_grant is None:
                    raise DeveloperWorkQueueConflictError(
                        "DEVELOPER_QUEUE_RECONCILIATION_APPROVAL_INVALID"
                    )
                canonical_tasks = {
                    task.task_ref: task
                    for task in snapshot.tasks
                    if self._is_canonical_queue_task(task)
                }
                exact_keys = (
                    set(canonical_contract_refs)
                    == set(task_revision_refs)
                    == set(canonical_tasks)
                )
                expected_legacy_keys = {
                    task_ref
                    for task_ref, task in canonical_tasks.items()
                    if task.canonical_item_contract_ref is None
                }
                legacy_keys_valid = (
                    set(legacy_transition_refs)
                    == set(legacy_source_refs)
                    == expected_legacy_keys
                )
                revisions_current = exact_keys and all(
                    task_revision_refs[task_ref]
                    == developer_work_task_revision_ref(task)
                    for task_ref, task in canonical_tasks.items()
                )
                from uaa_developer_orchestrator.queue_record import (
                    queue_record_canonical_item_contract_ref,
                    queue_record_legacy_source_acceptance_ref_from_values,
                )

                contracts_current = exact_keys and legacy_keys_valid
                if contracts_current:
                    for task_ref, task in canonical_tasks.items():
                        if task.canonical_item_contract_ref is not None:
                            current = canonical_contract_refs[
                                task_ref
                            ] == self._durable_task_contract_ref(task)
                        else:
                            source_refs = legacy_source_refs[task_ref]
                            item_id = task.canonical_task_ref.rsplit("/", maxsplit=1)[
                                -1
                            ]
                            current = legacy_transition_refs[
                                task_ref
                            ] == queue_record_legacy_source_acceptance_ref_from_values(
                                item_id=item_id,
                                task_ref=task_ref,
                                source_refs=source_refs,
                                legacy_fingerprint_ref=(
                                    task.canonical_source_fingerprint_ref
                                ),
                            ) and canonical_contract_refs[
                                task_ref
                            ] == queue_record_canonical_item_contract_ref(
                                task.model_copy(
                                    update={"canonical_source_refs": source_refs}
                                )
                            )
                        if not current:
                            contracts_current = False
                            break
                dependency_bindings_current = contracts_current and all(
                    self._dependency_contract_bindings_current(snapshot, task)
                    for task in canonical_tasks.values()
                )
                reconciled = (
                    bool(canonical_tasks)
                    and exact_keys
                    and legacy_keys_valid
                    and revisions_current
                    and contracts_current
                    and dependency_bindings_current
                )
                reconciliation_payload = {
                    "canonical_contract_refs": canonical_contract_refs,
                    "task_revision_refs": task_revision_refs,
                    "legacy_transition_refs": legacy_transition_refs,
                    "legacy_source_refs": legacy_source_refs,
                }
                reconciliation_ref = (
                    _hash_ref(
                        "developer-queue-reconciliation-ref",
                        reconciliation_payload,
                    )
                    if reconciled
                    else None
                )
                next_snapshot = snapshot.model_copy(
                    update={
                        "revision": snapshot.revision + 1,
                        "canonical_queue_contract_refs": (
                            canonical_contract_refs if reconciled else {}
                        ),
                        "canonical_queue_task_revision_refs": (
                            task_revision_refs if reconciled else {}
                        ),
                        "canonical_queue_legacy_transition_refs": (
                            legacy_transition_refs if reconciled else {}
                        ),
                        "canonical_queue_legacy_source_refs": (
                            legacy_source_refs if reconciled else {}
                        ),
                        "canonical_queue_reconciliation_ref": reconciliation_ref,
                    }
                )
                receipt = self._receipt(
                    event_kind=(
                        "queue_contracts_reconciled"
                        if reconciled
                        else "queue_contracts_invalidated"
                    ),
                    idempotency_ref=idempotency_ref,
                    payload=payload,
                    revision=next_snapshot.revision,
                    safe_summary=(
                        "Canonical Queue V2 contracts and exact task revisions were "
                        "durably reconciled under exact local approval."
                        if reconciled
                        else "Canonical Queue V2 claim readiness was invalidated under "
                        "exact local approval because reconciliation was stale."
                    ),
                    approval_ref=approval_ref,
                    approval_scope_ref=approval_scope_ref,
                    approving_actor_ref=_hash_ref(
                        "actor-ref", approval_grant.approved_by_actor_id
                    ),
                    reconciliation_ref=reconciliation_ref,
                    reconciliation_snapshot_revision=expected_snapshot_revision,
                    reconciliation_contract_refs=canonical_contract_refs,
                    reconciliation_task_revision_refs=task_revision_refs,
                    reconciliation_legacy_transition_refs=legacy_transition_refs,
                    reconciliation_legacy_source_refs=legacy_source_refs,
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
        expected_blocker_ref: str,
        evidence_ref: str,
        idempotency_ref: str,
    ) -> DeveloperWorkQueueReceipt:
        """Remove one exact reviewed blocker and return the task to the queue."""

        validate_task_ref(task_ref, "developer_work_unblock_task_ref")
        validate_task_ref(
            expected_blocker_ref, "developer_work_unblock_expected_blocker_ref"
        )
        validate_task_ref(evidence_ref, "developer_work_unblock_evidence_ref")
        validate_task_ref(idempotency_ref, "developer_work_unblock_idempotency_ref")
        with self._locked():
            snapshot = self._load_snapshot()
            task = self._find_task(snapshot, task_ref)
            payload = {
                "event_kind": "task_unblocked",
                "task_ref": task_ref,
                "expected_blocker_ref": expected_blocker_ref,
                "evidence_ref": evidence_ref,
            }
            replay = self._replay(idempotency_ref=idempotency_ref, payload=payload)
            if replay is not None:
                return replay
            if task.state != "blocked":
                raise DeveloperWorkQueueClaimError("DEVELOPER_WORK_TASK_NOT_BLOCKED")
            if task.blocker_refs != [expected_blocker_ref]:
                raise DeveloperWorkQueueClaimError(
                    "DEVELOPER_WORK_UNBLOCK_BLOCKER_SET_DRIFTED"
                )
            _validate_unblock_evidence(
                expected_blocker_ref=expected_blocker_ref,
                evidence_ref=evidence_ref,
            )
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
                    "Developer task returned to the queue after exact blocker and "
                    "evidence review; no shell, Git, remote dispatch, or task execution "
                    "occurred."
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
        reconciliation_current = self._canonical_queue_snapshot_reconciliation_current(
            snapshot
        )
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
            canonical_queue_reconciliation_ref=(
                snapshot.canonical_queue_reconciliation_ref
                if reconciliation_current
                else None
            ),
            canonical_queue_reconciled_task_refs=(
                sorted(snapshot.canonical_queue_contract_refs)
                if reconciliation_current
                else []
            ),
            nodes=sorted(snapshot.nodes, key=lambda node: node.node_ref),
            tasks=[
                DeveloperWorkQueueTaskView(
                    task_ref=task.task_ref,
                    queue_order=task.queue_order,
                    canonical_task_ref=task.canonical_task_ref,
                    canonical_source_ref=task.canonical_source_ref,
                    canonical_source_fingerprint_ref=task.canonical_source_fingerprint_ref,
                    canonical_source_refs=task.canonical_source_refs,
                    canonical_item_contract_ref=task.canonical_item_contract_ref,
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
                    workstream_ref=task.workstream_ref,
                    depends_on_task_refs=task.depends_on_task_refs,
                    dependency_contract_refs=task.dependency_contract_refs,
                    dependency_ready=self._dependencies_complete(snapshot, task),
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
    def _is_canonical_queue_task(task: DeveloperWorkTaskDraft) -> bool:
        return (
            task.task_ref.startswith("dev-task:queue-v2-")
            or task.canonical_task_ref.startswith("canonical-task-ref:queue-v2/")
            or task.canonical_source_ref.startswith("repo-ref:developer-queue-v2/")
        )

    @classmethod
    def _validate_canonical_queue_draft(cls, draft: DeveloperWorkTaskDraft) -> None:
        """Reserve the Queue V2 namespace for an exact manifest-derived draft."""

        if not cls._is_canonical_queue_task(draft):
            return
        try:
            from uaa_developer_orchestrator.queue_record import (
                build_developer_queue_record_drafts,
            )

            expected = next(
                (
                    candidate
                    for candidate in build_developer_queue_record_drafts(REPO_ROOT)
                    if candidate.task_ref == draft.task_ref
                ),
                None,
            )
        except (OSError, TypeError, ValueError):
            expected = None
        if expected is None or expected.model_dump(mode="json") != draft.model_dump(
            mode="json"
        ):
            raise DeveloperWorkQueueConflictError(
                "DEVELOPER_WORK_CANONICAL_TASK_CONTRACT_INVALID"
            )

    @classmethod
    def _validate_canonical_dependencies_for_admission(
        cls,
        snapshot: DeveloperWorkQueueSnapshot,
        draft: DeveloperWorkTaskDraft,
    ) -> None:
        if not cls._is_canonical_queue_task(draft):
            return
        from uaa_developer_orchestrator.queue_record import (
            build_developer_queue_record_drafts,
            load_developer_queue_record_manifest,
            queue_record_legacy_source_acceptance_ref,
            queue_record_task_ref,
            queue_record_task_contract_ref,
        )

        expected_by_ref = {
            candidate.task_ref: candidate
            for candidate in build_developer_queue_record_drafts(REPO_ROOT)
        }
        actual_by_ref = {candidate.task_ref: candidate for candidate in snapshot.tasks}
        manifest_item_by_ref = {
            queue_record_task_ref(item): item
            for item in load_developer_queue_record_manifest(REPO_ROOT).items
        }
        for dependency_ref in draft.depends_on_task_refs:
            expected = expected_by_ref.get(dependency_ref)
            actual = actual_by_ref.get(dependency_ref)
            if expected is None or actual is None:
                raise DeveloperWorkQueueConflictError(
                    "DEVELOPER_WORK_CANONICAL_DEPENDENCY_CONTRACT_INVALID"
                )
            if actual.canonical_item_contract_ref is not None:
                current = actual.canonical_item_contract_ref == (
                    expected.canonical_item_contract_ref
                )
            else:
                item = manifest_item_by_ref[dependency_ref]
                legacy_acceptance_ref = queue_record_legacy_source_acceptance_ref(
                    item, actual.canonical_source_fingerprint_ref
                )
                current = (
                    queue_record_task_contract_ref(actual)
                    == queue_record_task_contract_ref(expected)
                    and legacy_acceptance_ref in item.source_refs
                )
            if not current:
                raise DeveloperWorkQueueConflictError(
                    "DEVELOPER_WORK_CANONICAL_DEPENDENCY_CONTRACT_INVALID"
                )

    @staticmethod
    def _durable_task_contract_ref(task: DeveloperWorkTask) -> str:
        from uaa_developer_orchestrator.queue_record import (
            queue_record_canonical_item_contract_ref,
            queue_record_task_contract_ref,
        )

        if task.canonical_item_contract_ref is None:
            return queue_record_task_contract_ref(task)
        if task.canonical_item_contract_ref != (
            queue_record_canonical_item_contract_ref(task)
        ):
            raise DeveloperWorkQueueConflictError(
                "DEVELOPER_WORK_CANONICAL_TASK_CONTRACT_INVALID"
            )
        return task.canonical_item_contract_ref

    @classmethod
    def _dependencies_complete(
        cls,
        snapshot: DeveloperWorkQueueSnapshot,
        task: DeveloperWorkTask,
    ) -> bool:
        by_ref = {candidate.task_ref: candidate for candidate in snapshot.tasks}
        if not all(
            by_ref[ref].state == "completed" for ref in task.depends_on_task_refs
        ):
            return False
        if not cls._canonical_queue_reconciliation_current(snapshot, task):
            return False
        if not all(
            cls._canonical_queue_reconciliation_current(snapshot, by_ref[ref])
            for ref in task.depends_on_task_refs
        ):
            return False
        try:
            cls._durable_task_contract_ref(task)
        except (DeveloperWorkQueueConflictError, OSError, TypeError, ValueError):
            return False
        return cls._dependency_contract_bindings_current(snapshot, task)

    @classmethod
    def _dependency_contract_bindings_current(
        cls,
        snapshot: DeveloperWorkQueueSnapshot,
        task: DeveloperWorkTask,
    ) -> bool:
        """Verify that one task is still bound to every exact prerequisite contract."""

        if task.canonical_item_contract_ref is None:
            return True
        if set(task.dependency_contract_refs) != set(task.depends_on_task_refs):
            return False
        by_ref = {candidate.task_ref: candidate for candidate in snapshot.tasks}
        try:
            return all(
                task.dependency_contract_refs[dependency_ref]
                == cls._durable_task_contract_ref(by_ref[dependency_ref])
                for dependency_ref in task.depends_on_task_refs
            )
        except (
            DeveloperWorkQueueConflictError,
            KeyError,
            OSError,
            TypeError,
            ValueError,
        ):
            return False

    @classmethod
    def _canonical_queue_reconciliation_current(
        cls,
        snapshot: DeveloperWorkQueueSnapshot,
        task: DeveloperWorkTask,
    ) -> bool:
        if not cls._is_canonical_queue_task(task):
            return True
        if snapshot.canonical_queue_reconciliation_ref is None:
            return False
        canonical_task_refs = {
            candidate.task_ref
            for candidate in snapshot.tasks
            if cls._is_canonical_queue_task(candidate)
        }
        if set(snapshot.canonical_queue_contract_refs) != canonical_task_refs:
            return False
        canonical_tasks = {
            candidate.task_ref: candidate
            for candidate in snapshot.tasks
            if cls._is_canonical_queue_task(candidate)
        }
        if any(
            snapshot.canonical_queue_task_revision_refs.get(task_ref)
            != developer_work_task_revision_ref(candidate)
            for task_ref, candidate in canonical_tasks.items()
        ):
            return False
        reconciled_contract_ref = snapshot.canonical_queue_contract_refs.get(
            task.task_ref
        )
        if reconciled_contract_ref is None:
            return False
        if task.canonical_item_contract_ref is not None:
            try:
                return reconciled_contract_ref == cls._durable_task_contract_ref(task)
            except (DeveloperWorkQueueConflictError, TypeError, ValueError):
                return False
        return task.task_ref in snapshot.canonical_queue_legacy_transition_refs

    @classmethod
    def _canonical_queue_snapshot_reconciliation_current(
        cls,
        snapshot: DeveloperWorkQueueSnapshot,
    ) -> bool:
        canonical_tasks = [
            task for task in snapshot.tasks if cls._is_canonical_queue_task(task)
        ]
        return bool(canonical_tasks) and all(
            cls._canonical_queue_reconciliation_current(snapshot, task)
            for task in canonical_tasks
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
        approval_ref: str | None = None,
        approval_scope_ref: str | None = None,
        approving_actor_ref: str | None = None,
        prior_fingerprint_ref: str | None = None,
        prior_task_revision_ref: str | None = None,
        migration_evidence_ref: str | None = None,
        migration_replacement_draft: DeveloperWorkTaskDraft | None = None,
        migration_result_task: DeveloperWorkTask | None = None,
        migration_result_task_revision_ref: str | None = None,
        admission_snapshot_revision: int | None = None,
        admission_drafts: list[DeveloperWorkTaskDraft] | None = None,
        reconciliation_ref: str | None = None,
        reconciliation_snapshot_revision: int | None = None,
        reconciliation_contract_refs: dict[str, str] | None = None,
        reconciliation_task_revision_refs: dict[str, str] | None = None,
        reconciliation_legacy_transition_refs: dict[str, str] | None = None,
        reconciliation_legacy_source_refs: dict[str, list[str]] | None = None,
    ) -> DeveloperWorkQueueReceipt:
        payload_fingerprint_ref = _hash_ref("developer-work-payload-ref", payload)
        contract_refs = reconciliation_contract_refs or {}
        task_revision_refs = reconciliation_task_revision_refs or {}
        legacy_transition_refs = reconciliation_legacy_transition_refs or {}
        legacy_source_refs = reconciliation_legacy_source_refs or {}
        reconciliation_evidence_ref = None
        admitted_drafts = admission_drafts or []
        admission_evidence_ref = None
        migration_contract_evidence_ref = None
        if event_kind in {"queue_contracts_reconciled", "queue_contracts_invalidated"}:
            reconciliation_evidence_ref = _hash_ref(
                "developer-queue-reconciliation-evidence-ref",
                {
                    "canonical_contract_refs": contract_refs,
                    "task_revision_refs": task_revision_refs,
                    "legacy_transition_refs": legacy_transition_refs,
                    "legacy_source_refs": legacy_source_refs,
                    "expected_snapshot_revision": reconciliation_snapshot_revision,
                    "reconciliation_ref": reconciliation_ref,
                },
            )
            approval_proof = {
                "approval_ref": approval_ref,
                "approval_scope_ref": approval_scope_ref,
                "approving_actor_ref": approving_actor_ref,
                "reconciliation_evidence_ref": reconciliation_evidence_ref,
            }
        elif event_kind == "tasks_admitted":
            admission_evidence_ref = _hash_ref(
                "developer-queue-admission-evidence-ref",
                {
                    "drafts": [
                        draft.model_dump(mode="json") for draft in admitted_drafts
                    ],
                    "expected_snapshot_revision": admission_snapshot_revision,
                },
            )
            approval_proof = {
                "approval_ref": approval_ref,
                "approval_scope_ref": approval_scope_ref,
                "approving_actor_ref": approving_actor_ref,
                "admission_evidence_ref": admission_evidence_ref,
            }
        elif event_kind == "task_contract_migrated":
            migration_contract_evidence_ref = _hash_ref(
                "developer-queue-migration-contract-evidence-ref",
                {
                    "replacement_draft": (
                        migration_replacement_draft.model_dump(mode="json")
                        if migration_replacement_draft is not None
                        else None
                    ),
                    "result_task": (
                        migration_result_task.model_dump(mode="json")
                        if migration_result_task is not None
                        else None
                    ),
                    "result_task_revision_ref": migration_result_task_revision_ref,
                },
            )
            approval_proof = {
                "approval_ref": approval_ref,
                "approval_scope_ref": approval_scope_ref,
                "approving_actor_ref": approving_actor_ref,
                "prior_fingerprint_ref": prior_fingerprint_ref,
                "prior_task_revision_ref": prior_task_revision_ref,
                "migration_evidence_ref": migration_evidence_ref,
                "migration_contract_evidence_ref": migration_contract_evidence_ref,
            }
        else:
            approval_proof = {
                "approval_ref": approval_ref,
                "approval_scope_ref": approval_scope_ref,
                "approving_actor_ref": approving_actor_ref,
                "prior_fingerprint_ref": prior_fingerprint_ref,
                "prior_task_revision_ref": prior_task_revision_ref,
            }
        approval_proof_ref = (
            _hash_ref("developer-work-approval-proof-ref", approval_proof)
            if all(value is not None for value in approval_proof.values())
            else None
        )
        return DeveloperWorkQueueReceipt(
            receipt_ref=_hash_ref(
                "developer-work-receipt-ref",
                {
                    "event_kind": event_kind,
                    "idempotency_ref": idempotency_ref,
                    "payload": payload,
                    "approval_proof_ref": approval_proof_ref,
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
            approval_ref=approval_ref,
            approval_scope_ref=approval_scope_ref,
            approving_actor_ref=approving_actor_ref,
            prior_fingerprint_ref=prior_fingerprint_ref,
            prior_task_revision_ref=prior_task_revision_ref,
            migration_evidence_ref=migration_evidence_ref,
            migration_replacement_draft=migration_replacement_draft,
            migration_result_task=migration_result_task,
            migration_result_task_revision_ref=migration_result_task_revision_ref,
            migration_contract_evidence_ref=migration_contract_evidence_ref,
            admission_snapshot_revision=admission_snapshot_revision,
            admission_drafts=admitted_drafts,
            admission_evidence_ref=admission_evidence_ref,
            reconciliation_ref=reconciliation_ref,
            reconciliation_snapshot_revision=reconciliation_snapshot_revision,
            reconciliation_contract_refs=contract_refs,
            reconciliation_task_revision_refs=task_revision_refs,
            reconciliation_legacy_transition_refs=legacy_transition_refs,
            reconciliation_legacy_source_refs=legacy_source_refs,
            reconciliation_evidence_ref=reconciliation_evidence_ref,
            approval_proof_ref=approval_proof_ref,
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
            self._require_mutation_replay_evidence(receipt)
            return receipt.model_copy(update={"replayed": True})
        return None

    @staticmethod
    def _require_mutation_replay_evidence(
        receipt: DeveloperWorkQueueReceipt,
    ) -> None:
        """Keep legacy evidence readable without letting it authorize replay."""

        if receipt.event_kind == "tasks_admitted" and (
            receipt.admission_snapshot_revision is None
            or not receipt.admission_drafts
            or receipt.admission_evidence_ref is None
        ):
            raise DeveloperWorkQueueConflictError(
                "DEVELOPER_QUEUE_ADMISSION_REPLAY_EVIDENCE_REQUIRED"
            )
        if receipt.event_kind == "task_contract_migrated" and (
            receipt.migration_replacement_draft is None
            or receipt.migration_result_task is None
            or receipt.migration_result_task_revision_ref is None
            or receipt.migration_contract_evidence_ref is None
        ):
            raise DeveloperWorkQueueConflictError(
                "DEVELOPER_QUEUE_MIGRATION_REPLAY_EVIDENCE_REQUIRED"
            )

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
