#!/usr/bin/env python3
"""Verify the bounded founder-private Queue V2 Q32 CRM adoption loop."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.dev.uaa_crm import main as crm_cli_main  # noqa: E402
from ultimate_ai_agent.core.authority import AuthorityLeaseStore  # noqa: E402
from ultimate_ai_agent.core.crm import (  # noqa: E402
    CRM_ADOPTION_CONTRACT_REF,
    CRM_ADOPTION_FOUNDATION_REF,
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


RECORD_KINDS = (
    "person",
    "organization",
    "property",
    "relationship",
    "opportunity",
    "activity",
    "follow_up",
)
PRIVATE_MARKERS = (
    "Q32 Synthetic Private",
    "q32-private@example.test",
    "+1 555 0132",
)


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


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
        idempotency_ref=f"idempotency-ref:queue-v2-q32-verifier:{suffix}",
        confirmed=True,
    )


def verify() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="uaa-q32-verifier-") as directory:
        root = Path(directory)
        source = CrmAdoptionStore(root / "source")
        _require(source.read_view().storage_state == "empty", "Q32_EMPTY_STATE_FAILED")

        receipts = []
        for revision, kind in enumerate(RECORD_KINDS):
            receipts.append(
                _commit(
                    source,
                    CrmAdoptionMutationRequest(
                        action="create",
                        expected_revision=revision,
                        record=CrmAdoptionRecordDraft(
                            record_kind=kind,
                            display_name=f"Q32 Synthetic Private {kind}",
                            email=(
                                "q32-private@example.test" if kind == "person" else None
                            ),
                            phone="+1 555 0132" if kind == "person" else None,
                            notes="Synthetic private workflow evidence.",
                            status="active",
                            tags=["q32", kind],
                            amount_minor=250_000 if kind == "opportunity" else None,
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
                    ),
                    suffix=f"create-{kind}",
                )
            )

        restarted = CrmAdoptionStore(source.state_dir)
        view = restarted.read_view(query="Q32 Synthetic")
        _require(view.revision == len(RECORD_KINDS), "Q32_RESTART_REVISION_FAILED")
        _require(len(view.records) == len(RECORD_KINDS), "Q32_SEARCH_FAILED")
        _require(
            {item.record_kind for item in view.records} == set(RECORD_KINDS),
            "Q32_RECORD_KIND_COVERAGE_FAILED",
        )

        person = next(item for item in view.records if item.record_kind == "person")
        updated = _commit(
            restarted,
            CrmAdoptionMutationRequest(
                action="update",
                expected_revision=view.revision,
                target_ref=person.record_ref,
                patch=CrmAdoptionRecordPatch(
                    status="priority",
                    notes="Synthetic corrected private workflow evidence.",
                ),
            ),
            suffix="update-person",
        )
        archived = _commit(
            restarted,
            CrmAdoptionMutationRequest(
                action="archive",
                expected_revision=updated.after_revision,
                target_ref=person.record_ref,
            ),
            suffix="archive-person",
        )
        undone = _commit(
            restarted,
            CrmAdoptionMutationRequest(
                action="undo",
                expected_revision=archived.after_revision,
            ),
            suffix="undo-archive",
        )
        _require(
            restarted.read_view().records[0].archived is False,
            "Q32_UNDO_FAILED",
        )

        import_request = CrmAdoptionMutationRequest(
            action="import_contacts",
            expected_revision=undone.after_revision,
            csv_text=(
                "name,email,phone,tags\n"
                "Q32 Synthetic Private person,duplicate@example.test,555-0000,duplicate\n"
                "Q32 Synthetic Private import,q32-import@example.test,555-0199,imported\n"
            ),
        )
        import_preview = restarted.preview_mutation(import_request)
        _require(import_preview.affected_count == 1, "Q32_IMPORT_COUNT_FAILED")
        _require(
            import_preview.duplicate_candidate_count == 1,
            "Q32_IMPORT_DUPLICATE_FAILED",
        )
        receipts.append(_commit(restarted, import_request, suffix="import"))

        backup = restarted.create_portable_backup(
            CrmPortableBackupRequest(passphrase="q32 synthetic backup passphrase")
        )
        serialized_backup = backup.model_dump_json()
        _require(
            not any(marker in serialized_backup for marker in PRIVATE_MARKERS),
            "Q32_BACKUP_PLAINTEXT_LEAK",
        )
        restore_request = CrmPortableRestoreRequest(
            passphrase="q32 synthetic backup passphrase",
            backup=backup,
        )
        target = CrmAdoptionStore(root / "target")
        restore_preview = target.preview_restore(restore_request)
        restore_receipt = target.commit_restore(
            request=CrmPortableRestoreCommitRequest(
                **restore_request.model_dump(mode="python"),
                preview_ref=restore_preview.preview_ref,
                approval_ref=restore_preview.approval_ref,
            ),
            idempotency_ref="idempotency-ref:queue-v2-q32-verifier:restore",
            confirmed=True,
        )
        _require(
            len(target.read_view().records) == len(RECORD_KINDS) + 1,
            "Q32_RESTORE_FAILED",
        )
        restore_replay = target.commit_restore(
            request=CrmPortableRestoreCommitRequest(
                **restore_request.model_dump(mode="python"),
                preview_ref=restore_preview.preview_ref,
                approval_ref=restore_preview.approval_ref,
            ),
            idempotency_ref="idempotency-ref:queue-v2-q32-verifier:restore",
            confirmed=True,
        )
        _require(
            restore_replay.receipt_ref == restore_receipt.receipt_ref
            and restore_replay.replayed,
            "Q32_RESTORE_REPLAY_FAILED",
        )
        try:
            target.preview_restore(
                CrmPortableRestoreRequest(
                    passphrase="q32 incorrect backup passphrase",
                    backup=backup,
                )
            )
        except CrmAdoptionError as exc:
            _require(
                str(exc) == "CRM_ADOPTION_BACKUP_UNLOCK_FAILED",
                "Q32_WRONG_PASSPHRASE_CODE_FAILED",
            )
        else:
            raise RuntimeError("Q32_WRONG_PASSPHRASE_FAIL_CLOSED_FAILED")

        target.state_file.write_bytes(b"corrupt")
        _require(
            target.read_view().storage_state == "recovery_required",
            "Q32_CORRUPTION_STATE_FAILED",
        )
        recovery_preview = target.preview_restore(restore_request)
        target.commit_restore(
            request=CrmPortableRestoreCommitRequest(
                **restore_request.model_dump(mode="python"),
                preview_ref=recovery_preview.preview_ref,
                approval_ref=recovery_preview.approval_ref,
            ),
            idempotency_ref="idempotency-ref:queue-v2-q32-verifier:recovery",
            confirmed=True,
        )
        _require(target.read_view().storage_state == "ready", "Q32_RECOVERY_FAILED")

        state_bytes = restarted.state_file.read_bytes()
        audit_text = restarted.audit_file.read_text(encoding="utf-8")
        _require(
            not any(marker.encode("utf-8") in state_bytes for marker in PRIVATE_MARKERS),
            "Q32_STATE_PLAINTEXT_LEAK",
        )
        _require(
            not any(marker in audit_text for marker in PRIVATE_MARKERS),
            "Q32_AUDIT_PRIVATE_LEAK",
        )
        _require(restarted.state_dir.stat().st_mode & 0o077 == 0, "Q32_DIR_MODE_FAILED")
        _require(restarted.state_file.stat().st_mode & 0o077 == 0, "Q32_STATE_MODE_FAILED")
        _require(restarted.key_file.stat().st_mode & 0o077 == 0, "Q32_KEY_MODE_FAILED")
        _require(restarted.key_file.stat().st_nlink == 1, "Q32_KEY_LINK_FAILED")

        active_leases = AuthorityLeaseStore(
            restarted.state_dir / "authority"
        ).list_leases(active_only=True)
        _require(bool(active_leases), "Q32_AUTHORITY_LEASE_MISSING")
        for receipt in [*receipts, updated, archived, undone, restore_receipt]:
            _require(receipt.approval_authority_granted, "Q32_APPROVAL_FAILED")
            _require(bool(receipt.authority_lease_ref), "Q32_LEASE_REF_FAILED")
            _require(bool(receipt.authority_decision_ref), "Q32_DECISION_REF_FAILED")
            _require(not receipt.external_write_performed, "Q32_EXTERNAL_WRITE_OCCURRED")

        cli_output = io.StringIO()
        with contextlib.redirect_stdout(cli_output):
            exit_code = crm_cli_main(
                ["inspect-adoption", "--state-dir", str(restarted.state_dir)]
            )
        _require(exit_code == 0, "Q32_CLI_FAILED")
        safe_cli_text = cli_output.getvalue()
        _require(
            not any(marker in safe_cli_text for marker in PRIVATE_MARKERS),
            "Q32_CLI_PRIVATE_LEAK",
        )
        _require(
            json.loads(safe_cli_text)["private_values_included"] is False,
            "Q32_CLI_SAFE_DEFAULT_FAILED",
        )

        return {
            "schema_version": "queue-v2-q32-crm-functional-adoption-verification.v1",
            "contract_ref": CRM_ADOPTION_CONTRACT_REF,
            "foundation_contract_ref": CRM_ADOPTION_FOUNDATION_REF,
            "status": "verified",
            "record_kind_count": len(RECORD_KINDS),
            "restart_search_verified": True,
            "create_inspect_update_archive_undo_verified": True,
            "import_duplicate_review_verified": True,
            "encrypted_backup_restore_recovery_verified": True,
            "exact_local_approval_and_authority_lease_verified": True,
            "cli_private_values_default_omitted": True,
            "external_crm_write_performed": False,
            "provider_model_call_performed": False,
            "fixture_primary_truth": False,
            "public_or_production_claim": False,
        }


def main() -> int:
    try:
        result = verify()
    except (CrmAdoptionConflict, CrmAdoptionError, RuntimeError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": (
                        "queue-v2-q32-crm-functional-adoption-verification.v1"
                    ),
                    "status": "failed",
                    "safe_error_code": str(exc),
                },
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
