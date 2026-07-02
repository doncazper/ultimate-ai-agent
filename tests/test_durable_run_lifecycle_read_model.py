from pathlib import Path

import pytest

from ultimate_ai_agent.core.execution import (
    AppendFirstRunStorage,
    CANONICAL_RUN_EVENT_TYPES,
    CANONICAL_RUN_LIFECYCLE_STATES,
    DurableRunRecord,
    DurableRunState,
    DurableRunStorageDuplicateError,
    DurableRunTransitionKind,
    DurableRunTransitionRequest,
    DurableRunTransitionStatus,
    apply_durable_run_transition,
    build_durable_run_lifecycle_read_model,
    evaluate_durable_run_transition,
)


def _storage(tmp_path: Path) -> AppendFirstRunStorage:
    return AppendFirstRunStorage(tmp_path / "durable-runs.jsonl")


def _record(run_id: str = "durable-run:test") -> DurableRunRecord:
    return DurableRunRecord(
        run_id=run_id,
        source_ref="source-ref:test",
        state=DurableRunState.created,
        safe_summary="State-only durable run lifecycle summary.",
        metadata={"approval_refs": ["approval-ref:test"]},
    )


def _append_record(storage: AppendFirstRunStorage, record: DurableRunRecord, suffix: str = "create") -> None:
    storage.append_run_record(
        record,
        idempotency_key=f"idempotency-ref:test:{suffix}",
        audit_ref=f"audit-ref:test:{suffix}",
        receipt_ref=f"receipt-ref:test:{suffix}",
        rollback_ref=f"rollback-ref:test:{suffix}",
        safe_summary=f"State-only durable run record {suffix} persisted.",
        evidence_refs=[f"evidence-ref:test:{suffix}"],
    )
    storage.append_receipt_summary(
        run_id=record.run_id,
        receipt_ref=f"receipt-ref:test:{suffix}",
        idempotency_key=f"idempotency-ref:test:{suffix}:receipt",
        audit_ref=f"audit-ref:test:{suffix}",
        rollback_ref=f"rollback-ref:test:{suffix}",
        safe_summary=f"State-only durable receipt {suffix} persisted.",
        receipt_summary={
            "run_id": record.run_id,
            "state": record.state.value,
            "receipt_ref": f"receipt-ref:test:{suffix}",
            "safe_summary": f"State-only durable receipt {suffix} summary.",
            "safe_ref_only": True,
            "no_runtime_authority": True,
        },
        evidence_refs=[f"evidence-ref:test:{suffix}"],
    )


def _transition_request(
    record: DurableRunRecord,
    kind: DurableRunTransitionKind,
    suffix: str,
) -> DurableRunTransitionRequest:
    return DurableRunTransitionRequest(
        run_id=record.run_id,
        transition_id=f"durable-transition:test:{suffix}",
        transition_kind=kind,
        idempotency_key=f"idempotency-ref:test:{suffix}",
        actor_ref="actor-ref:test",
        audit_ref=f"audit-ref:test:{suffix}",
        receipt_ref=f"receipt-ref:test:{suffix}",
        replay_ref=f"replay-ref:test:{suffix}",
        rollback_ref=f"rollback-ref:test:{suffix}",
        safe_summary=f"State-only durable run transition {suffix}.",
        evidence_refs=[f"evidence-ref:test:{suffix}"],
    )


def test_lifecycle_read_model_projects_append_first_storage_with_safe_authority_flags(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    record = _record()
    _append_record(storage, record)

    model = build_durable_run_lifecycle_read_model(storage, record.run_id)

    assert model is not None
    assert model.status == "created"
    assert model.source_status == "created"
    assert model.canonical_states == list(CANONICAL_RUN_LIFECYCLE_STATES)
    assert model.canonical_event_types == list(CANONICAL_RUN_EVENT_TYPES)
    assert [event.event_type for event in model.events] == ["run_created", "receipt_recorded"]
    assert model.event_count == 2
    assert model.run_record_event_count == 1
    assert model.receipt_event_count == 1
    assert model.approval_refs == ["approval-ref:test"]
    assert model.receipt_hash_refs
    assert model.replay_validation_refs
    assert model.append_only_event_log is True
    assert model.idempotent_append_enforced is True
    assert model.hash_chain_verified_on_load is True
    assert model.safe_refs_only is True
    assert model.raw_payloads_persisted is False
    assert model.approval_refs_are_identifiers_only is True
    assert model.execution_authority_enabled is False
    assert model.execution_performed is False
    assert model.scheduler_enabled is False
    assert model.background_worker_enabled is False
    assert model.provider_model_calls_enabled is False
    assert model.tool_execution_expansion_enabled is False
    assert model.connector_writes_enabled is False
    assert model.streaming_runtime_enabled is False
    assert model.api_mutation_routes_added is False
    assert model.cancel_resume_controls_status == "planned_blocked_no_execution_authority"
    assert model.timestamps_recorded is False


def test_lifecycle_read_model_bounds_events_and_can_omit_receipts(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    record = _record()
    _append_record(storage, record)
    ready = apply_durable_run_transition(
        record,
        _transition_request(record, DurableRunTransitionKind.mark_ready, "ready"),
    ).record
    _append_record(storage, ready, "ready")

    without_receipts = build_durable_run_lifecycle_read_model(
        storage,
        record.run_id,
        include_receipts=False,
    )
    bounded = build_durable_run_lifecycle_read_model(storage, record.run_id, limit=1)

    assert without_receipts is not None
    assert [event.storage_entry_kind for event in without_receipts.events] == ["run_record", "run_record"]
    assert [event.event_type for event in without_receipts.events] == ["run_created", "run_queued"]
    assert without_receipts.receipt_event_count == 2
    assert bounded is not None
    assert bounded.event_count == 1
    assert bounded.events[0].sequence == 4


def test_invalid_lifecycle_transition_is_blocked_without_storage_mutation(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    record = _record()
    _append_record(storage, record)

    denied = evaluate_durable_run_transition(
        record,
        _transition_request(record, DurableRunTransitionKind.pause, "pause-from-created"),
    )

    assert denied.status == DurableRunTransitionStatus.denied
    assert "DURABLE_RUN_INVALID_TRANSITION_DENIED" in denied.reason_codes
    assert len(storage.list_entries(record.run_id)) == 2


def test_duplicate_idempotency_append_is_denied(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    record = _record()
    _append_record(storage, record)

    with pytest.raises(DurableRunStorageDuplicateError, match="DURABLE_RUN_STORAGE_IDEMPOTENCY_REPLAY_DENIED"):
        storage.append_run_record(
            record,
            idempotency_key="idempotency-ref:test:create",
            audit_ref="audit-ref:test:duplicate",
            receipt_ref="receipt-ref:test:duplicate",
            rollback_ref="rollback-ref:test:duplicate",
            safe_summary="Duplicate durable run record denied.",
            evidence_refs=["evidence-ref:test:duplicate"],
        )


def test_raw_prompt_language_is_rejected_before_projection(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    with pytest.raises(ValueError, match="unsafe durable evidence language"):
        _append_record(
            storage,
            DurableRunRecord(
                run_id="durable-run:unsafe",
                source_ref="source-ref:unsafe",
                state=DurableRunState.created,
                safe_summary="raw prompt must not persist",
            ),
        )
