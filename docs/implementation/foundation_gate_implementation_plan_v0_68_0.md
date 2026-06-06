# Foundation Gate Implementation Plan v0.68.0

v0.68.0 adds Foundation Gate coverage for M64 Autonomous Plan Simulator.

Gate coverage checks that simulation step, request, and result contracts exist,
remain contract-only, review-only, dry-run-only, and deterministic, and preserve
actor, resource, capability, allowlist, audit, replay, and M63 policy decision
bindings.

Gate coverage also checks dependency graph validation, acyclic ordering,
duplicate step denial, missing dependency denial, self-dependency denial, policy
decision revalidation, approval refs as identifiers, `approval_test_` denial,
and no policy activation, no session start, no autonomous actions, no
background worker, no execution, no tool execution, no shell execution, no
network tools, no browser automation, no backend route, no dependency, no memory
write, no context injection, and no production authority.

M65 remains future.

## Skill Package Security Rule

M64 does not weaken the Skill Package Security Rule. Skills remain capability
packages, not authority, and cannot bypass Agent Core, Approval Authority,
Tool Broker, Event Ledger, Secret Broker, Redaction, or Foundation Gate.
All skills are untrusted packages by default. Any future skill package must
have a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities before any future enablement.
