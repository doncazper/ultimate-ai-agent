# Phase 04: Foreground Relay Runner Orchestrator

Goal: implement the bounded foreground relay orchestrator if and only if the
adapter registry, policy, approval, safe-disable, and receipt gates are proven.
Otherwise, implement the no-execution preview/readiness runner and exact unblock
prompt.

## Required Work

1. Implement a UAA-owned relay orchestrator that creates turn packets, starts
   only approved configured foreground adapters, waits for bounded responses,
   validates/redacts responses, creates the next turn packet, and repeats until
   a stop condition.
2. Keep execution foreground and operator-visible. Do not add background
   autonomy.
3. Use UAA-owned state, not a shared markdown file, as source of truth.
4. If files are used as adapter inbox/outbox surfaces, treat them as temporary
   transport artifacts and store only refs/hashes/summaries in durable evidence.
5. Stop on max turns, timeout, user stop, policy block, approval need, adapter
   failure, output too large, missing sentinel, unsafe output, or scope
   expansion.
6. Add tests with fake adapters. Do not require real Codex or Claude binaries
   in unit tests.

## Acceptance Criteria

- Fake-adapter tests prove turn alternation, stop conditions, output limits,
  timeout handling, user stop, and final summary creation.
- Real adapter execution is disabled unless exact configured adapter authority
  is present and approved.
- The orchestrator never executes patch apply, Git mutation, browser actions,
  connector writes, or arbitrary commands.

## Verification

```bash
git diff --check
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
```

