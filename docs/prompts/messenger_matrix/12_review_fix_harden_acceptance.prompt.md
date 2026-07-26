# MSG-MX-012 — Integrated Review, Repair, And Acceptance Packet

Review the integrated Messenger Matrix implementation and produce the finite
acceptance packet. Read `AGENTS.md`, both complete design sources, every merged
MSG-MX PR, the accepted authority matrix, release/product truth, route/OpenAPI
inventory, and all Messenger tests/verifiers before editing.

## Branch Contract

- Fetch current `origin/main`, record its SHA, and create
  `codex/msg-mx-12-acceptance` from that exact commit in an isolated worktree.
- Inventory all open PRs and overlaps. Preserve unrelated work. Never reset,
  revert, clean, stash, overwrite, force-push, or modify historical tags.
- Prove MSG-MX-011 is merged and post-merge verified on the current
  `origin/main`; otherwise stop with an explicit blocked report.

Python Core remains authoritative and Control Center remains an operator shell.
Require API/CLI/macOS desktop parity for every accepted operator capability.

## Authority Preflight

This prompt grants no new runtime authority. Reconcile every implemented lane
with its current exact accepted authority before testing it. If any acceptance
scenario requires a missing, expired, unknown, or stale network, credential,
connector-read/write, crypto, media, model, room, or recovery lane, record that
scenario in an explicit blocked report and do not execute it or claim it passed.

## Exact Milestone

Perform one bounded integrated review and at most two focused repair passes:

- verify current code/test/operator evidence for every `MSG-MX-000` through
  `MSG-MX-012` board item and every `COMMS-MX-01` through `COMMS-MX-15` surface;
- fix safe in-scope defects without adding a new capability lane;
- run the complete authorized Messenger and Synapse suite, including restart,
  offline, rate-limit, revocation, decryption, backup, retry, duplicate,
  malicious-event, redaction, rollback, and safe-disable cases;
- run Element interoperability only when Element Desktop and the required test
  accounts/devices are genuinely available; otherwise record
  `external_facility_required` and never simulate acceptance evidence;
- reconcile API, CLI, macOS desktop, manifest, OpenAPI, route classification,
  documentation, and product truth;
- publish a redacted acceptance packet separating implemented, partial, blocked,
  unsupported, configuration-required, and external-facility-required states.

Do not claim public release, production authority, universal homeserver support,
hosted infrastructure, calling, agent participation, autonomous send, automatic
Memory truth, or any scenario lacking runtime evidence.

Every repair to a mutation must preserve exact safe refs, redaction, idempotency,
content-free receipts, rollback or rollback-readiness, and safe-disable. Evidence
must never contain raw messages, tokens, keys, attachments, provider payloads,
logs, paths, host/user identity, or recovery material.

Immediately before every runtime call, including a read, test, interoperability
operation, cleanup, or repaired mutation, re-evaluate PolicyEngine; exact
LocalApprovalAuthority scope where required; the current exact AuthorityLease;
exact capability, adapter, provider, target, mission, and run; TTL/deadline;
budget; readiness; kill switch; safe-disable; and idempotency/replay posture.
Approval refs alone never authorize. Unknown, stale, expired, or mismatched
state fails closed before the call starts.

## Required Verification

Run all focused Messenger tests plus the repository's affected regression suite
and authorized interoperability checks, then at minimum:

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

Adversarially audit authority, privacy, crypto, replay, failure truth, recovery,
operator UX, product claims, and the entire final diff. Fix every actionable in-
scope finding within the two repair-pass limit. Commit and push normally, open a
draft PR. While it is draft, complete local review and hardening. Mark it ready
only after local checks pass; run only repository-required GitHub-hosted CI on standard macOS runners,
never paid larger runners or self-hosted compute. Merge only when required checks are green,
update local `main` to the exact remote merge, run post-merge verification, push
verified `main`, confirm a clean worktree, and stop at the finite acceptance
endpoint. Do not generate a follow-on prompt pack or continue recursively.
The post-merge push must be a synchronization no-op: local `main` and
`origin/main` must resolve to the exact same merge SHA. If verification finds a
defect or divergence, use a new scoped branch and PR; never repair `main`
directly.

This milestone is desktop-only. Do not add, test, capture, or claim mobile
surfaces.

Final report: baseline SHA, acceptance matrix, repairs, commands/counts/timings,
blocked scenarios, remaining risks, commit, pushed branch, and draft PR URL.
