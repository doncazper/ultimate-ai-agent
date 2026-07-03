# Local Shell / Subprocess Allowlisted Command Blocker

Status: blocked, no shell/subprocess execution promoted
Lane: Local Shell / Subprocess
Attempted promotion: Level 2 manual foreground allowlisted command
Date: 2026-07-03

## Existing Verified Posture

UAA has mature shell/subprocess review and freeze contracts, but they are not
execution authority.

Existing foundations include:

- M82 Command Proposal Contracts:
  `src/ultimate_ai_agent/core/sandbox/command_proposal.py`
- M83 Shell Dry-Run Classifier:
  `src/ultimate_ai_agent/core/sandbox/shell_dry_run_classifier.py`
- M85 Read-Only Command Allowlist boundary:
  `docs/sandbox/READ_ONLY_COMMAND_ALLOWLIST_AUTHORITY_BOUNDARY.md`
- M90 Shell/Subprocess Hardening Freeze:
  `docs/sandbox/SHELL_SUBPROCESS_HARDENING_FREEZE_POLICY.md`
- authority candidate:
  `docs/control_center/authority_candidate_scorecard.json`
  candidate_id `shell_subprocess_local_maintenance`

The current scorecard marks `shell_subprocess_local_maintenance` as
`not_ready`. The existing boundary docs explicitly say the read-only allowlist
is not authority to execute anything, and M90 denies command execution,
subprocess execution, shell execution, process spawn, filesystem mutation,
network access, background workers, routes, Control Center controls, and
production authority.

## Why This Was Not Unblocked

The requested promotion requires one allowlisted foreground command with exact
approval, bounded cwd/env, timeout, redacted output summary refs, receipt,
audit, safe-disable, and denial paths for unapproved or unsafe commands.

That promotion was not safe in this run because:

- no exact local maintenance command family is selected;
- no validation-only local maintenance classifier exists for the exact command
  family;
- no LocalApprovalAuthority scope exists for one command invocation;
- no bounded cwd/env contract exists for a runtime command;
- no timeout/kill/safe-disable rule exists for the exact command family;
- no redacted stdout/stderr receipt schema exists;
- no CLI/API/Core parity contract exists for inspected command receipts;
- current M85/M90 contracts intentionally block all command execution.

## Missing Contract / Test / Evidence

- exact command family and safe argument schema;
- validation-only local maintenance classifier for that command family;
- explicit non-shell invocation shape with no shell strings;
- LocalApprovalAuthority scope and approval mismatch blockers;
- cwd allowlist and env allowlist with no secret/env dump persistence;
- timeout and safe-disable behavior;
- output redaction and bounded summary refs for stdout/stderr;
- idempotency/replay and audit receipt refs;
- denied-command receipts for unapproved, unsafe, network, background,
  privileged, package-install, and arbitrary shell attempts;
- CLI inspection over command receipts without re-executing commands;
- tests proving broad shell/subprocess authority remains blocked.

## Smallest Next Safe Action

Run a dedicated shell/subprocess unblock PR that implements only a
validation-only local maintenance classifier and receipt contract for one
candidate command family. Do not add a subprocess runner until that classifier,
approval scope, redaction, timeout, safe-disable, and CLI inspection contract is
green.

## Authority Still Blocked

- shell execution
- subprocess execution
- process spawn
- arbitrary command execution
- privileged commands
- package installs
- network shell behavior
- background processes
- filesystem mutation through commands
- provider/model calls
- connector writes
- browser automation
- memory writes or context injection from command output
- public beta, public release, or production authority
