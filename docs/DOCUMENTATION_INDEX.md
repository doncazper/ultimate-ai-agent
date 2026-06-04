# Documentation Index

Current active baseline: **v0.32.1**

This index is the active entrypoint for documentation navigation. Historical release documents remain in the repository for audit history, but active truth starts with the current baseline files listed here.

## Start Here

```text
README.md
VERSION.md
docs/README.md
docs/canonical/CANONICAL_DOC_MAP.md
docs/canonical/09_roadmap.md
docs/roadmap/README.md
docs/archive/README.md
docs/archive/releases/v0_32_1/README_IMPORT.md
docs/archive/releases/v0_32_1/master_plan.md
docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md
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
docs/runtime/LOCAL_MODEL_RUNTIME_ACTIVATION_CONTRACT.md
docs/runtime/LOCAL_RUNTIME_PROVIDER_PROFILES.md
docs/runtime/LOCAL_RUNTIME_ENDPOINT_POLICY.md
docs/runtime/LOCAL_RUNTIME_HEALTH_PROBE_PLAN.md
docs/runtime/LOCAL_RUNTIME_ACTIVATION_SECURITY_MODEL.md
docs/runtime/LOCAL_RUNTIME_ACTIVATION_NON_GOALS.md
docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md
docs/runtime/FIRST_LOCAL_LLM_CALL.md
docs/runtime/FIRST_LOCAL_LLM_CALL_M23.md
docs/runtime/M23_FIXED_PROMPT_POLICY.md
docs/runtime/M23_LOCAL_MODEL_CALL_POLICY.md
docs/runtime/M23_LOCAL_MODEL_CALL_SAFETY.md
docs/runtime/M23_LOCAL_MODEL_CALL_RECEIPTS.md
docs/runtime/M23_NON_AUTHORITATIVE_OUTPUT_POLICY.md
docs/runtime/M23_MANUAL_CLI_USAGE.md
docs/runtime/M23_TO_M24_BOUNDARY.md
docs/memory/MEMORY_PROVIDER_ABSTRACTION.md
docs/memory/LOCAL_MEMORY_STORE.md
docs/memory/MEMORY_RECORD_SCHEMA.md
docs/memory/MEMORY_WRITE_POLICY.md
docs/memory/MEMORY_REVIEW_AND_PROVENANCE.md
docs/memory/MEMORY_SOURCE_PRIORITY.md
docs/memory/MEMORY_RECALL_PLANNING.md
docs/memory/MEMORY_RETENTION_DELETE_EXPORT.md
docs/memory/MEMORY_CONFLICT_AND_STALENESS.md
docs/memory/MEMORY_DEDUP_DECAY_ARCHIVE.md
docs/memory/MEMORY_SECURITY_MODEL.md
docs/memory/MEMORY_NON_GOALS.md
docs/memory/MEMORYOS_REVIEW_INCORPORATION.md
docs/memory/M24_TO_M25_BOUNDARY.md
docs/truth/TRUTH_SOURCE_ROUTER.md
docs/truth/EVIDENCE_CLAIM_CHECKER.md
docs/truth/TRUTH_SOURCE_PRIORITY.md
docs/truth/CLAIM_EVIDENCE_CHAIN.md
docs/truth/CLAIM_VERIFICATION_POLICY.md
docs/truth/CLAIM_CONFLICT_AND_STALENESS.md
docs/truth/MEMORY_TRUTH_BOUNDARY.md
docs/truth/TRUTH_NON_GOALS.md
docs/truth/M25_TO_M26_BOUNDARY.md
docs/recall/GROUNDED_RECALL_ROUTER.md
docs/recall/CONTEXT_PACK_BUILDER.md
docs/recall/RECALL_SOURCE_PRIORITY.md
docs/recall/RECALL_CANDIDATE_POLICY.md
docs/recall/CONTEXT_PACK_SAFETY.md
docs/recall/RECALL_NON_GOALS.md
docs/recall/M26_TO_M27_BOUNDARY.md
docs/tools/TOOL_BROKER_V2.md
docs/tools/SAFE_TOOL_INTENT_CONTRACTS.md
docs/tools/TOOL_AUTHORITY_BOUNDARY.md
docs/tools/TOOL_INTENT_RECEIPT_PLAN.md
docs/tools/M27_TO_M28_BOUNDARY.md
docs/approvals/APPROVAL_AUTHORITY_V2.md
docs/approvals/ACTION_POLICY.md
docs/approvals/APPROVAL_GRANT_BINDING.md
docs/approvals/APPROVAL_EXPIRY_REVOCATION_REPLAY.md
docs/approvals/ACTION_RISK_AND_SIDE_EFFECT_POLICY.md
docs/approvals/APPROVAL_REF_NOT_AUTHORITY.md
docs/approvals/ACTION_POLICY_DECISION_ENVELOPE.md
docs/approvals/APPROVAL_RECEIPT_PLAN.md
docs/approvals/APPROVAL_AUTHORITY_V2_NON_GOALS.md
docs/approvals/M28_TO_M29_BOUNDARY.md
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
- consent, tools, approvals, and authority: `docs/canonical/21_consent_and_permissions_ledger.md`, `docs/canonical/37_tool_broker.md`, `docs/tools/TOOL_BROKER_V2.md`, `docs/tools/SAFE_TOOL_INTENT_CONTRACTS.md`, `docs/tools/TOOL_AUTHORITY_BOUNDARY.md`, `docs/tools/TOOL_INTENT_RECEIPT_PLAN.md`, `docs/tools/M27_TO_M28_BOUNDARY.md`, `docs/approvals/APPROVAL_AUTHORITY_V2.md`, `docs/approvals/ACTION_POLICY.md`, `docs/approvals/APPROVAL_GRANT_BINDING.md`, `docs/approvals/APPROVAL_EXPIRY_REVOCATION_REPLAY.md`, `docs/approvals/ACTION_RISK_AND_SIDE_EFFECT_POLICY.md`, `docs/approvals/APPROVAL_REF_NOT_AUTHORITY.md`, `docs/approvals/ACTION_POLICY_DECISION_ENVELOPE.md`, `docs/approvals/APPROVAL_RECEIPT_PLAN.md`, `docs/approvals/APPROVAL_AUTHORITY_V2_NON_GOALS.md`, `docs/approvals/M28_TO_M29_BOUNDARY.md`, `docs/canonical/42_autonomy_levels_and_standing_approvals.md`, `docs/canonical/48_actor_authority_and_identity.md`
- truth, evidence, memory, and files: `docs/canonical/03_memory_system.md`, `docs/canonical/10_file_management.md`, `docs/canonical/59_truth_grounding_and_evidence_governance.md`, `docs/canonical/60_truth_source_router.md`, `docs/canonical/61_evidence_manifest_and_claim_verification.md`, `docs/truth/TRUTH_SOURCE_ROUTER.md`, `docs/truth/EVIDENCE_CLAIM_CHECKER.md`, `docs/truth/TRUTH_SOURCE_PRIORITY.md`, `docs/truth/CLAIM_EVIDENCE_CHAIN.md`, `docs/truth/CLAIM_VERIFICATION_POLICY.md`, `docs/truth/CLAIM_CONFLICT_AND_STALENESS.md`, `docs/truth/MEMORY_TRUTH_BOUNDARY.md`, `docs/truth/TRUTH_NON_GOALS.md`, `docs/truth/M25_TO_M26_BOUNDARY.md`
- runtime and adapters: `docs/canonical/57_local_runtime_and_offline_agent_infrastructure.md`, `docs/canonical/58_agent_sdk_and_a2a_adapter_strategy.md`
- security and privacy: `docs/canonical/23_security_threat_model.md`, `docs/canonical/24_data_lifecycle_and_privacy.md`, `docs/canonical/45_trusted_computing_base.md`, `docs/canonical/50_data_classification_policy.md`, `docs/canonical/51_redaction_and_safe_debugging.md`
- mobile/device planning: `docs/canonical/64_mobile_companion_and_device_capability_broker.md`, `docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md`, `docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md`, `docs/device_capabilities/CAPABILITY_MANIFEST_SCHEMA.md`, `docs/device_capabilities/DEVICE_PERMISSION_LIFECYCLE.md`, `docs/device_capabilities/CAPTURE_INTENT_CONTRACT.md`, `docs/device_capabilities/SENSOR_BOUNDARY_AND_NON_GOALS.md`, `docs/device_capabilities/DEVICE_TRUST_AND_REVOCATION_CONTRACT.md`, `docs/device_capabilities/DEVICE_RECEIPT_AND_REDACTION_POLICY.md`, `docs/device_capabilities/DEVICE_CAPABILITY_SECURITY_MODEL.md`, `docs/device_capabilities/DEVICE_CAPABILITY_BROKER_NON_GOALS.md`, `docs/mobile/MOBILE_COMPANION_CONTRACT.md`, `docs/mobile/MOBILE_SENSOR_BOUNDARY.md`, `docs/mobile/MOBILE_SECURITY_MODEL.md`
- external tooling and Codex plugin governance: `docs/canonical/66_external_tooling_and_codex_plugin_governance.md`
- UI/client strategy: `docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md`, `docs/ui/CLIENT_SURFACE_ROLES.md`, `docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md`, `docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md`
- OpenWebUI bridge contract: `docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md`, `docs/openwebui/CHAT_SHELL_INTEGRATION_CONTRACT.md`, `docs/openwebui/SESSION_TRANSCRIPT_REF_POLICY.md`, `docs/openwebui/OPENWEBUI_SECURITY_MODEL.md`, `docs/openwebui/OPENWEBUI_AUTHORITY_BOUNDARY.md`, `docs/openwebui/OPENWEBUI_NON_GOALS.md`, `docs/openwebui/OPENWEBUI_FUTURE_INTEGRATION_STAGES.md`
- memory provider and local store: `docs/memory/MEMORY_PROVIDER_ABSTRACTION.md`, `docs/memory/LOCAL_MEMORY_STORE.md`, `docs/memory/MEMORY_WRITE_POLICY.md`, `docs/memory/MEMORY_SECURITY_MODEL.md`, `docs/memory/M24_TO_M25_BOUNDARY.md`
- M25 truth source router and evidence claim checker: `docs/truth/TRUTH_SOURCE_ROUTER.md`, `docs/truth/EVIDENCE_CLAIM_CHECKER.md`, `docs/truth/TRUTH_SOURCE_PRIORITY.md`, `docs/truth/CLAIM_EVIDENCE_CHAIN.md`, `docs/truth/CLAIM_VERIFICATION_POLICY.md`, `docs/truth/CLAIM_CONFLICT_AND_STALENESS.md`, `docs/truth/MEMORY_TRUTH_BOUNDARY.md`, `docs/truth/TRUTH_NON_GOALS.md`, `docs/truth/M25_TO_M26_BOUNDARY.md`

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

M12 Control Center docs describe backend contracts, read-only dashboard snapshots, and action preview policy only. M13 adds a local Web Control Center shell that consumes those routes, renders safe mock fallback data, and submits only preview-only action requests. v0.17.4 polishes local shell reviewability and adds safe local browser smoke reporting documentation. v0.18.0 / M14 stabilizes local backend connection behavior with local-only API base URL policy and visible live/degraded/mock fallback states. v0.18.1 hardens M14 connection safety for public/private non-loopback hosts, URL credentials, secret-like query parameters, and unknown/checking states. v0.18.2 adds Open Design governance docs for Control Center and Mobile Companion UI work. v0.19.0 / M15 adds read-only/preview-only approval queue, receipt viewer, and event viewer UI surfaces with redacted summary-only data. v0.19.1 hardens M15 approval authority and redacted-detail safety copy plus static verifier/Foundation Gate checks. v0.20.0 / M16 adds a read-only event timeline and run/receipt trace viewer with safe refs and Foundation Gate evidence summaries. v0.20.1 hardens M16 trace/redaction safety, second-trace selection coverage, generated build-output hygiene, and no-backend-route Foundation Gate checks. v0.21.0 / M17 adds read-only evidence, file ref, and memory ref summary viewers. v0.21.1 hardens M17 selected-state reviewability, alternate safe mock refs, frontend tests, static verifier coverage, docs, and Foundation Gate checks. v0.21.2 normalizes developer verification commands around `.venv/bin/python` and Makefile targets. v0.22.0 / M18 adds read-only local runtime status and validation-only manual smoke report summary surfaces. v0.23.0 / M19 adds mobile companion contract/API planning only. v0.23.1 hardens M19 roadmap status and mobile contract safety tests only. v0.24.0 / M20 adds Device Capability Broker Contract as contract-only planning and validation. v0.24.1 hardens M20 Device Capability Broker Contract safety without adding runtime authority. v0.25.0 / M21 adds OpenWebUI Bridge + Chat Shell Integration Contract as contract/planning/validation only. v0.25.1 hardens M21 OpenWebUI content-mode semantics, authority text validation, and verifier/Foundation Gate scanning without adding execution capability. v0.26.0 / M22 adds Local Model Runtime Activation Contract as contract/planning/validation only. v0.26.1 hardens M22 verifier precision and metadata key secret hygiene without adding execution capability. v0.27.0 / M23 adds manual fixed-prompt local model call contracts and CLI-only execution gating without backend routes or production authority.

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

v0.25.1 hardens M21 OpenWebUI Bridge + Chat Shell Integration Contract safety while keeping M21 contract/planning/validation only. OpenWebUI remains the preferred conversational web shell and is not the agent brain. Python Agent Core remains authority. M21 allows only summary/ref/redacted-preview content modes, rejects blocked raw/future modes for refs and envelopes, permits safe negated authority-boundary text, rejects positive OpenWebUI authority claims, and scans the OpenWebUI bridge package for forbidden runtime/config fragments. M21 adds no OpenWebUI integration, deployment config, Docker config, OpenWebUI plugins/functions/pipelines/tools/admin/auth/cookie/API key/admin token workflow, browser profile access, live OpenWebUI connection, backend API route, frontend feature, OpenWebUI runtime execution, user-content local LLM call, model/provider call, tool execution, memory write, file access, remote execution, browser automation, Computer Use, mobile sensor access, plugin enablement, dependency, or production authority. v0.26.0 implements M22 as contract-only metadata/validation. v0.26.1 hardens M22 verifier precision and metadata key secret hygiene only. v0.27.0 implements M23 as manual fixed-prompt local call only.

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
docs/runtime/LOCAL_MODEL_RUNTIME_ACTIVATION_CONTRACT.md
docs/runtime/LOCAL_RUNTIME_PROVIDER_PROFILES.md
docs/runtime/LOCAL_RUNTIME_ENDPOINT_POLICY.md
docs/runtime/LOCAL_RUNTIME_HEALTH_PROBE_PLAN.md
docs/runtime/LOCAL_RUNTIME_ACTIVATION_SECURITY_MODEL.md
docs/runtime/LOCAL_RUNTIME_ACTIVATION_NON_GOALS.md
docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md
```

Model runtime docs distinguish simulated runtime behavior, dev/manual loopback readiness, fixed-prompt manual smoke, and non-authoritative model output. They do not describe general production model execution.

M11 runtime readiness docs describe status/report validation only. They do not describe production runtime execution. v0.15.1 clarifies local loopback policy as supported validation-only and `fake_manual_loopback_smoke` as a fake/test report origin only.

v0.26.0 / M22 adds Local Model Runtime Activation Contract docs as contract/planning/validation only. v0.26.1 hardens M22 verifier precision, metadata key secret hygiene, route-count test ownership, and duplicate docs wording. v0.27.0 / M23 adds the first bounded manual local model call path. v0.27.1 hardens M23 endpoint-label safety, approval evidence checks, response redaction/caps, CLI guardrails, policy docs, static verification, Foundation Gate criteria, and Foundation Gate report atomic write/replace safety. v0.28.0 / M24 adds Memory Provider Abstraction + Local Memory Store as governed reviewed-write-only local memory foundation. v0.28.1 repairs the public M24 memory request contract and hardens M24 memory safety checks. v0.28.2 removes the duplicate/conflicting v0.28.1 planned/provisional roadmap row only. v0.29.0 / M25 adds Truth Source Router + Evidence Claim Checker as deterministic local contracts over provided refs only. v0.29.1 hardens M25 unknown/arbitrary truth ref denial. v0.29.2 hardens local-dev API authority and raw preview safety without adding routes. v0.29.3 reorganizes documentation archives and active/historical classification only, v0.29.4 repairs legacy archive references and self-maintaining docs policy coverage, v0.29.5 polishes duplicated policy wording, v0.30.0 implements M26 Grounded Recall Router + Evidence-Linked Context Pack Builder as deterministic local contracts over provided candidates only, v0.30.1 hardens M26 source_ref/source_kind consistency, v0.31.0 implements M27 Tool Broker v2 + Safe Tool Intent Contracts as validation-only and preview-only contracts, v0.31.1 normalizes the GitHub README polish commit into a clean docs-only baseline, v0.32.0 implements M28 Approval Authority v2 + Action Policy Expansion as policy-only and decision-only contracts, and v0.32.1 hardens M28 evaluator revalidation for raw/secret action inputs. Memory is recall, not authority. Memory is not ground truth. v0.32.1 adds no backend route, action execution, real tool execution, shell execution, file mutation, memory write, Event Ledger mutation, network call, web search, model/provider call, plugin enablement, browser automation, mobile/device access, remote execution, context injection, dependency, production persistence, M29 work, or production authority. OpenAPI path count remains `74`. M29-M40 remain planned/provisional.

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

Current release notes: `docs/release_notes/v0_32_1.md`

Historical release notes remain under `docs/release_notes/`. Historical docs may mention old active baselines in historical context; they are not the current source of truth.

Historical release import and master-plan packets live under `docs/archive/releases/`.
Retired planning packets live under `docs/archive/retired_plans/`. Archive docs are
audit records, not current implementation guidance.

Future milestone and review prompts must follow
`docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md`, including the rule that
legacy historical verifiers are not current release gates and must not live at
root or under active `scripts/`.

## How To Verify Docs

Run:

```bash
make doctor
make verify
```

The documentation integrity verifier checks active version alignment, active release docs, active index/map/checklist docs, design governance docs, OpenWebUI/CCC strategy docs, post-M20 roadmap projection docs, mobile/private mesh doc presence, and obvious unsafe implementation claims.
