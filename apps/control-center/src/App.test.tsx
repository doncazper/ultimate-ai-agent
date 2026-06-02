import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { API_ENDPOINTS, isAllowedReadEndpoint, isPreviewEndpoint, READ_ENDPOINTS } from "./api/endpoints";
import { EmptyState, LoadingState } from "./components/DataState";

function mockFetchWithFallback() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      throw new Error("backend unavailable");
    })
  );
}

describe("Web Control Center shell", () => {
  it("renders mock dashboard summaries without production authority", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/dashboard");
    render(<App />);

    expect(await screen.findByText("Mock fallback active")).toBeInTheDocument();
    expect(screen.getByText(/Backend unavailable; showing non-authoritative mock fallback data/i)).toBeInTheDocument();
    expect(screen.getByText(/API base: relative local API/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Overview" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Runtime" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Foundation Gate" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "API Routes" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Action Preview" })).toBeInTheDocument();
    expect(screen.getByText("Runtime readiness")).toBeInTheDocument();
    expect(screen.getByText("API boundary")).toBeInTheDocument();
    expect(screen.getByText(/No authority to run actions/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /execute/i })).not.toBeInTheDocument();
  });

  it("renders runtime, remote, mobile, and plugin governance panels as safe summaries", async () => {
    mockFetchWithFallback();

    window.history.pushState({}, "", "/runtime");
    const { unmount } = render(<App />);
    expect(await screen.findByText("Capability Matrix")).toBeInTheDocument();
    expect(screen.getByText("cloud_provider_runtime")).toBeInTheDocument();
    unmount();

    window.history.pushState({}, "", "/remote-workers");
    const remote = render(<App />);
    expect(await screen.findByText("Remote workers")).toBeInTheDocument();
    expect(screen.getByText("Private mesh")).toBeInTheDocument();
    remote.unmount();

    window.history.pushState({}, "", "/mobile-planning");
    const mobile = render(<App />);
    expect(await screen.findByText("Mobile Planning")).toBeInTheDocument();
    expect(screen.getByText(/Sensor access enabled: no/i)).toBeInTheDocument();
    mobile.unmount();

    window.history.pushState({}, "", "/plugin-governance");
    render(<App />);
    expect(await screen.findByText("Plugin Governance")).toBeInTheDocument();
    expect(screen.getByText(/Plugin enablement allowed: no/i)).toBeInTheDocument();
  });

  it("renders clear headings for every local shell page", async () => {
    const expectedHeadings = [
      ["/", /Dashboard overview/i],
      ["/dashboard", /Dashboard overview/i],
      ["/runtime", /Runtime readiness/i],
      ["/foundation-gate", /Foundation Gate/i],
      ["/api-routes", /API Routes/i],
      ["/approvals", /Approvals/i],
      ["/remote-workers", /Remote worker boundary/i],
      ["/mobile-planning", /Mobile planning/i],
      ["/plugin-governance", /Plugin governance/i],
      ["/action-preview", /Action Preview/i]
    ] as const;

    for (const [path, heading] of expectedHeadings) {
      mockFetchWithFallback();
      window.history.pushState({}, "", path);
      const { unmount } = render(<App />);
      expect(await screen.findByRole("heading", { name: heading })).toBeInTheDocument();
      unmount();
      vi.unstubAllGlobals();
    }
  });

  it("renders loading and empty states with safe operational copy", () => {
    const { rerender } = render(<LoadingState />);
    expect(screen.getByRole("status")).toHaveTextContent(/loading local control center/i);
    expect(screen.getByText(/checking local backend connection state/i)).toBeInTheDocument();
    expect(screen.getByText(/read-only/i)).toBeInTheDocument();

    rerender(<EmptyState title="No routes listed" message="No API routes were returned by the local mock." />);
    expect(screen.getByRole("status")).toHaveTextContent(/No routes listed/i);
    expect(screen.getByText(/No API routes were returned/i)).toBeInTheDocument();
  });

  it("keeps backend checking state informational while reads are pending", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => undefined)));
    window.history.pushState({}, "", "/dashboard");
    render(<App />);

    expect(screen.getByRole("status")).toHaveTextContent(/checking local backend connection state/i);
    expect(screen.queryByRole("button", { name: /execute/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /approve/i })).not.toBeInTheDocument();
  });

  it("submits action preview only to the preview endpoint", async () => {
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      if (options?.method === "POST") {
        return new Response(
          JSON.stringify({
            ok: true,
            result: {
              decision_id: "decision_mock",
              request_id: "frontend_preview_request",
              allowed: true,
              status: "allowed_preview",
              reason_codes: ["CONTROL_CENTER_PREVIEW_ALLOWED"],
              safe_message: "Control Center preview is allowed. No action was executed.",
              preview_summary: "Preview only; no action was executed.",
              metadata: { executed: false }
            }
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        );
      }
      throw new Error("backend unavailable");
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/action-preview");
    render(<App />);

    expect(await screen.findByText(/Preview only action request/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Risk level/i)).toBeInTheDocument();
    expect(screen.getByText(/High and critical previews remain non-execution decisions/i)).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /Blocked execution action/i })).toBeDisabled();
    fireEvent.click(await screen.findByRole("button", { name: /preview action/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(API_ENDPOINTS.actionPreview, expect.any(Object)));
    const [, options] = fetchMock.mock.calls.find((call) => call[1]?.method === "POST") ?? [];
    expect(options?.method).toBe("POST");
    expect(screen.queryByRole("button", { name: /execute/i })).not.toBeInTheDocument();
  });

  it("shows live local backend connection state only when every read request succeeds", async () => {
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      if (options?.method === "POST") {
        throw new Error("unexpected preview request");
      }
      return new Response(JSON.stringify(envelopeForReadEndpoint(String(url))), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/dashboard");
    render(<App />);

    expect(await screen.findByText("Backend online")).toBeInTheDocument();
    expect(screen.getByText(/Live data came from local read-only\/preview-only backend API routes/i)).toBeInTheDocument();
    expect(screen.queryByText(/Mock fallback active/i)).not.toBeInTheDocument();
  });

  it("shows degraded local backend state when only part of the read set succeeds", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (String(url).includes(API_ENDPOINTS.runtimeCapabilityMatrix)) {
        throw new Error("capability matrix unavailable");
      }
      return new Response(JSON.stringify(envelopeForReadEndpoint(String(url))), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/dashboard");
    render(<App />);

    expect(await screen.findByText("Backend degraded")).toBeInTheDocument();
    expect(screen.getByText(/Some local backend summaries were unavailable/i)).toBeInTheDocument();
    expect(screen.getByText(/non-authoritative mock fallback filled missing panels/i)).toBeInTheDocument();
  });

  it("does not expose dangerous action control labels", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/action-preview");
    render(<App />);

    await screen.findByText(/Preview only action request/i);

    for (const label of [/execute/i, /^run$/i, /send/i, /deploy/i, /enable/i, /approve/i]) {
      expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    }
  });

  it("renders unsafe preview decisions as blocked without claiming execution", async () => {
    const fetchMock = vi.fn(async (_url: string, options?: RequestInit) => {
      const body = JSON.parse(String(options?.body ?? "{}")) as { target_ref?: string };
      const reason = body.target_ref?.includes("remote-workers")
        ? "REMOTE_EXECUTION_BLOCKED"
        : body.target_ref?.includes("plugins")
          ? "PLUGIN_ENABLEMENT_BLOCKED"
          : body.target_ref?.includes("mobile")
            ? "MOBILE_SENSOR_BLOCKED"
            : "CONTROL_CENTER_PREVIEW_ALLOWED";
      return new Response(
        JSON.stringify({
          ok: reason === "CONTROL_CENTER_PREVIEW_ALLOWED",
          result: {
            decision_id: "decision_mock",
            request_id: "frontend_preview_request",
            allowed: false,
            status: "blocked",
            reason_codes: [reason],
            safe_message: "Control Center preview was blocked by read-only policy.",
            preview_summary: "Preview only; no action was executed.",
            metadata: { executed: false }
          }
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/action-preview");
    render(<App />);

    fireEvent.change(await screen.findByLabelText(/Target reference/i), {
      target: { value: "remote-workers/dispatch/job" }
    });
    fireEvent.click(screen.getByRole("button", { name: /preview action/i }));

    expect(await screen.findByText("blocked")).toBeInTheDocument();
    expect(screen.getByText(/REMOTE_EXECUTION_BLOCKED/i)).toBeInTheDocument();
    expect(screen.getByText(/no action was executed/i)).toBeInTheDocument();
  });

  it("redacts secret-like input before user-visible output", async () => {
    vi.stubGlobal("fetch", vi.fn());
    window.history.pushState({}, "", "/action-preview");
    render(<App />);

    fireEvent.change(await screen.findByLabelText(/Purpose/i), {
      target: { value: "token=supersecretvalue123" }
    });
    fireEvent.click(screen.getByRole("button", { name: /preview action/i }));

    expect(await screen.findByText(/Secret-like input was redacted/i)).toBeInTheDocument();
    expect(screen.queryByText(/supersecretvalue123/i)).not.toBeInTheDocument();
  });

  it("redacts secret-like backend preview errors before display", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            ok: false,
            error: {
              code: "SAFE_REJECTION",
              message: "Preview rejected because token=supersecretvalue123 was invalid."
            }
          }),
          { status: 400, headers: { "Content-Type": "application/json" } }
        )
      )
    );
    window.history.pushState({}, "", "/action-preview");
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: /preview action/i }));

    expect(await screen.findByText(/Preview rejected because \[redacted\] was invalid/i)).toBeInTheDocument();
    expect(screen.queryByText(/supersecretvalue123/i)).not.toBeInTheDocument();
  });

  it("keeps read endpoints separate from the single preview POST endpoint", () => {
    expect(READ_ENDPOINTS).not.toContain(API_ENDPOINTS.actionPreview);
    expect(API_ENDPOINTS.actionPreview).toBe("/control-center/actions/preview");
    expect(isPreviewEndpoint(API_ENDPOINTS.actionPreview)).toBe(true);
    expect(isAllowedReadEndpoint(API_ENDPOINTS.controlCenterDashboard)).toBe(true);
    expect(isAllowedReadEndpoint("/control-center/actions/execute")).toBe(false);
    expect(isPreviewEndpoint("/control-center/plugins/enable")).toBe(false);
  });
});

function envelopeForReadEndpoint(url: string) {
  const data = {
    [API_ENDPOINTS.controlCenterManifest]: {
      ...mockApiData.manifest,
      version: "0.18.1"
    },
    [API_ENDPOINTS.controlCenterDashboard]: {
      ...mockApiData.dashboard,
      baseline_version: "0.18.1"
    },
    [API_ENDPOINTS.controlCenterStatus]: mockApiData.status,
    [API_ENDPOINTS.controlCenterRoutes]: mockApiData.routes,
    [API_ENDPOINTS.runtimeReadiness]: {
      ...mockApiData.runtimeReadiness,
      baseline_version: "0.18.1"
    },
    [API_ENDPOINTS.runtimeCapabilityMatrix]: {
      ...mockApiData.capabilityMatrix,
      baseline_version: "0.18.1"
    }
  };
  const endpoint = Object.keys(data).find((candidate) => url.endsWith(candidate));
  return { ok: true, result: data[endpoint as keyof typeof data] };
}

const mockApiData = {
  manifest: {
    manifest_id: "test_manifest",
    version: "0.18.1",
    generated_at: "2026-01-01T00:00:00Z",
    declared_capabilities: ["control_center_read_only_dashboard"],
    blocked_capabilities: ["runtime_execution", "remote_dispatch", "mobile_sensor_access", "plugin_enablement"],
    api_route_refs: ["/control-center/dashboard", "/control-center/actions/preview"],
    metadata: { read_only: true, preview_only: true, production_control_center: false },
    surfaces: []
  },
  dashboard: {
    snapshot_id: "test_dashboard",
    baseline_version: "0.18.1",
    generated_at: "2026-01-01T00:00:00Z",
    system_status: {
      label: "Control Center",
      status: "read_only",
      summary: "Read-only local backend summary."
    },
    foundation_gate_summary: {
      status: "passed",
      passed_count: 1,
      failed_count: 0,
      summary: "Gate summary only."
    },
    runtime_readiness_summary: {
      status: "report_only",
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
      summary: "Read-only approval summary."
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
    warnings: [],
    blockers: [],
    next_recommended_action: "review_local_backend_status",
    metadata: { read_only: true, preview_only: true }
  },
  status: {
    status: "available",
    read_only: true,
    preview_only: true,
    frontend_shell: true,
    production_authority: false,
    message: "Local backend status only."
  },
  routes: {
    route_count: 8,
    routes: [
      {
        path: "/control-center/dashboard",
        methods: ["GET"],
        operation_id: "get_control_center_dashboard",
        tags: ["control-center"],
        validation_only: true
      }
    ]
  },
  runtimeReadiness: {
    report_id: "test_readiness",
    baseline_version: "0.18.1",
    status: "report_only",
    production_ready: false,
    real_model_runtime_ready: false,
    remote_execution_ready: false,
    mobile_sensor_ready: false,
    plugin_or_native_build_ready: false,
    capability_matrix_ref: "test_matrix",
    warnings: [],
    blockers: [],
    metadata: { model_output_authoritative: false }
  },
  capabilityMatrix: {
    matrix_id: "test_matrix",
    baseline_version: "0.18.1",
    metadata: { no_model_was_called: true },
    entries: []
  }
};
