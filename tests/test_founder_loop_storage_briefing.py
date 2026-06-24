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


def test_founder_loop_briefing_defaults_are_blocked_and_read_only(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop", seed_defaults=False)

    repo.upsert_briefing_item(
        FounderLoopBriefingRecord(
            briefing_ref="briefing:test-review",
            title="Briefing review",
            safe_summary="Bounded briefing summary for a local review-only item.",
            evidence_refs=["evidence-ref:founder-loop:test-briefing"],
        )
    )

    briefing = repo.morning_briefing()
    item = briefing["items"][0]
    assert briefing["refresh_enabled"] is False
    assert briefing["notification_delivery_enabled"] is False
    assert briefing["daily_loop_summary"]["home_surface"] == "Morning Briefing"
    assert briefing["daily_loop_summary"]["action_execution_enabled"] is False
    assert briefing["source_readiness_items"]
    assert {source["status"] for source in briefing["source_readiness_items"]} >= {
        "blocked",
        "not_configured",
        "metadata_only",
        "ready",
    }
    posture = briefing["source_readiness_posture"]
    assert posture["backend_owned"] is True
    assert posture["blocked_source_count"] >= 1
    assert posture["metadata_only_source_count"] >= 1
    assert posture["not_configured_source_count"] >= 1
    assert set(posture["supported_statuses"]) >= {
        "ready",
        "blocked",
        "missing",
        "metadata_only",
        "unavailable",
        "not_configured",
    }
    assert posture["connector_runtime_enabled"] is False
    assert posture["source_refresh_enabled"] is False
    assert briefing["daily_loop_sections"]
    assert {section["title"] for section in briefing["daily_loop_sections"]} >= {
        "Today priorities",
        "Blocked and missing sources",
        "CRM-lite follow-ups",
        "Memory why shown",
        "Review queue summary",
        "Dogfood capture",
    }
    assert briefing["dogfood_capture"]["local_private_only"] is True
    assert briefing["dogfood_capture"]["public_beta_claim_enabled"] is False
    assert briefing["dogfood_capture"]["action_execution_enabled"] is False
    assert briefing["weekly_review_narrative"]["status"] == "safe_ref_history_ready"
    assert item["briefing_ref"] == "briefing:test-review"
    assert item["priority"] == "medium"
    assert item["source_readiness"] == "blocked_missing_source_contract"
    assert item["source_refs"] == []
    assert item["missing_contract_refs"] == []
    assert item["blocked_states"] == []
    assert item["stale_state"] == "recheck_required_before_source_contract"
    assert "source connector evidence" in item["evidence_gap"]
    assert "read-only source contracts" in item["next_safe_action"]
