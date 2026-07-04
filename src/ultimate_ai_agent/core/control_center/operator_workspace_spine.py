from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_payload,
    validate_safe_execution_text,
)


OPERATOR_WORKSPACE_SPINE_SCHEMA_VERSION = "operator_workspace_spine_read_model.v1"
OPERATOR_WORKSPACE_SPINE_SOURCE = "python_core_operator_workspace_spine_read_model"
OPERATOR_WORKSPACE_SPINE_CONTRACT_REF = "contract-ref:operator-workspace-spine:v1"
OPERATOR_WORKSPACE_SPINE_ROUTE_REF = (
    "GET /control-center/today/summary#operator_workspace_spine"
)
OPERATOR_WORKSPACE_SPINE_CLI_REF = "python scripts/inspect_operator_workspace_spine.py"
OPERATOR_WORKSPACE_SPINE_PROOF_REF = "proof-ref:operator-workspace-spine:read-model"
OPERATOR_WORKSPACE_SPINE_SAFE_DISABLE_REF = (
    "safe-disable-ref:operator-workspace-spine:disable-read-model"
)
OPERATOR_WORKSPACE_SPINE_ROLLBACK_REF = (
    "rollback-ref:operator-workspace-spine:remove-read-model-projection"
)
OPERATOR_WORKSPACE_SPINE_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-state:operator-workspace:no-file-write",
    "blocked-state:operator-workspace:no-git-mutation",
    "blocked-state:operator-workspace:no-shell-subprocess-execution",
    "blocked-state:operator-workspace:no-browser-automation",
    "blocked-state:operator-workspace:no-dev-server-start",
    "blocked-state:operator-workspace:no-provider-model-call",
    "blocked-state:operator-workspace:no-connector-write",
    "blocked-state:operator-workspace:no-background-autonomy",
    "blocked-state:operator-workspace:no-raw-path-persistence",
    "blocked-state:operator-workspace:no-raw-log-persistence",
    "blocked-state:operator-workspace:no-production-authority",
)

OperatorWorkspaceLaneKind = Literal[
    "workspace_status",
    "git_posture",
    "preview_status",
    "run_logs",
    "coworker_handoff",
]


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


class OperatorWorkspaceSpineLane(BaseModel):
    lane_ref: str = Field(..., min_length=1)
    lane_kind: OperatorWorkspaceLaneKind
    label: str = Field(..., min_length=1, max_length=120)
    status: str = Field(..., min_length=1, max_length=160)
    safe_summary: str = Field(..., min_length=1, max_length=700)
    current_posture_ref: str = Field(..., min_length=1)
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    read_only: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    runtime_execution_enabled: bool = False
    mutation_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_lane(self) -> "OperatorWorkspaceSpineLane":
        validate_execution_ref(self.lane_ref, "lane_ref")
        validate_execution_ref(self.current_posture_ref, "current_posture_ref")
        for field_name in ("lane_kind", "label", "status", "safe_summary", "next_safe_action"):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        _validate_ref_list(self.source_refs, "source_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_ref_list(self.proof_refs, "proof_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        if (
            not self.read_only
            or not self.safe_refs_only
            or self.raw_content_included
            or self.runtime_execution_enabled
            or self.mutation_enabled
        ):
            raise ValueError("Operator workspace lanes must remain read-only safe refs")
        if not self.blocked_authority_refs:
            raise ValueError("Operator workspace lanes must expose blocked authority")
        return self


class OperatorWorkspaceSpineReadModel(BaseModel):
    schema_version: str = OPERATOR_WORKSPACE_SPINE_SCHEMA_VERSION
    contract_ref: str = OPERATOR_WORKSPACE_SPINE_CONTRACT_REF
    source: str = OPERATOR_WORKSPACE_SPINE_SOURCE
    backend_owned: bool = True
    status: str = "implemented_read_only_operator_workspace_spine"
    route_ref: str = OPERATOR_WORKSPACE_SPINE_ROUTE_REF
    cli_ref: str = OPERATOR_WORKSPACE_SPINE_CLI_REF
    workspace_ref: str = "workspace-ref:operator-workspace:local-control-center"
    workspace_status_ref: str = "workspace-status-ref:operator-workspace:local-loop"
    repo_scope_ref: str = "repo-scope:operator-workspace:local-safe-refs"
    git_posture_ref: str = "git-posture-ref:operator-workspace:read-only"
    preview_status_ref: str = "preview-status-ref:operator-workspace:manifest-only"
    run_log_posture_ref: str = "run-log-posture-ref:operator-workspace:redacted-refs"
    coworker_handoff_ref: str = "handoff-ref:operator-workspace:coworker-metadata-only"
    lane_order: list[OperatorWorkspaceLaneKind] = Field(
        default_factory=lambda: [
            "workspace_status",
            "git_posture",
            "preview_status",
            "run_logs",
            "coworker_handoff",
        ]
    )
    lanes: list[OperatorWorkspaceSpineLane] = Field(default_factory=list)
    proof_refs: list[str] = Field(
        default_factory=lambda: [OPERATOR_WORKSPACE_SPINE_PROOF_REF]
    )
    evidence_refs: list[str] = Field(
        default_factory=lambda: ["evidence-ref:operator-workspace-spine:today"]
    )
    safe_disable_refs: list[str] = Field(
        default_factory=lambda: [OPERATOR_WORKSPACE_SPINE_SAFE_DISABLE_REF]
    )
    rollback_refs: list[str] = Field(
        default_factory=lambda: [OPERATOR_WORKSPACE_SPINE_ROLLBACK_REF]
    )
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(OPERATOR_WORKSPACE_SPINE_BLOCKED_AUTHORITY_REFS)
    )
    promotion_path_refs: list[str] = Field(
        default_factory=lambda: [
            "promotion-path-ref:operator-workspace:exact-git-status-contract",
            "promotion-path-ref:operator-workspace:dev-server-manifest-contract",
            "promotion-path-ref:operator-workspace:allowlisted-run-log-receipts",
            "promotion-path-ref:operator-workspace:coworker-handoff-receipts",
        ]
    )
    route_refs: list[str] = Field(
        default_factory=lambda: [
            OPERATOR_WORKSPACE_SPINE_ROUTE_REF,
            "route-ref:control-center:today",
            "route-ref:control-center:trust",
            "route-ref:control-center:proof",
        ]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: ["docs/control_center/OPERATOR_WORKSPACE_SPINE.md"]
    )
    verifier_refs: list[str] = Field(
        default_factory=lambda: [
            "scripts/verify_beta_11_operator_workspace_spine.py"
        ]
    )
    full_strength_goal: str = (
        "A ZCode-inspired operator workspace cockpit showing workspace status, "
        "Git posture, preview status, run logs, and coworker handoff state."
    )
    repo_safe_scope: str = (
        "Backend-owned read model with safe refs and bounded posture summaries "
        "only; no file writes, Git mutation, shell execution, browser automation, "
        "dev-server control, provider calls, connector writes, or autonomy."
    )
    blocked_authority_summary: str = (
        "Mutating workspace actions, Git operations, command execution, browser "
        "preview automation, dev-server lifecycle control, external agents, and "
        "production authority require later exact authority graduation."
    )
    next_safe_action: str = (
        "Inspect workspace, Git, preview, run-log, and coworker posture refs; "
        "promote one exact authority lane only after verifier-backed contracts."
    )
    safe_refs_only: bool = True
    read_only: bool = True
    control_center_presentation_only: bool = True
    raw_path_persistence_enabled: bool = False
    raw_log_persistence_enabled: bool = False
    file_write_enabled: bool = False
    git_mutation_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_automation_enabled: bool = False
    dev_server_start_enabled: bool = False
    provider_model_call_enabled: bool = False
    connector_write_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "OperatorWorkspaceSpineReadModel":
        if self.schema_version != OPERATOR_WORKSPACE_SPINE_SCHEMA_VERSION:
            raise ValueError("Operator workspace spine schema drift")
        if self.contract_ref != OPERATOR_WORKSPACE_SPINE_CONTRACT_REF:
            raise ValueError("Operator workspace spine contract drift")
        if self.source != OPERATOR_WORKSPACE_SPINE_SOURCE:
            raise ValueError("Operator workspace spine source drift")
        if self.route_ref != OPERATOR_WORKSPACE_SPINE_ROUTE_REF:
            raise ValueError("Operator workspace spine route drift")
        if self.cli_ref != OPERATOR_WORKSPACE_SPINE_CLI_REF:
            raise ValueError("Operator workspace spine CLI drift")
        if [lane.lane_kind for lane in self.lanes] != self.lane_order:
            raise ValueError("Operator workspace spine lane order drift")
        if not self.backend_owned or not self.control_center_presentation_only:
            raise ValueError("Operator workspace spine must remain backend-owned")
        if (
            not self.safe_refs_only
            or not self.read_only
            or self.raw_path_persistence_enabled
            or self.raw_log_persistence_enabled
        ):
            raise ValueError("Operator workspace spine must stay safe-ref only")
        for flag in (
            "file_write_enabled",
            "git_mutation_enabled",
            "shell_subprocess_execution_enabled",
            "browser_automation_enabled",
            "dev_server_start_enabled",
            "provider_model_call_enabled",
            "connector_write_enabled",
            "background_autonomy_enabled",
            "production_authority_enabled",
        ):
            if getattr(self, flag):
                raise ValueError(f"Operator workspace spine enables {flag}")
        for ref in (
            self.contract_ref,
            self.workspace_ref,
            self.workspace_status_ref,
            self.repo_scope_ref,
            self.git_posture_ref,
            self.preview_status_ref,
            self.run_log_posture_ref,
            self.coworker_handoff_ref,
        ):
            validate_execution_ref(ref, "operator_workspace_ref")
        for field_name in (
            "status",
            "source",
            "route_ref",
            "cli_ref",
            "full_strength_goal",
            "repo_safe_scope",
            "blocked_authority_summary",
            "next_safe_action",
        ):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        _validate_text_list(self.route_refs, "route_refs")
        _validate_text_list(self.docs_refs, "docs_refs")
        _validate_text_list(self.verifier_refs, "verifier_refs")
        _validate_ref_list(self.proof_refs, "proof_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_ref_list(self.safe_disable_refs, "safe_disable_refs")
        _validate_ref_list(self.rollback_refs, "rollback_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _validate_ref_list(self.promotion_path_refs, "promotion_path_refs")
        lane_blocked_refs = _merge_unique(
            *[lane.blocked_authority_refs for lane in self.lanes]
        )
        for blocked_ref in lane_blocked_refs:
            if blocked_ref not in self.blocked_authority_refs:
                raise ValueError("Operator workspace blocked refs missing lane ref")
        validate_safe_execution_payload(self.model_dump(mode="json"))
        return self


def _workspace_lane(
    *,
    lane_kind: OperatorWorkspaceLaneKind,
    label: str,
    status: str,
    safe_summary: str,
    current_posture_ref: str,
    source_refs: list[str],
    blocked_authority_refs: list[str],
    next_safe_action: str,
) -> OperatorWorkspaceSpineLane:
    return OperatorWorkspaceSpineLane(
        lane_ref=f"operator-workspace-lane:{lane_kind.replace('_', '-')}",
        lane_kind=lane_kind,
        label=label,
        status=status,
        safe_summary=safe_summary,
        current_posture_ref=current_posture_ref,
        source_refs=source_refs,
        evidence_refs=["evidence-ref:operator-workspace-spine:today"],
        proof_refs=[OPERATOR_WORKSPACE_SPINE_PROOF_REF],
        blocked_authority_refs=blocked_authority_refs,
        next_safe_action=next_safe_action,
    )


def build_operator_workspace_spine_read_model() -> OperatorWorkspaceSpineReadModel:
    lanes = [
        _workspace_lane(
            lane_kind="workspace_status",
            label="Workspace status",
            status="read_only_safe_ref_posture",
            safe_summary="Local workspace posture is represented by scoped safe refs only.",
            current_posture_ref="workspace-status-ref:operator-workspace:local-loop",
            source_refs=[
                "repo-scope:operator-workspace:local-safe-refs",
                "contract-ref:governed-code-workbench:v1",
            ],
            blocked_authority_refs=[
                "blocked-state:operator-workspace:no-file-write",
                "blocked-state:operator-workspace:no-raw-path-persistence",
            ],
            next_safe_action="Inspect workspace refs without applying or writing files.",
        ),
        _workspace_lane(
            lane_kind="git_posture",
            label="Git posture",
            status="read_only_git_posture_no_mutation",
            safe_summary="Git posture is visible as safe refs; stage, commit, push, and PR operations remain blocked here.",
            current_posture_ref="git-posture-ref:operator-workspace:read-only",
            source_refs=["git-status-ref:operator-workspace:not-polled"],
            blocked_authority_refs=[
                "blocked-state:operator-workspace:no-git-mutation",
                "blocked-state:operator-workspace:no-shell-subprocess-execution",
            ],
            next_safe_action="Promote an exact Git status read lane before showing live changed-file claims.",
        ),
        _workspace_lane(
            lane_kind="preview_status",
            label="Preview status",
            status="manifest_only_preview_posture",
            safe_summary="Preview status is a manifest posture only; starting servers or driving browsers is not authorized.",
            current_posture_ref="preview-status-ref:operator-workspace:manifest-only",
            source_refs=["dev-server-status-ref:operator-workspace:not-started"],
            blocked_authority_refs=[
                "blocked-state:operator-workspace:no-browser-automation",
                "blocked-state:operator-workspace:no-dev-server-start",
            ],
            next_safe_action="Add a dev-server manifest contract before live preview controls.",
        ),
        _workspace_lane(
            lane_kind="run_logs",
            label="Run logs",
            status="redacted_ref_only_log_posture",
            safe_summary="Run-log posture stores receipt and summary refs only; raw command output and local paths are omitted.",
            current_posture_ref="run-log-posture-ref:operator-workspace:redacted-refs",
            source_refs=["run-log-ref:operator-workspace:not-attached"],
            blocked_authority_refs=[
                "blocked-state:operator-workspace:no-shell-subprocess-execution",
                "blocked-state:operator-workspace:no-raw-log-persistence",
            ],
            next_safe_action="Use existing proof and run receipts until allowlisted command receipts are promoted.",
        ),
        _workspace_lane(
            lane_kind="coworker_handoff",
            label="Coworker handoff",
            status="metadata_only_handoff_posture",
            safe_summary="Coworker handoff state is metadata only; no external agent, background worker, or provider dispatch is authorized.",
            current_posture_ref="handoff-ref:operator-workspace:coworker-metadata-only",
            source_refs=["coworker-state-ref:operator-workspace:not-dispatched"],
            blocked_authority_refs=[
                "blocked-state:operator-workspace:no-provider-model-call",
                "blocked-state:operator-workspace:no-connector-write",
                "blocked-state:operator-workspace:no-background-autonomy",
            ],
            next_safe_action="Record handoff proposals as safe refs only until worker authority graduates.",
        ),
    ]
    return OperatorWorkspaceSpineReadModel(lanes=lanes)
