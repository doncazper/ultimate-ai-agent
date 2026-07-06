import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RuntimeApprovalBridgeEnvelope,
    RuntimeApprovalBridgeReadModel,
    RuntimeApprovalFailClosedTimeoutPosture,
    build_runtime_approval_bridge_read_model,
    validate_runtime_approval_scope,
)


client = TestClient(app)


def test_runtime_approval_bridge_is_read_model_resolution_blocked() -> None:
    read_model = build_runtime_approval_bridge_read_model()

    assert read_model.schema_version == "runtime_approval_bridge.v1"
    assert read_model.status == "read_model_resolution_blocked"
    assert read_model.uaa_controls_authority is True
    assert read_model.control_center_talks_directly_to_runtime is False
    assert read_model.safe_refs_only is True
    assert read_model.pending_runtime_approval_count == 1
    assert read_model.denied_preview_count == 1
    assert read_model.timeout_preview_count == 1
    assert read_model.scope_mismatch_count == 1
    assert read_model.runtime_resolution_sent_count == 0
    assert read_model.approval_resolution_route_enabled is False
    assert read_model.deny_resolution_route_enabled is False
    assert read_model.timeout_resolution_route_enabled is False
    assert read_model.raw_runtime_payload_persisted is False
    assert read_model.fail_closed_timeout_posture.expired_waits_default_to_deny is True
    assert (
        read_model.fail_closed_timeout_posture.ambiguous_waits_default_to_deny is True
    )
    assert read_model.fail_closed_timeout_posture.auto_approve_enabled is False
    assert read_model.fail_closed_timeout_posture.approve_all_enabled is False
    assert (
        read_model.fail_closed_timeout_posture.standing_broad_authority_enabled
        is False
    )
    assert "blocked-authority:runtime-approval-resolution-send" in (
        read_model.blocked_authority_refs
    )
    assert "blocked-authority:runtime-approval-approve-all" in (
        read_model.blocked_authority_refs
    )


def test_runtime_approval_bridge_binds_action_inbox_and_proof_refs() -> None:
    read_model = build_runtime_approval_bridge_read_model()

    projection = read_model.action_inbox_projection
    assert projection.action_inbox_item_ref.startswith("action-inbox-ref:")
    assert projection.status == "review_required_resolution_blocked"
    assert projection.approval_controls_visible is False
    assert projection.runtime_resolution_controls_visible is False
    assert projection.proof_ref in read_model.proof_refs
    envelope = read_model.envelopes[0]
    assert envelope.action_inbox_item_ref == projection.action_inbox_item_ref
    assert envelope.proof_ref == projection.proof_ref
    assert envelope.approval_refs_are_identifiers_only is True
    assert envelope.runtime_resolution_sent is False


def test_runtime_approval_bridge_scope_denial_and_timeout_paths_are_blocked() -> None:
    read_model = build_runtime_approval_bridge_read_model()

    mismatch = read_model.scope_validation
    assert mismatch.scope_matches is False
    assert mismatch.status == "scope_mismatch_blocked"

    match = validate_runtime_approval_scope(
        "runtime-approval-scope-ref:test",
        "runtime-approval-scope-ref:test",
    )
    assert match.scope_matches is True
    assert match.status == "scope_match_review_only"

    decisions = {preview.decision_kind: preview for preview in read_model.decision_previews}
    assert decisions["deny"].runtime_resolution_sent is False
    assert decisions["timeout"].runtime_resolution_sent is False
    assert decisions["scope_mismatch"].runtime_resolution_sent is False


def test_runtime_approval_bridge_fail_closed_posture_rejects_broad_grants() -> None:
    posture_payload = (
        build_runtime_approval_bridge_read_model()
        .fail_closed_timeout_posture.model_dump()
    )
    posture_payload["approve_all_enabled"] = True

    with pytest.raises(ValueError, match="UNSAFE_AUTHORITY_DENIED"):
        RuntimeApprovalFailClosedTimeoutPosture(**posture_payload)

    posture_payload = (
        build_runtime_approval_bridge_read_model()
        .fail_closed_timeout_posture.model_dump()
    )
    posture_payload["expired_waits_default_to_deny"] = False

    with pytest.raises(ValueError, match="FAIL_CLOSED_REQUIRED"):
        RuntimeApprovalFailClosedTimeoutPosture(**posture_payload)

    model_payload = build_runtime_approval_bridge_read_model().model_dump()
    model_payload["blocked_authority_refs"].remove(
        "blocked-authority:runtime-approval-auto-approve"
    )

    with pytest.raises(ValueError, match="FAIL_CLOSED_BLOCKER_DRIFT"):
        RuntimeApprovalBridgeReadModel(**model_payload)


def test_runtime_approval_bridge_rejects_resolution_or_approval_ref_authority() -> None:
    model_payload = build_runtime_approval_bridge_read_model().model_dump()
    model_payload["approval_resolution_route_enabled"] = True

    with pytest.raises(ValueError, match="UNSAFE_AUTHORITY_DENIED"):
        RuntimeApprovalBridgeReadModel(**model_payload)

    envelope_payload = build_runtime_approval_bridge_read_model().envelopes[0].model_dump()
    envelope_payload["runtime_resolution_sent"] = True

    with pytest.raises(ValueError, match="RESOLUTION_DENIED"):
        RuntimeApprovalBridgeEnvelope(**envelope_payload)

    envelope_payload = build_runtime_approval_bridge_read_model().envelopes[0].model_dump()
    envelope_payload["approval_refs_are_identifiers_only"] = False

    with pytest.raises(ValueError, match="APPROVAL_REF_AUTHORITY_DENIED"):
        RuntimeApprovalBridgeEnvelope(**envelope_payload)


def test_api_runtime_approval_bridge_route_returns_safe_refs() -> None:
    response = client.get("/api/runtime/approval-bridge")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["schema_version"] == "runtime_approval_bridge.v1"
    assert data["route_ref"] == "GET /api/runtime/approval-bridge"
    assert data["runtime_resolution_sent_count"] == 0
    assert data["approval_resolution_route_enabled"] is False
    assert data["fail_closed_timeout_posture"]["approve_all_enabled"] is False
    assert (
        data["fail_closed_timeout_posture"]["ambiguous_waits_default_to_deny"]
        is True
    )
    assert data["raw_runtime_payload_persisted"] is False
    assert body["evidence"][0]["evidence_ref"] == (
        "evidence-ref:runtime-approval-bridge:phase-04"
    )


def test_cli_runtime_approval_bridge_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-approval-bridge",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_approval_bridge"]
    assert payload["execution_performed"] is False
    assert payload["approval_resolution_sent"] is False
    assert payload["denial_resolution_sent"] is False
    assert payload["timeout_resolution_sent"] is False
    assert payload["auto_approve_enabled"] is False
    assert payload["approve_all_enabled"] is False
    assert payload["standing_broad_authority_enabled"] is False
    assert read_model["route_ref"] == "GET /api/runtime/approval-bridge"
    assert read_model["cli_ref"] == "uaa runtime inspect-approval-bridge"
    assert read_model["runtime_resolution_sent_count"] == 0
    assert read_model["fail_closed_timeout_posture"]["policy_ref"] == (
        "timeout-policy-ref:runtime-approval-bridge:fail-closed-v1"
    )
