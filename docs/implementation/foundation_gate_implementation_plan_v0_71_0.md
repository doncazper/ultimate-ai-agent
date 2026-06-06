# Foundation Gate Implementation Plan v0.71.0

v0.71.0 adds Foundation Gate coverage for M67 Revocation + Kill Switch.

Gate coverage verifies:

- revocation and kill-switch contracts exist.
- records are contract-only and review-only.
- records are exact-bound to scoped approval bundles.
- revocation requested and kill-switch requested are review states only.
- approval refs are identifiers.
- records are actor-bound, resource-bound, capability-bound, allowlist-bound,
  non-transferable, and replay-safe.
- scoped approval bundles are revalidated at evaluator boundaries.
- `approval_test_` refs are denied.
- revocation action, kill-switch activation, session stop, process kill,
  execution, memory write, context injection, model/provider authority, and
  side effects are denied.
- backend revocation, kill-switch, session-stop, process-kill, autonomy
  activation, context, memory, tool, shell, browser, plugin, background, and
  execution routes are absent.
- M68 remains future.

M67 adds no revocation action, kill-switch activation, session stop, process
kill, policy activation, session start, autonomous actions, background worker,
execution, tool execution, shell execution, network tools, browser automation,
plugin execution, mobile sensor access, remote execution, memory write, context
injection, model/provider authority, backend routes, Control Center controls,
dependencies, or production authority.

## Skill Package Security Rule

M67 does not weaken the Skill Package Security Rule. Skills remain capability
packages, not authority, and cannot bypass Agent Core, Approval Authority,
Tool Broker, Event Ledger, Secret Broker, Redaction, or Foundation Gate.
All skills are untrusted packages by default. Any future skill package must
have a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before any future enablement.
