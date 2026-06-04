# M29 to M30 Boundary

Status: active M29 boundary. Current active baseline: **v0.33.1**.

v0.33.0 / M29 implements the Agent Task Planning Engine as deterministic, local, non-executing, review-only planning contracts. v0.33.1 hardens M29 dependency graph, risk, side-effect, authority-boundary, evaluator revalidation, and no-execution checks.

M29 may validate task goals, task steps, dependency graphs, input boundaries, risk boundaries, decision envelopes, and receipt plans. M29 may mark a safe plan valid for review.

M29 must not execute tasks, tools, actions, shell commands, files, memory writes, network calls, model/provider calls, browser/mobile/remote/plugin actions, scheduler jobs, background workers, context injection, backend execution routes, Control Center execute controls, dependencies, production authority, or M30 work.

M29 task plans remain non-authoritative. Approval refs, approval decision refs,
context pack refs, memory refs, tool-intent refs, OpenWebUI refs, Control
Center preview refs, and model output cannot authorize execution. Dependency
graphs must be acyclic, duplicate/missing step IDs are denied, risk downgrade
is denied, side effects cannot be hidden, and evaluator boundaries revalidate
safety-critical fields before review decisions.

M30 remains planned/provisional. Future M30 work requires a dedicated implementation prompt, review prompt, tests, verifier coverage, Foundation Gate criteria, and release tag.

M30-M40 remain planned/provisional.
