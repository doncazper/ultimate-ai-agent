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


RUNTIME_WORKTREE_PER_AGENT_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-worktree-per-agent:v1"
)
RUNTIME_WORKTREE_PER_AGENT_ROUTE_REF = "GET /api/runtime/worktree-per-agent"
RUNTIME_WORKTREE_PER_AGENT_CLI_REF = "uaa runtime inspect-worktree-per-agent"
RUNTIME_WORKTREE_PER_AGENT_SNAPSHOT_REF = (
    "worktree-per-agent-snapshot-ref:runtime:proposals"
)
RUNTIME_WORKTREE_PER_AGENT_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-33:worktree-per-agent"
)
RUNTIME_WORKTREE_PER_AGENT_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-33:worktree-per-agent"
)

RUNTIME_WORKTREE_PER_AGENT_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:worktree-per-agent-no-git-worktree-create",
    "blocked-authority:worktree-per-agent-no-git-worktree-delete",
    "blocked-authority:worktree-per-agent-no-branch-mutation",
    "blocked-authority:worktree-per-agent-no-file-write",
    "blocked-authority:worktree-per-agent-no-commit",
    "blocked-authority:worktree-per-agent-no-push",
    "blocked-authority:worktree-per-agent-no-shell-execution",
    "blocked-authority:worktree-per-agent-no-provider-call",
    "blocked-authority:worktree-per-agent-no-control-center-authority-mint",
    "blocked-authority:worktree-per-agent-no-raw-path-persistence",
)


class RuntimeWorktreeAgentRole(str, Enum):
    implementer = "implementer"
    reviewer = "reviewer"
    verifier = "verifier"


class RuntimeWorktreeLaneStatus(str, Enum):
    proposal = "proposal"
    review_ready = "review_ready"
    mutation_blocked = "mutation_blocked"


class RuntimeWorktreeIsolationMode(str, Enum):
    branch_proposal_only = "branch_proposal_only"
    existing_worktree_ref_only = "existing_worktree_ref_only"
    blocked_worktree_mutation = "blocked_worktree_mutation"


class RuntimeWorktreePerAgentLane(BaseModel):
    lane_ref: str
    display_label: str
    agent_role: RuntimeWorktreeAgentRole
    lane_status: RuntimeWorktreeLaneStatus
    isolation_mode: RuntimeWorktreeIsolationMode
    workspace_scope_ref: str
    branch_proposal_ref: str
    branch_name_ref: str
    worktree_ref: str
    checkpoint_plan_ref: str
    git_receipt_plan_ref: str
    rollback_plan_ref: str
    safe_summary: str
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    git_worktree_create_enabled: bool = False
    git_worktree_delete_enabled: bool = False
    branch_mutation_enabled: bool = False
    file_write_enabled: bool = False
    commit_enabled: bool = False
    push_enabled: bool = False
    shell_execution_enabled: bool = False
    provider_call_enabled: bool = False
    raw_path_persisted: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_lane(self) -> "RuntimeWorktreePerAgentLane":
        for value, field_name in [
            (self.lane_ref, "lane_ref"),
            (self.workspace_scope_ref, "workspace_scope_ref"),
            (self.branch_proposal_ref, "branch_proposal_ref"),
            (self.branch_name_ref, "branch_name_ref"),
            (self.worktree_ref, "worktree_ref"),
            (self.checkpoint_plan_ref, "checkpoint_plan_ref"),
            (self.git_receipt_plan_ref, "git_receipt_plan_ref"),
            (self.rollback_plan_ref, "rollback_plan_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "proof_refs",
            "blocked_authority_refs",
            "next_safe_action_refs",
        ):
            for value in getattr(self, field_name):
                validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.display_label, "display_label"),
            (str(self.agent_role), "agent_role"),
            (str(self.lane_status), "lane_status"),
            (str(self.isolation_mode), "isolation_mode"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "git_worktree_create_enabled": self.git_worktree_create_enabled,
            "git_worktree_delete_enabled": self.git_worktree_delete_enabled,
            "branch_mutation_enabled": self.branch_mutation_enabled,
            "file_write_enabled": self.file_write_enabled,
            "commit_enabled": self.commit_enabled,
            "push_enabled": self.push_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "raw_path_persisted": self.raw_path_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_WORKTREE_PER_AGENT_LANE_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_WORKTREE_PER_AGENT_BLOCKERS_REQUIRED")
        return self


class RuntimeWorktreePerAgentReadModel(BaseModel):
    schema_version: str = "runtime_worktree_per_agent.v1"
    contract_ref: str = RUNTIME_WORKTREE_PER_AGENT_CONTRACT_REF
    status: str = "read_only_worktree_lane_posture"
    snapshot_ref: str = RUNTIME_WORKTREE_PER_AGENT_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:runtime-worktree-per-agent:pending"
    route_ref: str = RUNTIME_WORKTREE_PER_AGENT_ROUTE_REF
    cli_ref: str = RUNTIME_WORKTREE_PER_AGENT_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    safe_summary: str = (
        "Worktree-per-agent posture exposes branch and worktree lane proposals "
        "only; Git and file mutation stay blocked."
    )
    lanes: list[RuntimeWorktreePerAgentLane] = Field(default_factory=list)
    lane_count: int = 0
    proposal_count: int = 0
    review_ready_count: int = 0
    mutation_blocked_count: int = 0
    workspace_grants_visible: bool = True
    branch_name_policy_visible: bool = True
    checkpoint_plan_visible: bool = True
    git_receipt_plan_visible: bool = True
    rollback_plan_visible: bool = True
    cli_parity_visible: bool = True
    git_worktree_create_enabled: bool = False
    git_worktree_delete_enabled: bool = False
    branch_mutation_enabled: bool = False
    file_write_enabled: bool = False
    commit_enabled: bool = False
    push_enabled: bool = False
    shell_execution_enabled: bool = False
    provider_call_enabled: bool = False
    control_center_mints_authority: bool = False
    raw_path_persisted: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + [
            "raw_paths_omitted",
            "raw_file_content_omitted",
            "raw_git_output_omitted",
        ]
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeWorktreePerAgentReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "promotion_path_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
            "redactions_applied",
        ):
            for value in getattr(self, field_name):
                if field_name == "redactions_applied":
                    validate_safe_execution_text(value, field_name)
                else:
                    validate_execution_ref(value, field_name)
        if self.lane_count != len(self.lanes):
            raise ValueError("RUNTIME_WORKTREE_PER_AGENT_LANE_COUNT_DRIFT")
        status_counts = {
            RuntimeWorktreeLaneStatus.proposal.value: self.proposal_count,
            RuntimeWorktreeLaneStatus.review_ready.value: self.review_ready_count,
            RuntimeWorktreeLaneStatus.mutation_blocked.value: (
                self.mutation_blocked_count
            ),
        }
        for status, expected in status_counts.items():
            actual = sum(1 for lane in self.lanes if lane.lane_status == status)
            if actual != expected:
                raise ValueError("RUNTIME_WORKTREE_PER_AGENT_STATUS_COUNT_DRIFT")
        visibility_flags = {
            "workspace_grants_visible": self.workspace_grants_visible,
            "branch_name_policy_visible": self.branch_name_policy_visible,
            "checkpoint_plan_visible": self.checkpoint_plan_visible,
            "git_receipt_plan_visible": self.git_receipt_plan_visible,
            "rollback_plan_visible": self.rollback_plan_visible,
            "cli_parity_visible": self.cli_parity_visible,
        }
        missing = [name for name, value in visibility_flags.items() if not value]
        if missing:
            raise ValueError(
                "RUNTIME_WORKTREE_PER_AGENT_VISIBILITY_REQUIRED: "
                + ", ".join(missing)
            )
        denied_flags = {
            "git_worktree_create_enabled": self.git_worktree_create_enabled,
            "git_worktree_delete_enabled": self.git_worktree_delete_enabled,
            "branch_mutation_enabled": self.branch_mutation_enabled,
            "file_write_enabled": self.file_write_enabled,
            "commit_enabled": self.commit_enabled,
            "push_enabled": self.push_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "control_center_mints_authority": self.control_center_mints_authority,
            "raw_path_persisted": self.raw_path_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_WORKTREE_PER_AGENT_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        for ref in RUNTIME_WORKTREE_PER_AGENT_BLOCKED_AUTHORITY_REFS:
            if ref not in self.blocked_authority_refs:
                raise ValueError("RUNTIME_WORKTREE_PER_AGENT_BLOCKER_MISSING")
        if RUNTIME_WORKTREE_PER_AGENT_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_WORKTREE_PER_AGENT_PROOF_REF_REQUIRED")
        if RUNTIME_WORKTREE_PER_AGENT_VERIFIER_REF not in self.verifier_refs:
            raise ValueError("RUNTIME_WORKTREE_PER_AGENT_VERIFIER_REF_REQUIRED")
        return self


def _snapshot_hash_ref(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(encoded).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-worktree-per-agent:{digest}"


def _lane(
    slug: str,
    *,
    display_label: str,
    agent_role: RuntimeWorktreeAgentRole,
    lane_status: RuntimeWorktreeLaneStatus,
    isolation_mode: RuntimeWorktreeIsolationMode,
    safe_summary: str,
) -> RuntimeWorktreePerAgentLane:
    return RuntimeWorktreePerAgentLane(
        lane_ref=f"worktree-agent-lane-ref:{slug}",
        display_label=display_label,
        agent_role=agent_role,
        lane_status=lane_status,
        isolation_mode=isolation_mode,
        workspace_scope_ref=f"workspace-scope-ref:worktree-agent:{slug}",
        branch_proposal_ref=f"branch-proposal-ref:worktree-agent:{slug}",
        branch_name_ref=f"branch-name-ref:worktree-agent:{slug}:proposal",
        worktree_ref=f"worktree-ref:worktree-agent:{slug}:safe-ref-only",
        checkpoint_plan_ref=f"checkpoint-plan-ref:worktree-agent:{slug}",
        git_receipt_plan_ref=f"git-receipt-plan-ref:worktree-agent:{slug}",
        rollback_plan_ref=f"rollback-plan-ref:worktree-agent:{slug}",
        safe_summary=safe_summary,
        proof_refs=[RUNTIME_WORKTREE_PER_AGENT_PROOF_REF],
        blocked_authority_refs=list(RUNTIME_WORKTREE_PER_AGENT_BLOCKED_AUTHORITY_REFS),
        next_safe_action_refs=[f"next-safe-action-ref:worktree-agent:{slug}:review"],
    )


def build_runtime_worktree_per_agent_read_model() -> (
    RuntimeWorktreePerAgentReadModel
):
    lanes = [
        _lane(
            "implementer",
            display_label="Implementer worktree lane",
            agent_role=RuntimeWorktreeAgentRole.implementer,
            lane_status=RuntimeWorktreeLaneStatus.proposal,
            isolation_mode=RuntimeWorktreeIsolationMode.branch_proposal_only,
            safe_summary=(
                "Implementer lane proposes a branch/worktree shape; no branch "
                "or file mutation is enabled."
            ),
        ),
        _lane(
            "reviewer",
            display_label="Reviewer comparison lane",
            agent_role=RuntimeWorktreeAgentRole.reviewer,
            lane_status=RuntimeWorktreeLaneStatus.review_ready,
            isolation_mode=RuntimeWorktreeIsolationMode.existing_worktree_ref_only,
            safe_summary=(
                "Reviewer lane can compare safe refs only; Git worktree create "
                "and delete remain blocked."
            ),
        ),
        _lane(
            "verifier",
            display_label="Verifier proof lane",
            agent_role=RuntimeWorktreeAgentRole.verifier,
            lane_status=RuntimeWorktreeLaneStatus.mutation_blocked,
            isolation_mode=RuntimeWorktreeIsolationMode.blocked_worktree_mutation,
            safe_summary=(
                "Verifier lane records checkpoint, Git receipt, and rollback "
                "plans without running Git or shell commands."
            ),
        ),
    ]
    payload_for_hash: dict[str, object] = {
        "lanes": [lane.model_dump(mode="json") for lane in lanes],
        "blocked": list(RUNTIME_WORKTREE_PER_AGENT_BLOCKED_AUTHORITY_REFS),
    }
    return RuntimeWorktreePerAgentReadModel(
        snapshot_hash_ref=_snapshot_hash_ref(payload_for_hash),
        lanes=lanes,
        lane_count=len(lanes),
        proposal_count=sum(
            1 for lane in lanes if lane.lane_status == RuntimeWorktreeLaneStatus.proposal.value
        ),
        review_ready_count=sum(
            1 for lane in lanes if lane.lane_status == RuntimeWorktreeLaneStatus.review_ready.value
        ),
        mutation_blocked_count=sum(
            1
            for lane in lanes
            if lane.lane_status == RuntimeWorktreeLaneStatus.mutation_blocked.value
        ),
        blocked_authority_refs=list(RUNTIME_WORKTREE_PER_AGENT_BLOCKED_AUTHORITY_REFS),
        promotion_path_refs=[
            "promotion-path-ref:worktree-per-agent:exact-workspace-grant",
            "promotion-path-ref:worktree-per-agent:branch-naming",
            "promotion-path-ref:worktree-per-agent:checkpoint",
            "promotion-path-ref:worktree-per-agent:git-receipt",
            "promotion-path-ref:worktree-per-agent:rollback",
            "promotion-path-ref:worktree-per-agent:cli-parity",
        ],
        proof_refs=[
            RUNTIME_WORKTREE_PER_AGENT_PROOF_REF,
            "proof-ref:worktree-per-agent:branch-lane-proposals",
            "proof-ref:worktree-per-agent:git-mutation-blocked",
        ],
        verifier_refs=[RUNTIME_WORKTREE_PER_AGENT_VERIFIER_REF],
        next_safe_action_refs=[
            "next-safe-action-ref:worktree-per-agent:review-branch-policy",
            "next-safe-action-ref:worktree-per-agent:bind-checkpoint-plan",
            "next-safe-action-ref:worktree-per-agent:keep-git-mutation-blocked",
        ],
    )
