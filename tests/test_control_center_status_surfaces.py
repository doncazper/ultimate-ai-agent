from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app


client = TestClient(app)


def test_control_center_settings_status_is_backend_owned_read_only() -> None:
    response = client.get("/control-center/settings/status")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_settings_status"
    assert "safe_refs_only" in body["redactions_applied"]

    data = body["data"]
    assert data["status"] == "read_only_status"
    assert data["maturity_gate_status"] == "active_promotion_gate"
    assert data["proposal_review_only"] is True
    assert "settings-proposal:kill-switch-status-route" in data["review_proposals"]
    assert data["maturity_manifest_ref"] == (
        "docs/control_center/operational_maturity_manifest.json"
    )
    assert data["verifier_ref"] == "scripts/verify_operational_maturity.py"
    assert data["feature_flag_mutation_enabled"] is False
    assert data["kill_switch_mutation_enabled"] is False
    assert data["settings_mutation_enabled"] is False
    assert data["production_authority_enabled"] is False
    assert "kill_switch_mutation" in data["blocked_authorities"]
    assert data["authority_postures"][0]["capability_key"] == "web"
    assert data["kill_switch_postures"][0]["state_label"] == "Not configured"
    assert data["kill_switch_postures"][0]["execution_enabled"] is False
    assert data["feature_flag_postures"][0]["state_label"] == "Metadata only"
    assert data["feature_flag_postures"][0]["toggle_enabled"] is False


def test_control_center_local_models_status_is_read_only_and_blocks_lifecycle() -> None:
    response = client.get("/control-center/local-models/status")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_local_models_status"
    assert body["redactions_applied"] == [
        "safe_refs_only",
        "raw_paths_omitted",
        "credentials_omitted",
        "no_model_calls",
    ]

    data = body["data"]
    assert data["status"] == "read_only_status"
    assert data["proposal_review_only"] is True
    assert "local-models-proposal:lifecycle-status-route" in data["review_proposals"]
    assert data["inventory"]["schema_version"] == "uaa_local_model_inventory.v1"
    assert data["gateway_posture"]["local_gateway_enabled"] is False
    assert data["gateway_posture"]["bearer_env_configured"] is False
    assert {adapter["adapter_id"] for adapter in data["adapter_readiness"]} == {
        "ollama",
        "mlx_lm",
    }
    assert all(
        adapter["runtime_calls_enabled"] is False
        for adapter in data["adapter_readiness"]
    )
    assert all(
        adapter["model_pulls_enabled"] is False
        for adapter in data["adapter_readiness"]
    )
    assert all(enabled is False for enabled in data["lifecycle_actions"].values())
    assert "model_download" in data["blocked_authorities"]
    assert "model_pull" in data["blocked_authorities"]
    assert "provider_model_authority" in data["blocked_authorities"]
