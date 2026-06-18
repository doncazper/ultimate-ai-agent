from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.approvals import ApprovalGrant, ApprovalRequest, LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import ApprovalRiskLevel, ApprovalSubjectType
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.task_decomposition.contracts import (
    CapabilityCallContext,
    CapabilityContract,
    DAGExecutionResult,
    PlanValidationContext,
    PlanValidationResult,
    TaskIntent,
    TaskPlan,
)
from ultimate_ai_agent.core.task_decomposition.decomposer import TaskDecomposer
from ultimate_ai_agent.core.task_decomposition.examples import (
    echo_summary_handler,
    validation_workflow_handler,
)
from ultimate_ai_agent.core.task_decomposition.executor import DAGExecutor
from ultimate_ai_agent.core.task_decomposition.learning import ReflectionStore
from ultimate_ai_agent.core.task_decomposition.registry import CapabilityRegistry
from ultimate_ai_agent.core.task_decomposition.validator import PlanValidator


DEFAULT_REGISTRY_PATH = ".uaa/task_decomposition_registry.json"

SAFE_HANDLER_REFS = {
    "example.echo_summary_handler": echo_summary_handler,
    "example.validation_workflow_handler": validation_workflow_handler,
}


class CapabilityRegistryStoreConfig(BaseModel):
    registry_path: str = DEFAULT_REGISTRY_PATH
    create_if_missing: bool = True

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionRegisterRequest(BaseModel):
    contract: CapabilityContract
    handler_ref: Optional[str] = None
    persist: bool = True

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionRequest(BaseModel):
    raw_request: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class TaskPlanValidationRequest(BaseModel):
    plan: TaskPlan
    context: PlanValidationContext = Field(default_factory=PlanValidationContext)

    model_config = ConfigDict(extra="forbid")


class TaskPlanExecutionRequest(BaseModel):
    plan: TaskPlan
    call_context: CapabilityCallContext = Field(default_factory=CapabilityCallContext)
    approval_grants: list[dict[str, Any]] = Field(default_factory=list)
    persist_reflections: bool = True

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionRunRequest(BaseModel):
    raw_request: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    call_context: CapabilityCallContext = Field(default_factory=CapabilityCallContext)
    approval_grants: list[dict[str, Any]] = Field(default_factory=list)
    persist_reflections: bool = True

    model_config = ConfigDict(extra="forbid")


class TaskCapabilityApprovalRequestPayload(BaseModel):
    capability_id: str = Field(..., min_length=1)
    run_id: str = "task-decomposition-run:local"
    actor_id: str = "local_actor"

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionRunResult(BaseModel):
    intent: TaskIntent
    plan: TaskPlan
    validation: PlanValidationResult
    execution: Optional[DAGExecutionResult] = None

    model_config = ConfigDict(extra="forbid")


class CapabilityRegistryStore:
    def __init__(self, config: CapabilityRegistryStoreConfig | None = None):
        self.config = config or CapabilityRegistryStoreConfig()

    @property
    def path(self) -> Path:
        return Path(self.config.registry_path)

    def load(self) -> CapabilityRegistry:
        registry = CapabilityRegistry()
        if not self.path.exists():
            if not self.config.create_if_missing:
                raise FileNotFoundError(str(self.path))
            return registry
        registry.import_json(self.path.read_text(encoding="utf-8"))
        self._attach_safe_handlers(registry)
        return registry

    def save(self, registry: CapabilityRegistry) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(registry.export_json(indent=2), encoding="utf-8")

    def ensure_example_registry(self) -> CapabilityRegistry:
        registry = self.load()
        from ultimate_ai_agent.core.task_decomposition.examples import (
            build_echo_tool_capability,
            build_validation_workflow_capability,
        )

        if registry.get("capability:example-echo-summary") is None:
            registry.register(build_echo_tool_capability(), echo_summary_handler)
        if registry.get("capability:example-validation-workflow") is None:
            registry.register(build_validation_workflow_capability(), validation_workflow_handler)
        self.save(registry)
        return registry

    def _attach_safe_handlers(self, registry: CapabilityRegistry) -> None:
        for card in registry.cards():
            contract = registry.get(card.id)
            if contract and contract.handler_ref in SAFE_HANDLER_REFS:
                registry.register_handler(card.id, SAFE_HANDLER_REFS[contract.handler_ref])


class TaskDecompositionService:
    def __init__(
        self,
        registry_store: CapabilityRegistryStore | None = None,
        registry: CapabilityRegistry | None = None,
        reflection_store: ReflectionStore | None = None,
        approval_authority: LocalApprovalAuthority | None = None,
    ):
        self.registry_store = registry_store or CapabilityRegistryStore()
        self.registry = registry or self.registry_store.load()
        self.approval_authority = approval_authority or LocalApprovalAuthority()
        self.registry.approval_authority = self.approval_authority
        self.reflection_store = reflection_store or ReflectionStore()
        self.validator = PlanValidator()

    @classmethod
    def from_env(cls) -> "TaskDecompositionService":
        path = os.environ.get("UAA_TASK_DECOMPOSITION_REGISTRY", DEFAULT_REGISTRY_PATH)
        return cls(registry_store=CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=path)))

    def catalog(self) -> list[dict[str, Any]]:
        return [card.model_dump(mode="json") for card in self.registry.cards()]

    def register(self, request: TaskDecompositionRegisterRequest) -> CapabilityContract:
        handler = SAFE_HANDLER_REFS.get(request.handler_ref or request.contract.handler_ref or "")
        contract = self.registry.register(request.contract, handler)
        if request.persist:
            self.registry_store.save(self.registry)
        return contract

    def ensure_examples(self) -> list[dict[str, Any]]:
        self.registry = self.registry_store.ensure_example_registry()
        return self.catalog()

    def classify(self, request: TaskDecompositionRequest) -> TaskIntent:
        return TaskDecomposer(self.registry).classify_intent(request.raw_request, request.context)

    def decompose(self, request: TaskDecompositionRequest) -> TaskDecompositionRunResult:
        decomposer = TaskDecomposer(self.registry, self.validator)
        intent = decomposer.classify_intent(request.raw_request, request.context)
        candidates = decomposer.retrieve_capabilities(intent)
        strategy = decomposer.select_strategy(intent, candidates)
        plan = decomposer.create_plan(intent, candidates, strategy)
        validation = decomposer.validate_plan(plan)
        return TaskDecompositionRunResult(intent=intent, plan=plan, validation=validation)

    def validate_plan(self, request: TaskPlanValidationRequest) -> PlanValidationResult:
        return self.validator.validate(request.plan, self.registry, request.context)

    def build_approval_request(self, request: TaskCapabilityApprovalRequestPayload) -> ApprovalRequest:
        contract = self.registry.get(request.capability_id)
        if contract is None:
            raise KeyError("CAPABILITY_NOT_REGISTERED")
        return ApprovalRequest(
            approval_request_id=f"areq_{request.run_id}_{request.capability_id}".replace(":", "_"),
            run_id=request.run_id,
            subject_type=ApprovalSubjectType.tool_request,
            subject_id=request.capability_id,
            actor_context=ActorContext(
                actor_type=ActorType.orchestrator,
                actor_id=request.actor_id,
                authority_source=AuthoritySource.explicit_user_request,
            ),
            requested_action="invoke_capability",
            purpose=f"Approve local task decomposition capability {request.capability_id}.",
            risk_level=ApprovalRiskLevel(contract.card.risk_level.value),
            data_classification=self._data_classification(contract.data_sensitivity.value),
            resource_refs=[request.capability_id],
            tool_id=request.capability_id,
        )

    async def execute_plan(self, request: TaskPlanExecutionRequest) -> DAGExecutionResult:
        self._load_approval_grants(request.approval_grants)
        self.registry.approval_authority = self.approval_authority
        call_context = request.call_context
        result = await DAGExecutor(self.registry, self.validator).execute(request.plan, call_context)
        if request.persist_reflections:
            self.reflection_store.record_execution(request.plan, result)
        return result

    def execute_plan_sync(self, request: TaskPlanExecutionRequest) -> DAGExecutionResult:
        return asyncio.run(self.execute_plan(request))

    async def run(self, request: TaskDecompositionRunRequest) -> TaskDecompositionRunResult:
        decomposed = self.decompose(TaskDecompositionRequest(raw_request=request.raw_request, context=request.context))
        if not decomposed.validation.valid:
            return decomposed
        execution = await self.execute_plan(
            TaskPlanExecutionRequest(
                plan=decomposed.plan,
                call_context=request.call_context,
                approval_grants=request.approval_grants,
                persist_reflections=request.persist_reflections,
            )
        )
        return decomposed.model_copy(update={"execution": execution})

    def run_sync(self, request: TaskDecompositionRunRequest) -> TaskDecompositionRunResult:
        return asyncio.run(self.run(request))

    def _load_approval_grants(self, grants: list[dict[str, Any]]) -> None:
        for item in grants:
            self.approval_authority.load_grant_for_validation(ApprovalGrant.model_validate(item))

    def _data_classification(self, sensitivity: str) -> DataClassification:
        mapping = {
            "public": ClassificationValue.public,
            "internal": ClassificationValue.system_internal,
            "private": ClassificationValue.project_private,
            "secret": ClassificationValue.credential_secret,
        }
        return DataClassification(
            classification=mapping.get(sensitivity, ClassificationValue.project_private),
            source="task_decomposition_capability",
            requires_consent=sensitivity in {"private", "secret"},
        )


def dump_json(data: Any) -> str:
    if isinstance(data, BaseModel):
        payload = data.model_dump(mode="json")
    else:
        payload = data
    return json.dumps(payload, indent=2, sort_keys=True)
