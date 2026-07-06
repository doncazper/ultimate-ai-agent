import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_PREVIEW_RAIL_BLOCKED_AUTHORITY_REFS,
    RUNTIME_PREVIEW_RAIL_CONTRACT_REF,
    RuntimePreviewRailReadModel,
    RuntimePreviewRailSlot,
    build_runtime_preview_rail_read_model,
)


client = TestClient(app)


def test_preview_rail_is_safe_ref_read_model() -> None:
    read_model = build_runtime_preview_rail_read_model()

    assert read_model.schema_version == "runtime_preview_rail.v1"
    assert read_model.contract_ref == RUNTIME_PREVIEW_RAIL_CONTRACT_REF
    assert read_model.status == "safe_ref_preview_rail_posture"
    assert read_model.route_ref == "GET /api/runtime/preview-rail"
    assert read_model.cli_ref == "uaa runtime inspect-preview-rail"
    assert read_model.slot_count == 6
    assert read_model.safe_ref_ready_count == 2
    assert read_model.bounded_preview_placeholder_count == 3
    assert read_model.execution_blocked_count == 1
    assert read_model.source_classification_visible is True
    assert read_model.redaction_policy_visible is True
    assert read_model.bounded_preview_visible is True
    assert read_model.operator_attach_visible is True
    assert read_model.receipt_plan_visible is True
    assert read_model.proof_link_visible is True
    assert read_model.browser_automation_enabled is False
    assert read_model.raw_sensitive_file_display_enabled is False
    assert read_model.direct_runtime_payload_rendering_enabled is False
    assert read_model.screenshot_capture_enabled is False
    assert read_model.file_read_enabled is False
    assert read_model.file_write_enabled is False
    assert read_model.shell_execution_enabled is False
    assert read_model.provider_call_enabled is False
    assert read_model.control_center_mints_authority is False
    assert read_model.raw_path_persisted is False
    assert read_model.raw_file_content_persisted is False
    assert read_model.raw_runtime_payload_persisted is False
    assert set(RUNTIME_PREVIEW_RAIL_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


def test_preview_rail_slots_cover_expected_safe_refs() -> None:
    read_model = build_runtime_preview_rail_read_model()
    statuses_by_label = {
        slot.display_label: slot.slot_status for slot in read_model.slots
    }

    assert statuses_by_label == {
        "Safe file ref preview": "safe_ref_ready",
        "Diff ref preview": "safe_ref_ready",
        "Artifact ref preview": "bounded_preview_placeholder",
        "Run output summary preview": "bounded_preview_placeholder",
        "Proof detail preview": "bounded_preview_placeholder",
        "Delegated runtime event preview": "execution_blocked",
    }
    for slot in read_model.slots:
        assert slot.slot_ref.startswith("preview-rail-slot-ref:")
        assert slot.source_ref.startswith("preview-source-ref:")
        assert slot.source_classification_ref.startswith("source-classification-ref:")
        assert slot.bounded_preview_ref.startswith("bounded-preview-ref:")
        assert slot.redaction_policy_ref.startswith("redaction-policy-ref:")
        assert slot.attach_plan_ref.startswith("attach-plan-ref:")
        assert slot.receipt_plan_ref.startswith("receipt-plan-ref:")
        assert slot.proof_ref.startswith("proof-ref:")
        assert slot.browser_automation_enabled is False
        assert slot.raw_sensitive_file_display_enabled is False
        assert slot.direct_runtime_payload_rendering_enabled is False
        assert slot.screenshot_capture_enabled is False
        assert slot.file_read_enabled is False
        assert slot.file_write_enabled is False
        assert slot.shell_execution_enabled is False
        assert slot.provider_call_enabled is False
        assert slot.raw_path_persisted is False
        assert slot.raw_file_content_persisted is False
        assert slot.raw_runtime_payload_persisted is False
        assert set(RUNTIME_PREVIEW_RAIL_BLOCKED_AUTHORITY_REFS).issubset(
            set(slot.blocked_authority_refs)
        )


@pytest.mark.parametrize(
    "field",
    [
        "browser_automation_enabled",
        "raw_sensitive_file_display_enabled",
        "direct_runtime_payload_rendering_enabled",
        "screenshot_capture_enabled",
        "file_read_enabled",
        "file_write_enabled",
        "shell_execution_enabled",
        "provider_call_enabled",
        "control_center_mints_authority",
        "raw_path_persisted",
        "raw_file_content_persisted",
        "raw_runtime_payload_persisted",
    ],
)
def test_preview_rail_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_preview_rail_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_PREVIEW_RAIL_AUTHORITY_DENIED"):
        RuntimePreviewRailReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "browser_automation_enabled",
        "raw_sensitive_file_display_enabled",
        "direct_runtime_payload_rendering_enabled",
        "screenshot_capture_enabled",
        "file_read_enabled",
        "file_write_enabled",
        "shell_execution_enabled",
        "provider_call_enabled",
        "raw_path_persisted",
        "raw_file_content_persisted",
        "raw_runtime_payload_persisted",
    ],
)
def test_preview_rail_slot_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_preview_rail_read_model().slots[0].model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_PREVIEW_RAIL_SLOT_AUTHORITY_DENIED",
    ):
        RuntimePreviewRailSlot(**payload)


def test_preview_rail_api_returns_safe_read_model() -> None:
    response = client.get("/api/runtime/preview-rail")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_preview_rail"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/preview-rail"
    assert data["slot_count"] == 6
    assert data["browser_automation_enabled"] is False
    assert data["raw_sensitive_file_display_enabled"] is False
    assert data["direct_runtime_payload_rendering_enabled"] is False
    assert data["raw_file_content_persisted"] is False
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "raw_path_value" not in serialized
    assert "raw_file_content_value" not in serialized
    assert "raw_runtime_payload_value" not in serialized


def test_preview_rail_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-preview-rail",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_preview_rail"]
    assert payload["safe_refs_only"] is True
    assert payload["bounded_preview_only"] is True
    assert payload["raw_paths_omitted"] is True
    assert payload["raw_file_content_omitted"] is True
    assert payload["raw_runtime_payloads_omitted"] is True
    assert payload["browser_automation_performed"] is False
    assert payload["screenshot_capture_performed"] is False
    assert payload["file_read_performed"] is False
    assert payload["file_write_performed"] is False
    assert payload["shell_execution_performed"] is False
    assert payload["provider_call_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/preview-rail"
    assert read_model["cli_ref"] == "uaa runtime inspect-preview-rail"
    assert read_model["slot_count"] == 6
