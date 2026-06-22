# UAA-P1-087.2b Private Trial Findings Capture And Acceptance Ledger

Status: implemented as an incremental acceptance ledger and manual smoke
runbook surface for local/private operator review.

UAA-P1-087.2b does not complete full UAA-P1-087.2. It turns the UAA-P1-087.2a
packet into review-ready acceptance refs so a local/private operator can record
accepted or revised findings later without granting runtime authority now.

The ledger is intentionally safe-ref-only. It records pending surface reviews,
manual smoke step refs, acceptance question refs, tuning decision refs, evidence
refs, and blocked authority refs. It does not contain raw prompts, responses,
provider payloads, screenshots, OCR, local paths, log bodies, usernames,
hostnames, credentials, or private UI content.

## Ledger

The canonical ledger is:

```text
docs/macos/private_operator_trial_acceptance_ledger_v1.json
```

It records:

- `operator_review_ready` trial state;
- `pending_operator_review` surface review refs for Local Boot, Today, Actions,
  Memory, Evidence, Chat/Plans Handoff, blocked-state language, and CRM-lite
  follow-ups;
- manual smoke step refs;
- acceptance question refs;
- pending tuning decision refs;
- evidence refs for the ledger, runbook, and pending operator findings;
- blocked authority refs.

The Control Center exposes these refs inside `/private-trial` as a read-only
operator surface. This route adds no backend endpoint, OpenAPI operation,
middleware, auth, CORS, security header, rate limit, connector behavior,
runtime model call, browser automation, shell authority, native app behavior,
memory write, action execution, Code apply, or provider authority.

## Full UAA-P1-087.2 Gate

Full UAA-P1-087.2 remains planned until the local/private operator review
records accepted or revised findings. UAA-P1-087.2b is the review ledger that
makes those findings collectable; it is not the finding itself.

Do not move to UAA-P1-087.3 as a product claim until full UAA-P1-087.2 records
accepted UI/copy tuning changes, manual smoke evidence refs, and remaining
blocker refs.

## Verification

Run:

```bash
.venv/bin/python scripts/verify_uaa_p1_087_2b_private_trial_acceptance_ledger.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_p1_087_2b_private_trial_acceptance_ledger.py
cd apps/control-center && npm test -- --run src/App.test.tsx
```
