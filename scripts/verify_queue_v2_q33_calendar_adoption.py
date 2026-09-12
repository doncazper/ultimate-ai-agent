#!/usr/bin/env python3
"""Verify the bounded Queue V2 Q33 founder-private Calendar loop."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.dev.uaa_calendar import main as calendar_cli_main  # noqa: E402
from ultimate_ai_agent.core.authority import AuthorityLeaseStore  # noqa: E402
from ultimate_ai_agent.core.control_center.calendar_adoption import (  # noqa: E402
    CALENDAR_ADOPTION_CONTRACT_REF,
    CalendarAdoptionApprovalCaptureRequest,
    CalendarAdoptionCalendarDraft,
    CalendarAdoptionCommitRequest,
    CalendarAdoptionError,
    CalendarAdoptionEventDraft,
    CalendarAdoptionMutationRequest,
    CalendarAdoptionPortableBackupRequest,
    CalendarAdoptionPortableRestoreRequest,
    CalendarAdoptionRestoreApprovalCaptureRequest,
    CalendarAdoptionRestoreCommitRequest,
    CalendarAdoptionStore,
)
from ultimate_ai_agent.core.ecosystem.calendar import CalendarView  # noqa: E402


PRIVATE_MARKERS = (
    "Q33 Synthetic Private",
    "Synthetic founder-only Calendar detail",
)


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def _commit(
    store: CalendarAdoptionStore,
    mutation: CalendarAdoptionMutationRequest,
    *,
    suffix: str,
):
    idempotency_ref = f"idempotency-ref:queue-v2-q33-calendar:{suffix}"
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    approval = store.capture_approval(
        CalendarAdoptionApprovalCaptureRequest(
            mutation=mutation,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    return store.commit_mutation(
        CalendarAdoptionCommitRequest(
            mutation=mutation,
            preview_ref=preview.preview_ref,
            approval_ref=approval.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )


def _calendar(suffix: str) -> CalendarAdoptionCalendarDraft:
    return CalendarAdoptionCalendarDraft(
        calendar_ref=f"calendar-ref:queue-v2-q33:{suffix}",
        name=f"Q33 Synthetic Private {suffix.title()}",
        timezone="America/Los_Angeles",
        color_ref=f"color-ref:queue-v2-q33:{suffix}",
    )


def _event(
    suffix: str,
    *,
    calendar_ref: str,
    starts_at: datetime,
) -> CalendarAdoptionEventDraft:
    return CalendarAdoptionEventDraft(
        event_ref=f"calendar-event-ref:queue-v2-q33:{suffix}",
        calendar_ref=calendar_ref,
        title=f"Q33 Synthetic Private {suffix.title()}",
        description="Synthetic founder-only Calendar detail",
        location="Local office",
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=1),
        timezone="America/Los_Angeles",
    )


def verify() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="uaa-q33-calendar-verifier-") as directory:
        root = Path(directory)
        source = CalendarAdoptionStore(root / "source")
        _require(source.read_view().status == "onboarding", "Q33_CALENDAR_EMPTY_FAILED")

        primary = _calendar("primary")
        work = _calendar("work")
        initialized = _commit(
            source,
            CalendarAdoptionMutationRequest(
                action="initialize",
                expected_revision=0,
                calendar=primary,
            ),
            suffix="initialize",
        )
        second_calendar = _commit(
            source,
            CalendarAdoptionMutationRequest(
                action="create_calendar",
                expected_revision=1,
                calendar=work,
            ),
            suffix="create-calendar",
        )
        starts_at = datetime(2026, 9, 14, 16, tzinfo=timezone.utc)
        first_event = _event(
            "briefing",
            calendar_ref=primary.calendar_ref,
            starts_at=starts_at,
        )
        second_event = _event(
            "overlap",
            calendar_ref=work.calendar_ref,
            starts_at=starts_at + timedelta(minutes=30),
        )
        created_first = _commit(
            source,
            CalendarAdoptionMutationRequest(
                action="create_event",
                expected_revision=2,
                event=first_event,
            ),
            suffix="create-first-event",
        )
        created_second = _commit(
            source,
            CalendarAdoptionMutationRequest(
                action="create_event",
                expected_revision=3,
                event=second_event,
            ),
            suffix="create-second-event",
        )

        restarted = CalendarAdoptionStore(source.state_dir)
        for view in CalendarView:
            projected = restarted.read_view(
                view=view,
                anchor=starts_at,
                timezone_name="America/Los_Angeles",
            )
            _require(projected.status == "ready", "Q33_CALENDAR_VIEW_FAILED")
        week = restarted.read_view(
            view=CalendarView.week,
            anchor=starts_at,
            timezone_name="America/Los_Angeles",
        )
        _require(len(week.calendars) == 2, "Q33_CALENDAR_MULTI_CALENDAR_FAILED")
        _require(len(week.conflict_items) == 1, "Q33_CALENDAR_CONFLICT_FAILED")

        updated_event = first_event.model_copy(
            update={"title": "Q33 Synthetic Private Updated Briefing"}
        )
        updated = _commit(
            restarted,
            CalendarAdoptionMutationRequest(
                action="update_event",
                expected_revision=4,
                target_ref=first_event.event_ref,
                event=updated_event,
            ),
            suffix="update-event",
        )
        archived = _commit(
            restarted,
            CalendarAdoptionMutationRequest(
                action="archive_event",
                expected_revision=updated.after_revision,
                target_ref=first_event.event_ref,
            ),
            suffix="archive-event",
        )
        recovered = _commit(
            restarted,
            CalendarAdoptionMutationRequest(
                action="recover_event",
                expected_revision=archived.after_revision,
                target_ref=first_event.event_ref,
            ),
            suffix="recover-event",
        )
        undone = _commit(
            restarted,
            CalendarAdoptionMutationRequest(
                action="undo",
                expected_revision=recovered.after_revision,
            ),
            suffix="undo",
        )
        _require(
            restarted.read_view(anchor=starts_at).archived_events[0].event_ref
            == first_event.event_ref,
            "Q33_CALENDAR_UNDO_FAILED",
        )
        final_recover = _commit(
            restarted,
            CalendarAdoptionMutationRequest(
                action="recover_event",
                expected_revision=undone.after_revision,
                target_ref=first_event.event_ref,
            ),
            suffix="final-recover",
        )

        passphrase = "q33 synthetic portable calendar passphrase"
        backup = restarted.create_portable_backup(
            CalendarAdoptionPortableBackupRequest(passphrase=passphrase)
        )
        _require(
            not any(marker in backup.model_dump_json() for marker in PRIVATE_MARKERS),
            "Q33_CALENDAR_BACKUP_PLAINTEXT_LEAK",
        )
        target = CalendarAdoptionStore(root / "target")
        restore = CalendarAdoptionPortableRestoreRequest(
            passphrase=passphrase,
            backup=backup,
        )
        restore_idempotency = "idempotency-ref:queue-v2-q33-calendar:restore"
        restore_preview = target.preview_restore(
            restore,
            idempotency_ref=restore_idempotency,
        )
        restore_scope = CalendarAdoptionRestoreCommitRequest(
            **restore.model_dump(mode="python"),
            preview_ref=restore_preview.preview_ref,
            approval_ref=restore_preview.approval_ref,
        )
        target.capture_restore_approval(
            CalendarAdoptionRestoreApprovalCaptureRequest(
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
            "Q33_CALENDAR_RESTORE_REPLAY_FAILED",
        )
        _require(
            len(target.read_view(anchor=starts_at).occurrence_items) == 2,
            "Q33_CALENDAR_RESTORE_FAILED",
        )

        try:
            target.preview_restore(
                CalendarAdoptionPortableRestoreRequest(
                    passphrase="q33 incorrect portable calendar passphrase",
                    backup=backup,
                ),
                idempotency_ref="idempotency-ref:queue-v2-q33-calendar:wrong-key",
            )
        except CalendarAdoptionError as exc:
            _require(
                str(exc) == "CALENDAR_ADOPTION_BACKUP_DECRYPT_FAILED",
                "Q33_CALENDAR_WRONG_KEY_CODE_FAILED",
            )
        else:
            raise RuntimeError("Q33_CALENDAR_WRONG_KEY_FAIL_CLOSED_FAILED")

        leases = AuthorityLeaseStore(
            restarted.state_dir / "authority"
        ).list_leases(active_only=True)
        _require(bool(leases), "Q33_CALENDAR_AUTHORITY_LEASE_MISSING")
        receipts = (
            initialized,
            second_calendar,
            created_first,
            created_second,
            updated,
            archived,
            recovered,
            undone,
            final_recover,
            restore_receipt,
        )
        for receipt in receipts:
            _require(bool(receipt.approval_ref), "Q33_CALENDAR_APPROVAL_MISSING")
            _require(bool(receipt.authority_lease_ref), "Q33_CALENDAR_LEASE_MISSING")
            _require(
                not receipt.external_calendar_write_performed,
                "Q33_CALENDAR_EXTERNAL_WRITE_OCCURRED",
            )
            _require(
                not receipt.provider_model_call_performed,
                "Q33_CALENDAR_PROVIDER_MODEL_CALL_OCCURRED",
            )
            _require(
                not receipt.background_scheduling_performed,
                "Q33_CALENDAR_BACKGROUND_SCHEDULING_OCCURRED",
            )

        cli_output = io.StringIO()
        with contextlib.redirect_stdout(cli_output):
            cli_exit = calendar_cli_main(
                [
                    "inspect-adoption",
                    "--state-dir",
                    str(restarted.state_dir),
                    "--anchor",
                    starts_at.isoformat(),
                    "--timezone",
                    "America/Los_Angeles",
                ]
            )
        _require(cli_exit == 0, "Q33_CALENDAR_CLI_FAILED")
        cli_text = cli_output.getvalue()
        _require(
            not any(marker in cli_text for marker in PRIVATE_MARKERS),
            "Q33_CALENDAR_CLI_PRIVATE_LEAK",
        )
        _require(
            json.loads(cli_text)["private_values_included"] is False,
            "Q33_CALENDAR_CLI_SAFE_DEFAULT_FAILED",
        )

        return {
            "schema_version": "queue-v2-q33-calendar-adoption-verification.v1",
            "contract_ref": CALENDAR_ADOPTION_CONTRACT_REF,
            "status": "verified",
            "multiple_calendars_and_all_views_verified": True,
            "create_update_archive_recover_undo_verified": True,
            "conflict_and_restart_verified": True,
            "encrypted_backup_restore_verified": True,
            "exact_restore_replay_verified": True,
            "exact_local_approval_and_authority_lease_verified": True,
            "cli_private_values_default_omitted": True,
            "external_calendar_write_performed": False,
            "provider_model_call_performed": False,
            "background_or_notification_execution_performed": False,
            "public_or_production_claim": False,
        }


def main() -> int:
    try:
        result = verify()
    except (CalendarAdoptionError, RuntimeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": (
                        "queue-v2-q33-calendar-adoption-verification.v1"
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
