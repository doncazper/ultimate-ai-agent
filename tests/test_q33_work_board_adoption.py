from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

import ultimate_ai_agent.core.control_center.work_board_adoption as work_board_adoption
import ultimate_ai_agent.core.single_writer_lock as single_writer_lock
from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.control_center.work_board_adoption import (
    WORK_BOARD_ADOPTION_RESTORE_ROUTE_REF,
    WORK_BOARD_ADOPTION_STATE_FILE,
    WorkBoardAdoptionApprovalCaptureRequest,
    WorkBoardAdoptionCardDraft,
    WorkBoardAdoptionCommitRequest,
    WorkBoardAdoptionConflict,
    WorkBoardAdoptionError,
    WorkBoardAdoptionMutationRequest,
    WorkBoardAdoptionPortableBackupRequest,
    WorkBoardAdoptionPortableRestoreRequest,
    WorkBoardAdoptionRestoreApprovalCaptureRequest,
    WorkBoardAdoptionRestoreCommitRequest,
    WorkBoardAdoptionState,
    WorkBoardAdoptionStore,
)
from ultimate_ai_agent.core.single_writer_lock import FileSingleWriterLockManager


def _idempotency(suffix: str) -> str:
    return f"idempotency-ref:q33-work-board-test:{suffix}"


def _commit(
    store: WorkBoardAdoptionStore,
    mutation: WorkBoardAdoptionMutationRequest,
    *,
    suffix: str,
):
    idempotency_ref = _idempotency(suffix)
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    approval = store.capture_approval(
        WorkBoardAdoptionApprovalCaptureRequest(
            mutation=mutation,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    receipt = store.commit_mutation(
        WorkBoardAdoptionCommitRequest(
            mutation=mutation,
            preview_ref=preview.preview_ref,
            approval_ref=approval.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    return preview, approval, receipt


def _draft(
    title: str = "Prepare founder briefing",
    *,
    lane_ref: str = "work-board-lane:inbox",
) -> WorkBoardAdoptionCardDraft:
    return WorkBoardAdoptionCardDraft(
        title=title,
        description="Collect the locally reviewed evidence before the briefing.",
        priority="high",
        lane_ref=lane_ref,
        tag_refs=("tag-ref:founder", "tag-ref:briefing"),
    )


def test_empty_work_board_is_backend_owned_and_ready(tmp_path: Path) -> None:
    view = WorkBoardAdoptionStore(tmp_path).read_view()

    assert view.status == "ready"
    assert view.revision == 0
    assert view.active_cards == ()
    assert view.archived_cards == ()
    assert view.can_undo is False
    assert view.backend_owned is True
    assert view.local_only is True
    assert view.exact_approval_required is True
    assert view.task_execution_enabled is False
    assert view.connector_write_enabled is False
    assert view.provider_model_call_enabled is False
    assert not (tmp_path / ".locks").exists()


def test_preview_is_non_mutating_and_exact_scope_bound(tmp_path: Path) -> None:
    store = WorkBoardAdoptionStore(tmp_path)
    mutation = WorkBoardAdoptionMutationRequest(
        action="create",
        expected_revision=0,
        draft=_draft(),
    )

    preview = store.preview_mutation(mutation, idempotency_ref=_idempotency("preview"))

    assert preview.mutation_performed is False
    assert preview.external_write_performed is False
    assert preview.expected_revision == 0
    assert preview.resulting_revision == 1
    assert preview.card_ref is not None
    assert store.read_view().revision == 0
    assert not (tmp_path / WORK_BOARD_ADOPTION_STATE_FILE).exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission-mode contract")
def test_preview_repairs_private_state_directory_mode_before_locking(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "work_board"
    state_dir.mkdir(mode=0o755)
    os.chmod(state_dir, 0o755)
    store = WorkBoardAdoptionStore(state_dir)

    store.preview_mutation(
        WorkBoardAdoptionMutationRequest(
            action="create",
            expected_revision=0,
            draft=_draft(),
        ),
        idempotency_ref=_idempotency("private-directory-mode"),
    )

    assert stat.S_IMODE(state_dir.stat().st_mode) == 0o700
    assert not (state_dir / WORK_BOARD_ADOPTION_STATE_FILE).exists()


def test_commit_requires_captured_exact_approval(tmp_path: Path) -> None:
    store = WorkBoardAdoptionStore(tmp_path)
    mutation = WorkBoardAdoptionMutationRequest(
        action="create",
        expected_revision=0,
        draft=_draft(),
    )
    preview = store.preview_mutation(
        mutation,
        idempotency_ref=_idempotency("missing-approval"),
    )

    with pytest.raises(
        WorkBoardAdoptionError,
        match="WORK_BOARD_ADOPTION_EXACT_APPROVAL_REQUIRED",
    ):
        store.commit_mutation(
            WorkBoardAdoptionCommitRequest(
                mutation=mutation,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
            ),
            idempotency_ref=_idempotency("missing-approval"),
        )

    assert store.read_view().revision == 0


def test_founder_private_card_lifecycle_survives_restart(tmp_path: Path) -> None:
    store = WorkBoardAdoptionStore(tmp_path)
    _, _, created = _commit(
        store,
        WorkBoardAdoptionMutationRequest(
            action="create",
            expected_revision=0,
            draft=_draft(),
        ),
        suffix="create",
    )
    assert created.card_ref is not None
    card_ref = created.card_ref

    restarted = WorkBoardAdoptionStore(tmp_path)
    view = restarted.read_view()
    assert view.revision == 1
    assert [card.card_ref for card in view.active_cards] == [card_ref]
    assert view.active_cards[0].title == "Prepare founder briefing"

    _commit(
        restarted,
        WorkBoardAdoptionMutationRequest(
            action="update",
            expected_revision=1,
            target_ref=card_ref,
            draft=_draft("Prepare Monday founder briefing"),
        ),
        suffix="update",
    )
    _commit(
        restarted,
        WorkBoardAdoptionMutationRequest(
            action="move",
            expected_revision=2,
            target_ref=card_ref,
            lane_ref="work-board-lane:doing",
        ),
        suffix="move",
    )
    _commit(
        restarted,
        WorkBoardAdoptionMutationRequest(
            action="archive",
            expected_revision=3,
            target_ref=card_ref,
        ),
        suffix="archive",
    )
    archived = WorkBoardAdoptionStore(tmp_path).read_view()
    assert archived.revision == 4
    assert archived.active_cards == ()
    assert archived.archived_cards[0].title == "Prepare Monday founder briefing"
    assert archived.archived_cards[0].lane_ref == "work-board-lane:doing"

    _commit(
        restarted,
        WorkBoardAdoptionMutationRequest(
            action="recover",
            expected_revision=4,
            target_ref=card_ref,
        ),
        suffix="recover",
    )
    recovered = WorkBoardAdoptionStore(tmp_path).read_view()
    assert recovered.revision == 5
    assert recovered.active_cards[0].card_ref == card_ref

    _, _, undone = _commit(
        restarted,
        WorkBoardAdoptionMutationRequest(action="undo", expected_revision=5),
        suffix="undo",
    )
    after_undo = WorkBoardAdoptionStore(tmp_path).read_view()
    assert undone.after_revision == 6
    assert after_undo.active_cards == ()
    assert after_undo.archived_cards[0].card_ref == card_ref
    assert after_undo.can_undo is True


def test_stale_revision_and_scope_substitution_fail_closed(tmp_path: Path) -> None:
    store = WorkBoardAdoptionStore(tmp_path)
    mutation = WorkBoardAdoptionMutationRequest(
        action="create",
        expected_revision=0,
        draft=_draft(),
    )
    preview = store.preview_mutation(mutation, idempotency_ref=_idempotency("scope"))

    with pytest.raises(
        WorkBoardAdoptionConflict,
        match="WORK_BOARD_ADOPTION_APPROVAL_SCOPE_MISMATCH",
    ):
        store.capture_approval(
            WorkBoardAdoptionApprovalCaptureRequest(
                mutation=mutation,
                preview_ref="preview-ref:work-board-adoption:substituted",
                approval_ref=preview.approval_ref,
            ),
            idempotency_ref=_idempotency("scope"),
        )

    _commit(store, mutation, suffix="stale-create")
    with pytest.raises(
        WorkBoardAdoptionConflict,
        match="WORK_BOARD_ADOPTION_STALE_REVISION",
    ):
        store.preview_mutation(mutation, idempotency_ref=_idempotency("stale"))


def test_exact_idempotent_replay_and_payload_conflict(tmp_path: Path) -> None:
    store = WorkBoardAdoptionStore(tmp_path)
    mutation = WorkBoardAdoptionMutationRequest(
        action="create",
        expected_revision=0,
        draft=_draft(),
    )
    idempotency_ref = _idempotency("replay")
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    store.capture_approval(
        WorkBoardAdoptionApprovalCaptureRequest(
            mutation=mutation,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    commit = WorkBoardAdoptionCommitRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    first = store.commit_mutation(commit, idempotency_ref=idempotency_ref)
    replayed_approval = store.capture_approval(
        WorkBoardAdoptionApprovalCaptureRequest(
            mutation=mutation,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    replay = store.commit_mutation(commit, idempotency_ref=idempotency_ref)

    assert first.replayed is False
    assert replayed_approval.approval_ref == first.approval_ref
    assert replayed_approval.approval_validation_ref == first.approval_validation_ref
    assert replayed_approval.expires_at == first.approval_expires_at
    assert replay.replayed is True
    assert replay.receipt_ref == first.receipt_ref
    assert store.read_view().revision == 1

    changed = WorkBoardAdoptionMutationRequest(
        action="create",
        expected_revision=0,
        draft=_draft("Substituted payload"),
    )
    with pytest.raises(
        WorkBoardAdoptionConflict,
        match="WORK_BOARD_ADOPTION_IDEMPOTENCY_CONFLICT",
    ):
        store.commit_mutation(
            WorkBoardAdoptionCommitRequest(
                mutation=changed,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
            ),
            idempotency_ref=idempotency_ref,
        )

    for substituted in (
        commit.model_copy(
            update={"preview_ref": "preview-ref:work-board-adoption:substituted"}
        ),
        commit.model_copy(
            update={"approval_ref": "approval-ref:work-board-adoption:substituted"}
        ),
    ):
        with pytest.raises(
            WorkBoardAdoptionConflict,
            match="WORK_BOARD_ADOPTION_IDEMPOTENCY_CONFLICT",
        ):
            store.commit_mutation(
                substituted,
                idempotency_ref=idempotency_ref,
            )


def test_restore_rejects_nonidentical_receipt_collision(tmp_path: Path) -> None:
    store = WorkBoardAdoptionStore(tmp_path)
    _, _, receipt = _commit(
        store,
        WorkBoardAdoptionMutationRequest(
            action="create",
            expected_revision=0,
            draft=_draft(),
        ),
        suffix="receipt-collision",
    )
    current = store._read_state()
    restored = WorkBoardAdoptionState(
        revision=current.revision,
        cards=current.cards,
        undo_stack=current.undo_stack,
        receipts=(
            receipt.model_copy(
                update={
                    "approval_ref": "approval-ref:work-board-adoption:forked"
                }
            ),
        ),
    )

    with pytest.raises(
        WorkBoardAdoptionConflict,
        match="WORK_BOARD_ADOPTION_RESTORE_RECEIPT_CONFLICT",
    ):
        store._merged_restore_receipts(
            current=current,
            restored=restored,
            receipt=receipt,
        )


def test_state_write_failures_are_redacted_and_publication_aware(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    mutation = WorkBoardAdoptionMutationRequest(
        action="create",
        expected_revision=0,
        draft=_draft(),
    )

    def approved_commit(
        store: WorkBoardAdoptionStore,
        suffix: str,
    ) -> tuple[str, WorkBoardAdoptionCommitRequest]:
        idempotency_ref = _idempotency(suffix)
        preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
        approval = store.capture_approval(
            WorkBoardAdoptionApprovalCaptureRequest(
                mutation=mutation,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
            ),
            idempotency_ref=idempotency_ref,
        )
        return idempotency_ref, WorkBoardAdoptionCommitRequest(
            mutation=mutation,
            preview_ref=preview.preview_ref,
            approval_ref=approval.approval_ref,
        )

    before_store = WorkBoardAdoptionStore(tmp_path / "before")
    before_ref, before_commit = approved_commit(before_store, "write-failed")
    original_mkstemp = work_board_adoption.tempfile.mkstemp
    attempts = 0

    def fail_before_publication(*_args: object, **_kwargs: object) -> tuple[int, str]:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("private path must not escape")
        return original_mkstemp(*_args, **_kwargs)

    monkeypatch.setattr(work_board_adoption.tempfile, "mkstemp", fail_before_publication)
    with pytest.raises(
        WorkBoardAdoptionError,
        match="WORK_BOARD_ADOPTION_STATE_WRITE_FAILED",
    ):
        before_store.commit_mutation(before_commit, idempotency_ref=before_ref)
    assert not before_store.state_path.exists()
    assert [
        lease.status
        for lease in AuthorityLeaseStore(
            before_store.state_dir / "authority"
        ).list_leases(active_only=True)
    ] == ["active"]
    retry = before_store.commit_mutation(before_commit, idempotency_ref=before_ref)
    assert retry.after_revision == 1
    assert before_store.read_view().revision == 1

    monkeypatch.undo()
    after_store = WorkBoardAdoptionStore(tmp_path / "after")
    after_ref, after_commit = approved_commit(after_store, "publication-uncertain")

    def fail_after_publication(_path: Path) -> None:
        raise OSError("private path must not escape")

    monkeypatch.setattr(work_board_adoption, "_fsync_directory", fail_after_publication)
    with pytest.raises(
        WorkBoardAdoptionError,
        match="WORK_BOARD_ADOPTION_PUBLICATION_UNCERTAIN",
    ):
        after_store.commit_mutation(after_commit, idempotency_ref=after_ref)
    assert after_store.read_view().revision == 1


def test_restore_transient_write_failure_keeps_exact_retry_usable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = WorkBoardAdoptionStore(tmp_path / "source")
    _commit(
        source,
        WorkBoardAdoptionMutationRequest(
            action="create",
            expected_revision=0,
            draft=_draft(),
        ),
        suffix="restore-retry-source",
    )
    backup = source.create_portable_backup(
        WorkBoardAdoptionPortableBackupRequest(
            passphrase="restore retry passphrase value"
        )
    )
    target = WorkBoardAdoptionStore(tmp_path / "target")
    idempotency_ref = _idempotency("restore-retry")
    request = WorkBoardAdoptionPortableRestoreRequest(
        passphrase="restore retry passphrase value",
        backup=backup,
    )
    preview = target.preview_restore(request, idempotency_ref=idempotency_ref)
    approval = target.capture_restore_approval(
        WorkBoardAdoptionRestoreApprovalCaptureRequest(
            **request.model_dump(mode="python"),
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    commit = WorkBoardAdoptionRestoreCommitRequest(
        **request.model_dump(mode="python"),
        preview_ref=preview.preview_ref,
        approval_ref=approval.approval_ref,
    )
    original_write = target._write_state
    attempts = 0

    def transient_write_failure(state: WorkBoardAdoptionState) -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise WorkBoardAdoptionError("WORK_BOARD_ADOPTION_STATE_WRITE_FAILED")
        original_write(state)

    monkeypatch.setattr(target, "_write_state", transient_write_failure)
    with pytest.raises(
        WorkBoardAdoptionError,
        match="WORK_BOARD_ADOPTION_STATE_WRITE_FAILED",
    ):
        target.commit_restore(commit, idempotency_ref=idempotency_ref)

    receipt = target.commit_restore(commit, idempotency_ref=idempotency_ref)
    assert receipt.after_revision == 2
    assert target.read_view().revision == 2


def test_revocation_failure_does_not_mask_publication_outcome(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    store = WorkBoardAdoptionStore(tmp_path)
    mutation = WorkBoardAdoptionMutationRequest(
        action="create",
        expected_revision=0,
        draft=_draft(),
    )
    idempotency_ref = _idempotency("revocation-failure")
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    approval = store.capture_approval(
        WorkBoardAdoptionApprovalCaptureRequest(
            mutation=mutation,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )

    def publication_uncertain(_state: WorkBoardAdoptionState) -> None:
        raise WorkBoardAdoptionError("WORK_BOARD_ADOPTION_PUBLICATION_UNCERTAIN")

    def revocation_failed(*_args: object, **_kwargs: object) -> None:
        raise OSError("private path must not escape")

    monkeypatch.setattr(store, "_write_state", publication_uncertain)
    monkeypatch.setattr(AuthorityLeaseStore, "revoke_lease", revocation_failed)
    with pytest.raises(
        WorkBoardAdoptionError,
        match="WORK_BOARD_ADOPTION_PUBLICATION_UNCERTAIN",
    ):
        store.commit_mutation(
            WorkBoardAdoptionCommitRequest(
                mutation=mutation,
                preview_ref=preview.preview_ref,
                approval_ref=approval.approval_ref,
            ),
            idempotency_ref=idempotency_ref,
        )
    assert "WORK_BOARD_ADOPTION_LEASE_REVOCATION_FAILED" in caplog.text


def test_file_writer_lock_uses_windows_interprocess_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FakeMsvcrt:
        LK_LOCK = 1
        LK_UNLCK = 2

        def __init__(self) -> None:
            self.calls: list[tuple[int, int]] = []

        def locking(self, _descriptor: int, mode: int, byte_count: int) -> None:
            self.calls.append((mode, byte_count))

    fake_msvcrt = FakeMsvcrt()
    monkeypatch.setattr(single_writer_lock, "_fcntl", None)
    monkeypatch.setattr(single_writer_lock, "_msvcrt", fake_msvcrt)
    monkeypatch.setattr(single_writer_lock.os, "fchmod", None)

    lock_manager = FileSingleWriterLockManager(tmp_path / "locks")
    with lock_manager.acquire("work-board"):
        pass

    assert fake_msvcrt.calls == [
        (fake_msvcrt.LK_LOCK, 1),
        (fake_msvcrt.LK_UNLCK, 1),
    ]


def test_malformed_or_symlinked_state_requires_recovery(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed"
    malformed.mkdir()
    (malformed / WORK_BOARD_ADOPTION_STATE_FILE).write_text("{", encoding="utf-8")
    assert WorkBoardAdoptionStore(malformed).read_view().status == "recovery_required"

    target = tmp_path / "target.json"
    target.write_text(json.dumps({"schema_version": "wrong"}), encoding="utf-8")
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / WORK_BOARD_ADOPTION_STATE_FILE).symlink_to(target)
    assert WorkBoardAdoptionStore(linked).read_view().status == "recovery_required"

    dangling = tmp_path / "dangling"
    dangling.mkdir()
    dangling_state = dangling / WORK_BOARD_ADOPTION_STATE_FILE
    dangling_state.symlink_to(tmp_path / "missing-state.json")
    dangling_store = WorkBoardAdoptionStore(dangling)
    assert dangling_store.read_view().status == "recovery_required"
    with pytest.raises(
        WorkBoardAdoptionError,
        match="WORK_BOARD_ADOPTION_STATE_OBJECT_UNSAFE",
    ):
        dangling_store.preview_mutation(
            WorkBoardAdoptionMutationRequest(
                action="create",
                expected_revision=0,
                draft=_draft(),
            ),
            idempotency_ref=_idempotency("dangling-state"),
        )
    assert dangling_state.is_symlink()


def test_windows_private_acl_is_applied_to_existing_private_tree(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    store = WorkBoardAdoptionStore(tmp_path / "windows-private")
    store.state_dir.mkdir()
    store.lock_manager.lock_dir.mkdir()
    lock_file = store.lock_manager.lock_dir / "work-board-adoption-state.lock"
    lock_file.write_bytes(b"")
    authority_dir = store.state_dir / "authority"
    authority_dir.mkdir()
    authority_file = authority_dir / "authority-leases.json"
    authority_file.write_text("{}", encoding="utf-8")
    store.state_path.write_text("{}", encoding="utf-8")
    secured: list[tuple[Path, bool]] = []

    def secure(path: Path, *, directory: bool) -> None:
        secured.append((path, directory))

    monkeypatch.setattr(work_board_adoption, "_IS_WINDOWS", True)
    monkeypatch.setattr(work_board_adoption, "_set_windows_private_acl", secure)
    store._ensure_private_state_directory()

    assert (store.state_dir, True) in secured
    assert (store.lock_manager.lock_dir, True) in secured
    assert (lock_file, False) in secured
    assert (authority_dir, True) in secured
    assert (authority_file, False) in secured
    assert (store.state_path, False) in secured


def test_forged_receipt_identity_requires_recovery(tmp_path: Path) -> None:
    store = WorkBoardAdoptionStore(tmp_path)
    _commit(
        store,
        WorkBoardAdoptionMutationRequest(
            action="create",
            expected_revision=0,
            draft=_draft(),
        ),
        suffix="forged-receipt",
    )
    payload = json.loads((tmp_path / WORK_BOARD_ADOPTION_STATE_FILE).read_text())
    payload["receipts"][0]["after_revision"] = 100
    (tmp_path / WORK_BOARD_ADOPTION_STATE_FILE).write_text(json.dumps(payload))

    assert WorkBoardAdoptionStore(tmp_path).read_view().status == "recovery_required"


def test_mutation_request_rejects_ambiguous_action_shapes() -> None:
    with pytest.raises(ValueError, match="WORK_BOARD_ADOPTION_CREATE_SCOPE_INVALID"):
        WorkBoardAdoptionMutationRequest(
            action="create",
            expected_revision=0,
            draft=_draft(),
            target_ref="work-board-card-ref:unexpected",
        )
    with pytest.raises(ValueError, match="WORK_BOARD_ADOPTION_UNDO_SCOPE_INVALID"):
        WorkBoardAdoptionMutationRequest(
            action="undo",
            expected_revision=0,
            lane_ref="work-board-lane:doing",
        )


def test_encrypted_backup_restores_into_fresh_workspace(tmp_path: Path) -> None:
    source = WorkBoardAdoptionStore(tmp_path / "source")
    _commit(
        source,
        WorkBoardAdoptionMutationRequest(
            action="create",
            expected_revision=0,
            draft=_draft("Private launch plan"),
        ),
        suffix="backup-source",
    )
    passphrase = "correct horse battery staple"
    backup = source.create_portable_backup(
        WorkBoardAdoptionPortableBackupRequest(passphrase=passphrase)
    )

    assert "Private launch plan" not in backup.ciphertext
    assert backup.private_values_encrypted is True
    assert backup.key_material_included is False

    restored = WorkBoardAdoptionStore(tmp_path / "restored")
    idempotency_ref = _idempotency("restore")
    restore_request = WorkBoardAdoptionPortableRestoreRequest(
        passphrase=passphrase,
        backup=backup,
    )
    preview = restored.preview_restore(
        restore_request,
        idempotency_ref=idempotency_ref,
    )
    approval = restored.capture_restore_approval(
        WorkBoardAdoptionRestoreApprovalCaptureRequest(
            **restore_request.model_dump(mode="python"),
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    commit_request = WorkBoardAdoptionRestoreCommitRequest(
        **restore_request.model_dump(mode="python"),
        preview_ref=preview.preview_ref,
        approval_ref=approval.approval_ref,
    )
    receipt = restored.commit_restore(
        commit_request,
        idempotency_ref=idempotency_ref,
    )
    replayed_approval = restored.capture_restore_approval(
        WorkBoardAdoptionRestoreApprovalCaptureRequest(
            **restore_request.model_dump(mode="python"),
            preview_ref=preview.preview_ref,
            approval_ref=approval.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    replay = restored.commit_restore(
        commit_request,
        idempotency_ref=idempotency_ref,
    )

    view = restored.read_view()
    assert receipt.action == "restore_backup"
    assert receipt.after_revision == 2
    assert view.revision == 2
    assert view.active_cards[0].title == "Private launch plan"
    assert view.can_undo is False
    assert replayed_approval.approval_validation_ref == receipt.approval_validation_ref
    assert replayed_approval.expires_at == receipt.approval_expires_at
    assert replay.replayed is True
    assert replay.receipt_ref == receipt.receipt_ref
    assert view.revision == 2

    substituted_backup = backup.model_copy(
        update={
            "ciphertext_fingerprint_ref": (
                "ciphertext-fingerprint-ref:sha256:" + "0" * 64
            )
        }
    )
    with pytest.raises(
        WorkBoardAdoptionError,
        match="WORK_BOARD_ADOPTION_BACKUP_FINGERPRINT_INVALID",
    ):
        restored.commit_restore(
            commit_request.model_copy(update={"backup": substituted_backup}),
            idempotency_ref=idempotency_ref,
        )


def test_restore_authority_binds_exact_published_route(tmp_path: Path) -> None:
    source = WorkBoardAdoptionStore(tmp_path / "source")
    _commit(
        source,
        WorkBoardAdoptionMutationRequest(
            action="create",
            expected_revision=0,
            draft=_draft(),
        ),
        suffix="route-source",
    )
    passphrase = "route binding passphrase value"
    backup = source.create_portable_backup(
        WorkBoardAdoptionPortableBackupRequest(passphrase=passphrase)
    )
    target = WorkBoardAdoptionStore(tmp_path / "target")
    idempotency_ref = _idempotency("route-binding")
    preview = target.preview_restore(
        WorkBoardAdoptionPortableRestoreRequest(
            passphrase=passphrase,
            backup=backup,
        ),
        idempotency_ref=idempotency_ref,
    )

    _, lease_request, _, _, _, route_ref = target._lease_context(
        preview,
        idempotency_ref=idempotency_ref,
    )

    assert route_ref == "POST /control-center/work-board/adoption/restore-commit"
    assert route_ref == WORK_BOARD_ADOPTION_RESTORE_ROUTE_REF
    assert lease_request.constraints["exact_route_ref"] == route_ref


def test_restore_revokes_lease_after_post_authority_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = WorkBoardAdoptionStore(tmp_path / "source")
    _commit(
        source,
        WorkBoardAdoptionMutationRequest(
            action="create",
            expected_revision=0,
            draft=_draft(),
        ),
        suffix="post-authority-source",
    )
    passphrase = "post authority failure passphrase"
    backup = source.create_portable_backup(
        WorkBoardAdoptionPortableBackupRequest(passphrase=passphrase)
    )
    target = WorkBoardAdoptionStore(tmp_path / "target")
    idempotency_ref = _idempotency("post-authority-failure")
    restore = WorkBoardAdoptionPortableRestoreRequest(
        passphrase=passphrase,
        backup=backup,
    )
    preview = target.preview_restore(restore, idempotency_ref=idempotency_ref)
    approval = target.capture_restore_approval(
        WorkBoardAdoptionRestoreApprovalCaptureRequest(
            **restore.model_dump(mode="python"),
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )

    def fail_after_authority(**_kwargs: object) -> None:
        raise OSError("synthetic restore assembly failure")

    monkeypatch.setattr(target, "_merged_restore_receipts", fail_after_authority)

    with pytest.raises(OSError, match="synthetic restore assembly failure"):
        target.commit_restore(
            WorkBoardAdoptionRestoreCommitRequest(
                **restore.model_dump(mode="python"),
                preview_ref=preview.preview_ref,
                approval_ref=approval.approval_ref,
            ),
            idempotency_ref=idempotency_ref,
        )

    authority_store = AuthorityLeaseStore(target.state_dir / "authority")
    assert authority_store.list_leases(active_only=True) == []
    assert [lease.status for lease in authority_store.list_leases()] == ["revoked"]
    assert target.read_view().revision == 0


def test_restore_rejects_wrong_passphrase_without_mutation(tmp_path: Path) -> None:
    source = WorkBoardAdoptionStore(tmp_path / "source")
    _commit(
        source,
        WorkBoardAdoptionMutationRequest(
            action="create",
            expected_revision=0,
            draft=_draft(),
        ),
        suffix="wrong-key-source",
    )
    backup = source.create_portable_backup(
        WorkBoardAdoptionPortableBackupRequest(
            passphrase="correct horse battery staple"
        )
    )
    target = WorkBoardAdoptionStore(tmp_path / "target")

    with pytest.raises(
        WorkBoardAdoptionError,
        match="WORK_BOARD_ADOPTION_BACKUP_UNLOCK_FAILED",
    ):
        target.preview_restore(
            WorkBoardAdoptionPortableRestoreRequest(
                passphrase="incorrect horse battery staple",
                backup=backup,
            ),
            idempotency_ref=_idempotency("wrong-key"),
        )

    assert target.read_view().revision == 0


def test_restore_can_recover_unreadable_state_with_exact_preview(tmp_path: Path) -> None:
    source = WorkBoardAdoptionStore(tmp_path / "source")
    _commit(
        source,
        WorkBoardAdoptionMutationRequest(
            action="create",
            expected_revision=0,
            draft=_draft("Recovery copy"),
        ),
        suffix="recovery-source",
    )
    passphrase = "recovery passphrase value"
    backup = source.create_portable_backup(
        WorkBoardAdoptionPortableBackupRequest(passphrase=passphrase)
    )

    target_dir = tmp_path / "target"
    target_dir.mkdir()
    (target_dir / WORK_BOARD_ADOPTION_STATE_FILE).write_text("{", encoding="utf-8")
    target = WorkBoardAdoptionStore(target_dir)
    restore = WorkBoardAdoptionPortableRestoreRequest(
        passphrase=passphrase,
        backup=backup,
    )
    idempotency_ref = _idempotency("recovery-restore")
    preview = target.preview_restore(restore, idempotency_ref=idempotency_ref)

    assert preview.impact_status == "unknown_current_state"
    assert preview.rollback_available is False
    approval = target.capture_restore_approval(
        WorkBoardAdoptionRestoreApprovalCaptureRequest(
            **restore.model_dump(mode="python"),
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    target.commit_restore(
        WorkBoardAdoptionRestoreCommitRequest(
            **restore.model_dump(mode="python"),
            preview_ref=preview.preview_ref,
            approval_ref=approval.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )

    assert target.read_view().active_cards[0].title == "Recovery copy"


def test_windows_directory_sync_skips_unsupported_directory_open(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(work_board_adoption.os, "name", "nt")

    def unexpected_open(*_args: object, **_kwargs: object) -> int:
        raise AssertionError("Windows durability must not open a directory descriptor")

    monkeypatch.setattr(work_board_adoption.os, "open", unexpected_open)

    work_board_adoption._fsync_directory(tmp_path)
