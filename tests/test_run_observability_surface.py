from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

import ultimate_ai_agent.api.app as api_app
from ultimate_ai_agent.core.execution import (
    BackgroundCoworkerWorkerEventContract,
    ConnectorDeliveryEnvelopeContract,
    ConnectorDeliveryTimelineEventContract,
    DurableRunRecord,
    DurableRunState,
    RunProgressEventReadModel,
    append_run_progress_event_receipt,
    record_background_coworker_worker_event,
    record_connector_delivery_event,
)
from ultimate_ai_agent.core.task_decomposition.cli import main as task_decomposition_cli_main
from ultimate_ai_agent.core.task_decomposition.runtime import (
    CapabilityRegistryStore,
    CapabilityRegistryStoreConfig,
    TaskCapabilityApprovalRequestPayload,
    TaskDecompositionApprovalGrantRequest,
    TaskDecompositionService,
)


RUN_REF = "task-decomposition-run:observability-surface"


def _service(tmp_path: Path) -> TaskDecompositionService:
    store = CapabilityRegistryStore(
        CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json"))
    )
    service = TaskDecompositionService(registry_store=store)
    service.ensure_examples()
    return service


def _progress_event(
    run_ref: str,
    *,
    sequence: int,
    event_type: str,
    suffix: str,
) -> RunProgressEventReadModel:
    return RunProgressEventReadModel.model_validate(
        {
            "run_ref": run_ref,
            "sequence": sequence,
            "event_type": event_type,
            "durable_run_event_ref": f"durable-run-event-ref:test:observability:{suffix}",
            "storage_entry_ref": f"durable-run-storage-entry:test:observability:{suffix}",
            "storage_entry_kind": "receipt",
            "redacted_delta_ref": (
                "redacted-delta-ref:test:observability"
                if event_type == "stream_delta_redacted"
                else None
            ),
            "evidence_refs": [f"evidence-ref:test:observability-{suffix}"],
            "safe_summary": "Recorded progress metadata uses safe refs only.",
        }
    )


def _record_observable_refs(service: TaskDecompositionService) -> None:
    request = service.build_approval_request(
        TaskCapabilityApprovalRequestPayload(
            capability_id="capability:example-echo-summary",
            run_id=RUN_REF,
            actor_id="local_actor",
        )
    )
    service.grant_approval(
        TaskDecompositionApprovalGrantRequest(
            approval_request_id=request.approval_request_id,
            approved_by_actor_id="local_reviewer",
        )
    )
    append_run_progress_event_receipt(
        service.durable_run_storage,
        _progress_event(
            RUN_REF,
            sequence=3,
            event_type="stream_started",
            suffix="stream-started",
        ),
        idempotency_key_ref="idempotency-ref:test:observability-stream-started",
        audit_ref="audit-ref:test:observability-stream-started",
        receipt_ref="receipt-ref:test:observability-stream-started",
        rollback_ref="rollback-ref:test:observability-stream-started",
    )
    append_run_progress_event_receipt(
        service.durable_run_storage,
        _progress_event(
            RUN_REF,
            sequence=4,
            event_type="stream_delta_redacted",
            suffix="stream-delta",
        ),
        idempotency_key_ref="idempotency-ref:test:observability-progress",
        audit_ref="audit-ref:test:observability-progress",
        receipt_ref="receipt-ref:test:observability-progress",
        rollback_ref="rollback-ref:test:observability-progress",
    )

    envelope = ConnectorDeliveryEnvelopeContract(
        delivery_ref="connector-delivery-ref:test:observability",
        run_ref=RUN_REF,
        connector_ref="connector-ref:test:email",
        channel_ref="connector-channel-ref:test:draft",
        target_session_ref="target-session-ref:test:founder-local",
        origin_ref="origin-ref:test:observability",
        origin_cleanup_posture_ref="origin-cleanup-posture-ref:test:no-effect",
        outbound_approval_ref="approval-ref:test:connector:metadata-only",
        idempotency_key_ref="idempotency-ref:test:connector:observability",
        redacted_subject_ref="redacted-subject-ref:test:connector",
        redacted_body_summary_ref="redacted-body-summary-ref:test:connector",
        evidence_refs=["evidence-ref:test:connector-observability"],
        expected_receipt_refs=["receipt-ref:test:connector:expected"],
        rollback_posture_ref="rollback-posture-ref:test:connector",
        safe_disable_posture_ref="safe-disable-posture-ref:test:connector",
        audit_ref="audit-ref:test:connector",
        replay_ref="replay-ref:test:connector",
    )
    record_connector_delivery_event(
        service.durable_run_storage,
        ConnectorDeliveryTimelineEventContract.from_envelope(
            envelope,
            event_ref="connector-delivery-event-ref:test:observability:pending",
            delivery_state="pending_approval",
            safe_summary="Connector delivery waits for metadata-only approval.",
        ),
        idempotency_key_ref="idempotency-ref:test:connector:record",
        audit_ref="audit-ref:test:connector:record",
        receipt_ref="receipt-ref:test:connector:record",
        rollback_ref="rollback-ref:test:connector:record",
    )

    record_background_coworker_worker_event(
        service.durable_run_storage,
        BackgroundCoworkerWorkerEventContract(
            event_ref="coworker-event-ref:test:observability:handoff",
            worker_ref="worker-ref:test:observability",
            worker_kind="review_worker",
            event_type="handoff_recorded",
            run_ref=RUN_REF,
            parent_run_ref=RUN_REF,
            child_run_ref="task-decomposition-run:observability-child",
            handoff_ref="handoff-ref:test:observability",
            lease_ref="lease-ref:test:observability",
            heartbeat_ref="heartbeat-ref:test:observability",
            evidence_refs=["evidence-ref:test:coworker-observability"],
            blocked_authority_refs=["blocked-state:test:no-coworker-runtime"],
            safe_summary="Coworker handoff is metadata-only.",
        ),
        idempotency_key_ref="idempotency-ref:test:coworker:record",
        audit_ref="audit-ref:test:coworker:record",
        receipt_ref="receipt-ref:test:coworker:record",
        rollback_ref="rollback-ref:test:coworker:record",
    )


def _append_orchestration_state(
    service: TaskDecompositionService,
    *,
    state: DurableRunState,
    suffix: str,
) -> None:
    failure_refs = []
    if state in {
        DurableRunState.blocked,
        DurableRunState.failed,
        DurableRunState.dead_lettered,
    }:
        failure_refs = [f"failure-ref:test:orchestration:{suffix}"]
    restart_refs = []
    if state in {DurableRunState.restart_recovery, DurableRunState.dead_lettered}:
        restart_refs = [f"restart-ref:test:orchestration:{suffix}"]
    service.durable_run_storage.append_run_record(
        DurableRunRecord(
            run_id=RUN_REF,
            source_ref=f"source-ref:test:orchestration:{suffix}",
            state=state,
            safe_summary=f"State-only durable run {suffix} summary.",
            metadata={"approval_refs": [f"approval-ref:test:orchestration:{suffix}"]},
            evidence_refs=[f"evidence-ref:test:orchestration:{suffix}"],
            failure_refs=failure_refs,
            restart_refs=restart_refs,
        ),
        idempotency_key=f"idempotency-ref:test:orchestration:{suffix}",
        audit_ref=f"audit-ref:test:orchestration:{suffix}",
        receipt_ref=f"receipt-ref:test:orchestration:{suffix}",
        rollback_ref=f"rollback-ref:test:orchestration:{suffix}",
        safe_summary=f"State-only durable run {suffix} checkpoint.",
        evidence_refs=[f"evidence-ref:test:orchestration:{suffix}"],
    )


def test_run_observability_aggregates_read_only_backend_refs(tmp_path: Path) -> None:
    service = _service(tmp_path)
    _record_observable_refs(service)

    observability = service.run_observability(
        RUN_REF,
        lifecycle_limit=20,
        related_limit=20,
    )

    assert observability["schema_version"] == "run_observability_read_model.v1"
    assert observability["source"] == "python_core_run_observability_read_model"
    assert observability["backend_owned"] is True
    assert observability["status"] == "implemented_read_only"
    assert observability["run_ref"] == RUN_REF
    assert observability["lifecycle"]["schema_version"] == "durable_run_lifecycle_read_model.v1"
    assert observability["progress"]["schema_version"] == "run_progress_read_model.v1"
    assert observability["approval_queue"]["schema_version"] == "run_attached_approval_queue.v1"
    assert observability["coworker_workers"]["schema_version"] == "background_coworker_read_model.v1"
    assert observability["connector_deliveries"]["schema_version"] == "connector_delivery_read_model.v1"
    assert (
        observability["connector_delivery_review_queue"]["schema_version"]
        == "connector_delivery_review_queue.v1"
    )
    assert observability["current_phase_ref"]
    assert observability["current_phase_status"]
    assert observability["current_step_ref"]
    assert observability["current_step_status"]
    assert observability["checkpoint_summaries"]
    assert observability["retry_recovery_posture"]["retry_execution_enabled"] is False
    assert observability["retry_recovery_posture"]["recovery_execution_enabled"] is False
    assert observability["approval_wait_state"]["approval_refs_are_identifiers_only"] is True
    assert observability["approval_wait_state"]["approval_ref_grants_authority"] is False
    assert observability["approval_wait_state"]["resume_execution_enabled"] is False
    assert observability["cancellation_dead_letter_state"]["cancel_execution_enabled"] is False
    assert (
        observability["cancellation_dead_letter_state"]["dead_letter_execution_enabled"]
        is False
    )
    assert observability["event_count"] >= 1
    assert observability["progress_event_count"] >= 1
    assert observability["approval_item_count"] >= 2
    assert observability["coworker_event_count"] == 1
    assert observability["connector_delivery_count"] == 1
    assert observability["connector_delivery_review_count"] == 1
    assert RUN_REF in observability["run_refs"]
    assert observability["approval_refs"]
    assert observability["progress_event_refs"]
    assert observability["coworker_handoff_refs"]
    assert observability["connector_delivery_refs"]
    assert observability["receipt_refs"]
    assert observability["evidence_refs"]
    assert observability["proof_refs"]
    assert observability["safe_refs_only"] is True
    assert observability["redacted_summaries_only"] is True
    assert observability["raw_payloads_persisted"] is False
    assert observability["prompt_content_stored"] is False
    assert observability["response_content_stored"] is False
    assert observability["provider_payload_content_stored"] is False
    assert observability["ui_mutation_controls_enabled"] is False
    assert observability["cancel_resume_controls_enabled"] is False
    assert observability["live_streaming_runtime_enabled"] is False
    assert observability["provider_model_calls_enabled"] is False
    assert observability["tool_execution_enabled"] is False
    assert observability["connector_writes_enabled"] is False
    assert observability["connector_sends_enabled"] is False
    assert observability["background_worker_enabled"] is False
    assert observability["scheduler_enabled"] is False
    assert observability["autonomous_execution_enabled"] is False

    serialized = json.dumps(observability)
    assert "/Users/" not in serialized
    assert "raw prompt" not in serialized.lower()
    assert "raw response" not in serialized.lower()
    assert "provider payload" not in serialized.lower()


def test_run_observability_exposes_recovery_and_dead_letter_posture(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    _append_orchestration_state(
        service,
        state=DurableRunState.created,
        suffix="created",
    )
    _append_orchestration_state(
        service,
        state=DurableRunState.restart_recovery,
        suffix="restart-recovery",
    )
    _append_orchestration_state(
        service,
        state=DurableRunState.dead_lettered,
        suffix="dead-letter",
    )

    observability = service.run_observability(
        RUN_REF,
        lifecycle_limit=20,
        related_limit=20,
    )

    assert observability["status"] == "implemented_read_only"
    assert observability["current_phase_status"] == "failed"
    assert observability["checkpoint_summaries"][-1]["checkpoint_status"] == "failed"
    assert observability["checkpoint_summaries"][-1]["raw_payloads_persisted"] is False
    assert observability["checkpoint_summaries"][-1]["execution_performed"] is False
    assert (
        observability["retry_recovery_posture"]["retry_state"]
        == "retry_metadata_visible_execution_blocked"
    )
    assert observability["retry_recovery_posture"]["retry_refs"]
    assert observability["retry_recovery_posture"]["recovery_refs"]
    assert observability["retry_recovery_posture"]["retry_execution_enabled"] is False
    assert observability["retry_recovery_posture"]["recovery_execution_enabled"] is False
    assert (
        observability["cancellation_dead_letter_state"]["dead_letter_state"]
        == "dead_letter_metadata_visible_execution_blocked"
    )
    assert observability["cancellation_dead_letter_state"]["dead_letter_refs"]
    assert observability["cancellation_dead_letter_state"]["cancel_execution_enabled"] is False
    assert (
        observability["cancellation_dead_letter_state"]["dead_letter_execution_enabled"]
        is False
    )
    assert observability["redacted_error_summaries"]
    assert all(
        summary["raw_error_omitted"] is True
        for summary in observability["redacted_error_summaries"]
    )
    serialized = json.dumps(observability)
    assert "/Users/" not in serialized
    assert "raw prompt" not in serialized.lower()
    assert "provider payload" not in serialized.lower()


def test_run_observability_reports_missing_state_without_writing(tmp_path: Path) -> None:
    service = _service(tmp_path)

    observability = service.run_observability()

    assert observability["status"] == "state_not_found_no_write"
    assert (
        observability["run_ref"]
        == "task-decomposition-run:observability:state-not-found"
    )
    assert observability["lifecycle"] is None
    assert observability["progress"] is None
    assert observability["current_phase_status"] == "state_not_found"
    assert observability["current_step_status"] == "inspect_refs_only"
    assert observability["checkpoint_summaries"] == []
    assert (
        observability["retry_recovery_posture"]["retry_state"]
        == "state_not_found_no_retry_execution"
    )
    assert observability["approval_wait_state"]["wait_state"] in {
        "no_pending_approval_wait",
        "waiting_for_exact_approval_ref",
    }
    assert (
        observability["approval_wait_state"]["pending_count"]
        == len(observability["approval_wait_state"]["pending_approval_refs"])
    )
    assert observability["approval_wait_state"]["resume_execution_enabled"] is False
    assert (
        observability["cancellation_dead_letter_state"]["cancellation_state"]
        == "state_not_found_no_cancel_execution"
    )
    assert observability["redacted_error_summaries"] == []
    assert observability["safe_refs_only"] is True
    assert observability["ui_mutation_controls_enabled"] is False
    assert observability["connector_sends_enabled"] is False
    assert observability["background_worker_enabled"] is False


def test_cli_inspects_run_observability_safe_refs_only(
    tmp_path: Path,
    capsys: object,
) -> None:
    service = _service(tmp_path)
    _record_observable_refs(service)

    exit_code = task_decomposition_cli_main(
        [
            "--registry",
            str(tmp_path / "registry.json"),
            "inspect-run-observability",
            RUN_REF,
            "--lifecycle-limit",
            "20",
            "--related-limit",
            "20",
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["schema_version"] == "task-decomposition-cli-inspect-run-observability.v1"
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True
    assert payload["cancel_resume_controls_enabled"] is False
    assert payload["connector_sends_enabled"] is False
    assert payload["background_worker_enabled"] is False
    assert payload["run_observability"]["run_ref"] == RUN_REF
    assert payload["run_observability"]["connector_delivery_refs"]
    assert "raw prompt" not in output.lower()
    assert "/Users/" not in output


def test_control_center_run_observability_route_is_read_only(
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    service = _service(tmp_path)
    _record_observable_refs(service)
    monkeypatch.setattr(api_app, "_task_decomposition_service", service)
    client = TestClient(api_app.app)

    response = client.get(
        "/control-center/runs/observability",
        params={"run_ref": RUN_REF, "lifecycle_limit": 20, "related_limit": 20},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_runs_observability"
    assert body["redactions_applied"] == [
        "safe_refs_only",
        "redacted_summaries_only",
        "raw_payloads_omitted",
        "read_only_control_center_projection",
        "runtime_authority_blocked",
    ]
    data = body["data"]
    assert data["schema_version"] == "run_observability_read_model.v1"
    assert data["source"] == "python_core_run_observability_read_model"
    assert data["backend_owned"] is True
    assert data["run_ref"] == RUN_REF
    assert data["safe_refs_only"] is True
    assert data["ui_mutation_controls_enabled"] is False
    assert data["cancel_resume_controls_enabled"] is False
    assert data["live_streaming_runtime_enabled"] is False
    assert data["provider_model_calls_enabled"] is False
    assert data["tool_execution_enabled"] is False
    assert data["connector_writes_enabled"] is False
    assert data["connector_sends_enabled"] is False
    assert data["background_worker_enabled"] is False
    assert data["scheduler_enabled"] is False
