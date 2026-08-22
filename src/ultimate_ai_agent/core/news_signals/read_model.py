from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Iterable, Literal

from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like


NEWS_SIGNALS_SCHEMA_VERSION = "uaa-news-signals-read-model.v1"
NEWS_SIGNALS_CONTRACT_REF = "contract-ref:queue-v2-q24-news-signals:v1"
NEWS_SIGNALS_ADAPTER_REF = (
    "connector-adapter-ref:q24:local-redacted-artifact-snapshot-v1"
)
NEWS_SIGNALS_STATE_DIR_ENV = "UAA_FOUNDER_LOOP_STATE_DIR"
DEFAULT_NEWS_SIGNALS_STATE_DIR = Path(".uaa") / "founder_loop"
MAX_NEWS_SIGNAL_SOURCES = 24

_SAFE_REF_RE = re.compile(r"^[a-z][a-z0-9-]*-ref:[a-z0-9][a-z0-9:-]{1,190}$")
_EMAIL_RE = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
_HOST_RE = re.compile(
    r"(?:\b[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+\b)|"
    r"(?:\b(?:\d{1,3}\.){3}\d{1,3}\b)",
    re.IGNORECASE,
)
_LOCAL_HOST_RE = re.compile(
    r"\b(?:localhost|localhost\.localdomain|ip6-localhost|ip6-loopback)\b",
    re.IGNORECASE,
)
_IPV6_CANDIDATE_RE = re.compile(
    r"(?<![a-z0-9])\[?([0-9a-f]*:[0-9a-f:]+)\]?(?![a-z0-9])",
    re.IGNORECASE,
)

SourceKind = Literal["official", "community", "rss", "public_social", "local"]
SourceState = Literal["ready", "blocked", "unknown", "revoked", "safe_disabled"]
EvidenceClass = Literal["primary", "corroborating", "community", "commentary"]
ClaimStance = Literal["supports", "disputes", "unknown"]


def _validate_ref(value: str, field_name: str) -> None:
    if not _SAFE_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name.upper()}_SAFE_REF_REQUIRED")


def _validate_refs(values: Iterable[str], field_name: str, *, limit: int = 24) -> None:
    refs = tuple(values)
    if len(refs) > limit or len(set(refs)) != len(refs):
        raise ValueError(f"{field_name.upper()}_BOUNDS_INVALID")
    for value in refs:
        _validate_ref(value, field_name)


def _validate_safe_text(value: str, field_name: str, *, maximum: int) -> None:
    if not value or len(value) > maximum or value != value.strip():
        raise ValueError(f"{field_name.upper()}_BOUNDS_INVALID")
    lowered = value.lower()
    if (
        "\n" in value
        or "\r" in value
        or "://" in value
        or "file:" in lowered
        or "/" in value
        or "\\" in value
        or _EMAIL_RE.search(value)
        or _HOST_RE.search(value)
        or _LOCAL_HOST_RE.search(value)
        or _contains_ipv6_address(value)
        or contains_secret_like(value)
    ):
        raise ValueError(f"{field_name.upper()}_REDACTION_REQUIRED")


def _contains_ipv6_address(value: str) -> bool:
    for match in _IPV6_CANDIDATE_RE.finditer(value):
        try:
            if isinstance(ipaddress.ip_address(match.group(1)), ipaddress.IPv6Address):
                return True
        except ValueError:
            continue
    return False


def _validate_timestamp(value: str, field_name: str) -> None:
    _parse_timestamp(value, field_name)


def _parse_timestamp(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name.upper()}_UTC_TIMESTAMP_REQUIRED") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name.upper()}_UTC_TIMESTAMP_REQUIRED")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class NewsSignalSource:
    source_ref: str
    source_kind: SourceKind
    safe_label: str
    state: SourceState
    observed_at: str | None
    freshness_ttl_seconds: int = 86_400
    adapter_ref: str = NEWS_SIGNALS_ADAPTER_REF
    provenance_ref: str = "provenance-ref:q24:local-redacted-artifact"
    retention_ref: str = "retention-ref:q24:bounded-metadata"
    reason_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.source_kind not in {
            "official",
            "community",
            "rss",
            "public_social",
            "local",
        }:
            raise ValueError("SOURCE_KIND_INVALID")
        if self.state not in {
            "ready",
            "blocked",
            "unknown",
            "revoked",
            "safe_disabled",
        }:
            raise ValueError("SOURCE_STATE_INVALID")
        for field_name in (
            "source_ref",
            "adapter_ref",
            "provenance_ref",
            "retention_ref",
        ):
            _validate_ref(str(getattr(self, field_name)), field_name)
        _validate_safe_text(self.safe_label, "safe_label", maximum=80)
        _validate_refs(self.reason_refs, "reason_refs")
        if self.observed_at is not None:
            _validate_timestamp(self.observed_at, "observed_at")
        if not 300 <= self.freshness_ttl_seconds <= 604_800:
            raise ValueError("FRESHNESS_TTL_SECONDS_BOUNDS_INVALID")


@dataclass(frozen=True)
class NewsSignalArtifact:
    artifact_ref: str
    source_ref: str
    source_revision_ref: str
    content_digest_ref: str
    cluster_ref: str
    claim_ref: str
    title: str
    safe_summary: str
    source_label: str
    topic_ref: str
    published_at: str
    observed_at: str
    confidence_percent: int
    evidence_class: EvidenceClass
    claim_stance: ClaimStance = "unknown"
    interest_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.evidence_class not in {
            "primary",
            "corroborating",
            "community",
            "commentary",
        }:
            raise ValueError("EVIDENCE_CLASS_INVALID")
        if self.claim_stance not in {"supports", "disputes", "unknown"}:
            raise ValueError("CLAIM_STANCE_INVALID")
        for field_name in (
            "artifact_ref",
            "source_ref",
            "source_revision_ref",
            "content_digest_ref",
            "cluster_ref",
            "claim_ref",
            "topic_ref",
        ):
            _validate_ref(str(getattr(self, field_name)), field_name)
        _validate_safe_text(self.title, "title", maximum=140)
        _validate_safe_text(self.safe_summary, "safe_summary", maximum=320)
        _validate_safe_text(self.source_label, "source_label", maximum=80)
        _validate_timestamp(self.published_at, "published_at")
        _validate_timestamp(self.observed_at, "observed_at")
        if not 0 <= self.confidence_percent <= 100:
            raise ValueError("CONFIDENCE_PERCENT_BOUNDS_INVALID")
        _validate_refs(self.interest_refs, "interest_refs", limit=12)
        _validate_refs(self.provenance_refs, "provenance_refs", limit=24)
        if not self.provenance_refs:
            raise ValueError("PROVENANCE_REFS_REQUIRED")


@dataclass(frozen=True)
class NewsSignalPreference:
    topic_ref: str
    weight: int
    preference_ref: str

    def __post_init__(self) -> None:
        _validate_ref(self.topic_ref, "topic_ref")
        _validate_ref(self.preference_ref, "preference_ref")
        if not -20 <= self.weight <= 20:
            raise ValueError("PREFERENCE_WEIGHT_BOUNDS_INVALID")


def _freshness_state(
    *, published_at: str, now: datetime, ttl_seconds: int
) -> Literal["fresh", "stale", "unknown"]:
    published = _parse_timestamp(published_at, "published_at")
    age_seconds = (now - published).total_seconds()
    if age_seconds < -300:
        return "unknown"
    return "fresh" if age_seconds <= ttl_seconds else "stale"


def _confidence_state(percent: int) -> Literal["high", "medium", "low"]:
    if percent >= 80:
        return "high"
    if percent >= 60:
        return "medium"
    return "low"


def _score(
    artifact: NewsSignalArtifact,
    *,
    source: NewsSignalSource,
    freshness: str,
    preference_weights: dict[str, int],
) -> tuple[int, list[str]]:
    score = artifact.confidence_percent
    reasons = [
        f"rank-reason-ref:q24:confidence-{_confidence_state(artifact.confidence_percent)}"
    ]
    if freshness == "fresh":
        score += 30
        reasons.append("rank-reason-ref:q24:fresh")
    elif freshness == "stale":
        score -= 25
        reasons.append("rank-reason-ref:q24:stale-penalty")
    else:
        score -= 40
        reasons.append("rank-reason-ref:q24:freshness-unknown-penalty")
    class_weight = {
        "primary": 20,
        "corroborating": 10,
        "community": 0,
        "commentary": -10,
    }[artifact.evidence_class]
    score += class_weight
    reasons.append(f"rank-reason-ref:q24:evidence-{artifact.evidence_class}")
    topic_weight = preference_weights.get(artifact.topic_ref, 0)
    if topic_weight:
        score += topic_weight
        reasons.append("rank-reason-ref:q24:explicit-topic-preference")
    if source.state != "ready":
        score -= 100
        reasons.append(f"rank-reason-ref:q24:source-{source.state}")
    return score, reasons


def build_news_signals_summary(
    *,
    sources: Iterable[NewsSignalSource],
    artifacts: Iterable[NewsSignalArtifact],
    preferences: Iterable[NewsSignalPreference] = (),
    now: datetime | None = None,
    limit: int = 20,
) -> dict[str, object]:
    """Build a deterministic, read-only projection from redacted artifacts."""

    if not 1 <= limit <= 100:
        raise ValueError("LIMIT_BOUNDS_INVALID")
    observed_now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    source_items = tuple(sources)
    artifact_items = tuple(artifacts)
    preference_items = tuple(preferences)
    source_by_ref = {source.source_ref: source for source in source_items}
    if len(source_by_ref) != len(source_items):
        raise ValueError("DUPLICATE_SOURCE_REF")
    if len(source_items) > MAX_NEWS_SIGNAL_SOURCES:
        raise ValueError("SOURCE_READINESS_LIMIT_EXCEEDED")
    if len({item.artifact_ref for item in artifact_items}) != len(artifact_items):
        raise ValueError("DUPLICATE_ARTIFACT_REF")
    preference_weights = {item.topic_ref: item.weight for item in preference_items}

    active_artifacts: list[NewsSignalArtifact] = []
    for artifact in artifact_items:
        if artifact.source_ref not in source_by_ref:
            raise ValueError("ARTIFACT_SOURCE_NOT_REGISTERED")
        if source_by_ref[artifact.source_ref].state == "ready":
            active_artifacts.append(artifact)

    stances_by_claim: dict[str, set[str]] = {}
    for artifact in active_artifacts:
        if artifact.claim_stance != "unknown":
            stances_by_claim.setdefault(artifact.claim_ref, set()).add(
                artifact.claim_stance
            )
    conflicting_claims = {
        claim_ref
        for claim_ref, stances in stances_by_claim.items()
        if {"supports", "disputes"}.issubset(stances)
    }

    ranked: list[tuple[int, NewsSignalArtifact, str, list[str]]] = []
    for artifact in active_artifacts:
        source = source_by_ref[artifact.source_ref]
        freshness = _freshness_state(
            published_at=artifact.published_at,
            now=observed_now,
            ttl_seconds=source.freshness_ttl_seconds,
        )
        score, reasons = _score(
            artifact,
            source=source,
            freshness=freshness,
            preference_weights=preference_weights,
        )
        if artifact.claim_ref in conflicting_claims:
            score -= 30
            reasons.append("rank-reason-ref:q24:conflicting-evidence-penalty")
        ranked.append((score, artifact, freshness, reasons))
    ranked.sort(key=lambda row: (-row[0], row[1].artifact_ref))

    cluster_coverage: dict[str, list[NewsSignalArtifact]] = {}
    for artifact in active_artifacts:
        cluster_coverage.setdefault(artifact.cluster_ref, []).append(artifact)
    deduplicated: list[dict[str, object]] = []
    seen_clusters: set[str] = set()
    for score, artifact, freshness, reasons in ranked:
        if artifact.cluster_ref in seen_clusters:
            continue
        seen_clusters.add(artifact.cluster_ref)
        source = source_by_ref[artifact.source_ref]
        coverage = sorted(
            {item.source_ref for item in cluster_coverage[artifact.cluster_ref]}
        )
        conflict_state = (
            "conflicting" if artifact.claim_ref in conflicting_claims else "none"
        )
        briefing_eligible = (
            source.state == "ready"
            and freshness == "fresh"
            and artifact.confidence_percent >= 60
            and conflict_state == "none"
        )
        deduplicated.append(
            {
                "signal_ref": artifact.artifact_ref,
                "cluster_ref": artifact.cluster_ref,
                "claim_ref": artifact.claim_ref,
                "title": artifact.title,
                "safe_summary": artifact.safe_summary,
                "source_ref": artifact.source_ref,
                "source_label": artifact.source_label,
                "source_kind": source.source_kind,
                "source_state": source.state,
                "source_revision_ref": artifact.source_revision_ref,
                "content_digest_ref": artifact.content_digest_ref,
                "topic_ref": artifact.topic_ref,
                "published_at": artifact.published_at,
                "observed_at": artifact.observed_at,
                "freshness_state": freshness,
                "confidence_percent": artifact.confidence_percent,
                "confidence_state": _confidence_state(artifact.confidence_percent),
                "evidence_class": artifact.evidence_class,
                "external_content_untrusted": True,
                "conflict_state": conflict_state,
                "coverage_source_refs": coverage,
                "coverage_count": len(coverage),
                "provenance_refs": list(artifact.provenance_refs),
                "rank_score": score,
                "rank_reason_refs": reasons,
                "briefing_candidate": briefing_eligible,
                "action_authority_granted": False,
            }
        )
    visible = deduplicated[:limit]

    ready_sources = [source for source in source_items if source.state == "ready"]
    if not source_items:
        status = "blocked_no_graduated_source"
    elif not ready_sources:
        status = "blocked_source_unavailable"
    elif not visible:
        status = "ready_empty"
    else:
        status = "ready"
    briefing_items = [item for item in deduplicated if item["briefing_candidate"]][:5]
    today_items = [
        item
        for item in deduplicated
        if item["freshness_state"] == "fresh"
        and item["source_state"] == "ready"
        and item["conflict_state"] == "none"
    ][:3]
    freshness_counts = {
        state: sum(item["freshness_state"] == state for item in visible)
        for state in ("fresh", "stale", "unknown")
    }
    source_readiness = [
        {
            **asdict(source),
            "reason_refs": list(source.reason_refs),
            "external_network_read_performed": False,
            "account_authority_granted": False,
        }
        for source in sorted(source_items, key=lambda item: item.source_ref)
    ]
    return {
        "schema_version": NEWS_SIGNALS_SCHEMA_VERSION,
        "contract_ref": NEWS_SIGNALS_CONTRACT_REF,
        "status": status,
        "backend_owned": True,
        "read_only": True,
        "local_artifact_snapshot_only": True,
        "external_content_untrusted": True,
        "live_fetch_enabled": False,
        "authenticated_source_enabled": False,
        "background_polling_enabled": False,
        "model_summarization_enabled": False,
        "connector_write_enabled": False,
        "action_authority_granted": False,
        "observed_at": observed_now.isoformat().replace("+00:00", "Z"),
        "source_readiness": source_readiness,
        "items": visible,
        "freshness_counts": freshness_counts,
        "conflicting_claim_refs": sorted(conflicting_claims),
        "today_projection": {
            "projection_ref": "projection-ref:q24:today",
            "item_refs": [str(item["signal_ref"]) for item in today_items],
            "bounded_limit": 3,
            "read_only": True,
        },
        "morning_briefing_projection": {
            "projection_ref": "projection-ref:q24:morning-briefing",
            "candidate_refs": [str(item["signal_ref"]) for item in briefing_items],
            "bounded_limit": 5,
            "review_required": True,
            "read_only": True,
        },
        "safe_summary": (
            "Backend-owned News and Signals projection from already-redacted "
            "local artifacts; external source content remains untrusted."
        ),
        "blocked_state_refs": (
            ["blocked-state-ref:q24:no-graduated-news-source"]
            if status == "blocked_no_graduated_source"
            else (
                ["blocked-state-ref:q24:source-unavailable"]
                if status == "blocked_source_unavailable"
                else []
            )
        ),
        "evidence_refs": [
            "evidence-ref:q24:safe-refs-and-bounded-summaries-only",
            "evidence-ref:q24:no-network-auth-model-write-or-action",
        ],
    }


class NewsSignalsRepository:
    """Local durable store for normalized, redacted source artifacts.

    Ingestion is intentionally a Python-core-only boundary.  Q24 exposes no
    mutation route and grants no source adapter or account authority.
    """

    def __init__(self, state_dir: Path, *, ensure_storage: bool = True) -> None:
        self.state_dir = state_dir
        self.db_path = state_dir / "news_signals.sqlite3"
        if ensure_storage:
            self._ensure_storage()

    @classmethod
    def from_env(cls, *, ensure_storage: bool = True) -> "NewsSignalsRepository":
        configured = os.environ.get(NEWS_SIGNALS_STATE_DIR_ENV)
        state_dir = Path(configured) if configured else DEFAULT_NEWS_SIGNALS_STATE_DIR
        return cls(state_dir, ensure_storage=ensure_storage)

    def upsert_source(self, source: NewsSignalSource) -> str:
        payload = json.dumps(list(source.reason_refs), separators=(",", ":"))
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT 1 FROM news_signal_sources WHERE source_ref = ?",
                (source.source_ref,),
            ).fetchone()
            if existing is None:
                source_count = conn.execute(
                    "SELECT COUNT(*) FROM news_signal_sources"
                ).fetchone()[0]
                if source_count >= MAX_NEWS_SIGNAL_SOURCES:
                    raise ValueError("SOURCE_READINESS_LIMIT_EXCEEDED")
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
                    payload,
                ),
            )
        return _receipt_ref(
            "source",
            json.dumps(asdict(source), sort_keys=True, separators=(",", ":")),
        )

    def ingest_artifact(
        self,
        artifact: NewsSignalArtifact,
        *,
        expected_current_source_revision_ref: str | None = None,
    ) -> str:
        if expected_current_source_revision_ref is not None:
            _validate_ref(
                expected_current_source_revision_ref,
                "expected_current_source_revision_ref",
            )
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            exists = conn.execute(
                "SELECT 1 FROM news_signal_sources WHERE source_ref = ?",
                (artifact.source_ref,),
            ).fetchone()
            if exists is None:
                raise ValueError("ARTIFACT_SOURCE_NOT_REGISTERED")
            prior = conn.execute(
                "SELECT * FROM news_signal_artifacts WHERE artifact_ref = ?",
                (artifact.artifact_ref,),
            ).fetchone()
            if prior is not None and prior["source_revision_ref"] == (
                artifact.source_revision_ref
            ):
                if _artifact_from_row(prior) != artifact:
                    raise ValueError("ARTIFACT_REVISION_CONFLICT")
                return _receipt_ref(
                    "artifact",
                    json.dumps(asdict(artifact), sort_keys=True, separators=(",", ":")),
                )
            if prior is not None:
                if prior["source_ref"] != artifact.source_ref:
                    raise ValueError("ARTIFACT_SOURCE_BINDING_CONFLICT")
                if expected_current_source_revision_ref is None:
                    raise ValueError("ARTIFACT_EXPECTED_CURRENT_REVISION_REQUIRED")
                if prior["source_revision_ref"] != (
                    expected_current_source_revision_ref
                ):
                    raise ValueError("ARTIFACT_STALE_REVISION_REPLAY")
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
                    source_ref=excluded.source_ref,
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
        return _receipt_ref(
            "artifact",
            json.dumps(asdict(artifact), sort_keys=True, separators=(",", ":")),
        )

    def summary(
        self,
        *,
        now: datetime | None = None,
        limit: int = 20,
        preferences: Iterable[NewsSignalPreference] = (),
    ) -> dict[str, object]:
        sources, artifacts = self._read_records()
        return build_news_signals_summary(
            sources=sources,
            artifacts=artifacts,
            preferences=preferences,
            now=now,
            limit=limit,
        )

    def _read_records(self) -> tuple[list[NewsSignalSource], list[NewsSignalArtifact]]:
        with self._connect() as conn:
            conn.execute("BEGIN")
            source_rows = conn.execute(
                "SELECT * FROM news_signal_sources ORDER BY source_ref"
            ).fetchall()
            artifact_rows = conn.execute(
                "SELECT * FROM news_signal_artifacts ORDER BY artifact_ref"
            ).fetchall()
        sources = [
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
        ]
        artifacts = [_artifact_from_row(row) for row in artifact_rows]
        return sources, artifacts

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_storage(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS news_signal_sources (
                    source_ref TEXT PRIMARY KEY,
                    source_kind TEXT NOT NULL,
                    safe_label TEXT NOT NULL,
                    state TEXT NOT NULL,
                    observed_at TEXT,
                    freshness_ttl_seconds INTEGER NOT NULL,
                    adapter_ref TEXT NOT NULL,
                    provenance_ref TEXT NOT NULL,
                    retention_ref TEXT NOT NULL,
                    reason_refs_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS news_signal_artifacts (
                    artifact_ref TEXT PRIMARY KEY,
                    source_ref TEXT NOT NULL,
                    source_revision_ref TEXT NOT NULL,
                    content_digest_ref TEXT NOT NULL,
                    cluster_ref TEXT NOT NULL,
                    claim_ref TEXT NOT NULL,
                    title TEXT NOT NULL,
                    safe_summary TEXT NOT NULL,
                    source_label TEXT NOT NULL,
                    topic_ref TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    confidence_percent INTEGER NOT NULL,
                    evidence_class TEXT NOT NULL,
                    claim_stance TEXT NOT NULL,
                    interest_refs_json TEXT NOT NULL,
                    provenance_refs_json TEXT NOT NULL,
                    FOREIGN KEY(source_ref) REFERENCES news_signal_sources(source_ref)
                );
                CREATE INDEX IF NOT EXISTS news_signal_artifacts_source_idx
                    ON news_signal_artifacts(source_ref);
                CREATE INDEX IF NOT EXISTS news_signal_artifacts_cluster_idx
                    ON news_signal_artifacts(cluster_ref);
                """
            )


def _receipt_ref(kind: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
    return f"receipt-ref:q24:{kind}:{digest}"


def _artifact_from_row(row: sqlite3.Row) -> NewsSignalArtifact:
    return NewsSignalArtifact(
        artifact_ref=row["artifact_ref"],
        source_ref=row["source_ref"],
        source_revision_ref=row["source_revision_ref"],
        content_digest_ref=row["content_digest_ref"],
        cluster_ref=row["cluster_ref"],
        claim_ref=row["claim_ref"],
        title=row["title"],
        safe_summary=row["safe_summary"],
        source_label=row["source_label"],
        topic_ref=row["topic_ref"],
        published_at=row["published_at"],
        observed_at=row["observed_at"],
        confidence_percent=row["confidence_percent"],
        evidence_class=row["evidence_class"],
        claim_stance=row["claim_stance"],
        interest_refs=tuple(json.loads(row["interest_refs_json"])),
        provenance_refs=tuple(json.loads(row["provenance_refs_json"])),
    )
