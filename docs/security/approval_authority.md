# Approval Authority

Status: active
Current through: v0.32.0
Purpose: Summarize approval authority boundaries across local/dev and M28 policy contracts.

M8.5 introduces a local/dev approval authority bridge. It is a contract and policy boundary, not production user authentication.

v0.32.0 / M28 adds Approval Authority v2 + Action Policy Expansion as
policy-only and decision-only contracts. M28 approval decisions are not action
execution, tool execution, file mutation, memory writes, network calls,
model/provider calls, browser/mobile/remote/plugin execution, shell execution,
backend execution routes, Control Center execute controls, or production
authority.

## Guarantees

- Approval requests, grants, validation decisions, and receipts are typed Pydantic contracts.
- `LocalApprovalAuthority` stores approvals in memory only.
- Arbitrary strings are not authority.
- Unknown, expired, revoked, actor-mismatched, subject-mismatched, action-mismatched, resource-mismatched, and risk-mismatched approval refs are denied.
- Approval receipts are safe to show and must not contain raw secrets.
- M28 action policy decisions keep `execution_authorized=False` and `execution_performed=False`.
- M28 wildcard, expired, revoked, replayed, and mismatched grants are denied.

## Compatibility

`approval_test_` refs remain compatibility/test-only. They are not runtime
authority. M28 denies `approval_test_` refs and `approval_ref` alone as action
policy authority.

## Future Production Work

Production approval requires later user auth, session binding, UI, durable storage, audit history, revocation controls, and explicit policy for high-risk capabilities. M29-M40 remain planned/provisional.

## Non-Goals

This milestone does not add OAuth, production auth, provider calls, model calls, network calls, production persistence, or external actions.
