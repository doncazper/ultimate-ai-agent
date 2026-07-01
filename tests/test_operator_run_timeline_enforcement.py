from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts import verify_operator_run_timeline_enforcement as verifier
from ultimate_ai_agent.core.storage import (
    FounderLoopOperatorRunCostUsage,
    FounderLoopRepository,
)


ROOT = Path(__file__).resolve().parent.parent


def _timeline(tmp_path: Path) -> dict:
    repository = FounderLoopRepository(tmp_path / "founder_loop")
    return repository.evidence_timeline()["operator_run_timeline"]


def test_inspect_operator_run_timeline_cli_outputs_redacted_json(
    tmp_path: Path,
) -> None:
    env = os.environ.copy()
    env["UAA_FOUNDER_LOOP_STATE_DIR"] = str(tmp_path / "founder_loop")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/inspect_operator_run_timeline.py",
            "--limit-events",
            "1",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        check=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["contract_ref"] == "contract-ref:operator-run-timeline:v1"
    assert payload["safe_refs_only"] is True
    assert payload["frontier_ai_usage_summary"]["cost_receipt_refs"]
    assert len(payload["run_events"]) == 1
    assert "raw prompt" not in result.stdout.lower()
    assert "provider_payload" not in result.stdout.lower()


def test_operator_run_timeline_verifier_passes_seed_payload(tmp_path: Path) -> None:
    assert verifier.verify(_timeline(tmp_path)) == []


def test_operator_run_timeline_cost_usage_model_rejects_denied_content_flag(
    tmp_path: Path,
) -> None:
    payload = copy.deepcopy(_timeline(tmp_path)["run_events"][0]["cost_usage"])
    payload["prompt_content_stored"] = True

    with pytest.raises((ValidationError, ValueError)):
        FounderLoopOperatorRunCostUsage(**payload)


def test_cost_slot_blocks_unknown_paid_cost_and_budget_exceeded(
    tmp_path: Path,
) -> None:
    repository = FounderLoopRepository(tmp_path / "founder_loop")
    over_budget = repository._operator_run_timeline_cost_slot(
        "evidence-event:frontier-over-budget",
        estimated_cost_usd=1.25,
        max_approved_cost_usd=0.25,
        provider_ref="provider-ref:frontier-approved-test",
        model_profile_ref="model-profile-ref:frontier-approved-test",
        input_metered_units=10,
        output_metered_units=5,
    )
    assert over_budget["cost_state_label"] == "Cost blocked"
    assert over_budget["cost_governor_allowed"] is False
    assert (
        "blocked-state:frontier-ai-cost-budget-exceeded"
        in over_budget["cost_blocked_state_refs"]
    )

    unknown_cost = repository._operator_run_timeline_cost_slot(
        "evidence-event:frontier-unknown-cost",
        provider_ref="provider-ref:frontier-approved-test",
        model_profile_ref="model-profile-ref:frontier-approved-test",
        unknown_cost=True,
    )
    assert unknown_cost["cost_state_label"] == "Unknown paid cost"
    assert unknown_cost["approval_required_for_unknown_paid_cost"] is True
    assert (
        "blocked-state:unknown-paid-cost-requires-approval"
        in unknown_cost["cost_blocked_state_refs"]
    )


def test_cost_slot_claimed_frontier_usage_has_receipt_refs(
    tmp_path: Path,
) -> None:
    repository = FounderLoopRepository(tmp_path / "founder_loop")
    slot = repository._operator_run_timeline_cost_slot(
        "evidence-event:frontier-claimed-usage",
        provider_ref="provider-ref:frontier-approved-test",
        model_profile_ref="model-profile-ref:frontier-approved-test",
        frontier_usage_claimed=True,
    )

    assert slot["frontier_usage_claimed"] is True
    assert slot["cost_receipt_refs"]
    assert {
        slot["cost_estimate_ref"],
        slot["captured_usage_ref"],
        slot["budget_decision_ref"],
        slot["provider_ref"],
        slot["model_profile_ref"],
    }.issubset(set(slot["cost_receipt_refs"]))


def test_verifier_fails_frontier_usage_without_cost_receipts(tmp_path: Path) -> None:
    payload = copy.deepcopy(_timeline(tmp_path))
    cost_usage = payload["run_events"][0]["cost_usage"]
    cost_usage["frontier_usage_claimed"] = True
    cost_usage["cost_receipt_refs"] = []

    failures = verifier.verify(payload)

    assert any("frontier usage claimed without cost receipts" in item for item in failures)


def test_verifier_fails_unknown_paid_cost_without_approval_binding(
    tmp_path: Path,
) -> None:
    payload = copy.deepcopy(_timeline(tmp_path))
    cost_usage = payload["run_events"][0]["cost_usage"]
    cost_usage["unknown_cost"] = True
    cost_usage["cost_state_label"] = "Unknown paid cost"
    cost_usage["approval_required_for_unknown_paid_cost"] = False
    cost_usage["cost_blocked_state_refs"] = [
        ref
        for ref in cost_usage["cost_blocked_state_refs"]
        if ref != "blocked-state:unknown-paid-cost-requires-approval"
    ]

    failures = verifier.verify(payload)

    assert any("unknown paid cost is not approval-bound" in item for item in failures)
    assert any("unknown paid cost missing blocked-state ref" in item for item in failures)


def test_verifier_fails_provider_model_authority_implied_without_scope(
    tmp_path: Path,
) -> None:
    payload = copy.deepcopy(_timeline(tmp_path))
    payload["frontier_ai_usage_summary"]["provider_sdk_call_enabled"] = True
    payload["run_events"][0]["cost_usage"]["frontier_ai_routing_allowed"] = True

    failures = verifier.verify(payload)

    assert any("provider_sdk_call_enabled" in item for item in failures)
    assert any("frontier_ai_routing_allowed" in item for item in failures)


def test_verifier_fails_prompt_response_or_provider_exchange_content(
    tmp_path: Path,
) -> None:
    payload = copy.deepcopy(_timeline(tmp_path))
    payload["run_events"][0]["cost_usage"]["response_content_stored"] = True
    payload["run_events"][0]["safe_summary"] = "raw response content was stored"

    failures = verifier.verify(payload)

    assert any("response_content_stored" in item for item in failures)
    assert any("unsafe content fragment" in item for item in failures)
