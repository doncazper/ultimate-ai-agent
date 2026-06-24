from __future__ import annotations

from pathlib import Path

import scripts.verify_fcc_briefing_001_morning_briefing_today_plan as verifier
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]


def test_fcc_briefing_001_verifier_passes_current_repo() -> None:
    assert verifier.validate_fcc_briefing_001_morning_briefing_today_plan() == []


def test_fcc_briefing_001_doc_pins_read_only_daily_loop_boundary() -> None:
    text = (
        ROOT
        / "docs/control_center/FCC_BRIEFING_001_MORNING_BRIEFING_TODAY_PLAN.md"
    ).read_text(encoding="utf-8")

    assert "Status: Implemented" in text
    assert "Primary surfaces: `/briefing` and `/today`" in text
    assert "GET /control-center/morning-briefing/summary" in text
    assert "source_readiness_posture" in text
    assert "does not add email or calendar fetch" in " ".join(text.split())
    assert verifier.VERIFIER_REF in text


def test_morning_briefing_read_model_exposes_daily_loop_without_authority(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder-loop.sqlite3")
    briefing = repo.morning_briefing()

    assert briefing["daily_loop_summary"]["home_surface"] == "Morning Briefing"
    assert briefing["daily_loop_summary"]["decision_surface"] == "Today"
    assert briefing["daily_loop_summary"]["action_execution_enabled"] is False
    assert briefing["refresh_enabled"] is False
    assert briefing["notification_delivery_enabled"] is False
    assert briefing["source_readiness_posture"]["backend_owned"] is True
    assert briefing["source_readiness_posture"]["connector_runtime_enabled"] is False
    assert briefing["source_readiness_posture"]["source_refresh_enabled"] is False
    assert briefing["source_readiness_items"]
    assert briefing["review_queue_groups"]
    assert briefing["weekly_review_narrative"]["status"] == "safe_ref_history_ready"
    assert briefing["dogfood_capture"]["public_beta_claim_enabled"] is False
    assert briefing["dogfood_capture"]["action_execution_enabled"] is False


def test_today_summary_carries_briefing_and_next_safe_action_refs(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder-loop.sqlite3")
    today = repo.today_summary()

    assert today["briefing_items"]
    assert today["next_safe_actions"]
    assert today["source_readiness_route_ref"] == "/control-center/sources/readiness"
    assert today["daily_loop_summary"]["home_surface"] == "Morning Briefing"
    assert today["daily_loop_summary"]["decision_surface"] == "Today"
