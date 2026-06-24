from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

import scripts.verify_fcc_dogfood_001_fourteen_day_private_harness as verifier
from ultimate_ai_agent.core.readiness import (
    PRIVATE_OPERATOR_DOGFOOD_HARNESS_CONTRACT_REF,
    PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS,
    PrivateDogfoodDailyEntry,
    PrivateDogfoodHarness,
    build_private_dogfood_harness,
)


def test_fcc_dogfood_001_verifier_passes_current_repo() -> None:
    assert verifier.validate_fcc_dogfood_001_fourteen_day_private_harness() == []


def test_private_dogfood_harness_defines_fourteen_pending_days() -> None:
    harness = build_private_dogfood_harness()
    payload = harness.model_dump(mode="json")

    assert payload["contract_ref"] == PRIVATE_OPERATOR_DOGFOOD_HARNESS_CONTRACT_REF
    assert payload["milestone_ref"] == "milestone:fcc-dogfood-001"
    assert payload["duration_days"] == 14
    assert len(payload["daily_entries"]) == 14
    assert [entry["day_index"] for entry in payload["daily_entries"]] == list(
        range(1, 15)
    )
    assert {entry["capture_state"] for entry in payload["daily_entries"]} == {
        "not_run"
    }
    assert {entry["manual_review_status"] for entry in payload["daily_entries"]} == {
        "pending_operator_review"
    }
    assert payload["accepted_finding_refs"] == []
    assert payload["revised_finding_refs"] == []
    assert payload["telemetry_upload_enabled"] is False
    assert payload["background_monitoring_enabled"] is False
    assert payload["raw_private_content_allowed"] is False
    assert payload["public_beta_claim_enabled"] is False
    assert payload["production_readiness_claim_enabled"] is False
    assert payload["action_execution_enabled"] is False
    assert payload["backend_route_added"] is False
    assert set(PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS) <= set(
        payload["blocked_state_refs"]
    )


def test_private_dogfood_harness_json_artifact_validates() -> None:
    artifact = Path("docs/macos/private_operator_14_day_dogfood_harness_v1.json")
    harness = PrivateDogfoodHarness.model_validate_json(
        artifact.read_text(encoding="utf-8")
    )

    assert harness.duration_days == 14
    assert len(harness.daily_entries) == 14
    assert harness.daily_entries[0].day_ref == "dogfood-day:fcc-dogfood-001:day-01"
    assert harness.daily_entries[-1].day_ref == "dogfood-day:fcc-dogfood-001:day-14"


def test_private_dogfood_harness_rejects_authority_and_raw_content() -> None:
    harness = build_private_dogfood_harness()
    payload = harness.model_dump(mode="json")

    unsafe = dict(payload)
    unsafe["telemetry_upload_enabled"] = True
    with pytest.raises(ValidationError):
        PrivateDogfoodHarness(**unsafe)

    unsafe = dict(payload)
    unsafe["production_authority_enabled"] = True
    with pytest.raises(ValidationError):
        PrivateDogfoodHarness(**unsafe)

    unsafe_entry = dict(payload["daily_entries"][0])
    unsafe_entry["action_execution_enabled"] = True
    with pytest.raises(ValidationError):
        PrivateDogfoodDailyEntry(**unsafe_entry)

    raw_entry = dict(payload["daily_entries"][0])
    raw_entry["safe_summary"] = "raw prompt material"
    with pytest.raises(ValidationError):
        PrivateDogfoodDailyEntry(**raw_entry)
