# v0.84.0 Master Plan

Milestone: M80 - Network/Browser/OpenWebUI Hardening Freeze.

Scope:

- Add freeze-only, review-only, deterministic M80 contracts.
- Require accepted milestone refs for M71-M79 and checklist refs.
- Deny unrestricted network access, authenticated network action, raw network
  response, browser navigation, browser click, browser screenshot, raw DOM, and
  authenticated browser profile.
- Deny OpenWebUI model authority, OpenWebUI tool execution, OpenWebUI memory
  write, OpenWebUI context injection, raw prompt, and raw provider payload.
- Deny plugin install, plugin enablement, plugin execution, runtime import,
  shell execution, background worker, backend route, Control Center control,
  dependency, and production authority.
- Add documentation-integrity checks, static verification, tests, and Foundation
  Gate coverage.

Non-goals:

- No runtime capability expansion.
- No backend route.
- No dependency.
- No M81 work.

M81 remains future as Runtime Sandbox Spec.
