from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.control_center import (
    CALENDAR_ADOPTION_MAX_REQUEST_BODY_BYTES,
    CALENDAR_ADOPTION_MAX_REQUEST_NESTING_DEPTH,
)
from ultimate_ai_agent.core.control_center.calendar_adoption import (
    CALENDAR_ADOPTION_DATABASE_FILE,
    CalendarAdoptionApprovalCaptureRequest,
    CalendarAdoptionCalendarDraft,
    CalendarAdoptionCommitRequest,
    CalendarAdoptionMutationRequest,
    CalendarAdoptionPortableBackupRequest,
    CalendarAdoptionStore,
)
from ultimate_ai_agent.core.ecosystem.calendar import CalendarConflict
from ultimate_ai_agent.core.ecosystem.local_data import EcosystemKeyUnavailable


def _headers(suffix: str, *, confirmed: bool = False) -> dict[str, str]:
    result = {"X-UAA-Idempotency-Key": f"idempotency-ref:calendar-api:{suffix}"}
    if confirmed:
        result["X-UAA-Operator-Confirmed"] = "true"
    return result


def _initialize_mutation() -> dict[str, object]:
    return {
        "action": "initialize",
        "expected_revision": 0,
        "target_ref": None,
        "event": None,
        "calendar": {
            "calendar_ref": "calendar-ref:q33:primary",
            "name": "Personal",
            "timezone": "America/Los_Angeles",
            "color_ref": "color-ref:q33:primary",
        },
    }


def test_calendar_adoption_api_completes_exact_local_loop(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("UAA_CALENDAR_STATE_DIR", str(tmp_path / "calendar"))
    client = TestClient(app)

    empty = client.get(
        "/control-center/calendar/adoption",
        params={
            "view": "week",
            "anchor": "2026-09-14T16:00:00Z",
            "timezone": "America/Los_Angeles",
        },
    )
    assert empty.status_code == 200
    assert empty.headers["Cache-Control"] == "no-store"
    assert empty.json()["data"]["status"] == "onboarding"

    mutation = _initialize_mutation()
    headers = _headers("initialize")
    preview_response = client.post(
        "/control-center/calendar/adoption/preview", json=mutation, headers=headers
    )
    assert preview_response.status_code == 200
    preview = preview_response.json()["data"]
    scope = {
        "mutation": mutation,
        "preview_ref": preview["preview_ref"],
        "approval_ref": preview["approval_ref"],
    }

    missing_confirmation = client.post(
        "/control-center/calendar/adoption/approval", json=scope, headers=headers
    )
    assert missing_confirmation.status_code == 403

    confirmed = _headers("initialize", confirmed=True)
    approval = client.post(
        "/control-center/calendar/adoption/approval", json=scope, headers=confirmed
    )
    assert approval.status_code == 200
    committed = client.post(
        "/control-center/calendar/adoption/commit", json=scope, headers=confirmed
    )
    assert committed.status_code == 200
    receipt = committed.json()["data"]
    assert receipt["after_revision"] == 1
    assert receipt["external_calendar_write_performed"] is False
    assert receipt["provider_model_call_performed"] is False

    replay = client.post(
        "/control-center/calendar/adoption/commit", json=scope, headers=confirmed
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["replayed"] is True

    populated = client.get(
        "/control-center/calendar/adoption",
        params={"timezone": "America/Los_Angeles"},
    )
    assert populated.status_code == 200
    assert populated.json()["data"]["calendars"][0]["name"] == "Personal"


def test_calendar_adoption_api_rejects_timezone_naive_anchor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    state_dir = tmp_path / "calendar"
    monkeypatch.setenv("UAA_CALENDAR_STATE_DIR", str(state_dir))

    response = TestClient(app).get(
        "/control-center/calendar/adoption",
        params={"anchor": "2026-09-14T16:00:00", "timezone": "UTC"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == (
        "CALENDAR_ADOPTION_ANCHOR_TIMEZONE_REQUIRED"
    )
    assert not state_dir.exists()


def test_calendar_adoption_api_rejects_extreme_agenda_anchor_without_state_access(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    state_dir = tmp_path / "calendar"
    monkeypatch.setenv("UAA_CALENDAR_STATE_DIR", str(state_dir))

    response = TestClient(app).get(
        "/control-center/calendar/adoption",
        params={"view": "agenda", "anchor": "9999-12-31T12:00:00Z", "timezone": "UTC"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == (
        "CALENDAR_ADOPTION_ANCHOR_OUT_OF_RANGE"
    )
    assert not state_dir.exists()


def test_calendar_adoption_api_rejects_extreme_month_anchor_without_state_access(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    state_dir = tmp_path / "calendar"
    monkeypatch.setenv("UAA_CALENDAR_STATE_DIR", str(state_dir))

    response = TestClient(app).get(
        "/control-center/calendar/adoption",
        params={
            "view": "month",
            "anchor": "9999-12-15T12:00:00Z",
            "timezone": "UTC",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == (
        "CALENDAR_ADOPTION_ANCHOR_OUT_OF_RANGE"
    )
    assert not state_dir.exists()


def test_calendar_adoption_api_returns_recovery_for_corrupt_database(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    state_dir = tmp_path / "calendar"
    state_dir.mkdir()
    (state_dir / CALENDAR_ADOPTION_DATABASE_FILE).write_bytes(b"not sqlite")
    monkeypatch.setenv("UAA_CALENDAR_STATE_DIR", str(state_dir))

    response = TestClient(app).get(
        "/control-center/calendar/adoption",
        params={"anchor": "2026-09-14T16:00:00Z", "timezone": "UTC"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "recovery_required"


@pytest.mark.parametrize("failure_mode", ["database", "key"])
def test_calendar_adoption_preview_translates_damaged_local_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure_mode: str,
) -> None:
    state_dir = tmp_path / "calendar"
    state_dir.mkdir()
    (state_dir / CALENDAR_ADOPTION_DATABASE_FILE).write_bytes(b"not sqlite")
    monkeypatch.setenv("UAA_CALENDAR_STATE_DIR", str(state_dir))
    if failure_mode == "key":

        def unavailable_repository(_store: CalendarAdoptionStore):
            raise EcosystemKeyUnavailable("ECO_KEY_NOT_FOUND")

        monkeypatch.setattr(
            CalendarAdoptionStore,
            "_repository",
            unavailable_repository,
        )

    response = TestClient(app).post(
        "/control-center/calendar/adoption/preview",
        json=_initialize_mutation(),
        headers=_headers("damaged-preview"),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == (
        "CALENDAR_ADOPTION_CURRENT_STATE_UNREADABLE"
    )


def test_calendar_restore_api_recovers_corrupt_database_after_exact_approval(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = CalendarAdoptionStore(tmp_path / "source")
    mutation = CalendarAdoptionMutationRequest(
        action="initialize",
        expected_revision=0,
        calendar=CalendarAdoptionCalendarDraft(
            calendar_ref="calendar-ref:q33:restore-api-source",
            name="Personal",
            timezone="America/Los_Angeles",
            color_ref="color-ref:q33:restore-api-source",
        ),
    )
    idempotency_ref = "idempotency-ref:calendar-api:restore-corrupt-source"
    preview = source.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    capture = CalendarAdoptionApprovalCaptureRequest(
        mutation=mutation,
        preview_ref=preview.preview_ref,
        approval_ref=preview.approval_ref,
    )
    source.capture_approval(capture, idempotency_ref=idempotency_ref)
    source.commit_mutation(
        CalendarAdoptionCommitRequest(**capture.model_dump(mode="python")),
        idempotency_ref=idempotency_ref,
    )
    passphrase = "founder private corrupt restore api"
    backup = source.create_portable_backup(
        CalendarAdoptionPortableBackupRequest(passphrase=passphrase)
    )
    state_dir = tmp_path / "target"
    state_dir.mkdir()
    (state_dir / CALENDAR_ADOPTION_DATABASE_FILE).write_bytes(b"not sqlite")
    monkeypatch.setenv("UAA_CALENDAR_STATE_DIR", str(state_dir))

    client = TestClient(app)
    idempotency_suffix = "restore-corrupt-target"
    response = client.post(
        "/control-center/calendar/adoption/restore-preview",
        json={"passphrase": passphrase, "backup": backup.model_dump(mode="json")},
        headers=_headers(idempotency_suffix),
    )
    assert response.status_code == 200
    preview_data = response.json()["data"]
    assert preview_data["impact_status"] == "unknown_current_state"
    assert preview_data["rollback_available"] is False
    scope = {
        "passphrase": passphrase,
        "backup": backup.model_dump(mode="json"),
        "preview_ref": preview_data["preview_ref"],
        "approval_ref": preview_data["approval_ref"],
    }
    approval = client.post(
        "/control-center/calendar/adoption/restore-approval",
        json=scope,
        headers=_headers(idempotency_suffix, confirmed=True),
    )
    assert approval.status_code == 200
    restored = client.post(
        "/control-center/calendar/adoption/restore-commit",
        json=scope,
        headers=_headers(idempotency_suffix, confirmed=True),
    )
    assert restored.status_code == 200
    assert restored.json()["data"]["after_revision"] == 1
    workspace = client.get(
        "/control-center/calendar/adoption",
        params={"anchor": "2026-09-14T16:00:00Z", "timezone": "UTC"},
    )
    assert workspace.status_code == 200
    assert workspace.json()["data"]["status"] == "ready"


def test_calendar_restore_api_blocks_malformed_live_key_recovery(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = CalendarAdoptionStore(tmp_path / "source")
    source_mutation = CalendarAdoptionMutationRequest(
        action="initialize",
        expected_revision=0,
        calendar=CalendarAdoptionCalendarDraft(
            calendar_ref="calendar-ref:q33:malformed-key-source",
            name="Personal",
            timezone="UTC",
            color_ref="color-ref:q33:malformed-key-source",
        ),
    )
    source_idempotency_ref = "idempotency-ref:calendar-api:malformed-key-source"
    source_preview = source.preview_mutation(
        source_mutation, idempotency_ref=source_idempotency_ref
    )
    source_capture = CalendarAdoptionApprovalCaptureRequest(
        mutation=source_mutation,
        preview_ref=source_preview.preview_ref,
        approval_ref=source_preview.approval_ref,
    )
    source.capture_approval(
        source_capture, idempotency_ref=source_idempotency_ref
    )
    source.commit_mutation(
        CalendarAdoptionCommitRequest(**source_capture.model_dump(mode="python")),
        idempotency_ref=source_idempotency_ref,
    )
    passphrase = "founder private malformed key recovery"
    backup = source.create_portable_backup(
        CalendarAdoptionPortableBackupRequest(passphrase=passphrase)
    )

    target_dir = tmp_path / "target"
    target = CalendarAdoptionStore(target_dir)
    target_mutation = CalendarAdoptionMutationRequest(
        action="initialize",
        expected_revision=0,
        calendar=CalendarAdoptionCalendarDraft(
            calendar_ref="calendar-ref:q33:malformed-key-target",
            name="Local",
            timezone="UTC",
            color_ref="color-ref:q33:malformed-key-target",
        ),
    )
    target_idempotency_ref = "idempotency-ref:calendar-api:malformed-key-target"
    target_preview = target.preview_mutation(
        target_mutation, idempotency_ref=target_idempotency_ref
    )
    target_capture = CalendarAdoptionApprovalCaptureRequest(
        mutation=target_mutation,
        preview_ref=target_preview.preview_ref,
        approval_ref=target_preview.approval_ref,
    )
    target.capture_approval(
        target_capture, idempotency_ref=target_idempotency_ref
    )
    target.commit_mutation(
        CalendarAdoptionCommitRequest(**target_capture.model_dump(mode="python")),
        idempotency_ref=target_idempotency_ref,
    )
    key_files = list((target_dir / "keys").glob("*.key"))
    assert len(key_files) == 1
    key_files[0].write_bytes(b"malformed")
    monkeypatch.setenv("UAA_CALENDAR_STATE_DIR", str(target_dir))

    response = TestClient(app).post(
        "/control-center/calendar/adoption/restore-preview",
        json={"passphrase": passphrase, "backup": backup.model_dump(mode="json")},
        headers=_headers("malformed-live-key"),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == (
        "CALENDAR_ADOPTION_KEY_RECOVERY_UNAVAILABLE"
    )


def test_calendar_adoption_api_enforces_body_and_structure_bounds(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("UAA_CALENDAR_STATE_DIR", str(tmp_path / "calendar"))
    client = TestClient(app)
    origin = "http://127.0.0.1:5173"
    oversized = client.post(
        "/control-center/calendar/adoption/preview",
        content=b"{}",
        headers={
            "content-type": "application/json",
            "content-length": str(CALENDAR_ADOPTION_MAX_REQUEST_BODY_BYTES + 1),
            "Origin": origin,
            **_headers("oversize"),
        },
    )
    assert oversized.status_code == 413
    assert oversized.headers["Cache-Control"] == "no-store"
    assert oversized.headers["Access-Control-Allow-Origin"] == origin
    assert oversized.json()["code"] == "CALENDAR_ADOPTION_REQUEST_BODY_LIMIT_EXCEEDED"

    nested = b"[" * (CALENDAR_ADOPTION_MAX_REQUEST_NESTING_DEPTH + 1)
    nested += b"]" * (CALENDAR_ADOPTION_MAX_REQUEST_NESTING_DEPTH + 1)
    for route in (
        "/control-center/calendar/adoption/preview",
        "/control-center/calendar/adoption/approval",
        "/control-center/calendar/adoption/commit",
        "/control-center/calendar/adoption/backup",
        "/control-center/calendar/adoption/restore-preview",
        "/control-center/calendar/adoption/restore-approval",
        "/control-center/calendar/adoption/restore-commit",
    ):
        response = client.post(
            route,
            content=nested,
            headers={"content-type": "application/json", **_headers("nested")},
        )
        assert response.status_code == 413, route


def test_calendar_body_limit_is_published_for_every_json_route() -> None:
    paths = app.openapi()["paths"]
    for route in (
        "/control-center/calendar/adoption/preview",
        "/control-center/calendar/adoption/approval",
        "/control-center/calendar/adoption/commit",
        "/control-center/calendar/adoption/backup",
        "/control-center/calendar/adoption/restore-preview",
        "/control-center/calendar/adoption/restore-approval",
        "/control-center/calendar/adoption/restore-commit",
    ):
        schema = paths[route]["post"]["responses"]["413"]["content"][
            "application/json"
        ]["schema"]
        assert schema["$ref"].endswith("/CalendarAdoptionBodyLimitResponse")


@pytest.mark.parametrize(
    ("headers", "expected_code"),
    [
        (
            {
                "X-UAA-Idempotency-Key": "idempotency-ref:calendar-api:first",
                "X-UAA-Idempotency-Ref": "idempotency-ref:calendar-api:second",
            },
            "API_IDEMPOTENCY_CONFLICT",
        ),
        ({"X-UAA-Idempotency-Key": "invalid!"}, "API_IDEMPOTENCY_INVALID"),
    ],
)
def test_calendar_adoption_api_rejects_bad_idempotency(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    headers: dict[str, str],
    expected_code: str,
) -> None:
    state_dir = tmp_path / "calendar"
    monkeypatch.setenv("UAA_CALENDAR_STATE_DIR", str(state_dir))
    response = TestClient(app).post(
        "/control-center/calendar/adoption/preview",
        json=_initialize_mutation(),
        headers=headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == expected_code
    assert not state_dir.exists()


def test_calendar_adoption_api_translates_canonical_repository_conflicts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("UAA_CALENDAR_STATE_DIR", str(tmp_path / "calendar"))

    def raise_canonical_conflict(*_args, **_kwargs):
        raise CalendarConflict("ECO_CALENDAR_EVENT_CALENDAR_NOT_FOUND")

    monkeypatch.setattr(
        CalendarAdoptionStore,
        "preview_mutation",
        raise_canonical_conflict,
    )
    response = TestClient(app).post(
        "/control-center/calendar/adoption/preview",
        json=_initialize_mutation(),
        headers=_headers("canonical-conflict"),
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == (
        "ECO_CALENDAR_EVENT_CALENDAR_NOT_FOUND"
    )
