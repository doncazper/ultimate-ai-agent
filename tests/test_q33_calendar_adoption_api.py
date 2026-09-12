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
    CalendarAdoptionStore,
)
from ultimate_ai_agent.core.ecosystem.calendar import CalendarConflict


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
