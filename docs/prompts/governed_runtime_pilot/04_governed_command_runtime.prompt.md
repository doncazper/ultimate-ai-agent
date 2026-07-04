# Phase 04: Governed Command Runtime

Goal: implement real local command execution under strict runtime governance.

This phase promotes command runtime authority for allowlisted commands only. It
must not add unrestricted shell/subprocess execution.

## Required Work

1. Implement `GovernedCommandRuntimeAdapter` behind `RuntimeGateway`.
2. Use argv arrays only. Never execute shell strings.
3. Enforce an allowlist of command intents, such as:
   - inspect git status;
   - run focused pytest targets;
   - run repo verifiers;
   - run frontend checks.
4. Bind execution cwd to approved repo/workspace roots.
5. Apply timeout, output byte caps, and env allowlist.
6. Redact command output before persistence or UI display.
7. Store receipt metadata:
   - command intent;
   - argv safe ref or bounded sanitized argv;
   - cwd safe ref;
   - start/end timestamps;
   - exit code;
   - timeout state;
   - redacted bounded output ref;
   - rollback/safe-disable state.
8. Require approval for execution unless the command is a read-only status
   command explicitly classified as no-op and approved by policy.

## Hard Blocks

- No `shell=True`.
- No arbitrary command text.
- No arbitrary cwd.
- No inherited secret-rich environment.
- No networked commands unless the exact command and reason are approved by a
  later milestone.
- No raw logs, local paths, usernames, hostnames, env dumps, or credentials in
  durable evidence.

## Acceptance Criteria

- Unknown command intent is blocked.
- Shell metacharacter attempts are blocked before execution.
- Command output is redacted and bounded.
- Timeout and non-zero exit are represented as safe receipts.
- Idempotency/replay behavior is tested.
- Safe-disable prevents new command execution.

## Verification

Run focused command runtime tests plus:

```bash
git diff --check
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

