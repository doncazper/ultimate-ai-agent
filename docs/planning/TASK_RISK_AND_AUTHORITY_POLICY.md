# Task Risk and Authority Policy

Status: active M29 contract. Current active baseline: **v0.33.0**.

M29 task plans are review-only. The evaluator denies caller attempts to downgrade risk or hide side effects for:

- tool execution
- action execution
- file mutation
- memory writes
- network calls
- model/provider calls
- browser/mobile/remote/plugin/shell execution
- destructive actions

Approval refs are identifiers, not task authority. `approval_test_*` refs are test-only and must not authorize runtime behavior.

M29 decisions always keep `execution_authorized=False`, `execution_performed=False`, and `scheduler_registered=False`.

M30-M40 remain planned/provisional.
