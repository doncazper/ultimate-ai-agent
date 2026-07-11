from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from ultimate_ai_agent.core.authority.contracts import (
    AuthorityCapability,
    AuthorityDomain,
)
from ultimate_ai_agent.core.authority.dispatch_contracts import (
    AuthorityDispatchCancelRequest,
    AuthorityDispatchReceipt,
    AuthorityDispatchRequest,
    AuthorityDispatchResult,
    AuthorityDispatchStatus,
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


def mission_step_action_ref(step_ref: str) -> str:
    return f"authority-action-ref:mission-step:{hash_text(step_ref)[:24]}"


def mission_step_dispatch_ref(step_ref: str) -> str:
    return f"authority-dispatch-ref:mission-step:{hash_text(step_ref)[:24]}"


def mission_step_idempotency_ref(step_ref: str) -> str:
    return f"idempotency-ref:mission-step:{hash_text(step_ref)[:24]}"


class AuthorityMissionStepResult(BaseModel):
    step: MissionStepReadModel
    dispatch_result: AuthorityDispatchResult | None = None
    replayed_terminal_step: bool = False
    execution_authority_minted_by_runner: Literal[False] = False
    autonomous_retry_performed: Literal[False] = False

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

    def run_once(
        self,
        definition: MissionStepDefinition,
        request: AuthorityDispatchRequest,
        *,
        owner_ref: str,
        claim_ttl_seconds: int = 30,
    ) -> AuthorityMissionStepResult:
        if definition.orchestration_plan_ref is not None:
            raise ValueError("MISSION_RUNNER_ORCHESTRATED_ENTRYPOINT_REQUIRED")
        return self._run_once(
            definition,
            request,
            owner_ref=owner_ref,
            claim_ttl_seconds=claim_ttl_seconds,
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
    ) -> AuthorityMissionStepResult:
        if definition.orchestration_plan_ref != orchestration_context.plan_ref:
            raise ValueError("MISSION_RUNNER_ORCHESTRATION_CONTEXT_INVALID")
        return self._run_once(
            definition,
            request,
            owner_ref=owner_ref,
            claim_ttl_seconds=claim_ttl_seconds,
            orchestration_context=orchestration_context,
        )

    def _run_once(
        self,
        definition: MissionStepDefinition,
        request: AuthorityDispatchRequest,
        *,
        owner_ref: str,
        claim_ttl_seconds: int,
        orchestration_context: MissionStepOrchestrationContext | None,
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
                        dispatch_result = self.dispatcher.execute(request)
            self._reconcile_dispatch(request, dispatch_result)
        except (AuthorityDispatchConflictError, AuthorityDispatchCorruptionError):
            self.step_store.complete(
                definition.step_ref,
                owner_ref=owner_ref,
                claim_ref=claim.claim_ref or "",
                generation=claim.generation,
                status=MissionStepStatus.recovery_required,
                reason_refs=["reason-ref:mission-step:dispatch-reconciliation-failed"],
            )
            raise
        status, reason_ref = self._terminal_posture(dispatch_result)
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
        if (
            definition.dependency_step_refs
            and definition.orchestration_plan_ref is None
        ):
            raise ValueError("MISSION_RUNNER_DURABLE_PLAN_BINDING_REQUIRED")
        if definition.orchestration_plan_ref is not None and (
            definition.planned_dispatch_ref != request.dispatch_ref
            or definition.planned_dispatch_request_fingerprint_ref
            != authority_dispatch_request_fingerprint(request)
        ):
            raise ValueError("MISSION_RUNNER_PLANNED_DISPATCH_BINDING_INVALID")
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
            "dispatch_ref": mission_step_dispatch_ref(definition.step_ref),
            "idempotency_ref": mission_step_idempotency_ref(definition.step_ref),
            "action_ref": mission_step_action_ref(definition.step_ref),
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
            receipt.budget_reservation_receipt_ref,
            receipt.budget_start_receipt_ref,
            receipt.budget_settlement_receipt_ref,
            receipt.execution_ref,
            *receipt.evidence_refs,
            *receipt.output_refs,
        ]
        return list(dict.fromkeys(value for value in values if value is not None))
