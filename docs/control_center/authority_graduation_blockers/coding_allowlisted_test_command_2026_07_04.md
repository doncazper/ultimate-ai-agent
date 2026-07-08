# Coding Allowlisted Test Command Blocker

Blocker ref: `blocker-ref:coding-allowlisted-test-command-2026-07-04`

Lane: Coding Cockpit Prompt 05 Allowlisted Test Command

Status: superseded by approval-required RuntimeGateway validation lane

## Full-Strength Goal

UAA Coding Cockpit shows focused allowlisted validation command posture while
RuntimeGateway runs exact fixed-command intents with timeout policy, bounded
redacted output summary, exit status, command receipts, Proof Detail binding,
and CLI parity after exact Action Inbox approval.

## Repo-Safe Current State

- `GET /control-center/coding/test-command-readiness` exposes backend-owned
  safe refs for the focused pytest, repo verifier, frontend check, and repo
  doctor RuntimeGateway validation lanes.
- `scripts/dev/uaa_coding.py inspect-test-command-readiness` inspects the same
  safe read model.
- `/coding` shows command refs, runtime lane refs, allowlist refs, expected
  receipt refs, runtime execution route refs, runtime CLI refs, and blocked
  authority refs.
- No raw command, raw output, exit code, raw local path, provider payload,
  account data, credential material, or private data is persisted.

## What Was Unblocked

This blocker is superseded for the exact RuntimeGateway validation intents that
already exist: focused pytest, repo verifier, frontend check, and repo doctor.
The Coding Cockpit does not execute commands directly. It points operators at
the existing RuntimeGateway Action Inbox execution path, which requires exact
approval, idempotency, fixed argv, bounded output redaction, command receipts,
and AuthorityLease scope.

Promoting this posture does not grant arbitrary shell, installs, network
commands, destructive commands, background processes, broad terminal access,
Git mutation, file mutation, provider/model calls, browser automation,
connector writes, public release, or production authority.

## Remaining Missing Contracts

- Expanded command kinds outside focused pytest, repo verifier, frontend check,
  and repo doctor.
- Standalone Coding-specific command receipt drilldown beyond RuntimeGateway
  receipt inspection.
- Universal Proof Detail binding for the Coding panel.
- Any live terminal control. This remains blocked.

## Required Tests And Verifiers

- Core tests for any expanded allowlist command kind.
- API tests for any future command execution or receipt routes not already
  covered by RuntimeGateway.
- CLI tests for readiness, receipt inspection, and blocked posture.
- Frontend tests proving mock fallback is non-authoritative and no mutation or
  execution control runs without backend authority.
- Documentation integrity, product truth, operational maturity, OpenAPI, release
  surface, and Control Center frontend verifiers.

## Safe Disable And Rollback

- RuntimeGateway safe-disable must block command execution before subprocess
  start.
- Long-running or stuck commands require timeout and termination posture.
- Replays must be blocked by idempotency refs.
- Rollback is not implied by validation command execution; any command that can
  mutate workspace state requires a separate exact receipt and
  rollback/safe-disable contract.

## Historical Unblock Prompt

`docs/prompts/authority_graduation_program/generated_unblock_prompts/unblock_coding_allowlisted_test_command.prompt.md`
