# Scoped Recurring Low-Risk Automation Policy

M98 policy allows low-risk read-only scoped recurrence for review only. Strict
cadence is required, approval renewal required, renewal expiry is enforced,
expiration required, stop conditions required, audit trail required, revocation
required, kill switch required, and safe refs only are required.

The policy denies scheduler behavior, background worker behavior, recurring
execution runtime, mutating tasks, credential or account actions, shell write,
network write, browser write, silent background collection, secret access,
memory write, context injection, export, backend route, Control Center control,
dependency changes, broad autonomy, and production authority.

Evaluator boundaries revalidate policy, request, decision, and receipt-plan
fields before a scoped recurring decision is accepted for review.

M99 remains future.
