from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
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


def test_expired_lease_uses_a_fresh_retry_scope_without_a_failed_commit(
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    request = _create_request()
    preview = store.preview_mutation(request)
    idempotency_ref = "idempotency-ref:crm-adoption-test:expired-lease-retry"
    capture_request = CrmAdoptionApprovalCaptureRequest(
        operation="mutation",
        mutation=CrmAdoptionCommitRequest(
            mutation=request,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
    )
    store.capture_approval(
        request=capture_request,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    store._authorize_exact_local_write(
        action=request.action,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
        payload_fingerprint_ref=store._mutation_fingerprint(request),
        expected_revision=request.expected_revision,
        idempotency_ref=idempotency_ref,
    )
    lease_store = AuthorityLeaseStore(store.state_dir / "authority")
    leases = lease_store.list_leases()
    assert len(leases) == 1
    lease_store._write_leases(
        [
            leases[0].model_copy(
                update={"expires_at": datetime.now(timezone.utc) - timedelta(minutes=1)}
            )
        ]
    )

    store.capture_approval(
        request=capture_request,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    receipt = store.commit_mutation(
        request=request,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )

    assert receipt.after_revision == 1
    assert len(AuthorityLeaseStore(store.state_dir / "authority").list_leases()) == 2


def test_expired_lease_retry_scope_remains_bound_to_client_idempotency() -> None:
    payload_fingerprint_ref = "payload-fingerprint-ref:crm-adoption:test"
    first_idempotency_ref = "idempotency-ref:crm-adoption-test:first"
    second_idempotency_ref = "idempotency-ref:crm-adoption-test:second"

    class InactiveLease:
        def __init__(self, idempotency_ref: str) -> None:
            self.constraints = {"idempotency_ref": idempotency_ref}

        @staticmethod
        def is_active() -> bool:
            return False

    class LeaseStore:
        @staticmethod
        def list_receipts(*, limit: int) -> list[object]:
            assert limit == 1_000_000
            return []

        @staticmethod
        def list_leases() -> list[InactiveLease]:
            return [
                InactiveLease(
                    adoption._hash_ref(
                        "idempotency-ref:crm-adoption-lease",
                        {
                            "payload_fingerprint_ref": payload_fingerprint_ref,
                            "idempotency_ref": idempotency_ref,
                        },
                    )
                )
                for idempotency_ref in (
                    first_idempotency_ref,
                    second_idempotency_ref,
                )
            ]

    first_retry = CrmAdoptionStore._lease_idempotency_ref(
        LeaseStore(),  # type: ignore[arg-type]
        payload_fingerprint_ref=payload_fingerprint_ref,
        idempotency_ref=first_idempotency_ref,
    )
    second_retry = CrmAdoptionStore._lease_idempotency_ref(
        LeaseStore(),  # type: ignore[arg-type]
        payload_fingerprint_ref=payload_fingerprint_ref,
        idempotency_ref=second_idempotency_ref,
    )

    assert first_retry != second_retry


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
    view = store.read_view()
    assert view.storage_state == "blocked_audit_capacity"
    assert [item.display_name for item in view.records] == ["First Person"]
    assert "Back up this workspace" in view.next_safe_action
    assert "rotate the local CRM audit log" in view.next_safe_action


def test_malformed_audit_blocks_reads_and_preview_before_approval(
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    _commit(store, _create_request(name="Protected Person"), suffix="audit-valid")
    store.audit_file.write_bytes(b'{"event_ref":')

    view = store.read_view()
    assert view.storage_state == "blocked_audit_unreadable"
    assert [item.display_name for item in view.records] == ["Protected Person"]
    assert "repair or rotate the unreadable local CRM audit log" in (
        view.next_safe_action
    )
    with pytest.raises(CrmAdoptionError, match="AUDIT_UNREADABLE"):
        store.preview_mutation(
            _create_request(revision=1, name="Blocked Before Approval")
        )


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


def test_approval_capture_scopes_internal_grants_to_idempotency_ref(
    tmp_path: Path,
) -> None:
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
    first = store.capture_approval(
        request=capture,
        idempotency_ref="idempotency-ref:crm-adoption-test:approval-binding-one",
        confirmed=True,
    )
    second = store.capture_approval(
        request=capture,
        idempotency_ref="idempotency-ref:crm-adoption-test:approval-binding-two",
        confirmed=True,
    )

    assert first.approval_ref == second.approval_ref == preview.approval_ref
    assert first.approval_validation_ref != second.approval_validation_ref


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

    bom_prefixed = CrmAdoptionMutationRequest(
        action="import_contacts",
        expected_revision=2,
        csv_text="\ufeffname,email\nBOM Person,bom@example.test\n",
    )
    bom_preview = store.preview_mutation(bom_prefixed)
    assert bom_preview.affected_count == 1
    assert bom_preview.private_preview_labels == ["BOM Person"]


def test_csv_import_rejects_non_utf8_text_at_request_boundary() -> None:
    with pytest.raises(ValueError, match="CRM_ADOPTION_IMPORT_UTF8_REQUIRED"):
        CrmAdoptionMutationRequest(
            action="import_contacts",
            expected_revision=0,
            csv_text="name,email\nInvalid,\ud800\n",
        )


def test_csv_import_treats_archived_contacts_as_duplicate_history(
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    created = _commit(
        store,
        _create_request(name="Archived Person"),
        suffix="archived-duplicate-source",
    )
    assert created.target_ref is not None
    _commit(
        store,
        CrmAdoptionMutationRequest(
            action="archive",
            expected_revision=1,
            target_ref=created.target_ref,
        ),
        suffix="archived-duplicate-archive",
    )

    with pytest.raises(CrmAdoptionConflict, match="IMPORT_NO_NEW_RECORDS"):
        store.preview_mutation(
            CrmAdoptionMutationRequest(
                action="import_contacts",
                expected_revision=2,
                csv_text=(
                    "name,email,phone\n"
                    "Archived Person,private.person@example.test,555-0100\n"
                ),
            )
        )


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
    assert restore_preview.affected_count == 2
    assert restore_preview.impact_status == "exact"
    assert restore_preview.rollback_available is True
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


def test_portable_backup_rejects_out_of_range_or_exhausted_revision(
    tmp_path: Path,
) -> None:
    source = CrmAdoptionStore(tmp_path / "source")
    _commit(source, _create_request(), suffix="source-create")
    passphrase = "correct horse battery staple"
    backup = source.create_portable_backup(
        CrmPortableBackupRequest(passphrase=passphrase)
    )
    salt = adoption._decode_b64(backup.salt, code="TEST_BACKUP_INVALID")
    nonce = adoption._decode_b64(backup.nonce, code="TEST_BACKUP_INVALID")
    ciphertext = adoption._decode_b64(backup.ciphertext, code="TEST_BACKUP_INVALID")
    key = source._derive_backup_key(passphrase, salt)
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, adoption._BACKUP_AAD)
    payload = json.loads(plaintext)

    def forge_revision(revision: int):
        payload["revision"] = revision
        forged_nonce = os.urandom(12)
        forged_ciphertext = AESGCM(key).encrypt(
            forged_nonce,
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(),
            adoption._BACKUP_AAD,
        )
        return backup.model_copy(
            update={
                "nonce": adoption._b64(forged_nonce),
                "ciphertext": adoption._b64(forged_ciphertext),
                "ciphertext_fingerprint_ref": (
                    "ciphertext-fingerprint-ref:sha256:"
                    f"{hashlib.sha256(forged_ciphertext).hexdigest()}"
                ),
            }
        )

    with pytest.raises(CrmAdoptionError, match="CRM_ADOPTION_BACKUP_UNLOCK_FAILED"):
        CrmAdoptionStore(tmp_path / "target").preview_restore(
            CrmPortableRestoreRequest(
                passphrase=passphrase,
                backup=forge_revision(adoption.CRM_ADOPTION_MAX_REVISION + 1),
            )
        )

    exhausted_target = CrmAdoptionStore(tmp_path / "exhausted-target")
    with pytest.raises(CrmAdoptionConflict, match="CRM_ADOPTION_REVISION_EXHAUSTED"):
        exhausted_target.preview_restore(
            CrmPortableRestoreRequest(
                passphrase=passphrase,
                backup=forge_revision(adoption.CRM_ADOPTION_MAX_REVISION),
            )
        )
    assert not AuthorityLeaseStore(
        exhausted_target.state_dir / "authority"
    ).list_leases()

    near_exhaustion_target = CrmAdoptionStore(tmp_path / "near-exhaustion-target")
    near_exhaustion_request = CrmPortableRestoreRequest(
        passphrase=passphrase,
        backup=forge_revision(adoption.CRM_ADOPTION_MAX_REVISION - 1),
    )
    near_exhaustion_preview = near_exhaustion_target.preview_restore(
        near_exhaustion_request
    )
    near_exhaustion_commit = CrmPortableRestoreCommitRequest(
        **near_exhaustion_request.model_dump(mode="python"),
        preview_ref=near_exhaustion_preview.preview_ref,
        approval_ref=near_exhaustion_preview.approval_ref,
    )
    near_exhaustion_idempotency_ref = (
        "idempotency-ref:crm-adoption-test:near-exhaustion-restore"
    )
    _capture_restore(
        near_exhaustion_target,
        near_exhaustion_commit,
        idempotency_ref=near_exhaustion_idempotency_ref,
    )
    near_exhaustion_target.commit_restore(
        request=near_exhaustion_commit,
        idempotency_ref=near_exhaustion_idempotency_ref,
        confirmed=True,
    )
    exhausted_view = near_exhaustion_target.read_view()
    assert exhausted_view.revision == adoption.CRM_ADOPTION_MAX_REVISION
    assert exhausted_view.storage_state == "blocked_revision_exhausted"
    assert "fresh CRM workspace" in exhausted_view.next_safe_action


def test_mutation_preview_rejects_exhausted_revision_before_approval(
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    store._secure_state_dir()
    store._write_state(
        adoption.CrmAdoptionState(revision=adoption.CRM_ADOPTION_MAX_REVISION)
    )

    with pytest.raises(CrmAdoptionConflict, match="CRM_ADOPTION_REVISION_EXHAUSTED"):
        store.preview_mutation(
            _create_request(revision=adoption.CRM_ADOPTION_MAX_REVISION)
        )
    assert not AuthorityLeaseStore(store.state_dir / "authority").list_leases()


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
    assert preview.affected_count == 1
    assert preview.impact_status == "exact"
    assert preview.rollback_available is False
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
    assert recovery_preview.affected_count is None
    assert recovery_preview.impact_status == "unknown_current_state"
    assert recovery_preview.rollback_available is False
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
    invalid_key_target.key_file.chmod(0o600)
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


def test_restore_repairs_malformed_key_when_workspace_has_no_state(
    tmp_path: Path,
) -> None:
    source = CrmAdoptionStore(tmp_path / "source")
    _commit(source, _create_request(name="Recovered Person"), suffix="empty-key-source")
    passphrase = "correct horse battery staple"
    backup = source.create_portable_backup(
        CrmPortableBackupRequest(passphrase=passphrase)
    )

    target = CrmAdoptionStore(tmp_path / "target")
    target.state_dir.mkdir(parents=True)
    target.key_file.write_bytes(b"malformed-key")
    target.key_file.chmod(0o600)
    assert target.read_view().storage_state == "locked"
    restore = CrmPortableRestoreRequest(passphrase=passphrase, backup=backup)
    preview = target.preview_restore(restore)
    request = CrmPortableRestoreCommitRequest(
        **restore.model_dump(mode="python"),
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    idempotency_ref = "idempotency-ref:crm-adoption-test:empty-key-recovery"
    _capture_restore(target, request, idempotency_ref=idempotency_ref)
    target.commit_restore(
        request=request,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )

    assert target.read_view().records[0].display_name == "Recovered Person"
    assert target.key_file.stat().st_size == 32
    assert len(list(target.state_dir.glob("*.invalid-*"))) == 1


def test_restore_preview_is_invalidated_when_key_readability_changes(
    tmp_path: Path,
) -> None:
    source = CrmAdoptionStore(tmp_path / "source")
    _commit(source, _create_request(name="Backup Person"), suffix="key-bound-source")
    passphrase = "correct horse battery staple"
    backup = source.create_portable_backup(
        CrmPortableBackupRequest(passphrase=passphrase)
    )
    target = CrmAdoptionStore(tmp_path / "target")
    _commit(target, _create_request(name="Current Person"), suffix="key-bound-target")
    restore = CrmPortableRestoreRequest(passphrase=passphrase, backup=backup)
    preview = target.preview_restore(restore)
    target.key_file.unlink()
    request = CrmPortableRestoreCommitRequest(
        **restore.model_dump(mode="python"),
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )

    assert target.read_view().storage_state == "locked"
    with pytest.raises(CrmAdoptionError, match="EXACT_APPROVAL_REQUIRED"):
        target.capture_approval(
            request=CrmAdoptionApprovalCaptureRequest(
                operation="restore",
                restore=request,
            ),
            idempotency_ref=(
                "idempotency-ref:crm-adoption-test:key-readability-change"
            ),
            confirmed=True,
        )


def test_unreadable_restore_approval_can_use_a_new_idempotency_scope(
    tmp_path: Path,
) -> None:
    source = CrmAdoptionStore(tmp_path / "source")
    _commit(source, _create_request(name="Backup Person"), suffix="rescope-source")
    passphrase = "correct horse battery staple"
    backup = source.create_portable_backup(
        CrmPortableBackupRequest(passphrase=passphrase)
    )
    target = CrmAdoptionStore(tmp_path / "target")
    target.state_dir.mkdir(parents=True)
    target.state_file.write_bytes(b"corrupt-state")
    restore = CrmPortableRestoreRequest(passphrase=passphrase, backup=backup)
    preview = target.preview_restore(restore)
    request = CrmPortableRestoreCommitRequest(
        **restore.model_dump(mode="python"),
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    capture = CrmAdoptionApprovalCaptureRequest(
        operation="restore",
        restore=request,
    )

    first = target.capture_approval(
        request=capture,
        idempotency_ref="idempotency-ref:crm-adoption-test:restore-rescope-one",
        confirmed=True,
    )
    second_idempotency_ref = "idempotency-ref:crm-adoption-test:restore-rescope-two"
    second = target.capture_approval(
        request=capture,
        idempotency_ref=second_idempotency_ref,
        confirmed=True,
    )
    receipt = target.commit_restore(
        request=request,
        idempotency_ref=second_idempotency_ref,
        confirmed=True,
    )

    assert first.approval_ref == second.approval_ref == preview.approval_ref
    assert first.approval_validation_ref != second.approval_validation_ref
    assert receipt.after_revision == 2
    assert target.read_view().records[0].display_name == "Backup Person"


def test_unsafe_state_is_blocked_instead_of_presented_as_recoverable(
    tmp_path: Path,
) -> None:
    source = CrmAdoptionStore(tmp_path / "source")
    _commit(source, _create_request(), suffix="unsafe-state-source")
    passphrase = "correct horse battery staple"
    backup = source.create_portable_backup(
        CrmPortableBackupRequest(passphrase=passphrase)
    )
    store = CrmAdoptionStore(tmp_path / "crm")
    store.state_dir.mkdir(parents=True)
    outside = tmp_path / "outside-state"
    outside.write_bytes(b"not CRM state")
    store.state_file.symlink_to(outside)

    view = store.read_view()
    assert view.storage_state == "blocked_unsafe"
    assert view.records == []
    assert "repair the unsafe local CRM storage" in view.next_safe_action
    with pytest.raises(CrmAdoptionError, match="STATE_UNSAFE"):
        store.preview_restore(
            CrmPortableRestoreRequest(passphrase=passphrase, backup=backup)
        )


@pytest.mark.parametrize(
    "unsafe_kind", ["symlink", "directory", "permissive", "hardlink"]
)
def test_unsafe_key_without_state_is_blocked_before_restore(
    tmp_path: Path,
    unsafe_kind: str,
) -> None:
    source = CrmAdoptionStore(tmp_path / "source")
    _commit(source, _create_request(), suffix=f"unsafe-key-source-{unsafe_kind}")
    passphrase = "correct horse battery staple"
    backup = source.create_portable_backup(
        CrmPortableBackupRequest(passphrase=passphrase)
    )
    store = CrmAdoptionStore(tmp_path / "crm")
    store.state_dir.mkdir(parents=True)
    if unsafe_kind == "symlink":
        outside = tmp_path / "outside-key"
        outside.write_bytes(b"0" * 32)
        store.key_file.symlink_to(outside)
    elif unsafe_kind == "directory":
        store.key_file.mkdir()
    else:
        store.key_file.write_bytes(b"0" * 32)
        store.key_file.chmod(0o600 if unsafe_kind == "hardlink" else 0o644)
        if unsafe_kind == "hardlink":
            os.link(store.key_file, tmp_path / "outside-key-hardlink")

    view = store.read_view()
    assert view.storage_state == "blocked_unsafe"
    assert view.records == []
    assert "repair the unsafe local CRM storage" in view.next_safe_action
    with pytest.raises(CrmAdoptionError, match="KEY_UNSAFE"):
        store.preview_restore(
            CrmPortableRestoreRequest(passphrase=passphrase, backup=backup)
        )


def test_approval_capture_replays_durable_mutation_and_restore_receipts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    mutation_store = CrmAdoptionStore(tmp_path / "mutation")
    mutation = _create_request()
    mutation_preview = mutation_store.preview_mutation(mutation)
    mutation_commit = CrmAdoptionCommitRequest(
        mutation=mutation,
        preview_ref=mutation_preview.preview_ref,
        approval_ref=mutation_preview.approval_ref,
    )
    mutation_capture = CrmAdoptionApprovalCaptureRequest(
        operation="mutation",
        mutation=mutation_commit,
    )
    mutation_idempotency_ref = (
        "idempotency-ref:crm-adoption-test:approval-lost-response"
    )
    mutation_store.capture_approval(
        request=mutation_capture,
        idempotency_ref=mutation_idempotency_ref,
        confirmed=True,
    )
    mutation_receipt = mutation_store.commit_mutation(
        request=mutation,
        preview_ref=mutation_preview.preview_ref,
        approval_ref=mutation_preview.approval_ref,
        idempotency_ref=mutation_idempotency_ref,
        confirmed=True,
    )
    replayed_mutation_approval = mutation_store.capture_approval(
        request=mutation_capture,
        idempotency_ref=mutation_idempotency_ref,
        confirmed=True,
    )
    assert (
        replayed_mutation_approval.approval_validation_ref
        == mutation_receipt.approval_validation_ref
    )
    assert (
        mutation_store.commit_mutation(
            request=mutation,
            preview_ref=mutation_preview.preview_ref,
            approval_ref=mutation_preview.approval_ref,
            idempotency_ref=mutation_idempotency_ref,
            confirmed=True,
        ).replayed
        is True
    )

    source = CrmAdoptionStore(tmp_path / "source")
    _commit(source, _create_request(name="Restore Person"), suffix="approval-source")
    passphrase = "correct horse battery staple"
    backup = source.create_portable_backup(
        CrmPortableBackupRequest(passphrase=passphrase)
    )
    restore_store = CrmAdoptionStore(tmp_path / "restore")
    restore = CrmPortableRestoreRequest(passphrase=passphrase, backup=backup)
    restore_preview = restore_store.preview_restore(restore)
    restore_commit = CrmPortableRestoreCommitRequest(
        **restore.model_dump(mode="python"),
        preview_ref=restore_preview.preview_ref,
        approval_ref=restore_preview.approval_ref,
    )
    restore_capture = CrmAdoptionApprovalCaptureRequest(
        operation="restore",
        restore=restore_commit,
    )
    restore_idempotency_ref = (
        "idempotency-ref:crm-adoption-test:restore-approval-lost-response"
    )
    restore_store.capture_approval(
        request=restore_capture,
        idempotency_ref=restore_idempotency_ref,
        confirmed=True,
    )
    opened = 0
    open_portable_backup = restore_store._open_portable_backup

    def count_open(request: CrmPortableRestoreRequest):
        nonlocal opened
        opened += 1
        return open_portable_backup(request)

    monkeypatch.setattr(restore_store, "_open_portable_backup", count_open)
    restore_receipt = restore_store.commit_restore(
        request=restore_commit,
        idempotency_ref=restore_idempotency_ref,
        confirmed=True,
    )
    replayed_restore_approval = restore_store.capture_approval(
        request=restore_capture,
        idempotency_ref=restore_idempotency_ref,
        confirmed=True,
    )
    assert opened == 1
    assert (
        replayed_restore_approval.approval_validation_ref
        == restore_receipt.approval_validation_ref
    )
    assert (
        restore_store.commit_restore(
            request=restore_commit,
            idempotency_ref=restore_idempotency_ref,
            confirmed=True,
        ).replayed
        is True
    )


def test_key_read_rejects_wrong_size_before_materializing_file(tmp_path: Path) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    store.state_dir.mkdir(parents=True)
    store.key_file.write_bytes(b"x" * 1_000_000)
    store.key_file.chmod(0o600)

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


def test_corrupt_state_recovery_preserves_and_replaces_orphan_pending_audit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = CrmAdoptionStore(tmp_path / "source")
    _commit(source, _create_request(name="Recovered Person"), suffix="source")
    passphrase = "correct horse battery staple"
    backup = source.create_portable_backup(
        CrmPortableBackupRequest(passphrase=passphrase)
    )

    target = CrmAdoptionStore(tmp_path / "target")
    request = _create_request(name="Interrupted Person")
    preview = target.preview_mutation(request)
    idempotency_ref = "idempotency-ref:crm-adoption-test:orphan-audit-source"
    target.capture_approval(
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
    append_audit = target._append_audit
    monkeypatch.setattr(
        target,
        "_append_audit",
        lambda _receipt: (_ for _ in ()).throw(OSError("synthetic audit failure")),
    )
    with pytest.raises(CrmAdoptionError, match="AUDIT_FINALIZATION_REQUIRED"):
        target.commit_mutation(
            request=request,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
            idempotency_ref=idempotency_ref,
            confirmed=True,
        )
    orphan_payload = target.pending_audit_file.read_bytes()
    target.state_file.write_bytes(b"corrupt-state")
    monkeypatch.setattr(target, "_append_audit", append_audit)

    restore = CrmPortableRestoreRequest(passphrase=passphrase, backup=backup)
    restore_preview = target.preview_restore(restore)
    restore_request = CrmPortableRestoreCommitRequest(
        **restore.model_dump(mode="python"),
        preview_ref=restore_preview.preview_ref,
        approval_ref=restore_preview.approval_ref,
    )
    restore_idempotency_ref = "idempotency-ref:crm-adoption-test:orphan-audit-recovery"
    _capture_restore(
        target,
        restore_request,
        idempotency_ref=restore_idempotency_ref,
    )
    target.commit_restore(
        request=restore_request,
        idempotency_ref=restore_idempotency_ref,
        confirmed=True,
    )

    assert target.read_view().records[0].display_name == "Recovered Person"
    assert not target.pending_audit_file.exists()
    quarantined = list(target.state_dir.glob("*.orphan-*"))
    assert len(quarantined) == 1
    assert quarantined[0].read_bytes() == orphan_payload


def test_corrupt_state_recovery_blocks_unsafe_pending_audit_before_preview(
    tmp_path: Path,
) -> None:
    source = CrmAdoptionStore(tmp_path / "source")
    _commit(source, _create_request(), suffix="unsafe-pending-source")
    passphrase = "correct horse battery staple"
    backup = source.create_portable_backup(
        CrmPortableBackupRequest(passphrase=passphrase)
    )
    target = CrmAdoptionStore(tmp_path / "target")
    target._secure_state_dir()
    target.state_file.write_bytes(b"corrupt-state")
    unsafe_target = tmp_path / "unsafe-pending-target"
    unsafe_target.write_text("not a journal", encoding="utf-8")
    target.pending_audit_file.symlink_to(unsafe_target)

    view = target.read_view()
    assert view.storage_state == "blocked_unsafe"
    assert "unsafe local CRM audit storage" in view.next_safe_action
    with pytest.raises(CrmAdoptionError, match="AUDIT_PENDING_UNSAFE"):
        target.preview_restore(
            CrmPortableRestoreRequest(passphrase=passphrase, backup=backup)
        )


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
    with pytest.raises(ValueError, match="CRM_ADOPTION_DISPLAY_NAME_REQUIRED"):
        CrmAdoptionRecordPatch(display_name=None)
    with pytest.raises(ValueError):
        CrmAdoptionRecordDraft(
            record_kind="opportunity",
            display_name="Unsafe rounded amount",
            amount_minor=adoption.CRM_ADOPTION_MAX_AMOUNT_MINOR + 1,
        )
    with pytest.raises(ValueError):
        CrmAdoptionRecordPatch(amount_minor=adoption.CRM_ADOPTION_MAX_AMOUNT_MINOR + 1)
    assert (
        CrmAdoptionRecordDraft(
            record_kind="opportunity",
            display_name="Largest exact-cent amount",
            amount_minor=adoption.CRM_ADOPTION_MAX_AMOUNT_MINOR,
        ).amount_minor
        == 90_071_992_547_409
    )

    store = CrmAdoptionStore(tmp_path / "crm")
    _commit(store, _create_request(), suffix="cli")
    private_workspace_name = "Founder Client Secret Workspace"
    store._write_state(
        store._read_state().model_copy(
            update={"workspace_name": private_workspace_name}
        )
    )
    assert crm_cli_main(["inspect-adoption", "--state-dir", str(store.state_dir)]) == 0
    safe_output = capsys.readouterr().out
    assert "Private Person" not in safe_output
    assert "private.person@example.test" not in safe_output
    assert private_workspace_name not in safe_output
    assert '"workspace_name": "Private workspace"' in safe_output
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
    assert private_workspace_name in private_output

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


def test_crm_body_guard_rejects_oversize_and_deep_json_with_cors() -> None:
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
    for route in (
        "/control-center/crm/adoption/query",
        "/control-center/crm/adoption/preview",
        "/control-center/crm/adoption/approval",
        "/control-center/crm/adoption/commit",
        "/control-center/crm/adoption/backup",
        "/control-center/crm/adoption/restore-preview",
        "/control-center/crm/adoption/restore",
    ):
        nested = client.post(
            route,
            content=deeply_nested,
            headers={
                "content-type": "application/json",
                "X-UAA-Idempotency-Key": ("idempotency-ref:crm-api:body-guard"),
                "X-UAA-Operator-Confirmed": "true",
            },
        )
        assert nested.status_code == 413, route
        assert nested.headers["Cache-Control"] == "no-store", route
        assert nested.json()["code"] == ("CRM_ADOPTION_REQUEST_BODY_LIMIT_EXCEEDED"), (
            route
        )


def test_crm_body_limit_is_published_for_every_json_input_route() -> None:
    paths = app.openapi()["paths"]
    for route in (
        "/control-center/crm/adoption/query",
        "/control-center/crm/adoption/preview",
        "/control-center/crm/adoption/approval",
        "/control-center/crm/adoption/commit",
        "/control-center/crm/adoption/backup",
        "/control-center/crm/adoption/restore-preview",
        "/control-center/crm/adoption/restore",
    ):
        response = paths[route]["post"]["responses"]["413"]
        schema = response["content"]["application/json"]["schema"]
        assert schema["$ref"].endswith("/CrmAdoptionBodyLimitResponse")


def test_structurally_incomplete_audit_event_blocks_reads_and_preview(
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    _commit(store, _create_request(name="Protected Person"), suffix="audit-shape")
    store.audit_file.write_text("{}\n", encoding="utf-8")

    view = store.read_view()
    assert view.storage_state == "blocked_audit_unreadable"
    assert [item.display_name for item in view.records] == ["Protected Person"]
    with pytest.raises(CrmAdoptionError, match="AUDIT_UNREADABLE"):
        store.preview_mutation(_create_request(revision=1, name="Blocked Person"))


def test_restore_preserves_target_local_idempotency_receipts(tmp_path: Path) -> None:
    source = CrmAdoptionStore(tmp_path / "source")
    _commit(source, _create_request(name="Backup Person"), suffix="receipt-source")
    passphrase = "correct horse battery staple"
    backup = source.create_portable_backup(
        CrmPortableBackupRequest(passphrase=passphrase)
    )

    target = CrmAdoptionStore(tmp_path / "target")
    local_request = _create_request(name="Local Person")
    local_preview = target.preview_mutation(local_request)
    local_idempotency_ref = "idempotency-ref:crm-adoption-test:local-before-restore"
    target.capture_approval(
        request=CrmAdoptionApprovalCaptureRequest(
            operation="mutation",
            mutation=CrmAdoptionCommitRequest(
                mutation=local_request,
                preview_ref=local_preview.preview_ref,
                approval_ref=local_preview.approval_ref,
            ),
        ),
        idempotency_ref=local_idempotency_ref,
        confirmed=True,
    )
    local_receipt = target.commit_mutation(
        request=local_request,
        preview_ref=local_preview.preview_ref,
        approval_ref=local_preview.approval_ref,
        idempotency_ref=local_idempotency_ref,
        confirmed=True,
    )

    restore = CrmPortableRestoreRequest(passphrase=passphrase, backup=backup)
    preview = target.preview_restore(restore)
    commit = CrmPortableRestoreCommitRequest(
        **restore.model_dump(mode="python"),
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    restore_idempotency_ref = "idempotency-ref:crm-adoption-test:receipt-restore"
    _capture_restore(target, commit, idempotency_ref=restore_idempotency_ref)
    target.commit_restore(
        request=commit,
        idempotency_ref=restore_idempotency_ref,
        confirmed=True,
    )

    replay = target.commit_mutation(
        request=local_request,
        preview_ref=local_preview.preview_ref,
        approval_ref=local_preview.approval_ref,
        idempotency_ref=local_idempotency_ref,
        confirmed=True,
    )
    assert replay.replayed is True
    assert replay.receipt_ref == local_receipt.receipt_ref


def test_unreadable_recovery_surfaces_audit_blocker_before_restore(
    tmp_path: Path,
) -> None:
    source = CrmAdoptionStore(tmp_path / "source")
    _commit(source, _create_request(name="Backup Person"), suffix="blocked-restore")
    passphrase = "correct horse battery staple"
    backup = source.create_portable_backup(
        CrmPortableBackupRequest(passphrase=passphrase)
    )
    target = CrmAdoptionStore(tmp_path / "target")
    target.state_dir.mkdir(parents=True)
    target.state_file.write_bytes(b"corrupt-state")
    target.audit_file.write_text("{}\n", encoding="utf-8")

    view = target.read_view()
    assert view.storage_state == "blocked_audit_unreadable"
    assert "before restoring" in view.next_safe_action
    with pytest.raises(CrmAdoptionError, match="AUDIT_UNREADABLE"):
        target.preview_restore(
            CrmPortableRestoreRequest(passphrase=passphrase, backup=backup)
        )


def test_record_version_exhaustion_is_rejected_during_preview(
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    receipt = _commit(store, _create_request(), suffix="record-version")
    state = store._read_state()
    record = state.records[0].model_copy(
        update={"version": adoption.CRM_ADOPTION_MAX_REVISION}
    )
    store._write_state(state.model_copy(update={"records": [record]}))
    request = CrmAdoptionMutationRequest(
        action="update",
        expected_revision=1,
        target_ref=receipt.target_ref,
        patch=CrmAdoptionRecordPatch(display_name="Cannot increment"),
    )

    with pytest.raises(CrmAdoptionConflict, match="RECORD_VERSION_EXHAUSTED"):
        store.preview_mutation(request)


def test_authority_unsafe_idempotency_ref_is_rejected_before_approval(
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    request = _create_request()
    preview = store.preview_mutation(request)

    with pytest.raises(CrmAdoptionError, match="SAFE_REF_REQUIRED"):
        store.capture_approval(
            request=CrmAdoptionApprovalCaptureRequest(
                operation="mutation",
                mutation=CrmAdoptionCommitRequest(
                    mutation=request,
                    preview_ref=preview.preview_ref,
                    approval_ref=preview.approval_ref,
                ),
            ),
            idempotency_ref="idempotency-ref:crm-client:secret-operation",
            confirmed=True,
        )
    assert not (store.state_dir / "authority").exists()


def test_crm_approval_grant_expires_after_five_minutes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    request = _create_request()
    preview = store.preview_mutation(request)
    idempotency_ref = "idempotency-ref:crm-adoption-test:five-minute-approval"
    approval = store.capture_approval(
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
    assert approval.expires_at is not None
    captured_at = adoption._utc_now()
    assert approval.expires_at <= captured_at + timedelta(minutes=5)

    monkeypatch.setattr(
        adoption,
        "_utc_now",
        lambda: captured_at + timedelta(minutes=6),
    )
    with pytest.raises(CrmAdoptionError, match="APPROVAL_EXPIRED"):
        store.commit_mutation(
            request=request,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
            idempotency_ref=idempotency_ref,
            confirmed=True,
        )


def test_key_publication_removes_temporary_link_before_directory_fsync(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    store._secure_state_dir()
    fsync = adoption.os.fsync
    observed_link_counts: list[int] = []

    def observe_directory_fsync(descriptor: int) -> None:
        if adoption.stat.S_ISDIR(os.fstat(descriptor).st_mode):
            observed_link_counts.append(store.key_file.stat().st_nlink)
            assert not list(store.state_dir.glob(f".{store.key_file.name}.*.tmp"))
        fsync(descriptor)

    monkeypatch.setattr(adoption.os, "fsync", observe_directory_fsync)
    store._create_key()

    assert observed_link_counts == [1]
    assert store.key_file.stat().st_nlink == 1


def test_recovery_state_identity_invalidates_pre_recovery_mutation_approval(
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    first = _commit(store, _create_request(name="First Person"), suffix="epoch-one")
    passphrase = "correct horse battery staple"
    backup = store.create_portable_backup(
        CrmPortableBackupRequest(passphrase=passphrase)
    )
    _commit(
        store,
        _create_request(revision=1, name="Second Person"),
        suffix="epoch-two",
    )
    old_request = CrmAdoptionMutationRequest(
        action="update",
        expected_revision=2,
        target_ref=first.target_ref,
        patch=CrmAdoptionRecordPatch(display_name="Old approved change"),
    )
    old_preview = store.preview_mutation(old_request)
    old_idempotency_ref = "idempotency-ref:crm-adoption-test:old-epoch-approval"
    store.capture_approval(
        request=CrmAdoptionApprovalCaptureRequest(
            operation="mutation",
            mutation=CrmAdoptionCommitRequest(
                mutation=old_request,
                preview_ref=old_preview.preview_ref,
                approval_ref=old_preview.approval_ref,
            ),
        ),
        idempotency_ref=old_idempotency_ref,
        confirmed=True,
    )

    store.state_file.write_bytes(b"corrupt-state")
    restore = CrmPortableRestoreRequest(passphrase=passphrase, backup=backup)
    restore_preview = store.preview_restore(restore)
    restore_commit = CrmPortableRestoreCommitRequest(
        **restore.model_dump(mode="python"),
        preview_ref=restore_preview.preview_ref,
        approval_ref=restore_preview.approval_ref,
    )
    restore_idempotency_ref = "idempotency-ref:crm-adoption-test:new-epoch-restore"
    _capture_restore(store, restore_commit, idempotency_ref=restore_idempotency_ref)
    store.commit_restore(
        request=restore_commit,
        idempotency_ref=restore_idempotency_ref,
        confirmed=True,
    )
    assert store.read_view().revision == 2

    with pytest.raises(CrmAdoptionError, match="EXACT_APPROVAL_REQUIRED"):
        store.commit_mutation(
            request=old_request,
            preview_ref=old_preview.preview_ref,
            approval_ref=old_preview.approval_ref,
            idempotency_ref=old_idempotency_ref,
            confirmed=True,
        )
