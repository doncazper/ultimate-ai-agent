# MSG-MX-011 — Messenger Reliability And Security Hardening

Implement only Phase 10 hardening for the integrated Messenger work. Read
`AGENTS.md`, the complete design sources, accepted authority matrix, current
Messenger code/tests, release truth, performance budgets, migration/recovery
plans, accessibility rules, and security/redaction verifiers before editing.

## Branch Contract

- Fetch current `origin/main`, record its SHA, and create
  `codex/msg-mx-11-hardening` from that exact commit in an isolated worktree.
- Inspect open PRs/overlaps and preserve unrelated work. Never reset, revert,
  clean, stash, overwrite, force-push, or move historical tags.
- Prove MSG-MX-010 is merged and post-merge verified on the current
  `origin/main`; otherwise stop with an explicit blocked report.

Python Core remains authoritative and Control Center remains an operator shell.
Preserve API/CLI parity while repairing any operator-visible runtime behavior.

## Authority Preflight

This prompt grants no new runtime lane. Inventory the exact authorities already
accepted by prompts 04–10 and run only tests permitted by those current scopes.
If a test or repair would require an unaccepted network, credential, connector,
crypto, write, media, model, call, agent-participant, hosted, or federation lane,
stop that item with an explicit blocked report rather than expanding authority.

## Exact Milestone

Harden the implemented surface for:

- large-room performance, sync backpressure, bounded caches and queues;
- migration/version failure, multi-device conflict, rate limits, abuse and
  malicious events, retention/deletion, low disk, restart, and offline recovery;
- accessibility, keyboard/focus behavior, localization readiness, telemetry
  redaction, dependency/SBOM truth, rollback, and safe-disable drills;
- operator-readable failure, readiness, blocked, degraded, recovery, receipt,
  and evidence posture across API/CLI/macOS desktop.

Calls, agent room participants, hosted infrastructure, public federation, and
production deployment remain separate later lanes. Do not implement them.

Every repaired mutation must retain exact safe refs, redaction, idempotency,
content-free receipts, rollback or rollback-readiness, and safe-disable. Do not
weaken policy, approval, leases, budget, target validation, route classification,
OpenAPI, redaction, or Foundation Gate.

Immediately before every runtime call, including a read, test, interoperability
operation, cleanup, or repaired mutation, re-evaluate PolicyEngine; exact
LocalApprovalAuthority scope where required; the current exact AuthorityLease;
exact capability, adapter, provider, target, mission, and run; TTL/deadline;
budget; readiness; kill switch; safe-disable; and idempotency/replay posture.
Approval refs alone never authorize. Unknown, stale, expired, or mismatched
state fails closed before the call starts.

## Required Verification

Run focused performance/security/recovery/migration/accessibility/localization/
redaction tests and the bounded authorized local interoperability suite. Element
Desktop and external test accounts remain an external facility; report
`external_facility_required` rather than simulating unavailable evidence. Then
run:

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

Adversarially review denial-of-service, queue/cache escape, malicious events,
telemetry leaks, recovery data loss, migration rollback, stale capability truth,
misleading UI, and authority regressions. Fix all actionable findings. Commit
and push normally and open a draft PR. While it is draft, complete local review
and hardening. Mark it ready only after local checks pass; run only
repository-required GitHub-hosted CI on standard macOS runners, never paid
larger runners or self-hosted compute. Merge only when required checks are
green, update local `main` to the exact remote merge, run
post-merge verification, push verified `main`, and confirm a clean worktree. Do
not begin MSG-MX-012 before that proof.
The post-merge push must be a synchronization no-op: local `main` and
`origin/main` must resolve to the exact same merge SHA. If verification finds a
defect or divergence, use a new scoped branch and PR; never repair `main`
directly.

This milestone is desktop-only. Do not add, test, capture, or claim mobile
surfaces.

Final report: baseline SHA, hardening findings/fixes, measured budgets, drills,
blocked later lanes, verification, commit, pushed branch, and draft PR URL.
