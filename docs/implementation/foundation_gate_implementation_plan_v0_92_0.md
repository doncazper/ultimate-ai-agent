# Foundation Gate Implementation Plan v0.92.0

v0.92.0 adds M88 Mutating Command Proposal, No Execution coverage to the
Foundation Gate.

The Skill Package Security Rule remains unchanged. All skills are untrusted packages by default.
Any future skill package must have a manifest, declared permissions,
source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping,
Event Ledger logging, version pinning, revocation/disable support,
and human approval for high-risk capabilities.

The gate checks:

- M88 mutating command proposal contracts exist.
- Decisions are contract-only, proposal-only, review-only, deterministic,
  local-only, and safe refs only.
- Exact M87 sandboxed command audit replay binding is required.
- Safe mutation scope and safe argument refs are required.
- Receipt plans are safe summary only and safe refs only.
- Evaluator boundaries revalidate safety-critical fields.
- Command execution, subprocess execution, shell execution, process spawn,
  filesystem mutation, network access, tool execution, browser automation,
  plugin execution, remote execution, model call, memory write, context
  injection, background worker, backend route, Control Center control,
  dependency, and production authority are denied.
- M89 remains future.
