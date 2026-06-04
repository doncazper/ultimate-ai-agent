# Agent Task Planning Engine

Status: active M29 contract. Current active baseline: **v0.35.0**.

The Agent Task Planning Engine defines deterministic task plans for human review. It accepts explicit task goals, steps, dependencies, constraints, and safe references, then returns a non-authoritative decision envelope.

M29 is planning only:

- no task execution
- no scheduler runtime
- no background worker
- no tool execution
- no action execution
- no file mutation
- no memory writes
- no network calls
- no model/provider calls
- no browser, mobile, remote, plugin, or shell execution
- no context injection
- no production authority

Safe plans may be marked `valid_for_review`. That status means the plan structure is reviewable; it does not authorize execution, scheduling, approvals, tools, actions, or writes.

v0.33.1 hardens the evaluator boundary. The evaluator revalidates safety-critical fields before any `valid_for_review` decision, denies model_copy-mutated raw or secret fields, denies hidden side effects in metadata, derives trusted step and plan risk from current step content, and keeps every decision non-authoritative with `execution_performed=False`.

M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool. M32-M40 remain planned/provisional.
