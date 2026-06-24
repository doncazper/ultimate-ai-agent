from __future__ import annotations

from pathlib import Path

import scripts.verify_fcc_memory_crm_001_professional_memory_crm_lite_binding as verifier
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
    for followup in followups:
        assert followup["relationship_ref"].startswith("crm-lite-relationship-ref:")
        assert followup["opportunity_ref"].startswith("crm-lite-opportunity-ref:")
        assert followup["status"] == "review_only_stale_check_required"
        assert followup["memory_refs"]
        assert followup["evidence_refs"]
        assert followup["crm_sync_enabled"] is False
        assert followup["crm_write_enabled"] is False
        assert followup["external_write_enabled"] is False
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
    assert all(
        followup["crm_sync_enabled"] is False
        and followup["crm_write_enabled"] is False
        and followup["external_write_enabled"] is False
        for followup in actions["crm_lite_followups"]
    )
    assert all(
        item["reviewed_recall_only"] is True
        and item["context_injection_authorized"] is False
        and item["memory_truth_authority"] is False
        for item in actions["memory_why_shown_items"]
    )
