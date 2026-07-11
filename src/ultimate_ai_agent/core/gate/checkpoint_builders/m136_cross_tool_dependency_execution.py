from __future__ import annotations
from typing import Any
from ultimate_ai_agent.core.autonomy import (
    M136_MAX_DEPENDENCY_STEP_REFS,
    AutonomyRiskClass,
    CrossToolDependencyEdge,
    CrossToolDependencyExecutionRequest,
)


def _edge(edge_ref: Any, upstream: Any, downstream: Any) -> Any:
    return CrossToolDependencyEdge(
        edge_ref=edge_ref,
        upstream_step_ref=upstream,
        downstream_step_ref=downstream,
        dependency_kind_ref="dependency-kind:m136:safe-output-ref",
        safe_dependency_summary="A safe dependency ref is reviewed before any execution.",
    )


def _request(**overrides: Any) -> Any:
    steps = [
        "dependency-step:m136:collect-safe-ref",
        "dependency-step:m136:review-safe-ref",
        "dependency-step:m136:final-safe-summary",
    ]
    data = {
        "request_ref": "cross-tool-dependency-execution-request:m136:review",
        "dependency_execution_plan_ref": "cross-tool-dependency-execution-plan:m136:review",
        "mode_ref": "autonomy-mode:m136:mode5",
        "actor_ref": "actor:m136:reviewer",
        "user_ref": "user:m136:owner",
        "workspace_ref": "workspace:m136:local",
        "scope_ref": "scope:m136:single-workspace",
        "resource_refs": ["resource:m136:dependency-summary"],
        "capability_refs": ["capability:m136:dependency-graph-review"],
        "allowlist_refs": ["allowlist:m136:safe-tool-refs-only"],
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
        "dependency_graph_ref": "dependency-graph:m136:declared",
        "dependency_step_refs": steps,
        "dependency_edges": [
            _edge("dependency-edge:m136:first", steps[0], steps[1]),
            _edge("dependency-edge:m136:second", steps[1], steps[2]),
        ],
        "safe_tool_refs": [
            "tool:m136:first-safe-tool-ref",
            "tool:m136:second-safe-tool-ref",
        ],
        "dry_run_plan_ref": "dry-run-plan:m136:no-execution",
        "execution_order_ref": "execution-order:m136:review-only",
        "dependency_resolution_ref": "dependency-resolution:m136:safe-refs-only",
        "conflict_policy_ref": "conflict-policy:m136:human-review",
        "failure_policy_ref": "failure-policy:m136:stop-and-review",
        "recovery_plan_ref": "recovery-plan:m136:no-execution",
        "checkpoint_ref": "checkpoint:m136:human-review",
        "human_checkpoint_ref": "human-checkpoint:m136:owner-review",
        "policy_decision_ref": "policy-decision:m136:mode5-dependency-review",
        "risk_decision_ref": "risk-decision:m136:low-only",
        "audit_ref": "audit:m136:dependency-review",
        "replay_ref": "replay:m136:dependency-review",
        "revocation_ref": "revocation:m136:dependency-review",
        "kill_switch_ref": "kill-switch:m136:dependency-review",
        "no_effect_receipt_plan_ref": "receipt-plan:m136:dependency:no-effect",
        "max_dependency_steps": M136_MAX_DEPENDENCY_STEP_REFS,
        "max_risk_class": AutonomyRiskClass.low,
        "safe_dependency_summary": (
            "Review a cross-tool dependency execution contract without running tools."
        ),
    }
    data.update(overrides)
    return CrossToolDependencyExecutionRequest(**data)
