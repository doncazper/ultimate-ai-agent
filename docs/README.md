# Ultimate AI Agent Docs

Status: active
Current through: v0.101.0 plus accepted checkpoint-m168 and active Operator Runtime Excellence P1 durable run spine, append-first storage, lifecycle contract, task decomposition durable-run binding, offline restore planning, replay-safe receipt hashing, Control Center route status manifest work, product language rules, browser smoke readiness, and accessible operator states
Purpose: Human-facing entrypoint for active documentation and historical archive navigation.

Active docs are few, indexed, and current. Historical docs are preserved under
`docs/archive/`, clearly treated as audit artifacts, and are not current source
of truth.

Start with:

```text
docs/DOCUMENTATION_INDEX.md
SECURITY.md
docs/canonical/09_roadmap.md
docs/canonical/CANONICAL_DOC_MAP.md
docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md
docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md
docs/control_center/OPERATOR_SHELL_GAP_MAP.md
docs/control_center/ROUTE_STATUS_MANIFEST.md
docs/control_center/PRODUCT_LANGUAGE_RULES.md
docs/control_center/LOCAL_BROWSER_SMOKE.md
docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md
docs/kanban/current_board.md
docs/execution/DURABLE_RUN_SPINE.md
docs/execution/APPEND_FIRST_RUN_STORAGE.md
docs/execution/DURABLE_RUN_BACKUP_RESTORE.md
docs/security/SECURITY_TRIAGE_RUNBOOK.md
docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md
docs/roadmap/README.md
docs/archive/README.md
docs/maintenance/SEMVER_POLICY.md
docs/maintenance/RELEASE_PROCESS.md
docs/maintenance/VERSION_REPAIR_LEDGER.md
docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md
```

Current release packet and active program packet:

```text
docs/archive/releases/v0_101_0/README_IMPORT.md
docs/archive/releases/v0_101_0/master_plan.md
docs/release_notes/v0_101_0.md
docs/implementation/foundation_gate_implementation_plan_v0_101_0.md
docs/release_notes/checkpoint_m168.md
docs/release_notes/checkpoint_m166.md
docs/release_notes/checkpoint_m167.md
docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md
docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md
docs/control_center/OPERATOR_SHELL_GAP_MAP.md
docs/control_center/ROUTE_STATUS_MANIFEST.md
docs/control_center/PRODUCT_LANGUAGE_RULES.md
docs/control_center/LOCAL_BROWSER_SMOKE.md
docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md
docs/kanban/current_board.md
docs/execution/DURABLE_RUN_SPINE.md
docs/execution/APPEND_FIRST_RUN_STORAGE.md
docs/execution/DURABLE_RUN_BACKUP_RESTORE.md
SECURITY.md
docs/security/SECURITY_TRIAGE_RUNBOOK.md
docs/maintenance/SEMVER_POLICY.md
docs/maintenance/RELEASE_PROCESS.md
docs/maintenance/VERSION_REPAIR_LEDGER.md
docs/production/M166_PRODUCTION_AUTHORITY_GATE.md
docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING.md
docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md
docs/production/M167_LOCAL_MODEL_E2E_SMOKE_HARNESS.md
docs/production/LLAMA_SERVER_PACKAGING_PROVENANCE_CHECKLIST.md
docs/production/LOCAL_MODEL_OPERATIONAL_RUNBOOK.md
docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md
docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING_BOUNDARY.md
docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING_NON_GOALS.md
docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING_RUNBOOK.md
docs/model_management/M153_M165_LOCAL_MODEL_MANAGEMENT_PROGRESSION.md
docs/model_management/M160_M165_LIVE_LANE_BOUNDARY.md
docs/beta/LOCAL_DEVELOPER_BETA_FREEZE.md
docs/beta/LOCAL_DEVELOPER_BETA_FREEZE_POLICY.md
docs/beta/LOCAL_DEVELOPER_BETA_FREEZE_AUTHORITY_BOUNDARY.md
docs/beta/POST_M60_AUTONOMY_BOUNDARY.md
docs/public_readiness/PUBLIC_GITHUB_READINESS.md
docs/public_readiness/PUBLIC_GITHUB_READINESS_POLICY.md
docs/public_readiness/PUBLIC_GITHUB_READINESS_AUTHORITY_BOUNDARY.md
docs/public_readiness/M59_TO_M60_BOUNDARY.md
docs/dry_run_audit/DRY_RUN_EXECUTION_AUDIT_HARNESS.md
docs/dry_run_audit/DRY_RUN_EXECUTION_AUDIT_POLICY.md
docs/dry_run_audit/DRY_RUN_EXECUTION_AUTHORITY_BOUNDARY.md
docs/dry_run_audit/M58_TO_M59_BOUNDARY.md
docs/sandbox/RUNTIME_SANDBOX_ARCHITECTURE_REVIEW.md
docs/sandbox/RUNTIME_SANDBOX_BOUNDARY_POLICY.md
docs/sandbox/RUNTIME_SANDBOX_AUTHORITY_BOUNDARY.md
docs/sandbox/M57_TO_M58_BOUNDARY.md
docs/observability/REDACTED_OBSERVABILITY_EXPORT.md
docs/observability/REDACTED_OBSERVABILITY_EXPORT_POLICY.md
docs/observability/REDACTED_OBSERVABILITY_EXPORT_AUTHORITY_BOUNDARY.md
docs/observability/M55_TO_M56_BOUNDARY.md
docs/evals/AGENT_EVAL_REGRESSION_HARNESS.md
docs/evals/AGENT_EVAL_REGRESSION_POLICY.md
docs/evals/AGENT_EVAL_REGRESSION_AUTHORITY_BOUNDARY.md
docs/evals/M56_TO_M57_BOUNDARY.md
docs/media/SAFE_MEDIA_METADATA_INSPECTOR.md
docs/media/SAFE_MEDIA_METADATA_POLICY.md
docs/media/SAFE_MEDIA_METADATA_AUTHORITY_BOUNDARY.md
docs/media/M54_TO_M55_BOUNDARY.md
docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md
docs/files/FILE_REVIEW_APPROVAL_CAPTURE.md
docs/files/FILE_REVIEW_APPROVAL_PERSISTENCE.md
docs/files/FILE_REVIEW_APPROVAL_AUTHORITY_BOUNDARY.md
docs/files/FILE_REVIEW_APPROVAL_API.md
docs/files/M37_TO_M38_BOUNDARY.md
docs/files/BROADER_FILE_CAPABILITY_REVIEW.md
docs/files/FILE_CAPABILITY_BOUNDARY_MATRIX.md
docs/files/FILE_CAPABILITY_RISK_REGISTER.md
docs/files/FILE_CAPABILITY_DECISION_RECORD.md
docs/files/M35_SAFE_FILE_REVIEW_WORKFLOW_READINESS.md
docs/files/M34_TO_M35_BOUNDARY.md
docs/control_center/FILE_REVIEW_SURFACE_READINESS.md
docs/tools/FILE_TOOL_CAPABILITY_MATRIX.md
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

The product/package baseline is `v0.101.0` / `0.101.0`. The latest
accepted repository checkpoint tag is `checkpoint-m168`. The latest accepted
local model lane checkpoint tags remain `checkpoint-m166` and
`checkpoint-m167`. Active Operator Runtime Excellence work now includes the
P0 repair lane, UAA-P1-010 durable run spine contracts, and UAA-P1-025
append-first local run storage, UAA-P1-026 durable lifecycle contracts, and
UAA-P1-027 task decomposition durable-run binding, plus UAA-P1-028
backup/verify/offline restore planning and UAA-P1-029 replay-safe receipt
hashing, UAA-P1-030 Control Center route status manifest work, UAA-P1-031
product language rules, UAA-P1-032 browser smoke readiness, and UAA-P1-033
accessible operator states; it
adds no production authority, backend route, Control Center control, dependency, public
distribution, broad autonomy, shell/subprocess authority, browser automation,
connector writes, plugin runtime import, mobile control, or model/provider
authority.

Use active canonical docs and active roadmap docs for current work. Use archive
docs only for historical review. Git tags and release history preserve exact
historical snapshots.

v0.29.5 is documentation policy polish only. It accepts the pushed duplicate
wording cleanup from `374bb1e` and remains the cleanup baseline before M26.

v0.38.0 implements M34 Broader File Capability Review as planning,
architecture review, documentation, verifier, and Foundation Gate work only. It
adds the file capability boundary review, matrix, risk register, decision
record, M35 readiness guidance, and M34-to-M35 boundary docs. It adds no runtime
file capability, backend routes, frontend runtime features, file-review
workflow, approval capture, context proposal, context injection, memory writes,
export, execution, dependencies, mobile or TestFlight implementation, or
production authority. M35-M60 remain planned/provisional.

Historical note: v0.38.2 repaired active M34 current-baseline labels and documentation-integrity
coverage after the v0.38.1 Yellow review. At that point, docs identified v0.38.2
as the current active baseline while preserving v0.38.0 as the historical M34
implementation release and v0.38.1 as a superseded hardening release. It added no
runtime file capability, backend route, frontend feature, raw file read,
context injection, memory write, export, execution, dependency, M35 work, or
production authority.

v0.41.0 implements M37 Review Approval Capture, Review-Only Persistence. It
adds safe review-only approval and denial capture for exact redacted review
packets, safe-ref-only persistence, idempotency/replay protection, one backend
capture route at `/files/review/approvals/capture`, Control Center
review-only capture controls, tests, static verification, documentation
integrity checks, and Foundation Gate coverage. It adds no raw file reads, raw
file display, raw file storage, full-file reads, unredacted preview,
context proposal, context injection, memory writes, export, execution/tool
controls, arbitrary filesystem tools, dependencies, M38 work, or production
authority.

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

v0.60.0 implements M56 Agent Eval Regression Harness as deterministic local
contract-only regression reporting over explicitly provided safe observations.
It adds no model/provider call, tool execution, shell execution, browser
automation, network access, memory write, context injection, raw prompt capture,
raw provider payload capture, external dataset fetch, backend route, Control
Center control, dependency, production authority, or M57 work.

Historical M57-M60 planning is preserved under
`docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md`; current active roadmap status
is summarized in `docs/canonical/09_roadmap.md` and the Operator Runtime
Excellence roadmap.
