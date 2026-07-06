from enum import Enum


class ExecutionFrameworkStatus(str, Enum):
    contract_only = "contract_only"
    state_machine_only = "state_machine_only"
    validation_only = "validation_only"
    review_only = "review_only"
    blocked = "blocked"


class ExecutionRunStatus(str, Enum):
    planned = "planned"
    ready = "ready"
    running_no_effect = "running_no_effect"
    waiting_for_dependency = "waiting_for_dependency"
    paused = "paused"
    blocked = "blocked"
    completed_no_effect = "completed_no_effect"
    denied = "denied"


class ExecutionStepStatus(str, Enum):
    pending = "pending"
    ready = "ready"
    waiting_for_dependency = "waiting_for_dependency"
    paused = "paused"
    blocked = "blocked"
    skipped = "skipped"
    completed_no_effect = "completed_no_effect"
    denied = "denied"


class ExecutionTransitionKind(str, Enum):
    validate_run = "validate_run"
    mark_step_ready = "mark_step_ready"
    complete_no_effect_step = "complete_no_effect_step"
    pause_run = "pause_run"
    block_run = "block_run"
    wait_for_dependency = "wait_for_dependency"
    finalize_no_effect_run = "finalize_no_effect_run"


class ExecutionTransitionStatus(str, Enum):
    approved_no_effect_transition = "approved_no_effect_transition"
    denied = "denied"
    blocked = "blocked"
    paused = "paused"
    waiting = "waiting"


class ExecutionStepMode(str, Enum):
    no_effect = "no_effect"
    validation_only = "validation_only"
    receipt_plan_only = "receipt_plan_only"
    approved_runtime_command = "approved_runtime_command"
    task_execution_blocked = "task_execution_blocked"
    action_execution_blocked = "action_execution_blocked"
    tool_execution_blocked = "tool_execution_blocked"
    file_mutation_blocked = "file_mutation_blocked"
    memory_write_blocked = "memory_write_blocked"
    event_ledger_mutation_blocked = "event_ledger_mutation_blocked"
    network_call_blocked = "network_call_blocked"
    model_call_blocked = "model_call_blocked"
    browser_action_blocked = "browser_action_blocked"
    mobile_device_action_blocked = "mobile_device_action_blocked"
    remote_execution_blocked = "remote_execution_blocked"
    plugin_enablement_blocked = "plugin_enablement_blocked"
    shell_execution_blocked = "shell_execution_blocked"
    scheduler_blocked = "scheduler_blocked"
    background_worker_blocked = "background_worker_blocked"
    unknown_blocked = "unknown_blocked"


class ExecutionInputTrustLevel(str, Enum):
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
    approval_decision_ref = "approval_decision_ref"
    model_output_blocked = "model_output_blocked"
    runtime_output_blocked = "runtime_output_blocked"
    openwebui_output_blocked = "openwebui_output_blocked"
    control_center_preview_blocked = "control_center_preview_blocked"
    unknown_blocked = "unknown_blocked"


class ExecutionBlockReason(str, Enum):
    task_execution_denied = "TASK_EXECUTION_DENIED"
    action_execution_denied = "ACTION_EXECUTION_DENIED"
    tool_execution_denied = "TOOL_EXECUTION_DENIED"
    file_mutation_denied = "FILE_MUTATION_DENIED"
    memory_write_denied = "MEMORY_WRITE_DENIED"
    event_ledger_mutation_denied = "EVENT_LEDGER_MUTATION_DENIED"
    network_call_denied = "NETWORK_CALL_DENIED"
    model_call_denied = "MODEL_CALL_DENIED"
    browser_action_denied = "BROWSER_ACTION_DENIED"
    mobile_device_action_denied = "MOBILE_DEVICE_ACTION_DENIED"
    remote_execution_denied = "REMOTE_EXECUTION_DENIED"
    plugin_enablement_denied = "PLUGIN_ENABLEMENT_DENIED"
    shell_execution_denied = "SHELL_EXECUTION_DENIED"
    scheduler_denied = "SCHEDULER_DENIED"
    background_worker_denied = "BACKGROUND_WORKER_DENIED"
    unknown_step_mode_denied = "UNKNOWN_STEP_MODE_DENIED"


class ExecutionPauseReason(str, Enum):
    user_review_required = "USER_REVIEW_REQUIRED"
    dependency_wait = "DEPENDENCY_WAIT"
    policy_review_required = "POLICY_REVIEW_REQUIRED"
