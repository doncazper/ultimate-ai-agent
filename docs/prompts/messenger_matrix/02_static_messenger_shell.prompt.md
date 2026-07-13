# MSG-MX-002 — Static Messenger Desktop Shell

Implement only Phase 1 of the Messenger Matrix plan: the fixture-backed desktop
Messenger shell. Read `AGENTS.md`, the complete implementation plan, north star,
render manifest, accepted desktop renders, product-language rules, and existing
Control Center architecture/tests before editing.

## Branch Contract

- Fetch current `origin/main`, record its SHA, and create
  `codex/msg-mx-02-static-shell` from that exact commit in an isolated worktree.
- Inventory overlapping UI work. Preserve it and avoid mobile surfaces. Never
  reset, revert, clean, stash, overwrite, force-push, or modify historical tags.
- Prove MSG-MX-001 is merged and post-merge verified on the current
  `origin/main`; otherwise stop with an explicit blocked report.

Python Core remains authoritative and Control Center remains an operator shell.
Preserve API/CLI parity; no UI state may become capability or authority truth.

## Exact Milestone

Implement `/messenger` as a fixture-only desktop product surface:

- an immersive Messenger rail with Back to Control Center;
- Home / All Messages, Founder HQ, Personal Circle, rooms, DMs, timelines,
  composers, inspectors, settings, security, setup, recovery, and dark theme;
- all 15 `COMMS-MX-*` surfaces and the required loading, empty, offline,
  undecryptable, queued, failed, retry, and narrower-desktop variations;
- typed fixture projections owned by backend-compatible contracts, while React
  owns only presentation and selection state;
- explicit Preview, Planned, or Blocked labels for every command;
- visible separation between human composer and UAA proposal/intelligence UI.

Add no Matrix dependency, SDK import, network call, runtime account state,
message read/send, room mutation, or fake connected posture. Fixtures must use
safe synthetic refs and content that cannot be mistaken for real user data.

## Fail-Closed Authority Rule

This milestone grants no runtime authority. Any control that would require
network, credential, connector-read/write, crypto, media, or room authority must
remain visibly blocked or preview-only. If the accepted UI cannot truthfully
represent that posture, stop with an exact blocked report rather than wiring a
mock mutation.

Any future mutation surfaced in the UI must declare safe refs, redaction, exact
idempotency, content-free receipts, rollback or rollback-readiness, and safe-
disable. The canonical posture is `safe-disable`; UI state and fixture content
never authorize an operation.

## Required Verification

Run focused React/unit/accessibility tests, desktop Playwright checks at the two
accepted widths, visual regression, product-language checks, typecheck, lint,
tests, and production build, then:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_frontend.py
make frontend-check
PYTHONPATH=src .venv/bin/python scripts/run_foundation_gate.py --command-mode report-only --no-write-latest
git diff --check
```

Adversarially review for React-owned truth, misleading connected/sent states,
hidden commands, raw JSON as primary UX, mobile scope, unsafe fixture data, and
Element copying. Fix all actionable findings. Commit and push normally and open
a draft PR. While it is draft, complete local review and hardening. Mark it ready
only after local checks pass; run only repository-scoped self-hosted macOS CI,
never paid or GitHub-hosted compute. Merge only when required checks are green,
update local `main` to the exact remote merge, run post-merge verification, push
verified `main`, and confirm a clean worktree. Do not begin MSG-MX-003 before
that proof.

This milestone is desktop-only. Do not add, test, capture, or claim mobile
surfaces.

Final report: baseline SHA, surfaces completed, commands blocked, screenshots or
visual evidence refs, verification, commit, pushed branch, and draft PR URL.
