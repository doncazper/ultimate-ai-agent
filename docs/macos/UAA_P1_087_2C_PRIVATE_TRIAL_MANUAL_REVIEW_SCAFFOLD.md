# UAA-P1-087.2c Private Trial Manual Review Scaffold

Status: implemented as an unanswered manual review intake scaffold.

UAA-P1-087.2c does not complete full UAA-P1-087.2. It extends the
UAA-P1-087.2a packet and UAA-P1-087.2b acceptance ledger with safe pending
question slots for a later local/private operator review. Every answer remains
`unanswered_pending_manual_review`; no accepted, revised, passed, or failed
manual-review findings are recorded by this milestone.

The scaffold is intentionally safe-ref-only. It records question refs, pending
answer refs, expected evidence refs, implementation prerequisite refs, deferred
decision refs, and blocked authority refs. It does not contain raw prompts,
responses, provider payloads, screenshots, OCR, local paths, log bodies,
usernames, hostnames, credentials, or private UI content.

## Scaffold

The canonical scaffold is:

```text
docs/macos/private_operator_trial_manual_review_scaffold_v1.json
```

It records:

- `manual_review_deferred_pending_implementation` review state;
- `unanswered_pending_manual_review` slots for Local Boot, Today, Actions,
  Memory, Evidence, Chat/Plans Handoff, blocked-state language, and CRM-lite
  follow-ups;
- pending answer refs for later manual review;
- missing Founder Loop implementation refs that should land before scoring;
- deferred decision refs for full UAA-P1-087.2, native boot cockpit work, and
  beta-readiness language;
- evidence refs for the scaffold and unanswered question posture;
- blocked authority refs.

The Control Center exposes these refs inside `/private-trial` as a read-only
operator surface. This route adds no backend endpoint, OpenAPI operation,
middleware, auth, CORS, security header, rate limit, connector behavior,
runtime model call, browser automation, shell authority, native app behavior,
memory write, action execution, Code apply, or provider authority.

## Full UAA-P1-087.2 Gate

Full UAA-P1-087.2 is deferred until more Founder Loop implementation exists and
a later local/private operator review records accepted or revised safe refs.
UAA-P1-087.2c is the intake scaffold for those later answers, not the answers
themselves.

Do not move to UAA-P1-087.3 as a product claim until full UAA-P1-087.2 records
accepted UI/copy tuning changes, manual smoke evidence refs, and remaining
blocker refs.

## Verification

Run:

```bash
.venv/bin/python scripts/verify_uaa_p1_087_2c_private_trial_manual_review_scaffold.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_p1_087_2c_private_trial_manual_review_scaffold.py
cd apps/control-center && npm test -- --run src/App.test.tsx
```
