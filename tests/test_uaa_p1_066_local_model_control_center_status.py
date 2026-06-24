from __future__ import annotations

from pathlib import Path

import pytest

import scripts.verify_uaa_p1_066_local_model_control_center_status as verifier
from ultimate_ai_agent.core.control_center.operational_status import (
    ControlCenterLocalModelsStatus,
    build_control_center_local_models_status,
)


ROOT = Path(__file__).resolve().parents[1]


def test_uaa_p1_066_scope_verifier_passes_current_repo() -> None:
    assert verifier.validate_uaa_p1_066_local_model_control_center_status() == []


def test_uaa_p1_066_scope_doc_pins_read_only_control_center_boundary() -> None:
    text = (
        ROOT
        / "docs/model_management/UAA_P1_066_LOCAL_MODEL_CONTROL_CENTER_READ_ONLY_STATUS.md"
    ).read_text(encoding="utf-8")

    assert "Status: Implemented" in text
    assert "GET /control-center/local-models/status" in text
    assert "ControlCenterLocalModelsStatus" in text
    assert "build_control_center_local_models_status" in text
    assert "No start, stop, activate, switch, unload, or lifecycle controls" in text
    assert "No React-owned model truth" in text
    assert "No model downloads" in text
    assert verifier.VERIFIER_REF in text


def test_control_center_local_models_status_remains_read_only() -> None:
    status = build_control_center_local_models_status(env={})

    assert status.status == "read_only_status"
    assert status.route_ref == "GET /control-center/local-models/status"
    assert status.proposal_review_only is True
    assert status.inventory["schema_version"] == "uaa_local_model_inventory.v1"
    assert all(enabled is False for enabled in status.lifecycle_actions.values())
    assert "model_download" in status.blocked_authorities
    assert "model_switch" in status.blocked_authorities
    assert "provider_model_authority" in status.blocked_authorities


def test_control_center_local_models_status_rejects_lifecycle_enablement() -> None:
    with pytest.raises(ValueError, match="CONTROL_CENTER_LOCAL_MODELS_LIFECYCLE_DENIED"):
        ControlCenterLocalModelsStatus(
            inventory={"schema_version": "uaa_local_model_inventory.v1"},
            gateway_posture={"local_gateway_enabled": False},
            lifecycle_actions={"download_enabled": True},
        )
