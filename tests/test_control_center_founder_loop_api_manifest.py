# ruff: noqa: F401
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from scripts.verification.api_routes import EXPECTED_ROUTE_COUNT

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

    assert manifest.route_count == EXPECTED_ROUTE_COUNT
    for path in [
        "/control-center/start-here/summary",
        "/control-center/today/summary",
        "/control-center/actions/inbox",
        "/control-center/actions/{action_id}/receipt",
        "/control-center/proof/index",
        "/control-center/proof/{proof_ref}",
        "/control-center/trust-authority/matrix",
        "/control-center/coding/session",
        "/control-center/coding/context",
        "/control-center/coding/patch-apply-readiness",
        "/control-center/coding/patch-proposal",
        "/control-center/coding/git-review",
        "/control-center/coding/test-command-readiness",
        "/control-center/evidence/timeline",
        "/control-center/memory/l1-index",
        "/control-center/memory/l2-index",
        "/control-center/memory/l3-index",
        "/control-center/memory/contradictions",
        "/control-center/memory/context-packs",
        "/control-center/memory/context-packs/{context_pack_ref}/preview",
        "/control-center/memory/observation-candidates",
        "/control-center/memory/probe",
        "/control-center/memory/review",
        "/control-center/memory/workbench",
        "/control-center/memory/search",
        "/control-center/morning-briefing/summary",
        "/control-center/storage/status",
    ]:
        assert path in routes
        assert routes[path].method == "GET"
        assert routes[path].side_effect_class == "local_dev_workspace_only"
        assert routes[path].operation_id.startswith("get_control_center_")
        assert routes[path].route_classification == "local_sensitive"

    expected_operation_ids = {
        "/control-center/start-here/summary": "get_control_center_start_here_summary",
        "/control-center/proof/index": "get_control_center_proof_index",
        "/control-center/proof/{proof_ref}": "get_control_center_proof_proof_ref",
        "/control-center/trust-authority/matrix": "get_control_center_trust_authority_matrix",
        "/control-center/coding/session": "get_control_center_coding_session",
        "/control-center/coding/context": "get_control_center_coding_context",
        "/control-center/coding/patch-apply-readiness": "get_control_center_coding_patch_apply_readiness",
        "/control-center/coding/patch-proposal": "get_control_center_coding_patch_proposal",
        "/control-center/coding/git-review": "get_control_center_coding_git_review",
        "/control-center/coding/test-command-readiness": "get_control_center_coding_test_command_readiness",
    }
    for path, operation_id in expected_operation_ids.items():
        assert path in routes
        assert routes[path].method == "GET"
        assert routes[path].side_effect_class == "local_dev_workspace_only"
        assert routes[path].operation_id == operation_id
        assert routes[path].approval_posture == "not_required_for_route_classification"
        assert routes[path].idempotency_required is False
        assert routes[path].protected_route is True
    settings_path = "/control-center/settings/status"
    assert settings_path in routes
    assert routes[settings_path].method == "GET"
    assert routes[settings_path].side_effect_class == "validation_only"
    assert routes[settings_path].operation_id == "get_control_center_settings_status"
    assert routes[settings_path].approval_posture == "not_required_for_route_classification"
    assert routes[settings_path].idempotency_required is False
    assert routes[settings_path].protected_route is True
    assert routes["/control-center/settings/status"].route_classification == (
        "local_readonly"
    )

    path = "/control-center/sources/readiness"
    assert path in routes
    assert routes[path].method == "GET"
    assert routes[path].operation_id == "get_control_center_sources_readiness"
    assert routes[path].side_effect_class == "local_dev_workspace_only"
    assert routes[path].route_classification == "local_readonly"
    assert routes[path].approval_posture == "not_required_for_route_classification"
    assert routes[path].idempotency_required is False
    assert routes[path].protected_route is True

    for path in [
        "/control-center/actions/{action_id}/approve",
        "/control-center/actions/{action_id}/edit",
        "/control-center/actions/{action_id}/reject",
        "/control-center/actions/{action_id}/defer",
        "/control-center/actions/{action_id}/local-task/commit",
    ]:
        assert path in routes
        assert routes[path].method == "POST"
        assert routes[path].side_effect_class == "local_dev_workspace_only"
        assert routes[path].route_classification == "mutating_requires_authority"
        assert routes[path].approval_posture == "required_before_mutation_authority"
        assert routes[path].idempotency_required is True
        assert routes[path].rate_limit_group == "action_decision"

    feedback_path = "/control-center/memory/feedback"
    assert feedback_path in routes
    assert routes[feedback_path].method == "POST"
    assert routes[feedback_path].side_effect_class == "local_dev_workspace_only"
    assert routes[feedback_path].route_classification == "mutating_requires_authority"
    assert routes[feedback_path].approval_posture == "required_before_mutation_authority"
    assert routes[feedback_path].idempotency_required is True
    assert routes[feedback_path].rate_limit_group == "memory_feedback"

    for path in [
        "/control-center/memory/review/{candidate_ref}/accept",
        "/control-center/memory/review/{candidate_ref}/correct",
        "/control-center/memory/review/{candidate_ref}/reject",
        "/control-center/memory/review/{candidate_ref}/defer",
        "/control-center/memory/review/{candidate_ref}/merge",
        "/control-center/memory/review/{candidate_ref}/supersede",
        "/control-center/memory/review/{candidate_ref}/forget-request",
        "/control-center/memory/review/manual-candidate",
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
        "control_center_action_local_task_commit"
        in manifest.capabilities_declared
    )
    assert (
        "control_center_memory_review_decision_receipts"
        in manifest.capabilities_declared
    )
    assert (
        "control_center_memory_l1_hot_local_index"
        in manifest.capabilities_declared
    )
    assert (
        "control_center_memory_context_pack_proposals"
        in manifest.capabilities_declared
    )
    assert (
        "control_center_memory_context_pack_previews"
        in manifest.capabilities_declared
    )
    assert (
        "control_center_memory_workbench_read_model"
        in manifest.capabilities_declared
    )
    assert (
        "control_center_memory_ranked_retrieval_read_model"
        in manifest.capabilities_declared
    )
    assert (
        "control_center_memory_search_filters"
        in manifest.capabilities_declared
    )
    assert (
        "control_center_manual_memory_candidate_intake"
        in manifest.capabilities_declared
    )
    assert (
        "control_center_memory_l2_factual_graph_temporal_index"
        in manifest.capabilities_declared
    )
    assert (
        "control_center_evidence_timeline_productization"
        in manifest.capabilities_declared
    )
    assert (
        "control_center_source_readiness_status"
        in manifest.capabilities_declared
    )
    assert (
        "control_center_coding_cockpit_session_read_model"
        in manifest.capabilities_declared
    )
    assert (
        "control_center_coding_context_pack_preview_read_model"
        in manifest.capabilities_declared
    )
    for blocked_capability in [
        "control_center_memory_ranked_retrieval_embeddings",
        "control_center_memory_ranked_retrieval_vector_db",
        "control_center_memory_ranked_retrieval_provider_calls",
        "control_center_memory_ranked_retrieval_context_injection",
        "control_center_memory_ranked_retrieval_memory_writes",
        "control_center_memory_ranked_retrieval_auto_maintenance",
        "control_center_memory_ranked_retrieval_action_execution",
        "control_center_memory_ranked_retrieval_connector_writes",
        "control_center_memory_ranked_retrieval_background_indexing",
        "control_center_memory_ranked_retrieval_truth_authority",
        "control_center_memory_ranked_retrieval_production_authority",
    ]:
        assert blocked_capability in manifest.capabilities_blocked
