# Ultimate AI Agent Docs

Status: active
Current through: v0.37.4
Purpose: Human-facing entrypoint for active documentation and historical archive navigation.

Active docs are few, indexed, and current. Historical docs are preserved under
`docs/archive/`, clearly treated as audit artifacts, and are not current source
of truth.

Start with:

```text
docs/DOCUMENTATION_INDEX.md
docs/canonical/09_roadmap.md
docs/canonical/CANONICAL_DOC_MAP.md
docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md
docs/roadmap/README.md
docs/archive/README.md
docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md
```

Current release packet:

```text
docs/archive/releases/v0_37_4/README_IMPORT.md
docs/archive/releases/v0_37_4/master_plan.md
docs/release_notes/v0_37_4.md
docs/implementation/foundation_gate_implementation_plan_v0_37_4.md
docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md
docs/developer/LOCAL_LAUNCHER.md
scripts/dev/README.md
docs/tools/REDACTED_FILE_PREVIEW_TOOL.md
docs/tools/REDACTED_FILE_PREVIEW_POLICY.md
docs/tools/REDACTED_FILE_PREVIEW_RESULT_CONTRACT.md
docs/tools/REDACTED_FILE_PREVIEW_REDACTION_POLICY.md
docs/tools/REDACTED_FILE_PREVIEW_AUTHORITY_BOUNDARY.md
docs/tools/REDACTED_FILE_PREVIEW_NON_GOALS.md
docs/tools/M33_TO_M34_BOUNDARY.md
docs/files/LOCAL_FILE_REDACTED_PREVIEW_POLICY.md
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

v0.37.4 supersedes the old active M35-M40 roadmap projection and defines the
active M34-M60 sequence. It keeps v0.38.0 / M34 as Broader File Capability
Review, marks M34 as planning/docs/verifier only, and strengthens
documentation-integrity checks for the active supersession labels. It adds no
M34 implementation, backend routes, frontend features, file-review workflow,
approval capture, context proposal, runtime behavior, dependencies, mobile or
TestFlight implementation, or production authority.

v0.37.1 hardens M33 First Safe Local File Read Proposal, Redacted Preview Only.
It keeps the governed tool runtime adapter entry
`tool:filesystem.redacted_preview.v1` bounded to redacted preview proposals
under server-owned safe roots.

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

M34-M60 remain planned/provisional under
`docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`.
