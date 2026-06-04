from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.enums import (
    PlanInputTrustLevel,
    TaskDependencyKind,
    TaskPlanAuthorityLevel,
    TaskPlanDecisionStatus,
    TaskPlanningStatus,
    TaskRiskLevel,
    TaskStepKind,
)
from ultimate_ai_agent.core.planning.validation import (
    input_trust_reasons,
    raw_input_reasons,
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)


class TaskGoal(BaseModel):
    goal_id: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    source_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_goal(self):
        validate_task_ref(self.goal_id, "goal_id")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        for ref in self.source_refs:
            validate_task_ref(ref, "source_ref")
        validate_safe_task_payload(self.metadata, "metadata")
        return self


class TaskStepInputBoundary(BaseModel):
    input_refs: List[str] = Field(default_factory=list)
    input_trust_level: PlanInputTrustLevel = PlanInputTrustLevel.safe_reference
    contains_raw_prompt: bool = False
    contains_raw_model_output: bool = False
    contains_raw_file_content: bool = False
    contains_raw_transcript: bool = False
    contains_secret_like_content: bool = False
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_input_boundary(self):
        for ref in [*self.input_refs, *self.metadata_refs]:
            validate_task_ref(ref, "input_ref")
        for reason in raw_input_reasons(self):
            raise ValueError(reason)
        validate_safe_task_payload(self.metadata, "metadata")
        return self


class TaskStep(BaseModel):
    step_id: str = Field(..., min_length=1)
    step_kind: TaskStepKind
    safe_summary: str = Field(..., min_length=1)
    input_boundary: TaskStepInputBoundary = Field(default_factory=TaskStepInputBoundary)
    depends_on: List[str] = Field(default_factory=list)
    declared_risk_level: TaskRiskLevel = TaskRiskLevel.low
    authority_level: TaskPlanAuthorityLevel = TaskPlanAuthorityLevel.review_plan_only
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_step(self):
        validate_task_ref(self.step_id, "step_id")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        for ref in [*self.depends_on, *self.metadata_refs]:
            validate_task_ref(ref, "step_ref")
        validate_safe_task_payload(self.metadata, "metadata")
        return self


class TaskDependency(BaseModel):
    dependency_id: str = Field(..., min_length=1)
    before_step_id: str = Field(..., min_length=1)
    after_step_id: str = Field(..., min_length=1)
    dependency_kind: TaskDependencyKind = TaskDependencyKind.before_after
    safe_summary: str = "Step ordering dependency."

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_dependency(self):
        validate_task_ref(self.dependency_id, "dependency_id")
        validate_task_ref(self.before_step_id, "before_step_id")
        validate_task_ref(self.after_step_id, "after_step_id")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        return self


class TaskConstraint(BaseModel):
    constraint_id: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    metadata_refs: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_constraint(self):
        validate_task_ref(self.constraint_id, "constraint_id")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        for ref in self.metadata_refs:
            validate_task_ref(ref, "metadata_ref")
        return self


class TaskPlan(BaseModel):
    plan_id: str = Field(..., min_length=1)
    goal: TaskGoal
    steps: List[TaskStep] = Field(..., min_length=1)
    dependencies: List[TaskDependency] = Field(default_factory=list)
    constraints: List[TaskConstraint] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    approval_ref: Optional[str] = None
    authority_level: TaskPlanAuthorityLevel = TaskPlanAuthorityLevel.review_plan_only
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_plan(self):
        validate_task_ref(self.plan_id, "plan_id")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        if self.approval_ref:
            validate_safe_task_text(self.approval_ref, "approval_ref")
        for ref in self.metadata_refs:
            validate_task_ref(ref, "metadata_ref")
        validate_safe_task_payload(self.metadata, "metadata")
        return self


class TaskPlanningRequest(BaseModel):
    plan: TaskPlan
    execution_requested: bool = False
    auto_run_requested: bool = False
    schedule_requested: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self):
        validate_safe_task_payload(self.metadata, "metadata")
        return self


class TaskPlanReceiptPlan(BaseModel):
    receipt_plan_ref: str = Field(..., min_length=1)
    plan_id: str = Field(..., min_length=1)
    decision_id: str = Field(..., min_length=1)
    authority_level: TaskPlanAuthorityLevel = TaskPlanAuthorityLevel.non_authoritative
    execution_authorized: bool = False
    execution_performed: bool = False
    scheduler_registered: bool = False
    raw_content_stored: bool = False
    memory_write_performed: bool = False
    file_mutation_performed: bool = False
    network_call_performed: bool = False
    tool_execution_performed: bool = False
    action_execution_performed: bool = False
    safe_summary: str = "Non-authoritative task planning receipt plan."
    metadata_refs: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self):
        if self.execution_authorized:
            raise ValueError("M29 receipt plans must not authorize execution")
        if self.execution_performed:
            raise ValueError("M29 receipt plans must not perform execution")
        if self.scheduler_registered:
            raise ValueError("M29 receipt plans must not register schedules")
        if self.raw_content_stored:
            raise ValueError("M29 receipt plans must not store raw content")
        if self.memory_write_performed:
            raise ValueError("M29 receipt plans must not write memory")
        if self.file_mutation_performed:
            raise ValueError("M29 receipt plans must not mutate files")
        if self.network_call_performed:
            raise ValueError("M29 receipt plans must not call networks")
        if self.tool_execution_performed:
            raise ValueError("M29 receipt plans must not execute tools")
        if self.action_execution_performed:
            raise ValueError("M29 receipt plans must not execute actions")
        validate_task_ref(self.receipt_plan_ref, "receipt_plan_ref")
        validate_task_ref(self.plan_id, "plan_id")
        validate_task_ref(self.decision_id, "decision_id")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        for ref in self.metadata_refs:
            validate_task_ref(ref, "metadata_ref")
        return self


class TaskPlanDecision(BaseModel):
    decision_id: str = Field(..., min_length=1)
    plan_id: str = Field(..., min_length=1)
    status: TaskPlanDecisionStatus
    valid_for_review: bool = False
    execution_authorized: bool = False
    execution_performed: bool = False
    scheduler_registered: bool = False
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    receipt_plan: Optional[TaskPlanReceiptPlan] = None
    no_tool_execution_performed: bool = True
    no_action_execution_performed: bool = True
    no_memory_write_performed: bool = True
    no_file_mutation_performed: bool = True
    no_network_call_performed: bool = True
    no_model_call_performed: bool = True
    no_event_ledger_mutation_performed: bool = True
    no_scheduler_registered: bool = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_decision(self):
        if self.execution_authorized:
            raise ValueError("M29 task plan decisions must not authorize execution")
        if self.execution_performed:
            raise ValueError("M29 task plan decisions must not perform execution")
        if self.scheduler_registered:
            raise ValueError("M29 task plan decisions must not register schedules")
        for field_name in [
            "no_tool_execution_performed",
            "no_action_execution_performed",
            "no_memory_write_performed",
            "no_file_mutation_performed",
            "no_network_call_performed",
            "no_model_call_performed",
            "no_event_ledger_mutation_performed",
            "no_scheduler_registered",
        ]:
            if not getattr(self, field_name):
                raise ValueError(f"M29 task plan decision invariant failed: {field_name}")
        validate_task_ref(self.decision_id, "decision_id")
        validate_task_ref(self.plan_id, "plan_id")
        validate_safe_task_text(self.safe_message, "safe_message")
        return self


class TaskPlanningManifest(BaseModel):
    baseline_version: str = "0.33.0"
    contract_version: str = "m29-agent-task-planning-engine"
    status: TaskPlanningStatus = TaskPlanningStatus.planning_only
    planning_enabled: bool = True
    task_execution_enabled: bool = False
    auto_run_enabled: bool = False
    scheduler_enabled: bool = False
    tool_execution_enabled: bool = False
    action_execution_enabled: bool = False
    file_mutation_enabled: bool = False
    memory_write_enabled: bool = False
    network_call_enabled: bool = False
    model_provider_call_enabled: bool = False
    browser_automation_enabled: bool = False
    mobile_device_access_enabled: bool = False
    remote_execution_enabled: bool = False
    plugin_enablement_enabled: bool = False
    backend_task_routes_added: bool = False
    control_center_execute_controls_enabled: bool = False
    context_injection_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_manifest(self):
        blocked_true_fields = [
            "task_execution_enabled",
            "auto_run_enabled",
            "scheduler_enabled",
            "tool_execution_enabled",
            "action_execution_enabled",
            "file_mutation_enabled",
            "memory_write_enabled",
            "network_call_enabled",
            "model_provider_call_enabled",
            "browser_automation_enabled",
            "mobile_device_access_enabled",
            "remote_execution_enabled",
            "plugin_enablement_enabled",
            "backend_task_routes_added",
            "control_center_execute_controls_enabled",
            "context_injection_enabled",
            "production_authority_enabled",
        ]
        for field_name in blocked_true_fields:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must be False in M29")
        return self


def boundary_reason_codes(boundary: TaskStepInputBoundary) -> list[str]:
    reasons = raw_input_reasons(boundary)
    for ref in [*getattr(boundary, "input_refs", []), *getattr(boundary, "metadata_refs", [])]:
        reasons.extend(input_trust_reasons(ref, boundary.input_trust_level))
    return list(dict.fromkeys(reasons))
