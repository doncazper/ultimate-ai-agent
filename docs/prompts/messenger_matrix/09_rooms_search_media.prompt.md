# MSG-MX-009 — Rooms, Search, And Media

Implement only Phase 8 of the Messenger Matrix plan. Read `AGENTS.md`, the full
design sources, accepted authority matrix, manual messaging/runtime contracts,
room/power-level semantics, media threat model, encrypted-cache/search design,
and API/CLI/UI parity conventions before editing.

## Branch Contract

- Fetch current `origin/main`, record its SHA, and create
  `codex/msg-mx-09-rooms-search-media` from that exact commit in an isolated
  worktree.
- Inspect overlaps and preserve unrelated work. Never reset, revert, clean,
  stash, overwrite, force-push, or alter historical tags.
- Prove MSG-MX-008 is merged and post-merge verified on the current
  `origin/main`; otherwise stop with an explicit blocked report.

Python Core remains authoritative and Control Center remains an operator shell.
Preserve API/CLI parity for every exact room, search, and media capability.

## Stage A — Exact Authority Acceptance

On this branch and PR, first implement and verify separate DM, room, invite,
join/leave, role/power, Space, notification/history, pin/favorite, media upload,
authenticated download, filesystem materialization, quarantine, safe preview,
cleanup, and encrypted local-search lanes. Bind exact account, room, member,
media, filesystem root, target, PolicyEngine decision, exact
LocalApprovalAuthority scope, current exact AuthorityLease, budget, byte/type/
count limits, deadline, readiness, kill switch, safe-disable, idempotency,
rollback/compensation, redaction, and content-free receipts. Add adversarial
tests for power escalation, target/path substitution, symlink/FIFO/device paths,
archive traversal, decompression bombs, MIME confusion, quarantine bypass,
preview parser escape, cross-room search leakage, and incomplete cleanup.

Review and verify Stage A locally before Stage B. Acceptance makes each lane
eligible for fresh request-scoped evaluation only; it does not grant standing
room, media, filesystem, or search authority. If exact authority cannot be
safely accepted, stop before Stage B with an explicit blocked report.

Immediately before every Stage B runtime call, including encrypted search,
authenticated reads, room administration, transfer, quarantine, preview, and
cleanup, re-evaluate PolicyEngine; exact LocalApprovalAuthority scope where
required; the current exact AuthorityLease; exact capability, adapter,
provider, target, mission, and run; TTL/deadline; budget; readiness; kill
switch; safe-disable; and idempotency/replay posture. Approval refs alone never
authorize. Unknown, stale, expired, or mismatched state fails closed before the
call starts.

## Stage B — Runtime Implementation

Implement the Phase 8 feature set:

- exact-scoped start DM, create room, invite, join, leave, roles/power levels,
  notification/history settings, pins, favorites, low priority, and server-side
  Space mapping;
- room/global search with encrypted-room local-index and retention rules;
- bounded file/image upload and authenticated download with size/type limits,
  quarantine, progress, cancel, retry, safe preview, and cleanup;
- keep downloaded bytes in an exact app-owned root; reject symlinks, FIFOs,
  device files, traversal, ambiguous extensions, executable content, unsafe
  archives, and preview handlers outside the allowlist; quarantine before any
  preview and require content-free scan/cleanup receipts;
- API/CLI/macOS desktop parity with event/transaction refs, failure recovery,
  receipts, and explicit blocked states.

Multi-account remains deferred until single-account client/crypto isolation is
proven. Do not add calls, public federation operations, autonomous actions, or
unbounded downloads/uploads.

Every mutation requires safe refs, redaction, exact idempotency, content-free
receipts, rollback or rollback-readiness, and safe-disable, with immediate pre-
execution authority re-evaluation.

## Required Verification

Run focused room/power/search/index/media/quarantine/authority/redaction/API/CLI/
UI tests and bounded local-Synapse integration. Element Desktop plus test
accounts are an external facility: run interoperability only when actually
available and authorized, and otherwise report `external_facility_required`
without simulating the gate. Then run:

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

Adversarially review power escalation, invite/target substitution, path traversal,
malicious media, decompression bombs, cross-room search leaks, deleted-index
residue, duplicate mutations, incomplete cleanup, and false completion. Fix all
actionable findings. Commit and push normally and open a draft PR. While it is
draft, complete local review and hardening of both stages. Mark it ready only
after local checks pass; run only repository-scoped self-hosted macOS CI, never
paid or GitHub-hosted compute. Merge only when required checks are green, update
local `main` to the exact remote merge, run post-merge verification, push
verified `main`, and confirm a clean worktree. Do not begin MSG-MX-010 before
that proof.

This milestone is desktop-only. Do not add, test, capture, or claim mobile
surfaces.

Final report: accepted authority refs, lanes implemented, retention/quarantine
evidence, tests, blockers, commit, pushed branch, and draft PR URL.
