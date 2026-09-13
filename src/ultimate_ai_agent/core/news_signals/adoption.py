"""Founder-private News and Signals adoption workflow for Queue V2 Q34.

The adoption layer turns the Q24 read model into a bounded local workflow for
operator-supplied, already-redacted source artifacts.  It deliberately does
not fetch URLs, authenticate source accounts, call a model, or perform an
external action.  Every state change is revision-bound, idempotent, explicitly
approved, authority-lease constrained, content-free in its receipt, and
reversible through one bounded undo snapshot.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
from typing import Any, Iterator, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityConstraint,
    AuthorityConstraintClaim,
    AuthorityConstraintKind,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseScope,
    AuthorityLeaseStore,
    TrustMode,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    AuthorityLeaseApprovalCapacityError,
    AuthorityLeaseApprovalConflictError,
    AuthorityLeaseApprovalStateError,
    AuthorityLeaseApprovalStore,
    build_authority_lease_approval_requirement_for_request,
    capture_authority_lease_backend_approval,
    issue_authority_lease_from_backend_state,
)
from ultimate_ai_agent.core.news_signals.read_model import (
    MAX_NEWS_SIGNAL_SOURCES,
    NewsSignalArtifact,
    NewsSignalPreference,
    NewsSignalSource,
    NewsSignalsRepository,
    _artifact_from_row,
    _parse_timestamp,
    _validate_ref,
    _validate_safe_text,
    build_news_signals_summary,
)


NEWS_SIGNALS_ADOPTION_SCHEMA_VERSION = "uaa-news-signals-adoption.v1"
NEWS_SIGNALS_ADOPTION_CONTRACT_REF = (
    "contract-ref:queue-v2-q34-news-signals-adoption:v1"
)
NEWS_SIGNALS_ADOPTION_WORKSPACE_REF = "news-workspace-ref:founder-private"
NEWS_SIGNALS_ADOPTION_ROUTE_REF = "POST /control-center/news-signals/adoption/commit"
NEWS_SIGNALS_ADOPTION_AUTHORITY_LANE_REF = (
    "authority-lane-ref:news-signals-adoption-local-write"
)
NEWS_SIGNALS_ADOPTION_SAFE_DISABLE_REF = (
    "safe-disable-ref:news-signals-adoption-local-write:deny"
)
NEWS_SIGNALS_ADOPTION_APPROVAL_TTL_MINUTES = 5
NEWS_SIGNALS_ADOPTION_MAX_REVISION = 9_007_199_254_740_991
NEWS_SIGNALS_ADOPTION_MAX_ARTIFACTS = 2_000
NEWS_SIGNALS_ADOPTION_MAX_PREFERENCES = 128
NEWS_SIGNALS_ADOPTION_MAX_RECEIPTS = 2_048
NEWS_SIGNALS_ADOPTION_MAX_UNDO_BYTES = 4 * 1024 * 1024
NEWS_SIGNALS_ADOPTION_MAX_UNDO_JSON_DEPTH = 32
NEWS_SIGNALS_ADOPTION_MAX_ROW_JSON_BYTES = 64 * 1024
NEWS_SIGNALS_ADOPTION_MAX_PAGE_SIZE = 100
NEWS_SIGNALS_ADOPTION_MAX_PAGE_OFFSET = 1_999
NEWS_SIGNALS_ADOPTION_MAX_SEARCH_LENGTH = 80
NEWS_SIGNALS_ADOPTION_ADAPTER_REF = (
    "connector-adapter-ref:q34:local-redacted-artifact-intake-v1"
)
NEWS_SIGNALS_ADOPTION_PROVENANCE_REF = (
    "provenance-ref:q34:operator-supplied-redacted-artifact"
)
NEWS_SIGNALS_ADOPTION_RETENTION_REF = "retention-ref:q34:bounded-local-metadata"

MutationAction = Literal[
    "register_source",
    "update_source",
    "ingest_signal",
    "update_signal",
    "set_preference",
    "remove_preference",
    "set_source_state",
    "archive_signal",
    "recover_signal",
    "undo",
]


class NewsSignalsAdoptionError(RuntimeError):
    """Safe-code-only Q34 adoption failure."""


class NewsSignalsAdoptionConflict(NewsSignalsAdoptionError):
    """A revision, idempotency, lifecycle, or approval conflict."""


class _AdoptionModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_JSON_INVALID") from exc


def _hash_ref(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(_canonical_json(value)).hexdigest()
    return f"{prefix}:sha256:{digest}"


def _approval_validation_ref(decision_id: str) -> str:
    return _hash_ref(
        "approval-validation-ref:news-signals-adoption",
        {"decision_id": decision_id},
    )


def _mutation_receipt_ref(
    *,
    action: MutationAction,
    target_ref: str | None,
    source_ref: str | None,
    signal_ref: str | None,
    before_revision: int,
    after_revision: int,
    idempotency_ref: str,
    payload_fingerprint_ref: str,
    preview_ref: str,
    approval_ref: str,
    approval_validation_ref: str,
    approval_expires_at: datetime,
    authority_decision_ref: str,
    authority_lease_ref: str,
    state_ref: str,
) -> str:
    return _hash_ref(
        "receipt-ref:news-signals-adoption",
        {
            "action": action,
            "target_ref": target_ref,
            "source_ref": source_ref,
            "signal_ref": signal_ref,
            "before_revision": before_revision,
            "after_revision": after_revision,
            "idempotency_ref": idempotency_ref,
            "payload_fingerprint_ref": payload_fingerprint_ref,
            "preview_ref": preview_ref,
            "approval_ref": approval_ref,
            "approval_validation_ref": approval_validation_ref,
            "approval_expires_at": _utc_text(approval_expires_at),
            "authority_decision_ref": authority_decision_ref,
            "authority_lease_ref": authority_lease_ref,
            "state_ref": state_ref,
        },
    )


def _json_nesting_exceeds_limit(value: str, *, maximum_depth: int) -> bool:
    depth = 0
    in_string = False
    escaped = False
    for character in value:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        elif character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > maximum_depth:
                return True
        elif character in "]}" and depth > 0:
            depth -= 1
    return False


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_label(value: str, field_name: str, maximum: int) -> str:
    _validate_safe_text(value, field_name, maximum=maximum)
    return value


class NewsSignalSourceDraft(_AdoptionModel):
    safe_label: str
    source_kind: Literal["official", "community", "rss", "public_social", "local"]
    freshness_ttl_seconds: int = Field(default=86_400, ge=300, le=604_800)

    @field_validator("safe_label")
    @classmethod
    def validate_safe_label(cls, value: str) -> str:
        return _safe_label(value, "safe_label", 80)


class NewsSignalArtifactDraft(_AdoptionModel):
    source_ref: str
    title: str
    safe_summary: str
    topic_label: str
    cluster_label: str
    claim_label: str | None = None
    published_at: str
    confidence_percent: int = Field(ge=0, le=100)
    evidence_class: Literal["primary", "corroborating", "community", "commentary"]
    claim_stance: Literal["supports", "disputes", "unknown"] = "unknown"

    @field_validator("source_ref")
    @classmethod
    def validate_source_ref(cls, value: str) -> str:
        _validate_ref(value, "source_ref")
        return value

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _safe_label(value, "title", 140)

    @field_validator("safe_summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        return _safe_label(value, "safe_summary", 320)

    @field_validator("topic_label", "cluster_label")
    @classmethod
    def validate_group_label(cls, value: str) -> str:
        return _safe_label(value, "group_label", 80)

    @field_validator("claim_label")
    @classmethod
    def validate_claim_label(cls, value: str | None) -> str | None:
        if value is not None:
            return _safe_label(value, "claim_label", 80)
        return value

    @field_validator("published_at")
    @classmethod
    def validate_published_at(cls, value: str) -> str:
        _parse_timestamp(value, "published_at")
        return value


class NewsSignalsAdoptionMutationRequest(_AdoptionModel):
    action: MutationAction
    expected_revision: int = Field(ge=0, le=NEWS_SIGNALS_ADOPTION_MAX_REVISION)
    target_ref: str | None = None
    source_draft: NewsSignalSourceDraft | None = None
    signal_draft: NewsSignalArtifactDraft | None = None
    topic_ref: str | None = None
    preference_weight: int | None = Field(default=None, ge=-20, le=20)
    source_state: Literal["ready", "safe_disabled"] | None = None

    @field_validator("target_ref", "topic_ref")
    @classmethod
    def validate_optional_ref(cls, value: str | None, info: Any) -> str | None:
        if value is not None:
            _validate_ref(value, info.field_name)
        return value

    @model_validator(mode="after")
    def validate_exact_action_shape(self) -> "NewsSignalsAdoptionMutationRequest":
        required: dict[str, tuple[str, ...]] = {
            "register_source": ("source_draft",),
            "update_source": ("target_ref", "source_draft"),
            "ingest_signal": ("signal_draft",),
            "update_signal": ("target_ref", "signal_draft"),
            "set_preference": ("topic_ref", "preference_weight"),
            "remove_preference": ("topic_ref",),
            "set_source_state": ("target_ref", "source_state"),
            "archive_signal": ("target_ref",),
            "recover_signal": ("target_ref",),
            "undo": (),
        }
        populated = {
            name
            for name in (
                "target_ref",
                "source_draft",
                "signal_draft",
                "topic_ref",
                "preference_weight",
                "source_state",
            )
            if getattr(self, name) is not None
        }
        expected = set(required[self.action])
        if populated != expected:
            raise ValueError("NEWS_SIGNALS_ADOPTION_ACTION_SHAPE_INVALID")
        if (
            self.action == "ingest_signal"
            and self.signal_draft is not None
            and self.signal_draft.claim_label is None
        ):
            raise ValueError("NEWS_SIGNALS_ADOPTION_CLAIM_LABEL_REQUIRED")
        return self


class NewsSignalsAdoptionApprovalCaptureRequest(_AdoptionModel):
    mutation: NewsSignalsAdoptionMutationRequest
    preview_ref: str
    approval_ref: str

    @field_validator("preview_ref", "approval_ref")
    @classmethod
    def validate_ref(cls, value: str, info: Any) -> str:
        _validate_ref(value, info.field_name)
        return value


class NewsSignalsAdoptionCommitRequest(NewsSignalsAdoptionApprovalCaptureRequest):
    pass


class NewsSignalsAdoptionMutationPreview(_AdoptionModel):
    schema_version: Literal["uaa-news-signals-adoption-preview.v1"] = (
        "uaa-news-signals-adoption-preview.v1"
    )
    contract_ref: Literal["contract-ref:queue-v2-q34-news-signals-adoption:v1"] = (
        NEWS_SIGNALS_ADOPTION_CONTRACT_REF
    )
    action: MutationAction
    target_ref: str | None
    source_ref: str | None
    signal_ref: str | None
    expected_revision: int
    resulting_revision: int
    current_state_ref: str
    payload_fingerprint_ref: str
    preview_ref: str
    approval_ref: str
    safe_summary: str
    external_network_read_performed: Literal[False] = False
    authenticated_source_access_performed: Literal[False] = False
    model_call_performed: Literal[False] = False
    external_write_performed: Literal[False] = False
    production_authority_granted: Literal[False] = False


class NewsSignalsAdoptionApprovalReceipt(_AdoptionModel):
    schema_version: Literal["uaa-news-signals-adoption-approval.v1"] = (
        "uaa-news-signals-adoption-approval.v1"
    )
    approval_ref: str
    approval_validation_ref: str
    preview_ref: str
    idempotency_ref: str
    expires_at: datetime
    safe_summary: Literal[
        "One exact founder-private News change is approved for commit."
    ] = "One exact founder-private News change is approved for commit."

    @field_validator(
        "approval_ref",
        "approval_validation_ref",
        "preview_ref",
        "idempotency_ref",
    )
    @classmethod
    def validate_receipt_ref(cls, value: str, info: Any) -> str:
        _validate_ref(value, info.field_name)
        return value

    @model_validator(mode="after")
    def validate_approval_binding(self) -> "NewsSignalsAdoptionApprovalReceipt":
        if self.approval_ref != _hash_ref(
            "approval-ref:news-signals-adoption",
            {"preview_ref": self.preview_ref},
        ):
            raise ValueError("NEWS_SIGNALS_ADOPTION_APPROVAL_RECEIPT_INVALID")
        if self.expires_at.tzinfo is None or self.expires_at.utcoffset() is None:
            raise ValueError("NEWS_SIGNALS_ADOPTION_APPROVAL_EXPIRY_INVALID")
        return self


class NewsSignalsAdoptionMutationReceipt(_AdoptionModel):
    schema_version: Literal["uaa-news-signals-adoption-receipt.v1"] = (
        "uaa-news-signals-adoption-receipt.v1"
    )
    contract_ref: Literal["contract-ref:queue-v2-q34-news-signals-adoption:v1"] = (
        NEWS_SIGNALS_ADOPTION_CONTRACT_REF
    )
    action: MutationAction
    target_ref: str | None
    source_ref: str | None
    signal_ref: str | None
    before_revision: int
    after_revision: int
    idempotency_ref: str
    payload_fingerprint_ref: str
    preview_ref: str
    approval_ref: str
    approval_validation_ref: str
    approval_expires_at: datetime
    authority_decision_ref: str
    authority_lease_ref: str
    receipt_ref: str
    state_ref: str
    rollback_ref: str
    replayed: bool = False
    external_network_read_performed: Literal[False] = False
    authenticated_source_access_performed: Literal[False] = False
    model_call_performed: Literal[False] = False
    external_write_performed: Literal[False] = False
    production_authority_granted: Literal[False] = False
    safe_summary: Literal["One exact local News and Signals change was persisted."] = (
        "One exact local News and Signals change was persisted."
    )

    @field_validator(
        "idempotency_ref",
        "payload_fingerprint_ref",
        "preview_ref",
        "approval_ref",
        "approval_validation_ref",
        "authority_decision_ref",
        "authority_lease_ref",
        "receipt_ref",
        "state_ref",
        "rollback_ref",
    )
    @classmethod
    def validate_receipt_ref(cls, value: str, info: Any) -> str:
        _validate_ref(value, info.field_name)
        return value

    @field_validator("target_ref", "source_ref", "signal_ref")
    @classmethod
    def validate_optional_receipt_ref(cls, value: str | None, info: Any) -> str | None:
        if value is not None:
            _validate_ref(value, info.field_name)
        return value

    @model_validator(mode="after")
    def validate_receipt_binding(self) -> "NewsSignalsAdoptionMutationReceipt":
        if self.after_revision != self.before_revision + 1:
            raise ValueError("NEWS_SIGNALS_ADOPTION_RECEIPT_REVISION_INVALID")
        if not 0 <= self.before_revision < NEWS_SIGNALS_ADOPTION_MAX_REVISION:
            raise ValueError("NEWS_SIGNALS_ADOPTION_RECEIPT_REVISION_INVALID")
        if self.approval_ref != _hash_ref(
            "approval-ref:news-signals-adoption",
            {"preview_ref": self.preview_ref},
        ):
            raise ValueError("NEWS_SIGNALS_ADOPTION_RECEIPT_APPROVAL_INVALID")
        expected_receipt_ref = _mutation_receipt_ref(
            action=self.action,
            target_ref=self.target_ref,
            source_ref=self.source_ref,
            signal_ref=self.signal_ref,
            before_revision=self.before_revision,
            after_revision=self.after_revision,
            idempotency_ref=self.idempotency_ref,
            payload_fingerprint_ref=self.payload_fingerprint_ref,
            preview_ref=self.preview_ref,
            approval_ref=self.approval_ref,
            approval_validation_ref=self.approval_validation_ref,
            approval_expires_at=self.approval_expires_at,
            authority_decision_ref=self.authority_decision_ref,
            authority_lease_ref=self.authority_lease_ref,
            state_ref=self.state_ref,
        )
        if self.receipt_ref != expected_receipt_ref:
            raise ValueError("NEWS_SIGNALS_ADOPTION_RECEIPT_BINDING_INVALID")
        if self.rollback_ref != _hash_ref(
            "rollback-ref:news-signals-adoption",
            {"receipt_ref": self.receipt_ref, "action": "undo"},
        ):
            raise ValueError("NEWS_SIGNALS_ADOPTION_RECEIPT_ROLLBACK_INVALID")
        if (
            self.approval_expires_at.tzinfo is None
            or self.approval_expires_at.utcoffset() is None
        ):
            raise ValueError("NEWS_SIGNALS_ADOPTION_RECEIPT_EXPIRY_INVALID")
        return self


@dataclass(frozen=True)
class _NewsSignalsSnapshot:
    revision: int
    sources: tuple[NewsSignalSource, ...]
    artifacts: tuple[NewsSignalArtifact, ...]
    preferences: tuple[NewsSignalPreference, ...]
    archived_refs: frozenset[str]
    undo_snapshot_ref: str | None
    can_undo: bool


class NewsSignalsAdoptionStore:
    """Bounded local mutation layer over the existing Q24 repository."""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = Path(os.path.abspath(os.path.expanduser(str(state_dir))))
        self._ensure_private_storage()
        self.db_path = self.state_dir / "news_signals.sqlite3"
        self._validate_existing_database_files()
        try:
            self.repository = NewsSignalsRepository(self.state_dir)
        except (OSError, sqlite3.DatabaseError) as exc:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_DATABASE_STATE_INVALID"
            ) from exc
        self.db_path = self.repository.db_path
        self._ensure_adoption_schema()

    @classmethod
    def from_env(cls) -> "NewsSignalsAdoptionStore":
        configured = os.environ.get("UAA_FOUNDER_LOOP_STATE_DIR")
        state_dir = Path(configured) if configured else Path(".uaa") / "founder_loop"
        return cls(state_dir)

    def read_view(
        self,
        *,
        now: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
        search_query: str | None = None,
    ) -> dict[str, object]:
        if not 1 <= limit <= NEWS_SIGNALS_ADOPTION_MAX_PAGE_SIZE:
            raise ValueError("LIMIT_BOUNDS_INVALID")
        if not 0 <= offset <= NEWS_SIGNALS_ADOPTION_MAX_PAGE_OFFSET:
            raise ValueError("OFFSET_BOUNDS_INVALID")
        if search_query is not None:
            _validate_safe_text(
                search_query.strip(),
                "search_query",
                maximum=NEWS_SIGNALS_ADOPTION_MAX_SEARCH_LENGTH,
            )
        with self._safe_connection() as conn:
            conn.execute("BEGIN")
            state = self._read_snapshot(conn)
        active = tuple(
            item
            for item in state.artifacts
            if item.artifact_ref not in state.archived_refs
        )
        summary = build_news_signals_summary(
            sources=state.sources,
            artifacts=active,
            preferences=state.preferences,
            now=now,
            limit=limit,
        )
        normalized_search = search_query.strip().casefold() if search_query else None
        active_for_page = sorted(
            active,
            key=lambda item: (item.published_at, item.artifact_ref),
            reverse=True,
        )
        if normalized_search is not None:
            active_for_page = [
                item
                for item in active_for_page
                if normalized_search
                in " ".join(
                    (item.title, item.safe_summary, item.source_label)
                ).casefold()
            ]
        active_page_items = active_for_page[offset : offset + limit]
        source_by_ref = {source.source_ref: source for source in state.sources}
        archived_by_ref = {
            artifact.artifact_ref: artifact
            for artifact in state.artifacts
            if artifact.artifact_ref in state.archived_refs
        }
        archived_items = [
            {
                "signal_ref": artifact.artifact_ref,
                "title": artifact.title,
                "safe_summary": artifact.safe_summary,
                "source_ref": artifact.source_ref,
                "source_label": artifact.source_label,
                "topic_ref": artifact.topic_ref,
                "published_at": artifact.published_at,
                "archived": True,
            }
            for artifact in sorted(
                archived_by_ref.values(), key=lambda item: item.artifact_ref
            )
        ]
        return {
            "schema_version": NEWS_SIGNALS_ADOPTION_SCHEMA_VERSION,
            "contract_ref": NEWS_SIGNALS_ADOPTION_CONTRACT_REF,
            "status": summary["status"],
            "revision": state.revision,
            "current_state_ref": self._state_ref(state),
            "can_undo": state.can_undo,
            "local_manual_intake_enabled": True,
            "backend_owned": True,
            "external_content_untrusted": True,
            "live_fetch_enabled": False,
            "authenticated_source_enabled": False,
            "background_polling_enabled": False,
            "model_summarization_enabled": False,
            "connector_write_enabled": False,
            "action_authority_granted": False,
            "summary": summary,
            "active_items_page": {
                "offset": offset,
                "limit": limit,
                "total_items": len(active_for_page),
                "returned_items": len(active_page_items),
                "has_previous": offset > 0,
                "has_next": offset + len(active_page_items) < len(active_for_page),
                "search_applied": normalized_search is not None,
                "items": [
                    {
                        "signal_ref": item.artifact_ref,
                        "title": item.title,
                        "safe_summary": item.safe_summary,
                        "source_ref": item.source_ref,
                        "source_label": item.source_label,
                        "source_state": source_by_ref[item.source_ref].state,
                        "topic_ref": item.topic_ref,
                        "published_at": item.published_at,
                        "evidence_class": item.evidence_class,
                        "claim_stance": item.claim_stance,
                        "confidence_percent": item.confidence_percent,
                        "external_content_untrusted": True,
                    }
                    for item in active_page_items
                ],
            },
            "preferences": [asdict(item) for item in state.preferences],
            "archived_items": archived_items,
            "next_safe_action": self._next_safe_action(state, summary),
            "evidence_refs": [
                "evidence-ref:q34:local-redacted-intake-only",
                "evidence-ref:q34:exact-approved-local-mutations",
                "evidence-ref:q34:today-and-briefing-projection",
            ],
        }

    def preview_mutation(
        self,
        request: NewsSignalsAdoptionMutationRequest,
        *,
        idempotency_ref: str,
    ) -> NewsSignalsAdoptionMutationPreview:
        _validate_ref(idempotency_ref, "idempotency_ref")
        with self._safe_connection() as conn:
            conn.execute("BEGIN")
            state = self._read_snapshot(conn)
        return self._preview(state, request, idempotency_ref=idempotency_ref)

    def capture_approval(
        self,
        request: NewsSignalsAdoptionApprovalCaptureRequest,
        *,
        idempotency_ref: str,
    ) -> NewsSignalsAdoptionApprovalReceipt:
        _validate_ref(idempotency_ref, "idempotency_ref")
        with self._safe_connection() as conn:
            conn.execute("BEGIN")
            replay = self._receipt_for_idempotency(conn, idempotency_ref)
            state = self._read_snapshot(conn)
        if replay is not None:
            return self._replay_approval(
                replay,
                request=request,
                idempotency_ref=idempotency_ref,
            )
        preview = self._preview(
            state,
            request.mutation,
            idempotency_ref=idempotency_ref,
        )
        if (
            preview.preview_ref != request.preview_ref
            or preview.approval_ref != request.approval_ref
        ):
            raise NewsSignalsAdoptionConflict(
                "NEWS_SIGNALS_ADOPTION_APPROVAL_SCOPE_MISMATCH"
            )
        return self._capture_preview_approval(
            preview,
            idempotency_ref=idempotency_ref,
        )

    def commit_mutation(
        self,
        request: NewsSignalsAdoptionCommitRequest,
        *,
        idempotency_ref: str,
    ) -> NewsSignalsAdoptionMutationReceipt:
        _validate_ref(idempotency_ref, "idempotency_ref")
        lease_store: AuthorityLeaseStore | None = None
        lease: AuthorityLease | None = None
        try:
            with self._safe_connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                replay = self._receipt_for_idempotency(conn, idempotency_ref)
                if replay is not None:
                    return self._validate_receipt_replay(
                        replay,
                        request=request,
                        idempotency_ref=idempotency_ref,
                    )
                state = self._read_snapshot(conn)
                preview = self._preview(
                    state,
                    request.mutation,
                    idempotency_ref=idempotency_ref,
                )
                if (
                    preview.preview_ref != request.preview_ref
                    or preview.approval_ref != request.approval_ref
                ):
                    raise NewsSignalsAdoptionConflict(
                        "NEWS_SIGNALS_ADOPTION_COMMIT_SCOPE_MISMATCH"
                    )
                (
                    lease_store,
                    lease,
                    authority_decision_ref,
                    approval_validation_ref,
                    approval_expires_at,
                ) = self._authorize(preview, idempotency_ref=idempotency_ref)
                self._store_undo_snapshot(conn, state, request.mutation.action)
                source_ref, signal_ref = self._apply_mutation(
                    conn,
                    state,
                    request.mutation,
                    preview=preview,
                    now=_utc_now(),
                )
                conn.execute(
                    "UPDATE news_signals_adoption_meta SET revision = ? WHERE singleton = 1",
                    (preview.resulting_revision,),
                )
                next_state = self._read_snapshot(conn)
                state_ref = self._state_ref(next_state)
                if request.mutation.action != "undo":
                    self._bind_undo_snapshot(conn, expected_state_ref=state_ref)
                receipt_ref = _mutation_receipt_ref(
                    action=request.mutation.action,
                    target_ref=request.mutation.target_ref,
                    source_ref=source_ref,
                    signal_ref=signal_ref,
                    before_revision=state.revision,
                    after_revision=preview.resulting_revision,
                    idempotency_ref=idempotency_ref,
                    payload_fingerprint_ref=preview.payload_fingerprint_ref,
                    preview_ref=preview.preview_ref,
                    approval_ref=preview.approval_ref,
                    approval_validation_ref=approval_validation_ref,
                    approval_expires_at=approval_expires_at,
                    authority_decision_ref=authority_decision_ref,
                    authority_lease_ref=lease.lease_ref,
                    state_ref=state_ref,
                )
                receipt = NewsSignalsAdoptionMutationReceipt(
                    action=request.mutation.action,
                    target_ref=request.mutation.target_ref,
                    source_ref=source_ref,
                    signal_ref=signal_ref,
                    before_revision=state.revision,
                    after_revision=preview.resulting_revision,
                    idempotency_ref=idempotency_ref,
                    payload_fingerprint_ref=preview.payload_fingerprint_ref,
                    preview_ref=preview.preview_ref,
                    approval_ref=preview.approval_ref,
                    approval_validation_ref=approval_validation_ref,
                    approval_expires_at=approval_expires_at,
                    authority_decision_ref=authority_decision_ref,
                    authority_lease_ref=lease.lease_ref,
                    receipt_ref=receipt_ref,
                    state_ref=state_ref,
                    rollback_ref=_hash_ref(
                        "rollback-ref:news-signals-adoption",
                        {"receipt_ref": receipt_ref, "action": "undo"},
                    ),
                )
                self._insert_receipt(conn, receipt)
            self._harden_database_files()
            return receipt
        except Exception:
            if lease_store is not None and lease is not None:
                self._revoke_lease(lease_store, lease)
            raise

    def _preview(
        self,
        state: _NewsSignalsSnapshot,
        request: NewsSignalsAdoptionMutationRequest,
        *,
        idempotency_ref: str,
    ) -> NewsSignalsAdoptionMutationPreview:
        if request.expected_revision != state.revision:
            raise NewsSignalsAdoptionConflict("NEWS_SIGNALS_ADOPTION_STALE_REVISION")
        if state.revision >= NEWS_SIGNALS_ADOPTION_MAX_REVISION:
            raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_REVISION_EXHAUSTED")
        source_by_ref = {item.source_ref: item for item in state.sources}
        artifact_by_ref = {item.artifact_ref: item for item in state.artifacts}
        preference_by_ref = {item.topic_ref: item for item in state.preferences}
        source_ref: str | None = None
        signal_ref: str | None = None
        action = request.action
        if action == "register_source":
            if len(state.sources) >= MAX_NEWS_SIGNAL_SOURCES:
                raise NewsSignalsAdoptionError(
                    "NEWS_SIGNALS_ADOPTION_SOURCE_LIMIT_EXCEEDED"
                )
            assert request.source_draft is not None
            source_ref = _hash_ref(
                "source-ref:q34",
                {
                    "idempotency_ref": idempotency_ref,
                    "safe_label": request.source_draft.safe_label,
                },
            )
            if source_ref in source_by_ref:
                raise NewsSignalsAdoptionConflict("NEWS_SIGNALS_ADOPTION_SOURCE_EXISTS")
        elif action == "update_source":
            assert request.target_ref is not None
            source_ref = request.target_ref
            if source_ref not in source_by_ref:
                raise NewsSignalsAdoptionConflict(
                    "NEWS_SIGNALS_ADOPTION_SOURCE_NOT_FOUND"
                )
        elif action in {"ingest_signal", "update_signal"}:
            assert request.signal_draft is not None
            source_ref = request.signal_draft.source_ref
            source = source_by_ref.get(source_ref)
            if source is None:
                raise NewsSignalsAdoptionConflict(
                    "NEWS_SIGNALS_ADOPTION_SOURCE_NOT_FOUND"
                )
            if source.state != "ready":
                raise NewsSignalsAdoptionConflict(
                    "NEWS_SIGNALS_ADOPTION_SOURCE_NOT_READY"
                )
            if action == "ingest_signal":
                if len(state.artifacts) >= NEWS_SIGNALS_ADOPTION_MAX_ARTIFACTS:
                    raise NewsSignalsAdoptionError(
                        "NEWS_SIGNALS_ADOPTION_ARTIFACT_LIMIT_EXCEEDED"
                    )
                signal_ref = _hash_ref(
                    "signal-ref:q34",
                    {"idempotency_ref": idempotency_ref},
                )
                if signal_ref in artifact_by_ref:
                    raise NewsSignalsAdoptionConflict(
                        "NEWS_SIGNALS_ADOPTION_SIGNAL_EXISTS"
                    )
            else:
                assert request.target_ref is not None
                signal_ref = request.target_ref
                prior = artifact_by_ref.get(signal_ref)
                if prior is None:
                    raise NewsSignalsAdoptionConflict(
                        "NEWS_SIGNALS_ADOPTION_SIGNAL_NOT_FOUND"
                    )
                if signal_ref in state.archived_refs:
                    raise NewsSignalsAdoptionConflict(
                        "NEWS_SIGNALS_ADOPTION_SIGNAL_ARCHIVED"
                    )
                if prior.source_ref != source_ref:
                    raise NewsSignalsAdoptionConflict(
                        "NEWS_SIGNALS_ADOPTION_SIGNAL_SOURCE_REBIND_BLOCKED"
                    )
        elif action in {"set_preference", "remove_preference"}:
            assert request.topic_ref is not None
            topic_refs = {item.topic_ref for item in state.artifacts}
            if request.topic_ref not in topic_refs:
                raise NewsSignalsAdoptionConflict(
                    "NEWS_SIGNALS_ADOPTION_TOPIC_NOT_FOUND"
                )
            if action == "set_preference":
                if (
                    request.topic_ref not in preference_by_ref
                    and len(state.preferences) >= NEWS_SIGNALS_ADOPTION_MAX_PREFERENCES
                ):
                    raise NewsSignalsAdoptionError(
                        "NEWS_SIGNALS_ADOPTION_PREFERENCE_LIMIT_EXCEEDED"
                    )
            elif request.topic_ref not in preference_by_ref:
                raise NewsSignalsAdoptionConflict(
                    "NEWS_SIGNALS_ADOPTION_PREFERENCE_NOT_FOUND"
                )
        elif action == "set_source_state":
            assert request.target_ref is not None
            source_ref = request.target_ref
            source = source_by_ref.get(source_ref)
            if source is None:
                raise NewsSignalsAdoptionConflict(
                    "NEWS_SIGNALS_ADOPTION_SOURCE_NOT_FOUND"
                )
            if source.state == request.source_state:
                raise NewsSignalsAdoptionConflict(
                    "NEWS_SIGNALS_ADOPTION_SOURCE_STATE_UNCHANGED"
                )
            if (source.state, request.source_state) not in {
                ("ready", "safe_disabled"),
                ("safe_disabled", "ready"),
            }:
                raise NewsSignalsAdoptionConflict(
                    "NEWS_SIGNALS_ADOPTION_SOURCE_STATE_TRANSITION_INVALID"
                )
        elif action in {"archive_signal", "recover_signal"}:
            assert request.target_ref is not None
            signal_ref = request.target_ref
            if signal_ref not in artifact_by_ref:
                raise NewsSignalsAdoptionConflict(
                    "NEWS_SIGNALS_ADOPTION_SIGNAL_NOT_FOUND"
                )
            archived = signal_ref in state.archived_refs
            if action == "archive_signal" and archived:
                raise NewsSignalsAdoptionConflict(
                    "NEWS_SIGNALS_ADOPTION_SIGNAL_ALREADY_ARCHIVED"
                )
            if action == "recover_signal" and not archived:
                raise NewsSignalsAdoptionConflict(
                    "NEWS_SIGNALS_ADOPTION_SIGNAL_NOT_ARCHIVED"
                )
        else:
            if not state.can_undo:
                raise NewsSignalsAdoptionConflict(
                    "NEWS_SIGNALS_ADOPTION_UNDO_UNAVAILABLE"
                )
        payload_fingerprint_ref = _hash_ref(
            "payload-fingerprint-ref:news-signals-adoption",
            {
                "request": request.model_dump(mode="json"),
                "idempotency_ref": idempotency_ref,
            },
        )
        current_state_ref = self._state_ref(state)
        preview_ref = _hash_ref(
            "preview-ref:news-signals-adoption",
            {
                "action": action,
                "current_state_ref": current_state_ref,
                "payload_fingerprint_ref": payload_fingerprint_ref,
                "resulting_revision": state.revision + 1,
                "source_ref": source_ref,
                "signal_ref": signal_ref,
            },
        )
        approval_ref = _hash_ref(
            "approval-ref:news-signals-adoption",
            {"preview_ref": preview_ref},
        )
        return NewsSignalsAdoptionMutationPreview(
            action=action,
            target_ref=request.target_ref,
            source_ref=source_ref,
            signal_ref=signal_ref,
            expected_revision=state.revision,
            resulting_revision=state.revision + 1,
            current_state_ref=current_state_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            preview_ref=preview_ref,
            approval_ref=approval_ref,
            safe_summary=self._preview_summary(action),
        )

    def _capture_preview_approval(
        self,
        preview: NewsSignalsAdoptionMutationPreview,
        *,
        idempotency_ref: str,
    ) -> NewsSignalsAdoptionApprovalReceipt:
        lease_store, request, lease_idempotency_ref, _, _, _ = self._lease_context(
            preview,
            idempotency_ref=idempotency_ref,
        )
        approval_ref = self._lease_approval_ref(
            approval_ref=preview.approval_ref,
            lease_idempotency_ref=lease_idempotency_ref,
        )
        try:
            requirement, grant = capture_authority_lease_backend_approval(
                lease_store,
                request,
                idempotency_ref=lease_idempotency_ref,
                approved_by_actor_id="operator-ref:local-user",
                approval_ref=approval_ref,
                approval_ttl_minutes=NEWS_SIGNALS_ADOPTION_APPROVAL_TTL_MINUTES,
            )
        except AuthorityLeaseApprovalConflictError as exc:
            raise NewsSignalsAdoptionConflict(
                "NEWS_SIGNALS_ADOPTION_APPROVAL_CONFLICT"
            ) from exc
        except AuthorityLeaseApprovalCapacityError as exc:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_APPROVAL_CAPACITY_EXHAUSTED"
            ) from exc
        except AuthorityLeaseApprovalStateError as exc:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_APPROVAL_STATE_INVALID"
            ) from exc
        if grant is None or grant.expires_at is None:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_EXACT_APPROVAL_REQUIRED"
            )
        approved_request = request.model_copy(update={"approval_ref": approval_ref})
        try:
            decision = AuthorityLeaseApprovalStore(lease_store.state_dir).validate(
                approved_request,
                requirement,
            )
        except AuthorityLeaseApprovalStateError as exc:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_APPROVAL_STATE_INVALID"
            ) from exc
        if decision is None or not decision.allowed:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_EXACT_APPROVAL_REQUIRED"
            )
        return NewsSignalsAdoptionApprovalReceipt(
            approval_ref=preview.approval_ref,
            approval_validation_ref=_approval_validation_ref(decision.decision_id),
            preview_ref=preview.preview_ref,
            idempotency_ref=idempotency_ref,
            expires_at=grant.expires_at,
        )

    def _authorize(
        self,
        preview: NewsSignalsAdoptionMutationPreview,
        *,
        idempotency_ref: str,
    ) -> tuple[AuthorityLeaseStore, AuthorityLease, str, str, datetime]:
        (
            lease_store,
            request,
            lease_idempotency_ref,
            resource_refs,
            action_ref,
            route_ref,
        ) = self._lease_context(preview, idempotency_ref=idempotency_ref)
        requirement = build_authority_lease_approval_requirement_for_request(
            request,
            idempotency_ref=lease_idempotency_ref,
        )
        lease_approval_ref = self._lease_approval_ref(
            approval_ref=preview.approval_ref,
            lease_idempotency_ref=lease_idempotency_ref,
        )
        approval_store = AuthorityLeaseApprovalStore(lease_store.state_dir)
        try:
            record = approval_store.resolve(lease_approval_ref)
        except AuthorityLeaseApprovalStateError as exc:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_AUTHORITY_STATE_INVALID"
            ) from exc
        if record is None:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_EXACT_APPROVAL_REQUIRED"
            )
        grant = record.grant
        if (
            grant.expires_at is None
            or grant.expires_at <= _utc_now()
            or grant.expires_at
            > grant.created_at
            + timedelta(minutes=NEWS_SIGNALS_ADOPTION_APPROVAL_TTL_MINUTES)
        ):
            raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_APPROVAL_EXPIRED")
        approved_request = request.model_copy(
            update={"approval_ref": lease_approval_ref}
        )
        try:
            approval_decision = approval_store.validate(
                approved_request,
                requirement,
            )
            lease, issue_receipt = issue_authority_lease_from_backend_state(
                lease_store,
                approved_request,
                idempotency_ref=lease_idempotency_ref,
            )
        except AuthorityLeaseApprovalStateError as exc:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_AUTHORITY_STATE_INVALID"
            ) from exc
        if (
            approval_decision is None
            or not approval_decision.allowed
            or lease is None
            or lease.status == "revoked"
            or issue_receipt.status not in {"issued", "replayed"}
        ):
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_EXACT_LEASE_ISSUANCE_DENIED"
            )
        decision = evaluate_authority_request(
            AuthorityActionRequest(
                action_ref=action_ref,
                domain=AuthorityDomain.workspace,
                capability=AuthorityCapability.write,
                safe_summary="Evaluate one exact local News and Signals change.",
                resource_refs=resource_refs,
                route_ref=route_ref,
                lane_ref=NEWS_SIGNALS_ADOPTION_AUTHORITY_LANE_REF,
                requested_mode=TrustMode.ask_before_changes,
                constraint_claims=[
                    AuthorityConstraintClaim(
                        kind=AuthorityConstraintKind.operation_budget,
                        value=1,
                    )
                ],
                rollback_ref=_hash_ref(
                    "rollback-ref:news-signals-adoption",
                    {"preview_ref": preview.preview_ref, "action": "undo"},
                ),
                safe_disable_ref=NEWS_SIGNALS_ADOPTION_SAFE_DISABLE_REF,
            ),
            [lease],
        )
        if decision.outcome not in {
            AuthorityDecisionOutcome.allow.value,
            AuthorityDecisionOutcome.ask.value,
        }:
            self._revoke_lease(lease_store, lease)
            raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_AUTHORITY_DENIED")
        return (
            lease_store,
            lease,
            decision.decision_ref,
            _approval_validation_ref(approval_decision.decision_id),
            grant.expires_at,
        )

    def _lease_context(
        self,
        preview: NewsSignalsAdoptionMutationPreview,
        *,
        idempotency_ref: str,
    ) -> tuple[
        AuthorityLeaseStore,
        AuthorityLeaseIssueRequest,
        str,
        list[str],
        str,
        str,
    ]:
        revision_ref = f"revision-ref:news-signals-adoption:{preview.expected_revision}"
        action_ref = f"action-ref:news-signals-adoption:{preview.action}"
        resource_refs = [
            NEWS_SIGNALS_ADOPTION_CONTRACT_REF,
            NEWS_SIGNALS_ADOPTION_WORKSPACE_REF,
            preview.preview_ref,
            preview.approval_ref,
            preview.payload_fingerprint_ref,
            idempotency_ref,
            action_ref,
            revision_ref,
        ]
        suffix = hashlib.sha256(
            preview.payload_fingerprint_ref.encode("utf-8")
        ).hexdigest()[:24]
        request = AuthorityLeaseIssueRequest(
            mode=TrustMode.ask_before_changes,
            scope=AuthorityLeaseScope.session,
            requested_domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
            authority_constraints=[
                AuthorityConstraint(
                    constraint_ref=(
                        "authority-constraint-ref:news-signals-adoption:"
                        f"resources:{suffix}"
                    ),
                    kind=AuthorityConstraintKind.resource_refs,
                    allowed_refs=resource_refs,
                    safe_summary=(
                        "Restrict one founder-private News change to exact preview, "
                        "approval, revision, payload, and idempotency refs."
                    ),
                ),
                AuthorityConstraint(
                    constraint_ref=(
                        "authority-constraint-ref:news-signals-adoption:"
                        f"budget:{suffix}"
                    ),
                    kind=AuthorityConstraintKind.operation_budget,
                    maximum=1,
                    safe_summary="Permit one exact local News state write.",
                ),
            ],
            constraints={
                "exact_lane_ref": NEWS_SIGNALS_ADOPTION_AUTHORITY_LANE_REF,
                "exact_action_ref": action_ref,
                "exact_route_ref": NEWS_SIGNALS_ADOPTION_ROUTE_REF,
                "exact_contract_ref": NEWS_SIGNALS_ADOPTION_CONTRACT_REF,
                "exact_preview_ref": preview.preview_ref,
                "exact_approval_ref": preview.approval_ref,
                "exact_payload_fingerprint_ref": preview.payload_fingerprint_ref,
                "exact_idempotency_ref": idempotency_ref,
                "exact_revision_ref": revision_ref,
                "exact_safe_disable_ref": NEWS_SIGNALS_ADOPTION_SAFE_DISABLE_REF,
            },
            decision_reason_ref=(
                "decision-reason-ref:news-signals-adoption:operator-confirmed"
            ),
            duration_minutes=NEWS_SIGNALS_ADOPTION_APPROVAL_TTL_MINUTES,
            safe_summary=(
                "Issue one exact operator-confirmed local News and Signals write lease."
            ),
        )
        lease_store = AuthorityLeaseStore(self.state_dir / "news_signals_authority")
        lease_idempotency_ref = _hash_ref(
            "idempotency-ref:news-signals-adoption-lease",
            {
                "idempotency_ref": idempotency_ref,
                "payload_fingerprint_ref": preview.payload_fingerprint_ref,
            },
        )
        return (
            lease_store,
            request,
            lease_idempotency_ref,
            resource_refs,
            action_ref,
            NEWS_SIGNALS_ADOPTION_ROUTE_REF,
        )

    @staticmethod
    def _lease_approval_ref(*, approval_ref: str, lease_idempotency_ref: str) -> str:
        return _hash_ref(
            "approval-ref:news-signals-adoption-lease-scope",
            {
                "approval_ref": approval_ref,
                "lease_idempotency_ref": lease_idempotency_ref,
            },
        )

    @staticmethod
    def _revoke_lease(lease_store: AuthorityLeaseStore, lease: AuthorityLease) -> bool:
        if lease.status == "revoked":
            return True
        try:
            from ultimate_ai_agent.core.authority import AuthorityLeaseRevokeRequest

            lease_store.revoke_lease(
                AuthorityLeaseRevokeRequest(
                    lease_ref=lease.lease_ref,
                    decision_reason_ref=(
                        "decision-reason-ref:news-signals-adoption:local-write-failed"
                    ),
                    safe_summary=(
                        "Revoke the exact News and Signals lease after local "
                        "persistence failed."
                    ),
                ),
                idempotency_ref=_hash_ref(
                    "idempotency-ref:news-signals-adoption-lease-revoke",
                    {"lease_ref": lease.lease_ref},
                ),
            )
        except Exception:  # pragma: no cover - bounded secondary failure
            return False
        return True

    def _apply_mutation(
        self,
        conn: sqlite3.Connection,
        state: _NewsSignalsSnapshot,
        request: NewsSignalsAdoptionMutationRequest,
        *,
        preview: NewsSignalsAdoptionMutationPreview,
        now: datetime,
    ) -> tuple[str | None, str | None]:
        source_by_ref = {item.source_ref: item for item in state.sources}
        artifact_by_ref = {item.artifact_ref: item for item in state.artifacts}
        source_ref = preview.source_ref
        signal_ref = preview.signal_ref
        if request.action in {"register_source", "update_source"}:
            assert request.source_draft is not None and source_ref is not None
            prior_source = source_by_ref.get(source_ref)
            source = NewsSignalSource(
                source_ref=source_ref,
                source_kind=request.source_draft.source_kind,
                safe_label=request.source_draft.safe_label,
                state=(prior_source.state if prior_source is not None else "ready"),
                observed_at=(
                    prior_source.observed_at
                    if prior_source is not None
                    else _utc_text(now)
                ),
                freshness_ttl_seconds=request.source_draft.freshness_ttl_seconds,
                adapter_ref=(
                    prior_source.adapter_ref
                    if prior_source is not None
                    else NEWS_SIGNALS_ADOPTION_ADAPTER_REF
                ),
                provenance_ref=(
                    prior_source.provenance_ref
                    if prior_source is not None
                    else NEWS_SIGNALS_ADOPTION_PROVENANCE_REF
                ),
                retention_ref=(
                    prior_source.retention_ref
                    if prior_source is not None
                    else NEWS_SIGNALS_ADOPTION_RETENTION_REF
                ),
                reason_refs=(
                    prior_source.reason_refs
                    if prior_source is not None
                    else (
                        "reason-ref:q34:operator-confirmed-local-intake",
                        preview.approval_ref,
                    )
                ),
            )
            self._write_source(conn, source)
            if request.action == "update_source":
                conn.execute(
                    "UPDATE news_signal_artifacts SET source_label = ? "
                    "WHERE source_ref = ?",
                    (source.safe_label, source.source_ref),
                )
        elif request.action in {"ingest_signal", "update_signal"}:
            assert request.signal_draft is not None and signal_ref is not None
            draft = request.signal_draft
            prior = artifact_by_ref.get(signal_ref)
            topic_ref = _hash_ref(
                "topic-ref:q34", {"safe_label": draft.topic_label.casefold()}
            )
            cluster_ref = _hash_ref(
                "cluster-ref:q34", {"safe_label": draft.cluster_label.casefold()}
            )
            claim_ref = (
                prior.claim_ref
                if prior is not None and draft.claim_label is None
                else _hash_ref(
                    "claim-ref:q34",
                    {"safe_label": str(draft.claim_label).casefold()},
                )
            )
            source_revision_ref = _hash_ref(
                "source-revision-ref:q34",
                {
                    "signal_ref": signal_ref,
                    "after_revision": preview.resulting_revision,
                    "payload_fingerprint_ref": preview.payload_fingerprint_ref,
                },
            )
            artifact = NewsSignalArtifact(
                artifact_ref=signal_ref,
                source_ref=draft.source_ref,
                source_revision_ref=source_revision_ref,
                content_digest_ref=_hash_ref(
                    "content-digest-ref:q34",
                    {"title": draft.title, "safe_summary": draft.safe_summary},
                ),
                cluster_ref=cluster_ref,
                claim_ref=claim_ref,
                title=draft.title,
                safe_summary=draft.safe_summary,
                source_label=source_by_ref[draft.source_ref].safe_label,
                topic_ref=topic_ref,
                published_at=_utc_text(
                    _parse_timestamp(draft.published_at, "published_at")
                ),
                observed_at=_utc_text(now),
                confidence_percent=draft.confidence_percent,
                evidence_class=draft.evidence_class,
                claim_stance=draft.claim_stance,
                interest_refs=(
                    _hash_ref(
                        "interest-ref:q34",
                        {"topic_ref": topic_ref},
                    ),
                ),
                provenance_refs=(
                    _hash_ref(
                        "provenance-ref:q34",
                        {
                            "source_ref": draft.source_ref,
                            "source_revision_ref": source_revision_ref,
                        },
                    ),
                    preview.approval_ref,
                ),
            )
            if prior is not None and prior.source_ref != artifact.source_ref:
                raise NewsSignalsAdoptionConflict(
                    "NEWS_SIGNALS_ADOPTION_SIGNAL_SOURCE_REBIND_BLOCKED"
                )
            self._write_artifact(conn, artifact)
            if (
                prior is not None
                and prior.topic_ref != artifact.topic_ref
                and not any(
                    item.artifact_ref != prior.artifact_ref
                    and item.topic_ref == prior.topic_ref
                    for item in state.artifacts
                )
            ):
                conn.execute(
                    "DELETE FROM news_signal_preferences WHERE topic_ref = ?",
                    (prior.topic_ref,),
                )
        elif request.action == "set_preference":
            assert request.topic_ref is not None
            assert request.preference_weight is not None
            preference = NewsSignalPreference(
                topic_ref=request.topic_ref,
                weight=request.preference_weight,
                preference_ref=_hash_ref(
                    "preference-ref:q34",
                    {
                        "topic_ref": request.topic_ref,
                        "weight": request.preference_weight,
                    },
                ),
            )
            conn.execute(
                """
                INSERT INTO news_signal_preferences(topic_ref, weight, preference_ref)
                VALUES (?, ?, ?)
                ON CONFLICT(topic_ref) DO UPDATE SET
                    weight=excluded.weight,
                    preference_ref=excluded.preference_ref
                """,
                (preference.topic_ref, preference.weight, preference.preference_ref),
            )
        elif request.action == "remove_preference":
            assert request.topic_ref is not None
            conn.execute(
                "DELETE FROM news_signal_preferences WHERE topic_ref = ?",
                (request.topic_ref,),
            )
        elif request.action == "set_source_state":
            assert request.target_ref is not None and request.source_state is not None
            source = source_by_ref[request.target_ref]
            self._write_source(
                conn,
                NewsSignalSource(
                    **{
                        **asdict(source),
                        "state": request.source_state,
                        "observed_at": _utc_text(now),
                        "reason_refs": (
                            source.reason_refs
                            if len(source.reason_refs) >= 24
                            else tuple(
                                dict.fromkeys(
                                    (
                                        *source.reason_refs,
                                        "reason-ref:q34:operator-confirmed-source-state",
                                    )
                                )
                            )
                        ),
                    }
                ),
            )
        elif request.action in {"archive_signal", "recover_signal"}:
            assert request.target_ref is not None
            conn.execute(
                """
                INSERT INTO news_signal_archives(artifact_ref, archived)
                VALUES (?, ?)
                ON CONFLICT(artifact_ref) DO UPDATE SET archived=excluded.archived
                """,
                (request.target_ref, request.action == "archive_signal"),
            )
        else:
            self._restore_undo_snapshot(
                conn,
                expected_snapshot_ref=state.undo_snapshot_ref,
                expected_state_ref=self._state_ref(state),
            )
        return source_ref, signal_ref

    def _store_undo_snapshot(
        self,
        conn: sqlite3.Connection,
        state: _NewsSignalsSnapshot,
        action: MutationAction,
    ) -> None:
        if action == "undo":
            return
        payload = self._snapshot_payload(state)
        encoded = _canonical_json(payload)
        if len(encoded) > NEWS_SIGNALS_ADOPTION_MAX_UNDO_BYTES:
            raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_UNDO_SIZE_LIMIT")
        conn.execute(
            """
            INSERT INTO news_signals_adoption_undo(singleton, snapshot_json)
            VALUES (1, ?)
            ON CONFLICT(singleton) DO UPDATE SET
                snapshot_json=excluded.snapshot_json,
                expected_state_ref=NULL
            """,
            (encoded.decode("utf-8"),),
        )

    def _bind_undo_snapshot(
        self,
        conn: sqlite3.Connection,
        *,
        expected_state_ref: str,
    ) -> None:
        _validate_ref(expected_state_ref, "expected_state_ref")
        updated = conn.execute(
            "UPDATE news_signals_adoption_undo SET expected_state_ref = ? "
            "WHERE singleton = 1",
            (expected_state_ref,),
        ).rowcount
        if updated != 1:
            raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_UNDO_STATE_INVALID")

    def _restore_undo_snapshot(
        self,
        conn: sqlite3.Connection,
        *,
        expected_snapshot_ref: str | None,
        expected_state_ref: str,
    ) -> None:
        row = conn.execute(
            "SELECT snapshot_json, expected_state_ref "
            "FROM news_signals_adoption_undo WHERE singleton = 1"
        ).fetchone()
        if row is None:
            raise NewsSignalsAdoptionConflict("NEWS_SIGNALS_ADOPTION_UNDO_UNAVAILABLE")
        snapshot_json = row["snapshot_json"]
        if (
            expected_snapshot_ref is None
            or self._undo_snapshot_ref(snapshot_json) != expected_snapshot_ref
        ):
            raise NewsSignalsAdoptionConflict(
                "NEWS_SIGNALS_ADOPTION_UNDO_SNAPSHOT_MISMATCH"
            )
        if row["expected_state_ref"] != expected_state_ref:
            raise NewsSignalsAdoptionConflict(
                "NEWS_SIGNALS_ADOPTION_UNDO_STATE_MISMATCH"
            )
        sources, artifacts, preferences, archived_refs = self._decode_undo_snapshot(
            snapshot_json
        )
        conn.execute("DELETE FROM news_signal_archives")
        conn.execute("DELETE FROM news_signal_preferences")
        conn.execute("DELETE FROM news_signal_artifacts")
        conn.execute("DELETE FROM news_signal_sources")
        for source in sources:
            self._write_source(conn, source)
        for artifact in artifacts:
            self._write_artifact(conn, artifact)
        for preference in preferences:
            conn.execute(
                "INSERT INTO news_signal_preferences VALUES (?, ?, ?)",
                (
                    preference.topic_ref,
                    preference.weight,
                    preference.preference_ref,
                ),
            )
        for artifact_ref in archived_refs:
            _validate_ref(artifact_ref, "artifact_ref")
            conn.execute(
                "INSERT INTO news_signal_archives VALUES (?, 1)",
                (artifact_ref,),
            )
        conn.execute("DELETE FROM news_signals_adoption_undo WHERE singleton = 1")

    @staticmethod
    def _write_source(conn: sqlite3.Connection, source: NewsSignalSource) -> None:
        conn.execute(
            """
            INSERT INTO news_signal_sources (
                source_ref, source_kind, safe_label, state, observed_at,
                freshness_ttl_seconds, adapter_ref, provenance_ref,
                retention_ref, reason_refs_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_ref) DO UPDATE SET
                source_kind=excluded.source_kind,
                safe_label=excluded.safe_label,
                state=excluded.state,
                observed_at=excluded.observed_at,
                freshness_ttl_seconds=excluded.freshness_ttl_seconds,
                adapter_ref=excluded.adapter_ref,
                provenance_ref=excluded.provenance_ref,
                retention_ref=excluded.retention_ref,
                reason_refs_json=excluded.reason_refs_json
            """,
            (
                source.source_ref,
                source.source_kind,
                source.safe_label,
                source.state,
                source.observed_at,
                source.freshness_ttl_seconds,
                source.adapter_ref,
                source.provenance_ref,
                source.retention_ref,
                json.dumps(list(source.reason_refs), separators=(",", ":")),
            ),
        )

    @staticmethod
    def _write_artifact(conn: sqlite3.Connection, artifact: NewsSignalArtifact) -> None:
        conn.execute(
            """
            INSERT INTO news_signal_artifacts (
                artifact_ref, source_ref, source_revision_ref,
                content_digest_ref, cluster_ref, claim_ref, title,
                safe_summary, source_label, topic_ref, published_at,
                observed_at, confidence_percent, evidence_class,
                claim_stance, interest_refs_json, provenance_refs_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(artifact_ref) DO UPDATE SET
                source_revision_ref=excluded.source_revision_ref,
                content_digest_ref=excluded.content_digest_ref,
                cluster_ref=excluded.cluster_ref,
                claim_ref=excluded.claim_ref,
                title=excluded.title,
                safe_summary=excluded.safe_summary,
                source_label=excluded.source_label,
                topic_ref=excluded.topic_ref,
                published_at=excluded.published_at,
                observed_at=excluded.observed_at,
                confidence_percent=excluded.confidence_percent,
                evidence_class=excluded.evidence_class,
                claim_stance=excluded.claim_stance,
                interest_refs_json=excluded.interest_refs_json,
                provenance_refs_json=excluded.provenance_refs_json
            """,
            (
                artifact.artifact_ref,
                artifact.source_ref,
                artifact.source_revision_ref,
                artifact.content_digest_ref,
                artifact.cluster_ref,
                artifact.claim_ref,
                artifact.title,
                artifact.safe_summary,
                artifact.source_label,
                artifact.topic_ref,
                artifact.published_at,
                artifact.observed_at,
                artifact.confidence_percent,
                artifact.evidence_class,
                artifact.claim_stance,
                json.dumps(list(artifact.interest_refs), separators=(",", ":")),
                json.dumps(list(artifact.provenance_refs), separators=(",", ":")),
            ),
        )

    def _read_snapshot(self, conn: sqlite3.Connection) -> _NewsSignalsSnapshot:
        revision_row = conn.execute(
            "SELECT revision FROM news_signals_adoption_meta WHERE singleton = 1"
        ).fetchone()
        if revision_row is None:
            raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_METADATA_MISSING")
        try:
            revision = int(revision_row["revision"])
        except (TypeError, ValueError) as exc:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_REVISION_STATE_INVALID"
            ) from exc
        if not 0 <= revision <= NEWS_SIGNALS_ADOPTION_MAX_REVISION:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_REVISION_STATE_INVALID"
            )
        source_rows = conn.execute(
            "SELECT * FROM news_signal_sources ORDER BY source_ref LIMIT ?",
            (MAX_NEWS_SIGNAL_SOURCES + 1,),
        ).fetchall()
        artifact_rows = conn.execute(
            "SELECT * FROM news_signal_artifacts ORDER BY artifact_ref LIMIT ?",
            (NEWS_SIGNALS_ADOPTION_MAX_ARTIFACTS + 1,),
        ).fetchall()
        preference_rows = conn.execute(
            "SELECT * FROM news_signal_preferences ORDER BY topic_ref LIMIT ?",
            (NEWS_SIGNALS_ADOPTION_MAX_PREFERENCES + 1,),
        ).fetchall()
        archive_rows = conn.execute(
            "SELECT artifact_ref FROM news_signal_archives "
            "WHERE archived = 1 ORDER BY artifact_ref LIMIT ?",
            (NEWS_SIGNALS_ADOPTION_MAX_ARTIFACTS + 1,),
        ).fetchall()
        receipt_rows = conn.execute(
            """
            SELECT idempotency_ref, payload_fingerprint_ref, preview_ref,
                   approval_ref, receipt_json
            FROM news_signals_adoption_receipts
            ORDER BY idempotency_ref
            LIMIT ?
            """,
            (NEWS_SIGNALS_ADOPTION_MAX_RECEIPTS + 1,),
        ).fetchall()
        if (
            len(source_rows) > MAX_NEWS_SIGNAL_SOURCES
            or len(artifact_rows) > NEWS_SIGNALS_ADOPTION_MAX_ARTIFACTS
            or len(preference_rows) > NEWS_SIGNALS_ADOPTION_MAX_PREFERENCES
            or len(archive_rows) > NEWS_SIGNALS_ADOPTION_MAX_ARTIFACTS
            or len(receipt_rows) > NEWS_SIGNALS_ADOPTION_MAX_RECEIPTS
        ):
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_DATABASE_CAPACITY_INVALID"
            )
        try:
            for row in source_rows:
                if len(row["reason_refs_json"].encode("utf-8")) > (
                    NEWS_SIGNALS_ADOPTION_MAX_ROW_JSON_BYTES
                ):
                    raise ValueError("SOURCE_REASON_REFS_SIZE_INVALID")
            for row in artifact_rows:
                if any(
                    len(row[field].encode("utf-8"))
                    > NEWS_SIGNALS_ADOPTION_MAX_ROW_JSON_BYTES
                    for field in ("interest_refs_json", "provenance_refs_json")
                ):
                    raise ValueError("ARTIFACT_REFS_SIZE_INVALID")
            sources = tuple(
                NewsSignalSource(
                    source_ref=row["source_ref"],
                    source_kind=row["source_kind"],
                    safe_label=row["safe_label"],
                    state=row["state"],
                    observed_at=row["observed_at"],
                    freshness_ttl_seconds=row["freshness_ttl_seconds"],
                    adapter_ref=row["adapter_ref"],
                    provenance_ref=row["provenance_ref"],
                    retention_ref=row["retention_ref"],
                    reason_refs=tuple(json.loads(row["reason_refs_json"])),
                )
                for row in source_rows
            )
            artifacts = tuple(_artifact_from_row(row) for row in artifact_rows)
            preferences = tuple(
                NewsSignalPreference(
                    topic_ref=row["topic_ref"],
                    weight=row["weight"],
                    preference_ref=row["preference_ref"],
                )
                for row in preference_rows
            )
            for row in receipt_rows:
                self._receipt_from_row(row)
        except (
            AttributeError,
            RecursionError,
            TypeError,
            UnicodeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_DATABASE_ROW_INVALID"
            ) from exc
        archived_refs = frozenset(row["artifact_ref"] for row in archive_rows)
        artifact_refs = {item.artifact_ref for item in artifacts}
        source_refs = {item.source_ref for item in sources}
        topic_refs = {item.topic_ref for item in artifacts}
        if (
            not archived_refs.issubset(artifact_refs)
            or any(item.source_ref not in source_refs for item in artifacts)
            or any(item.topic_ref not in topic_refs for item in preferences)
        ):
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_RELATIONSHIP_STATE_INVALID"
            )
        undo_row = conn.execute(
            "SELECT snapshot_json, expected_state_ref, "
            "length(CAST(snapshot_json AS BLOB)) AS snapshot_bytes "
            "FROM news_signals_adoption_undo WHERE singleton = 1"
        ).fetchone()
        if (
            undo_row is not None
            and undo_row["snapshot_bytes"] > NEWS_SIGNALS_ADOPTION_MAX_UNDO_BYTES
        ):
            raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_UNDO_SIZE_LIMIT")
        undo_snapshot_ref = (
            self._validated_undo_snapshot_ref(undo_row["snapshot_json"])
            if undo_row is not None
            else None
        )
        state = _NewsSignalsSnapshot(
            revision=revision,
            sources=sources,
            artifacts=artifacts,
            preferences=preferences,
            archived_refs=archived_refs,
            undo_snapshot_ref=undo_snapshot_ref,
            can_undo=False,
        )
        expected_state_ref = (
            undo_row["expected_state_ref"] if undo_row is not None else None
        )
        if expected_state_ref is not None:
            try:
                _validate_ref(expected_state_ref, "expected_state_ref")
            except ValueError as exc:
                raise NewsSignalsAdoptionError(
                    "NEWS_SIGNALS_ADOPTION_UNDO_STATE_INVALID"
                ) from exc
            state = _NewsSignalsSnapshot(
                revision=state.revision,
                sources=state.sources,
                artifacts=state.artifacts,
                preferences=state.preferences,
                archived_refs=state.archived_refs,
                undo_snapshot_ref=state.undo_snapshot_ref,
                can_undo=expected_state_ref == self._state_ref(state),
            )
        return state

    @staticmethod
    def _snapshot_payload(state: _NewsSignalsSnapshot) -> dict[str, object]:
        return {
            "sources": [asdict(item) for item in state.sources],
            "artifacts": [asdict(item) for item in state.artifacts],
            "preferences": [asdict(item) for item in state.preferences],
            "archived_refs": sorted(state.archived_refs),
        }

    def _state_ref(self, state: _NewsSignalsSnapshot) -> str:
        return _hash_ref(
            "state-ref:news-signals-adoption",
            {
                "revision": state.revision,
                "undo_snapshot_ref": state.undo_snapshot_ref,
                **self._snapshot_payload(state),
            },
        )

    @staticmethod
    def _undo_snapshot_ref(snapshot_json: object) -> str:
        if not isinstance(snapshot_json, str):
            raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_UNDO_STATE_INVALID")
        try:
            encoded = snapshot_json.encode("utf-8")
        except UnicodeError as exc:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_UNDO_STATE_INVALID"
            ) from exc
        if len(encoded) > NEWS_SIGNALS_ADOPTION_MAX_UNDO_BYTES:
            raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_UNDO_SIZE_LIMIT")
        return _hash_ref(
            "undo-snapshot-ref:news-signals-adoption",
            {"snapshot_json": snapshot_json},
        )

    def _validated_undo_snapshot_ref(self, snapshot_json: object) -> str:
        snapshot_ref = self._undo_snapshot_ref(snapshot_json)
        assert isinstance(snapshot_json, str)
        self._decode_undo_snapshot(snapshot_json)
        return snapshot_ref

    @staticmethod
    def _decode_undo_snapshot(
        snapshot_json: str,
    ) -> tuple[
        tuple[NewsSignalSource, ...],
        tuple[NewsSignalArtifact, ...],
        tuple[NewsSignalPreference, ...],
        tuple[str, ...],
    ]:
        if _json_nesting_exceeds_limit(
            snapshot_json,
            maximum_depth=NEWS_SIGNALS_ADOPTION_MAX_UNDO_JSON_DEPTH,
        ):
            raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_UNDO_STATE_INVALID")
        try:
            payload = json.loads(snapshot_json)
        except (json.JSONDecodeError, RecursionError) as exc:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_UNDO_STATE_INVALID"
            ) from exc
        if not isinstance(payload, dict) or set(payload) != {
            "sources",
            "artifacts",
            "preferences",
            "archived_refs",
        }:
            raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_UNDO_STATE_INVALID")
        source_items = payload["sources"]
        artifact_items = payload["artifacts"]
        preference_items = payload["preferences"]
        archived_items = payload["archived_refs"]
        if (
            not isinstance(source_items, list)
            or len(source_items) > MAX_NEWS_SIGNAL_SOURCES
            or not isinstance(artifact_items, list)
            or len(artifact_items) > NEWS_SIGNALS_ADOPTION_MAX_ARTIFACTS
            or not isinstance(preference_items, list)
            or len(preference_items) > NEWS_SIGNALS_ADOPTION_MAX_PREFERENCES
            or not isinstance(archived_items, list)
            or len(archived_items) > NEWS_SIGNALS_ADOPTION_MAX_ARTIFACTS
        ):
            raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_UNDO_STATE_INVALID")
        try:
            sources = tuple(NewsSignalSource(**item) for item in source_items)
            artifacts = tuple(NewsSignalArtifact(**item) for item in artifact_items)
            preferences = tuple(
                NewsSignalPreference(**item) for item in preference_items
            )
            archived_refs = tuple(archived_items)
            for artifact_ref in archived_refs:
                _validate_ref(artifact_ref, "artifact_ref")
        except (TypeError, ValueError) as exc:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_UNDO_STATE_INVALID"
            ) from exc
        source_refs = {item.source_ref for item in sources}
        artifact_refs = {item.artifact_ref for item in artifacts}
        preference_topic_refs = {item.topic_ref for item in preferences}
        topic_refs = {item.topic_ref for item in artifacts}
        if (
            len(source_refs) != len(sources)
            or len(artifact_refs) != len(artifacts)
            or len(preference_topic_refs) != len(preferences)
            or len(set(archived_refs)) != len(archived_refs)
            or not set(archived_refs).issubset(artifact_refs)
            or any(item.source_ref not in source_refs for item in artifacts)
            or any(item.topic_ref not in topic_refs for item in preferences)
        ):
            raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_UNDO_STATE_INVALID")
        return sources, artifacts, preferences, archived_refs

    def _receipt_for_idempotency(
        self, conn: sqlite3.Connection, idempotency_ref: str
    ) -> NewsSignalsAdoptionMutationReceipt | None:
        row = conn.execute(
            """
            SELECT idempotency_ref, payload_fingerprint_ref, preview_ref,
                   approval_ref, receipt_json
            FROM news_signals_adoption_receipts
            WHERE idempotency_ref = ?
            """,
            (idempotency_ref,),
        ).fetchone()
        if row is None:
            return None
        return self._receipt_from_row(row)

    @staticmethod
    def _receipt_from_row(
        row: sqlite3.Row,
    ) -> NewsSignalsAdoptionMutationReceipt:
        try:
            receipt_json = row["receipt_json"]
            if (
                not isinstance(receipt_json, str)
                or len(receipt_json.encode("utf-8"))
                > NEWS_SIGNALS_ADOPTION_MAX_ROW_JSON_BYTES
                or _json_nesting_exceeds_limit(
                    receipt_json,
                    maximum_depth=NEWS_SIGNALS_ADOPTION_MAX_UNDO_JSON_DEPTH,
                )
            ):
                raise ValueError("RECEIPT_JSON_SIZE_INVALID")
            receipt = NewsSignalsAdoptionMutationReceipt.model_validate_json(
                receipt_json
            )
        except (
            AttributeError,
            RecursionError,
            TypeError,
            UnicodeError,
            ValueError,
        ) as exc:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_RECEIPT_STATE_INVALID"
            ) from exc
        if receipt.replayed:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_RECEIPT_STATE_INVALID"
            )
        if (
            row["idempotency_ref"] != receipt.idempotency_ref
            or row["payload_fingerprint_ref"] != receipt.payload_fingerprint_ref
            or row["preview_ref"] != receipt.preview_ref
            or row["approval_ref"] != receipt.approval_ref
        ):
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_RECEIPT_STATE_INVALID"
            )
        return receipt

    def _insert_receipt(
        self,
        conn: sqlite3.Connection,
        receipt: NewsSignalsAdoptionMutationReceipt,
    ) -> None:
        receipt_json = receipt.model_dump_json()
        if len(receipt_json.encode("utf-8")) > NEWS_SIGNALS_ADOPTION_MAX_ROW_JSON_BYTES:
            raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_RECEIPT_SIZE_LIMIT")
        count = conn.execute(
            "SELECT COUNT(*) FROM news_signals_adoption_receipts"
        ).fetchone()[0]
        maximum_before_insert = (
            NEWS_SIGNALS_ADOPTION_MAX_RECEIPTS
            if receipt.action == "undo"
            else NEWS_SIGNALS_ADOPTION_MAX_RECEIPTS - 1
        )
        if count >= maximum_before_insert:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_RECEIPT_CAPACITY_EXHAUSTED"
            )
        conn.execute(
            """
            INSERT INTO news_signals_adoption_receipts(
                idempotency_ref, payload_fingerprint_ref, preview_ref,
                approval_ref, receipt_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                receipt.idempotency_ref,
                receipt.payload_fingerprint_ref,
                receipt.preview_ref,
                receipt.approval_ref,
                receipt_json,
            ),
        )

    def _validate_receipt_replay(
        self,
        receipt: NewsSignalsAdoptionMutationReceipt,
        *,
        request: NewsSignalsAdoptionCommitRequest,
        idempotency_ref: str,
    ) -> NewsSignalsAdoptionMutationReceipt:
        payload_fingerprint_ref = _hash_ref(
            "payload-fingerprint-ref:news-signals-adoption",
            {
                "request": request.mutation.model_dump(mode="json"),
                "idempotency_ref": idempotency_ref,
            },
        )
        expected_source_ref: str | None = None
        expected_signal_ref: str | None = None
        mutation = request.mutation
        if mutation.action == "register_source":
            assert mutation.source_draft is not None
            expected_source_ref = _hash_ref(
                "source-ref:q34",
                {
                    "idempotency_ref": idempotency_ref,
                    "safe_label": mutation.source_draft.safe_label,
                },
            )
        elif mutation.action in {"update_source", "set_source_state"}:
            expected_source_ref = mutation.target_ref
        elif mutation.action == "ingest_signal":
            assert mutation.signal_draft is not None
            expected_source_ref = mutation.signal_draft.source_ref
            expected_signal_ref = _hash_ref(
                "signal-ref:q34",
                {"idempotency_ref": idempotency_ref},
            )
        elif mutation.action == "update_signal":
            assert mutation.signal_draft is not None
            expected_source_ref = mutation.signal_draft.source_ref
            expected_signal_ref = mutation.target_ref
        elif mutation.action in {"archive_signal", "recover_signal"}:
            expected_signal_ref = mutation.target_ref
        if (
            receipt.payload_fingerprint_ref != payload_fingerprint_ref
            or receipt.preview_ref != request.preview_ref
            or receipt.approval_ref != request.approval_ref
            or receipt.action != mutation.action
            or receipt.target_ref != mutation.target_ref
            or receipt.source_ref != expected_source_ref
            or receipt.signal_ref != expected_signal_ref
        ):
            raise NewsSignalsAdoptionConflict(
                "NEWS_SIGNALS_ADOPTION_IDEMPOTENCY_CONFLICT"
            )
        return receipt.model_copy(update={"replayed": True})

    def _replay_approval(
        self,
        receipt: NewsSignalsAdoptionMutationReceipt,
        *,
        request: NewsSignalsAdoptionApprovalCaptureRequest,
        idempotency_ref: str,
    ) -> NewsSignalsAdoptionApprovalReceipt:
        self._validate_receipt_replay(
            receipt,
            request=NewsSignalsAdoptionCommitRequest(
                mutation=request.mutation,
                preview_ref=request.preview_ref,
                approval_ref=request.approval_ref,
            ),
            idempotency_ref=idempotency_ref,
        )
        return NewsSignalsAdoptionApprovalReceipt(
            approval_ref=receipt.approval_ref,
            approval_validation_ref=receipt.approval_validation_ref,
            preview_ref=receipt.preview_ref,
            idempotency_ref=idempotency_ref,
            expires_at=receipt.approval_expires_at,
        )

    def _connect(self) -> sqlite3.Connection:
        self._validate_existing_database_files()
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def _safe_connection(self) -> Iterator[sqlite3.Connection]:
        try:
            with self._connect() as conn:
                yield conn
        except NewsSignalsAdoptionError:
            raise
        except (OSError, sqlite3.DatabaseError) as exc:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_DATABASE_STATE_INVALID"
            ) from exc

    def _ensure_adoption_schema(self) -> None:
        with self._safe_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS news_signal_preferences (
                    topic_ref TEXT PRIMARY KEY,
                    weight INTEGER NOT NULL,
                    preference_ref TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS news_signal_archives (
                    artifact_ref TEXT PRIMARY KEY,
                    archived INTEGER NOT NULL CHECK(archived IN (0, 1)),
                    FOREIGN KEY(artifact_ref) REFERENCES news_signal_artifacts(artifact_ref)
                );
                CREATE TABLE IF NOT EXISTS news_signals_adoption_meta (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                    revision INTEGER NOT NULL
                );
                INSERT OR IGNORE INTO news_signals_adoption_meta(singleton, revision)
                VALUES (1, 0);
                CREATE TABLE IF NOT EXISTS news_signals_adoption_undo (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                    snapshot_json TEXT NOT NULL,
                    expected_state_ref TEXT
                );
                CREATE TABLE IF NOT EXISTS news_signals_adoption_receipts (
                    idempotency_ref TEXT PRIMARY KEY,
                    payload_fingerprint_ref TEXT NOT NULL,
                    preview_ref TEXT NOT NULL,
                    approval_ref TEXT NOT NULL,
                    receipt_json TEXT NOT NULL
                );
                """
            )
            undo_columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(news_signals_adoption_undo)"
                ).fetchall()
            }
            if "expected_state_ref" not in undo_columns:
                conn.execute(
                    "ALTER TABLE news_signals_adoption_undo "
                    "ADD COLUMN expected_state_ref TEXT"
                )
        self._harden_database_files()

    def _ensure_private_storage(self) -> None:
        try:
            if os.path.lexists(self.state_dir):
                metadata = self.state_dir.lstat()
                if self.state_dir.is_symlink() or not stat.S_ISDIR(metadata.st_mode):
                    raise NewsSignalsAdoptionError(
                        "NEWS_SIGNALS_ADOPTION_STATE_DIRECTORY_UNSAFE"
                    )
            self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            if os.name != "nt":
                os.chmod(self.state_dir, 0o700)
                metadata = self.state_dir.stat()
                if (
                    not stat.S_ISDIR(metadata.st_mode)
                    or metadata.st_mode & 0o077
                    or metadata.st_uid != os.getuid()
                ):
                    raise NewsSignalsAdoptionError(
                        "NEWS_SIGNALS_ADOPTION_STATE_DIRECTORY_UNSAFE"
                    )
        except NewsSignalsAdoptionError:
            raise
        except OSError as exc:
            raise NewsSignalsAdoptionError(
                "NEWS_SIGNALS_ADOPTION_STATE_DIRECTORY_UNSAFE"
            ) from exc

    def _harden_database_files(self) -> None:
        if os.name == "nt":
            return
        for path in (
            self.db_path,
            Path(f"{self.db_path}-wal"),
            Path(f"{self.db_path}-shm"),
            Path(f"{self.db_path}-journal"),
        ):
            if not os.path.lexists(path):
                continue
            try:
                metadata = path.lstat()
                if (
                    path.is_symlink()
                    or not stat.S_ISREG(metadata.st_mode)
                    or metadata.st_nlink != 1
                    or metadata.st_uid != os.getuid()
                ):
                    raise NewsSignalsAdoptionError(
                        "NEWS_SIGNALS_ADOPTION_DATABASE_FILE_UNSAFE"
                    )
                os.chmod(path, 0o600)
                if path.stat().st_mode & 0o077:
                    raise NewsSignalsAdoptionError(
                        "NEWS_SIGNALS_ADOPTION_DATABASE_FILE_UNSAFE"
                    )
            except OSError as exc:
                raise NewsSignalsAdoptionError(
                    "NEWS_SIGNALS_ADOPTION_DATABASE_FILE_UNSAFE"
                ) from exc

    def _validate_existing_database_files(self) -> None:
        if os.name == "nt":
            return
        for path in (
            self.db_path,
            Path(f"{self.db_path}-wal"),
            Path(f"{self.db_path}-shm"),
            Path(f"{self.db_path}-journal"),
        ):
            if not os.path.lexists(path):
                continue
            try:
                metadata = path.lstat()
            except OSError as exc:
                raise NewsSignalsAdoptionError(
                    "NEWS_SIGNALS_ADOPTION_DATABASE_FILE_UNSAFE"
                ) from exc
            if (
                path.is_symlink()
                or not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or metadata.st_uid != os.getuid()
            ):
                raise NewsSignalsAdoptionError(
                    "NEWS_SIGNALS_ADOPTION_DATABASE_FILE_UNSAFE"
                )

    @staticmethod
    def _preview_summary(action: MutationAction) -> str:
        summaries = {
            "register_source": "Register one local redacted-artifact source.",
            "update_source": "Update one local source label, kind, and freshness window.",
            "ingest_signal": "Add one already-redacted local source artifact.",
            "update_signal": "Correct one already-redacted local source artifact.",
            "set_preference": "Set one inspectable topic ranking preference.",
            "remove_preference": "Remove one topic ranking preference.",
            "set_source_state": "Safely disable or recover one local source.",
            "archive_signal": "Archive one local source artifact.",
            "recover_signal": "Recover one archived local source artifact.",
            "undo": "Restore the prior bounded local News snapshot.",
        }
        return summaries[action]

    @staticmethod
    def _next_safe_action(
        state: _NewsSignalsSnapshot,
        summary: dict[str, object],
    ) -> str:
        if not state.sources:
            return "Register the first local redacted-artifact source."
        if not state.artifacts:
            return "Add the first already-redacted signal from a ready local source."
        if summary["status"] == "blocked_source_unavailable":
            return "Review source posture and recover only an authorized local source."
        return (
            "Inspect ranked evidence, tune an explicit topic preference, or review "
            "the bounded Today and Morning Briefing candidates."
        )
