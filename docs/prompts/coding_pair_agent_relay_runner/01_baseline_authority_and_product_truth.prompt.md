# Phase 01: Baseline Authority And Product Truth

Goal: establish the truth baseline for Coding Cockpit multi-agent review before
building a paired-agent relay runner.

## Required Work

1. Inspect the existing Coding Cockpit multi-agent review read model, API route,
   CLI inspection path, Control Center UI, docs, route manifest, and tests.
2. Inspect existing governed runtime, command execution, approval, receipt,
   evidence, and safe-disable infrastructure.
3. Classify current status for read-only review readiness, manual artifact
   proposal, foreground local agent adapter execution, provider/model
   invocation, background dispatch, patch apply, Git mutation, and
   transcript/evidence storage.
4. Create or update `docs/control_center/CODING_PAIR_AGENT_RELAY_RUNNER.md`.
5. Define the exact target lane:
   `coding_pair_agent_foreground_relay_runner`.
6. Add a verifier or focused test that prevents product docs from claiming
   broad multi-agent execution without exact evidence.

## Acceptance Criteria

- The baseline doc distinguishes implemented, partial, planned, blocked,
  mock-only, deprecated, contradicted, and unknown states.
- Current blocked states remain accurate.
- No docs claim autonomous/background agents, provider SDK calls, patch apply,
  Git mutation, browser automation, connector writes, or production authority.

## Verification

```bash
git diff --check
.venv/bin/python scripts/verify_documentation_integrity.py
```

