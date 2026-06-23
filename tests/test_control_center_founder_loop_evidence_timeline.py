from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.code import (
    GOVERNED_CODE_WORKBENCH_CONTRACT_REF,
    GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS,
)
from ultimate_ai_agent.core.intent import (
    USER_INTENT_UNDERSTANDING_CONTRACT_REF,
    USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS,
)
from ultimate_ai_agent.core.memory import (
    CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF,
    CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS,
    MEMORY_TO_LOOP_BINDING_CONTRACT_REF,
    MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS,
)
from ultimate_ai_agent.core.readiness import (
    PRIVATE_BETA_READINESS_CONTRACT_REF,
    PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS,
)
from ultimate_ai_agent.core.storage import (
    EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF,
    PLANS_ACTION_ENVELOPE_CONTRACT_REF,
)


client = TestClient(app)


def test_control_center_founder_loop_evidence_timeline_is_safe_and_bound() -> None:
    today = client.get("/control-center/today/summary").json()["data"]
    timeline = today["evidence_timeline"]
    assert today["evidence_timeline_status"] == "implemented_productized_evidence_timeline_safe_refs_only"
    assert timeline
    for item in timeline:
        assert item["history_contract_ref"] == EVIDENCE_HISTORY_GRAMMAR_CONTRACT_REF
        assert set(item["history_answers"]) == set(
            today["evidence_history_required_states"]
        )
        assert item["approval_ref_authority"] is False
        assert item["rollback_execution_enabled"] is False
        assert item["memory_truth_authority"] is False
        assert item["context_injection_authorized"] is False
        assert item["raw_evidence_included"] is False

    action_history = next(
        item for item in timeline if item["item_kind"] == "receipt_audit_rollback_ref"
    )["history_answers"]
    assert "identifiers, not authority" in action_history["approved"]["answer"]
    assert "do not execute rollback" in action_history["undoable"]["answer"]

    plan_history_item = next(
        item for item in timeline if item["item_kind"] == "plan_action_envelope_ref"
    )
    assert PLANS_ACTION_ENVELOPE_CONTRACT_REF in plan_history_item["status_refs"]
    assert (
        "reviewable Action envelope"
        in plan_history_item["history_answers"]["proposed"]["answer"]
    )
    assert plan_history_item["receipt_refs"] == [
        "receipt-plan:plans-action-envelope:plan-summary-founder-loop-v1"
    ]
    assert (
        "blocked-state:no-approval-grant-capture"
        in plan_history_item["blocked_states"]
    )

    code_history_item = next(
        item
        for item in timeline
        if item["item_kind"] == "governed_code_workbench_proposal_ref"
    )
    assert GOVERNED_CODE_WORKBENCH_CONTRACT_REF in code_history_item["status_refs"]
    assert (
        today["governed_code_workbench_safe_diff_summary_ref"]
        in code_history_item["status_refs"]
    )
    assert (
        today["governed_code_workbench_expected_apply_receipt_ref"]
        in code_history_item["receipt_refs"]
    )
    assert (
        "no files were changed"
        in code_history_item["history_answers"]["happened"]["answer"]
    )
    assert code_history_item["history_answers"]["approved"]["status"] == "blocked"
    assert code_history_item["approval_ref_authority"] is False
    assert code_history_item["rollback_execution_enabled"] is False
    assert set(GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS) <= set(
        code_history_item["blocked_states"]
    )

    memory_intake_item = next(
        item
        for item in timeline
        if item["item_kind"] == "cross_surface_memory_intake_proposal_ref"
    )
    assert CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF in memory_intake_item[
        "status_refs"
    ]
    assert memory_intake_item["history_answers"]["approved"]["status"] == "blocked"
    assert "Only safe memory intake proposal metadata" in (
        memory_intake_item["history_answers"]["happened"]["answer"]
    )
    assert memory_intake_item["memory_truth_authority"] is False
    assert memory_intake_item["context_injection_authorized"] is False
    assert set(CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS) <= set(
        memory_intake_item["blocked_states"]
    )
    memory_loop_item = next(
        item
        for item in timeline
        if item["item_kind"] == "memory_to_loop_binding_ref"
    )
    assert MEMORY_TO_LOOP_BINDING_CONTRACT_REF in memory_loop_item["status_refs"]
    assert memory_loop_item["history_answers"]["approved"]["status"] == "blocked"
    assert memory_loop_item["memory_truth_authority"] is False
    assert memory_loop_item["context_injection_authorized"] is False
    assert memory_loop_item["approval_ref_authority"] is False
    assert memory_loop_item["rollback_execution_enabled"] is False
    assert set(MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS) <= set(
        memory_loop_item["blocked_states"]
    )
    private_beta_item = next(
        item
        for item in timeline
        if item["item_kind"] == "private_beta_readiness_gate_ref"
    )
    assert PRIVATE_BETA_READINESS_CONTRACT_REF in private_beta_item["status_refs"]
    assert private_beta_item["history_answers"]["approved"]["status"] == "blocked"
    assert private_beta_item["approval_ref_authority"] is False
    assert private_beta_item["rollback_execution_enabled"] is False
    assert private_beta_item["memory_truth_authority"] is False
    assert private_beta_item["context_injection_authorized"] is False
    assert set(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS) <= set(
        private_beta_item["blocked_states"]
    )
    user_intent_item = next(
        item
        for item in timeline
        if item["item_kind"] == "user_intent_understanding_proposal_ref"
    )
    assert USER_INTENT_UNDERSTANDING_CONTRACT_REF in user_intent_item["status_refs"]
    assert user_intent_item["history_answers"]["approved"]["status"] == "blocked"
    assert user_intent_item["approval_ref_authority"] is False
    assert user_intent_item["rollback_execution_enabled"] is False
    assert set(USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS) <= set(
        user_intent_item["blocked_states"]
    )
