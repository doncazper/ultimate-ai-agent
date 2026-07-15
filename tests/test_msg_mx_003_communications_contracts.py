from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.communications import (
    CommunicationsActionEnvelope,
    CommunicationsActionPosture,
    CommunicationsAdapterDisabled,
    CommunicationsProviderRegistry,
    CommunicationsReceipt,
    CommunicationsReceiptOutcome,
    CommunicationsRedactionStatus,
    CommunicationsRollbackPosture,
    CommunicationsRoomAIPolicy,
    CommunicationsRoomAIPolicyKind,
    DisabledMatrixAdapter,
    build_default_communications_service,
    communications_idempotency_binding_ref,
)
from ultimate_ai_agent.core.capability_availability import (
    CapabilityAvailabilitySnapshot,
)


CHECKED_AT = datetime(2026, 7, 14, tzinfo=timezone.utc)


def test_disabled_matrix_availability_preserves_unknown_and_blocked_truth() -> None:
    descriptor = DisabledMatrixAdapter().inspect_descriptor(checked_at=CHECKED_AT)
    snapshot = descriptor.availability

    assert descriptor.provider_status.value == "unsupported"
    assert snapshot.catalog_status.value == "unsupported"
    assert snapshot.compatibility_status.value == "unknown"
    assert snapshot.configuration_status.value == "not_configured"
    assert snapshot.health_status.value == "unknown"
    assert snapshot.authority_posture.value == "blocked"
    assert snapshot.resource_status.value == "unknown"
    assert snapshot.cost_posture.value == "unknown"
    assert snapshot.safe_disable_status.value == "unknown"
    assert snapshot.freshness_status.value == "unknown"
    assert snapshot.runtime_readiness_status.value == "unknown"
    assert "MATRIX_NETWORK_AUTHORITY_NOT_ACCEPTED" in snapshot.blocker_codes
    assert not hasattr(snapshot, "authorized")
    assert not hasattr(snapshot, "callable")


@pytest.mark.parametrize(
    "method",
    [
        "authenticate",
        "synchronize",
        "read_messages",
        "send_message",
        "initialize_crypto",
        "transfer_media",
    ],
)
def test_disabled_matrix_adapter_runtime_methods_fail_closed(method: str) -> None:
    with pytest.raises(
        CommunicationsAdapterDisabled, match="MATRIX_ADAPTER_RUNTIME_DISABLED"
    ):
        getattr(DisabledMatrixAdapter(), method)()


def test_default_service_is_empty_bounded_and_content_free() -> None:
    service = build_default_communications_service(checked_at=CHECKED_AT)
    rooms = service.list_rooms(limit=50)
    failed = service.list_failed_sends(limit=50)
    receipt = service.lookup_receipt("receipt-ref:communications:contract-inspection")

    assert rooms.items == []
    assert rooms.pagination.returned_count == 0
    assert rooms.message_read_performed is False
    assert rooms.raw_content_omitted is True
    assert failed.receipt_refs == []
    assert failed.send_performed is False
    assert receipt.outcome == CommunicationsReceiptOutcome.not_executed
    assert receipt.network_performed is False
    assert receipt.authentication_performed is False
    assert receipt.message_read_performed is False
    assert receipt.message_sent is False
    assert receipt.raw_content_stored is False
    assert receipt.provider_payload_persisted is False
    assert receipt.approval_or_lease_minted is False


@pytest.mark.parametrize("limit", [0, 51, -1])
def test_service_rejects_unbounded_pages(limit: int) -> None:
    service = build_default_communications_service(checked_at=CHECKED_AT)
    with pytest.raises(ValueError, match="COMMUNICATIONS_PAGE_LIMIT_OUT_OF_BOUNDS"):
        service.list_rooms(limit=limit)


def test_registry_rejects_duplicates_instead_of_overwriting() -> None:
    descriptor = DisabledMatrixAdapter().inspect_descriptor(checked_at=CHECKED_AT)
    with pytest.raises(ValueError, match="COMMUNICATIONS_PROVIDER_REF_DUPLICATE"):
        CommunicationsProviderRegistry([descriptor, descriptor])


def test_registry_rejects_unbounded_provider_inventory() -> None:
    descriptor = DisabledMatrixAdapter().inspect_descriptor(checked_at=CHECKED_AT)
    descriptors = []
    for index in range(17):
        provider_ref = f"provider-ref:matrix:{index}"
        availability = descriptor.availability.model_copy(
            update={"provider_ref": provider_ref}
        )
        descriptors.append(
            descriptor.model_copy(
                update={
                    "provider_ref": provider_ref,
                    "availability": availability,
                }
            )
        )
    with pytest.raises(ValueError, match="COMMUNICATIONS_PROVIDER_LIMIT_EXCEEDED"):
        CommunicationsProviderRegistry(descriptors)


def test_action_envelope_is_proposal_only_and_approval_ref_is_not_authority() -> None:
    request_fingerprint_ref = "fingerprint-ref:communications:test"
    idempotency_ref = "idempotency-ref:communications:test"
    envelope = CommunicationsActionEnvelope(
        envelope_ref="envelope-ref:communications:test",
        request_ref="request-ref:communications:test",
        request_fingerprint_ref=request_fingerprint_ref,
        capability_ref="capability-ref:communications:send",
        authority_domain_ref="authority-domain-ref:communications-data",
        provider_ref="provider-ref:communications:matrix",
        adapter_ref="adapter-ref:communications:matrix-disabled",
        target_refs=["conversation-ref:communications:test"],
        approval_ref="approval-ref:communications:identifier-only",
        idempotency_ref=idempotency_ref,
        idempotency_binding_ref=communications_idempotency_binding_ref(
            request_fingerprint_ref=request_fingerprint_ref,
            idempotency_ref=idempotency_ref,
        ),
        expected_receipt_ref="receipt-ref:communications:expected",
        rollback_ref="rollback-ref:communications:readiness-required",
        safe_disable_ref="safe-disable-ref:communications:required",
        posture=CommunicationsActionPosture.proposal_only,
        rollback_posture=CommunicationsRollbackPosture.readiness_required,
    )
    assert envelope.approval_ref_authorizes_execution is False
    assert envelope.authority_granted is False
    assert envelope.execution_permitted is False
    assert envelope.mutation_performed is False
    assert envelope.redaction_status == CommunicationsRedactionStatus.safe_refs_only

    with pytest.raises(ValidationError):
        envelope.model_copy(update={"authority_granted": True})

    with pytest.raises(
        ValidationError, match="COMMUNICATIONS_IDEMPOTENCY_BINDING_MISMATCH"
    ):
        envelope.model_copy(
            update={"idempotency_binding_ref": "binding-ref:communications:mismatch"}
        )


def test_room_ai_policy_cannot_enable_context_or_memory() -> None:
    policy = CommunicationsRoomAIPolicy(
        policy_ref="policy-ref:communications:room-ai-off",
        conversation_ref="conversation-ref:communications:test",
    )
    assert policy.policy == CommunicationsRoomAIPolicyKind.off
    assert policy.context_materialization_allowed is False
    assert policy.memory_write_allowed is False

    with pytest.raises(ValidationError):
        policy.model_copy(update={"policy": "scoped_allow"})


@pytest.mark.parametrize(
    "provider_ref",
    [
        "provider-ref:communications:@private-user",
        "provider-ref:communications:private.example.com",
        "provider-ref:communications:private.example.ai",
        "provider-ref:communications:private.example.co",
        "provider-ref:communications:localhost",
        "provider-ref:communications:127.0.0.1",
        "provider-ref:communications:2001:db8::1",
        "provider-ref:communications:[2001:db8::1]",
        "provider-ref:communications:::1",
        "provider-ref:communications:2001:db8::",
    ],
)
def test_contract_rejects_unhashed_identity_and_host_refs(provider_ref: str) -> None:
    receipt = build_default_communications_service(
        checked_at=CHECKED_AT
    ).lookup_receipt("receipt-ref:communications:contract-inspection")
    with pytest.raises(ValidationError):
        receipt.model_copy(update={"provider_ref": provider_ref})


@pytest.mark.parametrize(
    "safe_summary",
    [
        "Matrix homeserver private.example.ai is blocked.",
        "Matrix endpoint 127.0.0.1 is blocked.",
        "Matrix endpoint [2001:db8::1] is blocked.",
        "Matrix endpoint ::1 is blocked.",
        "Matrix endpoint 2001:db8:: is blocked.",
        "Matrix endpoint :: is blocked.",
    ],
)
def test_contract_rejects_host_or_ip_in_safe_summary(safe_summary: str) -> None:
    receipt = build_default_communications_service(
        checked_at=CHECKED_AT
    ).lookup_receipt("receipt-ref:communications:contract-inspection")
    with pytest.raises(ValidationError):
        receipt.model_copy(update={"safe_summary": safe_summary})


def test_provider_descriptor_binds_and_redacts_nested_availability_refs() -> None:
    descriptor = DisabledMatrixAdapter().inspect_descriptor(checked_at=CHECKED_AT)
    payload = descriptor.availability.model_dump(mode="python")
    payload["provider_ref"] = "provider-ref:communications:other"
    mismatched = CapabilityAvailabilitySnapshot.model_validate(payload)
    with pytest.raises(
        ValidationError, match="COMMUNICATIONS_AVAILABILITY_SCOPE_MISMATCH"
    ):
        descriptor.model_copy(update={"availability": mismatched})

    payload = descriptor.availability.model_dump(mode="python")
    payload["source_ref"] = "source-ref:communications:private.example.ai"
    unsafe = CapabilityAvailabilitySnapshot.model_validate(payload)
    with pytest.raises(
        ValidationError, match="contains unhashed identity or host data"
    ):
        descriptor.model_copy(update={"availability": unsafe})


def test_contract_rejects_content_smuggled_through_reason_codes() -> None:
    receipt = build_default_communications_service(
        checked_at=CHECKED_AT
    ).lookup_receipt("receipt-ref:communications:contract-inspection")
    with pytest.raises(ValidationError, match="COMMUNICATIONS_REASON_CODE_INVALID"):
        receipt.model_copy(update={"reason_codes": ["private conversation text"]})


def test_contract_rejects_raw_or_secret_like_extra_fields_without_echo() -> None:
    payload = {
        "receipt_ref": "receipt-ref:communications:test",
        "operation_ref": "operation-ref:communications:test",
        "request_ref": "request-ref:communications:test",
        "provider_ref": "provider-ref:communications:matrix",
        "outcome": "blocked",
        "occurred_at": CHECKED_AT,
        "redaction_status": CommunicationsRedactionStatus.safe_refs_only,
        "safe_summary": "The blocked contract stored no provider content.",
        "raw_message_body": "private ordinary conversation text",
    }
    with pytest.raises(ValidationError) as exc_info:
        CommunicationsReceipt.model_validate(payload)
    assert "private ordinary conversation text" not in str(exc_info.value)


def test_communications_runtime_modules_import_no_network_or_matrix_sdk() -> None:
    root = Path("src/ultimate_ai_agent/core/communications")
    denied_roots = {
        "aiohttp",
        "httpx",
        "matrix_client",
        "nio",
        "requests",
        "urllib3",
    }
    imported: set[str] = set()
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(denied_roots)
