from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import scripts.verify_fcc_memory_crm_001_professional_memory_crm_lite_binding as verifier
from ultimate_ai_agent.core.memory import (
    CRM_LITE_RELATIONSHIP_MEMORY_CONTRACT_REF,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]


def test_fcc_memory_crm_001_verifier_passes_current_repo() -> None:
    assert (
        verifier.validate_fcc_memory_crm_001_professional_memory_crm_lite_binding()
        == []
    )


def test_fcc_memory_crm_001_doc_pins_recall_not_authority_boundary() -> None:
    text = (
        ROOT
        / "docs/control_center/FCC_MEMORY_CRM_001_PROFESSIONAL_MEMORY_CRM_LITE_BINDING.md"
    ).read_text(encoding="utf-8")
    compact = " ".join(text.split())

    assert "Status: Implemented" in text
    assert "crm_lite_followups" in text
    assert "memory_why_shown_items" in text
    assert "CrmLiteRelationshipFollowUp" in text
    assert "scripts/inspect_relationship_crm_lite_memory.py" in text
    assert "recall, not truth or authority" in compact
    assert "does not add automatic memory truth" in compact
    assert "local/read-only/proposal-only" in compact
    assert verifier.VERIFIER_REF in text


def test_today_exposes_crm_lite_followups_without_external_write_authority(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder-loop.sqlite3")
    today = repo.today_summary()

    followups = today["crm_lite_followups"]
    assert followups
    assert (
        today["crm_lite_relationship_memory_contract_ref"]
        == CRM_LITE_RELATIONSHIP_MEMORY_CONTRACT_REF
    )
    posture = today["crm_lite_relationship_authority_posture"]
    assert posture["crm_sync_enabled"] is False
    assert posture["connector_read_authorized"] is False
    assert posture["context_injection_authorized"] is False
    assert posture["hidden_memory_write_authorized"] is False
    assert posture["model_provider_call_authorized"] is False
    for followup in followups:
        assert followup["contract_ref"] == CRM_LITE_RELATIONSHIP_MEMORY_CONTRACT_REF
        assert followup["relationship_ref"].startswith("crm-lite-relationship-ref:")
        assert followup["person_ref"].startswith("crm-lite-person-ref:")
        assert followup["org_ref"].startswith("crm-lite-org-ref:")
        assert followup["project_ref"].startswith("crm-lite-project-ref:")
        assert followup["opportunity_ref"].startswith("crm-lite-opportunity-ref:")
        assert followup["promise_ref"].startswith("crm-lite-promise-ref:")
        assert followup["status"] == "review_only_stale_check_required"
        assert followup["relationship_memory_posture"] == "reviewed_recall_only"
        assert followup["redaction_status"] == "redacted_summary_only"
        assert followup["review_envelope_ref"].startswith("review-envelope-ref:")
        assert not followup["review_envelope_ref"].startswith(
            "memory-derived-action-proposal:"
        )
        assert followup["memory_refs"]
        assert followup["evidence_refs"]
        assert followup["review_required_before_action"] is True
        assert followup["safe_refs_only"] is True
        assert followup["crm_sync_enabled"] is False
        assert followup["crm_write_enabled"] is False
        assert followup["external_write_enabled"] is False
        assert followup["connector_read_authorized"] is False
        assert followup["connector_write_authorized"] is False
        assert followup["account_sync_authorized"] is False
        assert followup["email_calendar_fetch_authorized"] is False
        assert followup["context_injection_authorized"] is False
        assert followup["hidden_memory_write_authorized"] is False
        assert followup["action_execution_authorized"] is False
        assert followup["model_provider_call_authorized"] is False
        assert followup["production_authority_enabled"] is False
        assert "blocked-state:crm-lite-no-connector-read" in followup[
            "blocked_state_refs"
        ]
        assert "blocked-state:crm-lite-no-hidden-context-injection" in followup[
            "blocked_state_refs"
        ]
        assert "blocked-state:no-external-crm-write" in followup[
            "blocked_state_refs"
        ]
        assert "blocked-state:no-account-sync" in followup["blocked_state_refs"]


def test_memory_why_shown_items_preserve_recall_only_provenance(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder-loop.sqlite3")
    today = repo.today_summary()

    items = today["memory_why_shown_items"]
    assert items
    for item in items:
        assert item["memory_ref"]
        assert item["loop_item_ref"]
        assert item["why_shown"]
        assert item["stale_state"]
        assert item["conflict_state"] == "conflict_unknown_review_required"
        assert item["reviewed_recall_only"] is True
        assert item["context_injection_authorized"] is False
        assert item["memory_truth_authority"] is False
        assert "not truth" in item["authority_boundary"]


def test_actions_inbox_carries_memory_crm_lite_context_without_crm_sync(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder-loop.sqlite3")
    actions = repo.actions_inbox()

    assert actions["crm_lite_followups"]
    assert actions["memory_why_shown_items"]
    assert (
        actions["crm_lite_relationship_memory_contract_ref"]
        == CRM_LITE_RELATIONSHIP_MEMORY_CONTRACT_REF
    )
    assert all(
        followup["crm_sync_enabled"] is False
        and followup["crm_write_enabled"] is False
        and followup["external_write_enabled"] is False
        and followup["connector_read_authorized"] is False
        and followup["hidden_memory_write_authorized"] is False
        for followup in actions["crm_lite_followups"]
    )
    assert all(
        item["reviewed_recall_only"] is True
        and item["context_injection_authorized"] is False
        and item["memory_truth_authority"] is False
        for item in actions["memory_why_shown_items"]
    )


def test_relationship_crm_lite_cli_inspection_is_safe_schema(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    FounderLoopRepository(state_dir)
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_relationship_crm_lite_memory.py"),
            "--state-dir",
            str(state_dir),
            "--limit",
            "2",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["contract_ref"] == CRM_LITE_RELATIONSHIP_MEMORY_CONTRACT_REF
    assert payload["storage_state"] == "existing_state_read_only"
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True
    assert payload["raw_paths_omitted"] is True
    assert payload["crm_sync_enabled"] is False
    assert payload["context_injection_authorized"] is False
    assert payload["production_authority_enabled"] is False
    assert payload["today_followups"]
    assert payload["today_followups"][0]["person_ref"].startswith(
        "crm-lite-person-ref:"
    )


def test_relationship_crm_lite_cli_inspection_does_not_seed_missing_state(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "missing-state"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_relationship_crm_lite_memory.py"),
            "--state-dir",
            str(state_dir),
            "--limit",
            "2",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["storage_state"] == "state_not_found_no_write"
    assert payload["today_followups"] == []
    assert payload["action_inbox_followups"] == []
    assert payload["memory_why_shown_items"] == []
    assert not state_dir.exists()


def test_relationship_crm_lite_cli_inspection_redacts_unreadable_state(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "broken-state"
    state_dir.mkdir()
    (state_dir / "founder_loop.sqlite3").write_text(
        "not a sqlite database",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_relationship_crm_lite_memory.py"),
            "--state-dir",
            str(state_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["storage_state"] == "existing_state_unreadable_redacted"
    assert (
        payload["inspection_error_ref"]
        == "error-ref:relationship-crm-lite-memory:read-failed-redacted"
    )
    assert payload["today_followups"] == []
    assert result.stderr == ""
    assert "Traceback" not in result.stdout
    assert str(state_dir) not in result.stdout
    assert str(ROOT) not in result.stdout
