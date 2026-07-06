# UAA Hermes Runtime Hardline Command Blocklist

Status: Hermes Runtime Adoption Phase 25, repo-safe read-only posture.

## Full-strength

UAA has a non-overridable catastrophic command deny floor for local, delegated,
and future command lanes. The floor applies before any runner starts and cannot
be bypassed by an approval envelope, provider output, delegated runtime output,
Control Center control, or future adapter.

## Repo-safe

Phase 25 adds a Python Core hardline command classifier, a static test corpus,
gateway checks before runner invocation, and a backend-owned read model exposed
through:

- `GET /api/runtime/hardline-command-blocklist`
- `scripts/dev/uaa_runtime.py inspect-hardline-command-blocklist`
- Control Center Runtime readiness posture

The read model stores safe refs, category labels, counts, proof refs, verifier
refs, and blocked authority refs only. It does not persist raw command text,
raw command output, local paths, environment material, or runner output. It
does not add a new command execution lane.

## Blocked / Needs Authority

The following remain blocked:

- hardline floor override or downgrade
- command string bypass
- shell metachar bypass
- destructive filesystem commands
- disk writer commands
- network transfer commands
- remote access commands
- Git mutation commands
- package install commands
- privilege escalation commands
- production orchestration commands
- browser or desktop automation commands
- raw command text persistence
- raw command output persistence
- production authority

## Exact Promotion Path

Future command authority must prove:

- security review for the exact command shape
- expanded test corpus coverage
- route side-effect classification
- Foundation Gate coverage
- approval binding and idempotency
- safe-disable posture
- rollback or rollback-readiness posture
- receipt and proof refs
- CLI/API/Core parity
- redaction of command text, output, paths, and environment material

The hardline floor remains always-on even when a narrower command lane is
promoted.
