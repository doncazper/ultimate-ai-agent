# Q30 Social Publishing Proposal And Dry-Run Acceptance Matrix

Status: accepted for the bounded local proposal/dry-run tier on 2026-08-26.

This matrix freezes the finite Q30 acceptance boundary. It proves that an
operator can inspect a content-free synthetic draft, three platform variants,
compatibility findings, an exact review plan, independent simulated outcomes,
and safe retry/reconciliation posture through Python Core, CLI, a GET-only API,
and readable Control Center UI. It does not accept or imply live publishing.

The founder accepted the displayed surface direction for private dogfooding.
Visual details remain intentionally revisable after use; later polish does not
invalidate this contract unless it changes the nouns, safety posture, route
authority, or exact plan/receipt semantics below.

## Accepted Checks

| Check | Accepted evidence | Frozen result |
|---|---|---|
| Canonical identity | Draft, media, variant, target, plan, and payload fingerprint refs are deterministic and content-free. | Pass |
| Platform inventory | Exactly Instagram, X, and TikTok fixture capabilities and variants are present. | Pass |
| Rights posture | Every admitted fixture variant has `verified_fixture` rights; missing or unknown rights block compatibility. | Pass |
| Compatibility | Deterministic info/warning findings render; blocking or unknown findings cannot enter the admitted plan. | Pass |
| Exact review binding | The dry-run envelope binds plan fingerprint, every target, every payload fingerprint, decision, and expiry. | Pass |
| Mixed settlement | Independent simulated child outcomes preserve known successes and expose eligible failures. | Pass |
| Successful-child retry | A succeeded child can never become retry eligible. | Pass |
| Failed-only retry | Only explicitly eligible failures enter a new retry plan, and the retry requires new exact review. | Pass |
| Unknown settlement | An unknown child requires reconciliation and cannot be blindly retried; an unmatched reconciliation requires new approval. | Pass |
| Exact replay | Repeating the same request returns the same result as a replay; conflicting idempotency reuse fails closed. | Pass |
| Concurrent exact replay | Eight simultaneous identical dry-runs produce one owner result and seven replays with one result ref. | Pass |
| Redaction | Raw post bodies, credentials, account data, local paths, secrets, and provider payloads are absent from fixtures, receipts, API data, UI, and docs. | Pass |
| GET-only API | `GET /control-center/social-publishing/proposal` is protected, `local_readonly`, and `validation_only`; the path exposes no mutation method. | Pass |
| CLI/API parity | The CLI inspects, validates, prepares exact dry-run review, simulates settlement, and reconciles; the API exposes the same backend-owned proposal truth for readable UI. | Pass |
| Readable Studio UI | Studio shows three platform cards, rights, capability limits, findings, plan fingerprint, blocked authorities, and next safe action without raw JSON. | Pass |
| No execution handler | The Control Center has no Publish control, no social mutation route, and no adapter invocation handler. | Pass |
| No live publishing authority | Account, credential, network, provider SDK, scheduler, platform write, publishing, external write, and production authority remain false. | Pass |

## Accepted Product Tier

Q30 is complete only as a local, private, synthetic proposal and deterministic
dry-run workflow. This is enough to use the surface, learn from actual operator
interaction, and revise layout or copy later without holding the queue open.

Any later live lane must be a new, separately accepted scope for exactly one
platform and operation, with enrolled credentials, test-account evidence,
current platform terms and capabilities, PolicyEngine and
LocalApprovalAuthority binding, explicit idempotency, correction and
reconciliation, safe-disable, redacted receipts, rollback posture, and exact
operator-present authority. Q30 itself grants none of those capabilities.

## Verification

- `scripts/verify_social_publishing_q30.py`
- `tests/test_social_publishing_q30.py`
- `tests/test_control_center_api_routes.py`
- `apps/control-center/src/api/client.summaryEndpoints.test.ts`
- `apps/control-center/src/northstar/NorthStarControlCenter.test.tsx`
- `scripts/verify_openapi_contract.py`
