from __future__ import annotations

from typing import Any

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.storage import FounderLoopStorageError

from .workspace import (
    ChatDraftCheckpointRequest,
    ChatThreadLifecycleRequest,
    ChatWorkspaceApprovalCaptureRequest,
    chat_workspace_payload_fingerprint_ref,
)
from .workspace_repository import ChatWorkspaceRepository


class ChatWorkspaceApprovalError(RuntimeError):
    """Raised before storage when exact local approval cannot be validated."""


class ChatWorkspaceControlCenterService:
    """API-facing service for the content-free Chat workspace."""

    def __init__(
        self,
        repository: ChatWorkspaceRepository,
        *,
        approval_authority: LocalApprovalAuthority,
    ) -> None:
        self.repository = repository
        self.approval_authority = approval_authority

    @classmethod
    def from_env(
        cls,
        *,
        approval_authority: LocalApprovalAuthority,
    ) -> "ChatWorkspaceControlCenterService":
        return cls(
            ChatWorkspaceRepository.from_env(),
            approval_authority=approval_authority,
        )

    def workspace(self) -> dict[str, Any]:
        return self.repository.workspace()

    def capture_approval(
        self,
        *,
        thread_ref: str,
        request: ChatWorkspaceApprovalCaptureRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        return self.repository.capture_approval(
            thread_ref=thread_ref,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )

    def record_draft_checkpoint(
        self,
        *,
        thread_ref: str,
        request: ChatDraftCheckpointRequest,
        idempotency_key_ref: str,
        approval_ref: str,
    ) -> dict[str, Any]:
        payload_fingerprint_ref = chat_workspace_payload_fingerprint_ref(
            {"thread_ref": thread_ref, **request.model_dump(mode="json")}
        )
        approval_refs = self._require_approval_for_new_or_exact_replay(
            mutation_kind="draft_checkpoint",
            lifecycle_action=None,
            thread_ref=thread_ref,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            approval_ref=approval_ref,
        )
        return self.repository.record_draft_checkpoint(
            thread_ref=thread_ref,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
            approval_refs=approval_refs,
        )

    def record_lifecycle(
        self,
        *,
        thread_ref: str,
        request: ChatThreadLifecycleRequest,
        idempotency_key_ref: str,
        approval_ref: str,
    ) -> dict[str, Any]:
        payload_fingerprint_ref = chat_workspace_payload_fingerprint_ref(
            {"thread_ref": thread_ref, **request.model_dump(mode="json")}
        )
        approval_refs = self._require_approval_for_new_or_exact_replay(
            mutation_kind="lifecycle",
            lifecycle_action=request.action,
            thread_ref=thread_ref,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            approval_ref=approval_ref,
        )
        return self.repository.record_lifecycle(
            thread_ref=thread_ref,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
            approval_refs=approval_refs,
        )

    def _require_approval_for_new_or_exact_replay(
        self,
        *,
        mutation_kind: str,
        lifecycle_action: str | None,
        thread_ref: str,
        request: ChatDraftCheckpointRequest | ChatThreadLifecycleRequest,
        idempotency_key_ref: str,
        payload_fingerprint_ref: str,
        approval_ref: str,
    ) -> dict[str, str]:
        replay = self.repository.exact_replay(
            thread_ref=thread_ref,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )
        return self._require_exact_approval(
            mutation_kind=mutation_kind,
            lifecycle_action=lifecycle_action,
            thread_ref=thread_ref,
            idempotency_key_ref=idempotency_key_ref,
            payload_fingerprint_ref=payload_fingerprint_ref,
            approval_ref=approval_ref,
            allow_expired_replay=replay is not None,
        )

    def _require_exact_approval(
        self,
        *,
        mutation_kind: str,
        lifecycle_action: str | None,
        thread_ref: str,
        idempotency_key_ref: str,
        payload_fingerprint_ref: str,
        approval_ref: str,
        allow_expired_replay: bool = False,
    ) -> dict[str, str]:
        try:
            grant, approval_request, refs = self.repository.load_exact_approval_grant(
                approval_ref=approval_ref,
                mutation_kind=mutation_kind,
                lifecycle_action=lifecycle_action,
                thread_ref=thread_ref,
                idempotency_key_ref=idempotency_key_ref,
                payload_fingerprint_ref=payload_fingerprint_ref,
                allow_expired_replay=allow_expired_replay,
            )
        except FounderLoopStorageError as exc:
            raise ChatWorkspaceApprovalError(str(exc)) from exc
        self.approval_authority.create_request(approval_request)
        self.approval_authority.load_grant_for_validation(grant)
        decision = self.approval_authority.validate_for_request(
            approval_request, approval_ref
        )
        if not decision.allowed:
            if allow_expired_replay and "APPROVAL_EXPIRED" in decision.reason_codes:
                return refs
            raise ChatWorkspaceApprovalError("CHAT_WORKSPACE_APPROVAL_DENIED")
        return refs
