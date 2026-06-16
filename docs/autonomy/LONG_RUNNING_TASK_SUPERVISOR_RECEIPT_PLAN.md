# Long-Running Task Supervisor Receipt Plan

M133 receipt plans are no-effect receipts. They store safe summaries and safe
refs only.

The receipt plan may reference the supervisor ref, scope ref, M132 trusted
workflow decision ref, M131 scoped work-session decision ref, supervisor plan
ref, task ref, run state ref, heartbeat plan ref, checkpoint plan ref, context
budget ref, audit ref, replay ref, revocation ref, and kill-switch ref.

The receipt plan must not store raw prompts, raw provider payloads, secrets,
raw task payloads, raw runtime output, raw checkpoint payloads, or raw
heartbeat payloads.

The receipt plan must also record no supervisor start, no supervisor runtime,
no heartbeat monitor, no checkpoint scheduler, no resume execution, no recovery
execution, no task execution, and no side effects.
