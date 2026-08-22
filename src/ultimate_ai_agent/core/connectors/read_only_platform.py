"""ECO-009 exact read-only connector platform.

The first admitted adapter is a caller-supplied calendar metadata snapshot. It
never authenticates an account or performs network I/O. The platform applies
the same bounds, cursor, provenance, retention, revocation, safe-disable, and
rate-limit contract that a later separately approved provider adapter must
honor.
"""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ECO009_SCHEMA_VERSION = "uaa-eco-009-read-only-connector-platform.v1"
ECO009_CONTRACT_REF = "contract-ref:eco-009-read-only-connector-platform:v1"
ECO009_CALENDAR_ADAPTER_REF = (
    "connector-adapter-ref:eco-009:calendar-metadata-snapshot-v1"
)
ECO009_DEFAULT_RETENTION_REF = "retention-ref:eco-009:bounded-metadata-default"

_SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:/-]{2,240}$")
_RAW_PATH_RE = re.compile(
    r"(?i)(?:^|[\s\"'`(:=,\[])(?:~[/\\]|"
    r"/(?:users|home|usr|var|private|tmp|etc)(?:/|$)|[a-z]:[/\\]|\\\\[^\\\s]+\\)"
)


class ConnectorSourceKind(str, Enum):
    calendar_metadata_snapshot = "calendar_metadata_snapshot"


class ConnectorSourceState(str, Enum):
    ready = "ready"
    revoked = "revoked"


class ConnectorReadStatus(str, Enum):
    completed = "completed"
    source_not_configured = "source_not_configured"
    source_revoked = "source_revoked"
    safe_disabled = "safe_disabled"
    rate_limited = "rate_limited"
    invalid_cursor = "invalid_cursor"
    invalid_scope = "invalid_scope"


class CalendarMetadataField(str, Enum):
    event_ref = "event_ref"
    starts_at = "starts_at"
    ends_at = "ends_at"
    availability_ref = "availability_ref"
    source_revision_ref = "source_revision_ref"


class _ECO009Model(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=False,
    )


def _safe_ref(value: str, field_name: str) -> str:
    if (
        not _SAFE_REF_RE.fullmatch(value)
        or _RAW_PATH_RE.search(value)
        or contains_obvious_secret(value)
    ):
        raise ValueError(f"ECO009_{field_name.upper()}_SAFE_REF_REQUIRED")
    return value


def _safe_refs(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(values) != len(set(values)):
        raise ValueError(f"ECO009_{field_name.upper()}_DUPLICATE_REF")
    for value in values:
        _safe_ref(value, field_name)
    return values


def _utc(value: datetime, code: str) -> datetime:
    if value.tzinfo is None:
        raise ValueError(f"{code}_TIMEZONE_REQUIRED")
    return value.astimezone(timezone.utc)


def _digest_ref(prefix: str, payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


class ConnectorReadPolicy(_ECO009Model):
    policy_ref: str = "policy-ref:eco-009:calendar-metadata-snapshot-v1"
    max_page_size: int = Field(default=100, ge=1, le=100)
    max_time_window_days: int = Field(default=31, ge=1, le=31)
    max_reads_per_minute: int = Field(default=60, ge=1, le=60)
    cursor_ttl_seconds: int = Field(default=900, ge=60, le=3600)
    max_cached_requests: int = Field(default=1000, ge=1, le=10000)
    safe_refs_only: Literal[True] = True
    provenance_required: Literal[True] = True
    retention_required: Literal[True] = True
    revocation_required: Literal[True] = True
    safe_disable_required: Literal[True] = True
    connector_write_enabled: Literal[False] = False
    account_auth_enabled: Literal[False] = False
    network_access_enabled: Literal[False] = False
    background_sync_enabled: Literal[False] = False
    raw_content_enabled: Literal[False] = False
    attachment_download_enabled: Literal[False] = False
    model_call_enabled: Literal[False] = False
    production_authority_enabled: Literal[False] = False

    @model_validator(mode="after")
    def validate_policy(self) -> "ConnectorReadPolicy":
        _safe_ref(self.policy_ref, "policy_ref")
        return self


class CalendarMetadataSnapshotRow(_ECO009Model):
    event_ref: str
    starts_at: datetime
    ends_at: datetime
    availability_ref: str
    provenance_ref: str
    source_revision_ref: str
    retention_ref: str = ECO009_DEFAULT_RETENTION_REF
    raw_title_included: Literal[False] = False
    raw_location_included: Literal[False] = False
    participant_identifiers_included: Literal[False] = False
    raw_body_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_row(self) -> "CalendarMetadataSnapshotRow":
        for field_name in (
            "event_ref",
            "availability_ref",
            "provenance_ref",
            "source_revision_ref",
            "retention_ref",
        ):
            _safe_ref(str(getattr(self, field_name)), field_name)
        start = _utc(self.starts_at, "ECO009_START")
        end = _utc(self.ends_at, "ECO009_END")
        if end <= start:
            raise ValueError("ECO009_EVENT_TIME_RANGE_INVALID")
        return self


class ConnectorReadRequest(_ECO009Model):
    request_ref: str
    workspace_ref: str
    source_ref: str
    field_refs: tuple[str, ...]
    starts_at: datetime
    ends_at: datetime
    limit: int = Field(default=50, ge=1, le=100)
    cursor_ref: str | None = None
    purpose_ref: str = "purpose-ref:eco-009:operator-read-only-inspection"

    @model_validator(mode="after")
    def validate_request(self) -> "ConnectorReadRequest":
        for field_name in ("request_ref", "workspace_ref", "source_ref", "purpose_ref"):
            _safe_ref(str(getattr(self, field_name)), field_name)
        _safe_refs(self.field_refs, "field_ref")
        if not self.field_refs:
            raise ValueError("ECO009_FIELD_REF_REQUIRED")
        if self.cursor_ref is not None:
            _safe_ref(self.cursor_ref, "cursor_ref")
        start = _utc(self.starts_at, "ECO009_START")
        end = _utc(self.ends_at, "ECO009_END")
        if end <= start:
            raise ValueError("ECO009_REQUEST_TIME_RANGE_INVALID")
        return self


class ConnectorReadItem(_ECO009Model):
    item_ref: str
    field_values: dict[str, str]
    provenance_ref: str
    source_revision_ref: str
    retention_ref: str

    @model_validator(mode="after")
    def validate_item(self) -> "ConnectorReadItem":
        for field_name in (
            "item_ref",
            "provenance_ref",
            "source_revision_ref",
            "retention_ref",
        ):
            _safe_ref(str(getattr(self, field_name)), field_name)
        for key, value in self.field_values.items():
            if key not in {field.value for field in CalendarMetadataField}:
                raise ValueError("ECO009_ITEM_FIELD_NOT_ALLOWED")
            if key.endswith("_ref"):
                _safe_ref(value, "field_value_ref")
            elif key in {
                CalendarMetadataField.starts_at.value,
                CalendarMetadataField.ends_at.value,
            }:
                _utc(datetime.fromisoformat(value), "ECO009_FIELD_TIME")
        return self


class ConnectorReadOutcome(_ECO009Model):
    schema_version: Literal["uaa-eco-009-read-only-connector-platform.v1"] = (
        ECO009_SCHEMA_VERSION
    )
    contract_ref: Literal["contract-ref:eco-009-read-only-connector-platform:v1"] = (
        ECO009_CONTRACT_REF
    )
    outcome_ref: str
    request_ref: str
    source_ref: str
    status: ConnectorReadStatus
    reason_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    items: tuple[ConnectorReadItem, ...] = ()
    next_cursor_ref: str | None = None
    expires_at: datetime | None = None
    safe_summary: str
    external_read_performed: Literal[False] = False
    network_access_performed: Literal[False] = False
    account_auth_performed: Literal[False] = False
    connector_write_performed: Literal[False] = False
    raw_content_included: Literal[False] = False
    model_call_performed: Literal[False] = False
    production_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_outcome(self) -> "ConnectorReadOutcome":
        for field_name in ("outcome_ref", "request_ref", "source_ref"):
            _safe_ref(str(getattr(self, field_name)), field_name)
        _safe_refs(self.reason_refs, "reason_ref")
        _safe_refs(self.evidence_refs, "evidence_ref")
        if self.next_cursor_ref is not None:
            _safe_ref(self.next_cursor_ref, "next_cursor_ref")
        if self.status != ConnectorReadStatus.completed and self.items:
            raise ValueError("ECO009_BLOCKED_OUTCOME_MUST_NOT_RETURN_ITEMS")
        if contains_obvious_secret(self.safe_summary) or _RAW_PATH_RE.search(
            self.safe_summary
        ):
            raise ValueError("ECO009_SAFE_SUMMARY_REDACTION_REQUIRED")
        return self


class ConnectorSourceDescriptor(_ECO009Model):
    source_ref: str
    source_kind: ConnectorSourceKind
    adapter_ref: Literal[
        "connector-adapter-ref:eco-009:calendar-metadata-snapshot-v1"
    ] = ECO009_CALENDAR_ADAPTER_REF
    workspace_ref: str
    source_fingerprint_ref: str
    provenance_ref: str
    retention_ref: str
    supported_field_refs: tuple[str, ...]
    state: ConnectorSourceState = ConnectorSourceState.ready
    revocation_ref: str | None = None
    fixture_or_caller_supplied_snapshot: Literal[True] = True
    live_account_connected: Literal[False] = False
    network_adapter_enabled: Literal[False] = False
    background_sync_enabled: Literal[False] = False
    write_operations_enabled: Literal[False] = False

    @model_validator(mode="after")
    def validate_descriptor(self) -> "ConnectorSourceDescriptor":
        for field_name in (
            "source_ref",
            "workspace_ref",
            "source_fingerprint_ref",
            "provenance_ref",
            "retention_ref",
        ):
            _safe_ref(str(getattr(self, field_name)), field_name)
        _safe_refs(self.supported_field_refs, "supported_field_ref")
        if self.state == ConnectorSourceState.revoked and self.revocation_ref is None:
            raise ValueError("ECO009_REVOCATION_REF_REQUIRED")
        if self.revocation_ref is not None:
            _safe_ref(self.revocation_ref, "revocation_ref")
        return self


class CalendarMetadataSnapshotAdapter:
    """Exact no-network adapter over an already-redacted metadata snapshot."""

    def __init__(
        self,
        *,
        source_ref: str,
        workspace_ref: str,
        rows: tuple[CalendarMetadataSnapshotRow, ...],
        provenance_ref: str,
        retention_ref: str = ECO009_DEFAULT_RETENTION_REF,
    ) -> None:
        _safe_ref(source_ref, "source_ref")
        _safe_ref(workspace_ref, "workspace_ref")
        _safe_ref(provenance_ref, "provenance_ref")
        _safe_ref(retention_ref, "retention_ref")
        ordered = tuple(sorted(rows, key=lambda row: (row.starts_at, row.event_ref)))
        self.rows = ordered
        self.descriptor = ConnectorSourceDescriptor(
            source_ref=source_ref,
            source_kind=ConnectorSourceKind.calendar_metadata_snapshot,
            workspace_ref=workspace_ref,
            source_fingerprint_ref=_digest_ref(
                "connector-source-fingerprint-ref",
                [row.model_dump(mode="json") for row in ordered],
            ),
            provenance_ref=provenance_ref,
            retention_ref=retention_ref,
            supported_field_refs=tuple(field.value for field in CalendarMetadataField),
        )

    def bounded_rows(
        self, request: ConnectorReadRequest
    ) -> tuple[CalendarMetadataSnapshotRow, ...]:
        start = _utc(request.starts_at, "ECO009_START")
        end = _utc(request.ends_at, "ECO009_END")
        return tuple(
            row
            for row in self.rows
            if _utc(row.starts_at, "ECO009_START") < end
            and _utc(row.ends_at, "ECO009_END") > start
        )


class _CursorState(_ECO009Model):
    source_ref: str
    request_binding_ref: str
    offset: int
    expires_at: datetime


class ConnectorReadPlatform:
    """In-memory exact-lane coordinator; it never owns provider credentials."""

    def __init__(self, *, policy: ConnectorReadPolicy | None = None) -> None:
        self.policy = policy or ConnectorReadPolicy()
        self._sources: dict[str, CalendarMetadataSnapshotAdapter] = {}
        self._revocations: dict[str, str] = {}
        self._cursor_state: dict[str, _CursorState] = {}
        self._request_bindings: dict[str, str] = {}
        self._request_cache: dict[str, ConnectorReadOutcome] = {}
        self._request_order: deque[str] = deque()
        self._read_times: dict[str, deque[datetime]] = defaultdict(deque)
        self._safe_disable_ref: str | None = None

    def register_calendar_snapshot(
        self, adapter: CalendarMetadataSnapshotAdapter
    ) -> None:
        source_ref = adapter.descriptor.source_ref
        if source_ref in self._sources:
            raise ValueError("ECO009_DUPLICATE_SOURCE_REF")
        self._sources[source_ref] = adapter

    def descriptors(self) -> tuple[ConnectorSourceDescriptor, ...]:
        descriptors: list[ConnectorSourceDescriptor] = []
        for source_ref in sorted(self._sources):
            descriptor = self._sources[source_ref].descriptor
            revocation_ref = self._revocations.get(source_ref)
            if revocation_ref is not None:
                descriptor = descriptor.model_copy(
                    update={
                        "state": ConnectorSourceState.revoked,
                        "revocation_ref": revocation_ref,
                    }
                )
            descriptors.append(descriptor)
        return tuple(descriptors)

    @property
    def safe_disable_active(self) -> bool:
        return self._safe_disable_ref is not None

    def set_safe_disable(self, safe_disable_ref: str) -> None:
        self._safe_disable_ref = _safe_ref(safe_disable_ref, "safe_disable_ref")

    def clear_safe_disable(self) -> None:
        self._safe_disable_ref = None

    def revoke_source(self, source_ref: str, revocation_ref: str) -> None:
        _safe_ref(source_ref, "source_ref")
        _safe_ref(revocation_ref, "revocation_ref")
        if source_ref not in self._sources:
            raise ValueError("ECO009_SOURCE_NOT_CONFIGURED")
        self._revocations[source_ref] = revocation_ref

    def read(
        self,
        request: ConnectorReadRequest,
        *,
        now: datetime | None = None,
    ) -> ConnectorReadOutcome:
        observed_at = _utc(now or datetime.now(timezone.utc), "ECO009_NOW")
        self._purge_expired_cursors(observed_at)
        binding_ref = self._request_binding_ref(request)
        previous_binding = self._request_bindings.get(request.request_ref)
        if previous_binding is not None:
            if previous_binding != binding_ref:
                return self._blocked(
                    request,
                    ConnectorReadStatus.invalid_scope,
                    "reason-ref:eco-009:request-ref-conflict",
                )
            if request.source_ref in self._revocations:
                return self._blocked(
                    request,
                    ConnectorReadStatus.source_revoked,
                    "reason-ref:eco-009:source-revoked",
                    evidence_refs=(self._revocations[request.source_ref],),
                )
            if self._safe_disable_ref is not None:
                return self._blocked(
                    request,
                    ConnectorReadStatus.safe_disabled,
                    "reason-ref:eco-009:safe-disable-active",
                    evidence_refs=(self._safe_disable_ref,),
                )
            return self._request_cache[request.request_ref]
        adapter = self._sources.get(request.source_ref)
        if adapter is None:
            return self._remember(
                request,
                self._blocked(
                    request,
                    ConnectorReadStatus.source_not_configured,
                    "reason-ref:eco-009:source-not-configured",
                ),
                binding_ref,
            )
        if adapter.descriptor.workspace_ref != request.workspace_ref:
            return self._remember(
                request,
                self._blocked(
                    request,
                    ConnectorReadStatus.invalid_scope,
                    "reason-ref:eco-009:workspace-binding-mismatch",
                ),
                binding_ref,
            )
        if request.source_ref in self._revocations:
            return self._remember(
                request,
                self._blocked(
                    request,
                    ConnectorReadStatus.source_revoked,
                    "reason-ref:eco-009:source-revoked",
                    evidence_refs=(self._revocations[request.source_ref],),
                ),
                binding_ref,
            )
        if self._safe_disable_ref is not None:
            return self._remember(
                request,
                self._blocked(
                    request,
                    ConnectorReadStatus.safe_disabled,
                    "reason-ref:eco-009:safe-disable-active",
                    evidence_refs=(self._safe_disable_ref,),
                ),
                binding_ref,
            )
        if request.limit > self.policy.max_page_size or (
            _utc(request.ends_at, "ECO009_END")
            - _utc(request.starts_at, "ECO009_START")
        ) > timedelta(days=self.policy.max_time_window_days):
            return self._remember(
                request,
                self._blocked(
                    request,
                    ConnectorReadStatus.invalid_scope,
                    "reason-ref:eco-009:request-bounds-exceeded",
                ),
                binding_ref,
            )
        if not set(request.field_refs) <= set(adapter.descriptor.supported_field_refs):
            return self._remember(
                request,
                self._blocked(
                    request,
                    ConnectorReadStatus.invalid_scope,
                    "reason-ref:eco-009:field-scope-not-allowed",
                ),
                binding_ref,
            )
        if self._rate_limited(request.source_ref, observed_at):
            return self._remember(
                request,
                self._blocked(
                    request,
                    ConnectorReadStatus.rate_limited,
                    "reason-ref:eco-009:rate-limit-reached",
                ),
                binding_ref,
            )

        offset = 0
        if request.cursor_ref is not None:
            cursor = self._cursor_state.get(request.cursor_ref)
            if (
                cursor is None
                or cursor.source_ref != request.source_ref
                or cursor.request_binding_ref != self._cursor_binding_ref(request)
                or _utc(cursor.expires_at, "ECO009_CURSOR_EXPIRY") <= observed_at
            ):
                return self._remember(
                    request,
                    self._blocked(
                        request,
                        ConnectorReadStatus.invalid_cursor,
                        "reason-ref:eco-009:cursor-invalid-or-expired",
                    ),
                    binding_ref,
                )
            offset = cursor.offset

        rows = adapter.bounded_rows(request)
        page = rows[offset : offset + request.limit]
        items = tuple(self._project_row(row, request.field_refs) for row in page)
        next_offset = offset + len(page)
        next_cursor_ref: str | None = None
        expires_at: datetime | None = None
        if next_offset < len(rows):
            expires_at = observed_at + timedelta(seconds=self.policy.cursor_ttl_seconds)
            next_cursor_ref = _digest_ref(
                "connector-cursor-ref",
                {
                    "source_ref": request.source_ref,
                    "binding_ref": self._cursor_binding_ref(request),
                    "offset": next_offset,
                    "expires_at": expires_at.isoformat(),
                },
            )
            self._cursor_state[next_cursor_ref] = _CursorState(
                source_ref=request.source_ref,
                request_binding_ref=self._cursor_binding_ref(request),
                offset=next_offset,
                expires_at=expires_at,
            )
        outcome = ConnectorReadOutcome(
            outcome_ref=_digest_ref(
                "connector-read-outcome-ref",
                {
                    "request_ref": request.request_ref,
                    "source_fingerprint_ref": adapter.descriptor.source_fingerprint_ref,
                    "item_refs": [item.item_ref for item in items],
                    "next_cursor_ref": next_cursor_ref,
                },
            ),
            request_ref=request.request_ref,
            source_ref=request.source_ref,
            status=ConnectorReadStatus.completed,
            reason_refs=("reason-ref:eco-009:bounded-snapshot-read-completed",),
            evidence_refs=(
                adapter.descriptor.source_fingerprint_ref,
                adapter.descriptor.provenance_ref,
                "evidence-ref:eco-009:no-network-account-or-write",
            ),
            items=items,
            next_cursor_ref=next_cursor_ref,
            expires_at=expires_at,
            safe_summary=(
                "A bounded caller-supplied calendar metadata snapshot was read "
                "with exact field, time, page, provenance, and retention limits."
            ),
        )
        return self._remember(request, outcome, binding_ref)

    def _project_row(
        self,
        row: CalendarMetadataSnapshotRow,
        field_refs: tuple[str, ...],
    ) -> ConnectorReadItem:
        values: dict[str, str] = {}
        for field_ref in field_refs:
            value = getattr(row, field_ref)
            values[field_ref] = (
                _utc(value, "ECO009_FIELD_TIME").isoformat()
                if isinstance(value, datetime)
                else str(value)
            )
        return ConnectorReadItem(
            item_ref=_digest_ref(
                "connector-read-item-ref",
                {"event_ref": row.event_ref, "fields": values},
            ),
            field_values=values,
            provenance_ref=row.provenance_ref,
            source_revision_ref=row.source_revision_ref,
            retention_ref=row.retention_ref,
        )

    def _rate_limited(self, source_ref: str, now: datetime) -> bool:
        history = self._read_times[source_ref]
        cutoff = now - timedelta(minutes=1)
        while history and history[0] <= cutoff:
            history.popleft()
        if len(history) >= self.policy.max_reads_per_minute:
            return True
        history.append(now)
        return False

    def _purge_expired_cursors(self, now: datetime) -> None:
        expired_refs = [
            cursor_ref
            for cursor_ref, cursor in self._cursor_state.items()
            if _utc(cursor.expires_at, "ECO009_CURSOR_EXPIRY") <= now
        ]
        for cursor_ref in expired_refs:
            del self._cursor_state[cursor_ref]

    def _remember(
        self,
        request: ConnectorReadRequest,
        outcome: ConnectorReadOutcome,
        binding_ref: str,
    ) -> ConnectorReadOutcome:
        self._request_cache[request.request_ref] = outcome
        self._request_bindings[request.request_ref] = binding_ref
        self._request_order.append(request.request_ref)
        while len(self._request_order) > self.policy.max_cached_requests:
            expired_request_ref = self._request_order.popleft()
            self._request_bindings.pop(expired_request_ref, None)
            self._request_cache.pop(expired_request_ref, None)
        return outcome

    def _blocked(
        self,
        request: ConnectorReadRequest,
        status: ConnectorReadStatus,
        reason_ref: str,
        *,
        evidence_refs: tuple[str, ...] = (),
    ) -> ConnectorReadOutcome:
        return ConnectorReadOutcome(
            outcome_ref=_digest_ref(
                "connector-read-outcome-ref",
                {
                    "request_ref": request.request_ref,
                    "source_ref": request.source_ref,
                    "status": status.value,
                    "reason_ref": reason_ref,
                },
            ),
            request_ref=request.request_ref,
            source_ref=request.source_ref,
            status=status,
            reason_refs=(reason_ref,),
            evidence_refs=tuple(
                dict.fromkeys(
                    [
                        *evidence_refs,
                        "evidence-ref:eco-009:blocked-no-external-read-or-write",
                    ]
                )
            ),
            safe_summary=(
                "The exact read-only connector request failed closed before "
                "returning metadata."
            ),
        )

    @staticmethod
    def _request_binding_ref(request: ConnectorReadRequest) -> str:
        return _digest_ref(
            "connector-request-binding-ref",
            request.model_dump(mode="json"),
        )

    @staticmethod
    def _cursor_binding_ref(request: ConnectorReadRequest) -> str:
        payload = request.model_dump(mode="json", exclude={"request_ref", "cursor_ref"})
        return _digest_ref("connector-cursor-binding-ref", payload)


def build_eco009_connector_read_platform_posture(
    platform: ConnectorReadPlatform | None = None,
) -> dict[str, Any]:
    """Return backend/UI-safe current truth without implying a live account."""

    descriptors = platform.descriptors() if platform is not None else ()
    configured = len(descriptors)
    revoked = sum(item.state == ConnectorSourceState.revoked for item in descriptors)
    ready = configured - revoked
    return {
        "schema_version": ECO009_SCHEMA_VERSION,
        "contract_ref": ECO009_CONTRACT_REF,
        "source": "python_core_eco009_connector_read_platform",
        "status": (
            "snapshot_source_ready"
            if ready
            else "implemented_inactive_no_snapshot_source"
        ),
        "adapter_ref": ECO009_CALENDAR_ADAPTER_REF,
        "configured_source_count": configured,
        "revoked_source_count": revoked,
        "ready_source_count": ready,
        "source_refs": [item.source_ref for item in descriptors],
        "provenance_refs": [item.provenance_ref for item in descriptors],
        "retention_refs": [item.retention_ref for item in descriptors],
        "safe_disable_supported": True,
        "safe_disable_active": (
            platform.safe_disable_active if platform is not None else False
        ),
        "revocation_supported": True,
        "bounded_cursor_supported": True,
        "rate_limit_supported": True,
        "fixture_or_caller_supplied_snapshot_only": True,
        "live_account_connected": False,
        "network_access_enabled": False,
        "account_auth_enabled": False,
        "background_sync_enabled": False,
        "raw_content_enabled": False,
        "connector_write_enabled": False,
        "production_authority_enabled": False,
        "safe_summary": (
            "ECO-009 provides one exact calendar metadata snapshot adapter with "
            "bounded fields, time, pages, cursors, provenance, retention, "
            "revocation, safe-disable, and rate limits. No live account is connected."
        ),
        "next_safe_action": (
            "Register an already-redacted caller-supplied snapshot for local "
            "inspection, or keep the lane visibly inactive."
        ),
    }
