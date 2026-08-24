from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from ultimate_ai_agent.api import communications as communications_api
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.local_auth import (
    LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV,
    LOCAL_API_BEARER_ENV,
)
from ultimate_ai_agent.core.communications import (
    COMMUNICATIONS_PROJECTION_STATE_DIR_ENV,
    CommunicationsProjectionInvalid,
    CommunicationsProjectionNotFound,
    ReviewedCommunicationsProjectionStore,
    ReviewedCommunicationsSnapshot,
    build_default_communications_service,
)


LOCAL_TEST_BEARER = "communications-projection-local-bearer"


def _snapshot_payload() -> dict[str, object]:
    return {
        "schema_version": "uaa-communications-reviewed-projection.v1",
        "snapshot_ref": "snapshot-ref:communications:reviewed-alpha",
        "source": {
            "source_ref": "source-ref:communications:reviewed-manual-import",
            "source_kind": "reviewed_manual_import",
            "schema_version": "uaa-communications-reviewed-projection.v1",
            "observed_at": "2026-08-24T18:00:00Z",
            "freshness": "current",
            "coverage_ref": "coverage-ref:communications:bounded-local-review",
            "retention_ref": "retention-ref:communications:operator-managed",
            "privacy_ref": "privacy-ref:communications:redacted-summary-only",
            "evidence_refs": ["evidence-ref:communications:reviewed-import-alpha"],
            "connector_configured": False,
            "live_sync_enabled": False,
            "external_actions_enabled": False,
            "raw_content_persisted": False,
        },
        "threads": [
            {
                "conversation_ref": "conversation-ref:communications:alpha",
                "channel_ref": "channel-ref:communications:social-review",
                "participant_refs": ["participant-ref:communications:reviewer-alpha"],
                "item_refs": ["item-ref:communications:alpha-1"],
                "latest_activity_at": "2026-08-24T17:55:00Z",
                "needs_attention": True,
                "safe_label": "Reviewed social signal",
                "safe_summary": "A reviewed redacted signal requires operator attention.",
                "evidence_refs": ["evidence-ref:communications:thread-alpha"],
            }
        ],
        "items": [
            {
                "item_ref": "item-ref:communications:alpha-1",
                "conversation_ref": "conversation-ref:communications:alpha",
                "sender_ref": "sender-ref:communications:reviewed-source-alpha",
                "item_kind": "message",
                "occurred_at": "2026-08-24T17:55:00Z",
                "safe_summary": "Reviewed redacted signal summary.",
                "content_fingerprint_ref": "fingerprint-ref:communications:alpha-1",
                "relation_ref": None,
                "evidence_refs": ["evidence-ref:communications:item-alpha-1"],
                "content_untrusted": True,
                "not_instruction_authority": True,
                "reviewed_redacted_summary_only": True,
                "raw_content_omitted": True,
            }
        ],
        "raw_content_persisted": False,
    }


def _write_snapshot(state_dir: Path, payload: dict[str, object] | None = None) -> None:
    state_dir.mkdir()
    (state_dir / "reviewed_projection.json").write_text(
        json.dumps(payload or _snapshot_payload()),
        encoding="utf-8",
    )


def test_reviewed_projection_is_strict_linked_bounded_and_read_only(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "projection"
    _write_snapshot(state_dir)
    store = ReviewedCommunicationsProjectionStore(state_dir)

    page = store.list_threads(limit=25, needs_attention=True)
    detail = store.get_thread("conversation-ref:communications:alpha")

    assert page.status.value == "ready"
    assert page.pagination.returned_count == 1
    assert page.items[0].safe_label == "Reviewed social signal"
    assert page.read_only is True
    assert page.send_enabled is False
    assert page.reply_enabled is False
    assert page.delete_enabled is False
    assert page.moderate_enabled is False
    assert page.raw_content_omitted is True
    assert detail.items[0].content_untrusted is True
    assert detail.items[0].reviewed_redacted_summary_only is True
    assert detail.items[0].raw_content_omitted is True
    assert detail.source.connector_configured is False
    assert detail.source.live_sync_enabled is False
    assert detail.source.external_actions_enabled is False


def test_reviewed_projection_missing_invalid_and_unknown_refs_fail_closed(
    tmp_path: Path,
) -> None:
    missing = ReviewedCommunicationsProjectionStore(tmp_path / "missing")
    page = missing.list_threads()
    assert page.status.value == "blocked"
    assert page.items == []
    assert page.source is None

    with pytest.raises(
        CommunicationsProjectionNotFound, match="COMMUNICATIONS_PROJECTION_NOT_FOUND"
    ):
        missing.get_thread("conversation-ref:communications:missing")

    invalid_dir = tmp_path / "invalid"
    payload = _snapshot_payload()
    payload["threads"][0]["item_refs"] = ["item-ref:communications:missing"]  # type: ignore[index]
    _write_snapshot(invalid_dir, payload)
    with pytest.raises(
        CommunicationsProjectionInvalid, match="COMMUNICATIONS_PROJECTION_INVALID"
    ):
        ReviewedCommunicationsProjectionStore(invalid_dir).list_threads()

    with pytest.raises(CommunicationsProjectionNotFound):
        missing.get_thread("not-a-safe-ref")


def test_reviewed_projection_rejects_symlink_and_authority_or_raw_content(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    _write_snapshot(source_dir)
    linked_dir = tmp_path / "linked"
    linked_dir.mkdir()
    (linked_dir / "reviewed_projection.json").symlink_to(
        source_dir / "reviewed_projection.json"
    )
    with pytest.raises(
        CommunicationsProjectionInvalid,
        match="COMMUNICATIONS_PROJECTION_FILE_NOT_REGULAR",
    ):
        ReviewedCommunicationsProjectionStore(linked_dir).load_snapshot()

    linked_state_dir = tmp_path / "linked-state-dir"
    linked_state_dir.symlink_to(source_dir, target_is_directory=True)
    with pytest.raises(
        CommunicationsProjectionInvalid,
        match="COMMUNICATIONS_PROJECTION_DIRECTORY_NOT_REAL",
    ):
        ReviewedCommunicationsProjectionStore(linked_state_dir).load_snapshot()

    payload = _snapshot_payload()
    payload["source"]["external_actions_enabled"] = True  # type: ignore[index]
    with pytest.raises(ValidationError):
        ReviewedCommunicationsSnapshot.model_validate(payload)

    payload = _snapshot_payload()
    payload["items"][0]["raw_message_body"] = "content must not be accepted"  # type: ignore[index]
    with pytest.raises(ValidationError) as exc_info:
        ReviewedCommunicationsSnapshot.model_validate(payload)
    assert "content must not be accepted" not in str(exc_info.value)


def test_reviewed_projection_api_and_cli_share_python_core_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = tmp_path / "projection"
    _write_snapshot(state_dir)
    monkeypatch.setenv(COMMUNICATIONS_PROJECTION_STATE_DIR_ENV, str(state_dir))
    monkeypatch.delenv(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV, raising=False)
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_TEST_BEARER)
    monkeypatch.setattr(
        communications_api,
        "_SERVICE",
        build_default_communications_service(),
    )

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {LOCAL_TEST_BEARER}"}
    response = client.get(
        "/control-center/communications/conversations?needs_attention=true",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["data"]["items"][0]["conversation_ref"] == (
        "conversation-ref:communications:alpha"
    )
    assert response.json()["data"]["send_enabled"] is False

    detail = client.get(
        "/control-center/communications/conversations/conversation-ref:communications:alpha",
        headers=headers,
    )
    assert detail.status_code == 200
    assert detail.json()["data"]["items"][0]["safe_summary"] == (
        "Reviewed redacted signal summary."
    )

    env = dict(os.environ)
    env[COMMUNICATIONS_PROJECTION_STATE_DIR_ENV] = str(state_dir)
    env.pop("PYTHONPATH", None)
    cli = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_communications.py",
            "conversations",
            "--needs-attention",
            "--json",
        ],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    payload = json.loads(cli.stdout)
    assert payload == response.json()["data"]
