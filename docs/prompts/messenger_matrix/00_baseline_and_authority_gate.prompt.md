# MSG-MX-000 — Baseline And Authority Gate

Execute one planning-only milestone in Ultimate AI Agent. Read `AGENTS.md`, the
Messenger Matrix implementation plan, the Messenger Matrix north star, current
boards, route inventory, API manifest, and capability/authority documentation
completely before editing.

## Branch Contract

- Fetch current `origin/main` and record its commit.
- Create `codex/msg-mx-00-baseline-authority` from that exact commit in an
  isolated worktree.
- Inspect open PRs and overlapping work first. Preserve unrelated work; never
  reset, revert, clean, stash, overwrite, force-push, or modify historical tags.

Python Core remains authoritative and Control Center remains an operator shell.
Preserve API/CLI parity for every operator-relevant truth or future capability.

## Exact Milestone

Audit integrated `main` against the design sources. Establish `MSG-MX-000`
through `MSG-MX-012` as subordinate items in the existing canonical board rather
than creating a competing roadmap. For every proposed Matrix lane, record:

- declaration and implementation status;
- authority domain and exact capability/adapter/target scope;
- side-effect and route classification;
- PolicyEngine, LocalApprovalAuthority, AuthorityLease, budget, deadline,
  readiness, kill-switch, and safe-disable posture;
- idempotency, replay, rollback or rollback-readiness, receipt, and redaction
  obligations;
- status as planned, blocked, separately authorized, unsupported, or unknown;
- exact acceptance evidence needed before the status may change.

Reconcile the board with current code and tests. Do not add runtime code,
dependencies, routes, UI controls, SDKs, network access, account authentication,
message reads, sends, or product-readiness claims.

## Fail-Closed Authority Rule

This milestone requires no new runtime authority. If completing the audit would
require implementing or exercising Matrix, local-network, credential, connector-
read, connector-write, crypto, media, or model authority, stop with an explicit
blocked report naming the exact lane. Planning text does not grant authority.

Any future mutation described by the plan must require exact safe refs,
redaction, request-bound idempotency, content-free receipts, rollback or rollback-
readiness, and safe-disable. Approval refs alone authorize nothing.

## Required Verification

Run focused documentation/board tests, then:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python scripts/run_foundation_gate.py --command-mode report-only --no-write-latest
git diff --check
```

Run frontend verification only if an existing frontend truth fixture was
necessarily changed; do not add a frontend feature in this milestone.

Adversarially review the diff for accidental authority, duplicate roadmaps,
misleading product truth, unsafe durable content, and unrelated changes. Fix all
actionable findings. Commit and push normally, then open a draft PR. While it is
draft, complete local review and hardening. Mark it ready only after local checks
pass; run only repository-scoped self-hosted macOS CI, never paid or GitHub-
hosted compute. Merge only when required checks are green, update local `main`
to the exact remote merge, run post-merge verification, push verified `main`,
and confirm a clean worktree. Do not begin MSG-MX-001 before that proof.

This milestone is desktop-only. Do not add, test, capture, or claim mobile
surfaces.

Final report: baseline SHA, files changed, lane classification, commands and
outcomes, blockers, commit, pushed branch, and draft PR URL.
