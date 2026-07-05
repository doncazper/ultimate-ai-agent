# Phase 11: CRM AI Proposal Layer

Branch: `codex/crm-11-ai-proposal-layer`

Commit: `Add CRM AI proposal layer`

Goal: Use existing governed local RuntimeGateway/provider-preview posture only
if available to produce proposal-only CRM intelligence.

Proposal types:

- contact summary
- next-best-follow-up
- relationship risk
- stale promise explanation
- draft message
- smart list reason
- opportunity update proposal

Rules:

- Model output is proposal only.
- No hidden context injection.
- No raw prompt/response/provider payload persistence.
- No provider calls unless an exact existing governed lane permits it.
- If model authority is unavailable, implement deterministic proposal fixtures
  visibly labeled non-authoritative.

Tests:

- proposal-only posture.
- no model output authority.
- blocked provider fallback.
- proof refs.
- no raw model payload persistence.

Verification:

- focused tests
- product truth verifier
- operational maturity verifier
- `git diff --check`
