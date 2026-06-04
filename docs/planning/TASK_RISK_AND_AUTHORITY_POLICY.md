# Task Risk and Authority Policy

Status: active M29 contract. Current active baseline: **v0.33.1**.

M29 task plans are review-only. The evaluator denies caller attempts to downgrade risk or hide side effects for:

- tool execution
- action execution
- file mutation
- memory writes
- network calls
- model/provider calls
- browser/mobile/remote/plugin/shell execution
- destructive actions

Derived risk wins over caller-declared risk. A mutating step cannot be
classified as `no_effect`, file write/delete cannot be downgraded to
`read_metadata`, memory writes cannot be downgraded, and hidden side effects in
step metadata are denied. Plan risk equals the highest trusted derived step
risk.

Approval refs are identifiers, not task authority. `approval_test_*` refs are test-only and must not authorize runtime behavior.

Approval decision refs, context pack refs, memory refs, tool intent refs,
OpenWebUI refs, Control Center preview refs, and model output cannot authorize
execution. Truth/evidence refs may explain planning rationale only.

M29 decisions always keep `execution_authorized=False`, `execution_performed=False`, and `scheduler_registered=False`.

M30-M40 remain planned/provisional.
