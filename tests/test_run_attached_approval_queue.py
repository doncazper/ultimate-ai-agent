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
    TaskDecompositionApprovalRevokeRequest,
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
    assert queue["summary"]["pending_count"] == 0
    assert queue["summary"]["approval_grants_created"] is True
    assert queue["summary"]["arbitrary_approval_ref_authority"] is False
    assert queue["summary"]["execution_authority_enabled"] is False
    assert {item["approval_state"] for item in queue["queue_items"]} == {
        "requested",
        "approved",
    }
    assert {item["durable_attachment_status"] for item in queue["queue_items"]} == {"attached"}
    approved_items = [
        item for item in queue["queue_items"] if item["approval_state"] == "approved"
    ]
    assert approved_items[0]["approval_scope_validation_ref"] is None
    assert queue["pending_approvals_by_run"] == []


def test_real_approval_paths_emit_named_durable_lifecycle_events(tmp_path: Path) -> None:
    service = _service(tmp_path)
    request = service.build_approval_request(
        TaskCapabilityApprovalRequestPayload(
            capability_id="capability:example-echo-summary",
            run_id="task-decomposition-run:approval-lifecycle",
            actor_id="local_actor",
        )
    )
    grant = service.grant_approval(
        TaskDecompositionApprovalGrantRequest(
            approval_request_id=request.approval_request_id,
            approved_by_actor_id="local_reviewer",
        )
    )
    service.revoke_approval(
        TaskDecompositionApprovalRevokeRequest(
            approval_ref=grant.approval_ref,
            reason="No longer needed for the local test run.",
        )
    )

    lifecycle = service.durable_run_lifecycle("task-decomposition-run:approval-lifecycle")

    assert lifecycle is not None
    event_types = [event["event_type"] for event in lifecycle["events"]]
    assert "approval_required" in event_types
    assert "approval_attached" in event_types
    assert "approval_revoked" in event_types
    queue = service.run_attached_approval_queue("task-decomposition-run:approval-lifecycle")
    assert queue["summary"]["approval_grants_created"] is True
    assert queue["summary"]["revoked_count"] == 1
    assert queue["summary"]["pending_count"] == 0
    assert {item["durable_attachment_status"] for item in queue["queue_items"]} == {"attached"}
    assert queue["pending_approvals_by_run"] == []


def test_durable_write_failure_does_not_persist_approval_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service = _service(tmp_path)

    def fail_append_run_record(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("durable write failed")

    monkeypatch.setattr(service.durable_run_storage, "append_run_record", fail_append_run_record)

    with pytest.raises(RuntimeError, match="durable write failed"):
        service.build_approval_request(
            TaskCapabilityApprovalRequestPayload(
                capability_id="capability:example-echo-summary",
                run_id="task-decomposition-run:approval-write-failure",
                actor_id="local_actor",
            )
        )

    persisted = service.registry_store.load_approval_state()
    assert persisted.requests == []
    assert persisted.grants == []
    assert service.approval_queue() == {"requests": [], "grants": []}


def test_durable_write_failure_does_not_create_visible_grant_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _service(tmp_path)
    request = service.build_approval_request(
        TaskCapabilityApprovalRequestPayload(
            capability_id="capability:example-echo-summary",
            run_id="task-decomposition-run:approval-grant-write-failure",
            actor_id="local_actor",
        )
    )

    def fail_append_run_record(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("durable write failed")

    monkeypatch.setattr(service.durable_run_storage, "append_run_record", fail_append_run_record)

    with pytest.raises(RuntimeError, match="durable write failed"):
        service.grant_approval(
            TaskDecompositionApprovalGrantRequest(
                approval_request_id=request.approval_request_id,
                approved_by_actor_id="local_reviewer",
            )
        )

    persisted = service.registry_store.load_approval_state()
    queue = service.approval_queue()
    assert persisted.grants == []
    assert queue["grants"] == []


def test_persist_failure_keeps_approval_visible_from_durable_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _service(tmp_path)

    def fail_save_approval_state(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("approval state save failed")

    monkeypatch.setattr(service.registry_store, "save_approval_state", fail_save_approval_state)

    with pytest.raises(RuntimeError, match="approval state save failed"):
        service.build_approval_request(
            TaskCapabilityApprovalRequestPayload(
                capability_id="capability:example-echo-summary",
                run_id="task-decomposition-run:approval-persist-failure",
                actor_id="local_actor",
            )
        )

    restarted = TaskDecompositionService(registry_store=service.registry_store)
    queue = restarted.run_attached_approval_queue("task-decomposition-run:approval-persist-failure")

    assert queue["summary"]["queue_item_count"] == 1
    assert queue["queue_items"][0]["approval_state"] == "requested"
    assert queue["queue_items"][0]["durable_attachment_status"] == "attached"


def test_durable_write_failure_restores_visible_grant_on_revoke(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _service(tmp_path)
    request = service.build_approval_request(
        TaskCapabilityApprovalRequestPayload(
            capability_id="capability:example-echo-summary",
            run_id="task-decomposition-run:approval-revoke-write-failure",
            actor_id="local_actor",
        )
    )
    grant = service.grant_approval(
        TaskDecompositionApprovalGrantRequest(
            approval_request_id=request.approval_request_id,
            approved_by_actor_id="local_reviewer",
        )
    )

    def fail_append_run_record(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("durable write failed")

    monkeypatch.setattr(service.durable_run_storage, "append_run_record", fail_append_run_record)

    with pytest.raises(RuntimeError, match="durable write failed"):
        service.revoke_approval(
            TaskDecompositionApprovalRevokeRequest(
                approval_ref=grant.approval_ref,
                reason="Durable failure should restore prior grant.",
            )
        )

    persisted = service.registry_store.load_approval_state()
    visible_grants = service.approval_queue()["grants"]
    assert [saved.status for saved in persisted.grants] == ["granted"]
    assert [saved["status"] for saved in visible_grants] == ["granted"]


def test_invalid_approval_run_id_uses_one_durable_run_ref(tmp_path: Path) -> None:
    service = _service(tmp_path)
    request = service.build_approval_request(
        TaskCapabilityApprovalRequestPayload(
            capability_id="capability:example-echo-summary",
            run_id="local approval run with spaces",
            actor_id="local_actor",
        )
    )

    queue = service.run_attached_approval_queue("local approval run with spaces")
    lifecycle = service.durable_run_lifecycle(request.run_id)

    assert lifecycle is not None
    assert queue["summary"]["queue_item_count"] == 1
    assert queue["queue_items"][0]["run_ref"] == request.run_id
    assert lifecycle["run_id"] == request.run_id


def test_duplicate_approval_request_does_not_duplicate_durable_events(tmp_path: Path) -> None:
    service = _service(tmp_path)
    payload = TaskCapabilityApprovalRequestPayload(
        capability_id="capability:example-echo-summary",
        run_id="task-decomposition-run:approval-idempotent",
        actor_id="local_actor",
    )

    first = service.build_approval_request(payload)
    second = service.build_approval_request(payload)
    lifecycle = service.durable_run_lifecycle("task-decomposition-run:approval-idempotent")

    assert first.approval_request_id == second.approval_request_id
    assert lifecycle is not None
    event_types = [event["event_type"] for event in lifecycle["events"]]
    assert event_types.count("approval_required") == 1


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
