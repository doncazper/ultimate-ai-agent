from enum import Enum


class OpenWebUIBridgeStatus(str, Enum):
    contract_only = "contract_only"
    planned_disabled = "planned_disabled"
    adapter_pilot = "adapter_pilot"
    blocked = "blocked"
    future_requires_review = "future_requires_review"
    not_implemented = "not_implemented"


class OpenWebUISurfaceRole(str, Enum):
    conversational_shell = "conversational_shell"
    chat_session_host = "chat_session_host"
    transcript_view = "transcript_view"
    context_link_source = "context_link_source"
    not_authority = "not_authority"


class OpenWebUIMessageDirection(str, Enum):
    user_to_agent_core_planned = "user_to_agent_core_planned"
    agent_core_to_user_planned = "agent_core_to_user_planned"
    system_status_to_shell_planned = "system_status_to_shell_planned"
    blocked = "blocked"


class OpenWebUIContentMode(str, Enum):
    summary_only = "summary_only"
    ref_only = "ref_only"
    redacted_preview = "redacted_preview"
    raw_content_blocked = "raw_content_blocked"
    future_requires_contract = "future_requires_contract"


class OpenWebUIAuthorityBoundary(str, Enum):
    agent_core_authority = "agent_core_authority"
    approval_authority_required = "approval_authority_required"
    no_direct_tool_execution = "no_direct_tool_execution"
    no_direct_memory_write = "no_direct_memory_write"
    no_direct_runtime_execution = "no_direct_runtime_execution"
    no_direct_provider_call = "no_direct_provider_call"


class OpenWebUIBridgeDecisionStatus(str, Enum):
    contract_valid = "contract_valid"
    denied = "denied"
    blocked = "blocked"
    requires_future_bridge = "requires_future_bridge"
    requires_user_approval = "requires_user_approval"
    not_implemented = "not_implemented"


class OpenWebUIBridgeAdapterStatus(str, Enum):
    safe_summary_ready = "safe_summary_ready"
    denied = "denied"
    blocked = "blocked"


class OpenWebUIRiskLevel(str, Enum):
    safe = "safe"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    forbidden = "forbidden"
