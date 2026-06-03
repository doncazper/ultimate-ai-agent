Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# README Import v0.15.1

Status: Active baseline after the M11 Runtime Readiness Taxonomy Clarification patch.

Import these files first:

```text
README.md
VERSION.md
ultimate_ai_agent_master_plan_v0_15_1.md
docs/DOCUMENTATION_INDEX.md
docs/canonical/CANONICAL_DOC_MAP.md
docs/canonical/09_roadmap.md
docs/canonical/20_user_control_center.md
docs/canonical/21_consent_and_permissions_ledger.md
docs/canonical/23_security_threat_model.md
docs/canonical/24_data_lifecycle_and_privacy.md
docs/canonical/30_agent_constitution.md
docs/canonical/37_tool_broker.md
docs/canonical/42_autonomy_levels_and_standing_approvals.md
docs/canonical/45_trusted_computing_base.md
docs/canonical/63_observability_standards_mapping.md
docs/canonical/64_mobile_companion_and_device_capability_broker.md
docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md
docs/canonical/66_external_tooling_and_codex_plugin_governance.md
docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md
docs/tooling/CODEX_PLUGIN_RISK_POLICY.md
docs/backlog/codex_plugin_enablement_backlog.md
docs/api/README.md
docs/api/openapi_contract.md
docs/api/route_inventory.md
docs/runtime/model_runtime_adapter_harness.md
docs/runtime/local_loopback_model_runtime.md
docs/runtime/RUNTIME_READINESS.md
docs/runtime/MANUAL_SMOKE_REPORTS.md
docs/runtime/RUNTIME_CAPABILITY_MATRIX.md
docs/remote/REMOTE_WORKER_FOUNDATION.md
docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md
docs/maintenance/documentation_integrity_checklist.md
docs/implementation/foundation_gate_implementation_plan_v0_15_1.md
```

v0.15.1 is a clarification-only patch on top of v0.15.0. It keeps `local_loopback_policy` as supported validation-only policy support and documents that real smoke execution remains manual-only, approval-gated, fixed-prompt-only, and non-authoritative. It explicitly records `fake_manual_loopback_smoke` as a fake/test report origin only.

v0.15.1 adds no runtime execution, cloud/provider calls, remote execution, live mesh/tailnet integrations, mobile sensor access, plugin enablement, native builds, dependencies, routes, production persistence, or production readiness claims.
