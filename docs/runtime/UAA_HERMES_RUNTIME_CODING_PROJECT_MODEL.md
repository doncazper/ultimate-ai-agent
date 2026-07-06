# UAA Hermes Runtime Coding Project Model

Status: Hermes Runtime Adoption Phase 21 repo-safe read model

## Full-Strength Version

UAA Coding Cockpit becomes a governed project command center for repos,
project lanes, branches, worktrees, files, diffs, tests, live preview,
terminal, Git, proof, and future delegated coding agents. UAA remains the
authority owner while Hermes, Codex, Claude, local agents, and future runtimes
can be supervised through safe refs, approval envelopes, receipts, and Proof.

## Repo-Safe Version

Phase 21 adds Python Core coding project posture inside the existing
`GET /control-center/coding/session` read model:

- `CodingProjectModelReadModel`
- `CodingProjectCapabilityReadModel`
- `scripts/dev/uaa_coding.py inspect-project-model`
- Control Center Coding Cockpit project posture display
- safe refs for workspace, repo, lane, branch, worktree, file refs, diff refs,
  test lane, live preview lane, terminal lane, Git lane, and proof spine
- backend-owned flags proving no raw paths, raw file content, file scan,
  command execution, Git execution, browser preview, provider/model call,
  background autonomy, or production authority

This is read-only project posture only. It does not read repo files, scan local
paths, write files, apply patches, run tests, run shell or Git commands, start
dev servers, open browser previews, call providers, dispatch local agents, or
claim production authority.

## Blocked / Needs Authority

- file mutation and patch apply
- raw repo file reading and context materialization
- shell, subprocess, terminal, and test command execution
- Git status execution, staging, commit, push, PR, or merge
- dev server control, browser preview, screenshot capture, console capture, and
  browser automation
- provider/model calls and delegated coding agent dispatch
- background coding autonomy
- production authority

## Exact Promotion Path

Future promotion must proceed lane by lane:

- context-pack preview with safe refs and sensitive-context guards
- patch proposal artifacts with bounded summaries and no apply
- exact approved patch apply with checkpoint, idempotency, approval binding,
  redacted receipt, rollback posture, and Proof
- allowlisted test commands with argv-only scope, timeout, redacted output,
  exit status, receipt, and CLI/API parity
- Git review lane first, then exact approved stage/commit/push/PR lanes
- live preview status first, then approved dev-server and browser proof lanes
- multi-agent review artifacts first, then exact foreground agent relay lanes

Every promotion needs safe-disable posture, verifier coverage, route
classification, redaction, CLI/API/Core parity, and frontend truth labels.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_coding_cockpit_read_model.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_21.py
npm run test --prefix apps/control-center -- --run src/App.test.tsx src/routes.test.ts
```
