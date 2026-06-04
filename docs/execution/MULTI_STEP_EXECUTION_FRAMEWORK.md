# Multi-Step Execution Framework

Status: active M30 source-of-truth documentation. Current active baseline: **v0.35.0**.

v0.34.0 / M30 implements the Multi-Step Execution Framework as deterministic,
local, state-machine-only contract logic. It models execution runs, execution
steps, transition requests, transition decisions, and receipt plans for
side-effect-safe state advancement.

v0.34.1 hardens M30 with ready-only no-effect step completion, incomplete
finalize denial, replay-key and transition-id replay protection, hidden
side-effect denial, evaluator revalidation, and no-side-effect invariants.

M30 is no real task execution and is not real execution. A valid transition may advance a no-effect step to
`completed_no_effect`, pause, block, or wait on dependencies. Every decision
keeps `execution_authorized=False`, `execution_performed=False`, and an empty
side-effect list.

M30 adds:

- execution run contracts.
- execution step contracts.
- transition request and decision contracts.
- dependency-aware progression.
- replay protection through deterministic replay keys and transition IDs.
- evaluator-side revalidation of safety-critical fields.
- non-authoritative receipt plans.
- static verifier and Foundation Gate coverage.

M30 denies:

- real task execution.
- action execution.
- tool execution.
- file mutation.
- memory writes.
- Event Ledger mutation.
- network calls.
- model/provider calls.
- browser, mobile, remote, plugin, shell, scheduler/background worker, autonomous loop, and context injection behavior.
- backend execution routes.
- Control Center execute controls.
- production authority.

M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32-M40 remain planned/provisional.
