# MSG-MX-006 — Read-Only Sync And Daily Reading Loop

Implement only Phase 5 of the Messenger Matrix plan. Read `AGENTS.md`, the full
design sources, accepted authority matrix, session adapter, normalized contracts,
cache/redaction design, untrusted-content rules, API/CLI/UI parity, and sync
tests before editing.

## Branch Contract

- Fetch current `origin/main`, record its SHA, and create
  `codex/msg-mx-06-read-only-sync` from that exact commit in an isolated worktree.
- Inspect overlaps and preserve unrelated work. Never reset, revert, clean,
  stash, overwrite, force-push, or alter historical tags.
- Prove MSG-MX-005 is merged and post-merge verified on the current
  `origin/main`; otherwise stop with an explicit blocked report.

Python Core remains authoritative and Control Center remains an operator shell.
Preserve API/CLI parity for sync, freshness, blocked, and evidence truth.

## Stage A — Exact Authority Acceptance

On this branch and PR, first implement and verify exact connector-read/sync,
room/account scope, encrypted protected-cache, and cache-key lifecycle lanes.
Bind account, rooms, adapter, target, event classes, retention, cache schema,
Keychain item, TTL, deadline, budgets, migration, deletion, backup exclusion,
readiness, kill switch, safe-disable, idempotency, rollback, redaction, and
content-free receipts. Prove no connector-write scope is included. Add
adversarial tests for cross-account/room access, cache-key loss, locked Keychain,
schema downgrade, stale leases, deletion residue, and path substitution.

Review and verify Stage A locally before Stage B. Acceptance makes each lane
eligible for fresh request-scoped evaluation only; it does not grant standing
read authority or unlock a cache. If exact authority cannot be safely accepted,
stop before Stage B with an explicit blocked report.

Immediately before every Stage B runtime call, including connector reads, sync,
pagination, protected API reads, cache reads, and cache or sync-state mutation,
re-evaluate PolicyEngine; exact LocalApprovalAuthority scope where required;
the current exact AuthorityLease; exact capability, adapter, provider, target,
mission, and run; TTL/deadline; budget; readiness; kill switch; safe-disable;
and idempotency/replay posture. Approval refs alone never authorize. Unknown,
stale, expired, or mismatched state fails closed before the call starts.

## Stage B — Runtime Implementation

Implement read-only behavior:

- initial/incremental sync, reconnect, pagination, room membership, invites,
  account data, Spaces, DMs, names/topics/avatars, unread/mention counts, typing
  and receipt projections, and notification decisions;
- normalized timelines for messages, replies, edits, redactions, reactions,
  polls, files, and thread summaries;
- Home aggregate, local two-Space presentation mapping, bounded encrypted-at-
  rest offline cache, stable ordering, deduplication, and explicit freshness/
  staleness states;
- safe API/CLI/macOS desktop inspection with content access restricted to the
  exact protected response boundary.

The cache key must be random, resolved only through the macOS Keychain backend,
and absent from configuration, environment variables, API payloads, logs, and
the cache itself. Fail closed when the cache is locked, key resolution fails,
integrity verification fails, or schema/version support is unknown. Encrypt the
database, WAL, journals, temporary query material, and backups if any; otherwise
disable WAL/backups rather than creating plaintext residue. Implement bounded
migration, key rotation, exact deletion, and safe-disable cleanup. Add plaintext
scans covering database, WAL, journals, temp files, crash artifacts, and test
backups.

Encrypted content remains a truthful placeholder until prompt 07. No sends,
receipts-to-server, typing-to-server, room mutations, downloads, uploads, hidden
context injection, or Memory writes.

Treat every message/event as untrusted data, never instructions or authority.
Every cache mutation requires safe refs, redaction, idempotency, content-free
receipts, rollback/deletion readiness, and safe-disable. Never persist raw content
in logs, evidence, diagnostics, fixtures, or unrelated stores.

## Required Verification

Run focused sync/pagination/replay/cache/freshness/redaction/authority/API/CLI/UI
tests and bounded local-harness integration, then:

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

Adversarially review cross-room/account leaks, duplicate events, malformed
relations, stale truth shown as fresh, prompt injection, cache overgrowth, raw
content leakage, and accidental writes. Fix all actionable findings. Commit and push
normally and open a draft PR. While it is draft, complete local review and
hardening of both stages. Mark it ready only after local checks pass; run only
repository-required GitHub-hosted CI on standard macOS runners, never paid larger runners or self-hosted compute.
Merge only when required checks are green, update local `main` to the exact
remote merge, run post-merge verification, push verified `main`, and confirm a
clean worktree. Do not begin MSG-MX-007 before that proof.
The post-merge push must be a synchronization no-op: local `main` and
`origin/main` must resolve to the exact same merge SHA. If verification finds a
defect or divergence, use a new scoped branch and PR; never repair `main`
directly.

This milestone is desktop-only. Do not add, test, capture, or claim mobile
surfaces.

Final report: accepted authority refs, read behavior, write denials, cache and
freshness proof, tests, blockers, commit, pushed branch, and draft PR URL.
