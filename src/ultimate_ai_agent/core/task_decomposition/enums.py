from enum import Enum


class CapabilityKind(str, Enum):
    tool = "tool"
    skill = "skill"
    agent = "agent"
    workflow = "workflow"
    mcp_tool = "mcp_tool"
    knowledge_source = "knowledge_source"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class CostHint(str, Enum):
    free = "free"
    low = "low"
    medium = "medium"
    high = "high"


class DataSensitivity(str, Enum):
    public = "public"
    internal = "internal"
    private = "private"
    secret = "secret"


class ExecutionMode(str, Enum):
    python_callable = "python_callable"
    agent_as_tool = "agent_as_tool"
    handoff = "handoff"
    workflow = "workflow"
    mcp = "mcp"
    shell = "shell"
    external_api = "external_api"


class AmbiguityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ComplexityLevel(str, Enum):
    simple = "simple"
    moderate = "moderate"
    complex = "complex"
    long_horizon = "long_horizon"


class PlanStrategy(str, Enum):
    direct = "direct"
    linear_plan = "linear_plan"
    dag_plan = "dag_plan"
    react_loop = "react_loop"
    tree_search = "tree_search"
    skill_reuse = "skill_reuse"
    human_in_loop = "human_in_loop"


class TaskNodeStrategy(str, Enum):
    direct = "direct"
    react_loop = "react_loop"
    linear = "linear"
    parallel_child = "parallel_child"
    human_approval = "human_approval"
    evaluate = "evaluate"
    repair = "repair"


class PlanValidationStatus(str, Enum):
    valid = "valid"
    invalid = "invalid"
    approval_required = "approval_required"


class NodeExecutionStatus(str, Enum):
    pending = "pending"
    ready = "ready"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"
    awaiting_approval = "awaiting_approval"


class DAGExecutionStatus(str, Enum):
    succeeded = "succeeded"
    failed = "failed"
    awaiting_approval = "awaiting_approval"
    validation_failed = "validation_failed"


class CapabilityCallStatus(str, Enum):
    succeeded = "succeeded"
    failed = "failed"
    validation_failed = "validation_failed"
    approval_required = "approval_required"
    unavailable = "unavailable"


class CapabilityOutcomeStatus(str, Enum):
    succeeded = "succeeded"
    failed = "failed"
    validation_failed = "validation_failed"
    approval_required = "approval_required"
