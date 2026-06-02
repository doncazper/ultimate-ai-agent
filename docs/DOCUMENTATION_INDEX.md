# Documentation Index

Current active baseline: **v0.25.1**

This index is the active entrypoint for documentation navigation. Historical release documents remain in the repository for audit history, but active truth starts with the current baseline files listed here.

## Start Here

```text
README.md
VERSION.md
README_IMPORT_v0_25_1.md
ultimate_ai_agent_master_plan_v0_25_1.md
docs/canonical/CANONICAL_DOC_MAP.md
docs/canonical/09_roadmap.md
docs/roadmap/MILESTONE_CHARTERS.md
docs/roadmap/NEXT_SEQUENCE_v0_17_5.md
docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md
docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md
docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md
docs/roadmap/ECOSYSTEM_WATCHLIST.md
docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md
docs/maintenance/documentation_integrity_checklist.md
docs/maintenance/codex_plugin_capability_inventory.md
docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md
docs/tooling/CODEX_PLUGIN_RISK_POLICY.md
docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md
docs/ui/CLIENT_SURFACE_ROLES.md
docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md
docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md
docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md
docs/openwebui/CHAT_SHELL_INTEGRATION_CONTRACT.md
docs/openwebui/SESSION_TRANSCRIPT_REF_POLICY.md
docs/openwebui/OPENWEBUI_SECURITY_MODEL.md
docs/openwebui/OPENWEBUI_AUTHORITY_BOUNDARY.md
docs/openwebui/OPENWEBUI_NON_GOALS.md
docs/openwebui/OPENWEBUI_FUTURE_INTEGRATION_STAGES.md
docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md
docs/device_capabilities/CAPABILITY_MANIFEST_SCHEMA.md
docs/device_capabilities/DEVICE_PERMISSION_LIFECYCLE.md
docs/device_capabilities/CAPTURE_INTENT_CONTRACT.md
docs/device_capabilities/SENSOR_BOUNDARY_AND_NON_GOALS.md
docs/device_capabilities/DEVICE_TRUST_AND_REVOCATION_CONTRACT.md
docs/device_capabilities/DEVICE_RECEIPT_AND_REDACTION_POLICY.md
docs/device_capabilities/DEVICE_CAPABILITY_SECURITY_MODEL.md
docs/device_capabilities/DEVICE_CAPABILITY_BROKER_NON_GOALS.md
docs/mobile/MOBILE_COMPANION_CONTRACT.md
docs/mobile/MOBILE_CLIENT_SURFACE_ROLES.md
docs/mobile/MOBILE_API_PLANNING.md
docs/mobile/MOBILE_PERMISSION_RECEIPT_FLOW.md
docs/mobile/MOBILE_SENSOR_BOUNDARY.md
docs/mobile/MOBILE_SECURITY_MODEL.md
docs/mobile/MOBILE_CAPTURE_POLICY.md
docs/mobile/CCC_IOS_ANDROID_STRATEGY.md
docs/mobile/MOBILE_PAIRING_TRUST_PLANNING.md
docs/mobile/MOBILE_COMPANION_NON_GOALS.md
docs/control_center/APPROVAL_QUEUE_UI.md
docs/control_center/RECEIPT_EVENT_VIEWER.md
docs/control_center/APPROVAL_RECEIPT_UI_SAFETY.md
docs/control_center/EVENT_TIMELINE_UI.md
docs/control_center/RUN_RECEIPT_TRACE_VIEWER.md
docs/control_center/TRACE_REDACTION_POLICY.md
docs/control_center/EVIDENCE_VIEWER.md
docs/control_center/FILE_REFERENCE_VIEWER.md
docs/control_center/MEMORY_VIEWER.md
docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md
docs/control_center/LOCAL_RUNTIME_STATUS_UI.md
docs/control_center/MANUAL_SMOKE_CONTROL_SURFACE.md
docs/control_center/RUNTIME_SMOKE_UI_SAFETY.md
```

## Active Canonical Docs

The active canonical docs live in `docs/canonical/`. Use `docs/canonical/CANONICAL_DOC_MAP.md` to map systems to canonical files.

Key active canonical groups:

- roadmap and sequencing: `docs/canonical/09_roadmap.md`, `docs/roadmap/MILESTONE_CHARTERS.md`, `docs/roadmap/NEXT_SEQUENCE_v0_17_5.md`, `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`, `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`, `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`
- user control: `docs/canonical/20_user_control_center.md`
- consent, tools, approvals, and authority: `docs/canonical/21_consent_and_permissions_ledger.md`, `docs/canonical/37_tool_broker.md`, `docs/canonical/42_autonomy_levels_and_standing_approvals.md`, `docs/canonical/48_actor_authority_and_identity.md`
- truth, evidence, memory, and files: `docs/canonical/03_memory_system.md`, `docs/canonical/10_file_management.md`, `docs/canonical/59_truth_grounding_and_evidence_governance.md`, `docs/canonical/60_truth_source_router.md`, `docs/canonical/61_evidence_manifest_and_claim_verification.md`
- runtime and adapters: `docs/canonical/57_local_runtime_and_offline_agent_infrastructure.md`, `docs/canonical/58_agent_sdk_and_a2a_adapter_strategy.md`
- security and privacy: `docs/canonical/23_security_threat_model.md`, `docs/canonical/24_data_lifecycle_and_privacy.md`, `docs/canonical/45_trusted_computing_base.md`, `docs/canonical/50_data_classification_policy.md`, `docs/canonical/51_redaction_and_safe_debugging.md`
- mobile/device planning: `docs/canonical/64_mobile_companion_and_device_capability_broker.md`, `docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md`, `docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md`, `docs/device_capabilities/CAPABILITY_MANIFEST_SCHEMA.md`, `docs/device_capabilities/DEVICE_PERMISSION_LIFECYCLE.md`, `docs/device_capabilities/CAPTURE_INTENT_CONTRACT.md`, `docs/device_capabilities/SENSOR_BOUNDARY_AND_NON_GOALS.md`, `docs/device_capabilities/DEVICE_TRUST_AND_REVOCATION_CONTRACT.md`, `docs/device_capabilities/DEVICE_RECEIPT_AND_REDACTION_POLICY.md`, `docs/device_capabilities/DEVICE_CAPABILITY_SECURITY_MODEL.md`, `docs/device_capabilities/DEVICE_CAPABILITY_BROKER_NON_GOALS.md`, `docs/mobile/MOBILE_COMPANION_CONTRACT.md`, `docs/mobile/MOBILE_SENSOR_BOUNDARY.md`, `docs/mobile/MOBILE_SECURITY_MODEL.md`
- external tooling and Codex plugin governance: `docs/canonical/66_external_tooling_and_codex_plugin_governance.md`
- UI/client strategy: `docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md`, `docs/ui/CLIENT_SURFACE_ROLES.md`, `docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md`, `docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md`
- OpenWebUI bridge contract: `docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md`, `docs/openwebui/CHAT_SHELL_INTEGRATION_CONTRACT.md`, `docs/openwebui/SESSION_TRANSCRIPT_REF_POLICY.md`, `docs/openwebui/OPENWEBUI_SECURITY_MODEL.md`, `docs/openwebui/OPENWEBUI_AUTHORITY_BOUNDARY.md`, `docs/openwebui/OPENWEBUI_NON_GOALS.md`, `docs/openwebui/OPENWEBUI_FUTURE_INTEGRATION_STAGES.md`

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
docs/control_center/LOCAL_BACKEND_CONNECTION.md
docs/control_center/LOCAL_BROWSER_SMOKE.md
docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md
docs/control_center/APPROVAL_QUEUE_UI.md
docs/control_center/RECEIPT_EVENT_VIEWER.md
docs/control_center/APPROVAL_RECEIPT_UI_SAFETY.md
docs/control_center/EVENT_TIMELINE_UI.md
docs/control_center/RUN_RECEIPT_TRACE_VIEWER.md
docs/control_center/TRACE_REDACTION_POLICY.md
docs/control_center/EVIDENCE_VIEWER.md
docs/control_center/FILE_REFERENCE_VIEWER.md
docs/control_center/MEMORY_VIEWER.md
docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md
docs/control_center/LOCAL_RUNTIME_STATUS_UI.md
docs/control_center/MANUAL_SMOKE_CONTROL_SURFACE.md
docs/control_center/RUNTIME_SMOKE_UI_SAFETY.md
```

M12 Control Center docs describe backend contracts, read-only dashboard snapshots, and action preview policy only. M13 adds a local Web Control Center shell that consumes those routes, renders safe mock fallback data, and submits only preview-only action requests. v0.17.4 polishes local shell reviewability and adds safe local browser smoke reporting documentation. v0.18.0 / M14 stabilizes local backend connection behavior with local-only API base URL policy and visible live/degraded/mock fallback states. v0.18.1 hardens M14 connection safety for public/private non-loopback hosts, URL credentials, secret-like query parameters, and unknown/checking states. v0.18.2 adds Open Design governance docs for Control Center and Mobile Companion UI work. v0.19.0 / M15 adds read-only/preview-only approval queue, receipt viewer, and event viewer UI surfaces with redacted summary-only data. v0.19.1 hardens M15 approval authority and redacted-detail safety copy plus static verifier/Foundation Gate checks. v0.20.0 / M16 adds a read-only event timeline and run/receipt trace viewer with safe refs and Foundation Gate evidence summaries. v0.20.1 hardens M16 trace/redaction safety, second-trace selection coverage, generated build-output hygiene, and no-backend-route Foundation Gate checks. v0.21.0 / M17 adds read-only evidence, file ref, and memory ref summary viewers. v0.21.1 hardens M17 selected-state reviewability, alternate safe mock refs, frontend tests, static verifier coverage, docs, and Foundation Gate checks. v0.21.2 normalizes developer verification commands around `.venv/bin/python` and Makefile targets. v0.22.0 / M18 adds read-only local runtime status and validation-only manual smoke report summary surfaces. v0.23.0 / M19 adds mobile companion contract/API planning only. v0.23.1 hardens M19 roadmap status and mobile contract safety tests only. v0.24.0 / M20 adds Device Capability Broker Contract as contract-only planning and validation. v0.24.1 hardens M20 Device Capability Broker Contract safety without adding runtime authority. v0.25.0 / M21 adds OpenWebUI Bridge + Chat Shell Integration Contract as contract/planning/validation only. v0.25.1 hardens M21 OpenWebUI content-mode semantics, authority text validation, and verifier/Foundation Gate scanning without adding execution capability.

## Active Design Governance Docs

```text
docs/design/OPEN_DESIGN_SYSTEM.md
docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md
docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md
docs/design/ACCESSIBILITY_BASELINE.md
docs/design/DESIGN_TOOLING_POLICY.md
docs/design/DESIGN_TOKEN_ROADMAP.md
docs/design/UI_COPY_AND_ACTION_LANGUAGE.md
docs/design/DESIGN_ARTIFACT_GOVERNANCE.md
docs/design/COMPONENT_TAXONOMY.md
docs/design/RESPONSIVE_LAYOUT_BASELINE.md
```

v0.18.2 adds Open Design System and UI Design Governance documentation only. The design source of truth is repo-owned docs, reviewed components, and future repo-owned tokens. Design tools, design SaaS, UI generators, screenshot-to-code, and design-to-code systems are not enabled and are not authority.

M15 Approval Queue + Receipt/Event Viewer UI is implemented in v0.19.0 as read-only/preview-only CCC Web summary views. v0.19.1 hardens its authority-boundary and redacted-detail safety checks. v0.20.0 adds M16 Event Timeline + Run/Receipt Trace Viewer as a read-only summary surface. v0.20.1 hardens M16 trace/redaction safety and keeps generated frontend artifacts ignored/untracked. v0.21.0 adds M17 Evidence/File/Memory Viewer as read-only, summary-only CCC Web views. v0.21.1 hardens the existing M17 views without adding approval execution, backend authority, raw data display, or backend API routes. v0.21.2 is dev tooling/docs only and changes no Control Center behavior. v0.22.0 adds M18 local runtime status and manual smoke report summary surfaces; v0.23.0 adds M19 mobile companion contract/API planning only; v0.23.1 hardens M19 roadmap and contract safety checks only.

## Active UI Client Strategy Docs

```text
docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md
docs/ui/CLIENT_SURFACE_ROLES.md
docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md
docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md
```

v0.18.3 clarifies that OpenWebUI is the preferred conversational web shell, CCC means Control Center Clients, and CCC covers CCC Web, CCC iOS, CCC Android, and CCC macOS. Open Design governs custom CCC surfaces and does not replace OpenWebUI. These docs add no OpenWebUI integration, deployment config, frontend feature, backend API route, native app, native build workflow, mobile sensor access, OS permission integration, signing, keystore, provisioning, App Store, or Play Store workflow.

v0.25.1 hardens M21 OpenWebUI Bridge + Chat Shell Integration Contract safety while keeping M21 contract/planning/validation only. OpenWebUI remains the preferred conversational web shell and is not the agent brain. Python Agent Core remains authority. M21 allows only summary/ref/redacted-preview content modes, rejects blocked raw/future modes for refs and envelopes, permits safe negated authority-boundary text, rejects positive OpenWebUI authority claims, and scans the OpenWebUI bridge package for forbidden runtime/config fragments. M21 adds no OpenWebUI integration, deployment config, Docker config, OpenWebUI plugins/functions/pipelines/tools/admin/auth/cookie/API key/admin token workflow, browser profile access, live OpenWebUI connection, backend API route, frontend feature, runtime execution, local LLM call, model/provider call, tool execution, memory write, file access, remote execution, browser automation, Computer Use, mobile sensor access, plugin enablement, dependency, or production authority. M22 and M23 remain planned/provisional.

## Active Post-M20 Roadmap Projection Docs

```text
docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md
docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md
docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md
docs/roadmap/ECOSYSTEM_WATCHLIST.md
docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md
```

v0.18.4 adds post-M20 roadmap projection and M21-M40 capability-layer charters only. M14-M20 remain frozen and unchanged. M21-M40 are planned/provisional and require dedicated future implementation and review prompts. The ecosystem and standards watchlists are watchlist-only and add no integration, plugin enablement, external network, dependency, or parity claim.

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
docs/backlog/open_design_system_backlog.md
```

Backlog files are not implementation claims.

## Roadmap Guardrails

Future prompts must check `docs/roadmap/MILESTONE_CHARTERS.md` and `docs/roadmap/NEXT_SEQUENCE_v0_17_5.md` before selecting milestone scope. Parked work, including local branches or tags, must not be merged, reactivated, or treated as accepted baseline without an explicit reintroduction prompt.

Future prompts after M20 must also read `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`, `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`, and `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md` before implementation.

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

Current release notes: `docs/release_notes/v0_25_1.md`

Historical release notes remain under `docs/release_notes/`. Historical docs may mention old active baselines in historical context; they are not the current source of truth.

## How To Verify Docs

Run:

```bash
make doctor
make verify
```

The documentation integrity verifier checks active version alignment, active release docs, active index/map/checklist docs, design governance docs, OpenWebUI/CCC strategy docs, post-M20 roadmap projection docs, mobile/private mesh doc presence, and obvious unsafe implementation claims.
