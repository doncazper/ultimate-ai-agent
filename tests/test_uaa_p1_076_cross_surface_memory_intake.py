import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.memory import (
    BUSINESS_MEMORY_QUALITY_CONTRACT_REF,
    CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF,
    CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS,
    CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_REF_FIELDS,
    CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES,
    MEMORY_REVIEW_DECISION_CONTRACT_REF,
    MEMORY_SOURCE_PROVENANCE_CONTRACT_REF,
    MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE,
    CrossSurfaceMemoryIntakeProposal,
    build_cross_surface_memory_intake_proposal,
    cross_surface_memory_intake_authority_posture,
    cross_surface_memory_intake_proposals,
    cross_surface_memory_intake_surface_bindings,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


DENIED_FLAGS = [
    "memory_write_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "provider_call_enabled",
    "account_fetch_enabled",
    "browser_import_enabled",
    "shell_history_import_enabled",
    "raw_file_import_enabled",
    "connector_runtime_enabled",
    "source_truth_authority",
    "accepted_as_recall",
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_authority_enabled",
]

EXPECTED_SOURCE_BY_SURFACE = {
    "Today": "evidence_timeline_ref",
    "Chat": "local_chat_summary",
    "Plans": "task_plan",
    "Actions": "action_proposal",
    "Evidence": "evidence_timeline_ref",
    "Local Coding": "local_coding_summary",
    "External Assistant Review": "external_assistant_review_summary",
}

EXPECTED_CANDIDATE_BY_SURFACE = {
    "Today": "follow_up",
    "Chat": "preference",
    "Plans": "decision",
    "Actions": "commitment",
    "Evidence": "decision",
    "Local Coding": "project",
    "External Assistant Review": "opportunity",
}


def test_cross_surface_memory_intake_proposals_are_review_only() -> None:
    proposals = cross_surface_memory_intake_proposals()
    payloads = [proposal.model_dump(mode="json") for proposal in proposals]

    assert [payload["surface"] for payload in payloads] == (
        CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES
    )
    for payload in payloads:
        surface = payload["surface"]
        assert payload["contract_ref"] == CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF
        assert payload["source_kind"] == EXPECTED_SOURCE_BY_SURFACE[surface]
        assert payload["candidate_kind"] == EXPECTED_CANDIDATE_BY_SURFACE[surface]
        assert payload["proposal_ref"].startswith("memory-intake-proposal:")
        assert payload["candidate_ref"].startswith("business-memory-candidate:")
        assert payload["review_queue_ref"].startswith("memory-review-queue-ref:")
        assert payload["source_provenance_contract_ref"] == (
            MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
        )
        assert payload["memory_review_decision_contract_ref"] == (
            MEMORY_REVIEW_DECISION_CONTRACT_REF
        )
        assert payload["business_memory_quality_contract_ref"] == (
            BUSINESS_MEMORY_QUALITY_CONTRACT_REF
        )
        assert payload["source_trust_posture"] == MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE
        assert payload["source_refs"]
        assert payload["provenance_refs"]
        assert payload["evidence_refs"]
        assert payload["missing_evidence_refs"]
        assert payload["missing_evidence_posture"] == (
            "missing_safe_evidence_until_reviewed"
        )
        assert payload["confidence_posture"] == "low_confidence_until_reviewed"
        assert payload["stale_state"] == "recheck_source_refs_before_memory_intake"
        assert payload["review_required"] is True
        assert payload["safe_summary_only"] is True
        assert payload["source_payload_storage_allowed"] is False
        assert set(CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS) <= set(
            payload["blocked_state_refs"]
        )

        for denied_flag in DENIED_FLAGS:
            assert payload[denied_flag] is False
            unsafe = dict(payload)
            unsafe[denied_flag] = True
            with pytest.raises(ValidationError):
                CrossSurfaceMemoryIntakeProposal(**unsafe)


def test_cross_surface_memory_intake_rejects_unsafe_or_mismatched_payloads() -> None:
    payload = build_cross_surface_memory_intake_proposal(
        surface="Chat"
    ).model_dump(mode="json")

    unsafe = dict(payload)
    unsafe["safe_summary"] = "raw file material"
    with pytest.raises(ValidationError):
        CrossSurfaceMemoryIntakeProposal(**unsafe)

    mismatched_source = dict(payload)
    mismatched_source["source_kind"] = "task_plan"
    with pytest.raises(ValidationError):
        CrossSurfaceMemoryIntakeProposal(**mismatched_source)

    mismatched_candidate = dict(payload)
    mismatched_candidate["candidate_kind"] = "decision"
    with pytest.raises(ValidationError):
        CrossSurfaceMemoryIntakeProposal(**mismatched_candidate)

    missing_blocker = dict(payload)
    missing_blocker["blocked_state_refs"] = [
        ref
        for ref in payload["blocked_state_refs"]
        if ref != "blocked-state:no-context-injection"
    ]
    with pytest.raises(ValidationError):
        CrossSurfaceMemoryIntakeProposal(**missing_blocker)


def test_cross_surface_memory_intake_posture_and_surface_bindings() -> None:
    posture = cross_surface_memory_intake_authority_posture()
    bindings = {
        binding["surface"]: binding
        for binding in cross_surface_memory_intake_surface_bindings()
    }

    assert posture["safe_refs_only"] is True
    assert posture["review_required"] is True
    assert posture["safe_summary_only"] is True
    assert posture["source_payload_storage_allowed"] is False
    for denied_flag in DENIED_FLAGS:
        assert posture[denied_flag] is False

    assert set(bindings) == set(CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES)
    assert bindings["Local Coding"]["feed_ref"] == (
        "memory-intake-proposal:local-coding"
    )
    assert bindings["External Assistant Review"]["feed_status"] == (
        "implemented_memory_intake_proposal_refs"
    )


def test_founder_loop_today_binds_cross_surface_memory_intake(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path, seed_defaults=True)
    today = repo.today_summary()

    assert (
        today["cross_surface_memory_intake_contract_ref"]
        == CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF
    )
    assert today["cross_surface_memory_intake_required_surfaces"] == (
        CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES
    )
    assert today["cross_surface_memory_intake_required_ref_fields"] == (
        CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_REF_FIELDS
    )
    assert today["cross_surface_memory_intake_proposal_count"] == len(
        CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES
    )
    assert set(CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS) <= set(
        today["cross_surface_memory_intake_blocked_state_refs"]
    )
    assert {
        proposal["surface"]
        for proposal in today["cross_surface_memory_intake_proposals"]
    } == set(CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_SURFACES)

    module_feeds = {item["module"]: item for item in today["module_feed_contract"]}
    assert module_feeds["Memory"]["status"] == (
        "implemented_review_queue_quality_intake_and_loop_binding_contract"
    )
    assert CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF in module_feeds["Memory"][
        "current_feed_refs"
    ]

    timeline_item = next(
        item
        for item in today["evidence_timeline"]
        if item["item_kind"] == "cross_surface_memory_intake_proposal_ref"
    )
    assert CROSS_SURFACE_MEMORY_INTAKE_CONTRACT_REF in timeline_item["status_refs"]
    assert MEMORY_SOURCE_PROVENANCE_CONTRACT_REF in timeline_item["status_refs"]
    assert MEMORY_REVIEW_DECISION_CONTRACT_REF in timeline_item["status_refs"]
    assert BUSINESS_MEMORY_QUALITY_CONTRACT_REF in timeline_item["status_refs"]
    assert timeline_item["history_answers"]["approved"]["status"] == "blocked"
    assert timeline_item["history_answers"]["happened"]["status"] == (
        "proposal_refs_only"
    )
    assert "Seven review-only memory intake candidates" in (
        timeline_item["history_answers"]["proposed"]["answer"]
    )
    assert timeline_item["approval_ref_authority"] is False
    assert timeline_item["rollback_execution_enabled"] is False
    assert timeline_item["memory_truth_authority"] is False
    assert timeline_item["context_injection_authorized"] is False
    assert timeline_item["raw_evidence_included"] is False
    assert set(CROSS_SURFACE_MEMORY_INTAKE_REQUIRED_BLOCKED_REFS) <= set(
        timeline_item["blocked_states"]
    )

    serialized = json.dumps(today, sort_keys=True).lower()
    for forbidden in [
        "raw prompt",
        "raw response",
        "provider payload",
        "api key",
        "/users/",
        "/home/",
        "/var/",
        "/etc/",
    ]:
        assert forbidden not in serialized
