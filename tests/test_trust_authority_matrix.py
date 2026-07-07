from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.authority import AuthorityDomain
from ultimate_ai_agent.core.control_center.founder_loop import (
    FounderLoopControlCenterService,
)
from ultimate_ai_agent.core.control_center.trust_authority import (
    TRUST_AUTHORITY_MATRIX_CONTRACT_REF,
    TRUST_AUTHORITY_MATRIX_ROUTE_REF,
    TrustAuthorityMatrixReadModel,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]


def _assert_no_runtime_authority(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, sort_keys=True).lower()
    forbidden = [
        'broad_approval_enabled": true',
        'standing_authority_enabled": true',
        'runtime_context_injection_enabled": true',
        'connector_write_enabled": true',
        'provider_model_call_enabled": true',
        'shell_subprocess_execution_enabled": true',
        'browser_execution_enabled": true',
        'background_autonomy_enabled": true',
        'production_authority_enabled": true',
        'control_center_grants_authority": true',
        'raw_content_included": true',
        "/users/",
        "raw prompt",
        "raw response",
        "provider payload",
        "credential",
        "secret",
    ]
    for fragment in forbidden:
        assert fragment not in text


def test_trust_authority_matrix_explains_available_approval_and_blocked(
    tmp_path: Path,
) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )

    matrix = service.trust_authority_matrix()
    parsed = TrustAuthorityMatrixReadModel(**matrix)

    assert parsed.contract_ref == TRUST_AUTHORITY_MATRIX_CONTRACT_REF
    assert parsed.route_ref == TRUST_AUTHORITY_MATRIX_ROUTE_REF
    assert parsed.backend_owned is True
    assert parsed.safe_refs_only is True
    assert parsed.available_now_lane_refs
    assert parsed.approval_required_lane_refs
    assert "trust-lane:local-task-commit" in parsed.approval_required_lane_refs
    assert "trust-lane:work-board-durable-mutation" in (
        parsed.approval_required_lane_refs
    )
    assert "trust-lane:governed-command-execution" in (
        parsed.approval_required_lane_refs
    )
    for blocked_lane_ref in (
        "trust-lane:provider-model-invocation",
        "trust-lane:issue-tracker-sync",
        "trust-lane:connector-write-low-risk",
        "trust-lane:browser-low-risk-action",
        "trust-lane:background-autonomy-scoped",
        "trust-lane:production-authority-gate",
    ):
        assert blocked_lane_ref in parsed.blocked_lane_refs
    assert "trust-lane:local-draft-proposal" in parsed.available_now_lane_refs
    assert "trust-lane:web-evidence-product-slice" in parsed.available_now_lane_refs
    assert "trust-lane:model-slot-posture" in parsed.available_now_lane_refs
    assert "trust-lane:provider-draft-summarize" in parsed.available_now_lane_refs
    assert "trust-lane:connector-draft-only" in parsed.available_now_lane_refs
    assert any(
        lane.tier == 2 and lane.authority_state == "available_now"
        for lane in parsed.lanes
    )
    assert any(
        lane.tier == 3 and lane.requires_exact_approval for lane in parsed.lanes
    )
    assert all(
        lane.authority_state != "available_now" for lane in parsed.lanes if lane.tier >= 4
    )
    assert all(lane.authority_state == "blocked" for lane in parsed.lanes if lane.tier >= 4)
    assert all(lane.cli_inspection_refs for lane in parsed.lanes)
    assert all(lane.safe_disable_refs for lane in parsed.lanes)
    assert all(lane.rollback_refs for lane in parsed.lanes)
    assert all(lane.promotion_path_refs for lane in parsed.lanes)
    assert all(
        lane.authority_domain_ref.startswith("authority-domain-ref:")
        for lane in parsed.lanes
    )
    assert all(
        lane.authority_capability_ref.startswith("authority-capability-ref:")
        for lane in parsed.lanes
    )
    assert all(
        lane.authority_lease_requirement_ref.startswith(
            "authority-lease-requirement-ref:"
        )
        for lane in parsed.lanes
    )
    assert all(lane.required_authority_mode for lane in parsed.lanes)
    assert len(parsed.authority_capability_catalog) == len(parsed.lanes)
    assert parsed.authority_capability_catalog_refs == [
        entry.catalog_ref for entry in parsed.authority_capability_catalog
    ]
    assert [entry.source_lane_ref for entry in parsed.authority_capability_catalog] == [
        lane.lane_ref for lane in parsed.lanes
    ]
    catalog_by_lane = {
        entry.source_lane_ref: entry for entry in parsed.authority_capability_catalog
    }
    for lane in parsed.lanes:
        entry = catalog_by_lane[lane.lane_ref]
        assert entry.authority_domain_ref == lane.authority_domain_ref
        assert entry.authority_capability_ref == lane.authority_capability_ref
        assert entry.required_authority_mode == lane.required_authority_mode
        assert (
            entry.authority_lease_requirement_ref
            == lane.authority_lease_requirement_ref
        )
        assert entry.active_lease_required is True
        assert entry.unknown_authority_denied is True
        assert entry.safe_refs_only is True
        assert entry.control_center_grants_authority is False
        assert entry.execution_claimed is False
    assert parsed.authority_domain_coverage
    coverage_by_ref = {
        coverage.domain_ref: coverage for coverage in parsed.authority_domain_coverage
    }
    assert set(coverage_by_ref) == {
        f"authority-domain-ref:{domain.value}" for domain in AuthorityDomain
    }
    workspace_coverage = coverage_by_ref["authority-domain-ref:workspace"]
    assert workspace_coverage.status == "implemented"
    assert workspace_coverage.implemented_mapping_count > 0
    assert "lane-ref:runtime-command-focused-pytest" in (
        workspace_coverage.visible_mapping_refs
    )
    shell_coverage = coverage_by_ref["authority-domain-ref:shell"]
    assert shell_coverage.status == "planned"
    assert shell_coverage.planned_mapping_count == 1
    assert "lane-ref:shell-arbitrary-command-adapter" in (
        shell_coverage.visible_mapping_refs
    )
    assert "adapter-ref:shell-arbitrary-command:not-implemented" in (
        shell_coverage.unsupported_adapter_refs
    )
    calendar_coverage = coverage_by_ref["authority-domain-ref:calendar"]
    assert calendar_coverage.status == "partial"
    assert calendar_coverage.partial_mapping_count == 1
    for coverage in parsed.authority_domain_coverage:
        assert coverage.active_lease_required is True
        assert coverage.safe_refs_only is True
        assert coverage.execution_claimed is False
        assert coverage.known_authority is True
        assert coverage.mapping_count == (
            coverage.implemented_mapping_count
            + coverage.partial_mapping_count
            + coverage.planned_mapping_count
        )
        assert coverage.hidden_mapping_ref_count == (
            coverage.mapping_count - len(coverage.visible_mapping_refs)
        )
        assert coverage.authority_state_route_ref == "GET /api/runtime/authority-state"
        assert (
            coverage.authority_state_cli_ref
            == "repo-local-command:uaa-runtime-inspect-authority-state"
        )
    assert set(parsed.cli_inspection_refs) == {
        ref for lane in parsed.lanes for ref in lane.cli_inspection_refs
    }
    assert set(parsed.safe_disable_refs) == {
        ref for lane in parsed.lanes for ref in lane.safe_disable_refs
    }
    assert set(parsed.rollback_refs) == {
        ref for lane in parsed.lanes for ref in lane.rollback_refs
    }
    assert set(parsed.promotion_path_refs) == {
        ref for lane in parsed.lanes for ref in lane.promotion_path_refs
    }
    assert set(parsed.blocked_authority_refs) == {
        ref for lane in parsed.lanes for ref in lane.blocked_authority_refs
    }
    tier_2 = [lane for lane in parsed.lanes if lane.tier == 2]
    assert tier_2
    assert all(lane.operator_posture == "review_only" for lane in tier_2)
    assert all(not lane.rollback_execution_enabled for lane in parsed.lanes)
    tier_3_plus = [lane for lane in parsed.lanes if lane.tier >= 3]
    assert tier_3_plus
    assert all(lane.requires_safe_disable for lane in tier_3_plus)
    assert all(lane.requires_rollback_posture for lane in tier_3_plus)
    assert all(lane.safe_disable_refs for lane in tier_3_plus)
    assert all(lane.rollback_refs for lane in tier_3_plus)
    assert all(
        not any(ref.endswith(":read-model-only") for ref in lane.safe_disable_refs)
        for lane in tier_3_plus
    )
    assert all(
        not any(ref.endswith(":no-mutation") for ref in lane.rollback_refs)
        for lane in tier_3_plus
    )
    lanes_by_ref = {lane.lane_ref: lane for lane in parsed.lanes}
    command_lane = lanes_by_ref["trust-lane:governed-command-execution"]
    assert command_lane.authority_domain_ref == "authority-domain-ref:workspace"
    assert command_lane.authority_capability_ref == "authority-capability-ref:execute"
    assert command_lane.required_authority_mode == "ask_before_changes"
    assert (
        command_lane.authority_lease_requirement_ref
        == "authority-lease-requirement-ref:governed-command-execution:workspace:execute"
    )
    provider_lane = lanes_by_ref["trust-lane:provider-model-invocation"]
    assert (
        provider_lane.authority_domain_ref
        == "authority-domain-ref:provider_model_calls"
    )
    assert provider_lane.authority_capability_ref == "authority-capability-ref:execute"
    assert provider_lane.required_authority_mode == "full_machine_access_session"
    browser_lane = lanes_by_ref["trust-lane:browser-low-risk-action"]
    assert browser_lane.authority_domain_ref == "authority-domain-ref:browser"
    assert browser_lane.authority_capability_ref == "authority-capability-ref:click"
    _assert_no_runtime_authority(matrix)


def test_trust_authority_route_is_backend_owned() -> None:
    api_client = TestClient(app)
    response = api_client.get("/control-center/trust-authority/matrix")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    matrix = payload["data"]
    TrustAuthorityMatrixReadModel(**matrix)
    assert matrix["route_ref"] == "GET /control-center/trust-authority/matrix"
    assert "read_only_control_center_projection" in payload["redactions_applied"]
    _assert_no_runtime_authority(payload)


def test_trust_authority_cli_outputs_safe_refs_only(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "--state-dir",
            str(state_dir),
            "inspect-trust-authority",
            "--limit",
            "5",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["command_ref"] == "repo-local-command:founder-loop-trust-authority"
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True
    TrustAuthorityMatrixReadModel(**payload["trust_authority_matrix"])
    _assert_no_runtime_authority(payload)
    assert str(state_dir).lower() not in result.stdout.lower()


@pytest.mark.parametrize("flag", [
    "broad_approval_enabled",
    "standing_authority_enabled",
    "runtime_context_injection_enabled",
    "connector_write_enabled",
    "provider_model_call_enabled",
    "shell_subprocess_execution_enabled",
    "browser_execution_enabled",
    "background_autonomy_enabled",
    "production_authority_enabled",
])
def test_trust_authority_matrix_rejects_authority_creep(
    tmp_path: Path,
    flag: str,
) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )
    matrix = service.trust_authority_matrix()
    matrix[flag] = True

    with pytest.raises(ValidationError):
        TrustAuthorityMatrixReadModel(**matrix)


def test_trust_authority_matrix_rejects_posture_ref_drift(
    tmp_path: Path,
) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )
    matrix = service.trust_authority_matrix()
    matrix["safe_disable_refs"] = []

    with pytest.raises(ValidationError):
        TrustAuthorityMatrixReadModel(**matrix)


def test_trust_authority_matrix_rejects_domain_coverage_drift(
    tmp_path: Path,
) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )
    matrix = service.trust_authority_matrix()
    matrix["authority_domain_coverage"] = [
        coverage
        for coverage in matrix["authority_domain_coverage"]
        if coverage["domain_ref"] != "authority-domain-ref:shell"
    ]

    with pytest.raises(ValidationError):
        TrustAuthorityMatrixReadModel(**matrix)


@pytest.mark.parametrize("field,value", [
    ("operator_posture", "enabled_read_only"),
    ("rollback_execution_enabled", True),
    ("cli_inspection_refs", []),
])
def test_trust_authority_matrix_rejects_lane_posture_drift(
    tmp_path: Path,
    field: str,
    value: Any,
) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )
    matrix = service.trust_authority_matrix()
    tier_2_index = next(
        index for index, lane in enumerate(matrix["lanes"]) if lane["tier"] == 2
    )
    matrix["lanes"][tier_2_index][field] = value

    with pytest.raises(ValidationError):
        TrustAuthorityMatrixReadModel(**matrix)


def test_trust_authority_route_is_in_openapi() -> None:
    schema = app.openapi()
    route = schema["paths"]["/control-center/trust-authority/matrix"]["get"]

    assert route["operationId"] == "get_control_center_trust_authority_matrix"
