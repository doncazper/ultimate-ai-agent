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
  runtimeSmokeReportValidate: "/runtime/smoke-reports/validate",
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

export function isAllowedReadEndpoint(endpoint: string): endpoint is (typeof READ_ENDPOINTS)[number] {
  return READ_ENDPOINTS.includes(endpoint as (typeof READ_ENDPOINTS)[number]);
}

export function isPreviewEndpoint(endpoint: string): endpoint is typeof API_ENDPOINTS.actionPreview {
  return endpoint === API_ENDPOINTS.actionPreview;
}

export function isRuntimeValidationEndpoint(
  endpoint: string
): endpoint is typeof API_ENDPOINTS.runtimeSmokeReportValidate {
  return endpoint === API_ENDPOINTS.runtimeSmokeReportValidate;
}
