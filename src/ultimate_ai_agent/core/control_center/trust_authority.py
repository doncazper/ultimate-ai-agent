from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.control_center.founder_loop_runs_integration import (
    FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF,
)
from ultimate_ai_agent.core.control_center.operator_workspace_spine import (
    OPERATOR_WORKSPACE_SPINE_BLOCKED_AUTHORITY_REFS,
    OPERATOR_WORKSPACE_SPINE_CLI_REF,
    OPERATOR_WORKSPACE_SPINE_PROOF_REF,
    OPERATOR_WORKSPACE_SPINE_ROUTE_REF,
)
from ultimate_ai_agent.core.control_center.local_tasks import (
    FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF,
)
from ultimate_ai_agent.core.control_center.web_evidence_product_slice import (
    WEB_EVIDENCE_PRODUCT_SLICE_BLOCKED_AUTHORITY_REFS,
    WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_ROLLBACK_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_SAFE_DISABLE_REF,
)
from ultimate_ai_agent.core.connectors.connector_draft_proposals import (
    CONNECTOR_DRAFT_PROPOSAL_CLI_REF,
    CONNECTOR_DRAFT_PROPOSAL_CONTRACT_REF,
    CONNECTOR_DRAFT_PROPOSAL_PROOF_REF,
    CONNECTOR_DRAFT_PROPOSAL_ROUTE_REF,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.memory import (
    MEMORY_REVIEW_WRITE_ROLLBACK_REF,
    MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF,
)
from ultimate_ai_agent.core.providers.draft_summarize import (
    PROVIDER_DRAFT_SUMMARIZE_CLI_REF,
    PROVIDER_DRAFT_SUMMARIZE_LANE_REF,
    PROVIDER_DRAFT_SUMMARIZE_PROOF_REF,
    PROVIDER_DRAFT_SUMMARIZE_SAFE_DISABLE_REF,
)


TRUST_AUTHORITY_MATRIX_CONTRACT_REF = (
    "contract-ref:usable-authority-trust-authority-map:v1"
)
TRUST_AUTHORITY_MATRIX_ROUTE_REF = "GET /control-center/trust-authority/matrix"
TRUST_AUTHORITY_MATRIX_CLI_REF = (
    "python scripts/dev/uaa_founder_loop.py inspect-trust-authority"
)
TRUST_AUTHORITY_MATRIX_DOC_REF = "docs/control_center/USABLE_AUTHORITY_GRADUATION_PLAN.md"
TRUST_AUTHORITY_ALLOWED_CLI_INSPECTION_REFS: tuple[str, ...] = (
    TRUST_AUTHORITY_MATRIX_CLI_REF,
    "python scripts/dev/uaa_founder_loop.py inspect",
    "python scripts/dev/uaa_founder_loop.py inspect-start-here",
    "python scripts/dev/uaa_founder_loop.py inspect-action-work-queue",
    "python scripts/dev/uaa_founder_loop.py inspect-evidence-memory-binding",
    "python scripts/dev/uaa_founder_loop.py inspect-proof",
    "python scripts/dev/uaa_founder_loop.py inspect-web-evidence",
    "python scripts/dev/uaa_founder_loop.py memory-workbench",
    "python scripts/dev/uaa_founder_loop.py memory-context-manifest",
    "python scripts/dev/uaa_founder_loop.py memory-receipts",
    OPERATOR_WORKSPACE_SPINE_CLI_REF,
    PROVIDER_DRAFT_SUMMARIZE_CLI_REF,
    CONNECTOR_DRAFT_PROPOSAL_CLI_REF,
)

TrustAuthorityState = Literal[
    "available_now",
    "approval_required",
    "planned",
    "blocked",
]
TrustOperatorPosture = Literal[
    "enabled_read_only",
    "review_only",
    "approval_required",
    "planned",
    "blocked",
]
TrustAuthorityLaneKind = Literal[
    "read_preview",
    "draft_proposal",
    "reversible_local_mutation",
    "external_mutation",
    "background_standing_authority",
]

_DENIED_FLAGS = (
    "broad_approval_enabled",
    "standing_authority_enabled",
    "runtime_context_injection_enabled",
    "connector_write_enabled",
    "provider_model_call_enabled",
    "shell_subprocess_execution_enabled",
    "browser_execution_enabled",
    "background_autonomy_enabled",
    "production_authority_enabled",
)
_TIER_LABELS = {
    0: "UI/ephemeral state",
    1: "Local read/preview",
    2: "Local draft/proposal",
    3: "Reversible local mutation",
    4: "External mutation",
    5: "Background/standing authority",
}
_TIER_IDS = {
    0: "tier_0_ui_ephemeral_state",
    1: "tier_1_local_read_preview",
    2: "tier_2_local_draft_proposal",
    3: "tier_3_reversible_local_mutation",
    4: "tier_4_external_mutation",
    5: "tier_5_background_standing_authority",
}


class TrustAuthorityLane(BaseModel):
    lane_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=160)
    tier: int = Field(..., ge=0, le=5)
    tier_id: str = Field(..., min_length=1)
    tier_label: str = Field(..., min_length=1, max_length=120)
    lane_kind: TrustAuthorityLaneKind
    authority_state: TrustAuthorityState
    authority_state_label: str = Field(..., min_length=1, max_length=120)
    operator_posture: TrustOperatorPosture
    current_posture: str = Field(..., min_length=1, max_length=700)
    approval_posture: str = Field(..., min_length=1, max_length=500)
    operator_can_do_now: str = Field(..., min_length=1, max_length=500)
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    route_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    docs_refs: list[str] = Field(default_factory=list)
    cli_inspection_refs: list[str] = Field(default_factory=list)
    safe_disable_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    requires_exact_approval: bool = False
    requires_safe_disable: bool = False
    requires_rollback_posture: bool = False
    rollback_execution_enabled: bool = False
    safe_refs_only: bool = True
    control_center_grants_authority: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_lane(self) -> "TrustAuthorityLane":
        validate_execution_ref(self.lane_ref, "lane_ref")
        if self.tier_id != _TIER_IDS[self.tier]:
            raise ValueError("Trust authority lane tier id drift")
        if self.tier_label != _TIER_LABELS[self.tier]:
            raise ValueError("Trust authority lane tier label drift")
        for field_name in (
            "label",
            "authority_state_label",
            "current_posture",
            "approval_posture",
            "operator_can_do_now",
            "next_safe_action",
        ):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        _validate_text_list(self.route_refs, "route_refs")
        _validate_ref_list(self.proof_refs, "proof_refs")
        _validate_text_list(self.verifier_refs, "verifier_refs")
        _validate_text_list(self.docs_refs, "docs_refs")
        _validate_text_list(self.cli_inspection_refs, "cli_inspection_refs")
        for cli_ref in self.cli_inspection_refs:
            if cli_ref not in TRUST_AUTHORITY_ALLOWED_CLI_INSPECTION_REFS:
                raise ValueError("Trust authority CLI inspection ref is not registered")
        _validate_ref_list(self.safe_disable_refs, "safe_disable_refs")
        _validate_ref_list(self.rollback_refs, "rollback_refs")
        _validate_ref_list(self.promotion_path_refs, "promotion_path_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        if (
            not self.safe_refs_only
            or self.control_center_grants_authority
            or self.rollback_execution_enabled
        ):
            raise ValueError("Trust authority lanes must stay read-model only")
        if self.operator_posture != _expected_operator_posture(
            self.authority_state,
            self.tier,
        ):
            raise ValueError("Trust authority operator posture drift")
        if not self.cli_inspection_refs:
            raise ValueError("Trust authority lanes require CLI inspection refs")
        if self.tier >= 3 and (not self.safe_disable_refs or not self.rollback_refs):
            raise ValueError("Mutation authority lanes require rollback posture refs")
        if self.authority_state in {"planned", "blocked"} and not self.promotion_path_refs:
            raise ValueError("Blocked/planned lanes require promotion path refs")
        if self.tier >= 4 and self.authority_state != "blocked":
            raise ValueError("Tier 4 and Tier 5 authority remains blocked here")
        return self


class TrustAuthorityTierSummary(BaseModel):
    tier: int = Field(..., ge=0, le=5)
    tier_id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    available_now_count: int = Field(ge=0)
    approval_required_count: int = Field(ge=0)
    planned_count: int = Field(ge=0)
    blocked_count: int = Field(ge=0)
    operator_summary: str = Field(..., min_length=1, max_length=500)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_summary(self) -> "TrustAuthorityTierSummary":
        if self.tier_id != _TIER_IDS[self.tier]:
            raise ValueError("Trust authority tier id drift")
        if self.label != _TIER_LABELS[self.tier]:
            raise ValueError("Trust authority tier label drift")
        validate_safe_execution_text(self.operator_summary, "operator_summary")
        return self


class TrustAuthorityMatrixReadModel(BaseModel):
    schema_version: str = "control-center-trust-authority-matrix.v1"
    contract_ref: str = TRUST_AUTHORITY_MATRIX_CONTRACT_REF
    route_ref: str = TRUST_AUTHORITY_MATRIX_ROUTE_REF
    cli_ref: str = TRUST_AUTHORITY_MATRIX_CLI_REF
    status: str = "implemented_backend_owned_trust_authority_map"
    backend_owned: bool = True
    local_read_model_only: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    control_center_grants_authority: bool = False
    doctrine: str = Field(..., min_length=1, max_length=300)
    operator_summary: str = Field(..., min_length=1, max_length=700)
    lanes: list[TrustAuthorityLane] = Field(default_factory=list)
    tier_summaries: list[TrustAuthorityTierSummary] = Field(default_factory=list)
    available_now_lane_refs: list[str] = Field(default_factory=list)
    approval_required_lane_refs: list[str] = Field(default_factory=list)
    planned_lane_refs: list[str] = Field(default_factory=list)
    blocked_lane_refs: list[str] = Field(default_factory=list)
    route_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    docs_refs: list[str] = Field(default_factory=list)
    cli_inspection_refs: list[str] = Field(default_factory=list)
    safe_disable_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    broad_approval_enabled: bool = False
    standing_authority_enabled: bool = False
    runtime_context_injection_enabled: bool = False
    connector_write_enabled: bool = False
    provider_model_call_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_execution_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_matrix(self) -> "TrustAuthorityMatrixReadModel":
        if self.schema_version != "control-center-trust-authority-matrix.v1":
            raise ValueError("Trust authority matrix schema drift")
        if self.contract_ref != TRUST_AUTHORITY_MATRIX_CONTRACT_REF:
            raise ValueError("Trust authority matrix contract drift")
        if self.route_ref != TRUST_AUTHORITY_MATRIX_ROUTE_REF:
            raise ValueError("Trust authority matrix route drift")
        if self.cli_ref != TRUST_AUTHORITY_MATRIX_CLI_REF:
            raise ValueError("Trust authority matrix CLI drift")
        if not self.backend_owned or not self.local_read_model_only:
            raise ValueError("Trust authority matrix must stay backend-owned")
        if (
            not self.safe_refs_only
            or self.raw_content_included
            or self.control_center_grants_authority
        ):
            raise ValueError("Trust authority matrix must stay safe-ref only")
        for field_name in ("doctrine", "operator_summary", "next_safe_action"):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        _validate_text_list(self.route_refs, "route_refs")
        _validate_ref_list(self.proof_refs, "proof_refs")
        _validate_text_list(self.verifier_refs, "verifier_refs")
        _validate_text_list(self.docs_refs, "docs_refs")
        _validate_text_list(self.cli_inspection_refs, "cli_inspection_refs")
        _validate_ref_list(self.safe_disable_refs, "safe_disable_refs")
        _validate_ref_list(self.rollback_refs, "rollback_refs")
        _validate_ref_list(self.promotion_path_refs, "promotion_path_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _validate_ref_list(self.available_now_lane_refs, "available_now_lane_refs")
        _validate_ref_list(
            self.approval_required_lane_refs,
            "approval_required_lane_refs",
        )
        _validate_ref_list(self.planned_lane_refs, "planned_lane_refs")
        _validate_ref_list(self.blocked_lane_refs, "blocked_lane_refs")
        lane_refs = [lane.lane_ref for lane in self.lanes]
        if len(lane_refs) != len(set(lane_refs)):
            raise ValueError("Trust authority lane refs must be unique")
        if set(self.available_now_lane_refs) != {
            lane.lane_ref for lane in self.lanes if lane.authority_state == "available_now"
        }:
            raise ValueError("Trust authority available lane refs drift")
        if set(self.approval_required_lane_refs) != {
            lane.lane_ref
            for lane in self.lanes
            if lane.authority_state == "approval_required"
        }:
            raise ValueError("Trust authority approval lane refs drift")
        if set(self.planned_lane_refs) != {
            lane.lane_ref for lane in self.lanes if lane.authority_state == "planned"
        }:
            raise ValueError("Trust authority planned lane refs drift")
        if set(self.blocked_lane_refs) != {
            lane.lane_ref for lane in self.lanes if lane.authority_state == "blocked"
        }:
            raise ValueError("Trust authority blocked lane refs drift")
        if self.cli_inspection_refs != _merge_unique(
            [ref for lane in self.lanes for ref in lane.cli_inspection_refs]
        ):
            raise ValueError("Trust authority CLI inspection refs drift")
        if self.safe_disable_refs != _merge_unique(
            [ref for lane in self.lanes for ref in lane.safe_disable_refs]
        ):
            raise ValueError("Trust authority safe-disable refs drift")
        if self.rollback_refs != _merge_unique(
            [ref for lane in self.lanes for ref in lane.rollback_refs]
        ):
            raise ValueError("Trust authority rollback refs drift")
        if self.promotion_path_refs != _merge_unique(
            [ref for lane in self.lanes for ref in lane.promotion_path_refs]
        ):
            raise ValueError("Trust authority promotion path refs drift")
        if self.blocked_authority_refs != _merge_unique(
            [ref for lane in self.lanes for ref in lane.blocked_authority_refs]
        ):
            raise ValueError("Trust authority blocked authority refs drift")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag):
                raise ValueError(f"Trust authority matrix must not enable {flag}")
        return self


def build_trust_authority_matrix_read_model(
    *,
    today_summary: dict[str, Any],
) -> dict[str, Any]:
    runs = today_summary.get("founder_loop_runs_integration_read_model")
    primary_loop_proof_ref = (
        runs.get("primary_proof_ref")
        if isinstance(runs, dict) and isinstance(runs.get("primary_proof_ref"), str)
        else FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF
    )
    lanes = _trust_authority_lanes(primary_loop_proof_ref=primary_loop_proof_ref)
    tier_summaries = _tier_summaries(lanes)
    model = TrustAuthorityMatrixReadModel(
        doctrine="Earned authority, low friction by default, strict only where consequences justify it.",
        operator_summary=(
            "UAA can inspect local read models, previews, drafts, proof, evidence, "
            "memory review state, one exact local task commit lane, and one "
            "allowlisted web evidence preview lane now. External mutation and "
            "standing authority remain blocked."
        ),
        lanes=lanes,
        tier_summaries=tier_summaries,
        available_now_lane_refs=[
            lane.lane_ref for lane in lanes if lane.authority_state == "available_now"
        ],
        approval_required_lane_refs=[
            lane.lane_ref
            for lane in lanes
            if lane.authority_state == "approval_required"
        ],
        planned_lane_refs=[
            lane.lane_ref for lane in lanes if lane.authority_state == "planned"
        ],
        blocked_lane_refs=[
            lane.lane_ref for lane in lanes if lane.authority_state == "blocked"
        ],
        route_refs=_merge_unique(
            [TRUST_AUTHORITY_MATRIX_ROUTE_REF],
            [route for lane in lanes for route in lane.route_refs],
        ),
        proof_refs=_merge_unique([proof for lane in lanes for proof in lane.proof_refs]),
        verifier_refs=_merge_unique(
            [verifier for lane in lanes for verifier in lane.verifier_refs]
        ),
        docs_refs=_merge_unique(
            [TRUST_AUTHORITY_MATRIX_DOC_REF],
            [doc for lane in lanes for doc in lane.docs_refs],
        ),
        cli_inspection_refs=_merge_unique(
            [TRUST_AUTHORITY_MATRIX_CLI_REF],
            [ref for lane in lanes for ref in lane.cli_inspection_refs],
        ),
        safe_disable_refs=_merge_unique(
            [ref for lane in lanes for ref in lane.safe_disable_refs]
        ),
        rollback_refs=_merge_unique(
            [ref for lane in lanes for ref in lane.rollback_refs]
        ),
        promotion_path_refs=_merge_unique(
            [ref for lane in lanes for ref in lane.promotion_path_refs]
        ),
        blocked_authority_refs=_merge_unique(
            [ref for lane in lanes for ref in lane.blocked_authority_refs]
        ),
        next_safe_action=(
            "Use available local read, preview, draft, proof, evidence, and exact "
            "local receipt lanes; graduate external and standing authority only "
            "through separate verifier-backed PRs."
        ),
    )
    return model.model_dump(mode="json")


def _trust_authority_lanes(
    *,
    primary_loop_proof_ref: str,
) -> list[TrustAuthorityLane]:
    return [
        _lane(
            lane_ref="trust-lane:start-here-read",
            label="Start Here local loop summary",
            tier=1,
            lane_kind="read_preview",
            authority_state="available_now",
            current_posture="Backend-owned local read model for readiness, next safe action, proof refs, and blocked authority refs.",
            approval_posture="No approval required for local read and preview.",
            operator_can_do_now="Open Start Here and inspect the next safe governed loop step.",
            next_safe_action="Follow the linked local loop, then inspect Proof.",
            route_refs=["GET /control-center/start-here/summary"],
            proof_refs=[primary_loop_proof_ref],
            verifier_refs=["tests/test_control_center_start_here.py"],
            docs_refs=[TRUST_AUTHORITY_MATRIX_DOC_REF],
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                "python scripts/dev/uaa_founder_loop.py inspect-start-here",
            ],
        ),
        _lane(
            lane_ref="trust-lane:today-loop-read",
            label="Today daily loop",
            tier=1,
            lane_kind="read_preview",
            authority_state="available_now",
            current_posture="Backend-owned Today read model shows action, memory, evidence, proof, and run refs.",
            approval_posture="No approval required to read the local daily loop.",
            operator_can_do_now="Review Today, linked Action Inbox items, evidence, and memory cues.",
            next_safe_action="Review the next local action proposal or proof detail.",
            route_refs=["GET /control-center/today/summary"],
            proof_refs=[primary_loop_proof_ref],
            verifier_refs=["tests/test_control_center_api_routes.py"],
            docs_refs=["docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md"],
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                "python scripts/dev/uaa_founder_loop.py inspect",
            ],
        ),
        _lane(
            lane_ref="trust-lane:proof-detail-read",
            label="Universal Proof Detail",
            tier=1,
            lane_kind="read_preview",
            authority_state="available_now",
            current_posture="Proof index/detail expose safe refs, receipts, evidence, redaction, and next safe action only.",
            approval_posture="No approval required for proof inspection.",
            operator_can_do_now="Open proof records for the loop, actions, memory decisions, and evidence events.",
            next_safe_action="Use proof refs to verify what happened before approving any mutation.",
            route_refs=[
                "GET /control-center/proof/index",
                "GET /control-center/proof/{proof_ref}",
            ],
            proof_refs=[primary_loop_proof_ref],
            verifier_refs=["tests/test_control_center_proof_spine.py"],
            docs_refs=["docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md"],
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                "python scripts/dev/uaa_founder_loop.py inspect-proof",
            ],
        ),
        _lane(
            lane_ref="trust-lane:operator-workspace-spine",
            label="Operator Workspace Spine",
            tier=1,
            lane_kind="read_preview",
            authority_state="available_now",
            current_posture=(
                "Backend-owned safe-ref cockpit posture for workspace scope, "
                "Git posture, preview status, run-log posture, and coworker "
                "handoff metadata."
            ),
            approval_posture=(
                "No approval required to inspect the read model; any Git, "
                "workspace, command, preview, or coworker mutation requires a "
                "separate exact authority lane."
            ),
            operator_can_do_now=(
                "Inspect workspace, Git, preview, run-log, and coworker "
                "posture refs without editing, running, dispatching, or "
                "starting anything."
            ),
            next_safe_action=(
                "Use the CLI and Proof record to inspect posture; promote live "
                "Git status, command receipts, preview control, or coworker "
                "dispatch separately."
            ),
            route_refs=[OPERATOR_WORKSPACE_SPINE_ROUTE_REF],
            proof_refs=[OPERATOR_WORKSPACE_SPINE_PROOF_REF],
            verifier_refs=[
                "tests/test_beta_11_operator_workspace_spine.py",
                "scripts/verify_beta_11_operator_workspace_spine.py",
            ],
            docs_refs=["docs/control_center/OPERATOR_WORKSPACE_SPINE.md"],
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                OPERATOR_WORKSPACE_SPINE_CLI_REF,
            ],
            blocked_authority_refs=list(OPERATOR_WORKSPACE_SPINE_BLOCKED_AUTHORITY_REFS),
        ),
        _lane(
            lane_ref="trust-lane:action-inbox-work-queue",
            label="Action Inbox work queue",
            tier=1,
            lane_kind="read_preview",
            authority_state="available_now",
            current_posture="Action Inbox shows backend-owned queue state, lane counts, next item posture, and proof refs.",
            approval_posture="No approval required to inspect the queue; approval is required for exact local commits.",
            operator_can_do_now="Review requested, blocked, receipt-recorded, and no-authority items without executing them.",
            next_safe_action="Pick a local task commit candidate only when exact approval is available.",
            route_refs=["GET /control-center/actions/inbox"],
            proof_refs=[primary_loop_proof_ref],
            verifier_refs=["tests/test_action_inbox_work_queue.py"],
            docs_refs=["docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md"],
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                "python scripts/dev/uaa_founder_loop.py inspect-action-work-queue",
            ],
        ),
        _lane(
            lane_ref="trust-lane:local-task-commit",
            label="Exact local task commit",
            tier=3,
            lane_kind="reversible_local_mutation",
            authority_state="approval_required",
            current_posture="One local UAA task record lane can commit only with exact LocalApprovalAuthority scope, idempotency, receipt, evidence, proof, and safe-disable posture.",
            approval_posture="Exact local approval required; approval refs are identifiers until scope validates.",
            operator_can_do_now="Commit the proven local task lane only through the backend receipt route.",
            next_safe_action="Inspect the local task receipt and proof detail after commit.",
            route_refs=[
                "POST /control-center/actions/{action_id}/local-task/commit",
            ],
            proof_refs=[primary_loop_proof_ref],
            verifier_refs=[
                "tests/test_fcc_action_001_approval_bound_local_micro_lanes.py",
                "tests/test_action_inbox_work_queue.py",
            ],
            docs_refs=["docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md"],
            requires_exact_approval=True,
            requires_safe_disable=True,
            requires_rollback_posture=True,
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                "python scripts/dev/uaa_founder_loop.py inspect-action-work-queue",
            ],
            safe_disable_refs=[FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF],
            rollback_refs=[FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF],
            promotion_path_refs=[
                "promotion-path-ref:trust:local-task-commit:additional-local-lanes",
            ],
            blocked_authority_refs=[
                "blocked-state:local-task-commit:no-external-side-effects"
            ],
        ),
        _lane(
            lane_ref="trust-lane:memory-review-read",
            label="Memory Review and loop binding",
            tier=1,
            lane_kind="read_preview",
            authority_state="available_now",
            current_posture="Memory Review and Evidence/Memory loop binding explain candidate, source, why-shown, action, run, proof, and evidence refs.",
            approval_posture="No approval required to inspect memory recall and why-shown refs.",
            operator_can_do_now="Inspect why memory appeared and which evidence supports it.",
            next_safe_action="Treat memory as recall, not truth, before recording a decision.",
            route_refs=["GET /control-center/memory/review"],
            proof_refs=[primary_loop_proof_ref],
            verifier_refs=[
                "tests/test_evidence_memory_loop_binding.py",
                "tests/test_fcc_v1_005_memory_review_decisions.py",
            ],
            docs_refs=["docs/control_center/PRODUCT_LANGUAGE_RULES.md"],
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                "python scripts/dev/uaa_founder_loop.py inspect-evidence-memory-binding",
            ],
            blocked_authority_refs=[
                "blocked-state:trust:no-memory-truth-authority",
                "blocked-state:trust:no-runtime-context-injection",
            ],
        ),
        _lane(
            lane_ref="trust-lane:reviewed-memory-write",
            label="Reviewed Memory accept/correct",
            tier=3,
            lane_kind="reversible_local_mutation",
            authority_state="approval_required",
            current_posture="Accept/correct may create reviewed recall-only local memory records after exact approval and receipt validation.",
            approval_posture="Exact Memory Review decision authority required; no automatic memory write.",
            operator_can_do_now="Accept or correct only reviewed Memory Review candidates through backend receipt routes.",
            next_safe_action="Inspect receipt and evidence refs; keep broad memory write blocked.",
            route_refs=[
                "POST /control-center/memory/review/{candidate_ref}/accept",
                "POST /control-center/memory/review/{candidate_ref}/correct",
            ],
            proof_refs=[primary_loop_proof_ref],
            verifier_refs=[
                "tests/test_fcc_v1_005_memory_review_decisions.py",
            ],
            docs_refs=["docs/control_center/FCC_V1_005_MEMORY_REVIEW_DECISIONS.md"],
            requires_exact_approval=True,
            requires_safe_disable=True,
            requires_rollback_posture=True,
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                "python scripts/dev/uaa_founder_loop.py memory-receipts",
            ],
            safe_disable_refs=[MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF],
            rollback_refs=[MEMORY_REVIEW_WRITE_ROLLBACK_REF],
            promotion_path_refs=[
                "promotion-path-ref:trust:reviewed-memory-write:broad-memory-separate-contract",
                "promotion-path-ref:trust:reviewed-memory-write:context-injection-separate-contract",
            ],
            blocked_authority_refs=[
                "blocked-state:trust:no-automatic-memory-write",
                "blocked-state:trust:no-memory-delete-export",
            ],
        ),
        _lane(
            lane_ref="trust-lane:evidence-timeline-read",
            label="Evidence Timeline",
            tier=1,
            lane_kind="read_preview",
            authority_state="available_now",
            current_posture="Evidence Timeline is read-only safe-ref history linked to actions, memory, runs, receipts, and proof.",
            approval_posture="No approval required for evidence inspection.",
            operator_can_do_now="Inspect what changed, why it was recorded, and which proof refs support it.",
            next_safe_action="Use Evidence to verify decisions; do not execute from evidence.",
            route_refs=["GET /control-center/evidence/timeline"],
            proof_refs=[primary_loop_proof_ref],
            verifier_refs=[
                "tests/test_fcc_v1_006_evidence_timeline_productization.py",
                "tests/test_evidence_memory_loop_binding.py",
            ],
            docs_refs=["docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md"],
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                "python scripts/dev/uaa_founder_loop.py inspect",
            ],
        ),
        _lane(
            lane_ref="trust-lane:local-draft-proposal",
            label="Local drafts and proposals",
            tier=2,
            lane_kind="draft_proposal",
            authority_state="available_now",
            current_posture="Local action, plan, context-pack, and file proposals can exist as review artifacts without external side effects.",
            approval_posture="No approval required to create a local draft/proposal; approval is required to commit, send, apply, or execute.",
            operator_can_do_now="Review drafts and proposals without treating them as completed work.",
            next_safe_action="Approve only the exact commit/apply/send lane when separately proven.",
            route_refs=[
                "GET /control-center/memory/context-packs",
                "GET /control-center/memory/context-packs/{context_pack_ref}/preview",
            ],
            proof_refs=["proof-ref:proposal:local-review"],
            verifier_refs=["tests/test_governed_memory_context_pack_proposals.py"],
            docs_refs=[TRUST_AUTHORITY_MATRIX_DOC_REF],
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                "python scripts/dev/uaa_founder_loop.py memory-context-manifest",
            ],
            promotion_path_refs=[
                "promotion-path-ref:trust:local-draft-proposal:exact-apply-lane",
                "promotion-path-ref:trust:local-draft-proposal:send-write-separate-contract",
            ],
            blocked_authority_refs=[
                "blocked-state:trust:draft-is-not-send",
                "blocked-state:trust:preview-is-not-execution",
            ],
        ),
        _lane(
            lane_ref="trust-lane:web-evidence-product-slice",
            label="Web evidence product slice",
            tier=1,
            lane_kind="read_preview",
            authority_state="available_now",
            current_posture="One operator-requested allowlisted HTTPS GET preview can run through WebAccessGateway and attach safe receipt refs to the local loop.",
            approval_posture="No action approval required for Tier 1 read-only preview; browser action, session state, downloads, uploads, mutation methods, context, memory, provider, connector, and production authority remain blocked.",
            operator_can_do_now="Attach one allowlisted web evidence preview from Proof or the CLI and inspect its receipt refs.",
            next_safe_action="Open Web Evidence proof and inspect receipt, audit, preview, and blocked-authority refs.",
            route_refs=[WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF],
            proof_refs=[WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF],
            verifier_refs=[
                "tests/test_web_evidence_product_slice.py",
                "scripts/verify_web_runtime_authority.py",
            ],
            docs_refs=["docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md"],
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                "python scripts/dev/uaa_founder_loop.py inspect-web-evidence",
            ],
            safe_disable_refs=[WEB_EVIDENCE_PRODUCT_SLICE_SAFE_DISABLE_REF],
            rollback_refs=[WEB_EVIDENCE_PRODUCT_SLICE_ROLLBACK_REF],
            promotion_path_refs=[
                "promotion-path-ref:trust:web-evidence:browser-observe-separate-contract",
                "promotion-path-ref:trust:web-evidence:browser-action-separate-contract",
            ],
            blocked_authority_refs=list(WEB_EVIDENCE_PRODUCT_SLICE_BLOCKED_AUTHORITY_REFS),
        ),
        _lane(
            lane_ref="trust-lane:provider-draft-summarize",
            label="Provider draft/summarize",
            tier=2,
            lane_kind="draft_proposal",
            authority_state="available_now",
            current_posture="The exact provider draft/summarize core and CLI lane can produce review-only draft refs when the existing tiny exact-approved provider path is satisfied; default Control Center invocation remains blocked.",
            approval_posture="Each provider attempt requires exact scope, CostGovernor posture, durable receipts, and blocked output authority; the draft is not truth, send authority, memory, action execution, or connector authority.",
            operator_can_do_now="Inspect the provider draft/summarize CLI posture and fixture proof; do not call providers from Trust.",
            next_safe_action="Use the provider draft/summarize lane only through its exact core/CLI wrapper; live provider setup and default UI invocation remain separately blocked.",
            route_refs=[PROVIDER_DRAFT_SUMMARIZE_LANE_REF],
            proof_refs=[PROVIDER_DRAFT_SUMMARIZE_PROOF_REF],
            verifier_refs=[
                "tests/test_provider_draft_summarize_lane.py",
                "scripts/inspect_provider_draft_summarize_lane.py",
            ],
            docs_refs=[
                "docs/control_center/PROVIDER_DRAFT_SUMMARIZE_MICRO_LANE.md",
                PROVIDER_DRAFT_SUMMARIZE_CLI_REF,
            ],
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                PROVIDER_DRAFT_SUMMARIZE_CLI_REF,
            ],
            safe_disable_refs=[PROVIDER_DRAFT_SUMMARIZE_SAFE_DISABLE_REF],
            rollback_refs=[
                "rollback-ref:provider-draft-summarize:discard-local-draft",
            ],
            promotion_path_refs=[
                "promotion-path-ref:trust:provider-draft-summarize:live-provider-separate-contract",
                "promotion-path-ref:trust:provider-draft-summarize:ui-invocation-separate-contract",
            ],
            blocked_authority_refs=[
                "blocked-state:trust:no-provider-model-call",
                "blocked-state:trust:no-provider-output-authority",
                "blocked-state:trust:no-provider-default-ui-invocation",
            ],
        ),
        _lane(
            lane_ref="trust-lane:connector-draft-only",
            label="Connector draft-only",
            tier=2,
            lane_kind="draft_proposal",
            authority_state="available_now",
            current_posture="Backend-owned connector draft proposals are available as safe refs for operator review through Source Readiness; live connector runtime, sends, writes, account sync, and source ingestion remain blocked.",
            approval_posture="No approval is required to inspect draft proposal refs. Exact approval, idempotency, receipt, rollback, and safe-disable posture are still required before any future send/write.",
            operator_can_do_now="Inspect email-response and calendar-hold draft proposal refs from Inbox, Source Readiness, or the CLI.",
            next_safe_action="Review connector draft proposals only as local safe-ref artifacts; graduate a separate test-send/write lane before any external effect.",
            route_refs=[CONNECTOR_DRAFT_PROPOSAL_ROUTE_REF],
            proof_refs=[CONNECTOR_DRAFT_PROPOSAL_PROOF_REF],
            verifier_refs=[
                "tests/test_connector_draft_proposals.py",
                CONNECTOR_DRAFT_PROPOSAL_CLI_REF,
            ],
            docs_refs=[
                "docs/control_center/CONNECTOR_DRAFT_ONLY_PROPOSALS.md",
                CONNECTOR_DRAFT_PROPOSAL_CONTRACT_REF,
            ],
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                CONNECTOR_DRAFT_PROPOSAL_CLI_REF,
            ],
            safe_disable_refs=[
                "safe-disable-ref:connector-draft-only:disable-local-draft-surface",
            ],
            rollback_refs=[
                "rollback-ref:connector-draft-only:discard-local-draft",
            ],
            promotion_path_refs=[
                "promotion-path-ref:trust:connector-draft-only:test-send-separate-contract",
                "promotion-path-ref:trust:connector-draft-only:oauth-read-separate-contract",
            ],
            blocked_authority_refs=[
                "blocked-state:trust:no-connector-send",
                "blocked-state:trust:no-connector-write",
            ],
        ),
        _lane(
            lane_ref="trust-lane:external-mutations",
            label="External sends/writes and broad runtime actions",
            tier=4,
            lane_kind="external_mutation",
            authority_state="blocked",
            current_posture="Connector writes/sends, shell/subprocess execution, browser actions, broad provider/model calls, and external side effects remain blocked.",
            approval_posture="Future Tier 4 lanes require exact approval, idempotency, receipts, safe-disable, rollback posture, redaction, and tests.",
            operator_can_do_now="Use local read, preview, draft, and exact local receipt lanes only.",
            next_safe_action="Promote one external mutation lane at a time with a verifier-backed contract.",
            route_refs=[],
            proof_refs=["proof-ref:external-mutation:blocked"],
            verifier_refs=["scripts/verify_operational_maturity.py"],
            docs_refs=[TRUST_AUTHORITY_MATRIX_DOC_REF],
            cli_inspection_refs=[TRUST_AUTHORITY_MATRIX_CLI_REF],
            safe_disable_refs=[
                "safe-disable-ref:trust:external-mutations:default-deny",
            ],
            rollback_refs=[
                "rollback-ref:trust:external-mutations:future-lane-required",
            ],
            promotion_path_refs=[
                "promotion-path-ref:trust:external-mutations:connector-write-send",
                "promotion-path-ref:trust:external-mutations:shell-subprocess",
                "promotion-path-ref:trust:external-mutations:browser-action",
                "promotion-path-ref:trust:external-mutations:provider-model-call",
            ],
            blocked_authority_refs=[
                "blocked-state:trust:no-connector-write-send",
                "blocked-state:trust:no-shell-subprocess-execution",
                "blocked-state:trust:no-browser-execution",
                "blocked-state:trust:no-broad-provider-model-call",
            ],
            requires_exact_approval=True,
            requires_safe_disable=True,
            requires_rollback_posture=True,
        ),
        _lane(
            lane_ref="trust-lane:background-standing-authority",
            label="Background and standing authority",
            tier=5,
            lane_kind="background_standing_authority",
            authority_state="blocked",
            current_posture="Schedulers, background workers, auto-send, standing provider calls, and broad autonomy remain blocked.",
            approval_posture="Separate Tier 5 graduation is required with revocation, pause/cancel/kill, queue inspection, budgets, replay/audit, observability, and safe-disable.",
            operator_can_do_now="Run foreground local review loops only.",
            next_safe_action="Do not add standing authority until exact scope and kill-switch posture are proven.",
            route_refs=[],
            proof_refs=["proof-ref:background-authority:blocked"],
            verifier_refs=["scripts/verify_operational_maturity.py"],
            docs_refs=[TRUST_AUTHORITY_MATRIX_DOC_REF],
            cli_inspection_refs=[TRUST_AUTHORITY_MATRIX_CLI_REF],
            safe_disable_refs=[
                "safe-disable-ref:trust:background-standing-authority:default-deny",
            ],
            rollback_refs=[
                "rollback-ref:trust:background-standing-authority:future-lane-required",
            ],
            promotion_path_refs=[
                "promotion-path-ref:trust:background-standing-authority:revocation-and-kill-switch",
                "promotion-path-ref:trust:background-standing-authority:queue-inspection",
                "promotion-path-ref:trust:background-standing-authority:budget-and-replay",
            ],
            blocked_authority_refs=[
                "blocked-state:trust:no-background-autonomy",
                "blocked-state:trust:no-standing-authority",
                "blocked-state:trust:no-production-authority",
            ],
            requires_exact_approval=True,
            requires_safe_disable=True,
            requires_rollback_posture=True,
        ),
    ]


def _lane(
    *,
    lane_ref: str,
    label: str,
    tier: int,
    lane_kind: TrustAuthorityLaneKind,
    authority_state: TrustAuthorityState,
    current_posture: str,
    approval_posture: str,
    operator_can_do_now: str,
    next_safe_action: str,
    route_refs: list[str],
    proof_refs: list[str],
    verifier_refs: list[str],
    docs_refs: list[str],
    authority_state_label: str | None = None,
    operator_posture: TrustOperatorPosture | None = None,
    cli_inspection_refs: list[str] | None = None,
    safe_disable_refs: list[str] | None = None,
    rollback_refs: list[str] | None = None,
    promotion_path_refs: list[str] | None = None,
    blocked_authority_refs: list[str] | None = None,
    requires_exact_approval: bool = False,
    requires_safe_disable: bool = False,
    requires_rollback_posture: bool = False,
) -> TrustAuthorityLane:
    lane_suffix = _lane_suffix(lane_ref)
    return TrustAuthorityLane(
        lane_ref=lane_ref,
        label=label,
        tier=tier,
        tier_id=_TIER_IDS[tier],
        tier_label=_TIER_LABELS[tier],
        lane_kind=lane_kind,
        authority_state=authority_state,
        authority_state_label=authority_state_label
        or _authority_state_label(authority_state),
        operator_posture=operator_posture
        or _expected_operator_posture(authority_state, tier),
        current_posture=current_posture,
        approval_posture=approval_posture,
        operator_can_do_now=operator_can_do_now,
        next_safe_action=next_safe_action,
        route_refs=route_refs,
        proof_refs=proof_refs,
        verifier_refs=verifier_refs,
        docs_refs=docs_refs,
        cli_inspection_refs=cli_inspection_refs or [TRUST_AUTHORITY_MATRIX_CLI_REF],
        safe_disable_refs=safe_disable_refs
        or [f"safe-disable-ref:trust:{lane_suffix}:read-model-only"],
        rollback_refs=rollback_refs or [f"rollback-ref:trust:{lane_suffix}:no-mutation"],
        promotion_path_refs=promotion_path_refs
        or [f"promotion-path-ref:trust:{lane_suffix}:exact-scope-required"],
        blocked_authority_refs=blocked_authority_refs or [],
        requires_exact_approval=requires_exact_approval,
        requires_safe_disable=requires_safe_disable,
        requires_rollback_posture=requires_rollback_posture,
    )


def _tier_summaries(lanes: list[TrustAuthorityLane]) -> list[TrustAuthorityTierSummary]:
    summaries: list[TrustAuthorityTierSummary] = []
    for tier in range(6):
        tier_lanes = [lane for lane in lanes if lane.tier == tier]
        summaries.append(
            TrustAuthorityTierSummary(
                tier=tier,
                tier_id=_TIER_IDS[tier],
                label=_TIER_LABELS[tier],
                available_now_count=sum(
                    lane.authority_state == "available_now" for lane in tier_lanes
                ),
                approval_required_count=sum(
                    lane.authority_state == "approval_required" for lane in tier_lanes
                ),
                planned_count=sum(
                    lane.authority_state == "planned" for lane in tier_lanes
                ),
                blocked_count=sum(
                    lane.authority_state == "blocked" for lane in tier_lanes
                ),
                operator_summary=_tier_operator_summary(tier, tier_lanes),
            )
        )
    return summaries


def _tier_operator_summary(tier: int, lanes: list[TrustAuthorityLane]) -> str:
    available = sum(lane.authority_state == "available_now" for lane in lanes)
    approval = sum(lane.authority_state == "approval_required" for lane in lanes)
    planned = sum(lane.authority_state == "planned" for lane in lanes)
    blocked = sum(lane.authority_state == "blocked" for lane in lanes)
    return (
        f"{_TIER_LABELS[tier]}: {available} available now, {approval} require "
        f"approval, {planned} planned, {blocked} blocked."
    )


def _expected_operator_posture(
    authority_state: TrustAuthorityState,
    tier: int,
) -> TrustOperatorPosture:
    if authority_state == "available_now":
        return "review_only" if tier == 2 else "enabled_read_only"
    if authority_state == "approval_required":
        return "approval_required"
    if authority_state == "planned":
        return "planned"
    return "blocked"


def _authority_state_label(authority_state: TrustAuthorityState) -> str:
    return authority_state.replace("_", " ")


def _lane_suffix(lane_ref: str) -> str:
    suffix = lane_ref.removeprefix("trust-lane:").replace("_", "-")
    return suffix or "unknown"


def _validate_ref_list(refs: list[str], field_name: str) -> None:
    for ref in refs:
        validate_execution_ref(ref, field_name)


def _validate_text_list(values: list[str], field_name: str) -> None:
    for value in values:
        validate_safe_execution_text(value, field_name)


def _merge_unique(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for value in group:
            if value not in merged:
                merged.append(value)
    return merged
