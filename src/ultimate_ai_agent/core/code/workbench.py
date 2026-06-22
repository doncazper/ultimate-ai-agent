from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)


GOVERNED_CODE_WORKBENCH_CONTRACT_REF = (
    "contract-ref:governed-code-workbench:v1"
)
GOVERNED_CODE_WORKBENCH_REQUIRED_REF_FIELDS = [
    "proposal_ref",
    "repo_scope_ref",
    "safe_diff_summary_ref",
    "validation_plan_ref",
    "validation_result_refs",
    "approval_requirement_ref",
    "expected_apply_receipt_ref",
    "expected_rollback_receipt_ref",
    "evidence_refs",
    "idempotency_key_ref",
    "blocked_state_refs",
]
GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-unapproved-mutation",
    "blocked-state:no-apply-execution",
    "blocked-state:no-approval-grant-capture",
    "blocked-state:no-unrestricted-shell",
    "blocked-state:no-shell-subprocess-execution",
    "blocked-state:no-remote-execution",
    "blocked-state:no-broad-coding-agent-autonomy",
    "blocked-state:no-provider-sdk-call",
    "blocked-state:no-web-fetch",
    "blocked-state:no-connector-write",
    "blocked-state:no-diff-body-storage",
    "blocked-state:no-production-authority",
]
SAFE_CODE_SUFFIX_CHARS = re.compile(r"[^a-z0-9_.@-]+")
UNSAFE_CODE_WORKBENCH_TEXT_FRAGMENTS = (
    "raw diff",
    "full diff",
    "unredacted diff",
    "raw patch",
    "provider payload",
    "api key",
    "authorization",
    "credential",
    "password",
)


class GovernedCodeWorkbenchProposal(BaseModel):
    contract_ref: str = GOVERNED_CODE_WORKBENCH_CONTRACT_REF
    proposal_ref: str = Field(..., min_length=1)
    repo_scope_ref: str = Field(..., min_length=1)
    safe_diff_summary_ref: str = Field(..., min_length=1)
    validation_plan_ref: str = Field(..., min_length=1)
    validation_result_refs: list[str] = Field(default_factory=list, min_length=1)
    approval_requirement_ref: str = Field(..., min_length=1)
    expected_apply_receipt_ref: str = Field(..., min_length=1)
    expected_rollback_receipt_ref: str = Field(..., min_length=1)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    idempotency_key_ref: str = Field(..., min_length=1)
    blocked_state_refs: list[str] = Field(default_factory=list, min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    validation_plan_summary: str = Field(..., min_length=1, max_length=500)
    side_effect_class: str = "local_dev_workspace_only"
    risk_class: str = "high"
    repo_local_scope_required: bool = True
    safe_diff_summary_only: bool = True
    validation_required_before_apply: bool = True
    approval_required_before_apply: bool = True
    atomic_apply_required: bool = True
    rollback_receipt_required: bool = True
    audit_required: bool = True
    redaction_required: bool = True
    apply_execution_enabled: bool = False
    approval_grant_capture_enabled: bool = False
    direct_file_write_enabled: bool = False
    unrestricted_shell_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    remote_execution_enabled: bool = False
    broad_coding_agent_autonomy_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    web_fetch_enabled: bool = False
    connector_write_enabled: bool = False
    diff_body_storage_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_proposal(self) -> "GovernedCodeWorkbenchProposal":
        if self.contract_ref != GOVERNED_CODE_WORKBENCH_CONTRACT_REF:
            raise ValueError("unexpected governed Code workbench contract ref")
        for field_name in [
            "contract_ref",
            "proposal_ref",
            "repo_scope_ref",
            "safe_diff_summary_ref",
            "validation_plan_ref",
            "approval_requirement_ref",
            "expected_apply_receipt_ref",
            "expected_rollback_receipt_ref",
            "idempotency_key_ref",
        ]:
            validate_task_ref(getattr(self, field_name), field_name)
        for field_name in [
            "validation_result_refs",
            "evidence_refs",
            "blocked_state_refs",
        ]:
            for ref_value in getattr(self, field_name):
                validate_task_ref(ref_value, field_name)
        for field_name in [
            "safe_summary",
            "validation_plan_summary",
            "side_effect_class",
            "risk_class",
        ]:
            validate_safe_task_text(getattr(self, field_name), field_name)
        missing_blockers = set(GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blockers:
            raise ValueError("governed Code workbench proposal missing blocked refs")
        required_true_flags = {
            "repo_local_scope_required": self.repo_local_scope_required,
            "safe_diff_summary_only": self.safe_diff_summary_only,
            "validation_required_before_apply": self.validation_required_before_apply,
            "approval_required_before_apply": self.approval_required_before_apply,
            "atomic_apply_required": self.atomic_apply_required,
            "rollback_receipt_required": self.rollback_receipt_required,
            "audit_required": self.audit_required,
            "redaction_required": self.redaction_required,
        }
        missing_true = [name for name, value in required_true_flags.items() if not value]
        if missing_true:
            raise ValueError(f"governed Code workbench disabled {missing_true[0]}")
        denied_flags = {
            "apply_execution_enabled": self.apply_execution_enabled,
            "approval_grant_capture_enabled": self.approval_grant_capture_enabled,
            "direct_file_write_enabled": self.direct_file_write_enabled,
            "unrestricted_shell_enabled": self.unrestricted_shell_enabled,
            "shell_subprocess_execution_enabled": self.shell_subprocess_execution_enabled,
            "remote_execution_enabled": self.remote_execution_enabled,
            "broad_coding_agent_autonomy_enabled": (
                self.broad_coding_agent_autonomy_enabled
            ),
            "provider_sdk_call_enabled": self.provider_sdk_call_enabled,
            "web_fetch_enabled": self.web_fetch_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "diff_body_storage_enabled": self.diff_body_storage_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(f"governed Code workbench enabled {enabled[0]}")
        payload = self.model_dump(mode="json")
        _validate_no_denied_fragments(payload)
        validate_safe_task_payload(payload, "governed_code_workbench_proposal")
        return self


def build_governed_code_workbench_proposal(
    *,
    proposal_ref: str = "code-proposal:founder-loop-safe-diff",
    safe_summary: str = (
        "Governed Code proposal records repo-local scope, safe diff summary, "
        "validation plan, approval requirement, expected apply receipt, and "
        "rollback receipt refs; apply remains blocked."
    ),
    validation_plan_summary: str = (
        "Run focused tests and verifiers before any exact approval-bound apply."
    ),
    validation_result_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
) -> GovernedCodeWorkbenchProposal:
    suffix = _safe_suffix(proposal_ref)
    return GovernedCodeWorkbenchProposal(
        proposal_ref=proposal_ref,
        repo_scope_ref=f"repo-scope:governed-code:{suffix}",
        safe_diff_summary_ref=f"diff-summary-ref:governed-code:{suffix}",
        validation_plan_ref=f"validation-plan-ref:governed-code:{suffix}",
        validation_result_refs=validation_result_refs
        or ["validation-result-ref:governed-code:not-run"],
        approval_requirement_ref=f"approval-requirement:governed-code:{suffix}",
        expected_apply_receipt_ref=f"receipt-plan:governed-code-apply:{suffix}",
        expected_rollback_receipt_ref=(
            f"rollback-receipt-plan:governed-code:{suffix}"
        ),
        evidence_refs=evidence_refs or ["evidence-ref:governed-code:today"],
        idempotency_key_ref=f"idempotency-ref:governed-code:{suffix}",
        blocked_state_refs=list(GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS),
        safe_summary=safe_summary,
        validation_plan_summary=validation_plan_summary,
    )


def governed_code_workbench_authority_posture() -> dict[str, bool]:
    return {
        "safe_refs_only": True,
        "repo_local_scope_required": True,
        "safe_diff_summary_only": True,
        "validation_required_before_apply": True,
        "approval_required_before_apply": True,
        "atomic_apply_required": True,
        "rollback_receipt_required": True,
        "audit_required": True,
        "redaction_required": True,
        "apply_execution_enabled": False,
        "approval_grant_capture_enabled": False,
        "direct_file_write_enabled": False,
        "unrestricted_shell_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "remote_execution_enabled": False,
        "broad_coding_agent_autonomy_enabled": False,
        "provider_sdk_call_enabled": False,
        "web_fetch_enabled": False,
        "connector_write_enabled": False,
        "diff_body_storage_enabled": False,
        "production_authority_enabled": False,
    }


def governed_code_workbench_surface_bindings() -> list[dict[str, str]]:
    return [
        {
            "surface": "Today",
            "feed_status": "implemented_governed_code_proposal_refs",
            "feed_ref": GOVERNED_CODE_WORKBENCH_CONTRACT_REF,
            "authority_boundary": "Code state is safe proposal metadata only.",
        },
        {
            "surface": "Code",
            "feed_status": "repo_local_safe_diff_summary_contract",
            "feed_ref": "code-proposal:governed-workbench",
            "authority_boundary": "Code proposals do not apply mutations.",
        },
        {
            "surface": "Actions",
            "feed_status": "approval_bound_apply_receipt_refs_only",
            "feed_ref": "receipt-plan:governed-code-apply",
            "authority_boundary": "Apply receipts are expected refs until scoped.",
        },
        {
            "surface": "Evidence",
            "feed_status": "validation_and_rollback_receipt_refs",
            "feed_ref": "evidence-ref:governed-code",
            "authority_boundary": "Evidence records proposal posture, not file changes.",
        },
        {
            "surface": "Memory",
            "feed_status": "cross_surface_memory_intake_proposal_refs_only",
            "feed_ref": "memory-intake-proposal:local-coding",
            "authority_boundary": (
                "Code can feed reviewed memory intake candidates only; memory "
                "writes and context injection remain blocked."
            ),
        },
    ]


def _safe_suffix(value: str) -> str:
    lowered = value.strip().lower().replace(":", "-")
    suffix = SAFE_CODE_SUFFIX_CHARS.sub("-", lowered).strip("-")
    return suffix or "missing"


def _validate_no_denied_fragments(payload: Any) -> None:
    if isinstance(payload, str):
        lowered = payload.lower()
        for fragment in UNSAFE_CODE_WORKBENCH_TEXT_FRAGMENTS:
            if fragment in lowered:
                raise ValueError("governed Code workbench contains denied content")
        return
    if isinstance(payload, dict):
        for value in payload.values():
            _validate_no_denied_fragments(value)
        return
    if isinstance(payload, list):
        for value in payload:
            _validate_no_denied_fragments(value)
