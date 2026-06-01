# Canonical Document Map

Current active baseline: **v0.14.6**

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
| Approval Authority | `docs/security/approval_authority.md`, `docs/canonical/42_autonomy_levels_and_standing_approvals.md` |
| Model Runtime Adapter Harness | `docs/runtime/model_runtime_adapter_harness.md` |
| Local Loopback Runtime | `docs/runtime/local_loopback_model_runtime.md`, `docs/canonical/57_local_runtime_and_offline_agent_infrastructure.md` |
| Manual Smoke Harness | `docs/runtime/local_loopback_model_runtime.md` |
| Remote Worker Foundation | `docs/remote/REMOTE_WORKER_FOUNDATION.md`, `docs/remote/REMOTE_NODE_SECURITY_MODEL.md`, `docs/remote/REMOTE_JOB_ENVELOPE.md` |
| Private Mesh / Headscale / WireGuard / Tailscale Taxonomy | `docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md`, `docs/remote/TAILNET_TRANSPORT_POLICY.md`, `docs/decisions/ADR-open-source-first-private-networking.md` |
| Mobile Companion | `docs/canonical/64_mobile_companion_and_device_capability_broker.md`, `docs/backlog/mobile_companion_backlog.md` |
| Device Capability Broker | `docs/canonical/64_mobile_companion_and_device_capability_broker.md`, `docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md`, `docs/backlog/device_capability_broker_backlog.md` |
| Codex Plugin and External Tooling Governance | `docs/canonical/66_external_tooling_and_codex_plugin_governance.md`, `docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md`, `docs/tooling/CODEX_PLUGIN_RISK_POLICY.md`, `docs/backlog/codex_plugin_enablement_backlog.md` |
| Foundation Gate | `docs/implementation/foundation_gate_implementation_plan_v0_14_6.md`, `docs/evals/foundation_gate_eval.md` |
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
