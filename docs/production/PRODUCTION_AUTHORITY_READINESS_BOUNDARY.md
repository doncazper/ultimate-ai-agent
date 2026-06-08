# Production Authority Readiness Boundary

The M120 boundary is contract-only and review-only. Production Authority
Readiness Review records may reference the M119 Production Red-Team Harness
through safe refs, but they cannot convert readiness status into authority.

Required bindings are actor-bound, baseline-bound,
source-production-red-team-harness-bound, user-bound, workspace-bound,
deployment-mode-bound, environment-bound, authority-tier-bound,
readiness-check-bound, launch-blocker-bound, rollback-readiness-bound, audit,
replay, and no-effect receipt plan.

The boundary denies production authority, production runtime, go-live,
production deployment, external distribution, traffic routing, credential
handling, network access, account action, model call, memory write, context
injection, execution, tool execution, shell execution, browser automation,
plugin execution, mobile sensor, backend route, Control Center control,
dependency, M121 work, beta release, and production authority.

M121 remains future. M150 remains the planned v1.0.0-alpha target.
