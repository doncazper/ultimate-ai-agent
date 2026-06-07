# Recurring Automation Contracts

v1.1.0 / M97 adds Recurring Automation Contracts as contract-only, disabled by
default planning metadata. M97 defines cadence, exact scope, resource/action
binding, approval renewal, expiration, stop conditions, audit, revocation, and
receipt-plan refs for future recurring automation review.

M97 is not a recurrence runtime. It adds no recurrence runtime, no background
execution, no cron, no daemon, no scheduler, no side effects, no shell
execution, no network access, no browser automation, no plugin execution, no
memory write, no context injection, no backend route, no Control Center control,
no dependency, and no production authority.

Approval renewal required, expiration required, stop conditions required, audit
required, and revocation required are safety-critical contract fields.
Evaluator boundaries revalidate those fields so constructor validation alone is
not trusted.

M98 remains future.
