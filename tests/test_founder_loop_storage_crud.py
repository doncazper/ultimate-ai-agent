# ruff: noqa: F401
from pathlib import Path
import json

import pytest

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
    FOUNDER_LOOP_SCHEMA_VERSION,
    MEMORY_REVIEW_DECISION_CONTRACT_REF,
    MEMORY_SOURCE_PROVENANCE_CONTRACT_REF,
    PLANS_ACTION_ENVELOPE_CONTRACT_REF,
    TODAY_PRODUCT_SPINE_CONTRACT_REF,
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
    JsonlLogKind,
)
from ultimate_ai_agent.core.storage.founder_loop import (
    FounderLoopActionRecord,
    FounderLoopBriefingRecord,
    FounderLoopEvidenceTimelineItem,
    FounderLoopMemoryReviewRecord,
)


HISTORY_KEYS = {
    "proposed",
    "approved",
    "happened",
    "changed",
    "undoable",
    "stale",
    "blocked",
}


def _history_answers() -> dict[str, dict[str, object]]:
    return {
        key: {
            "question": f"What is {key}?",
            "answer": f"Safe redacted answer for {key}.",
            "refs": [f"status-ref:test-{key}"],
            "status": "present",
        }
        for key in HISTORY_KEYS
    }


def test_founder_loop_repository_crud_and_idempotency_denial(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop", seed_defaults=False)

    repo.upsert_action(
        FounderLoopActionRecord(
            item_ref="founder-action:test-review",
            title="Review storage-backed action",
            safe_summary="Bounded summary for a review-only action inbox item.",
            surface="Actions",
            evidence_refs=["evidence-ref:founder-loop:test-review"],
        )
    )
    repo.record_idempotency_key(
        key_ref="idempotency-ref:founder-loop:test",
        scope_ref="approval-scope:founder-loop:test",
        receipt_ref="receipt-ref:founder-loop:test",
    )

    inbox = repo.actions_inbox()
    assert inbox["user_intent_understanding_contract_ref"] == (
        USER_INTENT_UNDERSTANDING_CONTRACT_REF
    )
    assert inbox["user_intent_proposals"]
    assert (
        inbox["user_intent_authority_posture"]["low_confidence_asks_user"] is True
    )
    assert inbox["user_intent_authority_posture"]["action_execution_enabled"] is False
    assert set(USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS) <= set(
        inbox["user_intent_blocked_state_refs"]
    )
    assert inbox["items"][0]["item_ref"] == "founder-action:test-review"
    assert (
        inbox["items"][0]["approval_envelope_status"] == "missing_until_scoped_contract"
    )
    assert (
        inbox["items"][0]["state_change_readiness"]
        == "blocked_missing_backend_contract"
    )
    assert inbox["items"][0]["receipt_refs"] == []
    assert inbox["items"][0]["audit_refs"] == []
    assert inbox["items"][0]["idempotency_key_ref"] is None
    assert inbox["items"][0]["rollback_ref"] is None
    assert inbox["items"][0]["safe_disable_ref"] is None
    approval_envelope = inbox["items"][0]["approval_envelope"]
    assert approval_envelope["backend_owned"] is True
    assert approval_envelope["action_kind"] == "review_only"
    assert approval_envelope["exact_scope"] == "missing"
    assert approval_envelope["approval_requirement"] == "missing"
    assert approval_envelope["idempotency_ref"] == "missing"
    assert approval_envelope["expected_receipt_refs"] == ["missing"]
    assert "evidence-ref:founder-loop:test-review" in approval_envelope["evidence_refs"]
    assert "exact_scope:missing" in approval_envelope["missing_field_states"]
    assert "approval_requirement:missing" in approval_envelope["missing_field_states"]
    assert "idempotency_ref:missing" in approval_envelope["missing_field_states"]
    receipt_visibility = inbox["items"][0]["receipt_visibility"]
    assert receipt_visibility["backend_owned"] is True
    assert receipt_visibility["decision_receipt_ref"] == "pending"
    assert receipt_visibility["local_task_ref"] == "not_applicable"
    assert receipt_visibility["local_task_commit_receipt_ref"] == "not_applicable"
    assert receipt_visibility["evidence_timeline_event_ref"] == "pending"
    assert receipt_visibility["replay_posture"] == "pending"
    assert receipt_visibility["conflict_posture"] == "pending"
    assert "decision_receipt_ref:pending" in receipt_visibility[
        "missing_field_states"
    ]
    assert repo.storage_status()["counts"]["idempotency_keys"] == 1

    with pytest.raises(FounderLoopStorageDuplicateError):
        repo.record_idempotency_key(
            key_ref="idempotency-ref:founder-loop:test",
            scope_ref="approval-scope:founder-loop:test",
            receipt_ref="receipt-ref:founder-loop:test",
        )
