import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_MESSAGING_GATEWAY_POSTURE_AUTHORITY_MAPPING_REF,
    RUNTIME_MESSAGING_GATEWAY_BLOCKED_AUTHORITY_REFS,
    RUNTIME_MESSAGING_GATEWAY_POSTURE_ROUTE_REF,
    RuntimeMessagingGatewayPlatform,
    RuntimeMessagingGatewayPostureReadModel,
    build_runtime_messaging_gateway_posture_read_model,
)


client = TestClient(app)


def test_messaging_gateway_is_metadata_readiness_only() -> None:
    read_model = build_runtime_messaging_gateway_posture_read_model()

    assert read_model.schema_version == "runtime_messaging_gateway_posture.v1"
    assert read_model.status == "metadata_readiness_map_only"
    assert read_model.route_ref == RUNTIME_MESSAGING_GATEWAY_POSTURE_ROUTE_REF
    assert read_model.cli_ref == "uaa runtime inspect-messaging-gateway-posture"
    assert (
        read_model.authority_state_mapping_ref
        == RUNTIME_MESSAGING_GATEWAY_POSTURE_AUTHORITY_MAPPING_REF
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
    assert "adapter-ref:messaging-gateway-email:not-implemented" in (
        read_model.unsupported_adapter_refs
    )
    assert read_model.platform_count == 6
    assert read_model.blocked_platform_count == 6
    assert read_model.connector_runtime_enabled is False
    assert read_model.connector_read_enabled is False
    assert read_model.send_enabled is False
    assert read_model.oauth_enabled is False
    assert read_model.webhook_exposure_enabled is False
    assert read_model.account_sync_enabled is False
    assert read_model.external_write_enabled is False
    assert read_model.raw_message_persisted is False
    assert read_model.control_center_mints_authority is False
    assert set(RUNTIME_MESSAGING_GATEWAY_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


def test_messaging_gateway_route_returns_authority_bound_read_model() -> None:
    response = client.get("/api/runtime/messaging-gateway-posture")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_messaging_gateway_posture"
    data = body["data"]
    assert data["schema_version"] == "runtime_messaging_gateway_posture.v1"
    assert data["route_ref"] == "GET /api/runtime/messaging-gateway-posture"
    assert (
        data["authority_state_mapping_ref"]
        == "lane-ref:runtime-messaging-gateway-posture-read-model"
    )
    assert data["authority_state_decision_outcome"] == "allow"
    assert data["platform_count"] == 6
    assert data["blocked_platform_count"] == 6
    assert data["connector_runtime_enabled"] is False
    assert data["send_enabled"] is False
    assert data["oauth_enabled"] is False
    assert data["external_write_enabled"] is False


def test_messaging_gateway_platform_labels_are_blocked() -> None:
    read_model = build_runtime_messaging_gateway_posture_read_model()
    platform_kinds = {platform.platform_kind for platform in read_model.platforms}

    assert platform_kinds == {
        "email",
        "slack",
        "telegram",
        "sms",
        "discord",
        "generic_webhook",
    }
    for platform in read_model.platforms:
        assert platform.status == "blocked_until_authority"
        assert platform.platform_ref.startswith("messaging-platform-ref:")
        assert platform.connector_label_ref.startswith("connector-label-ref:")
        assert platform.inbound_readiness_ref.startswith("inbound-readiness-ref:")
        assert platform.outbound_write_label_ref.startswith("outbound-write-label-ref:")
        assert platform.oauth_label_ref.startswith("oauth-label-ref:")
        assert platform.webhook_label_ref.startswith("webhook-label-ref:")
        assert platform.account_sync_label_ref.startswith("account-sync-label-ref:")
        assert platform.redaction_policy_ref.startswith("redaction-policy-ref:")
        assert platform.connector_runtime_enabled is False
        assert platform.connector_read_enabled is False
        assert platform.send_enabled is False
        assert platform.oauth_enabled is False
        assert platform.webhook_exposure_enabled is False
        assert platform.account_sync_enabled is False
        assert platform.external_write_enabled is False
        assert platform.raw_message_persisted is False
        assert platform.control_center_mints_authority is False


@pytest.mark.parametrize(
    "field",
    [
        "connector_runtime_enabled",
        "connector_read_enabled",
        "send_enabled",
        "oauth_enabled",
        "webhook_exposure_enabled",
        "account_sync_enabled",
        "external_write_enabled",
        "raw_message_persisted",
        "control_center_mints_authority",
    ],
)
def test_messaging_gateway_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_messaging_gateway_posture_read_model().model_dump(
        mode="json"
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_MESSAGING_GATEWAY_READ_MODEL_AUTHORITY_DENIED",
    ):
        RuntimeMessagingGatewayPostureReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "connector_runtime_enabled",
        "connector_read_enabled",
        "send_enabled",
        "oauth_enabled",
        "webhook_exposure_enabled",
        "account_sync_enabled",
        "external_write_enabled",
        "raw_message_persisted",
        "control_center_mints_authority",
    ],
)
def test_messaging_gateway_platform_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_messaging_gateway_posture_read_model()
        .platforms[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_MESSAGING_GATEWAY_PLATFORM_AUTHORITY_DENIED",
    ):
        RuntimeMessagingGatewayPlatform(**payload)


def test_messaging_gateway_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-messaging-gateway-posture",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "raw_message_value" not in result.stdout
    assert "connector_payload_value" not in result.stdout
    payload = json.loads(result.stdout)
    read_model = payload["runtime_messaging_gateway_posture"]
    assert payload["send_performed"] is False
    assert payload["oauth_performed"] is False
    assert payload["webhook_exposure_performed"] is False
    assert payload["external_write_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/messaging-gateway-posture"
    assert (
        read_model["authority_state_mapping_ref"]
        == "lane-ref:runtime-messaging-gateway-posture-read-model"
    )
    assert read_model["authority_state_decision_outcome"] == "allow"
    assert read_model["platform_count"] == 6
    assert read_model["blocked_platform_count"] == 6
