from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.dev.uaa_crm import main as crm_cli_main
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.crm import (
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
    return store.commit_mutation(
        request=request,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
        idempotency_ref=f"idempotency-ref:crm-adoption-test:{suffix}",
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
    receipt = store.commit_mutation(
        request=request,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
        idempotency_ref="idempotency-ref:crm-adoption-test:replay",
        confirmed=True,
    )
    replay = store.commit_mutation(
        request=request,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
        idempotency_ref="idempotency-ref:crm-adoption-test:replay",
        confirmed=True,
    )
    assert replay.receipt_ref == receipt.receipt_ref
    assert replay.replayed is True

    with pytest.raises(CrmAdoptionConflict, match="IDEMPOTENCY_CONFLICT"):
        store.commit_mutation(
            request=request,
            preview_ref=preview.preview_ref,
            approval_ref="approval-ref:crm-adoption:substituted",
            idempotency_ref="idempotency-ref:crm-adoption-test:replay",
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
            idempotency_ref="idempotency-ref:crm-adoption-test:replay",
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

    def fail_state_write(_state: object) -> None:
        raise OSError("synthetic state write failure")

    monkeypatch.setattr(store, "_write_state", fail_state_write)
    with pytest.raises(OSError, match="synthetic state write failure"):
        store.commit_mutation(
            request=request,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
            idempotency_ref="idempotency-ref:crm-adoption-test:state-write-failure",
            confirmed=True,
        )

    assert not store.audit_file.exists()
    assert store.read_view().revision == 0


def test_audit_failure_keeps_authoritative_state_and_replay_repairs_it(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    store = CrmAdoptionStore(tmp_path / "crm")
    request = _create_request()
    preview = store.preview_mutation(request)
    idempotency_ref = "idempotency-ref:crm-adoption-test:audit-repair"
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

    assert store.read_view().revision == 1
    assert not store.audit_file.exists()
    replay = store.commit_mutation(
        request=request,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    assert replay.replayed is True
    assert replay.after_revision == 1
    assert store.audit_file.exists()
    assert attempts == 2


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
    receipt = store.commit_mutation(
        request=request,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
        idempotency_ref="idempotency-ref:crm-adoption-test:import",
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
    restore_request = CrmPortableRestoreRequest(
        passphrase=passphrase, backup=backup
    )
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
    receipt = target.commit_restore(
        request=commit_request,
        idempotency_ref="idempotency-ref:crm-adoption-test:restore",
        confirmed=True,
    )
    assert receipt.after_revision == 2
    assert target.read_view().records[0].display_name == "Private Person"
    replay = target.commit_restore(
        request=commit_request,
        idempotency_ref="idempotency-ref:crm-adoption-test:restore",
        confirmed=True,
    )
    assert replay.receipt_ref == receipt.receipt_ref
    assert replay.replayed is True
    with pytest.raises(CrmAdoptionConflict, match="IDEMPOTENCY_CONFLICT"):
        target.commit_restore(
            request=commit_request.model_copy(
                update={"approval_ref": "approval-ref:crm-adoption:substituted"}
            ),
            idempotency_ref="idempotency-ref:crm-adoption-test:restore",
            confirmed=True,
        )

    with pytest.raises(CrmAdoptionError, match="BACKUP_UNLOCK_FAILED"):
        target.preview_restore(
            CrmPortableRestoreRequest(passphrase="wrong passphrase value", backup=backup)
        )

    target.state_file.write_bytes(b"corrupt")
    assert target.read_view().storage_state == "recovery_required"
    recovery_preview = target.preview_restore(restore_request)
    recovery_request = CrmPortableRestoreCommitRequest(
        **restore_request.model_dump(mode="python"),
        preview_ref=recovery_preview.preview_ref,
        approval_ref=recovery_preview.approval_ref,
    )
    target.commit_restore(
        request=recovery_request,
        idempotency_ref="idempotency-ref:crm-adoption-test:recovery",
        confirmed=True,
    )
    assert target.read_view().storage_state == "ready"


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

    assert target.read_view().records[0].display_name == "Private Person"
    assert not target.audit_file.exists()
    replay = target.commit_restore(
        request=request,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    assert replay.replayed is True
    assert target.audit_file.exists()
    assert attempts == 2


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
    assert crm_cli_main(
        ["inspect-adoption", "--state-dir", str(store.state_dir)]
    ) == 0
    safe_output = capsys.readouterr().out
    assert "Private Person" not in safe_output
    assert "private.person@example.test" not in safe_output
    assert '"private_values_included": false' in safe_output

    assert crm_cli_main(
        [
            "inspect-adoption",
            "--state-dir",
            str(store.state_dir),
            "--show-private",
        ]
    ) == 0
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

    committed = client.post(
        "/control-center/crm/adoption/commit",
        json=commit_body,
        headers={
            "X-UAA-Idempotency-Key": "idempotency-ref:crm-api:test",
            "X-UAA-Operator-Confirmed": "true",
        },
    )
    assert committed.status_code == 200
    assert committed.json()["data"]["external_write_performed"] is False
    assert committed.json()["data"]["approval_authority_granted"] is True
    populated = client.get(
        "/control-center/crm/adoption", params={"query": "example.test"}
    ).json()["data"]
    assert populated["records"][0]["display_name"] == "Private Person"

    backup_response = client.post(
        "/control-center/crm/adoption/backup",
        json={"passphrase": "correct horse battery staple"},
        headers={"X-UAA-Idempotency-Key": "idempotency-ref:crm-api:backup"},
    )
    assert backup_response.status_code == 200
    backup = backup_response.json()["data"]
    assert "Private Person" not in json.dumps(backup)
    assert backup["private_values_encrypted"] is True
