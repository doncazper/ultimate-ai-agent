from enum import Enum


class CapabilityKind(str, Enum):
    tool = "tool"
    agent = "agent"
    workflow = "workflow"
    handoff = "handoff"
    reviewer = "reviewer"
    human_gate = "human_gate"
    mcp_tool = "mcp_tool"
    a2a_agent = "a2a_agent"
    deterministic = "deterministic"


class SideEffectLevel(str, Enum):
    none = "none"
    read = "read"
    write = "write"
    external = "external"
    destructive = "destructive"


class CapabilityAuthorityLevel(str, Enum):
    metadata_only = "metadata_only"
    read_only = "read_only"
    mutating = "mutating"
    external = "external"
    destructive = "destructive"


class CapabilityPrivacyLevel(str, Enum):
    public = "public"
    local_private = "local_private"
    sensitive = "sensitive"
    secret_ref_only = "secret_ref_only"


class CapabilityLatencyClass(str, Enum):
    unknown = "unknown"
    interactive = "interactive"
    background = "background"
    long_running = "long_running"


class CapabilityCostClass(str, Enum):
    unknown = "unknown"
    none = "none"
    low = "low"
    metered = "metered"
    high = "high"


class RiskLevel(str, Enum):
    safe = "safe"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    forbidden = "forbidden"


class CoordinationMode(str, Enum):
    direct_tool = "direct_tool"
    agent_as_tool = "agent_as_tool"
    handoff = "handoff"
    workflow_node = "workflow_node"
    parallel_read_fanout = "parallel_read_fanout"
    reviewer = "reviewer"
    human_gate = "human_gate"


class CapabilityHealthStatus(str, Enum):
    healthy = "healthy"
    degraded = "degraded"
    unhealthy = "unhealthy"
    unknown = "unknown"


class TaskNodeStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    denied = "denied"
    failed = "failed"
    approval_required = "approval_required"


class PolicyDecisionStatus(str, Enum):
    allowed = "allowed"
    denied = "denied"
    approval_required = "approval_required"
    degraded = "degraded"
