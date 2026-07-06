# Phase 03: Adapter Registry, Policy, And Approval Gate

Goal: define the only acceptable way a foreground local agent adapter may be
started: exact configured adapters, argv-only, approval-bound, safe-disable
aware, redacted, and receipt-backed.

## Required Work

1. Inspect existing UAA governed runtime and command execution infrastructure.
2. Add or harden an adapter registry contract for configured agent adapters:
   adapter id, display label, executable or command ref, argv template refs,
   allowed workspace refs, allowed modes, max runtime, max output bytes, env
   policy, disabled reason, and evidence refs.
3. Do not allow arbitrary command strings from UI/API.
4. Add policy checks for exact adapter allowlist, workspace scope, no ambient
   credential/env dump, no unrestricted shell, no background mode, no
   network/browser/connector authority, safe-disable, and approval required.
5. Bind approval to pair run ref, adapter refs, task ref, scope refs, turn
   budget, timeout, idempotency key, and policy decision ref.
6. If existing infrastructure cannot safely start configured foreground
   adapters, expose the blocked readiness result and generate an exact unblock
   prompt.
7. Add tests for allowlisted adapter pass, arbitrary command reject, approval
   missing, approval scope drift, safe-disable, timeout policy, output limit,
   and environment redaction.

## Explicit Non-Goals

- No provider SDK calls.
- No arbitrary shell commands.
- No background daemon or scheduler.
- No automatic patch apply, file write, Git mutation, browser automation, or
  connector write.

## Verification

```bash
git diff --check
PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_runtime_authority_boundaries.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_runtime_replay_protection.py -q
```

