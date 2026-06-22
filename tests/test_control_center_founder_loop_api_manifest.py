# ruff: noqa: F401
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.chat import CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF
from ultimate_ai_agent.core.code import (
    GOVERNED_CODE_WORKBENCH_CONTRACT_REF,
    GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS,
    GOVERNED_CODE_WORKBENCH_REQUIRED_REF_FIELDS,
)
from ultimate_ai_agent.core.memory import (
    CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF,
    CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS,
    CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_REF_FIELDS,
    CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES,
    MEMORY_DERIVED_ACTION_REQUIRED_REF_FIELDS,
    MEMORY_TO_LOOP_BINDING_CONTRACT_REF,
    MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS,
    MEMORY_TO_LOOP_REQUIRED_REF_FIELDS,
    MEMORY_TO_LOOP_REQUIRED_SURFACES,
)
from ultimate_ai_agent.core.intent import (
    USER_INTENT_UNDERSTANDING_CONTRACT_REF,
    USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS,
    USER_INTENT_UNDERSTANDING_REQUIRED_DEPENDENCY_REFS,
    USER_INTENT_UNDERSTANDING_REQUIRED_REF_FIELDS,
    USER_INTENT_UNDERSTANDING_REQUIRED_SURFACES,
    USER_INTENT_UNDERSTANDING_ROUTING_DECISIONS,
)
from ultimate_ai_agent.core.readiness import (
    PRIVATE_BETA_READINESS_ACCEPTANCE_STATES,
    PRIVATE_BETA_READINESS_CONTRACT_REF,
    PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS,
    PRIVATE_BETA_READINESS_REQUIRED_REF_FIELDS,
    PRIVATE_BETA_READINESS_REQUIRED_SURFACES,
)
from ultimate_ai_agent.core.storage import (
    BUSINESS_MEMORY_QUALITY_CONTRACT_REF,
    EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF,
    MEMORY_REVIEW_DECISION_CONTRACT_REF,
    MEMORY_SOURCE_PROVENANCE_CONTRACT_REF,
    PLANS_ACTION_ENVELOPE_CONTRACT_REF,
    TODAY_PRODUCT_SPINE_CONTRACT_REF,
)


client = TestClient(app)


def test_control_center_founder_loop_routes_are_in_manifest_with_local_state_class(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    manifest = build_api_manifest(app)
    routes = {route.path: route for route in manifest.routes}

    assert manifest.route_count == 127
    for path in [
        "/control-center/today/summary",
        "/control-center/actions/inbox",
        "/control-center/actions/{action_id}/receipt",
        "/control-center/evidence/timeline",
        "/control-center/memory/review",
        "/control-center/morning-briefing/summary",
        "/control-center/storage/status",
    ]:
        assert path in routes
        assert routes[path].method == "GET"
        assert routes[path].side_effect_class == "local_dev_workspace_only"
        assert routes[path].operation_id.startswith("get_control_center_")
        assert routes[path].route_classification == "local_sensitive"

    for path in [
        "/control-center/actions/{action_id}/approve",
        "/control-center/actions/{action_id}/edit",
        "/control-center/actions/{action_id}/reject",
        "/control-center/actions/{action_id}/defer",
    ]:
        assert path in routes
        assert routes[path].method == "POST"
        assert routes[path].side_effect_class == "local_dev_workspace_only"
        assert routes[path].route_classification == "mutating_requires_authority"
        assert routes[path].approval_posture == "required_before_mutation_authority"
        assert routes[path].idempotency_required is True
        assert routes[path].rate_limit_group == "action_decision"

    for path in [
        "/control-center/memory/review/{candidate_ref}/accept",
        "/control-center/memory/review/{candidate_ref}/correct",
        "/control-center/memory/review/{candidate_ref}/reject",
    ]:
        assert path in routes
        assert routes[path].method == "POST"
        assert routes[path].side_effect_class == "local_dev_workspace_only"
        assert routes[path].route_classification == "mutating_requires_authority"
        assert routes[path].approval_posture == "required_before_mutation_authority"
        assert routes[path].idempotency_required is True
        assert routes[path].rate_limit_group == "memory_review_decision"

    assert (
        "control_center_founder_loop_storage_summaries"
        in manifest.capabilities_declared
    )
    assert (
        "control_center_action_decision_state_machine"
        in manifest.capabilities_declared
    )
    assert (
        "control_center_memory_review_decision_receipts"
        in manifest.capabilities_declared
    )
    assert (
        "control_center_evidence_timeline_productization"
        in manifest.capabilities_declared
    )
