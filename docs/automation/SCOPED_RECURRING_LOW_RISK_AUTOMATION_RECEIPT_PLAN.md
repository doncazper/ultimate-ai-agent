# Scoped Recurring Low-Risk Automation Receipt Plan

M98 receipt plans store safe refs only. They may include request, actor, scope,
resource, workflow, action, cadence, approval bundle, renewal, expiration, audit,
revocation, and kill switch refs. They must not store raw payloads, raw prompts,
raw provider payloads, credentials, account data, or secret access material.

Receipt plans record no scheduler start, no background worker start, no
recurring execution runtime, no mutating task, no shell write, no network write,
no browser write, no silent background collection, no memory write, no context
injection, no export, and no side effects.

Evaluator boundaries revalidate receipt plans before accepting a decision for
review.

M99 remains future.
