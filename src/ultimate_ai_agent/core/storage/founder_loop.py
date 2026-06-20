from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.time import utc_now


FOUNDER_LOOP_SCHEMA_VERSION = "founder_loop_storage.v1"
FOUNDER_LOOP_STATE_DIR_ENV = "UAA_FOUNDER_LOOP_STATE_DIR"
DEFAULT_FOUNDER_LOOP_STATE_DIR = Path(".uaa") / "founder_loop"

UNSAFE_STORAGE_TEXT_FRAGMENTS = (
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
    "environment dump",
    "environment_dump",
    "credential material",
    "credential_material",
    "unredacted transcript",
    "full transcript",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
)
UNSAFE_STORAGE_KEY_FRAGMENTS = (
    "api_key",
    "authorization",
    "client_secret",
    "cookie",
    "credential",
    "hostname",
    "password",
    "private_key",
    "provider_payload",
    "raw_log",
    "raw_path",
    "raw_prompt",
    "raw_response",
    "secret",
    "serial",
    "token",
    "username",
)


class FounderLoopStorageError(Exception):
    """Base error for storage-backed Founder Loop state."""


class FounderLoopStorageDuplicateError(FounderLoopStorageError):
    """Raised when a duplicate idempotency key is denied."""


class JsonlLogKind(str, Enum):
    audit = "audit"
    transcript = "transcript"
    realtime = "realtime"
    receipt = "receipt"


class FounderLoopActionRecord(BaseModel):
    item_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    surface: str = Field(..., min_length=1, max_length=80)
    priority: str = Field(default="medium", min_length=1, max_length=40)
    risk_class: str = Field(default="medium", min_length=1, max_length=40)
    status: str = Field(default="review_ready", min_length=1, max_length=80)
    side_effect_class: str = Field(default="validation_only", min_length=1, max_length=80)
    authority_boundary: str = Field(
        default=(
            "Control Center is review-only; Python Agent Core approval is required "
            "before mutation."
        ),
        min_length=1,
        max_length=240,
    )
    approval_required: bool = True
    approval_envelope_ref: str | None = Field(default=None, max_length=120)
    approval_envelope_status: str = Field(
        default="missing_until_scoped_contract",
        min_length=1,
        max_length=80,
    )
    state_change_contract_ref: str | None = Field(default=None, max_length=120)
    state_change_readiness: str = Field(
        default="blocked_missing_backend_contract",
        min_length=1,
        max_length=80,
    )
    blocked_state: str | None = Field(default=None, max_length=160)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    idempotency_key_ref: str | None = Field(default=None, max_length=120)
    expires_at: str | None = Field(default=None, max_length=80)
    stale_state: str = Field(
        default="recheck_required_before_mutation",
        min_length=1,
        max_length=120,
    )
    rollback_ref: str | None = Field(default=None, max_length=120)
    safe_disable_ref: str | None = Field(default=None, max_length=120)
    next_safe_action: str = Field(
        default="Review the safe summary and keep mutation blocked until a scoped backend contract exists.",
        min_length=1,
        max_length=240,
    )
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopActionRecord":
        _validate_safe_ref(self.item_ref, "item_ref")
        for field_name in [
            "approval_envelope_ref",
            "state_change_contract_ref",
            "idempotency_key_ref",
            "rollback_ref",
            "safe_disable_ref",
        ]:
            ref_value = getattr(self, field_name)
            if ref_value is not None:
                _validate_safe_ref(ref_value, field_name)
        for field_name in ["evidence_refs", "receipt_refs", "audit_refs"]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        _validate_safe_payload(self.model_dump(mode="json"), "action_record")
        return self


class FounderLoopPlanRecord(BaseModel):
    plan_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    status: str = Field(default="partial_backend_not_product_ready", min_length=1, max_length=80)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    next_step_summary: str = Field(..., min_length=1, max_length=500)
    evidence_refs: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopPlanRecord":
        _validate_safe_ref(self.plan_ref, "plan_ref")
        _validate_safe_payload(self.model_dump(mode="json"), "plan_record")
        return self


class FounderLoopMemoryReviewRecord(BaseModel):
    review_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    candidate_kind: str = Field(default="preference", min_length=1, max_length=80)
    priority: str = Field(default="medium", min_length=1, max_length=40)
    status: str = Field(default="review_needed", min_length=1, max_length=80)
    review_state: str = Field(default="review_needed", min_length=1, max_length=80)
    side_effect_class: str = Field(default="local_dev_workspace_only", min_length=1, max_length=80)
    authority_boundary: str = Field(
        default=(
            "Review-only memory candidate; memory writes and context injection "
            "remain unscoped."
        ),
        min_length=1,
        max_length=240,
    )
    provenance_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    missing_contract_refs: list[str] = Field(default_factory=list)
    correction_posture: str = Field(
        default="correction_requires_scoped_memory_write_contract",
        min_length=1,
        max_length=160,
    )
    rejection_posture: str = Field(
        default="rejection_is_review_state_only",
        min_length=1,
        max_length=160,
    )
    retention_posture: str = Field(
        default="retention_policy_not_bound",
        min_length=1,
        max_length=160,
    )
    delete_posture: str = Field(
        default="delete_execution_not_scoped",
        min_length=1,
        max_length=160,
    )
    confidence_posture: str = Field(
        default="safe_summary_unverified",
        min_length=1,
        max_length=160,
    )
    stale_state: str = Field(
        default="recheck_source_refs_before_memory_use",
        min_length=1,
        max_length=160,
    )
    blocked_states: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(
        default=(
            "Review provenance and evidence refs; keep writes blocked until a "
            "scoped memory policy milestone."
        ),
        min_length=1,
        max_length=240,
    )
    evidence_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopMemoryReviewRecord":
        _validate_safe_ref(self.review_ref, "review_ref")
        for field_name in [
            "provenance_refs",
            "source_refs",
            "missing_contract_refs",
            "evidence_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        _validate_safe_payload(self.model_dump(mode="json"), "memory_review_record")
        return self


class FounderLoopBriefingRecord(BaseModel):
    briefing_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    priority: str = Field(default="medium", min_length=1, max_length=40)
    status: str = Field(default="active", min_length=1, max_length=80)
    side_effect_class: str = Field(default="local_dev_workspace_only", min_length=1, max_length=80)
    authority_boundary: str = Field(
        default="Review-only briefing summary; source reads and delivery remain unscoped.",
        min_length=1,
        max_length=240,
    )
    source_readiness: str = Field(
        default="blocked_missing_source_contract",
        min_length=1,
        max_length=100,
    )
    source_refs: list[str] = Field(default_factory=list)
    missing_contract_refs: list[str] = Field(default_factory=list)
    blocked_states: list[str] = Field(default_factory=list)
    stale_state: str = Field(
        default="recheck_required_before_source_contract",
        min_length=1,
        max_length=120,
    )
    evidence_gap: str = Field(
        default="No source connector evidence is bound in this briefing slice.",
        min_length=1,
        max_length=240,
    )
    next_safe_action: str = Field(
        default="Define read-only source contracts before source reads or refresh.",
        min_length=1,
        max_length=240,
    )
    evidence_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopBriefingRecord":
        _validate_safe_ref(self.briefing_ref, "briefing_ref")
        for field_name in ["source_refs", "missing_contract_refs", "evidence_refs"]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        _validate_safe_payload(self.model_dump(mode="json"), "briefing_record")
        return self


class FounderLoopEvidenceTimelineItem(BaseModel):
    timeline_item_ref: str = Field(..., min_length=1)
    item_kind: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    source_refs: list[str] = Field(default_factory=list)
    status_refs: list[str] = Field(default_factory=list)
    related_route_refs: list[str] = Field(default_factory=list)
    side_effect_class: str = Field(default="local_dev_workspace_only", min_length=1, max_length=80)
    authority_posture: str = Field(..., min_length=1, max_length=240)
    approval_posture: str = Field(
        default="approval_refs_are_identifiers_only_not_authority",
        min_length=1,
        max_length=160,
    )
    receipt_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    replay_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    rollback_blockers: list[str] = Field(default_factory=list)
    latency_refs: list[str] = Field(default_factory=list)
    foundation_gate_refs: list[str] = Field(default_factory=list)
    redaction_status: str = Field(default="redacted_summary_only", min_length=1, max_length=80)
    stale_state: str = Field(default="recheck_refs_before_use", min_length=1, max_length=120)
    missing_evidence_posture: str = Field(default="no_missing_safe_refs", min_length=1, max_length=180)
    blocked_states: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=240)
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_record(self) -> "FounderLoopEvidenceTimelineItem":
        _validate_safe_ref(self.timeline_item_ref, "timeline_item_ref")
        for field_name in [
            "source_refs",
            "status_refs",
            "receipt_refs",
            "audit_refs",
            "replay_refs",
            "rollback_refs",
            "latency_refs",
            "foundation_gate_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_ref(ref_value, field_name)
        for route_ref in self.related_route_refs:
            _validate_safe_text(route_ref, "related_route_ref")
        _validate_safe_payload(self.model_dump(mode="json"), "evidence_timeline_item")
        return self


def _validate_safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _validate_safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in UNSAFE_STORAGE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe Founder Loop storage text")


def _validate_safe_payload(value: Any, field_name: str) -> None:
    if isinstance(value, str):
        if value:
            _validate_safe_text(value, field_name)
        return
    if isinstance(value, list):
        for item in value:
            _validate_safe_payload(item, field_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = str(key).lower().replace("-", "_")
            if any(fragment in normalized_key for fragment in UNSAFE_STORAGE_KEY_FRAGMENTS):
                raise ValueError(f"{field_name} contains unsafe Founder Loop storage key")
            _validate_safe_payload(str(key), field_name)
            _validate_safe_payload(item, field_name)


def _json_dumps(value: Any) -> str:
    _validate_safe_payload(value, "json_payload")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _timeline_ref(kind: str, source_ref: str) -> str:
    return f"evidence-timeline:{kind}/{source_ref.replace(':', '/')}"


def _utc_iso() -> str:
    return utc_now().isoformat()


def _row_to_payload(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    for key in list(payload):
        if key.endswith("_json"):
            payload[key.removesuffix("_json")] = json.loads(payload.pop(key) or "[]")
    if "approval_required" in payload:
        payload["approval_required"] = bool(payload["approval_required"])
    return payload


class FounderLoopRepository:
    """Stdlib SQLite plus JSONL repository for the first Founder Loop state."""

    def __init__(self, state_dir: Path, *, seed_defaults: bool = True) -> None:
        self.state_dir = state_dir
        self.db_path = self.state_dir / "founder_loop.sqlite3"
        self.logs_dir = self.state_dir / "logs"
        self.seed_defaults = seed_defaults
        self._ensure_storage()

    @classmethod
    def from_env(cls, *, seed_defaults: bool = True) -> "FounderLoopRepository":
        configured = os.environ.get(FOUNDER_LOOP_STATE_DIR_ENV)
        state_dir = Path(configured) if configured else DEFAULT_FOUNDER_LOOP_STATE_DIR
        return cls(state_dir=state_dir, seed_defaults=seed_defaults)

    def storage_status(self) -> dict[str, Any]:
        counts = {
            "action_inbox": self._count("action_inbox"),
            "briefing_items": self._count("briefing_items"),
            "plan_summaries": self._count("plan_summaries"),
            "memory_review_queue": self._count("memory_review_queue"),
            "idempotency_keys": self._count("idempotency_keys"),
            "route_state_snapshots": self._count("route_state_snapshots"),
            "evidence_refs": self._count("evidence_refs"),
        }
        log_refs = {
            kind.value: f"founder-loop-log:{kind.value}"
            for kind in JsonlLogKind
        }
        return {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "migration_version": self._schema_version(),
            "storage_ref": "founder-loop-storage:local-sqlite-jsonl",
            "sqlite_state_ref": "founder-loop-sqlite:local-state",
            "jsonl_log_refs": log_refs,
            "counts": counts,
            "safe_refs_only": True,
            "raw_content_stored": False,
            "postgres_sync_required": False,
            "postgres_sync_status": "adapter_boundary_only",
            "backup_manifest_ref": "backup-manifest:founder-loop-minimum-set",
            "updated_at": _utc_iso(),
        }

    def today_summary(self, *, limit: int = 6) -> dict[str, Any]:
        actions = self.list_action_inbox(limit=limit)
        plans = self.list_plan_summaries(limit=3)
        memory_items = self.list_memory_review_queue(limit=3)
        briefing_items = self.list_briefing_items(limit=3)
        evidence_timeline = self._build_evidence_timeline(
            actions=actions,
            plans=plans,
            memory_items=memory_items,
            briefing_items=briefing_items,
        )
        return {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "status": "storage_backed_partial_loop",
            "surface": "Today",
            "storage_ref": "founder-loop-storage:local-sqlite-jsonl",
            "side_effect_class": "local_dev_workspace_only",
            "approval_required_before_mutation": True,
            "sections": {
                "action_inbox_count": len(actions),
                "plan_count": len(plans),
                "memory_review_count": len(memory_items),
                "briefing_count": len(briefing_items),
                "evidence_timeline_count": len(evidence_timeline),
            },
            "actions": actions,
            "plans": plans,
            "memory_review_queue": memory_items,
            "memory_review_route_ref": "/memory",
            "memory_review_backend_route_ref": "GET /control-center/today/summary",
            "memory_review_status": "storage_backed_review_queue",
            "memory_review_authority_boundary": (
                "Review-only memory candidates; recall is not truth, and writes, "
                "deletes, context injection, connector writes, model/provider calls, "
                "and background sync are unscoped."
            ),
            "memory_write_enabled": False,
            "memory_delete_enabled": False,
            "context_injection_enabled": False,
            "memory_review_missing_contract_refs": [
                "contract-ref:memory-write-policy-binding-missing",
                "contract-ref:memory-retention-delete-missing",
                "contract-ref:memory-review-decision-capture-missing",
                "contract-ref:context-injection-missing",
            ],
            "memory_review_blocked_states": [
                "no_memory_write",
                "no_context_injection",
                "no_memory_delete",
                "no_raw_source_display",
                "no_connector_write",
                "no_model_provider_authority",
                "no_background_sync",
            ],
            "briefing_items": briefing_items,
            "evidence_timeline": evidence_timeline,
            "evidence_timeline_route_ref": "/evidence",
            "evidence_timeline_backend_route_ref": "GET /control-center/today/summary",
            "evidence_timeline_status": "storage_backed_redacted_refs",
            "evidence_timeline_authority_boundary": (
                "Evidence Timeline is safe-ref and redacted-summary only. It does "
                "not expose raw content, grant approval, execute rollback, or confer "
                "production authority."
            ),
            "evidence_timeline_blocked_states": [
                "no_raw_evidence_display",
                "no_rollback_execution",
                "approval_refs_are_identifiers_only",
                "foundation_gate_refs_not_production_authority",
                "latency_refs_not_authority",
                "connector_source_runtime_blocked",
            ],
            "evidence_refs": ["evidence-ref:founder-loop:today-summary"],
            "blocked_states": [
                "no_action_execution_route",
                "no_connector_write_route",
                "no_runtime_model_call_route",
            ],
        }

    def _build_evidence_timeline(
        self,
        *,
        actions: list[dict[str, Any]],
        plans: list[dict[str, Any]],
        memory_items: list[dict[str, Any]],
        briefing_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        timeline: list[FounderLoopEvidenceTimelineItem] = []
        for action in actions:
            action_ref = str(action["item_ref"])
            receipt_refs = list(action.get("receipt_refs") or [])
            audit_refs = list(action.get("audit_refs") or [])
            rollback_refs = [action["rollback_ref"]] if action.get("rollback_ref") else []
            rollback_blockers = (
                []
                if rollback_refs
                else ["rollback_refs_missing_until_scoped_state_change_contract"]
            )
            blocked_states = [
                str(value)
                for value in [
                    action.get("blocked_state"),
                    action.get("state_change_readiness"),
                ]
                if value
            ]
            timeline.append(
                FounderLoopEvidenceTimelineItem(
                    timeline_item_ref=_timeline_ref("action", action_ref),
                    item_kind="receipt_audit_rollback_ref",
                    title=str(action["title"]),
                    safe_summary=(
                        "Action evidence is shown as receipt, audit, idempotency, "
                        "rollback, and safe-disable refs only; mutation stays blocked."
                    ),
                    source_refs=[action_ref],
                    status_refs=["status-ref:founder-loop-action-inbox"],
                    related_route_refs=["GET /control-center/actions/inbox", "/actions"],
                    side_effect_class=str(action.get("side_effect_class", "validation_only")),
                    authority_posture=str(action.get("authority_boundary")),
                    approval_posture=str(
                        action.get(
                            "approval_envelope_status",
                            "approval_refs_are_identifiers_only_not_authority",
                        )
                    ),
                    receipt_refs=receipt_refs,
                    audit_refs=audit_refs,
                    replay_refs=["replay-ref:founder-loop:action-inbox"],
                    rollback_refs=rollback_refs,
                    rollback_blockers=rollback_blockers,
                    redaction_status="redacted_summary_only",
                    stale_state=str(action.get("stale_state", "recheck_action_refs_before_use")),
                    missing_evidence_posture=(
                        "receipt_refs_available"
                        if receipt_refs
                        else "receipt_refs_missing_until_scoped_contract"
                    ),
                    blocked_states=blocked_states,
                    next_safe_action=str(action.get("next_safe_action")),
                )
            )
        for plan in plans:
            plan_ref = str(plan["plan_ref"])
            timeline.append(
                FounderLoopEvidenceTimelineItem(
                    timeline_item_ref=_timeline_ref("plan", plan_ref),
                    item_kind="plan_evidence_ref",
                    title=str(plan["title"]),
                    safe_summary=(
                        "Plan evidence is a bounded summary ref. It does not create "
                        "execution authority or a durable run by itself."
                    ),
                    source_refs=[plan_ref],
                    status_refs=["status-ref:founder-loop-plan-summary"],
                    related_route_refs=["/plans", "/task-decomposition/status"],
                    side_effect_class="validation_only",
                    authority_posture="Plan summary is inspection-only and not execution authority.",
                    approval_posture="approval_required_before_execution_scope",
                    receipt_refs=[],
                    audit_refs=[],
                    replay_refs=["replay-ref:founder-loop:plan-summary"],
                    rollback_refs=[],
                    rollback_blockers=["rollback_not_applicable_for_plan_summary"],
                    redaction_status="redacted_summary_only",
                    stale_state="recheck_plan_refs_before_execution_claims",
                    missing_evidence_posture="run_receipt_missing_until_execution_contract",
                    blocked_states=["no_plan_execution_from_evidence_timeline"],
                    next_safe_action=str(plan.get("next_step_summary")),
                )
            )
        for item in memory_items:
            review_ref = str(item["review_ref"])
            missing_contract_refs = list(item.get("missing_contract_refs") or [])
            timeline.append(
                FounderLoopEvidenceTimelineItem(
                    timeline_item_ref=_timeline_ref("memory", review_ref),
                    item_kind="memory_review_evidence_ref",
                    title=str(item["title"]),
                    safe_summary=(
                        "Memory evidence is recall metadata only. Memory is not "
                        "truth, not approval, and not context-injection authority."
                    ),
                    source_refs=[review_ref, *list(item.get("source_refs") or [])],
                    status_refs=[
                        "status-ref:founder-loop-memory-review",
                        *missing_contract_refs,
                    ],
                    related_route_refs=["GET /control-center/today/summary", "/memory"],
                    side_effect_class=str(item.get("side_effect_class", "local_dev_workspace_only")),
                    authority_posture=str(item.get("authority_boundary")),
                    approval_posture="memory_review_refs_do_not_authorize_writes",
                    receipt_refs=[],
                    audit_refs=[],
                    replay_refs=["replay-ref:founder-loop:memory-review"],
                    rollback_refs=[],
                    rollback_blockers=["memory_write_or_delete_rollback_not_scoped"],
                    redaction_status="redacted_summary_only",
                    stale_state=str(item.get("stale_state", "recheck_memory_refs_before_use")),
                    missing_evidence_posture=(
                        "memory_contract_refs_missing_until_scoped_review_contracts"
                        if missing_contract_refs
                        else "no_missing_memory_contract_refs"
                    ),
                    blocked_states=list(item.get("blocked_states") or []),
                    next_safe_action=str(item.get("next_safe_action")),
                )
            )
        for item in briefing_items:
            briefing_ref = str(item["briefing_ref"])
            timeline.append(
                FounderLoopEvidenceTimelineItem(
                    timeline_item_ref=_timeline_ref("briefing", briefing_ref),
                    item_kind="source_readiness_evidence_ref",
                    title=str(item["title"]),
                    safe_summary=(
                        "Briefing evidence is source-readiness posture only. Email, "
                        "calendar, connector, refresh, and notification runtime stay blocked."
                    ),
                    source_refs=[briefing_ref, *list(item.get("source_refs") or [])],
                    status_refs=[
                        _timeline_ref(
                            "briefing-status",
                            str(item.get("source_readiness", "blocked_missing_source_contract")),
                        )
                    ],
                    related_route_refs=[
                        "GET /control-center/morning-briefing/summary",
                        "/briefing",
                    ],
                    side_effect_class=str(item.get("side_effect_class", "local_dev_workspace_only")),
                    authority_posture=str(item.get("authority_boundary")),
                    approval_posture="source_refs_do_not_authorize_connector_runtime",
                    receipt_refs=[],
                    audit_refs=[],
                    replay_refs=["replay-ref:founder-loop:morning-briefing"],
                    rollback_refs=[],
                    rollback_blockers=["source_refresh_rollback_not_scoped"],
                    redaction_status="redacted_summary_only",
                    stale_state=str(item.get("stale_state", "recheck_source_refs_before_use")),
                    missing_evidence_posture=str(item.get("evidence_gap")),
                    blocked_states=list(item.get("blocked_states") or []),
                    next_safe_action=str(item.get("next_safe_action")),
                )
            )
        timeline.append(
            FounderLoopEvidenceTimelineItem(
                timeline_item_ref="evidence-timeline:foundation-gate/latency",
                item_kind="foundation_gate_latency_ref",
                title="Foundation Gate and latency posture",
                safe_summary=(
                    "Foundation Gate and latency refs are status evidence only; "
                    "they do not grant production authority or runtime authority."
                ),
                source_refs=["status-ref:foundation-gate-summary"],
                status_refs=["status-ref:foundation-gate-report"],
                related_route_refs=[
                    "GET /control-center/foundation-gate/summary",
                    "/foundation-gate",
                ],
                side_effect_class="validation_only",
                authority_posture=(
                    "Foundation Gate status and latency measurements are evidence, "
                    "not production authority."
                ),
                approval_posture="approval_refs_are_identifiers_only_not_authority",
                audit_refs=["audit-ref:foundation-gate:latest"],
                replay_refs=["replay-ref:foundation-gate:latest"],
                rollback_blockers=["rollback_execution_not_scoped"],
                latency_refs=[
                    "latency-ref:foundation-gate:latest-report",
                    "performance-ref:release-latency-baseline",
                ],
                foundation_gate_refs=["foundation-gate-ref:latest-report"],
                redaction_status="safe_refs_only",
                stale_state="recheck_foundation_gate_report_before_release_claim",
                missing_evidence_posture="release_evidence_packet_missing_until_scoped_release",
                blocked_states=[
                    "foundation_gate_refs_not_production_authority",
                    "latency_refs_not_authority",
                    "no_release_authority",
                ],
                next_safe_action=(
                    "Inspect Foundation Gate and latency refs; keep production "
                    "claims blocked until release evidence is scoped."
                ),
            )
        )
        return [item.model_dump(mode="json") for item in timeline]

    def actions_inbox(self, *, limit: int = 50) -> dict[str, Any]:
        items = self.list_action_inbox(limit=limit)
        return {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "status": "storage_backed_review_queue",
            "surface": "Actions",
            "storage_ref": "founder-loop-storage:local-sqlite-jsonl",
            "side_effect_class": "local_dev_workspace_only",
            "route_ref": "/control-center/actions/inbox",
            "read_only_route_refs": [
                "GET /control-center/actions/inbox",
                "GET /control-center/storage/status",
                "GET /control-center/routes",
                "GET /control-center/runtime-readiness/summary",
                "GET /control-center/foundation-gate/summary",
            ],
            "local_prerequisite_refs": [
                "status-ref:founder-loop-storage",
                "status-ref:control-center-route-manifest",
                "capability-ref:local-approval-authority",
            ],
            "items": items,
            "approval_required_before_mutation": True,
            "mutating_controls_enabled": False,
            "disabled_state_label": "Exact backend approval contract required",
            "evidence_refs": ["evidence-ref:founder-loop:action-inbox"],
            "blocked_states": [
                "no_action_execution_route",
                "no_approval_grant_capture_route",
                "no_state_change_contract_route",
                "no_connector_write_route",
                "no_runtime_model_call_route",
            ],
        }

    def morning_briefing(self, *, limit: int = 10) -> dict[str, Any]:
        items = self.list_briefing_items(limit=limit)
        return {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "status": "storage_backed_briefing_skeleton",
            "surface": "Morning Briefing",
            "storage_ref": "founder-loop-storage:local-sqlite-jsonl",
            "side_effect_class": "local_dev_workspace_only",
            "route_ref": "/control-center/morning-briefing/summary",
            "read_only_route_refs": [
                "GET /control-center/morning-briefing/summary",
                "GET /control-center/storage/status",
                "GET /control-center/routes",
                "GET /control-center/runtime-readiness/summary",
                "GET /control-center/foundation-gate/summary",
            ],
            "local_prerequisite_refs": [
                "status-ref:founder-loop-storage",
                "status-ref:control-center-route-manifest",
                "contract-ref:email-read-only-missing",
                "contract-ref:calendar-read-only-missing",
                "contract-ref:notification-delivery-missing",
            ],
            "source_readiness": "blocked_missing_email_calendar_notification_contracts",
            "authority_boundary": (
                "Read-only briefing summary; no email, calendar, connector, refresh, "
                "notification, model, memory, or delivery authority."
            ),
            "bounded_preview_only": True,
            "refresh_enabled": False,
            "notification_delivery_enabled": False,
            "missing_contract_refs": [
                "contract-ref:email-read-only-missing",
                "contract-ref:calendar-read-only-missing",
                "contract-ref:notification-delivery-missing",
            ],
            "items": items,
            "evidence_refs": ["evidence-ref:founder-loop:morning-briefing"],
            "blocked_states": [
                "no_email_read_authority",
                "no_calendar_read_authority",
                "no_connector_runtime",
                "no_account_auth",
                "no_background_refresh",
                "no_notification_delivery",
                "no_memory_write",
                "no_model_provider_call",
            ],
        }

    def list_action_inbox(self, *, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT item_ref, title, safe_summary, surface, priority, status,
                   risk_class, side_effect_class, authority_boundary,
                   approval_required, approval_envelope_ref,
                   approval_envelope_status, state_change_contract_ref,
                   state_change_readiness, blocked_state, evidence_refs_json,
                   receipt_refs_json, audit_refs_json, idempotency_key_ref,
                   expires_at, stale_state, rollback_ref, safe_disable_ref,
                   next_safe_action, created_at, updated_at
            FROM action_inbox
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        return [_row_to_payload(row) for row in rows]

    def list_plan_summaries(self, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT plan_ref, title, status, safe_summary, next_step_summary,
                   evidence_refs_json, updated_at
            FROM plan_summaries
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        return [_row_to_payload(row) for row in rows]

    def list_memory_review_queue(self, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT review_ref, title, safe_summary, candidate_kind, priority,
                   status, review_state, side_effect_class, authority_boundary,
                   provenance_refs_json, source_refs_json,
                   missing_contract_refs_json, correction_posture,
                   rejection_posture, retention_posture, delete_posture,
                   confidence_posture, stale_state, blocked_states_json,
                   next_safe_action, evidence_refs_json, created_at
            FROM memory_review_queue
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        return [_row_to_payload(row) for row in rows]

    def list_briefing_items(self, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT briefing_ref, title, safe_summary, priority, status,
                   side_effect_class, authority_boundary, source_readiness,
                   source_refs_json, missing_contract_refs_json,
                   blocked_states_json, stale_state, evidence_gap,
                   next_safe_action, evidence_refs_json, created_at
            FROM briefing_items
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (self._bounded_limit(limit),),
        )
        return [_row_to_payload(row) for row in rows]

    def upsert_action(self, record: FounderLoopActionRecord) -> None:
        self._execute(
            """
            INSERT INTO action_inbox (
                item_ref, title, safe_summary, surface, priority, status,
                risk_class, side_effect_class, authority_boundary,
                approval_required, approval_envelope_ref,
                approval_envelope_status, state_change_contract_ref,
                state_change_readiness, blocked_state, evidence_refs_json,
                receipt_refs_json, audit_refs_json, idempotency_key_ref,
                expires_at, stale_state, rollback_ref, safe_disable_ref,
                next_safe_action, created_at, updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT(item_ref) DO UPDATE SET
                title = excluded.title,
                safe_summary = excluded.safe_summary,
                surface = excluded.surface,
                priority = excluded.priority,
                status = excluded.status,
                risk_class = excluded.risk_class,
                side_effect_class = excluded.side_effect_class,
                authority_boundary = excluded.authority_boundary,
                approval_required = excluded.approval_required,
                approval_envelope_ref = excluded.approval_envelope_ref,
                approval_envelope_status = excluded.approval_envelope_status,
                state_change_contract_ref = excluded.state_change_contract_ref,
                state_change_readiness = excluded.state_change_readiness,
                blocked_state = excluded.blocked_state,
                evidence_refs_json = excluded.evidence_refs_json,
                receipt_refs_json = excluded.receipt_refs_json,
                audit_refs_json = excluded.audit_refs_json,
                idempotency_key_ref = excluded.idempotency_key_ref,
                expires_at = excluded.expires_at,
                stale_state = excluded.stale_state,
                rollback_ref = excluded.rollback_ref,
                safe_disable_ref = excluded.safe_disable_ref,
                next_safe_action = excluded.next_safe_action,
                updated_at = excluded.updated_at
            """,
            (
                record.item_ref,
                record.title,
                record.safe_summary,
                record.surface,
                record.priority,
                record.status,
                record.risk_class,
                record.side_effect_class,
                record.authority_boundary,
                int(record.approval_required),
                record.approval_envelope_ref,
                record.approval_envelope_status,
                record.state_change_contract_ref,
                record.state_change_readiness,
                record.blocked_state,
                _json_dumps(record.evidence_refs),
                _json_dumps(record.receipt_refs),
                _json_dumps(record.audit_refs),
                record.idempotency_key_ref,
                record.expires_at,
                record.stale_state,
                record.rollback_ref,
                record.safe_disable_ref,
                record.next_safe_action,
                record.created_at.isoformat(),
                record.updated_at.isoformat(),
            ),
        )

    def upsert_plan(self, record: FounderLoopPlanRecord) -> None:
        self._execute(
            """
            INSERT INTO plan_summaries (
                plan_ref, title, status, safe_summary, next_step_summary,
                evidence_refs_json, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(plan_ref) DO UPDATE SET
                title = excluded.title,
                status = excluded.status,
                safe_summary = excluded.safe_summary,
                next_step_summary = excluded.next_step_summary,
                evidence_refs_json = excluded.evidence_refs_json,
                updated_at = excluded.updated_at
            """,
            (
                record.plan_ref,
                record.title,
                record.status,
                record.safe_summary,
                record.next_step_summary,
                _json_dumps(record.evidence_refs),
                record.updated_at.isoformat(),
            ),
        )

    def upsert_memory_review(self, record: FounderLoopMemoryReviewRecord) -> None:
        self._execute(
            """
            INSERT INTO memory_review_queue (
                review_ref, title, safe_summary, candidate_kind, priority,
                status, review_state, side_effect_class, authority_boundary,
                provenance_refs_json, source_refs_json, missing_contract_refs_json,
                correction_posture, rejection_posture, retention_posture,
                delete_posture, confidence_posture, stale_state,
                blocked_states_json, next_safe_action, evidence_refs_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(review_ref) DO UPDATE SET
                title = excluded.title,
                safe_summary = excluded.safe_summary,
                candidate_kind = excluded.candidate_kind,
                priority = excluded.priority,
                status = excluded.status,
                review_state = excluded.review_state,
                side_effect_class = excluded.side_effect_class,
                authority_boundary = excluded.authority_boundary,
                provenance_refs_json = excluded.provenance_refs_json,
                source_refs_json = excluded.source_refs_json,
                missing_contract_refs_json = excluded.missing_contract_refs_json,
                correction_posture = excluded.correction_posture,
                rejection_posture = excluded.rejection_posture,
                retention_posture = excluded.retention_posture,
                delete_posture = excluded.delete_posture,
                confidence_posture = excluded.confidence_posture,
                stale_state = excluded.stale_state,
                blocked_states_json = excluded.blocked_states_json,
                next_safe_action = excluded.next_safe_action,
                evidence_refs_json = excluded.evidence_refs_json
            """,
            (
                record.review_ref,
                record.title,
                record.safe_summary,
                record.candidate_kind,
                record.priority,
                record.status,
                record.review_state,
                record.side_effect_class,
                record.authority_boundary,
                _json_dumps(record.provenance_refs),
                _json_dumps(record.source_refs),
                _json_dumps(record.missing_contract_refs),
                record.correction_posture,
                record.rejection_posture,
                record.retention_posture,
                record.delete_posture,
                record.confidence_posture,
                record.stale_state,
                _json_dumps(record.blocked_states),
                record.next_safe_action,
                _json_dumps(record.evidence_refs),
                record.created_at.isoformat(),
            ),
        )

    def upsert_briefing_item(self, record: FounderLoopBriefingRecord) -> None:
        self._execute(
            """
            INSERT INTO briefing_items (
                briefing_ref, title, safe_summary, priority, status,
                side_effect_class, authority_boundary, source_readiness,
                source_refs_json, missing_contract_refs_json, blocked_states_json,
                stale_state, evidence_gap, next_safe_action, evidence_refs_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(briefing_ref) DO UPDATE SET
                title = excluded.title,
                safe_summary = excluded.safe_summary,
                priority = excluded.priority,
                status = excluded.status,
                side_effect_class = excluded.side_effect_class,
                authority_boundary = excluded.authority_boundary,
                source_readiness = excluded.source_readiness,
                source_refs_json = excluded.source_refs_json,
                missing_contract_refs_json = excluded.missing_contract_refs_json,
                blocked_states_json = excluded.blocked_states_json,
                stale_state = excluded.stale_state,
                evidence_gap = excluded.evidence_gap,
                next_safe_action = excluded.next_safe_action,
                evidence_refs_json = excluded.evidence_refs_json
            """,
            (
                record.briefing_ref,
                record.title,
                record.safe_summary,
                record.priority,
                record.status,
                record.side_effect_class,
                record.authority_boundary,
                record.source_readiness,
                _json_dumps(record.source_refs),
                _json_dumps(record.missing_contract_refs),
                _json_dumps(record.blocked_states),
                record.stale_state,
                record.evidence_gap,
                record.next_safe_action,
                _json_dumps(record.evidence_refs),
                record.created_at.isoformat(),
            ),
        )

    def record_idempotency_key(self, *, key_ref: str, scope_ref: str, receipt_ref: str) -> None:
        _validate_safe_ref(key_ref, "key_ref")
        _validate_safe_ref(scope_ref, "scope_ref")
        _validate_safe_ref(receipt_ref, "receipt_ref")
        try:
            self._execute(
                """
                INSERT INTO idempotency_keys (key_ref, scope_ref, receipt_ref, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (key_ref, scope_ref, receipt_ref, _utc_iso()),
            )
        except sqlite3.IntegrityError as exc:
            raise FounderLoopStorageDuplicateError("FOUNDER_LOOP_IDEMPOTENCY_DUPLICATE") from exc

    def append_log(self, kind: JsonlLogKind, payload: dict[str, Any]) -> dict[str, str]:
        _validate_safe_payload(payload, f"{kind.value}_log")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        path = self.logs_dir / f"{kind.value}.jsonl"
        record = {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "kind": kind.value,
            "event_ref": payload.get("event_ref", f"founder-loop-log:{kind.value}"),
            "safe_summary": payload.get("safe_summary", "Founder Loop redacted event recorded."),
            "evidence_refs": payload.get("evidence_refs", []),
            "created_at": _utc_iso(),
        }
        _validate_safe_payload(record, f"{kind.value}_log_record")
        with path.open("a", encoding="utf-8") as handle:
            handle.write(_json_dumps(record) + "\n")
        return {
            "log_ref": f"founder-loop-log:{kind.value}",
            "event_ref": str(record["event_ref"]),
        }

    def backup_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": FOUNDER_LOOP_SCHEMA_VERSION,
            "manifest_ref": "backup-manifest:founder-loop-minimum-set",
            "required_artifact_refs": [
                "founder-loop-sqlite:local-state",
                "founder-loop-log:audit",
                "founder-loop-log:transcript",
                "founder-loop-log:realtime",
                "founder-loop-log:receipt",
            ],
            "raw_paths_included": False,
            "raw_logs_included": False,
            "safe_refs_only": True,
        }

    def _ensure_storage(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS storage_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_inbox (
                    item_ref TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    safe_summary TEXT NOT NULL,
                    surface TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    risk_class TEXT NOT NULL DEFAULT 'medium',
                    side_effect_class TEXT NOT NULL,
                    authority_boundary TEXT NOT NULL DEFAULT 'Control Center is review-only; Python Agent Core approval is required before mutation.',
                    approval_required INTEGER NOT NULL,
                    approval_envelope_ref TEXT,
                    approval_envelope_status TEXT NOT NULL DEFAULT 'missing_until_scoped_contract',
                    state_change_contract_ref TEXT,
                    state_change_readiness TEXT NOT NULL DEFAULT 'blocked_missing_backend_contract',
                    blocked_state TEXT,
                    evidence_refs_json TEXT NOT NULL,
                    receipt_refs_json TEXT NOT NULL DEFAULT '[]',
                    audit_refs_json TEXT NOT NULL DEFAULT '[]',
                    idempotency_key_ref TEXT,
                    expires_at TEXT,
                    stale_state TEXT NOT NULL DEFAULT 'recheck_required_before_mutation',
                    rollback_ref TEXT,
                    safe_disable_ref TEXT,
                    next_safe_action TEXT NOT NULL DEFAULT 'Review the safe summary and keep mutation blocked until a scoped backend contract exists.',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS plan_summaries (
                    plan_ref TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    safe_summary TEXT NOT NULL,
                    next_step_summary TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memory_review_queue (
                    review_ref TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    safe_summary TEXT NOT NULL,
                    candidate_kind TEXT NOT NULL DEFAULT 'preference',
                    priority TEXT NOT NULL DEFAULT 'medium',
                    status TEXT NOT NULL,
                    review_state TEXT NOT NULL DEFAULT 'review_needed',
                    side_effect_class TEXT NOT NULL DEFAULT 'local_dev_workspace_only',
                    authority_boundary TEXT NOT NULL DEFAULT 'Review-only memory candidate; memory writes and context injection remain unscoped.',
                    provenance_refs_json TEXT NOT NULL DEFAULT '[]',
                    source_refs_json TEXT NOT NULL DEFAULT '[]',
                    missing_contract_refs_json TEXT NOT NULL DEFAULT '[]',
                    correction_posture TEXT NOT NULL DEFAULT 'correction_requires_scoped_memory_write_contract',
                    rejection_posture TEXT NOT NULL DEFAULT 'rejection_is_review_state_only',
                    retention_posture TEXT NOT NULL DEFAULT 'retention_policy_not_bound',
                    delete_posture TEXT NOT NULL DEFAULT 'delete_execution_not_scoped',
                    confidence_posture TEXT NOT NULL DEFAULT 'safe_summary_unverified',
                    stale_state TEXT NOT NULL DEFAULT 'recheck_source_refs_before_memory_use',
                    blocked_states_json TEXT NOT NULL DEFAULT '[]',
                    next_safe_action TEXT NOT NULL DEFAULT 'Review provenance and evidence refs; keep writes blocked until a scoped memory policy milestone.',
                    evidence_refs_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS briefing_items (
                    briefing_ref TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    safe_summary TEXT NOT NULL,
                    priority TEXT NOT NULL DEFAULT 'medium',
                    status TEXT NOT NULL,
                    side_effect_class TEXT NOT NULL DEFAULT 'local_dev_workspace_only',
                    authority_boundary TEXT NOT NULL DEFAULT 'Review-only briefing summary; source reads and delivery remain unscoped.',
                    source_readiness TEXT NOT NULL DEFAULT 'blocked_missing_source_contract',
                    source_refs_json TEXT NOT NULL DEFAULT '[]',
                    missing_contract_refs_json TEXT NOT NULL DEFAULT '[]',
                    blocked_states_json TEXT NOT NULL DEFAULT '[]',
                    stale_state TEXT NOT NULL DEFAULT 'recheck_required_before_source_contract',
                    evidence_gap TEXT NOT NULL DEFAULT 'No source connector evidence is bound in this briefing slice.',
                    next_safe_action TEXT NOT NULL DEFAULT 'Define read-only source contracts before source reads or refresh.',
                    evidence_refs_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS idempotency_keys (
                    key_ref TEXT PRIMARY KEY,
                    scope_ref TEXT NOT NULL,
                    receipt_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS route_state_snapshots (
                    snapshot_ref TEXT PRIMARY KEY,
                    route_ref TEXT NOT NULL,
                    status TEXT NOT NULL,
                    side_effect_class TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evidence_refs (
                    evidence_ref TEXT PRIMARY KEY,
                    safe_summary TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                INSERT INTO storage_metadata (key, value, updated_at)
                VALUES ('schema_version', ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (FOUNDER_LOOP_SCHEMA_VERSION, _utc_iso()),
            )
            self._ensure_action_inbox_contract_columns(conn)
            self._ensure_memory_review_contract_columns(conn)
            self._ensure_briefing_contract_columns(conn)
        if self.seed_defaults:
            self._seed_defaults_if_empty()
            self._backfill_seed_action_contract_metadata()
            self._backfill_seed_memory_review_contract_metadata()
            self._backfill_seed_briefing_contract_metadata()

    def _ensure_action_inbox_contract_columns(self, conn: sqlite3.Connection) -> None:
        existing = {
            str(row["name"])
            for row in conn.execute("PRAGMA table_info(action_inbox)").fetchall()
        }
        additions = {
            "risk_class": "TEXT NOT NULL DEFAULT 'medium'",
            "authority_boundary": (
                "TEXT NOT NULL DEFAULT 'Control Center is review-only; Python Agent Core "
                "approval is required before mutation.'"
            ),
            "approval_envelope_ref": "TEXT",
            "approval_envelope_status": "TEXT NOT NULL DEFAULT 'missing_until_scoped_contract'",
            "state_change_contract_ref": "TEXT",
            "state_change_readiness": "TEXT NOT NULL DEFAULT 'blocked_missing_backend_contract'",
            "receipt_refs_json": "TEXT NOT NULL DEFAULT '[]'",
            "audit_refs_json": "TEXT NOT NULL DEFAULT '[]'",
            "idempotency_key_ref": "TEXT",
            "expires_at": "TEXT",
            "stale_state": "TEXT NOT NULL DEFAULT 'recheck_required_before_mutation'",
            "rollback_ref": "TEXT",
            "safe_disable_ref": "TEXT",
            "next_safe_action": (
                "TEXT NOT NULL DEFAULT 'Review the safe summary and keep mutation blocked "
                "until a scoped backend contract exists.'"
            ),
        }
        for column_name, column_spec in additions.items():
            if column_name not in existing:
                conn.execute(f"ALTER TABLE action_inbox ADD COLUMN {column_name} {column_spec}")

    def _ensure_memory_review_contract_columns(self, conn: sqlite3.Connection) -> None:
        existing = {
            str(row["name"])
            for row in conn.execute("PRAGMA table_info(memory_review_queue)").fetchall()
        }
        additions = {
            "candidate_kind": "TEXT NOT NULL DEFAULT 'preference'",
            "priority": "TEXT NOT NULL DEFAULT 'medium'",
            "review_state": "TEXT NOT NULL DEFAULT 'review_needed'",
            "side_effect_class": "TEXT NOT NULL DEFAULT 'local_dev_workspace_only'",
            "authority_boundary": (
                "TEXT NOT NULL DEFAULT 'Review-only memory candidate; memory writes "
                "and context injection remain unscoped.'"
            ),
            "provenance_refs_json": "TEXT NOT NULL DEFAULT '[]'",
            "source_refs_json": "TEXT NOT NULL DEFAULT '[]'",
            "missing_contract_refs_json": "TEXT NOT NULL DEFAULT '[]'",
            "correction_posture": (
                "TEXT NOT NULL DEFAULT 'correction_requires_scoped_memory_write_contract'"
            ),
            "rejection_posture": "TEXT NOT NULL DEFAULT 'rejection_is_review_state_only'",
            "retention_posture": "TEXT NOT NULL DEFAULT 'retention_policy_not_bound'",
            "delete_posture": "TEXT NOT NULL DEFAULT 'delete_execution_not_scoped'",
            "confidence_posture": "TEXT NOT NULL DEFAULT 'safe_summary_unverified'",
            "stale_state": "TEXT NOT NULL DEFAULT 'recheck_source_refs_before_memory_use'",
            "blocked_states_json": "TEXT NOT NULL DEFAULT '[]'",
            "next_safe_action": (
                "TEXT NOT NULL DEFAULT 'Review provenance and evidence refs; keep "
                "writes blocked until a scoped memory policy milestone.'"
            ),
        }
        for column_name, column_spec in additions.items():
            if column_name not in existing:
                conn.execute(
                    f"ALTER TABLE memory_review_queue ADD COLUMN {column_name} {column_spec}"
                )

    def _ensure_briefing_contract_columns(self, conn: sqlite3.Connection) -> None:
        existing = {
            str(row["name"])
            for row in conn.execute("PRAGMA table_info(briefing_items)").fetchall()
        }
        additions = {
            "priority": "TEXT NOT NULL DEFAULT 'medium'",
            "side_effect_class": "TEXT NOT NULL DEFAULT 'local_dev_workspace_only'",
            "authority_boundary": (
                "TEXT NOT NULL DEFAULT 'Review-only briefing summary; source reads and "
                "delivery remain unscoped.'"
            ),
            "source_readiness": "TEXT NOT NULL DEFAULT 'blocked_missing_source_contract'",
            "source_refs_json": "TEXT NOT NULL DEFAULT '[]'",
            "missing_contract_refs_json": "TEXT NOT NULL DEFAULT '[]'",
            "blocked_states_json": "TEXT NOT NULL DEFAULT '[]'",
            "stale_state": "TEXT NOT NULL DEFAULT 'recheck_required_before_source_contract'",
            "evidence_gap": (
                "TEXT NOT NULL DEFAULT 'No source connector evidence is bound in this "
                "briefing slice.'"
            ),
            "next_safe_action": (
                "TEXT NOT NULL DEFAULT 'Define read-only source contracts before source "
                "reads or refresh.'"
            ),
        }
        for column_name, column_spec in additions.items():
            if column_name not in existing:
                conn.execute(f"ALTER TABLE briefing_items ADD COLUMN {column_name} {column_spec}")

    def _seed_defaults_if_empty(self) -> None:
        if self._count("action_inbox") == 0:
            self.upsert_action(
                FounderLoopActionRecord(
                    item_ref="founder-action:setup-assistant-hardening",
                    title="Setup Assistant hardening review",
                    safe_summary=(
                        "Dry-run setup envelopes are available for review only; installer and "
                        "background-service authority remain blocked."
                    ),
                    surface="Actions",
                    priority="high",
                    risk_class="high",
                    status="review_ready",
                    side_effect_class="validation_only",
                    authority_boundary=(
                        "Review-only display; Python Agent Core and LocalApprovalAuthority must "
                        "validate exact scope before mutation."
                    ),
                    approval_required=True,
                    approval_envelope_ref="approval-envelope:founder-loop:setup-assistant-hardening",
                    approval_envelope_status="dry_run_ref_available",
                    state_change_contract_ref="contract-ref:founder-loop:setup-assistant-hardening",
                    state_change_readiness="blocked_pending_scoped_mutation_contract",
                    blocked_state="Mutation requires exact approval, idempotency, rollback, and receipt refs.",
                    evidence_refs=["evidence-ref:founder-loop:setup-assistant"],
                    receipt_refs=["receipt-plan:founder-loop:setup-assistant-hardening"],
                    audit_refs=["audit-plan:founder-loop:setup-assistant-hardening"],
                    idempotency_key_ref="idempotency-ref:founder-loop:setup-assistant-hardening",
                    expires_at="review_required_before_mutation",
                    stale_state="recheck_setup_summary_before_mutation",
                    rollback_ref="rollback-plan:founder-loop:setup-assistant-hardening",
                    safe_disable_ref="safe-disable:founder-loop:setup-assistant-hardening",
                    next_safe_action=(
                        "Review refs only; request a scoped state-change milestone before mutation."
                    ),
                )
            )
            self.upsert_action(
                FounderLoopActionRecord(
                    item_ref="founder-action:morning-briefing-skeleton",
                    title="Morning Briefing skeleton review",
                    safe_summary=(
                        "Briefing items are storage-backed summaries only; email and calendar reads "
                        "remain future contracts."
                    ),
                    surface="Today",
                    priority="medium",
                    risk_class="medium",
                    status="review_ready",
                    side_effect_class="local_dev_workspace_only",
                    authority_boundary=(
                        "Review-only display; source reads and delivery remain unscoped."
                    ),
                    approval_required=False,
                    approval_envelope_status="not_required_for_inspection",
                    state_change_readiness="blocked_no_source_read_contract",
                    blocked_state="Connector reads and notification delivery are not scoped.",
                    evidence_refs=["evidence-ref:founder-loop:briefing"],
                    audit_refs=["audit-plan:founder-loop:briefing-review"],
                    expires_at="review_required_before_source_contract",
                    stale_state="recheck_source_status_before_contract",
                    safe_disable_ref="safe-disable:founder-loop:briefing-surface",
                    next_safe_action="Define read-only briefing source refs before source reads.",
                )
            )
        if self._count("plan_summaries") == 0:
            self.upsert_plan(
                FounderLoopPlanRecord(
                    plan_ref="plan-summary:founder-loop-v1",
                    title="Founder Loop v1 product spine",
                    safe_summary=(
                        "Today, Actions, Plans, Memory, Evidence, and Settings are the active "
                        "single-user operator loop."
                    ),
                    next_step_summary=(
                        "Keep the loop storage-backed and review-gated before adding broader "
                        "runtime surfaces."
                    ),
                    evidence_refs=["evidence-ref:founder-loop:product-spine"],
                )
            )
        if self._count("memory_review_queue") == 0:
            self.upsert_memory_review(
                FounderLoopMemoryReviewRecord(
                    review_ref="memory-review:founder-loop-preferences",
                    title="Founder Loop memory review",
                    safe_summary=(
                        "Memory remains a review queue with safe summaries; recall is not treated "
                        "as truth or execution authority."
                    ),
                    candidate_kind="operator_preference",
                    priority="high",
                    status="review_needed",
                    review_state="review_needed",
                    authority_boundary=(
                        "Review-only memory candidate; recall is not truth, and writes, "
                        "deletes, and context injection remain unscoped."
                    ),
                    provenance_refs=["provenance-ref:founder-loop-memory:preferences"],
                    source_refs=["source-ref:founder-loop-storage"],
                    missing_contract_refs=[
                        "contract-ref:memory-write-policy-binding-missing",
                        "contract-ref:memory-retention-delete-missing",
                        "contract-ref:memory-review-decision-capture-missing",
                        "contract-ref:context-injection-missing",
                    ],
                    correction_posture="correction_requires_scoped_memory_write_contract",
                    rejection_posture="rejection_is_review_state_only_until_capture_contract",
                    retention_posture="retention_policy_not_bound",
                    delete_posture="delete_execution_not_scoped",
                    confidence_posture="safe_summary_unverified",
                    stale_state="recheck_source_refs_before_memory_use",
                    blocked_states=[
                        "no_memory_write",
                        "no_context_injection",
                        "no_memory_delete",
                        "no_raw_source_display",
                        "no_connector_write",
                        "no_model_provider_authority",
                        "no_background_sync",
                    ],
                    next_safe_action=(
                        "Review provenance and evidence refs; keep writes blocked until a "
                        "scoped memory policy milestone."
                    ),
                    evidence_refs=["evidence-ref:founder-loop:memory"],
                )
            )
        if self._count("briefing_items") == 0:
            self.upsert_briefing_item(
                FounderLoopBriefingRecord(
                    briefing_ref="briefing:api-boundary-modularization",
                    title="API boundary modularization",
                    safe_summary=(
                        "New Founder Loop summaries use router and repository seams while the "
                        "legacy FastAPI module remains a compatibility boundary."
                    ),
                    priority="high",
                    status="active",
                    source_readiness="local_status_refs_only",
                    source_refs=["source-ref:control-center-route-status"],
                    missing_contract_refs=[
                        "contract-ref:email-read-only-missing",
                        "contract-ref:calendar-read-only-missing",
                        "contract-ref:notification-delivery-missing",
                    ],
                    blocked_states=[
                        "no_email_calendar_source_contract",
                        "no_background_refresh",
                    ],
                    stale_state="recheck_route_status_before_briefing_use",
                    evidence_gap="No email, calendar, or notification source evidence is bound.",
                    next_safe_action=(
                        "Use route and storage refs only; define source contracts before refresh."
                    ),
                    evidence_refs=["evidence-ref:founder-loop:api-boundary"],
                )
            )
            self.upsert_briefing_item(
                FounderLoopBriefingRecord(
                    briefing_ref="briefing:storage-state-first-loop",
                    title="Storage-backed first loop",
                    safe_summary=(
                        "SQLite stores indexed loop state and JSONL logs are reserved for "
                        "redacted append-only receipts, audits, transcripts, and realtime events."
                    ),
                    priority="medium",
                    status="active",
                    source_readiness="local_storage_refs_only",
                    source_refs=["source-ref:founder-loop-storage"],
                    missing_contract_refs=[
                        "contract-ref:email-read-only-missing",
                        "contract-ref:calendar-read-only-missing",
                        "contract-ref:notification-delivery-missing",
                    ],
                    blocked_states=[
                        "no_connector_runtime",
                        "no_notification_delivery",
                    ],
                    stale_state="recheck_storage_status_before_briefing_use",
                    evidence_gap="No connector receipts or source refresh receipts are bound.",
                    next_safe_action=(
                        "Inspect storage status only; keep source reads blocked until scoped."
                    ),
                    evidence_refs=["evidence-ref:founder-loop:storage"],
                )
            )
        if self._count("evidence_refs") == 0:
            self._execute(
                """
                INSERT INTO evidence_refs (evidence_ref, safe_summary, created_at)
                VALUES (?, ?, ?)
                """,
                (
                    "evidence-ref:founder-loop:seed",
                    "Initial storage-backed Founder Loop safe refs.",
                    _utc_iso(),
                ),
            )

    def _backfill_seed_action_contract_metadata(self) -> None:
        self._update_action_contract_metadata(
            "founder-action:setup-assistant-hardening",
            {
                "risk_class": "high",
                "authority_boundary": (
                    "Review-only display; Python Agent Core and LocalApprovalAuthority must "
                    "validate exact scope before mutation."
                ),
                "approval_envelope_ref": "approval-envelope:founder-loop:setup-assistant-hardening",
                "approval_envelope_status": "dry_run_ref_available",
                "state_change_contract_ref": "contract-ref:founder-loop:setup-assistant-hardening",
                "state_change_readiness": "blocked_pending_scoped_mutation_contract",
                "receipt_refs": ["receipt-plan:founder-loop:setup-assistant-hardening"],
                "audit_refs": ["audit-plan:founder-loop:setup-assistant-hardening"],
                "idempotency_key_ref": "idempotency-ref:founder-loop:setup-assistant-hardening",
                "expires_at": "review_required_before_mutation",
                "stale_state": "recheck_setup_summary_before_mutation",
                "rollback_ref": "rollback-plan:founder-loop:setup-assistant-hardening",
                "safe_disable_ref": "safe-disable:founder-loop:setup-assistant-hardening",
                "next_safe_action": (
                    "Review refs only; request a scoped state-change milestone before mutation."
                ),
            },
        )
        self._update_action_contract_metadata(
            "founder-action:morning-briefing-skeleton",
            {
                "risk_class": "medium",
                "authority_boundary": (
                    "Review-only display; source reads and delivery remain unscoped."
                ),
                "approval_envelope_status": "not_required_for_inspection",
                "state_change_readiness": "blocked_no_source_read_contract",
                "audit_refs": ["audit-plan:founder-loop:briefing-review"],
                "expires_at": "review_required_before_source_contract",
                "stale_state": "recheck_source_status_before_contract",
                "safe_disable_ref": "safe-disable:founder-loop:briefing-surface",
                "next_safe_action": "Define read-only briefing source refs before source reads.",
            },
        )

    def _update_action_contract_metadata(self, item_ref: str, metadata: dict[str, Any]) -> None:
        _validate_safe_ref(item_ref, "item_ref")
        _validate_safe_payload(metadata, "action_contract_metadata")
        self._execute(
            """
            UPDATE action_inbox
            SET risk_class = COALESCE(?, risk_class),
                authority_boundary = COALESCE(?, authority_boundary),
                approval_envelope_ref = ?,
                approval_envelope_status = COALESCE(?, approval_envelope_status),
                state_change_contract_ref = ?,
                state_change_readiness = COALESCE(?, state_change_readiness),
                receipt_refs_json = COALESCE(?, receipt_refs_json),
                audit_refs_json = COALESCE(?, audit_refs_json),
                idempotency_key_ref = ?,
                expires_at = ?,
                stale_state = COALESCE(?, stale_state),
                rollback_ref = ?,
                safe_disable_ref = ?,
                next_safe_action = COALESCE(?, next_safe_action),
                updated_at = ?
            WHERE item_ref = ?
            """,
            (
                metadata.get("risk_class"),
                metadata.get("authority_boundary"),
                metadata.get("approval_envelope_ref"),
                metadata.get("approval_envelope_status"),
                metadata.get("state_change_contract_ref"),
                metadata.get("state_change_readiness"),
                _json_dumps(metadata["receipt_refs"]) if "receipt_refs" in metadata else None,
                _json_dumps(metadata["audit_refs"]) if "audit_refs" in metadata else None,
                metadata.get("idempotency_key_ref"),
                metadata.get("expires_at"),
                metadata.get("stale_state"),
                metadata.get("rollback_ref"),
                metadata.get("safe_disable_ref"),
                metadata.get("next_safe_action"),
                _utc_iso(),
                item_ref,
            ),
        )

    def _backfill_seed_memory_review_contract_metadata(self) -> None:
        self._update_memory_review_contract_metadata(
            "memory-review:founder-loop-preferences",
            {
                "candidate_kind": "operator_preference",
                "priority": "high",
                "review_state": "review_needed",
                "side_effect_class": "local_dev_workspace_only",
                "authority_boundary": (
                    "Review-only memory candidate; recall is not truth, and writes, "
                    "deletes, and context injection remain unscoped."
                ),
                "provenance_refs": ["provenance-ref:founder-loop-memory:preferences"],
                "source_refs": ["source-ref:founder-loop-storage"],
                "missing_contract_refs": [
                    "contract-ref:memory-write-policy-binding-missing",
                    "contract-ref:memory-retention-delete-missing",
                    "contract-ref:memory-review-decision-capture-missing",
                    "contract-ref:context-injection-missing",
                ],
                "correction_posture": "correction_requires_scoped_memory_write_contract",
                "rejection_posture": "rejection_is_review_state_only_until_capture_contract",
                "retention_posture": "retention_policy_not_bound",
                "delete_posture": "delete_execution_not_scoped",
                "confidence_posture": "safe_summary_unverified",
                "stale_state": "recheck_source_refs_before_memory_use",
                "blocked_states": [
                    "no_memory_write",
                    "no_context_injection",
                    "no_memory_delete",
                    "no_raw_source_display",
                    "no_connector_write",
                    "no_model_provider_authority",
                    "no_background_sync",
                ],
                "next_safe_action": (
                    "Review provenance and evidence refs; keep writes blocked until a "
                    "scoped memory policy milestone."
                ),
            },
        )

    def _update_memory_review_contract_metadata(
        self,
        review_ref: str,
        metadata: dict[str, Any],
    ) -> None:
        _validate_safe_ref(review_ref, "review_ref")
        _validate_safe_payload(metadata, "memory_review_contract_metadata")
        self._execute(
            """
            UPDATE memory_review_queue
            SET candidate_kind = COALESCE(?, candidate_kind),
                priority = COALESCE(?, priority),
                review_state = COALESCE(?, review_state),
                side_effect_class = COALESCE(?, side_effect_class),
                authority_boundary = COALESCE(?, authority_boundary),
                provenance_refs_json = COALESCE(?, provenance_refs_json),
                source_refs_json = COALESCE(?, source_refs_json),
                missing_contract_refs_json = COALESCE(?, missing_contract_refs_json),
                correction_posture = COALESCE(?, correction_posture),
                rejection_posture = COALESCE(?, rejection_posture),
                retention_posture = COALESCE(?, retention_posture),
                delete_posture = COALESCE(?, delete_posture),
                confidence_posture = COALESCE(?, confidence_posture),
                stale_state = COALESCE(?, stale_state),
                blocked_states_json = COALESCE(?, blocked_states_json),
                next_safe_action = COALESCE(?, next_safe_action)
            WHERE review_ref = ?
            """,
            (
                metadata.get("candidate_kind"),
                metadata.get("priority"),
                metadata.get("review_state"),
                metadata.get("side_effect_class"),
                metadata.get("authority_boundary"),
                (
                    _json_dumps(metadata["provenance_refs"])
                    if "provenance_refs" in metadata
                    else None
                ),
                _json_dumps(metadata["source_refs"]) if "source_refs" in metadata else None,
                (
                    _json_dumps(metadata["missing_contract_refs"])
                    if "missing_contract_refs" in metadata
                    else None
                ),
                metadata.get("correction_posture"),
                metadata.get("rejection_posture"),
                metadata.get("retention_posture"),
                metadata.get("delete_posture"),
                metadata.get("confidence_posture"),
                metadata.get("stale_state"),
                _json_dumps(metadata["blocked_states"]) if "blocked_states" in metadata else None,
                metadata.get("next_safe_action"),
                review_ref,
            ),
        )

    def _backfill_seed_briefing_contract_metadata(self) -> None:
        common_missing_contract_refs = [
            "contract-ref:email-read-only-missing",
            "contract-ref:calendar-read-only-missing",
            "contract-ref:notification-delivery-missing",
        ]
        self._update_briefing_contract_metadata(
            "briefing:api-boundary-modularization",
            {
                "priority": "high",
                "side_effect_class": "local_dev_workspace_only",
                "authority_boundary": (
                    "Review-only briefing summary; source reads and delivery remain unscoped."
                ),
                "source_readiness": "local_status_refs_only",
                "source_refs": ["source-ref:control-center-route-status"],
                "missing_contract_refs": common_missing_contract_refs,
                "blocked_states": [
                    "no_email_calendar_source_contract",
                    "no_background_refresh",
                ],
                "stale_state": "recheck_route_status_before_briefing_use",
                "evidence_gap": "No email, calendar, or notification source evidence is bound.",
                "next_safe_action": (
                    "Use route and storage refs only; define source contracts before refresh."
                ),
            },
        )
        self._update_briefing_contract_metadata(
            "briefing:storage-state-first-loop",
            {
                "priority": "medium",
                "side_effect_class": "local_dev_workspace_only",
                "authority_boundary": (
                    "Review-only briefing summary; source reads and delivery remain unscoped."
                ),
                "source_readiness": "local_storage_refs_only",
                "source_refs": ["source-ref:founder-loop-storage"],
                "missing_contract_refs": common_missing_contract_refs,
                "blocked_states": [
                    "no_connector_runtime",
                    "no_notification_delivery",
                ],
                "stale_state": "recheck_storage_status_before_briefing_use",
                "evidence_gap": "No connector receipts or source refresh receipts are bound.",
                "next_safe_action": (
                    "Inspect storage status only; keep source reads blocked until scoped."
                ),
            },
        )

    def _update_briefing_contract_metadata(
        self,
        briefing_ref: str,
        metadata: dict[str, Any],
    ) -> None:
        _validate_safe_ref(briefing_ref, "briefing_ref")
        _validate_safe_payload(metadata, "briefing_contract_metadata")
        self._execute(
            """
            UPDATE briefing_items
            SET priority = COALESCE(?, priority),
                side_effect_class = COALESCE(?, side_effect_class),
                authority_boundary = COALESCE(?, authority_boundary),
                source_readiness = COALESCE(?, source_readiness),
                source_refs_json = COALESCE(?, source_refs_json),
                missing_contract_refs_json = COALESCE(?, missing_contract_refs_json),
                blocked_states_json = COALESCE(?, blocked_states_json),
                stale_state = COALESCE(?, stale_state),
                evidence_gap = COALESCE(?, evidence_gap),
                next_safe_action = COALESCE(?, next_safe_action)
            WHERE briefing_ref = ?
            """,
            (
                metadata.get("priority"),
                metadata.get("side_effect_class"),
                metadata.get("authority_boundary"),
                metadata.get("source_readiness"),
                _json_dumps(metadata["source_refs"]) if "source_refs" in metadata else None,
                (
                    _json_dumps(metadata["missing_contract_refs"])
                    if "missing_contract_refs" in metadata
                    else None
                ),
                _json_dumps(metadata["blocked_states"]) if "blocked_states" in metadata else None,
                metadata.get("stale_state"),
                metadata.get("evidence_gap"),
                metadata.get("next_safe_action"),
                briefing_ref,
            ),
        )

    def _schema_version(self) -> str:
        rows = self._fetch_all(
            "SELECT value FROM storage_metadata WHERE key = 'schema_version' LIMIT 1",
            (),
        )
        return str(rows[0]["value"]) if rows else FOUNDER_LOOP_SCHEMA_VERSION

    def _count(self, table: str) -> int:
        allowed = {
            "action_inbox",
            "briefing_items",
            "plan_summaries",
            "memory_review_queue",
            "idempotency_keys",
            "route_state_snapshots",
            "evidence_refs",
        }
        if table not in allowed:
            raise FounderLoopStorageError("FOUNDER_LOOP_TABLE_REF_DENIED")
        rows = self._fetch_all(f"SELECT COUNT(*) AS count FROM {table}", ())
        return int(rows[0]["count"])

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _execute(self, sql: str, params: tuple[Any, ...]) -> None:
        with self._connect() as conn:
            conn.execute(sql, params)

    def _fetch_all(self, sql: str, params: tuple[Any, ...]) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return list(conn.execute(sql, params).fetchall())

    @staticmethod
    def _bounded_limit(limit: int) -> int:
        return max(1, min(int(limit), 100))
