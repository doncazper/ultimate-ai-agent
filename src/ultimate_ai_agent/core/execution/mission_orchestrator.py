from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.authority.contracts import (
    AuthorityDecisionOutcome,
    AuthorityLeaseScope,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.authority.authority_constants import (
    AUTHORITY_STATE_LOCK_KEY,
)
from ultimate_ai_agent.core.authority.dispatch_contracts import AuthorityDispatchRequest
from ultimate_ai_agent.core.authority.dispatch_contracts import (
    AuthorityDispatchWorkerClaimFence,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    authority_dispatch_request_fingerprint,
)
from ultimate_ai_agent.core.execution.durable_mission_plans import (
    DURABLE_MISSION_PLAN_MAX_STEPS,
    DurableMissionPlan,
    DurableMissionPlanReceipt,
    DurableMissionPlanStepBinding,
    DurableMissionPlanStore,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MISSION_PLAN_MATERIALIZATION_LOCK_KEY,
    MissionStepConflictError,
    MissionStepDefinition,
    MissionStepReadModel,
    MissionStepStatus,
    MissionStepStore,
    TERMINAL_MISSION_STEP_STATUSES,
)
from ultimate_ai_agent.core.execution.mission_runner import (
    AuthorityMissionRunner,
    mission_step_action_ref,
    mission_step_dispatch_ref,
    mission_step_idempotency_ref,
)
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)


AUTHORITY_MISSION_ORCHESTRATION_SCHEMA_VERSION = (
    "uaa-authority-mission-orchestration.v1"
)


class AuthorityMissionOrchestrationStatus(str, Enum):
    succeeded = "succeeded"
    failed = "failed"
    recovery_required = "recovery_required"
    in_progress = "in_progress"


class _MissionOrchestrationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class AuthorityMissionOrchestrationStepInput(_MissionOrchestrationModel):
    definition: MissionStepDefinition
    request: AuthorityDispatchRequest


class AuthorityMissionOrchestrationRequest(_MissionOrchestrationModel):
    schema_version: Literal["uaa-authority-mission-orchestration.v1"] = (
        AUTHORITY_MISSION_ORCHESTRATION_SCHEMA_VERSION
    )
    plan_ref: str
    mission_ref: str
    run_ref: str
    steps: list[AuthorityMissionOrchestrationStepInput] = Field(
        ...,
        min_length=1,
        max_length=DURABLE_MISSION_PLAN_MAX_STEPS,
    )
    safe_summary: str = Field(..., min_length=1, max_length=320)
    fail_fast: Literal[True] = True
    background_execution_requested: Literal[False] = False
    automatic_retry_requested: Literal[False] = False
    parallel_execution_requested: Literal[False] = False

    @model_validator(mode="after")
    def validate_request(self) -> "AuthorityMissionOrchestrationRequest":
        for value, field_name in [
            (self.plan_ref, "authority_mission_orchestration_plan_ref"),
            (self.mission_ref, "authority_mission_orchestration_mission_ref"),
            (self.run_ref, "authority_mission_orchestration_run_ref"),
        ]:
            validate_task_ref(value, field_name)
        validate_safe_task_text(
            self.safe_summary,
            "authority_mission_orchestration_summary",
        )
        step_refs = [step.definition.step_ref for step in self.steps]
        if len(step_refs) != len(set(step_refs)):
            raise ValueError("AUTHORITY_MISSION_ORCHESTRATION_DUPLICATE_STEP_DENIED")
        for step in self.steps:
            definition = step.definition
            request = step.request
            if (
                definition.mission_ref != self.mission_ref
                or definition.run_ref != self.run_ref
                or request.run_ref != self.run_ref
                or request.lease_ref != definition.lease_ref
                or request.adapter_ref != definition.adapter_ref
                or request.action_request.capability_ref != definition.capability_ref
                or request.dispatch_ref
                != mission_step_dispatch_ref(definition.step_ref)
                or request.idempotency_ref
                != mission_step_idempotency_ref(definition.step_ref)
                or request.action_request.action_ref
                != mission_step_action_ref(definition.step_ref)
                or request.start_deadline != definition.deadline
            ):
                raise ValueError("AUTHORITY_MISSION_ORCHESTRATION_STEP_BINDING_INVALID")
            if self.mission_ref not in request.action_request.resource_refs:
                raise ValueError(
                    "AUTHORITY_MISSION_ORCHESTRATION_ACTION_MISSION_SCOPE_REQUIRED"
                )
            recognized_constraint_missions = {
                value
                for key in ("mission_ref", "authority_mission_ref")
                if (value := request.action_request.constraints.get(key)) is not None
            }
            if recognized_constraint_missions - {self.mission_ref}:
                raise ValueError(
                    "AUTHORITY_MISSION_ORCHESTRATION_ACTION_MISSION_SCOPE_CONFLICT"
                )
            planned_values = (
                definition.orchestration_plan_ref,
                definition.planned_dispatch_ref,
                definition.planned_dispatch_request_fingerprint_ref,
            )
            if any(value is not None for value in planned_values) and (
                definition.orchestration_plan_ref != self.plan_ref
                or definition.planned_dispatch_ref != request.dispatch_ref
                or definition.planned_dispatch_request_fingerprint_ref
                != authority_dispatch_request_fingerprint(request)
            ):
                raise ValueError(
                    "AUTHORITY_MISSION_ORCHESTRATION_PREBOUND_STEP_CONFLICT"
                )
        self.build_durable_plan()
        return self

    def bound_definition(
        self,
        step: AuthorityMissionOrchestrationStepInput,
    ) -> MissionStepDefinition:
        return step.definition.model_copy(
            update={
                "orchestration_plan_ref": self.plan_ref,
                "planned_dispatch_ref": step.request.dispatch_ref,
                "planned_dispatch_request_fingerprint_ref": (
                    authority_dispatch_request_fingerprint(step.request)
                ),
            }
        )

    def build_durable_plan(self) -> DurableMissionPlan:
        return DurableMissionPlan(
            plan_ref=self.plan_ref,
            mission_ref=self.mission_ref,
            run_ref=self.run_ref,
            ordered_steps=[
                DurableMissionPlanStepBinding(
                    step_ref=step.definition.step_ref,
                    definition_fingerprint_ref=self.bound_definition(
                        step
                    ).fingerprint_ref,
                    dispatch_ref=step.request.dispatch_ref,
                    dispatch_request_fingerprint_ref=(
                        authority_dispatch_request_fingerprint(step.request)
                    ),
                    dependency_step_refs=list(step.definition.dependency_step_refs),
                )
                for step in self.steps
            ],
            safe_summary=self.safe_summary,
        )


class AuthorityMissionOrchestrationResult(_MissionOrchestrationModel):
    schema_version: Literal["uaa-authority-mission-orchestration.v1"] = (
        AUTHORITY_MISSION_ORCHESTRATION_SCHEMA_VERSION
    )
    plan_ref: str
    plan_fingerprint_ref: str
    plan_receipt_ref: str
    mission_ref: str
    run_ref: str
    status: AuthorityMissionOrchestrationStatus
    steps: list[MissionStepReadModel]
    evaluated_step_count: int = Field(..., ge=0)
    started_step_count: int = Field(..., ge=0)
    invoked_step_count: int = Field(..., ge=0)
    replayed_step_count: int = Field(..., ge=0)
    dependency_blocked_step_count: int = Field(..., ge=0)
    reason_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    operator_summary: str = Field(..., min_length=1, max_length=520)
    request_scoped_authority_evaluated_for_each_attempted_step: Literal[True] = True
    execution_authority_minted_by_orchestrator: Literal[False] = False
    direct_adapter_invocation_performed: Literal[False] = False
    background_execution_performed: Literal[False] = False
    parallel_execution_performed: Literal[False] = False
    automatic_retry_performed: Literal[False] = False
    mission_cancellation_claimed: Literal[False] = False
    raw_request_payload_persisted: Literal[False] = False
    raw_output_persisted: Literal[False] = False


class SynchronousAuthorityMissionOrchestrator:
    def __init__(
        self,
        *,
        runner: AuthorityMissionRunner,
        plan_store: DurableMissionPlanStore,
    ) -> None:
        if runner.step_store.state_dir.resolve() != plan_store.state_dir.resolve():
            raise ValueError("AUTHORITY_MISSION_ORCHESTRATION_STATE_DIR_MISMATCH")
        self.runner = runner
        self.step_store: MissionStepStore = runner.step_store
        self.plan_store = plan_store
        self.step_store._bind_plan_binding_resolver(  # noqa: SLF001
            self.plan_store.resolve_definition_binding
        )

    def run(
        self,
        request: AuthorityMissionOrchestrationRequest,
        *,
        owner_ref: str,
        claim_ttl_seconds: int = 30,
        max_step_count: Literal[1] | None = None,
        heartbeat_interval_seconds: int | None = None,
        worker_claim_fence: AuthorityDispatchWorkerClaimFence | None = None,
    ) -> AuthorityMissionOrchestrationResult:
        validate_task_ref(owner_ref, "authority_mission_orchestration_owner_ref")
        request = AuthorityMissionOrchestrationRequest.model_validate(
            request.model_dump(mode="python")
        )
        plan, plan_receipt, bound_definitions = self._materialize(request)
        steps_by_ref = {step.definition.step_ref: step for step in request.steps}
        orchestration_context = self.plan_store.resolve_definition_binding(
            bound_definitions[plan.topological_step_refs[0]]
        )
        if orchestration_context is None:
            raise ValueError("AUTHORITY_MISSION_ORCHESTRATION_PLAN_CONTEXT_REQUIRED")

        evaluated = 0
        replayed = 0
        terminal_failure = self._first_terminal_failure(plan)
        if terminal_failure is not None:
            self._apply_fail_fast(plan, terminal_failure.step_ref)
            return self._result(
                request,
                plan,
                plan_receipt,
                evaluated=evaluated,
                replayed=replayed,
            )

        for step_ref in plan.topological_step_refs:
            current = self.step_store.read(step_ref)
            if current.status == MissionStepStatus.succeeded.value:
                replayed += 1
                continue
            if current.status in TERMINAL_MISSION_STEP_STATUSES:
                self._apply_fail_fast(plan, current.step_ref)
                break
            terminal_failure = self._first_terminal_failure(plan)
            if terminal_failure is not None:
                self._apply_fail_fast(plan, terminal_failure.step_ref)
                break
            step = steps_by_ref[step_ref]
            try:
                result = self.runner._run_orchestrated_once(  # noqa: SLF001
                    bound_definitions[step_ref],
                    step.request,
                    owner_ref=owner_ref,
                    claim_ttl_seconds=claim_ttl_seconds,
                    orchestration_context=orchestration_context,
                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                    worker_claim_fence=worker_claim_fence,
                )
            except MissionStepConflictError as exc:
                if str(exc) == "MISSION_STEP_ALREADY_CLAIMED":
                    break
                raise
            if result.replayed_terminal_step:
                replayed += 1
            else:
                evaluated += 1
            if result.step.status != MissionStepStatus.succeeded.value:
                self._apply_fail_fast(plan, result.step.step_ref)
                break
            if max_step_count is not None and evaluated >= max_step_count:
                break
        return self._result(
            request,
            plan,
            plan_receipt,
            evaluated=evaluated,
            replayed=replayed,
        )

    def materialize(
        self,
        request: AuthorityMissionOrchestrationRequest,
    ) -> DurableMissionPlanReceipt:
        """Persist one immutable safe-ref plan without starting an adapter."""
        validated = AuthorityMissionOrchestrationRequest.model_validate(
            request.model_dump(mode="python")
        )
        _, receipt, _ = self._materialize(validated)
        return receipt

    def _materialize(
        self,
        request: AuthorityMissionOrchestrationRequest,
    ) -> tuple[
        DurableMissionPlan,
        DurableMissionPlanReceipt,
        dict[str, MissionStepDefinition],
    ]:
        plan = request.build_durable_plan()
        steps_by_ref = {step.definition.step_ref: step for step in request.steps}
        bound_definitions = {
            step_ref: request.bound_definition(step)
            for step_ref, step in steps_by_ref.items()
        }
        self._preflight(request, bound_definitions)
        definitions = [
            bound_definitions[step_ref] for step_ref in plan.topological_step_refs
        ]
        with (
            self.step_store.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
            self.step_store.lock_manager.acquire(MISSION_PLAN_MATERIALIZATION_LOCK_KEY),
        ):
            self.plan_store.preflight_acceptance(plan)
            self.step_store._preflight_definitions_under_orchestration_lock(  # noqa: SLF001
                definitions
            )
            plan_receipt = self.plan_store._accept_under_materialization_lock(  # noqa: SLF001
                plan
            )
            self.step_store._materialize_definitions_under_orchestration_lock(  # noqa: SLF001
                definitions
            )
        return plan, plan_receipt, bound_definitions

    def _preflight(
        self,
        request: AuthorityMissionOrchestrationRequest,
        bound_definitions: dict[str, MissionStepDefinition],
    ) -> None:
        leases = {
            lease.lease_ref: lease
            for lease in self.runner.dispatcher.lease_store.list_leases(
                active_only=False
            )
        }
        for step in request.steps:
            definition = bound_definitions[step.definition.step_ref]
            lease = leases.get(step.request.lease_ref)
            if (
                lease is None
                or lease.scope != AuthorityLeaseScope.mission.value
                or lease.mission_ref != request.mission_ref
            ):
                raise ValueError(
                    "AUTHORITY_MISSION_ORCHESTRATION_MISSION_LEASE_REQUIRED"
                )
            decision = evaluate_authority_request(
                step.request.action_request,
                [lease],
            )
            policy_eligible = (
                decision.outcome == AuthorityDecisionOutcome.allow.value
                or (
                    decision.outcome == AuthorityDecisionOutcome.ask.value
                    and step.request.approval_validation_request is not None
                )
            )
            if not policy_eligible or decision.lease_ref != lease.lease_ref:
                raise ValueError(
                    "AUTHORITY_MISSION_ORCHESTRATION_POLICY_PREFLIGHT_DENIED"
                )
            self.runner.validate_step(definition, step.request)
            if self.runner.dispatcher.structural_preflight_reason_refs(step.request):
                raise ValueError(
                    "AUTHORITY_MISSION_ORCHESTRATION_STRUCTURAL_PREFLIGHT_DENIED"
                )

    def _apply_fail_fast(
        self,
        plan: DurableMissionPlan,
        terminal_step_ref: str,
    ) -> None:
        for step_ref in plan.topological_step_refs:
            current = self.step_store.read(step_ref)
            if current.status != MissionStepStatus.pending.value:
                continue
            binding = next(
                item for item in plan.ordered_steps if item.step_ref == step_ref
            )
            for dependency_ref in binding.dependency_step_refs:
                dependency = self.step_store.read(dependency_ref)
                if (
                    dependency.status in TERMINAL_MISSION_STEP_STATUSES
                    and dependency.status != MissionStepStatus.succeeded.value
                ):
                    self.step_store.block_from_terminal_dependency(
                        step_ref,
                        dependency_step_ref=dependency_ref,
                    )
                    break
            else:
                self.step_store.halt_from_fail_fast_terminal(
                    step_ref,
                    terminal_step_ref=terminal_step_ref,
                )

    def _first_terminal_failure(
        self,
        plan: DurableMissionPlan,
    ) -> MissionStepReadModel | None:
        return next(
            (
                step
                for step in (
                    self.step_store.read(step_ref)
                    for step_ref in plan.topological_step_refs
                )
                if step.status in TERMINAL_MISSION_STEP_STATUSES
                and step.status != MissionStepStatus.succeeded.value
            ),
            None,
        )

    def _result(
        self,
        request: AuthorityMissionOrchestrationRequest,
        plan: DurableMissionPlan,
        plan_receipt: DurableMissionPlanReceipt,
        *,
        evaluated: int,
        replayed: int,
    ) -> AuthorityMissionOrchestrationResult:
        steps, latest_receipts = self.step_store.snapshot(plan.topological_step_refs)
        statuses = {step.status for step in steps}
        if MissionStepStatus.recovery_required.value in statuses:
            status = AuthorityMissionOrchestrationStatus.recovery_required
            reason_refs = [
                "reason-ref:authority-mission-orchestration:recovery-required"
            ]
        elif any(
            item
            in {
                MissionStepStatus.failed.value,
                MissionStepStatus.cancelled.value,
                MissionStepStatus.dependency_blocked.value,
                MissionStepStatus.fail_fast_halted.value,
            }
            for item in statuses
        ):
            status = AuthorityMissionOrchestrationStatus.failed
            reason_refs = ["reason-ref:authority-mission-orchestration:failed"]
        elif all(item == MissionStepStatus.succeeded.value for item in statuses):
            status = AuthorityMissionOrchestrationStatus.succeeded
            reason_refs = ["reason-ref:authority-mission-orchestration:succeeded"]
        else:
            status = AuthorityMissionOrchestrationStatus.in_progress
            reason_refs = ["reason-ref:authority-mission-orchestration:in-progress"]
        evidence_refs = [
            plan_receipt.receipt_ref,
            plan_receipt.entry_hash_ref,
            *[
                value
                for step_ref in plan.topological_step_refs
                for value in [
                    latest_receipts[step_ref].receipt_ref,
                    latest_receipts[step_ref].entry_hash_ref,
                ]
            ],
        ]
        dispatch_receipts = self.runner.dispatcher.list_receipts()
        return AuthorityMissionOrchestrationResult(
            plan_ref=request.plan_ref,
            plan_fingerprint_ref=plan.fingerprint_ref,
            plan_receipt_ref=plan_receipt.receipt_ref,
            mission_ref=request.mission_ref,
            run_ref=request.run_ref,
            status=status,
            steps=steps,
            evaluated_step_count=evaluated,
            started_step_count=sum(
                receipt.dispatch_ref is not None
                and any(
                    dispatch.dispatch_ref == receipt.dispatch_ref
                    and dispatch.execution_started
                    for dispatch in dispatch_receipts
                )
                for receipt in latest_receipts.values()
            ),
            invoked_step_count=sum(
                receipt.dispatch_ref is not None
                and any(
                    dispatch.dispatch_ref == receipt.dispatch_ref
                    and dispatch.adapter_invocation_performed
                    for dispatch in dispatch_receipts
                )
                for receipt in latest_receipts.values()
            ),
            replayed_step_count=replayed,
            dependency_blocked_step_count=sum(
                step.status == MissionStepStatus.dependency_blocked.value
                for step in steps
            ),
            reason_refs=reason_refs,
            evidence_refs=evidence_refs,
            operator_summary=self._operator_summary(status),
        )

    @staticmethod
    def _operator_summary(status: AuthorityMissionOrchestrationStatus) -> str:
        summaries = {
            AuthorityMissionOrchestrationStatus.succeeded.value: (
                "Bounded synchronous mission orchestration succeeded through "
                "request-scoped AuthorityDispatcher evaluation."
            ),
            AuthorityMissionOrchestrationStatus.failed.value: (
                "Bounded synchronous mission orchestration failed closed; "
                "unscheduled work is durably blocked or halted."
            ),
            AuthorityMissionOrchestrationStatus.recovery_required.value: (
                "Mission orchestration requires recovery because durable execution "
                "truth is unresolved."
            ),
            AuthorityMissionOrchestrationStatus.in_progress.value: (
                "Mission orchestration remains in progress under an existing fenced claim."
            ),
        }
        key = (
            status.value
            if isinstance(status, AuthorityMissionOrchestrationStatus)
            else status
        )
        return summaries[key]
