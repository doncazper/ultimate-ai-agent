# Recurring Automation Renewal Policy

M97 recurring automation contracts require approval renewal before any future
recurring automation could be considered. Approval refs are identifiers only and
do not authorize recurring execution. `approval_test_*` refs are never runtime
authority.

Renewal metadata must be exact-scope, actor-bound, resource-bound,
non-transferable, expiring, revocable, auditable, and safe-ref-only. Missing
renewal or expiration metadata is denied.

M97 remains contract-only: no recurrence runtime, no background execution, no
cron, no daemon, no scheduler, no side effects, no backend route, no dependency,
and no production authority.

M98 remains future.
