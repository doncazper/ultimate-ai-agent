# Ultimate AI Agent Docs

Status: active
Current through: v0.36.1
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
docs/archive/releases/v0_36_1/README_IMPORT.md
docs/archive/releases/v0_36_1/master_plan.md
docs/release_notes/v0_36_1.md
docs/implementation/foundation_gate_implementation_plan_v0_36_1.md
docs/tools/FILESYSTEM_METADATA_TOOL.md
docs/tools/FILESYSTEM_METADATA_PATH_POLICY.md
docs/tools/FILESYSTEM_METADATA_RESULT_CONTRACT.md
docs/tools/FILESYSTEM_METADATA_AUTHORITY_BOUNDARY.md
docs/tools/FILESYSTEM_METADATA_NON_GOALS.md
docs/tools/M32_TO_M33_BOUNDARY.md
docs/tools/TOOL_RUNTIME_ADAPTER.md
docs/tools/NOOP_TOOL_RUNTIME.md
docs/tools/TOOL_RUNTIME_INVOCATION_CONTRACT.md
docs/tools/TOOL_RUNTIME_AUTHORITY_BOUNDARY.md
docs/tools/TOOL_RUNTIME_REPLAY_POLICY.md
docs/tools/TOOL_RUNTIME_RECEIPT_PLAN.md
docs/tools/TOOL_RUNTIME_NON_GOALS.md
docs/tools/M31_TO_M32_BOUNDARY.md
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

v0.36.1 hardens M32 safe local filesystem metadata under server-owned safe
roots. It strengthens path normalization, encoded traversal denial,
home/Windows/double-separator path denial, hidden/private-key-like path denial,
caller-selected root denial, metadata alias flag denial, evaluator
revalidation, static verification, documentation, and Foundation Gate coverage.
It returns metadata only and denies raw content, text preview, content hash,
directory listing, recursive traversal, symlink following, caller-selected
roots, file mutation, backend execution routes, dependencies, M33 work, and
production authority.

v0.35.1 hardens M31 Real Tool Runtime Adapter, Single Safe No-Op Tool. It
strengthens allowlist validation, tool_ref/tool_name consistency, dynamic
dispatch denial, hidden side-effect denial, authority-boundary checks,
evaluator revalidation, replay protection, safe no-op result handling, static
verification, documentation, and Foundation Gate coverage. It adds no arbitrary
tool execution, side-effecting tools, shell execution, file mutation, memory
writes, network/model/provider calls, backend execute routes, Control Center
execute controls, dependencies, production authority, or M32 work.

v0.34.1 hardens M30 Multi-Step Execution Framework as deterministic, local,
side-effect-safe, state-machine-only contracts.

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

M33-M40 remain planned/provisional.
