from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)


MEMORY_TO_LOOP_BINDING_CONTRACT_REF = "contract-ref:memory-to-loop-binding:v1"

MemoryToLoopSurface = Literal[
    "Today",
    "Action Inbox",
    "Evidence Timeline",
    "Weekly CEO Review",
]

MemoryToLoopBindingState = Literal[
    "candidate",
    "accepted_recall",
    "correction",
    "rejected",
    "follow_up_commitment",
    "stale",
    "missing_evidence_blocker",
]

MEMORY_TO_LOOP_REQUIRED_SURFACES: list[MemoryToLoopSurface] = [
    "Today",
    "Action Inbox",
    "Evidence Timeline",
    "Weekly CEO Review",
]

MEMORY_TO_LOOP_REQUIRED_REF_FIELDS = [
    "loop_item_ref",
    "surface",
    "loop_binding_state",
    "memory_candidate_ref",
    "source_refs",
    "evidence_refs",
    "accepted_recall_refs",
    "correction_refs",
    "rejected_item_refs",
    "follow_up_commitment_refs",
    "stale_state",
    "missing_evidence_refs",
    "blocked_state_refs",
    "next_safe_action",
]

MEMORY_DERIVED_ACTION_REQUIRED_REF_FIELDS = [
    "proposal_ref",
    "source_memory_ref",
    "source_loop_item_ref",
    "source_review_ref",
    "source_refs",
    "provenance_refs",
    "evidence_refs",
    "side_effect_class",
    "risk_class",
    "approval_required",
    "approval_posture",
    "approval_requirement_ref",
    "action_envelope_ref",
    "scope_ref",
    "review_posture_refs",
    "expected_receipt_refs",
    "next_safe_action",
    "blocked_state_refs",
]

MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-memory-write",
    "blocked-state:no-automatic-recall",
    "blocked-state:no-context-injection",
    "blocked-state:no-approval-grant-capture",
    "blocked-state:no-action-execution",
    "blocked-state:no-connector-write",
    "blocked-state:no-account-sync",
    "blocked-state:no-source-truth-authority",
    "blocked-state:no-public-beta-or-distribution",
    "blocked-state:no-production-authority",
]

_DENIED_FLAGS = [
    "memory_write_authorized",
    "automatic_recall_enabled",
    "context_injection_authorized",
    "approval_grant_capture_enabled",
    "action_execution_enabled",
    "connector_write_enabled",
    "account_sync_enabled",
    "source_truth_authority",
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_authority_enabled",
]

_UNSAFE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "raw file",
    "raw_file",
    "raw log",
    "raw_log",
    "shell history",
    "browser state",
    "account identifier",
    "username",
    "hostname",
    "credential",
    "api key",
    "authorization",
    "password",
    "token",
    "secret",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
)


class MemoryToLoopBindingItem(BaseModel):
    contract_ref: str = MEMORY_TO_LOOP_BINDING_CONTRACT_REF
    loop_item_ref: str = Field(..., min_length=1)
    surface: MemoryToLoopSurface
    loop_binding_state: MemoryToLoopBindingState
    memory_candidate_ref: str = Field(..., min_length=1)
    review_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=420)
    source_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    accepted_recall_refs: list[str] = Field(default_factory=list)
    correction_refs: list[str] = Field(default_factory=list)
    rejected_item_refs: list[str] = Field(default_factory=list)
    follow_up_commitment_refs: list[str] = Field(default_factory=list)
    stale_state: str = "recheck_memory_refs_before_loop_use"
    missing_evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    missing_evidence_posture: str = "missing_evidence_blocks_memory_derived_action"
    side_effect_class: str = "local_dev_workspace_only"
    approval_posture: str = "approval_refs_are_identifiers_only_not_authority"
    next_safe_action: str = Field(..., min_length=1, max_length=240)
    review_required: bool = True
    safe_refs_only: bool = True
    memory_write_authorized: bool = False
    automatic_recall_enabled: bool = False
    context_injection_authorized: bool = False
    approval_grant_capture_enabled: bool = False
    action_execution_enabled: bool = False
    connector_write_enabled: bool = False
    account_sync_enabled: bool = False
    source_truth_authority: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_authority_enabled: bool = False
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_loop_item(self) -> "MemoryToLoopBindingItem":
        if self.contract_ref != MEMORY_TO_LOOP_BINDING_CONTRACT_REF:
            raise ValueError("memory-to-loop contract ref drifted")
        for field_name in [
            "contract_ref",
            "loop_item_ref",
            "memory_candidate_ref",
            "review_ref",
        ]:
            _safe_ref(getattr(self, field_name), field_name)
        for field_name in [
            "source_refs",
            "evidence_refs",
            "accepted_recall_refs",
            "correction_refs",
            "rejected_item_refs",
            "follow_up_commitment_refs",
            "missing_evidence_refs",
            "blocked_state_refs",
        ]:
            _safe_refs(getattr(self, field_name), field_name)
        for field_name in [
            "surface",
            "loop_binding_state",
            "safe_summary",
            "stale_state",
            "missing_evidence_posture",
            "side_effect_class",
            "approval_posture",
            "next_safe_action",
        ]:
            _safe_text(str(getattr(self, field_name)), field_name)
        missing_blocked = set(MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blocked:
            raise ValueError("memory-to-loop item missing blocked refs")
        if self.review_required is not True:
            raise ValueError("memory-to-loop binding requires review")
        if self.safe_refs_only is not True:
            raise ValueError("memory-to-loop binding requires safe refs")
        if self.loop_binding_state == "accepted_recall" and not self.accepted_recall_refs:
            raise ValueError("accepted recall loop item requires recall refs")
        if self.loop_binding_state == "correction" and not self.correction_refs:
            raise ValueError("correction loop item requires correction refs")
        if self.loop_binding_state == "rejected" and not self.rejected_item_refs:
            raise ValueError("rejected loop item requires rejected item refs")
        if (
            self.loop_binding_state == "follow_up_commitment"
            and not self.follow_up_commitment_refs
        ):
            raise ValueError("follow-up loop item requires commitment refs")
        if (
            self.loop_binding_state == "missing_evidence_blocker"
            and not self.missing_evidence_refs
        ):
            raise ValueError("missing-evidence loop item requires blocker refs")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by memory-to-loop binding")
        return self


class MemoryDerivedActionProposal(BaseModel):
    contract_ref: str = MEMORY_TO_LOOP_BINDING_CONTRACT_REF
    proposal_ref: str = Field(..., min_length=1)
    source_memory_ref: str = Field(..., min_length=1)
    source_loop_item_ref: str = Field(..., min_length=1)
    source_review_ref: str = Field(..., min_length=1)
    source_intake_proposal_ref: str | None = None
    safe_summary: str = Field(..., min_length=1, max_length=360)
    source_refs: list[str] = Field(default_factory=list, min_length=1)
    provenance_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    side_effect_class: str = "local_dev_workspace_only"
    risk_class: str = "medium"
    approval_required: bool = True
    approval_posture: str = "approval_required_before_any_memory_derived_action"
    approval_requirement_ref: str = "approval-requirement:memory-derived-action"
    action_envelope_ref: str = "action-envelope:memory-derived-action-review"
    scope_ref: str = "scope-ref:memory-derived-action-review-only"
    review_posture_refs: list[str] = Field(
        default_factory=lambda: ["review-posture:approve-edit-reject-defer"]
    )
    expected_receipt_refs: list[str] = Field(
        default_factory=lambda: ["receipt-plan:memory-derived-action-review"]
    )
    idempotency_key_ref: str = "idempotency-ref:memory-derived-action-review"
    expires_at: str = "review_required_before_action"
    rollback_ref: str = "rollback-plan:memory-derived-action-no-mutation"
    safe_disable_ref: str = "safe-disable:memory-derived-action-review"
    next_safe_action: str = Field(..., min_length=1, max_length=240)
    stale_state: str = "recheck_memory_refs_before_action_review"
    missing_evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS)
    )
    memory_write_authorized: bool = False
    automatic_recall_enabled: bool = False
    context_injection_authorized: bool = False
    approval_grant_capture_enabled: bool = False
    action_execution_enabled: bool = False
    connector_write_enabled: bool = False
    account_sync_enabled: bool = False
    source_truth_authority: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_action_proposal(self) -> "MemoryDerivedActionProposal":
        if self.contract_ref != MEMORY_TO_LOOP_BINDING_CONTRACT_REF:
            raise ValueError("memory-derived action contract ref drifted")
        for field_name in [
            "contract_ref",
            "proposal_ref",
            "source_memory_ref",
            "source_loop_item_ref",
            "source_review_ref",
            "approval_requirement_ref",
            "action_envelope_ref",
            "scope_ref",
            "idempotency_key_ref",
            "rollback_ref",
            "safe_disable_ref",
        ]:
            _safe_ref(getattr(self, field_name), field_name)
        if self.source_intake_proposal_ref is not None:
            _safe_ref(self.source_intake_proposal_ref, "source_intake_proposal_ref")
        for field_name in [
            "source_refs",
            "provenance_refs",
            "evidence_refs",
            "review_posture_refs",
            "expected_receipt_refs",
            "missing_evidence_refs",
            "blocked_state_refs",
        ]:
            _safe_refs(getattr(self, field_name), field_name)
        for field_name in [
            "safe_summary",
            "side_effect_class",
            "risk_class",
            "approval_posture",
            "next_safe_action",
            "stale_state",
            "expires_at",
        ]:
            _safe_text(str(getattr(self, field_name)), field_name)
        if self.approval_required is not True:
            raise ValueError("memory-derived actions require approval review")
        missing_blocked = set(MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blocked:
            raise ValueError("memory-derived action missing blocked refs")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by memory-derived actions")
        return self


def build_memory_to_loop_binding_item(
    *,
    surface: MemoryToLoopSurface,
    loop_binding_state: MemoryToLoopBindingState,
    memory_candidate_ref: str,
    review_ref: str,
    safe_summary: str,
    source_refs: list[str],
    evidence_refs: list[str],
    missing_evidence_refs: list[str],
    stale_state: str,
    correction_refs: list[str] | None = None,
    rejected_item_refs: list[str] | None = None,
    follow_up_commitment_refs: list[str] | None = None,
    accepted_recall_refs: list[str] | None = None,
    next_safe_action: str,
) -> MemoryToLoopBindingItem:
    surface_slug = surface.lower().replace(" ", "-")
    memory_slug = memory_candidate_ref.replace(":", "-")
    return MemoryToLoopBindingItem(
        loop_item_ref=f"memory-loop-binding:{surface_slug}:{memory_slug}",
        surface=surface,
        loop_binding_state=loop_binding_state,
        memory_candidate_ref=memory_candidate_ref,
        review_ref=review_ref,
        safe_summary=safe_summary,
        source_refs=source_refs,
        evidence_refs=evidence_refs,
        accepted_recall_refs=accepted_recall_refs or [],
        correction_refs=correction_refs or [],
        rejected_item_refs=rejected_item_refs or [],
        follow_up_commitment_refs=follow_up_commitment_refs or [],
        stale_state=stale_state,
        missing_evidence_refs=missing_evidence_refs,
        next_safe_action=next_safe_action,
    )


def build_memory_derived_action_proposal(
    *,
    proposal_ref: str,
    source_memory_ref: str,
    source_loop_item_ref: str,
    source_review_ref: str,
    source_intake_proposal_ref: str | None = None,
    safe_summary: str,
    source_refs: list[str],
    provenance_refs: list[str] | None = None,
    evidence_refs: list[str],
    missing_evidence_refs: list[str],
    next_safe_action: str,
) -> MemoryDerivedActionProposal:
    return MemoryDerivedActionProposal(
        proposal_ref=proposal_ref,
        source_memory_ref=source_memory_ref,
        source_loop_item_ref=source_loop_item_ref,
        source_review_ref=source_review_ref,
        source_intake_proposal_ref=source_intake_proposal_ref,
        safe_summary=safe_summary,
        source_refs=source_refs,
        provenance_refs=provenance_refs or [],
        evidence_refs=evidence_refs,
        missing_evidence_refs=missing_evidence_refs,
        next_safe_action=next_safe_action,
    )


def memory_to_loop_authority_posture() -> dict[str, bool]:
    return {
        "safe_refs_only": True,
        "review_required": True,
        "memory_write_authorized": False,
        "automatic_recall_enabled": False,
        "context_injection_authorized": False,
        "approval_grant_capture_enabled": False,
        "action_execution_enabled": False,
        "connector_write_enabled": False,
        "account_sync_enabled": False,
        "source_truth_authority": False,
        "public_beta_claim_enabled": False,
        "public_distribution_claim_enabled": False,
        "production_authority_enabled": False,
    }


def memory_to_loop_surface_bindings() -> list[dict[str, str]]:
    return [
        {
            "surface": surface,
            "feed_status": "implemented_read_only_memory_loop_refs",
            "feed_ref": f"memory-loop-binding:{surface.lower().replace(' ', '-')}",
            "authority_boundary": (
                "Memory loop bindings are review-only safe refs and cannot write "
                "memory, inject context, approve work, or execute actions."
            ),
        }
        for surface in MEMORY_TO_LOOP_REQUIRED_SURFACES
    ]


def memory_to_loop_weekly_review_refs(
    loop_items: list[MemoryToLoopBindingItem],
) -> list[str]:
    return [
        f"weekly-review-ref:{item.loop_item_ref.replace(':', '-')}"
        for item in loop_items
    ]


def memory_to_loop_payload_is_safe(payload: dict[str, Any]) -> bool:
    serialized = str(payload).lower()
    return not any(fragment in serialized for fragment in _UNSAFE_TEXT_FRAGMENTS)


def _safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)
    _reject_unsafe_text(value, field_name)


def _safe_refs(values: list[str], field_name: str) -> None:
    for value in values:
        _safe_ref(value, field_name)


def _safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    _reject_unsafe_text(value, field_name)


def _reject_unsafe_text(value: str, field_name: str) -> None:
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe memory-to-loop text")


__all__ = [
    "MEMORY_DERIVED_ACTION_REQUIRED_REF_FIELDS",
    "MEMORY_TO_LOOP_BINDING_CONTRACT_REF",
    "MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS",
    "MEMORY_TO_LOOP_REQUIRED_REF_FIELDS",
    "MEMORY_TO_LOOP_REQUIRED_SURFACES",
    "MemoryDerivedActionProposal",
    "MemoryToLoopBindingState",
    "MemoryToLoopBindingItem",
    "MemoryToLoopSurface",
    "build_memory_derived_action_proposal",
    "build_memory_to_loop_binding_item",
    "memory_to_loop_authority_posture",
    "memory_to_loop_payload_is_safe",
    "memory_to_loop_surface_bindings",
    "memory_to_loop_weekly_review_refs",
]
