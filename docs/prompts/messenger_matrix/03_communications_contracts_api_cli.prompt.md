# MSG-MX-003 — Communications Contracts, API, CLI, And Disabled Adapter

Implement only Phase 2 of the Messenger Matrix plan. Read `AGENTS.md`, the full
design sources, existing capability availability, provider registry, API
manifest, OpenAPI, route classification, CLI, redaction, receipt, and Control
Center client-generation patterns before editing.

## Branch Contract

- Fetch current `origin/main`, record its SHA, and create
  `codex/msg-mx-03-contracts-api-cli` from that exact commit in an isolated
  worktree.
- Inspect overlaps and preserve unrelated work. Never reset, revert, clean,
  stash, overwrite, force-push, or move historical tags.
- Prove MSG-MX-002 is merged and post-merge verified on the current
  `origin/main`; otherwise stop with an explicit blocked report.

Python Core remains authoritative and Control Center remains an operator shell.
Preserve human-readable API/CLI parity for every operator-relevant contract.

## Exact Milestone

Add canonical, backend-owned, normalized contracts without live Matrix runtime:

- Python `CommunicationsService` and provider registry;
- typed accounts, conversations, events, members, attachments, pagination,
  freshness, security posture, action envelope, room AI policy, safe refs,
  redaction posture, and content-free receipts;
- read-only API and human-readable CLI inspection parity for provider/session
  posture, rooms, failed-send posture, security, and receipt refs;
- stable OpenAPI operation IDs, API manifest declarations, route side-effect
  classification, bounded responses, and TypeScript bindings;
- a disabled Matrix adapter shell with explicit unsupported/configuration/
  authority-blocked states.

Do not install a Matrix dependency, call a network, authenticate an account,
read or send a message, persist raw content, or expose mutating routes. Do not
create a competing capability registry.

## Fail-Closed Authority Rule

This milestone grants no Matrix runtime authority. If any inspection contract
cannot be implemented without a live provider or account, represent its truth as
unknown/blocked and use deterministic injected fixtures in tests. Stop if scope
would require network, credential, connector-read/write, crypto, or media
authority, and produce an explicit blocked report.

Every proposed mutation contract must already define exact safe refs, redaction,
request-bound idempotency, content-free receipts, rollback or rollback-readiness,
and safe-disable. Approval refs alone authorize nothing.

## Required Verification

Run focused service/model/CLI/API/OpenAPI/route/redaction tests, TypeScript client
tests, and applicable frontend checks plus:

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

Adversarially review for raw payload leakage, callable disabled adapters,
unclassified routes, API/CLI drift, global authorization booleans, unsafe refs,
and product overclaims. Fix all actionable findings. Commit and push normally
and open a draft PR. While it is draft, complete local review and hardening. Mark
it ready only after local checks pass; run only repository-scoped self-hosted
macOS CI, never paid or GitHub-hosted compute. Merge only when required checks
are green, update local `main` to the exact remote merge, run post-merge
verification, push verified `main`, and confirm a clean worktree. Do not begin
MSG-MX-004 before that proof.

This milestone is desktop-only. Do not add, test, capture, or claim mobile
surfaces.

Final report: baseline SHA, contracts and surfaces added, blocked adapter truth,
verification, commit, pushed branch, and draft PR URL.
