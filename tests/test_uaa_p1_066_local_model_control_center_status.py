from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.verify_uaa_p1_066_local_model_control_center_status as verifier
from ultimate_ai_agent.core.control_center.operational_status import (
    ControlCenterLocalModelsStatus,
    build_control_center_local_models_status,
)
from ultimate_ai_agent.core.local_model_management.readiness import (
    OptionalLocalModelAdapterReadiness,
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
    assert "model_pull" in status.blocked_authorities
    assert "model_switch" in status.blocked_authorities
    assert "provider_model_authority" in status.blocked_authorities
    assert "ollama_runtime_call" in status.blocked_authorities
    assert "mlx_lm_runtime_call" in status.blocked_authorities


def test_control_center_local_models_status_includes_optional_stack_readiness() -> None:
    status = build_control_center_local_models_status(env={})
    adapters = {item.adapter_id: item for item in status.adapter_readiness}

    assert set(adapters) >= {"ollama", "mlx_lm"}
    assert adapters["ollama"].display_name == "Ollama"
    assert adapters["mlx_lm"].display_name == "MLX-LM"

    for adapter in adapters.values():
        assert adapter.readiness_state == "blocked"
        assert adapter.install_detection_posture == "blocked_manual_verification_required"
        assert adapter.config_detection_posture == "blocked_manual_verification_required"
        assert "GET /control-center/local-models/status" in adapter.route_refs
        assert adapter.runtime_calls_enabled is False
        assert adapter.model_pulls_enabled is False
        assert adapter.model_downloads_enabled is False
        assert adapter.lifecycle_start_stop_switch_enabled is False
        assert adapter.provider_model_authority_enabled is False
        assert adapter.control_center_subprocess_execution_enabled is False
        assert "blocked-authority:model-call" in adapter.blocked_authority_refs
        assert "blocked-authority:model-pull-download" in adapter.blocked_authority_refs

    serialized = json.dumps(status.model_dump(mode="json"), sort_keys=True).lower()
    for forbidden in ["/users/", "/home/", "password", "secret", "raw_prompt", "raw_response"]:
        assert forbidden not in serialized


def test_control_center_local_models_status_rejects_lifecycle_enablement() -> None:
    with pytest.raises(ValueError, match="CONTROL_CENTER_LOCAL_MODELS_LIFECYCLE_DENIED"):
        ControlCenterLocalModelsStatus(
            inventory={"schema_version": "uaa_local_model_inventory.v1"},
            gateway_posture={"local_gateway_enabled": False},
            lifecycle_actions={"download_enabled": True},
        )


def test_control_center_local_models_status_rejects_adapter_authority_enablement() -> None:
    with pytest.raises(ValueError, match="OPTIONAL_LOCAL_MODEL_ADAPTER_AUTHORITY_DENIED"):
        ControlCenterLocalModelsStatus(
            inventory={"schema_version": "uaa_local_model_inventory.v1"},
            gateway_posture={"local_gateway_enabled": False},
            adapter_readiness=[
                {
                    "adapter_id": "ollama",
                    "display_name": "Ollama",
                    "safe_evidence_refs": [
                        "evidence-ref:local-model-readiness:ollama:test"
                    ],
                    "runtime_calls_enabled": True,
                },
                {
                    "adapter_id": "mlx_lm",
                    "display_name": "MLX-LM",
                    "safe_evidence_refs": [
                        "evidence-ref:local-model-readiness:mlx-lm:test"
                    ],
                },
            ],
        )


@pytest.mark.parametrize(
    "unsafe_summary",
    [
        "manual check saw /Users/example/.ollama/models",
        "run ollama generate to verify this model",
    ],
)
def test_optional_local_model_adapter_readiness_rejects_unsafe_payload_text(
    unsafe_summary: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="OPTIONAL_LOCAL_MODEL_ADAPTER_UNSAFE_PAYLOAD_DENIED",
    ):
        OptionalLocalModelAdapterReadiness(
            adapter_id="ollama",
            display_name="Ollama",
            safe_evidence_refs=["evidence-ref:local-model-readiness:ollama:test"],
            next_safe_action=unsafe_summary,
        )


def test_control_center_local_models_status_rejects_duplicate_adapter_entries() -> None:
    with pytest.raises(
        ValueError,
        match="CONTROL_CENTER_LOCAL_MODELS_OPTIONAL_ADAPTERS_MISSING",
    ):
        ControlCenterLocalModelsStatus(
            inventory={"schema_version": "uaa_local_model_inventory.v1"},
            gateway_posture={"local_gateway_enabled": False},
            adapter_readiness=[
                {
                    "adapter_id": "ollama",
                    "display_name": "Ollama",
                    "safe_evidence_refs": [
                        "evidence-ref:local-model-readiness:ollama:test-a"
                    ],
                },
                {
                    "adapter_id": "ollama",
                    "display_name": "Ollama",
                    "safe_evidence_refs": [
                        "evidence-ref:local-model-readiness:ollama:test-b"
                    ],
                },
            ],
        )
