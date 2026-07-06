# UAA Hermes Runtime Skill Write Approval Gate

Status: Hermes Runtime Adoption Phase 14 repo-safe staged proposal posture

## Full-Strength Version

UAA can let agents propose new or updated skills, show the proposed diff,
route the proposal through operator review, run static checks, then apply the
exact reviewed skill write only through a future approved local mutation lane.

## Repo-Safe Version

Phase 14 adds a backend-owned Skill Write Approval Gate read model inside the
inspectable extension catalog and CLI inspection:

- `skill_write_approval_gate` in `GET /extensions/catalog`
- `scripts/dev/uaa_extensions.py inspect-skill-write-gate`
- staged skill-write proposal refs
- diff-preview refs with raw diff and raw file content omitted
- review decision refs and awaiting-review status
- blocked execution labels
- proof/verifier refs

This is proposal/readiness metadata only. It performs no file writes, skill
enablement, runtime import, execution, provider/model calls, connector writes,
shell/subprocess work, browser automation, or production authority.

## Blocked / Needs Authority

- direct writes into skill paths
- applying staged skill diffs
- enabling executable skills
- plugin or skill runtime import
- connector writes
- shell/subprocess execution
- provider/model calls
- browser automation
- production authority

## Exact Promotion Path

Future promotion requires exact `LocalApprovalAuthority` scope, reviewed diff
receipt, quarantine or staging path, static checks, safe-disable posture,
rollback readiness, idempotency, redaction, proof refs, CLI/API/Core parity,
and focused tests that prove only the approved skill diff can be applied.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_skill_write_gate.py tests/test_inspectable_extension_catalog.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_14.py
```
