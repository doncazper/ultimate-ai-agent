from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from ultimate_ai_agent.core.communications.contracts import (
    COMMUNICATIONS_MAX_PAGE_SIZE,
    CommunicationConversation,
    CommunicationsFailedSendPage,
    CommunicationsFreshnessStatus,
    CommunicationsPagination,
    CommunicationsProviderDescriptor,
    CommunicationsReceipt,
    CommunicationsReceiptOutcome,
    CommunicationsRedactionStatus,
    CommunicationsRoomPage,
    CommunicationsSecurityPosture,
    CommunicationsSessionPosture,
    CommunicationsSessionStatus,
)
from ultimate_ai_agent.core.communications.matrix_disabled import (
    DisabledMatrixAdapter,
    MATRIX_PROVIDER_REF,
)
from ultimate_ai_agent.core.communications.registry import (
    CommunicationsProviderRegistry,
)
from ultimate_ai_agent.core.execution.validation import validate_execution_ref
from ultimate_ai_agent.core.time import utc_now


class CommunicationsReceiptNotFound(LookupError):
    pass


class CommunicationsService:
    """Backend-owned, injected communications inspection truth."""

    def __init__(
        self,
        *,
        registry: CommunicationsProviderRegistry,
        session: CommunicationsSessionPosture,
        rooms: Iterable[CommunicationConversation] = (),
        failed_send_receipt_refs: Iterable[str] = (),
        security: CommunicationsSecurityPosture,
        receipts: Iterable[CommunicationsReceipt] = (),
    ) -> None:
        self._registry = registry
        self._session = session.model_copy(deep=True)
        self._rooms = tuple(room.model_copy(deep=True) for room in rooms)
        self._failed_send_receipt_refs = tuple(failed_send_receipt_refs)
        self._security = security.model_copy(deep=True)
        receipt_items = tuple(receipts)
        self._receipts = {
            receipt.receipt_ref: receipt.model_copy(deep=True)
            for receipt in receipt_items
        }
        if len(self._receipts) != len(receipt_items):
            raise ValueError("COMMUNICATIONS_RECEIPT_REF_DUPLICATE")
        for receipt_ref in self._failed_send_receipt_refs:
            validate_execution_ref(
                receipt_ref, "communications_failed_send_receipt_ref"
            )

    def inspect_provider_posture(self) -> tuple[CommunicationsProviderDescriptor, ...]:
        return self._registry.list_descriptors()

    def inspect_session_posture(self) -> CommunicationsSessionPosture:
        return self._session.model_copy(deep=True)

    def list_rooms(self, *, limit: int = 25) -> CommunicationsRoomPage:
        bounded_limit = _validated_limit(limit)
        items = [room.model_copy(deep=True) for room in self._rooms[:bounded_limit]]
        next_ref = (
            "cursor-ref:communications:rooms:next"
            if len(self._rooms) > bounded_limit
            else None
        )
        return CommunicationsRoomPage(
            items=items,
            pagination=CommunicationsPagination(
                page_size=bounded_limit,
                returned_count=len(items),
                next_cursor_ref=next_ref,
            ),
            freshness=CommunicationsFreshnessStatus.unknown,
            reason_codes=["COMMUNICATIONS_ROOM_INSPECTION_CONTRACT_AVAILABLE"],
            blocker_codes=["MATRIX_ACCOUNT_SESSION_NOT_CONFIGURED"],
            safe_summary="No room data is available because Matrix synchronization is disabled.",
        )

    def list_failed_sends(self, *, limit: int = 25) -> CommunicationsFailedSendPage:
        bounded_limit = _validated_limit(limit)
        refs = list(self._failed_send_receipt_refs[:bounded_limit])
        next_ref = (
            "cursor-ref:communications:failed-sends:next"
            if len(self._failed_send_receipt_refs) > bounded_limit
            else None
        )
        return CommunicationsFailedSendPage(
            receipt_refs=refs,
            pagination=CommunicationsPagination(
                page_size=bounded_limit,
                returned_count=len(refs),
                next_cursor_ref=next_ref,
            ),
            reason_codes=["COMMUNICATIONS_FAILED_SEND_INSPECTION_CONTRACT_AVAILABLE"],
            blocker_codes=["COMMUNICATIONS_OUTBOX_RUNTIME_NOT_IMPLEMENTED"],
            safe_summary="No send runtime exists; failed-send inspection is empty and blocked.",
        )

    def inspect_security_posture(self) -> CommunicationsSecurityPosture:
        return self._security.model_copy(deep=True)

    def lookup_receipt(self, receipt_ref: str) -> CommunicationsReceipt:
        try:
            validate_execution_ref(receipt_ref, "communications_receipt_ref")
        except ValueError as exc:
            raise CommunicationsReceiptNotFound(
                "COMMUNICATIONS_RECEIPT_NOT_FOUND"
            ) from exc
        receipt = self._receipts.get(receipt_ref)
        if receipt is None:
            raise CommunicationsReceiptNotFound("COMMUNICATIONS_RECEIPT_NOT_FOUND")
        return receipt.model_copy(deep=True)


def build_default_communications_service(
    *, checked_at: datetime | None = None
) -> CommunicationsService:
    observed_at = checked_at or utc_now()
    descriptor = DisabledMatrixAdapter().inspect_descriptor(checked_at=observed_at)
    receipt = CommunicationsReceipt(
        receipt_ref="receipt-ref:communications:contract-inspection",
        operation_ref="operation-ref:communications:contract-inspection",
        request_ref="request-ref:communications:contract-inspection",
        provider_ref=MATRIX_PROVIDER_REF,
        outcome=CommunicationsReceiptOutcome.not_executed,
        occurred_at=observed_at,
        reason_codes=["COMMUNICATIONS_CONTRACT_INSPECTED"],
        blocker_codes=["MATRIX_RUNTIME_DISABLED"],
        evidence_refs=["evidence-ref:communications:contract-inspection"],
        redaction_status=CommunicationsRedactionStatus.safe_refs_only,
        safe_summary="Communications contracts were inspected without provider execution.",
    )
    return CommunicationsService(
        registry=CommunicationsProviderRegistry([descriptor]),
        session=CommunicationsSessionPosture(
            provider_ref=MATRIX_PROVIDER_REF,
            session_ref="session-ref:communications:matrix:not-configured",
            status=CommunicationsSessionStatus.not_configured,
            freshness=CommunicationsFreshnessStatus.unknown,
            reason_codes=["MATRIX_SESSION_DECLARATION_ONLY"],
            blocker_codes=[
                "MATRIX_NETWORK_AUTHORITY_NOT_ACCEPTED",
                "MATRIX_ACCOUNT_SESSION_NOT_CONFIGURED",
            ],
            safe_summary="Matrix account and session runtime are not configured.",
        ),
        security=CommunicationsSecurityPosture(
            posture_ref="security-posture-ref:communications:matrix:blocked",
            provider_ref=MATRIX_PROVIDER_REF,
            encryption_posture_ref="encryption-posture-ref:communications:not-initialized",
            key_lifecycle_posture_ref="key-lifecycle-posture-ref:communications:not-configured",
            cache_posture_ref="cache-posture-ref:communications:not-opened",
            reason_codes=["COMMUNICATIONS_SECURITY_CONTRACT_DECLARED"],
            blocker_codes=[
                "MATRIX_CRYPTO_RUNTIME_NOT_IMPLEMENTED",
                "MATRIX_CREDENTIAL_AUTHORITY_NOT_ACCEPTED",
                "MATRIX_CACHE_RUNTIME_NOT_IMPLEMENTED",
            ],
            safe_summary="Credential, encryption, and cache runtimes remain unavailable.",
        ),
        receipts=[receipt],
    )


def _validated_limit(limit: int) -> int:
    if limit < 1 or limit > COMMUNICATIONS_MAX_PAGE_SIZE:
        raise ValueError("COMMUNICATIONS_PAGE_LIMIT_OUT_OF_BOUNDS")
    return limit
