from enum import Enum


class ToolRuntimeAdapterStatus(str, Enum):
    contract_only = "contract_only"
    noop_only = "noop_only"
    safe_metadata_only = "safe_metadata_only"
    redacted_preview_only = "redacted_preview_only"
    read_only_http_fetch_allowlisted = "read_only_http_fetch_allowlisted"
    validation_only = "validation_only"
    blocked = "blocked"
    future_tool_runtime_required = "future_tool_runtime_required"


class ToolRuntimeMode(str, Enum):
    noop_only = "noop_only"
    safe_metadata_only = "safe_metadata_only"
    redacted_preview_only = "redacted_preview_only"
    read_only_http_fetch_allowlisted = "read_only_http_fetch_allowlisted"
    dry_run_only = "dry_run_only"
    validation_only = "validation_only"
    blocked = "blocked"
    future_side_effecting_tools_required = "future_side_effecting_tools_required"


class ToolInvocationStatus(str, Enum):
    requested = "requested"
    denied = "denied"
    blocked = "blocked"
    noop_completed = "noop_completed"
    metadata_completed = "metadata_completed"
    preview_completed = "preview_completed"
    http_fetch_completed = "http_fetch_completed"
    failed_validation = "failed_validation"
    replay_detected = "replay_detected"
    future_tool_required = "future_tool_required"


class ToolInvocationKind(str, Enum):
    noop = "noop"
    filesystem_metadata = "filesystem_metadata"
    redacted_file_preview = "redacted_file_preview"
    read_only_http_fetch = "read_only_http_fetch"
    validation_only = "validation_only"
    portable_evidence_signing = "portable_evidence_signing"
    sealed_arithmetic = "sealed_arithmetic"
    matrix_harness = "matrix_harness"
    matrix_session = "matrix_session"
    matrix_sync = "matrix_sync"
    matrix_messaging = "matrix_messaging"
    matrix_rooms_media = "matrix_rooms_media"
    blocked_unknown = "blocked_unknown"
    blocked_effectful = "blocked_effectful"
    blocked_shell = "blocked_shell"
    blocked_file = "blocked_file"
    blocked_memory = "blocked_memory"
    blocked_network = "blocked_network"
    blocked_model = "blocked_model"
    blocked_browser = "blocked_browser"
    blocked_mobile = "blocked_mobile"
    blocked_remote = "blocked_remote"
    blocked_plugin = "blocked_plugin"


class ToolRuntimeCapability(str, Enum):
    noop = "noop"
    filesystem_metadata = "filesystem_metadata"
    redacted_file_preview = "redacted_file_preview"
    read_only_http_fetch_allowlisted = "read_only_http_fetch_allowlisted"
    deterministic_result = "deterministic_result"
    no_effect = "no_effect"
    metadata_only_filesystem = "metadata_only_filesystem"
    redacted_preview_only_filesystem = "redacted_preview_only_filesystem"
    no_memory_write = "no_memory_write"
    no_network = "no_network"
    no_unrestricted_network = "no_unrestricted_network"
    no_authenticated_network = "no_authenticated_network"
    no_model_call = "no_model_call"
    no_shell = "no_shell"
    no_browser = "no_browser"
    no_mobile = "no_mobile"
    no_remote = "no_remote"
    no_plugin = "no_plugin"


class ToolRuntimeBlockReason(str, Enum):
    unknown_tool = "unknown_tool"
    tool_not_allowlisted = "tool_not_allowlisted"
    effectful_tool_blocked = "effectful_tool_blocked"
    raw_content_denied = "raw_content_denied"
    secret_content_denied = "secret_content_denied"
    approval_ref_not_authority = "approval_ref_not_authority"
    approval_test_ref_denied = "approval_test_ref_denied"
    unsafe_input = "unsafe_input"
    replay_detected = "replay_detected"
    dynamic_dispatch_denied = "dynamic_dispatch_denied"
    dependency_unmet = "dependency_unmet"
    future_milestone_required = "future_milestone_required"


class ToolRuntimeAuthorityLevel(str, Enum):
    non_authoritative = "non_authoritative"
    noop_runtime_only = "noop_runtime_only"
    metadata_runtime_only = "metadata_runtime_only"
    blocked_authority = "blocked_authority"
