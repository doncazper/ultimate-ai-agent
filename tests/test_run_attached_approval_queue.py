from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.execution import (
    AppendFirstRunStorage,
    DurableRunRecord,
    RunAttachedApprovalQueueItemReadModel,
    build_durable_run_lifecycle_read_model,
    record_run_attached_approval_event,
)
from ultimate_ai_agent.core.execution.approval_queue import (
    RUN_ATTACHED_APPROVAL_EVENT_RECEIPT_SCHEMA_VERSION,
)
from ultimate_ai_agent.core.task_decomposition.cli import main as task_decomposition_cli_main
from ultimate_ai_agent.core.task_decomposition.runtime import (
    CapabilityRegistryStore,
    CapabilityRegistryStoreConfig,
    TaskCapabilityApprovalRequestPayload,
    TaskDecompositionApprovalGrantRequest,
    TaskDecompositionService,
)


def _service(tmp_path: Path) -> TaskDecompositionService:
    store = CapabilityRegistryStore(
        CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json"))
    )
    service = TaskDecompositionService(registry_store=store)
    service.ensure_examples()
    return service


def test_run_attached_approval_queue_projects_requests_and_grants(tmp_path: Path) -> None:
    service = _service(tmp_path)
    request = service.build_approval_request(
        TaskCapabilityApprovalRequestPayload(
            capability_id="capability:example-echo-summary",
            run_id="task-decomposition-run:approval-queue",
            actor_id="local_actor",
        )
    )

    requested = service.run_attached_approval_queue()

    assert requested["schema_version"] == "run_attached_approval_queue.v1"
    assert requested["summary"]["queue_item_count"] == 1
    assert requested["summary"]["pending_count"] == 1
    assert requested["queue_items"][0]["approval_state"] == "requested"
    assert requested["queue_items"][0]["durable_attachment_status"] == "attached"
    assert requested["queue_items"][0]["approval_refs_are_identifiers_only"] is True
    assert requested["queue_items"][0]["approval_authority_enabled"] is False
    assert requested["queue_items"][0]["execution_authority_enabled"] is False
    assert requested["queue_items"][0]["ui_mutation_controls_enabled"] is False
    assert requested["queue_items"][0]["raw_payloads_persisted"] is False

    service.grant_approval(
        TaskDecompositionApprovalGrantRequest(
            approval_request_id=request.approval_request_id,
            approved_by_actor_id="local_reviewer",
        )
    )
    queue = service.run_attached_approval_queue()

    assert queue["summary"]["queue_item_count"] == 2
    assert queue["summary"]["approved_count"] == 1
    assert queue["summary"]["approval_grants_created"] is True
    assert queue["summary"]["arbitrary_approval_ref_authority"] is False
    assert queue["summary"]["execution_authority_enabled"] is False
    assert {item["approval_state"] for item in queue["queue_items"]} == {
        "requested",
        "approved",
    }
    assert {item["durable_attachment_status"] for item in queue["queue_items"]} == {"attached"}


def test_run_attached_approval_queue_state_specific_refs_are_required() -> None:
    with pytest.raises(ValidationError, match="RUN_ATTACHED_APPROVAL_APPROVED_REFS_REQUIRED"):
        RunAttachedApprovalQueueItemReadModel(
            item_ref="run-approval-queue-item:test:approved",
            approval_request_ref="approval-request:test",
            run_ref="task-decomposition-run:test",
            step_ref="step:test",
            requested_scope_ref="approval-scope:test",
            approval_state="approved",
            approval_event_type="approval_attached",
            safe_summary="Approved state must include receipt and decision refs.",
        )

    with pytest.raises(ValidationError, match="RUN_ATTACHED_APPROVAL_RAW_PAYLOADS_DENIED"):
        RunAttachedApprovalQueueItemReadModel(
            item_ref="run-approval-queue-item:test:raw-denied",
            approval_request_ref="approval-request:test",
            run_ref="task-decomposition-run:test",
            step_ref="step:test",
            requested_scope_ref="approval-scope:test",
            approval_state="requested",
            approval_event_type="approval_required",
            raw_payloads_persisted=True,
            safe_summary="Requested state is safe refs only.",
        )

    with pytest.raises(ValidationError, match="RUN_ATTACHED_APPROVAL_BLOCKED_REFS_REQUIRED"):
        RunAttachedApprovalQueueItemReadModel(
            item_ref="run-approval-queue-item:test:block-denied",
            approval_request_ref="approval-request:test",
            run_ref="task-decomposition-run:test",
            step_ref="step:test",
            requested_scope_ref="approval-scope:test",
            approval_state="scope_mismatch_blocked",
            approval_event_type="approval_scope_mismatch_blocked",
            safe_summary="Scope mismatch must include blocked authority refs.",
        )


def test_run_attached_approval_event_receipt_surfaces_lifecycle_event(tmp_path: Path) -> None:
    storage = AppendFirstRunStorage(tmp_path / "runs.jsonl")
    run_id = "task-decomposition-run:approval-events"
    storage.append_run_record(
        DurableRunRecord(
            run_id=run_id,
            source_ref="source-ref:test:approval-events",
            safe_summary="Durable run exists for approval event tests.",
        ),
        idempotency_key="idempotency-ref:test:approval-events:run",
        audit_ref="audit-ref:test:approval-events:run",
        receipt_ref="receipt-ref:test:approval-events:run",
        rollback_ref="rollback-ref:test:approval-events:run",
        safe_summary="Durable run record created for approval queue testing.",
    )
    item = RunAttachedApprovalQueueItemReadModel(
        item_ref="run-approval-queue-item:test:required",
        approval_request_ref="approval-request:test:required",
        run_ref=run_id,
        step_ref="step:test:required",
        requested_scope_ref="approval-scope:test:required",
        approval_state="requested",
        approval_event_type="approval_required",
        evidence_refs=["evidence-ref:test:approval-required"],
        safe_summary="Approval request is attached to the durable run.",
    )

    record_run_attached_approval_event(
        storage,
        item,
        idempotency_key_ref="idempotency-ref:test:approval-required",
        audit_ref="audit-ref:test:approval-required",
        receipt_ref="receipt-ref:test:approval-required",
        rollback_ref="rollback-ref:test:approval-required",
    )

    receipt = storage.list_receipt_summaries(run_id)[0]
    assert receipt["schema_version"] == RUN_ATTACHED_APPROVAL_EVENT_RECEIPT_SCHEMA_VERSION
    assert receipt["run_approval_event_type"] == "approval_required"
    lifecycle = build_durable_run_lifecycle_read_model(storage, run_id)
    assert lifecycle is not None
    assert [event.event_type for event in lifecycle.events] == [
        "run_created",
        "approval_required",
    ]
    assert lifecycle.approval_refs_are_identifiers_only is True
    assert lifecycle.execution_authority_enabled is False


def test_task_decomposition_cli_inspects_run_attached_approval_queue(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry_path = str(tmp_path / "registry.json")

    assert task_decomposition_cli_main(["--registry", registry_path, "init-examples"]) == 0
    assert task_decomposition_cli_main(["--registry", registry_path, "inspect-approvals"]) == 0

    output = capsys.readouterr().out
    assert '"command_ref": "cli:task-decomposition:inspect-approvals"' in output
    assert '"safe_refs_only": true' in output
    assert '"approval_authority_enabled": false' in output
    assert '"execution_authority_enabled": false' in output
    assert "provider payload" not in output.lower()
    assert "raw prompt" not in output.lower()
