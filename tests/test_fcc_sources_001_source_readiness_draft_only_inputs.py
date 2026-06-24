from __future__ import annotations

from pathlib import Path

import scripts.verify_fcc_sources_001_source_readiness_draft_only_inputs as verifier
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]


def test_fcc_sources_001_verifier_passes_current_repo() -> None:
    assert verifier.validate_fcc_sources_001_source_readiness_draft_only_inputs() == []


def test_fcc_sources_001_doc_pins_draft_only_source_boundary() -> None:
    text = (
        ROOT
        / "docs/control_center/FCC_SOURCES_001_SOURCE_READINESS_DRAFT_ONLY_INPUTS.md"
    ).read_text(encoding="utf-8")
    compact = " ".join(text.split())

    assert "Status: Implemented" in text
    assert "GET /control-center/sources/readiness" in text
    assert "source_readiness_proposal_candidates" in text
    assert "proposal_only_no_execution_path" in text
    assert "does not add account auth" in compact
    assert "React must not invent source readiness" in compact
    assert verifier.VERIFIER_REF in text


def test_source_readiness_read_model_is_backend_owned_and_draft_only(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder-loop.sqlite3")
    source_readiness = repo.source_readiness()

    assert source_readiness["schema_version"] == "founder_loop_source_readiness.v1"
    assert source_readiness["backend_owned"] is True
    assert source_readiness["route_ref"] == "/control-center/sources/readiness"
    assert set(source_readiness["supported_statuses"]) >= {
        "ready",
        "blocked",
        "missing",
        "metadata_only",
        "unavailable",
        "not_configured",
    }
    assert source_readiness["connector_runtime_enabled"] is False
    assert source_readiness["source_refresh_enabled"] is False
    assert source_readiness["notification_delivery_enabled"] is False
    assert source_readiness["account_auth_enabled"] is False
    assert source_readiness["raw_source_ingestion_enabled"] is False
    assert source_readiness["write_authority_enabled"] is False
    assert "blocked-state:no-connector-write" in source_readiness[
        "blocked_authority_refs"
    ]

    proposals = source_readiness["source_readiness_proposal_candidates"]
    assert {proposal["title"] for proposal in proposals} == {
        "Define email read-only metadata contract",
        "Define calendar read-only metadata contract",
        "Resolve missing account-auth boundary",
    }
    for proposal in proposals:
        assert proposal["backend_owned"] is True
        assert proposal["proposal_classification"] == "proposal_only_no_execution_path"
        assert proposal["local_task_commit_eligible"] is False
        assert proposal["connector_runtime_enabled"] is False
        assert proposal["account_auth_enabled"] is False
        assert proposal["raw_source_ingestion_enabled"] is False
        assert proposal["write_authority_enabled"] is False


def test_source_readiness_is_embedded_in_today_and_action_inbox(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder-loop.sqlite3")
    source_readiness = repo.source_readiness()
    today = repo.today_summary()
    actions = repo.actions_inbox()

    assert today["source_readiness_route_ref"] == "/control-center/sources/readiness"
    assert today["source_readiness_items"] == source_readiness["source_readiness_items"]
    assert (
        today["source_readiness_posture"]
        == source_readiness["source_readiness_posture"]
    )
    source_actions = [
        item
        for item in actions["items"]
        if item.get("source_readiness_proposal_classification")
        == "proposal_only_no_execution_path"
    ]
    assert len(source_actions) == len(
        source_readiness["source_readiness_proposal_candidates"]
    )
    assert all(item["approval_required"] is False for item in source_actions)
    assert all(
        item["side_effect_class"] == "local_dev_workspace_only"
        for item in source_actions
    )
