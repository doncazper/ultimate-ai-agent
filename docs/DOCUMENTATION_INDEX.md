# Documentation Index

Current active baseline: **v0.17.1**

This index is the active entrypoint for documentation navigation. Historical release documents remain in the repository for audit history, but active truth starts with the current baseline files listed here.

## Start Here

```text
README.md
VERSION.md
README_IMPORT_v0_17_1.md
ultimate_ai_agent_master_plan_v0_17_1.md
docs/canonical/CANONICAL_DOC_MAP.md
docs/canonical/09_roadmap.md
docs/maintenance/documentation_integrity_checklist.md
docs/maintenance/codex_plugin_capability_inventory.md
docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md
docs/tooling/CODEX_PLUGIN_RISK_POLICY.md
```

## Active Canonical Docs

The active canonical docs live in `docs/canonical/`. Use `docs/canonical/CANONICAL_DOC_MAP.md` to map systems to canonical files.

Key active canonical groups:

- roadmap and sequencing: `docs/canonical/09_roadmap.md`
- user control: `docs/canonical/20_user_control_center.md`
- consent, tools, approvals, and authority: `docs/canonical/21_consent_and_permissions_ledger.md`, `docs/canonical/37_tool_broker.md`, `docs/canonical/42_autonomy_levels_and_standing_approvals.md`, `docs/canonical/48_actor_authority_and_identity.md`
- truth, evidence, memory, and files: `docs/canonical/03_memory_system.md`, `docs/canonical/10_file_management.md`, `docs/canonical/59_truth_grounding_and_evidence_governance.md`, `docs/canonical/60_truth_source_router.md`, `docs/canonical/61_evidence_manifest_and_claim_verification.md`
- runtime and adapters: `docs/canonical/57_local_runtime_and_offline_agent_infrastructure.md`, `docs/canonical/58_agent_sdk_and_a2a_adapter_strategy.md`
- security and privacy: `docs/canonical/23_security_threat_model.md`, `docs/canonical/24_data_lifecycle_and_privacy.md`, `docs/canonical/45_trusted_computing_base.md`, `docs/canonical/50_data_classification_policy.md`, `docs/canonical/51_redaction_and_safe_debugging.md`
- mobile/device planning: `docs/canonical/64_mobile_companion_and_device_capability_broker.md`, `docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md`
- external tooling and Codex plugin governance: `docs/canonical/66_external_tooling_and_codex_plugin_governance.md`

## Active API Docs

```text
docs/api/README.md
docs/api/openapi_contract.md
docs/api/route_inventory.md
```

API docs describe implemented validation, dry-run, simulated, status, and preview-only routes. Future mobile/device routes are not implemented.

## Active Control Center Docs

```text
docs/control_center/CONTROL_CENTER_CONTRACT.md
docs/control_center/DASHBOARD_SNAPSHOT.md
docs/control_center/ACTION_PREVIEW_POLICY.md
docs/control_center/WEB_CONTROL_CENTER_SHELL.md
docs/control_center/FRONTEND_SAFETY_POLICY.md
docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md
```

M12 Control Center docs describe backend contracts, read-only dashboard snapshots, and action preview policy only. M13 adds a local Web Control Center shell that consumes those routes, renders safe mock fallback data, and submits only preview-only action requests. v0.17.1 hardens the frontend safety contract and verifier coverage. The shell is not production authority and does not add execution capability.

## Active Runtime Docs

```text
docs/runtime/model_runtime_adapter_harness.md
docs/runtime/local_loopback_model_runtime.md
docs/runtime/RUNTIME_READINESS.md
docs/runtime/MANUAL_SMOKE_REPORTS.md
docs/runtime/RUNTIME_CAPABILITY_MATRIX.md
```

Model runtime docs distinguish simulated runtime behavior, dev/manual loopback readiness, fixed-prompt manual smoke, and non-authoritative model output. They do not describe general production model execution.

M11 runtime readiness docs describe status/report validation only. They do not describe production runtime execution. v0.15.1 clarifies local loopback policy as supported validation-only and `fake_manual_loopback_smoke` as a fake/test report origin only.

## Active Remote Worker and Private Mesh Docs

```text
docs/remote/REMOTE_WORKER_FOUNDATION.md
docs/remote/REMOTE_NODE_SECURITY_MODEL.md
docs/remote/REMOTE_JOB_ENVELOPE.md
docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md
docs/remote/TAILNET_TRANSPORT_POLICY.md
docs/decisions/remote_worker_tailnet_foundation.md
docs/decisions/ADR-open-source-first-private-networking.md
```

Remote workers remain foundation-only. Private mesh, Headscale, generic WireGuard, Tailscale, tailnet, and LAN entries remain planned/disabled metadata only.

## Active Mobile and Device Capability Planning Docs

```text
docs/canonical/64_mobile_companion_and_device_capability_broker.md
docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md
docs/backlog/mobile_companion_backlog.md
docs/backlog/device_capability_broker_backlog.md
docs/schemas/mobile_device_manifest.schema.todo.md
docs/schemas/mobile_sensor_permission_manifest.schema.todo.md
docs/schemas/device_capability_manifest.schema.todo.md
```

Mobile Companion and Device Capability Broker docs are planning only. No mobile app, sensor API, OS permission integration, background service, or runtime Device Capability Broker exists.

## Active Security and Privacy Docs

```text
docs/security/approval_authority.md
docs/canonical/23_security_threat_model.md
docs/canonical/24_data_lifecycle_and_privacy.md
docs/canonical/30_agent_constitution.md
docs/canonical/42_autonomy_levels_and_standing_approvals.md
docs/canonical/45_trusted_computing_base.md
docs/canonical/50_data_classification_policy.md
docs/canonical/51_redaction_and_safe_debugging.md
```

## Backlog and Future Work

```text
docs/backlog/parking_lot.md
docs/backlog/external_agent_tooling_watchlist.md
docs/backlog/mobile_companion_backlog.md
docs/backlog/device_capability_broker_backlog.md
docs/backlog/codex_plugin_enablement_backlog.md
```

Backlog files are not implementation claims.

## Development Tooling Inventory

```text
docs/maintenance/codex_plugin_capability_inventory.md
docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md
docs/tooling/CODEX_PLUGIN_RISK_POLICY.md
docs/canonical/66_external_tooling_and_codex_plugin_governance.md
docs/backlog/codex_plugin_enablement_backlog.md
```

The Codex plugin capability inventory and risk policy record available development-assist tool classes and the approval boundaries for future UI, Mobile Companion, Desktop Companion, CI, security, and documentation milestones. They are guidance-only and do not enable plugins, activate build tools, add runtime behavior, or authorize credential-bearing workflows.

## Release Notes Index

Current release notes: `docs/release_notes/v0_17_1.md`

Historical release notes remain under `docs/release_notes/`. Historical docs may mention old active baselines in historical context; they are not the current source of truth.

## How To Verify Docs

Run:

```bash
python scripts/verify_documentation_integrity.py
python scripts/verify_current_baseline.py
python scripts/verify_all.py
python scripts/run_foundation_gate.py
```

The documentation integrity verifier checks active version alignment, active release docs, active index/map/checklist docs, mobile/private mesh doc presence, and obvious unsafe implementation claims.
