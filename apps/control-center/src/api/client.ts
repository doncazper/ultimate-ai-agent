import { mockControlCenterData } from "../mocks/controlCenterData";
import type {
  ActionPreviewDecision,
  ActionPreviewRequest,
  ControlCenterDashboardSnapshot,
  ControlCenterData,
  ControlCenterManifest,
  ControlCenterStatus,
  ResultEnvelope,
  RuntimeCapabilityMatrix,
  RuntimeReadinessReport,
  ApiRouteInventory
} from "./types";
import { API_ENDPOINTS } from "./endpoints";
import { sanitizeForDisplay } from "./redaction";

const API_BASE_URL = (import.meta.env.VITE_UAA_API_BASE_URL ?? "").replace(/\/$/, "");

async function readEnvelope<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
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
  try {
    const [manifest, dashboard, status, routes, runtimeReadiness, capabilityMatrix] = await Promise.all([
      readEnvelope<ControlCenterManifest>(API_ENDPOINTS.controlCenterManifest),
      readEnvelope<ControlCenterDashboardSnapshot>(API_ENDPOINTS.controlCenterDashboard),
      readEnvelope<ControlCenterStatus>(API_ENDPOINTS.controlCenterStatus),
      readEnvelope<ApiRouteInventory>(API_ENDPOINTS.controlCenterRoutes),
      readEnvelope<RuntimeReadinessReport>(API_ENDPOINTS.runtimeReadiness),
      readEnvelope<RuntimeCapabilityMatrix>(API_ENDPOINTS.runtimeCapabilityMatrix)
    ]);
    return { manifest, dashboard, status, routes, runtimeReadiness, capabilityMatrix, source: "api" };
  } catch {
    return mockControlCenterData;
  }
}

export async function submitActionPreview(request: ActionPreviewRequest): Promise<ActionPreviewDecision> {
  const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.actionPreview}`, {
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
