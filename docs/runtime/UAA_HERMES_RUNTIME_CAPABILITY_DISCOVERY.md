# UAA Hermes Runtime Capability Discovery

Status: Phase 02 repo-safe read model.

UAA now exposes a backend-owned runtime capability discovery posture for the
optional Hermes Agent runtime target. This is not live discovery and does not
grant runtime authority.

Implemented:

- Python Core `RuntimeCapabilityDiscoveryReadModel`.
- Capability taxonomy for models, runs, events, approvals, sessions, skills,
  toolsets, jobs, and blocked actions.
- `GET /api/runtime/capability-discovery`.
- `scripts/dev/uaa_runtime.py inspect-capability-discovery`.
- Control Center `/runtime` display of runtime support versus UAA
  authorization status.
- Stale or unreachable runtime state degrades to blocked.
- Safe refs, redacted summaries, and snapshot hash refs only.

Blocked:

- Live runtime capability calls.
- Runtime-supported capability granting UAA permission.
- Live run submission.
- Provider/model calls.
- Tool execution.
- Shell/subprocess execution.
- Browser automation.
- Connector writes.
- Plugin runtime import.
- Background autonomy.
- Production authority.
- Raw prompt, response, provider payload, runtime payload, log, local path, or
  credential persistence.

Promotion path:

1. Add an exact signed/hashed live capability snapshot lane.
2. Define freshness policy and stale-snapshot denial behavior.
3. Evaluate every discovered capability through UAA policy before any control
   appears actionable.
4. Bind promoted controls to approval envelopes, receipt refs, rollback or
   safe-disable posture, CLI/API/Core parity, and focused verifiers.
