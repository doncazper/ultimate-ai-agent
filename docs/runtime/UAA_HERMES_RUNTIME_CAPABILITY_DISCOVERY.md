# UAA Hermes Runtime Capability Discovery

Status: Phase 02 repo-safe read model, extended by Phase 09 toolset posture and AuthorityState binding.

UAA now exposes a backend-owned runtime capability discovery posture for the
optional Hermes Agent runtime target. The read model is bound to AuthorityState
as `lane-ref:runtime-capability-discovery-read-model`, which evaluates as
Read-only `workspace/read` inspection when that lease scope is active. This is
not live discovery and does not grant runtime authority.

Implemented:

- Python Core `RuntimeCapabilityDiscoveryReadModel`.
- Capability taxonomy for models, runs, events, approvals, sessions, skills,
  toolsets, jobs, and blocked actions.
- Phase 09 `RuntimeToolsetCapabilityPosture` with per-toolset runtime support
  versus UAA allowance state.
- `GET /api/runtime/capability-discovery`.
- `scripts/dev/uaa_runtime.py inspect-capability-discovery`.
- Control Center `/runtime` display of runtime support versus UAA
  authorization status.
- AuthorityState route, CLI, mapping, decision outcome, reason refs, and
  unsupported adapter refs.
- Stale or unreachable runtime state degrades to blocked.
- Safe refs, redacted summaries, and snapshot hash refs only.

AuthorityState:

- AuthorityState route: `GET /api/runtime/authority-state`
- AuthorityState CLI: `repo-local-command:uaa-runtime-inspect-authority-state`
- mapping ref: `lane-ref:runtime-capability-discovery-read-model`
- domain/capability: `workspace/read`
- required mode: `read_only`
- status: `implemented_authority_bound_read_model`

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

Phase 09 toolset posture:

- Defines UAA-native toolset categories that can map delegated runtime tool
  groups without copying Hermes code or importing Hermes packages.
- Shows `enabled_read_only`, `configured_metadata_only`,
  `approval_required_future_lane`, `blocked`, and `unsupported` allowance
  states.
- Separates `runtime_support_status` from `uaa_allowance_status` for every
  toolset record.
- Keeps `uaa_allowed_execution_count` at `0`.
- Keeps live tool invocation, toolset configuration mutation, Hermes toolset
  enablement, raw tool payload persistence, and production authority disabled.
- Binds proof to `proof-ref:hermes-runtime-adoption:phase-09:toolsets`.

Exact authority path:

1. Add an exact signed/hashed live capability snapshot lane.
2. Define freshness policy and stale-snapshot denial behavior.
3. Evaluate every discovered capability through UAA policy before any control
   appears actionable.
4. Bind promoted controls to approval envelopes, receipt refs, rollback or
   safe-disable posture, CLI/API/Core parity, and focused verifiers.
