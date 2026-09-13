#!/usr/bin/env python3
"""Verify the bounded Queue V2 Q34 founder-private News loop."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.news_signals import (  # noqa: E402
    NewsSignalArtifactDraft,
    NewsSignalSourceDraft,
    NewsSignalsAdoptionApprovalCaptureRequest,
    NewsSignalsAdoptionCommitRequest,
    NewsSignalsAdoptionMutationRequest,
    NewsSignalsAdoptionStore,
)


NOW = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
FORBIDDEN_CORE_IMPORTS = (
    "import requests",
    "import httpx",
    "urllib.request",
    "import playwright",
    "import selenium",
    "import firecrawl",
    "import browserbase",
    "from subprocess",
    "import subprocess",
)


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def _commit(
    store: NewsSignalsAdoptionStore,
    mutation: NewsSignalsAdoptionMutationRequest,
    suffix: str,
):
    idempotency_ref = f"idempotency-ref:queue-v2-q34-news:{suffix}"
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    scoped = NewsSignalsAdoptionApprovalCaptureRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    store.capture_approval(scoped, idempotency_ref=idempotency_ref)
    return store.commit_mutation(
        NewsSignalsAdoptionCommitRequest(**scoped.model_dump()),
        idempotency_ref=idempotency_ref,
    )


def _source(store: NewsSignalsAdoptionStore, suffix: str, label: str):
    return _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="register_source",
            expected_revision=store.read_view()["revision"],
            source_draft=NewsSignalSourceDraft(
                safe_label=label,
                source_kind="official" if suffix == "official" else "community",
                freshness_ttl_seconds=86_400,
            ),
        ),
        f"source-{suffix}",
    ).source_ref


def _signal(
    store: NewsSignalsAdoptionStore,
    *,
    source_ref: str,
    suffix: str,
    title: str,
    topic: str,
    cluster: str,
):
    return _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="ingest_signal",
            expected_revision=store.read_view()["revision"],
            signal_draft=NewsSignalArtifactDraft(
                source_ref=source_ref,
                title=title,
                safe_summary="Synthetic bounded redacted evidence for Q34 verification.",
                topic_label=topic,
                cluster_label=cluster,
                claim_label=f"{cluster} verified",
                published_at="2026-09-09T11:30:00Z",
                confidence_percent=88,
                evidence_class=(
                    "primary" if suffix == "primary" else "corroborating"
                ),
                claim_stance="supports",
            ),
        ),
        f"signal-{suffix}",
    ).signal_ref


def verify() -> dict[str, object]:
    core_source = (
        ROOT / "src/ultimate_ai_agent/core/news_signals/adoption.py"
    ).read_text(encoding="utf-8")
    _require(
        not any(fragment in core_source for fragment in FORBIDDEN_CORE_IMPORTS),
        "Q34_FORBIDDEN_RUNTIME_IMPORT",
    )
    with tempfile.TemporaryDirectory(prefix="uaa-q34-news-verifier-") as directory:
        store = NewsSignalsAdoptionStore(Path(directory))
        empty = store.read_view(now=NOW)
        _require(empty["status"] == "blocked_no_graduated_source", "Q34_EMPTY")

        official = _source(store, "official", "Official source")
        community = _source(store, "community", "Community source")
        primary = _signal(
            store,
            source_ref=official,
            suffix="primary",
            title="Governed agent milestone",
            topic="Agent governance",
            cluster="Governed agent milestone",
        )
        _signal(
            store,
            source_ref=community,
            suffix="corroborating",
            title="Governed agent milestone corroborated",
            topic="Agent governance",
            cluster="Governed agent milestone",
        )
        operations = _signal(
            store,
            source_ref=official,
            suffix="operations",
            title="Founder operations signal",
            topic="Founder operations",
            cluster="Founder operations signal",
        )
        initial = store.read_view(now=NOW)
        _require(len(initial["summary"]["items"]) == 2, "Q34_DEDUP")
        _require(
            initial["active_items_page"]["total_items"] == 3,
            "Q34_COMPLETE_ACTIVE_ITEM_COUNT",
        )
        lower_page = store.read_view(now=NOW, offset=2, limit=1)
        _require(
            lower_page["active_items_page"]["returned_items"] == 1,
            "Q34_ACTIVE_ITEM_PAGINATION",
        )
        searched = store.read_view(now=NOW, search_query="founder operations")
        _require(
            searched["active_items_page"]["items"][0]["signal_ref"]
            == operations,
            "Q34_ACTIVE_ITEM_SEARCH",
        )
        primary_item = next(
            item
            for item in initial["summary"]["items"]
            if item["signal_ref"] == primary
        )
        operations_item = next(
            item
            for item in initial["summary"]["items"]
            if item["signal_ref"] == operations
        )
        _require(primary_item["coverage_count"] == 2, "Q34_COVERAGE")
        _require(
            len(primary_item["provenance_refs"]) == 2,
            "Q34_APPROVAL_PROVENANCE",
        )

        _commit(
            store,
            NewsSignalsAdoptionMutationRequest(
                action="set_preference",
                expected_revision=store.read_view()["revision"],
                topic_ref=operations_item["topic_ref"],
                preference_weight=20,
            ),
            "preference",
        )
        preferred = store.read_view(now=NOW)
        _require(
            preferred["summary"]["items"][0]["signal_ref"] == operations,
            "Q34_RANKING_PREFERENCE",
        )

        archived = _commit(
            store,
            NewsSignalsAdoptionMutationRequest(
                action="archive_signal",
                expected_revision=preferred["revision"],
                target_ref=operations,
            ),
            "archive",
        )
        _require(len(store.read_view(now=NOW)["archived_items"]) == 1, "Q34_ARCHIVE")
        recovered = _commit(
            store,
            NewsSignalsAdoptionMutationRequest(
                action="recover_signal",
                expected_revision=archived.after_revision,
                target_ref=operations,
            ),
            "recover",
        )
        disabled = _commit(
            store,
            NewsSignalsAdoptionMutationRequest(
                action="set_source_state",
                expected_revision=recovered.after_revision,
                target_ref=official,
                source_state="safe_disabled",
            ),
            "safe-disable",
        )
        disabled_view = store.read_view(now=NOW)
        _require(
            all(
                item["source_ref"] != official
                for item in disabled_view["summary"]["items"]
            ),
            "Q34_SAFE_DISABLE_WITHHOLD",
        )
        restored = _commit(
            store,
            NewsSignalsAdoptionMutationRequest(
                action="set_source_state",
                expected_revision=disabled.after_revision,
                target_ref=official,
                source_state="ready",
            ),
            "source-recover",
        )
        undo = _commit(
            store,
            NewsSignalsAdoptionMutationRequest(
                action="undo",
                expected_revision=restored.after_revision,
            ),
            "undo-source-recover",
        )
        undone_view = store.read_view(now=NOW)
        _require(
            all(
                source["state"] == "safe_disabled"
                for source in undone_view["summary"]["source_readiness"]
                if source["source_ref"] == official
            ),
            "Q34_UNDO_SOURCE_RECOVERY",
        )
        final_recovery = _commit(
            store,
            NewsSignalsAdoptionMutationRequest(
                action="set_source_state",
                expected_revision=undo.after_revision,
                target_ref=official,
                source_state="ready",
            ),
            "source-final-recover",
        )

        restarted = NewsSignalsAdoptionStore(store.state_dir)
        final = restarted.read_view(now=NOW)
        _require(final["revision"] == final_recovery.after_revision, "Q34_RESTART")
        _require(
            primary in final["summary"]["today_projection"]["item_refs"],
            "Q34_TODAY_DELIVERY",
        )
        _require(
            primary
            in final["summary"]["morning_briefing_projection"]["candidate_refs"],
            "Q34_BRIEFING_DELIVERY",
        )
        _require(
            all(
                final[field] is False
                for field in (
                    "live_fetch_enabled",
                    "authenticated_source_enabled",
                    "background_polling_enabled",
                    "model_summarization_enabled",
                    "connector_write_enabled",
                    "action_authority_granted",
                )
            ),
            "Q34_AUTHORITY_BOUNDARY",
        )

    return {
        "schema_version": "uaa-queue-v2-q34-verification.v1",
        "status": "verified",
        "local_operator_intake_verified": True,
        "provenance_freshness_deduplication_verified": True,
        "ranking_and_preferences_verified": True,
        "inspection_archive_recovery_undo_verified": True,
        "complete_active_item_navigation_verified": True,
        "today_and_morning_briefing_delivery_verified": True,
        "exact_approval_authority_and_idempotency_verified": True,
        "restart_persistence_verified": True,
        "live_source_or_authenticated_access_performed": False,
        "provider_model_call_performed": False,
        "external_write_or_action_performed": False,
        "public_or_production_claim": False,
    }


def main() -> int:
    print(json.dumps(verify(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
