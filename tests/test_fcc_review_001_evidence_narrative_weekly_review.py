from __future__ import annotations

from pathlib import Path

import scripts.verify_fcc_review_001_evidence_narrative_weekly_review as verifier
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]


def test_fcc_review_001_verifier_passes_current_repo() -> None:
    assert verifier.validate_fcc_review_001_evidence_narrative_weekly_review() == []


def test_fcc_review_001_doc_pins_read_only_review_boundary() -> None:
    text = (
        ROOT
        / "docs/control_center/FCC_REVIEW_001_EVIDENCE_NARRATIVE_WEEKLY_REVIEW.md"
    ).read_text(encoding="utf-8")
    compact = " ".join(text.split())

    assert "Status: Implemented" in text
    assert "GET /control-center/evidence/timeline" in text
    assert "completed_refs" in text
    assert "missing_source_refs" in text
    assert "does not add automatic weekly generation by model/provider" in compact
    assert verifier.VERIFIER_REF in text


def test_weekly_review_narrative_exposes_required_state_buckets(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder-loop.sqlite3")
    today = repo.today_summary()
    narrative = today["weekly_review_narrative"]

    assert narrative["status"] == "safe_ref_history_ready"
    for field in [
        "completed_refs",
        "deferred_refs",
        "rejected_refs",
        "blocked_refs",
        "stale_refs",
        "planned_refs",
        "missing_source_refs",
        "memory_change_refs",
        "crm_movement_refs",
        "draft_refs",
        "next_week_priority_refs",
    ]:
        assert field in narrative
        assert isinstance(narrative[field], list)
    assert narrative["planned_refs"]
    assert narrative["blocked_refs"]
    assert narrative["stale_refs"]
    assert narrative["missing_source_refs"]
    assert narrative["memory_change_refs"]
    assert narrative["crm_movement_refs"]
    assert narrative["draft_refs"]
    assert narrative["next_week_priority_refs"]
    assert "does not invent truth" in narrative["authority_boundary"]


def test_evidence_timeline_remains_safe_ref_read_only_history(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder-loop.sqlite3")
    timeline = repo.evidence_timeline()

    assert timeline["safe_refs_only"] is True
    assert timeline["raw_content_stored"] is False
    assert timeline["approval_ref_authority"] is False
    assert timeline["rollback_execution_enabled"] is False
    assert timeline["context_injection_authorized"] is False
    assert timeline["action_execution_enabled"] is False
    assert timeline["production_authority_enabled"] is False
    assert timeline["events"]
    assert set(timeline["review_answer_refs"]) == {
        "proposed",
        "decided",
        "changed",
        "denied",
        "skipped",
        "corrected",
        "blocked",
        "reversible_safe_disabled",
    }
    assert timeline["review_answer_refs"]["proposed"]
    assert timeline["review_answer_refs"]["blocked"]
    assert timeline["narrative_items"]
    for event in timeline["events"]:
        assert set(event["history_answers"]) >= {
            "proposed",
            "approved",
            "happened",
            "changed",
            "undoable",
            "stale",
            "blocked",
        }
