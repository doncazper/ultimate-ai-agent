import pytest

from ultimate_ai_agent.core.agent_runtime import HandoffEnvelope


def _handoff(**overrides: object) -> HandoffEnvelope:
    payload = {
        "handoff_ref": "handoff-ref:agent-runtime:test",
        "source_turn_ref": "turn-ref:agent-runtime:test",
        "source_capability_ref": "cap:chat",
        "target_capability_ref": "cap:agent-runtime:deterministic-specialist",
        "objective_ref": "objective-ref:agent-runtime:test",
        "safe_objective_summary": "Review safe refs for a future specialist handoff.",
        "allowed_authority_refs": ["authority-ref:observe-only"],
        "blocked_authority_refs": [
            "blocked-authority-ref:no-execution",
            "blocked-authority-ref:no-memory-write",
            "blocked-authority-ref:no-context-injection",
        ],
        "evidence_refs": ["evidence-ref:agent-runtime:test"],
        "receipt_refs": ["receipt-ref:agent-runtime:test"],
        "expected_output_schema_ref": "schema-ref:agent-runtime:test",
        "timeout_policy_ref": "timeout-policy-ref:agent-runtime:test",
        "idempotency_ref": "idempotency-ref:agent-runtime:test",
        "rollback_or_safe_disable_ref": "safe-disable-ref:agent-runtime:test",
    }
    payload.update(overrides)
    return HandoffEnvelope(**payload)


def test_handoff_envelope_is_reviewable_not_executable_by_default() -> None:
    handoff = _handoff()

    assert handoff.human_review_required is True
    assert handoff.execution_authorized is False
    assert handoff.memory_write_authorized is False
    assert handoff.context_injection_authorized is False
    assert handoff.connector_write_authorized is False


def test_handoff_envelope_requires_source_and_blocked_authority_refs() -> None:
    with pytest.raises(ValueError, match="HANDOFF_SOURCE_REF_REQUIRED"):
        _handoff(source_turn_ref=None, source_run_ref=None)

    with pytest.raises(ValueError, match="HANDOFF_BLOCKED_AUTHORITY_REFS_REQUIRED"):
        _handoff(blocked_authority_refs=[])


def test_handoff_envelope_denies_execution_authority() -> None:
    with pytest.raises(ValueError, match="HANDOFF_EXECUTION_AUTHORITY_DENIED"):
        _handoff(execution_authorized=True)

    with pytest.raises(ValueError, match="HANDOFF_EXECUTION_AUTHORITY_DENIED"):
        _handoff(memory_write_authorized=True)


def test_handoff_envelope_rejects_raw_content_markers_in_safe_summary() -> None:
    with pytest.raises(ValueError, match="forbidden raw-content marker"):
        _handoff(safe_objective_summary="Review raw_prompt marker")
