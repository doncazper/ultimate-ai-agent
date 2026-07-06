# UAA Hermes Runtime Profile Isolation

Status: Phase 06 repo-safe read model.

UAA now exposes a backend-owned runtime profile isolation posture for optional
Hermes delegation and future delegated runtimes. This is not a runtime profile
manager. It models UAA-owned profile refs separately from delegated runtime
profile refs, with safe display labels, role, configured status, authority
posture, workspace scope ref, memory scope ref, toolset posture, health, proof
refs, and blocked reasons.

Implemented:

- Python Core `RuntimeProfileIsolationReadModel`.
- Five UAA profile roles: coding, research, operations, CRM, and review.
- UAA profile refs that are distinct from delegated runtime profile refs.
- Safe display labels and profile health.
- Workspace scope refs, memory scope refs, and toolset posture summaries.
- `GET /api/runtime/profiles`.
- `scripts/dev/uaa_runtime.py inspect-profiles`.
- Control Center `/runtime` display of route, CLI, profile counts, health,
  authority posture, and profile isolation blockers.

Blocked:

- Creating or deleting runtime profiles.
- Writing runtime configuration.
- Copying credential material or other sensitive material into profiles.
- Changing runtime defaults.
- Treating delegated runtime profile names as UAA authority.
- Cross-profile authority bleed.
- Runtime model calls, provider SDK calls, tool execution, shell/subprocess
  execution, browser automation, connector writes, plugin runtime import,
  background autonomy, remote execution, and production authority.
- Raw profile names, workspace paths, prompt/response content, provider
  payloads, logs, account material, or credential material persistence.

Promotion path:

1. Define a profile storage contract owned by Python Core.
2. Require exact operator approval before create/delete/config/default changes.
3. Bind profile changes to safe-disable refs, rollback posture, audit receipts,
   proof refs, and idempotency.
4. Store credential references only; never copy credential material into profile
   records.
5. Add CLI/API/Core/Control Center parity plus focused isolation, no-raw-path,
   no-sensitive-material, no-cross-profile-bleed, rollback, and safe-disable
   verifiers.
