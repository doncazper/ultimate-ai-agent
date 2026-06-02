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


class LocalModelRuntimeKind(str, Enum):
    ollama_planned = "ollama_planned"
    llama_cpp_planned = "llama_cpp_planned"
    mlx_planned = "mlx_planned"
    vllm_planned = "vllm_planned"
    lm_studio_planned = "lm_studio_planned"
    openai_compatible_local_planned = "openai_compatible_local_planned"
    generic_loopback_http_planned = "generic_loopback_http_planned"


class LocalModelRuntimeStatus(str, Enum):
    contract_only = "contract_only"
    planned_disabled = "planned_disabled"
    blocked = "blocked"
    future_requires_review = "future_requires_review"
    not_implemented = "not_implemented"


class LocalModelRuntimeTransportKind(str, Enum):
    none = "none"
    loopback_http_metadata = "loopback_http_metadata"
    local_named_endpoint_metadata = "local_named_endpoint_metadata"


class LocalModelRuntimeActivationStatus(str, Enum):
    contract_valid = "contract_valid"
    denied = "denied"
    blocked = "blocked"
    requires_m23 = "requires_m23"
    not_implemented = "not_implemented"


class LocalModelRuntimeTrustLevel(str, Enum):
    untrusted = "untrusted"
    local_metadata_only = "local_metadata_only"
    future_review_required = "future_review_required"


class LocalModelRuntimeRiskLevel(str, Enum):
    safe_metadata = "safe_metadata"
    low = "low"
    medium = "medium"
    high = "high"
    forbidden = "forbidden"
