from importlib import import_module

from .contracts import (
    CAPABILITY_AVAILABILITY_CLI_REF,
    CAPABILITY_AVAILABILITY_READ_MODEL_SCHEMA_VERSION,
    CAPABILITY_AVAILABILITY_ROUTE_REF,
    CAPABILITY_AVAILABILITY_SCHEMA_VERSION,
    CAPABILITY_INVOCATION_DECISION_CONTRACT_REF,
    CAPABILITY_INVOCATION_DECISION_SCHEMA_VERSION,
    EXECUTION_RECEIPT_CONTRACT_REF,
    AuthorityPosture,
    CapabilityAvailabilityReadModel,
    CapabilityAvailabilitySnapshot,
    CapabilityInvocationDecision,
    CapabilityInvocationRequest,
    CatalogStatus,
    CompatibilityStatus,
    ConfigurationStatus,
    CostPosture,
    DerivedRuntimeReadinessStatus,
    FreshnessStatus,
    HealthStatus,
    IdempotencyPosture,
    InvocationDecisionCachePosture,
    InvocationDecisionOutcome,
    ResourceBudgetStatus,
    RuntimeReadinessDerivation,
    SafeDisableStatus,
    WebHybridAvailabilityReadModel,
    WebHybridCapabilityLanePosture,
    WebResearchAggregationPosture,
    build_capability_availability_snapshot,
    derive_runtime_readiness,
    evaluate_capability_invocation,
)

_LAZY_EXPORT_MODULES = {
    "build_capability_availability_read_model": ".read_model",
    "build_web_hybrid_availability_read_model": ".read_model",
    "snapshot_from_capability_catalog_entry": ".adapters",
    "snapshot_from_capability_manifest": ".adapters",
    "snapshot_from_extension_catalog_entry": ".adapters",
    "snapshot_from_provider_manifest": ".adapters",
}


def __getattr__(name: str):
    """Load provider-backed adapters only when their public export is requested."""

    module_name = _LAZY_EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value

__all__ = [
    "CAPABILITY_AVAILABILITY_CLI_REF",
    "CAPABILITY_AVAILABILITY_READ_MODEL_SCHEMA_VERSION",
    "CAPABILITY_AVAILABILITY_ROUTE_REF",
    "CAPABILITY_AVAILABILITY_SCHEMA_VERSION",
    "CAPABILITY_INVOCATION_DECISION_CONTRACT_REF",
    "CAPABILITY_INVOCATION_DECISION_SCHEMA_VERSION",
    "EXECUTION_RECEIPT_CONTRACT_REF",
    "AuthorityPosture",
    "CapabilityAvailabilityReadModel",
    "CapabilityAvailabilitySnapshot",
    "CapabilityInvocationDecision",
    "CapabilityInvocationRequest",
    "CatalogStatus",
    "CompatibilityStatus",
    "ConfigurationStatus",
    "CostPosture",
    "DerivedRuntimeReadinessStatus",
    "FreshnessStatus",
    "HealthStatus",
    "IdempotencyPosture",
    "InvocationDecisionCachePosture",
    "InvocationDecisionOutcome",
    "ResourceBudgetStatus",
    "RuntimeReadinessDerivation",
    "SafeDisableStatus",
    "WebHybridAvailabilityReadModel",
    "WebHybridCapabilityLanePosture",
    "WebResearchAggregationPosture",
    "build_capability_availability_read_model",
    "build_capability_availability_snapshot",
    "build_web_hybrid_availability_read_model",
    "derive_runtime_readiness",
    "evaluate_capability_invocation",
    "snapshot_from_capability_catalog_entry",
    "snapshot_from_capability_manifest",
    "snapshot_from_extension_catalog_entry",
    "snapshot_from_provider_manifest",
]
