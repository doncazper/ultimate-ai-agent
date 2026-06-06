# Foundation Gate Implementation Plan v0.85.0

v0.85.0 adds Foundation Gate coverage for M81 Runtime Sandbox Spec.

Gate coverage:

- M81 runtime sandbox spec contracts exist and build a spec-only, review-only,
  deterministic, local-only report.
- Prior milestone refs for M57, M58, and M80 are required.
- Boundary refs, threat model refs, and audit requirement refs are validated.
- Runtime sandbox execution, command proposal, command execution, subprocess
  execution, shell execution, process spawn, filesystem mutation, network
  access, tool execution, browser automation, plugin execution, remote
  execution, model call, memory write, context injection, background worker,
  backend route, Control Center control, dependency, and production authority
  flags are denied.
- Evaluator boundaries revalidate model-copy mutated fields.
- Static safety checks deny runtime sandbox execution, command proposal,
  command execution, shell execution, process spawn, backend route, dependency,
  background worker, and production authority fragments.
- OpenAPI remains at 75 paths and forbidden sandbox, command, shell, process,
  filesystem, network, browser, plugin, remote, memory, context, and tool
  routes are absent.
- M82 remains future.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill or plugin-related
package review requires a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

M81 does not install, enable, execute, import, or trust any skill package,
plugin package, OpenWebUI tool, browser tool, network tool, shell tool, command
tool, runtime sandbox, or external package runtime.
