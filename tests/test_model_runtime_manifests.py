import pytest
from pydantic import ValidationError

from tests.m8_helpers import simulated_manifest
from ultimate_ai_agent.core.model_runtime import ModelRuntimeKind, ModelRuntimeSafetyMode, validate_runtime_manifest


def test_valid_simulated_manifest_passes():
    manifest = simulated_manifest()

    result = validate_runtime_manifest(manifest)

    assert result.success is True
    assert result.data["adapter_id"] == "sim_adapter"
    assert manifest.runtime_kind == ModelRuntimeKind.simulated
    assert manifest.safety_mode == ModelRuntimeSafetyMode.simulated


def test_manifest_rejects_unknown_fields_and_raw_secrets():
    payload = simulated_manifest().model_dump()
    payload["api_key"] = "ABCDEFGHIJKLMNOP"

    with pytest.raises(ValidationError):
        type(simulated_manifest())(**payload)

    payload = simulated_manifest().model_dump()
    payload["metadata"] = {"note": "password='ABCDEFGHIJKLMNOP'"}

    with pytest.raises(ValueError, match="secret-like"):
        type(simulated_manifest())(**payload)


def test_disabled_manifest_cannot_be_used():
    result = validate_runtime_manifest(simulated_manifest(enabled=False))

    assert result.success is False
    assert result.error.code == "MODEL_RUNTIME_ADAPTER_DISABLED"


def test_manifest_cannot_declare_live_runtime_endpoint():
    payload = simulated_manifest().model_dump()
    payload["simulated_base_url"] = "https://example.invalid"

    with pytest.raises(ValidationError):
        type(simulated_manifest())(**payload)
