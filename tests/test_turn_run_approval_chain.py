import json

import pytest

from scripts.dev import uaa_runtime
from ultimate_ai_agent.core.execution import (
    DurableRunRef,
    TurnRunApprovalLinkage,
    TurnRunApprovalState,
    TurnRunApprovalTransitionRequest,
    TurnRunApprovalTransitionStatus,
    apply_turn_run_approval_transition,
    build_empty_turn_run_approval_chain,
    build_sample_turn_run_approval_chain,
)


def _request(chain, to_state: TurnRunApprovalState, suffix: str, **overrides):
    data = {
        "transition_ref": f"turn-run-transition:test-{suffix}",
        "from_state": chain.current_state,
        "to_state": to_state,
        "actor_ref": "actor-ref:turn-run-test",
        "idempotency_key": f"idempotency-ref:turn-run-test-{suffix}",
        "checkpoint_ref": f"checkpoint-ref:turn-run-test-{suffix}",
        "receipt_ref": f"receipt-ref:turn-run-test-{suffix}",
        "replay_ref": f"replay-ref:turn-run-test-{suffix}",
        "approval_ref": chain.linkage.approval_ref.ref if chain.linkage.approval_ref else None,
        "approval_scope_run_ref": chain.linkage.durable_run_ref.ref,
        "approval_scope_turn_ref": chain.linkage.turn_ref.ref if chain.linkage.turn_ref else None,
        "route_decision_binding_ref": (
            chain.linkage.route_decision_binding_ref.ref if chain.linkage.route_decision_binding_ref else None
        ),
        "evidence_refs": [f"evidence-ref:turn-run-test-{suffix}"],
        "reason_refs": [f"reason-ref:turn-run-test-{suffix}"],
        "safe_summary": "Test transition records state-only runtime chain posture.",
    }
    data.update(overrides)
    return TurnRunApprovalTransitionRequest(**data)


def _running_chain():
    chain = build_sample_turn_run_approval_chain()
    chain, decision = apply_turn_run_approval_transition(
        chain,
        _request(chain, TurnRunApprovalState.approved, "approved"),
    )
    assert decision.status == TurnRunApprovalTransitionStatus.accepted.value
    chain, decision = apply_turn_run_approval_transition(
        chain,
        _request(chain, TurnRunApprovalState.running, "running"),
    )
    assert decision.status == TurnRunApprovalTransitionStatus.accepted.value
    return chain


def test_turn_run_approval_chain_requires_turn_or_operator_task_ref() -> None:
    with pytest.raises(ValueError, match="requires a safe turn ref or operator task ref"):
        TurnRunApprovalLinkage(
            durable_run_ref=DurableRunRef(ref="durable-run-ref:orphan"),
        )


def test_sample_turn_run_approval_chain_is_waiting_for_approval() -> None:
    chain = build_sample_turn_run_approval_chain()

    assert chain.current_state == TurnRunApprovalState.waiting_for_approval.value
    assert chain.linkage.turn_ref.ref == "turn-ref:sample-runtime-parity"
    assert chain.linkage.durable_run_ref.ref == "durable-run-ref:sample-runtime-parity"
    assert chain.approval_ref_grants_authority is False
    assert chain.execution_performed is False
    assert set(chain.canonical_states) == {
        "created",
        "routed",
        "planning",
        "waiting_for_approval",
        "approved",
        "running",
        "retry_scheduled",
        "paused",
        "resumed",
        "cancelled",
        "failed",
        "blocked",
        "completed",
    }


def test_approval_scope_mismatch_cannot_approve_changed_run() -> None:
    chain = build_sample_turn_run_approval_chain()
    request = _request(
        chain,
        TurnRunApprovalState.approved,
        "approval-mismatch",
        approval_scope_run_ref="durable-run-ref:changed",
    )

    unchanged, decision = apply_turn_run_approval_transition(chain, request)

    assert unchanged.current_state == TurnRunApprovalState.waiting_for_approval.value
    assert decision.status == TurnRunApprovalTransitionStatus.denied.value
    assert "reason-ref:turn-run-chain:approval-run-scope-mismatch" in decision.reason_refs
    assert decision.execution_performed is False


def test_matching_approval_scope_can_advance_to_running_without_execution() -> None:
    chain = _running_chain()

    assert chain.current_state == TurnRunApprovalState.running.value
    assert chain.transitions[-1].approval_ref.ref == chain.linkage.approval_ref.ref
    assert chain.execution_enabled is False
    assert chain.execution_performed is False


def test_retry_resume_and_cancel_states_are_inspectable() -> None:
    running = _running_chain()

    paused, pause_decision = apply_turn_run_approval_transition(
        running,
        _request(running, TurnRunApprovalState.paused, "paused"),
    )
    assert pause_decision.status == TurnRunApprovalTransitionStatus.accepted.value
    assert paused.current_state == TurnRunApprovalState.paused.value

    resumed, resume_decision = apply_turn_run_approval_transition(
        paused,
        _request(paused, TurnRunApprovalState.resumed, "resumed"),
    )
    assert resume_decision.status == TurnRunApprovalTransitionStatus.accepted.value
    assert resumed.current_state == TurnRunApprovalState.resumed.value

    failed, fail_decision = apply_turn_run_approval_transition(
        running,
        _request(running, TurnRunApprovalState.failed, "failed"),
    )
    assert fail_decision.status == TurnRunApprovalTransitionStatus.accepted.value
    retry, retry_decision = apply_turn_run_approval_transition(
        failed,
        _request(failed, TurnRunApprovalState.retry_scheduled, "retry"),
    )
    assert retry_decision.status == TurnRunApprovalTransitionStatus.accepted.value
    assert retry.current_state == TurnRunApprovalState.retry_scheduled.value

    cancelled, cancel_decision = apply_turn_run_approval_transition(
        running,
        _request(running, TurnRunApprovalState.cancelled, "cancelled"),
    )
    assert cancel_decision.status == TurnRunApprovalTransitionStatus.accepted.value
    assert cancelled.current_state == TurnRunApprovalState.cancelled.value


def test_transition_replay_is_idempotent_and_conflict_is_denied() -> None:
    chain = build_sample_turn_run_approval_chain()
    request = _request(chain, TurnRunApprovalState.approved, "approved-replay")

    updated, first = apply_turn_run_approval_transition(chain, request)
    replayed, second = apply_turn_run_approval_transition(updated, request)
    conflict = request.model_copy(
        update={
            "transition_ref": "turn-run-transition:test-approved-conflict",
            "receipt_ref": "receipt-ref:turn-run-test-approved-conflict",
        }
    )
    still_updated, third = apply_turn_run_approval_transition(updated, conflict)

    assert first.status == TurnRunApprovalTransitionStatus.accepted.value
    assert second.status == TurnRunApprovalTransitionStatus.idempotent_replay.value
    assert replayed.current_state == updated.current_state
    assert third.status == TurnRunApprovalTransitionStatus.denied.value
    assert "reason-ref:turn-run-chain:idempotency-conflict" in third.reason_refs
    assert still_updated.current_state == updated.current_state


def test_transition_execution_and_raw_payload_flags_are_denied() -> None:
    chain = build_sample_turn_run_approval_chain()
    request = _request(
        chain,
        TurnRunApprovalState.approved,
        "unsafe",
        execution_requested=True,
        raw_payloads_included=True,
    )

    unchanged, decision = apply_turn_run_approval_transition(chain, request)

    assert unchanged.current_state == chain.current_state
    assert decision.status == TurnRunApprovalTransitionStatus.denied.value
    assert "reason-ref:turn-run-chain:execution-requested-denied" in decision.reason_refs
    assert "reason-ref:turn-run-chain:raw-payload-denied" in decision.reason_refs


def test_runtime_cli_inspects_turn_run_approval_chain_safe_json(capsys) -> None:
    exit_code = uaa_runtime.main(["inspect-turn-run-approval-chain", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    chain = payload["turn_run_approval_chain"]
    assert chain["current_state"] == "waiting_for_approval"
    assert chain["approval_ref_grants_authority"] is False
    assert chain["execution_performed"] is False
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True
