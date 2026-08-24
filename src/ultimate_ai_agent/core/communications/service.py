from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from ultimate_ai_agent.core.communications.contracts import (
    COMMUNICATIONS_MAX_PAGE_SIZE,
    CommunicationConversation,
    CommunicationsFailedSendPage,
    CommunicationsCryptoRuntimeStatus,
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
    ReviewedCommunicationThreadDetail,
    ReviewedCommunicationsThreadPage,
)
from ultimate_ai_agent.core.communications.local_projection import (
    ReviewedCommunicationsProjectionStore,
)
from ultimate_ai_agent.core.communications.matrix_disabled import (
    MATRIX_PROVIDER_REF,
)
from ultimate_ai_agent.core.communications.matrix_session.availability import (
    build_matrix_session_provider_descriptor,
)
from ultimate_ai_agent.core.communications.matrix_crypto import (
    build_default_matrix_crypto_posture,
    build_matrix_crypto_availability,
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
        reviewed_projection_store: ReviewedCommunicationsProjectionStore | None = None,
    ) -> None:
        self._registry = registry
        self._session = session.model_copy(deep=True)
        self._rooms = tuple(room.model_copy(deep=True) for room in rooms)
        self._failed_send_receipt_refs = tuple(failed_send_receipt_refs)
        self._security = security.model_copy(deep=True)
        self._reviewed_projection_store = (
            reviewed_projection_store
            or ReviewedCommunicationsProjectionStore.from_env()
        )
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

    def list_reviewed_conversations(
        self, *, limit: int = 25, needs_attention: bool | None = None
    ) -> ReviewedCommunicationsThreadPage:
        return self._reviewed_projection_store.list_threads(
            limit=limit, needs_attention=needs_attention
        )

    def get_reviewed_conversation(
        self, conversation_ref: str
    ) -> ReviewedCommunicationThreadDetail:
        return self._reviewed_projection_store.get_thread(conversation_ref)

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
    repo_root = Path(__file__).resolve().parents[4]
    descriptor = build_matrix_session_provider_descriptor(
        repo_root=repo_root,
        checked_at=observed_at,
    )
    crypto_posture = build_default_matrix_crypto_posture()
    receipt = CommunicationsReceipt(
        receipt_ref="receipt-ref:communications:contract-inspection",
        operation_ref="operation-ref:communications:contract-inspection",
        request_ref="request-ref:communications:contract-inspection",
        provider_ref=MATRIX_PROVIDER_REF,
        outcome=CommunicationsReceiptOutcome.not_executed,
        occurred_at=observed_at,
        reason_codes=["COMMUNICATIONS_CONTRACT_INSPECTED"],
        blocker_codes=["MATRIX_ACCOUNT_SESSION_NOT_CONFIGURED"],
        evidence_refs=["evidence-ref:communications:contract-inspection"],
        redaction_status=CommunicationsRedactionStatus.safe_refs_only,
        safe_summary="Matrix discovery/session-read posture was inspected without execution.",
    )
    return CommunicationsService(
        registry=CommunicationsProviderRegistry([descriptor]),
        session=CommunicationsSessionPosture(
            provider_ref=MATRIX_PROVIDER_REF,
            session_ref="session-ref:communications:matrix:not-configured",
            status=CommunicationsSessionStatus.not_configured,
            freshness=CommunicationsFreshnessStatus.unknown,
            reason_codes=["MATRIX_SESSION_READ_LANES_AVAILABLE_FOR_EXACT_EVALUATION"],
            blocker_codes=[
                "MATRIX_ACCOUNT_SESSION_NOT_CONFIGURED",
            ],
            safe_summary="Matrix account and session runtime are not configured.",
        ),
        security=CommunicationsSecurityPosture(
            posture_ref="security-posture-ref:communications:matrix:crypto-adapter-required",
            provider_ref=MATRIX_PROVIDER_REF,
            encryption_posture_ref="encryption-posture-ref:communications:exact-authority-accepted",
            key_lifecycle_posture_ref="key-lifecycle-posture-ref:communications:exact-authority-accepted",
            cache_posture_ref="cache-posture-ref:communications:not-opened",
            crypto_runtime_status=CommunicationsCryptoRuntimeStatus.adapter_required,
            crypto_availability=build_matrix_crypto_availability(
                checked_at=observed_at
            ),
            crypto_authority_lane_refs=list(crypto_posture.authority_lane_refs),
            crypto_live_executor_refs=list(crypto_posture.live_executor_operation_refs),
            crypto_blocked_operation_refs=list(crypto_posture.blocked_operation_refs),
            recovery_posture_ref="recovery-posture-ref:matrix:external-facility-required",
            backup_posture_ref="backup-posture-ref:matrix:persistent-broker-required",
            single_owner_posture_ref="owner-posture-ref:matrix-crypto:fenced-owner-required",
            reason_codes=[
                "COMMUNICATIONS_SECURITY_CONTRACT_DECLARED",
                "MATRIX_CRYPTO_EXACT_AUTHORITY_CONTRACTS_ACCEPTED",
            ],
            blocker_codes=[
                "MATRIX_CRYPTO_PERSISTENT_RUST_BACKEND_REQUIRED",
                "MATRIX_CRYPTO_LIVE_EXECUTOR_UNCOMPOSED",
                "MATRIX_CRYPTO_ELEMENT_INTEROPERABILITY_EXTERNAL",
                "MATRIX_SSO_BROKER_NOT_IMPLEMENTED",
            ],
            safe_summary=(
                "Exact Matrix crypto authority is declared, while live persistent "
                "Rust crypto and recovery remain adapter-required."
            ),
        ),
        receipts=[receipt],
    )


def _validated_limit(limit: int) -> int:
    if limit < 1 or limit > COMMUNICATIONS_MAX_PAGE_SIZE:
        raise ValueError("COMMUNICATIONS_PAGE_LIMIT_OUT_OF_BOUNDS")
    return limit
