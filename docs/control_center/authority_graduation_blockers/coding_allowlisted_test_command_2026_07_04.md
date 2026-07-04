# Coding Allowlisted Test Command Blocker

Blocker ref: `blocker-ref:coding-allowlisted-test-command-2026-07-04`

Lane: Coding Cockpit Prompt 05 Allowlisted Test Command

Status: blocked, readiness model implemented

## Full-Strength Goal

UAA Coding Cockpit runs focused allowlisted test, lint, typecheck, and repo
verifier commands with command preview, timeout policy, bounded redacted output
summary, exit status, command/test receipts, Proof Detail binding, and CLI
parity.

## Repo-Safe Current State

- `GET /control-center/coding/test-command-readiness` exposes backend-owned
  safe refs for test command readiness only.
- `scripts/dev/uaa_coding.py inspect-test-command-readiness` inspects the same
  safe read model.
- `/coding` shows suggested command refs, allowlist refs, expected receipt refs,
  and blocked authority refs.
- No raw command, raw output, exit code, raw local path, provider payload,
  account data, credential material, or private data is persisted.

## Why This Was Not Unblocked

The current Coding terminal/test-output lane stores safe command refs and
expected receipt refs only. It does not implement exact allowlist enforcement,
command preview approval posture, subprocess execution, timeout policy, output
redaction, exit-code capture, command receipt storage, test receipt storage, or
Proof Detail binding.

Promoting command execution without those pieces would create shell authority
that is not exact-scoped, approval-bound where required, bounded, redacted,
auditable, and test-backed.

## Missing Contracts

- Exact command allowlist with command refs, argument bounds, and denied command
  classes.
- Command preview contract with authority mode and approval posture.
- LocalApprovalAuthority validation for any command that requires explicit
  approval.
- Timeout and process termination policy.
- Bounded output redaction and summary contract.
- Exit-code/status capture.
- Command and test receipt contracts with evidence/proof refs.
- Safe-disable posture for the command lane.
- Universal Proof Detail binding.
- CLI parity for readiness, receipt inspection, and blocker inspection.
- Frontend tests proving no command control executes without backend authority.

## Required Tests And Verifiers

- Core tests for allowlist matching, denied command classes, timeout posture,
  output redaction, receipt shape, proof refs, idempotency, and safe-disable.
- API tests for any future command execution or receipt routes.
- CLI tests for readiness, receipt inspection, and blocked posture.
- Frontend tests proving mock fallback is non-authoritative and no mutation or
  execution control runs without backend authority.
- Documentation integrity, product truth, operational maturity, OpenAPI, release
  surface, and Control Center frontend verifiers.

## Safe Disable And Rollback

- Command execution lane must be disabled by default.
- A per-session disable ref must block command execution before subprocess
  start.
- Long-running or stuck commands require timeout and termination posture.
- Replays must be blocked by idempotency refs.
- Rollback is not implied by command execution; any command that can mutate
  workspace state requires a separate exact receipt and rollback/safe-disable
  contract.

## Next Unblock Prompt

`docs/prompts/authority_graduation_program/generated_unblock_prompts/unblock_coding_allowlisted_test_command.prompt.md`
