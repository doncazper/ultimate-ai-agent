from __future__ import annotations

from datetime import datetime
from pathlib import Path
import threading
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityConstraintClaim,
    AuthorityConstraintKind,
    AuthorityDispatchRequest,
    AuthorityDomain,
    AuthorityLeaseStore,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatcher,
    authority_dispatch_execution_ref,
    build_authority_dispatch_cost_estimate_ref,
    build_authority_dispatch_cost_governor_decision_ref,
)
from ultimate_ai_agent.core.costs import BudgetScope, CostBudget, CostEstimate
from ultimate_ai_agent.core.execution.durable_mission_plans import (
    DurableMissionPlanStore,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepDefinition,
    MissionStepStore,
)
from ultimate_ai_agent.core.execution.mission_orchestrator import (
    AuthorityMissionOrchestrationRequest,
    AuthorityMissionOrchestrationResult,
    AuthorityMissionOrchestrationStepInput,
    SynchronousAuthorityMissionOrchestrator,
)
from ultimate_ai_agent.core.execution.mission_runner import (
    AuthorityMissionRunner,
    mission_step_action_ref,
    mission_step_dispatch_ref,
    mission_step_idempotency_ref,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.tools.runtime.contracts import ToolInvocationRequest
from ultimate_ai_agent.core.tools.runtime.enums import ToolInvocationKind

from .adapter import (
    SEALED_CALCULATION_GRAMMAR_POLICY_REF,
    SealedCalculationAuthorityDispatchAdapter,
)
from .backend import (
    DockerSealedCalculationBackend,
    TransientCalculationInputStore,
)
from .contracts import (
    SEALED_CALCULATION_ADAPTER_REF,
    SEALED_CALCULATION_CAPABILITY_REF,
    SEALED_CALCULATION_LANE_REF,
    SEALED_CALCULATION_ROLLBACK_REF,
    SEALED_CALCULATION_SAFE_DISABLE_REF,
    SEALED_CALCULATION_TARGET_REF,
    SEALED_CALCULATION_TOOL_NAME,
    SEALED_CALCULATION_TOOL_REF,
    SealedCalculationRequest,
    SealedCalculationResult,
)


class _SealedCalculationMissionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class SealedCalculationMissionRequest(_SealedCalculationMissionModel):
    request_ref: str
    input_ref: str
    expression: str = Field(
        ...,
        min_length=1,
        max_length=512,
        exclude=True,
        repr=False,
    )
    expression_sha256: str
    plan_ref: str
    mission_ref: str
    run_ref: str
    step_ref: str
    lease_ref: str
    request_created_at: datetime
    start_deadline: datetime
    safe_summary: str = "Run one sealed deterministic calculation mission."

    @model_validator(mode="after")
    def validate_request(self) -> "SealedCalculationMissionRequest":
        for ref in (
            self.request_ref,
            self.input_ref,
            self.plan_ref,
            self.mission_ref,
            self.run_ref,
            self.step_ref,
            self.lease_ref,
        ):
            validate_execution_ref(ref, "sealed_calculation_mission_ref")
        validate_safe_execution_text(self.safe_summary, "sealed_calculation_summary")
        if self.request_created_at.tzinfo is None or self.start_deadline.tzinfo is None:
            raise ValueError("SEALED_CALCULATION_START_DEADLINE_TIMEZONE_REQUIRED")
        if self.request_created_at >= self.start_deadline:
            raise ValueError("SEALED_CALCULATION_START_DEADLINE_INVALID")
        if self.expression_sha256 != hash_text(self.expression):
            raise ValueError("SEALED_CALCULATION_EXPRESSION_HASH_MISMATCH")
        return self


class SealedCalculationMissionResult(_SealedCalculationMissionModel):
    orchestration: AuthorityMissionOrchestrationResult
    transient_result: SealedCalculationResult | None = None
    expression_sha256: str
    output_sha256: str | None = None
    result_preview: str | None = Field(default=None, max_length=128)
    result_is_evidence_not_authority: Literal[True] = True
    raw_expression_persisted: Literal[False] = False
    raw_result_persisted: Literal[False] = False
    no_per_invocation_approval_used: Literal[True] = True
    exact_mission_lease_required: Literal[True] = True
    safe_summary: str

    @model_validator(mode="after")
    def validate_result(self) -> "SealedCalculationMissionResult":
        validate_safe_execution_text(self.safe_summary, "sealed_calculation_summary")
        if self.transient_result is not None and (
            self.output_sha256 != self.transient_result.output_sha256
            or self.result_preview != self.transient_result.result_preview
        ):
            raise ValueError("SEALED_CALCULATION_MISSION_RESULT_BINDING_INVALID")
        return self


class SealedCalculationMissionService:
    def __init__(
        self,
        *,
        state_dir: Path,
        backend: DockerSealedCalculationBackend,
        lease_store: AuthorityLeaseStore,
    ) -> None:
        self.input_store = TransientCalculationInputStore()
        self._run_lock = threading.RLock()
        self.adapter = SealedCalculationAuthorityDispatchAdapter(
            backend=backend,
            input_store=self.input_store,
        )
        dispatcher = AuthorityDispatcher(
            state_dir,
            adapters=[self.adapter],
            lease_store=lease_store,
        )
        self.orchestrator = SynchronousAuthorityMissionOrchestrator(
            runner=AuthorityMissionRunner(
                dispatcher=dispatcher,
                step_store=MissionStepStore(state_dir),
            ),
            plan_store=DurableMissionPlanStore(state_dir),
        )

    def run(
        self,
        request: SealedCalculationMissionRequest,
        *,
        owner_ref: str,
    ) -> SealedCalculationMissionResult:
        with self._run_lock:
            return self._run_once(request, owner_ref=owner_ref)

    def _run_once(
        self,
        request: SealedCalculationMissionRequest,
        *,
        owner_ref: str,
    ) -> SealedCalculationMissionResult:
        validate_execution_ref(owner_ref, "sealed_calculation_owner_ref")
        transient = SealedCalculationRequest(
            request_ref=request.request_ref,
            input_ref=request.input_ref,
            expression=request.expression,
            expression_sha256=request.expression_sha256,
        )
        action_resources = self._action_resource_refs(request)
        self._require_exact_mission_lease(request, action_resources)
        self.input_store.put(transient)
        try:
            orchestration_request = self._build_orchestration_request(
                request,
                transient,
                action_resources,
            )
            orchestration = self.orchestrator.run(
                orchestration_request,
                owner_ref=owner_ref,
            )
        finally:
            self.input_store.discard(request.input_ref)
        dispatch_request = orchestration_request.steps[0].request
        execution_ref = authority_dispatch_execution_ref(dispatch_request)
        transient_result = self.adapter.take_result(execution_ref)
        return SealedCalculationMissionResult(
            orchestration=orchestration,
            transient_result=transient_result,
            expression_sha256=request.expression_sha256,
            output_sha256=(
                transient_result.output_sha256
                if transient_result is not None
                else next(
                    (
                        ref.removeprefix("output-hash-ref:sha256:")
                        for ref in orchestration.evidence_refs
                        if ref.startswith("output-hash-ref:sha256:")
                    ),
                    None,
                )
            ),
            result_preview=(
                transient_result.result_preview
                if transient_result is not None
                else None
            ),
            safe_summary=(
                "Sealed calculation mission completed with transient numeric evidence."
                if transient_result is not None
                else "Sealed calculation mission replay returned durable content-free evidence only."
            ),
        )

    def _build_orchestration_request(
        self,
        request: SealedCalculationMissionRequest,
        transient: SealedCalculationRequest,
        action_resources: list[str],
    ) -> AuthorityMissionOrchestrationRequest:
        dispatch_ref = mission_step_dispatch_ref(request.step_ref)
        idempotency_ref = mission_step_idempotency_ref(request.step_ref)
        cost_estimate = CostEstimate(
            estimate_id=f"cost-estimate:sealed-calculation:{hash_text(dispatch_ref)}",
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            estimated_cost_usd=0,
            estimated_token_cost_usd=0,
            created_at=request.request_created_at,
        )
        cost_budgets = [
            CostBudget(
                budget_id=f"cost-budget:sealed-calculation:{hash_text(request.run_ref)}",
                scope=BudgetScope.run,
                scope_id=request.run_ref,
                max_cost_usd=0,
                max_total_tokens=1,
                created_at=request.request_created_at,
            )
        ]
        provisional_action = AuthorityActionRequest(
            action_ref=mission_step_action_ref(request.step_ref),
            domain=AuthorityDomain.workspace,
            capability=AuthorityCapability.execute,
            capability_ref=SEALED_CALCULATION_CAPABILITY_REF,
            lane_ref=SEALED_CALCULATION_LANE_REF,
            adapter_ref=SEALED_CALCULATION_ADAPTER_REF,
            resource_refs=action_resources,
            constraint_claims=[
                AuthorityConstraintClaim(
                    kind=AuthorityConstraintKind.operation_budget,
                    value=1,
                ),
                AuthorityConstraintClaim(
                    kind=AuthorityConstraintKind.cost_budget_microusd,
                    value=0,
                ),
            ],
            constraints={
                "mission_ref": request.mission_ref,
                "target_ref": SEALED_CALCULATION_TARGET_REF,
            },
            rollback_ref=SEALED_CALCULATION_ROLLBACK_REF,
            safe_disable_ref=SEALED_CALCULATION_SAFE_DISABLE_REF,
            safe_summary="Evaluate one bounded arithmetic expression in the sealed backend.",
        )
        metadata = {
            "input_ref": transient.input_ref,
            "expression_sha256": transient.expression_sha256,
            "expression_bytes": len(transient.expression.encode("utf-8")),
            "target_ref": SEALED_CALCULATION_TARGET_REF,
            "grammar_policy_ref": SEALED_CALCULATION_GRAMMAR_POLICY_REF,
            "limits_ref": self.adapter._backend.attestation.limits_ref,  # noqa: SLF001
            "attestation_ref": self.adapter._backend.attestation.attestation_ref,  # noqa: SLF001
        }
        tool_request = ToolInvocationRequest(
            invocation_id=dispatch_ref,
            tool_ref=SEALED_CALCULATION_TOOL_REF,
            tool_name=SEALED_CALCULATION_TOOL_NAME,
            invocation_kind=ToolInvocationKind.sealed_arithmetic,
            replay_key=idempotency_ref,
            safe_summary="Resolve one transient bounded arithmetic input by exact hash.",
            input_refs=[transient.input_ref, SEALED_CALCULATION_TARGET_REF],
            metadata_refs=[
                SEALED_CALCULATION_GRAMMAR_POLICY_REF,
                self.adapter._backend.attestation.attestation_ref,  # noqa: SLF001
            ],
            metadata=metadata,
        )
        provisional_dispatch = AuthorityDispatchRequest(
            dispatch_ref=dispatch_ref,
            run_ref=request.run_ref,
            idempotency_ref=idempotency_ref,
            lease_ref=request.lease_ref,
            adapter_ref=SEALED_CALCULATION_ADAPTER_REF,
            action_request=provisional_action,
            tool_invocation_request=tool_request.model_dump(mode="json"),
            operation_count=1,
            estimated_cost_microusd=0,
            cost_estimate=cost_estimate,
            cost_budgets=cost_budgets,
            cost_estimate_ref=build_authority_dispatch_cost_estimate_ref(cost_estimate),
            cost_governor_decision_ref=(
                build_authority_dispatch_cost_governor_decision_ref(
                    cost_estimate,
                    cost_budgets,
                )
            ),
            cost_governor_allowed=True,
            start_deadline=request.start_deadline,
            safe_summary="Run one exact sealed calculation mission step.",
        )
        policy_ref = self.adapter.policy_decision_ref(provisional_dispatch)
        action = provisional_action.model_copy(
            update={
                "constraints": {
                    **provisional_action.constraints,
                    "policy_decision_ref": policy_ref,
                }
            }
        )
        dispatch = provisional_dispatch.model_copy(update={"action_request": action})
        definition = MissionStepDefinition(
            mission_ref=request.mission_ref,
            run_ref=request.run_ref,
            step_ref=request.step_ref,
            capability_ref=SEALED_CALCULATION_CAPABILITY_REF,
            adapter_ref=SEALED_CALCULATION_ADAPTER_REF,
            lease_ref=request.lease_ref,
            deadline=request.start_deadline,
            safe_summary="Run one exact no-approval sealed calculation step.",
        )
        return AuthorityMissionOrchestrationRequest(
            plan_ref=request.plan_ref,
            mission_ref=request.mission_ref,
            run_ref=request.run_ref,
            steps=[
                AuthorityMissionOrchestrationStepInput(
                    definition=definition,
                    request=dispatch,
                )
            ],
            safe_summary="Execute one bounded sealed calculation mission.",
        )

    def _require_exact_mission_lease(
        self,
        request: SealedCalculationMissionRequest,
        action_resources: list[str],
    ) -> None:
        lease = next(
            (
                item
                for item in self.orchestrator.runner.dispatcher.lease_store.list_leases(
                    active_only=False
                )
                if item.lease_ref == request.lease_ref
            ),
            None,
        )
        resource_constraint = (
            next(
                (
                    constraint
                    for constraint in lease.authority_constraints
                    if constraint.kind == AuthorityConstraintKind.resource_refs.value
                ),
                None,
            )
            if lease is not None
            else None
        )
        if (
            lease is None
            or lease.scope != "mission"
            or lease.mission_ref != request.mission_ref
            or resource_constraint is None
            or set(resource_constraint.allowed_refs) != set(action_resources)
        ):
            raise ValueError("SEALED_CALCULATION_EXACT_MISSION_LEASE_REQUIRED")

    def _action_resource_refs(
        self,
        request: SealedCalculationMissionRequest,
    ) -> list[str]:
        attestation = self.adapter._backend.attestation  # noqa: SLF001
        return [
            SEALED_CALCULATION_CAPABILITY_REF,
            SEALED_CALCULATION_ADAPTER_REF,
            SEALED_CALCULATION_TARGET_REF,
            request.input_ref,
            f"expression-hash-ref:sha256:{request.expression_sha256}",
            SEALED_CALCULATION_GRAMMAR_POLICY_REF,
            attestation.attestation_ref,
            attestation.limits_ref,
            request.mission_ref,
        ]
