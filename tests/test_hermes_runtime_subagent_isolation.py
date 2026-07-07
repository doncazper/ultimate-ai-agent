import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_MAPPING_REF,
    RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_STATE_CLI_REF,
    RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_STATE_ROUTE_REF,
    RUNTIME_SUBAGENT_ISOLATION_BLOCKED_AUTHORITY_REFS,
    RUNTIME_SUBAGENT_ISOLATION_CONTRACT_REF,
    RuntimeSubagentIsolationReadModel,
    RuntimeSubagentIsolationRole,
    RuntimeSubagentReviewArtifact,
    build_runtime_subagent_isolation_read_model,
)


client = TestClient(app)


def test_subagent_isolation_is_readiness_only() -> None:
    read_model = build_runtime_subagent_isolation_read_model()

    assert read_model.schema_version == "runtime_subagent_isolation.v1"
    assert read_model.contract_ref == RUNTIME_SUBAGENT_ISOLATION_CONTRACT_REF
    assert read_model.status == "identity_isolation_readiness"
    assert read_model.route_ref == "GET /api/runtime/subagent-isolation"
    assert read_model.cli_ref == "uaa runtime inspect-subagent-isolation"
    assert (
        read_model.authority_state_route_ref
        == RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_STATE_ROUTE_REF
    )
    assert (
        read_model.authority_state_cli_ref
        == RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_STATE_CLI_REF
    )
    assert (
        read_model.authority_state_mapping_ref
        == RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_MAPPING_REF
    )
    assert read_model.authority_state_catalog_ref.startswith(
        "authority-decision-catalog-ref:"
    )
    assert read_model.authority_state_decision_ref.startswith(
        "authority-policy-decision-ref:"
    )
    assert read_model.authority_state_decision_outcome == "deny"
    assert read_model.authority_state_status == "planned_unsupported_adapter"
    assert "reason-ref:authority:adapter-unsupported" in (
        read_model.authority_state_reason_refs
    )
    assert "adapter-ref:subagent-live-dispatch:not-implemented" in (
        read_model.unsupported_adapter_refs
    )
    assert read_model.role_count == 3
    assert read_model.review_artifact_count == 3
    assert read_model.contract_ready_count == 1
    assert read_model.review_ready_count == 1
    assert read_model.blocked_dispatch_count == 1
    assert read_model.identity_registry_visible is True
    assert read_model.scope_envelopes_visible is True
    assert read_model.context_pack_grants_visible is True
    assert read_model.tool_grants_visible is True
    assert read_model.memory_grants_visible is True
    assert read_model.budget_visible is True
    assert read_model.kill_switch_visible is True
    assert read_model.receipt_plan_visible is True
    assert read_model.proof_visible is True
    assert read_model.live_dispatch_enabled is False
    assert read_model.background_fanout_enabled is False
    assert read_model.cross_agent_memory_transfer_enabled is False
    assert read_model.tool_sharing_enabled is False
    assert read_model.autonomous_delegation_enabled is False
    assert read_model.provider_call_enabled is False
    assert read_model.shell_execution_enabled is False
    assert read_model.connector_write_enabled is False
    assert read_model.control_center_mints_authority is False
    assert read_model.raw_transcript_persisted is False
    assert set(RUNTIME_SUBAGENT_ISOLATION_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


def test_subagent_roles_and_artifacts_are_safe_refs_only() -> None:
    read_model = build_runtime_subagent_isolation_read_model()
    statuses_by_label = {
        role.display_label: role.readiness_status for role in read_model.roles
    }

    assert statuses_by_label == {
        "Implementer": "contract_ready",
        "Reviewer": "review_ready",
        "Verifier": "blocked_dispatch",
    }
    for role in read_model.roles:
        assert role.role_ref.startswith("subagent-role-ref:")
        assert role.scope_envelope_ref.startswith("scope-envelope-ref:subagent:")
        assert role.context_pack_ref.startswith("context-pack-ref:subagent:")
        assert role.tool_grant_ref.startswith("tool-grant-ref:subagent:")
        assert role.memory_grant_ref.startswith("memory-grant-ref:subagent:")
        assert role.budget_ref.startswith("budget-ref:subagent:")
        assert role.kill_switch_ref.startswith("kill-switch-ref:subagent:")
        assert role.receipt_plan_ref.startswith("receipt-plan-ref:subagent:")
        assert role.live_dispatch_enabled is False
        assert role.background_fanout_enabled is False
        assert role.cross_agent_memory_transfer_enabled is False
        assert role.tool_sharing_enabled is False
        assert role.autonomous_delegation_enabled is False
        assert role.provider_call_enabled is False
        assert role.shell_execution_enabled is False
        assert role.connector_write_enabled is False
        assert role.raw_transcript_persisted is False
        assert set(RUNTIME_SUBAGENT_ISOLATION_BLOCKED_AUTHORITY_REFS).issubset(
            set(role.blocked_authority_refs)
        )
    for artifact in read_model.review_artifacts:
        assert artifact.artifact_ref.startswith("subagent-artifact-ref:")
        assert artifact.source_role_refs
        assert artifact.proof_refs
        assert artifact.raw_agent_output_persisted is False
        assert artifact.executable_authority is False


@pytest.mark.parametrize(
    "field",
    [
        "live_dispatch_enabled",
        "background_fanout_enabled",
        "cross_agent_memory_transfer_enabled",
        "tool_sharing_enabled",
        "autonomous_delegation_enabled",
        "provider_call_enabled",
        "shell_execution_enabled",
        "connector_write_enabled",
        "control_center_mints_authority",
        "raw_transcript_persisted",
    ],
)
def test_subagent_isolation_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_subagent_isolation_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_DENIED"):
        RuntimeSubagentIsolationReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "live_dispatch_enabled",
        "background_fanout_enabled",
        "cross_agent_memory_transfer_enabled",
        "tool_sharing_enabled",
        "autonomous_delegation_enabled",
        "provider_call_enabled",
        "shell_execution_enabled",
        "connector_write_enabled",
        "raw_transcript_persisted",
    ],
)
def test_subagent_role_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_subagent_isolation_read_model()
        .roles[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_SUBAGENT_ROLE_AUTHORITY_DENIED"):
        RuntimeSubagentIsolationRole(**payload)


def test_subagent_review_artifacts_deny_raw_output_and_authority() -> None:
    payload = (
        build_runtime_subagent_isolation_read_model()
        .review_artifacts[0]
        .model_dump(mode="json")
    )
    payload["raw_agent_output_persisted"] = True

    with pytest.raises(ValueError, match="RUNTIME_SUBAGENT_ARTIFACT_AUTHORITY_DENIED"):
        RuntimeSubagentReviewArtifact(**payload)

    payload["raw_agent_output_persisted"] = False
    payload["executable_authority"] = True

    with pytest.raises(ValueError, match="RUNTIME_SUBAGENT_ARTIFACT_AUTHORITY_DENIED"):
        RuntimeSubagentReviewArtifact(**payload)


def test_subagent_isolation_api_returns_safe_read_model() -> None:
    response = client.get("/api/runtime/subagent-isolation")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_subagent_isolation"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/subagent-isolation"
    assert (
        data["authority_state_mapping_ref"]
        == RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_MAPPING_REF
    )
    assert data["authority_state_decision_outcome"] == "deny"
    assert data["authority_state_status"] == "planned_unsupported_adapter"
    assert "reason-ref:authority:adapter-unsupported" in (
        data["authority_state_reason_refs"]
    )
    assert "adapter-ref:subagent-live-dispatch:not-implemented" in (
        data["unsupported_adapter_refs"]
    )
    assert data["role_count"] == 3
    assert data["live_dispatch_enabled"] is False
    assert data["background_fanout_enabled"] is False
    assert data["tool_sharing_enabled"] is False
    assert data["connector_write_enabled"] is False
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "raw_prompt_value" not in serialized
    assert "provider_payload_value" not in serialized
    assert "raw_transcript_value" not in serialized


def test_subagent_isolation_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-subagent-isolation",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_subagent_isolation"]
    assert payload["safe_refs_only"] is True
    assert payload["readiness_only"] is True
    assert payload["live_dispatch_performed"] is False
    assert payload["background_fanout_performed"] is False
    assert payload["cross_agent_memory_transfer_performed"] is False
    assert payload["tool_sharing_performed"] is False
    assert payload["autonomous_delegation_performed"] is False
    assert payload["provider_call_performed"] is False
    assert payload["shell_execution_performed"] is False
    assert payload["connector_write_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/subagent-isolation"
    assert read_model["cli_ref"] == "uaa runtime inspect-subagent-isolation"
    assert (
        read_model["authority_state_mapping_ref"]
        == RUNTIME_SUBAGENT_ISOLATION_AUTHORITY_MAPPING_REF
    )
    assert read_model["authority_state_decision_outcome"] == "deny"
    assert read_model["authority_state_status"] == "planned_unsupported_adapter"
    assert "reason-ref:authority:adapter-unsupported" in (
        read_model["authority_state_reason_refs"]
    )
    assert read_model["role_count"] == 3
