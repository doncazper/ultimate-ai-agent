from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.control_center.local_tasks import (
    FOUNDER_LOOP_LOCAL_TASK_BLOCKED_REFS,
    FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF,
    FOUNDER_LOOP_LOCAL_TASK_COMMIT_ROUTE_REF,
    FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
    FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_payload,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
    GOVERNED_RUNTIME_SAFE_DISABLE_REF,
)
from ultimate_ai_agent.core.tools.v2 import build_default_tool_catalog


ACTION_TOOL_CODE_CATALOG_CONTRACT_REF = (
    "contract-ref:goatcitadel-catchup-action-tool-code-catalog:v1"
)
ACTION_TOOL_CODE_CATALOG_SOURCE = (
    "python_core_action_tool_code_lane_catalog_read_model"
)
ACTION_TOOL_CODE_CATALOG_ROUTE_REF = "GET /control-center/actions/inbox"
ACTION_TOOL_CODE_CATALOG_CLI_REF = (
    "scripts/dev/uaa_founder_loop.py inspect-action-tool-code-catalog"
)
ACTION_TOOL_CODE_CATALOG_REF = "action-tool-code-catalog:founder-loop:v1"
ACTION_TOOL_CODE_BLOCKED_AUTHORITY_REFS = (
    "blocked-authority:action-tool-code:no-generic-tool-execution",
    "blocked-authority:action-tool-code:no-unrestricted-shell",
    "blocked-authority:action-tool-code:no-browser-automation",
    "blocked-authority:action-tool-code:no-connector-write",
    "blocked-authority:action-tool-code:no-plugin-runtime-import",
    "blocked-authority:action-tool-code:no-remote-execution",
    "blocked-authority:action-tool-code:no-provider-model-call",
    "blocked-authority:action-tool-code:no-background-autonomy",
    "blocked-authority:action-tool-code:no-production-authority",
)
RUNTIME_EXACT_COMMAND_LANE_SPECS = (
    {
        "command_intent": "focused_pytest",
        "capability_id": "runtime.focused_pytest_action_inbox",
        "capability_ref": "capability-ref:runtime-gateway:focused-pytest-action-inbox",
        "lane_ref": "lane-ref:runtime-gateway:focused-pytest-action-inbox",
        "label": "RuntimeGateway focused pytest command",
        "receipt_ref": "receipt-plan:runtime-action-inbox:focused-pytest",
        "evidence_ref": "evidence-ref:runtime-action-inbox:focused-pytest",
        "proof_ref": "proof-ref:runtime-action-inbox:focused-pytest",
    },
    {
        "command_intent": "repo_verifier",
        "capability_id": "runtime.repo_verifier_action_inbox",
        "capability_ref": "capability-ref:runtime-gateway:repo-verifier-action-inbox",
        "lane_ref": "lane-ref:runtime-gateway:repo-verifier-action-inbox",
        "label": "RuntimeGateway documentation verifier command",
        "receipt_ref": "receipt-plan:runtime-action-inbox:repo-verifier",
        "evidence_ref": "evidence-ref:runtime-action-inbox:repo-verifier",
        "proof_ref": "proof-ref:runtime-action-inbox:repo-verifier",
    },
    {
        "command_intent": "frontend_check",
        "capability_id": "runtime.frontend_check_action_inbox",
        "capability_ref": "capability-ref:runtime-gateway:frontend-check-action-inbox",
        "lane_ref": "lane-ref:runtime-gateway:frontend-check-action-inbox",
        "label": "RuntimeGateway frontend check command",
        "receipt_ref": "receipt-plan:runtime-action-inbox:frontend-check",
        "evidence_ref": "evidence-ref:runtime-action-inbox:frontend-check",
        "proof_ref": "proof-ref:runtime-action-inbox:frontend-check",
    },
    {
        "command_intent": "repo_doctor",
        "capability_id": "runtime.repo_doctor_action_inbox",
        "capability_ref": "capability-ref:runtime-gateway:repo-doctor-action-inbox",
        "lane_ref": "lane-ref:runtime-gateway:repo-doctor-action-inbox",
        "label": "RuntimeGateway repo doctor command",
        "receipt_ref": "receipt-plan:runtime-action-inbox:repo-doctor",
        "evidence_ref": "evidence-ref:runtime-action-inbox:repo-doctor",
        "proof_ref": "proof-ref:runtime-action-inbox:repo-doctor",
    },
)


ActionToolCodeCapabilityKind = Literal[
    "tool_preview",
    "action_micro_lane",
    "runtime_micro_lane",
    "code_workflow",
]
ActionToolCodeStatus = Literal[
    "implemented_preview_only",
    "implemented_exact_local_mutation_lane",
    "implemented_exact_approval_required",
    "proposal_only",
    "blocked_missing_exact_authority",
]


class ActionToolCodeLaneEntry(BaseModel):
    capability_id: str = Field(..., min_length=1, max_length=160)
    capability_ref: str = Field(..., min_length=1)
    lane_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=160)
    capability_kind: ActionToolCodeCapabilityKind
    surface: str = Field(..., min_length=1, max_length=80)
    status: ActionToolCodeStatus
    side_effect_class: str = Field(..., min_length=1, max_length=120)
    required_approval_scope: str = Field(..., min_length=1, max_length=180)
    eligibility_reason: str = Field(..., min_length=1, max_length=520)
    blocked_reason: str = Field(..., min_length=1, max_length=520)
    receipt_requirement: str = Field(..., min_length=1, max_length=520)
    rollback_or_safe_disable_posture: str = Field(..., min_length=1, max_length=520)
    route_refs: list[str] = Field(default_factory=list)
    cli_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    unblock_prompt_refs: list[str] = Field(default_factory=list)
    operator_visible: bool = True
    inspectable_now: bool = True
    proposal_only: bool = False
    exact_local_mutation_available: bool = False
    exact_runtime_lane_available: bool = False
    generic_tool_execution_enabled: bool = False
    unrestricted_shell_execution_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    plugin_runtime_import_enabled: bool = False
    remote_execution_enabled: bool = False
    provider_model_call_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_entry(self) -> "ActionToolCodeLaneEntry":
        for ref in [
            self.capability_ref,
            self.lane_ref,
            *self.receipt_refs,
            *self.evidence_refs,
            *self.proof_refs,
            *self.blocked_authority_refs,
            *self.unblock_prompt_refs,
        ]:
            validate_execution_ref(ref, "action_tool_code_catalog_ref")
        for value in [
            self.capability_id,
            self.label,
            self.capability_kind,
            self.surface,
            self.status,
            self.side_effect_class,
            self.required_approval_scope,
            self.eligibility_reason,
            self.blocked_reason,
            self.receipt_requirement,
            self.rollback_or_safe_disable_posture,
            *self.route_refs,
            *self.cli_refs,
        ]:
            validate_safe_execution_text(str(value), "action_tool_code_catalog_text")
        if not self.operator_visible or not self.inspectable_now:
            raise ValueError("ACTION_TOOL_CODE_ENTRY_MUST_STAY_OPERATOR_VISIBLE")
        if self.proposal_only and self.exact_local_mutation_available:
            raise ValueError("ACTION_TOOL_CODE_PROPOSAL_CANNOT_MUTATE")
        if self.status == "implemented_exact_local_mutation_lane":
            if not self.exact_local_mutation_available:
                raise ValueError("ACTION_TOOL_CODE_EXACT_LOCAL_LANE_REQUIRED")
            if not self.receipt_refs:
                raise ValueError("ACTION_TOOL_CODE_EXACT_LOCAL_RECEIPT_REQUIRED")
        if self.status == "implemented_exact_approval_required":
            if not self.exact_runtime_lane_available:
                raise ValueError("ACTION_TOOL_CODE_EXACT_RUNTIME_LANE_REQUIRED")
            if not self.receipt_refs:
                raise ValueError("ACTION_TOOL_CODE_EXACT_RUNTIME_RECEIPT_REQUIRED")
        for flag in (
            "generic_tool_execution_enabled",
            "unrestricted_shell_execution_enabled",
            "browser_automation_enabled",
            "connector_write_enabled",
            "plugin_runtime_import_enabled",
            "remote_execution_enabled",
            "provider_model_call_enabled",
            "background_autonomy_enabled",
            "production_authority_enabled",
        ):
            if getattr(self, flag):
                raise ValueError(f"ACTION_TOOL_CODE_BROAD_AUTHORITY_DENIED:{flag}")
        return self


class ActionToolCodeUnblockPrompt(BaseModel):
    prompt_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=160)
    target_capability_ref: str = Field(..., min_length=1)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    copy_ready_prompt: str = Field(..., min_length=1, max_length=1500)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_prompt(self) -> "ActionToolCodeUnblockPrompt":
        for ref in [
            self.prompt_ref,
            self.target_capability_ref,
            *self.blocked_authority_refs,
        ]:
            validate_execution_ref(ref, "action_tool_code_unblock_prompt_ref")
        validate_safe_execution_text(self.title, "action_tool_code_unblock_title")
        validate_safe_execution_text(
            self.copy_ready_prompt,
            "action_tool_code_unblock_prompt",
        )
        return self


class ActionToolCodeLaneCatalogReadModel(BaseModel):
    schema_version: Literal["uaa-action-tool-code-lane-catalog.v1"] = (
        "uaa-action-tool-code-lane-catalog.v1"
    )
    contract_ref: str = ACTION_TOOL_CODE_CATALOG_CONTRACT_REF
    source: str = ACTION_TOOL_CODE_CATALOG_SOURCE
    catalog_ref: str = ACTION_TOOL_CODE_CATALOG_REF
    route_ref: str = ACTION_TOOL_CODE_CATALOG_ROUTE_REF
    cli_ref: str = ACTION_TOOL_CODE_CATALOG_CLI_REF
    status: str = "implemented_backend_owned_inspectable_catalog"
    backend_owned: bool = True
    control_center_presentation_only: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    entry_count: int = Field(..., ge=0)
    preview_only_count: int = Field(..., ge=0)
    exact_local_mutation_count: int = Field(..., ge=0)
    exact_runtime_lane_count: int = Field(..., ge=0)
    proposal_only_count: int = Field(..., ge=0)
    blocked_count: int = Field(..., ge=0)
    entries: list[ActionToolCodeLaneEntry] = Field(default_factory=list)
    unblock_prompts: list[ActionToolCodeUnblockPrompt] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = (
        "Inspect lane eligibility and receipts; graduate each blocked capability "
        "through an exact authority lane before execution."
    )
    operator_summary: str = Field(..., min_length=1, max_length=700)
    generic_tool_execution_enabled: bool = False
    unrestricted_shell_execution_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    plugin_runtime_import_enabled: bool = False
    remote_execution_enabled: bool = False
    provider_model_call_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_catalog(self) -> "ActionToolCodeLaneCatalogReadModel":
        for ref in [
            self.contract_ref,
            self.catalog_ref,
            *self.blocked_authority_refs,
        ]:
            validate_execution_ref(ref, "action_tool_code_catalog_ref")
        for value in [
            self.source,
            self.route_ref,
            self.cli_ref,
            self.status,
            self.next_safe_action,
            self.operator_summary,
        ]:
            validate_safe_execution_text(str(value), "action_tool_code_catalog_text")
        if self.entry_count != len(self.entries):
            raise ValueError("ACTION_TOOL_CODE_ENTRY_COUNT_DRIFT")
        if self.preview_only_count != sum(
            1 for entry in self.entries if entry.status == "implemented_preview_only"
        ):
            raise ValueError("ACTION_TOOL_CODE_PREVIEW_COUNT_DRIFT")
        if self.exact_local_mutation_count != sum(
            1 for entry in self.entries if entry.exact_local_mutation_available
        ):
            raise ValueError("ACTION_TOOL_CODE_LOCAL_MUTATION_COUNT_DRIFT")
        if self.exact_runtime_lane_count != sum(
            1 for entry in self.entries if entry.exact_runtime_lane_available
        ):
            raise ValueError("ACTION_TOOL_CODE_RUNTIME_COUNT_DRIFT")
        if self.proposal_only_count != sum(1 for entry in self.entries if entry.proposal_only):
            raise ValueError("ACTION_TOOL_CODE_PROPOSAL_COUNT_DRIFT")
        if self.blocked_count != sum(
            1 for entry in self.entries if entry.status == "blocked_missing_exact_authority"
        ):
            raise ValueError("ACTION_TOOL_CODE_BLOCKED_COUNT_DRIFT")
        if (
            not self.backend_owned
            or not self.control_center_presentation_only
            or not self.safe_refs_only
            or self.raw_content_included
        ):
            raise ValueError("ACTION_TOOL_CODE_CATALOG_TRUTH_BOUNDARY_DRIFT")
        for flag in (
            "generic_tool_execution_enabled",
            "unrestricted_shell_execution_enabled",
            "browser_automation_enabled",
            "connector_write_enabled",
            "plugin_runtime_import_enabled",
            "remote_execution_enabled",
            "provider_model_call_enabled",
            "background_autonomy_enabled",
            "production_authority_enabled",
        ):
            if getattr(self, flag):
                raise ValueError(f"ACTION_TOOL_CODE_BROAD_AUTHORITY_DENIED:{flag}")
        validate_safe_execution_payload(
            self.model_dump(mode="json"),
            "action_tool_code_catalog",
        )
        return self


def build_action_tool_code_lane_catalog_read_model(
    *,
    action_work_queue: dict[str, Any] | None = None,
    runtime_action_bridge: dict[str, Any] | None = None,
) -> ActionToolCodeLaneCatalogReadModel:
    entries: list[ActionToolCodeLaneEntry] = []
    entries.extend(_tool_preview_entries())
    entries.append(_local_task_entry(action_work_queue))
    entries.extend(_runtime_exact_command_entries(runtime_action_bridge))
    entries.extend(_code_workflow_entries())
    prompts = _unblock_prompts()
    blocked_refs = list(
        dict.fromkeys(
            [
                *ACTION_TOOL_CODE_BLOCKED_AUTHORITY_REFS,
                *[ref for entry in entries for ref in entry.blocked_authority_refs],
            ]
        )
    )
    return ActionToolCodeLaneCatalogReadModel(
        entry_count=len(entries),
        preview_only_count=sum(
            1 for entry in entries if entry.status == "implemented_preview_only"
        ),
        exact_local_mutation_count=sum(
            1 for entry in entries if entry.exact_local_mutation_available
        ),
        exact_runtime_lane_count=sum(
            1 for entry in entries if entry.exact_runtime_lane_available
        ),
        proposal_only_count=sum(1 for entry in entries if entry.proposal_only),
        blocked_count=sum(
            1 for entry in entries if entry.status == "blocked_missing_exact_authority"
        ),
        entries=entries,
        unblock_prompts=prompts,
        blocked_authority_refs=blocked_refs,
        operator_summary=(
            f"{len(entries)} action, tool, runtime, and code lanes are inspectable; "
            "only exact local/approved micro-lanes may produce receipts, while "
            "generic tool execution remains blocked."
        ),
    )


def _tool_preview_entries() -> list[ActionToolCodeLaneEntry]:
    entries: list[ActionToolCodeLaneEntry] = []
    for tool_id, tool in build_default_tool_catalog().items():
        entries.append(
            ActionToolCodeLaneEntry(
                capability_id=tool_id,
                capability_ref=f"capability-ref:tool-broker-v2:{tool_id}",
                lane_ref=f"lane-ref:tool-preview:{tool_id}",
                label=tool.display_name,
                capability_kind="tool_preview",
                surface="Tools",
                status="implemented_preview_only",
                side_effect_class="validation_only",
                required_approval_scope=str(tool.approval_requirement),
                eligibility_reason=tool.safe_description
                or "Preview is available for safe refs only.",
                blocked_reason=(
                    "Execution is not callable from Tool Broker v2; preview "
                    "decisions produce receipt plans only."
                ),
                receipt_requirement=(
                    "receipt-plan-ref only; no runtime tool receipt is created."
                ),
                rollback_or_safe_disable_posture=(
                    "No side effect is performed, so rollback is not applicable."
                ),
                cli_refs=["tests/test_tool_broker_v2_contracts.py"],
                proof_refs=["proof-ref:tool-broker-v2:preview-only"],
                evidence_refs=["evidence-ref:tool-broker-v2:preview-only"],
                blocked_authority_refs=[
                    "blocked-authority:action-tool-code:no-generic-tool-execution"
                ],
                proposal_only=True,
            )
        )
    return entries


def _local_task_entry(
    action_work_queue: dict[str, Any] | None,
) -> ActionToolCodeLaneEntry:
    receipt_refs: list[str] = [
        "receipt-plan:founder-loop-local-task-create:exact-approved"
    ]
    if action_work_queue:
        for item in action_work_queue.get("work_items") or []:
            if item.get("action_kind") != FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND:
                continue
            receipt_refs.extend(item.get("expected_receipt_refs") or [])
            receipt_refs.extend(item.get("receipt_refs") or [])
    receipt_refs = list(dict.fromkeys(ref for ref in receipt_refs if isinstance(ref, str)))
    return ActionToolCodeLaneEntry(
        capability_id=FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
        capability_ref="capability-ref:action-inbox:local-task-create",
        lane_ref="lane-ref:action-inbox:local-task-create",
        label="Action Inbox local task create",
        capability_kind="action_micro_lane",
        surface="Action Inbox",
        status="implemented_exact_local_mutation_lane",
        side_effect_class="local_dev_workspace_only",
        required_approval_scope="approval-scope:founder-loop-local-task-create-exact",
        eligibility_reason=(
            "Available only for Action Inbox items with exact local-task approval "
            "and idempotency refs."
        ),
        blocked_reason=(
            "No connector write, model call, shell, browser, memory write, or "
            "external side effect is included."
        ),
        receipt_requirement=(
            "Requires idempotency, LocalApprovalAuthority validation, audit ref, "
            "and local task commit receipt."
        ),
        rollback_or_safe_disable_posture=(
            f"Safe-disable ref {FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF}; "
            f"rollback ref {FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF}."
        ),
        route_refs=[FOUNDER_LOOP_LOCAL_TASK_COMMIT_ROUTE_REF],
        cli_refs=["scripts/dev/uaa_founder_loop.py commit-local-task"],
        receipt_refs=receipt_refs,
        evidence_refs=["evidence-ref:founder-loop:local-task-create"],
        proof_refs=["proof-ref:founder-loop:local-task-create"],
        blocked_authority_refs=list(FOUNDER_LOOP_LOCAL_TASK_BLOCKED_REFS),
        exact_local_mutation_available=True,
    )


def _runtime_exact_command_entries(
    runtime_action_bridge: dict[str, Any] | None,
) -> list[ActionToolCodeLaneEntry]:
    return [
        _runtime_exact_command_entry(spec, runtime_action_bridge)
        for spec in RUNTIME_EXACT_COMMAND_LANE_SPECS
    ]


def _runtime_exact_command_entry(
    spec: dict[str, str],
    runtime_action_bridge: dict[str, Any] | None,
) -> ActionToolCodeLaneEntry:
    command_intent = spec["command_intent"]
    receipt_refs = [spec["receipt_ref"]]
    evidence_refs = [spec["evidence_ref"]]
    if runtime_action_bridge:
        for item in runtime_action_bridge.get("items") or []:
            if (
                not isinstance(item, dict)
                or item.get("command_intent") != command_intent
            ):
                continue
            receipt_refs.extend(item.get("receipt_refs") or [])
            evidence_refs.extend(item.get("evidence_refs") or [])
    return ActionToolCodeLaneEntry(
        capability_id=spec["capability_id"],
        capability_ref=spec["capability_ref"],
        lane_ref=spec["lane_ref"],
        label=spec["label"],
        capability_kind="runtime_micro_lane",
        surface="Runtime",
        status="implemented_exact_approval_required",
        side_effect_class="local_dev_workspace_only",
        required_approval_scope="approval-scope-ref:governed-runtime-exact-envelope",
        eligibility_reason=(
            "Eligible only through exact Action Inbox approval envelopes, argv-only "
            "allowlist, jailed cwd, timeout, env scrub, and redacted receipt refs."
        ),
        blocked_reason=(
            "Arbitrary commands, installs, network commands, background processes, "
            "and unapproved shell work remain blocked."
        ),
        receipt_requirement=(
            "Requires RuntimeGateway policy decision, approval validation, "
            "idempotency ref, command receipt, and redacted output ref."
        ),
        rollback_or_safe_disable_posture=(
            f"Runtime safe-disable ref {GOVERNED_RUNTIME_SAFE_DISABLE_REF}; "
            "receipts are inspection artifacts, not approval authority."
        ),
        route_refs=[
            "POST /api/runtime/invocations/{id}/execute",
            "GET /control-center/actions/inbox",
        ],
        cli_refs=[
            "scripts/dev/uaa_runtime.py inspect-action-inbox-bridge",
            "scripts/dev/uaa_runtime.py receipts",
        ],
        receipt_refs=list(dict.fromkeys(ref for ref in receipt_refs if isinstance(ref, str))),
        evidence_refs=list(dict.fromkeys(ref for ref in evidence_refs if isinstance(ref, str))),
        proof_refs=[spec["proof_ref"]],
        blocked_authority_refs=list(GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS),
        exact_runtime_lane_available=True,
    )


def _code_workflow_entries() -> list[ActionToolCodeLaneEntry]:
    from ultimate_ai_agent.core.code import (
        build_coding_git_review,
        build_coding_live_preview,
        build_coding_patch_apply_readiness,
        build_coding_patch_proposal_preview,
        build_coding_test_command_readiness,
    )

    patch_proposal = build_coding_patch_proposal_preview()
    patch_apply = build_coding_patch_apply_readiness()
    test_command = build_coding_test_command_readiness()
    git_review = build_coding_git_review()
    live_preview = build_coding_live_preview()
    return [
        ActionToolCodeLaneEntry(
            capability_id="coding.patch_proposal_preview",
            capability_ref="capability-ref:coding:patch-proposal-preview",
            lane_ref="lane-ref:coding:patch-proposal-preview",
            label="Coding patch proposal preview",
            capability_kind="code_workflow",
            surface="Coding",
            status="proposal_only",
            side_effect_class="validation_only",
            required_approval_scope="approval-scope:not-required-for-preview",
            eligibility_reason=patch_proposal.safe_summary,
            blocked_reason="Patch apply and file writes remain blocked.",
            receipt_requirement="Expected apply receipt refs are plans only.",
            rollback_or_safe_disable_posture="Rollback is planned before apply authority.",
            route_refs=list(patch_proposal.backend_route_refs),
            cli_refs=list(patch_proposal.cli_inspection_refs),
            receipt_refs=list(patch_proposal.proof_refs),
            evidence_refs=list(patch_proposal.evidence_refs),
            proof_refs=list(patch_proposal.proof_refs),
            blocked_authority_refs=list(patch_proposal.blocked_authority_refs),
            proposal_only=True,
        ),
        ActionToolCodeLaneEntry(
            capability_id="coding.approved_patch_apply",
            capability_ref="capability-ref:coding:approved-patch-apply",
            lane_ref="lane-ref:coding:approved-patch-apply",
            label="Coding approved patch apply",
            capability_kind="code_workflow",
            surface="Coding",
            status="blocked_missing_exact_authority",
            side_effect_class="local_dev_workspace_only",
            required_approval_scope="approval-scope:coding-approved-patch-apply-exact",
            eligibility_reason=patch_apply.repo_safe_current_state,
            blocked_reason=patch_apply.safe_summary,
            receipt_requirement="Requires checkpoint, exact patch/hunk receipt, and rollback ref.",
            rollback_or_safe_disable_posture=(
                "Requires checkpoint and rollback contract before apply."
            ),
            route_refs=list(patch_apply.backend_route_refs),
            cli_refs=list(patch_apply.cli_inspection_refs),
            receipt_refs=list(patch_apply.expected_receipt_refs),
            evidence_refs=list(patch_apply.evidence_refs),
            proof_refs=list(patch_apply.proof_refs),
            blocked_authority_refs=list(patch_apply.blocked_authority_refs),
            unblock_prompt_refs=list(patch_apply.unblock_prompt_refs),
        ),
        ActionToolCodeLaneEntry(
            capability_id="coding.allowlisted_test_command",
            capability_ref="capability-ref:coding:allowlisted-test-command",
            lane_ref="lane-ref:coding:allowlisted-test-command",
            label="Coding allowlisted test command",
            capability_kind="code_workflow",
            surface="Coding",
            status="blocked_missing_exact_authority",
            side_effect_class="local_dev_workspace_only",
            required_approval_scope="approval-scope:coding-allowlisted-test-command-exact",
            eligibility_reason=test_command.repo_safe_current_state,
            blocked_reason=test_command.safe_summary,
            receipt_requirement=(
                "Requires argv allowlist, bounded output, exit code, and test receipt."
            ),
            rollback_or_safe_disable_posture="Requires command safe-disable and timeout posture.",
            route_refs=list(test_command.backend_route_refs),
            cli_refs=list(test_command.cli_inspection_refs),
            receipt_refs=list(test_command.expected_receipt_refs),
            evidence_refs=list(test_command.evidence_refs),
            proof_refs=list(test_command.proof_refs),
            blocked_authority_refs=list(test_command.blocked_authority_refs),
            unblock_prompt_refs=list(test_command.unblock_prompt_refs),
        ),
        ActionToolCodeLaneEntry(
            capability_id="coding.git_review",
            capability_ref="capability-ref:coding:git-review",
            lane_ref="lane-ref:coding:git-review",
            label="Coding Git review",
            capability_kind="code_workflow",
            surface="Coding",
            status="blocked_missing_exact_authority",
            side_effect_class="local_dev_workspace_only",
            required_approval_scope="approval-scope:coding-git-review-exact",
            eligibility_reason=git_review.repo_safe_current_state,
            blocked_reason=git_review.safe_summary,
            receipt_requirement="Requires Git status/diff refs and commit proposal receipt plans.",
            rollback_or_safe_disable_posture="Git mutation stays separate from read-only review.",
            route_refs=list(git_review.backend_route_refs),
            cli_refs=list(git_review.cli_inspection_refs),
            receipt_refs=list(git_review.expected_receipt_refs),
            evidence_refs=list(git_review.evidence_refs),
            proof_refs=list(git_review.proof_refs),
            blocked_authority_refs=list(git_review.blocked_authority_refs),
            unblock_prompt_refs=list(git_review.unblock_prompt_refs),
        ),
        ActionToolCodeLaneEntry(
            capability_id="coding.live_preview",
            capability_ref="capability-ref:coding:live-preview",
            lane_ref="lane-ref:coding:live-preview",
            label="Coding live preview",
            capability_kind="code_workflow",
            surface="Coding",
            status="blocked_missing_exact_authority",
            side_effect_class="validation_only",
            required_approval_scope="approval-scope:coding-live-preview-exact",
            eligibility_reason=live_preview.repo_safe_current_state,
            blocked_reason=live_preview.safe_summary,
            receipt_requirement=(
                "Requires preview status, screenshot, console, or visual proof refs."
            ),
            rollback_or_safe_disable_posture="Dev-server and browser controls remain disabled.",
            route_refs=list(live_preview.backend_route_refs),
            cli_refs=list(live_preview.cli_inspection_refs),
            evidence_refs=list(
                dict.fromkeys(
                    [
                        *live_preview.evidence_refs,
                        *live_preview.visual_proof_refs,
                        *live_preview.screenshot_refs,
                    ]
                )
            ),
            proof_refs=list(live_preview.proof_refs),
            blocked_authority_refs=list(live_preview.blocked_authority_refs),
            unblock_prompt_refs=list(live_preview.unblock_prompt_refs),
        ),
    ]


def _unblock_prompts() -> list[ActionToolCodeUnblockPrompt]:
    return [
        ActionToolCodeUnblockPrompt(
            prompt_ref="prompt-ref:unblock-coding-approved-patch-apply",
            title="Unblock exact approved Coding patch apply",
            target_capability_ref="capability-ref:coding:approved-patch-apply",
            blocked_authority_refs=[
                "blocked-authority:action-tool-code:no-generic-tool-execution",
                "blocked-state:coding-no-file-write",
            ],
            copy_ready_prompt=(
                "Promote only exact Coding patch apply. Add checkpoint creation, "
                "approval binding, selected file/hunk apply, idempotency, redacted "
                "receipt refs, rollback refs, CLI/API/Core parity, route "
                "classification, and focused tests. Do not add broad file writes "
                "or shell execution."
            ),
        ),
        ActionToolCodeUnblockPrompt(
            prompt_ref="prompt-ref:unblock-coding-allowlisted-test-command",
            title="Unblock exact allowlisted Coding test command",
            target_capability_ref="capability-ref:coding:allowlisted-test-command",
            blocked_authority_refs=[
                "blocked-authority:action-tool-code:no-unrestricted-shell",
                "blocked-state:coding-no-shell-subprocess",
            ],
            copy_ready_prompt=(
                "Promote only allowlisted Coding test commands. Require argv-only "
                "commands, cwd jail, timeout, env scrub, bounded redacted output, "
                "idempotency, exact approval binding, test receipts, CLI/API/Core "
                "parity, route classification, and focused verifier coverage. "
                "Keep arbitrary shell, installs, network commands, and background "
                "processes blocked."
            ),
        ),
        ActionToolCodeUnblockPrompt(
            prompt_ref="prompt-ref:unblock-callable-tool-catalog",
            title="Unblock callable tool catalog separation",
            target_capability_ref="capability-ref:tool-catalog:callable-separated",
            blocked_authority_refs=[
                "blocked-authority:action-tool-code:no-generic-tool-execution",
                "blocked-authority:action-tool-code:no-plugin-runtime-import",
            ],
            copy_ready_prompt=(
                "Add inspectable and callable tool catalog separation. Callable "
                "entries must require policy eligibility, exact approval scope "
                "where needed, idempotency, receipt refs, rollback or safe-disable "
                "posture, redaction, CLI/API/Core parity, and tests proving "
                "proposal-only entries cannot execute."
            ),
        ),
    ]
