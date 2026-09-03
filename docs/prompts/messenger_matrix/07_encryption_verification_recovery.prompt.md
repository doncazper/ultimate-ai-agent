# MSG-MX-007 — Encryption, Verification, Backup, And Recovery

Implement only Phase 6 of the Messenger Matrix plan. Read `AGENTS.md`, the full
design sources, accepted authority matrix, current Matrix SDK/CryptoApi guidance,
credential boundary, cache/backup design, recovery threat model, redaction
rules, and interoperability tests before editing.

## Branch Contract

- Fetch current `origin/main`, record its SHA, and create
  `codex/msg-mx-07-encryption-recovery` from that exact commit in an isolated
  worktree.
- Inspect overlaps and preserve unrelated work. Never reset, revert, clean,
  stash, overwrite, force-push, or modify historical tags.
- Prove MSG-MX-006 is merged and post-merge verified on the current
  `origin/main`; otherwise stop with an explicit blocked report.

Python Core remains authoritative and Control Center remains an operator shell.
Preserve API/CLI parity for security posture and every exact recovery command.

## Stage A — Exact Authority Acceptance

On this branch and PR, first implement and verify separately scoped persistent
crypto-store, credential/key lifecycle, device verification, cross-signing,
secure backup, restore, recovery, and destructive crypto-reset lanes for the
exact account, device, adapter, store, and recovery target. Bind PolicyEngine,
exact LocalApprovalAuthority scope, current exact AuthorityLease, target, TTL,
deadline, budget, readiness, kill switch, safe-disable, idempotency, replay,
irreversibility/rollback posture, redaction, and content-free receipts. Add
adversarial tests for key substitution, device confusion, stale verification,
backup rollback, recovery replay, destructive-reset mismatch, and secret leaks.

Review and verify Stage A locally before Stage B. Acceptance makes each lane
eligible for fresh request-scoped evaluation only; it does not grant standing
crypto authority or trust any device. If exact authority cannot be safely
accepted, stop before Stage B with an explicit blocked report.

Immediately before every Stage B runtime call, including crypto-store reads,
verification, backup, recovery, key lifecycle, and destructive reset,
re-evaluate PolicyEngine; exact LocalApprovalAuthority scope where required;
the current exact AuthorityLease; exact capability, adapter, provider, target,
mission, and run; TTL/deadline; budget; readiness; kill switch; safe-disable;
and idempotency/replay posture. Approval refs alone never authorize. Unknown,
stale, expired, or mismatched state fails closed before the call starts.

## Stage B — Runtime Implementation

Implement current Rust crypto through the approved Matrix SDK boundary:

- crypto initialization and single-owner persistent store;
- secret-storage callbacks, device trust, verification requests, cross-signing,
  backup status, restore progress, key requests, and typed decryption failures;
- one-time protected recovery-key display and destructive-reset consequence
  review;
- session verification, recovery drills, lost-key and undecryptable-event UI;
- Element-to-UAA encrypted-message interoperability and clean-reinstall restore.

Do not use legacy crypto APIs. Recovery material must never enter screenshots,
clipboard persistence, analytics, logs, receipts, API payloads, fixtures, or
durable prompts.

Every crypto mutation requires exact safe refs, redaction, idempotency, content-
free receipts, rollback or explicit irreversibility warning, recovery readiness,
and safe-disable. Re-evaluate authority immediately before mutation.

## Required Verification

Run focused crypto/store/verification/backup/recovery/redaction/authority tests
and bounded local-Synapse integration. Element Desktop plus separately managed
test accounts/devices are an external facility: run interoperability only when
they are actually available and authorized. Never simulate, weaken, or mark that
gate green from fixtures; report it as `external_facility_required` otherwise.
Then run:

```bash
.venv/bin/python -m ruff check .
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py tests/test_control_center_api_routes.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_frontend.py
make frontend-check
.venv/bin/python -I -B -S scripts/run_foundation_gate.py --command-mode report-only --no-write-latest
git diff --check
```

Adversarially review key/recovery leakage, store sharing, unverified-device trust,
backup rollback, reset confusion, malicious encrypted events, migration failure,
and false decryption success. Fix all actionable findings. Commit and push
normally and open a draft PR. While it is draft, complete local review and
hardening of both stages. Mark it ready only after local checks pass; run only
repository-required GitHub-hosted CI on standard macOS runners, never paid larger runners or self-hosted compute.
Merge only when required checks are green, update local `main` to the exact
remote merge, run post-merge verification, push verified `main`, and confirm a
clean worktree. Do not begin MSG-MX-008 before that proof.
The post-merge push must be a synchronization no-op: local `main` and
`origin/main` must resolve to the exact same merge SHA. If verification finds a
defect or divergence, use a new scoped branch and PR; never repair `main`
directly.

This milestone is desktop-only. Do not add, test, capture, or claim mobile
surfaces.

Final report: accepted authority refs, crypto/recovery evidence, irreversible
operations, test outcomes, blockers, commit, pushed branch, and draft PR URL.
