from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.execution import (
    AppendFirstRunStorage,
    CONNECTOR_DELIVERY_SOURCE_FREEZE_REF,
    ConnectorDeliveryEnvelopeContract,
    ConnectorDeliveryReviewQueueItemReadModel,
    ConnectorDeliveryReviewQueueReadModel,
    ConnectorDeliveryTimelineEventContract,
    ConnectorDeliveryValidationContext,
    build_connector_delivery_review_queue,
    build_connector_delivery_read_model,
    record_connector_delivery_event,
    validate_connector_delivery_contract_payload,
    validate_connector_delivery_envelope,
)
from ultimate_ai_agent.core.execution import connector_delivery
from ultimate_ai_agent.core.execution.run_storage import DurableRunStorageDuplicateError
from ultimate_ai_agent.core.task_decomposition.cli import main as task_decomposition_cli_main
from ultimate_ai_agent.core.task_decomposition.runtime import (
    CapabilityRegistryStore,
    CapabilityRegistryStoreConfig,
    TaskDecompositionService,
)


RUN_REF = "task-decomposition-run:connector-delivery"
DELIVERY_REF = "connector-delivery-ref:test:email-proposal"
CONNECTOR_REF = "connector-ref:test:email"
CHANNEL_REF = "connector-channel-ref:test:email-draft"
TARGET_SESSION_REF = "target-session-ref:test:founder-local"
APPROVAL_REF = "approval-ref:test:connector-delivery:exact"


def _storage(tmp_path: Path) -> AppendFirstRunStorage:
    return AppendFirstRunStorage(tmp_path / "durable-runs.jsonl")


def _envelope(**overrides: object) -> ConnectorDeliveryEnvelopeContract:
    payload: dict[str, object] = {
        "delivery_ref": DELIVERY_REF,
        "run_ref": RUN_REF,
        "connector_ref": CONNECTOR_REF,
        "channel_ref": CHANNEL_REF,
        "target_session_ref": TARGET_SESSION_REF,
        "origin_ref": "origin-ref:test:action-inbox-proposal",
        "origin_cleanup_posture_ref": "origin-cleanup-posture-ref:test:no-effect",
        "outbound_approval_ref": APPROVAL_REF,
        "idempotency_key_ref": "idempotency-ref:test:connector-delivery",
        "redacted_subject_ref": "redacted-subject-ref:test:connector-delivery",
        "redacted_body_summary_ref": "redacted-body-summary-ref:test:connector-delivery",
        "attachment_refs": ["attachment-ref:test:metadata-only"],
        "evidence_refs": ["evidence-ref:test:connector-delivery"],
        "expected_receipt_refs": ["receipt-ref:test:connector-delivery:expected"],
        "rollback_posture_ref": "rollback-posture-ref:test:connector-delivery",
        "safe_disable_posture_ref": "safe-disable-posture-ref:test:connector-delivery",
        "audit_ref": "audit-ref:test:connector-delivery",
        "replay_ref": "replay-ref:test:connector-delivery",
    }
    payload.update(overrides)
    return ConnectorDeliveryEnvelopeContract.model_validate(payload)


def _event(
    state: str = "draft_created_metadata_only",
    **overrides: object,
) -> ConnectorDeliveryTimelineEventContract:
    envelope = _envelope()
    return ConnectorDeliveryTimelineEventContract.from_envelope(
        envelope,
        event_ref=f"connector-delivery-event-ref:test:{state}",
        delivery_state=state,  # type: ignore[arg-type]
        safe_summary="Connector delivery state is metadata-only and does not send or write.",
        **overrides,
    )


def _record_event(
    storage: AppendFirstRunStorage,
    event: ConnectorDeliveryTimelineEventContract,
    suffix: str,
) -> None:
    record_connector_delivery_event(
        storage,
        event,
        idempotency_key_ref=f"idempotency-ref:test:connector-delivery:{suffix}",
        audit_ref=f"audit-ref:test:connector-delivery:{suffix}",
        receipt_ref=f"receipt-ref:test:connector-delivery:{suffix}",
        rollback_ref=f"rollback-ref:test:connector-delivery:{suffix}",
    )


def test_valid_envelope_validates_contract_only_without_delivery_authority() -> None:
    envelope = _envelope()
    context = ConnectorDeliveryValidationContext(
        known_connector_refs=[CONNECTOR_REF],
        known_channel_refs=[CHANNEL_REF],
        outbound_approval_ref=APPROVAL_REF,
        outbound_approval_state="approved_metadata_only",
    )

    decision = validate_connector_delivery_envelope(envelope, context)

    assert envelope.source_connector_safety_freeze_ref == CONNECTOR_DELIVERY_SOURCE_FREEZE_REF
    assert decision.validation_status == "valid_contract_only"
    assert decision.contract_valid is True
    assert decision.blocked is False
    assert decision.delivery_permitted is False
    assert envelope.target_session_ref_grants_authority is False
    assert envelope.outbound_approval_ref_grants_authority is False
    assert envelope.connector_write_enabled is False
    assert envelope.connector_send_enabled is False
    assert envelope.account_sync_enabled is False
    assert envelope.oauth_enabled is False
    assert envelope.credential_collection_enabled is False


@pytest.mark.parametrize("approval_state", ["not_validated", "requested"])
def test_connector_delivery_requires_metadata_only_approval_posture(
    approval_state: str,
) -> None:
    envelope = _envelope()

    decision = validate_connector_delivery_envelope(
        envelope,
        ConnectorDeliveryValidationContext(
            known_connector_refs=[CONNECTOR_REF],
            known_channel_refs=[CHANNEL_REF],
            outbound_approval_ref=APPROVAL_REF,
            outbound_approval_state=approval_state,
        ),
    )

    assert decision.validation_status == "approval_required"
    assert decision.contract_valid is False
    assert decision.blocked is True
    assert decision.delivery_permitted is False
    assert "OUTBOUND_APPROVAL_REQUIRED" in decision.reason_codes


def test_missing_target_approval_idempotency_and_origin_cleanup_block() -> None:
    payload = _envelope().model_dump(mode="json")
    for key in [
        "target_session_ref",
        "outbound_approval_ref",
        "idempotency_key_ref",
        "origin_cleanup_posture_ref",
    ]:
        payload.pop(key)

    decision = validate_connector_delivery_envelope(payload)

    assert decision.blocked is True
    assert "MISSING_TARGET_SESSION_REF_BLOCKED" in decision.reason_codes
    assert "MISSING_OUTBOUND_APPROVAL_BLOCKED" in decision.reason_codes
    assert "MISSING_IDEMPOTENCY_REF_BLOCKED" in decision.reason_codes
    assert "MISSING_ORIGIN_CLEANUP_POSTURE_BLOCKED" in decision.reason_codes


def test_unknown_connector_and_channel_block_by_default() -> None:
    envelope = _envelope()

    decision = validate_connector_delivery_envelope(
        envelope,
        ConnectorDeliveryValidationContext(
            known_connector_refs=["connector-ref:test:calendar"],
            known_channel_refs=["connector-channel-ref:test:calendar-proposal"],
            outbound_approval_ref=APPROVAL_REF,
            outbound_approval_state="approved_metadata_only",
        ),
    )

    assert decision.blocked is True
    assert decision.delivery_performed is False
    assert "UNKNOWN_CONNECTOR_BLOCKED" in decision.reason_codes
    assert "UNKNOWN_CHANNEL_BLOCKED" in decision.reason_codes


def test_raw_body_contact_like_target_and_credentials_are_rejected() -> None:
    raw_reasons = validate_connector_delivery_contract_payload(
        {
            **_envelope().model_dump(mode="json"),
            "target_session_ref": "target-session-ref:test:founder@example.com",
            "raw_message_body": "raw message body with bearer token",
            "credential": "secret token",
        }
    )

    assert "CONNECTOR_DELIVERY_RAW_CONTENT_FIELD_BLOCKED" in raw_reasons
    assert "CONNECTOR_DELIVERY_RAW_CONTENT_VALUE_BLOCKED" in raw_reasons
    decision = validate_connector_delivery_envelope(
        {
            **_envelope().model_dump(mode="json"),
            "target_session_ref": "target-session-ref:test:founder@example.com",
        }
    )
    assert decision.blocked is True
    assert "CONNECTOR_DELIVERY_RAW_CONTENT_VALUE_BLOCKED" in decision.reason_codes


def test_approval_test_wildcard_source_drift_and_authority_flags_are_denied() -> None:
    with pytest.raises(ValidationError, match="APPROVAL_TEST_REF_BLOCKED"):
        _envelope(outbound_approval_ref="approval_test-ref:test:connector-delivery")
    with pytest.raises(ValidationError, match="WILDCARD_APPROVAL_REF_BLOCKED"):
        _envelope(outbound_approval_ref="approval-ref:test:all")
    with pytest.raises(ValidationError, match="CONNECTOR_DELIVERY_SOURCE_FREEZE_REF_MISMATCH"):
        _envelope(source_connector_safety_freeze_ref="connector-safety-freeze:m129")
    with pytest.raises(ValidationError, match="CONNECTOR_DELIVERY_AUTHORITY_DENIED:connector_send_enabled"):
        _envelope(connector_send_enabled=True)
    with pytest.raises(ValidationError, match="CONNECTOR_DELIVERY_SIDE_EFFECTS_DENIED"):
        _envelope(side_effects_performed=["send"])


def test_retry_failure_and_sent_not_supported_states_are_safe_ref_only(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    _record_event(storage, _event("pending_approval"), "pending")
    _record_event(
        storage,
        _event(
            "retry_scheduled_metadata_only",
            retry_ref="retry-ref:test:connector-delivery",
        ),
        "retry",
    )
    _record_event(
        storage,
        _event(
            "failed_metadata_only",
            failure_receipt_refs=["receipt-ref:test:connector-delivery:failure"],
        ),
        "failure",
    )
    _record_event(
        storage,
        _event(
            "sent_not_supported",
            blocked_reason_refs=["blocked-authority-ref:test:no-send"],
        ),
        "sent-not-supported",
    )

    read_model = build_connector_delivery_read_model(storage, run_ref=RUN_REF)

    assert read_model.schema_version == "connector_delivery_read_model.v1"
    assert read_model.event_count == 4
    assert read_model.delivery_count == 1
    assert read_model.pending_approval_count == 1
    assert read_model.blocked_count == 1
    assert read_model.retry_count == 1
    assert read_model.failure_count == 1
    assert read_model.delivery_statuses[0].no_send_action is True
    assert read_model.delivery_statuses[0].sent_not_supported_visible is True
    assert read_model.connector_sends_enabled is False
    assert read_model.connector_writes_enabled is False
    assert read_model.background_delivery_worker_enabled is False


def test_connector_delivery_review_queue_projects_safe_operator_review(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    _record_event(storage, _event("delivery_ready_not_sent"), "ready-not-sent")
    blocked_event = ConnectorDeliveryTimelineEventContract.from_envelope(
        _envelope(delivery_ref="connector-delivery-ref:test:email-blocked"),
        event_ref="connector-delivery-event-ref:test:delivery-blocked",
        delivery_state="delivery_blocked",
        blocked_reason_refs=["blocked-authority-ref:test:no-send"],
        safe_summary="Connector delivery is blocked as metadata only and does not send or write.",
    )
    _record_event(storage, blocked_event, "blocked")

    review_queue = build_connector_delivery_review_queue(storage, run_ref=RUN_REF)
    dumped = json.dumps(review_queue.model_dump(mode="json"), sort_keys=True)

    assert review_queue.schema_version == "connector_delivery_review_queue.v1"
    assert review_queue.source == "python_core_connector_delivery_review_queue_read_model"
    assert review_queue.backend_owned is True
    assert review_queue.delivery_count == 2
    assert review_queue.delivery_ready_not_sent_count == 1
    assert review_queue.blocked_count == 1
    assert review_queue.safe_refs_only is True
    assert review_queue.raw_payloads_persisted is False
    assert review_queue.no_send_action is True
    assert review_queue.connector_sends_enabled is False
    assert review_queue.connector_writes_enabled is False
    assert review_queue.delivery_execution_enabled is False
    assert review_queue.background_delivery_worker_enabled is False
    ready_item = next(
        item
        for item in review_queue.queue_items
        if item.latest_state == "delivery_ready_not_sent"
    )
    assert ready_item.delivery_state_label == "delivery ready metadata only / not sent"
    assert ready_item.delivery_execution_posture == "blocked_planned_no_delivery_execution"
    assert ready_item.redacted_subject_refs == ["redacted-subject-ref:test:connector-delivery"]
    assert ready_item.redacted_body_summary_refs == ["redacted-body-summary-ref:test:connector-delivery"]
    assert ready_item.outbound_approval_refs == [APPROVAL_REF]
    assert ready_item.idempotency_key_refs == ["idempotency-ref:test:connector-delivery"]
    assert "blocked-state:no-connector-send" in ready_item.blocked_authority_refs
    assert "blocked-state:no-background-delivery-worker" in ready_item.blocked_authority_refs
    blocked_item = next(
        item for item in review_queue.queue_items if item.latest_state == "delivery_blocked"
    )
    assert "blocked-authority-ref:test:no-send" in blocked_item.blocked_reason_refs
    assert "blocked-authority-ref:test:no-send" in review_queue.blocked_reason_refs
    assert "founder@example.com" not in dumped
    assert "raw message body" not in dumped.lower()
    assert "bearer token" not in dumped.lower()
    assert "/Users/" not in dumped


def test_connector_delivery_review_queue_denies_authority_flags(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    _record_event(storage, _event("delivery_ready_not_sent"), "ready-not-sent")
    review_queue = build_connector_delivery_review_queue(storage, run_ref=RUN_REF)
    item_payload = review_queue.queue_items[0].model_dump(mode="json")
    queue_payload = review_queue.model_dump(mode="json")

    with pytest.raises(
        ValidationError,
        match="CONNECTOR_DELIVERY_REVIEW_READY_STATE_MUST_LABEL_NOT_SENT",
    ):
        ConnectorDeliveryReviewQueueItemReadModel.model_validate(
            {**item_payload, "delivery_state_label": "delivery ready metadata only"}
        )

    for field_name in [
        "delivery_execution_performed",
        "connector_write_enabled",
        "connector_send_enabled",
        "account_sync_enabled",
        "oauth_enabled",
        "credential_collection_enabled",
        "provider_model_calls_enabled",
        "live_web_runtime_enabled",
        "browser_runtime_enabled",
        "shell_runtime_enabled",
        "background_delivery_worker_enabled",
        "scheduler_enabled",
    ]:
        with pytest.raises(ValidationError, match="CONNECTOR_DELIVERY_REVIEW_ITEM_AUTHORITY_DENIED"):
            ConnectorDeliveryReviewQueueItemReadModel.model_validate(
                {**item_payload, field_name: True}
            )

    for field_name in [
        "delivery_execution_enabled",
        "connector_writes_enabled",
        "connector_sends_enabled",
        "account_sync_enabled",
        "oauth_enabled",
        "credential_collection_enabled",
        "provider_model_calls_enabled",
        "live_web_runtime_enabled",
        "browser_runtime_enabled",
        "shell_runtime_enabled",
        "background_delivery_worker_enabled",
        "scheduler_enabled",
    ]:
        with pytest.raises(ValidationError, match="CONNECTOR_DELIVERY_REVIEW_QUEUE_AUTHORITY_DENIED"):
            ConnectorDeliveryReviewQueueReadModel.model_validate(
                {**queue_payload, field_name: True}
            )


def test_delivery_event_duplicate_idempotency_is_denied(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    event = _event("delivery_blocked", blocked_reason_refs=["blocked-authority-ref:test:no-send"])
    _record_event(storage, event, "duplicate")

    with pytest.raises(DurableRunStorageDuplicateError):
        _record_event(storage, event, "duplicate")


def test_task_decomposition_cli_inspects_connector_deliveries_safe_refs_only(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry_path = str(tmp_path / "registry.json")
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=registry_path))
    service = TaskDecompositionService(registry_store=store)
    _record_event(service.durable_run_storage, _event("pending_approval"), "pending")

    assert task_decomposition_cli_main(["--registry", registry_path, "inspect-connector-deliveries", RUN_REF]) == 0
    output = capsys.readouterr().out

    assert '"command_ref": "cli:task-decomposition:inspect-connector-deliveries"' in output
    assert '"safe_refs_only": true' in output
    assert '"connector_send_enabled": false' in output
    assert '"connector_write_enabled": false' in output
    assert '"background_delivery_worker_enabled": false' in output
    assert "raw message body" not in output.lower()
    assert "founder@example.com" not in output
    assert "bearer token" not in output.lower()


def test_task_decomposition_cli_inspects_connector_delivery_review_queue(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry_path = str(tmp_path / "registry.json")
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=registry_path))
    service = TaskDecompositionService(registry_store=store)
    _record_event(service.durable_run_storage, _event("delivery_ready_not_sent"), "ready-not-sent")

    assert (
        task_decomposition_cli_main(
            ["--registry", registry_path, "inspect-connector-delivery-review", RUN_REF]
        )
        == 0
    )
    output = capsys.readouterr().out

    assert '"command_ref": "cli:task-decomposition:inspect-connector-delivery-review"' in output
    assert '"schema_version": "connector_delivery_review_queue.v1"' in output
    assert '"delivery_state_label": "delivery ready metadata only / not sent"' in output
    assert '"safe_refs_only": true' in output
    assert '"connector_send_enabled": false' in output
    assert '"connector_write_enabled": false' in output
    assert '"background_delivery_worker_enabled": false' in output
    assert "raw message body" not in output.lower()
    assert "founder@example.com" not in output
    assert "bearer token" not in output.lower()


def test_connector_delivery_contract_adds_no_runtime_imports() -> None:
    source = inspect.getsource(connector_delivery)

    assert "import requests" not in source
    assert "import httpx" not in source
    assert "import openai" not in source
    assert "import anthropic" not in source
    assert "import subprocess" not in source
    assert "from playwright" not in source
    assert "from selenium" not in source
    assert "smtplib" not in source
