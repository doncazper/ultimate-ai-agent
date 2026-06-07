# Scoped Recurring Low-Risk Automation

v1.2.0 / M98 adds Scoped Recurring Low-Risk Automation as review-ready
contracts for low-risk read-only recurrence. M98 requires exact scope, actor,
resource, workflow, approval bundle, renewal, expiration, stop condition, audit,
revocation, and kill switch refs before any scoped recurrence can be considered.

M98 is not a scheduler and not a background worker. It adds no recurring
execution runtime, no mutating tasks, no credential or account actions, no shell
write, no network write, no browser write, no silent background collection, no
secret access, no memory write, no context injection, no export, no backend
route, no dependency, no production authority, and no M99 work.

Evaluator boundaries revalidate safety-critical fields, including model-copy
mutations, before decisions are valid for review.

M99 remains future.
