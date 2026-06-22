import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.memory import (
    MEMORY_DERIVED_ACTION_REQUIRED_REF_FIELDS,
    MEMORY_TO_LOOP_BINDING_CONTRACT_REF,
    MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS,
    MEMORY_TO_LOOP_REQUIRED_REF_FIELDS,
    MEMORY_TO_LOOP_REQUIRED_SURFACES,
    MemoryDerivedActionProposal,
    MemoryToLoopBindingItem,
    build_memory_derived_action_proposal,
    build_memory_to_loop_binding_item,
    memory_to_loop_authority_posture,
    memory_to_loop_surface_bindings,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


DENIED_FLAGS = [
    "memory_write_authorized",
    "automatic_recall_enabled",
    "context_injection_authorized",
    "approval_grant_capture_enabled",
    "action_execution_enabled",
    "connector_write_enabled",
    "account_sync_enabled",
    "source_truth_authority",
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_authority_enabled",
]


def test_memory_to_loop_binding_item_is_state_specific_and_review_only() -> None:
    item = build_memory_to_loop_binding_item(
        surface="Action Inbox",
        loop_binding_state="follow_up_commitment",
        memory_candidate_ref="business-memory-candidate:preference:sample",
        review_ref="memory-review:sample",
        safe_summary="Action Inbox shows reviewed memory state as safe refs only.",
        source_refs=["source-ref:manual-note:sample"],
        evidence_refs=["evidence-ref:memory-loop:sample"],
        missing_evidence_refs=["missing-evidence-ref:memory-loop:sample"],
        stale_state="recheck_memory_refs_before_loop_use",
        follow_up_commitment_refs=["follow-up-commitment-ref:sample"],
        next_safe_action="Review memory refs before any later scoped action.",
    )
    payload = item.model_dump(mode="json")

    assert payload["contract_ref"] == MEMORY_TO_LOOP_BINDING_CONTRACT_REF
    assert payload["loop_binding_state"] == "follow_up_commitment"
    assert payload["follow_up_commitment_refs"] == [
        "follow-up-commitment-ref:sample"
    ]
    assert payload["accepted_recall_refs"] == []
    assert payload["correction_refs"] == []
    assert set(MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS) <= set(
        payload["blocked_state_refs"]
    )
    for denied_flag in DENIED_FLAGS:
        assert payload[denied_flag] is False
        unsafe = dict(payload)
        unsafe[denied_flag] = True
        with pytest.raises(ValidationError):
            MemoryToLoopBindingItem(**unsafe)


def test_memory_to_loop_rejects_fake_or_unsafe_refs() -> None:
    base = build_memory_to_loop_binding_item(
        surface="Today",
        loop_binding_state="candidate",
        memory_candidate_ref="business-memory-candidate:preference:sample",
        review_ref="memory-review:sample",
        safe_summary="Today shows reviewed memory candidate refs only.",
        source_refs=["source-ref:manual-note:sample"],
        evidence_refs=["evidence-ref:memory-loop:sample"],
        missing_evidence_refs=["missing-evidence-ref:memory-loop:sample"],
        stale_state="recheck_memory_refs_before_loop_use",
        next_safe_action="Review candidate refs before any later memory action.",
    ).model_dump(mode="json")

    unsafe = dict(base)
    unsafe["safe_summary"] = "raw prompt material"
    with pytest.raises(ValidationError):
        MemoryToLoopBindingItem(**unsafe)

    missing_follow_up = dict(base)
    missing_follow_up["loop_binding_state"] = "follow_up_commitment"
    with pytest.raises(ValidationError):
        MemoryToLoopBindingItem(**missing_follow_up)


def test_memory_derived_action_proposal_names_scope_and_denies_authority() -> None:
    proposal = build_memory_derived_action_proposal(
        proposal_ref="memory-derived-action-proposal:sample",
        source_memory_ref="business-memory-candidate:preference:sample",
        source_loop_item_ref="memory-loop-binding:today:sample",
        source_review_ref="memory-review:sample",
        source_intake_proposal_ref="memory-intake-proposal:today",
        safe_summary="A memory-derived follow-up can be reviewed only.",
        source_refs=["source-ref:manual-note:sample"],
        provenance_refs=["provenance-ref:manual-note:sample"],
        evidence_refs=["evidence-ref:memory-loop:sample"],
        missing_evidence_refs=["missing-evidence-ref:memory-loop:sample"],
        next_safe_action="Review in Action Inbox before any scoped mutation.",
    ).model_dump(mode="json")

    assert proposal["source_loop_item_ref"] == "memory-loop-binding:today:sample"
    assert proposal["source_review_ref"] == "memory-review:sample"
    assert proposal["approval_required"] is True
    assert proposal["approval_requirement_ref"].startswith("approval-requirement:")
    assert proposal["action_envelope_ref"].startswith("action-envelope:")
    assert proposal["scope_ref"].startswith("scope-ref:")
    assert proposal["expected_receipt_refs"]
    for denied_flag in DENIED_FLAGS:
        assert proposal[denied_flag] is False
        unsafe = dict(proposal)
        unsafe[denied_flag] = True
        with pytest.raises(ValidationError):
            MemoryDerivedActionProposal(**unsafe)


def test_founder_loop_today_and_actions_bind_memory_to_loop(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path, seed_defaults=True)
    today = repo.today_summary()
    inbox = repo.actions_inbox()

    assert today["memory_to_loop_binding_contract_ref"] == (
        MEMORY_TO_LOOP_BINDING_CONTRACT_REF
    )
    assert today["memory_to_loop_required_surfaces"] == (
        MEMORY_TO_LOOP_REQUIRED_SURFACES
    )
    assert today["memory_to_loop_required_ref_fields"] == (
        MEMORY_TO_LOOP_REQUIRED_REF_FIELDS
    )
    assert today["memory_derived_action_required_ref_fields"] == (
        MEMORY_DERIVED_ACTION_REQUIRED_REF_FIELDS
    )
    assert set(MEMORY_TO_LOOP_REQUIRED_BLOCKED_REFS) <= set(
        today["memory_to_loop_blocked_state_refs"]
    )
    assert today["memory_to_loop_item_count"] == len(
        MEMORY_TO_LOOP_REQUIRED_SURFACES
    )
    assert {
        item["surface"] for item in today["memory_to_loop_items"]
    } == set(MEMORY_TO_LOOP_REQUIRED_SURFACES)
    assert {
        item["loop_binding_state"] for item in today["memory_to_loop_items"]
    } >= {"candidate", "follow_up_commitment", "missing_evidence_blocker", "stale"}
    assert today["accepted_recall_refs"]
    assert today["correction_refs"]
    assert today["rejected_item_refs"]
    assert today["follow_up_commitment_refs"]
    assert today["stale_memory_refs"]
    assert today["missing_evidence_blocker_refs"]
    assert today["memory_derived_action_proposal_refs"]
    assert today["weekly_ceo_review_summary"]["weekly_review_ref"] == (
        "weekly-review-ref:memory-to-loop-binding"
    )
    assert today["memory_to_loop_authority_posture"] == (
        memory_to_loop_authority_posture()
    )
    assert {
        binding["surface"] for binding in memory_to_loop_surface_bindings()
    } == set(MEMORY_TO_LOOP_REQUIRED_SURFACES)
    for denied_flag in DENIED_FLAGS:
        assert today["memory_to_loop_authority_posture"][denied_flag] is False

    memory_loop_item = next(
        item
        for item in today["evidence_timeline"]
        if item["item_kind"] == "memory_to_loop_binding_ref"
    )
    assert MEMORY_TO_LOOP_BINDING_CONTRACT_REF in memory_loop_item["status_refs"]
    assert memory_loop_item["history_answers"]["approved"]["status"] == "blocked"
    assert memory_loop_item["memory_truth_authority"] is False
    assert memory_loop_item["context_injection_authorized"] is False
    assert memory_loop_item["approval_ref_authority"] is False
    assert memory_loop_item["rollback_execution_enabled"] is False
    assert memory_loop_item["raw_evidence_included"] is False

    assert inbox["memory_to_loop_binding_contract_ref"] == (
        MEMORY_TO_LOOP_BINDING_CONTRACT_REF
    )
    assert inbox["memory_derived_action_proposals"]
    action_proposal = inbox["memory_derived_action_proposals"][0]
    assert action_proposal["source_refs"]
    assert action_proposal["evidence_refs"]
    assert action_proposal["side_effect_class"] == "local_dev_workspace_only"
    assert action_proposal["approval_posture"]
    assert action_proposal["next_safe_action"]
    assert action_proposal["action_execution_enabled"] is False

    serialized = json.dumps(today, sort_keys=True).lower()
    for forbidden in [
        "raw prompt",
        "raw response",
        "provider payload",
        "raw log",
        "api key",
        "/users/",
        "/home/",
        "/var/",
        "/etc/",
    ]:
        assert forbidden not in serialized
