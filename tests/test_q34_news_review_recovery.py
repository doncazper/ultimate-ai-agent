from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
import sqlite3

import pytest

from ultimate_ai_agent.core.news_signals.adoption import (
    NEWS_SIGNALS_ADOPTION_MAX_UNDO_BYTES,
    NewsSignalArtifactDraft,
    NewsSignalSourceDraft,
    NewsSignalsAdoptionCommitRequest,
    NewsSignalsAdoptionError,
    NewsSignalsAdoptionMutationRequest,
    NewsSignalsAdoptionStore,
    _canonical_json,
)
from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.news_signals import adoption
from ultimate_ai_agent.core.news_signals.read_model import (
    NewsSignalArtifact,
    NewsSignalPreference,
    NewsSignalSource,
    NewsSignalsRepository,
    build_news_signals_summary,
)


SOURCE = "source-ref:q34:recovery"
TOPIC = "topic-ref:q34:recovery"
NOW = datetime(2026, 9, 13, 12, tzinfo=timezone.utc)


def _source():
    return NewsSignalSource(
        source_ref=SOURCE,
        source_kind="official",
        safe_label="Reviewed source",
        state="ready",
        observed_at="2026-09-13T12:00:00Z",
    )


def _artifact(index):
    return NewsSignalArtifact(
        artifact_ref=f"artifact-ref:q34:recovery:{index}",
        source_ref=SOURCE,
        source_revision_ref=f"revision-ref:q34:recovery:{index}",
        content_digest_ref=f"digest-ref:q34:recovery:{index}",
        cluster_ref=f"cluster-ref:q34:recovery:{index}",
        claim_ref=f"claim-ref:q34:recovery:{index}",
        title="Reviewed local source " + "a" * 118,
        safe_summary="Reviewed summary " + "b" * 303,
        source_label=f"Reviewed source {index}",
        topic_ref=TOPIC,
        published_at="2026-09-13T11:00:00Z",
        observed_at="2026-09-13T12:00:00Z",
        confidence_percent=90,
        evidence_class="primary",
        interest_refs=tuple(
            f"interest-ref:q34:{i}:" + "reviewed" * 23 for i in range(12)
        ),
        provenance_refs=tuple(
            f"provenance-ref:q34:{i}:" + "reviewed" * 23 for i in range(24)
        ),
    )


def _snapshot(store):
    with store._read_connection() as conn:
        return store._read_snapshot(conn)


def _prepare(store, mutation, key):
    preview = store.preview_mutation(mutation, idempotency_ref=key)
    request = NewsSignalsAdoptionCommitRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    store.capture_approval(request, idempotency_ref=key)
    return request


def _commit(store, action, label, **fields):
    mutation = NewsSignalsAdoptionMutationRequest(
        action=action,
        expected_revision=_snapshot(store).revision,
        **fields,
    )
    key = f"idempotency-ref:q34:recovery:{label}"
    return store.commit_mutation(_prepare(store, mutation, key), idempotency_ref=key)


def _large_store(path, count):
    repository = NewsSignalsRepository(path)
    repository.upsert_source(_source())
    store = NewsSignalsAdoptionStore(path)
    with sqlite3.connect(repository.db_path) as conn:
        for index in range(count):
            # Q24 already admits these bounded, redacted artifacts.
            store._write_artifact(conn, _artifact(index))
    return store


@pytest.mark.parametrize(
    "action",
    [
        "archive_signal",
        "recover_signal",
        "set_source_state",
        "update_source",
        "update_signal",
        "set_preference",
        "remove_preference",
        "register_source",
        "ingest_signal",
    ],
)
def test_large_shared_workspace_mutation_and_exact_undo_remain_available(
    tmp_path, action
):
    store = _large_store(tmp_path, 2000 if action == "archive_signal" else 650)
    target = "artifact-ref:q34:recovery:0"
    if action == "recover_signal":
        _commit(store, "archive_signal", "archive-first", target_ref=target)
    if action in {"remove_preference", "update_signal"}:
        _commit(
            store,
            "set_preference",
            "prefer-first",
            topic_ref=TOPIC,
            preference_weight=10,
        )
    before = store._snapshot_payload(_snapshot(store))
    assert len(_canonical_json(before)) > NEWS_SIGNALS_ADOPTION_MAX_UNDO_BYTES
    fields = {}
    if action in {"archive_signal", "recover_signal"}:
        fields = {"target_ref": target}
    elif action == "set_source_state":
        fields = {"target_ref": SOURCE, "source_state": "safe_disabled"}
    elif action in {"register_source", "update_source"}:
        fields = {
            "source_draft": NewsSignalSourceDraft(
                safe_label="Corrected source", source_kind="official"
            )
        }
        if action == "update_source":
            fields["target_ref"] = SOURCE
    elif action in {"ingest_signal", "update_signal"}:
        fields = {
            "signal_draft": NewsSignalArtifactDraft(
                source_ref=SOURCE,
                title="Corrected signal",
                safe_summary="Reviewed local correction",
                topic_label="New reviewed topic",
                cluster_label="New story",
                claim_label="New claim",
                published_at="2026-09-13T11:00:00Z",
                confidence_percent=90,
                evidence_class="primary",
            )
        }
        if action == "update_signal":
            fields["target_ref"] = target
    else:
        fields = {"topic_ref": TOPIC}
        if action == "set_preference":
            fields["preference_weight"] = 10
    _commit(store, action, "large-change", **fields)
    with sqlite3.connect(store.db_path) as conn:
        payload = conn.execute(
            "SELECT snapshot_json FROM news_signals_adoption_undo"
        ).fetchone()[0]
    assert json.loads(payload)["snapshot_format"] == "reference-delta-v1"
    assert len(payload.encode()) <= NEWS_SIGNALS_ADOPTION_MAX_UNDO_BYTES
    assert _snapshot(store).can_undo
    _commit(store, "undo", "large-undo")
    after = store._snapshot_payload(_snapshot(store))
    assert (
        hashlib.sha256(_canonical_json(after)).digest()
        == hashlib.sha256(_canonical_json(before)).digest()
    )


def test_projection_records_are_independent_of_ranked_page_limit():
    artifacts = [
        replace(_artifact(i), published_at="2026-09-01T11:00:00Z") for i in range(20)
    ]
    candidate = replace(
        _artifact(20),
        confidence_percent=60,
        evidence_class="corroborating",
        topic_ref="topic-ref:q34:secondary",
    )
    artifacts.append(candidate)
    summary = build_news_signals_summary(
        sources=[_source()],
        artifacts=artifacts,
        now=NOW,
        limit=20,
        preferences=[
            NewsSignalPreference(
                topic_ref=TOPIC, weight=20, preference_ref="preference-ref:q34:primary"
            ),
            NewsSignalPreference(
                topic_ref=candidate.topic_ref,
                weight=-20,
                preference_ref="preference-ref:q34:secondary",
            ),
        ],
    )
    projected = {item["signal_ref"] for item in summary["projection_items"]}
    assert candidate.artifact_ref in projected
    assert set(summary["today_projection"]["item_refs"]) <= projected
    assert set(summary["morning_briefing_projection"]["candidate_refs"]) <= projected
    assert len(summary["items"]) == 20
    assert candidate.artifact_ref not in {
        item["signal_ref"] for item in summary["items"]
    }
    assert len(summary["projection_items"]) <= 8


@pytest.mark.parametrize("tamper", ["whitespace", "reference", "source_label"])
def test_compact_undo_remains_bound_to_exact_reviewed_bytes(tmp_path, tamper):
    store = _large_store(tmp_path, 650)
    _commit(
        store,
        "archive_signal",
        "before-tamper",
        target_ref="artifact-ref:q34:recovery:0",
    )
    mutation = NewsSignalsAdoptionMutationRequest(
        action="undo", expected_revision=_snapshot(store).revision
    )
    key = "idempotency-ref:q34:recovery:tampered-undo"
    request = _prepare(store, mutation, key)
    with sqlite3.connect(store.db_path) as conn:
        encoded = conn.execute(
            "SELECT snapshot_json FROM news_signals_adoption_undo"
        ).fetchone()[0]
        payload = json.loads(encoded)
        if tamper == "reference":
            payload["unchanged_artifact_refs"][0] = "artifact-ref:q34:substitution"
            encoded = _canonical_json(payload).decode()
        elif tamper == "source_label":
            payload["source_label_overrides"][payload["unchanged_artifact_refs"][0]] = (
                "Substituted label"
            )
            encoded = _canonical_json(payload).decode()
        else:
            encoded += " "
        conn.execute(
            "UPDATE news_signals_adoption_undo SET snapshot_json = ?", (encoded,)
        )
    assert _snapshot(store).can_undo is False
    with pytest.raises(NewsSignalsAdoptionError, match="UNDO_UNAVAILABLE"):
        store.commit_mutation(request, idempotency_ref=key)
    assert _snapshot(store).revision == mutation.expected_revision


def test_compact_undo_does_not_revert_later_shared_q24_state(tmp_path):
    store = _large_store(tmp_path, 650)
    _commit(
        store,
        "archive_signal",
        "before-shared-change",
        target_ref="artifact-ref:q34:recovery:0",
    )
    with sqlite3.connect(store.db_path) as conn:
        store._write_artifact(conn, replace(_artifact(1), title="Later shared change"))
    current = _snapshot(store)
    assert current.can_undo is False
    assert (
        next(
            item
            for item in current.artifacts
            if item.artifact_ref == "artifact-ref:q34:recovery:1"
        ).title
        == "Later shared change"
    )


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission contract")
def test_hardening_failure_rolls_back_before_receipt_is_committed(
    tmp_path, monkeypatch
):
    store = NewsSignalsAdoptionStore(tmp_path)
    mutation = NewsSignalsAdoptionMutationRequest(
        action="register_source",
        expected_revision=0,
        source_draft=NewsSignalSourceDraft(
            safe_label="Reviewed source", source_kind="official"
        ),
    )
    key = "idempotency-ref:q34:recovery:hardening"
    request = _prepare(store, mutation, key)

    def fail_hardening():
        raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_DATABASE_FILE_UNSAFE")

    monkeypatch.setattr(store, "_harden_database_files", fail_hardening)
    with pytest.raises(NewsSignalsAdoptionError, match="DATABASE_FILE_UNSAFE"):
        store.commit_mutation(request, idempotency_ref=key)
    assert _snapshot(store).revision == 0
    assert _snapshot(store).sources == ()
    with store._read_connection() as conn:
        assert store._receipt_for_idempotency(conn, key) is None


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission contract")
def test_exact_replay_repairs_older_committed_file_postcondition(tmp_path, monkeypatch):
    store = NewsSignalsAdoptionStore(tmp_path)
    mutation = NewsSignalsAdoptionMutationRequest(
        action="register_source",
        expected_revision=0,
        source_draft=NewsSignalSourceDraft(
            safe_label="Reviewed source", source_kind="official"
        ),
    )
    key = "idempotency-ref:q34:recovery:replay-hardening"
    request = _prepare(store, mutation, key)
    receipt = store.commit_mutation(request, idempotency_ref=key)
    os.chmod(store.db_path, 0o644)
    os.chmod(store.state_dir, 0o755)
    replay = store.commit_mutation(request, idempotency_ref=key)
    assert replay.replayed and replay.receipt_ref == receipt.receipt_ref
    assert store.db_path.stat().st_mode & 0o777 == 0o600
    assert store.state_dir.stat().st_mode & 0o777 == 0o700

    def fail_hardening():
        raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_DATABASE_FILE_UNSAFE")

    monkeypatch.setattr(store, "_harden_database_files", fail_hardening)
    with pytest.raises(NewsSignalsAdoptionError, match="COMMITTED_HARDENING_REQUIRED"):
        store.commit_mutation(request, idempotency_ref=key)
    assert _snapshot(store).revision == receipt.after_revision


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission contract")
def test_rolled_back_hardening_failure_keeps_exact_retry_recoverable(
    tmp_path, monkeypatch
):
    store = NewsSignalsAdoptionStore(tmp_path)
    mutation = NewsSignalsAdoptionMutationRequest(
        action="register_source",
        expected_revision=0,
        source_draft=NewsSignalSourceDraft(
            safe_label="Reviewed retry", source_kind="official"
        ),
    )
    key = "idempotency-ref:q34:recovery:hardening-retry"
    request = _prepare(store, mutation, key)
    harden = store._harden_database_files

    def fail_hardening():
        raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_DATABASE_FILE_UNSAFE")

    monkeypatch.setattr(store, "_harden_database_files", fail_hardening)
    with pytest.raises(NewsSignalsAdoptionError, match="DATABASE_FILE_UNSAFE"):
        store.commit_mutation(request, idempotency_ref=key)
    assert _snapshot(store).revision == 0
    with store._read_connection() as conn:
        assert store._receipt_for_idempotency(conn, key) is None
    monkeypatch.setattr(store, "_harden_database_files", harden)
    receipt = store.commit_mutation(request, idempotency_ref=key)
    assert receipt.after_revision == 1 and not receipt.replayed
    replay = store.commit_mutation(request, idempotency_ref=key)
    assert replay.replayed and replay.receipt_ref == receipt.receipt_ref
    assert len(_snapshot(store).sources) == 1


@pytest.mark.parametrize(
    "invalidated",
    ["approval_expired", "lease_revoked", "payload_rebound", "state_changed"],
)
def test_hardening_retry_still_requires_exact_current_authority(
    tmp_path, monkeypatch, invalidated
):
    store = NewsSignalsAdoptionStore(tmp_path)
    mutation = NewsSignalsAdoptionMutationRequest(
        action="register_source",
        expected_revision=0,
        source_draft=NewsSignalSourceDraft(
            safe_label="Reviewed retry", source_kind="official"
        ),
    )
    key = "idempotency-ref:q34:recovery:retry-authority"
    request = _prepare(store, mutation, key)
    harden = store._harden_database_files

    def fail_hardening():
        raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_DATABASE_FILE_UNSAFE")

    monkeypatch.setattr(store, "_harden_database_files", fail_hardening)
    with pytest.raises(NewsSignalsAdoptionError, match="DATABASE_FILE_UNSAFE"):
        store.commit_mutation(request, idempotency_ref=key)
    monkeypatch.setattr(store, "_harden_database_files", harden)
    leases = AuthorityLeaseStore(store.state_dir / "news_signals_authority")
    active = leases.list_leases(active_only=True)
    assert len(active) == 1
    expected_error = "COMMIT_SCOPE_MISMATCH"
    if invalidated == "approval_expired":
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        monkeypatch.setattr(adoption, "_utc_now", lambda: future)
        expected_error = "APPROVAL_EXPIRED"
    elif invalidated == "lease_revoked":
        assert store._revoke_lease(leases, active[0])
        expected_error = "EXACT_LEASE_ISSUANCE_DENIED"
    elif invalidated == "payload_rebound":
        request = request.model_copy(
            update={
                "mutation": mutation.model_copy(
                    update={
                        "source_draft": NewsSignalSourceDraft(
                            safe_label="Unreviewed replacement", source_kind="official"
                        ),
                    }
                )
            }
        )
    else:
        NewsSignalsRepository(tmp_path).upsert_source(_source())
    before = store._snapshot_payload(_snapshot(store))
    with pytest.raises(NewsSignalsAdoptionError, match=expected_error):
        store.commit_mutation(request, idempotency_ref=key)
    assert store._snapshot_payload(_snapshot(store)) == before
    with store._read_connection() as conn:
        assert store._receipt_for_idempotency(conn, key) is None


@pytest.mark.parametrize("failure_stage", ["mutation", "rollback_or_close"])
def test_only_confirmed_hardening_rollback_retains_its_lease(
    tmp_path, monkeypatch, failure_stage
):
    store = NewsSignalsAdoptionStore(tmp_path)
    mutation = NewsSignalsAdoptionMutationRequest(
        action="register_source",
        expected_revision=0,
        source_draft=NewsSignalSourceDraft(
            safe_label="Reviewed retry", source_kind="official"
        ),
    )
    key = "idempotency-ref:q34:recovery:uncertain-rollback"
    request = _prepare(store, mutation, key)

    def fail_operation(*args, **kwargs):
        raise NewsSignalsAdoptionError("NEWS_SIGNALS_ADOPTION_DATABASE_FILE_UNSAFE")

    if failure_stage == "mutation":
        monkeypatch.setattr(store, "_apply_mutation", fail_operation)
    else:
        safe_connection = store._safe_connection

        @contextmanager
        def replaced_rollback_error():
            try:
                with safe_connection() as conn:
                    yield conn
            except NewsSignalsAdoptionError as exc:
                raise NewsSignalsAdoptionError(
                    "NEWS_SIGNALS_ADOPTION_DATABASE_STATE_INVALID"
                ) from exc

        monkeypatch.setattr(store, "_safe_connection", replaced_rollback_error)
        monkeypatch.setattr(store, "_harden_database_files", fail_operation)
    with pytest.raises(NewsSignalsAdoptionError):
        store.commit_mutation(request, idempotency_ref=key)
    leases = AuthorityLeaseStore(
        store.state_dir / "news_signals_authority"
    ).list_leases()
    assert len(leases) == 1 and leases[0].status == "revoked"
