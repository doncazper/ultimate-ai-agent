import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.readiness import (
    PRIVATE_BETA_READINESS_ACCEPTANCE_STATES,
    PRIVATE_BETA_READINESS_CONTRACT_REF,
    PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS,
    PRIVATE_BETA_READINESS_REQUIRED_REF_FIELDS,
    PRIVATE_BETA_READINESS_REQUIRED_SURFACES,
    PRIVATE_BETA_READINESS_SURFACE_BLOCKED_REFS,
    PrivateBetaReadinessCriterion,
    PrivateBetaReadinessGate,
    build_private_beta_readiness_gate,
    private_beta_readiness_authority_posture,
    private_beta_readiness_surface_bindings,
)
from ultimate_ai_agent.core.readiness.private_operator_trial import (
    PRIVATE_PRODUCT_LOOP_TRIAL_SCRIPT_CONTRACT_REF,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


DENIED_FLAGS = [
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_readiness_claim_enabled",
    "production_authority_enabled",
    "broad_autonomy_enabled",
    "connector_write_enabled",
    "provider_model_authority_allowed",
    "unrestricted_shell_enabled",
    "shell_subprocess_execution_enabled",
    "remote_execution_enabled",
    "account_sync_enabled",
    "crm_write_enabled",
    "memory_write_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "approval_grant_capture_enabled",
    "action_execution_enabled",
    "code_apply_execution_enabled",
]


def test_private_beta_readiness_gate_defines_local_acceptance_states() -> None:
    gate = build_private_beta_readiness_gate()
    payload = gate.model_dump(mode="json")

    assert payload["contract_ref"] == PRIVATE_BETA_READINESS_CONTRACT_REF
    assert payload["overall_gate_state"] == "partial"
    assert payload["required_surfaces"] == PRIVATE_BETA_READINESS_REQUIRED_SURFACES
    assert payload["acceptance_states"] == PRIVATE_BETA_READINESS_ACCEPTANCE_STATES
    assert payload["required_ref_fields"] == PRIVATE_BETA_READINESS_REQUIRED_REF_FIELDS
    assert (
        payload["product_loop_trial_script_ref"]
        == PRIVATE_PRODUCT_LOOP_TRIAL_SCRIPT_CONTRACT_REF
    )
    assert (
        payload["private_operator_trial_ledger_ref"]
        == "ledger-ref:private-operator-trial-acceptance:v1"
    )
    assert payload["full_strength_goal"]
    assert payload["repo_safe_scope"]
    assert payload["blocked_authority_summary"]
    assert payload["promotion_path_refs"]
    assert {
        definition["state"]
        for definition in payload["acceptance_state_definitions"]
    } == set(PRIVATE_BETA_READINESS_ACCEPTANCE_STATES)
    assert {criterion["surface"] for criterion in payload["criteria"]} == set(
        PRIVATE_BETA_READINESS_REQUIRED_SURFACES
    )
    assert {
        "Start Here",
        "Setup Assistant",
        "Proof Detail",
        "Trust Authority Map",
        "Dogfood Live Loop",
    } <= {criterion["surface"] for criterion in payload["criteria"]}
    assert [criterion["surface"] for criterion in payload["criteria"]] == (
        PRIVATE_BETA_READINESS_REQUIRED_SURFACES
    )
    assert len({criterion["criterion_ref"] for criterion in payload["criteria"]}) == (
        len(payload["criteria"])
    )
    for criterion in payload["criteria"]:
        assert set(
            PRIVATE_BETA_READINESS_SURFACE_BLOCKED_REFS[criterion["surface"]]
        ) <= set(criterion["blocked_state_refs"])
        assert criterion["evidence_refs"]
        assert criterion["required_contract_refs"]
        assert criterion["acceptance_refs"]
    assert {criterion["gate_state"] for criterion in payload["criteria"]} >= {
        "partial",
        "mock_only",
        "blocked",
    }
    assert set(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS) <= set(
        payload["blocked_state_refs"]
    )
    assert payload["authority_posture"] == private_beta_readiness_authority_posture()
    assert {
        binding["surface"] for binding in private_beta_readiness_surface_bindings()
    } == set(PRIVATE_BETA_READINESS_REQUIRED_SURFACES)
    assert payload["private_beta_execution_authorized"] is False
    for denied_flag in DENIED_FLAGS:
        assert payload[denied_flag] is False
        assert payload["authority_posture"][denied_flag] is False


def test_private_beta_readiness_rejects_authority_creep_and_unsafe_text() -> None:
    gate = build_private_beta_readiness_gate()
    payload = gate.model_dump(mode="json")
    unsafe = dict(payload)
    unsafe["public_beta_claim_enabled"] = True
    with pytest.raises(ValidationError):
        PrivateBetaReadinessGate(**unsafe)

    unsafe_posture = dict(payload)
    unsafe_posture["authority_posture"] = dict(payload["authority_posture"])
    unsafe_posture["authority_posture"]["connector_write_enabled"] = True
    with pytest.raises(ValidationError):
        PrivateBetaReadinessGate(**unsafe_posture)

    criterion_payload = dict(payload["criteria"][0])
    criterion_payload["safe_summary"] = "raw prompt material"
    with pytest.raises(ValidationError):
        PrivateBetaReadinessCriterion(**criterion_payload)

    missing_blocked = dict(payload["criteria"][0])
    missing_blocked["blocked_state_refs"] = []
    with pytest.raises(ValidationError):
        PrivateBetaReadinessCriterion(**missing_blocked)

    duplicate_surface = dict(payload)
    duplicate_surface["criteria"] = list(payload["criteria"])
    duplicate_surface["criteria"][1] = dict(duplicate_surface["criteria"][0])
    duplicate_surface["criteria"][1]["criterion_ref"] = (
        "private-beta-readiness-criterion:duplicate-start-here"
    )
    with pytest.raises(ValidationError):
        PrivateBetaReadinessGate(**duplicate_surface)

    duplicate_ref = dict(payload)
    duplicate_ref["criteria"] = [dict(criterion) for criterion in payload["criteria"]]
    duplicate_ref["criteria"][1]["criterion_ref"] = (
        duplicate_ref["criteria"][0]["criterion_ref"]
    )
    with pytest.raises(ValidationError):
        PrivateBetaReadinessGate(**duplicate_ref)

    unsafe_pass = dict(payload)
    unsafe_pass["overall_gate_state"] = "pass"
    with pytest.raises(ValidationError):
        PrivateBetaReadinessGate(**unsafe_pass)


def test_founder_loop_surfaces_private_beta_readiness_without_authority(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path, seed_defaults=True)
    today = repo.today_summary()
    inbox = repo.actions_inbox()

    assert today["private_beta_readiness_contract_ref"] == (
        PRIVATE_BETA_READINESS_CONTRACT_REF
    )
    assert today["private_beta_readiness_required_surfaces"] == (
        PRIVATE_BETA_READINESS_REQUIRED_SURFACES
    )
    assert today["private_beta_readiness_acceptance_states"] == (
        PRIVATE_BETA_READINESS_ACCEPTANCE_STATES
    )
    assert today["private_beta_readiness_criterion_count"] == len(
        PRIVATE_BETA_READINESS_REQUIRED_SURFACES
    )
    assert today["private_beta_readiness_local_private_only"] is True
    assert today["private_beta_readiness_execution_authorized"] is False
    assert today["private_beta_readiness_full_strength_goal"]
    assert today["private_beta_readiness_repo_safe_scope"]
    assert today["private_beta_readiness_blocked_authority_summary"]
    assert today["private_beta_readiness_promotion_path_refs"]
    assert today["private_beta_readiness_product_loop_trial_script_ref"] == (
        PRIVATE_PRODUCT_LOOP_TRIAL_SCRIPT_CONTRACT_REF
    )
    assert today["private_beta_readiness_private_operator_trial_ledger_ref"] == (
        "ledger-ref:private-operator-trial-acceptance:v1"
    )
    assert (
        today["private_beta_readiness_authority_posture"][
            "public_beta_claim_enabled"
        ]
        is False
    )
    assert (
        today["private_beta_readiness_authority_posture"]["crm_write_enabled"]
        is False
    )
    assert set(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS) <= set(
        today["private_beta_readiness_blocked_state_refs"]
    )

    readiness_item = next(
        item
        for item in today["evidence_timeline"]
        if item["item_kind"] == "private_beta_readiness_gate_ref"
    )
    assert PRIVATE_BETA_READINESS_CONTRACT_REF in readiness_item["status_refs"]
    assert readiness_item["history_answers"]["approved"]["status"] == "blocked"
    assert readiness_item["approval_ref_authority"] is False
    assert readiness_item["rollback_execution_enabled"] is False
    assert readiness_item["memory_truth_authority"] is False
    assert readiness_item["context_injection_authorized"] is False
    assert readiness_item["raw_evidence_included"] is False
    assert set(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS) <= set(
        readiness_item["blocked_states"]
    )

    assert inbox["private_beta_readiness_contract_ref"] == (
        PRIVATE_BETA_READINESS_CONTRACT_REF
    )
    assert inbox["private_beta_readiness_criteria"]
    assert (
        inbox["private_beta_readiness_authority_posture"][
            "action_execution_enabled"
        ]
        is False
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
