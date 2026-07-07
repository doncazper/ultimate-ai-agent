import subprocess
import sys

from fastapi.testclient import TestClient
import pytest

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_VOICE_MEDIA_POSTURE_AUTHORITY_MAPPING_REF,
    RUNTIME_VOICE_MEDIA_POSTURE_BLOCKED_AUTHORITY_REFS,
    RUNTIME_VOICE_MEDIA_POSTURE_ROUTE_REF,
    RuntimeVoiceMediaLane,
    RuntimeVoiceMediaPostureReadModel,
    build_runtime_voice_media_posture_read_model,
)


client = TestClient(app)


def test_voice_media_posture_is_blocked_read_model_only() -> None:
    read_model = build_runtime_voice_media_posture_read_model()

    assert read_model.schema_version == "runtime_voice_media_posture.v1"
    assert read_model.status == "read_model_posture_only"
    assert read_model.route_ref == RUNTIME_VOICE_MEDIA_POSTURE_ROUTE_REF
    assert read_model.cli_ref == "uaa runtime inspect-voice-media-posture"
    assert (
        read_model.authority_state_mapping_ref
        == RUNTIME_VOICE_MEDIA_POSTURE_AUTHORITY_MAPPING_REF
    )
    assert read_model.authority_state_route_ref == "GET /api/runtime/authority-state"
    assert (
        read_model.authority_state_cli_ref
        == "repo-local-command:uaa-runtime-inspect-authority-state"
    )
    assert read_model.authority_state_decision_outcome == "allow"
    assert read_model.authority_state_status == "implemented_authority_bound_read_model"
    assert "reason-ref:authority:active-lease-grants-domain-capability" in (
        read_model.authority_state_reason_refs
    )
    assert "adapter-ref:voice-media-microphone:not-implemented" in (
        read_model.unsupported_adapter_refs
    )
    assert read_model.lane_count == 7
    assert read_model.blocked_lane_count == 7
    assert read_model.microphone_access_enabled is False
    assert read_model.camera_access_enabled is False
    assert read_model.file_upload_enabled is False
    assert read_model.transcription_enabled is False
    assert read_model.media_generation_enabled is False
    assert read_model.provider_calls_enabled is False
    assert read_model.external_delivery_enabled is False
    assert read_model.raw_media_persisted is False
    assert read_model.control_center_mints_authority is False
    assert set(RUNTIME_VOICE_MEDIA_POSTURE_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


def test_voice_media_posture_route_returns_authority_bound_read_model() -> None:
    response = client.get("/api/runtime/voice-media-posture")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_voice_media_posture"
    data = body["data"]
    assert data["schema_version"] == "runtime_voice_media_posture.v1"
    assert data["route_ref"] == "GET /api/runtime/voice-media-posture"
    assert (
        data["authority_state_mapping_ref"]
        == "lane-ref:runtime-voice-media-posture-read-model"
    )
    assert data["authority_state_decision_outcome"] == "allow"
    assert data["lane_count"] == 7
    assert data["blocked_lane_count"] == 7
    assert data["microphone_access_enabled"] is False
    assert data["media_generation_enabled"] is False
    assert data["provider_calls_enabled"] is False


def test_voice_media_lanes_require_promotion_controls() -> None:
    read_model = build_runtime_voice_media_posture_read_model()
    lane_kinds = {lane.lane_kind for lane in read_model.lanes}

    assert lane_kinds == {
        "voice_input",
        "speech_to_text",
        "text_to_speech",
        "image_input",
        "image_generation",
        "media_upload",
        "media_delivery",
    }
    for lane in read_model.lanes:
        assert lane.status == "blocked_until_authority"
        assert lane.lane_ref.startswith("voice-media-lane-ref:")
        assert lane.device_permission_ref.startswith("device-permission-ref:")
        assert lane.consent_ref.startswith("consent-ref:")
        assert lane.redaction_policy_ref.startswith("redaction-policy-ref:")
        assert lane.receipt_plan_ref.startswith("receipt-plan-ref:")
        assert lane.safe_disable_ref.startswith("safe-disable-ref:")
        assert lane.local_only_option_required is True
        assert lane.provider_boundary_required is True
        assert lane.consent_required is True
        assert lane.receipt_required is True
        assert lane.safe_disable_required is True
        assert lane.microphone_access_enabled is False
        assert lane.camera_access_enabled is False
        assert lane.file_upload_enabled is False
        assert lane.transcription_enabled is False
        assert lane.media_generation_enabled is False
        assert lane.provider_calls_enabled is False
        assert lane.external_delivery_enabled is False
        assert lane.raw_media_persisted is False
        assert lane.control_center_mints_authority is False


@pytest.mark.parametrize(
    "field",
    [
        "microphone_access_enabled",
        "camera_access_enabled",
        "file_upload_enabled",
        "transcription_enabled",
        "media_generation_enabled",
        "provider_calls_enabled",
        "external_delivery_enabled",
        "raw_media_persisted",
        "control_center_mints_authority",
    ],
)
def test_voice_media_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_voice_media_posture_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(
        ValueError, match="RUNTIME_VOICE_MEDIA_READ_MODEL_AUTHORITY_DENIED"
    ):
        RuntimeVoiceMediaPostureReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "microphone_access_enabled",
        "camera_access_enabled",
        "file_upload_enabled",
        "transcription_enabled",
        "media_generation_enabled",
        "provider_calls_enabled",
        "external_delivery_enabled",
        "raw_media_persisted",
        "control_center_mints_authority",
    ],
)
def test_voice_media_lane_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_voice_media_posture_read_model().lanes[0].model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_VOICE_MEDIA_LANE_AUTHORITY_DENIED"):
        RuntimeVoiceMediaLane(**payload)


def test_voice_media_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-voice-media-posture",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "raw_media_value" not in result.stdout
    assert "provider_payload_value" not in result.stdout
    payload = __import__("json").loads(result.stdout)
    read_model = payload["runtime_voice_media_posture"]
    assert payload["microphone_access_performed"] is False
    assert payload["media_generation_performed"] is False
    assert payload["provider_call_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/voice-media-posture"
    assert (
        read_model["authority_state_mapping_ref"]
        == "lane-ref:runtime-voice-media-posture-read-model"
    )
    assert read_model["authority_state_decision_outcome"] == "allow"
    assert read_model["lane_count"] == 7
    assert read_model["blocked_lane_count"] == 7
