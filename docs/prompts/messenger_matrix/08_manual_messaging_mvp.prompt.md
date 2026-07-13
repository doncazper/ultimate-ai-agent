# MSG-MX-008 — Exact Human-Commanded Manual Messaging MVP

Implement only Phase 7 of the Messenger Matrix plan. Read `AGENTS.md`, the full
design sources, accepted authority matrix, session/sync/crypto contracts, exact
action/approval/lease patterns, dispatcher/idempotency/receipt conventions, and
desktop Messenger tests before editing.

## Branch Contract

- Fetch current `origin/main`, record its SHA, and create
  `codex/msg-mx-08-manual-messaging-mvp` from that exact commit in an isolated
  worktree.
- Inspect overlaps and preserve unrelated work. Never reset, revert, clean,
  stash, overwrite, force-push, or move historical tags.
- Prove MSG-MX-007 is merged and post-merge verified on the current
  `origin/main`; otherwise stop with an explicit blocked report.

Python Core remains authoritative and Control Center remains an operator shell.
Preserve API/CLI parity for every command, state transition, and receipt.

## Stage A — Exact Authority Acceptance

On this branch and PR, first implement and verify separate human-commanded send,
reply, thread, reaction, edit, redaction, typing, read-receipt, encrypted draft/
outbox persistence, outbox cleanup, and desktop-notification lanes. Bind exact
account, room, event or transaction, content fingerprint, draft/outbox record,
notification target, adapter, PolicyEngine decision, exact
LocalApprovalAuthority scope, current exact AuthorityLease, TTL/deadline,
budget, readiness, kill switch, safe-disable, idempotency, replay, rollback or
compensation, redaction, and content-free receipts. Add adversarial tests for
changed content/target, duplicate execution, stale approval, revoked lease,
cross-room replay, outbox-key failure, and notification substitution.

Review and verify Stage A locally before Stage B. Acceptance makes each lane
eligible for fresh request-scoped evaluation only; it does not grant standing
write authority, and an approval ref remains only an identifier. If exact
authority cannot be safely accepted, stop before Stage B with an explicit
blocked report.

Immediately before every Stage B runtime call, including outbox reads,
notifications, sends, retries, edits, reactions, redactions, and receipt writes,
re-evaluate PolicyEngine; exact LocalApprovalAuthority scope where required;
the current exact AuthorityLease; exact capability, adapter, provider, target,
mission, and run; TTL/deadline; budget; readiness; kill switch; safe-disable;
and idempotency/replay posture. Approval refs alone never authorize. Unknown,
stale, expired, or mismatched state fails closed before the call starts.

## Stage B — Runtime Implementation

Implement the human-commanded messaging MVP:

- stable transaction IDs; local echo; queued, sending, server-acknowledged,
  remote-echo, failed, retry, and discard states;
- replies, threads, reactions, edits, redactions, mentions, bounded formatting,
  drafts, typing settings, read-receipt settings, and desktop notifications;
- store pending drafts and outbox entries in a separate encrypted, TTL-bounded
  store with a distinct Keychain-backed key, exact account/room binding,
  migration/deletion/plaintext-scan proof, and no raw content in receipts;
- restart/offline recovery, deduplication, uncertain-result reconciliation,
  keyboard navigation, accessibility, and focus return;
- API/CLI/macOS desktop parity for exact command posture and content-free receipt
  inspection.

Opening a composer or pressing Retry never marks success; only bound adapter
evidence does. AI-generated or autonomous sends remain blocked.

Every mutation must use safe refs, redaction, exact idempotency, content-free
receipts, rollback or compensation readiness, and safe-disable, with authority
re-evaluated immediately before execution, including PolicyEngine, exact
LocalApprovalAuthority scope, the current exact AuthorityLease, adapter, target,
TTL/deadline, budget, readiness, and kill switch. Raw message bodies never enter
receipts, logs, evidence, telemetry, fixtures, or durable prompts.

## Required Verification

Run focused action/authority/idempotency/replay/restart/redaction/API/CLI/UI tests
and bounded local-Synapse integration. Element Desktop plus test accounts are an
external facility: run encrypted interoperability only when actually available
and authorized, and otherwise report `external_facility_required` without
simulating the gate. Then run:

```bash
.venv/bin/python -m ruff check .
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py tests/test_control_center_api_routes.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_frontend.py
make frontend-check
PYTHONPATH=src .venv/bin/python scripts/run_foundation_gate.py --command-mode report-only --no-write-latest
git diff --check
```

Adversarially review duplicate sends, changed target/content, approval-ref misuse,
revocation races, uncertain execution truth, redaction leaks, false success,
cross-room replay, and autonomous-send escalation. Fix all actionable findings.
Commit and push normally and open a draft PR. While it is draft, complete local
review and hardening of both stages. Mark it ready only after local checks pass;
run only repository-scoped self-hosted macOS CI, never paid or GitHub-hosted
compute. Merge only when required checks are green, update local `main` to the
exact remote merge, run post-merge verification, push verified `main`, and
confirm a clean worktree. Do not begin MSG-MX-009 before that proof.

This milestone is desktop-only. Do not add, test, capture, or claim mobile
surfaces.

Final report: accepted authority refs, exact command lanes, interoperability and
recovery evidence, blockers, commit, pushed branch, and draft PR URL.
