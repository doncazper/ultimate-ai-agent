# M27 to M28 Boundary

Status: active
Current through: v0.33.1
Purpose: Keep M27 Tool Broker v2 separate from M28 approval policy and future execution work.

v0.31.0 / M27 implements Tool Broker v2 + Safe Tool Intent Contracts as
validation-only and preview-only contract logic.

M27 adds:

- safe tool intent contracts.
- target ref/kind consistency checks.
- input-boundary checks.
- catalog-backed risk and side-effect checks.
- approval_ref-not-authority denial.
- context-pack-not-authority denial.
- non-executing receipt plans.
- Foundation Gate and static verifier coverage.

M27 does not add:

- real tool execution.
- local sandbox backend runtime.
- shell execution.
- file mutation.
- memory writes.
- Event Ledger mutation.
- network calls.
- browser automation.
- plugin enablement.
- model/provider calls.
- backend tool execution routes.
- Control Center execute controls.
- production authority.

v0.32.0 / M28 implements Approval Authority v2 + Action Policy Expansion as
policy-only, contract-only, and decision-only logic. M28 approval decisions are
not action execution and do not make Tool Broker v2 intents executable.

v0.33.0 implements M29 Agent Task Planning Engine as deterministic, local,
non-executing, review-only planning contracts. M30-M40 remain planned/provisional. Any future local sandbox, dry-run, approval-gated
execution, plugin runtime, browser automation, or production tool authority
must arrive through its own reviewed milestone.
