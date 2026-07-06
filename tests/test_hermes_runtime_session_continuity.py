import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_SESSION_CONTINUITY_BLOCKED_AUTHORITY_REFS,
    RUNTIME_SESSION_CONTINUITY_CONTRACT_REF,
    RuntimeSessionContinuityReadModel,
    RuntimeSessionContinuitySurface,
    build_runtime_session_continuity_read_model,
)


client = TestClient(app)


def test_session_continuity_is_safe_ref_read_only_posture() -> None:
    read_model = build_runtime_session_continuity_read_model()

    assert read_model.schema_version == "runtime_session_continuity.v1"
    assert read_model.contract_ref == RUNTIME_SESSION_CONTINUITY_CONTRACT_REF
    assert read_model.status == "read_only_multi_surface_session_continuity_posture"
    assert read_model.route_ref == "GET /api/runtime/session-continuity"
    assert read_model.cli_ref == "uaa runtime inspect-session-continuity"
    assert read_model.surface_count == 5
    assert read_model.current_count == 2
    assert read_model.stale_count == 1
    assert read_model.conflict_count == 1
    assert read_model.blocked_count == 1
    assert read_model.source_labels_visible is True
    assert read_model.staleness_states_visible is True
    assert read_model.conflict_states_visible is True
    assert read_model.delivery_receipts_required_for_promotion is True
    assert read_model.revoke_required_for_promotion is True
    assert read_model.audit_required_for_promotion is True
    assert read_model.external_message_gateway_enabled is False
    assert read_model.account_sync_enabled is False
    assert read_model.connector_write_enabled is False
    assert read_model.remote_session_enabled is False
    assert read_model.raw_transcript_persisted is False
    assert read_model.raw_prompt_persisted is False
    assert read_model.raw_response_persisted is False
    assert read_model.raw_provider_payload_persisted is False
    assert read_model.control_center_mints_authority is False
    assert set(RUNTIME_SESSION_CONTINUITY_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


def test_session_continuity_surfaces_keep_states_and_blocked_authority_visible() -> None:
    read_model = build_runtime_session_continuity_read_model()

    states_by_source = {
        surface.source: surface.continuity_state for surface in read_model.surfaces
    }
    assert states_by_source == {
        "control_center_desktop": "current",
        "cli": "current",
        "delegated_runtime": "stale",
        "coding_cockpit": "conflict_review",
        "future_mobile": "blocked",
    }
    for surface in read_model.surfaces:
        assert surface.source_label
        assert surface.staleness_state_ref.startswith(
            "staleness-state-ref:session-continuity:"
        )
        assert surface.conflict_state_ref.startswith(
            "conflict-state-ref:session-continuity:"
        )
        assert surface.external_message_gateway_enabled is False
        assert surface.account_sync_enabled is False
        assert surface.connector_write_enabled is False
        assert surface.remote_session_enabled is False
        assert surface.raw_transcript_persisted is False
        assert surface.raw_prompt_persisted is False
        assert surface.raw_response_persisted is False
        assert surface.raw_provider_payload_persisted is False
        assert surface.control_center_mints_authority is False
        assert set(RUNTIME_SESSION_CONTINUITY_BLOCKED_AUTHORITY_REFS).issubset(
            set(surface.blocked_authority_refs)
        )


@pytest.mark.parametrize(
    "field",
    [
        "external_message_gateway_enabled",
        "account_sync_enabled",
        "connector_write_enabled",
        "remote_session_enabled",
        "raw_transcript_persisted",
        "raw_prompt_persisted",
        "raw_response_persisted",
        "raw_provider_payload_persisted",
        "control_center_mints_authority",
    ],
)
def test_session_continuity_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_session_continuity_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_SESSION_CONTINUITY_AUTHORITY_DENIED"):
        RuntimeSessionContinuityReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "external_message_gateway_enabled",
        "account_sync_enabled",
        "connector_write_enabled",
        "remote_session_enabled",
        "raw_transcript_persisted",
        "raw_prompt_persisted",
        "raw_response_persisted",
        "raw_provider_payload_persisted",
        "control_center_mints_authority",
    ],
)
def test_session_continuity_surface_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_session_continuity_read_model()
        .surfaces[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_SESSION_CONTINUITY_AUTHORITY_DENIED"):
        RuntimeSessionContinuitySurface(**payload)


def test_session_continuity_api_returns_safe_read_model() -> None:
    response = client.get("/api/runtime/session-continuity")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_session_continuity"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/session-continuity"
    assert data["external_message_gateway_enabled"] is False
    assert data["account_sync_enabled"] is False
    assert data["connector_write_enabled"] is False
    assert data["remote_session_enabled"] is False
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "raw_prompt_value" not in serialized
    assert "provider_payload_value" not in serialized


def test_session_continuity_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-session-continuity",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_session_continuity"]
    assert payload["safe_refs_only"] is True
    assert payload["external_message_gateway_performed"] is False
    assert payload["account_sync_performed"] is False
    assert payload["connector_write_performed"] is False
    assert payload["remote_session_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/session-continuity"
    assert read_model["cli_ref"] == "uaa runtime inspect-session-continuity"
    assert read_model["surface_count"] == 5
