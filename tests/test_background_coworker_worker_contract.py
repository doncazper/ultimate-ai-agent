from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.execution import (
    AppendFirstRunStorage,
    BackgroundCoworkerHandoffEnvelopeContract,
    BackgroundCoworkerWorkerEventContract,
    BackgroundCoworkerWorkerIdentityContract,
    DurableRunRecord,
    DurableRunState,
    build_background_coworker_read_model,
    record_background_coworker_worker_event,
    validate_background_coworker_contract_payload,
)
from ultimate_ai_agent.core.execution import background_coworker
from ultimate_ai_agent.core.execution.run_storage import DurableRunStorageDuplicateError
from ultimate_ai_agent.core.task_decomposition.cli import main as task_decomposition_cli_main
from ultimate_ai_agent.core.task_decomposition.runtime import (
    CapabilityRegistryStore,
    CapabilityRegistryStoreConfig,
    TaskDecompositionService,
)


PARENT_RUN_REF = "task-decomposition-run:coworker-parent"
CHILD_RUN_REF = "task-decomposition-run:coworker-child"
WORKER_REF = "worker-ref:test:metadata-reviewer"


def _storage(tmp_path: Path) -> AppendFirstRunStorage:
    return AppendFirstRunStorage(tmp_path / "durable-runs.jsonl")


def _append_run_record(storage: AppendFirstRunStorage, run_ref: str, suffix: str) -> None:
    storage.append_run_record(
        DurableRunRecord(
            run_id=run_ref,
            source_ref=f"source-ref:test:{suffix}",
            state=DurableRunState.created,
            safe_summary=f"Durable run {suffix} exists for coworker metadata inspection.",
            evidence_refs=[f"evidence-ref:test:{suffix}"],
        ),
        idempotency_key=f"idempotency-ref:test:run:{suffix}",
        audit_ref=f"audit-ref:test:run:{suffix}",
        receipt_ref=f"receipt-ref:test:run:{suffix}",
        rollback_ref=f"rollback-ref:test:run:{suffix}",
        safe_summary=f"Durable run {suffix} record persisted as safe metadata.",
        evidence_refs=[f"evidence-ref:test:{suffix}"],
    )


def _event(event_type: str, **overrides: object) -> BackgroundCoworkerWorkerEventContract:
    payload: dict[str, object] = {
        "event_ref": f"coworker-event-ref:test:{event_type}",
        "worker_ref": WORKER_REF,
        "worker_kind": "review_worker",
        "event_type": event_type,
        "run_ref": PARENT_RUN_REF,
        "lease_ref": "lease-ref:test:coworker",
        "heartbeat_ref": "heartbeat-ref:test:coworker",
        "evidence_refs": ["evidence-ref:test:coworker"],
        "blocked_authority_refs": ["authority-boundary-ref:test:no-worker-runtime"],
        "safe_summary": "Coworker worker event is metadata-only and safe-ref-only.",
    }
    payload.update(overrides)
    return BackgroundCoworkerWorkerEventContract.model_validate(payload)


def _record_event(
    storage: AppendFirstRunStorage,
    event: BackgroundCoworkerWorkerEventContract,
    suffix: str,
) -> None:
    record_background_coworker_worker_event(
        storage,
        event,
        idempotency_key_ref=f"idempotency-ref:test:coworker:{suffix}",
        audit_ref=f"audit-ref:test:coworker:{suffix}",
        receipt_ref=f"receipt-ref:test:coworker:{suffix}",
        rollback_ref=f"rollback-ref:test:coworker:{suffix}",
    )


def test_worker_identity_ref_does_not_authorize_execution() -> None:
    identity = BackgroundCoworkerWorkerIdentityContract(
        worker_ref=WORKER_REF,
        worker_kind="review_worker",
        capability_scope_refs=["capability-scope-ref:test:review-only"],
        allowed_run_type_refs=["run-type-ref:test:durable-metadata"],
        denied_authority_refs=["authority-boundary-ref:test:no-background-execution"],
        lease_ref="lease-ref:test:coworker",
        heartbeat_ref="heartbeat-ref:test:coworker",
        parent_run_ref=PARENT_RUN_REF,
        child_run_refs=[CHILD_RUN_REF],
    )

    assert identity.no_execution_authority is True
    assert identity.worker_ref_grants_authority is False
    assert identity.background_execution_enabled is False
    assert identity.scheduler_enabled is False
    assert identity.provider_sdk_calls_enabled is False
    assert identity.tool_execution_enabled is False

    with pytest.raises(ValidationError, match="BACKGROUND_COWORKER_AUTHORITY_DENIED:worker_ref_grants_authority"):
        BackgroundCoworkerWorkerIdentityContract.model_validate(
            {
                **identity.model_dump(mode="json"),
                "worker_ref_grants_authority": True,
            }
        )


def test_handoff_envelope_requires_safe_refs_and_blocks_raw_context_payload() -> None:
    envelope = BackgroundCoworkerHandoffEnvelopeContract(
        handoff_ref="handoff-ref:test:coworker",
        parent_run_ref=PARENT_RUN_REF,
        child_run_ref=CHILD_RUN_REF,
        objective_safe_summary_ref="objective-summary-ref:test:coworker",
        context_pack_ref="context-pack-ref:test:coworker",
        approval_scope_ref="approval-scope-ref:test:coworker",
        evidence_refs=["evidence-ref:test:coworker"],
        timeout_ref="timeout-ref:test:coworker",
        expected_output_schema_ref="schema-ref:test:coworker-output",
        blocked_authority_refs=["authority-boundary-ref:test:no-dispatch"],
    )

    assert envelope.safe_refs_only is True
    assert envelope.worker_dispatch_enabled is False
    assert envelope.execution_authority_enabled is False
    assert envelope.raw_context_payload_persisted is False

    raw_reasons = validate_background_coworker_contract_payload(
        {
            **envelope.model_dump(mode="json"),
            "raw_context_payload": "raw prompt hidden body",
        }
    )
    assert "BACKGROUND_COWORKER_RAW_CONTEXT_FIELD_BLOCKED" in raw_reasons
    assert "BACKGROUND_COWORKER_RAW_CONTEXT_VALUE_BLOCKED" in raw_reasons
    with pytest.raises(ValidationError):
        BackgroundCoworkerHandoffEnvelopeContract.model_validate(
            {
                **envelope.model_dump(mode="json"),
                "raw_context_payload": "raw prompt hidden body",
            }
        )


def test_lease_heartbeat_and_handoff_events_project_metadata_only_read_model(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    _append_run_record(storage, PARENT_RUN_REF, "parent")
    _append_run_record(storage, CHILD_RUN_REF, "child")
    _record_event(storage, _event("lease_requested"), "lease-requested")
    _record_event(storage, _event("heartbeat_stale"), "heartbeat-stale")
    _record_event(
        storage,
        _event(
            "handoff_recorded",
            parent_run_ref=PARENT_RUN_REF,
            child_run_ref=CHILD_RUN_REF,
            handoff_ref="handoff-ref:test:coworker",
        ),
        "handoff-recorded",
    )

    read_model = build_background_coworker_read_model(storage)

    assert read_model.schema_version == "background_coworker_read_model.v1"
    assert read_model.event_count == 3
    assert read_model.worker_count == 1
    assert read_model.run_tree_count == 1
    assert read_model.events[-1].event_type == "handoff_recorded"
    assert read_model.worker_statuses[0].worker_ref == WORKER_REF
    assert read_model.worker_statuses[0].stale_heartbeat_visible is True
    assert read_model.worker_statuses[0].background_execution_enabled is False
    assert read_model.worker_statuses[0].queue_consumer_enabled is False
    assert read_model.run_trees[0].parent_run_ref == PARENT_RUN_REF
    assert read_model.run_trees[0].child_run_refs == [CHILD_RUN_REF]
    assert read_model.all_execution_states_blocked_or_planned is True
    assert read_model.background_execution_enabled is False
    assert read_model.scheduler_enabled is False
    assert read_model.external_process_started is False
    assert read_model.queue_consumer_enabled is False
    assert read_model.raw_payloads_persisted is False


def test_cancel_and_resume_requests_record_intent_without_live_worker_control(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    _append_run_record(storage, PARENT_RUN_REF, "parent")
    _record_event(storage, _event("cancel_requested"), "cancel-requested")
    _record_event(storage, _event("resume_requested"), "resume-requested")

    read_model = build_background_coworker_read_model(storage, run_ref=PARENT_RUN_REF)

    assert read_model.event_type_counts == {"cancel_requested": 1, "resume_requested": 1}
    assert {event.live_worker_control_performed for event in read_model.events} == {False}
    assert {event.execution_performed for event in read_model.events} == {False}
    assert {event.external_process_started for event in read_model.events} == {False}


def test_worker_event_duplicate_idempotency_is_denied(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    event = _event("worker_blocked")
    _record_event(storage, event, "duplicate")

    with pytest.raises(DurableRunStorageDuplicateError):
        _record_event(storage, event, "duplicate")


def test_task_decomposition_cli_inspects_coworker_workers_safe_refs_only(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry_path = str(tmp_path / "registry.json")
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=registry_path))
    service = TaskDecompositionService(registry_store=store)
    _append_run_record(service.durable_run_storage, PARENT_RUN_REF, "parent")
    _record_event(service.durable_run_storage, _event("heartbeat_recorded"), "heartbeat-recorded")

    assert task_decomposition_cli_main(["--registry", registry_path, "inspect-coworker-workers", PARENT_RUN_REF]) == 0
    output = capsys.readouterr().out

    assert '"command_ref": "cli:task-decomposition:inspect-coworker-workers"' in output
    assert '"safe_refs_only": true' in output
    assert '"background_execution_enabled": false' in output
    assert '"worker_runtime_started": false' in output
    assert '"queue_consumer_enabled": false' in output
    assert "raw prompt" not in output.lower()
    assert "provider payload" not in output.lower()
    assert "tool payload" not in output.lower()


def test_background_coworker_contract_adds_no_runtime_imports() -> None:
    source = inspect.getsource(background_coworker)

    assert "import requests" not in source
    assert "import httpx" not in source
    assert "import openai" not in source
    assert "import anthropic" not in source
    assert "import subprocess" not in source
    assert "from playwright" not in source
    assert "from selenium" not in source
