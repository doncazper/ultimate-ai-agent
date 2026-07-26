# MSG-MX-001 — Design ADR, Render Acceptance, And Threat Model

Execute only Phase 0 of the canonical Messenger Matrix plan. Read `AGENTS.md`,
the complete implementation plan, north-star design, all 15 renders and render
manifest, current ADR conventions, security/redaction rules, and capability
authority documentation before editing.

## Branch Contract

- Fetch current `origin/main`, record the SHA, and create
  `codex/msg-mx-01-design-threat-model` from that exact commit in an isolated
  worktree.
- Inventory overlapping branches/PRs and preserve unrelated work. Never reset,
  revert, clean, stash, overwrite, force-push, or move historical tags.
- Prove MSG-MX-000 is merged and post-merge verified on the current
  `origin/main`; otherwise stop with an explicit blocked report.

Python Core remains authoritative and Control Center remains an operator shell.
Preserve API/CLI parity in every designed operator-relevant contract.

## Exact Milestone

Finish the design gate without runtime implementation:

- accept or explicitly reject each of `COMMS-MX-01` through `COMMS-MX-15` as a
  desktop target render, including normal and narrower desktop widths;
- write one clean-room/license ADR covering the original UAA implementation,
  Matrix protocol boundary, `matrix-js-sdk` decision, singleton client/crypto-
  store ownership, and Element interoperability-only posture;
- specify macOS credential storage, crypto store, protected cache, backup,
  migration, deletion, recovery, and Python/TypeScript ownership boundaries;
- produce the threat model for messages, attachments, tokens, recovery material,
  cache, logs, receipts, context grants, malicious events, and prompt injection;
- define the exact capability/authority matrix for discovery, login, sync,
  receipts, typing, send, edit, redact, reaction, media, room, invite, settings,
  verification, recovery, and calls.

Do not add runtime code, dependencies, routes, SDKs, network access, credential
handling, message reads/sends, or implementation claims. Do not copy Element
source, styles, assets, branding, internal identifiers, or product copy.

## Fail-Closed Authority Rule

This milestone grants no runtime authority. If a design decision cannot be made
without exercising a network, account, connector, credential, crypto, or message
lane, record the exact unknown and stop with an explicit blocked report. Do not
treat render acceptance as runtime evidence.

Every future mutation must be bound to safe refs, redaction, exact idempotency,
content-free receipts, rollback or rollback-readiness, and safe-disable. Approval
refs are identifiers only.

## Required Verification

Run focused ADR, render-manifest, product-language, and security documentation
checks plus:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python scripts/run_foundation_gate.py --command-mode report-only --no-write-latest
git diff --check
```

Run frontend checks only if an existing desktop render contract changed.
Adversarially review for copied implementation details, missing trust boundaries,
authority escalation, raw-content examples, and inflated product claims. Fix all
actionable findings. Commit and push normally and open a draft PR. While it is
draft, complete local review and hardening. Mark it ready only after local checks
pass; run only repository-required GitHub-hosted CI on standard macOS runners,
never paid larger runners or self-hosted compute. Merge only when required checks
are green, update local `main`
to the exact remote merge, run post-merge verification, push verified `main`,
and confirm a clean worktree. Do not begin MSG-MX-002 before that proof.
The post-merge push must be a synchronization no-op: local `main` and
`origin/main` must resolve to the exact same merge SHA. If verification finds a
defect or divergence, use a new scoped branch and PR; never repair `main`
directly.

This milestone is desktop-only. Do not add, test, capture, or claim mobile
surfaces.

Final report: baseline SHA, render decisions, ADR/threat-model outputs, authority
matrix, blockers, verification, commit, pushed branch, and draft PR URL.
