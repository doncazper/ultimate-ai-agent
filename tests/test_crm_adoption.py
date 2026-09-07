from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import ultimate_ai_agent.core.crm.adoption as adoption
from scripts.dev.uaa_crm import main as crm_cli_main
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.control_center import (
    CRM_ADOPTION_MAX_REQUEST_BODY_BYTES,
    CRM_ADOPTION_MAX_REQUEST_NESTING_DEPTH,
)
from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.crm import (
    CRM_ADOPTION_MAX_BACKUP_FILE_BYTES,
    CrmAdoptionApprovalCaptureRequest,
    CrmAdoptionCommitRequest,
    CrmAdoptionConflict,
    CrmAdoptionError,
    CrmAdoptionMutationRequest,
    CrmAdoptionRecordDraft,
    CrmAdoptionRecordPatch,
    CrmAdoptionStore,
    CrmPortableBackupRequest,
    CrmPortableRestoreCommitRequest,
    CrmPortableRestoreRequest,
)


def _create_request(revision: int = 0, *, name: str = "Private Person"):
    return CrmAdoptionMutationRequest(
        action="create",
        expected_revision=revision,
        record=CrmAdoptionRecordDraft(
            record_kind="person",
            display_name=name,
            email="private.person@example.test",
            phone="+1 555 0100",
            notes="Founder-owned private relationship context.",
            tags=["priority", "real estate"],
            status="active",
        ),
    )


def _commit(
    store: CrmAdoptionStore,
    request: CrmAdoptionMutationRequest,
    *,
    suffix: str,
):
    preview = store.preview_mutation(request)
    idempotency_ref = f"idempotency-ref:crm-adoption-test:{suffix}"
    store.capture_approval(
        request=CrmAdoptionApprovalCaptureRequest(
            operation="mutation",
            mutation=CrmAdoptionCommitRequest(
                mutation=request,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
            ),
        ),
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    return store.commit_mutation(
        request=request,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )


def _capture_restore(
    store: CrmAdoptionStore,
    request: CrmPortableRestoreCommitRequest,
    *,
    idempotency_ref: str,
) -> None:
    store.capture_approval(
        request=CrmAdoptionApprovalCaptureRequest(
            operation="restore",
            restore=request,
        ),
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )


def test_private_crm_lifecycle_is_encrypted_searchable_and_restart_safe(
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    empty = store.read_view()
    assert empty.storage_state == "empty"
    assert empty.revision == 0
    assert empty.records == []
    assert empty.fixture_primary_truth is False

    create = _create_request()
    preview = store.preview_mutation(create)
    with pytest.raises(CrmAdoptionError, match="OPERATOR_CONFIRMATION_REQUIRED"):
        store.commit_mutation(
            request=create,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
            idempotency_ref="idempotency-ref:crm-adoption-test:not-confirmed",
            confirmed=False,
        )
    with pytest.raises(CrmAdoptionError, match="EXACT_APPROVAL_REQUIRED"):
        store.commit_mutation(
            request=create,
            preview_ref=preview.preview_ref,
            approval_ref="approval-ref:crm-adoption:wrong",
            idempotency_ref="idempotency-ref:crm-adoption-test:wrong-approval",
            confirmed=True,
        )
    with pytest.raises(CrmAdoptionError, match="EXACT_APPROVAL_REQUIRED"):
        store.commit_mutation(
            request=create,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
            idempotency_ref="idempotency-ref:crm-adoption-test:no-grant",
            confirmed=True,
        )

    created = _commit(store, create, suffix="create")
    assert created.before_revision == 0
    assert created.after_revision == 1
    assert created.target_ref is not None
    assert created.approval_authority_granted is True
    assert created.approval_validation_ref.startswith("appr_dec_")
    assert created.authority_lease_ref.startswith("authority-lease-ref:")
    assert created.authority_decision_ref.startswith("authority-policy-decision-ref:")
    leases = AuthorityLeaseStore(store.state_dir / "authority").list_leases()
    assert any(item.lease_ref == created.authority_lease_ref for item in leases)
    assert b"Private Person" not in store.state_file.read_bytes()
    assert b"private.person@example.test" not in store.state_file.read_bytes()
    assert "Private Person" not in store.audit_file.read_text(encoding="utf-8")
    assert "example.test" not in store.audit_file.read_text(encoding="utf-8")
    assert store.key_file.stat().st_mode & 0o077 == 0

    restarted = CrmAdoptionStore(store.state_dir)
    result = restarted.read_view(query="example.test")
    assert result.storage_state == "ready"
    assert result.revision == 1
    assert [item.display_name for item in result.records] == ["Private Person"]

    target_ref = str(created.target_ref)
    update = CrmAdoptionMutationRequest(
        action="update",
        expected_revision=1,
        target_ref=target_ref,
        patch=CrmAdoptionRecordPatch(
            display_name="Updated Private Person",
            notes="Corrected private context.",
        ),
    )
    _commit(restarted, update, suffix="update")
    archive = CrmAdoptionMutationRequest(
        action="archive", expected_revision=2, target_ref=target_ref
    )
    _commit(restarted, archive, suffix="archive")
    assert restarted.read_view().records == []
    assert restarted.read_view(include_archived=True).records[0].archived is True

    restore = CrmAdoptionMutationRequest(
        action="restore", expected_revision=3, target_ref=target_ref
    )
    _commit(restarted, restore, suffix="restore")
    assert restarted.read_view().records[0].display_name == "Updated Private Person"

    undo = CrmAdoptionMutationRequest(action="undo", expected_revision=4)
    _commit(restarted, undo, suffix="undo")
    assert restarted.read_view(include_archived=True).records[0].archived is True


def test_stale_revision_replay_and_changed_replay_fail_closed(tmp_path: Path) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    request = _create_request()
    preview = store.preview_mutation(request)
    replay_idempotency_ref = "idempotency-ref:crm-adoption-test:replay"
    store.capture_approval(
        request=CrmAdoptionApprovalCaptureRequest(
            operation="mutation",
            mutation=CrmAdoptionCommitRequest(
                mutation=request,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
            ),
        ),
        idempotency_ref=replay_idempotency_ref,
        confirmed=True,
    )
    receipt = store.commit_mutation(
        request=request,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
        idempotency_ref=replay_idempotency_ref,
        confirmed=True,
    )
    replay = store.commit_mutation(
        request=request,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
        idempotency_ref=replay_idempotency_ref,
        confirmed=True,
    )
    assert replay.receipt_ref == receipt.receipt_ref
    assert replay.replayed is True

    with pytest.raises(CrmAdoptionConflict, match="IDEMPOTENCY_CONFLICT"):
        store.commit_mutation(
            request=request,
            preview_ref=preview.preview_ref,
            approval_ref="approval-ref:crm-adoption:substituted",
            idempotency_ref=replay_idempotency_ref,
            confirmed=True,
        )

    with pytest.raises(CrmAdoptionConflict, match="IDEMPOTENCY_CONFLICT"):
        changed = _create_request(name="Changed replay")
        changed_preview = store.preview_mutation(
            changed.model_copy(update={"expected_revision": 1})
        )
        store.commit_mutation(
            request=changed,
            preview_ref=changed_preview.preview_ref,
            approval_ref=changed_preview.approval_ref,
            idempotency_ref=replay_idempotency_ref,
            confirmed=True,
        )

    with pytest.raises(CrmAdoptionConflict, match="STALE_REVISION"):
        store.preview_mutation(_create_request())


def test_state_write_failure_does_not_publish_audit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    request = _create_request()
    preview = store.preview_mutation(request)
    idempotency_ref = "idempotency-ref:crm-adoption-test:state-write-failure"
    store.capture_approval(
        request=CrmAdoptionApprovalCaptureRequest(
            operation="mutation",
            mutation=CrmAdoptionCommitRequest(
                mutation=request,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
            ),
        ),
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )

    write_state = store._write_state

    def fail_state_write(_state: object) -> None:
        raise OSError("synthetic state write failure")

    monkeypatch.setattr(store, "_write_state", fail_state_write)
    with pytest.raises(OSError, match="synthetic state write failure"):
        store.commit_mutation(
            request=request,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
            idempotency_ref=idempotency_ref,
            confirmed=True,
        )

    assert not store.audit_file.exists()
    assert not store.pending_audit_file.exists()
    assert store.read_view().revision == 0

    monkeypatch.setattr(store, "_write_state", write_state)
    retry_approval = store.capture_approval(
        request=CrmAdoptionApprovalCaptureRequest(
            operation="mutation",
            mutation=CrmAdoptionCommitRequest(
                mutation=request,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
            ),
        ),
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    retried = store.commit_mutation(
        request=request,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    assert retry_approval.approval_ref == preview.approval_ref
    assert retried.after_revision == 1


def test_ambiguous_state_publication_preserves_journal_for_restart_recovery(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    request = _create_request()
    preview = store.preview_mutation(request)
    idempotency_ref = "idempotency-ref:crm-adoption-test:ambiguous-publication"
    store.capture_approval(
        request=CrmAdoptionApprovalCaptureRequest(
            operation="mutation",
            mutation=CrmAdoptionCommitRequest(
                mutation=request,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
            ),
        ),
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    write_state = store._write_state

    def publish_then_report_uncertain(state: object) -> None:
        write_state(state)  # type: ignore[arg-type]
        raise adoption.CrmAdoptionStatePublicationUncertain(
            "CRM_ADOPTION_STATE_PUBLICATION_UNCERTAIN"
        )

    monkeypatch.setattr(store, "_write_state", publish_then_report_uncertain)
    with pytest.raises(
        adoption.CrmAdoptionStatePublicationUncertain,
        match="STATE_PUBLICATION_UNCERTAIN",
    ):
        store.commit_mutation(
            request=request,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
            idempotency_ref=idempotency_ref,
            confirmed=True,
        )

    assert store._read_state().revision == 1
    assert store.pending_audit_file.exists()
    restarted = CrmAdoptionStore(store.state_dir)
    assert restarted.read_view().revision == 1
    assert restarted.audit_file.exists()
    assert not restarted.pending_audit_file.exists()
    replay = restarted.commit_mutation(
        request=request,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    assert replay.replayed is True


def test_atomic_write_marks_post_replace_fsync_failure_as_uncertain(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    store._secure_state_dir()
    destination = store.state_dir / "atomic-publication-test"
    fsync = adoption.os.fsync
    calls = 0

    def fail_directory_fsync(descriptor: int) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic directory fsync failure")
        fsync(descriptor)

    monkeypatch.setattr(adoption.os, "fsync", fail_directory_fsync)
    with pytest.raises(
        adoption._AtomicWritePublicationUncertain,
        match="ATOMIC_PUBLICATION_UNCERTAIN",
    ):
        store._atomic_write(destination, b"published payload")

    assert destination.read_bytes() == b"published payload"
    assert destination.stat().st_mode & 0o077 == 0


def test_audit_capacity_is_rejected_before_state_publication(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    _commit(store, _create_request(name="First Person"), suffix="audit-capacity-one")
    request = _create_request(revision=1, name="Second Person")
    preview = store.preview_mutation(request)
    idempotency_ref = "idempotency-ref:crm-adoption-test:audit-capacity-two"
    store.capture_approval(
        request=CrmAdoptionApprovalCaptureRequest(
            operation="mutation",
            mutation=CrmAdoptionCommitRequest(
                mutation=request,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
            ),
        ),
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    monkeypatch.setattr(
        adoption,
        "CRM_ADOPTION_MAX_AUDIT_BYTES",
        store.audit_file.stat().st_size,
    )

    with pytest.raises(CrmAdoptionError, match="AUDIT_CAPACITY_EXHAUSTED"):
        store.commit_mutation(
            request=request,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
            idempotency_ref=idempotency_ref,
            confirmed=True,
        )

    assert store._read_state().revision == 1
    assert not store.pending_audit_file.exists()


def test_audit_failure_keeps_authoritative_state_and_replay_repairs_it(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    request = _create_request()
    preview = store.preview_mutation(request)
    idempotency_ref = "idempotency-ref:crm-adoption-test:audit-repair"
    store.capture_approval(
        request=CrmAdoptionApprovalCaptureRequest(
            operation="mutation",
            mutation=CrmAdoptionCommitRequest(
                mutation=request,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
            ),
        ),
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    append_audit = store._append_audit
    attempts = 0

    def fail_once(receipt: object) -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("synthetic audit write failure")
        append_audit(receipt)  # type: ignore[arg-type]

    monkeypatch.setattr(store, "_append_audit", fail_once)
    with pytest.raises(CrmAdoptionError, match="AUDIT_FINALIZATION_REQUIRED"):
        store.commit_mutation(
            request=request,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
            idempotency_ref=idempotency_ref,
            confirmed=True,
        )

    assert store._read_state().revision == 1
    assert not store.audit_file.exists()
    assert store.pending_audit_file.exists()
    monkeypatch.setattr(store, "_append_audit", append_audit)
    restarted = CrmAdoptionStore(store.state_dir)
    assert restarted.read_view().revision == 1
    assert restarted.audit_file.exists()
    assert not restarted.pending_audit_file.exists()
    replay = restarted.commit_mutation(
        request=request,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    assert replay.replayed is True
    assert replay.after_revision == 1
    assert attempts == 1


def test_pending_audit_is_bound_to_the_authoritative_receipt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    request = _create_request()
    preview = store.preview_mutation(request)
    idempotency_ref = "idempotency-ref:crm-adoption-test:audit-binding"
    store.capture_approval(
        request=CrmAdoptionApprovalCaptureRequest(
            operation="mutation",
            mutation=CrmAdoptionCommitRequest(
                mutation=request,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
            ),
        ),
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    monkeypatch.setattr(
        store,
        "_append_audit",
        lambda _receipt: (_ for _ in ()).throw(OSError("synthetic audit failure")),
    )
    with pytest.raises(CrmAdoptionError, match="AUDIT_FINALIZATION_REQUIRED"):
        store.commit_mutation(
            request=request,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
            idempotency_ref=idempotency_ref,
            confirmed=True,
        )

    event = json.loads(store.pending_audit_file.read_text(encoding="utf-8"))
    event["after_revision"] = 999
    store.pending_audit_file.write_text(json.dumps(event), encoding="utf-8")
    restarted = CrmAdoptionStore(store.state_dir)
    view = restarted.read_view()
    assert view.storage_state == "ready"
    assert not restarted.pending_audit_file.exists()
    audit_event = json.loads(restarted.audit_file.read_text(encoding="utf-8"))
    assert audit_event["after_revision"] == 1


def test_approval_capture_rejects_exact_ref_rebinding(tmp_path: Path) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    request = _create_request()
    preview = store.preview_mutation(request)
    capture = CrmAdoptionApprovalCaptureRequest(
        operation="mutation",
        mutation=CrmAdoptionCommitRequest(
            mutation=request,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
    )
    store.capture_approval(
        request=capture,
        idempotency_ref="idempotency-ref:crm-adoption-test:approval-binding-one",
        confirmed=True,
    )
    with pytest.raises(CrmAdoptionConflict, match="APPROVAL_CONFLICT"):
        store.capture_approval(
            request=capture,
            idempotency_ref="idempotency-ref:crm-adoption-test:approval-binding-two",
            confirmed=True,
        )


def test_csv_import_requires_preview_and_never_silently_merges(tmp_path: Path) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    _commit(store, _create_request(name="Existing Person"), suffix="existing")
    csv_text = "name,email,phone,tags\nExisting Person,other@example.test,555-1000,old\nNew Person,new@example.test,555-2000,new\n"
    request = CrmAdoptionMutationRequest(
        action="import_contacts",
        expected_revision=1,
        csv_text=csv_text,
    )
    preview = store.preview_mutation(request)
    assert preview.affected_count == 1
    assert preview.duplicate_candidate_count == 1
    import_idempotency_ref = "idempotency-ref:crm-adoption-test:import"
    store.capture_approval(
        request=CrmAdoptionApprovalCaptureRequest(
            operation="mutation",
            mutation=CrmAdoptionCommitRequest(
                mutation=request,
                preview_ref=preview.preview_ref,
                approval_ref=preview.approval_ref,
            ),
        ),
        idempotency_ref=import_idempotency_ref,
        confirmed=True,
    )
    receipt = store.commit_mutation(
        request=request,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
        idempotency_ref=import_idempotency_ref,
        confirmed=True,
    )
    assert receipt.after_revision == 2
    view = store.read_view(record_kind="person")
    assert sorted(item.display_name for item in view.records) == [
        "Existing Person",
        "New Person",
    ]
    all_duplicate = CrmAdoptionMutationRequest(
        action="import_contacts",
        expected_revision=2,
        csv_text="name,email\nNew Person,new@example.test\n",
    )
    with pytest.raises(CrmAdoptionConflict, match="IMPORT_NO_NEW_RECORDS"):
        store.preview_mutation(all_duplicate)

    digitless_phones = CrmAdoptionMutationRequest(
        action="import_contacts",
        expected_revision=2,
        csv_text=(
            "name,email,phone\n"
            "Distinct Alpha,alpha@example.test,N/A\n"
            "Distinct Beta,beta@example.test,unknown\n"
        ),
    )
    digitless_preview = store.preview_mutation(digitless_phones)
    assert digitless_preview.affected_count == 2
    assert digitless_preview.duplicate_candidate_count == 0


def test_restore_undo_reports_exact_record_impact_and_stops_at_local_lineage(
    tmp_path: Path,
) -> None:
    source = CrmAdoptionStore(tmp_path / "source")
    _commit(source, _create_request(name="Backup Person"), suffix="source-create")
    passphrase = "correct horse battery staple"
    backup = source.create_portable_backup(
        CrmPortableBackupRequest(passphrase=passphrase)
    )

    target = CrmAdoptionStore(tmp_path / "target")
    _commit(target, _create_request(name="Current Person"), suffix="target-create")
    restore_request = CrmPortableRestoreRequest(
        passphrase=passphrase,
        backup=backup,
    )
    restore_preview = target.preview_restore(restore_request)
    restore_commit = CrmPortableRestoreCommitRequest(
        **restore_request.model_dump(mode="python"),
        preview_ref=restore_preview.preview_ref,
        approval_ref=restore_preview.approval_ref,
    )
    restore_idempotency_ref = "idempotency-ref:crm-adoption-test:lineage-restore"
    _capture_restore(
        target,
        restore_commit,
        idempotency_ref=restore_idempotency_ref,
    )
    target.commit_restore(
        request=restore_commit,
        idempotency_ref=restore_idempotency_ref,
        confirmed=True,
    )

    undo_request = CrmAdoptionMutationRequest(action="undo", expected_revision=2)
    undo_preview = target.preview_mutation(undo_request)
    assert undo_preview.affected_count == 2
    _commit(target, undo_request, suffix="lineage-undo")
    assert [item.display_name for item in target.read_view().records] == [
        "Current Person"
    ]
    with pytest.raises(CrmAdoptionConflict, match="UNDO_EMPTY"):
        target.preview_mutation(
            CrmAdoptionMutationRequest(action="undo", expected_revision=3)
        )


def test_encrypted_portable_backup_restores_on_another_store_and_recovers(
    tmp_path: Path,
) -> None:
    source = CrmAdoptionStore(tmp_path / "source")
    _commit(source, _create_request(), suffix="source-create")
    passphrase = "correct horse battery staple"
    backup = source.create_portable_backup(
        CrmPortableBackupRequest(passphrase=passphrase)
    )
    serialized = backup.model_dump_json()
    assert "Private Person" not in serialized
    assert "example.test" not in serialized

    target = CrmAdoptionStore(tmp_path / "target")
    restore_request = CrmPortableRestoreRequest(passphrase=passphrase, backup=backup)
    preview = target.preview_restore(restore_request)
    assert preview.integrity_status == "ok"
    assert preview.record_count == 1
    duplicate_receipt_request = CrmPortableRestoreCommitRequest(
        **restore_request.model_dump(mode="python"),
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    with pytest.raises(CrmAdoptionConflict, match="IDEMPOTENCY_CONFLICT"):
        target.commit_restore(
            request=duplicate_receipt_request,
            idempotency_ref="idempotency-ref:crm-adoption-test:source-create",
            confirmed=True,
        )
    commit_request = CrmPortableRestoreCommitRequest(
        **restore_request.model_dump(mode="python"),
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    restore_idempotency_ref = "idempotency-ref:crm-adoption-test:restore"
    _capture_restore(
        target,
        commit_request,
        idempotency_ref=restore_idempotency_ref,
    )
    receipt = target.commit_restore(
        request=commit_request,
        idempotency_ref=restore_idempotency_ref,
        confirmed=True,
    )
    assert receipt.after_revision == 2
    assert target.read_view().records[0].display_name == "Private Person"
    replay = target.commit_restore(
        request=commit_request,
        idempotency_ref=restore_idempotency_ref,
        confirmed=True,
    )
    assert replay.receipt_ref == receipt.receipt_ref
    assert replay.replayed is True
    with pytest.raises(CrmAdoptionConflict, match="IDEMPOTENCY_CONFLICT"):
        target.commit_restore(
            request=commit_request.model_copy(
                update={"approval_ref": "approval-ref:crm-adoption:substituted"}
            ),
            idempotency_ref=restore_idempotency_ref,
            confirmed=True,
        )

    with pytest.raises(CrmAdoptionError, match="BACKUP_UNLOCK_FAILED"):
        target.preview_restore(
            CrmPortableRestoreRequest(
                passphrase="wrong passphrase value", backup=backup
            )
        )

    target.state_file.write_bytes(b"corrupt")
    assert target.read_view().storage_state == "recovery_required"
    recovery_preview = target.preview_restore(restore_request)
    recovery_request = CrmPortableRestoreCommitRequest(
        **restore_request.model_dump(mode="python"),
        preview_ref=recovery_preview.preview_ref,
        approval_ref=recovery_preview.approval_ref,
    )
    recovery_idempotency_ref = "idempotency-ref:crm-adoption-test:recovery"
    _capture_restore(
        target,
        recovery_request,
        idempotency_ref=recovery_idempotency_ref,
    )
    target.commit_restore(
        request=recovery_request,
        idempotency_ref=recovery_idempotency_ref,
        confirmed=True,
    )
    assert target.read_view().storage_state == "ready"

    invalid_key_target = CrmAdoptionStore(tmp_path / "invalid-key-target")
    invalid_key_target.state_dir.mkdir(parents=True)
    invalid_key_target.state_file.write_bytes(b"corrupt-state")
    invalid_key_target.key_file.write_bytes(b"truncated-key")
    invalid_key_preview = invalid_key_target.preview_restore(restore_request)
    invalid_key_request = CrmPortableRestoreCommitRequest(
        **restore_request.model_dump(mode="python"),
        preview_ref=invalid_key_preview.preview_ref,
        approval_ref=invalid_key_preview.approval_ref,
    )
    invalid_key_idempotency_ref = (
        "idempotency-ref:crm-adoption-test:invalid-key-recovery"
    )
    _capture_restore(
        invalid_key_target,
        invalid_key_request,
        idempotency_ref=invalid_key_idempotency_ref,
    )
    invalid_key_target.commit_restore(
        request=invalid_key_request,
        idempotency_ref=invalid_key_idempotency_ref,
        confirmed=True,
    )
    recovered_state = invalid_key_target._read_state()
    assert recovered_state.records[0].display_name == "Private Person"
    assert recovered_state.undo_stack == []
    assert invalid_key_target.key_file.stat().st_size == 32
    assert len(list(invalid_key_target.state_dir.glob("*.invalid-*"))) == 1


def test_key_read_rejects_wrong_size_before_materializing_file(tmp_path: Path) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    store.state_dir.mkdir(parents=True)
    store.key_file.write_bytes(b"x" * 1_000_000)

    with pytest.raises(CrmAdoptionError, match="KEY_UNAVAILABLE"):
        store._read_key()


def test_restore_audit_failure_is_repaired_by_exact_replay(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = CrmAdoptionStore(tmp_path / "source")
    _commit(source, _create_request(), suffix="restore-audit-source")
    passphrase = "correct horse battery staple"
    backup = source.create_portable_backup(
        CrmPortableBackupRequest(passphrase=passphrase)
    )
    target = CrmAdoptionStore(tmp_path / "target")
    restore = CrmPortableRestoreRequest(passphrase=passphrase, backup=backup)
    preview = target.preview_restore(restore)
    request = CrmPortableRestoreCommitRequest(
        **restore.model_dump(mode="python"),
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    idempotency_ref = "idempotency-ref:crm-adoption-test:restore-audit-repair"
    _capture_restore(target, request, idempotency_ref=idempotency_ref)
    append_audit = target._append_audit
    attempts = 0

    def fail_once(receipt: object) -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("synthetic restore audit write failure")
        append_audit(receipt)  # type: ignore[arg-type]

    monkeypatch.setattr(target, "_append_audit", fail_once)
    with pytest.raises(CrmAdoptionError, match="AUDIT_FINALIZATION_REQUIRED"):
        target.commit_restore(
            request=request,
            idempotency_ref=idempotency_ref,
            confirmed=True,
        )

    assert target._read_state().records[0].display_name == "Private Person"
    assert not target.audit_file.exists()
    assert target.pending_audit_file.exists()
    monkeypatch.setattr(target, "_append_audit", append_audit)
    restarted = CrmAdoptionStore(target.state_dir)
    assert restarted.read_view().records[0].display_name == "Private Person"
    assert restarted.audit_file.exists()
    assert not restarted.pending_audit_file.exists()
    replay = restarted.commit_restore(
        request=request,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    assert replay.replayed is True
    assert target.audit_file.exists()
    assert attempts == 1


def test_all_supported_record_kinds_are_durable_and_searchable(tmp_path: Path) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    kinds = [
        "person",
        "organization",
        "property",
        "relationship",
        "opportunity",
        "activity",
        "follow_up",
    ]
    for revision, kind in enumerate(kinds):
        request = CrmAdoptionMutationRequest(
            action="create",
            expected_revision=revision,
            record=CrmAdoptionRecordDraft(
                record_kind=kind,
                display_name=f"Synthetic {kind}",
                notes=f"Private {kind} fixture.",
                amount_minor=125_000 if kind == "opportunity" else None,
                currency="USD" if kind == "opportunity" else None,
                occurred_at=(
                    datetime(2026, 9, 6, 17, tzinfo=timezone.utc)
                    if kind == "activity"
                    else None
                ),
                due_at=(
                    datetime(2026, 9, 7, 17, tzinfo=timezone.utc)
                    if kind == "follow_up"
                    else None
                ),
            ),
        )
        _commit(store, request, suffix=f"kind-{kind}")

    view = CrmAdoptionStore(store.state_dir).read_view(query="Synthetic")
    assert view.revision == len(kinds)
    assert {item.record_kind for item in view.records} == set(kinds)
    assert all(view.counts[kind] == 1 for kind in kinds)


def test_record_validation_and_cli_private_output_are_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="CRM_ADOPTION_DUPLICATE_TAG"):
        CrmAdoptionRecordDraft(
            record_kind="person",
            display_name="Invalid tags",
            tags=["Duplicate", "duplicate"],
        )
    with pytest.raises(ValueError, match="CRM_ADOPTION_PATCH_CLEAR_CONFLICT"):
        CrmAdoptionRecordPatch(email="new@example.test", clear_fields=["email"])

    store = CrmAdoptionStore(tmp_path / "crm")
    _commit(store, _create_request(), suffix="cli")
    assert crm_cli_main(["inspect-adoption", "--state-dir", str(store.state_dir)]) == 0
    safe_output = capsys.readouterr().out
    assert "Private Person" not in safe_output
    assert "private.person@example.test" not in safe_output
    assert '"private_values_included": false' in safe_output

    assert (
        crm_cli_main(
            [
                "inspect-adoption",
                "--state-dir",
                str(store.state_dir),
                "--show-private",
            ]
        )
        == 0
    )
    private_output = capsys.readouterr().out
    assert "Private Person" in private_output
    assert "private.person@example.test" in private_output

    monkeypatch.delenv("UAA_CRM_BACKUP_PASSPHRASE", raising=False)
    with pytest.raises(ValueError, match="BACKUP_PASSPHRASE_ENV_REQUIRED"):
        crm_cli_main(
            [
                "verify-adoption-backup",
                "--state-dir",
                str(store.state_dir),
                "--backup",
                str(tmp_path / "not-read.json"),
            ]
        )

    oversized_backup = tmp_path / "oversized-backup.json"
    with oversized_backup.open("wb") as handle:
        handle.seek(CRM_ADOPTION_MAX_BACKUP_FILE_BYTES)
        handle.write(b"x")
    monkeypatch.setenv("UAA_CRM_BACKUP_PASSPHRASE", "correct horse battery staple")
    with pytest.raises(ValueError, match="BACKUP_FILE_SIZE_LIMIT"):
        crm_cli_main(
            [
                "verify-adoption-backup",
                "--state-dir",
                str(store.state_dir),
                "--backup",
                str(oversized_backup),
            ]
        )


def test_control_center_private_crm_routes_reject_ambiguous_idempotency_headers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_CRM_ADOPTION_STATE_DIR", str(tmp_path / "crm"))
    client = TestClient(app)
    mutation = _create_request().model_dump(mode="json")
    approval_body = {
        "operation": "mutation",
        "mutation": {
            "mutation": mutation,
            "preview_ref": "preview-ref:crm-api:header-validation",
            "approval_ref": "approval-ref:crm-api:header-validation",
        },
        "restore": None,
    }

    conflict = client.post(
        "/control-center/crm/adoption/approval",
        json=approval_body,
        headers={
            "X-UAA-Idempotency-Key": "idempotency-ref:crm-api:first",
            "X-UAA-Idempotency-Ref": "idempotency-ref:crm-api:second",
            "X-UAA-Operator-Confirmed": "true",
        },
    )
    assert conflict.status_code == 400
    assert conflict.json()["detail"]["code"] == "API_IDEMPOTENCY_CONFLICT"

    invalid = client.post(
        "/control-center/crm/adoption/approval",
        json=approval_body,
        headers={
            "X-UAA-Idempotency-Key": "short",
            "X-UAA-Idempotency-Ref": "idempotency-ref:crm-api:valid",
            "X-UAA-Operator-Confirmed": "true",
        },
    )
    assert invalid.status_code == 400
    assert invalid.json()["detail"]["code"] == "API_IDEMPOTENCY_INVALID"


def test_control_center_private_crm_routes_complete_exact_local_loop(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_CRM_ADOPTION_STATE_DIR", str(tmp_path / "crm"))
    client = TestClient(app)
    view_response = client.get("/control-center/crm/adoption")
    assert view_response.status_code == 200
    view = view_response.json()["data"]
    assert view["storage_state"] == "empty"
    assert view["private_values_confined_to_local_response"] is True
    assert view["external_crm_write_enabled"] is False

    mutation = _create_request().model_dump(mode="json")
    preview_response = client.post(
        "/control-center/crm/adoption/preview", json=mutation
    )
    assert preview_response.status_code == 200
    preview = preview_response.json()["data"]

    commit_body = CrmAdoptionCommitRequest(
        mutation=CrmAdoptionMutationRequest.model_validate(mutation),
        preview_ref=preview["preview_ref"],
        approval_ref=preview["approval_ref"],
    ).model_dump(mode="json")
    missing_confirmation = client.post(
        "/control-center/crm/adoption/commit",
        json=commit_body,
        headers={"X-UAA-Idempotency-Key": "idempotency-ref:crm-api:test"},
    )
    assert missing_confirmation.status_code == 403

    missing_grant = client.post(
        "/control-center/crm/adoption/commit",
        json=commit_body,
        headers={
            "X-UAA-Idempotency-Key": "idempotency-ref:crm-api:no-grant",
            "X-UAA-Operator-Confirmed": "true",
        },
    )
    assert missing_grant.status_code == 403
    assert missing_grant.json()["detail"]["code"] == (
        "CRM_ADOPTION_EXACT_APPROVAL_REQUIRED"
    )

    approval = client.post(
        "/control-center/crm/adoption/approval",
        json={"operation": "mutation", "mutation": commit_body, "restore": None},
        headers={
            "X-UAA-Idempotency-Key": "idempotency-ref:crm-api:test",
            "X-UAA-Operator-Confirmed": "true",
        },
    )
    assert approval.status_code == 200
    assert approval.headers["Cache-Control"] == "no-store"
    assert approval.json()["data"]["mutation_performed"] is False

    committed = client.post(
        "/control-center/crm/adoption/commit",
        json=commit_body,
        headers={
            "X-UAA-Idempotency-Key": "idempotency-ref:crm-api:test",
            "X-UAA-Operator-Confirmed": "true",
        },
    )
    assert committed.status_code == 200
    assert committed.headers["Cache-Control"] == "no-store"
    assert committed.json()["data"]["external_write_performed"] is False
    assert committed.json()["data"]["approval_authority_granted"] is True
    populated = client.post(
        "/control-center/crm/adoption/query",
        json={
            "query": "example.test",
            "record_kind": None,
            "include_archived": False,
        },
    ).json()["data"]
    assert populated["records"][0]["display_name"] == "Private Person"

    backup_response = client.post(
        "/control-center/crm/adoption/backup",
        json={"passphrase": "correct horse battery staple"},
        headers={"X-UAA-Idempotency-Key": "idempotency-ref:crm-api:backup"},
    )
    assert backup_response.status_code == 200
    assert backup_response.headers["Cache-Control"] == "no-store"
    backup = backup_response.json()["data"]
    assert "Private Person" not in json.dumps(backup)
    assert backup["private_values_encrypted"] is True

    restore_preview_response = client.post(
        "/control-center/crm/adoption/restore-preview",
        json={
            "passphrase": "correct horse battery staple",
            "backup": backup,
        },
    )
    assert restore_preview_response.status_code == 200
    assert restore_preview_response.headers["Cache-Control"] == "no-store"
    restore_preview = restore_preview_response.json()["data"]
    restore_body = {
        "passphrase": "correct horse battery staple",
        "backup": backup,
        "preview_ref": restore_preview["preview_ref"],
        "approval_ref": restore_preview["approval_ref"],
    }
    restore_headers = {
        "X-UAA-Idempotency-Key": "idempotency-ref:crm-api:restore",
        "X-UAA-Operator-Confirmed": "true",
    }
    restore_approval = client.post(
        "/control-center/crm/adoption/approval",
        json={"operation": "restore", "mutation": None, "restore": restore_body},
        headers=restore_headers,
    )
    assert restore_approval.status_code == 200
    assert restore_approval.headers["Cache-Control"] == "no-store"
    restored = client.post(
        "/control-center/crm/adoption/restore",
        json=restore_body,
        headers=restore_headers,
    )
    assert restored.status_code == 200
    assert restored.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/control-center/crm/adoption"),
        ("post", "/control-center/crm/adoption/query"),
        ("post", "/control-center/crm/adoption/preview"),
        ("post", "/control-center/crm/adoption/backup"),
        ("post", "/control-center/crm/adoption/restore-preview"),
    ],
)
def test_private_crm_routes_are_never_cached(method: str, path: str) -> None:
    client = TestClient(app)
    response = client.request(method, path, json={} if method == "post" else None)

    assert response.headers["Cache-Control"] == "no-store"


def test_crm_restore_body_guard_rejects_oversize_and_deep_json_with_cors() -> None:
    client = TestClient(app)
    origin = "http://127.0.0.1:5173"
    oversized = client.post(
        "/control-center/crm/adoption/restore-preview",
        content=b"{" + b"x" * CRM_ADOPTION_MAX_REQUEST_BODY_BYTES,
        headers={
            "content-type": "application/json",
            "content-length": "1",
            "Origin": origin,
        },
    )

    assert oversized.status_code == 413
    assert oversized.headers["Cache-Control"] == "no-store"
    assert oversized.headers["Access-Control-Allow-Origin"] == origin
    assert oversized.json() == {
        "detail": "The private CRM request body exceeds the permitted local bound.",
        "code": "CRM_ADOPTION_REQUEST_BODY_LIMIT_EXCEEDED",
        "contract_ref": "contract-ref:queue-v2-q32-crm-adoption:v1",
        "maximum_body_bytes": CRM_ADOPTION_MAX_REQUEST_BODY_BYTES,
        "maximum_json_nesting_depth": CRM_ADOPTION_MAX_REQUEST_NESTING_DEPTH,
    }

    deeply_nested = b"[" * (CRM_ADOPTION_MAX_REQUEST_NESTING_DEPTH + 1)
    deeply_nested += b"]" * (CRM_ADOPTION_MAX_REQUEST_NESTING_DEPTH + 1)
    nested = client.post(
        "/control-center/crm/adoption/restore-preview",
        content=deeply_nested,
        headers={"content-type": "application/json", "Origin": origin},
    )
    assert nested.status_code == 413
    assert nested.headers["Cache-Control"] == "no-store"
    assert nested.headers["Access-Control-Allow-Origin"] == origin
    assert nested.json()["code"] == "CRM_ADOPTION_REQUEST_BODY_LIMIT_EXCEEDED"


def test_crm_restore_body_limit_is_published_for_every_backup_bearing_route() -> None:
    paths = app.openapi()["paths"]
    for route in (
        "/control-center/crm/adoption/approval",
        "/control-center/crm/adoption/restore-preview",
        "/control-center/crm/adoption/restore",
    ):
        response = paths[route]["post"]["responses"]["413"]
        schema = response["content"]["application/json"]["schema"]
        assert schema["$ref"].endswith("/CrmAdoptionBodyLimitResponse")
