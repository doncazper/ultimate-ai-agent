# Foundation Gate Implementation Plan v0.66.0

Status: M62 Scoped Autonomy Session Contracts.

M62 extends the Foundation Gate with contract, static safety, route-boundary,
and roadmap-currentness checks for scoped autonomy session contracts.

Gate coverage verifies:

- scoped autonomy session contracts exist
- session scopes are actor-bound, resource-bound, duration-bound, and
  allowlist-bound
- revocation and audit/replay refs are required
- review-only decisions perform no side effects
- approval refs and approval_test_* refs cannot authorize session start
- session start and activation are denied
- autonomous actions, background workers, execution, tool execution, shell
  execution, network tools, browser automation, backend routes, dependencies,
  and production authority remain denied
- M63 remains future

## Skill Package Security Rule

M62 does not weaken the Skill Package Security Rule. Skills remain capability
packages, not authority, and cannot bypass Agent Core, Approval Authority,
Tool Broker, Event Ledger, Secret Broker, Redaction, or Foundation Gate.
All skills are untrusted packages by default. Any future skill package must
have a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before any future enablement.
