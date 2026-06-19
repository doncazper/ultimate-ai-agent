# Local Model Production Readiness Boundary

M166 supersedes the M120 no-authority readiness review only for the exact local
llama.cpp and OpenWebUI gateway scope established by M160-M165.

The production authority grant is not a route, deploy command, traffic switch,
OpenWebUI admin action, plugin installation, credential export, model download,
model selection change, or automatic runtime mutation. It is a typed release
gate decision over redacted evidence refs.

Required evidence remains local and bounded:

- live install/run tests must be loopback-only.
- OpenWebUI E2E tests must keep OpenWebUI as a shell, not the agent brain.
- security review must cover source, route, dependency, prompt, provider,
  credential, raw path, and log redaction.
- packaging must preserve reviewed dependency and artifact refs.
- operational rollback must prove previous-known-good restoration.
- load tests must use bounded localhost traffic and redacted metrics.

The gate is revocable, replay-safe, audit-bound, rollback-bound, exact-scope
bound, and blocker-bound.
