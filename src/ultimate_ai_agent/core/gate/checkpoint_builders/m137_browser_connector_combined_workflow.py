from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.autonomy import (
    M137_MAX_BROWSER_PLAN_REFS,
    M137_MAX_WORKFLOW_STEP_REFS,
    AutonomyAuthorityMode,
    AutonomyRiskClass,
    BrowserConnectorCombinedWorkflowPolicy,
    BrowserConnectorCombinedWorkflowRequest,
    BrowserConnectorCombinedWorkflowStatus,
    build_browser_connector_combined_workflow_decision,
    validate_browser_connector_combined_workflow_decision,
    validate_browser_connector_combined_workflow_policy,
    validate_browser_connector_combined_workflow_request,
)


def _request(**overrides: Any) -> Any:
    data = {
        "request_ref": "browser-connector-combined-workflow-request:m137:review",
        "combined_workflow_plan_ref": "combined-workflow-plan:m137:review",
        "mode_ref": "autonomy-mode:m137:mode5",
        "actor_ref": "actor:m137:reviewer",
        "user_ref": "user:m137:owner",
        "workspace_ref": "workspace:m137:local",
        "scope_ref": "scope:m137:single-workspace",
        "resource_refs": ["resource:m137:workflow-summary"],
        "capability_refs": ["capability:m137:combined-workflow-review"],
        "allowlist_refs": ["allowlist:m137:safe-browser-connector-refs-only"],
        "m136_dependency_execution_decision_ref": (
            "cross-tool-dependency-execution-decision:m136:review"
        ),
        "m135_recovery_planner_decision_ref": (
            "autonomous-recovery-planner-decision:m135:review"
        ),
        "m134_human_checkpoint_decision_ref": (
            "human-checkpoint-scheduling-decision:m134:review"
        ),
        "m133_supervisor_decision_ref": (
            "long-running-task-supervisor-decision:m133:review"
        ),
        "m132_trusted_workflow_decision_ref": (
            "trusted-recurring-workflow-decision:m132:review"
        ),
        "browser_workflow_ref": "browser-workflow:m137:observe-plan",
        "browser_observation_ref": "browser-observation:m137:safe-visible-text",
        "browser_action_plan_refs": [
            "browser-action-plan:m137:review-only-click",
            "browser-action-plan:m137:review-only-form",
        ],
        "connector_workflow_ref": "connector-workflow:m137:review-plan",
        "connector_account_scope_ref": "connector-account-scope:m137:safe-ref",
        "connector_action_plan_refs": [
            "connector-action-plan:m137:review-only-read",
            "connector-action-plan:m137:review-only-write",
        ],
        "workflow_step_refs": [
            "workflow-step:m137:observe",
            "workflow-step:m137:connector-review",
            "workflow-step:m137:human-checkpoint",
        ],
        "combined_dependency_graph_ref": "combined-dependency-graph:m137:declared",
        "dependency_order_ref": "dependency-order:m137:review-only",
        "safe_handoff_ref": "safe-handoff:m137:redacted-summary",
        "dry_run_plan_ref": "dry-run-plan:m137:no-execution",
        "approval_bundle_ref": "approval-bundle:m137:review-only",
        "checkpoint_ref": "checkpoint:m137:human-review",
        "human_checkpoint_ref": "human-checkpoint:m137:owner-review",
        "policy_decision_ref": "policy-decision:m137:mode5-combined-review",
        "risk_decision_ref": "risk-decision:m137:low-only",
        "audit_ref": "audit:m137:combined-review",
        "replay_ref": "replay:m137:combined-review",
        "revocation_ref": "revocation:m137:combined-review",
        "kill_switch_ref": "kill-switch:m137:combined-review",
        "no_effect_receipt_plan_ref": "receipt-plan:m137:combined:no-effect",
        "max_workflow_steps": M137_MAX_WORKFLOW_STEP_REFS,
        "max_risk_class": AutonomyRiskClass.low,
        "safe_workflow_summary": (
            "Review browser and connector workflow refs without running actions."
        ),
    }
    data.update(overrides)
    return BrowserConnectorCombinedWorkflowRequest(**data)
