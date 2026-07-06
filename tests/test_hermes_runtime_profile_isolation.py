import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RuntimeProfileIsolationReadModel,
    RuntimeProfileIsolationRecord,
    build_runtime_profile_isolation_read_model,
)


client = TestClient(app)


def test_runtime_profile_isolation_is_read_model_only() -> None:
    read_model = build_runtime_profile_isolation_read_model()

    assert read_model.schema_version == "runtime_profile_isolation.v1"
    assert read_model.status == "profile_metadata_read_model_only"
    assert read_model.route_ref == "GET /api/runtime/profiles"
    assert read_model.cli_ref == "uaa runtime inspect-profiles"
    assert read_model.profile_count == 5
    assert read_model.configured_profile_count == 2
    assert read_model.blocked_profile_count == 3
    assert read_model.uaa_profile_refs_separate_from_delegated_runtime_refs is True
    assert read_model.profile_creation_enabled is False
    assert read_model.profile_deletion_enabled is False
    assert read_model.runtime_config_write_enabled is False
    assert read_model.sensitive_material_copy_enabled is False
    assert read_model.runtime_default_change_enabled is False
    assert read_model.cross_profile_authority_bleed_allowed is False
    assert read_model.control_center_mints_profiles is False
    assert read_model.raw_profile_names_persisted is False
    assert read_model.raw_workspace_paths_persisted is False
    assert read_model.raw_sensitive_material_persisted is False


def test_runtime_profile_records_keep_uaa_refs_separate() -> None:
    read_model = build_runtime_profile_isolation_read_model()

    profile_refs = {profile.profile_ref for profile in read_model.profiles}
    delegated_refs = {
        profile.delegated_runtime_profile_ref for profile in read_model.profiles
    }
    assert profile_refs.isdisjoint(delegated_refs)
    assert {profile.role for profile in read_model.profiles} == {
        "coding",
        "research",
        "operations",
        "crm",
        "review",
    }
    assert all(profile.can_write_runtime_config is False for profile in read_model.profiles)
    assert all(profile.can_copy_sensitive_material is False for profile in read_model.profiles)
    assert all(profile.can_change_runtime_defaults is False for profile in read_model.profiles)
    assert all(profile.can_execute_tools is False for profile in read_model.profiles)
    assert all(profile.can_call_models is False for profile in read_model.profiles)
    assert all(profile.can_write_memory is False for profile in read_model.profiles)


def test_runtime_profile_isolation_rejects_mutation_or_bleed() -> None:
    payload = build_runtime_profile_isolation_read_model().model_dump()
    payload["profile_creation_enabled"] = True

    with pytest.raises(ValueError, match="MUTATION_AUTHORITY_DENIED"):
        RuntimeProfileIsolationReadModel(**payload)

    payload = build_runtime_profile_isolation_read_model().model_dump()
    payload["uaa_profile_refs_separate_from_delegated_runtime_refs"] = False

    with pytest.raises(ValueError, match="SEPARATE_REFS_REQUIRED"):
        RuntimeProfileIsolationReadModel(**payload)

    record_payload = build_runtime_profile_isolation_read_model().profiles[0].model_dump()
    record_payload["can_call_models"] = True

    with pytest.raises(ValueError, match="AUTHORITY_DENIED"):
        RuntimeProfileIsolationRecord(**record_payload)


def test_api_runtime_profiles_route_returns_safe_metadata() -> None:
    response = client.get("/api/runtime/profiles")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["schema_version"] == "runtime_profile_isolation.v1"
    assert data["route_ref"] == "GET /api/runtime/profiles"
    assert data["profile_creation_enabled"] is False
    assert data["runtime_config_write_enabled"] is False
    assert data["raw_workspace_paths_persisted"] is False
    assert body["evidence"][0]["evidence_ref"] == (
        "evidence-ref:runtime-profiles:phase-06"
    )


def test_cli_runtime_profiles_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-profiles",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_profile_isolation"]
    assert payload["execution_performed"] is False
    assert payload["profile_creation_performed"] is False
    assert payload["runtime_config_write_performed"] is False
    assert payload["sensitive_material_copy_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/profiles"
    assert read_model["cli_ref"] == "uaa runtime inspect-profiles"
    assert read_model["profile_count"] == 5
