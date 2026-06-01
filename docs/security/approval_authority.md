# Approval Authority

M8.5 introduces a local/dev approval authority bridge. It is a contract and policy boundary, not production user authentication.

## Guarantees

- Approval requests, grants, validation decisions, and receipts are typed Pydantic contracts.
- `LocalApprovalAuthority` stores approvals in memory only.
- Arbitrary strings are not authority.
- Unknown, expired, revoked, actor-mismatched, subject-mismatched, action-mismatched, resource-mismatched, and risk-mismatched approval refs are denied.
- Approval receipts are safe to show and must not contain raw secrets.

## Compatibility

`approval_test_` refs remain compatibility/test-only. They are accepted only through explicit local/test paths or authority fixtures and must not be treated as production approval.

## Future Production Work

Production approval requires later user auth, session binding, UI, durable storage, audit history, revocation controls, and explicit policy for high-risk capabilities.

## Non-Goals

This milestone does not add OAuth, production auth, provider calls, model calls, network calls, production persistence, or external actions.
