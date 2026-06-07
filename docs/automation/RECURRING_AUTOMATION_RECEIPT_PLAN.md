# Recurring Automation Receipt Plan

M97 receipt plans store safe refs only. They may include request, actor, scope,
resource, action, cadence, approval-renewal, expiration, audit, and revocation
refs.

Receipt plans store no raw payload and record no recurrence runtime,
background execution, cron, daemon, scheduler, recurring execution, side
effects, backend route, dependency, or production authority.

Receipt plans are audit metadata for contract review only. They are not
authority to start a worker, schedule a job, run a tool, write memory, inject
context, or perform production actions.

M98 remains future.
