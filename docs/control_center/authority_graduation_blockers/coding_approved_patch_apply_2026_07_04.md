# Coding Approved Patch Apply Blocker

Blocker ref: `blocker-ref:coding-approved-patch-apply-2026-07-04`

Lane: Coding Cockpit Prompt 04 Approved Patch Apply

Status: blocked, readiness model implemented

## Full-Strength Goal

UAA Coding Cockpit applies selected files or hunks from an exact patch proposal
after operator approval, checkpoint creation, apply receipt emission, rollback
receipt posture, Proof Detail binding, redaction, and CLI parity.

## Repo-Safe Current State

- `GET /control-center/coding/patch-apply-readiness` exposes backend-owned safe
  refs for apply readiness only.
- `scripts/dev/uaa_coding.py inspect-patch-apply-readiness` inspects the same
  safe read model.
- `/coding` shows blocked apply prerequisites and keeps all patch controls
  disabled.
- No patch body, raw diff body, raw path, raw file content, command output,
  provider payload, account data, credential material, or private data is
  persisted.

## Why This Was Not Unblocked

The current Coding patch proposal lane stores safe file refs, hunk refs, and
bounded summaries only. It does not store an exact patch body, selected file or
hunk scope, checkpoint contract, apply receipt contract, rollback receipt
contract, Proof Detail binding, or a verifier-backed sensitive diff guard.

Promoting apply without those pieces would create file mutation authority that
is not exact-scoped, approval-bound, rollback-aware, redacted, and test-backed.

## Missing Contracts

- Exact patch artifact storage with safe refs and no raw sensitive persistence.
- Selected file and hunk scope contract.
- LocalApprovalAuthority validation for the selected proposal and authority
  mode.
- Checkpoint creation before apply.
- Apply receipt with preimage and postimage refs.
- Rollback receipt and safe rollback posture.
- Sensitive diff guard for protected values, generated output, deletes, and
  sensitive config.
- Universal Proof Detail binding.
- CLI parity for inspect, apply preview, receipt inspection, and rollback
  posture.
- Frontend tests proving controls remain disabled unless exact backend authority
  exists.

## Required Tests And Verifiers

- Core tests for exact patch artifact refs, selected scope, approval mismatch,
  idempotency, checkpoint, apply receipt, rollback receipt, and sensitive diff
  blocking.
- API tests for any future apply route and receipt route.
- CLI tests for apply readiness, receipt inspection, and rollback posture.
- Frontend tests proving mock fallback is non-authoritative and no mutation
  control executes without backend authority.
- Documentation integrity, product truth, operational maturity, OpenAPI, release
  surface, and Control Center frontend verifiers.

## Safe Disable And Rollback

- Apply lane must be disabled by default.
- A per-session disable ref must block apply before mutation.
- Rollback must be exact-scoped to the generated apply receipt.
- Replays must be blocked by idempotency refs.

## Next Unblock Prompt

`docs/prompts/authority_graduation_program/generated_unblock_prompts/unblock_coding_approved_patch_apply.prompt.md`
