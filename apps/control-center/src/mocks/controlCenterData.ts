import type { ControlCenterData } from "../api/types";

export const mockControlCenterData: ControlCenterData = {
  source: "mock",
  manifest: {
    manifest_id: "mock_control_center_manifest_m13",
    version: "0.17.4",
    generated_at: "2026-01-01T00:00:00Z",
    declared_capabilities: ["control_center_read_only_dashboard", "control_center_action_preview"],
    blocked_capabilities: [
      "runtime_execution",
      "model_execution",
      "provider_invocation",
      "remote_dispatch",
      "mobile_sensor_access",
      "plugin_enablement",
      "native_build_control"
    ],
    api_route_refs: [
      "/control-center/manifest",
      "/control-center/dashboard",
      "/control-center/status",
      "/control-center/routes",
      "/control-center/actions/preview"
    ],
    metadata: {
      mock: true,
      read_only: true,
      preview_only: true,
      production_control_center: false
    },
    surfaces: [
      {
        surface: "dashboard",
        status: "available_read_only",
        description: "Mock dashboard summary for local frontend development.",
        route_refs: ["/control-center/dashboard"],
        execution_allowed: false,
        mutation_allowed: false,
        credential_resolution_allowed: false,
        approval_grant_allowed: false,
        metadata: { mock: true }
      },
      {
        surface: "action_preview",
        status: "preview_only",
        description: "Mock preview-only action decision surface.",
        route_refs: ["/control-center/actions/preview"],
        execution_allowed: false,
        mutation_allowed: false,
        credential_resolution_allowed: false,
        approval_grant_allowed: false,
        metadata: { mock: true }
      },
      {
        surface: "remote_workers",
        status: "dry_run_only",
        description: "Remote worker controls remain dry-run-only.",
        route_refs: [],
        execution_allowed: false,
        mutation_allowed: false,
        credential_resolution_allowed: false,
        approval_grant_allowed: false,
        metadata: { mock: true }
      },
      {
        surface: "mobile_planning",
        status: "planned_disabled",
        description: "Mobile capabilities are future planning only.",
        route_refs: [],
        execution_allowed: false,
        mutation_allowed: false,
        credential_resolution_allowed: false,
        approval_grant_allowed: false,
        metadata: { mock: true }
      },
      {
        surface: "plugin_governance",
        status: "planned_disabled",
        description: "Plugin governance is policy-only in this shell.",
        route_refs: [],
        execution_allowed: false,
        mutation_allowed: false,
        credential_resolution_allowed: false,
        approval_grant_allowed: false,
        metadata: { mock: true }
      }
    ]
  },
  dashboard: {
    snapshot_id: "mock_control_center_dashboard_m13",
    baseline_version: "0.17.4",
    generated_at: "2026-01-01T00:00:00Z",
    system_status: {
      label: "Control Center",
      status: "mock_read_only",
      summary: "Mock frontend fallback is read-only and preview-only."
    },
    foundation_gate_summary: {
      status: "mock_passed",
      passed_count: 0,
      failed_count: 0,
      summary: "Mock gate summary only; verify the backend for release evidence."
    },
    runtime_readiness_summary: {
      status: "readiness_report_only",
      production_ready: false,
      real_model_runtime_ready: false,
      remote_execution_ready: false,
      mobile_sensor_ready: false,
      plugin_or_native_build_ready: false
    },
    approval_summary: {
      pending_count: 0,
      approval_grants_created: false,
      arbitrary_approval_ref_authority: false,
      summary: "Mock approval summary only; no approval is granted."
    },
    api_summary: {
      route_count: 74,
      control_center_route_count: 8,
      operation_ids_unique: true,
      execution_routes_present: false
    },
    remote_worker_summary: {
      status: "dry_run_only",
      execution_enabled: false,
      dispatch_enabled: false
    },
    private_mesh_summary: {
      status: "planned_disabled",
      headscale_integrated: false,
      tailscale_integrated: false,
      wireguard_integrated: false
    },
    mobile_planning_summary: {
      status: "planned_disabled",
      sensor_access_enabled: false,
      mobile_app_implemented: false
    },
    plugin_governance_summary: {
      status: "planned_disabled",
      plugin_enablement_allowed: false,
      native_build_tools_enabled: false
    },
    warnings: ["MOCK_DATA_ONLY", "NO_PRODUCTION_AUTHORITY"],
    blockers: [],
    next_recommended_action: "connect_to_local_backend_for_live_status",
    metadata: {
      mock: true,
      read_only: true,
      preview_only: true
    }
  },
  status: {
    status: "mock_available",
    read_only: true,
    preview_only: true,
    frontend_shell: true,
    production_authority: false,
    message: "Mock status fallback; no backend authority is implied."
  },
  routes: {
    route_count: 8,
    routes: [
      {
        path: "/control-center/manifest",
        methods: ["GET"],
        operation_id: "get_control_center_manifest",
        tags: ["control-center"],
        validation_only: true
      },
      {
        path: "/control-center/actions/preview",
        methods: ["POST"],
        operation_id: "preview_control_center_action",
        tags: ["control-center"],
        validation_only: true
      }
    ]
  },
  runtimeReadiness: {
    report_id: "mock_runtime_readiness_m13",
    baseline_version: "0.17.4",
    status: "report_only",
    production_ready: false,
    real_model_runtime_ready: false,
    remote_execution_ready: false,
    mobile_sensor_ready: false,
    plugin_or_native_build_ready: false,
    capability_matrix_ref: "mock_runtime_capability_matrix_m13",
    warnings: ["MOCK_DATA_ONLY"],
    blockers: [],
    metadata: { mock: true, model_output_authoritative: false }
  },
  capabilityMatrix: {
    matrix_id: "mock_runtime_capability_matrix_m13",
    baseline_version: "0.17.4",
    metadata: { mock: true, no_model_was_called: true },
    entries: [
      {
        surface: "simulated_runtime",
        status: "simulated",
        risk_class: "low",
        real_network_allowed: false,
        real_model_call_allowed: false,
        cloud_allowed: false,
        user_content_allowed: false,
        secrets_allowed: false,
        summary: "Simulated adapter only."
      },
      {
        surface: "manual_loopback_smoke",
        status: "manual_only",
        risk_class: "medium",
        real_network_allowed: false,
        real_model_call_allowed: false,
        cloud_allowed: false,
        user_content_allowed: false,
        secrets_allowed: false,
        summary: "Manual fixed-prompt loopback smoke only."
      },
      {
        surface: "cloud_provider_runtime",
        status: "blocked",
        risk_class: "critical",
        real_network_allowed: false,
        real_model_call_allowed: false,
        cloud_allowed: false,
        user_content_allowed: false,
        secrets_allowed: false,
        summary: "Cloud provider runtime is blocked."
      }
    ]
  }
};
