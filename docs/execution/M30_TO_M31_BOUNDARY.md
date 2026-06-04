# M30 to M31 Boundary

Status: active M30-to-M31 boundary. Current active baseline: **v0.35.1**.

v0.34.0 / M30 implements Multi-Step Execution Framework as deterministic,
local, side-effect-safe, state-machine-only contracts. It may validate
execution runs, execution steps, transition requests, dependency-aware no-effect
progression, replay protection, evaluator revalidation, non-authoritative
decisions, and receipt plans.

v0.34.1 hardens that boundary with ready-only step completion, incomplete run
finalization denial, transition-id replay protection, hidden side-effect
metadata denial, and evaluator revalidation for no-side-effect decisions.

M30 must not perform real task execution, action execution, tool execution,
file mutation, memory writes, Event Ledger mutation, network calls,
model/provider calls, browser/mobile/remote/plugin/shell actions, scheduler
runtime, background workers, autonomous loops, context injection, backend
execution routes, Control Center execute controls, dependencies, production
authority, or M31 work.

M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single
Safe No-Op Tool. It allows only the deterministic no-op tool and does not
weaken M30 state-machine no-side-effect boundaries.

M32-M40 remain planned/provisional.
