from __future__ import annotations

import json
from pathlib import Path

from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
)
from ultimate_ai_agent.core.control_center.health_recommendations import (
    FCC_HEALTH_RECOMMENDATION_ACTION_KIND,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository
from tests.authority_helpers import workspace_write_authority_lease


def _memory_recommendation_item(repo: FounderLoopRepository) -> dict[str, object]:
    return next(
        item
        for item in repo.actions_inbox()["items"]
        if item.get("action_kind") == FCC_HEALTH_RECOMMENDATION_ACTION_KIND
        and item.get("health_recommendation_kind") == "memory_quality_issue"
    )


def test_fcc_mem_021_projects_memory_quality_into_action_inbox(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder-loop")

    first = _memory_recommendation_item(repo)
    second = _memory_recommendation_item(repo)

    assert first["item_ref"] == second["item_ref"]
    assert first["status"] == "proposed"
    assert first["action_group_id"] == "proposal_only_no_execution_path"
    assert first["approval_required"] is False
    assert first["approval_envelope_status"] == (
        "not_required_recommendation_review_only"
    )
    assert first["state_change_readiness"] == (
        "recommendation_review_only_no_execution_path"
    )
    assert first["health_recommendation_source_route_refs"] == [
        "GET /control-center/memory/quality-issues",
        "GET /control-center/memory/maintenance-runs",
        "GET /control-center/actions/inbox",
    ]
    assert "memory-proposal-bridge-ref:fcc-mem-021-action-inbox" in first[
        "health_recommendation_source_signal_refs"
    ]
    assert first["health_recommendation_auto_apply_authorized"] is False
    assert first["health_recommendation_auto_code_authorized"] is False
    assert first["health_recommendation_memory_write_authorized"] is False
    assert first["health_recommendation_context_injection_authorized"] is False
    assert first["health_recommendation_action_execution_authorized"] is False
    assert first["health_recommendation_production_authority_enabled"] is False
    serialized = json.dumps(first, sort_keys=True).lower()
    assert "raw_prompt" not in serialized
    assert "provider_payload" not in serialized


def test_fcc_mem_021_memory_proposal_decision_receipt_does_not_mutate_memory(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder-loop",
        active_authority_leases=[workspace_write_authority_lease()],
    )
    item = _memory_recommendation_item(repo)
    before = repo.storage_status()["counts"]

    receipt = repo.record_action_decision(
        action_id=str(item["item_ref"]),
        decision="defer",
        request=FounderLoopActionDecisionRequest(
            expected_revision_ref=str(item["action_revision_ref"]),
            decision_reason_ref="decision-reason-ref:fcc-mem-021-memory-proposal-defer",
            defer_until_ref="defer-until-ref:fcc-mem-021-review-later",
            metadata_refs=[
                "metadata-ref:fcc-mem-021-memory-proposal",
                str(item["item_ref"]),
            ],
        ),
        idempotency_key_ref="idempotency-ref:fcc-mem-021-memory-proposal-defer",
    )
    after = repo.storage_status()["counts"]

    assert receipt["status"] == "deferred"
    assert receipt["action_executed"] is False
    assert receipt["memory_write_performed"] is False
    assert receipt["connector_write_performed"] is False
    assert receipt["raw_content_stored"] is False
    assert after["action_receipts"] == before["action_receipts"] + 1
    assert after["action_decision_events"] == before["action_decision_events"] + 1
    assert after["memory_review_decisions"] == before["memory_review_decisions"]
    assert after["memory_feedback_receipts"] == before["memory_feedback_receipts"]
    assert after["local_tasks"] == before["local_tasks"]


def test_fcc_mem_021_context_manifest_stays_preview_only(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder-loop")

    manifest = repo.memory_context_manifest(limit=5)
    inbox_item = _memory_recommendation_item(repo)

    assert manifest["proposal_only"] is True
    assert manifest["context_injection_authorized"] is False
    assert manifest["hidden_prompt_context_authorized"] is False
    assert manifest["automatic_context_injection_authorized"] is False
    assert manifest["memory_write_authorized"] is False
    assert manifest["action_execution_authorized"] is False
    assert manifest["model_provider_authority_allowed"] is False
    assert inbox_item["health_recommendation_context_injection_authorized"] is False
    assert inbox_item["health_recommendation_action_execution_authorized"] is False
