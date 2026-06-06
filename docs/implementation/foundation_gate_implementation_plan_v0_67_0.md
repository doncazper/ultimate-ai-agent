# Foundation Gate Implementation Plan v0.67.0

v0.67.0 adds Foundation Gate coverage for M63 Autonomy Policy Engine v1.

Gate coverage checks that policy rules and evaluation contracts exist, remain
contract-only and review-only, preserve actor-bound, resource-bound,
capability-bound, allowlist-bound, risk ceiling, duration ceiling, revocation,
and audit/replay requirements, and keep approval refs as identifiers.

Gate coverage also checks no policy activation, no session start, no autonomous
actions, no background worker, no execution, no tool execution, no shell
execution, no network tools, no browser automation, no backend route, no
dependency, no memory write, no context injection, and no production authority.

M64 remains future.

## Skill Package Security Rule

M63 does not weaken the Skill Package Security Rule. Skills remain capability
packages, not authority, and cannot bypass Agent Core, Approval Authority,
Tool Broker, Event Ledger, Secret Broker, Redaction, or Foundation Gate.
All skills are untrusted packages by default. Any future skill package must
have a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before any future enablement.
