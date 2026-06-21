from typing import Any
from ultimate_ai_agent.core.capabilities.catalog import render_compact_catalog
from ultimate_ai_agent.core.capabilities.context import NotesStore, SimpleNotesStore
from ultimate_ai_agent.core.capabilities.coordinator import Coordinator, PolicyDeniedError
from ultimate_ai_agent.core.capabilities.approval import CapabilityApprovalGrant, LocalApprovalAuthority
from ultimate_ai_agent.core.capabilities.decorators import as_registration, capability, get_capability_spec, tool_capability
from ultimate_ai_agent.core.capabilities.defaults import (
    BLOCKED_FOUNDATION_CAPABILITY_NAMES,
    capability_is_foundation_blocked,
    default_foundation_capability_registry,
    foundation_blocked_capability_specs,
)
from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityHealthStatus,
    CapabilityKind,
    CoordinationMode,
    PolicyDecisionStatus,
    RiskLevel as CoordinationRiskLevel,
    SideEffectLevel,
    TaskNodeStatus,
)
from ultimate_ai_agent.core.capabilities.models import (
    Artifact,
    CapabilityCatalogEntry,
    CapabilityHealthReport,
    CapabilityManifest,
    CapabilityPack,
    CapabilityPolicy,
    CapabilityRegistration,
    CapabilityResult,
    CapabilityRunContext,
    CapabilitySearchFilters,
    CapabilitySelection,
    CapabilitySpec,
    ContextPolicy,
    PolicyDecision,
    QualitySignals,
    RiskLevel,
    RuntimePolicy,
    SafetyPolicy,
    TaskEnvelope,
    TaskNode,
    TaskPlan,
    TelemetryEvent,
)
from ultimate_ai_agent.core.capabilities.observability import (
    CapabilityEvent,
    CapabilityEventSink,
    LoggerCapabilityEventSink,
    NoopCapabilityEventSink,
)
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.capabilities.registry import CapabilityRegistry
from ultimate_ai_agent.core.capabilities.selection import DeterministicSelector, LLMSelector, select_capabilities
from ultimate_ai_agent.core.capabilities.state import FileCoordinatorStateStore, InMemoryCoordinatorStateStore
from ultimate_ai_agent.core.capabilities.telemetry import InMemoryTelemetrySink, NoOpTelemetrySink, TelemetrySink

__all__ = [
    "AgentAdapter",
    "Artifact",
    "CallableCapabilityAdapter",
    "CapabilityAdapter",
    "CapabilityApprovalGrant",
    "CapabilityCatalogEntry",
    "CapabilityEvent",
    "CapabilityEventSink",
    "CapabilityHealthReport",
    "CapabilityHealthStatus",
    "CapabilityKind",
    "CapabilityManifest",
    "CapabilityPack",
    "CapabilityPolicy",
    "CapabilityRegistration",
    "CapabilityRegistry",
    "CapabilityResult",
    "CapabilityRunContext",
    "CapabilitySearchFilters",
    "CapabilitySelection",
    "CapabilitySpec",
    "ContextPolicy",
    "CoordinationMode",
    "CoordinationRiskLevel",
    "Coordinator",
    "DeterministicSelector",
    "HandoffAdapter",
    "HumanGateAdapter",
    "FileCoordinatorStateStore",
    "InMemoryTelemetrySink",
    "InMemoryCoordinatorStateStore",
    "LLMSelector",
    "LocalApprovalAuthority",
    "LoggerCapabilityEventSink",
    "NoOpTelemetrySink",
    "NoopCapabilityEventSink",
    "NotesStore",
    "PolicyDecision",
    "PolicyDecisionStatus",
    "PolicyDeniedError",
    "PolicyEngine",
    "QualitySignals",
    "ReviewerAdapter",
    "RiskLevel",
    "RuntimePolicy",
    "SafetyPolicy",
    "SideEffectLevel",
    "SimpleNotesStore",
    "TaskEnvelope",
    "TaskNode",
    "TaskNodeStatus",
    "TaskPlan",
    "TelemetryEvent",
    "TelemetrySink",
    "ToolAdapter",
    "WorkflowAdapter",
    "BLOCKED_FOUNDATION_CAPABILITY_NAMES",
    "as_registration",
    "capability_is_foundation_blocked",
    "capability",
    "default_foundation_capability_registry",
    "foundation_blocked_capability_specs",
    "get_capability_spec",
    "render_compact_catalog",
    "select_capabilities",
    "tool_capability",
    "wrap_agent",
    "wrap_tool",
]

_ADAPTER_EXPORTS = {
    "AgentAdapter",
    "CallableCapabilityAdapter",
    "CapabilityAdapter",
    "HandoffAdapter",
    "HumanGateAdapter",
    "ReviewerAdapter",
    "ToolAdapter",
    "WorkflowAdapter",
    "wrap_agent",
    "wrap_tool",
}

def __getattr__(name: str) -> Any:
    if name in _ADAPTER_EXPORTS:
        from ultimate_ai_agent.core.capabilities import adapters

        value = getattr(adapters, name)
        globals()[name] = value
        return value
    raise AttributeError(name)
