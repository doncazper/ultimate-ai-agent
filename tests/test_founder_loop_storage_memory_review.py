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


def test_founder_loop_memory_review_defaults_are_review_only(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop", seed_defaults=False)

    repo.upsert_memory_review(
        FounderLoopMemoryReviewRecord(
            review_ref="memory-review:test-review",
            title="Memory review",
            safe_summary="Bounded memory review summary for a local review-only item.",
            evidence_refs=["evidence-ref:founder-loop:test-memory"],
        )
    )

    today = repo.today_summary()
    item = today["memory_review_queue"][0]
    assert today["memory_review_route_ref"] == "/memory"
    assert today["memory_write_enabled"] is False
    assert today["memory_delete_enabled"] is False
    assert today["context_injection_enabled"] is False
    assert (
        "contract-ref:context-injection-missing"
        in (today["memory_review_missing_contract_refs"])
    )
    assert "no_background_sync" in today["memory_review_blocked_states"]
    assert item["review_ref"] == "memory-review:test-review"
    assert item["candidate_kind"] == "preference"
    assert item["priority"] == "medium"
    assert item["review_state"] == "review_needed"
    assert item["side_effect_class"] == "local_dev_workspace_only"
    assert "remain unscoped" in item["authority_boundary"]
    assert item["provenance_refs"] == []
    assert item["source_refs"] == []
    assert item["source_policy_ref"] == MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
    assert item["source_kind"] == "manual_note"
    assert item["source_refs_status"] == "missing_safe_source_refs"
    assert item["provenance_refs_status"] == "missing_provenance_refs"
    assert item["source_review_required"] is True
    assert item["source_trust_posture"] == "untrusted_until_reviewed"
    assert item["accepted_as_truth"] is False
    assert item["memory_write_authorized"] is False
    assert item["context_injection_authorized"] is False
    assert item["decision_contract_ref"] == MEMORY_REVIEW_DECISION_CONTRACT_REF
    assert item["decision_capture_status"] == "review_needed_no_decision_captured"
    assert item["decision_review_only"] is True
    assert item["memory_delete_authorized"] is False
    assert item["memory_export_authorized"] is False
    assert item["missing_contract_refs"] == []
    assert (
        item["correction_posture"] == "correction_requires_scoped_memory_write_contract"
    )
    assert item["rejection_posture"] == "rejection_is_review_state_only"
    assert item["retention_posture"] == "retention_policy_not_bound"
    assert item["delete_posture"] == "delete_execution_not_scoped"
    assert item["confidence_posture"] == "safe_summary_unverified"
    assert item["stale_state"] == "recheck_source_refs_before_memory_use"
    assert item["blocked_states"] == []
    assert "scoped memory policy milestone" in item["next_safe_action"]
