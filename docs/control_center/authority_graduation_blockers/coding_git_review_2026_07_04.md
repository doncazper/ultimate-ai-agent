# Coding Git Review Blocker

Blocker ref: `blocker-ref:coding-git-review-2026-07-04`

Lane: Coding Cockpit Prompt 06 Git Review

Status: blocked, review/readiness model implemented

## Full-Strength Goal

UAA Coding Cockpit reviews Git status, diffs, changed files, staged and
unstaged posture, commit proposals, pull-request description proposals, and
later approved stage, commit, push, and draft PR actions with receipts, redacted
evidence, Proof Detail binding, and CLI parity.

## Repo-Safe Current State

- `GET /control-center/coding/git-review` exposes backend-owned safe refs for
  Git review readiness only.
- `scripts/dev/uaa_coding.py inspect-git-review` inspects the same safe read
  model.
- `/coding` shows Git status, diff, changed-file, commit proposal, and
  pull-request proposal refs plus expected receipt refs and blocked authority
  refs.
- No live Git command, raw Git output, raw diff, raw local path, commit message
  text, pull-request description text, Git receipt, provider payload, account
  data, credential material, or private data is persisted.

## Why This Was Not Unblocked

The current Coding Git panel stores safe review refs and expected receipt refs
only. It does not implement live Git status reads, live Git diff reads, changed
file extraction, redaction, commit or PR text proposals, receipt storage, Proof
Detail binding, or exact approval for any Git mutation.

Promoting Git review without those pieces would create shell/Git authority that
is not exact-scoped, bounded, redacted, auditable, and test-backed.

## Missing Contracts

- Read-only Git status contract with bounded output and safe refs.
- Read-only Git diff contract with raw diff redaction and safe hunk/file refs.
- Changed-file extraction with raw local path omission.
- Commit proposal and PR description proposal contracts over safe summaries.
- Git receipt contracts with evidence/proof refs.
- LocalApprovalAuthority validation for any stage, commit, push, or PR action.
- Safe-disable posture for Git read and Git mutation lanes.
- Universal Proof Detail binding.
- CLI parity for readiness, receipt inspection, and blocked posture.
- Frontend tests proving no Git control executes without backend authority.

## Required Tests And Verifiers

- Core tests for Git status refs, diff refs, changed-file refs, proposal refs,
  redaction, receipt shape, proof refs, idempotency, and safe-disable.
- API tests for any future Git read, receipt, or mutation routes.
- CLI tests for readiness, receipt inspection, and blocked posture.
- Frontend tests proving mock fallback is non-authoritative and no Git mutation
  control runs without backend authority.
- Documentation integrity, product truth, operational maturity, OpenAPI, release
  surface, and Control Center frontend verifiers.

## Safe Disable And Rollback

- Live Git read and Git mutation lanes must be disabled by default.
- A per-session disable ref must block Git reads or mutations before subprocess
  start.
- Git mutation replay must be blocked by idempotency refs.
- Stage, commit, push, PR open, merge, tag, and release each require separate
  exact approval posture.
- Rollback is not implied by Git mutation; each mutation lane needs its own
  receipt and safe-disable or rollback posture.

## Next Unblock Prompt

`docs/prompts/authority_graduation_program/generated_unblock_prompts/unblock_coding_git_review.prompt.md`
