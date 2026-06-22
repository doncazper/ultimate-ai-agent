from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts import verify_uaa_p1_087_2a_private_trial_packet as p1_087_2a
from ultimate_ai_agent.core.readiness import (
    PRIVATE_OPERATOR_TRIAL_CONTRACT_REF,
    PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS,
    PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES,
    PrivateOperatorTrialChecklistItem,
    PrivateOperatorTrialPacket,
    build_private_operator_trial_packet,
)


def test_private_operator_trial_packet_defines_safe_checklist() -> None:
    packet = build_private_operator_trial_packet()
    payload = packet.model_dump(mode="json")

    assert payload["contract_ref"] == PRIVATE_OPERATOR_TRIAL_CONTRACT_REF
    assert payload["milestone_ref"] == "milestone:uaa-p1-087.2a"
    assert payload["status"] == (
        "implemented_private_trial_packet_ui_surface_authority_blocked"
    )
    assert {item["surface"] for item in payload["checklist_items"]} == set(
        PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES
    )
    assert {item["trial_state"] for item in payload["checklist_items"]} >= {
        "pass",
        "partial",
        "blocked",
    }
    assert set(PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS) <= set(
        payload["blocked_state_refs"]
    )
    assert payload["local_private_only"] is True
    assert payload["safe_refs_only"] is True
    assert payload["manual_operator_review_required"] is True
    assert payload["public_beta_claim_enabled"] is False
    assert payload["production_readiness_claim_enabled"] is False
    assert payload["action_execution_enabled"] is False
    assert payload["backend_route_added"] is False


def test_private_operator_trial_json_artifact_validates() -> None:
    artifact = Path("docs/macos/private_operator_trial_packet_v1.json")
    packet = PrivateOperatorTrialPacket.model_validate_json(
        artifact.read_text(encoding="utf-8")
    )

    assert packet.milestone_ref == "milestone:uaa-p1-087.2a"
    assert packet.boot_command_ref == "launcher-command:uaa-trial-boot"
    assert len(packet.checklist_items) == len(PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES)


def test_private_operator_trial_rejects_authority_creep_and_unsafe_text() -> None:
    packet = build_private_operator_trial_packet()
    payload = packet.model_dump(mode="json")
    unsafe = dict(payload)
    unsafe["action_execution_enabled"] = True
    with pytest.raises(ValidationError):
        PrivateOperatorTrialPacket(**unsafe)

    unsafe_item = dict(payload["checklist_items"][0])
    unsafe_item["memory_write_authorized"] = True
    with pytest.raises(ValidationError):
        PrivateOperatorTrialChecklistItem(**unsafe_item)

    raw_item = dict(payload["checklist_items"][0])
    raw_item["safe_summary"] = "raw prompt material"
    with pytest.raises(ValidationError):
        PrivateOperatorTrialChecklistItem(**raw_item)


def test_p1_087_2a_verifier_passes_current_repo() -> None:
    assert p1_087_2a.verify() == []


def test_p1_087_2a_verifier_flags_full_087_2_completion_claim() -> None:
    failures = p1_087_2a.verify(
        packet_text=build_private_operator_trial_packet().model_dump_json(),
        active_doc_text={
            "README.md": "UAA-P1-087.2 is complete for private UI tuning.",
        },
        check_files=False,
    )

    assert any("claims full UAA-P1-087.2 completion" in item for item in failures)
