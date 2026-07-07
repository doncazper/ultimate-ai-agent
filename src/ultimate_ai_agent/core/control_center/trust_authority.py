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
TRUST_AUTHORITY_MATRIX_DOC_REF = (
    "docs/strategy/UAA_AUTHORITY_MODES_AND_MISSION_LEASES.md"
)
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
    "python scripts/dev/uaa_work_board.py inspect-board",
    "python scripts/dev/uaa_work_board.py inspect-reorder-receipt",
    "python scripts/dev/uaa_runtime.py capabilities --json",
    "python scripts/dev/uaa_runtime.py status --json",
    "python scripts/inspect_model_provider_control_plane.py",
    "python scripts/inspect_tiny_provider_invocation_lane.py",
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
    authority_domain_ref: str = Field(..., min_length=1)
    authority_capability_ref: str = Field(..., min_length=1)
    required_authority_mode: str = Field(..., min_length=1, max_length=120)
    authority_lease_requirement_ref: str = Field(..., min_length=1)
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
        _validate_ref_list(
            [
                self.authority_domain_ref,
                self.authority_capability_ref,
                self.authority_lease_requirement_ref,
            ],
            "authority_lease_mapping_refs",
        )
        validate_safe_execution_text(self.required_authority_mode, "required_authority_mode")
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
        if self.tier >= 4 and self.authority_state == "available_now":
            raise ValueError("Tier 4 and Tier 5 authority requires exact approval")
        if self.tier >= 4 and self.authority_state == "approval_required":
            if (
                not self.requires_exact_approval
                or not self.requires_safe_disable
                or not self.requires_rollback_posture
            ):
                raise ValueError("Tier 4 and Tier 5 lanes require exact safeguards")
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
            "memory review state, exact local receipt lanes, governed runtime "
            "capabilities, and high-authority mode/domain requirements that remain "
            "blocked until an active AuthorityLease plus exact route, CLI, receipt, "
            "rollback, and verifier contracts exist."
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
            "local receipt capabilities; use Trust rows to inspect the required "
            "AuthorityLease mode, domain, and capability before any external or "
            "standing authority is proposed."
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
                "separate AuthorityLease-gated capability."
            ),
            operator_can_do_now=(
                "Inspect workspace, Git, preview, run-log, and coworker "
                "posture refs without editing, running, dispatching, or "
                "starting anything."
            ),
            next_safe_action=(
                "Use the CLI and Proof record to inspect posture; add live Git "
                "status, command receipts, preview control, or coworker dispatch "
                "as separate AuthorityLease-gated capabilities."
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
            lane_ref="trust-lane:work-board-durable-mutation",
            label="Work Board durable mutation and persisted reorder",
            tier=3,
            lane_kind="reversible_local_mutation",
            authority_state="approval_required",
            current_posture=(
                "Persisted Work Board reorder is an AuthorityLease-gated local "
                "mutation capability requiring approval, idempotency, receipt, "
                "safe-disable, and rollback posture before persistence; card "
                "create/archive/assignment remain separate unsupported capabilities."
            ),
            approval_posture=(
                "Exact Work Board approval required for a selected reorder; "
                "local drag/drop preview and card mutation controls are not authority."
            ),
            operator_can_do_now=(
                "Use the Work Board preview, then submit only the exact approved "
                "reorder through Python Core once the approval scope validates."
            ),
            next_safe_action=(
                "Bind persisted reorder to a Work Board receipt and rollback ref."
            ),
            route_refs=[
                "GET /control-center/work-board",
                "POST /control-center/work-board/reorder",
            ],
            proof_refs=["proof-ref:work-board-kanban-shell"],
            verifier_refs=[
                "tests/test_control_center_work_board.py",
                "apps/control-center/src/App.test.tsx",
            ],
            docs_refs=[
                "docs/prompts/kanban_board/00_execute_kanban_board_end_to_end.prompt.md",
                TRUST_AUTHORITY_MATRIX_DOC_REF,
            ],
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                "python scripts/dev/uaa_work_board.py inspect-board",
                "python scripts/dev/uaa_work_board.py inspect-reorder-receipt",
            ],
            safe_disable_refs=[
                "safe-disable-ref:work-board:durable-mutation",
            ],
            rollback_refs=[
                "rollback-ref:work-board:restore-previous-board-order",
            ],
            promotion_path_refs=[
                "promotion-path-ref:work-board:durable-mutation-route",
                "promotion-path-ref:work-board:persisted-reorder-receipt",
            ],
            blocked_authority_refs=[
                "blocked-state:work-board:no-broad-board-mutation",
                "blocked-state:work-board:no-issue-tracker-write-from-board",
            ],
            requires_exact_approval=True,
            requires_safe_disable=True,
            requires_rollback_posture=True,
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
            lane_ref="trust-lane:model-slot-posture",
            label="Main and auxiliary model slot posture",
            tier=1,
            lane_kind="read_preview",
            authority_state="available_now",
            current_posture=(
                "Model slots for main thinking, summarization, title, approval "
                "scoring, compression, retrieval, vision, and review are "
                "visible as backend-owned routing intent only."
            ),
            approval_posture=(
                "No approval is required to inspect slot posture; any live "
                "model call, provider SDK use, runtime default mutation, or "
                "hidden model routing remains separately blocked."
            ),
            operator_can_do_now=(
                "Inspect which slots are intended, planned, unavailable, or "
                "runtime-reported without invoking or switching models."
            ),
            next_safe_action=(
                "Use the model/provider control plane to review slot warnings; "
                "promote exact model invocation separately with traces, cost, "
                "truth envelopes, and receipts."
            ),
            route_refs=["GET /control-center/providers/runtime-control-plane"],
            proof_refs=[
                "proof-ref:hermes-runtime-adoption:phase-08:model-slot-posture"
            ],
            verifier_refs=["scripts/verify_hermes_runtime_adoption_phase_08.py"],
            docs_refs=["docs/runtime/UAA_HERMES_RUNTIME_MODEL_SLOT_POSTURE.md"],
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                "python scripts/inspect_model_provider_control_plane.py",
            ],
            blocked_authority_refs=[
                "blocked-state:model-slot:live-auxiliary-model-calls",
                "blocked-state:model-slot:provider-sdk-use",
                "blocked-state:model-slot:runtime-selection-mutation",
                "blocked-state:model-slot:hidden-model-routing",
            ],
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
            next_safe_action="Review connector draft proposals only as local safe-ref artifacts; add a separately scoped connector send/write AuthorityLease capability before any external effect.",
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
            lane_ref="trust-lane:governed-command-execution",
            label="Governed allowlisted command execution",
            tier=3,
            lane_kind="reversible_local_mutation",
            authority_state="approval_required",
            current_posture=(
                "RuntimeGateway supports argv-only allowlisted local commands "
                "with redacted receipts; arbitrary shell strings, networked "
                "commands, installs, and raw output persistence remain denied."
            ),
            approval_posture=(
                "Exact Action Inbox approval envelope required for mutation-capable "
                "command intents; read-only git status stays allowlisted."
            ),
            operator_can_do_now=(
                "Run governed command capabilities through `/api/runtime/command/run` "
                "when the intent is allowlisted and the approval envelope validates."
            ),
            next_safe_action="Inspect runtime receipt refs and keep arbitrary shell blocked.",
            route_refs=[
                "POST /api/runtime/command/run",
                "GET /api/runtime/capabilities",
            ],
            proof_refs=["proof-ref:governed-runtime-command-run"],
            verifier_refs=[
                "tests/test_governed_runtime_contracts.py",
                "tests/test_governed_runtime_api_routes.py",
            ],
            docs_refs=["docs/prompts/governed_runtime_pilot/00_execute_end_to_end_merge_push_harden.prompt.md"],
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                "python scripts/dev/uaa_runtime.py capabilities --json",
                "python scripts/dev/uaa_runtime.py status --json",
            ],
            safe_disable_refs=["safe-disable-ref:governed-runtime-pilot"],
            rollback_refs=["rollback-ref:governed-runtime-pilot:disable-profile"],
            promotion_path_refs=[
                "promotion-path-ref:runtime:allowlisted-command-expansion",
            ],
            blocked_authority_refs=[
                "blocked-authority:runtime-unrestricted-command-execution",
                "blocked-authority:runtime-command-network-access",
            ],
            requires_exact_approval=True,
            requires_safe_disable=True,
            requires_rollback_posture=True,
        ),
        _lane(
            lane_ref="trust-lane:provider-model-invocation",
            label="Exact approved provider/model invocation",
            tier=4,
            lane_kind="external_mutation",
            authority_state="blocked",
            current_posture=(
                "Provider/model invocation remains blocked as a broad UAA runtime "
                "authority. Existing local evidence is lease-scope proof only; "
                "Trust does not invoke providers or models."
            ),
            approval_posture=(
                "Future execution requires provider_model_calls/execute "
                "AuthorityLease scope plus exact provider, model, access ref, cost "
                "estimate, budget, idempotency, receipt, safe-disable, and rollback binding."
            ),
            operator_can_do_now=(
                "Inspect local runtime and lease-scope proof refs only; do not "
                "treat Trust as provider/model execution."
            ),
            next_safe_action="Inspect model/provider receipts; do not treat output as authority.",
            route_refs=[
                "POST /api/runtime/local-model/call",
                "provider-lane-ref:tiny-exact-approved-provider-invocation",
            ],
            proof_refs=[
                PROVIDER_DRAFT_SUMMARIZE_PROOF_REF,
                "proof-ref:provider-runtime:tiny-exact-approved",
            ],
            verifier_refs=[
                "tests/test_tiny_provider_invocation_lane.py",
                "tests/test_tiny_live_provider_adapter.py",
                "tests/test_governed_runtime_api_routes.py",
            ],
            docs_refs=[
                "docs/control_center/EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md",
                "docs/control_center/PROVIDER_DRAFT_SUMMARIZE_MICRO_LANE.md",
            ],
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                "python scripts/inspect_tiny_provider_invocation_lane.py",
                PROVIDER_DRAFT_SUMMARIZE_CLI_REF,
            ],
            safe_disable_refs=[
                PROVIDER_DRAFT_SUMMARIZE_SAFE_DISABLE_REF,
                "safe-disable-ref:provider-runtime:tiny-exact-approved",
            ],
            rollback_refs=[
                "rollback-ref:provider-runtime:discard-receipt-bound-draft",
            ],
            promotion_path_refs=[
                "promotion-path-ref:provider-runtime:additional-provider-adapters",
            ],
            blocked_authority_refs=[
                "blocked-state:trust:no-provider-output-authority",
                "blocked-state:trust:no-broad-provider-router",
            ],
            requires_exact_approval=True,
            requires_safe_disable=True,
            requires_rollback_posture=True,
        ),
        _lane(
            lane_ref="trust-lane:issue-tracker-sync",
            label="Issue tracker sync",
            tier=4,
            lane_kind="external_mutation",
            authority_state="blocked",
            current_posture=(
                "Issue tracker sync remains blocked until an exact external "
                "mutation route, adapter, receipt, safe-disable, rollback, and "
                "CLI inspection lane exists."
            ),
            approval_posture="Future exact issue workspace, project, item, field, and write action approval required.",
            operator_can_do_now="Inspect the planned authority-scope path only; no issue tracker write is available from UAA.",
            next_safe_action="Implement a route/API/CLI/receipt capability before enabling issue sync.",
            route_refs=["external-lane-ref:issue-tracker-sync-exact-approved"],
            proof_refs=["proof-ref:issue-tracker-sync:exact-approved"],
            verifier_refs=["scripts/verify_operational_maturity.py"],
            docs_refs=[TRUST_AUTHORITY_MATRIX_DOC_REF],
            cli_inspection_refs=[TRUST_AUTHORITY_MATRIX_CLI_REF],
            safe_disable_refs=["safe-disable-ref:issue-tracker-sync:exact-approved"],
            rollback_refs=["rollback-ref:issue-tracker-sync:compensating-update-required"],
            promotion_path_refs=["promotion-path-ref:issue-tracker-sync:adapter-implementation"],
            blocked_authority_refs=[
                "blocked-state:issue-tracker-sync:no-bulk-write",
                "blocked-state:issue-tracker-sync:no-unapproved-project-access",
            ],
            requires_exact_approval=True,
            requires_safe_disable=True,
            requires_rollback_posture=True,
        ),
        _lane(
            lane_ref="trust-lane:connector-write-low-risk",
            label="Connector writes",
            tier=4,
            lane_kind="external_mutation",
            authority_state="blocked",
            current_posture=(
                "Connector writes remain blocked in UAA runtime. Connector draft "
                "proposals are available as local review artifacts only."
            ),
            approval_posture="Future exact connector, dry-run, write target, safe result, audit, replay, revocation, and approval refs required.",
            operator_can_do_now="Use connector draft proposals only; no connector send/write executes.",
            next_safe_action="Implement a live adapter scope with receipts before enabling connector writes.",
            route_refs=[CONNECTOR_DRAFT_PROPOSAL_ROUTE_REF],
            proof_refs=["proof-ref:connector-write:low-risk-exact"],
            verifier_refs=[
                "tests/test_m128_connector_write_execution_low_risk.py",
                "tests/test_connector_draft_proposals.py",
            ],
            docs_refs=[
                "docs/connectors/CONNECTOR_WRITE_EXECUTION_LOW_RISK.md",
                "docs/control_center/CONNECTOR_DRAFT_ONLY_PROPOSALS.md",
            ],
            cli_inspection_refs=[
                TRUST_AUTHORITY_MATRIX_CLI_REF,
                CONNECTOR_DRAFT_PROPOSAL_CLI_REF,
            ],
            safe_disable_refs=["safe-disable-ref:connector-write:low-risk"],
            rollback_refs=["rollback-ref:connector-write:compensating-action-required"],
            promotion_path_refs=["promotion-path-ref:connector-write:live-adapter-scope"],
            blocked_authority_refs=[
                "blocked-state:connector-write:no-bulk-send",
                "blocked-state:connector-write:no-sensitive-material",
            ],
            requires_exact_approval=True,
            requires_safe_disable=True,
            requires_rollback_posture=True,
        ),
        _lane(
            lane_ref="trust-lane:browser-low-risk-action",
            label="Browser automation inside UAA",
            tier=4,
            lane_kind="external_mutation",
            authority_state="blocked",
            current_posture=(
                "Browser automation inside UAA remains blocked. Browser observe, "
                "dry-run, clicks, forms, auth, downloads, uploads, raw DOM, "
                "screenshots, and broad navigation require separate AuthorityLease capabilities."
            ),
            approval_posture="Future exact scoped session, page, action, dry-run, policy, approval, audit, replay, revocation, and kill switch refs required.",
            operator_can_do_now="Inspect blocked browser posture only; no browser action executes inside UAA.",
            next_safe_action="Implement browser observe/dry-run AuthorityLease capability before any action capability.",
            route_refs=["browser-lane-ref:low-risk-click-exact-approved"],
            proof_refs=["proof-ref:browser-low-risk-click:exact-approved"],
            verifier_refs=["tests/test_m94_low_risk_browser_clicks.py"],
            docs_refs=["docs/browser/LOW_RISK_BROWSER_CLICKS.md"],
            cli_inspection_refs=[TRUST_AUTHORITY_MATRIX_CLI_REF],
            safe_disable_refs=["safe-disable-ref:browser-low-risk-click"],
            rollback_refs=["rollback-ref:browser-low-risk-click:revocation-and-replay"],
            promotion_path_refs=["promotion-path-ref:browser:forms-auth-downloads-separate-lanes"],
            blocked_authority_refs=[
                "blocked-state:browser:no-authenticated-actions",
                "blocked-state:browser:no-form-submit-download-upload",
            ],
            requires_exact_approval=True,
            requires_safe_disable=True,
            requires_rollback_posture=True,
        ),
        _lane(
            lane_ref="trust-lane:background-autonomy-scoped",
            label="Background autonomy",
            tier=5,
            lane_kind="background_standing_authority",
            authority_state="blocked",
            current_posture=(
                "Background autonomy remains blocked until scoped work-session "
                "runtime, supervisor, checkpoint, queue inspection, revocation, "
                "kill switch, budgets, receipts, and replay are implemented."
            ),
            approval_posture="Future exact workflow, schedule/session, budget, queue, supervisor, checkpoint, revocation, and kill-switch approval required.",
            operator_can_do_now="Inspect blocked background posture only; no background worker or standing session starts.",
            next_safe_action="Keep standing recurring workflows disabled until exact runtime evidence exists.",
            route_refs=["autonomy-lane-ref:scoped-background-work-session"],
            proof_refs=["proof-ref:background-autonomy:scoped-work-session"],
            verifier_refs=[
                "tests/test_m132_trusted_recurring_workflow.py",
                "tests/test_m137_browser_connector_combined_workflow.py",
            ],
            docs_refs=[
                "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
                "docs/autonomy/BROWSER_CONNECTOR_COMBINED_WORKFLOW.md",
            ],
            cli_inspection_refs=[TRUST_AUTHORITY_MATRIX_CLI_REF],
            safe_disable_refs=["safe-disable-ref:background-autonomy:scoped-work-session"],
            rollback_refs=["rollback-ref:background-autonomy:pause-cancel-kill"],
            promotion_path_refs=["promotion-path-ref:background-autonomy:standing-recurring-separate-review"],
            blocked_authority_refs=[
                "blocked-state:background-autonomy:no-unbounded-standing-authority",
                "blocked-state:background-autonomy:no-uninspected-queue",
            ],
            requires_exact_approval=True,
            requires_safe_disable=True,
            requires_rollback_posture=True,
        ),
        _lane(
            lane_ref="trust-lane:production-authority-gate",
            label="Production authority",
            tier=5,
            lane_kind="background_standing_authority",
            authority_state="blocked",
            current_posture=(
                "Production authority remains blocked. Readiness-review docs do "
                "not grant deployment, release, merge, tag, public beta, or "
                "production action authority."
            ),
            approval_posture="Future exact production environment, deployment mode, authority tier, release evidence, rollback, audit, and operator approval required.",
            operator_can_do_now="Inspect readiness blockers only; no production action is available.",
            next_safe_action="Complete production red-team and rollback evidence before proposing a production gate.",
            route_refs=["production-lane-ref:authority-readiness-review"],
            proof_refs=["proof-ref:production-authority-readiness-review"],
            verifier_refs=[
                "tests/test_m120_production_authority_readiness_review.py",
                "tests/test_m166_production_release_gate.py",
            ],
            docs_refs=["docs/production/PRODUCTION_AUTHORITY_READINESS_REVIEW.md"],
            cli_inspection_refs=[TRUST_AUTHORITY_MATRIX_CLI_REF],
            safe_disable_refs=["safe-disable-ref:production-authority:global-off"],
            rollback_refs=["rollback-ref:production-authority:release-rollback-required"],
            promotion_path_refs=["promotion-path-ref:production-authority:go-live-exact-gate"],
            blocked_authority_refs=[
                "blocked-state:production-authority:no-silent-go-live",
                "blocked-state:production-authority:no-unreviewed-release",
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
    authority_domain_ref: str | None = None,
    authority_capability_ref: str | None = None,
    required_authority_mode: str | None = None,
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
    default_domain_ref, default_capability_ref = _default_authority_mapping_refs(
        lane_ref=lane_ref,
        lane_kind=lane_kind,
        tier=tier,
    )
    domain_ref = authority_domain_ref or default_domain_ref
    capability_ref = authority_capability_ref or default_capability_ref
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
        authority_domain_ref=domain_ref,
        authority_capability_ref=capability_ref,
        required_authority_mode=required_authority_mode
        or _required_authority_mode_for_tier(tier, lane_kind),
        authority_lease_requirement_ref=(
            f"authority-lease-requirement-ref:{lane_suffix}:"
            f"{domain_ref.removeprefix('authority-domain-ref:')}:"
            f"{capability_ref.removeprefix('authority-capability-ref:')}"
        ),
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


def _default_authority_mapping_refs(
    *,
    lane_ref: str,
    lane_kind: TrustAuthorityLaneKind,
    tier: int,
) -> tuple[str, str]:
    lane = lane_ref.removeprefix("trust-lane:")
    if "memory" in lane:
        capability = "write" if tier >= 3 else "read"
        return "authority-domain-ref:memory", f"authority-capability-ref:{capability}"
    if "provider" in lane or "model" in lane:
        capability = "execute" if tier >= 4 else "draft"
        return (
            "authority-domain-ref:provider_model_calls",
            f"authority-capability-ref:{capability}",
        )
    if "connector-draft" in lane:
        return "authority-domain-ref:email", "authority-capability-ref:draft"
    if "connector-write" in lane:
        return "authority-domain-ref:email", "authority-capability-ref:send"
    if "web-evidence" in lane or "browser" in lane:
        capability = "click" if tier >= 4 else "observe"
        return "authority-domain-ref:browser", f"authority-capability-ref:{capability}"
    if "production" in lane:
        return "authority-domain-ref:cloud_production", "authority-capability-ref:deploy"
    if "background-autonomy" in lane:
        return "authority-domain-ref:apps", "authority-capability-ref:execute"
    if "issue-tracker" in lane:
        return "authority-domain-ref:apps", "authority-capability-ref:write"
    if "governed-command" in lane:
        return "authority-domain-ref:workspace", "authority-capability-ref:execute"
    if "work-board" in lane or "local-task" in lane:
        return "authority-domain-ref:workspace", "authority-capability-ref:write"
    if lane_kind == "draft_proposal":
        return "authority-domain-ref:workspace", "authority-capability-ref:draft"
    if lane_kind == "reversible_local_mutation":
        return "authority-domain-ref:workspace", "authority-capability-ref:write"
    if lane_kind == "external_mutation":
        return "authority-domain-ref:apps", "authority-capability-ref:write"
    if lane_kind == "background_standing_authority":
        return "authority-domain-ref:apps", "authority-capability-ref:execute"
    return "authority-domain-ref:workspace", "authority-capability-ref:read"


def _required_authority_mode_for_tier(
    tier: int,
    lane_kind: TrustAuthorityLaneKind,
) -> str:
    if tier <= 2:
        return "read_only"
    if tier == 3:
        return "ask_before_changes"
    if lane_kind == "background_standing_authority":
        return "delegated_mission_autonomous_window"
    return "full_machine_access_session"


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
