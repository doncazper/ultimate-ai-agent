# Connector Safety Freeze Policy

The M130 policy requires:

- contract-only, review-only, freeze-only, deterministic, local-only operation
- safe refs only and safe summaries only
- exact M129 Connector Audit + Revocation Hardening binding
- accepted checkpoint refs for M121 through M129
- audit ref, replay ref, revocation ref, kill-switch ref, safety checklist ref,
  and no-effect receipt plan ref
- M131 remains future

The policy denies live connector runtime, account auth, network access,
credential handling, raw connector content, full content read, connector write,
connector send, connector delete, connector export, connector bulk export,
attachment download, audit export, revocation execution, kill-switch execution,
approval revocation, connector session stop, background workers, schedulers,
external services, model calls, memory writes, context injection, backend
routes, Control Center controls, dependencies, beta release, and production
authority.
