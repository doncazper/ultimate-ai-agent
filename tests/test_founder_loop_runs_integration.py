from __future__ import annotations

from pathlib import Path

from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
)
from ultimate_ai_agent.core.control_center.founder_loop_runs_integration import (
    FOUNDER_LOOP_RUNS_INTEGRATION_CONTRACT_REF,
    FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF,
    FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF,
    FOUNDER_LOOP_RUNS_INTEGRATION_READ_MODEL_SOURCE,
    FOUNDER_LOOP_RUNS_INTEGRATION_REQUIRED_BLOCKED_REFS,
    FOUNDER_LOOP_RUNS_INTEGRATION_SURFACE_ORDER,
)
from ultimate_ai_agent.core.memory import (
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


def _first_candidate_ref(repo: FounderLoopRepository) -> str:
    return str(
        repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"]
    )


def _assert_runs_integration(read_model: dict[str, object]) -> None:
    assert read_model["schema_version"] == "founder-loop-runs-integration.v1"
    assert read_model["contract_ref"] == FOUNDER_LOOP_RUNS_INTEGRATION_CONTRACT_REF
    assert read_model["source"] == FOUNDER_LOOP_RUNS_INTEGRATION_READ_MODEL_SOURCE
    assert read_model["backend_owned"] is True
    assert read_model["local_read_model_only"] is True
    assert read_model["safe_refs_only"] is True
    assert read_model["redacted_summaries_only"] is True
    assert read_model["raw_payloads_persisted"] is False
    assert read_model["ui_truth_source"] == "python_core_read_model"
    assert (
        read_model["primary_run_ref"] == FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF
    )
    assert (
        read_model["primary_proof_ref"]
        == FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF
    )
    assert read_model["surface_order"] == list(
        FOUNDER_LOOP_RUNS_INTEGRATION_SURFACE_ORDER
    )
    assert read_model["surface_count"] == len(
        FOUNDER_LOOP_RUNS_INTEGRATION_SURFACE_ORDER
    )
    assert [
        binding["surface_id"] for binding in read_model["surface_bindings"]
    ] == list(FOUNDER_LOOP_RUNS_INTEGRATION_SURFACE_ORDER)
    assert set(FOUNDER_LOOP_RUNS_INTEGRATION_REQUIRED_BLOCKED_REFS) <= set(
        read_model["blocked_authority_refs"]
    )
    for flag in [
        "provider_model_call_enabled",
        "runtime_model_call_enabled",
        "connector_write_enabled",
        "connector_send_enabled",
        "browser_execution_enabled",
        "live_web_enabled",
        "shell_subprocess_execution_enabled",
        "scheduler_enabled",
        "background_autonomy_enabled",
        "action_execution_enabled",
        "approval_authority_enabled",
        "memory_write_authorized",
        "context_injection_authorized",
        "ui_mutation_authority_enabled",
        "production_authority_enabled",
    ]:
        assert read_model[flag] is False
    for binding in read_model["surface_bindings"]:
        assert binding["run_ref"] == FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF
        assert binding["proof_ref"].startswith("proof-ref:founder-loop-v1:")
        assert binding["proof_detail_ref"].startswith(
            "proof-detail-ref:founder-loop-v1:"
        )
        assert binding["proof_detail_route_ref"] == (
            "proof-detail-route:planned-universal-proof"
        )


def test_founder_loop_today_and_morning_share_backend_owned_run_proof_refs(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    today = repo.today_summary()
    briefing = repo.morning_briefing()

    today_read_model = today["founder_loop_runs_integration_read_model"]
    briefing_read_model = briefing["founder_loop_runs_integration_read_model"]
    _assert_runs_integration(today_read_model)
    _assert_runs_integration(briefing_read_model)
    assert today_read_model["primary_run_ref"] == briefing_read_model["primary_run_ref"]
    assert (
        today_read_model["primary_proof_ref"]
        == briefing_read_model["primary_proof_ref"]
    )
    assert today["loop_trace_refs"]["run_refs"] == [
        FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF
    ]
    assert (
        briefing["loop_trace_refs"]["proof_refs"]
        == today["loop_trace_refs"]["proof_refs"]
    )


def test_founder_loop_trace_links_action_receipts_evidence_memory_and_weekly_review(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    action_receipt = repo.record_action_decision(
        action_id="setup-assistant-hardening",
        decision="defer",
        request=FounderLoopActionDecisionRequest(
            expected_revision_ref=next(
                str(item["action_revision_ref"])
                for item in repo.list_action_inbox(limit=200)
                if item["item_ref"]
                == "founder-action:setup-assistant-hardening"
            ),
            decision_reason_ref="decision-reason-ref:runs-integration-action-defer"
        ),
        idempotency_key_ref="idempotency-ref:runs-integration-action-defer",
    )
    memory_receipt = repo.record_memory_review_decision(
        candidate_ref=_first_candidate_ref(repo),
        decision="defer",
        request=MemoryReviewDecisionRequest(
            reviewer_ref="actor-ref:runs-integration-test",
            source_refs=["source-ref:manual-note:runs-integration-test"],
            evidence_refs=["evidence-ref:memory-review:runs-integration-test"],
            blocked_state_refs=list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
        ),
        idempotency_key_ref="idempotency-ref:runs-integration-memory-defer",
    )

    today = repo.today_summary()
    evidence = repo.evidence_timeline()
    read_model = today["founder_loop_runs_integration_read_model"]
    bindings = {
        binding["surface_id"]: binding for binding in read_model["surface_bindings"]
    }

    assert action_receipt["receipt_ref"] in read_model["receipt_refs"]
    assert memory_receipt["receipt_ref"] in read_model["receipt_refs"]
    assert action_receipt["receipt_ref"] in bindings["decision_receipt"]["receipt_refs"]
    assert memory_receipt["receipt_ref"] in bindings["memory_review"]["receipt_refs"]
    assert bindings["action_inbox"]["action_source_refs"]
    assert bindings["evidence_timeline"]["operator_run_event_refs"]
    assert bindings["memory_review"]["memory_candidate_refs"]
    assert bindings["weekly_review"]["action_source_refs"]
    assert evidence["founder_loop_runs_integration_read_model"]["primary_run_ref"] == (
        FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF
    )
    assert evidence["loop_trace_refs"]["operator_run_event_refs"]
    assert evidence["loop_trace_refs"]["evidence_event_refs"]
    assert "proof-ref:founder-loop-v1:weekly_review" in read_model["proof_refs"]
