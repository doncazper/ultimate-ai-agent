from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


MORNING_BRIEFING_V1_CONTRACT_REF = (
    "contract-ref:product-loop-007-morning-briefing-v1:v1"
)
MORNING_BRIEFING_V1_READ_MODEL_SOURCE = (
    "python_core_morning_briefing_v1_read_model"
)
MORNING_BRIEFING_V1_REQUIRED_BLOCKED_REFS: tuple[str, ...] = (
    "blocked-state:morning-briefing-no-email-calendar-fetch",
    "blocked-state:morning-briefing-no-account-auth",
    "blocked-state:morning-briefing-no-live-web",
    "blocked-state:morning-briefing-no-connector-runtime",
    "blocked-state:morning-briefing-no-connector-write",
    "blocked-state:morning-briefing-no-model-provider-call",
    "blocked-state:morning-briefing-no-automatic-recommendations",
    "blocked-state:morning-briefing-no-hidden-memory-write",
    "blocked-state:morning-briefing-no-action-execution",
    "blocked-state:morning-briefing-no-context-injection",
    "blocked-state:morning-briefing-no-repo-write",
    "blocked-state:morning-briefing-no-workbench-apply",
    "blocked-state:morning-briefing-no-shell-subprocess",
    "blocked-state:morning-briefing-no-browser-execution",
    "blocked-state:morning-briefing-no-production-authority",
)

_SAFE_REF_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9:_./@#=-]{0,239}$")
_SAFE_SUFFIX_RE = re.compile(r"[^a-z0-9_.@-]+")
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
    "connector_read_enabled",
    "connector_runtime_enabled",
    "connector_write_enabled",
    "email_calendar_fetch_enabled",
    "account_auth_enabled",
    "live_web_enabled",
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "automatic_recommendations_enabled",
    "hidden_memory_write_authorized",
    "memory_write_authorized",
    "context_injection_authorized",
    "action_execution_enabled",
    "repo_write_enabled",
    "workbench_apply_enabled",
    "shell_subprocess_execution_enabled",
    "browser_execution_enabled",
    "notification_delivery_enabled",
    "source_refresh_enabled",
    "production_authority_enabled",
)


class MorningBriefingV1ReadModel(BaseModel):
    schema_version: str = "product-loop-007-morning-briefing.v1"
    contract_ref: str = MORNING_BRIEFING_V1_CONTRACT_REF
    status: str = "implemented_backend_owned_local_briefing_v1"
    source: str = MORNING_BRIEFING_V1_READ_MODEL_SOURCE
    backend_owned: bool = True
    local_read_model_only: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    bounded_preview_only: bool = True
    source_readiness_required: bool = True
    missing_sources_visible: bool = True
    item_count: int = Field(default=0, ge=0)
    section_count: int = Field(default=0, ge=0)
    open_action_count: int = Field(default=0, ge=0)
    follow_up_count: int = Field(default=0, ge=0)
    memory_review_count: int = Field(default=0, ge=0)
    source_blocker_count: int = Field(default=0, ge=0)
    safe_summary: str = (
        "Morning Briefing V1 is built from local safe refs for Today, open "
        "actions, follow-ups, memory review, evidence, storage/workbench status, "
        "and source-readiness blockers."
    )
    today_summary_ref: str = Field(default="daily-loop-summary:morning-briefing")
    source_readiness_posture_ref: str = Field(
        default="source-readiness-posture:morning-briefing-v1"
    )
    repo_status_refs: list[str] = Field(default_factory=list, min_length=1)
    workbench_status_refs: list[str] = Field(default_factory=list, min_length=1)
    source_readiness_refs: list[str] = Field(default_factory=list)
    missing_source_refs: list[str] = Field(default_factory=list)
    open_action_refs: list[str] = Field(default_factory=list)
    follow_up_refs: list[str] = Field(default_factory=list)
    memory_review_refs: list[str] = Field(default_factory=list)
    evidence_timeline_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    blocked_state_refs: list[str] = Field(default_factory=list, min_length=1)
    next_safe_action: str = (
        "Review local safe refs and missing-source blockers before using the "
        "briefing as a daily review input."
    )
    authority_boundary: str = (
        "Morning Briefing V1 is a backend-owned local read model. It does not "
        "fetch email/calendar/account data, call models/providers, read live web, "
        "run connectors, write memory, inject context, execute actions, deliver "
        "notifications, write repo state, apply workbench changes, run shell or "
        "browser execution, or grant production authority."
    )
    connector_read_enabled: bool = False
    connector_runtime_enabled: bool = False
    connector_write_enabled: bool = False
    email_calendar_fetch_enabled: bool = False
    account_auth_enabled: bool = False
    live_web_enabled: bool = False
    provider_model_call_enabled: bool = False
    runtime_model_call_enabled: bool = False
    automatic_recommendations_enabled: bool = False
    hidden_memory_write_authorized: bool = False
    memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    action_execution_enabled: bool = False
    repo_write_enabled: bool = False
    workbench_apply_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_execution_enabled: bool = False
    notification_delivery_enabled: bool = False
    source_refresh_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "MorningBriefingV1ReadModel":
        for field_name in (
            "contract_ref",
            "today_summary_ref",
            "source_readiness_posture_ref",
        ):
            _validate_safe_ref(str(getattr(self, field_name)), field_name)
        for field_name in (
            "status",
            "source",
            "safe_summary",
            "next_safe_action",
            "authority_boundary",
        ):
            _validate_safe_text(str(getattr(self, field_name)), field_name)
        if self.source != MORNING_BRIEFING_V1_READ_MODEL_SOURCE:
            raise ValueError("unexpected Morning Briefing V1 read-model source")
        if self.schema_version != "product-loop-007-morning-briefing.v1":
            raise ValueError("unexpected Morning Briefing V1 schema version")
        if self.contract_ref != MORNING_BRIEFING_V1_CONTRACT_REF:
            raise ValueError("unexpected Morning Briefing V1 contract ref")
        for field_name in (
            "backend_owned",
            "local_read_model_only",
            "safe_refs_only",
            "bounded_preview_only",
            "source_readiness_required",
            "missing_sources_visible",
        ):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must remain true")
        if self.raw_content_included:
            raise ValueError("Morning Briefing V1 must not include raw content")
        for field_name in (
            "repo_status_refs",
            "workbench_status_refs",
            "source_readiness_refs",
            "missing_source_refs",
            "open_action_refs",
            "follow_up_refs",
            "memory_review_refs",
            "evidence_timeline_refs",
            "evidence_refs",
            "blocked_state_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        if set(MORNING_BRIEFING_V1_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        ):
            raise ValueError("Morning Briefing V1 missing required blocked refs")
        _validate_denied_flags(self)
        return self


def build_morning_briefing_v1_read_model(
    *,
    briefing: dict[str, Any],
    actions: list[dict[str, Any]],
    memory_items: list[dict[str, Any]],
    evidence_timeline: list[dict[str, Any]],
    storage_status: dict[str, Any],
    memory_workbench: dict[str, Any],
) -> dict[str, Any]:
    source_items = _safe_records(briefing.get("source_readiness_items"))
    sections = _safe_records(briefing.get("daily_loop_sections"))
    followups = _safe_records(briefing.get("crm_lite_followups"))
    source_posture = (
        briefing.get("source_readiness_posture")
        if isinstance(briefing.get("source_readiness_posture"), dict)
        else {}
    )
    workbench_health = (
        memory_workbench.get("health")
        if isinstance(memory_workbench.get("health"), dict)
        else {}
    )
    jsonl_log_refs = (
        list(storage_status.get("jsonl_log_refs", {}).values())
        if isinstance(storage_status.get("jsonl_log_refs"), dict)
        else []
    )
    section_blocked_refs = [
        ref
        for section in sections
        for ref in section.get("blocked_state_refs", [])
    ]
    briefing_items = _safe_records(briefing.get("items"))
    briefing_item_evidence_refs = [
        ref
        for item in briefing_items
        for ref in item.get("evidence_refs", [])
    ]
    section_evidence_refs = [
        ref
        for section in sections
        for ref in section.get("evidence_refs", [])
    ]
    blocked_refs = _dedupe(
        [
            *MORNING_BRIEFING_V1_REQUIRED_BLOCKED_REFS,
            *(briefing.get("blocked_states") or []),
            *(source_posture.get("blocked_state_refs") or []),
            *(memory_workbench.get("blocked_state_refs") or []),
            *section_blocked_refs,
        ]
    )
    repo_status_refs = _safe_refs(
        [
            storage_status.get("storage_ref"),
            storage_status.get("sqlite_state_ref"),
            storage_status.get("backup_manifest_ref"),
            *jsonl_log_refs,
        ]
    ) or ["storage-ref:founder-loop:missing"]
    workbench_status_refs = _safe_refs(
        [
            memory_workbench.get("contract_ref"),
            _status_ref("memory-workbench", memory_workbench.get("status")),
            *(workbench_health.get("needs_attention_refs") or []),
        ]
    ) or ["workbench-ref:memory:missing"]
    open_action_refs = _safe_refs(action.get("item_ref") for action in actions)
    follow_up_refs = _safe_refs(followup.get("follow_up_ref") for followup in followups)
    memory_review_refs = _safe_refs(item.get("review_ref") for item in memory_items)
    evidence_timeline_refs = _safe_refs(
        item.get("timeline_item_ref") for item in evidence_timeline
    )
    evidence_refs = _dedupe(
        [
            *(briefing.get("evidence_refs") or []),
            *briefing_item_evidence_refs,
            *section_evidence_refs,
        ]
    ) or ["evidence-ref:founder-loop:morning-briefing-v1"]
    missing_source_refs = _safe_refs(
        ref
        for item in source_items
        if item.get("status") in {"blocked", "missing", "unavailable", "not_configured"}
        for ref in [
            *(item.get("missing_contract_refs") or []),
            *(item.get("source_refs") or []),
        ]
    )
    source_blocker_count = len(source_posture.get("blocked_state_refs") or [])
    read_model = MorningBriefingV1ReadModel(
        item_count=len(briefing_items),
        section_count=len(sections),
        open_action_count=len(open_action_refs),
        follow_up_count=len(follow_up_refs),
        memory_review_count=len(memory_review_refs),
        source_blocker_count=source_blocker_count,
        today_summary_ref=_safe_ref_or_default(
            (briefing.get("daily_loop_summary") or {}).get("loop_ref")
            if isinstance(briefing.get("daily_loop_summary"), dict)
            else None,
            "daily-loop-summary:morning-briefing",
        ),
        source_readiness_posture_ref=_source_readiness_posture_ref(source_posture),
        repo_status_refs=repo_status_refs,
        workbench_status_refs=workbench_status_refs,
        source_readiness_refs=_safe_refs(item.get("source_ref") for item in source_items),
        missing_source_refs=missing_source_refs,
        open_action_refs=open_action_refs,
        follow_up_refs=follow_up_refs,
        memory_review_refs=memory_review_refs,
        evidence_timeline_refs=evidence_timeline_refs,
        evidence_refs=evidence_refs,
        blocked_state_refs=blocked_refs,
    )
    return read_model.model_dump(mode="json")


def _source_readiness_posture_ref(source_posture: dict[str, Any]) -> str:
    counts = [
        str(source_posture.get("blocked_source_count", 0)),
        str(source_posture.get("metadata_only_source_count", 0)),
        str(source_posture.get("not_configured_source_count", 0)),
    ]
    return "source-readiness-posture:morning-briefing-v1:" + "-".join(counts)


def _status_ref(prefix: str, value: object) -> str:
    suffix = _safe_suffix(str(value or "unknown"))
    return f"status-ref:{prefix}:{suffix}"


def _validate_denied_flags(model: BaseModel) -> None:
    enabled = [field for field in _DENIED_FLAGS if bool(getattr(model, field))]
    if enabled:
        raise ValueError(f"{enabled[0]} must remain false")


def _validate_ref_list(values: list[str], field_name: str) -> None:
    for value in values:
        _validate_safe_ref(str(value), field_name)


def _validate_safe_ref(value: str, field_name: str) -> None:
    _validate_safe_text(value, field_name)
    if not _SAFE_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a safe ref")


def _validate_safe_text(value: str, field_name: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe/private content")


def _safe_ref_or_default(value: object, default: str) -> str:
    candidate = _safe_ref_or_none(value)
    return candidate or default


def _safe_ref_or_none(value: object) -> str | None:
    if value is None:
        return None
    candidate = str(value).strip()
    if not candidate:
        return None
    try:
        _validate_safe_ref(candidate, "ref")
    except ValueError:
        return None
    return candidate


def _safe_refs(values: Any) -> list[str]:
    if values is None:
        return []
    refs: list[str] = []
    for value in values:
        candidate = _safe_ref_or_none(value)
        if candidate:
            refs.append(candidate)
    return _dedupe(refs)


def _safe_suffix(value: str) -> str:
    suffix = _SAFE_SUFFIX_RE.sub("-", value.lower()).strip("-")
    return suffix[:80] or "unknown"


def _safe_records(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        candidate = _safe_ref_or_none(value)
        if candidate and candidate not in seen:
            seen.add(candidate)
            result.append(candidate)
    return result
