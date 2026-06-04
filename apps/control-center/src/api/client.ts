import { mockControlCenterData } from "../mocks/controlCenterData";
import type {
  ActionPreviewDecision,
  ActionPreviewRequest,
  BackendConnectionSummary,
  ControlCenterDashboardSnapshot,
  ControlCenterData,
  ControlCenterManifest,
  ControlCenterStatus,
  ResultEnvelope,
  RuntimeCapabilityMatrix,
  RuntimeReadinessReport,
  ApiRouteInventory
} from "./types";
import { resolveApiBaseUrl } from "./baseUrl";
import { API_ENDPOINTS } from "./endpoints";
import { sanitizeForDisplay } from "./redaction";

const API_BASE_POLICY = resolveApiBaseUrl(import.meta.env.VITE_UAA_API_BASE_URL);

async function readEnvelope<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_POLICY.baseUrl}${endpoint}`, {
    headers: { Accept: "application/json" }
  });
  const data = (await response.json()) as ResultEnvelope<T> | T;
  if (!response.ok) {
    throw new Error(sanitizeForDisplay(data));
  }
  if (typeof data === "object" && data !== null && ("ok" in data || "success" in data)) {
    const envelope = data as ResultEnvelope<T>;
    const result = envelope.result ?? envelope.data;
    const ok = envelope.ok ?? envelope.success;
    if (!ok || result === undefined) {
      throw new Error(sanitizeForDisplay(envelope.error?.message ?? "Request failed"));
    }
    return result;
  }
  return data as T;
}

export async function loadControlCenterData(): Promise<ControlCenterData> {
  if (!API_BASE_POLICY.allowed) {
    return withConnection(mockControlCenterData, {
      state: "mock_fallback",
      safeMessage: API_BASE_POLICY.safeMessage,
      usingMockData: true,
      warnings: API_BASE_POLICY.warnings
    });
  }

  const results = await Promise.allSettled([
    readEnvelope<ControlCenterManifest>(API_ENDPOINTS.controlCenterManifest),
    readEnvelope<ControlCenterDashboardSnapshot>(API_ENDPOINTS.controlCenterDashboard),
    readEnvelope<ControlCenterStatus>(API_ENDPOINTS.controlCenterStatus),
    readEnvelope<ApiRouteInventory>(API_ENDPOINTS.controlCenterRoutes),
    readEnvelope<RuntimeReadinessReport>(API_ENDPOINTS.runtimeReadiness),
    readEnvelope<RuntimeCapabilityMatrix>(API_ENDPOINTS.runtimeCapabilityMatrix)
  ] as const);

  const manifest = fulfilledValue(results[0]);
  const dashboard = fulfilledValue(results[1]);
  const status = fulfilledValue(results[2]);
  const routes = fulfilledValue(results[3]);
  const runtimeReadiness = fulfilledValue(results[4]);
  const capabilityMatrix = fulfilledValue(results[5]);
  const fulfilledCount = results.filter((result) => result.status === "fulfilled").length;

  if (fulfilledCount === 0) {
    return withConnection(mockControlCenterData, {
      state: "mock_fallback",
      safeMessage: "Backend unavailable; showing non-authoritative mock fallback data.",
      usingMockData: true,
      warnings: ["LOCAL_BACKEND_UNAVAILABLE", "MOCK_DATA_ONLY"]
    });
  }

  const data: ControlCenterData = {
    manifest: manifest ?? mockControlCenterData.manifest,
    dashboard: dashboard ?? mockControlCenterData.dashboard,
    status: status ?? mockControlCenterData.status,
    routes: routes ?? mockControlCenterData.routes,
    runtimeReadiness: runtimeReadiness ?? mockControlCenterData.runtimeReadiness,
    capabilityMatrix: capabilityMatrix ?? mockControlCenterData.capabilityMatrix,
    m15Review: mockControlCenterData.m15Review,
    m16Trace: mockControlCenterData.m16Trace,
    m17Knowledge: mockControlCenterData.m17Knowledge,
    m18Runtime: mockControlCenterData.m18Runtime,
    m36FileReview: mockControlCenterData.m36FileReview,
    source: "api",
    connection: mockControlCenterData.connection
  };

  if (fulfilledCount === results.length) {
    return withConnection(data, {
      state: "online",
      safeMessage: "Live data came from local read-only/preview-only backend API routes.",
      usingMockData: false,
      warnings: []
    });
  }

  return withConnection(data, {
    state: "degraded",
    safeMessage: "Some local backend summaries were unavailable; non-authoritative mock fallback filled missing panels.",
    usingMockData: true,
    warnings: ["LOCAL_BACKEND_DEGRADED", "PARTIAL_MOCK_FALLBACK"]
  });
}

export async function submitActionPreview(request: ActionPreviewRequest): Promise<ActionPreviewDecision> {
  if (!API_BASE_POLICY.allowed) {
    throw new Error(API_BASE_POLICY.safeMessage);
  }
  const response = await fetch(`${API_BASE_POLICY.baseUrl}${API_ENDPOINTS.actionPreview}`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });
  const data = (await response.json()) as ResultEnvelope<ActionPreviewDecision>;
  const decision = data.result ?? data.data;
  if (!response.ok || !decision) {
    throw new Error(sanitizeForDisplay(data.error?.message ?? "Preview request was rejected safely."));
  }
  return decision;
}

function withConnection(
  data: ControlCenterData,
  connection: Pick<BackendConnectionSummary, "state" | "safeMessage" | "usingMockData" | "warnings">
): ControlCenterData {
  return {
    ...data,
    connection: {
      ...connection,
      apiBaseLabel: API_BASE_POLICY.label,
      checkedAt: new Date().toISOString()
    }
  };
}

function fulfilledValue<T>(result: PromiseSettledResult<T>): T | undefined {
  return result.status === "fulfilled" ? result.value : undefined;
}
