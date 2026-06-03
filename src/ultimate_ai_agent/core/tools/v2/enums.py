from enum import Enum


class ToolExecutionMode(str, Enum):
    validate_only = "validate_only"
    preview_only = "preview_only"
    dry_run_plan = "dry_run_plan"
    execute = "execute"


class ToolRiskClass(str, Enum):
    safe = "safe"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    forbidden = "forbidden"


class ToolSideEffectKind(str, Enum):
    none = "none"
    file_read = "file_read"
    file_write = "file_write"
    file_delete = "file_delete"
    memory_read = "memory_read"
    memory_write = "memory_write"
    external_send = "external_send"
    network_call = "network_call"
    browser_action = "browser_action"
    plugin_enablement = "plugin_enablement"
    shell_execution = "shell_execution"
    model_call = "model_call"
    context_injection = "context_injection"
    remote_execution = "remote_execution"
    device_sensor_access = "device_sensor_access"


class ToolApprovalRequirement(str, Enum):
    not_required = "not_required"
    validated_local_approval_required = "validated_local_approval_required"
    future_runtime_approval_required = "future_runtime_approval_required"


class ToolIntentDecisionStatus(str, Enum):
    preview_allowed = "preview_allowed"
    denied = "denied"
    blocked_by_policy = "blocked_by_policy"
    future_milestone = "future_milestone"


class ToolAuthorityLevel(str, Enum):
    validation_only = "validation_only"
    preview_only = "preview_only"
    approval_ref_present = "approval_ref_present"
    execution_requested = "execution_requested"
    production_authority = "production_authority"


class ToolInputTrustLevel(str, Enum):
    trusted_system_refs = "trusted_system_refs"
    user_provided_refs = "user_provided_refs"
    context_pack_refs = "context_pack_refs"
    model_output = "model_output"
    runtime_output = "runtime_output"
    openwebui_output = "openwebui_output"
    unknown = "unknown"


class ToolTargetKind(str, Enum):
    none = "none"
    file_ref = "file_ref"
    memory_ref = "memory_ref"
    message_draft_ref = "message_draft_ref"
    api_route_ref = "api_route_ref"
    local_runtime_ref = "local_runtime_ref"
    browser_ref = "browser_ref"
    plugin_ref = "plugin_ref"
    remote_node_ref = "remote_node_ref"
    mobile_device_ref = "mobile_device_ref"
    context_pack_ref = "context_pack_ref"
    unknown = "unknown"
