# UAA Hermes Runtime Tool Registry Availability

Status: Phase 10 repo-safe read model, AuthorityState-bound.

UAA now exposes a backend-owned runtime tool registry availability posture. It
lists UAA-native preview tools and delegated runtime tool references with
availability, configured status, authority class, side-effect class, risk, safe
summary, blocker refs, proof refs, and next safe actions.

This is Read-only `workspace/read` inspection through
`lane-ref:runtime-tool-registry-read-model`, not tool invocation. UAA does not
discover remote tools live, import plugins, activate connector writes, call
models/providers, execute delegated runtime tools, or persist raw tool payloads.

Implemented:

- Python Core `RuntimeToolRegistryAvailabilityReadModel`.
- Per-tool `RuntimeToolRegistryEntry` records for:
  - UAA-native file metadata preview
  - UAA-native memory metadata preview
  - UAA-native message draft preview
  - UAA-native API route preview
  - Hermes coding workspace context reference
  - Hermes command execution reference
  - Codex patch proposal review reference
  - Claude review summary reference
  - MCP catalog metadata reference
  - future browser observe reference
  - future connector write reference
  - future production operation reference
- Availability states for metadata-only available, configured-disabled,
  approval-required future lane, blocked, and unsupported tools.
- Authority classes for preview-only, approval-required future lane,
  blocked high-authority, and unsupported posture.
- CLI/API/UI parity through `GET /api/runtime/tool-registry`,
  `scripts/dev/uaa_runtime.py inspect-tool-registry`, and Control Center
  `/runtime`.
- AuthorityState route, CLI, mapping, decision outcome, reason refs, and
  unsupported adapter refs from `GET /api/runtime/authority-state`.
- Verifier coverage in `scripts/verify_hermes_runtime_adoption_phase_10.py`.

AuthorityState:

- AuthorityState route: `GET /api/runtime/authority-state`
- AuthorityState CLI: `repo-local-command:uaa-runtime-inspect-authority-state`
- mapping ref: `lane-ref:runtime-tool-registry-read-model`
- domain/capability: `workspace/read`
- required mode: `read_only`
- status: `implemented_authority_bound_read_model`

Blocked:

- Runtime tool invocation.
- Remote tool discovery that performs live web/network fetches.
- Provider/model calls.
- Hermes tool execution.
- Codex or Claude runtime dispatch.
- Browser automation.
- Connector writes or connector activation.
- Plugin runtime import.
- Shell/subprocess execution.
- Production operations authority.
- Raw tool payload persistence.

Exact authority path:

1. Pick one exact tool lane and side-effect class.
2. Define per-tool approval scope, idempotency key, and stale-approval denial.
3. Bind safe-disable posture and rollback or rollback-readiness posture.
4. Add receipt/proof refs and redacted bounded output summaries.
5. Prove CLI/API/Core parity with focused tests and a verifier.
6. Keep Control Center as presentation/initiation only.
7. Promote only that exact tool lane; no class-wide tool authority is granted.

Current invariant:

`invocation_enabled_count` is `0`; `tool_invocation_enabled`,
`remote_discovery_enabled`, `live_web_fetch_enabled`,
`provider_model_call_enabled`, `plugin_import_enabled`,
`connector_write_activation_enabled`, `raw_tool_payload_persisted`, and
`production_authority_enabled` are all false.
