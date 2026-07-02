from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.execution import (
    AppendFirstRunStorage,
    DurableRunRecord,
    DurableRunState,
    RunProgressEventReadModel,
    append_run_progress_event_receipt,
    build_run_progress_read_model,
    validate_run_progress_event_sequence,
)
from ultimate_ai_agent.core.execution import read_models
from ultimate_ai_agent.core.task_decomposition.cli import main as task_decomposition_cli_main
from ultimate_ai_agent.core.task_decomposition.runtime import (
    CapabilityRegistryStore,
    CapabilityRegistryStoreConfig,
    TaskCapabilityApprovalRequestPayload,
    TaskDecompositionService,
)


def _storage(tmp_path: Path) -> AppendFirstRunStorage:
    return AppendFirstRunStorage(tmp_path / "durable-runs.jsonl")


def _append_run_record(
    storage: AppendFirstRunStorage,
    run_id: str,
    state: DurableRunState = DurableRunState.created,
    suffix: str = "created",
) -> None:
    storage.append_run_record(
        DurableRunRecord(
            run_id=run_id,
            source_ref=f"source-ref:test:{suffix}",
            state=state,
            safe_summary=f"Durable run {suffix} state recorded as safe metadata.",
            evidence_refs=[f"evidence-ref:test:{suffix}"],
        ),
        idempotency_key=f"idempotency-ref:test:{suffix}",
        audit_ref=f"audit-ref:test:{suffix}",
        receipt_ref=f"receipt-ref:test:{suffix}",
        rollback_ref=f"rollback-ref:test:{suffix}",
        safe_summary=f"Durable run {suffix} record persisted as safe metadata.",
        evidence_refs=[f"evidence-ref:test:{suffix}"],
    )


def _progress_event(
    run_id: str,
    sequence: int,
    event_type: str = "stream_started",
    **overrides: object,
) -> RunProgressEventReadModel:
    payload: dict[str, object] = {
        "run_ref": run_id,
        "sequence": sequence,
        "event_type": event_type,
        "durable_run_event_ref": f"durable-run-event-ref:test:{sequence}",
        "storage_entry_ref": f"durable-run-storage-entry:test:{sequence}",
        "storage_entry_kind": "receipt",
        "evidence_refs": [f"evidence-ref:test:{sequence}"],
        "safe_summary": "Recorded progress metadata uses safe refs only.",
    }
    payload.update(overrides)
    return RunProgressEventReadModel.model_validate(payload)


def test_progress_model_projects_ordered_durable_entries_and_summary(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    run_id = "task-decomposition-run:progress-basic"
    _append_run_record(storage, run_id, DurableRunState.created, "created")
    started = _progress_event(run_id, 2, "stream_started")
    append_run_progress_event_receipt(
        storage,
        started,
        idempotency_key_ref="idempotency-ref:test:stream-started",
        audit_ref="audit-ref:test:stream-started",
        receipt_ref="receipt-ref:test:stream-started",
        rollback_ref="rollback-ref:test:stream-started",
    )
    delta = _progress_event(
        run_id,
        3,
        "stream_delta_redacted",
        redacted_delta_ref="redacted-delta-ref:test:one",
    )
    append_run_progress_event_receipt(
        storage,
        delta,
        idempotency_key_ref="idempotency-ref:test:stream-delta",
        audit_ref="audit-ref:test:stream-delta",
        receipt_ref="receipt-ref:test:stream-delta",
        rollback_ref="rollback-ref:test:stream-delta",
    )

    progress = build_run_progress_read_model(storage, run_id)

    assert progress is not None
    assert progress.schema_version == "run_progress_read_model.v1"
    assert progress.sequence_start == 1
    assert progress.sequence_end == 3
    assert progress.event_count == 3
    assert [event.sequence for event in progress.events] == [1, 2, 3]
    assert [event.event_type for event in progress.events] == [
        "run_created",
        "stream_started",
        "stream_delta_redacted",
    ]
    assert progress.redacted_delta_refs == ["redacted-delta-ref:test:one"]
    assert progress.receipt_refs == [
        "receipt-ref:test:created",
        "receipt-ref:test:stream-delta",
        "receipt-ref:test:stream-started",
    ]
    receipt_summary = storage.list_receipt_summaries(run_id)[0]
    assert "safe_summary" not in receipt_summary
    assert receipt_summary["safe_summary_ref"].startswith("run-progress-summary-ref:")
    assert receipt_summary["stream_transport_active"] is False
    assert receipt_summary["runtime_execution_performed"] is False
    assert progress.safe_refs_only is True
    assert progress.raw_content_persisted is False
    assert progress.live_streaming_runtime_enabled is False
    assert progress.provider_model_calls_enabled is False
    assert progress.execution_performed is False


def test_progress_model_bounded_events_preserve_global_sequence(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    run_id = "task-decomposition-run:progress-bounded"
    _append_run_record(storage, run_id, DurableRunState.created, "created")
    for index in range(2, 6):
        event = _progress_event(
            run_id,
            index,
            "stream_heartbeat",
            heartbeat_ref=f"heartbeat-ref:test:{index}",
        )
        append_run_progress_event_receipt(
            storage,
            event,
            idempotency_key_ref=f"idempotency-ref:test:heartbeat:{index}",
            audit_ref=f"audit-ref:test:heartbeat:{index}",
            receipt_ref=f"receipt-ref:test:heartbeat:{index}",
            rollback_ref=f"rollback-ref:test:heartbeat:{index}",
        )

    progress = build_run_progress_read_model(storage, run_id, limit=2)

    assert progress is not None
    assert [event.sequence for event in progress.events] == [4, 5]
    assert progress.sequence_start == 4
    assert progress.sequence_end == 5
    assert progress.heartbeat_refs == ["heartbeat-ref:test:4", "heartbeat-ref:test:5"]


def test_progress_event_sequence_validator_blocks_non_monotonic_and_raw_chunk() -> None:
    reasons = validate_run_progress_event_sequence(
        [
            _progress_event("task-decomposition-run:progress-validator", 1).model_dump(mode="json"),
            _progress_event("task-decomposition-run:progress-validator", 3).model_dump(mode="json"),
        ]
    )
    raw_reasons = validate_run_progress_event_sequence(
        [
            {
                **_progress_event("task-decomposition-run:progress-validator", 1).model_dump(mode="json"),
                "raw_chunk": "unsafe hidden content",
            }
        ]
    )

    assert "RUN_PROGRESS_SEQUENCE_NOT_MONOTONIC" in reasons
    assert "RUN_PROGRESS_RAW_PAYLOAD_FIELD_BLOCKED" in raw_reasons


def test_progress_event_requires_redacted_delta_and_terminal_for_completed_stream(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="RUN_PROGRESS_REDACTED_DELTA_REF_REQUIRED"):
        _progress_event("task-decomposition-run:progress-redaction", 1, "stream_delta_redacted")

    storage = _storage(tmp_path)
    run_id = "task-decomposition-run:progress-terminal"
    _append_run_record(storage, run_id, DurableRunState.created, "created")
    append_run_progress_event_receipt(
        storage,
        _progress_event(run_id, 2, "stream_started"),
        idempotency_key_ref="idempotency-ref:test:terminal:start",
        audit_ref="audit-ref:test:terminal:start",
        receipt_ref="receipt-ref:test:terminal:start",
        rollback_ref="rollback-ref:test:terminal:start",
    )
    _append_run_record(storage, run_id, DurableRunState.succeeded, "succeeded")

    with pytest.raises(ValidationError, match="RUN_PROGRESS_TERMINAL_EVENT_REQUIRED"):
        build_run_progress_read_model(storage, run_id)

    append_run_progress_event_receipt(
        storage,
        _progress_event(run_id, 4, "stream_completed"),
        idempotency_key_ref="idempotency-ref:test:terminal:completed",
        audit_ref="audit-ref:test:terminal:completed",
        receipt_ref="receipt-ref:test:terminal:completed",
        rollback_ref="rollback-ref:test:terminal:completed",
    )
    progress = build_run_progress_read_model(storage, run_id)

    assert progress is not None
    assert progress.progress_state == "completed"
    assert progress.terminal_event_present is True
    assert progress.events[-1].event_type == "stream_completed"


def test_progress_model_rejects_authority_flags() -> None:
    event = _progress_event("task-decomposition-run:progress-authority", 1)
    with pytest.raises(ValidationError, match="RUN_PROGRESS_AUTHORITY_DENIED:live_streaming_runtime_enabled"):
        RunProgressEventReadModel.model_validate(
            {
                **event.model_dump(mode="json"),
                "live_streaming_runtime_enabled": True,
            }
        )


def test_task_decomposition_cli_inspects_progress_safe_refs_only(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry_path = str(tmp_path / "registry.json")
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=registry_path))
    service = TaskDecompositionService(registry_store=store)
    service.ensure_examples()
    request = service.build_approval_request(
        TaskCapabilityApprovalRequestPayload(
            capability_id="capability:example-echo-summary",
            run_id="task-decomposition-run:progress-cli",
            actor_id="local_actor",
        )
    )

    assert task_decomposition_cli_main(["--registry", registry_path, "inspect-run-progress", request.run_id]) == 0
    output = capsys.readouterr().out

    assert '"command_ref": "cli:task-decomposition:inspect-run-progress"' in output
    assert '"safe_refs_only": true' in output
    assert '"live_streaming_runtime_enabled": false' in output
    assert '"provider_model_calls_enabled": false' in output
    assert '"execution_authority_enabled": false' in output
    assert "raw prompt" not in output.lower()
    assert "provider payload" not in output.lower()
    assert "raw chunk" not in output.lower()


def test_progress_read_model_adds_no_live_stream_or_runtime_imports() -> None:
    source = inspect.getsource(read_models)

    assert "import requests" not in source
    assert "import httpx" not in source
    assert "import openai" not in source
    assert "import anthropic" not in source
    assert "from websockets" not in source
    assert "EventSource" not in source
