import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_WORKTREE_PER_AGENT_BLOCKED_AUTHORITY_REFS,
    RUNTIME_WORKTREE_PER_AGENT_CONTRACT_REF,
    RuntimeWorktreePerAgentLane,
    RuntimeWorktreePerAgentReadModel,
    build_runtime_worktree_per_agent_read_model,
)


client = TestClient(app)


def test_worktree_per_agent_is_read_only_posture() -> None:
    read_model = build_runtime_worktree_per_agent_read_model()

    assert read_model.schema_version == "runtime_worktree_per_agent.v1"
    assert read_model.contract_ref == RUNTIME_WORKTREE_PER_AGENT_CONTRACT_REF
    assert read_model.status == "read_only_worktree_lane_posture"
    assert read_model.route_ref == "GET /api/runtime/worktree-per-agent"
    assert read_model.cli_ref == "uaa runtime inspect-worktree-per-agent"
    assert read_model.lane_count == 3
    assert read_model.proposal_count == 1
    assert read_model.review_ready_count == 1
    assert read_model.mutation_blocked_count == 1
    assert read_model.workspace_grants_visible is True
    assert read_model.branch_name_policy_visible is True
    assert read_model.checkpoint_plan_visible is True
    assert read_model.git_receipt_plan_visible is True
    assert read_model.rollback_plan_visible is True
    assert read_model.cli_parity_visible is True
    assert read_model.git_worktree_create_enabled is False
    assert read_model.git_worktree_delete_enabled is False
    assert read_model.branch_mutation_enabled is False
    assert read_model.file_write_enabled is False
    assert read_model.commit_enabled is False
    assert read_model.push_enabled is False
    assert read_model.shell_execution_enabled is False
    assert read_model.provider_call_enabled is False
    assert read_model.control_center_mints_authority is False
    assert read_model.raw_path_persisted is False
    assert set(RUNTIME_WORKTREE_PER_AGENT_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


def test_worktree_lanes_show_branch_checkpoint_and_rollback_refs() -> None:
    read_model = build_runtime_worktree_per_agent_read_model()
    statuses_by_label = {lane.display_label: lane.lane_status for lane in read_model.lanes}

    assert statuses_by_label == {
        "Implementer worktree lane": "proposal",
        "Reviewer comparison lane": "review_ready",
        "Verifier proof lane": "mutation_blocked",
    }
    for lane in read_model.lanes:
        assert lane.lane_ref.startswith("worktree-agent-lane-ref:")
        assert lane.workspace_scope_ref.startswith("workspace-scope-ref:")
        assert lane.branch_proposal_ref.startswith("branch-proposal-ref:")
        assert lane.branch_name_ref.startswith("branch-name-ref:")
        assert lane.worktree_ref.startswith("worktree-ref:")
        assert lane.checkpoint_plan_ref.startswith("checkpoint-plan-ref:")
        assert lane.git_receipt_plan_ref.startswith("git-receipt-plan-ref:")
        assert lane.rollback_plan_ref.startswith("rollback-plan-ref:")
        assert lane.git_worktree_create_enabled is False
        assert lane.git_worktree_delete_enabled is False
        assert lane.branch_mutation_enabled is False
        assert lane.file_write_enabled is False
        assert lane.commit_enabled is False
        assert lane.push_enabled is False
        assert lane.shell_execution_enabled is False
        assert lane.provider_call_enabled is False
        assert lane.raw_path_persisted is False
        assert set(RUNTIME_WORKTREE_PER_AGENT_BLOCKED_AUTHORITY_REFS).issubset(
            set(lane.blocked_authority_refs)
        )


@pytest.mark.parametrize(
    "field",
    [
        "git_worktree_create_enabled",
        "git_worktree_delete_enabled",
        "branch_mutation_enabled",
        "file_write_enabled",
        "commit_enabled",
        "push_enabled",
        "shell_execution_enabled",
        "provider_call_enabled",
        "control_center_mints_authority",
        "raw_path_persisted",
    ],
)
def test_worktree_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_worktree_per_agent_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_WORKTREE_PER_AGENT_AUTHORITY_DENIED"):
        RuntimeWorktreePerAgentReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "git_worktree_create_enabled",
        "git_worktree_delete_enabled",
        "branch_mutation_enabled",
        "file_write_enabled",
        "commit_enabled",
        "push_enabled",
        "shell_execution_enabled",
        "provider_call_enabled",
        "raw_path_persisted",
    ],
)
def test_worktree_lane_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_worktree_per_agent_read_model()
        .lanes[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_WORKTREE_PER_AGENT_LANE_AUTHORITY_DENIED",
    ):
        RuntimeWorktreePerAgentLane(**payload)


def test_worktree_per_agent_api_returns_safe_read_model() -> None:
    response = client.get("/api/runtime/worktree-per-agent")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_worktree_per_agent"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/worktree-per-agent"
    assert data["lane_count"] == 3
    assert data["git_worktree_create_enabled"] is False
    assert data["branch_mutation_enabled"] is False
    assert data["file_write_enabled"] is False
    assert data["commit_enabled"] is False
    assert data["push_enabled"] is False
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "raw_path_value" not in serialized
    assert "raw_git_output_value" not in serialized


def test_worktree_per_agent_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-worktree-per-agent",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_worktree_per_agent"]
    assert payload["safe_refs_only"] is True
    assert payload["proposal_only"] is True
    assert payload["git_worktree_create_performed"] is False
    assert payload["git_worktree_delete_performed"] is False
    assert payload["branch_mutation_performed"] is False
    assert payload["file_write_performed"] is False
    assert payload["commit_performed"] is False
    assert payload["push_performed"] is False
    assert payload["shell_execution_performed"] is False
    assert payload["provider_call_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/worktree-per-agent"
    assert read_model["cli_ref"] == "uaa runtime inspect-worktree-per-agent"
    assert read_model["lane_count"] == 3
