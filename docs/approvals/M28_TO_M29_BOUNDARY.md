# M28 to M29 Boundary

Status: active
Current through: v0.33.1
Purpose: Keep M28 approval policy separate from future milestones.

v0.32.0 / M28 implements Approval Authority v2 + Action Policy Expansion as
policy-only, contract-only, and decision-only.

M28 adds:

- actor/action/resource/scope binding contracts.
- approval grant expiry, revocation, and replay protection.
- approval_ref-not-authority and approval_test_-not-authority denial.
- consent_ref-not-authority denial.
- wildcard approval denial.
- action risk and side-effect policy.
- action policy decision envelopes.
- non-authoritative approval receipt plans.
- tests, docs, static verifier coverage, and Foundation Gate coverage.

M28 does not add action execution, tool execution, shell execution, file
mutation, memory writes, Event Ledger mutation, network calls, model/provider
calls, browser/mobile/remote/plugin execution, backend execution routes, Control
Center execute controls, dependencies, production authority, or M29 work.

v0.33.0 implements M29 Agent Task Planning Engine as deterministic, local,
non-executing, review-only planning contracts. v0.33.1 hardens M29 dependency
graph, derived risk, hidden side-effect, authority-boundary, evaluator
revalidation, and no-execution coverage. M30 Multi-Step Execution Framework is
implemented/released by v0.34.0 as deterministic, local, state-machine-only
contracts. M31-M40 remain planned/provisional. Future milestones must not treat M28 policy decisions,
approval refs, consent refs, memory refs, model output, context packs, or tool
intents as execution authority.
