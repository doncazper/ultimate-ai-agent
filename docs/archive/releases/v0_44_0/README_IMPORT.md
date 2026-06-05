# v0.44.0 README Import

Status: historical release packet after acceptance.
Release: **v0.44.0 / M40 - Context Handoff Approval, No Injection**.

v0.44.0 adds contract-only Context Handoff Approval for safe context proposals.
It validates exact proposal binding and returns review-only, no-injection
decision envelopes with safe-ref-only receipt plans.

## Boundaries

- exact proposal binding.
- review-only.
- no context injection.
- no OpenWebUI handoff execution.
- no model calls.
- no memory writes.
- no export.
- no execution.
- no raw file access.
- approval_ref alone is not authority.
- approval_test_ is not runtime authority.
- evaluator boundaries revalidate safety-critical fields.
- no backend routes.
- no frontend mutation controls.
- no dependencies.

M41 remains future.
