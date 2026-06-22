from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)


PLANS_ACTION_ENVELOPE_CONTRACT_REF = "contract-ref:plans-action-envelope:v1"
PLANS_ACTION_ENVELOPE_REVIEW_ACTIONS = ("approve", "edit", "reject", "defer")
PLANS_ACTION_ENVELOPE_ALLOWED_SIDE_EFFECT_CLASSES = (
    "validation_only",
    "local_dev_workspace_only",
)
PLANS_ACTION_ENVELOPE_RISK_CLASSES = (
    "none",
    "low",
    "medium",
    "high",
    "critical",
    "blocked",
)
PLANS_ACTION_ENVELOPE_REQUIRED_REF_FIELDS = [
    "action_envelope_ref",
    "source_plan_ref",
    "scope_ref",
    "side_effect_class",
    "risk_class",
    "approval_requirement_ref",
    "review_posture_refs",
    "evidence_refs",
    "expected_receipt_refs",
    "idempotency_key_ref",
    "expires_at",
    "rollback_ref",
    "safe_disable_ref",
    "blocked_state_refs",
]
PLANS_ACTION_ENVELOPE_REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-action-execution",
    "blocked-state:no-approval-grant-capture",
    "blocked-state:approval-refs-identifiers-only",
    "blocked-state:no-connector-write",
    "blocked-state:no-shell-subprocess-execution",
    "blocked-state:no-model-provider-authority",
    "blocked-state:no-public-beta-or-distribution",
    "blocked-state:no-production-authority",
]
SAFE_ENVELOPE_SUFFIX_CHARS = re.compile(r"[^a-z0-9_.@-]+")
UNSAFE_ACTION_ENVELOPE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "raw provider",
    "raw_provider",
    "raw path",
    "raw_path",
    "raw log",
    "raw_log",
    "account identifier",
    "account_identifier",
    "username",
    "hostname",
    "credential material",
    "credential_material",
    "unredacted transcript",
    "full transcript",
)


class PlanActionEnvelope(BaseModel):
    contract_ref: str = PLANS_ACTION_ENVELOPE_CONTRACT_REF
    action_envelope_ref: str = Field(..., min_length=1)
    source_plan_ref: str = Field(..., min_length=1)
    source_action_ref: str | None = Field(default=None, max_length=160)
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    scope_ref: str = Field(..., min_length=1)
    side_effect_class: str = Field(default="validation_only", min_length=1, max_length=80)
    risk_class: str = Field(default="medium", min_length=1, max_length=40)
    approval_required: bool = True
    approval_requirement_ref: str = Field(..., min_length=1)
    review_actions: list[str] = Field(
        default_factory=lambda: list(PLANS_ACTION_ENVELOPE_REVIEW_ACTIONS)
    )
    review_posture_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    expected_receipt_refs: list[str] = Field(default_factory=list, min_length=1)
    audit_refs: list[str] = Field(default_factory=list)
    idempotency_key_ref: str = Field(..., min_length=1)
    expires_at: str = Field(default="review_required_before_mutation", min_length=1)
    stale_state: str = Field(
        default="recheck_plan_and_action_refs_before_mutation",
        min_length=1,
        max_length=120,
    )
    rollback_ref: str = Field(..., min_length=1)
    safe_disable_ref: str = Field(..., min_length=1)
    blocked_state_refs: list[str] = Field(default_factory=list, min_length=1)
    authority_boundary: str = Field(
        default=(
            "Reviewable Action envelope only; execution and approval grant capture "
            "remain blocked until exact scoped LocalApprovalAuthority validation exists."
        ),
        min_length=1,
        max_length=280,
    )
    next_safe_action: str = Field(
        default=(
            "Review, edit, reject, or defer the envelope metadata; keep execution "
            "blocked until a scoped authority milestone exists."
        ),
        min_length=1,
        max_length=260,
    )
    exact_scope_required: bool = True
    approval_ref_authority: bool = False
    approval_grant_capture_enabled: bool = False
    action_execution_enabled: bool = False
    connector_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    model_provider_authority_allowed: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_authority_enabled: bool = False
    safe_refs_only: bool = True
    raw_content_included: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_envelope(self) -> "PlanActionEnvelope":
        if self.contract_ref != PLANS_ACTION_ENVELOPE_CONTRACT_REF:
            raise ValueError("unexpected Plans Action envelope contract ref")
        for field_name in [
            "contract_ref",
            "action_envelope_ref",
            "source_plan_ref",
            "scope_ref",
            "approval_requirement_ref",
            "idempotency_key_ref",
            "rollback_ref",
            "safe_disable_ref",
        ]:
            validate_task_ref(getattr(self, field_name), field_name)
        if self.source_action_ref is not None:
            validate_task_ref(self.source_action_ref, "source_action_ref")
        for field_name in [
            "review_posture_refs",
            "evidence_refs",
            "expected_receipt_refs",
            "audit_refs",
            "blocked_state_refs",
        ]:
            for ref_value in getattr(self, field_name):
                validate_task_ref(ref_value, field_name)
        validate_safe_task_text(self.title, "title")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        validate_safe_task_text(self.side_effect_class, "side_effect_class")
        validate_safe_task_text(self.risk_class, "risk_class")
        validate_safe_task_text(self.expires_at, "expires_at")
        validate_safe_task_text(self.stale_state, "stale_state")
        validate_safe_task_text(self.authority_boundary, "authority_boundary")
        validate_safe_task_text(self.next_safe_action, "next_safe_action")
        if self.side_effect_class not in PLANS_ACTION_ENVELOPE_ALLOWED_SIDE_EFFECT_CLASSES:
            raise ValueError("side_effect_class is not allowed for reviewable envelopes")
        if self.risk_class not in PLANS_ACTION_ENVELOPE_RISK_CLASSES:
            raise ValueError("risk_class is not allowed for reviewable envelopes")
        missing_actions = set(PLANS_ACTION_ENVELOPE_REVIEW_ACTIONS) - set(
            self.review_actions
        )
        if missing_actions:
            raise ValueError("review_actions must include approve, edit, reject, and defer")
        missing_blockers = set(PLANS_ACTION_ENVELOPE_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blockers:
            raise ValueError("blocked_state_refs must include denied authority posture")
        if not self.exact_scope_required:
            raise ValueError("reviewable envelopes must require exact scope")
        denied_flags = {
            "approval_ref_authority": self.approval_ref_authority,
            "approval_grant_capture_enabled": self.approval_grant_capture_enabled,
            "action_execution_enabled": self.action_execution_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "shell_subprocess_execution_enabled": self.shell_subprocess_execution_enabled,
            "model_provider_authority_allowed": self.model_provider_authority_allowed,
            "public_beta_claim_enabled": self.public_beta_claim_enabled,
            "public_distribution_claim_enabled": self.public_distribution_claim_enabled,
            "production_authority_enabled": self.production_authority_enabled,
            "raw_content_included": self.raw_content_included,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(f"reviewable envelope enabled denied authority: {enabled[0]}")
        if not self.safe_refs_only:
            raise ValueError("reviewable envelopes must be safe-ref only")
        payload = self.model_dump(mode="json")
        _validate_no_denied_fragments(payload, "plan_action_envelope")
        validate_safe_task_payload(payload, "plan_action_envelope")
        return self


def plans_action_envelope_ref(source_ref: str) -> str:
    return f"action-envelope:plans:{_safe_suffix(source_ref)}"


def plans_action_scope_ref(source_ref: str) -> str:
    return f"scope-ref:plans-action-envelope:{_safe_suffix(source_ref)}"


def plans_action_approval_requirement_ref(source_ref: str) -> str:
    return f"approval-requirement:plans-action-envelope:{_safe_suffix(source_ref)}"


def plans_action_expected_receipt_ref(source_ref: str) -> str:
    return f"receipt-plan:plans-action-envelope:{_safe_suffix(source_ref)}"


def plans_action_idempotency_ref(source_ref: str) -> str:
    return f"idempotency-ref:plans-action-envelope:{_safe_suffix(source_ref)}"


def plans_action_rollback_ref(source_ref: str) -> str:
    return f"rollback-plan:plans-action-envelope:{_safe_suffix(source_ref)}"


def plans_action_safe_disable_ref(source_ref: str) -> str:
    return f"safe-disable:plans-action-envelope:{_safe_suffix(source_ref)}"


def plans_action_review_posture_ref(action: str) -> str:
    return f"review-posture:plans-action-envelope:{_safe_suffix(action)}"


def plans_action_envelope_review_posture_rows() -> list[dict[str, Any]]:
    return [
        {
            "review_action": action,
            "review_posture_ref": plans_action_review_posture_ref(action),
            "exact_scope_required": True,
            "safe_refs_required": True,
            "receipt_refs_required": True,
            "grants_execution_authority": False,
            "captures_approval_grant": False,
        }
        for action in PLANS_ACTION_ENVELOPE_REVIEW_ACTIONS
    ]


def plans_action_envelope_surface_bindings() -> list[dict[str, str]]:
    return [
        {
            "surface": "Today",
            "feed_status": "implemented_plan_action_state_contract",
            "feed_ref": "today-ref:plans-action-envelope-state",
            "authority_boundary": "Today can show envelope posture but cannot execute actions.",
        },
        {
            "surface": "Plans",
            "feed_status": "implemented_reviewable_action_envelope_refs",
            "feed_ref": "plan-ref:reviewable-action-envelope",
            "authority_boundary": "Plans can produce envelope metadata but not execution authority.",
        },
        {
            "surface": "Actions",
            "feed_status": "implemented_action_inbox_envelope_refs",
            "feed_ref": "action-inbox-ref:reviewable-envelope-queue",
            "authority_boundary": "Actions can show review posture without grant capture.",
        },
        {
            "surface": "Evidence",
            "feed_status": "implemented_history_refs_for_envelope_posture",
            "feed_ref": "evidence-ref:plans-action-envelope-history",
            "authority_boundary": "Evidence records proposed envelope posture and blockers only.",
        },
        {
            "surface": "Memory",
            "feed_status": "cross_surface_memory_intake_proposal_refs_only",
            "feed_ref": "memory-intake-proposal:plans",
            "authority_boundary": (
                "Envelope refs can feed reviewed memory intake candidates only; "
                "memory recall, writes, and context injection remain blocked."
            ),
        },
    ]


def plans_action_envelope_authority_posture() -> dict[str, bool]:
    return {
        "safe_refs_only": True,
        "exact_scope_required": True,
        "approval_required_before_mutation": True,
        "approval_ref_authority": False,
        "approval_grant_capture_enabled": False,
        "action_execution_enabled": False,
        "state_change_enabled": False,
        "connector_write_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "model_provider_authority_allowed": False,
        "memory_write_authorized": False,
        "context_injection_authorized": False,
        "public_beta_claim_enabled": False,
        "public_distribution_claim_enabled": False,
        "production_authority_enabled": False,
    }


def build_plan_action_envelope(
    *,
    source_plan_ref: str,
    title: str,
    safe_summary: str,
    evidence_refs: list[str],
    source_action_ref: str | None = None,
    side_effect_class: str = "validation_only",
    risk_class: str = "medium",
    approval_required: bool = True,
    audit_refs: list[str] | None = None,
    blocked_state_refs: list[str] | None = None,
    next_safe_action: str | None = None,
) -> PlanActionEnvelope:
    envelope_ref = plans_action_envelope_ref(source_action_ref or source_plan_ref)
    default_blockers = list(PLANS_ACTION_ENVELOPE_REQUIRED_BLOCKED_REFS)
    extra_blockers = blocked_state_refs or []
    return PlanActionEnvelope(
        action_envelope_ref=envelope_ref,
        source_plan_ref=source_plan_ref,
        source_action_ref=source_action_ref,
        title=title,
        safe_summary=safe_summary,
        scope_ref=plans_action_scope_ref(source_action_ref or source_plan_ref),
        side_effect_class=side_effect_class,
        risk_class=risk_class,
        approval_required=approval_required,
        approval_requirement_ref=plans_action_approval_requirement_ref(
            source_action_ref or source_plan_ref
        ),
        review_posture_refs=[
            plans_action_review_posture_ref(action)
            for action in PLANS_ACTION_ENVELOPE_REVIEW_ACTIONS
        ],
        evidence_refs=evidence_refs,
        expected_receipt_refs=[
            plans_action_expected_receipt_ref(source_action_ref or source_plan_ref)
        ],
        audit_refs=audit_refs or [],
        idempotency_key_ref=plans_action_idempotency_ref(
            source_action_ref or source_plan_ref
        ),
        rollback_ref=plans_action_rollback_ref(source_action_ref or source_plan_ref),
        safe_disable_ref=plans_action_safe_disable_ref(source_action_ref or source_plan_ref),
        blocked_state_refs=list(dict.fromkeys([*default_blockers, *extra_blockers])),
        next_safe_action=next_safe_action
        or (
            "Review, edit, reject, or defer the envelope metadata; keep execution "
            "blocked until exact scoped authority exists."
        ),
    )


def _safe_suffix(value: str) -> str:
    suffix = SAFE_ENVELOPE_SUFFIX_CHARS.sub("-", value.lower()).strip("-")
    return suffix or "missing"


def _validate_no_denied_fragments(value: Any, field_name: str) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_ACTION_ENVELOPE_TEXT_FRAGMENTS):
            raise ValueError(f"{field_name} contains denied raw-content language")
        return
    if isinstance(value, list):
        for item in value:
            _validate_no_denied_fragments(item, field_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_no_denied_fragments(str(key), field_name)
            _validate_no_denied_fragments(item, field_name)
