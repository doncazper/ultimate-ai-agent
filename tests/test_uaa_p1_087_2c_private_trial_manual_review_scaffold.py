from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts import verify_uaa_p1_087_2c_private_trial_manual_review_scaffold as p1_087_2c
from ultimate_ai_agent.core.readiness import (
    PRIVATE_OPERATOR_TRIAL_CONTRACT_REF,
    PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS,
    PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES,
    PrivateOperatorTrialManualReviewItem,
    PrivateOperatorTrialManualReviewScaffold,
    build_private_operator_trial_manual_review_scaffold,
)


def test_private_operator_trial_manual_review_scaffold_stays_unanswered() -> None:
    scaffold = build_private_operator_trial_manual_review_scaffold()
    payload = scaffold.model_dump(mode="json")

    assert payload["contract_ref"] == PRIVATE_OPERATOR_TRIAL_CONTRACT_REF
    assert payload["milestone_ref"] == "milestone:uaa-p1-087.2c"
    assert payload["review_state"] == "manual_review_deferred_pending_implementation"
    assert {item["surface"] for item in payload["review_items"]} == set(
        PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES
    )
    assert {item["answer_state"] for item in payload["review_items"]} == {
        "unanswered_pending_manual_review"
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


def test_private_operator_trial_manual_review_scaffold_json_artifact_validates() -> None:
    artifact = Path("docs/macos/private_operator_trial_manual_review_scaffold_v1.json")
    scaffold = PrivateOperatorTrialManualReviewScaffold.model_validate_json(
        artifact.read_text(encoding="utf-8")
    )

    assert scaffold.milestone_ref == "milestone:uaa-p1-087.2c"
    assert scaffold.source_ledger_ref == "ledger-ref:private-operator-trial-acceptance:v1"
    assert len(scaffold.review_items) == len(PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES)
    assert {item.answer_state for item in scaffold.review_items} == {
        "unanswered_pending_manual_review"
    }


def test_private_operator_trial_manual_review_scaffold_rejects_answers() -> None:
    scaffold = build_private_operator_trial_manual_review_scaffold()
    payload = scaffold.model_dump(mode="json")
    answered_item = dict(payload["review_items"][0])
    answered_item["answer_state"] = "accepted"
    with pytest.raises(ValidationError):
        PrivateOperatorTrialManualReviewItem(**answered_item)

    answered_scaffold = dict(payload)
    answered_scaffold["review_items"] = [*payload["review_items"]]
    answered_scaffold["review_items"][0] = dict(answered_scaffold["review_items"][0])
    answered_scaffold["review_items"][0]["answer_state"] = "revised"
    with pytest.raises(ValidationError):
        PrivateOperatorTrialManualReviewScaffold(**answered_scaffold)


def test_private_operator_trial_manual_review_scaffold_rejects_authority_and_unsafe_text() -> None:
    scaffold = build_private_operator_trial_manual_review_scaffold()
    payload = scaffold.model_dump(mode="json")

    unsafe = dict(payload)
    unsafe["production_readiness_claim_enabled"] = True
    with pytest.raises(ValidationError):
        PrivateOperatorTrialManualReviewScaffold(**unsafe)

    raw_item = dict(payload["review_items"][0])
    raw_item["safe_question"] = "raw prompt answer"
    with pytest.raises(ValidationError):
        PrivateOperatorTrialManualReviewItem(**raw_item)


def test_p1_087_2c_verifier_passes_current_repo() -> None:
    assert p1_087_2c.verify() == []


def test_p1_087_2c_verifier_flags_answer_claim() -> None:
    failures = p1_087_2c.verify(
        scaffold_text=build_private_operator_trial_manual_review_scaffold().model_dump_json(),
        active_doc_text={
            "README.md": "UAA-P1-087.2c accepted the founder findings.",
        },
        check_files=False,
    )

    assert any("claims manual review answers" in item for item in failures)
