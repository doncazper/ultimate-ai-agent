from enum import Enum


class ModelRuntimeKind(str, Enum):
    simulated = "simulated"
    local_stub = "local_stub"
    cloud_stub = "cloud_stub"
    openai_compatible_stub = "openai_compatible_stub"
    sdk_adapter_stub = "sdk_adapter_stub"


class ModelRuntimeRequestStatus(str, Enum):
    accepted = "accepted"
    denied = "denied"
    validation_failed = "validation_failed"
    simulated = "simulated"
    blocked_by_policy = "blocked_by_policy"
    blocked_by_secret_scan = "blocked_by_secret_scan"


class ModelRuntimeResponseStatus(str, Enum):
    simulated_success = "simulated_success"
    simulated_refusal = "simulated_refusal"
    simulated_error = "simulated_error"
    validation_failed = "validation_failed"
    local_loopback_success = "local_loopback_success"
    local_loopback_error = "local_loopback_error"


class ModelRuntimeSafetyMode(str, Enum):
    validate_only = "validate_only"
    dry_run = "dry_run"
    simulated = "simulated"
    local_loopback_dev = "local_loopback_dev"
    disabled = "disabled"


class ModelRuntimeOutputFormat(str, Enum):
    text = "text"
    json = "json"
    structured = "structured"
    tool_call_plan = "tool_call_plan"
    refusal = "refusal"
