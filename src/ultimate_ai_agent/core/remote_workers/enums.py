from enum import Enum


class RemoteTransportKind(str, Enum):
    local = "local"
    mock = "mock"
    manual = "manual"
    tailnet_planned = "tailnet_planned"
    lan_planned = "lan_planned"


class RemoteTransportStatus(str, Enum):
    available = "available"
    disabled = "disabled"
    planned = "planned"
    not_configured = "not_configured"
    denied = "denied"


class RemoteNodeStatus(str, Enum):
    unknown = "unknown"
    local_only = "local_only"
    mock_available = "mock_available"
    planned = "planned"
    disabled = "disabled"
    denied = "denied"


class RemoteJobStatus(str, Enum):
    draft = "draft"
    dry_run_only = "dry_run_only"
    dispatch_blocked = "dispatch_blocked"
    validation_failed = "validation_failed"
    simulated_result = "simulated_result"
    denied = "denied"


class RemoteOutputTrustLevel(str, Enum):
    untrusted_remote_output = "untrusted_remote_output"
    model_output = "model_output"
    local_mock_output = "local_mock_output"


class RemoteRiskLevel(str, Enum):
    safe = "safe"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    forbidden = "forbidden"

