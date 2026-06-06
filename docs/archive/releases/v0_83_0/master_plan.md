# v0.83.0 Master Plan

Milestone: M79 - Plugin Install Review, Disabled by Default.

Scope:
- Add plugin install review contracts.
- Require exact approval binding to install review request, M78 manifest
  security decision, manifest ref, plugin ref, version pin, and actor.
- Require source package ref, provenance ref, static review, sandbox test plan,
  Tool Broker mapping, Event Ledger plan, version pin, revocation, receipt
  plans, tests, documentation, static verification, and Foundation Gate
  coverage.
- Keep plugin install disabled by default.

Non-goals:
- No plugin install.
- No plugin enablement.
- No plugin execution.
- No runtime import.
- No network access.
- No model/provider call.
- No browser automation.
- No shell execution.
- No mobile device access.
- No remote execution.
- No credentials or cookies.
- No raw manifest content.
- No raw package content.
- No raw prompt or raw provider payload.
- No backend route, Control Center control, dependency, M80 work, or production
  authority.
