# UAA Hermes Runtime Toolset Capability Posture

Status: Phase 09 repo-safe read model, AuthorityState-bound through capability discovery.

UAA now exposes a backend-owned toolset posture inside runtime capability
discovery. This lets the operator see what an optional delegated runtime may
support by reference, what UAA allows, and why high-authority toolsets remain
blocked.

This is Read-only `workspace/read` inspection through
`lane-ref:runtime-capability-discovery-read-model`. It is not Hermes tool
enablement. It does not invoke tools, change Hermes configuration, write runtime
profiles, or grant execution authority.

Implemented:

- Python Core `RuntimeToolsetCapabilityPosture`.
- Per-toolset `RuntimeToolsetCapabilityRecord` entries for:
  - core read-only metadata
  - profile and session metadata
  - coding workspace tools
  - command execution tools
  - browser and web tools
  - connector write tools
  - plugin runtime import tools
  - production operations tools
- Distinct `runtime_support_status` and `uaa_allowance_status` labels.
- Allowance states for read-only enabled, configured metadata-only,
  approval-required future lane, blocked, and unsupported posture.
- CLI/API/UI parity through `GET /api/runtime/capability-discovery`,
  `scripts/dev/uaa_runtime.py inspect-capability-discovery`, and Control Center
  `/runtime`.
- AuthorityState mapping and decision refs from
  `GET /api/runtime/authority-state`.
- Verifier coverage in `scripts/verify_hermes_runtime_adoption_phase_09.py`.

Blocked:

- Runtime tool invocation.
- Hermes toolset enablement.
- Toolset configuration mutation.
- File mutation through delegated runtime tools.
- Unrestricted command execution.
- Browser automation or web fetch outside an exact WebAccessGateway lane.
- Connector writes.
- Plugin runtime import.
- Production operations authority.
- Raw tool payload persistence.

Exact authority path:

1. Define an exact toolset grant for one lane.
2. Classify each tool by side-effect class.
3. Bind the grant to LocalApprovalAuthority, idempotency, receipt refs, and
   safe-disable posture.
4. Add rollback or rollback-readiness posture where the lane can mutate state.
5. Add redaction, bounded output previews, and proof refs.
6. Add CLI/API/Core parity plus focused verifier coverage.
7. Only then make a Control Center control appear actionable.

Current invariant:

`uaa_allowed_execution_count` is `0`; live tool invocation, toolset config
mutation, Hermes toolset enablement, raw tool payload persistence, and
production authority are all false.
