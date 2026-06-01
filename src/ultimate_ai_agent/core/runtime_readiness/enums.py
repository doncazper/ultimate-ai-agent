from enum import Enum


class RuntimeReadinessStatus(str, Enum):
    ready_for_manual_smoke = "ready_for_manual_smoke"
    ready_for_simulated_only = "ready_for_simulated_only"
    blocked = "blocked"
    planned = "planned"
    disabled = "disabled"
    failed = "failed"


class RuntimeCapabilityStatus(str, Enum):
    supported = "supported"
    simulated_only = "simulated_only"
    manual_only = "manual_only"
    dry_run_only = "dry_run_only"
    planned_disabled = "planned_disabled"
    blocked = "blocked"


class RuntimeSurface(str, Enum):
    simulated_model_runtime = "simulated_model_runtime"
    local_loopback_policy = "local_loopback_policy"
    manual_loopback_smoke = "manual_loopback_smoke"
    remote_worker_foundation = "remote_worker_foundation"
    private_mesh_planned = "private_mesh_planned"
    tailnet_planned = "tailnet_planned"
    headscale_planned = "headscale_planned"
    generic_wireguard_planned = "generic_wireguard_planned"
    tailscale_planned = "tailscale_planned"
    model_router = "model_router"
    cost_governor = "cost_governor"
    approval_authority = "approval_authority"
    api_boundary = "api_boundary"
    foundation_gate = "foundation_gate"
    mobile_companion_planned = "mobile_companion_planned"
    device_capability_broker_planned = "device_capability_broker_planned"
    codex_plugin_governance = "codex_plugin_governance"
    cloud_provider_runtime = "cloud_provider_runtime"


class SmokeReportStatus(str, Enum):
    valid = "valid"
    invalid = "invalid"
    accepted = "accepted"
    rejected = "rejected"
    redacted = "redacted"
    blocked = "blocked"


class RuntimeRiskClass(str, Enum):
    safe = "safe"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    forbidden = "forbidden"
