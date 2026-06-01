export const API_ENDPOINTS = {
  health: "/health",
  version: "/version",
  apiManifest: "/api/manifest",
  controlCenterManifest: "/control-center/manifest",
  controlCenterDashboard: "/control-center/dashboard",
  controlCenterStatus: "/control-center/status",
  controlCenterRoutes: "/control-center/routes",
  approvalSummary: "/control-center/approvals/summary",
  runtimeReadinessSummary: "/control-center/runtime-readiness/summary",
  foundationGateSummary: "/control-center/foundation-gate/summary",
  runtimeReadiness: "/runtime/readiness",
  runtimeCapabilityMatrix: "/runtime/capability-matrix",
  actionPreview: "/control-center/actions/preview"
} as const;

export const READ_ENDPOINTS = [
  API_ENDPOINTS.health,
  API_ENDPOINTS.version,
  API_ENDPOINTS.apiManifest,
  API_ENDPOINTS.controlCenterManifest,
  API_ENDPOINTS.controlCenterDashboard,
  API_ENDPOINTS.controlCenterStatus,
  API_ENDPOINTS.controlCenterRoutes,
  API_ENDPOINTS.approvalSummary,
  API_ENDPOINTS.runtimeReadinessSummary,
  API_ENDPOINTS.foundationGateSummary,
  API_ENDPOINTS.runtimeReadiness,
  API_ENDPOINTS.runtimeCapabilityMatrix
] as const;
