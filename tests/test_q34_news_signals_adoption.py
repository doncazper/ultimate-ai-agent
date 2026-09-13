from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
import gc
import hashlib
import os
import sqlite3

import pytest

from ultimate_ai_agent.core.authority.approval_validation import (
    AuthorityLeaseApprovalStateError,
    AuthorityLeaseApprovalStore,
)
from ultimate_ai_agent.core.news_signals.adoption import (
    NEWS_SIGNALS_ADOPTION_MAX_RECEIPTS,
    NewsSignalArtifactDraft,
    NewsSignalSourceDraft,
    NewsSignalsAdoptionApprovalCaptureRequest,
    NewsSignalsAdoptionCommitRequest,
    NewsSignalsAdoptionConflict,
    NewsSignalsAdoptionError,
    NewsSignalsAdoptionMutationRequest,
    NewsSignalsAdoptionMutationReceipt,
    NewsSignalsAdoptionStore,
    _hash_ref,
    _mutation_receipt_ref,
)
from ultimate_ai_agent.core.news_signals.read_model import (
    NewsSignalSource,
    NewsSignalsRepository,
)


def _news_disk_fingerprint(state_dir):
    if not state_dir.exists():
        return {}
    return {
        str(path.relative_to(state_dir)): (
            path.stat().st_mode,
            hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None,
        )
        for path in (state_dir, *sorted(state_dir.rglob("*")))
    }


def _seed_q24_source(state_dir):
    repository = NewsSignalsRepository(state_dir)
    repository.upsert_source(
        NewsSignalSource(
            source_ref="source-ref:q24:preserved-admission",
            source_kind="official",
            safe_label="Existing reviewed source",
            state="ready",
            observed_at="2026-09-09T10:00:00Z",
            reason_refs=("reason-ref:q24:original-admission",),
        )
    )
    gc.collect()
    return repository


def test_fresh_inspection_preview_and_denied_commit_do_not_initialize_storage(tmp_path):
    state_dir = tmp_path / "uninitialized-news"
    store = NewsSignalsAdoptionStore(state_dir)
    assert not state_dir.exists()
    view = store.read_view()
    assert view["storage_status"] == "missing"
    assert view["summary"]["today_projection"]["storage_status"] == "missing"
    request = NewsSignalsAdoptionMutationRequest(
        action="register_source", expected_revision=0, source_draft=_source_draft()
    )
    key = "idempotency-ref:q34:test:missing-storage"
    preview = store.preview_mutation(request, idempotency_ref=key)
    assert "Initialize local News storage" in preview.safe_summary
    assert not state_dir.exists()
    with pytest.raises(NewsSignalsAdoptionError, match="EXACT_APPROVAL_REQUIRED"):
        store.commit_mutation(
            NewsSignalsAdoptionCommitRequest(
                mutation=request,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
            ),
            idempotency_ref=key,
        )
    assert not state_dir.exists()


@pytest.mark.parametrize("adopted", [False, True])
@pytest.mark.parametrize("live_wal", [False, True])
def test_read_and_preview_preserve_q24_or_adopted_files_and_live_wal(
    tmp_path, adopted, live_wal
):
    repository = _seed_q24_source(tmp_path)
    store = NewsSignalsAdoptionStore(tmp_path)
    if adopted:
        _register(store)
    gc.collect()
    writer = sqlite3.connect(repository.db_path)
    try:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute(
            "UPDATE news_signal_sources SET safe_label = ? WHERE source_ref = ?",
            ("Committed journal label", "source-ref:q24:preserved-admission"),
        )
        writer.commit()
        if not live_wal:
            writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            writer.close()
        if os.name != "nt" and not adopted:
            os.chmod(tmp_path, 0o755)
            os.chmod(repository.db_path, 0o644)
        before = _news_disk_fingerprint(tmp_path)
        reopened = NewsSignalsAdoptionStore(tmp_path)
        view = reopened.read_view(now=NOW)
        assert view["storage_status"] == ("ready" if adopted else "q24_only")
        source = next(
            item
            for item in view["summary"]["source_readiness"]
            if item["source_ref"] == "source-ref:q24:preserved-admission"
        )
        assert source["safe_label"] == "Committed journal label"
        assert source["reason_refs"] == ["reason-ref:q24:original-admission"]
        reopened.preview_mutation(
            NewsSignalsAdoptionMutationRequest(
                action="register_source",
                expected_revision=view["revision"],
                source_draft=_source_draft("Additional source"),
            ),
            idempotency_ref="idempotency-ref:q34:test:read-invariance",
        )
        assert _news_disk_fingerprint(tmp_path) == before
    finally:
        writer.close()


@pytest.mark.parametrize("existing_q24", [False, True])
def test_first_approved_commit_initializes_atomically_and_preserves_existing_data(
    tmp_path, existing_q24
):
    state_dir = tmp_path / "news"
    if existing_q24:
        _seed_q24_source(state_dir)
    store = NewsSignalsAdoptionStore(state_dir)
    mutation = NewsSignalsAdoptionMutationRequest(
        action="register_source", expected_revision=0, source_draft=_source_draft()
    )
    key = "idempotency-ref:q34:test:approved-bootstrap"
    preview = store.preview_mutation(mutation, idempotency_ref=key)
    exact = NewsSignalsAdoptionApprovalCaptureRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    store.capture_approval(exact, idempotency_ref=key)
    if existing_q24:
        with store._read_connection() as conn:
            assert store._storage_status(conn) == "q24_only"
    else:
        assert not store.db_path.exists()
    commit = NewsSignalsAdoptionCommitRequest(**exact.model_dump())
    receipt = store.commit_mutation(commit, idempotency_ref=key)
    assert receipt.after_revision == 1
    view = store.read_view()
    assert view["storage_status"] == "ready"
    assert len(view["summary"]["source_readiness"]) == (2 if existing_q24 else 1)
    assert store.commit_mutation(commit, idempotency_ref=key).replayed
    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(action="undo", expected_revision=1),
        "undo-first-approved-write",
    )
    restored = store.read_view()
    assert len(restored["summary"]["source_readiness"]) == (1 if existing_q24 else 0)


def test_read_does_not_repair_partial_schema_or_migrate_legacy_undo(tmp_path):
    store = NewsSignalsAdoptionStore(tmp_path)
    _register(store)
    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "ALTER TABLE news_signals_adoption_undo DROP COLUMN expected_state_ref"
        )
    gc.collect()
    before = _news_disk_fingerprint(tmp_path)
    view = NewsSignalsAdoptionStore(tmp_path).read_view()
    assert view["storage_status"] == "migration_required"
    assert view["can_undo"] is False
    assert _news_disk_fingerprint(tmp_path) == before
    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="register_source",
            expected_revision=1,
            source_draft=_source_draft("Migration source"),
        ),
        "approved-schema-migration",
    )
    assert store.read_view()["storage_status"] == "ready"
    with sqlite3.connect(store.db_path) as conn:
        conn.execute("DROP TABLE news_signal_preferences")
    gc.collect()
    before = _news_disk_fingerprint(tmp_path)
    with pytest.raises(NewsSignalsAdoptionError, match="SCHEMA_STATE_INVALID"):
        NewsSignalsAdoptionStore(tmp_path).read_view()
    assert _news_disk_fingerprint(tmp_path) == before


def test_first_write_schema_is_rolled_back_when_receipt_insertion_fails(
    tmp_path, monkeypatch
):
    store = NewsSignalsAdoptionStore(tmp_path)

    def fail_receipt(*_):
        raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_TEST_RECEIPT_FAILURE")

    monkeypatch.setattr(store, "_insert_receipt", fail_receipt)
    with pytest.raises(NewsSignalsAdoptionError, match="TEST_RECEIPT_FAILURE"):
        _register(store)
    with sqlite3.connect(store.db_path) as conn:
        assert (
            conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            == []
        )
    assert store.read_view()["storage_status"] == "missing"


def test_read_rejects_source_drift_and_excessive_snapshot_size(tmp_path, monkeypatch):
    _seed_q24_source(tmp_path)
    store = NewsSignalsAdoptionStore(tmp_path)
    versions = store._read_file_versions()
    original = store._read_file_versions
    calls = 0

    def changing_versions():
        nonlocal calls
        calls += 1
        return versions if calls == 1 else {}

    monkeypatch.setattr(store, "_read_file_versions", changing_versions)
    with pytest.raises(NewsSignalsAdoptionConflict, match="READ_SNAPSHOT_UNAVAILABLE"):
        store.read_view()
    monkeypatch.setattr(store, "_read_file_versions", original)
    monkeypatch.setattr(
        "ultimate_ai_agent.core.news_signals.adoption.NEWS_SIGNALS_ADOPTION_MAX_DATABASE_FILE_BYTES",
        1,
    )
    with pytest.raises(NewsSignalsAdoptionError, match="DATABASE_SIZE_LIMIT"):
        store.read_view()


NOW = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)


def _source_draft(label: str = "Official source") -> NewsSignalSourceDraft:
    return NewsSignalSourceDraft(
        safe_label=label,
        source_kind="official",
        freshness_ttl_seconds=86_400,
    )


def _signal_draft(
    source_ref: str,
    *,
    title: str = "Governed agents reach a new milestone",
    summary: str = "A bounded redacted summary supplied for local review.",
    topic: str = "Agent governance",
) -> NewsSignalArtifactDraft:
    return NewsSignalArtifactDraft(
        source_ref=source_ref,
        title=title,
        safe_summary=summary,
        topic_label=topic,
        cluster_label=topic,
        claim_label=f"{topic} verified",
        published_at="2026-09-09T11:00:00Z",
        confidence_percent=92,
        evidence_class="primary",
        claim_stance="supports",
    )


def _commit(
    store: NewsSignalsAdoptionStore,
    mutation: NewsSignalsAdoptionMutationRequest,
    suffix: str,
):
    idempotency_ref = f"idempotency-ref:q34:test:{suffix}"
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    capture = NewsSignalsAdoptionApprovalCaptureRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    approval = store.capture_approval(capture, idempotency_ref=idempotency_ref)
    receipt = store.commit_mutation(
        NewsSignalsAdoptionCommitRequest(**capture.model_dump()),
        idempotency_ref=idempotency_ref,
    )
    return preview, approval, receipt


def _register(store: NewsSignalsAdoptionStore):
    _, _, receipt = _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="register_source",
            expected_revision=store.read_view()["revision"],
            source_draft=_source_draft(),
        ),
        "register-source",
    )
    assert receipt.source_ref is not None
    return receipt.source_ref


def _ingest(store: NewsSignalsAdoptionStore, source_ref: str):
    _, _, receipt = _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="ingest_signal",
            expected_revision=store.read_view()["revision"],
            signal_draft=_signal_draft(source_ref),
        ),
        "ingest-signal",
    )
    assert receipt.signal_ref is not None
    return receipt.signal_ref


def test_empty_adoption_view_is_truthful_and_fail_closed(tmp_path) -> None:
    view = NewsSignalsAdoptionStore(tmp_path).read_view(now=NOW)

    assert view["status"] == "blocked_no_graduated_source"
    assert view["revision"] == 0
    assert view["summary"]["items"] == []
    assert view["local_manual_intake_enabled"] is True
    assert view["external_content_untrusted"] is True
    for field in (
        "live_fetch_enabled",
        "authenticated_source_enabled",
        "background_polling_enabled",
        "model_summarization_enabled",
        "connector_write_enabled",
        "action_authority_granted",
    ):
        assert view[field] is False


def test_register_and_ingest_deliver_ranked_today_and_briefing_signal(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    signal_ref = _ingest(store, source_ref)

    view = store.read_view(now=NOW)

    assert view["revision"] == 2
    assert view["status"] == "ready"
    assert view["summary"]["items"][0]["signal_ref"] == signal_ref
    assert view["summary"]["today_projection"]["item_refs"] == [signal_ref]
    assert view["summary"]["morning_briefing_projection"]["candidate_refs"] == [
        signal_ref
    ]
    assert view["summary"]["items"][0]["external_content_untrusted"] is True
    assert view["summary"]["items"][0]["provenance_refs"][1].startswith(
        "approval-ref:news-signals-adoption:"
    )
    assert view["summary"]["source_readiness"][0]["reason_refs"][1].startswith(
        "approval-ref:news-signals-adoption:"
    )


def test_distinct_claims_in_one_topic_do_not_create_a_false_conflict(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    _ingest(store, source_ref)
    second_draft = _signal_draft(
        source_ref,
        title="A separate governance observation",
        summary="A different bounded assertion in the same reviewed topic.",
    ).model_copy(
        update={
            "claim_label": "A separate governance assertion",
            "claim_stance": "disputes",
        }
    )

    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="ingest_signal",
            expected_revision=2,
            signal_draft=second_draft,
        ),
        "ingest-distinct-claim",
    )
    view = store.read_view(now=NOW)

    assert view["active_items_page"]["returned_items"] == 2
    assert view["summary"]["conflicting_claim_refs"] == []


def test_preference_is_inspectable_and_changes_ranking(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    first_ref = _ingest(store, source_ref)
    _, _, second_receipt = _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="ingest_signal",
            expected_revision=2,
            signal_draft=_signal_draft(
                source_ref,
                title="Local operations signal",
                summary="A second bounded summary for local review.",
                topic="Local operations",
            ),
        ),
        "ingest-second-signal",
    )
    second_ref = second_receipt.signal_ref
    before = store.read_view(now=NOW)
    second = next(
        item for item in before["summary"]["items"] if item["signal_ref"] == second_ref
    )

    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="set_preference",
            expected_revision=3,
            topic_ref=second["topic_ref"],
            preference_weight=20,
        ),
        "prefer-local-operations",
    )
    after = store.read_view(now=NOW)

    assert after["summary"]["items"][0]["signal_ref"] == second_ref
    assert after["summary"]["items"][1]["signal_ref"] == first_ref
    assert after["preferences"][0]["weight"] == 20
    assert (
        "rank-reason-ref:q24:explicit-topic-preference"
        in after["summary"]["items"][0]["rank_reason_refs"]
    )


def test_source_safe_disable_and_recovery_are_truthful(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    signal_ref = _ingest(store, source_ref)
    admitted_reason_refs = store.read_view(now=NOW)["summary"]["source_readiness"][0][
        "reason_refs"
    ]

    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="set_source_state",
            expected_revision=2,
            target_ref=source_ref,
            source_state="safe_disabled",
        ),
        "disable-source",
    )
    disabled = store.read_view(now=NOW)
    assert disabled["status"] == "blocked_source_unavailable"
    assert disabled["summary"]["today_projection"]["item_refs"] == []
    disabled_reason_refs = disabled["summary"]["source_readiness"][0]["reason_refs"]
    assert disabled_reason_refs[:2] == admitted_reason_refs
    assert disabled_reason_refs[1].startswith("approval-ref:news-signals-adoption:")
    assert disabled_reason_refs[2:] == [
        "reason-ref:q34:operator-confirmed-source-state"
    ]

    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="set_source_state",
            expected_revision=3,
            target_ref=source_ref,
            source_state="ready",
        ),
        "recover-source",
    )
    recovered = store.read_view(now=NOW)
    assert recovered["status"] == "ready"
    assert recovered["summary"]["today_projection"]["item_refs"] == [signal_ref]
    assert recovered["summary"]["source_readiness"][0]["reason_refs"] == (
        disabled_reason_refs
    )


def test_source_transition_preserves_a_full_admission_reason_set(tmp_path) -> None:
    NewsSignalsRepository(tmp_path)
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = "source-ref:q24:full-reason-set"
    reason_refs = tuple(f"reason-ref:q24:admission-{index}" for index in range(24))
    store.repository.upsert_source(
        NewsSignalSource(
            source_ref=source_ref,
            source_kind="official",
            safe_label="Fully evidenced source",
            state="ready",
            observed_at="2026-09-09T10:00:00Z",
            reason_refs=reason_refs,
        )
    )

    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="set_source_state",
            expected_revision=0,
            target_ref=source_ref,
            source_state="safe_disabled",
        ),
        "disable-source-with-full-reason-set",
    )

    source = store.read_view(now=NOW)["summary"]["source_readiness"][0]
    assert source["state"] == "safe_disabled"
    assert source["reason_refs"] == list(reason_refs)


@pytest.mark.parametrize("source_state", ["blocked", "unknown", "revoked"])
def test_source_recovery_cannot_override_non_q34_authority_states(
    tmp_path,
    source_state,
) -> None:
    NewsSignalsRepository(tmp_path)
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = f"source-ref:q24:{source_state}"
    store.repository.upsert_source(
        NewsSignalSource(
            source_ref=source_ref,
            source_kind="official",
            safe_label=f"{source_state.title()} source",
            state=source_state,
            observed_at="2026-09-09T10:00:00Z",
            freshness_ttl_seconds=86_400,
            adapter_ref="connector-adapter-ref:q24:reviewed-source",
            provenance_ref="provenance-ref:q24:reviewed-source",
            retention_ref="retention-ref:q24:reviewed-source",
            reason_refs=(f"reason-ref:q24:{source_state}",),
        )
    )

    with pytest.raises(
        NewsSignalsAdoptionConflict,
        match="SOURCE_STATE_TRANSITION_INVALID",
    ):
        store.preview_mutation(
            NewsSignalsAdoptionMutationRequest(
                action="set_source_state",
                expected_revision=0,
                target_ref=source_ref,
                source_state="safe_disabled",
            ),
            idempotency_ref=(
                f"idempotency-ref:q34:test:invalid-transition:{source_state}"
            ),
        )


def test_source_update_keeps_artifact_label_and_approval_binding_current(
    tmp_path,
) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    _ingest(store, source_ref)
    before_source = store.read_view(now=NOW)["summary"]["source_readiness"][0]

    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="update_source",
            expected_revision=2,
            target_ref=source_ref,
            source_draft=_source_draft("Renamed official source"),
        ),
        "rename-source",
    )
    view = store.read_view(now=NOW)

    assert view["summary"]["items"][0]["source_label"] == "Renamed official source"
    after_source = view["summary"]["source_readiness"][0]
    assert after_source["reason_refs"] == before_source["reason_refs"]


def test_source_update_preserves_shared_source_origin_contract(tmp_path) -> None:
    NewsSignalsRepository(tmp_path)
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = "source-ref:q24:shared-origin"
    store.repository.upsert_source(
        NewsSignalSource(
            source_ref=source_ref,
            source_kind="rss",
            safe_label="Shared source",
            state="ready",
            observed_at="2026-09-08T10:00:00Z",
            freshness_ttl_seconds=86_400,
            adapter_ref="connector-adapter-ref:q24:shared-origin",
            provenance_ref="provenance-ref:q24:shared-origin",
            retention_ref="retention-ref:q24:shared-origin",
            reason_refs=("reason-ref:q24:shared-origin",),
        )
    )

    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="update_source",
            expected_revision=0,
            target_ref=source_ref,
            source_draft=NewsSignalSourceDraft(
                safe_label="Corrected shared source",
                source_kind="official",
                freshness_ttl_seconds=172_800,
            ),
        ),
        "correct-shared-source",
    )
    source = store.read_view(now=NOW)["summary"]["source_readiness"][0]

    assert source["safe_label"] == "Corrected shared source"
    assert source["source_kind"] == "official"
    assert source["freshness_ttl_seconds"] == 172_800
    assert source["observed_at"] == "2026-09-08T10:00:00Z"
    assert source["adapter_ref"] == "connector-adapter-ref:q24:shared-origin"
    assert source["provenance_ref"] == "provenance-ref:q24:shared-origin"
    assert source["retention_ref"] == "retention-ref:q24:shared-origin"
    assert source["reason_refs"] == ["reason-ref:q24:shared-origin"]


def test_active_signal_page_reaches_deduplicated_items_and_supports_search(
    tmp_path,
) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    first_ref = _ingest(store, source_ref)
    _, _, second_receipt = _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="ingest_signal",
            expected_revision=2,
            signal_draft=_signal_draft(
                source_ref,
                title="A second view of the milestone",
                summary="A separate redacted artifact in the same cluster.",
            ),
        ),
        "ingest-deduplicated-signal",
    )
    assert second_receipt.signal_ref is not None

    first_page = store.read_view(now=NOW, limit=1, offset=0)["active_items_page"]
    second_page = store.read_view(now=NOW, limit=1, offset=1)["active_items_page"]
    searched = store.read_view(
        now=NOW,
        limit=10,
        search_query="second view",
    )["active_items_page"]

    assert first_page["total_items"] == 2
    assert first_page["has_next"] is True
    assert second_page["has_previous"] is True
    assert {
        first_page["items"][0]["signal_ref"],
        second_page["items"][0]["signal_ref"],
    } == {first_ref, second_receipt.signal_ref}
    assert searched["search_applied"] is True
    assert searched["items"][0]["signal_ref"] == second_receipt.signal_ref
    assert len(store.read_view(now=NOW)["summary"]["items"]) == 1

    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="ingest_signal",
            expected_revision=3,
            signal_draft=_signal_draft(
                source_ref,
                title="A distinct founder signal",
                summary="A second ranked topic for bounded summary verification.",
                topic="Founder operations",
            ),
        ),
        "ingest-distinct-signal",
    )
    assert len(store.read_view(now=NOW, limit=1)["summary"]["items"]) == 1
    assert len(store.read_view(now=NOW, limit=10)["summary"]["items"]) == 2

    with pytest.raises(ValueError, match="SEARCH_QUERY_REDACTION_REQUIRED"):
        store.read_view(search_query="unsafe/path")


def test_archive_recover_correction_and_undo(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    signal_ref = _ingest(store, source_ref)

    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="archive_signal",
            expected_revision=2,
            target_ref=signal_ref,
        ),
        "archive-signal",
    )
    archived = store.read_view(now=NOW)
    assert archived["summary"]["items"] == []
    assert archived["archived_items"][0]["signal_ref"] == signal_ref

    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="recover_signal",
            expected_revision=3,
            target_ref=signal_ref,
        ),
        "recover-signal",
    )
    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="update_signal",
            expected_revision=4,
            target_ref=signal_ref,
            signal_draft=_signal_draft(
                source_ref,
                summary="A corrected bounded summary supplied for local review.",
            ),
        ),
        "correct-signal",
    )
    assert store.read_view(now=NOW)["summary"]["items"][0]["safe_summary"].startswith(
        "A corrected"
    )

    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(action="undo", expected_revision=5),
        "undo-correction",
    )
    undone = store.read_view(now=NOW)
    assert undone["revision"] == 6
    assert undone["can_undo"] is False
    assert undone["summary"]["items"][0]["safe_summary"].startswith("A bounded")


def test_signal_correction_preserves_claim_identity_when_label_is_omitted(
    tmp_path,
) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    signal_ref = _ingest(store, source_ref)
    before = store.read_view(now=NOW)["summary"]["items"][0]
    draft = _signal_draft(
        source_ref,
        summary="A corrected bounded summary supplied for local review.",
    ).model_copy(update={"claim_label": None})

    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="update_signal",
            expected_revision=2,
            target_ref=signal_ref,
            signal_draft=draft,
        ),
        "correct-signal-preserve-claim",
    )
    after = store.read_view(now=NOW)["summary"]["items"][0]

    assert after["safe_summary"].startswith("A corrected")
    assert after["claim_ref"] == before["claim_ref"]


def test_signal_correction_preserves_topic_identity_when_label_is_omitted(
    tmp_path,
) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    signal_ref = _ingest(store, source_ref)
    before = store.read_view(now=NOW)["summary"]["items"][0]
    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="set_preference",
            expected_revision=2,
            topic_ref=before["topic_ref"],
            preference_weight=12,
        ),
        "prefer-before-preserved-topic-correction",
    )
    draft = _signal_draft(
        source_ref,
        summary="A corrected bounded summary supplied for local review.",
    ).model_copy(update={"topic_label": None})

    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="update_signal",
            expected_revision=3,
            target_ref=signal_ref,
            signal_draft=draft,
        ),
        "correct-signal-preserve-topic",
    )
    after = store.read_view(now=NOW)

    assert after["summary"]["items"][0]["topic_ref"] == before["topic_ref"]
    assert after["preferences"][0]["topic_ref"] == before["topic_ref"]


@pytest.mark.parametrize("shared_q24", [False, True])
def test_signal_text_corrections_preserve_admission_and_unedited_identity(
    tmp_path,
    shared_q24,
) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    signal_ref = _ingest(store, source_ref)
    original = store.repository._read_records()[1][0]
    if shared_q24:
        shared = replace(
            original,
            source_revision_ref="source-revision-ref:q24:shared",
            topic_ref="topic-ref:q24:shared",
            cluster_ref="cluster-ref:q24:shared",
            claim_ref="claim-ref:q24:shared",
            published_at="2026-09-09T11:00:37.123456789Z",
            observed_at="2026-09-09T11:30:21.654321Z",
            interest_refs=tuple(f"interest-ref:q24:shared-{i}" for i in range(12)),
            provenance_refs=tuple(f"provenance-ref:q24:shared-{i}" for i in range(24)),
        )
        store.repository.ingest_artifact(
            shared,
            expected_current_source_revision_ref=original.source_revision_ref,
        )
        original = shared

    for index in range(3):
        draft = _signal_draft(
            source_ref,
            summary=f"A reviewed text correction number {index}.",
        ).model_copy(
            update={
                "topic_label": None,
                "cluster_label": None,
                "claim_label": None,
                "published_at": original.published_at,
            }
        )
        preview, _, receipt = _commit(
            store,
            NewsSignalsAdoptionMutationRequest(
                action="update_signal",
                expected_revision=store.read_view()["revision"],
                target_ref=signal_ref,
                signal_draft=draft,
            ),
            f"preserve-admission-{index}",
        )
        after = store.repository._read_records()[1][0]
        for field in (
            "artifact_ref",
            "source_ref",
            "topic_ref",
            "cluster_ref",
            "claim_ref",
            "published_at",
            "interest_refs",
            "provenance_refs",
        ):
            assert getattr(after, field) == getattr(original, field), field
        assert after.safe_summary == draft.safe_summary
        assert after.source_revision_ref != original.source_revision_ref
        assert receipt.approval_ref == preview.approval_ref
        with sqlite3.connect(store.db_path) as conn:
            saved = conn.execute(
                "SELECT receipt_json FROM news_signals_adoption_receipts "
                "WHERE idempotency_ref = ?",
                (f"idempotency-ref:q34:test:preserve-admission-{index}",),
            ).fetchone()
        assert json.loads(saved[0])["approval_ref"] == preview.approval_ref


def test_explicit_cluster_correction_changes_only_the_requested_group(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    signal_ref = _ingest(store, source_ref)
    before = store.read_view(now=NOW)["summary"]["items"][0]
    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="update_signal",
            expected_revision=2,
            target_ref=signal_ref,
            signal_draft=_signal_draft(source_ref).model_copy(
                update={"cluster_label": "Corrected story group"},
            ),
        ),
        "correct-cluster",
    )
    after = store.read_view(now=NOW)["summary"]["items"][0]
    assert after["cluster_ref"] != before["cluster_ref"]
    assert after["topic_ref"] == before["topic_ref"]
    assert after["claim_ref"] == before["claim_ref"]
    assert after["provenance_refs"] == before["provenance_refs"]


def test_ingest_requires_an_explicit_cluster_label(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    with pytest.raises(ValueError, match="CLUSTER_LABEL_REQUIRED"):
        NewsSignalsAdoptionMutationRequest(
            action="ingest_signal",
            expected_revision=1,
            signal_draft=_signal_draft(source_ref).model_copy(
                update={"cluster_label": None},
            ),
        )


def test_ingest_requires_an_explicit_claim_label(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)

    with pytest.raises(ValueError, match="CLAIM_LABEL_REQUIRED"):
        NewsSignalsAdoptionMutationRequest(
            action="ingest_signal",
            expected_revision=1,
            signal_draft=_signal_draft(source_ref).model_copy(
                update={"claim_label": None}
            ),
        )


def test_ingest_requires_an_explicit_topic_label(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)

    with pytest.raises(ValueError, match="TOPIC_LABEL_REQUIRED"):
        NewsSignalsAdoptionMutationRequest(
            action="ingest_signal",
            expected_revision=1,
            signal_draft=_signal_draft(source_ref).model_copy(
                update={"topic_label": None}
            ),
        )


def test_signal_topic_correction_removes_orphaned_preference(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    signal_ref = _ingest(store, source_ref)
    current = store.read_view(now=NOW)["summary"]["items"][0]
    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="set_preference",
            expected_revision=2,
            topic_ref=current["topic_ref"],
            preference_weight=12,
        ),
        "prefer-before-topic-correction",
    )

    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(
            action="update_signal",
            expected_revision=3,
            target_ref=signal_ref,
            signal_draft=_signal_draft(source_ref, topic="Corrected governance"),
        ),
        "correct-preferred-topic",
    )
    view = store.read_view(now=NOW)

    assert view["preferences"] == []
    assert view["summary"]["items"][0]["topic_ref"] != current["topic_ref"]


def test_stale_revision_and_approval_substitution_are_rejected(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    mutation = NewsSignalsAdoptionMutationRequest(
        action="register_source",
        expected_revision=0,
        source_draft=_source_draft(),
    )
    idempotency_ref = "idempotency-ref:q34:test:approval-scope"
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)

    with pytest.raises(NewsSignalsAdoptionConflict, match="APPROVAL_SCOPE_MISMATCH"):
        store.capture_approval(
            NewsSignalsAdoptionApprovalCaptureRequest(
                mutation=mutation,
                preview_ref=preview.preview_ref,
                approval_ref="approval-ref:q34:substituted",
            ),
            idempotency_ref=idempotency_ref,
        )

    _commit(store, mutation, "register-exact")
    with pytest.raises(NewsSignalsAdoptionConflict, match="STALE_REVISION"):
        store.preview_mutation(
            mutation,
            idempotency_ref="idempotency-ref:q34:test:stale",
        )


def test_undo_approval_binds_the_exact_snapshot_bytes(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    mutation = NewsSignalsAdoptionMutationRequest(
        action="undo",
        expected_revision=1,
    )
    idempotency_ref = "idempotency-ref:q34:test:undo-snapshot-binding"
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    exact = NewsSignalsAdoptionCommitRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    store.capture_approval(exact, idempotency_ref=idempotency_ref)

    with sqlite3.connect(store.db_path) as conn:
        original = conn.execute(
            "SELECT snapshot_json FROM news_signals_adoption_undo WHERE singleton = 1"
        ).fetchone()[0]
        conn.execute(
            "UPDATE news_signals_adoption_undo SET snapshot_json = ? "
            "WHERE singleton = 1",
            (f"{original} ",),
        )

    with pytest.raises(NewsSignalsAdoptionConflict, match="UNDO_UNAVAILABLE"):
        store.commit_mutation(exact, idempotency_ref=idempotency_ref)

    view = store.read_view(now=NOW)
    assert view["revision"] == 1
    assert view["summary"]["source_readiness"][0]["source_ref"] == source_ref


def test_undo_is_invalidated_by_later_shared_q24_state(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    store.repository.upsert_source(
        NewsSignalSource(
            source_ref="source-ref:q24:later-admission",
            source_kind="community",
            safe_label="Later shared admission",
            state="ready",
            observed_at="2026-09-09T11:30:00Z",
            reason_refs=("reason-ref:q24:later-admission",),
        )
    )

    view = store.read_view(now=NOW)
    assert view["can_undo"] is False
    assert {item["source_ref"] for item in view["summary"]["source_readiness"]} == {
        source_ref,
        "source-ref:q24:later-admission",
    }
    with pytest.raises(NewsSignalsAdoptionConflict, match="UNDO_UNAVAILABLE"):
        store.preview_mutation(
            NewsSignalsAdoptionMutationRequest(action="undo", expected_revision=1),
            idempotency_ref="idempotency-ref:q34:test:stale-shared-state-undo",
        )


def test_invalid_undo_snapshot_fails_closed_before_undo_is_advertised(
    tmp_path,
) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    _register(store)
    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE news_signals_adoption_undo SET snapshot_json = ? "
            "WHERE singleton = 1",
            ('{"sources":',),
        )

    with pytest.raises(
        NewsSignalsAdoptionError,
        match="UNDO_STATE_INVALID",
    ):
        store.read_view(now=NOW)


def test_commit_requires_captured_exact_approval_and_replays_idempotently(
    tmp_path,
) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    mutation = NewsSignalsAdoptionMutationRequest(
        action="register_source",
        expected_revision=0,
        source_draft=_source_draft(),
    )
    idempotency_ref = "idempotency-ref:q34:test:replay"
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    commit = NewsSignalsAdoptionCommitRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    with pytest.raises(NewsSignalsAdoptionError, match="EXACT_APPROVAL_REQUIRED"):
        store.commit_mutation(commit, idempotency_ref=idempotency_ref)

    store.capture_approval(
        NewsSignalsAdoptionApprovalCaptureRequest(**commit.model_dump()),
        idempotency_ref=idempotency_ref,
    )
    first = store.commit_mutation(commit, idempotency_ref=idempotency_ref)
    replay = NewsSignalsAdoptionStore(tmp_path).commit_mutation(
        commit,
        idempotency_ref=idempotency_ref,
    )

    assert replay.receipt_ref == first.receipt_ref
    assert replay.replayed is True
    assert store.read_view()["revision"] == 1


def test_receipt_capacity_reserves_the_final_slot_for_undo(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    with sqlite3.connect(store.db_path) as conn:
        original = NewsSignalsAdoptionMutationReceipt.model_validate_json(
            conn.execute(
                "SELECT receipt_json FROM news_signals_adoption_receipts LIMIT 1"
            ).fetchone()[0]
        )
        rows = []
        for index in range(NEWS_SIGNALS_ADOPTION_MAX_RECEIPTS - 2):
            idempotency_ref = f"idempotency-ref:q34:capacity:{index}"
            receipt_ref = _mutation_receipt_ref(
                action=original.action,
                target_ref=original.target_ref,
                source_ref=original.source_ref,
                signal_ref=original.signal_ref,
                before_revision=original.before_revision,
                after_revision=original.after_revision,
                idempotency_ref=idempotency_ref,
                payload_fingerprint_ref=original.payload_fingerprint_ref,
                preview_ref=original.preview_ref,
                approval_ref=original.approval_ref,
                approval_validation_ref=original.approval_validation_ref,
                approval_expires_at=original.approval_expires_at,
                authority_decision_ref=original.authority_decision_ref,
                authority_lease_ref=original.authority_lease_ref,
                state_ref=original.state_ref,
            )
            clone = original.model_copy(
                update={
                    "idempotency_ref": idempotency_ref,
                    "receipt_ref": receipt_ref,
                    "rollback_ref": _hash_ref(
                        "rollback-ref:news-signals-adoption",
                        {"receipt_ref": receipt_ref, "action": "undo"},
                    ),
                }
            )
            rows.append(
                (
                    clone.idempotency_ref,
                    clone.payload_fingerprint_ref,
                    clone.preview_ref,
                    clone.approval_ref,
                    clone.model_dump_json(),
                )
            )
        conn.executemany(
            """
            INSERT INTO news_signals_adoption_receipts(
                idempotency_ref, payload_fingerprint_ref, preview_ref,
                approval_ref, receipt_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )

    update = NewsSignalsAdoptionMutationRequest(
        action="update_source",
        expected_revision=1,
        target_ref=source_ref,
        source_draft=_source_draft("Capacity update"),
    )
    update_ref = "idempotency-ref:q34:test:capacity-update"
    update_preview = store.preview_mutation(update, idempotency_ref=update_ref)
    update_request = NewsSignalsAdoptionCommitRequest(
        mutation=update,
        preview_ref=update_preview.preview_ref,
        approval_ref=update_preview.approval_ref,
    )
    store.capture_approval(update_request, idempotency_ref=update_ref)
    with pytest.raises(
        NewsSignalsAdoptionError,
        match="RECEIPT_CAPACITY_EXHAUSTED",
    ):
        store.commit_mutation(update_request, idempotency_ref=update_ref)

    unchanged = store.read_view(now=NOW)
    assert unchanged["revision"] == 1
    assert unchanged["summary"]["source_readiness"][0]["safe_label"] == (
        "Official source"
    )

    _commit(
        store,
        NewsSignalsAdoptionMutationRequest(action="undo", expected_revision=1),
        "capacity-final-undo",
    )
    assert store.read_view(now=NOW)["summary"]["source_readiness"] == []


def test_approval_resolution_failure_is_bounded_and_does_not_mutate(
    tmp_path,
    monkeypatch,
) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    mutation = NewsSignalsAdoptionMutationRequest(
        action="register_source",
        expected_revision=0,
        source_draft=_source_draft(),
    )
    idempotency_ref = "idempotency-ref:q34:test:approval-resolution-failure"
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    exact = NewsSignalsAdoptionCommitRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    store.capture_approval(exact, idempotency_ref=idempotency_ref)

    def fail_resolve(*_args: object, **_kwargs: object) -> None:
        raise AuthorityLeaseApprovalStateError("synthetic invalid approval store")

    monkeypatch.setattr(AuthorityLeaseApprovalStore, "resolve", fail_resolve)

    with pytest.raises(
        NewsSignalsAdoptionError,
        match="AUTHORITY_STATE_INVALID",
    ):
        store.commit_mutation(exact, idempotency_ref=idempotency_ref)
    assert store.read_view(now=NOW)["revision"] == 0


def test_idempotency_ref_cannot_be_rebound_to_changed_payload(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    mutation = NewsSignalsAdoptionMutationRequest(
        action="register_source",
        expected_revision=0,
        source_draft=_source_draft(),
    )
    idempotency_ref = "idempotency-ref:q34:test:rebound"
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    exact = NewsSignalsAdoptionApprovalCaptureRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    store.capture_approval(exact, idempotency_ref=idempotency_ref)
    store.commit_mutation(
        NewsSignalsAdoptionCommitRequest(**exact.model_dump()),
        idempotency_ref=idempotency_ref,
    )
    changed = NewsSignalsAdoptionMutationRequest(
        action="register_source",
        expected_revision=0,
        source_draft=_source_draft("Changed source"),
    )
    with pytest.raises(NewsSignalsAdoptionConflict, match="IDEMPOTENCY_CONFLICT"):
        store.commit_mutation(
            NewsSignalsAdoptionCommitRequest(
                mutation=changed,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
            ),
            idempotency_ref=idempotency_ref,
        )


@pytest.mark.skipif(os.name == "nt", reason="POSIX private modes")
def test_local_state_files_are_private(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path / "news")
    _register(store)

    assert store.state_dir.stat().st_mode & 0o077 == 0
    assert store.db_path.stat().st_mode & 0o077 == 0


@pytest.mark.skipif(os.name == "nt", reason="POSIX link safety")
def test_database_symlink_is_rejected_before_open(tmp_path) -> None:
    state_dir = tmp_path / "news"
    state_dir.mkdir(mode=0o700)
    outside = tmp_path / "outside.sqlite3"
    outside.write_text("unchanged", encoding="utf-8")
    (state_dir / "news_signals.sqlite3").symlink_to(outside)

    with pytest.raises(NewsSignalsAdoptionError, match="DATABASE_FILE_UNSAFE"):
        NewsSignalsAdoptionStore(state_dir)

    assert outside.read_text(encoding="utf-8") == "unchanged"


@pytest.mark.skipif(os.name == "nt", reason="POSIX link safety")
def test_state_directory_symlink_is_rejected(tmp_path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    linked = tmp_path / "linked"
    linked.symlink_to(outside, target_is_directory=True)

    with pytest.raises(NewsSignalsAdoptionError, match="STATE_DIRECTORY_UNSAFE"):
        NewsSignalsAdoptionStore(linked)


def test_corrupt_database_and_receipt_state_fail_with_safe_codes(tmp_path) -> None:
    corrupt_dir = tmp_path / "corrupt"
    corrupt_dir.mkdir(mode=0o700)
    (corrupt_dir / "news_signals.sqlite3").write_bytes(b"not a sqlite database")
    with pytest.raises(NewsSignalsAdoptionError, match="DATABASE_STATE_INVALID"):
        NewsSignalsAdoptionStore(corrupt_dir).read_view()

    receipt_store = NewsSignalsAdoptionStore(tmp_path / "receipt")
    mutation = NewsSignalsAdoptionMutationRequest(
        action="register_source",
        expected_revision=0,
        source_draft=_source_draft(),
    )
    idempotency_ref = "idempotency-ref:q34:test:corrupt-receipt"
    preview = receipt_store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    exact = NewsSignalsAdoptionCommitRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    receipt_store.capture_approval(exact, idempotency_ref=idempotency_ref)
    receipt_store.commit_mutation(exact, idempotency_ref=idempotency_ref)
    with sqlite3.connect(receipt_store.db_path) as conn:
        conn.execute(
            "UPDATE news_signals_adoption_receipts "
            "SET payload_fingerprint_ref = ? WHERE idempotency_ref = ?",
            ("payload-fingerprint-ref:q34:forged", idempotency_ref),
        )
    with pytest.raises(NewsSignalsAdoptionError, match="RECEIPT_STATE_INVALID"):
        receipt_store.commit_mutation(exact, idempotency_ref=idempotency_ref)


def test_unrelated_corrupt_receipt_blocks_reads_and_new_mutations(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    _ingest(store, source_ref)
    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE news_signals_adoption_receipts SET receipt_json = ? "
            "WHERE idempotency_ref = ?",
            ("{}", "idempotency-ref:q34:test:register-source"),
        )

    with pytest.raises(NewsSignalsAdoptionError, match="RECEIPT_STATE_INVALID"):
        store.read_view(now=NOW)
    with pytest.raises(NewsSignalsAdoptionError, match="RECEIPT_STATE_INVALID"):
        store.preview_mutation(
            NewsSignalsAdoptionMutationRequest(
                action="update_source",
                expected_revision=2,
                target_ref=source_ref,
                source_draft=_source_draft("Blocked by receipt corruption"),
            ),
            idempotency_ref="idempotency-ref:q34:test:after-receipt-corruption",
        )


def test_object_shaped_durable_reference_lists_fail_closed(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    signal_ref = _ingest(store, source_ref)

    with sqlite3.connect(store.db_path) as conn:
        original = conn.execute(
            "SELECT reason_refs_json FROM news_signal_sources WHERE source_ref = ?",
            (source_ref,),
        ).fetchone()[0]
        conn.execute(
            "UPDATE news_signal_sources SET reason_refs_json = ? WHERE source_ref = ?",
            (json.dumps({"reason-ref:q34:forged": True}), source_ref),
        )
    with pytest.raises(NewsSignalsAdoptionError, match="DATABASE_ROW_INVALID"):
        store.read_view(now=NOW)
    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE news_signal_sources SET reason_refs_json = ? WHERE source_ref = ?",
            (original, source_ref),
        )

    with sqlite3.connect(store.db_path) as conn:
        original = conn.execute(
            "SELECT interest_refs_json FROM news_signal_artifacts "
            "WHERE artifact_ref = ?",
            (signal_ref,),
        ).fetchone()[0]
        conn.execute(
            "UPDATE news_signal_artifacts SET interest_refs_json = ? "
            "WHERE artifact_ref = ?",
            (json.dumps({"interest-ref:q34:forged": True}), signal_ref),
        )
    with pytest.raises(NewsSignalsAdoptionError, match="DATABASE_ROW_INVALID"):
        store.read_view(now=NOW)
    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE news_signal_artifacts SET interest_refs_json = ? "
            "WHERE artifact_ref = ?",
            (original, signal_ref),
        )

    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE news_signal_artifacts SET provenance_refs_json = ? "
            "WHERE artifact_ref = ?",
            (json.dumps({"provenance-ref:q34:forged": True}), signal_ref),
        )
    with pytest.raises(NewsSignalsAdoptionError, match="DATABASE_ROW_INVALID"):
        store.read_view(now=NOW)


def test_durable_receipt_rejects_substituted_lifecycle_and_authority_fields(
    tmp_path,
) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    mutation = NewsSignalsAdoptionMutationRequest(
        action="register_source",
        expected_revision=0,
        source_draft=_source_draft(),
    )
    idempotency_ref = "idempotency-ref:q34:test:receipt-complete-binding"
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    exact = NewsSignalsAdoptionCommitRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    store.capture_approval(exact, idempotency_ref=idempotency_ref)
    original_receipt = store.commit_mutation(
        exact,
        idempotency_ref=idempotency_ref,
    )
    original_json = original_receipt.model_dump_json()
    substitutions = {
        "action": "undo",
        "target_ref": "signal-ref:q34:forged",
        "source_ref": "source-ref:q34:forged",
        "signal_ref": "signal-ref:q34:forged",
        "approval_validation_ref": "approval-validation-ref:q34:forged",
        "approval_expires_at": "2099-01-01T00:00:00Z",
        "authority_decision_ref": "authority-decision-ref:q34:forged",
        "authority_lease_ref": "authority-lease-ref:q34:forged",
        "replayed": True,
    }

    for field, replacement in substitutions.items():
        forged = json.loads(original_json)
        forged[field] = replacement
        with sqlite3.connect(store.db_path) as conn:
            conn.execute(
                "UPDATE news_signals_adoption_receipts SET receipt_json = ? "
                "WHERE idempotency_ref = ?",
                (json.dumps(forged), idempotency_ref),
            )
        with pytest.raises(
            NewsSignalsAdoptionError,
            match="RECEIPT_STATE_INVALID",
        ):
            store.commit_mutation(exact, idempotency_ref=idempotency_ref)

    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE news_signals_adoption_receipts SET receipt_json = ? "
            "WHERE idempotency_ref = ?",
            (original_json, idempotency_ref),
        )
    replay = store.commit_mutation(exact, idempotency_ref=idempotency_ref)
    assert replay.receipt_ref == original_receipt.receipt_ref
    assert replay.replayed is True


def test_direct_database_capacity_inflation_fails_before_projection(tmp_path) -> None:
    NewsSignalsRepository(tmp_path)
    store = NewsSignalsAdoptionStore(tmp_path)
    with sqlite3.connect(store.db_path) as conn:
        for index in range(25):
            conn.execute(
                "INSERT INTO news_signal_sources VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    f"source-ref:q34:capacity-{index}",
                    "local",
                    f"Local source {index}",
                    "ready",
                    "2026-09-09T12:00:00Z",
                    86_400,
                    "connector-adapter-ref:q34:local",
                    "provenance-ref:q34:local",
                    "retention-ref:q34:local",
                    "[]",
                ),
            )

    with pytest.raises(NewsSignalsAdoptionError, match="DATABASE_CAPACITY_INVALID"):
        store.read_view()
