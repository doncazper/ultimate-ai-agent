from __future__ import annotations

import json
import threading
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.authority.contracts import (
    AuthorityCapability,
    AuthorityConstraintKind,
    AuthorityDomain,
)
from ultimate_ai_agent.core.authority.dispatch_contracts import (
    AuthorityDispatchCancelRequest,
    AuthorityDispatchExecutionFence,
    AuthorityDispatchFailureCategory,
    AuthorityDispatchReceipt,
    AuthorityDispatchRequest,
    AuthorityDispatchResult,
    AuthorityDispatchStatus,
    AuthorityDispatchWorkerClaimFence,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchConflictError,
    AuthorityDispatchCorruptionError,
    AuthorityDispatcher,
    ToolRuntimeAuthorityDispatchAdapter,
    authority_dispatch_request_fingerprint,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepConflictError,
    MissionStepDefinition,
    MissionStepOrchestrationContext,
    MissionStepReadModel,
    MissionStepStatus,
    MissionStepStore,
    TERMINAL_MISSION_STEP_STATUSES,
)
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.tools.runtime.filesystem_metadata import (
    FILESYSTEM_METADATA_TOOL_REF,
)


def _mission_step_attempt_source(step_ref: str, attempt_no: int) -> str:
    if attempt_no < 1:
        raise ValueError("MISSION_STEP_ATTEMPT_NUMBER_INVALID")
    return step_ref if attempt_no == 1 else f"{step_ref}:attempt:{attempt_no}"


def mission_step_action_ref(step_ref: str, attempt_no: int = 1) -> str:
    return (
        "authority-action-ref:mission-step:"
        f"{hash_text(_mission_step_attempt_source(step_ref, attempt_no))[:24]}"
    )


def mission_step_dispatch_ref(step_ref: str, attempt_no: int = 1) -> str:
    return (
        "authority-dispatch-ref:mission-step:"
        f"{hash_text(_mission_step_attempt_source(step_ref, attempt_no))[:24]}"
    )


def mission_step_idempotency_ref(step_ref: str, attempt_no: int = 1) -> str:
    return (
        "idempotency-ref:mission-step:"
        f"{hash_text(_mission_step_attempt_source(step_ref, attempt_no))[:24]}"
    )


class MissionStepApprovalPosture(str, Enum):
    not_required = "not_required"
    ready = "ready"
    wait = "wait"
    invalid = "invalid"


class MissionStepApprovalEvaluation(BaseModel):
    posture: MissionStepApprovalPosture
    approval_request_ref: str | None = None
    approval_ref: str | None = None
    approval_scope_fingerprint_ref: str | None = None
    validation_evidence_ref: str | None = None
    reason_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class AuthorityMissionStepResult(BaseModel):
    step: MissionStepReadModel
    dispatch_result: AuthorityDispatchResult | None = None
    replayed_terminal_step: bool = False
    execution_authority_minted_by_runner: Literal[False] = False
    autonomous_retry_performed: bool = False

    model_config = ConfigDict(extra="forbid")


class AuthorityMissionRunner:
    """Synchronous V1 runner for one exact filesystem-metadata mission step."""

    def __init__(
        self,
        *,
        dispatcher: AuthorityDispatcher,
        step_store: MissionStepStore,
    ) -> None:
        self.dispatcher = dispatcher
        self.step_store = step_store
        self.step_store._bind_dispatch_receipt_resolver(  # noqa: SLF001
            self._resolve_dispatch_receipt
        )

    def evaluate_approval_posture(
        self,
        request: AuthorityDispatchRequest,
    ) -> MissionStepApprovalEvaluation:
        adapter = self.dispatcher.adapters.get(request.adapter_ref)
        if adapter is None or not adapter.descriptor.approval_required:
            return MissionStepApprovalEvaluation(
                posture=MissionStepApprovalPosture.not_required,
            )
        validation_request = request.approval_validation_request
        authority = self.dispatcher.approval_authority
        if validation_request is None or authority is None:
            return MissionStepApprovalEvaluation(
                posture=MissionStepApprovalPosture.invalid,
                reason_refs=["reason-ref:mission-step:approval-authority-unavailable"],
            )
        scope_payload = validation_request.model_dump(
            mode="json",
            exclude={"current_time"},
        )
        scope_fingerprint_ref = (
            "approval-scope-fingerprint-ref:sha256:"
            f"{hash_text(json.dumps(scope_payload, sort_keys=True))[:24]}"
        )
        registered = authority.find_request_for_validation(validation_request)
        if registered is None:
            return MissionStepApprovalEvaluation(
                posture=MissionStepApprovalPosture.invalid,
                approval_ref=validation_request.approval_ref,
                approval_scope_fingerprint_ref=scope_fingerprint_ref,
                reason_refs=[
                    "reason-ref:mission-step:approval-request-not-registered"
                ],
            )
        grant = authority.get_grant(validation_request.approval_ref)
        if grant is None:
            return MissionStepApprovalEvaluation(
                posture=MissionStepApprovalPosture.wait,
                approval_request_ref=registered.approval_request_id,
                approval_ref=validation_request.approval_ref,
                approval_scope_fingerprint_ref=scope_fingerprint_ref,
                reason_refs=["reason-ref:mission-step:approval-not-yet-granted"],
            )
        decision = authority._validate_at_trusted_time(  # noqa: SLF001
            validation_request,
            current_time=self.step_store.current_time(),
        )
        evidence_payload = {
            "approval_ref": validation_request.approval_ref,
            "matched_grant_ref": decision.matched_grant_ref,
            "allowed": decision.allowed,
            "status": decision.status,
            "reason_codes": decision.reason_codes,
            "scope_fingerprint_ref": scope_fingerprint_ref,
        }
        evidence_ref = (
            "approval-validation-ref:mission-step:sha256:"
            f"{hash_text(json.dumps(evidence_payload, sort_keys=True))[:24]}"
        )
        if (
            decision.allowed
            and decision.matched_grant_ref == validation_request.approval_ref
        ):
            return MissionStepApprovalEvaluation(
                posture=MissionStepApprovalPosture.ready,
                approval_request_ref=registered.approval_request_id,
                approval_ref=validation_request.approval_ref,
                approval_scope_fingerprint_ref=scope_fingerprint_ref,
                validation_evidence_ref=evidence_ref,
                reason_refs=["reason-ref:mission-step:approval-freshly-validated"],
            )
        return MissionStepApprovalEvaluation(
            posture=MissionStepApprovalPosture.invalid,
            approval_request_ref=registered.approval_request_id,
            approval_ref=validation_request.approval_ref,
            approval_scope_fingerprint_ref=scope_fingerprint_ref,
            validation_evidence_ref=evidence_ref,
            reason_refs=["reason-ref:mission-step:approval-invalid"],
        )

    def run_once(
        self,
        definition: MissionStepDefinition,
        request: AuthorityDispatchRequest,
        *,
        owner_ref: str,
        claim_ttl_seconds: int = 30,
        heartbeat_interval_seconds: int | None = None,
    ) -> AuthorityMissionStepResult:
        if definition.orchestration_plan_ref is not None:
            raise ValueError("MISSION_RUNNER_ORCHESTRATED_ENTRYPOINT_REQUIRED")
        return self._run_once(
            definition,
            request,
            owner_ref=owner_ref,
            claim_ttl_seconds=claim_ttl_seconds,
            heartbeat_interval_seconds=heartbeat_interval_seconds,
            worker_claim_fence=None,
            orchestration_context=None,
        )

    def _run_orchestrated_once(
        self,
        definition: MissionStepDefinition,
        request: AuthorityDispatchRequest,
        *,
        owner_ref: str,
        claim_ttl_seconds: int,
        orchestration_context: MissionStepOrchestrationContext,
        heartbeat_interval_seconds: int | None = None,
        worker_claim_fence: AuthorityDispatchWorkerClaimFence | None = None,
    ) -> AuthorityMissionStepResult:
        if definition.orchestration_plan_ref != orchestration_context.plan_ref:
            raise ValueError("MISSION_RUNNER_ORCHESTRATION_CONTEXT_INVALID")
        return self._run_once(
            definition,
            request,
            owner_ref=owner_ref,
            claim_ttl_seconds=claim_ttl_seconds,
            orchestration_context=orchestration_context,
            heartbeat_interval_seconds=heartbeat_interval_seconds,
            worker_claim_fence=worker_claim_fence,
        )

    def _run_once(
        self,
        definition: MissionStepDefinition,
        request: AuthorityDispatchRequest,
        *,
        owner_ref: str,
        claim_ttl_seconds: int,
        orchestration_context: MissionStepOrchestrationContext | None,
        heartbeat_interval_seconds: int | None,
        worker_claim_fence: AuthorityDispatchWorkerClaimFence | None,
    ) -> AuthorityMissionStepResult:
        self.validate_step(definition, request)
        initial = self.step_store.create(definition)
        if initial.status in TERMINAL_MISSION_STEP_STATUSES:
            return AuthorityMissionStepResult(
                step=self.step_store.read(definition.step_ref),
                replayed_terminal_step=True,
            )
        request_fingerprint_ref = authority_dispatch_request_fingerprint(request)
        try:
            claim = self.step_store.claim(
                definition.step_ref,
                owner_ref=owner_ref,
                ttl_seconds=claim_ttl_seconds,
                dispatch_ref=request.dispatch_ref,
                dispatch_request_fingerprint_ref=request_fingerprint_ref,
                orchestration_context=orchestration_context,
            )
        except MissionStepConflictError as exc:
            if str(exc) == "MISSION_STEP_PREPARED_DEADLINE_EXPIRED":
                return self._cancel_expired_step(definition, request)
            raise
        if claim.status in TERMINAL_MISSION_STEP_STATUSES:
            dispatch_result = None
            if claim.dispatch_receipt_ref is not None:
                dispatch_result = self.dispatcher.prepare(request)
                self._reconcile_dispatch(request, dispatch_result)
            return AuthorityMissionStepResult(
                step=self.step_store.read(definition.step_ref),
                dispatch_result=dispatch_result,
                replayed_terminal_step=True,
            )
        stop_heartbeat = threading.Event()
        heartbeat_errors: list[BaseException] = []
        heartbeat_thread: threading.Thread | None = None
        if heartbeat_interval_seconds is not None:
            if (
                heartbeat_interval_seconds < 1
                or heartbeat_interval_seconds * 2 >= claim_ttl_seconds
            ):
                raise ValueError("MISSION_STEP_HEARTBEAT_INTERVAL_UNSAFE")

            def renew_claim() -> None:
                while not stop_heartbeat.wait(heartbeat_interval_seconds):
                    try:
                        self.step_store.heartbeat(
                            definition.step_ref,
                            owner_ref=owner_ref,
                            claim_ref=claim.claim_ref or "",
                            generation=claim.generation,
                            ttl_seconds=claim_ttl_seconds,
                        )
                    except (
                        BaseException
                    ) as exc:  # pragma: no cover - asserted by caller
                        heartbeat_errors.append(exc)
                        return

            heartbeat_thread = threading.Thread(
                target=renew_claim,
                name="uaa-mission-step-heartbeat",
                daemon=True,
            )
            heartbeat_thread.start()

        def stop_claim_heartbeat() -> None:
            stop_heartbeat.set()
            if heartbeat_thread is not None:
                heartbeat_thread.join(timeout=(heartbeat_interval_seconds or 1) + 1)

        dispatch_error: (
            AuthorityDispatchConflictError | AuthorityDispatchCorruptionError | None
        ) = None
        try:
            dispatch_result = self.dispatcher.prepare(request)
            if dispatch_result.receipt.status == AuthorityDispatchStatus.prepared.value:
                if definition.deadline <= self.step_store.current_time():
                    return self._cancel_expired_step(definition, request)
                else:
                    claim = self.step_store.heartbeat(
                        definition.step_ref,
                        owner_ref=owner_ref,
                        claim_ref=claim.claim_ref or "",
                        generation=claim.generation,
                        ttl_seconds=claim_ttl_seconds,
                    )
                    if definition.deadline <= self.step_store.current_time():
                        return self._cancel_expired_step(definition, request)
                    else:
                        execution_fence = None
                        if worker_claim_fence is not None:
                            if worker_claim_fence.worker_ref != owner_ref:
                                raise MissionStepConflictError(
                                    "MISSION_STEP_WORKER_FENCE_OWNER_MISMATCH"
                                )
                            execution_fence = AuthorityDispatchExecutionFence(
                                **worker_claim_fence.model_dump(mode="python"),
                                step_ref=definition.step_ref,
                                step_claim_ref=claim.claim_ref or "",
                                step_generation=claim.generation,
                            )
                        dispatch_result = self.dispatcher.execute(
                            request,
                            execution_fence=execution_fence,
                        )
            self._reconcile_dispatch(request, dispatch_result)
        except (
            AuthorityDispatchConflictError,
            AuthorityDispatchCorruptionError,
        ) as exc:
            dispatch_error = exc
        finally:
            stop_claim_heartbeat()
        if dispatch_error is not None:
            self.step_store.complete(
                definition.step_ref,
                owner_ref=owner_ref,
                claim_ref=claim.claim_ref or "",
                generation=claim.generation,
                status=MissionStepStatus.recovery_required,
                reason_refs=["reason-ref:mission-step:dispatch-reconciliation-failed"],
            )
            raise dispatch_error
        failure_category = dispatch_result.receipt.failure_category
        retryable_failure = (
            dispatch_result.receipt.status == AuthorityDispatchStatus.failed.value
            and failure_category is not None
            and failure_category in definition.retryable_failure_categories
            and definition.max_attempts > 1
            and request.approval_validation_request is None
        )
        if retryable_failure and claim.attempt_no < definition.max_attempts:
            adapter = self.dispatcher.adapters[request.adapter_ref]
            if adapter.descriptor.idempotent_replay_supported:
                try:
                    retried = self.step_store.schedule_retry(
                        definition.step_ref,
                        owner_ref=owner_ref,
                        claim_ref=claim.claim_ref or "",
                        generation=claim.generation,
                        failure_category=AuthorityDispatchFailureCategory(
                            failure_category
                        ),
                        dispatch_receipt=dispatch_result.receipt,
                        evidence_refs=self._evidence_refs(dispatch_result),
                    )
                except MissionStepConflictError as exc:
                    if str(exc) != "MISSION_STEP_RETRY_DEADLINE_EXHAUSTED":
                        raise
                else:
                    return AuthorityMissionStepResult(
                        step=self.step_store.read(retried.definition.step_ref),
                        dispatch_result=dispatch_result,
                        autonomous_retry_performed=True,
                    )
        status, reason_ref = self._terminal_posture(dispatch_result)
        if retryable_failure and claim.attempt_no >= definition.max_attempts:
            status = MissionStepStatus.dead_lettered
            reason_ref = "reason-ref:mission-step:retry-attempts-exhausted"
        evidence_refs = self._evidence_refs(dispatch_result)
        self.step_store.complete(
            definition.step_ref,
            owner_ref=owner_ref,
            claim_ref=claim.claim_ref or "",
            generation=claim.generation,
            status=status,
            reason_refs=[reason_ref, *dispatch_result.receipt.reason_refs],
            evidence_refs=evidence_refs,
            dispatch_receipt=dispatch_result.receipt,
        )
        if heartbeat_errors:
            raise MissionStepConflictError(
                "MISSION_STEP_HEARTBEAT_FAILED"
            ) from heartbeat_errors[0]
        return AuthorityMissionStepResult(
            step=self.step_store.read(definition.step_ref),
            dispatch_result=dispatch_result,
            replayed_terminal_step=dispatch_result.replayed,
        )

    def _cancel_expired_step(
        self,
        definition: MissionStepDefinition,
        request: AuthorityDispatchRequest,
    ) -> AuthorityMissionStepResult:
        dispatch_result = self.dispatcher.cancel(
            AuthorityDispatchCancelRequest(
                dispatch_ref=request.dispatch_ref,
                idempotency_ref=(
                    "idempotency-ref:mission-step:deadline-cancel:"
                    f"{hash_text(request.dispatch_ref)[:24]}"
                ),
                reason_ref="reason-ref:mission-step:deadline-expired-before-dispatch",
                safe_summary=("Cancel a prepared mission step whose deadline expired."),
            )
        )
        self._reconcile_dispatch(request, dispatch_result)
        self.step_store.reconcile_expired_dispatch(
            definition.step_ref,
            dispatch_receipt=dispatch_result.receipt,
            evidence_refs=self._evidence_refs(dispatch_result),
        )
        return AuthorityMissionStepResult(
            step=self.step_store.read(definition.step_ref),
            dispatch_result=dispatch_result,
            replayed_terminal_step=dispatch_result.replayed,
        )

    def _resolve_dispatch_receipt(
        self,
        dispatch_ref: str,
    ) -> AuthorityDispatchReceipt | None:
        return next(
            (
                receipt
                for receipt in reversed(self.dispatcher.list_receipts())
                if receipt.dispatch_ref == dispatch_ref
            ),
            None,
        )

    def validate_step(
        self,
        definition: MissionStepDefinition,
        request: AuthorityDispatchRequest,
    ) -> None:
        attempt_no = self._request_attempt_no(definition, request)
        if (
            definition.dependency_step_refs
            and definition.orchestration_plan_ref is None
        ):
            raise ValueError("MISSION_RUNNER_DURABLE_PLAN_BINDING_REQUIRED")
        if definition.orchestration_plan_ref is not None:
            if attempt_no == 1:
                planned_dispatch_ref = definition.planned_dispatch_ref
                planned_fingerprint_ref = (
                    definition.planned_dispatch_request_fingerprint_ref
                )
            else:
                planned_attempt = next(
                    item
                    for item in definition.planned_retry_attempts
                    if item.attempt_no == attempt_no
                )
                planned_dispatch_ref = planned_attempt.dispatch_ref
                planned_fingerprint_ref = (
                    planned_attempt.dispatch_request_fingerprint_ref
                )
            if (
                planned_dispatch_ref != request.dispatch_ref
                or planned_fingerprint_ref
                != authority_dispatch_request_fingerprint(request)
            ):
                raise ValueError(
                    "MISSION_RUNNER_PLANNED_DISPATCH_BINDING_INVALID"
                )
        adapter = self.dispatcher.adapters.get(definition.adapter_ref)
        if type(adapter) is not ToolRuntimeAuthorityDispatchAdapter:
            raise ValueError("MISSION_RUNNER_FILESYSTEM_ADAPTER_REQUIRED")
        descriptor = adapter.descriptor
        tool_request = request.tool_invocation_request
        expected = {
            "run_ref": definition.run_ref,
            "lease_ref": definition.lease_ref,
            "adapter_ref": definition.adapter_ref,
            "capability_ref": definition.capability_ref,
            "dispatch_ref": mission_step_dispatch_ref(
                definition.step_ref, attempt_no
            ),
            "idempotency_ref": mission_step_idempotency_ref(
                definition.step_ref, attempt_no
            ),
            "action_ref": mission_step_action_ref(definition.step_ref, attempt_no),
        }
        actual = {
            "run_ref": request.run_ref,
            "lease_ref": request.lease_ref,
            "adapter_ref": request.adapter_ref,
            "capability_ref": request.action_request.capability_ref,
            "dispatch_ref": request.dispatch_ref,
            "idempotency_ref": request.idempotency_ref,
            "action_ref": request.action_request.action_ref,
        }
        if actual != expected:
            raise ValueError("MISSION_RUNNER_DISPATCH_BINDING_INVALID")
        if (
            descriptor.tool_ref != FILESYSTEM_METADATA_TOOL_REF
            or descriptor.domain != AuthorityDomain.files.value
            or descriptor.capability != AuthorityCapability.read.value
            or request.action_request.domain != AuthorityDomain.files.value
            or request.action_request.capability != AuthorityCapability.read.value
            or tool_request.get("tool_ref") != FILESYSTEM_METADATA_TOOL_REF
            or request.operation_count != 1
            or request.estimated_cost_microusd != 0
        ):
            raise ValueError("MISSION_RUNNER_EXACT_FILESYSTEM_LANE_REQUIRED")
        root_ref = tool_request.get("metadata", {}).get("root_ref")
        if root_ref not in {root.root_ref for root in adapter.safe_roots}:
            raise ValueError("MISSION_RUNNER_INJECTED_ROOT_REQUIRED")
        if definition.max_attempts > 1:
            retry_claim = next(
                (
                    claim
                    for claim in request.action_request.constraint_claims
                    if claim.kind == AuthorityConstraintKind.retry_attempts.value
                ),
                None,
            )
            if (
                not descriptor.idempotent_replay_supported
                or descriptor.approval_required
                or request.approval_validation_request is not None
                or retry_claim is None
                or retry_claim.value != definition.max_attempts
            ):
                raise ValueError("MISSION_RUNNER_RETRY_AUTHORITY_REQUIRED")

    @staticmethod
    def _request_attempt_no(
        definition: MissionStepDefinition,
        request: AuthorityDispatchRequest,
    ) -> int:
        if definition.max_attempts == 1:
            return 1
        if request.dispatch_ref == definition.planned_dispatch_ref or (
            definition.planned_dispatch_ref is None
            and request.dispatch_ref
            == mission_step_dispatch_ref(definition.step_ref)
        ):
            return 1
        attempt = next(
            (
                item
                for item in definition.planned_retry_attempts
                if item.dispatch_ref == request.dispatch_ref
                and item.dispatch_request_fingerprint_ref
                == authority_dispatch_request_fingerprint(request)
            ),
            None,
        )
        if attempt is None:
            raise ValueError("MISSION_RUNNER_RETRY_REQUEST_NOT_PLANNED")
        return attempt.attempt_no

    def _reconcile_dispatch(
        self,
        request: AuthorityDispatchRequest,
        result: AuthorityDispatchResult,
    ) -> None:
        receipt = result.receipt
        if (
            receipt.dispatch_ref != request.dispatch_ref
            or receipt.run_ref != request.run_ref
            or receipt.idempotency_ref != request.idempotency_ref
            or receipt.lease_ref != request.lease_ref
            or receipt.action_ref != request.action_request.action_ref
            or receipt.adapter_ref != request.adapter_ref
            or receipt.capability_ref != request.action_request.capability_ref
        ):
            raise AuthorityDispatchCorruptionError(
                "MISSION_RUNNER_DISPATCH_RECEIPT_BINDING_INVALID"
            )
        latest = next(
            (
                item
                for item in reversed(self.dispatcher.list_receipts())
                if item.dispatch_ref == request.dispatch_ref
            ),
            None,
        )
        if latest is None or latest.receipt_ref != receipt.receipt_ref:
            raise AuthorityDispatchCorruptionError(
                "MISSION_RUNNER_DISPATCH_RECEIPT_NOT_DURABLE"
            )

    @staticmethod
    def _terminal_posture(
        result: AuthorityDispatchResult,
    ) -> tuple[MissionStepStatus, str]:
        status = result.receipt.status
        if status == AuthorityDispatchStatus.succeeded.value:
            if (
                not result.receipt.execution_started
                or not result.receipt.adapter_invocation_performed
                or result.receipt.budget_settlement_receipt_ref is None
            ):
                return (
                    MissionStepStatus.recovery_required,
                    "reason-ref:mission-step:success-evidence-incomplete",
                )
            return MissionStepStatus.succeeded, "reason-ref:mission-step:succeeded"
        if status == AuthorityDispatchStatus.cancelled_before_start.value:
            return MissionStepStatus.cancelled, "reason-ref:mission-step:cancelled"
        if result.recovery_required:
            return (
                MissionStepStatus.recovery_required,
                "reason-ref:mission-step:dispatch-recovery-required",
            )
        return MissionStepStatus.failed, "reason-ref:mission-step:dispatch-failed"

    @staticmethod
    def _evidence_refs(result: AuthorityDispatchResult) -> list[str]:
        receipt = result.receipt
        values = [
            receipt.receipt_ref,
            receipt.entry_hash_ref,
            receipt.authority_decision_ref,
            receipt.authority_policy_receipt_ref,
            receipt.approval_validation_ref,
            receipt.execution_fence_ref,
            receipt.budget_reservation_receipt_ref,
            receipt.budget_start_receipt_ref,
            receipt.budget_settlement_receipt_ref,
            receipt.execution_ref,
            *receipt.evidence_refs,
            *receipt.output_refs,
        ]
        return list(dict.fromkeys(value for value in values if value is not None))
