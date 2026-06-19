from enum import Enum


class ModelProviderKind(str, Enum):
    local_runtime = "local_runtime"
    cloud_provider = "cloud_provider"
    openai_compatible = "openai_compatible"
    self_hosted = "self_hosted"
    sdk_adapter_placeholder = "sdk_adapter_placeholder"


class ModelTaskCapability(str, Enum):
    chat = "chat"
    reasoning = "reasoning"
    coding = "coding"
    summarization = "summarization"
    classification = "classification"
    extraction = "extraction"
    tool_calling = "tool_calling"
    structured_output = "structured_output"
    vision = "vision"
    embeddings = "embeddings"
    reranking = "reranking"
    long_context = "long_context"
    low_latency = "low_latency"


class ModelRouteCostMode(str, Enum):
    cheap = "cheap"
    balanced = "balanced"
    premium = "premium"
    critical = "critical"
    local_private = "local_private"


class ModelPrivacyClass(str, Enum):
    local_only = "local_only"
    private_allowed = "private_allowed"
    project_allowed = "project_allowed"
    cloud_allowed = "cloud_allowed"
    restricted = "restricted"


class ModelRouteStatus(str, Enum):
    selected = "selected"
    denied = "denied"
    no_candidate = "no_candidate"
    approval_required = "approval_required"
    budget_exceeded = "budget_exceeded"
    privacy_blocked = "privacy_blocked"
    capability_missing = "capability_missing"
    context_too_small = "context_too_small"


class ModelRiskClass(str, Enum):
    safe = "safe"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
