from enum import Enum


class TaskPlanningStatus(str, Enum):
    contract_only = "contract_only"
    planning_only = "planning_only"
    validation_only = "validation_only"
    review_only = "review_only"
    blocked = "blocked"


class TaskPlanDecisionStatus(str, Enum):
    valid_for_review = "valid_for_review"
    denied = "denied"
    blocked = "blocked"
    requires_user_review = "requires_user_review"
    future_execution_required = "future_execution_required"


class TaskPlanAuthorityLevel(str, Enum):
    non_authoritative = "non_authoritative"
    review_plan_only = "review_plan_only"
    blocked_authority = "blocked_authority"


class TaskStepKind(str, Enum):
    no_effect = "no_effect"
    review_metadata = "review_metadata"
    summarize_refs = "summarize_refs"
    compare_refs = "compare_refs"
    prepare_checklist = "prepare_checklist"
    tool_execution_planned = "tool_execution_planned"
    action_execution_planned = "action_execution_planned"
    file_mutation_planned = "file_mutation_planned"
    memory_write_planned = "memory_write_planned"
    network_call_planned = "network_call_planned"
    model_call_planned = "model_call_planned"
    browser_action_planned = "browser_action_planned"
    mobile_device_action_planned = "mobile_device_action_planned"
    remote_execution_planned = "remote_execution_planned"
    plugin_enablement_planned = "plugin_enablement_planned"
    shell_execution_blocked = "shell_execution_blocked"
    destructive_blocked = "destructive_blocked"
    unknown_blocked = "unknown_blocked"


class TaskRiskLevel(str, Enum):
    none = "none"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    blocked = "blocked"
    unknown_blocked = "unknown_blocked"


class TaskDependencyKind(str, Enum):
    before_after = "before_after"
    requires_output_summary = "requires_output_summary"
    blocks_until_reviewed = "blocks_until_reviewed"


class PlanInputTrustLevel(str, Enum):
    safe_reference = "safe_reference"
    canonical_ref = "canonical_ref"
    evidence_ref = "evidence_ref"
    receipt_ref = "receipt_ref"
    event_ref = "event_ref"
    user_reviewed_ref = "user_reviewed_ref"
    memory_ref = "memory_ref"
    context_pack_ref = "context_pack_ref"
    tool_intent_ref = "tool_intent_ref"
    approval_ref = "approval_ref"
    model_output_blocked = "model_output_blocked"
    runtime_output_blocked = "runtime_output_blocked"
    openwebui_output_blocked = "openwebui_output_blocked"
    unknown_blocked = "unknown_blocked"
