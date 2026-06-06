# Foundation Gate Implementation Plan v0.61.0

v0.61.0 implements M57 Runtime Sandbox Architecture Review.

All skills are untrusted packages by default. Coverage continues the Skill
Package Security Rule language requiring a manifest, declared permissions,
source/provenance metadata, static review, sandbox test execution, Tool Broker
permission mapping, Event Ledger logging, version pinning, revocation/disable
support, and human approval for high-risk capabilities.

Foundation Gate coverage requires:

- deterministic local runtime sandbox architecture review contracts.
- policy validation for sandbox execution, subprocess execution, shell
  execution, process spawn, file mutation, network access, tool execution,
  browser automation, plugin execution, remote execution, model call, memory
  write, context injection, side effects, backend route, dependency, production
  authority, and M58 denial.
- OpenAPI route-boundary checks for no sandbox run/execute, subprocess,
  process-spawn, shell, context, memory, browser, plugin, or tool execution
  routes.
- documentation-integrity checks for M57 docs and M58 future status.

The Skill Package Security Rule, Tool Broker permission mapping, and
revocation/disable support remain unchanged by M57.
