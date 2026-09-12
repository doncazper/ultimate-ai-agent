from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import sqlite3

import pytest

from ultimate_ai_agent.core.news_signals.adoption import (
    NewsSignalArtifactDraft,
    NewsSignalSourceDraft,
    NewsSignalsAdoptionApprovalCaptureRequest,
    NewsSignalsAdoptionCommitRequest,
    NewsSignalsAdoptionConflict,
    NewsSignalsAdoptionError,
    NewsSignalsAdoptionMutationRequest,
    NewsSignalsAdoptionStore,
)


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
    second = next(item for item in before["summary"]["items"] if item["signal_ref"] == second_ref)

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
    assert "rank-reason-ref:q24:explicit-topic-preference" in after["summary"]["items"][0]["rank_reason_refs"]


def test_source_safe_disable_and_recovery_are_truthful(tmp_path) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    signal_ref = _ingest(store, source_ref)

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
    assert disabled["summary"]["source_readiness"][0]["reason_refs"][1].startswith(
        "approval-ref:news-signals-adoption:"
    )

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


def test_source_update_keeps_artifact_label_and_approval_binding_current(
    tmp_path,
) -> None:
    store = NewsSignalsAdoptionStore(tmp_path)
    source_ref = _register(store)
    _ingest(store, source_ref)

    preview, _, _ = _commit(
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
    assert view["summary"]["source_readiness"][0]["reason_refs"][-1] == (
        preview.approval_ref
    )


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

    with pytest.raises(NewsSignalsAdoptionConflict, match="COMMIT_SCOPE_MISMATCH"):
        store.commit_mutation(exact, idempotency_ref=idempotency_ref)

    view = store.read_view(now=NOW)
    assert view["revision"] == 1
    assert view["summary"]["source_readiness"][0]["source_ref"] == source_ref


def test_commit_requires_captured_exact_approval_and_replays_idempotently(tmp_path) -> None:
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
        NewsSignalsAdoptionStore(corrupt_dir)

    receipt_store = NewsSignalsAdoptionStore(tmp_path / "receipt")
    mutation = NewsSignalsAdoptionMutationRequest(
        action="register_source",
        expected_revision=0,
        source_draft=_source_draft(),
    )
    idempotency_ref = "idempotency-ref:q34:test:corrupt-receipt"
    preview = receipt_store.preview_mutation(
        mutation, idempotency_ref=idempotency_ref
    )
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
