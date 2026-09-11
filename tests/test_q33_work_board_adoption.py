from __future__ import annotations

import json
from pathlib import Path

import pytest

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
    WorkBoardAdoptionStore,
)


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
    replay = store.commit_mutation(commit, idempotency_ref=idempotency_ref)

    assert first.replayed is False
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
