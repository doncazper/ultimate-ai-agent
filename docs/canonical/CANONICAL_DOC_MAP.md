# Canonical Document Map

Current active baseline: **v0.30.1**

This map links major systems to their canonical documentation. If a system has both canonical docs and runtime/API docs, canonical docs define principles and sequencing while runtime/API docs define current implementation boundaries.

| System | Canonical Docs |
|---|---|
| Execution Contract | `docs/canonical/35_execution_contract.md` |
| Context Pack | `docs/canonical/36_context_pack.md` |
| Event Ledger | `docs/canonical/22_observability_and_event_ledger.md`, `docs/canonical/63_observability_standards_mapping.md` |
| World State | `docs/canonical/53_structured_world_state.md` |
| Context Budget | `docs/canonical/54_context_budget_and_session_survival.md`, `docs/canonical/55_tool_result_retention_and_context_trimming.md`, `docs/canonical/56_prompt_tool_prefix_cache_policy.md` |
| Consent Ledger | `docs/canonical/21_consent_and_permissions_ledger.md` |
| Tool Broker | `docs/canonical/37_tool_broker.md` |
| Secret Broker | `docs/canonical/40_credentials_secret_broker_and_provider_registry.md` |
| Provider Registry | `docs/canonical/40_credentials_secret_broker_and_provider_registry.md` |
| Memory Service | `docs/canonical/03_memory_system.md`, `docs/canonical/41_memory_retrieval_v1.md`, `docs/memory/MEMORY_PROVIDER_ABSTRACTION.md`, `docs/memory/LOCAL_MEMORY_STORE.md`, `docs/memory/MEMORY_RECORD_SCHEMA.md`, `docs/memory/MEMORY_WRITE_POLICY.md`, `docs/memory/MEMORY_REVIEW_AND_PROVENANCE.md`, `docs/memory/MEMORY_SOURCE_PRIORITY.md`, `docs/memory/MEMORY_RECALL_PLANNING.md`, `docs/memory/MEMORY_RETENTION_DELETE_EXPORT.md`, `docs/memory/MEMORY_CONFLICT_AND_STALENESS.md`, `docs/memory/MEMORY_DEDUP_DECAY_ARCHIVE.md`, `docs/memory/MEMORY_SECURITY_MODEL.md`, `docs/memory/MEMORY_NON_GOALS.md`, `docs/memory/MEMORYOS_REVIEW_INCORPORATION.md`, `docs/memory/M24_TO_M25_BOUNDARY.md` |
| File Manager | `docs/canonical/10_file_management.md` |
| Truth Source Router | `docs/canonical/60_truth_source_router.md`, `docs/truth/TRUTH_SOURCE_ROUTER.md`, `docs/truth/TRUTH_SOURCE_PRIORITY.md`, `docs/truth/CLAIM_VERIFICATION_POLICY.md`, `docs/truth/TRUTH_NON_GOALS.md`, `docs/truth/M25_TO_M26_BOUNDARY.md` |
| Evidence Manifest | `docs/canonical/59_truth_grounding_and_evidence_governance.md`, `docs/canonical/61_evidence_manifest_and_claim_verification.md`, `docs/truth/EVIDENCE_CLAIM_CHECKER.md`, `docs/truth/CLAIM_EVIDENCE_CHAIN.md`, `docs/truth/CLAIM_CONFLICT_AND_STALENESS.md`, `docs/truth/MEMORY_TRUTH_BOUNDARY.md` |
| Grounded Recall Router and Context Pack Builder | `docs/canonical/36_context_pack.md`, `docs/canonical/41_memory_retrieval_v1.md`, `docs/recall/GROUNDED_RECALL_ROUTER.md`, `docs/recall/CONTEXT_PACK_BUILDER.md`, `docs/recall/RECALL_SOURCE_PRIORITY.md`, `docs/recall/RECALL_CANDIDATE_POLICY.md`, `docs/recall/CONTEXT_PACK_SAFETY.md`, `docs/recall/RECALL_NON_GOALS.md`, `docs/recall/M26_TO_M27_BOUNDARY.md` |
| Model Router | `docs/canonical/26_model_routing_strategy.md` |
| Cost Governor | `docs/canonical/25_cost_and_resource_governor.md` |
| API Boundary | `docs/api/README.md`, `docs/api/openapi_contract.md`, `docs/api/route_inventory.md` |
| Roadmap Sequencing | `docs/canonical/09_roadmap.md`, `docs/roadmap/MILESTONE_CHARTERS.md`, `docs/roadmap/NEXT_SEQUENCE_v0_17_5.md`, `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`, `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`, `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`, `docs/roadmap/ECOSYSTEM_WATCHLIST.md`, `docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md` |
| Control Center | `docs/canonical/20_user_control_center.md`, `docs/control_center/CONTROL_CENTER_CONTRACT.md`, `docs/control_center/DASHBOARD_SNAPSHOT.md`, `docs/control_center/ACTION_PREVIEW_POLICY.md`, `docs/control_center/WEB_CONTROL_CENTER_SHELL.md`, `docs/control_center/FRONTEND_SAFETY_POLICY.md`, `docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md`, `docs/control_center/LOCAL_BACKEND_CONNECTION.md`, `docs/control_center/LOCAL_BROWSER_SMOKE.md`, `docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md`, `docs/control_center/APPROVAL_QUEUE_UI.md`, `docs/control_center/RECEIPT_EVENT_VIEWER.md`, `docs/control_center/APPROVAL_RECEIPT_UI_SAFETY.md`, `docs/control_center/EVENT_TIMELINE_UI.md`, `docs/control_center/RUN_RECEIPT_TRACE_VIEWER.md`, `docs/control_center/TRACE_REDACTION_POLICY.md`, `docs/control_center/EVIDENCE_VIEWER.md`, `docs/control_center/FILE_REFERENCE_VIEWER.md`, `docs/control_center/MEMORY_VIEWER.md`, `docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md`, `docs/control_center/LOCAL_RUNTIME_STATUS_UI.md`, `docs/control_center/MANUAL_SMOKE_CONTROL_SURFACE.md`, `docs/control_center/RUNTIME_SMOKE_UI_SAFETY.md` |
| Open Design System and UI Governance | `docs/design/OPEN_DESIGN_SYSTEM.md`, `docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md`, `docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md`, `docs/design/ACCESSIBILITY_BASELINE.md`, `docs/design/DESIGN_TOOLING_POLICY.md`, `docs/design/DESIGN_TOKEN_ROADMAP.md`, `docs/design/UI_COPY_AND_ACTION_LANGUAGE.md`, `docs/design/DESIGN_ARTIFACT_GOVERNANCE.md`, `docs/design/COMPONENT_TAXONOMY.md`, `docs/design/RESPONSIVE_LAYOUT_BASELINE.md`, `docs/backlog/open_design_system_backlog.md` |
| OpenWebUI and CCC Client Strategy | `docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md`, `docs/ui/CLIENT_SURFACE_ROLES.md`, `docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md`, `docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md` |
| OpenWebUI Bridge Contract | `docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md`, `docs/openwebui/CHAT_SHELL_INTEGRATION_CONTRACT.md`, `docs/openwebui/SESSION_TRANSCRIPT_REF_POLICY.md`, `docs/openwebui/OPENWEBUI_SECURITY_MODEL.md`, `docs/openwebui/OPENWEBUI_AUTHORITY_BOUNDARY.md`, `docs/openwebui/OPENWEBUI_NON_GOALS.md`, `docs/openwebui/OPENWEBUI_FUTURE_INTEGRATION_STAGES.md` |
| Approval Authority | `docs/security/approval_authority.md`, `docs/canonical/42_autonomy_levels_and_standing_approvals.md` |
| Model Runtime Adapter Harness | `docs/runtime/model_runtime_adapter_harness.md` |
| Local Loopback Runtime | `docs/runtime/local_loopback_model_runtime.md`, `docs/canonical/57_local_runtime_and_offline_agent_infrastructure.md` |
| Manual Smoke Harness | `docs/runtime/local_loopback_model_runtime.md` |
| Runtime Readiness | `docs/runtime/RUNTIME_READINESS.md`, `docs/runtime/MANUAL_SMOKE_REPORTS.md`, `docs/runtime/RUNTIME_CAPABILITY_MATRIX.md` |
| Local Model Runtime Activation Contract | `docs/runtime/LOCAL_MODEL_RUNTIME_ACTIVATION_CONTRACT.md`, `docs/runtime/LOCAL_RUNTIME_PROVIDER_PROFILES.md`, `docs/runtime/LOCAL_RUNTIME_ENDPOINT_POLICY.md`, `docs/runtime/LOCAL_RUNTIME_HEALTH_PROBE_PLAN.md`, `docs/runtime/LOCAL_RUNTIME_ACTIVATION_SECURITY_MODEL.md`, `docs/runtime/LOCAL_RUNTIME_ACTIVATION_NON_GOALS.md`, `docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md` |
| First Local LLM Call M23 | `docs/runtime/FIRST_LOCAL_LLM_CALL.md`, `docs/runtime/FIRST_LOCAL_LLM_CALL_M23.md`, `docs/runtime/M23_FIXED_PROMPT_POLICY.md`, `docs/runtime/M23_LOCAL_MODEL_CALL_POLICY.md`, `docs/runtime/M23_LOCAL_MODEL_CALL_SAFETY.md`, `docs/runtime/M23_LOCAL_MODEL_CALL_RECEIPTS.md`, `docs/runtime/M23_NON_AUTHORITATIVE_OUTPUT_POLICY.md`, `docs/runtime/M23_MANUAL_CLI_USAGE.md`, `docs/runtime/M23_TO_M24_BOUNDARY.md`, `docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md` |
| Remote Worker Foundation | `docs/remote/REMOTE_WORKER_FOUNDATION.md`, `docs/remote/REMOTE_NODE_SECURITY_MODEL.md`, `docs/remote/REMOTE_JOB_ENVELOPE.md` |
| Private Mesh / Headscale / WireGuard / Tailscale Taxonomy | `docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md`, `docs/remote/TAILNET_TRANSPORT_POLICY.md`, `docs/decisions/ADR-open-source-first-private-networking.md` |
| Mobile Companion | `docs/canonical/64_mobile_companion_and_device_capability_broker.md`, `docs/mobile/MOBILE_COMPANION_CONTRACT.md`, `docs/mobile/MOBILE_CLIENT_SURFACE_ROLES.md`, `docs/mobile/MOBILE_API_PLANNING.md`, `docs/mobile/MOBILE_PERMISSION_RECEIPT_FLOW.md`, `docs/mobile/MOBILE_SENSOR_BOUNDARY.md`, `docs/mobile/MOBILE_SECURITY_MODEL.md`, `docs/mobile/MOBILE_CAPTURE_POLICY.md`, `docs/mobile/CCC_IOS_ANDROID_STRATEGY.md`, `docs/mobile/MOBILE_PAIRING_TRUST_PLANNING.md`, `docs/mobile/MOBILE_COMPANION_NON_GOALS.md`, `docs/backlog/mobile_companion_backlog.md` |
| Device Capability Broker | `docs/canonical/64_mobile_companion_and_device_capability_broker.md`, `docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md`, `docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md`, `docs/device_capabilities/CAPABILITY_MANIFEST_SCHEMA.md`, `docs/device_capabilities/DEVICE_PERMISSION_LIFECYCLE.md`, `docs/device_capabilities/CAPTURE_INTENT_CONTRACT.md`, `docs/device_capabilities/SENSOR_BOUNDARY_AND_NON_GOALS.md`, `docs/device_capabilities/DEVICE_TRUST_AND_REVOCATION_CONTRACT.md`, `docs/device_capabilities/DEVICE_RECEIPT_AND_REDACTION_POLICY.md`, `docs/device_capabilities/DEVICE_CAPABILITY_SECURITY_MODEL.md`, `docs/device_capabilities/DEVICE_CAPABILITY_BROKER_NON_GOALS.md`, `docs/mobile/MOBILE_SENSOR_BOUNDARY.md`, `docs/backlog/device_capability_broker_backlog.md` |
| Codex Plugin and External Tooling Governance | `docs/canonical/66_external_tooling_and_codex_plugin_governance.md`, `docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md`, `docs/tooling/CODEX_PLUGIN_RISK_POLICY.md`, `docs/backlog/codex_plugin_enablement_backlog.md` |
| Foundation Gate | `docs/implementation/foundation_gate_implementation_plan_v0_30_1.md`, `docs/evals/foundation_gate_eval.md` |
| Testing Strategy | `docs/testing/test_strategy_v0.md`, `docs/testing/contract_test_matrix_v0_5_0.md`, `docs/testing/shadow_replay_plan_v0_5_0.md` |
| Documentation Organization | `docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md`, `docs/maintenance/documentation_integrity_checklist.md`, `docs/DOCUMENTATION_INDEX.md`, `docs/archive/README.md` |

## Source-of-Truth Hierarchy

```text
1. Current user instruction and current release prompt
2. VERSION.md, README.md, docs/README.md, and active archived release-packet/release docs
3. Canonical docs and active ADRs
4. API/runtime docs and verifier scripts
5. Historical release docs and older import/master plans
6. Backlog and parking-lot notes
```

Historical docs are audit records, not active implementation claims.

Before writing future milestone prompts, check the roadmap sequencing docs. Parked local branches or tags are not accepted baseline and must not be merged automatically.
