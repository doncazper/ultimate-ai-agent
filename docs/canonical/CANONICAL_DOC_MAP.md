# Canonical Document Map

Current active baseline: **v0.21.1**

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
| Memory Service | `docs/canonical/03_memory_system.md`, `docs/canonical/41_memory_retrieval_v1.md` |
| File Manager | `docs/canonical/10_file_management.md` |
| Truth Source Router | `docs/canonical/60_truth_source_router.md` |
| Evidence Manifest | `docs/canonical/59_truth_grounding_and_evidence_governance.md`, `docs/canonical/61_evidence_manifest_and_claim_verification.md` |
| Model Router | `docs/canonical/26_model_routing_strategy.md` |
| Cost Governor | `docs/canonical/25_cost_and_resource_governor.md` |
| API Boundary | `docs/api/README.md`, `docs/api/openapi_contract.md`, `docs/api/route_inventory.md` |
| Roadmap Sequencing | `docs/canonical/09_roadmap.md`, `docs/roadmap/MILESTONE_CHARTERS.md`, `docs/roadmap/NEXT_SEQUENCE_v0_17_5.md`, `docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md`, `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`, `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`, `docs/roadmap/ECOSYSTEM_WATCHLIST.md`, `docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md` |
| Control Center | `docs/canonical/20_user_control_center.md`, `docs/control_center/CONTROL_CENTER_CONTRACT.md`, `docs/control_center/DASHBOARD_SNAPSHOT.md`, `docs/control_center/ACTION_PREVIEW_POLICY.md`, `docs/control_center/WEB_CONTROL_CENTER_SHELL.md`, `docs/control_center/FRONTEND_SAFETY_POLICY.md`, `docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md`, `docs/control_center/LOCAL_BACKEND_CONNECTION.md`, `docs/control_center/LOCAL_BROWSER_SMOKE.md`, `docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md`, `docs/control_center/APPROVAL_QUEUE_UI.md`, `docs/control_center/RECEIPT_EVENT_VIEWER.md`, `docs/control_center/APPROVAL_RECEIPT_UI_SAFETY.md`, `docs/control_center/EVENT_TIMELINE_UI.md`, `docs/control_center/RUN_RECEIPT_TRACE_VIEWER.md`, `docs/control_center/TRACE_REDACTION_POLICY.md`, `docs/control_center/EVIDENCE_VIEWER.md`, `docs/control_center/FILE_REFERENCE_VIEWER.md`, `docs/control_center/MEMORY_VIEWER.md`, `docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md` |
| Open Design System and UI Governance | `docs/design/OPEN_DESIGN_SYSTEM.md`, `docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md`, `docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md`, `docs/design/ACCESSIBILITY_BASELINE.md`, `docs/design/DESIGN_TOOLING_POLICY.md`, `docs/design/DESIGN_TOKEN_ROADMAP.md`, `docs/design/UI_COPY_AND_ACTION_LANGUAGE.md`, `docs/design/DESIGN_ARTIFACT_GOVERNANCE.md`, `docs/design/COMPONENT_TAXONOMY.md`, `docs/design/RESPONSIVE_LAYOUT_BASELINE.md`, `docs/backlog/open_design_system_backlog.md` |
| OpenWebUI and CCC Client Strategy | `docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md`, `docs/ui/CLIENT_SURFACE_ROLES.md`, `docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md`, `docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md` |
| Approval Authority | `docs/security/approval_authority.md`, `docs/canonical/42_autonomy_levels_and_standing_approvals.md` |
| Model Runtime Adapter Harness | `docs/runtime/model_runtime_adapter_harness.md` |
| Local Loopback Runtime | `docs/runtime/local_loopback_model_runtime.md`, `docs/canonical/57_local_runtime_and_offline_agent_infrastructure.md` |
| Manual Smoke Harness | `docs/runtime/local_loopback_model_runtime.md` |
| Runtime Readiness | `docs/runtime/RUNTIME_READINESS.md`, `docs/runtime/MANUAL_SMOKE_REPORTS.md`, `docs/runtime/RUNTIME_CAPABILITY_MATRIX.md` |
| Remote Worker Foundation | `docs/remote/REMOTE_WORKER_FOUNDATION.md`, `docs/remote/REMOTE_NODE_SECURITY_MODEL.md`, `docs/remote/REMOTE_JOB_ENVELOPE.md` |
| Private Mesh / Headscale / WireGuard / Tailscale Taxonomy | `docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md`, `docs/remote/TAILNET_TRANSPORT_POLICY.md`, `docs/decisions/ADR-open-source-first-private-networking.md` |
| Mobile Companion | `docs/canonical/64_mobile_companion_and_device_capability_broker.md`, `docs/backlog/mobile_companion_backlog.md` |
| Device Capability Broker | `docs/canonical/64_mobile_companion_and_device_capability_broker.md`, `docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md`, `docs/backlog/device_capability_broker_backlog.md` |
| Codex Plugin and External Tooling Governance | `docs/canonical/66_external_tooling_and_codex_plugin_governance.md`, `docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md`, `docs/tooling/CODEX_PLUGIN_RISK_POLICY.md`, `docs/backlog/codex_plugin_enablement_backlog.md` |
| Foundation Gate | `docs/implementation/foundation_gate_implementation_plan_v0_21_1.md`, `docs/evals/foundation_gate_eval.md` |
| Testing Strategy | `docs/testing/test_strategy_v0.md`, `docs/testing/contract_test_matrix_v0_5_0.md`, `docs/testing/shadow_replay_plan_v0_5_0.md` |

## Source-of-Truth Hierarchy

```text
1. Current user instruction and current release prompt
2. VERSION.md and active README/import/master/release docs
3. Canonical docs and active ADRs
4. API/runtime docs and verifier scripts
5. Historical release docs and older import/master plans
6. Backlog and parking-lot notes
```

Historical docs are audit records, not active implementation claims.

Before writing future milestone prompts, check the roadmap sequencing docs. Parked local branches or tags are not accepted baseline and must not be merged automatically.
