# README Import v0.17.1

Status: Active baseline after the Web Control Center Safety Polish and Frontend Contract Hardening patch.

Import these files first:

```text
README.md
VERSION.md
ultimate_ai_agent_master_plan_v0_17_1.md
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
docs/control_center/CONTROL_CENTER_CONTRACT.md
docs/control_center/DASHBOARD_SNAPSHOT.md
docs/control_center/ACTION_PREVIEW_POLICY.md
docs/control_center/WEB_CONTROL_CENTER_SHELL.md
docs/control_center/FRONTEND_SAFETY_POLICY.md
docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md
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
docs/implementation/foundation_gate_implementation_plan_v0_17_1.md
```

v0.17.1 hardens the local React/Vite/TypeScript Web Control Center shell added in v0.17.0.

v0.17.1 adds clearer preview-only action language, endpoint allowlist helpers, safe blocked-decision display, static frontend safety verification, and Foundation Gate coverage for forbidden frontend endpoints, action labels, browser storage, sensor APIs, native/plugin references, and secret-like fixtures.

v0.17.1 adds no production Control Center authority, public execution API, runtime/model/provider call, remote dispatch, mobile/native app, sensor access, plugin enablement, Chrome authenticated profile control, Computer Use automation, iOS/macOS build workflow, analytics/auth/payment/SaaS SDK, production persistence, external action, or new backend OpenAPI path.
