from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.dev.uaa_calendar import main
from ultimate_ai_agent.core.control_center.calendar_adoption import (
    CalendarAdoptionApprovalCaptureRequest,
    CalendarAdoptionCalendarDraft,
    CalendarAdoptionCommitRequest,
    CalendarAdoptionEventDraft,
    CalendarAdoptionMutationRequest,
    CalendarAdoptionStore,
)


def _commit(
    store: CalendarAdoptionStore,
    mutation: CalendarAdoptionMutationRequest,
    idempotency_ref: str,
) -> None:
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    request = CalendarAdoptionApprovalCaptureRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    store.capture_approval(request, idempotency_ref=idempotency_ref)
    store.commit_mutation(
        CalendarAdoptionCommitRequest(**request.model_dump()),
        idempotency_ref=idempotency_ref,
    )


def _seed(state_dir: Path) -> None:
    store = CalendarAdoptionStore(state_dir)
    _commit(
        store,
        CalendarAdoptionMutationRequest(
            action="initialize",
            expected_revision=0,
            calendar=CalendarAdoptionCalendarDraft(
                calendar_ref="calendar-ref:q33:cli",
                name="Private founder calendar",
                timezone="UTC",
            ),
        ),
        "idempotency-ref:q33-calendar-cli:initialize",
    )
    start = datetime(2026, 9, 14, 16, tzinfo=timezone.utc)
    _commit(
        store,
        CalendarAdoptionMutationRequest(
            action="create_event",
            expected_revision=1,
            event=CalendarAdoptionEventDraft(
                event_ref="calendar-event-ref:q33:cli-private",
                calendar_ref="calendar-ref:q33:cli",
                title="Private founder acquisition meeting",
                starts_at=start,
                ends_at=start + timedelta(hours=1),
                timezone="UTC",
            ),
        ),
        "idempotency-ref:q33-calendar-cli:create",
    )


def test_calendar_cli_omits_private_values_by_default(tmp_path: Path, capsys) -> None:
    _seed(tmp_path)
    assert (
        main(
            [
                "inspect-adoption",
                "--state-dir",
                str(tmp_path),
                "--anchor",
                "2026-09-14T16:00:00+00:00",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload["status"] == "ready"
    assert payload["occurrence_count"] == 1
    assert payload["private_values_included"] is False
    assert "Private founder acquisition meeting" not in json.dumps(payload)


def test_calendar_cli_private_view_is_explicit(tmp_path: Path, capsys) -> None:
    _seed(tmp_path)
    assert (
        main(
            [
                "inspect-adoption",
                "--state-dir",
                str(tmp_path),
                "--anchor",
                "2026-09-14T16:00:00+00:00",
                "--include-private",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload["private_values_included"] is True
    assert payload["occurrence_items"][0]["event"]["title"] == (
        "Private founder acquisition meeting"
    )
