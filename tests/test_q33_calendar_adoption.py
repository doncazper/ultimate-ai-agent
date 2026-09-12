from __future__ import annotations

import json
import os
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.authority.contracts import (
    evaluate_authority_request as evaluate_authority_request_contract,
)
from ultimate_ai_agent.core.control_center import (
    calendar_adoption as calendar_adoption_module,
)
from ultimate_ai_agent.core.control_center.calendar_adoption import (
    CALENDAR_ADOPTION_DATABASE_FILE,
    CALENDAR_ADOPTION_MAX_DATABASE_CLUSTER_BYTES,
    CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_FILE,
    CalendarAdoptionApprovalCaptureRequest,
    CalendarAdoptionCalendarDraft,
    CalendarAdoptionCommitRequest,
    CalendarAdoptionConflict,
    CalendarAdoptionError,
    CalendarAdoptionEventDraft,
    CalendarAdoptionMutationRequest,
    CalendarAdoptionPortableBackupRequest,
    CalendarAdoptionPortableRestoreRequest,
    CalendarAdoptionRestoreApprovalCaptureRequest,
    CalendarAdoptionRestoreCommitRequest,
    CalendarAdoptionStore,
)
from ultimate_ai_agent.core.ecosystem.calendar import CalendarRepository, CalendarView
from ultimate_ai_agent.core.ecosystem.local_data import EcosystemKeyUnavailable


def _idempotency(suffix: str) -> str:
    return f"idempotency-ref:q33-calendar-test:{suffix}"


def _calendar(
    suffix: str = "primary", *, timezone_name: str = "America/Los_Angeles"
) -> CalendarAdoptionCalendarDraft:
    return CalendarAdoptionCalendarDraft(
        calendar_ref=f"calendar-ref:q33:{suffix}",
        name=suffix.title(),
        timezone=timezone_name,
        color_ref=f"color-ref:q33:{suffix}",
    )


def _event(
    suffix: str,
    *,
    calendar_ref: str = "calendar-ref:q33:primary",
    starts_at: datetime | None = None,
) -> CalendarAdoptionEventDraft:
    starts = starts_at or datetime(2026, 9, 14, 16, tzinfo=timezone.utc)
    return CalendarAdoptionEventDraft(
        event_ref=f"calendar-event-ref:q33:{suffix}",
        calendar_ref=calendar_ref,
        title=f"Private {suffix} event",
        description="Founder-only planning details",
        location="Local office",
        starts_at=starts,
        ends_at=starts + timedelta(hours=1),
        timezone="America/Los_Angeles",
    )


def _commit(
    store: CalendarAdoptionStore,
    mutation: CalendarAdoptionMutationRequest,
    *,
    suffix: str,
):
    idempotency_ref = _idempotency(suffix)
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    approval = store.capture_approval(
        CalendarAdoptionApprovalCaptureRequest(
            mutation=mutation,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    receipt = store.commit_mutation(
        CalendarAdoptionCommitRequest(
            mutation=mutation,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    return preview, approval, receipt


def _initialize(store: CalendarAdoptionStore, *, suffix: str = "initialize") -> None:
    _commit(
        store,
        CalendarAdoptionMutationRequest(
            action="initialize",
            expected_revision=0,
            calendar=_calendar(),
        ),
        suffix=suffix,
    )


def test_empty_calendar_is_read_only_onboarding(tmp_path: Path) -> None:
    state_dir = tmp_path / "calendar"
    view = CalendarAdoptionStore(state_dir).read_view(
        view=CalendarView.week,
        anchor=datetime(2026, 9, 14, tzinfo=timezone.utc),
        timezone_name="America/Los_Angeles",
    )

    assert view.status == "onboarding"
    assert view.revision == 0
    assert view.calendars == ()
    assert view.occurrence_items == ()
    assert view.backend_owned is True
    assert view.local_only is True
    assert view.exact_approval_required is True
    assert view.external_calendar_write_enabled is False
    assert view.provider_model_call_enabled is False
    assert not state_dir.exists()


def test_corrupt_calendar_database_enters_recovery_required(tmp_path: Path) -> None:
    state_dir = tmp_path / "calendar"
    state_dir.mkdir()
    (state_dir / CALENDAR_ADOPTION_DATABASE_FILE).write_bytes(b"not a sqlite database")

    view = CalendarAdoptionStore(state_dir).read_view(
        view=CalendarView.week,
        anchor=datetime(2026, 9, 14, tzinfo=timezone.utc),
        timezone_name="America/Los_Angeles",
    )

    assert view.status == "recovery_required"
    assert view.revision == 0
    assert view.occurrence_items == ()
    assert view.backend_owned is True
    assert view.local_only is True
    assert view.exact_approval_required is True
    assert view.external_calendar_write_enabled is False
    assert view.provider_model_call_enabled is False
    assert state_dir.exists()


def test_unreadable_database_cluster_hashing_is_size_bounded(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "calendar"
    state_dir.mkdir()
    with (state_dir / CALENDAR_ADOPTION_DATABASE_FILE).open("wb") as handle:
        handle.truncate(CALENDAR_ADOPTION_MAX_DATABASE_CLUSTER_BYTES + 1)

    with pytest.raises(
        CalendarAdoptionError,
        match="CALENDAR_ADOPTION_DATABASE_CLUSTER_SIZE_LIMIT",
    ):
        CalendarAdoptionStore(state_dir)._database_cluster_state_ref()


def test_expired_uncommitted_checkpoints_are_reclaimable(tmp_path: Path) -> None:
    store = CalendarAdoptionStore(tmp_path)
    store._ensure_private_state_directory()
    expired_at = datetime(2026, 9, 1, tzinfo=timezone.utc)

    def checkpoint(index: int, *, expires_at: datetime):
        suffix = f"capacity-{index}"
        return calendar_adoption_module._CalendarAdoptionReceiptCheckpoint(
            action="initialize",
            target_ref="calendar-ref:q33:primary",
            before_revision=0,
            after_revision=1,
            idempotency_ref=_idempotency(suffix),
            payload_fingerprint_ref=f"payload-fingerprint-ref:q33:{suffix}",
            preview_ref=f"preview-ref:q33:{suffix}",
            approval_ref=f"approval-ref:q33:{suffix}",
            approval_validation_ref=(
                calendar_adoption_module._PENDING_APPROVAL_VALIDATION_REF
            ),
            approval_expires_at=expires_at,
            authority_decision_ref=(
                calendar_adoption_module._PENDING_AUTHORITY_DECISION_REF
            ),
            authority_lease_ref=(calendar_adoption_module._PENDING_AUTHORITY_LEASE_REF),
            operation_ref=f"operation-ref:q33:{suffix}",
        )

    expired = [
        checkpoint(index, expires_at=expired_at)
        for index in range(
            calendar_adoption_module.CALENDAR_ADOPTION_MAX_RECEIPT_CHECKPOINTS
        )
    ]
    store._write_receipt_checkpoints(expired)
    current = checkpoint(256, expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc))

    store._write_receipt_checkpoints([*expired, current])

    retained = store._read_receipt_checkpoints()
    assert (
        len(retained)
        == calendar_adoption_module.CALENDAR_ADOPTION_MAX_RECEIPT_CHECKPOINTS
    )
    assert store._checkpoint_for(retained, current.idempotency_ref) == current
    assert store._checkpoint_for(retained, expired[0].idempotency_ref) is None
    assert store._checkpoint_for(retained, expired[1].idempotency_ref) == expired[1]


def test_commit_requires_exact_captured_approval(tmp_path: Path) -> None:
    store = CalendarAdoptionStore(tmp_path)
    mutation = CalendarAdoptionMutationRequest(
        action="initialize", expected_revision=0, calendar=_calendar()
    )
    preview = store.preview_mutation(
        mutation, idempotency_ref=_idempotency("missing-approval")
    )

    with pytest.raises(
        CalendarAdoptionError, match="CALENDAR_ADOPTION_EXACT_APPROVAL_REQUIRED"
    ):
        store.commit_mutation(
            CalendarAdoptionCommitRequest(
                mutation=mutation,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
            ),
            idempotency_ref=_idempotency("missing-approval"),
        )

    assert store.read_view().status == "onboarding"
    assert not (tmp_path / CALENDAR_ADOPTION_DATABASE_FILE).exists()


def test_final_authority_denial_revokes_issued_calendar_lease(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    store = CalendarAdoptionStore(tmp_path)
    mutation = CalendarAdoptionMutationRequest(
        action="initialize", expected_revision=0, calendar=_calendar()
    )
    idempotency_ref = _idempotency("final-authority-denial")
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    request = CalendarAdoptionApprovalCaptureRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    store.capture_approval(request, idempotency_ref=idempotency_ref)

    def deny_final_evaluation(action_request, _leases):
        return evaluate_authority_request_contract(action_request, [])

    monkeypatch.setattr(
        calendar_adoption_module,
        "evaluate_authority_request",
        deny_final_evaluation,
    )
    with pytest.raises(
        CalendarAdoptionError, match="CALENDAR_ADOPTION_AUTHORITY_DENIED"
    ):
        store.commit_mutation(
            CalendarAdoptionCommitRequest(**request.model_dump()),
            idempotency_ref=idempotency_ref,
        )

    assert not AuthorityLeaseStore(tmp_path / "authority").list_leases(active_only=True)
    assert not (tmp_path / CALENDAR_ADOPTION_DATABASE_FILE).exists()


def test_restore_authority_denial_does_not_create_database(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = CalendarAdoptionStore(tmp_path / "source")
    _initialize(source, suffix="restore-denial-source")
    backup = source.create_portable_backup(
        CalendarAdoptionPortableBackupRequest(
            passphrase="founder private restore denial calendar"
        )
    )
    target_dir = tmp_path / "target"
    target = CalendarAdoptionStore(target_dir)
    idempotency_ref = _idempotency("restore-final-authority-denial")
    restore = CalendarAdoptionPortableRestoreRequest(
        passphrase="founder private restore denial calendar",
        backup=backup,
    )
    preview = target.preview_restore(restore, idempotency_ref=idempotency_ref)
    approval = target.capture_restore_approval(
        CalendarAdoptionRestoreApprovalCaptureRequest(
            **restore.model_dump(mode="python"),
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )

    def deny_final_evaluation(action_request, _leases):
        return evaluate_authority_request_contract(action_request, [])

    monkeypatch.setattr(
        calendar_adoption_module,
        "evaluate_authority_request",
        deny_final_evaluation,
    )
    with pytest.raises(
        CalendarAdoptionError, match="CALENDAR_ADOPTION_AUTHORITY_DENIED"
    ):
        target.commit_restore(
            CalendarAdoptionRestoreCommitRequest(
                **restore.model_dump(mode="python"),
                preview_ref=preview.preview_ref,
                approval_ref=approval.approval_ref,
            ),
            idempotency_ref=idempotency_ref,
        )

    assert not AuthorityLeaseStore(target_dir / "authority").list_leases(
        active_only=True
    )
    assert not (target_dir / CALENDAR_ADOPTION_DATABASE_FILE).exists()
    assert target.read_view().status == "onboarding"


def test_calendar_lifecycle_views_conflicts_and_undo_survive_restart(
    tmp_path: Path,
) -> None:
    store = CalendarAdoptionStore(tmp_path)
    _initialize(store)
    _commit(
        store,
        CalendarAdoptionMutationRequest(
            action="create_calendar",
            expected_revision=1,
            calendar=_calendar("work"),
        ),
        suffix="create-calendar",
    )
    first = _event("briefing")
    second = _event(
        "overlap",
        calendar_ref="calendar-ref:q33:work",
        starts_at=first.starts_at + timedelta(minutes=30),
    )
    _commit(
        store,
        CalendarAdoptionMutationRequest(
            action="create_event", expected_revision=2, event=first
        ),
        suffix="create-first",
    )
    _commit(
        store,
        CalendarAdoptionMutationRequest(
            action="create_event", expected_revision=3, event=second
        ),
        suffix="create-second",
    )

    restarted = CalendarAdoptionStore(tmp_path)
    week = restarted.read_view(
        view=CalendarView.week,
        anchor=first.starts_at,
        timezone_name="America/Los_Angeles",
    )
    assert week.status == "ready"
    assert week.revision == 4
    assert len(week.calendars) == 2
    assert len(week.occurrence_items) == 2
    assert len(week.conflict_items) == 1

    _commit(
        restarted,
        CalendarAdoptionMutationRequest(
            action="archive_event",
            expected_revision=4,
            target_ref=first.event_ref,
        ),
        suffix="archive",
    )
    archived = restarted.read_view(anchor=first.starts_at)
    assert archived.revision == 5
    assert [event.event_ref for event in archived.archived_events] == [first.event_ref]

    _commit(
        restarted,
        CalendarAdoptionMutationRequest(action="undo", expected_revision=5),
        suffix="undo",
    )
    recovered = restarted.read_view(anchor=first.starts_at)
    assert recovered.revision == 6
    assert recovered.archived_events == ()
    assert len(recovered.occurrence_items) == 2


def test_exact_idempotent_replay_rejects_substitution(tmp_path: Path) -> None:
    store = CalendarAdoptionStore(tmp_path)
    mutation = CalendarAdoptionMutationRequest(
        action="initialize", expected_revision=0, calendar=_calendar()
    )
    idempotency_ref = _idempotency("replay")
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    capture = CalendarAdoptionApprovalCaptureRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    store.capture_approval(capture, idempotency_ref=idempotency_ref)
    commit = CalendarAdoptionCommitRequest(**capture.model_dump())
    first = store.commit_mutation(commit, idempotency_ref=idempotency_ref)
    replay = CalendarAdoptionStore(tmp_path).commit_mutation(
        commit, idempotency_ref=idempotency_ref
    )

    assert first.replayed is False
    assert replay.replayed is True
    assert replay.receipt_ref == first.receipt_ref
    assert replay.authority_decision_ref == first.authority_decision_ref
    assert store.read_view().revision == 1

    with pytest.raises(
        CalendarAdoptionConflict, match="CALENDAR_ADOPTION_IDEMPOTENCY_CONFLICT"
    ):
        store.commit_mutation(
            commit.model_copy(
                update={"preview_ref": "preview-ref:q33-calendar:substituted"}
            ),
            idempotency_ref=idempotency_ref,
        )


def test_mutation_commit_translates_damaged_checkpoint_recovery(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    store = CalendarAdoptionStore(tmp_path)
    mutation = CalendarAdoptionMutationRequest(
        action="initialize", expected_revision=0, calendar=_calendar()
    )
    idempotency_ref = _idempotency("damaged-mutation-recovery")
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    capture = CalendarAdoptionApprovalCaptureRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    store.capture_approval(capture, idempotency_ref=idempotency_ref)
    commit = CalendarAdoptionCommitRequest(**capture.model_dump(mode="python"))
    store.commit_mutation(commit, idempotency_ref=idempotency_ref)

    def unavailable_receipt(_repository: CalendarRepository, **_kwargs: object):
        raise EcosystemKeyUnavailable("ECO_KEY_NOT_FOUND")

    monkeypatch.setattr(
        CalendarRepository,
        "recover_create_receipt",
        unavailable_receipt,
    )
    with pytest.raises(
        CalendarAdoptionError,
        match="CALENDAR_ADOPTION_CURRENT_STATE_UNREADABLE",
    ):
        store.commit_mutation(commit, idempotency_ref=idempotency_ref)


@pytest.mark.parametrize("target_kind", ["event", "calendar"])
def test_update_replay_binds_original_lifecycle_state(
    tmp_path: Path,
    target_kind: str,
) -> None:
    store = CalendarAdoptionStore(tmp_path / target_kind)
    _initialize(store, suffix=f"{target_kind}-lifecycle-initialize")
    if target_kind == "event":
        draft = _event("lifecycle-replay")
        _commit(
            store,
            CalendarAdoptionMutationRequest(
                action="create_event",
                expected_revision=1,
                event=draft,
            ),
            suffix="event-lifecycle-create",
        )
        update = CalendarAdoptionMutationRequest(
            action="update_event",
            expected_revision=2,
            target_ref=draft.event_ref,
            event=draft.model_copy(update={"title": "Updated before archive"}),
        )
        lifecycle_action = "archive_event"
        target_ref = draft.event_ref
    else:
        draft = _calendar("lifecycle-replay")
        _commit(
            store,
            CalendarAdoptionMutationRequest(
                action="create_calendar",
                expected_revision=1,
                calendar=draft,
            ),
            suffix="calendar-lifecycle-create",
        )
        update = CalendarAdoptionMutationRequest(
            action="update_calendar",
            expected_revision=2,
            target_ref=draft.calendar_ref,
            calendar=draft.model_copy(update={"name": "Updated before archive"}),
        )
        lifecycle_action = "archive_calendar"
        target_ref = draft.calendar_ref

    idempotency_ref = _idempotency(f"{target_kind}-lifecycle-update")
    preview = store.preview_mutation(update, idempotency_ref=idempotency_ref)
    capture = CalendarAdoptionApprovalCaptureRequest(
        mutation=update,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    store.capture_approval(capture, idempotency_ref=idempotency_ref)
    commit = CalendarAdoptionCommitRequest(**capture.model_dump(mode="python"))
    first = store.commit_mutation(commit, idempotency_ref=idempotency_ref)
    _commit(
        store,
        CalendarAdoptionMutationRequest(
            action=lifecycle_action,
            expected_revision=3,
            target_ref=target_ref,
        ),
        suffix=f"{target_kind}-lifecycle-archive",
    )

    replay = CalendarAdoptionStore(store.state_dir).commit_mutation(
        commit,
        idempotency_ref=idempotency_ref,
    )

    assert replay.replayed is True
    assert replay.receipt_ref == first.receipt_ref
    assert CalendarAdoptionStore(store.state_dir).read_view().revision == 4


def test_approval_capture_binds_idempotency_before_commit(tmp_path: Path) -> None:
    store = CalendarAdoptionStore(tmp_path)
    _initialize(store)
    idempotency_ref = _idempotency("approval-binding")
    first = CalendarAdoptionMutationRequest(
        action="create_event",
        expected_revision=1,
        event=_event("first-approval"),
    )
    first_preview = store.preview_mutation(first, idempotency_ref=idempotency_ref)
    store.capture_approval(
        CalendarAdoptionApprovalCaptureRequest(
            mutation=first,
            preview_ref=first_preview.preview_ref,
            approval_ref=first_preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    second = first.model_copy(update={"event": _event("second-approval")})
    second_preview = store.preview_mutation(second, idempotency_ref=idempotency_ref)

    with pytest.raises(
        CalendarAdoptionConflict, match="CALENDAR_ADOPTION_IDEMPOTENCY_CONFLICT"
    ):
        store.capture_approval(
            CalendarAdoptionApprovalCaptureRequest(
                mutation=second,
                preview_ref=second_preview.preview_ref,
                approval_ref=second_preview.approval_ref,
            ),
            idempotency_ref=idempotency_ref,
        )


def test_restore_approval_capture_binds_idempotency_before_commit(
    tmp_path: Path,
) -> None:
    source = CalendarAdoptionStore(tmp_path / "source")
    _initialize(source, suffix="restore-binding-source")
    first_backup = source.create_portable_backup(
        CalendarAdoptionPortableBackupRequest(
            passphrase="founder private first restore binding"
        )
    )
    _commit(
        source,
        CalendarAdoptionMutationRequest(
            action="create_event",
            expected_revision=1,
            event=_event("restore-binding-source-event"),
        ),
        suffix="restore-binding-source-event",
    )
    second_backup = source.create_portable_backup(
        CalendarAdoptionPortableBackupRequest(
            passphrase="founder private second restore binding"
        )
    )
    target = CalendarAdoptionStore(tmp_path / "target")
    idempotency_ref = _idempotency("restore-approval-binding")
    first = CalendarAdoptionPortableRestoreRequest(
        passphrase="founder private first restore binding",
        backup=first_backup,
    )
    first_preview = target.preview_restore(first, idempotency_ref=idempotency_ref)
    target.capture_restore_approval(
        CalendarAdoptionRestoreApprovalCaptureRequest(
            **first.model_dump(mode="python"),
            preview_ref=first_preview.preview_ref,
            approval_ref=first_preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    second = CalendarAdoptionPortableRestoreRequest(
        passphrase="founder private second restore binding",
        backup=second_backup,
    )
    second_preview = target.preview_restore(second, idempotency_ref=idempotency_ref)

    with pytest.raises(
        CalendarAdoptionConflict, match="CALENDAR_ADOPTION_IDEMPOTENCY_CONFLICT"
    ):
        target.capture_restore_approval(
            CalendarAdoptionRestoreApprovalCaptureRequest(
                **second.model_dump(mode="python"),
                preview_ref=second_preview.preview_ref,
                approval_ref=second_preview.approval_ref,
            ),
            idempotency_ref=idempotency_ref,
        )


def test_replay_rejects_checkpoint_receipt_substitution(tmp_path: Path) -> None:
    store = CalendarAdoptionStore(tmp_path)
    mutation = CalendarAdoptionMutationRequest(
        action="initialize", expected_revision=0, calendar=_calendar()
    )
    idempotency_ref = _idempotency("forged-checkpoint")
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    capture = CalendarAdoptionApprovalCaptureRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    store.capture_approval(capture, idempotency_ref=idempotency_ref)
    commit = CalendarAdoptionCommitRequest(**capture.model_dump())
    store.commit_mutation(commit, idempotency_ref=idempotency_ref)

    checkpoint_path = tmp_path / CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_FILE
    payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    payload[0]["receipt"]["receipt_ref"] = "receipt-ref:forged-checkpoint"
    checkpoint_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        CalendarAdoptionError,
        match="CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_DURABLE_MISMATCH",
    ):
        CalendarAdoptionStore(tmp_path).commit_mutation(
            commit,
            idempotency_ref=idempotency_ref,
        )


def test_lost_response_recovers_durable_receipt_without_second_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    store = CalendarAdoptionStore(tmp_path)
    mutation = CalendarAdoptionMutationRequest(
        action="initialize", expected_revision=0, calendar=_calendar()
    )
    idempotency_ref = _idempotency("lost-response")
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    capture = CalendarAdoptionApprovalCaptureRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    store.capture_approval(capture, idempotency_ref=idempotency_ref)
    commit = CalendarAdoptionCommitRequest(**capture.model_dump())
    original = store._save_checkpoint
    calls = 0

    def fail_completion(checkpoints: list[object], checkpoint: object) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise CalendarAdoptionError("CALENDAR_ADOPTION_TEST_RESPONSE_LOST")
        original(checkpoints, checkpoint)  # type: ignore[arg-type]

    monkeypatch.setattr(store, "_save_checkpoint", fail_completion)
    with pytest.raises(
        CalendarAdoptionError, match="CALENDAR_ADOPTION_TEST_RESPONSE_LOST"
    ):
        store.commit_mutation(commit, idempotency_ref=idempotency_ref)

    assert not AuthorityLeaseStore(tmp_path / "authority").list_leases(active_only=True)
    recovered = CalendarAdoptionStore(tmp_path).commit_mutation(
        commit, idempotency_ref=idempotency_ref
    )
    assert recovered.replayed is True
    assert recovered.after_revision == 1
    assert CalendarAdoptionStore(tmp_path).read_view().revision == 1


def test_lost_restore_response_revokes_lease_and_recovers_receipt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = CalendarAdoptionStore(tmp_path / "source")
    _initialize(source, suffix="lost-restore-source")
    passphrase = "founder private lost restore response"
    backup = source.create_portable_backup(
        CalendarAdoptionPortableBackupRequest(passphrase=passphrase)
    )
    target_dir = tmp_path / "target"
    target = CalendarAdoptionStore(target_dir)
    idempotency_ref = _idempotency("lost-restore-response")
    restore = CalendarAdoptionPortableRestoreRequest(
        passphrase=passphrase,
        backup=backup,
    )
    preview = target.preview_restore(restore, idempotency_ref=idempotency_ref)
    target.capture_restore_approval(
        CalendarAdoptionRestoreApprovalCaptureRequest(
            **restore.model_dump(mode="python"),
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    commit = CalendarAdoptionRestoreCommitRequest(
        **restore.model_dump(mode="python"),
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    original = target._save_checkpoint
    calls = 0

    def fail_completion(checkpoints: list[object], checkpoint: object) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise CalendarAdoptionError("CALENDAR_ADOPTION_TEST_RESPONSE_LOST")
        original(checkpoints, checkpoint)  # type: ignore[arg-type]

    monkeypatch.setattr(target, "_save_checkpoint", fail_completion)
    with pytest.raises(
        CalendarAdoptionError, match="CALENDAR_ADOPTION_TEST_RESPONSE_LOST"
    ):
        target.commit_restore(commit, idempotency_ref=idempotency_ref)

    assert not AuthorityLeaseStore(target_dir / "authority").list_leases(
        active_only=True
    )
    recovered = CalendarAdoptionStore(target_dir).commit_restore(
        commit, idempotency_ref=idempotency_ref
    )
    assert recovered.replayed is True
    assert recovered.after_revision == 1
    assert CalendarAdoptionStore(target_dir).read_view().revision == 1


def test_restore_replaces_corrupt_current_database_after_exact_approval(
    tmp_path: Path,
) -> None:
    source = CalendarAdoptionStore(tmp_path / "source")
    _initialize(source, suffix="corrupt-restore-source")
    passphrase = "founder private corrupt restore response"
    backup = source.create_portable_backup(
        CalendarAdoptionPortableBackupRequest(passphrase=passphrase)
    )
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    (target_dir / CALENDAR_ADOPTION_DATABASE_FILE).write_bytes(b"not sqlite")
    target = CalendarAdoptionStore(target_dir)
    restore = CalendarAdoptionPortableRestoreRequest(
        passphrase=passphrase,
        backup=backup,
    )
    idempotency_ref = _idempotency("corrupt-restore-target")
    preview = target.preview_restore(restore, idempotency_ref=idempotency_ref)
    assert preview.impact_status == "unknown_current_state"
    assert preview.rollback_available is False
    capture = CalendarAdoptionRestoreApprovalCaptureRequest(
        **restore.model_dump(mode="python"),
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    target.capture_restore_approval(capture, idempotency_ref=idempotency_ref)
    commit = CalendarAdoptionRestoreCommitRequest(**capture.model_dump(mode="python"))
    receipt = target.commit_restore(commit, idempotency_ref=idempotency_ref)

    assert receipt.before_revision == 0
    assert receipt.after_revision == 1
    assert target.read_view().status == "ready"
    replay = target.commit_restore(commit, idempotency_ref=idempotency_ref)
    assert replay.replayed is True
    assert replay.receipt_ref == receipt.receipt_ref


def test_restore_commit_translates_damaged_checkpoint_recovery(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = CalendarAdoptionStore(tmp_path / "source")
    _initialize(source, suffix="damaged-recovery-source")
    passphrase = "founder private damaged checkpoint recovery"
    backup = source.create_portable_backup(
        CalendarAdoptionPortableBackupRequest(passphrase=passphrase)
    )
    target = CalendarAdoptionStore(tmp_path / "target")
    _initialize(target, suffix="damaged-recovery-target")
    restore = CalendarAdoptionPortableRestoreRequest(
        passphrase=passphrase,
        backup=backup,
    )
    idempotency_ref = _idempotency("damaged-restore-recovery")
    preview = target.preview_restore(restore, idempotency_ref=idempotency_ref)
    capture = CalendarAdoptionRestoreApprovalCaptureRequest(
        **restore.model_dump(mode="python"),
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    target.capture_restore_approval(capture, idempotency_ref=idempotency_ref)

    def unavailable_receipt(_repository: CalendarRepository, **_kwargs: object):
        raise EcosystemKeyUnavailable("ECO_KEY_NOT_FOUND")

    monkeypatch.setattr(
        CalendarRepository,
        "recover_mutation_receipt",
        unavailable_receipt,
    )
    with pytest.raises(
        CalendarAdoptionError,
        match="CALENDAR_ADOPTION_CURRENT_STATE_UNREADABLE",
    ):
        target.commit_restore(
            CalendarAdoptionRestoreCommitRequest(**capture.model_dump(mode="python")),
            idempotency_ref=idempotency_ref,
        )


def test_lost_response_recovers_archived_event_and_calendar_updates(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def commit_with_lost_completion(
        store: CalendarAdoptionStore,
        mutation: CalendarAdoptionMutationRequest,
        *,
        suffix: str,
    ):
        idempotency_ref = _idempotency(suffix)
        preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
        capture = CalendarAdoptionApprovalCaptureRequest(
            mutation=mutation,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        )
        store.capture_approval(capture, idempotency_ref=idempotency_ref)
        commit = CalendarAdoptionCommitRequest(**capture.model_dump())
        original = store._save_checkpoint
        calls = 0

        def fail_completion(checkpoints: list[object], checkpoint: object) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise CalendarAdoptionError("CALENDAR_ADOPTION_TEST_RESPONSE_LOST")
            original(checkpoints, checkpoint)  # type: ignore[arg-type]

        monkeypatch.setattr(store, "_save_checkpoint", fail_completion)
        with pytest.raises(
            CalendarAdoptionError, match="CALENDAR_ADOPTION_TEST_RESPONSE_LOST"
        ):
            store.commit_mutation(commit, idempotency_ref=idempotency_ref)
        return commit, idempotency_ref

    event_store = CalendarAdoptionStore(tmp_path / "event")
    _initialize(event_store, suffix="archived-event-initialize")
    archived_event = _event("lost-archived-update")
    _commit(
        event_store,
        CalendarAdoptionMutationRequest(
            action="create_event", expected_revision=1, event=archived_event
        ),
        suffix="archived-event-create",
    )
    _commit(
        event_store,
        CalendarAdoptionMutationRequest(
            action="archive_event",
            expected_revision=2,
            target_ref=archived_event.event_ref,
        ),
        suffix="archived-event-archive",
    )
    event_commit, event_idempotency = commit_with_lost_completion(
        event_store,
        CalendarAdoptionMutationRequest(
            action="update_event",
            expected_revision=3,
            target_ref=archived_event.event_ref,
            event=archived_event.model_copy(update={"title": "Updated while archived"}),
        ),
        suffix="archived-event-update",
    )
    event_replay = CalendarAdoptionStore(event_store.state_dir).commit_mutation(
        event_commit,
        idempotency_ref=event_idempotency,
    )
    assert event_replay.replayed is True
    assert event_replay.after_revision == 4
    assert CalendarAdoptionStore(event_store.state_dir).read_view().revision == 4

    calendar_store = CalendarAdoptionStore(tmp_path / "calendar")
    _initialize(calendar_store, suffix="archived-calendar-initialize")
    archived_calendar = _calendar("archived-update")
    _commit(
        calendar_store,
        CalendarAdoptionMutationRequest(
            action="create_calendar",
            expected_revision=1,
            calendar=archived_calendar,
        ),
        suffix="archived-calendar-create",
    )
    _commit(
        calendar_store,
        CalendarAdoptionMutationRequest(
            action="archive_calendar",
            expected_revision=2,
            target_ref=archived_calendar.calendar_ref,
        ),
        suffix="archived-calendar-archive",
    )
    calendar_commit, calendar_idempotency = commit_with_lost_completion(
        calendar_store,
        CalendarAdoptionMutationRequest(
            action="update_calendar",
            expected_revision=3,
            target_ref=archived_calendar.calendar_ref,
            calendar=archived_calendar.model_copy(
                update={"name": "Updated Archived Calendar"}
            ),
        ),
        suffix="archived-calendar-update",
    )
    calendar_replay = CalendarAdoptionStore(calendar_store.state_dir).commit_mutation(
        calendar_commit,
        idempotency_ref=calendar_idempotency,
    )
    assert calendar_replay.replayed is True
    assert calendar_replay.after_revision == 4
    assert CalendarAdoptionStore(calendar_store.state_dir).read_view().revision == 4


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("approval_validation_ref", "forged-decision"),
        ("approval_validation_ref", "appr_dec_deadbeefcafe"),
        ("approval_expires_at", "2099-01-01T00:00:00"),
    ],
)
def test_tampered_checkpoint_approval_evidence_fails_closed(
    tmp_path: Path, field: str, value: str
) -> None:
    store = CalendarAdoptionStore(tmp_path)
    mutation = CalendarAdoptionMutationRequest(
        action="initialize", expected_revision=0, calendar=_calendar()
    )
    idempotency_ref = _idempotency(f"tampered-{field}-{value}")
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    capture = CalendarAdoptionApprovalCaptureRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    store.capture_approval(capture, idempotency_ref=idempotency_ref)
    store.commit_mutation(
        CalendarAdoptionCommitRequest(**capture.model_dump()),
        idempotency_ref=idempotency_ref,
    )
    checkpoint_path = tmp_path / CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_FILE
    payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    payload[0][field] = value
    checkpoint_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        CalendarAdoptionError,
        match="CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_INVALID",
    ):
        CalendarAdoptionStore(tmp_path).capture_approval(
            capture,
            idempotency_ref=idempotency_ref,
        )


def test_private_values_are_encrypted_and_receipts_are_content_free(
    tmp_path: Path,
) -> None:
    store = CalendarAdoptionStore(tmp_path)
    _initialize(store)
    private_title = "Private acquisition discussion 7ef245"
    event = _event("encrypted")
    event = event.model_copy(update={"title": private_title})
    _commit(
        store,
        CalendarAdoptionMutationRequest(
            action="create_event", expected_revision=1, event=event
        ),
        suffix="encrypted-event",
    )

    assert (
        private_title.encode()
        not in (tmp_path / CALENDAR_ADOPTION_DATABASE_FILE).read_bytes()
    )
    assert (
        private_title.encode()
        not in (tmp_path / CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_FILE).read_bytes()
    )
    assert (
        CalendarAdoptionStore(tmp_path)
        .read_view(anchor=event.starts_at)
        .occurrence_items[0]
        .event.title
        == private_title
    )


def test_encrypted_backup_restores_to_new_computer_and_replays(tmp_path: Path) -> None:
    source = CalendarAdoptionStore(tmp_path / "source")
    _initialize(source)
    event = _event("portable")
    _commit(
        source,
        CalendarAdoptionMutationRequest(
            action="create_event", expected_revision=1, event=event
        ),
        suffix="portable-event",
    )
    backup = source.create_portable_backup(
        CalendarAdoptionPortableBackupRequest(
            passphrase="founder private portable calendar"
        )
    )
    target = CalendarAdoptionStore(tmp_path / "target")
    idempotency_ref = _idempotency("restore")
    request = CalendarAdoptionPortableRestoreRequest(
        passphrase="founder private portable calendar", backup=backup
    )
    preview = target.preview_restore(request, idempotency_ref=idempotency_ref)
    approval = target.capture_restore_approval(
        CalendarAdoptionRestoreApprovalCaptureRequest(
            **request.model_dump(mode="python"),
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    commit = CalendarAdoptionRestoreCommitRequest(
        **request.model_dump(mode="python"),
        preview_ref=preview.preview_ref,
        approval_ref=approval.approval_ref,
    )
    receipt = target.commit_restore(commit, idempotency_ref=idempotency_ref)
    replay = target.commit_restore(commit, idempotency_ref=idempotency_ref)

    restored = target.read_view(anchor=event.starts_at)
    assert receipt.before_revision == 0
    assert receipt.after_revision == 1
    assert receipt.backup_fingerprint_ref == backup.ciphertext_fingerprint_ref
    assert replay.replayed is True
    assert restored.occurrence_items[0].event.title == event.title
    assert restored.external_calendar_write_enabled is False

    with pytest.raises(
        CalendarAdoptionError, match="CALENDAR_ADOPTION_BACKUP_DECRYPT_FAILED"
    ):
        target.preview_restore(
            CalendarAdoptionPortableRestoreRequest(
                passphrase="incorrect portable passphrase", backup=backup
            ),
            idempotency_ref=_idempotency("wrong-passphrase"),
        )

    with pytest.raises(
        CalendarAdoptionError, match="CALENDAR_ADOPTION_BACKUP_METADATA_MISMATCH"
    ):
        target.preview_restore(
            CalendarAdoptionPortableRestoreRequest(
                passphrase="founder private portable calendar",
                backup=backup.model_copy(
                    update={"source_revision": backup.source_revision + 1}
                ),
            ),
            idempotency_ref=_idempotency("forged-backup-metadata"),
        )


def test_restore_translates_decrypted_json_recursion_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = CalendarAdoptionStore(tmp_path / "source-recursion")
    _initialize(source, suffix="backup-recursion-initialize")
    passphrase = "founder private recursive backup"
    backup = source.create_portable_backup(
        CalendarAdoptionPortableBackupRequest(passphrase=passphrase)
    )

    def raise_recursion(_value: object) -> object:
        raise RecursionError("nested payload")

    monkeypatch.setattr(calendar_adoption_module.json, "loads", raise_recursion)
    with pytest.raises(
        CalendarAdoptionError,
        match="CALENDAR_ADOPTION_BACKUP_DECRYPT_FAILED",
    ):
        CalendarAdoptionStore(tmp_path / "target-recursion").preview_restore(
            CalendarAdoptionPortableRestoreRequest(
                passphrase=passphrase,
                backup=backup,
            ),
            idempotency_ref=_idempotency("recursive-backup"),
        )


def test_encrypted_backup_restores_from_setup_incomplete_state(tmp_path: Path) -> None:
    source = CalendarAdoptionStore(tmp_path / "source")
    _initialize(source)
    backup = source.create_portable_backup(
        CalendarAdoptionPortableBackupRequest(
            passphrase="founder private setup recovery calendar"
        )
    )
    target = CalendarAdoptionStore(tmp_path / "target")
    target._repository()
    assert target.read_view().status == "setup_incomplete"

    idempotency_ref = _idempotency("setup-incomplete-restore")
    restore = CalendarAdoptionPortableRestoreRequest(
        passphrase="founder private setup recovery calendar",
        backup=backup,
    )
    preview = target.preview_restore(restore, idempotency_ref=idempotency_ref)
    approval = target.capture_restore_approval(
        CalendarAdoptionRestoreApprovalCaptureRequest(
            **restore.model_dump(mode="python"),
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    target.commit_restore(
        CalendarAdoptionRestoreCommitRequest(
            **restore.model_dump(mode="python"),
            preview_ref=preview.preview_ref,
            approval_ref=approval.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )

    assert target.read_view().status == "ready"


def test_restore_preview_only_advertises_undo_when_bounded_history_keeps_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = CalendarAdoptionStore(tmp_path / "source")
    target = CalendarAdoptionStore(tmp_path / "target")
    _initialize(source, suffix="source-initialize")
    _initialize(target, suffix="target-initialize")
    backup = source.create_portable_backup(
        CalendarAdoptionPortableBackupRequest(
            passphrase="founder private bounded restore calendar"
        )
    )
    request = CalendarAdoptionPortableRestoreRequest(
        passphrase="founder private bounded restore calendar",
        backup=backup,
    )

    monkeypatch.setattr(
        CalendarRepository,
        "_record_plaintext_size",
        staticmethod(
            lambda calendar_set: 2 * 1024 * 1024 if calendar_set.undo_stack else 1
        ),
    )
    idempotency_ref = _idempotency("bounded-restore")
    preview = target.preview_restore(request, idempotency_ref=idempotency_ref)

    assert preview.expected_revision == 1
    assert preview.impact_status == "exact"
    assert preview.rollback_available is False
    approval = target.capture_restore_approval(
        CalendarAdoptionRestoreApprovalCaptureRequest(
            **request.model_dump(mode="python"),
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    target.commit_restore(
        CalendarAdoptionRestoreCommitRequest(
            **request.model_dump(mode="python"),
            preview_ref=preview.preview_ref,
            approval_ref=approval.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    assert target.read_view().can_undo is False


def test_invalid_timezone_fails_closed_before_reading_state(tmp_path: Path) -> None:
    with pytest.raises(
        CalendarAdoptionError, match="CALENDAR_ADOPTION_TIMEZONE_INVALID"
    ):
        CalendarAdoptionStore(tmp_path).read_view(
            timezone_name="Invalid/Founder-Timezone"
        )


def test_database_metadata_access_failure_uses_calendar_safe_code(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    store = CalendarAdoptionStore(tmp_path / "calendar")
    store.state_dir.mkdir(parents=True)
    real_lstat = os.lstat

    def fail_database_lstat(path):
        if Path(path) == store.database_path:
            raise PermissionError("calendar database metadata unavailable")
        return real_lstat(path)

    monkeypatch.setattr(os, "lstat", fail_database_lstat)

    with pytest.raises(
        CalendarAdoptionError, match="CALENDAR_ADOPTION_STATE_OBJECT_UNSAFE"
    ):
        store.read_view()


@pytest.mark.skipif(os.name == "nt", reason="POSIX link contract")
def test_checkpoint_symlink_and_hardlink_fail_closed(tmp_path: Path) -> None:
    linked = tmp_path / "linked"
    linked.mkdir()
    target = tmp_path / "target.json"
    target.write_text("[]", encoding="utf-8")
    (linked / CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_FILE).symlink_to(target)
    with pytest.raises(
        CalendarAdoptionError, match="CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_INVALID"
    ):
        CalendarAdoptionStore(linked)._read_receipt_checkpoints()

    hardlinked = tmp_path / "hardlinked"
    hardlinked.mkdir()
    os.link(target, hardlinked / CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_FILE)
    with pytest.raises(
        CalendarAdoptionError, match="CALENDAR_ADOPTION_RECEIPT_CHECKPOINT_INVALID"
    ):
        CalendarAdoptionStore(hardlinked)._read_receipt_checkpoints()


@pytest.mark.skipif(os.name == "nt", reason="POSIX link contract")
def test_state_directory_root_symlink_fails_before_target_permissions_change(
    tmp_path: Path,
) -> None:
    target = tmp_path / "unrelated"
    target.mkdir(mode=0o755)
    marker = target / "user-file.txt"
    marker.write_text("unrelated", encoding="utf-8")
    marker.chmod(0o644)
    linked = tmp_path / "calendar"
    linked.symlink_to(target, target_is_directory=True)

    store = CalendarAdoptionStore(linked)
    assert store.state_dir == linked.absolute()
    with pytest.raises(
        CalendarAdoptionError,
        match="CALENDAR_ADOPTION_STATE_DIRECTORY_UNSAFE",
    ):
        store.preview_mutation(
            CalendarAdoptionMutationRequest(
                action="initialize",
                expected_revision=0,
                calendar=_calendar(),
            ),
            idempotency_ref=_idempotency("root-symlink"),
        )

    assert stat.S_IMODE(target.stat().st_mode) == 0o755
    assert stat.S_IMODE(marker.stat().st_mode) == 0o644


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission contract")
def test_existing_broad_state_root_is_rejected_before_permissions_change(
    tmp_path: Path,
) -> None:
    broad = tmp_path / "shared"
    broad.mkdir(mode=0o755)
    marker = broad / "user-file.txt"
    marker.write_text("unrelated", encoding="utf-8")
    marker.chmod(0o644)

    with pytest.raises(
        CalendarAdoptionError,
        match="CALENDAR_ADOPTION_STATE_DIRECTORY_UNSAFE",
    ):
        CalendarAdoptionStore(broad).preview_mutation(
            CalendarAdoptionMutationRequest(
                action="initialize",
                expected_revision=0,
                calendar=_calendar(),
            ),
            idempotency_ref=_idempotency("broad-root"),
        )

    assert stat.S_IMODE(broad.stat().st_mode) == 0o755
    assert stat.S_IMODE(marker.stat().st_mode) == 0o644


@pytest.mark.skipif(os.name == "nt", reason="POSIX root contract")
def test_shallow_state_root_is_rejected_without_home_directory_access() -> None:
    store = CalendarAdoptionStore(Path("/"))

    with pytest.raises(
        CalendarAdoptionError,
        match="CALENDAR_ADOPTION_STATE_DIRECTORY_UNSAFE",
    ):
        store._validate_state_tree_before_permission_change()
