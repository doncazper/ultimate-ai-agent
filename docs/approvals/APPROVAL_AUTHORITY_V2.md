# Approval Authority v2

Status: active
Current through: v0.32.0
Purpose: Define the M28 approval authority contract boundary.

v0.32.0 / M28 implements Approval Authority v2 + Action Policy Expansion as
contract/policy/decision only. Approval decisions are not action execution.

Approval Authority v2 provides typed contracts for:

- actor/action/resource/scope binding.
- approval grant status, expiry, revocation, and replay checks.
- approval and action policy decision envelopes.
- non-authoritative approval receipt plans.
- risk and side-effect policy decisions.

Approval Authority v2 does not add action execution, tool execution, file
mutation, memory writes, network calls, model/provider calls, browser
automation, mobile/device access, remote execution, plugin enablement, shell
execution, backend execution routes, Control Center execute controls,
dependencies, production authority, or M29 work.

In M28 there is no action execution, no tool execution, and no memory writes.

`approval_ref` values are identifiers only. `approval_ref` alone is not
authority. `approval_test_` refs are test-only and are not runtime authority.
`consent_ref` alone is not authority.

Wildcard approvals are denied. Expired, revoked, replayed, and mismatched grants
are denied. Raw action inputs and secret-like summaries or metadata are rejected.

M29-M40 remain planned/provisional.
