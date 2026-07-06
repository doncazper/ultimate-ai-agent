from __future__ import annotations

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_CHECKPOINT_ROLLBACK_BLOCKED_AUTHORITY_REFS,
    RUNTIME_CHECKPOINT_ROLLBACK_CONTRACT_REF,
    RuntimeCheckpointRollbackReadModel,
    build_runtime_checkpoint_rollback_read_model,
)


client = TestClient(app)


def test_checkpoint_rollback_posture_is_read_only_safe_ref_model() -> None:
    read_model = build_runtime_checkpoint_rollback_read_model()

    assert read_model.schema_version == "runtime_checkpoint_rollback.v1"
    assert read_model.contract_ref == RUNTIME_CHECKPOINT_ROLLBACK_CONTRACT_REF
    assert read_model.status == "read_only_checkpoint_rollback_posture"
    assert read_model.route_ref == "GET /api/runtime/checkpoint-rollback"
    assert read_model.cli_ref == "uaa runtime inspect-checkpoint-rollback"
    assert read_model.lane_count == 5
    assert read_model.checkpoint_required_count == 5
    assert read_model.checkpoint_available_count == 3
    assert read_model.exact_core_supported_count == 1
    assert read_model.blocked_lane_count == 1
    assert read_model.broad_filesystem_snapshot_enabled is False
    assert read_model.rollback_execution_route_enabled is False
    assert read_model.git_mutation_enabled is False
    assert read_model.raw_content_persistence_enabled is False
    assert read_model.raw_path_persistence_enabled is False
    assert read_model.production_authority_enabled is False
    assert set(RUNTIME_CHECKPOINT_ROLLBACK_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )
    assert read_model.snapshot_hash_ref.startswith(
        "snapshot-hash-ref:runtime-checkpoint-rollback:"
    )


def test_checkpoint_rollback_lanes_do_not_execute_or_persist_raw_material() -> None:
    read_model = build_runtime_checkpoint_rollback_read_model()
    kinds = {lane.lane_kind for lane in read_model.lanes}

    assert kinds == {
        "file_patch_core",
        "work_board_reorder",
        "crm_local_mutation",
        "local_task_commit",
        "coding_patch_apply_readiness",
    }
    file_patch = next(lane for lane in read_model.lanes if lane.lane_kind == "file_patch_core")
    assert file_patch.exact_core_rollback_receipts_supported is True
    for lane in read_model.lanes:
        assert lane.checkpoint_required is True
        assert lane.checkpoint_ref.startswith("checkpoint-ref:")
        assert lane.checkpoint_hash_ref.startswith("checkpoint-hash-ref:")
        assert lane.mutation_receipt_ref.startswith("receipt-ref:")
        assert lane.rollback_plan_ref.startswith("rollback-plan-ref:")
        assert lane.rollback_receipt_ref.startswith("receipt-ref:")
        assert lane.approval_scope_ref.startswith("approval-scope-ref:")
        assert lane.idempotency_ref.startswith("idempotency-ref:")
        assert lane.api_rollback_execution_enabled is False
        assert lane.control_center_rollback_execution_enabled is False
        assert lane.broad_filesystem_snapshot_enabled is False
        assert lane.git_mutation_enabled is False
        assert lane.raw_content_persisted is False
        assert lane.raw_path_persisted is False
        assert lane.provider_model_call_performed is False
        assert lane.shell_execution_performed is False
        assert lane.browser_automation_performed is False
        assert lane.production_authority_enabled is False
        assert set(RUNTIME_CHECKPOINT_ROLLBACK_BLOCKED_AUTHORITY_REFS).issubset(
            set(lane.blocked_authority_refs)
        )


@pytest.mark.parametrize(
    "field",
    [
        "broad_filesystem_snapshot_enabled",
        "rollback_execution_route_enabled",
        "git_mutation_enabled",
        "raw_content_persistence_enabled",
        "raw_path_persistence_enabled",
        "production_authority_enabled",
    ],
)
def test_checkpoint_rollback_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_checkpoint_rollback_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_CHECKPOINT_ROLLBACK_AUTHORITY_DENIED"):
        RuntimeCheckpointRollbackReadModel(**payload)


def test_checkpoint_rollback_api_returns_read_only_posture() -> None:
    response = client.get("/api/runtime/checkpoint-rollback")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_checkpoint_rollback"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/checkpoint-rollback"
    assert data["rollback_execution_route_enabled"] is False
    assert data["lane_count"] == 5
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "raw_content_payload" not in serialized
    assert "target_path" not in serialized


def test_checkpoint_rollback_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-checkpoint-rollback",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_checkpoint_rollback"]
    assert payload["safe_refs_only"] is True
    assert payload["broad_filesystem_snapshot_performed"] is False
    assert payload["rollback_execution_performed"] is False
    assert payload["git_mutation_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/checkpoint-rollback"
    assert read_model["cli_ref"] == "uaa runtime inspect-checkpoint-rollback"
    assert read_model["lane_count"] == 5
