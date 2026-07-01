from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


WEEKLY_CEO_REVIEW_V1_CONTRACT_REF = (
    "contract-ref:product-loop-008-weekly-ceo-review-v1:v1"
)
WEEKLY_CEO_REVIEW_V1_READ_MODEL_SOURCE = (
    "python_core_weekly_ceo_review_v1_read_model"
)
WEEKLY_CEO_REVIEW_V1_REQUIRED_BLOCKED_REFS: tuple[str, ...] = (
    "blocked-state:weekly-ceo-review-no-raw-logs",
    "blocked-state:weekly-ceo-review-no-raw-prompts",
    "blocked-state:weekly-ceo-review-no-raw-responses",
    "blocked-state:weekly-ceo-review-no-provider-payloads",
    "blocked-state:weekly-ceo-review-no-connector-runtime",
    "blocked-state:weekly-ceo-review-no-connector-write",
    "blocked-state:weekly-ceo-review-no-email-calendar-fetch",
    "blocked-state:weekly-ceo-review-no-model-summary",
    "blocked-state:weekly-ceo-review-no-provider-model-call",
    "blocked-state:weekly-ceo-review-no-automatic-memory-write",
    "blocked-state:weekly-ceo-review-no-context-injection",
    "blocked-state:weekly-ceo-review-no-action-execution",
    "blocked-state:weekly-ceo-review-no-production-claim",
    "blocked-state:weekly-ceo-review-no-production-authority",
)

_SAFE_REF_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9:_#=-]{0,239}$")
_SAFE_SUFFIX_RE = re.compile(r"[^a-z0-9_-]+")
_UNSAFE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "provider exchange",
    "raw provider",
    "raw_provider",
    "raw path",
    "raw_path",
    "raw log",
    "raw_log",
    "account identifier",
    "account_identifier",
    "username",
    "user name",
    "hostname",
    "host name",
    "credential",
    "api_key",
    "authorization",
    "secret",
    "bearer",
    "token",
    "cookie",
    "password",
    "private_key",
    "env dump",
    "environment dump",
    "stack trace",
    "traceback",
    "serial",
    "/users/",
    "/home/",
    "/private/",
    "/tmp/",
    "/var/",
    "/etc/",
    "\\users\\",
    "\\appdata\\",
    ":\\",
)
_DENIED_FLAGS = (
    "raw_logs_included",
    "prompt_content_included",
    "response_content_included",
    "provider_exchange_content_included",
    "connector_read_enabled",
    "connector_runtime_enabled",
    "connector_write_enabled",
    "email_calendar_fetch_enabled",
    "live_web_enabled",
    "model_summary_enabled",
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "action_execution_enabled",
    "shell_subprocess_execution_enabled",
    "browser_execution_enabled",
    "public_beta_claim_enabled",
    "production_claim_enabled",
    "production_authority_enabled",
)


class WeeklyCeoReviewV1ReadModel(BaseModel):
    schema_version: str = "product-loop-008-weekly-ceo-review.v1"
    contract_ref: str = WEEKLY_CEO_REVIEW_V1_CONTRACT_REF
    status: str = "implemented_backend_owned_weekly_review_artifact_v1"
    source: str = WEEKLY_CEO_REVIEW_V1_READ_MODEL_SOURCE
    backend_owned: bool = True
    local_review_artifact_only: bool = True
    safe_refs_only: bool = True
    safe_summary_only: bool = True
    raw_content_included: bool = False
    evidence_backed: bool = True
    review_period_ref: str = "review-period-ref:local-weekly-window"
    safe_summary: str = (
        "Weekly CEO Review V1 summarizes local completed, deferred, rejected, "
        "blocked, stale, unresolved, follow-up, memory-decision, action-decision, "
        "and evidence refs without storing raw source content."
    )
    completed_count: int = Field(default=0, ge=0)
    deferred_count: int = Field(default=0, ge=0)
    rejected_count: int = Field(default=0, ge=0)
    blocked_count: int = Field(default=0, ge=0)
    stale_count: int = Field(default=0, ge=0)
    unresolved_count: int = Field(default=0, ge=0)
    action_decision_count: int = Field(default=0, ge=0)
    memory_decision_count: int = Field(default=0, ge=0)
    follow_up_count: int = Field(default=0, ge=0)
    evidence_event_count: int = Field(default=0, ge=0)
    completed_refs: list[str] = Field(default_factory=list)
    deferred_refs: list[str] = Field(default_factory=list)
    rejected_refs: list[str] = Field(default_factory=list)
    blocked_refs: list[str] = Field(default_factory=list)
    stale_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    carry_forward_refs: list[str] = Field(default_factory=list)
    next_week_priority_refs: list[str] = Field(default_factory=list)
    action_decision_refs: list[str] = Field(default_factory=list)
    memory_decision_refs: list[str] = Field(default_factory=list)
    follow_up_refs: list[str] = Field(default_factory=list)
    evidence_event_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    receipt_refs: list[str] = Field(default_factory=list)
    missing_source_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list, min_length=1)
    next_safe_action: str = (
        "Review carry-forward, unresolved, blocked, stale, and missing-source "
        "refs before choosing the next local product loop priority."
    )
    authority_boundary: str = (
        "Weekly CEO Review V1 is a backend-owned local review artifact. It "
        "summarizes safe refs only and does not fetch connectors, call models, "
        "summarize with providers, write memory, inject context, execute actions, "
        "read live web, run shell or browser execution, or claim production "
        "readiness."
    )
    raw_logs_included: bool = False
    prompt_content_included: bool = False
    response_content_included: bool = False
    provider_exchange_content_included: bool = False
    connector_read_enabled: bool = False
    connector_runtime_enabled: bool = False
    connector_write_enabled: bool = False
    email_calendar_fetch_enabled: bool = False
    live_web_enabled: bool = False
    model_summary_enabled: bool = False
    provider_model_call_enabled: bool = False
    runtime_model_call_enabled: bool = False
    automatic_memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    action_execution_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_execution_enabled: bool = False
    public_beta_claim_enabled: bool = False
    production_claim_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "WeeklyCeoReviewV1ReadModel":
        if self.schema_version != "product-loop-008-weekly-ceo-review.v1":
            raise ValueError("unexpected Weekly CEO Review V1 schema version")
        if self.contract_ref != WEEKLY_CEO_REVIEW_V1_CONTRACT_REF:
            raise ValueError("unexpected Weekly CEO Review V1 contract ref")
        if self.source != WEEKLY_CEO_REVIEW_V1_READ_MODEL_SOURCE:
            raise ValueError("unexpected Weekly CEO Review V1 read-model source")
        for field_name in (
            "backend_owned",
            "local_review_artifact_only",
            "safe_refs_only",
            "safe_summary_only",
            "evidence_backed",
        ):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must remain true")
        if self.raw_content_included:
            raise ValueError("Weekly CEO Review V1 must not include raw content")
        for field_name in _DENIED_FLAGS:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must remain false")
        for field_name in (
            "status",
            "source",
            "safe_summary",
            "next_safe_action",
            "authority_boundary",
        ):
            _validate_safe_text(str(getattr(self, field_name)), field_name)
        _validate_safe_ref(self.review_period_ref, "review_period_ref")
        for field_name in (
            "completed_refs",
            "deferred_refs",
            "rejected_refs",
            "blocked_refs",
            "stale_refs",
            "unresolved_refs",
            "carry_forward_refs",
            "next_week_priority_refs",
            "action_decision_refs",
            "memory_decision_refs",
            "follow_up_refs",
            "evidence_event_refs",
            "evidence_refs",
            "receipt_refs",
            "missing_source_refs",
            "blocked_authority_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        missing_blockers = set(WEEKLY_CEO_REVIEW_V1_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_authority_refs
        )
        if missing_blockers:
            raise ValueError("Weekly CEO Review V1 missing blocked authority refs")
        for ref in self.evidence_event_refs:
            if not ref.startswith("evidence-event:"):
                raise ValueError("Weekly CEO Review V1 evidence event refs must be productized")
        count_pairs = (
            ("completed_count", "completed_refs"),
            ("deferred_count", "deferred_refs"),
            ("rejected_count", "rejected_refs"),
            ("blocked_count", "blocked_refs"),
            ("stale_count", "stale_refs"),
            ("unresolved_count", "unresolved_refs"),
            ("action_decision_count", "action_decision_refs"),
            ("memory_decision_count", "memory_decision_refs"),
            ("follow_up_count", "follow_up_refs"),
            ("evidence_event_count", "evidence_event_refs"),
        )
        for count_field, refs_field in count_pairs:
            if getattr(self, count_field) != len(getattr(self, refs_field)):
                raise ValueError(f"{count_field} must match {refs_field}")
        return self


def build_weekly_ceo_review_v1_read_model(
    *,
    weekly_review_narrative: dict[str, Any],
    actions: list[dict[str, Any]],
    memory_review_decisions: list[dict[str, Any]],
    follow_up_tracker: dict[str, Any],
    evidence_timeline: list[dict[str, Any]],
    source_readiness_items: list[dict[str, Any]],
    evidence_event_refs: list[str],
) -> dict[str, Any]:
    completed_refs = _receipt_backed_completed_refs(actions)
    deferred_refs = _refs(weekly_review_narrative.get("deferred_refs"))
    rejected_refs = _refs(weekly_review_narrative.get("rejected_refs"))
    blocked_refs = _refs(weekly_review_narrative.get("blocked_refs"))
    stale_refs = _refs(weekly_review_narrative.get("stale_refs"))
    missing_source_refs = _refs(weekly_review_narrative.get("missing_source_refs"))
    carry_forward_refs = _refs(weekly_review_narrative.get("carry_forward_refs"))
    next_week_priority_refs = _refs(
        weekly_review_narrative.get("next_week_priority_refs")
    )
    follow_up_refs = _refs(follow_up_tracker.get("relationship_follow_up_refs"))
    follow_up_refs.extend(_refs(follow_up_tracker.get("promise_refs")))
    follow_up_refs.extend(_refs(follow_up_tracker.get("open_loop_refs")))
    follow_up_refs.extend(_refs(follow_up_tracker.get("pending_reply_refs")))
    follow_up_refs.extend(_refs(follow_up_tracker.get("deferred_decision_refs")))

    action_decision_refs: list[str] = []
    receipt_refs: list[str] = []
    blocked_authority_refs: list[str] = list(WEEKLY_CEO_REVIEW_V1_REQUIRED_BLOCKED_REFS)
    for action in actions:
        visibility = action.get("receipt_visibility")
        if isinstance(visibility, dict):
            decision_ref = str(visibility.get("decision_receipt_ref", ""))
            if decision_ref.startswith("receipt:"):
                action_decision_refs.append(decision_ref)
                receipt_refs.append(decision_ref)
        receipt_refs.extend(
            ref for ref in _refs(action.get("receipt_refs")) if ref.startswith("receipt:")
        )
        blocked_authority_refs.extend(_refs(action.get("action_blocked_state_refs")))
        blocked_authority_refs.extend(_refs(action.get("cost_blocked_state_refs")))
        blocked_authority_refs.extend(_refs(action.get("local_task_commit_blocked_reasons")))

    memory_decision_refs = [
        str(decision["receipt_ref"])
        for decision in memory_review_decisions
        if decision.get("receipt_ref")
    ]
    receipt_refs.extend(memory_decision_refs)
    bounded_evidence_event_refs = _refs(evidence_event_refs)[:12]
    evidence_refs = _unique_refs(
        [
            "evidence-ref:weekly-ceo-review-v1",
            *_refs(weekly_review_narrative.get("evidence_refs")),
            *[
                evidence_ref
                for item in evidence_timeline[:8]
                for evidence_ref in _refs(item.get("evidence_refs"))
            ],
        ]
    )
    unresolved_refs = _unique_refs(
        [
            *carry_forward_refs,
            *blocked_refs,
            *missing_source_refs,
            *[
                item["source_ref"]
                for item in source_readiness_items
                if item.get("status")
                in {"missing", "blocked", "unavailable", "not_configured"}
            ],
        ]
    )
    blocked_authority_refs.extend(blocked_refs)
    blocked_authority_refs.extend(
        [
            blocked_ref
            for item in source_readiness_items
            for blocked_ref in _refs(item.get("blocked_state_refs"))
        ]
    )

    model = WeeklyCeoReviewV1ReadModel(
        completed_count=len(completed_refs),
        deferred_count=len(deferred_refs),
        rejected_count=len(rejected_refs),
        blocked_count=len(blocked_refs),
        stale_count=len(stale_refs),
        unresolved_count=len(unresolved_refs),
        action_decision_count=len(_unique_refs(action_decision_refs)),
        memory_decision_count=len(memory_decision_refs),
        follow_up_count=len(_unique_refs(follow_up_refs)),
        evidence_event_count=len(bounded_evidence_event_refs),
        completed_refs=completed_refs,
        deferred_refs=deferred_refs,
        rejected_refs=rejected_refs,
        blocked_refs=blocked_refs,
        stale_refs=stale_refs,
        unresolved_refs=unresolved_refs,
        carry_forward_refs=carry_forward_refs,
        next_week_priority_refs=next_week_priority_refs,
        action_decision_refs=_unique_refs(action_decision_refs),
        memory_decision_refs=_unique_refs(memory_decision_refs),
        follow_up_refs=_unique_refs(follow_up_refs),
        evidence_event_refs=bounded_evidence_event_refs,
        evidence_refs=evidence_refs,
        receipt_refs=_unique_refs(receipt_refs),
        missing_source_refs=missing_source_refs,
        blocked_authority_refs=_unique_refs(blocked_authority_refs),
    )
    return model.model_dump(mode="json")


def _refs(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        str(item)
        for item in value
        if isinstance(item, str) and item and _is_safe_ref(str(item))
    ]


def _receipt_backed_completed_refs(actions: list[dict[str, Any]]) -> list[str]:
    completed_refs: list[str] = []
    for action in actions:
        status = str(action.get("status", "unknown"))
        if status in {"completed", "receipt_recorded"} and _completion_receipt_refs(
            action
        ):
            completed_refs.append(
                "action-status-ref:"
                f"{str(action.get('item_ref', 'unknown')).replace(':', '-')}:"
                f"{status}"
            )
    return _unique_refs(completed_refs)


def _completion_receipt_refs(action: dict[str, Any]) -> list[str]:
    receipt_refs = [
        ref for ref in _refs(action.get("receipt_refs")) if ref.startswith("receipt:")
    ]
    local_task_receipt_ref = action.get("local_task_commit_receipt_ref")
    if isinstance(local_task_receipt_ref, str) and local_task_receipt_ref.startswith(
        "receipt:"
    ):
        receipt_refs.append(local_task_receipt_ref)
    return _unique_refs(receipt_refs)


def _unique_refs(refs: list[str]) -> list[str]:
    return sorted(set(refs))


def _validate_ref_list(refs: list[str], field_name: str) -> None:
    for ref in refs:
        _validate_safe_ref(str(ref), field_name)


def _validate_safe_ref(value: str, field_name: str) -> None:
    if not _SAFE_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} contains unsafe ref")
    _validate_safe_text(value, field_name)


def _is_safe_ref(value: str) -> bool:
    try:
        _validate_safe_ref(value, "ref")
    except ValueError:
        return False
    return True


def _validate_safe_text(value: str, field_name: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe/private content")
    suffix = _SAFE_SUFFIX_RE.sub("-", lowered).strip("-")
    if suffix in {"secret", "token", "password", "credential"}:
        raise ValueError(f"{field_name} contains unsafe/private content")
