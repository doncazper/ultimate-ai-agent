import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.intent import (
    USER_INTENT_UNDERSTANDING_CONTRACT_REF,
    USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS,
    USER_INTENT_UNDERSTANDING_REQUIRED_DEPENDENCY_REFS,
    USER_INTENT_UNDERSTANDING_REQUIRED_REF_FIELDS,
    USER_INTENT_UNDERSTANDING_REQUIRED_SURFACES,
    USER_INTENT_UNDERSTANDING_ROUTING_DECISIONS,
    ReviewableUserIntentProposal,
    UserIntentUnderstandingContract,
    build_user_intent_understanding_contract,
    user_intent_understanding_authority_posture,
    user_intent_understanding_surface_bindings,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


DENIED_FLAGS = [
    "hidden_authority_enabled",
    "acts_without_review",
    "action_execution_enabled",
    "approval_grant_capture_enabled",
    "memory_write_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "tool_execution_enabled",
    "provider_model_authority_allowed",
    "connector_write_enabled",
    "shell_subprocess_execution_enabled",
    "code_apply_execution_enabled",
    "broad_autonomy_enabled",
    "public_beta_claim_enabled",
    "production_authority_enabled",
]


def test_user_intent_contract_defines_reviewable_taxonomy() -> None:
    contract = build_user_intent_understanding_contract()
    payload = contract.model_dump(mode="json")

    assert payload["contract_ref"] == USER_INTENT_UNDERSTANDING_CONTRACT_REF
    assert payload["required_surfaces"] == USER_INTENT_UNDERSTANDING_REQUIRED_SURFACES
    assert payload["routing_decisions"] == USER_INTENT_UNDERSTANDING_ROUTING_DECISIONS
    assert (
        payload["required_dependency_refs"]
        == USER_INTENT_UNDERSTANDING_REQUIRED_DEPENDENCY_REFS
    )
    assert payload["required_ref_fields"] == USER_INTENT_UNDERSTANDING_REQUIRED_REF_FIELDS
    assert {proposal["routing_decision"] for proposal in payload["proposals"]} >= {
        "ask",
        "act",
        "defer",
    }
    assert {proposal["confidence_band"] for proposal in payload["proposals"]} >= {
        "high",
        "medium",
        "low",
        "conflicting",
    }
    assert set(USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS) <= set(
        payload["blocked_state_refs"]
    )
    assert payload["authority_posture"] == user_intent_understanding_authority_posture()
    assert {
        binding["surface"] for binding in user_intent_understanding_surface_bindings()
    } == set(USER_INTENT_UNDERSTANDING_REQUIRED_SURFACES)
    for denied_flag in DENIED_FLAGS:
        assert payload[denied_flag] is False
        assert payload["authority_posture"][denied_flag] is False


def test_user_intent_low_confidence_or_conflict_asks_user() -> None:
    contract = build_user_intent_understanding_contract()
    payload = contract.model_dump(mode="json")
    low_or_conflicting = [
        proposal
        for proposal in payload["proposals"]
        if proposal["confidence_band"] in {"low", "conflicting"}
    ]

    assert low_or_conflicting
    for proposal in low_or_conflicting:
        assert proposal["routing_decision"] == "ask"
        assert proposal["ask_user_question_ref"]
        assert proposal["action_execution_enabled"] is False
        assert proposal["acts_without_review"] is False

    unsafe = dict(low_or_conflicting[0])
    unsafe["routing_decision"] = "act"
    with pytest.raises(ValidationError):
        ReviewableUserIntentProposal(**unsafe)

    unsafe_conflict = dict(low_or_conflicting[-1])
    unsafe_conflict["conflict_refs"] = []
    with pytest.raises(ValidationError):
        ReviewableUserIntentProposal(**unsafe_conflict)


def test_user_intent_rejects_authority_creep_and_missing_dependencies() -> None:
    contract = build_user_intent_understanding_contract()
    payload = contract.model_dump(mode="json")

    unsafe = dict(payload)
    unsafe["action_execution_enabled"] = True
    with pytest.raises(ValidationError):
        UserIntentUnderstandingContract(**unsafe)

    unsafe_posture = dict(payload)
    unsafe_posture["authority_posture"] = dict(payload["authority_posture"])
    unsafe_posture["authority_posture"]["hidden_authority_enabled"] = True
    with pytest.raises(ValidationError):
        UserIntentUnderstandingContract(**unsafe_posture)

    missing_dependency = dict(payload["proposals"][0])
    missing_dependency["dependency_refs"] = []
    with pytest.raises(ValidationError):
        ReviewableUserIntentProposal(**missing_dependency)

    unsafe_text = dict(payload["proposals"][0])
    unsafe_text["safe_summary"] = "raw prompt material"
    with pytest.raises(ValidationError):
        ReviewableUserIntentProposal(**unsafe_text)


def test_founder_loop_surfaces_user_intent_without_authority(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path, seed_defaults=True)
    today = repo.today_summary()
    inbox = repo.actions_inbox()

    assert (
        today["user_intent_understanding_contract_ref"]
        == USER_INTENT_UNDERSTANDING_CONTRACT_REF
    )
    assert today["user_intent_required_surfaces"] == (
        USER_INTENT_UNDERSTANDING_REQUIRED_SURFACES
    )
    assert today["user_intent_routing_decisions"] == (
        USER_INTENT_UNDERSTANDING_ROUTING_DECISIONS
    )
    assert today["user_intent_proposal_count"] == len(
        today["user_intent_proposals"]
    )
    assert today["user_intent_low_confidence_asks_user"] is True
    assert today["user_intent_conflicting_intent_asks_user"] is True
    assert today["user_intent_hidden_authority_enabled"] is False
    assert today["user_intent_action_execution_enabled"] is False
    assert (
        today["user_intent_authority_posture"]["action_execution_enabled"] is False
    )
    assert set(USER_INTENT_UNDERSTANDING_REQUIRED_BLOCKED_REFS) <= set(
        today["user_intent_blocked_state_refs"]
    )

    intent_item = next(
        item
        for item in today["evidence_timeline"]
        if item["item_kind"] == "user_intent_understanding_proposal_ref"
    )
    assert USER_INTENT_UNDERSTANDING_CONTRACT_REF in intent_item["status_refs"]
    assert intent_item["history_answers"]["approved"]["status"] == "blocked"
    assert intent_item["approval_ref_authority"] is False
    assert intent_item["rollback_execution_enabled"] is False
    assert intent_item["memory_truth_authority"] is False
    assert intent_item["context_injection_authorized"] is False
    assert intent_item["raw_evidence_included"] is False

    assert (
        inbox["user_intent_understanding_contract_ref"]
        == USER_INTENT_UNDERSTANDING_CONTRACT_REF
    )
    assert inbox["user_intent_proposals"]
    assert inbox["user_intent_authority_posture"]["action_execution_enabled"] is False

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
