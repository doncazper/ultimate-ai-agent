# Ultimate AI Agent Docs

Status: active
Current through: v0.34.0
Purpose: Human-facing entrypoint for active documentation and historical archive navigation.

Active docs are few, indexed, and current. Historical docs are preserved under
`docs/archive/`, clearly treated as audit artifacts, and are not current source
of truth.

Start with:

```text
docs/DOCUMENTATION_INDEX.md
docs/canonical/09_roadmap.md
docs/canonical/CANONICAL_DOC_MAP.md
docs/roadmap/README.md
docs/archive/README.md
docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md
```

Current release packet:

```text
docs/archive/releases/v0_34_0/README_IMPORT.md
docs/archive/releases/v0_34_0/master_plan.md
docs/release_notes/v0_34_0.md
docs/implementation/foundation_gate_implementation_plan_v0_34_0.md
docs/execution/MULTI_STEP_EXECUTION_FRAMEWORK.md
docs/execution/EXECUTION_STATE_MACHINE.md
docs/execution/EXECUTION_STEP_CONTRACTS.md
docs/execution/EXECUTION_DEPENDENCY_POLICY.md
docs/execution/EXECUTION_TRANSITION_POLICY.md
docs/execution/EXECUTION_INPUT_BOUNDARY.md
docs/execution/EXECUTION_RECEIPT_PLAN.md
docs/execution/EXECUTION_NON_GOALS.md
docs/execution/M30_TO_M31_BOUNDARY.md
docs/planning/TASK_PLANNING_ENGINE.md
docs/planning/TASK_GOAL_STEP_PLAN_CONTRACTS.md
docs/planning/TASK_DEPENDENCY_GRAPH.md
docs/planning/TASK_INPUT_BOUNDARY.md
docs/planning/TASK_RISK_AND_AUTHORITY_POLICY.md
docs/planning/TASK_PLAN_DECISION_ENVELOPE.md
docs/planning/TASK_PLAN_RECEIPT_PLAN.md
docs/planning/TASK_PLANNING_NON_GOALS.md
docs/planning/M29_TO_M30_BOUNDARY.md
docs/approvals/APPROVAL_AUTHORITY_V2.md
docs/approvals/ACTION_POLICY.md
docs/approvals/APPROVAL_GRANT_BINDING.md
docs/approvals/APPROVAL_EXPIRY_REVOCATION_REPLAY.md
docs/approvals/ACTION_RISK_AND_SIDE_EFFECT_POLICY.md
docs/approvals/APPROVAL_REF_NOT_AUTHORITY.md
docs/approvals/ACTION_POLICY_DECISION_ENVELOPE.md
docs/approvals/APPROVAL_RECEIPT_PLAN.md
docs/approvals/APPROVAL_AUTHORITY_V2_NON_GOALS.md
docs/approvals/M28_TO_M29_BOUNDARY.md
docs/tools/TOOL_BROKER_V2.md
docs/tools/SAFE_TOOL_INTENT_CONTRACTS.md
docs/tools/TOOL_AUTHORITY_BOUNDARY.md
docs/tools/TOOL_INTENT_RECEIPT_PLAN.md
```

Use active canonical docs and active roadmap docs for current work. Use archive
docs only for historical review. Git tags and release history preserve exact
historical snapshots.

v0.29.5 is documentation policy polish only. It accepts the pushed duplicate
wording cleanup from `374bb1e` and remains the cleanup baseline before M26.

v0.34.0 implements M30 Multi-Step Execution Framework as deterministic, local,
side-effect-safe, state-machine-only contracts. It adds no real task execution,
action execution, tool execution, backend execution routes, Control Center
execute controls, dependencies, production authority, or M31 work.

v0.33.1 hardens M29 Agent Task Planning Engine as deterministic, local,
non-executing, review-only planning contracts. It strengthens dependency graph
validation, duplicate/missing step denial, self/indirect cycle detection,
derived risk checks, hidden side-effect denial, authority-boundary checks,
evaluator revalidation, static verification, and Foundation Gate coverage.
v0.33.1 added no backend execution routes, frontend features, task execution,
scheduler/background worker, action execution, tool execution, file mutation,
memory writes, network calls, model/provider calls, plugin enablement, browser
automation, mobile/device access, remote execution, shell execution,
dependencies, context injection, or production authority.

M31-M40 remain planned/provisional.
