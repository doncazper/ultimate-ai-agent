import { afterEach, describe, expect, it, vi } from "vitest";
import { loadControlCenterData } from "./client";
import { API_ENDPOINTS } from "./endpoints";
import { mockControlCenterData } from "../mocks/controlCenterData";

describe("loadControlCenterData summary endpoint wiring", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("prefers dedicated Control Center summaries over embedded dashboard summaries", async () => {
    const directApprovalSummary = {
      ...mockControlCenterData.dashboard.approval_summary,
      pending_count: 7,
      summary: "Dedicated approval summary route.",
    };
    const directRuntimeSummary = {
      ...mockControlCenterData.dashboard.runtime_readiness_summary,
      status: "dedicated_runtime_summary",
    };
    const directFoundationSummary = {
      ...mockControlCenterData.dashboard.foundation_gate_summary,
      status: "dedicated_foundation_summary",
    };

    stubControlCenterFetch({
      ...baseRouteData(),
      [API_ENDPOINTS.controlCenterDashboard]: {
        ...mockControlCenterData.dashboard,
        approval_summary: {
          ...mockControlCenterData.dashboard.approval_summary,
          pending_count: 1,
        },
        runtime_readiness_summary: {
          ...mockControlCenterData.dashboard.runtime_readiness_summary,
          status: "dashboard_runtime_summary",
        },
        foundation_gate_summary: {
          ...mockControlCenterData.dashboard.foundation_gate_summary,
          status: "dashboard_foundation_summary",
        },
      },
      [API_ENDPOINTS.approvalSummary]: directApprovalSummary,
      [API_ENDPOINTS.runtimeReadinessSummary]: directRuntimeSummary,
      [API_ENDPOINTS.foundationGateSummary]: directFoundationSummary,
    });

    const data = await loadControlCenterData();

    expect(data.dashboard.approval_summary).toEqual(directApprovalSummary);
    expect(data.dashboard.runtime_readiness_summary).toEqual(
      directRuntimeSummary,
    );
    expect(data.dashboard.foundation_gate_summary).toEqual(
      directFoundationSummary,
    );
    expect(data.connection.state).toBe("online");
    expect(data.connection.usingMockData).toBe(false);
  });

  it("degrades without mock data when only dedicated summary routes fail", async () => {
    const routeData = baseRouteData();
    delete routeData[API_ENDPOINTS.approvalSummary];
    delete routeData[API_ENDPOINTS.runtimeReadinessSummary];
    delete routeData[API_ENDPOINTS.foundationGateSummary];
    stubControlCenterFetch(routeData);

    const data = await loadControlCenterData();

    expect(data.dashboard.approval_summary).toEqual(
      mockControlCenterData.dashboard.approval_summary,
    );
    expect(data.dashboard.runtime_readiness_summary).toEqual(
      mockControlCenterData.dashboard.runtime_readiness_summary,
    );
    expect(data.dashboard.foundation_gate_summary).toEqual(
      mockControlCenterData.dashboard.foundation_gate_summary,
    );
    expect(data.connection.state).toBe("degraded");
    expect(data.connection.usingMockData).toBe(false);
    expect(data.connection.warnings).toContain(
      "CONTROL_CENTER_SUMMARY_ENDPOINT_FALLBACK",
    );
    expect(data.connection.warnings).not.toContain("PARTIAL_MOCK_FALLBACK");
  });
});

function baseRouteData(): Record<string, unknown> {
  return {
    [API_ENDPOINTS.controlCenterManifest]: mockControlCenterData.manifest,
    [API_ENDPOINTS.controlCenterDashboard]: mockControlCenterData.dashboard,
    [API_ENDPOINTS.controlCenterStatus]: mockControlCenterData.status,
    [API_ENDPOINTS.controlCenterRoutes]: mockControlCenterData.routes,
    [API_ENDPOINTS.runtimeReadiness]: mockControlCenterData.runtimeReadiness,
    [API_ENDPOINTS.runtimeCapabilityMatrix]:
      mockControlCenterData.capabilityMatrix,
    [API_ENDPOINTS.setupAssistantSummary]:
      mockControlCenterData.macosSetupAssistant,
    [API_ENDPOINTS.providerSetupGuide]: mockControlCenterData.providerCatalog,
    [API_ENDPOINTS.controlCenterSettingsStatus]:
      mockControlCenterData.settingsStatus,
    [API_ENDPOINTS.controlCenterLocalModelsStatus]:
      mockControlCenterData.localModelsStatus,
    [API_ENDPOINTS.founderTodaySummary]: mockControlCenterData.founderToday,
    [API_ENDPOINTS.founderEvidenceTimeline]:
      mockControlCenterData.founderEvidenceTimeline,
    [API_ENDPOINTS.founderMemoryReview]:
      mockControlCenterData.founderMemoryReview,
    [API_ENDPOINTS.founderMemoryWorkbench]:
      mockControlCenterData.founderMemoryWorkbench,
    [API_ENDPOINTS.founderMemoryContextPacks]:
      mockControlCenterData.founderMemoryContextPacks,
    [API_ENDPOINTS.founderActionsInbox]:
      mockControlCenterData.founderActionsInbox,
    [API_ENDPOINTS.founderMorningBriefing]:
      mockControlCenterData.founderMorningBriefing,
    [API_ENDPOINTS.founderSourceReadiness]:
      mockControlCenterData.founderSourceReadiness,
    [API_ENDPOINTS.founderStorageStatus]:
      mockControlCenterData.founderStorageStatus,
    [API_ENDPOINTS.approvalSummary]:
      mockControlCenterData.dashboard.approval_summary,
    [API_ENDPOINTS.runtimeReadinessSummary]:
      mockControlCenterData.dashboard.runtime_readiness_summary,
    [API_ENDPOINTS.foundationGateSummary]:
      mockControlCenterData.dashboard.foundation_gate_summary,
  };
}

function stubControlCenterFetch(routeData: Record<string, unknown>): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown) => {
      const path = endpointPath(input);
      if (!Object.prototype.hasOwnProperty.call(routeData, path)) {
        throw new Error(`missing test route fixture for ${path}`);
      }
      return new Response(
        JSON.stringify({
          ok: true,
          data: routeData[path],
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    }),
  );
}

function endpointPath(input: unknown): string {
  if (typeof input === "string") {
    return new URL(input, "http://127.0.0.1").pathname;
  }
  if (input instanceof URL) {
    return input.pathname;
  }
  if (typeof input === "object" && input !== null && "url" in input) {
    return new URL(
      String((input as { url: unknown }).url),
      "http://127.0.0.1",
    ).pathname;
  }
  return new URL(String(input), "http://127.0.0.1").pathname;
}
