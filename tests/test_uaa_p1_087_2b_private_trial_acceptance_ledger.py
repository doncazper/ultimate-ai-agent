from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts import verify_uaa_p1_087_2b_private_trial_acceptance_ledger as p1_087_2b
from ultimate_ai_agent.core.readiness import (
    PRIVATE_OPERATOR_TRIAL_CONTRACT_REF,
    PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS,
    PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES,
    PrivateOperatorTrialAcceptanceLedger,
    PrivateOperatorTrialSurfaceReview,
    build_private_operator_trial_acceptance_ledger,
)


def test_private_operator_trial_acceptance_ledger_defines_pending_reviews() -> None:
    ledger = build_private_operator_trial_acceptance_ledger()
    payload = ledger.model_dump(mode="json")

    assert payload["contract_ref"] == PRIVATE_OPERATOR_TRIAL_CONTRACT_REF
    assert payload["milestone_ref"] == "milestone:uaa-p1-087.2b"
    assert payload["status"] == (
        "implemented_private_trial_acceptance_ledger_authority_blocked"
    )
    assert payload["trial_run_state"] == "operator_review_ready"
    assert {review["surface"] for review in payload["surface_reviews"]} == set(
        PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES
    )
    assert {review["review_state"] for review in payload["surface_reviews"]} == {
        "pending_operator_review"
    }
    assert set(PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS) <= set(
        payload["blocked_state_refs"]
    )
    assert payload["local_private_only"] is True
    assert payload["safe_refs_only"] is True
    assert payload["manual_operator_review_required"] is True
    assert payload["public_beta_claim_enabled"] is False
    assert payload["production_readiness_claim_enabled"] is False
    assert payload["memory_write_authorized"] is False
    assert payload["action_execution_enabled"] is False
    assert payload["backend_route_added"] is False


def test_private_operator_trial_acceptance_ledger_json_artifact_validates() -> None:
    artifact = Path("docs/macos/private_operator_trial_acceptance_ledger_v1.json")
    ledger = PrivateOperatorTrialAcceptanceLedger.model_validate_json(
        artifact.read_text(encoding="utf-8")
    )

    assert ledger.milestone_ref == "milestone:uaa-p1-087.2b"
    assert ledger.source_packet_ref == "packet-ref:private-operator-trial:v1"
    assert len(ledger.surface_reviews) == len(PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES)
    assert {review.review_state for review in ledger.surface_reviews} == {
        "pending_operator_review"
    }


def test_private_operator_trial_acceptance_ledger_rejects_authority_creep() -> None:
    ledger = build_private_operator_trial_acceptance_ledger()
    payload = ledger.model_dump(mode="json")
    unsafe = dict(payload)
    unsafe["memory_write_authorized"] = True
    with pytest.raises(ValidationError):
        PrivateOperatorTrialAcceptanceLedger(**unsafe)

    unsafe_review = dict(payload["surface_reviews"][0])
    unsafe_review["action_execution_enabled"] = True
    with pytest.raises(ValidationError):
        PrivateOperatorTrialSurfaceReview(**unsafe_review)


def test_private_operator_trial_acceptance_ledger_rejects_unsafe_text() -> None:
    ledger = build_private_operator_trial_acceptance_ledger()
    payload = ledger.model_dump(mode="json")
    raw_review = dict(payload["surface_reviews"][0])
    raw_review["next_safe_action"] = "raw screenshot text"
    with pytest.raises(ValidationError):
        PrivateOperatorTrialSurfaceReview(**raw_review)

    raw_ledger = dict(payload)
    raw_ledger["next_safe_action"] = "raw prompt material"
    with pytest.raises(ValidationError):
        PrivateOperatorTrialAcceptanceLedger(**raw_ledger)


def test_p1_087_2b_verifier_passes_current_repo() -> None:
    assert p1_087_2b.verify() == []


def test_p1_087_2b_verifier_flags_full_087_2_completion_claim() -> None:
    failures = p1_087_2b.verify(
        ledger_text=build_private_operator_trial_acceptance_ledger().model_dump_json(),
        active_doc_text={
            "README.md": "UAA-P1-087.2 is complete for private UI tuning.",
        },
        check_files=False,
    )

    assert any("claims full UAA-P1-087.2 completion" in item for item in failures)
