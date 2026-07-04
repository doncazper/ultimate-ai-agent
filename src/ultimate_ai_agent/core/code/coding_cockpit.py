from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)


CODING_COCKPIT_CONTRACT_REF = "contract-ref:coding-cockpit-shell:v1"
CODING_COCKPIT_SESSION_REF = "coding-session:local-readonly-cockpit"
CODING_COCKPIT_ROUTE_REF = "route-ref:control-center-coding-session"
CODING_COCKPIT_BACKEND_ROUTE_REF = "GET /control-center/coding/session"
CODING_COCKPIT_FRONTEND_ROUTE_REF = "/coding"
CODING_COCKPIT_REQUIRED_BLOCKED_REFS = [
    "blocked-state:coding-no-file-write",
    "blocked-state:coding-no-shell-subprocess",
    "blocked-state:coding-no-git-mutation",
    "blocked-state:coding-no-provider-model-call",
    "blocked-state:coding-no-browser-automation",
    "blocked-state:coding-no-connector-write",
    "blocked-state:coding-no-background-autonomy",
    "blocked-state:coding-no-production-authority",
]


AuthorityModeState = Literal["current", "planned", "blocked", "hard_gate"]
CockpitPanelState = Literal[
    "backend_owned",
    "read_only",
    "proposal_only",
    "preview_only",
    "blocked",
    "planned",
]
CockpitTaskStatus = Literal["read_only_seed", "proposal_only_blocked_runtime"]


class CodingCockpitAuthorityMode(BaseModel):
    mode_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=80)
    state: AuthorityModeState
    operator_posture: str = Field(..., min_length=1, max_length=160)
    safe_summary: str = Field(..., min_length=1, max_length=360)
    allowed_now: bool
    planned: bool
    blocked: bool
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_mode(self) -> "CodingCockpitAuthorityMode":
        validate_task_ref(self.mode_ref, "mode_ref")
        for ref in self.blocked_authority_refs + self.promotion_path_refs:
            validate_task_ref(ref, "authority_mode_ref")
        for value in [
            self.label,
            self.state,
            self.operator_posture,
            self.safe_summary,
        ]:
            validate_safe_task_text(value, "authority_mode_text")
        if self.state in {"blocked", "hard_gate"} and not self.blocked:
            raise ValueError("blocked authority mode must be blocked")
        if self.state == "current" and not self.allowed_now:
            raise ValueError("current authority mode must be allowed now")
        return self


class CodingCockpitRefItem(BaseModel):
    item_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    status: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=420)
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_item(self) -> "CodingCockpitRefItem":
        validate_task_ref(self.item_ref, "item_ref")
        for ref in (
            self.source_refs
            + self.evidence_refs
            + self.proof_refs
            + self.blocked_authority_refs
        ):
            validate_task_ref(ref, "coding_item_ref")
        for value in [self.label, self.status, self.safe_summary]:
            validate_safe_task_text(value, "coding_item_text")
        return self


class CodingCockpitPreviewPanel(BaseModel):
    panel_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    state: CockpitPanelState
    safe_summary: str = Field(..., min_length=1, max_length=520)
    items: list[CodingCockpitRefItem] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=360)
    mutation_enabled: bool = False
    runtime_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_panel(self) -> "CodingCockpitPreviewPanel":
        validate_task_ref(self.panel_ref, "panel_ref")
        for ref in self.proof_refs + self.blocked_authority_refs:
            validate_task_ref(ref, "coding_panel_ref")
        for value in [self.title, self.state, self.safe_summary, self.next_safe_action]:
            validate_safe_task_text(value, "coding_panel_text")
        if self.mutation_enabled:
            raise ValueError("coding cockpit panel cannot enable mutation")
        if self.runtime_authority_enabled:
            raise ValueError("coding cockpit panel cannot enable runtime authority")
        return self


class CodingCockpitSessionReadModel(BaseModel):
    schema_version: Literal["uaa-coding-cockpit-session.v1"] = (
        "uaa-coding-cockpit-session.v1"
    )
    contract_ref: str = CODING_COCKPIT_CONTRACT_REF
    route_ref: str = CODING_COCKPIT_ROUTE_REF
    session_ref: str = CODING_COCKPIT_SESSION_REF
    workspace_ref: str = "workspace-ref:coding:local-uaa"
    repo_scope_ref: str = "repo-scope:coding:local-uaa"
    branch_ref: str = "branch-ref:coding:current-local"
    authority_profile_ref: str = "authority-profile:coding:read-only"
    active_agent_ref: str = "agent-ref:coding:codex-slot"
    active_task_ref: str = "coding-task:cockpit-shell-seed"
    active_context_pack_ref: str = "context-pack:coding-cockpit-seed"
    active_patch_proposal_ref: str = "patch-proposal:coding-blocked-seed"
    active_command_proposal_ref: str = "command-proposal:coding-blocked-seed"
    active_git_ref: str = "git-status:coding-readonly-seed"
    active_proof_ref: str = "proof-ref:coding-cockpit-seed"
    active_preview_ref: str = "preview-ref:coding-blocked-seed"
    backend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_BACKEND_ROUTE_REF]
    )
    frontend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs-ref:control-center-coding-cockpit",
            "docs-ref:operator-shell-gap-map",
        ]
    )
    cli_inspection_refs: list[str] = Field(
        default_factory=lambda: ["scripts/dev/uaa_coding.py inspect-session"]
    )
    status: str = "implemented_read_only_cockpit_seed"
    task_status: CockpitTaskStatus = "read_only_seed"
    branch_label: str = "current local branch ref"
    active_agent_label: str = "Codex slot, read-only seed"
    authority_mode: str = "Read Only"
    backend_owned: bool = True
    mock_fallback: bool = False
    local_read_model_only: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    control_center_grants_authority: bool = False
    full_strength_goal: str = Field(
        default=(
            "Local coding cockpit for chat, context, diff, terminal, Git, "
            "preview, proof, and multi-agent review."
        ),
        min_length=1,
        max_length=300,
    )
    repo_safe_scope: str = Field(
        default=(
            "Prompt 01 seed renders backend-owned read-only cockpit state with "
            "proposal placeholders and blocked runtime lanes."
        ),
        min_length=1,
        max_length=300,
    )
    authority_modes: list[CodingCockpitAuthorityMode] = Field(default_factory=list)
    workspace_context: CodingCockpitPreviewPanel
    task_thread: CodingCockpitPreviewPanel
    task_timeline: CodingCockpitPreviewPanel
    diff_preview: CodingCockpitPreviewPanel
    proof_preview: CodingCockpitPreviewPanel
    terminal_preview: CodingCockpitPreviewPanel
    git_preview: CodingCockpitPreviewPanel
    test_output_preview: CodingCockpitPreviewPanel
    live_preview: CodingCockpitPreviewPanel
    chat_thread: CodingCockpitPreviewPanel
    same_ref_spine: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=420)
    file_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    git_mutation_enabled: bool = False
    provider_model_call_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_session(self) -> "CodingCockpitSessionReadModel":
        for field_name in [
            "contract_ref",
            "route_ref",
            "session_ref",
            "workspace_ref",
            "repo_scope_ref",
            "branch_ref",
            "authority_profile_ref",
            "active_agent_ref",
            "active_task_ref",
            "active_context_pack_ref",
            "active_patch_proposal_ref",
            "active_command_proposal_ref",
            "active_git_ref",
            "active_proof_ref",
            "active_preview_ref",
        ]:
            validate_task_ref(getattr(self, field_name), field_name)
        for ref in (
            self.same_ref_spine
            + self.blocked_authority_refs
            + self.promotion_path_refs
            + self.redactions_applied
            + self.docs_refs
        ):
            validate_task_ref(ref, "coding_session_ref")
        for value in (
            self.backend_route_refs
            + self.frontend_route_refs
            + self.cli_inspection_refs
            + [
                self.status,
                self.task_status,
                self.branch_label,
                self.active_agent_label,
                self.authority_mode,
                self.full_strength_goal,
                self.repo_safe_scope,
                self.next_safe_action,
            ]
        ):
            validate_safe_task_text(value, "coding_session_text")
        missing = set(CODING_COCKPIT_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_authority_refs
        )
        if missing:
            raise ValueError("coding cockpit session missing blocked refs")
        required_false_flags = {
            "raw_content_included": self.raw_content_included,
            "control_center_grants_authority": self.control_center_grants_authority,
            "file_write_enabled": self.file_write_enabled,
            "shell_subprocess_execution_enabled": (
                self.shell_subprocess_execution_enabled
            ),
            "git_mutation_enabled": self.git_mutation_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "background_autonomy_enabled": self.background_autonomy_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in required_false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding cockpit enabled {enabled[0]}")
        required_true_flags = {
            "backend_owned": self.backend_owned,
            "local_read_model_only": self.local_read_model_only,
            "safe_refs_only": self.safe_refs_only,
        }
        disabled = [name for name, value in required_true_flags.items() if not value]
        if disabled:
            raise ValueError(f"coding cockpit disabled {disabled[0]}")
        payload = self.model_dump(mode="json")
        validate_safe_task_payload(payload, "coding_cockpit_session")
        return self


def build_coding_cockpit_session_seed() -> CodingCockpitSessionReadModel:
    blocked = list(CODING_COCKPIT_REQUIRED_BLOCKED_REFS)
    proof_refs = ["proof-ref:coding-cockpit-seed"]
    evidence_refs = ["evidence-ref:coding-cockpit-read-model"]
    return CodingCockpitSessionReadModel(
        authority_modes=[
            CodingCockpitAuthorityMode(
                mode_ref="authority-mode:coding-read-only",
                label="Read Only",
                state="current",
                operator_posture="Inspect, search, plan, and compose context refs.",
                safe_summary=(
                    "Current session may show repo and task posture through safe "
                    "refs only."
                ),
                allowed_now=True,
                planned=False,
                blocked=False,
                blocked_authority_refs=[],
                promotion_path_refs=["promotion-path:coding-context-pack-preview"],
            ),
            CodingCockpitAuthorityMode(
                mode_ref="authority-mode:coding-ask-before-changes",
                label="Ask Before Changes",
                state="planned",
                operator_posture="Proposal lane before exact approved mutation.",
                safe_summary=(
                    "Future session mode may prepare exact patch proposals for "
                    "operator review."
                ),
                allowed_now=False,
                planned=True,
                blocked=False,
                blocked_authority_refs=[],
                promotion_path_refs=["promotion-path:coding-patch-proposal-lane"],
            ),
            CodingCockpitAuthorityMode(
                mode_ref="authority-mode:coding-safe-local-work",
                label="Approve Safe Local Work For Me",
                state="planned",
                operator_posture="Session-scoped safe local lane after verifiers.",
                safe_summary=(
                    "Future scoped mode requires allowlisted edits, receipts, "
                    "and rollback posture before enablement."
                ),
                allowed_now=False,
                planned=True,
                blocked=False,
                blocked_authority_refs=[],
                promotion_path_refs=["promotion-path:coding-approved-apply-lane"],
            ),
            CodingCockpitAuthorityMode(
                mode_ref="authority-mode:coding-full-local-workspace",
                label="Full Local Workspace Access",
                state="blocked",
                operator_posture="Broad local repo authority is not granted.",
                safe_summary=(
                    "Broad editing and local command lanes require separate "
                    "receipts, rollback posture, and verifier gates."
                ),
                allowed_now=False,
                planned=False,
                blocked=True,
                blocked_authority_refs=[
                    "blocked-state:coding-no-file-write",
                    "blocked-state:coding-no-shell-subprocess",
                    "blocked-state:coding-no-git-mutation",
                ],
                promotion_path_refs=["promotion-path:coding-approved-local-work"],
            ),
            CodingCockpitAuthorityMode(
                mode_ref="authority-mode:coding-external-production",
                label="External / Production Authority",
                state="hard_gate",
                operator_posture="External write and production lanes are separate.",
                safe_summary=(
                    "External side effects require a separate authority gate and "
                    "cannot be bundled with the coding cockpit."
                ),
                allowed_now=False,
                planned=False,
                blocked=True,
                blocked_authority_refs=[
                    "blocked-state:coding-no-connector-write",
                    "blocked-state:coding-no-production-authority",
                ],
                promotion_path_refs=["promotion-path:external-production-gate"],
            ),
        ],
        workspace_context=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:workspace-context",
            title="Workspace Context",
            state="backend_owned",
            safe_summary=(
                "Workspace panel seeds pinned context, excluded noisy refs, and "
                "context budget posture without storing raw file paths."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref="context-item:coding-pinned-files",
                    label="Pinned refs",
                    status="read-only seed",
                    safe_summary="Operator-selected file refs are planned for Prompt 03.",
                    source_refs=["context-pack:coding-cockpit-seed"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=["blocked-state:coding-no-file-write"],
                ),
                CodingCockpitRefItem(
                    item_ref="context-item:coding-excluded-noise",
                    label="Excluded refs",
                    status="planned",
                    safe_summary="Generated and noisy path filters are visible as refs only.",
                    source_refs=["context-pack:coding-cockpit-seed"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=[],
                ),
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=["blocked-state:coding-no-file-write"],
            next_safe_action="Inspect safe context refs and promote context pack preview later.",
        ),
        task_thread=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:task-thread",
            title="Coding Task",
            state="read_only",
            safe_summary=(
                "Active task seed links plan, context, patch proposal, command "
                "proposal, Git posture, and proof refs."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref="coding-task:cockpit-shell-seed",
                    label="Prompt 01 cockpit shell",
                    status="read-only seed",
                    safe_summary="Render the cockpit shell and read model seed only.",
                    source_refs=["coding-session:local-readonly-cockpit"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=blocked,
                )
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=blocked,
            next_safe_action="Review the seeded read model before later proposal lanes.",
        ),
        task_timeline=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:timeline",
            title="Workflow Timeline",
            state="read_only",
            safe_summary=(
                "Timeline shows planned agent workflow checkpoints as safe refs; "
                "no background autonomy is enabled."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref="timeline-item:coding-context-selected",
                    label="Context refs selected",
                    status="seeded",
                    safe_summary="Context pack preview is planned and not yet generated.",
                    source_refs=["context-pack:coding-cockpit-seed"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=[],
                ),
                CodingCockpitRefItem(
                    item_ref="timeline-item:coding-patch-blocked",
                    label="Patch lane",
                    status="blocked until Prompt 04",
                    safe_summary="Patch apply remains unavailable in this seed.",
                    source_refs=["patch-proposal:coding-blocked-seed"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=["blocked-state:coding-no-file-write"],
                ),
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=["blocked-state:coding-no-background-autonomy"],
            next_safe_action="Use timeline refs as proof posture only.",
        ),
        diff_preview=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:diff-preview",
            title="Diff Preview",
            state="proposal_only",
            safe_summary=(
                "Diff lane is a placeholder for future patch proposals; no diff "
                "body or apply control is enabled."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref="patch-proposal:coding-blocked-seed",
                    label="Patch proposal placeholder",
                    status="planned",
                    safe_summary="File-by-file and hunk review arrive after proposal artifacts.",
                    source_refs=["coding-task:cockpit-shell-seed"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=["blocked-state:coding-no-file-write"],
                )
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=["blocked-state:coding-no-file-write"],
            next_safe_action="Promote patch proposal artifacts before any apply lane.",
        ),
        proof_preview=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:proof-preview",
            title="Proof Detail",
            state="backend_owned",
            safe_summary=(
                "Proof preview binds request, plan, context, patch, command, "
                "Git, terminal, and preview refs to one safe spine."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref="proof-ref:coding-cockpit-seed",
                    label="Coding cockpit proof",
                    status="seeded",
                    safe_summary="Proof ref records blocked authority and next safe action.",
                    source_refs=["coding-session:local-readonly-cockpit"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=blocked,
                )
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=blocked,
            next_safe_action="Open universal Proof after the proof lane is expanded.",
        ),
        terminal_preview=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:terminal-preview",
            title="Terminal Preview",
            state="blocked",
            safe_summary=(
                "Terminal panel shows suggested command posture only; local "
                "command running is blocked in Prompt 01."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref="command-proposal:coding-blocked-seed",
                    label="Suggested command lane",
                    status="blocked",
                    safe_summary="Allowlisted test command receipts are future work.",
                    source_refs=["coding-task:cockpit-shell-seed"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=["blocked-state:coding-no-shell-subprocess"],
                )
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=["blocked-state:coding-no-shell-subprocess"],
            next_safe_action="Keep command previews disabled until allowlisted tests graduate.",
        ),
        git_preview=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:git-preview",
            title="Git Preview",
            state="preview_only",
            safe_summary=(
                "Git panel seeds branch and changed-file posture only; stage, "
                "commit, push, and pull-request actions are not enabled."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref="git-status:coding-readonly-seed",
                    label="Git posture",
                    status="read-only planned",
                    safe_summary="Git status read model is planned for a later lane.",
                    source_refs=["coding-session:local-readonly-cockpit"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=["blocked-state:coding-no-git-mutation"],
                )
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=["blocked-state:coding-no-git-mutation"],
            next_safe_action="Add Git status read model before any approved Git lane.",
        ),
        test_output_preview=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:test-output-preview",
            title="Test Output",
            state="planned",
            safe_summary=(
                "Test output lane is receipt-oriented future work; no test "
                "runner is invoked by this read model."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref="test-receipt:coding-blocked-seed",
                    label="Test receipt placeholder",
                    status="planned",
                    safe_summary="Focused test receipts arrive after allowlisted command lane.",
                    source_refs=["command-proposal:coding-blocked-seed"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=["blocked-state:coding-no-shell-subprocess"],
                )
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=["blocked-state:coding-no-shell-subprocess"],
            next_safe_action="Promote allowlisted command receipts before rendering test claims.",
        ),
        live_preview=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:live-preview",
            title="Live Preview",
            state="blocked",
            safe_summary=(
                "Live preview panel is visible as a blocked lane; browser "
                "automation and dev server control are not available."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref="preview-ref:coding-blocked-seed",
                    label="App preview placeholder",
                    status="blocked",
                    safe_summary="Preview status can be added later as a read model.",
                    source_refs=["coding-session:local-readonly-cockpit"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=[
                        "blocked-state:coding-no-browser-automation",
                        "blocked-state:coding-no-shell-subprocess",
                    ],
                )
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-browser-automation",
                "blocked-state:coding-no-shell-subprocess",
            ],
            next_safe_action="Add preview status refs before any browser interaction lane.",
        ),
        chat_thread=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:chat-thread",
            title="Agent Thread",
            state="proposal_only",
            safe_summary=(
                "Chat lane can display task refs and review prompts, but does "
                "not call models or dispatch agents in Prompt 01."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref="agent-handoff:coding-claude-review-blocked",
                    label="Reviewer slot",
                    status="planned",
                    safe_summary="Multi-agent review remains proposal metadata only.",
                    source_refs=["coding-task:cockpit-shell-seed"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=[
                        "blocked-state:coding-no-provider-model-call",
                        "blocked-state:coding-no-background-autonomy",
                    ],
                )
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-provider-model-call",
                "blocked-state:coding-no-background-autonomy",
            ],
            next_safe_action="Keep chat as task-thread presentation until provider authority is scoped.",
        ),
        same_ref_spine=[
            "coding-session:local-readonly-cockpit",
            "coding-task:cockpit-shell-seed",
            "context-pack:coding-cockpit-seed",
            "patch-proposal:coding-blocked-seed",
            "command-proposal:coding-blocked-seed",
            "git-status:coding-readonly-seed",
            "proof-ref:coding-cockpit-seed",
            "preview-ref:coding-blocked-seed",
        ],
        blocked_authority_refs=blocked,
        promotion_path_refs=[
            "promotion-path:coding-context-pack-preview",
            "promotion-path:coding-patch-proposal-lane",
            "promotion-path:coding-approved-apply-lane",
            "promotion-path:coding-allowlisted-test-command",
            "promotion-path:coding-git-review-lane",
            "promotion-path:coding-live-preview-status",
            "promotion-path:coding-multi-agent-review",
        ],
        redactions_applied=[
            "redaction-ref:safe-refs-only",
            "redaction-ref:bounded-summaries-only",
            "redaction-ref:raw-content-omitted",
            "redaction-ref:raw-paths-omitted",
        ],
        next_safe_action=(
            "Review the read-only cockpit shell and promote Prompt 02 contracts "
            "before adding proposal artifacts."
        ),
    )
