#!/usr/bin/env python3
"""Verify the bounded Queue V2 Q33 founder-private Work Board loop."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.dev.uaa_work_board import main as work_board_cli_main  # noqa: E402
from ultimate_ai_agent.core.authority import AuthorityLeaseStore  # noqa: E402
from ultimate_ai_agent.core.control_center.work_board_adoption import (  # noqa: E402
    WORK_BOARD_ADOPTION_CONTRACT_REF,
    WORK_BOARD_ADOPTION_STATE_FILE,
    WorkBoardAdoptionApprovalCaptureRequest,
    WorkBoardAdoptionCardDraft,
    WorkBoardAdoptionCommitRequest,
    WorkBoardAdoptionError,
    WorkBoardAdoptionMutationRequest,
    WorkBoardAdoptionPortableBackupRequest,
    WorkBoardAdoptionPortableRestoreRequest,
    WorkBoardAdoptionRestoreApprovalCaptureRequest,
    WorkBoardAdoptionRestoreCommitRequest,
    WorkBoardAdoptionStore,
)


PRIVATE_MARKERS = (
    "Q33 Synthetic Private",
    "Synthetic operator-only Work Board detail",
)


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def _commit(
    store: WorkBoardAdoptionStore,
    mutation: WorkBoardAdoptionMutationRequest,
    *,
    suffix: str,
):
    idempotency_ref = f"idempotency-ref:queue-v2-q33-work-board:{suffix}"
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
    return receipt


def verify() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="uaa-q33-work-board-verifier-") as directory:
        root = Path(directory)
        source = WorkBoardAdoptionStore(root / "source")
        _require(source.read_view().revision == 0, "Q33_WORK_BOARD_EMPTY_STATE_FAILED")

        created = _commit(
            source,
            WorkBoardAdoptionMutationRequest(
                action="create",
                expected_revision=0,
                draft=WorkBoardAdoptionCardDraft(
                    title="Q33 Synthetic Private briefing",
                    description="Synthetic operator-only Work Board detail",
                    priority="high",
                    tag_refs=("tag-ref:q33",),
                ),
            ),
            suffix="create",
        )
        _require(created.card_ref is not None, "Q33_WORK_BOARD_CREATE_FAILED")
        card_ref = created.card_ref

        restarted = WorkBoardAdoptionStore(source.state_dir)
        _require(
            restarted.read_view().active_cards[0].card_ref == card_ref,
            "Q33_WORK_BOARD_RESTART_FAILED",
        )
        updated = _commit(
            restarted,
            WorkBoardAdoptionMutationRequest(
                action="update",
                expected_revision=1,
                target_ref=card_ref,
                draft=WorkBoardAdoptionCardDraft(
                    title="Q33 Synthetic Private Monday briefing",
                    description="Synthetic operator-only Work Board detail",
                    priority="critical",
                    tag_refs=("tag-ref:q33", "tag-ref:daily-loop"),
                ),
            ),
            suffix="update",
        )
        moved = _commit(
            restarted,
            WorkBoardAdoptionMutationRequest(
                action="move",
                expected_revision=updated.after_revision,
                target_ref=card_ref,
                lane_ref="work-board-lane:doing",
            ),
            suffix="move",
        )
        archived = _commit(
            restarted,
            WorkBoardAdoptionMutationRequest(
                action="archive",
                expected_revision=moved.after_revision,
                target_ref=card_ref,
            ),
            suffix="archive",
        )
        recovered = _commit(
            restarted,
            WorkBoardAdoptionMutationRequest(
                action="recover",
                expected_revision=archived.after_revision,
                target_ref=card_ref,
            ),
            suffix="recover",
        )
        undone = _commit(
            restarted,
            WorkBoardAdoptionMutationRequest(
                action="undo",
                expected_revision=recovered.after_revision,
            ),
            suffix="undo",
        )
        _require(
            restarted.read_view().archived_cards[0].card_ref == card_ref,
            "Q33_WORK_BOARD_UNDO_FAILED",
        )
        final_recover = _commit(
            restarted,
            WorkBoardAdoptionMutationRequest(
                action="recover",
                expected_revision=undone.after_revision,
                target_ref=card_ref,
            ),
            suffix="final-recover",
        )

        passphrase = "q33 synthetic portable backup passphrase"
        backup = restarted.create_portable_backup(
            WorkBoardAdoptionPortableBackupRequest(passphrase=passphrase)
        )
        backup_text = backup.model_dump_json()
        _require(
            not any(marker in backup_text for marker in PRIVATE_MARKERS),
            "Q33_WORK_BOARD_BACKUP_PLAINTEXT_LEAK",
        )

        target = WorkBoardAdoptionStore(root / "target")
        restore = WorkBoardAdoptionPortableRestoreRequest(
            passphrase=passphrase,
            backup=backup,
        )
        restore_idempotency = "idempotency-ref:queue-v2-q33-work-board:restore"
        restore_preview = target.preview_restore(
            restore,
            idempotency_ref=restore_idempotency,
        )
        restore_scope = WorkBoardAdoptionRestoreCommitRequest(
            **restore.model_dump(mode="python"),
            preview_ref=restore_preview.preview_ref,
            approval_ref=restore_preview.approval_ref,
        )
        target.capture_restore_approval(
            WorkBoardAdoptionRestoreApprovalCaptureRequest(
                **restore_scope.model_dump(mode="python")
            ),
            idempotency_ref=restore_idempotency,
        )
        restore_receipt = target.commit_restore(
            restore_scope,
            idempotency_ref=restore_idempotency,
        )
        replay = target.commit_restore(
            restore_scope,
            idempotency_ref=restore_idempotency,
        )
        _require(
            replay.replayed and replay.receipt_ref == restore_receipt.receipt_ref,
            "Q33_WORK_BOARD_RESTORE_REPLAY_FAILED",
        )
        _require(
            target.read_view().active_cards[0].card_ref == card_ref,
            "Q33_WORK_BOARD_RESTORE_FAILED",
        )

        try:
            target.preview_restore(
                WorkBoardAdoptionPortableRestoreRequest(
                    passphrase="q33 incorrect portable backup passphrase",
                    backup=backup,
                ),
                idempotency_ref="idempotency-ref:queue-v2-q33-work-board:wrong-key",
            )
        except WorkBoardAdoptionError as exc:
            _require(
                str(exc) == "WORK_BOARD_ADOPTION_BACKUP_UNLOCK_FAILED",
                "Q33_WORK_BOARD_WRONG_KEY_CODE_FAILED",
            )
        else:
            raise RuntimeError("Q33_WORK_BOARD_WRONG_KEY_FAIL_CLOSED_FAILED")

        target.state_path.write_text("{", encoding="utf-8")
        _require(
            target.read_view().status == "recovery_required",
            "Q33_WORK_BOARD_CORRUPTION_STATE_FAILED",
        )
        recovery_idempotency = "idempotency-ref:queue-v2-q33-work-board:recovery"
        recovery_preview = target.preview_restore(
            restore,
            idempotency_ref=recovery_idempotency,
        )
        recovery_scope = WorkBoardAdoptionRestoreCommitRequest(
            **restore.model_dump(mode="python"),
            preview_ref=recovery_preview.preview_ref,
            approval_ref=recovery_preview.approval_ref,
        )
        target.capture_restore_approval(
            WorkBoardAdoptionRestoreApprovalCaptureRequest(
                **recovery_scope.model_dump(mode="python")
            ),
            idempotency_ref=recovery_idempotency,
        )
        target.commit_restore(
            recovery_scope,
            idempotency_ref=recovery_idempotency,
        )
        _require(target.read_view().status == "ready", "Q33_WORK_BOARD_RECOVERY_FAILED")

        _require(
            restarted.state_dir.stat().st_mode & 0o077 == 0,
            "Q33_WORK_BOARD_DIR_MODE_FAILED",
        )
        _require(
            (restarted.state_dir / WORK_BOARD_ADOPTION_STATE_FILE).stat().st_mode
            & 0o077
            == 0,
            "Q33_WORK_BOARD_STATE_MODE_FAILED",
        )
        leases = AuthorityLeaseStore(
            restarted.state_dir / "authority"
        ).list_leases(active_only=True)
        _require(bool(leases), "Q33_WORK_BOARD_AUTHORITY_LEASE_MISSING")
        for receipt in (
            created,
            updated,
            moved,
            archived,
            recovered,
            undone,
            final_recover,
            restore_receipt,
        ):
            _require(bool(receipt.approval_ref), "Q33_WORK_BOARD_APPROVAL_MISSING")
            _require(bool(receipt.authority_lease_ref), "Q33_WORK_BOARD_LEASE_MISSING")
            _require(not receipt.task_execution_performed, "Q33_TASK_EXECUTION_OCCURRED")
            _require(not receipt.connector_write_performed, "Q33_CONNECTOR_WRITE_OCCURRED")
            _require(
                not receipt.provider_model_call_performed,
                "Q33_PROVIDER_MODEL_CALL_OCCURRED",
            )

        cli_output = io.StringIO()
        with contextlib.redirect_stdout(cli_output):
            cli_exit = work_board_cli_main(
                ["inspect-adoption", "--state-dir", str(restarted.state_dir)]
            )
        _require(cli_exit == 0, "Q33_WORK_BOARD_CLI_FAILED")
        cli_text = cli_output.getvalue()
        _require(
            not any(marker in cli_text for marker in PRIVATE_MARKERS),
            "Q33_WORK_BOARD_CLI_PRIVATE_LEAK",
        )
        _require(
            json.loads(cli_text)["private_values_included"] is False,
            "Q33_WORK_BOARD_CLI_SAFE_DEFAULT_FAILED",
        )

        return {
            "schema_version": "queue-v2-q33-work-board-adoption-verification.v1",
            "contract_ref": WORK_BOARD_ADOPTION_CONTRACT_REF,
            "status": "verified",
            "create_update_move_archive_recover_undo_verified": True,
            "restart_and_readable_state_verified": True,
            "encrypted_backup_restore_recovery_verified": True,
            "exact_restore_replay_verified": True,
            "exact_local_approval_and_authority_lease_verified": True,
            "cli_private_values_default_omitted": True,
            "task_execution_performed": False,
            "connector_write_performed": False,
            "provider_model_call_performed": False,
            "browser_or_shell_execution_performed": False,
            "public_or_production_claim": False,
        }


def main() -> int:
    try:
        result = verify()
    except (WorkBoardAdoptionError, RuntimeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": (
                        "queue-v2-q33-work-board-adoption-verification.v1"
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
