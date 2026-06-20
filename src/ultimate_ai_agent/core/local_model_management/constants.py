from __future__ import annotations

import re


LOCAL_MODEL_MANAGEMENT_DOCS = [
    "docs/model_management/LOCAL_MODEL_MANAGEMENT_CHARTER.md",
    "docs/model_management/LOCAL_MODEL_MANAGEMENT_AUTHORITY_BOUNDARY.md",
    "docs/model_management/LOCAL_MODEL_MANAGEMENT_NON_GOALS.md",
    "docs/model_management/LOCAL_MODEL_MANAGEMENT_RECEIPT_PLAN.md",
    "docs/model_management/M152_TO_M153_BOUNDARY.md",
]
LOCAL_MODEL_MANAGEMENT_M153_M165_DOCS = [
    "docs/model_management/M153_M165_LOCAL_MODEL_MANAGEMENT_PROGRESSION.md",
    "docs/model_management/M160_M165_LIVE_LANE_BOUNDARY.md",
]
REQUIRED_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS = tuple(
    f"checkpoint:m{index}" for index in range(152, 159)
)
REQUIRED_LOCAL_MODEL_MANAGEMENT_M153_M165_CHECKPOINT_REFS = tuple(
    f"checkpoint:m{index}" for index in range(153, 166)
)
SAFE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS = tuple(
    f"checkpoint:m{index}" for index in range(153, 160)
)
LIVE_READ_ONLY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS = ("checkpoint:m160", "checkpoint:m161")
LIVE_MODEL_ACQUISITION_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS = ("checkpoint:m162",)
LIVE_LLAMA_CPP_SUPERVISOR_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS = ("checkpoint:m163",)
LIVE_OPENAI_GATEWAY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS = ("checkpoint:m164",)
LIVE_SETTINGS_TUNING_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS = ("checkpoint:m165",)
FUTURE_LIVE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS: tuple[str, ...] = ()
LOCAL_MODEL_SELECTION_WEIGHTS = {
    "hardware_fit": 0.35,
    "task_capability": 0.20,
    "query_name": 0.15,
    "popularity": 0.10,
    "recency": 0.10,
    "license_provenance": 0.10,
}

_RAW_LOCAL_PATH_RE = re.compile(r"(/Users/|/home/|/var/|/etc/|[A-Za-z]:\\|~/|\.\./)")
_URL_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://")
_SECRET_LIKE_RE = re.compile(
    r"(api[_-]?key|authorization|bearer\s+|cookie|password|private[_-]?key|secret|token=|client[_-]?secret)",
    re.IGNORECASE,
)

_POLICY_REQUIRED_TRUE = [
    ("contract_only", "M152_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M152_REVIEW_ONLY_REQUIRED"),
    ("post_m151_only", "M152_POST_M151_ONLY_REQUIRED"),
    ("deterministic", "M152_DETERMINISTIC_REQUIRED"),
    ("local_only", "M152_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M152_SAFE_REFS_ONLY_REQUIRED"),
    ("disabled_by_default", "M152_DISABLED_BY_DEFAULT_REQUIRED"),
    ("no_effect_receipt_required", "M152_NO_EFFECT_RECEIPT_REQUIRED"),
    ("model_router_metadata_only", "M152_MODEL_ROUTER_METADATA_ONLY_REQUIRED"),
    ("model_runtime_contracts_only", "M152_MODEL_RUNTIME_CONTRACTS_ONLY_REQUIRED"),
    ("openwebui_shell_only", "M152_OPENWEBUI_SHELL_ONLY_REQUIRED"),
    ("control_center_review_surface_only", "M152_CONTROL_CENTER_REVIEW_SURFACE_ONLY_REQUIRED"),
]
_POLICY_DENIALS = [
    ("live_hf_search_enabled", "M152_LIVE_HF_SEARCH_DENIED"),
    ("local_system_probe_enabled", "M152_LOCAL_SYSTEM_PROBE_DENIED"),
    ("model_download_enabled", "M152_MODEL_DOWNLOAD_DENIED"),
    ("model_file_read_enabled", "M152_MODEL_FILE_READ_DENIED"),
    ("llama_cpp_import_enabled", "M152_LLAMA_CPP_IMPORT_DENIED"),
    ("llama_cpp_server_enabled", "M152_LLAMA_CPP_SERVER_DENIED"),
    ("llama_cpp_settings_apply_enabled", "M152_SETTINGS_APPLY_DENIED"),
    ("runtime_execution_enabled", "M152_RUNTIME_EXECUTION_DENIED"),
    ("subprocess_execution_enabled", "M152_SUBPROCESS_EXECUTION_DENIED"),
    ("network_access_enabled", "M152_NETWORK_ACCESS_DENIED"),
    ("prompt_processing_enabled", "M152_PROMPT_PROCESSING_DENIED"),
    ("model_call_enabled", "M152_MODEL_CALL_DENIED"),
    ("raw_prompt_logging_enabled", "M152_RAW_PROMPT_LOGGING_DENIED"),
    ("raw_response_logging_enabled", "M152_RAW_RESPONSE_LOGGING_DENIED"),
    ("memory_write_enabled", "M152_MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "M152_CONTEXT_INJECTION_DENIED"),
    ("backend_route_enabled", "M152_BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "M152_CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "M152_DEPENDENCY_DENIED"),
    ("production_authority_granted", "M152_PRODUCTION_AUTHORITY_DENIED"),
]
_HARDWARE_REQUIRED_TRUE = [("injected_summary_only", "M152_INJECTED_HARDWARE_SUMMARY_REQUIRED")]
_HARDWARE_DENIALS = [
    ("local_probe_performed", "M152_LOCAL_SYSTEM_PROBE_DENIED"),
    ("raw_hostname_included", "M152_RAW_HOSTNAME_DENIED"),
    ("raw_serial_included", "M152_RAW_SERIAL_DENIED"),
    ("raw_username_included", "M152_RAW_USERNAME_DENIED"),
    ("raw_path_included", "M152_RAW_PATH_DENIED"),
    ("env_dump_included", "M152_ENV_DUMP_DENIED"),
]
_GGUF_REQUIRED_TRUE = [("gguf_declared", "M152_GGUF_REQUIRED")]
_GGUF_DENIALS = [
    ("download_requested", "M152_MODEL_DOWNLOAD_DENIED"),
    ("model_file_read_requested", "M152_MODEL_FILE_READ_DENIED"),
    ("raw_url_included", "M152_RAW_URL_DENIED"),
    ("raw_local_path_included", "M152_RAW_PATH_DENIED"),
    ("raw_model_card_included", "M152_RAW_MODEL_CARD_DENIED"),
]
_HF_PREVIEW_REQUIRED_TRUE = [
    ("inert_preview_only", "M152_INERT_HF_PREVIEW_REQUIRED"),
    ("injected_candidates_only", "M152_INJECTED_CANDIDATES_ONLY_REQUIRED"),
]
_HF_PREVIEW_DENIALS = [
    ("live_search_requested", "M152_LIVE_HF_SEARCH_DENIED"),
    ("network_access_requested", "M152_NETWORK_ACCESS_DENIED"),
    ("authenticated_request_requested", "M152_AUTHENTICATED_HF_REQUEST_DENIED"),
    ("token_use_requested", "M152_TOKEN_USE_DENIED"),
    ("raw_model_card_requested", "M152_RAW_MODEL_CARD_DENIED"),
    ("download_requested", "M152_MODEL_DOWNLOAD_DENIED"),
    ("model_call_requested", "M152_MODEL_CALL_DENIED"),
]
_SETTINGS_REQUIRED_TRUE = [
    ("ctx_size_capped_by_fit", "M152_CTX_SIZE_FIT_CAP_REQUIRED"),
    ("fit_enabled", "M152_FIT_SETTING_REQUIRED"),
    ("prompt_cache_enabled", "M152_PROMPT_CACHE_PLAN_REQUIRED"),
    ("metrics_loopback_only", "M152_LOOPBACK_METRICS_ONLY_REQUIRED"),
]
_SETTINGS_DENIALS = [
    ("llama_cpp_imported", "M152_LLAMA_CPP_IMPORT_DENIED"),
    ("server_started", "M152_LLAMA_CPP_SERVER_DENIED"),
    ("subprocess_spawned", "M152_SUBPROCESS_EXECUTION_DENIED"),
    ("argv_executed", "M152_ARGV_EXECUTION_DENIED"),
    ("endpoint_contacted", "M152_ENDPOINT_CONTACT_DENIED"),
    ("settings_applied", "M152_SETTINGS_APPLY_DENIED"),
    ("model_loaded", "M152_MODEL_LOAD_DENIED"),
    ("prompt_processed", "M152_PROMPT_PROCESSING_DENIED"),
    ("model_call_performed", "M152_MODEL_CALL_DENIED"),
]
_SELECTION_REQUIRED_TRUE = [("injected_candidates_only", "M152_INJECTED_CANDIDATES_ONLY_REQUIRED")]
_SELECTION_DENIALS = [
    ("live_search_performed", "M152_LIVE_HF_SEARCH_DENIED"),
    ("selection_authority_granted", "M152_SELECTION_AUTHORITY_DENIED"),
    ("routing_authority_granted", "M152_ROUTING_AUTHORITY_DENIED"),
    ("download_performed", "M152_MODEL_DOWNLOAD_DENIED"),
    ("model_loaded", "M152_MODEL_LOAD_DENIED"),
    ("model_call_performed", "M152_MODEL_CALL_DENIED"),
]
_OBSERVABILITY_SIGNAL_REQUIRED_TRUE = [
    ("redacted", "M152_OBSERVABILITY_REDACTION_REQUIRED"),
    ("local_only", "M152_OBSERVABILITY_LOCAL_ONLY_REQUIRED"),
]
_OBSERVABILITY_SIGNAL_DENIALS = [
    ("raw_prompt_included", "M152_RAW_PROMPT_DENIED"),
    ("raw_response_included", "M152_RAW_RESPONSE_DENIED"),
    ("raw_provider_payload_included", "M152_RAW_PROVIDER_PAYLOAD_DENIED"),
    ("raw_log_included", "M152_RAW_LOG_DENIED"),
    ("env_vars_included", "M152_ENV_DUMP_DENIED"),
    ("raw_path_included", "M152_RAW_PATH_DENIED"),
    ("secret_included", "M152_SECRET_DENIED"),
    ("settings_applied", "M152_SETTINGS_APPLY_DENIED"),
    ("restart_requested", "M152_RESTART_DENIED"),
]
_OBSERVABILITY_PREVIEW_REQUIRED_TRUE = [
    ("redacted_only", "M152_OBSERVABILITY_REDACTION_REQUIRED"),
    ("local_only", "M152_OBSERVABILITY_LOCAL_ONLY_REQUIRED"),
    ("advisory_only", "M152_ADVISORY_ONLY_REQUIRED"),
]
_OBSERVABILITY_PREVIEW_DENIALS = [
    ("settings_applied", "M152_SETTINGS_APPLY_DENIED"),
    ("restart_requested", "M152_RESTART_DENIED"),
    ("model_call_performed", "M152_MODEL_CALL_DENIED"),
    ("raw_prompt_exported", "M152_RAW_PROMPT_DENIED"),
    ("raw_response_exported", "M152_RAW_RESPONSE_DENIED"),
]
_FREEZE_REQUIRED_TRUE = [
    ("contract_only", "M152_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M152_REVIEW_ONLY_REQUIRED"),
    ("freeze_only", "M152_FREEZE_ONLY_REQUIRED"),
    ("deterministic", "M152_DETERMINISTIC_REQUIRED"),
]
_FREEZE_REQUEST_DENIALS = [
    ("live_search_requested", "M152_LIVE_HF_SEARCH_DENIED"),
    ("local_probe_requested", "M152_LOCAL_SYSTEM_PROBE_DENIED"),
    ("download_requested", "M152_MODEL_DOWNLOAD_DENIED"),
    ("llama_cpp_server_requested", "M152_LLAMA_CPP_SERVER_DENIED"),
    ("subprocess_execution_requested", "M152_SUBPROCESS_EXECUTION_DENIED"),
    ("network_access_requested", "M152_NETWORK_ACCESS_DENIED"),
    ("model_call_requested", "M152_MODEL_CALL_DENIED"),
    ("backend_route_requested", "M152_BACKEND_ROUTE_DENIED"),
    ("control_center_control_requested", "M152_CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_requested", "M152_DEPENDENCY_DENIED"),
    ("production_authority_requested", "M152_PRODUCTION_AUTHORITY_DENIED"),
]
_FREEZE_RECORD_DENIALS = [
    ("live_search_performed", "M152_LIVE_HF_SEARCH_DENIED"),
    ("local_probe_performed", "M152_LOCAL_SYSTEM_PROBE_DENIED"),
    ("download_performed", "M152_MODEL_DOWNLOAD_DENIED"),
    ("llama_cpp_server_started", "M152_LLAMA_CPP_SERVER_DENIED"),
    ("subprocess_execution_performed", "M152_SUBPROCESS_EXECUTION_DENIED"),
    ("network_access_performed", "M152_NETWORK_ACCESS_DENIED"),
    ("model_call_performed", "M152_MODEL_CALL_DENIED"),
    ("backend_route_added", "M152_BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "M152_CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "M152_DEPENDENCY_DENIED"),
    ("production_authority_granted", "M152_PRODUCTION_AUTHORITY_DENIED"),
]
_M153_M165_REQUIRED_TRUE = [
    ("contract_only", "M153_M165_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M153_M165_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M153_M165_DETERMINISTIC_REQUIRED"),
    ("local_only", "M153_M165_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M153_M165_SAFE_REFS_ONLY_REQUIRED"),
    ("disabled_by_default", "M153_M165_DISABLED_BY_DEFAULT_REQUIRED"),
    ("no_effect_only", "M153_M165_NO_EFFECT_ONLY_REQUIRED"),
]
_M153_M165_MILESTONE_REQUIRED_TRUE = _M153_M165_REQUIRED_TRUE + [
    ("future_live_authority_contract_only", "M153_M165_FUTURE_LIVE_AUTHORITY_CONTRACT_ONLY_REQUIRED"),
]
_M153_M165_PLAN_REQUIRED_TRUE = _M153_M165_REQUIRED_TRUE + [
    ("m153_m159_safe_lane_complete", "M153_M159_SAFE_LANE_REQUIRED"),
    ("m160_live_read_only_lane_enabled", "M160_LIVE_READ_ONLY_LANE_REQUIRED"),
    ("m162_live_acquisition_lane_enabled", "M162_LIVE_ACQUISITION_LANE_REQUIRED"),
    ("m163_live_supervisor_lane_enabled", "M163_LIVE_SUPERVISOR_LANE_REQUIRED"),
    ("m164_live_gateway_lane_enabled", "M164_LIVE_GATEWAY_LANE_REQUIRED"),
    ("m165_live_tuning_lane_enabled", "M165_LIVE_TUNING_LANE_REQUIRED"),
]
_M153_M165_DENIALS = [
    ("live_capability_authorized", "M153_M165_LIVE_CAPABILITY_AUTHORITY_DENIED"),
    ("live_hf_search_performed", "M160_LIVE_HF_SEARCH_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("local_system_probe_performed", "M161_LOCAL_SYSTEM_PROBE_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("model_download_performed", "M162_MODEL_DOWNLOAD_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("llama_cpp_server_started", "M163_LLAMA_CPP_SERVER_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("subprocess_execution_performed", "M163_SUBPROCESS_EXECUTION_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("network_access_performed", "M160_NETWORK_ACCESS_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("model_call_performed", "M164_MODEL_CALL_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("settings_applied", "M165_SETTINGS_APPLY_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("backend_route_added", "M153_M165_BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "M153_M165_CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "M153_M165_DEPENDENCY_DENIED"),
    ("production_authority_granted", "M153_M165_PRODUCTION_AUTHORITY_DENIED"),
]
_M153_M165_MILESTONE_EXTRA_DENIALS = [
    ("model_file_read_performed", "M153_M165_MODEL_FILE_READ_DENIED"),
    ("model_cache_write_performed", "M162_MODEL_CACHE_WRITE_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("llama_cpp_import_performed", "M163_LLAMA_CPP_IMPORT_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("prompt_processed", "M164_PROMPT_PROCESSING_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("runtime_restart_performed", "M165_RUNTIME_RESTART_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("openwebui_" "plugin_added", "M153_M165_OPENWEBUI_" "PLUGIN_DENIED"),
    ("memory_write_performed", "M153_M165_MEMORY_WRITE_DENIED"),
    ("context_injection_performed", "M153_M165_CONTEXT_INJECTION_DENIED"),
    ("tool_execution_performed", "M153_M165_TOOL_EXECUTION_DENIED"),
]
_FUTURE_LIVE_CONTRACT_REQUIRED_TRUE = [
    ("approval_bound", "M160_M165_APPROVAL_BOUND_REQUIRED"),
    ("approval_refs_are_identifiers_only", "M160_M165_APPROVAL_REFS_IDENTIFIERS_ONLY_REQUIRED"),
    ("exact_scope_bound", "M160_M165_EXACT_SCOPE_BOUND_REQUIRED"),
    ("non_transferable", "M160_M165_NON_TRANSFERABLE_REQUIRED"),
    ("revocable", "M160_M165_REVOCABLE_REQUIRED"),
    ("replay_safe", "M160_M165_REPLAY_SAFE_REQUIRED"),
    ("disabled_by_default", "M160_M165_DISABLED_BY_DEFAULT_REQUIRED"),
    ("review_only", "M160_M165_REVIEW_ONLY_REQUIRED"),
    ("no_effect_only", "M160_M165_NO_EFFECT_ONLY_REQUIRED"),
]
_FUTURE_LIVE_CONTRACT_DENIALS = [
    ("live_capability_authorized", "M160_M165_LIVE_CAPABILITY_AUTHORITY_DENIED"),
    ("network_access_performed", "M160_NETWORK_ACCESS_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("local_system_probe_performed", "M161_LOCAL_SYSTEM_PROBE_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("download_performed", "M162_MODEL_DOWNLOAD_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("model_file_read_performed", "M162_MODEL_FILE_READ_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("model_cache_write_performed", "M162_MODEL_CACHE_WRITE_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("llama_cpp_import_performed", "M163_LLAMA_CPP_IMPORT_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("subprocess_execution_performed", "M163_SUBPROCESS_EXECUTION_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("server_started", "M163_LLAMA_CPP_SERVER_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("shell_string_included", "M163_SHELL_STRING_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("argv_executed", "M163_ARGV_EXECUTION_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("prompt_processed", "M164_PROMPT_PROCESSING_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("raw_prompt_logged", "M164_RAW_PROMPT_LOGGING_DENIED"),
    ("raw_response_logged", "M164_RAW_RESPONSE_LOGGING_DENIED"),
    ("model_call_performed", "M164_MODEL_CALL_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("settings_applied", "M165_SETTINGS_APPLY_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("runtime_restart_performed", "M165_RUNTIME_RESTART_DENIED_UNTIL_RUNTIME_MILESTONE"),
    ("backend_route_added", "M160_M165_BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "M160_M165_CONTROL_CENTER_CONTROL_DENIED"),
    ("openwebui_settings_mutation_requested", "M164_OPENWEBUI_SETTINGS_MUTATION_DENIED"),
    ("openwebui_privileged_management_used", "M164_OPENWEBUI_" "ADMIN_API_DENIED"),
    ("openwebui_" "plugin_added", "M164_OPENWEBUI_" "PLUGIN_DENIED"),
    ("openwebui_is_agent_brain", "M164_OPENWEBUI_AUTHORITY_DENIED"),
    ("memory_write_performed", "M160_M165_MEMORY_WRITE_DENIED"),
    ("context_injection_performed", "M160_M165_CONTEXT_INJECTION_DENIED"),
    ("tool_execution_performed", "M160_M165_TOOL_EXECUTION_DENIED"),
    ("dependency_added", "M160_M165_DEPENDENCY_DENIED"),
    ("production_authority_granted", "M160_M165_PRODUCTION_AUTHORITY_DENIED"),
]
