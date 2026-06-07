# Foundation Gate Implementation Plan v0.93.0

v0.93.0 adds Foundation Gate coverage for M89 Emergency Stop + Process Kill
Safety.

The Skill Package Security Rule remains unchanged. All skills are untrusted packages by default.
Any future skill package must have a manifest, declared permissions,
source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping,
Event Ledger logging, version pinning, revocation/disable support,
and human approval for high-risk capabilities.

Gate coverage:

- M89 emergency stop/process kill safety contracts exist.
- M89 decisions bind exactly to M88 Mutating Command Proposal decisions.
- Safe target process ref and safe emergency scope ref are required.
- Receipt plans are safe summary only and safe refs only.
- No raw PID and no raw signal are stored.
- Evaluator boundaries revalidate safety-critical fields.
- No emergency stop execution, process kill, process signal, command execution,
  subprocess execution, shell execution, process spawn, filesystem mutation,
  network access, tool execution, browser automation, plugin execution, remote
  execution, model call, memory write, context injection, background worker,
  backend route, Control Center control, dependency, or production authority is
  added.
- M90 remains future.

## Skill Package Security Rule

Skill packages, plugin packages, and generated capability bundles are untrusted
until reviewed. They must not become runtime authority, execution authority,
provider authority, filesystem authority, network authority, plugin authority,
or production authority merely because they exist in the repository or are
referenced by a plan, roadmap, prompt, receipt, approval ref, model output, or
tool intent.
