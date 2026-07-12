from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import validate_execution_ref
from ultimate_ai_agent.core.memory.l1_index import L1HotMemoryIndex


GOVERNED_MEMORY_CONTEXT_CONTRACT_REF = (
    "contract-ref:governed-memory-context-manifest:v1"
)
GOVERNED_MEMORY_CONTEXT_ROUTE_REF = "GET /control-center/memory/context-manifest"
GOVERNED_MEMORY_CONTEXT_BLOCKED_STATE_REFS = (
    "blocked-state:memory-context-no-hidden-injection",
    "blocked-state:memory-context-no-automatic-memory-truth",
    "blocked-state:memory-context-no-action-authority",
    "blocked-state:memory-context-no-approval-authority",
    "blocked-state:memory-context-no-connector-write",
    "blocked-state:memory-context-no-model-provider-call",
    "blocked-state:memory-context-no-production-authority",
)

MemoryContextBudgetStatus = Literal["available", "constrained", "exhausted"]


def _safe_ref(value: str, field_name: str) -> str:
    validate_execution_ref(value, field_name)
    return value


def _safe_refs(values: list[str], field_name: str) -> list[str]:
    refs = list(dict.fromkeys(str(value) for value in values))
    for ref in refs:
        _safe_ref(ref, field_name)
    return refs


def _fingerprint(payload: dict[str, Any], prefix: str) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"


def _token_estimate(refs: list[str]) -> int:
    return sum(max(1, (len(ref) + 3) // 4) for ref in refs)


def _confidence_posture(score: float, trust: float) -> str:
    combined = min(score, trust)
    band = "high" if combined >= 0.8 else "medium" if combined >= 0.5 else "low"
    return f"confidence-posture-ref:memory-context:{band}"


class MemoryContextBudget(BaseModel):
    max_items: int = Field(ge=1, le=50)
    max_tokens: int = Field(ge=1, le=10000)
    selected_items: int = Field(ge=0)
    used_tokens: int = Field(ge=0)
    capacity_excluded_items: int = Field(default=0, ge=0)
    status: MemoryContextBudgetStatus

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_budget(self) -> "MemoryContextBudget":
        if self.selected_items > self.max_items:
            raise ValueError("memory context item budget exceeded")
        if self.used_tokens > self.max_tokens:
            raise ValueError("memory context token budget exceeded")
        expected = (
            "exhausted"
            if self.selected_items == 0
            else "constrained"
            if self.capacity_excluded_items > 0
            or self.selected_items == self.max_items
            or self.used_tokens == self.max_tokens
            else "available"
        )
        if self.status != expected:
            raise ValueError("memory context budget status drifted")
        return self


class MemoryContextSelection(BaseModel):
    memory_ref: str
    source_refs: list[str]
    evidence_refs: list[str]
    receipt_refs: list[str]
    inclusion_reason_refs: list[str]
    confidence_posture_ref: str
    freshness_posture_ref: str
    conflict_posture_ref: str
    sensitivity_posture_ref: str
    token_estimate: int = Field(ge=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_selection(self) -> "MemoryContextSelection":
        for field_name in (
            "memory_ref",
            "confidence_posture_ref",
            "freshness_posture_ref",
            "conflict_posture_ref",
            "sensitivity_posture_ref",
        ):
            _safe_ref(str(getattr(self, field_name)), field_name)
        for field_name in (
            "source_refs",
            "evidence_refs",
            "receipt_refs",
            "inclusion_reason_refs",
        ):
            values = getattr(self, field_name)
            if not values:
                raise ValueError(f"{field_name} is required")
            _safe_refs(values, field_name)
        return self


class MemoryContextExclusion(BaseModel):
    memory_ref: str
    reason_refs: list[str]

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_exclusion(self) -> "MemoryContextExclusion":
        _safe_ref(self.memory_ref, "memory_ref")
        if not self.reason_refs:
            raise ValueError("memory context exclusion requires reason refs")
        _safe_refs(self.reason_refs, "reason_refs")
        return self


class GovernedMemoryContextManifest(BaseModel):
    schema_version: str = "governed_memory_context_manifest.v1"
    contract_ref: str = GOVERNED_MEMORY_CONTEXT_CONTRACT_REF
    route_ref: str = GOVERNED_MEMORY_CONTEXT_ROUTE_REF
    status: Literal["ready_for_operator_preview", "blocked_no_eligible_context"]
    context_manifest_ref: str
    manifest_fingerprint_ref: str
    context_receipt_ref: str
    context_receipt_status: Literal["derived_preview_not_persisted"] = (
        "derived_preview_not_persisted"
    )
    query_ref: str
    source_index_generated_at: datetime
    source_scan_truncated: bool = False
    candidate_count_complete: bool = True
    checked_at: datetime
    expires_at: datetime
    budget: MemoryContextBudget
    candidate_count: int = Field(ge=0)
    selection_count: int = Field(ge=0)
    exclusion_count: int = Field(ge=0)
    selections: list[MemoryContextSelection]
    exclusions: list[MemoryContextExclusion]
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(GOVERNED_MEMORY_CONTEXT_BLOCKED_STATE_REFS)
    )
    redaction_status: str = "safe_refs_only"
    preview_only: bool = True
    context_injection_authorized: bool = False
    automatic_memory_inclusion_authorized: bool = False
    memory_truth_authority: bool = False
    action_execution_authorized: bool = False
    approval_authority_granted: bool = False
    connector_write_authorized: bool = False
    model_provider_authority_allowed: bool = False
    raw_content_persisted: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_manifest(self) -> "GovernedMemoryContextManifest":
        if self.schema_version != "governed_memory_context_manifest.v1":
            raise ValueError("memory context schema version drifted")
        if self.contract_ref != GOVERNED_MEMORY_CONTEXT_CONTRACT_REF:
            raise ValueError("memory context contract ref drifted")
        if self.route_ref != GOVERNED_MEMORY_CONTEXT_ROUTE_REF:
            raise ValueError("memory context route ref drifted")
        if self.redaction_status != "safe_refs_only":
            raise ValueError("memory context redaction posture drifted")
        for field_name in (
            "contract_ref",
            "context_manifest_ref",
            "manifest_fingerprint_ref",
            "context_receipt_ref",
            "query_ref",
        ):
            _safe_ref(str(getattr(self, field_name)), field_name)
        _safe_refs(self.blocked_state_refs, "blocked_state_refs")
        if not set(GOVERNED_MEMORY_CONTEXT_BLOCKED_STATE_REFS).issubset(
            self.blocked_state_refs
        ):
            raise ValueError("memory context required blockers drifted")
        if self.selection_count != len(self.selections):
            raise ValueError("memory context selection count drifted")
        if self.exclusion_count != len(self.exclusions):
            raise ValueError("memory context exclusion count drifted")
        if self.candidate_count != self.selection_count + self.exclusion_count:
            raise ValueError("memory context candidate count drifted")
        if self.candidate_count_complete == self.source_scan_truncated:
            raise ValueError("memory context candidate completeness drifted")
        if self.budget.selected_items != self.selection_count:
            raise ValueError("memory context budget selection count drifted")
        if self.budget.used_tokens != sum(
            selection.token_estimate for selection in self.selections
        ):
            raise ValueError("memory context token accounting drifted")
        if set(selection.memory_ref for selection in self.selections).intersection(
            exclusion.memory_ref for exclusion in self.exclusions
        ):
            raise ValueError("memory context ref cannot be selected and excluded")
        if len({selection.memory_ref for selection in self.selections}) != len(
            self.selections
        ):
            raise ValueError("memory context selections must be unique")
        if len({exclusion.memory_ref for exclusion in self.exclusions}) != len(
            self.exclusions
        ):
            raise ValueError("memory context exclusions must be unique")
        if self.expires_at <= self.checked_at:
            raise ValueError("memory context manifest must expire after checking")
        if self.status == "ready_for_operator_preview" and not self.selections:
            raise ValueError("ready context manifest requires selections")
        if self.status == "blocked_no_eligible_context" and self.selections:
            raise ValueError("blocked context manifest cannot contain selections")
        for field_name in (
            "preview_only",
        ):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must remain true")
        for field_name in (
            "context_injection_authorized",
            "automatic_memory_inclusion_authorized",
            "memory_truth_authority",
            "action_execution_authorized",
            "approval_authority_granted",
            "connector_write_authorized",
            "model_provider_authority_allowed",
            "raw_content_persisted",
            "production_authority_enabled",
        ):
            if getattr(self, field_name) is not False:
                raise ValueError(f"{field_name} must remain false")
        return self


def build_governed_memory_context_manifest(
    *,
    l1_index: L1HotMemoryIndex | dict[str, Any],
    query_ref: str | None,
    checked_at: datetime | None = None,
    max_items: int = 8,
    max_tokens: int = 512,
) -> GovernedMemoryContextManifest:
    index = l1_index if isinstance(l1_index, L1HotMemoryIndex) else L1HotMemoryIndex(**l1_index)
    effective_checked_at = checked_at or index.generated_at
    if effective_checked_at.tzinfo is None:
        effective_checked_at = effective_checked_at.replace(tzinfo=timezone.utc)
    index_generated_at = index.generated_at
    if index_generated_at.tzinfo is None:
        index_generated_at = index_generated_at.replace(tzinfo=timezone.utc)
    if effective_checked_at != index_generated_at:
        raise ValueError("memory context checked_at must match the L1 index snapshot")
    effective_query_ref = (
        index.query_ref
        or index.safe_query_ref
        or "query-ref:memory-context:default"
    )
    if query_ref is not None and query_ref != effective_query_ref:
        raise ValueError("memory context query_ref must match the L1 index query")
    bounded_items = max(1, min(int(max_items), 50))
    bounded_tokens = max(1, min(int(max_tokens), 10000))
    exclusions_by_ref = {
        ref: [reason]
        for ref, reason in sorted(index.skipped_record_reasons.items())
    }
    selections: list[MemoryContextSelection] = []
    used_tokens = 0
    capacity_excluded_items = 0
    for preview in sorted(
        index.previews,
        key=lambda item: (-item.score, item.memory_record_ref),
    ):
        supporting_refs = _safe_refs(
            [
                preview.memory_record_ref,
                *preview.source_refs,
                *preview.evidence_refs,
                *preview.receipt_refs,
            ],
            "supporting_refs",
        )
        estimate = _token_estimate(supporting_refs)
        reason: str | None = None
        if index.scan_truncated:
            reason = "excluded-reason-ref:memory-context:source-scan-truncated"
        elif preview.expires_at is not None and preview.expires_at <= effective_checked_at:
            reason = "excluded-reason-ref:memory-context:expired-at-snapshot"
        elif preview.sensitivity == "unknown" or preview.data_classification == "unknown":
            reason = "excluded-reason-ref:memory-context:sensitivity-unknown"
        elif len(selections) >= bounded_items:
            reason = "excluded-reason-ref:memory-context:item-budget"
        elif used_tokens + estimate > bounded_tokens:
            reason = "excluded-reason-ref:memory-context:capacity-budget"
        if reason is not None:
            exclusions_by_ref.setdefault(preview.memory_record_ref, []).append(reason)
            if reason.endswith(("item-budget", "capacity-budget")):
                capacity_excluded_items += 1
            continue
        selection = MemoryContextSelection(
            memory_ref=preview.memory_record_ref,
            source_refs=list(preview.source_refs),
            evidence_refs=list(preview.evidence_refs),
            receipt_refs=list(preview.receipt_refs),
            inclusion_reason_refs=[
                "inclusion-reason-ref:memory-context:reviewed-recall",
                "inclusion-reason-ref:memory-context:provenance-bound",
                "inclusion-reason-ref:memory-context:within-budget",
            ],
            confidence_posture_ref=_confidence_posture(
                preview.confidence_score,
                preview.trust_score,
            ),
            freshness_posture_ref=(
                "freshness-posture-ref:memory-context:observed-at-index-snapshot"
            ),
            conflict_posture_ref="conflict-posture-ref:memory-context:none",
            sensitivity_posture_ref=(
                "sensitivity-posture-ref:memory-context:"
                + preview.sensitivity.replace("_", "-")
            ),
            token_estimate=estimate,
        )
        selections.append(selection)
        used_tokens += estimate
    exclusions = [
        MemoryContextExclusion(memory_ref=ref, reason_refs=_safe_refs(reasons, "reason_refs"))
        for ref, reasons in sorted(exclusions_by_ref.items())
    ]
    basis = {
        "contract_ref": GOVERNED_MEMORY_CONTEXT_CONTRACT_REF,
        "route_ref": GOVERNED_MEMORY_CONTEXT_ROUTE_REF,
        "query_ref": effective_query_ref,
        "checked_at": effective_checked_at.isoformat(),
        "source_index_generated_at": index_generated_at.isoformat(),
        "source_scan_limit": index.scan_limit,
        "source_scanned_record_count": index.scanned_record_count,
        "source_scan_truncated": index.scan_truncated,
        "source_query_mode": index.query_mode,
        "source_safe_query_ref": index.safe_query_ref,
        "selections": [selection.model_dump(mode="json") for selection in selections],
        "excluded": [exclusion.model_dump(mode="json") for exclusion in exclusions],
        "max_items": bounded_items,
        "max_tokens": bounded_tokens,
        "used_tokens": used_tokens,
        "capacity_excluded_items": capacity_excluded_items,
        "blocked_state_refs": list(GOVERNED_MEMORY_CONTEXT_BLOCKED_STATE_REFS),
    }
    fingerprint = _fingerprint(basis, "fingerprint-ref:memory-context-manifest")
    suffix = fingerprint.rsplit(":", 1)[-1][:24]
    budget_status: MemoryContextBudgetStatus = (
        "exhausted"
        if not selections
        else "constrained"
        if capacity_excluded_items > 0
        or len(selections) == bounded_items
        or used_tokens == bounded_tokens
        else "available"
    )
    selected_expiries = [
        preview.expires_at
        for preview in index.previews
        if preview.memory_record_ref
        in {selection.memory_ref for selection in selections}
        and preview.expires_at is not None
    ]
    snapshot_expires_at = effective_checked_at + timedelta(hours=12)
    effective_expires_at = min(
        [snapshot_expires_at, *selected_expiries]
    )
    return GovernedMemoryContextManifest(
        status=(
            "ready_for_operator_preview"
            if selections
            else "blocked_no_eligible_context"
        ),
        context_manifest_ref=f"context-manifest-ref:governed-memory:{suffix}",
        manifest_fingerprint_ref=fingerprint,
        context_receipt_ref=f"receipt-ref:memory-context:{suffix}",
        query_ref=str(basis["query_ref"]),
        checked_at=effective_checked_at,
        source_index_generated_at=index_generated_at,
        source_scan_truncated=index.scan_truncated,
        candidate_count_complete=not index.scan_truncated,
        expires_at=effective_expires_at,
        budget=MemoryContextBudget(
            max_items=bounded_items,
            max_tokens=bounded_tokens,
            selected_items=len(selections),
            used_tokens=used_tokens,
            capacity_excluded_items=capacity_excluded_items,
            status=budget_status,
        ),
        candidate_count=len(selections) + len(exclusions),
        selection_count=len(selections),
        exclusion_count=len(exclusions),
        selections=selections,
        exclusions=exclusions,
    )


__all__ = [
    "GOVERNED_MEMORY_CONTEXT_BLOCKED_STATE_REFS",
    "GOVERNED_MEMORY_CONTEXT_CONTRACT_REF",
    "GOVERNED_MEMORY_CONTEXT_ROUTE_REF",
    "GovernedMemoryContextManifest",
    "MemoryContextBudget",
    "MemoryContextExclusion",
    "MemoryContextSelection",
    "build_governed_memory_context_manifest",
]
