# Foundation Gate Implementation Plan v0.70.0

v0.70.0 adds Foundation Gate coverage for M66 Scoped Approval Bundles.

Gate coverage verifies:

- scoped approval bundle contracts exist.
- scoped approval bundles are contract-only and review-only.
- approval refs are identifiers.
- bundles are exact-scope, actor-bound, resource-bound, capability-bound,
  allowlist-bound, non-transferable, revocable, and replay-safe.
- duplicate, test, revoked, expired, and replay-used bundles are denied.
- source scope and audit replay view fields are revalidated at evaluator
  boundaries.
- backend approval-bundle, autonomy activation, context, memory, tool, shell,
  browser, plugin, background, and execution routes are absent.
- M67 remains future.

M66 adds no policy activation, session start, autonomous actions, background
worker, execution, tool execution, shell execution, network tools, browser
automation, plugin execution, mobile sensor access, remote execution, memory
write, context injection, model/provider authority, backend routes, Control
Center controls, dependencies, or production authority.

## Skill Package Security Rule

M66 does not weaken the Skill Package Security Rule. Skills remain capability
packages, not authority, and cannot bypass Agent Core, Approval Authority,
Tool Broker, Event Ledger, Secret Broker, Redaction, or Foundation Gate.
All skills are untrusted packages by default. Any future skill package must
have a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before any future enablement.
