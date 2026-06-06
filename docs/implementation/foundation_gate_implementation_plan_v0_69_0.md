# Foundation Gate Implementation Plan v0.69.0

v0.69.0 adds Foundation Gate coverage for M65 Autonomy Audit + Replay Viewer.

Gate coverage checks that autonomy audit replay view contracts exist, remain
contract-only, review-only, replay-view-only, and deterministic, and preserve
exact simulation result, simulation request, policy decision, actor, audit,
replay, and exact replay step bindings.

Gate coverage also checks replay step mismatch denial, forged replay step
denial, `approval_test_` denial, secret-like metadata denial, evaluator
revalidation of mutated M64 simulation results, and no policy activation, no
session start, no autonomous actions, no background worker, no execution, no
tool execution, no shell execution, no network tools, no browser automation, no
backend route, no dependency, no memory write, no context injection, and no
production authority.

M66 remains future.

## Skill Package Security Rule

M65 does not weaken the Skill Package Security Rule. Skills remain capability
packages, not authority, and cannot bypass Agent Core, Approval Authority,
Tool Broker, Event Ledger, Secret Broker, Redaction, or Foundation Gate.
All skills are untrusted packages by default. Any future skill package must
have a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities before any future enablement.
