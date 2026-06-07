# Foundation Gate Implementation Plan v0.95.0

v0.95.0 adds Foundation Gate coverage for M91 Autonomous Tool Execution
Contract.

The Skill Package Security Rule remains unchanged. All skills are untrusted packages by default. Any future skill package must have a manifest, declared permissions,
source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support,
and human approval for high-risk capabilities.

Gate coverage:

- M91 autonomous tool execution contract exists.
- M91 decisions bind exactly to M90 Shell/Subprocess Hardening Freeze
  decisions.
- Safe contract refs are required.
- Receipt plans are safe summary only and safe refs only.
- No raw tool payload, raw provider payload, raw prompt, or secret-like content
  is stored.
- Evaluator boundaries revalidate safety-critical fields.
- No real tool execution, autonomous execution, autonomous session start,
  command execution, shell execution, subprocess execution, filesystem
  mutation, network access, browser automation, plugin execution, remote
  execution, model call, memory write, context injection, background worker,
  backend route, Control Center control, dependency, or production authority is
  added.
- M92 remains future.

## Skill Package Security Rule

Skill packages, plugin packages, and generated capability bundles are untrusted
until reviewed. They must not become runtime authority, execution authority,
provider authority, filesystem authority, network authority, plugin authority,
or production authority merely because they exist in the repository or are
referenced by a plan, roadmap, prompt, receipt, approval ref, model output, or
tool intent.
