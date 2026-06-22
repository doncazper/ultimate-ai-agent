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


def test_founder_loop_jsonl_logs_are_append_only_and_redacted(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop", seed_defaults=False)

    result = repo.append_log(
        JsonlLogKind.audit,
        {
            "event_ref": "founder-loop-event:audit-test",
            "safe_summary": "Redacted audit event for storage verifier.",
            "evidence_refs": ["evidence-ref:founder-loop:audit-test"],
        },
    )

    assert result == {
        "log_ref": "founder-loop-log:audit",
        "event_ref": "founder-loop-event:audit-test",
    }
    log_path = tmp_path / "founder_loop" / "logs" / "audit.jsonl"
    first = log_path.read_text(encoding="utf-8")
    repo.append_log(
        JsonlLogKind.audit,
        {
            "event_ref": "founder-loop-event:audit-test-two",
            "safe_summary": "Second redacted audit event for storage verifier.",
            "evidence_refs": ["evidence-ref:founder-loop:audit-test-two"],
        },
    )
    second = log_path.read_text(encoding="utf-8")

    assert second.startswith(first)
    assert len(second.splitlines()) == 2
    assert str(tmp_path) not in second
    assert "raw_prompt" not in second
    assert "provider_payload" not in second


def test_founder_loop_storage_rejects_unsafe_payload_language(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop", seed_defaults=False)

    with pytest.raises(ValueError):
        repo.upsert_action(
            FounderLoopActionRecord(
                item_ref="founder-action:unsafe",
                title="Unsafe action",
                safe_summary="This includes raw_prompt material and must be denied.",
                surface="Actions",
                evidence_refs=["evidence-ref:founder-loop:unsafe"],
            )
        )


def test_founder_loop_evidence_timeline_rejects_unsafe_content() -> None:
    with pytest.raises(ValueError):
        FounderLoopEvidenceTimelineItem(
            timeline_item_ref="evidence-timeline:unsafe/test",
            item_kind="unsafe_evidence_ref",
            title="Unsafe evidence",
            safe_summary="This includes raw_prompt material and must be denied.",
            history_answers=_history_answers(),
            source_refs=["evidence-ref:founder-loop:unsafe"],
            status_refs=["status-ref:founder-loop:unsafe"],
            authority_posture="Review-only evidence posture.",
            next_safe_action="Keep unsafe evidence blocked.",
        )


@pytest.mark.parametrize(
    "unsafe_update",
    [
        {"approval_ref_authority": True},
        {"rollback_execution_enabled": True},
        {"memory_truth_authority": True},
        {"context_injection_authorized": True},
        {"raw_evidence_included": True},
    ],
)
def test_founder_loop_evidence_timeline_rejects_authority_creep(
    unsafe_update: dict[str, bool],
) -> None:
    with pytest.raises(ValueError):
        FounderLoopEvidenceTimelineItem(
            timeline_item_ref="evidence-timeline:unsafe/authority",
            item_kind="unsafe_authority_ref",
            title="Unsafe authority",
            safe_summary="Safe summary for rejected authority posture.",
            history_answers=_history_answers(),
            source_refs=["evidence-ref:founder-loop:unsafe-authority"],
            status_refs=["status-ref:founder-loop:unsafe-authority"],
            authority_posture="Review-only evidence posture.",
            next_safe_action="Keep unsafe authority blocked.",
            **unsafe_update,
        )
