from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Callable, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.local_model_management.gateway import (
    build_m164_gateway_model_from_env,
    M164ChatCompletionRequest,
    M164ChatMessage,
    M164GatewayTransport,
    M164LocalGatewayModel,
    StdlibM164LlamaCppGatewayTransport,
    build_m164_chat_completion_response,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    RuntimeAuthority,
    RuntimeExecuteRequest,
    RuntimeInvocationRecord,
    RuntimeInvocationRequest,
    RuntimeInvocationStatus,
    RuntimeLocalModelReceiptMetadata,
    RuntimePolicyDecision,
    RuntimeProfile,
    build_local_model_receipt,
    build_policy_decision,
    runtime_payload_fingerprint_ref,
)
from ultimate_ai_agent.core.runtime_gateway.command import (
    GovernedCommandRuntimeAdapter,
    RuntimeCommandExecutionRequest,
    RuntimeCommandGatewayResult,
    invoke_governed_command,
    invoke_approved_governed_command,
)
from ultimate_ai_agent.core.runtime_gateway.goal_runtime import GoalRuntimeService
from ultimate_ai_agent.core.runtime_gateway.storage import (
    RuntimeInvocationStorageError,
    RuntimeInvocationStore,
    active_runtime_authority_leases,
)


LOCAL_MODEL_RUNTIME_ADAPTER_ID = "local-model-runtime-adapter"
LOCAL_MODEL_RUNTIME_MAX_MESSAGES = 12
LOCAL_MODEL_RUNTIME_MAX_MESSAGE_CHARS = 8_000
LOCAL_MODEL_RUNTIME_MAX_PREVIEW_CHARS = 500
LOCAL_MODEL_RUNTIME_MAX_RESPONSE_BYTES = 64_000
LOCAL_MODEL_RUNTIME_MAX_TIMEOUT_SECONDS = 30.0
RUNTIME_LOCAL_MODEL_ENABLED_ENV = "UAA_RUNTIME_LOCAL_MODEL_ENABLED"
RUNTIME_LOCAL_MODEL_ENABLED_VALUES = {"1", "true", "yes", "on", "local-runtime"}


class RuntimeLocalModelMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1, max_length=LOCAL_MODEL_RUNTIME_MAX_MESSAGE_CHARS)

    model_config = ConfigDict(extra="forbid")


class RuntimeLocalModelCallRequest(BaseModel):
    base_url: str = Field(..., min_length=1, max_length=300)
    model_ref: str = Field(..., min_length=1, max_length=120)
    messages: list[RuntimeLocalModelMessage] = Field(
        ...,
        min_length=1,
        max_length=LOCAL_MODEL_RUNTIME_MAX_MESSAGES,
    )
    requested_profile: RuntimeProfile = RuntimeProfile.local_runtime
    mission_ref: str | None = None
    safe_summary: str = Field(..., min_length=1, max_length=500)
    allow_bounded_preview: bool = False
    max_preview_chars: int = Field(default=0, ge=0, le=LOCAL_MODEL_RUNTIME_MAX_PREVIEW_CHARS)
    timeout_seconds: float = Field(default=10.0, gt=0, le=LOCAL_MODEL_RUNTIME_MAX_TIMEOUT_SECONDS)
    max_response_bytes: int = Field(
        default=16_000,
        gt=0,
        le=LOCAL_MODEL_RUNTIME_MAX_RESPONSE_BYTES,
    )
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=8_192)
    metadata_refs: list[str] = Field(default_factory=list)
    prompt_content_persisted: bool = False
    response_content_persisted: bool = False
    provider_exchange_persisted: bool = False
    tools_enabled: bool = False
    streaming_enabled: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_request_shape(self) -> "RuntimeLocalModelCallRequest":
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        validate_safe_execution_text(self.model_ref, "model_ref")
        if self.mission_ref:
            validate_execution_ref(self.mission_ref, "mission_ref")
        for ref in self.metadata_refs:
            validate_execution_ref(ref, "metadata_ref")
        if self.requested_profile not in {
            RuntimeProfile.local_runtime.value,
            RuntimeProfile.operator_approved.value,
        }:
            raise ValueError("RUNTIME_LOCAL_MODEL_PROFILE_REQUIRED")
        if self.prompt_content_persisted or self.response_content_persisted:
            raise ValueError("RUNTIME_LOCAL_MODEL_RAW_CONTENT_PERSISTENCE_DENIED")
        if self.provider_exchange_persisted:
            raise ValueError("RUNTIME_LOCAL_MODEL_PROVIDER_EXCHANGE_PERSISTENCE_DENIED")
        if self.tools_enabled:
            raise ValueError("RUNTIME_LOCAL_MODEL_TOOLS_DENIED")
        if self.streaming_enabled:
            raise ValueError("RUNTIME_LOCAL_MODEL_STREAMING_DENIED")
        if self.allow_bounded_preview and self.max_preview_chars < 1:
            raise ValueError("RUNTIME_LOCAL_MODEL_PREVIEW_LIMIT_REQUIRED")
        return self


class RuntimeLocalModelGatewayResult(BaseModel):
    record: RuntimeInvocationRecord
    response_preview: str | None = None
    response_preview_returned: bool = False
    response_persisted: bool = False
    request_byte_count: int = Field(default=0, ge=0)
    response_byte_count: int = Field(default=0, ge=0)
    error_category: str | None = None
    replayed: bool = False
    local_model_runtime_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_result(self) -> "RuntimeLocalModelGatewayResult":
        if self.response_persisted:
            raise ValueError("RUNTIME_LOCAL_MODEL_RESPONSE_PERSISTENCE_DENIED")
        if self.response_preview:
            validate_safe_execution_text(self.response_preview, "response_preview")
        if self.error_category:
            validate_safe_execution_text(self.error_category, "error_category")
        return self


@dataclass(frozen=True)
class _LocalModelTransportBoundaryPosture:
    runtime_enabled: bool
    gateway_error_category: str | None
    blocked_error_category: str | None
    status: RuntimeInvocationStatus
    policy_decision: RuntimePolicyDecision


class _LocalModelTransportBoundaryBlocked(RuntimeError):
    def __init__(self, posture: _LocalModelTransportBoundaryPosture) -> None:
        super().__init__(posture.blocked_error_category)
        self.posture = posture


@dataclass(frozen=True)
class _AdapterAttempt:
    request_byte_count: int
    response_byte_count: int
    response_preview: str | None
    response_preview_returned: bool
    status_code: int | None
    response_received: bool
    response_truncated: bool
    error_category: str | None
    transport_performed: bool
    boundary_posture: _LocalModelTransportBoundaryPosture | None


class RuntimeLocalModelTransportFactory(Protocol):
    def __call__(self, request: RuntimeLocalModelCallRequest) -> M164GatewayTransport:
        ...


class _GuardedM164GatewayTransport:
    def __init__(
        self,
        transport: M164GatewayTransport,
        guard: Callable[[], _LocalModelTransportBoundaryPosture],
    ) -> None:
        self._transport = transport
        self._guard = guard
        self.boundary_posture: _LocalModelTransportBoundaryPosture | None = None
        self.transport_performed = False

    def chat_completions(
        self,
        gateway_model: M164LocalGatewayModel,
        chat_request: M164ChatCompletionRequest,
        *,
        api_key: str | None = None,
    ) -> dict[str, object]:
        posture = self._guard()
        self.boundary_posture = posture
        if posture.blocked_error_category is not None:
            raise _LocalModelTransportBoundaryBlocked(posture)
        self.transport_performed = True
        return self._transport.chat_completions(
            gateway_model,
            chat_request,
            api_key=api_key,
        )


class LocalModelRuntimeAdapter:
    def __init__(
        self,
        *,
        transport_factory: RuntimeLocalModelTransportFactory | None = None,
    ) -> None:
        self._transport_factory = transport_factory or _default_transport_factory

    def invoke(
        self,
        request: RuntimeLocalModelCallRequest,
        *,
        pre_transport_guard: Callable[
            [], _LocalModelTransportBoundaryPosture
        ]
        | None = None,
    ) -> _AdapterAttempt:
        request_byte_count = _request_byte_count(request)
        guarded_transport: _GuardedM164GatewayTransport | None = None
        try:
            gateway_model = M164LocalGatewayModel(
                model_id=request.model_ref,
                base_url=request.base_url,
            )
            chat_request = M164ChatCompletionRequest(
                model=request.model_ref,
                messages=[
                    M164ChatMessage(role=message.role, content=message.content)
                    for message in request.messages
                ],
                stream=False,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            transport = self._transport_factory(request)
            active_transport = transport
            if pre_transport_guard is not None:
                guarded_transport = _GuardedM164GatewayTransport(
                    transport,
                    pre_transport_guard,
                )
                active_transport = guarded_transport
            response = build_m164_chat_completion_response(
                chat_request,
                gateway_model=gateway_model,
                transport=active_transport,
                api_key=None,
            )
        except _LocalModelTransportBoundaryBlocked as exc:
            return _AdapterAttempt(
                request_byte_count=request_byte_count,
                response_byte_count=0,
                response_preview=None,
                response_preview_returned=False,
                status_code=None,
                response_received=False,
                response_truncated=False,
                error_category=exc.posture.blocked_error_category,
                transport_performed=False,
                boundary_posture=exc.posture,
            )
        except (ValueError, ValidationError) as exc:
            return _AdapterAttempt(
                request_byte_count=request_byte_count,
                response_byte_count=0,
                response_preview=None,
                response_preview_returned=False,
                status_code=None,
                response_received=False,
                response_truncated=False,
                error_category=_safe_error_category(str(exc)),
                transport_performed=bool(
                    guarded_transport and guarded_transport.transport_performed
                ),
                boundary_posture=(
                    guarded_transport.boundary_posture
                    if guarded_transport is not None
                    else None
                ),
            )

        response_text = _assistant_text(response)
        response_bytes = len(response_text.encode("utf-8"))
        truncated = response_bytes > request.max_response_bytes
        preview = None
        preview_returned = False
        if request.allow_bounded_preview:
            preview = response_text[: request.max_preview_chars]
            validate_safe_execution_text(preview, "response_preview")
            preview_returned = True
        return _AdapterAttempt(
            request_byte_count=request_byte_count,
            response_byte_count=min(response_bytes, request.max_response_bytes),
            response_preview=preview,
            response_preview_returned=preview_returned,
            status_code=200,
            response_received=True,
            response_truncated=truncated,
            error_category=None,
            transport_performed=True,
            boundary_posture=(
                guarded_transport.boundary_posture
                if guarded_transport is not None
                else None
            ),
        )


class RuntimeGateway:
    def __init__(
        self,
        *,
        store: RuntimeInvocationStore | None = None,
        local_model_adapter: LocalModelRuntimeAdapter | None = None,
        command_adapter: GovernedCommandRuntimeAdapter | None = None,
        local_model_runtime_enabled: bool | None = None,
        goal_runtime_service: GoalRuntimeService | None = None,
    ) -> None:
        self.store = store or RuntimeInvocationStore(
            active_authority_leases=active_runtime_authority_leases()
        )
        self.local_model_adapter = local_model_adapter or LocalModelRuntimeAdapter()
        self.command_adapter = command_adapter or GovernedCommandRuntimeAdapter()
        self._local_model_runtime_enabled = local_model_runtime_enabled
        self.goal_runtime_service = (
            goal_runtime_service
            or GoalRuntimeService.for_runtime_store(self.store.state_dir)
        )

    def invoke_command(
        self,
        request: RuntimeCommandExecutionRequest,
        *,
        idempotency_ref: str,
    ) -> RuntimeCommandGatewayResult:
        result = invoke_governed_command(
            store=self.store,
            adapter=self.command_adapter,
            request=request,
            idempotency_ref=idempotency_ref,
        )
        self.goal_runtime_service.record_accepted_runtime_invocation(result.record)
        return result

    def execute_approved_command(
        self,
        invocation_ref: str,
        request: RuntimeCommandExecutionRequest,
        execute_request: RuntimeExecuteRequest,
        *,
        idempotency_ref: str,
    ) -> RuntimeCommandGatewayResult:
        record = self.store.get_invocation(invocation_ref)
        result = invoke_approved_governed_command(
            store=self.store,
            adapter=self.command_adapter,
            record=record,
            request=request,
            execute_request=execute_request,
            idempotency_ref=idempotency_ref,
        )
        if result.record.action_inbox_envelope is None:
            self.goal_runtime_service.record_accepted_runtime_invocation(
                result.record
            )
            return result
        updated = self.store.mark_action_inbox_execution_receipt(
            result.record.invocation_ref,
            idempotency_ref=_operation_idempotency_ref(
                idempotency_ref,
                "action-inbox-execution-receipt",
            ),
            payload_fingerprint_ref=_operation_fingerprint_ref(
                result.record.invocation_ref,
                {
                    "operation": "action_inbox_execution_receipt",
                    "receipt_ref": (
                        result.record.receipt.receipt_ref
                        if result.record.receipt
                        else "runtime-receipt-ref:missing"
                    ),
                    "status": result.record.status,
                },
            ),
        )
        final_result = result.model_copy(update={"record": updated})
        self.goal_runtime_service.record_accepted_runtime_invocation(
            final_result.record
        )
        return final_result

    def invoke_local_model(
        self,
        request: RuntimeLocalModelCallRequest,
        *,
        idempotency_ref: str,
    ) -> RuntimeLocalModelGatewayResult:
        result = self._invoke_local_model(
            request,
            idempotency_ref=idempotency_ref,
        )
        self.goal_runtime_service.record_accepted_runtime_invocation(
            result.record
        )
        return result

    def _invoke_local_model(
        self,
        request: RuntimeLocalModelCallRequest,
        *,
        idempotency_ref: str,
    ) -> RuntimeLocalModelGatewayResult:
        validate_execution_ref(idempotency_ref, "idempotency_ref")
        runtime_disabled = self.store.operator_safe_disable_active()
        runtime_enabled = self._runtime_local_model_enabled()
        endpoint_error = _validate_loopback_endpoint(request)
        blocked_error = _blocked_error_category(
            runtime_disabled=runtime_disabled,
            runtime_enabled=runtime_enabled,
            endpoint_error=endpoint_error,
        )
        force_sealed = blocked_error not in {
            None,
            "RUNTIME_LOCAL_MODEL_SAFE_DISABLED",
        }
        invocation_request = _runtime_invocation_request(
            request,
            force_sealed=force_sealed,
        )
        existing = self.store.get_invocation_for_idempotency(idempotency_ref)
        if (
            existing is not None
            and runtime_payload_fingerprint_ref(invocation_request)
            != existing.payload_fingerprint_ref
        ):
            alternate_request = _runtime_invocation_request(
                request,
                force_sealed=not force_sealed,
            )
            if (
                runtime_payload_fingerprint_ref(alternate_request)
                == existing.payload_fingerprint_ref
            ):
                invocation_request = alternate_request
        created = self.store.create_invocation(
            invocation_request,
            idempotency_ref=idempotency_ref,
            local_model_gateway_validated=blocked_error is None,
        )
        record = created.record
        if blocked_error is None and record.status == RuntimeInvocationStatus.safe_disabled.value:
            blocked_error = "RUNTIME_LOCAL_MODEL_SAFE_DISABLED"
        if created.replayed:
            replay_runtime_disabled = self.store.operator_safe_disable_active()
            replay_runtime_enabled = self._runtime_local_model_enabled()
            replay_endpoint_error = _validate_loopback_endpoint(request)
            replay_gateway_error = _blocked_error_category(
                runtime_disabled=replay_runtime_disabled,
                runtime_enabled=replay_runtime_enabled,
                endpoint_error=replay_endpoint_error,
            )
            replay_blocked_error = replay_gateway_error
            replay_gateway_validated = replay_gateway_error is None
            completed_receipt = _receipt_proves_completed_local_model_attempt(record)
            completed_receipt_error = (
                record.receipt.model_receipt_metadata.error_category
                if completed_receipt
                and record.receipt is not None
                and record.receipt.model_receipt_metadata is not None
                else None
            )
            if replay_blocked_error is None and replay_runtime_disabled:
                replay_blocked_error = "RUNTIME_LOCAL_MODEL_SAFE_DISABLED"
            if (
                replay_blocked_error is None
                and record.receipt is not None
                and not completed_receipt
            ):
                replay_blocked_error = (
                    record.receipt.model_receipt_metadata.error_category
                    if record.receipt.model_receipt_metadata is not None
                    else None
                ) or "RUNTIME_LOCAL_MODEL_IDEMPOTENT_REPLAY_BLOCKED"
                replay_gateway_validated = False
            replay_status = (
                RuntimeInvocationStatus.safe_disabled
                if replay_runtime_disabled
                else (
                    RuntimeInvocationStatus.execution_blocked
                    if replay_blocked_error is not None
                    else RuntimeInvocationStatus.receipt_recorded
                )
            )
            replay_policy_decision = build_policy_decision(
                record.request,
                invocation_ref=record.invocation_ref,
                approval_ref=record.approval_requirement.approval_ref,
                status=replay_status,
                local_model_gateway_validated=replay_gateway_validated,
                active_authority_leases=self.store.current_authority_leases(),
                kill_switch_engaged=(
                    self.store.authority_lease_kill_switch_engaged()
                ),
            )
            if (
                replay_blocked_error is None
                and not replay_policy_decision.allowed_to_execute
            ):
                replay_blocked_error = (
                    "RUNTIME_LOCAL_MODEL_POLICY_EXECUTION_BLOCKED"
                )
                replay_status = RuntimeInvocationStatus.execution_blocked
            replay_policy_decision = replay_policy_decision.model_copy(
                update={
                    "approval_requirement": record.approval_requirement,
                    "invocation_status": replay_status,
                }
            )
            if record.receipt is not None:
                if replay_blocked_error is None:
                    revalidated = self._record_local_model_replay_posture(
                        record,
                        request=request,
                        policy_decision=replay_policy_decision,
                        status=RuntimeInvocationStatus.receipt_recorded,
                        error_category=None,
                        idempotency_ref=idempotency_ref,
                        local_model_gateway_validated=replay_gateway_validated,
                        gateway_error_category=replay_gateway_error,
                    )
                    return RuntimeLocalModelGatewayResult(
                        record=revalidated,
                        request_byte_count=(
                            record.receipt.model_receipt_metadata.request_byte_count
                            if record.receipt.model_receipt_metadata
                            else 0
                        ),
                        response_byte_count=(
                            record.receipt.model_receipt_metadata.response_byte_count
                            if record.receipt.model_receipt_metadata
                            else 0
                        ),
                        error_category=completed_receipt_error,
                        replayed=True,
                        local_model_runtime_enabled=replay_runtime_enabled,
                    )
                updated = self._record_local_model_replay_posture(
                    record,
                    request=request,
                    policy_decision=replay_policy_decision,
                    status=replay_status,
                    error_category=replay_blocked_error,
                    idempotency_ref=idempotency_ref,
                    local_model_gateway_validated=replay_gateway_validated,
                    gateway_error_category=replay_gateway_error,
                )
                receipt_metadata = (
                    updated.receipt.model_receipt_metadata
                    if updated.receipt is not None
                    else None
                )
                return RuntimeLocalModelGatewayResult(
                    record=updated,
                    request_byte_count=(
                        receipt_metadata.request_byte_count
                        if receipt_metadata is not None
                        else 0
                    ),
                    response_byte_count=(
                        receipt_metadata.response_byte_count
                        if receipt_metadata is not None
                        else 0
                    ),
                    error_category=(
                        completed_receipt_error
                        if completed_receipt
                        and replay_blocked_error
                        != "RUNTIME_LOCAL_MODEL_POLICY_EXECUTION_BLOCKED"
                        else replay_blocked_error
                    ),
                    replayed=True,
                    local_model_runtime_enabled=replay_runtime_enabled,
                )
            metadata = RuntimeLocalModelReceiptMetadata(
                model_ref=request.model_ref,
                endpoint_ref=_endpoint_ref(request.base_url),
                profile=RuntimeProfile(request.requested_profile),
                request_byte_count=_request_byte_count(request),
                response_byte_count=0,
                status_code=None,
                response_received=False,
                response_truncated=False,
                bounded_preview_returned=False,
                bounded_preview_persisted=False,
                error_category="RUNTIME_LOCAL_MODEL_IDEMPOTENT_REPLAY_WITHOUT_RECEIPT",
                safe_summary="Local model runtime replay was blocked before transport.",
            )
            recovery = self.store.record_local_model_replay_without_receipt(
                record.invocation_ref,
                metadata,
                idempotency_ref=_operation_idempotency_ref(
                    idempotency_ref,
                    "local-model-replay-without-receipt",
                ),
                payload_fingerprint_ref=_operation_fingerprint_ref(
                    record.invocation_ref,
                    {
                        "operation": "local_model_replay_without_receipt",
                        "metadata": metadata.model_dump(mode="json"),
                    },
                ),
            )
            if recovery.replayed:
                return self._invoke_local_model(
                    request,
                    idempotency_ref=idempotency_ref,
                )
            updated = recovery.record
            return RuntimeLocalModelGatewayResult(
                record=updated,
                request_byte_count=metadata.request_byte_count,
                error_category=metadata.error_category,
                replayed=True,
                local_model_runtime_enabled=replay_runtime_enabled,
            )
        if blocked_error is not None or not record.policy_decision.allowed_to_execute:
            metadata = RuntimeLocalModelReceiptMetadata(
                model_ref=request.model_ref,
                endpoint_ref=_endpoint_ref(request.base_url),
                profile=RuntimeProfile(request.requested_profile),
                request_byte_count=_request_byte_count(request),
                response_byte_count=0,
                status_code=None,
                response_received=False,
                response_truncated=False,
                bounded_preview_returned=False,
                bounded_preview_persisted=False,
                error_category=blocked_error
                or "RUNTIME_LOCAL_MODEL_POLICY_EXECUTION_BLOCKED",
                safe_summary="Local model runtime request was blocked before transport.",
            )
            receipt = build_local_model_receipt(
                record,
                metadata=metadata,
                execution_performed=False,
                model_call_performed=False,
                status=RuntimeInvocationStatus.execution_blocked,
            )
            updated = self.store.record_receipt(
                record.invocation_ref,
                receipt,
                idempotency_ref=_operation_idempotency_ref(idempotency_ref, "local-model-blocked"),
                payload_fingerprint_ref=_operation_fingerprint_ref(
                    record.invocation_ref,
                    {
                        "operation": "local_model_blocked",
                        "metadata": metadata.model_dump(mode="json"),
                    },
                ),
            )
            return RuntimeLocalModelGatewayResult(
                record=updated,
                request_byte_count=metadata.request_byte_count,
                error_category=metadata.error_category,
                local_model_runtime_enabled=runtime_enabled,
            )

        attempt_marker_metadata = RuntimeLocalModelReceiptMetadata(
            model_ref=request.model_ref,
            endpoint_ref=_endpoint_ref(request.base_url),
            profile=record.policy_decision.profile,
            request_byte_count=_request_byte_count(request),
            response_byte_count=0,
            status_code=None,
            response_received=False,
            response_truncated=False,
            bounded_preview_returned=False,
            bounded_preview_persisted=False,
            error_category="RUNTIME_LOCAL_MODEL_ATTEMPT_OUTCOME_UNKNOWN",
            attempt_outcome_unknown=True,
            safe_summary=(
                "Local model transport attempt was authorized; outcome is not yet known."
            ),
        )
        attempt_marker = build_local_model_receipt(
            record,
            metadata=attempt_marker_metadata,
            execution_performed=False,
            model_call_performed=False,
            status=RuntimeInvocationStatus.receipt_recorded,
        )
        record = self.store.record_receipt(
            record.invocation_ref,
            attempt_marker,
            idempotency_ref=_operation_idempotency_ref(
                idempotency_ref,
                "local-model-attempt-marker",
            ),
            payload_fingerprint_ref=_operation_fingerprint_ref(
                record.invocation_ref,
                {
                    "operation": "local_model_attempt_marker",
                    "metadata": attempt_marker_metadata.model_dump(mode="json"),
                },
            ),
        )
        attempt = self.local_model_adapter.invoke(
            request,
            pre_transport_guard=lambda: (
                self._local_model_transport_boundary_posture(record, request)
            ),
        )
        boundary_posture = attempt.boundary_posture
        attempt_policy_decision = (
            boundary_posture.policy_decision
            if boundary_posture is not None
            else record.policy_decision
        )
        boundary_blocked = bool(
            boundary_posture is not None
            and boundary_posture.blocked_error_category is not None
            and not attempt.transport_performed
        )
        if boundary_blocked:
            attempt_safe_summary = (
                "Local model runtime request was blocked at the exact transport "
                "boundary before the send."
            )
        elif attempt.error_category is None:
            attempt_safe_summary = (
                "Local model call reached a loopback endpoint and stored metadata only."
            )
        else:
            attempt_safe_summary = (
                "Local model call attempt failed safely with metadata only."
            )
        metadata = RuntimeLocalModelReceiptMetadata(
            model_ref=request.model_ref,
            endpoint_ref=_endpoint_ref(request.base_url),
            profile=RuntimeProfile(request.requested_profile),
            request_byte_count=attempt.request_byte_count,
            response_byte_count=attempt.response_byte_count,
            status_code=attempt.status_code,
            response_received=attempt.response_received,
            response_truncated=attempt.response_truncated,
            bounded_preview_returned=attempt.response_preview_returned,
            bounded_preview_persisted=False,
            error_category=attempt.error_category,
            safe_summary=attempt_safe_summary,
        )
        model_call_performed = attempt.transport_performed
        receipt = build_local_model_receipt(
            record,
            metadata=metadata,
            execution_performed=model_call_performed,
            model_call_performed=model_call_performed,
            status=(
                RuntimeInvocationStatus.execution_blocked
                if boundary_blocked
                else RuntimeInvocationStatus.receipt_recorded
            ),
        )
        updated = self.store.record_receipt(
            record.invocation_ref,
            receipt,
            idempotency_ref=_operation_idempotency_ref(idempotency_ref, "local-model-receipt"),
            payload_fingerprint_ref=_operation_fingerprint_ref(
                record.invocation_ref,
                {
                    "operation": "local_model_receipt",
                    "metadata": metadata.model_dump(mode="json"),
                },
            ),
            policy_decision=attempt_policy_decision,
            local_model_gateway_error_recheck=(
                None
                if boundary_blocked
                else lambda: _blocked_error_category(
                    runtime_disabled=self.store.operator_safe_disable_active(),
                    runtime_enabled=self._runtime_local_model_enabled(),
                    endpoint_error=_validate_loopback_endpoint(request),
                )
            ),
        )
        return RuntimeLocalModelGatewayResult(
            record=updated,
            response_preview=attempt.response_preview,
            response_preview_returned=attempt.response_preview_returned,
            request_byte_count=attempt.request_byte_count,
            response_byte_count=attempt.response_byte_count,
            error_category=attempt.error_category,
            replayed=False,
            local_model_runtime_enabled=(
                boundary_posture.runtime_enabled
                if boundary_posture is not None
                else runtime_enabled
            ),
        )

    def _local_model_transport_boundary_posture(
        self,
        record: RuntimeInvocationRecord,
        request: RuntimeLocalModelCallRequest,
    ) -> _LocalModelTransportBoundaryPosture:
        runtime_disabled = self.store.operator_safe_disable_active()
        runtime_enabled = self._runtime_local_model_enabled()
        gateway_error = _blocked_error_category(
            runtime_disabled=runtime_disabled,
            runtime_enabled=runtime_enabled,
            endpoint_error=_validate_loopback_endpoint(request),
        )
        status = (
            RuntimeInvocationStatus.safe_disabled
            if runtime_disabled
            else (
                RuntimeInvocationStatus.execution_blocked
                if gateway_error is not None
                else RuntimeInvocationStatus.receipt_recorded
            )
        )
        policy_decision = build_policy_decision(
            record.request,
            invocation_ref=record.invocation_ref,
            approval_ref=record.approval_requirement.approval_ref,
            status=status,
            local_model_gateway_validated=gateway_error is None,
            active_authority_leases=self.store.current_authority_leases(),
            kill_switch_engaged=self.store.authority_lease_kill_switch_engaged(),
        ).model_copy(
            update={
                "approval_requirement": record.approval_requirement,
                "invocation_status": status,
            }
        )
        blocked_error = gateway_error
        if blocked_error is None and not policy_decision.allowed_to_execute:
            blocked_error = "RUNTIME_LOCAL_MODEL_POLICY_EXECUTION_BLOCKED"
            status = RuntimeInvocationStatus.execution_blocked
            policy_decision = policy_decision.model_copy(
                update={"invocation_status": status}
            )
        return _LocalModelTransportBoundaryPosture(
            runtime_enabled=runtime_enabled,
            gateway_error_category=gateway_error,
            blocked_error_category=blocked_error,
            status=status,
            policy_decision=policy_decision,
        )

    def _record_local_model_replay_posture(
        self,
        record: RuntimeInvocationRecord,
        *,
        request: RuntimeLocalModelCallRequest,
        policy_decision: RuntimePolicyDecision,
        status: RuntimeInvocationStatus,
        error_category: str | None,
        idempotency_ref: str,
        local_model_gateway_validated: bool,
        gateway_error_category: str | None,
    ) -> RuntimeInvocationRecord:
        if record.receipt is None:
            raise RuntimeInvocationStorageError(
                "RUNTIME_REPLAY_POSTURE_RECEIPT_REQUIRED"
            )
        posture_ref = _hash_ref(
            "runtime-local-model-replay-posture-ref",
            {
                "prior_policy_decision": record.policy_decision.model_dump(
                    mode="json",
                    exclude={"decided_at"},
                ),
                "prior_status": record.status,
                "receipt": record.receipt.model_dump(mode="json"),
                "policy_decision": policy_decision.model_dump(
                    mode="json",
                    exclude={"decided_at"},
                ),
                "status": status.value,
                "error_category": error_category,
            },
        )
        return self.store.record_replay_posture(
            record.invocation_ref,
            policy_decision,
            status,
            local_model_gateway_validated=local_model_gateway_validated,
            gateway_error_category=gateway_error_category,
            gateway_error_recheck=lambda: _blocked_error_category(
                runtime_disabled=self.store.operator_safe_disable_active(),
                runtime_enabled=self._runtime_local_model_enabled(),
                endpoint_error=_validate_loopback_endpoint(request),
            ),
            expected_receipt=record.receipt,
            idempotency_ref=_operation_idempotency_ref(
                idempotency_ref,
                posture_ref,
            ),
            payload_fingerprint_ref=_operation_fingerprint_ref(
                record.invocation_ref,
                {
                    "operation": "local_model_replay_posture_recorded",
                    "posture_ref": posture_ref,
                },
            ),
        )

    def _runtime_local_model_enabled(self) -> bool:
        if self._local_model_runtime_enabled is not None:
            return self._local_model_runtime_enabled
        return local_model_runtime_enabled()


def _default_transport_factory(request: RuntimeLocalModelCallRequest) -> M164GatewayTransport:
    return StdlibM164LlamaCppGatewayTransport(
        timeout_seconds=request.timeout_seconds,
        max_response_bytes=request.max_response_bytes,
    )


def local_model_runtime_enabled() -> bool:
    return os.getenv(RUNTIME_LOCAL_MODEL_ENABLED_ENV, "").strip().lower() in (
        RUNTIME_LOCAL_MODEL_ENABLED_VALUES
    )


def _validate_loopback_endpoint(request: RuntimeLocalModelCallRequest) -> str | None:
    try:
        M164LocalGatewayModel(
            model_id=request.model_ref,
            base_url=request.base_url,
        )
        configured = build_m164_gateway_model_from_env()
    except (ValueError, ValidationError) as exc:
        return _safe_error_category(str(exc))
    if request.base_url.rstrip("/") != configured.base_url.rstrip("/"):
        return "RUNTIME_LOCAL_MODEL_ENDPOINT_NOT_CONFIGURED"
    return None


def _blocked_error_category(
    *,
    runtime_disabled: bool,
    runtime_enabled: bool,
    endpoint_error: str | None,
) -> str | None:
    if runtime_disabled:
        return "RUNTIME_LOCAL_MODEL_SAFE_DISABLED"
    if not runtime_enabled:
        return "RUNTIME_LOCAL_MODEL_DISABLED_BY_DEFAULT"
    return endpoint_error


def _request_byte_count(request: RuntimeLocalModelCallRequest) -> int:
    return len(
        _canonical_json(
            {
                "model": request.model_ref,
                "message_count": len(request.messages),
                "message_bytes": [
                    len(message.content.encode("utf-8"))
                    for message in request.messages
                ],
                "stream": False,
            }
        ).encode("utf-8")
    )


def _runtime_invocation_request(
    request: RuntimeLocalModelCallRequest,
    *,
    force_sealed: bool = False,
) -> RuntimeInvocationRequest:
    prompt_ref = _prompt_ref(request)
    return RuntimeInvocationRequest(
        requested_authority=RuntimeAuthority.local_model,
        requested_profile=RuntimeProfile.sealed if force_sealed else request.requested_profile,
        input_ref=prompt_ref,
        mission_ref=request.mission_ref,
        safe_summary=request.safe_summary,
        metadata_refs=[
            _endpoint_ref(request.base_url),
            _model_ref(request.model_ref),
            prompt_ref,
            *([request.mission_ref] if request.mission_ref else []),
            *request.metadata_refs,
        ],
    )


def _receipt_proves_completed_local_model_attempt(
    record: RuntimeInvocationRecord,
) -> bool:
    receipt = record.receipt
    metadata = receipt.model_receipt_metadata if receipt is not None else None
    return bool(
        receipt is not None
        and receipt.invocation_status
        == RuntimeInvocationStatus.receipt_recorded.value
        and metadata is not None
        and not metadata.attempt_outcome_unknown
    )


def _assistant_text(response: dict[str, object]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("RUNTIME_LOCAL_MODEL_RESPONSE_CHOICE_MISSING")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("RUNTIME_LOCAL_MODEL_RESPONSE_CHOICE_INVALID")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("RUNTIME_LOCAL_MODEL_RESPONSE_MESSAGE_INVALID")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("RUNTIME_LOCAL_MODEL_RESPONSE_CONTENT_MISSING")
    return content.strip()


def _safe_error_category(value: str) -> str:
    for known in [
        "M164_LOOPBACK_ONLY_REQUIRED",
        "M164_BASE_URL_SCOPE_DENIED",
        "M164_MODEL_ID_UNSAFE",
        "M164_GATEWAY_REDIRECT_DENIED",
        "M164_LLAMA_CPP_GATEWAY_UNAVAILABLE",
        "M164_GATEWAY_RESPONSE_TOO_LARGE",
        "M164_GATEWAY_JSON_REQUIRED",
        "M164_GATEWAY_OBJECT_REQUIRED",
        "RUNTIME_LOCAL_MODEL_ENDPOINT_NOT_CONFIGURED",
    ]:
        if known in value:
            return known
    safe = value.strip().upper().replace(" ", "_")
    if not safe:
        return "RUNTIME_LOCAL_MODEL_ERROR"
    allowed = "".join(ch for ch in safe if ch.isalnum() or ch == "_")
    return allowed[:80] or "RUNTIME_LOCAL_MODEL_ERROR"


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash_ref(prefix: str, value: object) -> str:
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:sha256:{digest}"


def _prompt_ref(request: RuntimeLocalModelCallRequest) -> str:
    return _hash_ref(
        "runtime-local-model-input-ref",
        {
            "model_ref": request.model_ref,
            "message_count": len(request.messages),
            "messages": [message.model_dump(mode="json") for message in request.messages],
        },
    )


def _endpoint_ref(base_url: str) -> str:
    return _hash_ref("runtime-local-model-endpoint-ref", {"base_url": base_url})


def _model_ref(model_ref: str) -> str:
    return _hash_ref("runtime-local-model-model-ref", {"model_ref": model_ref})


def _operation_idempotency_ref(base_ref: str, operation: str) -> str:
    return _hash_ref(
        "idempotency-ref",
        {
            "base_idempotency_ref": base_ref,
            "operation": operation,
        },
    )


def _operation_fingerprint_ref(invocation_ref: str, payload: object) -> str:
    return _hash_ref(
        "runtime-operation-fingerprint-ref",
        {
            "invocation_ref": invocation_ref,
            "payload": payload,
        },
    )
