# MSG-MX-004 — Disposable Loopback Synapse Harness

Implement only Phase 3 of the Messenger Matrix plan. Read `AGENTS.md`, the full
design sources, accepted authority matrix, local service packaging, Docker/test-
harness conventions, redaction requirements, and current CI cost policy before
editing.

## Branch Contract

- Fetch current `origin/main`, record its SHA, and create
  `codex/msg-mx-04-local-synapse-harness` from that exact commit in an isolated
  worktree.
- Inspect overlaps and preserve unrelated work. Never reset, revert, clean,
  stash, overwrite, force-push, or alter historical tags.
- Prove MSG-MX-003 is merged and post-merge verified on the current
  `origin/main`; otherwise stop with an explicit blocked report.

Python Core remains authoritative and Control Center remains an operator shell.
Preserve API/CLI parity for every inspectable harness posture or command.

## Stage A — Exact Authority Acceptance

On this branch and PR, first implement and verify the exact loopback local-
network, pinned-container/dependency, and disposable test-harness authority
lanes. Bind them to the official digest-pinned Synapse image, allowlisted
loopback targets and ports, bounded lifetime and resources, disposable data, no
federation, and exact start/inspect/smoke/stop/reset commands. Define route side-
effect classes, API/CLI parity, safe refs, redaction, idempotency, content-free
receipts, cleanup/rollback, and safe-disable. Add adversarial tests for public
binding, target substitution, stale leases, retained data, and cleanup failure.

Review and verify Stage A locally before Stage B. Acceptance makes each lane
eligible for fresh request-scoped evaluation only; it does not grant standing
authority or make a harness globally enabled. If the exact authority cannot be
safely accepted, stop before Stage B with an explicit blocked report.

Immediately before every Stage B runtime call, including harness reads,
mutations, startup, shutdown, reset, and cleanup, re-evaluate PolicyEngine;
exact LocalApprovalAuthority scope where required; the current exact
AuthorityLease; exact capability, adapter, provider, target, mission, and run;
TTL/deadline; budget; readiness; kill switch; safe-disable; and
idempotency/replay posture. Approval refs alone never authorize. Unknown,
stale, expired, or mismatched state fails closed before the call starts.

## Stage B — Runtime Implementation

Add the opt-in, local-only development harness:

- pinned official Synapse image, loopback-only exposure, SQLite test storage,
  closed registration, no federation, bounded resource/lifetime limits;
- deterministic ephemeral accounts, rooms, Spaces, messages, relations, and
  unencrypted fixtures generated at runtime, never committed;
- explicit encryption metadata and placeholder states for later crypto tests;
  do not claim encrypted-message fixtures before MSG-MX-007 proves crypto;
- start, inspect, smoke-test, stop, and destructive reset/cleanup commands;
- Element Desktop interoperability checklist without bundling Element;
- explicit no-production warning, safe-disable, failure states, and full cleanup
  proof.

Use safe refs and synthetic test content. Do not add hosted infrastructure,
public exposure, production homeserver configuration, durable credentials, or
message fixtures.

Every harness mutation must be exact-scoped and define safe refs, redaction,
idempotency, content-free receipts for every mutation, rollback/cleanup, and
safe-disable.

## Required Verification

Run focused configuration/verifier tests and, only after authority preflight,
the bounded local create/smoke/cleanup cycle with post-cleanup proof. Also run:

```bash
.venv/bin/python -m ruff check .
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python scripts/run_foundation_gate.py --command-mode report-only --no-write-latest
git diff --check
```

Run frontend checks only if an existing harness-status surface changed.
Adversarially review for public binding, federation, retained volumes, secrets,
unsafe logs, unpinned images, paid services, and incomplete cleanup. Fix every
actionable finding. Commit and push normally and open a draft PR. While it is
draft, complete local review and hardening of both stages. Mark it ready only
after local checks pass; run only repository-scoped self-hosted macOS CI, never
paid or GitHub-hosted compute. Merge only when required checks are green, update
local `main` to the exact remote merge, run post-merge verification, push
verified `main`, and confirm a clean worktree. Do not begin MSG-MX-005 before
that proof.
The post-merge push must be a synchronization no-op: local `main` and
`origin/main` must resolve to the exact same merge SHA. If verification finds a
defect or divergence, use a new scoped branch and PR; never repair `main`
directly.

This milestone is desktop-only. Do not add, test, capture, or claim mobile
surfaces.

Final report: authority evidence refs, baseline SHA, lifecycle proof, residual
resources, verification, blockers, commit, pushed branch, and draft PR URL.
