from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)


WORK_BOARD_CONTRACT_REF = "contract-ref:work-board-kanban-shell:v1"
WORK_BOARD_BOARD_REF = "work-board:founder-command-center-kanban"
WORK_BOARD_ROUTE_REF = "route-ref:control-center-work-board"
WORK_BOARD_BACKEND_ROUTE_REF = "GET /control-center/work-board"
WORK_BOARD_FRONTEND_ROUTE_REF = "/work-board"
WORK_BOARD_CLI_REF = "scripts/dev/uaa_work_board.py inspect-board"
WORK_BOARD_REQUIRED_BLOCKED_REFS = [
    "blocked-state:work-board-no-durable-reorder",
    "blocked-state:work-board-no-board-mutation",
    "blocked-state:work-board-no-issue-tracker-write",
    "blocked-state:work-board-no-connector-write",
    "blocked-state:work-board-no-shell-subprocess",
    "blocked-state:work-board-no-browser-automation",
    "blocked-state:work-board-no-background-autonomy",
    "blocked-state:work-board-no-production-authority",
]


BoardStatus = Literal["backend_owned_read_model"]
ColumnStatus = Literal["planned", "in_progress", "review", "blocked", "done"]
CardPriority = Literal["critical", "high", "medium", "low"]
CardAuthorityState = Literal["enabled_read_only", "proposal_only", "blocked"]


class WorkBoardBlockedLaneReadModel(BaseModel):
    lane_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=420)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_lane(self) -> "WorkBoardBlockedLaneReadModel":
        for ref in [
            self.lane_ref,
            *self.blocked_authority_refs,
            *self.promotion_path_refs,
        ]:
            validate_task_ref(ref, "work_board_blocked_lane_ref")
        for value in [self.label, self.safe_summary]:
            validate_safe_task_text(value, "work_board_blocked_lane_text")
        if not self.blocked_authority_refs:
            raise ValueError("blocked work board lane requires blocker refs")
        return self


class WorkBoardCardReadModel(BaseModel):
    card_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=140)
    safe_summary: str = Field(..., min_length=1, max_length=520)
    column_ref: str = Field(..., min_length=1)
    priority: CardPriority
    authority_state: CardAuthorityState
    owner_ref: str = Field(..., min_length=1)
    progress_label: str = Field(..., min_length=1, max_length=80)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocker_refs: list[str] = Field(default_factory=list)
    surface_refs: list[str] = Field(default_factory=list)
    cli_inspection_refs: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    raw_path_included: bool = False
    raw_content_included: bool = False
    mutation_enabled: bool = False
    drag_persistence_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_card(self) -> "WorkBoardCardReadModel":
        for ref in [
            self.card_ref,
            self.column_ref,
            self.owner_ref,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocker_refs,
            *self.surface_refs,
        ]:
            validate_task_ref(ref, "work_board_card_ref")
        for value in (
            [
                self.title,
                self.safe_summary,
                self.priority,
                self.authority_state,
                self.progress_label,
            ]
            + self.cli_inspection_refs
            + self.tags
        ):
            validate_safe_task_text(value, "work_board_card_text")
        if self.raw_path_included:
            raise ValueError("work board card cannot include raw paths")
        if self.raw_content_included:
            raise ValueError("work board card cannot include raw content")
        if self.mutation_enabled:
            raise ValueError("work board card cannot enable mutation")
        if self.drag_persistence_enabled:
            raise ValueError("work board card cannot enable drag persistence")
        if self.authority_state == "blocked" and not self.blocker_refs:
            raise ValueError("blocked work board card requires blocker refs")
        return self


class WorkBoardColumnReadModel(BaseModel):
    column_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=80)
    status: ColumnStatus
    safe_summary: str = Field(..., min_length=1, max_length=360)
    card_refs: list[str] = Field(default_factory=list)
    wip_limit: int = Field(..., ge=1, le=24)
    blocked_authority_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_column(self) -> "WorkBoardColumnReadModel":
        for ref in [self.column_ref, *self.card_refs, *self.blocked_authority_refs]:
            validate_task_ref(ref, "work_board_column_ref")
        for value in [self.label, self.status, self.safe_summary]:
            validate_safe_task_text(value, "work_board_column_text")
        return self


class WorkBoardDragDropPostureReadModel(BaseModel):
    posture_ref: str = "drag-drop-posture:work-board-local-preview-only"
    safe_summary: str = Field(..., min_length=1, max_length=520)
    local_preview_enabled: bool = True
    keyboard_reorder_preview_enabled: bool = True
    durable_reorder_enabled: bool = False
    backend_mutation_route_available: bool = False
    receipt_created: bool = False
    rollback_available: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_posture(self) -> "WorkBoardDragDropPostureReadModel":
        for ref in [
            self.posture_ref,
            *self.blocked_authority_refs,
            *self.promotion_path_refs,
        ]:
            validate_task_ref(ref, "work_board_drag_posture_ref")
        validate_safe_task_text(self.safe_summary, "work_board_drag_posture_text")
        if not self.local_preview_enabled:
            raise ValueError("work board local drag preview should be visible")
        if not self.keyboard_reorder_preview_enabled:
            raise ValueError("work board keyboard reorder preview should be visible")
        forbidden_flags = {
            "durable_reorder_enabled": self.durable_reorder_enabled,
            "backend_mutation_route_available": self.backend_mutation_route_available,
            "receipt_created": self.receipt_created,
            "rollback_available": self.rollback_available,
        }
        enabled = [name for name, value in forbidden_flags.items() if value]
        if enabled:
            raise ValueError(f"work board drag posture enabled {enabled[0]}")
        return self


class WorkBoardReadModel(BaseModel):
    schema_version: Literal["uaa-work-board-read-model.v1"] = (
        "uaa-work-board-read-model.v1"
    )
    contract_ref: str = WORK_BOARD_CONTRACT_REF
    board_ref: str = WORK_BOARD_BOARD_REF
    route_ref: str = WORK_BOARD_ROUTE_REF
    backend_route_refs: list[str] = Field(
        default_factory=lambda: [WORK_BOARD_BACKEND_ROUTE_REF]
    )
    frontend_route_refs: list[str] = Field(
        default_factory=lambda: [WORK_BOARD_FRONTEND_ROUTE_REF]
    )
    cli_inspection_refs: list[str] = Field(default_factory=lambda: [WORK_BOARD_CLI_REF])
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs-ref:founder-command-center-board",
            "docs-ref:current-kanban-board",
            "docs-ref:control-center-frontend-routes",
        ]
    )
    source_label: str = "python_core_work_board_read_model"
    status: BoardStatus = "backend_owned_read_model"
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=640)
    northstar_ref: str = "northstar-ref:uaa-local-first-kanban-cockpit"
    repo_safe_scope: str = Field(..., min_length=1, max_length=640)
    full_strength_goal: str = Field(..., min_length=1, max_length=640)
    columns: list[WorkBoardColumnReadModel] = Field(default_factory=list)
    cards: list[WorkBoardCardReadModel] = Field(default_factory=list)
    blocked_lanes: list[WorkBoardBlockedLaneReadModel] = Field(default_factory=list)
    drag_drop_posture: WorkBoardDragDropPostureReadModel
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=420)
    backend_owned: bool = True
    read_only: bool = True
    safe_refs_only: bool = True
    non_authoritative_mock_fallback: bool = False
    raw_paths_included: bool = False
    raw_content_included: bool = False
    board_mutation_enabled: bool = False
    durable_drag_drop_enabled: bool = False
    issue_tracker_write_enabled: bool = False
    connector_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_automation_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_board(self) -> "WorkBoardReadModel":
        for ref in [
            self.contract_ref,
            self.board_ref,
            self.route_ref,
            self.northstar_ref,
            *self.docs_refs,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocked_authority_refs,
            *self.promotion_path_refs,
            *self.redactions_applied,
        ]:
            validate_task_ref(ref, "work_board_ref")
        for value in (
            self.backend_route_refs
            + self.frontend_route_refs
            + self.cli_inspection_refs
            + [
                self.source_label,
                self.status,
                self.title,
                self.safe_summary,
                self.repo_safe_scope,
                self.full_strength_goal,
                self.next_safe_action,
            ]
        ):
            validate_safe_task_text(value, "work_board_text")
        column_refs = {column.column_ref for column in self.columns}
        card_refs = {card.card_ref for card in self.cards}
        if not column_refs:
            raise ValueError("work board requires columns")
        if not card_refs:
            raise ValueError("work board requires cards")
        for card in self.cards:
            if card.column_ref not in column_refs:
                raise ValueError("work board card references missing column")
        for column in self.columns:
            if not set(column.card_refs).issubset(card_refs):
                raise ValueError("work board column references missing card")
        card_column_pairs = {
            (card.card_ref, card.column_ref) for card in self.cards
        }
        for column in self.columns:
            for card_ref in column.card_refs:
                if (card_ref, column.column_ref) not in card_column_pairs:
                    raise ValueError("work board column card ordering drifted")
        if not set(WORK_BOARD_REQUIRED_BLOCKED_REFS).issubset(
            self.blocked_authority_refs
        ):
            raise ValueError("work board missing required blocker refs")
        required_true_flags = {
            "backend_owned": self.backend_owned,
            "read_only": self.read_only,
            "safe_refs_only": self.safe_refs_only,
        }
        disabled = [name for name, value in required_true_flags.items() if not value]
        if disabled:
            raise ValueError(f"work board disabled {disabled[0]}")
        forbidden_flags = {
            "raw_paths_included": self.raw_paths_included,
            "raw_content_included": self.raw_content_included,
            "board_mutation_enabled": self.board_mutation_enabled,
            "durable_drag_drop_enabled": self.durable_drag_drop_enabled,
            "issue_tracker_write_enabled": self.issue_tracker_write_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "shell_subprocess_execution_enabled": (
                self.shell_subprocess_execution_enabled
            ),
            "browser_automation_enabled": self.browser_automation_enabled,
            "background_autonomy_enabled": self.background_autonomy_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in forbidden_flags.items() if value]
        if enabled:
            raise ValueError(f"work board enabled {enabled[0]}")
        validate_safe_task_payload(self.model_dump(mode="json"), "work_board")
        return self


def build_work_board_read_model() -> WorkBoardReadModel:
    columns = [
        WorkBoardColumnReadModel(
            column_ref="work-board-column:triage",
            label="Triage",
            status="planned",
            safe_summary="New Founder Loop work enters here as safe refs and blocked-authority posture.",
            card_refs=["work-board-card:setup-assistant-hardening"],
            wip_limit=6,
            blocked_authority_refs=[],
        ),
        WorkBoardColumnReadModel(
            column_ref="work-board-column:ready",
            label="Ready",
            status="planned",
            safe_summary="Repo-safe lanes with backend contracts and proof expectations ready for implementation.",
            card_refs=[
                "work-board-card:action-inbox-work-queue",
                "work-board-card:proof-run-spine",
            ],
            wip_limit=5,
            blocked_authority_refs=[],
        ),
        WorkBoardColumnReadModel(
            column_ref="work-board-column:doing",
            label="Doing",
            status="in_progress",
            safe_summary="Active local-first product lanes currently in implementation or hardening.",
            card_refs=[
                "work-board-card:work-board-kanban-shell",
                "work-board-card:daily-loop-productization",
            ],
            wip_limit=3,
            blocked_authority_refs=[],
        ),
        WorkBoardColumnReadModel(
            column_ref="work-board-column:review",
            label="Review",
            status="review",
            safe_summary="Changes that need proof, language, safety, OpenAPI, and UI review before promotion.",
            card_refs=["work-board-card:trust-authority-map"],
            wip_limit=4,
            blocked_authority_refs=[],
        ),
        WorkBoardColumnReadModel(
            column_ref="work-board-column:blocked",
            label="Blocked",
            status="blocked",
            safe_summary="Full-strength lanes visible but blocked until exact authority contracts exist.",
            card_refs=[
                "work-board-card:external-agent-dispatch",
                "work-board-card:connector-write-actions",
            ],
            wip_limit=8,
            blocked_authority_refs=[
                "blocked-state:work-board-no-connector-write",
                "blocked-state:work-board-no-background-autonomy",
            ],
        ),
        WorkBoardColumnReadModel(
            column_ref="work-board-column:done",
            label="Done",
            status="done",
            safe_summary="Completed or acceptance-baselined lanes with safe proof refs.",
            card_refs=["work-board-card:coding-cockpit-shell"],
            wip_limit=8,
            blocked_authority_refs=[],
        ),
    ]
    cards = [
        _card(
            "work-board-card:setup-assistant-hardening",
            "Setup Assistant hardening",
            "work-board-column:triage",
            "Make first-run local setup clearer without installer side effects or distribution claims.",
            "high",
            "proposal_only",
            "Queued",
            ["route-ref:control-center-setup"],
            ["proof-ref:setup-assistant-read-model"],
            [],
            ["setup", "local-first"],
        ),
        _card(
            "work-board-card:action-inbox-work-queue",
            "Action Inbox work queue",
            "work-board-column:ready",
            "Show exact local work, approval posture, blocked states, receipts, and proof refs.",
            "critical",
            "enabled_read_only",
            "Ready",
            ["route-ref:control-center-actions"],
            ["proof-ref:action-inbox-queue"],
            [],
            ["actions", "approvals"],
        ),
        _card(
            "work-board-card:proof-run-spine",
            "Universal Proof spine",
            "work-board-column:ready",
            "Bind actions, evidence, receipts, memory, and setup events into coherent proof detail.",
            "critical",
            "enabled_read_only",
            "Ready",
            ["route-ref:control-center-proof"],
            ["proof-ref:universal-proof-spine"],
            [],
            ["proof", "receipts"],
        ),
        _card(
            "work-board-card:work-board-kanban-shell",
            "Kanban Work Board shell",
            "work-board-column:doing",
            "Render the Work Board as a real cockpit from Python Core read-model truth.",
            "critical",
            "enabled_read_only",
            "In progress",
            [WORK_BOARD_ROUTE_REF],
            ["proof-ref:work-board-kanban-shell"],
            [],
            ["kanban", "control-center"],
        ),
        _card(
            "work-board-card:daily-loop-productization",
            "Daily loop productization",
            "work-board-column:doing",
            "Unify Start Here, Today, Action Inbox, Proof, Evidence, Memory, Trust, and Settings.",
            "high",
            "enabled_read_only",
            "Hardening",
            ["route-ref:control-center-today"],
            ["proof-ref:daily-loop-productization"],
            [],
            ["today", "loop"],
        ),
        _card(
            "work-board-card:trust-authority-map",
            "Trust authority map",
            "work-board-column:review",
            "Keep enabled, review-only, planned, blocked, safe-disable, rollback, and CLI inspection visible.",
            "high",
            "enabled_read_only",
            "Review",
            ["route-ref:control-center-trust"],
            ["proof-ref:trust-authority-map"],
            [],
            ["trust", "authority"],
        ),
        _card(
            "work-board-card:external-agent-dispatch",
            "External agent dispatch",
            "work-board-column:blocked",
            "Full-strength multi-agent orchestration remains blocked until provider and local-agent authority graduates.",
            "medium",
            "blocked",
            "Blocked",
            ["route-ref:control-center-coding"],
            ["proof-ref:multi-agent-blocked"],
            [
                "blocked-state:work-board-no-background-autonomy",
                "blocked-state:work-board-no-production-authority",
            ],
            ["agents", "blocked"],
        ),
        _card(
            "work-board-card:connector-write-actions",
            "Connector write actions",
            "work-board-column:blocked",
            "Email, calendar, CRM, and external connector writes remain draft-only until exact approval lanes exist.",
            "medium",
            "blocked",
            "Blocked",
            ["route-ref:control-center-sources"],
            ["proof-ref:connector-write-blocked"],
            ["blocked-state:work-board-no-connector-write"],
            ["connectors", "blocked"],
        ),
        _card(
            "work-board-card:coding-cockpit-shell",
            "Coding Cockpit shell",
            "work-board-column:done",
            "Read-only Coding cockpit baseline with context, patch, terminal, Git, preview, and agent review posture.",
            "high",
            "enabled_read_only",
            "Merged",
            ["route-ref:control-center-coding"],
            ["proof-ref:coding-cockpit-shell"],
            [],
            ["coding", "cockpit"],
        ),
    ]
    return WorkBoardReadModel(
        title="Work Board",
        safe_summary=(
            "Backend-owned Kanban read model for the Founder Command Center. "
            "Control Center may filter, select, and preview drag/drop order locally, "
            "but it cannot persist board changes or grant execution authority."
        ),
        repo_safe_scope=(
            "Render a polished Kanban cockpit, safe refs, blocked authority, and "
            "ephemeral drag/drop preview only. No issue tracker, connector, shell, "
            "browser, or background work is invoked."
        ),
        full_strength_goal=(
            "A real operator Work Board where plans, actions, receipts, proof, "
            "agents, Git, and releases eventually coordinate through exact approval "
            "lanes and reversible receipts."
        ),
        columns=columns,
        cards=cards,
        blocked_lanes=[
            WorkBoardBlockedLaneReadModel(
                lane_ref="blocked-lane:work-board-durable-reorder",
                label="Durable board edits",
                safe_summary="Persisted reorder, create, archive, and assignment require a mutation contract, idempotency, receipt, and rollback.",
                blocked_authority_refs=[
                    "blocked-state:work-board-no-durable-reorder",
                    "blocked-state:work-board-no-board-mutation",
                ],
                promotion_path_refs=["prompt-ref:unblock-work-board-durable-edits"],
            ),
            WorkBoardBlockedLaneReadModel(
                lane_ref="blocked-lane:work-board-external-sync",
                label="External sync",
                safe_summary="Issue tracker, connector, and agent dispatch writes are separate authority lanes.",
                blocked_authority_refs=[
                    "blocked-state:work-board-no-issue-tracker-write",
                    "blocked-state:work-board-no-connector-write",
                    "blocked-state:work-board-no-background-autonomy",
                ],
                promotion_path_refs=["prompt-ref:unblock-work-board-external-sync"],
            ),
        ],
        drag_drop_posture=WorkBoardDragDropPostureReadModel(
            safe_summary=(
                "Cards can be dragged or moved by keyboard as an unsaved local layout "
                "preview. The preview is resettable and never becomes backend truth."
            ),
            blocked_authority_refs=[
                "blocked-state:work-board-no-durable-reorder",
                "blocked-state:work-board-no-board-mutation",
            ],
            promotion_path_refs=["prompt-ref:unblock-work-board-durable-edits"],
        ),
        proof_refs=["proof-ref:work-board-kanban-shell"],
        evidence_refs=["evidence-ref:work-board-read-model"],
        blocked_authority_refs=WORK_BOARD_REQUIRED_BLOCKED_REFS,
        promotion_path_refs=[
            "prompt-ref:unblock-work-board-durable-edits",
            "prompt-ref:unblock-work-board-external-sync",
        ],
        redactions_applied=[
            "redaction-ref:safe-refs-only",
            "redaction-ref:raw-paths-omitted",
            "redaction-ref:raw-content-omitted",
        ],
        next_safe_action=(
            "Use the board for local planning and preview-only drag/drop. Promote "
            "durable board changes through an exact backend mutation contract."
        ),
    )


def _card(
    card_ref: str,
    title: str,
    column_ref: str,
    safe_summary: str,
    priority: CardPriority,
    authority_state: CardAuthorityState,
    progress_label: str,
    surface_refs: list[str],
    proof_refs: list[str],
    blocker_refs: list[str],
    tags: list[str],
) -> WorkBoardCardReadModel:
    return WorkBoardCardReadModel(
        card_ref=card_ref,
        title=title,
        safe_summary=safe_summary,
        column_ref=column_ref,
        priority=priority,
        authority_state=authority_state,
        owner_ref="owner-ref:python-agent-core-work-board",
        progress_label=progress_label,
        proof_refs=proof_refs,
        evidence_refs=["evidence-ref:work-board-read-model"],
        blocker_refs=blocker_refs,
        surface_refs=surface_refs,
        cli_inspection_refs=[WORK_BOARD_CLI_REF],
        tags=tags,
    )
