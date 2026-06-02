import type { ControlCenterData } from "../api/types";

export const mockControlCenterData: ControlCenterData = {
  source: "mock",
  connection: {
    state: "mock_fallback",
    apiBaseLabel: "relative local API",
    checkedAt: "2026-01-01T00:00:00Z",
    safeMessage: "Backend unavailable; showing non-authoritative mock fallback data.",
    usingMockData: true,
    warnings: ["MOCK_DATA_ONLY", "NO_PRODUCTION_AUTHORITY"]
  },
  manifest: {
    manifest_id: "mock_control_center_manifest_m16",
    version: "0.20.0",
    generated_at: "2026-01-01T00:00:00Z",
    declared_capabilities: [
      "control_center_read_only_dashboard",
      "control_center_action_preview",
      "control_center_m15_review_preview",
      "control_center_m16_timeline_trace_preview"
    ],
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
        surface: "approval_receipt_event_review",
        status: "preview_only",
        description: "Mock approval, receipt, and event review summaries for M15.",
        route_refs: [],
        execution_allowed: false,
        mutation_allowed: false,
        credential_resolution_allowed: false,
        approval_grant_allowed: false,
        metadata: { mock: true, redacted_summary_only: true }
      },
      {
        surface: "event_timeline_trace_viewer",
        status: "preview_only",
        description: "Mock event timeline and run/receipt trace summaries for M16.",
        route_refs: [],
        execution_allowed: false,
        mutation_allowed: false,
        credential_resolution_allowed: false,
        approval_grant_allowed: false,
        metadata: { mock: true, redacted_summary_only: true, external_export_allowed: false }
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
    snapshot_id: "mock_control_center_dashboard_m16",
    baseline_version: "0.20.0",
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
    report_id: "mock_runtime_readiness_m16",
    baseline_version: "0.20.0",
    status: "report_only",
    production_ready: false,
    real_model_runtime_ready: false,
    remote_execution_ready: false,
    mobile_sensor_ready: false,
    plugin_or_native_build_ready: false,
    capability_matrix_ref: "mock_runtime_capability_matrix_m16",
    warnings: ["MOCK_DATA_ONLY"],
    blockers: [],
    metadata: { mock: true, model_output_authoritative: false }
  },
  capabilityMatrix: {
    matrix_id: "mock_runtime_capability_matrix_m16",
    baseline_version: "0.20.0",
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
  },
  m15Review: {
    status: "mock_preview_only",
    readOnly: true,
    previewOnly: true,
    mock: true,
    nonAuthoritative: true,
    authorityBoundary: "Approval Authority handles final decision; Control Center displays summaries only.",
    warningCodes: ["MOCK_DATA_ONLY", "NO_PRODUCTION_AUTHORITY", "REDACTED_SUMMARY_ONLY"],
    approvalQueue: [
      {
        approvalRef: "mock_approval_ref_001",
        status: "pending_review",
        riskLevel: "medium",
        dataClassification: "internal",
        actorSummary: "Local developer session summary",
        requestedActionSummary: "Preview-only policy review for a proposed local workspace change.",
        subjectSummary: "Mock local review subject; no file body or prompt body is shown.",
        reasonCodes: ["CONTROL_CENTER_REVIEW_REQUIRED", "APPROVAL_AUTHORITY_REQUIRED"],
        createdAt: "2026-01-01T00:00:00Z",
        expiresAt: "2026-01-01T01:00:00Z",
        requiredNextAction: "Review in Python Agent Core approval authority.",
        safeMessage: "No approval was granted from this UI.",
        previewOutcomeSummary: "Grant or denial outcome is preview-only and non-authoritative.",
        relatedRefs: ["mock_receipt_ref_001", "mock_event_ref_001"],
        previewOnly: true,
        readOnly: true,
        mock: true
      },
      {
        approvalRef: "mock_approval_ref_002",
        status: "preview_only",
        riskLevel: "low",
        dataClassification: "public",
        actorSummary: "Control Center mock reviewer",
        requestedActionSummary: "Summary inspection request for a redacted receipt.",
        subjectSummary: "Mock receipt summary reference only.",
        reasonCodes: ["SUMMARY_ONLY", "NO_AUTHORITY_GRANTED"],
        createdAt: "2026-01-01T00:10:00Z",
        requiredNextAction: "No action available in the Control Center.",
        safeMessage: "Approval refs are displayed as identifiers only, never as authority.",
        previewOutcomeSummary: "Preview indicates no mutation path.",
        relatedRefs: ["mock_receipt_ref_002"],
        previewOnly: true,
        readOnly: true,
        mock: true
      }
    ],
    receipts: [
      {
        receiptRef: "mock_receipt_ref_001",
        eventRefs: ["mock_event_ref_001"],
        actionTypeSummary: "approval_review_preview",
        actorSummary: "Local developer session summary",
        status: "recorded_summary",
        riskLevel: "medium",
        dataClassification: "internal",
        redactionStatus: "redacted_summary_only",
        safeMessage: "Receipt is a redacted summary; no receipt mutation is available from this UI.",
        timestamp: "2026-01-01T00:02:00Z",
        relatedRefs: ["mock_approval_ref_001"],
        previewOnly: true,
        readOnly: true,
        mock: true
      },
      {
        receiptRef: "mock_receipt_ref_002",
        eventRefs: ["mock_event_ref_002"],
        actionTypeSummary: "event_summary_review",
        actorSummary: "Control Center mock reviewer",
        status: "summary_only",
        riskLevel: "low",
        dataClassification: "public",
        redactionStatus: "redacted_summary_only",
        safeMessage: "Mock receipt summary only; backend evidence remains source of truth.",
        timestamp: "2026-01-01T00:12:00Z",
        relatedRefs: ["mock_approval_ref_002"],
        previewOnly: true,
        readOnly: true,
        mock: true
      }
    ],
    events: [
      {
        eventRef: "mock_event_ref_001",
        eventType: "approval_review_preview",
        actorSummary: "Local developer session summary",
        sourceSurface: "CCC Web mock surface",
        resultStatus: "summary_recorded",
        reasonCodes: ["CONTROL_CENTER_REVIEW_REQUIRED", "REDACTED_SUMMARY_ONLY"],
        timestamp: "2026-01-01T00:02:00Z",
        relatedRefs: ["mock_approval_ref_001", "mock_receipt_ref_001"],
        redactionStatus: "redacted_summary_only",
        safeMessage: "No event action is available from this UI.",
        previewOnly: true,
        readOnly: true,
        mock: true
      },
      {
        eventRef: "mock_event_ref_002",
        eventType: "receipt_summary_view",
        actorSummary: "Control Center mock reviewer",
        sourceSurface: "CCC Web mock surface",
        resultStatus: "summary_only",
        reasonCodes: ["NO_AUTHORITY_GRANTED"],
        timestamp: "2026-01-01T00:12:00Z",
        relatedRefs: ["mock_receipt_ref_002"],
        redactionStatus: "redacted_summary_only",
        safeMessage: "Event record is safe display metadata only.",
        previewOnly: true,
        readOnly: true,
        mock: true
      }
    ]
  },
  m16Trace: {
    status: "mock_preview_only",
    readOnly: true,
    previewOnly: true,
    mock: true,
    nonAuthoritative: true,
    boundarySummary:
      "Trace summaries use refs and safe messages only; Python Agent Core and Event Ledger remain source of truth.",
    warningCodes: ["MOCK_DATA_ONLY", "NO_PRODUCTION_AUTHORITY", "REDACTED_SUMMARY_ONLY", "NO_EXTERNAL_EXPORT"],
    timelineEvents: [
      {
        eventRef: "mock_event_ref_001",
        eventType: "approval_review_preview",
        sourceSurface: "CCC Web mock surface",
        actorSummary: "Local developer session summary",
        timestamp: "2026-01-01T00:02:00Z",
        status: "summary_recorded",
        runRef: "mock_run_ref_001",
        correlationRef: "mock_correlation_ref_001",
        childEventRefs: ["mock_event_ref_002"],
        receiptRefs: ["mock_receipt_ref_001"],
        evidenceRefs: ["mock_evidence_ref_gate_001"],
        redactionStatus: "redacted_summary_only",
        safeMessage: "Timeline event is summary metadata only; no execution path is available.",
        previewOnly: true,
        readOnly: true,
        mock: true
      },
      {
        eventRef: "mock_event_ref_002",
        eventType: "receipt_summary_view",
        sourceSurface: "CCC Web mock surface",
        actorSummary: "Control Center mock reviewer",
        timestamp: "2026-01-01T00:12:00Z",
        status: "summary_only",
        runRef: "mock_run_ref_001",
        correlationRef: "mock_correlation_ref_001",
        parentEventRef: "mock_event_ref_001",
        childEventRefs: [],
        receiptRefs: ["mock_receipt_ref_002"],
        evidenceRefs: ["mock_evidence_ref_gate_001"],
        redactionStatus: "redacted_summary_only",
        safeMessage: "Trace relation is safe display metadata only.",
        previewOnly: true,
        readOnly: true,
        mock: true
      }
    ],
    traceRelations: [
      {
        relationRef: "mock_relation_ref_001",
        relationType: "child",
        fromRef: "mock_event_ref_001",
        toRef: "mock_event_ref_002",
        safeSummary: "Event summary review followed the approval review preview.",
        redactionStatus: "redacted_summary_only"
      },
      {
        relationRef: "mock_relation_ref_002",
        relationType: "receipt",
        fromRef: "mock_event_ref_001",
        toRef: "mock_receipt_ref_001",
        safeSummary: "Receipt summary is linked by ref only.",
        redactionStatus: "redacted_summary_only"
      },
      {
        relationRef: "mock_relation_ref_003",
        relationType: "evidence",
        fromRef: "mock_event_ref_001",
        toRef: "mock_evidence_ref_gate_001",
        safeSummary: "Foundation Gate evidence summary is linked by ref only.",
        redactionStatus: "redacted_summary_only"
      }
    ],
    foundationGateEvidence: [
      {
        evidenceRef: "mock_evidence_ref_gate_001",
        criterionRef: "m16_event_timeline_trace_viewer_safe",
        status: "mock_passed",
        receiptRefs: ["mock_receipt_ref_001"],
        eventRefs: ["mock_event_ref_001", "mock_event_ref_002"],
        safeSummary: "Mock Foundation Gate evidence confirms timeline trace summaries stay read-only and redacted.",
        redactionStatus: "redacted_summary_only"
      }
    ]
  }
};
