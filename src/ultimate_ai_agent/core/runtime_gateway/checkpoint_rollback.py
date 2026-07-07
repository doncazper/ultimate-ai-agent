from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)


RUNTIME_CHECKPOINT_ROLLBACK_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-checkpoint-rollback:v1"
)
RUNTIME_CHECKPOINT_ROLLBACK_ROUTE_REF = "GET /api/runtime/checkpoint-rollback"
RUNTIME_CHECKPOINT_ROLLBACK_CLI_REF = "uaa runtime inspect-checkpoint-rollback"
RUNTIME_CHECKPOINT_ROLLBACK_SNAPSHOT_REF = (
    "checkpoint-rollback-snapshot-ref:runtime:shadow-store"
)
RUNTIME_CHECKPOINT_ROLLBACK_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-18:checkpoint-rollback"
)

RUNTIME_CHECKPOINT_ROLLBACK_BLOCKED_AUTHORITY_REFS = [
    "blocked-authority:checkpoint-rollback-no-broad-filesystem-snapshot",
    "blocked-authority:checkpoint-rollback-no-rollback-execution-route",
    "blocked-authority:checkpoint-rollback-no-git-mutation",
    "blocked-authority:checkpoint-rollback-no-raw-content-persistence",
    "blocked-authority:checkpoint-rollback-no-raw-path-persistence",
    "blocked-authority:checkpoint-rollback-no-provider-model-call",
    "blocked-authority:checkpoint-rollback-no-shell-execution",
    "blocked-authority:checkpoint-rollback-no-browser-automation",
    "blocked-authority:checkpoint-rollback-no-production-authority",
]


class RuntimeCheckpointLaneKind(str, Enum):
    file_patch_core = "file_patch_core"
    work_board_reorder = "work_board_reorder"
    crm_local_mutation = "crm_local_mutation"
    local_task_commit = "local_task_commit"
    coding_patch_apply_readiness = "coding_patch_apply_readiness"


class RuntimeCheckpointLaneStatus(str, Enum):
    core_exact_verified = "core_exact_verified"
    exact_local_receipt_posture = "exact_local_receipt_posture"
    readiness_only = "readiness_only"
    blocked = "blocked"


class RuntimeCheckpointRollbackLane(BaseModel):
    lane_ref: str
    lane_kind: RuntimeCheckpointLaneKind
    status: RuntimeCheckpointLaneStatus
    safe_summary: str
    checkpoint_required: bool = True
    checkpoint_available: bool = False
    checkpoint_ref: str
    checkpoint_hash_ref: str
    mutation_receipt_ref: str
    rollback_plan_ref: str
    rollback_receipt_ref: str
    approval_scope_ref: str
    idempotency_ref: str
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    exact_core_rollback_receipts_supported: bool = False
    api_rollback_execution_enabled: bool = False
    control_center_rollback_execution_enabled: bool = False
    broad_filesystem_snapshot_enabled: bool = False
    git_mutation_enabled: bool = False
    raw_content_persisted: bool = False
    raw_path_persisted: bool = False
    provider_model_call_performed: bool = False
    shell_execution_performed: bool = False
    browser_automation_performed: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_lane(self) -> "RuntimeCheckpointRollbackLane":
        for value, field_name in [
            (self.lane_ref, "lane_ref"),
            (self.checkpoint_ref, "checkpoint_ref"),
            (self.checkpoint_hash_ref, "checkpoint_hash_ref"),
            (self.mutation_receipt_ref, "mutation_receipt_ref"),
            (self.rollback_plan_ref, "rollback_plan_ref"),
            (self.rollback_receipt_ref, "rollback_receipt_ref"),
            (self.approval_scope_ref, "approval_scope_ref"),
            (self.idempotency_ref, "idempotency_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "proof_refs",
            "evidence_refs",
            "verifier_refs",
            "blocked_authority_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (str(self.lane_kind), "lane_kind"),
            (str(self.status), "status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        if self.checkpoint_required and not self.checkpoint_ref:
            raise ValueError("RUNTIME_CHECKPOINT_REF_REQUIRED")
        if self.checkpoint_available and not self.checkpoint_hash_ref:
            raise ValueError("RUNTIME_CHECKPOINT_HASH_REQUIRED")
        denied_flags = {
            "api_rollback_execution_enabled": self.api_rollback_execution_enabled,
            "control_center_rollback_execution_enabled": (
                self.control_center_rollback_execution_enabled
            ),
            "broad_filesystem_snapshot_enabled": self.broad_filesystem_snapshot_enabled,
            "git_mutation_enabled": self.git_mutation_enabled,
            "raw_content_persisted": self.raw_content_persisted,
            "raw_path_persisted": self.raw_path_persisted,
            "provider_model_call_performed": self.provider_model_call_performed,
            "shell_execution_performed": self.shell_execution_performed,
            "browser_automation_performed": self.browser_automation_performed,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_CHECKPOINT_ROLLBACK_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_CHECKPOINT_ROLLBACK_BLOCKERS_REQUIRED")
        return self


class RuntimeCheckpointRollbackReadModel(BaseModel):
    schema_version: str = "runtime_checkpoint_rollback.v1"
    contract_ref: str = RUNTIME_CHECKPOINT_ROLLBACK_CONTRACT_REF
    status: str = "read_only_checkpoint_rollback_posture"
    snapshot_ref: str = RUNTIME_CHECKPOINT_ROLLBACK_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:runtime-checkpoint-rollback:pending"
    route_ref: str = RUNTIME_CHECKPOINT_ROLLBACK_ROUTE_REF
    cli_ref: str = RUNTIME_CHECKPOINT_ROLLBACK_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    safe_summary: str = (
        "Checkpoint rollback posture exposes AuthorityLease capability refs, "
        "receipts, and blocked broad snapshot or rollback execution authority."
    )
    lanes: list[RuntimeCheckpointRollbackLane]
    lane_count: int = 0
    checkpoint_required_count: int = 0
    checkpoint_available_count: int = 0
    exact_core_supported_count: int = 0
    blocked_lane_count: int = 0
    broad_filesystem_snapshot_enabled: bool = False
    rollback_execution_route_enabled: bool = False
    git_mutation_enabled: bool = False
    raw_content_persistence_enabled: bool = False
    raw_path_persistence_enabled: bool = False
    production_authority_enabled: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: (
            list(GOVERNED_RUNTIME_REDACTIONS)
            + [
                "raw_paths_omitted",
                "raw_content_omitted",
                "checkpoint_payloads_omitted",
                "rollback_payloads_omitted",
            ]
        )
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeCheckpointRollbackReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        if self.lane_count != len(self.lanes):
            raise ValueError("RUNTIME_CHECKPOINT_ROLLBACK_LANE_COUNT_MISMATCH")
        if self.checkpoint_required_count != len(
            [lane for lane in self.lanes if lane.checkpoint_required]
        ):
            raise ValueError("RUNTIME_CHECKPOINT_REQUIRED_COUNT_MISMATCH")
        if self.checkpoint_available_count != len(
            [lane for lane in self.lanes if lane.checkpoint_available]
        ):
            raise ValueError("RUNTIME_CHECKPOINT_AVAILABLE_COUNT_MISMATCH")
        if self.exact_core_supported_count != len(
            [lane for lane in self.lanes if lane.exact_core_rollback_receipts_supported]
        ):
            raise ValueError("RUNTIME_CHECKPOINT_CORE_SUPPORT_COUNT_MISMATCH")
        if self.blocked_lane_count != len(
            [
                lane
                for lane in self.lanes
                if lane.status == RuntimeCheckpointLaneStatus.blocked.value
            ]
        ):
            raise ValueError("RUNTIME_CHECKPOINT_BLOCKED_COUNT_MISMATCH")
        denied_flags = {
            "broad_filesystem_snapshot_enabled": self.broad_filesystem_snapshot_enabled,
            "rollback_execution_route_enabled": self.rollback_execution_route_enabled,
            "git_mutation_enabled": self.git_mutation_enabled,
            "raw_content_persistence_enabled": self.raw_content_persistence_enabled,
            "raw_path_persistence_enabled": self.raw_path_persistence_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_CHECKPOINT_ROLLBACK_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if RUNTIME_CHECKPOINT_ROLLBACK_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_CHECKPOINT_ROLLBACK_PROOF_REQUIRED")
        if set(RUNTIME_CHECKPOINT_ROLLBACK_BLOCKED_AUTHORITY_REFS) - set(
            self.blocked_authority_refs
        ):
            raise ValueError("RUNTIME_CHECKPOINT_ROLLBACK_BLOCKERS_REQUIRED")
        return self


def _hash_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-checkpoint-rollback:{digest}"


def _lane(
    *,
    lane_ref: str,
    lane_kind: RuntimeCheckpointLaneKind,
    status: RuntimeCheckpointLaneStatus,
    safe_summary: str,
    checkpoint_available: bool,
    checkpoint_ref: str,
    checkpoint_hash_ref: str,
    mutation_receipt_ref: str,
    rollback_plan_ref: str,
    rollback_receipt_ref: str,
    approval_scope_ref: str,
    idempotency_ref: str,
    proof_refs: list[str],
    evidence_refs: list[str],
    verifier_refs: list[str],
    exact_core_rollback_receipts_supported: bool = False,
) -> RuntimeCheckpointRollbackLane:
    return RuntimeCheckpointRollbackLane(
        lane_ref=lane_ref,
        lane_kind=lane_kind,
        status=status,
        safe_summary=safe_summary,
        checkpoint_available=checkpoint_available,
        checkpoint_ref=checkpoint_ref,
        checkpoint_hash_ref=checkpoint_hash_ref,
        mutation_receipt_ref=mutation_receipt_ref,
        rollback_plan_ref=rollback_plan_ref,
        rollback_receipt_ref=rollback_receipt_ref,
        approval_scope_ref=approval_scope_ref,
        idempotency_ref=idempotency_ref,
        proof_refs=proof_refs,
        evidence_refs=evidence_refs,
        verifier_refs=verifier_refs,
        blocked_authority_refs=list(RUNTIME_CHECKPOINT_ROLLBACK_BLOCKED_AUTHORITY_REFS),
        exact_core_rollback_receipts_supported=exact_core_rollback_receipts_supported,
    )


def _default_lanes() -> list[RuntimeCheckpointRollbackLane]:
    return [
        _lane(
            lane_ref="checkpoint-rollback-lane-ref:file-patch-core",
            lane_kind=RuntimeCheckpointLaneKind.file_patch_core,
            status=RuntimeCheckpointLaneStatus.core_exact_verified,
            safe_summary=(
                "Core file patch lane has exact approval, checkpoint, receipt, "
                "idempotency, and rollback receipt coverage in a scoped workspace."
            ),
            checkpoint_available=True,
            checkpoint_ref="checkpoint-ref:file-patch-core:preimage",
            checkpoint_hash_ref="checkpoint-hash-ref:file-patch-core:preimage",
            mutation_receipt_ref="receipt-ref:file-patch-core:apply",
            rollback_plan_ref="rollback-plan-ref:file-patch-core",
            rollback_receipt_ref="receipt-ref:file-patch-core:rollback",
            approval_scope_ref="approval-scope-ref:file-patch-core:exact",
            idempotency_ref="idempotency-ref:file-patch-core:apply-rollback",
            proof_refs=["proof-ref:file-patch-core:rollback-tests"],
            evidence_refs=["evidence-ref:filesystem-mutation-dogfood:temp-workspace"],
            verifier_refs=["verifier-ref:filesystem-mutation-lane-inspector"],
            exact_core_rollback_receipts_supported=True,
        ),
        _lane(
            lane_ref="checkpoint-rollback-lane-ref:work-board-reorder",
            lane_kind=RuntimeCheckpointLaneKind.work_board_reorder,
            status=RuntimeCheckpointLaneStatus.exact_local_receipt_posture,
            safe_summary=(
                "Work Board reorder has exact local receipt posture; rollback "
                "execution remains blocked until a rollback AuthorityLease "
                "capability is implemented and active."
            ),
            checkpoint_available=True,
            checkpoint_ref="checkpoint-ref:work-board-reorder:previous-order",
            checkpoint_hash_ref="checkpoint-hash-ref:work-board-reorder:previous-order",
            mutation_receipt_ref="receipt-ref:work-board-reorder:exact-local",
            rollback_plan_ref="rollback-plan-ref:work-board-reorder:readiness",
            rollback_receipt_ref="receipt-ref:work-board-reorder:blocked",
            approval_scope_ref="approval-scope-ref:work-board-reorder:exact",
            idempotency_ref="idempotency-ref:work-board-reorder:exact",
            proof_refs=["proof-ref:work-board-reorder:local-receipt"],
            evidence_refs=["evidence-ref:work-board-reorder:local-receipt"],
            verifier_refs=["verifier-ref:control-center-work-board"],
        ),
        _lane(
            lane_ref="checkpoint-rollback-lane-ref:crm-local-mutation",
            lane_kind=RuntimeCheckpointLaneKind.crm_local_mutation,
            status=RuntimeCheckpointLaneStatus.exact_local_receipt_posture,
            safe_summary=(
                "CRM local mutations carry exact receipt posture; external CRM "
                "writes and broad rollback execution remain blocked."
            ),
            checkpoint_available=True,
            checkpoint_ref="checkpoint-ref:crm-local-mutation:pre-change",
            checkpoint_hash_ref="checkpoint-hash-ref:crm-local-mutation:pre-change",
            mutation_receipt_ref="receipt-ref:crm-local-mutation:exact-local",
            rollback_plan_ref="rollback-plan-ref:crm-local-mutation:readiness",
            rollback_receipt_ref="receipt-ref:crm-local-mutation:blocked",
            approval_scope_ref="approval-scope-ref:crm-local-mutation:exact",
            idempotency_ref="idempotency-ref:crm-local-mutation:exact",
            proof_refs=["proof-ref:crm-local-command-center:m2"],
            evidence_refs=["evidence-ref:crm-local-mutation:receipt"],
            verifier_refs=["verifier-ref:crm-local-command-center"],
        ),
        _lane(
            lane_ref="checkpoint-rollback-lane-ref:local-task-commit",
            lane_kind=RuntimeCheckpointLaneKind.local_task_commit,
            status=RuntimeCheckpointLaneStatus.readiness_only,
            safe_summary=(
                "Local task commit exposes rollback and safe-disable refs, but "
                "rollback execution remains future-gated."
            ),
            checkpoint_available=False,
            checkpoint_ref="checkpoint-ref:local-task-commit:required",
            checkpoint_hash_ref="checkpoint-hash-ref:local-task-commit:pending",
            mutation_receipt_ref="receipt-ref:local-task-commit:exact",
            rollback_plan_ref="rollback-plan-ref:local-task-commit:readiness",
            rollback_receipt_ref="receipt-ref:local-task-commit:blocked",
            approval_scope_ref="approval-scope-ref:local-task-commit:exact",
            idempotency_ref="idempotency-ref:local-task-commit:exact",
            proof_refs=["proof-ref:founder-loop:local-task-commit"],
            evidence_refs=["evidence-ref:founder-loop:local-task-commit"],
            verifier_refs=["verifier-ref:operational-maturity"],
        ),
        _lane(
            lane_ref="checkpoint-rollback-lane-ref:coding-patch-apply",
            lane_kind=RuntimeCheckpointLaneKind.coding_patch_apply_readiness,
            status=RuntimeCheckpointLaneStatus.blocked,
            safe_summary=(
                "Coding patch apply needs exact selected patch scope, checkpoint, "
                "receipt, and rollback proof before execution can be promoted."
            ),
            checkpoint_available=False,
            checkpoint_ref="checkpoint-ref:coding-patch-apply:required",
            checkpoint_hash_ref="checkpoint-hash-ref:coding-patch-apply:pending",
            mutation_receipt_ref="receipt-ref:coding-patch-apply:blocked",
            rollback_plan_ref="rollback-plan-ref:coding-patch-apply:required",
            rollback_receipt_ref="receipt-ref:coding-patch-apply:blocked",
            approval_scope_ref="approval-scope-ref:coding-patch-apply:required",
            idempotency_ref="idempotency-ref:coding-patch-apply:required",
            proof_refs=["proof-ref:coding-patch-apply:blocked-readiness"],
            evidence_refs=["evidence-ref:coding-patch-apply:blocked-readiness"],
            verifier_refs=["verifier-ref:coding-patch-apply:future"],
        ),
    ]


def build_runtime_checkpoint_rollback_read_model() -> (
    RuntimeCheckpointRollbackReadModel
):
    lanes = _default_lanes()
    model = RuntimeCheckpointRollbackReadModel(
        lanes=lanes,
        lane_count=len(lanes),
        checkpoint_required_count=len([lane for lane in lanes if lane.checkpoint_required]),
        checkpoint_available_count=len([lane for lane in lanes if lane.checkpoint_available]),
        exact_core_supported_count=len(
            [lane for lane in lanes if lane.exact_core_rollback_receipts_supported]
        ),
        blocked_lane_count=len(
            [
                lane
                for lane in lanes
                if lane.status == RuntimeCheckpointLaneStatus.blocked.value
            ]
        ),
        blocked_authority_refs=list(RUNTIME_CHECKPOINT_ROLLBACK_BLOCKED_AUTHORITY_REFS),
        proof_refs=[RUNTIME_CHECKPOINT_ROLLBACK_PROOF_REF],
        verifier_refs=["verifier-ref:hermes-runtime-adoption:phase-18"],
        next_safe_action_refs=[
            "next-safe-action-ref:checkpoint-rollback:inspect-read-model",
            "next-safe-action-ref:checkpoint-rollback:keep-broad-snapshots-blocked",
            "next-safe-action-ref:checkpoint-rollback:promote-only-exact-lanes",
        ],
    )
    payload = model.model_dump(mode="json", exclude={"snapshot_hash_ref"})
    return model.model_copy(update={"snapshot_hash_ref": _hash_payload(payload)})
