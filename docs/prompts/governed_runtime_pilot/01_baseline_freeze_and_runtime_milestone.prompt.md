# Phase 01: Baseline Freeze And Runtime Milestone

Goal: freeze the current safe baseline and update UAA's project contract to
allow a scoped `v0.105.0 Governed Runtime Pilot`.

This phase is docs, contract, and release-planning work. It must not implement
runtime calls yet.

## Required Work

1. Record current branch, commit, status, and remote.
2. Run baseline verification that is already expected for the repo.
3. Create an annotated baseline tag only when the working tree and verification
   state are clean enough to preserve as an audit point.
4. Update the smallest relevant docs to introduce:
   - `v0.105.0 Governed Runtime Pilot`;
   - runtime profiles: `sealed`, `local-runtime`, `operator-approved`;
   - authority promoted by the pilot;
   - authority still blocked;
   - release truth and product-language limits.
5. Add or update a task board entry for the governed runtime milestone.
6. Add acceptance criteria and rollback/safe-disable posture.

## Contract Language

The new milestone may say:

```text
UAA v0.105.0 may promote scoped local runtime authority through a governed
RuntimeGateway. The pilot is limited to configured loopback/local model calls,
allowlisted argv-only local command execution, exact Action Inbox approval
envelopes, redacted evidence receipts, and CLI/API/Control Center parity.
Browser automation, connector writes, plugin runtime import, remote execution,
unrestricted web access, production authority, public beta, and broad autonomy
remain blocked.
```

## Acceptance Criteria

- Existing invariants are not silently deleted.
- The new milestone explicitly narrows what is allowed.
- The docs distinguish implemented, planned, blocked, and pilot-scoped states.
- Historical tags are not changed.
- Baseline tag creation is recorded or explicitly skipped with reason.
- No runtime model, command, browser, web, connector, plugin, or remote
  authority is implemented in this phase.

## Verification

Run:

```bash
git diff --check
.venv/bin/python scripts/verify_documentation_integrity.py
```

Run additional docs/product-language verifiers if they exist.
