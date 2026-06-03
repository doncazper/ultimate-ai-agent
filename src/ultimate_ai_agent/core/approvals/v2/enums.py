from enum import Enum


class ApprovalAuthorityV2Status(str, Enum):
    contract_only = "contract_only"
    policy_only = "policy_only"
    preview_only = "preview_only"
    validation_only = "validation_only"
    blocked = "blocked"
    future_execution_required = "future_execution_required"


class ActionPolicyMode(str, Enum):
    contract_only = "contract_only"
    evaluation_only = "evaluation_only"
    approval_decision_only = "approval_decision_only"
    no_execution = "no_execution"
    blocked = "blocked"


class ActionIntentStatus(str, Enum):
    draft = "draft"
    policy_evaluation_requested = "policy_evaluation_requested"
    approval_requested = "approval_requested"
    approved_for_policy_only = "approved_for_policy_only"
    denied = "denied"
    blocked = "blocked"
    expired = "expired"
    revoked = "revoked"
    future_execution_required = "future_execution_required"


class ActionKind(str, Enum):
    no_effect = "no_effect"
    read_metadata = "read_metadata"
    read_content_planned = "read_content_planned"
    file_write_planned = "file_write_planned"
    file_delete_planned = "file_delete_planned"
    memory_write_planned = "memory_write_planned"
    tool_execution_planned = "tool_execution_planned"
    network_call_planned = "network_call_planned"
    model_call_planned = "model_call_planned"
    browser_action_planned = "browser_action_planned"
    mobile_device_action_planned = "mobile_device_action_planned"
    remote_execution_planned = "remote_execution_planned"
    plugin_enable_planned = "plugin_enable_planned"
    shell_execution_blocked = "shell_execution_blocked"
    destructive_blocked = "destructive_blocked"
    credential_access_blocked = "credential_access_blocked"
    unknown_blocked = "unknown_blocked"


class ActionRiskLevel(str, Enum):
    none = "none"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    blocked = "blocked"
    unknown_blocked = "unknown_blocked"


class ActionSideEffectClass(str, Enum):
    none = "none"
    read_only_metadata = "read_only_metadata"
    read_only_content_planned = "read_only_content_planned"
    local_mutation_blocked = "local_mutation_blocked"
    memory_mutation_blocked = "memory_mutation_blocked"
    external_effect_blocked = "external_effect_blocked"
    execution_blocked = "execution_blocked"
    destructive_blocked = "destructive_blocked"
    credential_access_blocked = "credential_access_blocked"


class ApprovalScopeKind(str, Enum):
    single_action = "single_action"
    action_family = "action_family"
    resource_bound = "resource_bound"
    time_bound = "time_bound"
    actor_bound = "actor_bound"
    session_bound = "session_bound"
    blocked_wildcard = "blocked_wildcard"


class ApprovalGrantStatus(str, Enum):
    draft = "draft"
    active_for_policy_only = "active_for_policy_only"
    expired = "expired"
    revoked = "revoked"
    superseded = "superseded"
    blocked = "blocked"
    invalid = "invalid"


class ApprovalDecisionStatus(str, Enum):
    allowed_for_policy = "allowed_for_policy"
    denied = "denied"
    blocked = "blocked"
    requires_user_review = "requires_user_review"
    requires_local_approval_authority = "requires_local_approval_authority"
    requires_action_center = "requires_action_center"
    expired = "expired"
    revoked = "revoked"
    replay_detected = "replay_detected"
    future_execution_required = "future_execution_required"


class ApprovalBindingStatus(str, Enum):
    bound = "bound"
    mismatch = "mismatch"
    missing_actor = "missing_actor"
    missing_action = "missing_action"
    missing_resource = "missing_resource"
    missing_scope = "missing_scope"
    expired = "expired"
    revoked = "revoked"
    replay_detected = "replay_detected"
    blocked = "blocked"


class ActorTrustLevel(str, Enum):
    user = "user"
    local_agent_core = "local_agent_core"
    control_center_preview = "control_center_preview"
    openwebui_shell = "openwebui_shell"
    model_output_blocked = "model_output_blocked"
    memory_recall_blocked = "memory_recall_blocked"
    context_pack_non_authoritative = "context_pack_non_authoritative"
    unknown_blocked = "unknown_blocked"


class ResourceRefKind(str, Enum):
    none = "none"
    file_ref = "file_ref"
    memory_ref = "memory_ref"
    tool_intent_ref = "tool_intent_ref"
    context_pack_ref = "context_pack_ref"
    truth_claim_ref = "truth_claim_ref"
    runtime_ref = "runtime_ref"
    browser_ref = "browser_ref"
    mobile_device_ref = "mobile_device_ref"
    remote_node_ref = "remote_node_ref"
    plugin_ref = "plugin_ref"
    model_output_ref = "model_output_ref"
    unknown = "unknown"
