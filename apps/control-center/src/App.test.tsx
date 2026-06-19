import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { App } from "./App";
import {
  API_ENDPOINTS,
  isAllowedReadEndpoint,
  isPreviewEndpoint,
  READ_ENDPOINTS,
} from "./api/endpoints";
import { EmptyState, ErrorState, LoadingState } from "./components/DataState";

function mockFetchWithFallback() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      throw new Error("backend unavailable");
    }),
  );
}

describe("Web Control Center shell", () => {
  it("renders mock dashboard summaries without production authority", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/dashboard");
    render(<App />);

    expect(await screen.findByText("Mock fallback active")).toBeInTheDocument();
    expect(
      screen.getByText(/Backend unavailable; showing non-authoritative mock fallback data/i),
    ).toBeInTheDocument();
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
      ["/chat", /^Chat Shell$/i],
      ["/plans", /^Plans$/i],
      ["/models", /^Models$/i],
      ["/runtime", /Runtime readiness/i],
      ["/foundation-gate", /Foundation Gate/i],
      ["/api-routes", /API Routes/i],
      ["/approvals", /Approval Queue/i],
      ["/receipts", /Receipt Viewer/i],
      ["/events", /Event Viewer/i],
      ["/events/timeline", /Event Timeline/i],
      ["/evidence", /Evidence Viewer/i],
      ["/files", /File Reference Viewer/i],
      ["/files/review", /File Review Surface/i],
      ["/context/proposals", /Context Proposal Surface/i],
      ["/memory", /Memory Viewer/i],
      ["/runtime/local", /Local Runtime Status/i],
      ["/runtime/manual-smoke", /Manual Smoke Control Surface/i],
      ["/remote-workers", /Remote worker boundary/i],
      ["/mobile-planning", /Mobile planning/i],
      ["/plugin-governance", /Plugin governance/i],
      ["/settings", /^Settings$/i],
      ["/action-preview", /Action Preview/i],
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

  it("renders accessible operator states for required Control Center surfaces", async () => {
    const requiredSurfaceChecks = [
      {
        path: "/chat",
        heading: /^Chat Shell$/,
        stateHeading: /Chat Shell states/i,
        blocked: /Blocked: dedicated chat shell not implemented/i,
        denied: /Denied: model output is not authority/i,
      },
      {
        path: "/plans",
        heading: /^Plans$/,
        stateHeading: /Plans states/i,
        blocked: /Blocked: product Plans loop incomplete/i,
        denied: /Denied: no unapproved plan execution/i,
      },
      {
        path: "/models",
        heading: /^Models$/,
        stateHeading: /Models states/i,
        blocked: /Blocked: model selection not implemented/i,
        denied: /Denied: no provider or model authority/i,
      },
      {
        path: "/approvals",
        heading: /^Approval Queue$/,
        stateHeading: /Approvals states/i,
        blocked: /Blocked: live approval binding incomplete/i,
        denied: /Denied: no UI approval grant/i,
      },
      {
        path: "/files",
        heading: /^File Reference Viewer$/,
        stateHeading: /Files states/i,
        blocked: /Blocked: broad file workbench incomplete/i,
        denied: /Denied: no unapproved file mutation/i,
      },
      {
        path: "/runtime",
        heading: /^Runtime readiness$/,
        stateHeading: /Runtime states/i,
        blocked: /Blocked: lifecycle controls not scoped/i,
        denied: /Denied: no hidden runtime authority/i,
      },
      {
        path: "/evidence",
        heading: /^Evidence Viewer$/,
        stateHeading: /Evidence states/i,
        blocked: /Blocked: release evidence index incomplete/i,
        denied: /Denied: no sensitive evidence display/i,
      },
      {
        path: "/settings",
        heading: /^Settings$/,
        stateHeading: /Settings states/i,
        blocked: /Blocked: settings routes not implemented/i,
        denied: /Denied: no authority toggle/i,
      },
    ] as const;

    for (const check of requiredSurfaceChecks) {
      mockFetchWithFallback();
      window.history.pushState({}, "", check.path);
      const { unmount } = render(<App />);

      expect(await screen.findByRole("heading", { name: check.heading })).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: check.stateHeading })).toBeInTheDocument();
      expect(screen.getByText(check.blocked)).toBeInTheDocument();
      expect(screen.getByText(check.denied)).toBeInTheDocument();
      expect(screen.getAllByRole("status").length).toBeGreaterThanOrEqual(4);
      expect(screen.getAllByRole("alert").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/Next safe action:/i).length).toBeGreaterThanOrEqual(5);
      expect(screen.queryByRole("button", { name: /^run$/i })).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /^send$/i })).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /^approve$/i })).not.toBeInTheDocument();

      unmount();
      vi.unstubAllGlobals();
    }
  });

  it("covers first product loop browser smoke readiness with truthful mocked and blocked states", async () => {
    const firstLoopStates = {
      openControlCenter: "mocked",
      inspectRuntimeHealthAndModelReadiness: "mocked",
      selectOrApproveLocalGgufModel: "blocked",
      chatShellThroughUaaV1: "blocked",
      createTaskDecompositionPlan: "blocked",
      approveSafeRegisteredCapability: "mocked",
      inspectReceiptAuditLatencyRollback: "mocked",
    };

    expect(firstLoopStates).toEqual({
      openControlCenter: "mocked",
      inspectRuntimeHealthAndModelReadiness: "mocked",
      selectOrApproveLocalGgufModel: "blocked",
      chatShellThroughUaaV1: "blocked",
      createTaskDecompositionPlan: "blocked",
      approveSafeRegisteredCapability: "mocked",
      inspectReceiptAuditLatencyRollback: "mocked",
    });

    mockFetchWithFallback();
    window.history.pushState({}, "", "/dashboard");
    const dashboard = render(<App />);
    expect(await screen.findByRole("heading", { name: /Dashboard overview/i })).toBeInTheDocument();
    expect(screen.getByText("Mock fallback active")).toBeInTheDocument();
    expect(screen.getByText(/Backend unavailable; showing non-authoritative mock fallback data/i)).toBeInTheDocument();
    expect(screen.getByText(/API base: relative local API/i)).toBeInTheDocument();
    expect(screen.getByText(/No authority to run actions/i)).toBeInTheDocument();
    dashboard.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/runtime");
    const runtime = render(<App />);
    expect(await screen.findByRole("heading", { name: /Runtime readiness/i })).toBeInTheDocument();
    expect(screen.getByText(/Production readiness claim/i)).toBeInTheDocument();
    expect(screen.getByText(/Reviewed local model runtime evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/Local contract state only/i)).toBeInTheDocument();
    runtime.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/runtime/local");
    const localRuntime = render(<App />);
    expect(
      await screen.findByRole("heading", { name: /Local Runtime Status/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/NO_RUNTIME_EXECUTION/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Model output remains non-authoritative/i)).toBeInTheDocument();
    localRuntime.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/runtime/manual-smoke");
    const manualSmoke = render(<App />);
    expect(
      await screen.findByRole("heading", { name: /Manual Smoke Control Surface/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Manual smoke reports are safe summaries/i)).toBeInTheDocument();
    expect(screen.getByText(/no smoke attempt was performed/i)).toBeInTheDocument();
    manualSmoke.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/action-preview");
    const actionPreview = render(<App />);
    expect(await screen.findByText(/Preview only action request/i)).toBeInTheDocument();
    expect(screen.getByText(/never runs, enables, grants, deploys, or dispatches anything/i)).toBeInTheDocument();
    expect(screen.getByText(/approval reference is never treated as authority/i)).toBeInTheDocument();
    actionPreview.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/approvals");
    const approvals = render(<App />);
    expect(await screen.findByRole("heading", { name: /Approval Queue/i })).toBeInTheDocument();
    expect(screen.getByText(/No approval was granted from this UI/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Python Agent Core remains the only approval authority/i).length).toBeGreaterThan(0);
    approvals.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/events/timeline");
    const evidence = render(<App />);
    expect(await screen.findByRole("heading", { name: /Event Timeline/i })).toBeInTheDocument();
    expect(screen.getByText(/Trace detail is redacted summary metadata only/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Foundation Gate evidence summary/i).length).toBeGreaterThan(0);
    evidence.unmount();
    vi.unstubAllGlobals();

    for (const forbidden of [
      /raw json/i,
      /completed successfully/i,
      /production ready for external users/i,
      /^execute$/i,
      /^run$/i,
      /^send$/i,
      /^approve$/i,
    ]) {
      expect(screen.queryByText(forbidden)).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: forbidden })).not.toBeInTheDocument();
    }
  });

  it("renders loading and empty states with safe operational copy", () => {
    const { rerender } = render(<LoadingState />);
    expect(screen.getByRole("status")).toHaveTextContent(/loading local control center/i);
    expect(screen.getByText(/checking local backend connection state/i)).toBeInTheDocument();
    expect(screen.getByText(/read-only/i)).toBeInTheDocument();

    rerender(
      <EmptyState
        title="No routes listed"
        message="No API routes were returned by the local mock."
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent(/No routes listed/i);
    expect(screen.getByText(/No API routes were returned/i)).toBeInTheDocument();

    rerender(<ErrorState message="Control Center data could not be loaded safely." />);
    expect(screen.getByRole("alert")).toHaveTextContent(/Control Center data unavailable/i);
    expect(screen.getByText(/Next safe action: verify the local backend/i)).toBeInTheDocument();
  });

  it("keeps backend checking state informational while reads are pending", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise(() => undefined)),
    );
    window.history.pushState({}, "", "/dashboard");
    render(<App />);

    expect(screen.getByRole("status")).toHaveTextContent(
      /checking local backend connection state/i,
    );
    expect(screen.queryByRole("button", { name: /execute/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /approve/i })).not.toBeInTheDocument();
  });

  it("renders M15 approval queue as read-only preview-only summaries", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/approvals");
    render(<App />);

    expect(await screen.findByRole("heading", { name: /Approval Queue/i })).toBeInTheDocument();
    expect(screen.getAllByText(/read-only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/preview-only/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Approval Authority handles final decision/i)).toBeInTheDocument();
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_approval_ref_001").length).toBeGreaterThan(0);
    expect(screen.getByText(/risk: medium/i)).toBeInTheDocument();
    expect(screen.getByText(/data: internal/i)).toBeInTheDocument();
    expect(screen.getByText(/CONTROL_CENTER_REVIEW_REQUIRED/i)).toBeInTheDocument();
    expect(screen.getByText(/No approval was granted from this UI/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^approve$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^deny$/i })).not.toBeInTheDocument();
  });

  it("makes approval detail authority boundaries explicit without dark-pattern action language", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/approvals");
    render(<App />);

    expect(await screen.findByRole("heading", { name: /Approval Queue/i })).toBeInTheDocument();
    expect(
      screen.getAllByText(/This UI cannot grant, deny, execute, or bypass approvals/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Approval refs are identifiers only and never authority/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Python Agent Core remains the only approval authority/i).length,
    ).toBeGreaterThan(0);

    for (const label of [
      /^approve$/i,
      /^deny$/i,
      /^execute$/i,
      /^run$/i,
      /^send$/i,
      /^deploy$/i,
      /^enable$/i,
    ]) {
      expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    }
  });

  it("renders M15 receipt summaries and details without raw sensitive content", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/receipts");
    render(<App />);

    expect(await screen.findByRole("heading", { name: /Receipt Viewer/i })).toBeInTheDocument();
    expect(screen.getByText(/redacted summary-only receipt records/i)).toBeInTheDocument();
    expect(screen.getAllByText("mock_receipt_ref_001").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/redacted_summary_only/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/No receipt mutation is available from this UI/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(/Receipt detail is redacted summary metadata only/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw file/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw memory/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/supersecretvalue123/i)).not.toBeInTheDocument();
  });

  it("renders M15 event summaries and details without raw prompt file memory or credentials", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/events");
    render(<App />);

    expect(await screen.findByRole("heading", { name: /Event Viewer/i })).toBeInTheDocument();
    expect(screen.getByText(/redacted event summaries/i)).toBeInTheDocument();
    expect(screen.getAllByText("mock_event_ref_001").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/source: CCC Web mock surface/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/No event action is available from this UI/i)).toBeInTheDocument();
    expect(screen.getByText(/Event detail is redacted summary metadata only/i)).toBeInTheDocument();
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw file/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw memory/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/credential/i)).not.toBeInTheDocument();
  });

  it("renders M16 event timeline and run receipt trace summaries without raw payloads", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/events/timeline");
    render(<App />);

    expect(await screen.findByRole("heading", { name: /Event Timeline/i })).toBeInTheDocument();
    expect(screen.getByText(/M16 trace surface/i)).toBeInTheDocument();
    expect(screen.getByText(/Timeline and trace views are read-only/i)).toBeInTheDocument();
    expect(screen.getAllByText(/redacted summary-only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_run_ref_001").length).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_correlation_ref_001").length).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_event_ref_001").length).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_receipt_ref_001").length).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_evidence_ref_gate_001").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Foundation Gate evidence summary/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText(/No trace export or external telemetry is available/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Trace detail is redacted summary metadata only/i)).toBeInTheDocument();

    for (const label of [
      /^execute$/i,
      /^run$/i,
      /^export$/i,
      /^send$/i,
      /^deploy$/i,
      /^enable$/i,
    ]) {
      expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw secret/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw file/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw memory/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw credential/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider payload/i)).not.toBeInTheDocument();
  });

  it("switches the selected M16 trace while keeping the timeline read-only", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/events/timeline");
    render(<App />);

    expect(await screen.findByRole("heading", { name: /Event Timeline/i })).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { name: "mock_event_ref_001" }).length).toBeGreaterThan(
      0,
    );
    expect(screen.getByRole("article", { name: /mock_event_ref_001/i })).toHaveAttribute(
      "aria-current",
      "true",
    );

    const traceButtons = screen.getAllByRole("button", { name: /view trace/i });
    fireEvent.click(traceButtons[1]);

    expect(screen.getAllByRole("heading", { name: "mock_event_ref_002" }).length).toBeGreaterThan(
      0,
    );
    expect(screen.getByRole("article", { name: /mock_event_ref_002/i })).toHaveAttribute(
      "aria-current",
      "true",
    );
    expect(screen.getByText(/Trace detail is redacted summary metadata only/i)).toBeInTheDocument();
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/NO_PRODUCTION_AUTHORITY/i).length).toBeGreaterThan(0);

    for (const label of [
      /^execute$/i,
      /^run$/i,
      /^export$/i,
      /^send$/i,
      /^write$/i,
      /^deploy$/i,
      /^enable$/i,
    ]) {
      expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw secret/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw file/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw memory/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw credential/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider payload/i)).not.toBeInTheDocument();
  });

  it("renders M17 evidence summaries and details as read-only redacted metadata", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/evidence");
    render(<App />);

    expect(await screen.findByRole("heading", { name: /Evidence Viewer/i })).toBeInTheDocument();
    expect(screen.getByText(/M17 knowledge surface/i)).toBeInTheDocument();
    expect(screen.getByText(/Evidence views are read-only/i)).toBeInTheDocument();
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/REDACTED_SUMMARY_ONLY/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_evidence_ref_001").length).toBeGreaterThan(0);
    expect(screen.getByText(/Source type/i)).toBeInTheDocument();
    expect(screen.getByText(/Provenance summary/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Evidence detail is redacted summary metadata only/i),
    ).toBeInTheDocument();

    for (const label of [
      /^execute$/i,
      /^run$/i,
      /^write$/i,
      /^delete$/i,
      /^reveal raw$/i,
      /^show raw$/i,
    ]) {
      expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw secret/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw file/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw memory/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider payload/i)).not.toBeInTheDocument();
  });

  it("renders M17 file ref summaries without raw file contents or filesystem controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/files");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /File Reference Viewer/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/File ref views are read-only/i)).toBeInTheDocument();
    expect(screen.getAllByText("mock_file_ref_001").length).toBeGreaterThan(0);
    expect(screen.getByText(/Safe filename/i)).toBeInTheDocument();
    expect(screen.getByText(/File writes are not available from this UI/i)).toBeInTheDocument();
    expect(screen.getByText(/No filesystem browsing is available/i)).toBeInTheDocument();

    for (const label of [
      /open file/i,
      /delete file/i,
      /write file/i,
      /browse filesystem/i,
      /^execute$/i,
    ]) {
      expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw file content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(new RegExp("/Users/", "i"))).not.toBeInTheDocument();
    expect(screen.queryByText(/\/home\//i)).not.toBeInTheDocument();
  });

  it("renders M37 file review packets with review-only approval capture controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/files/review");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /File Review Surface/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/M37 review approval capture/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/mock and non-authoritative/i)).toBeInTheDocument();
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/NO_PRODUCTION_AUTHORITY/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Review-only surface/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^Redacted preview$/i })).toBeInTheDocument();
    expect(
      screen.getByText(/Reviewed change summary mentions \[REDACTED:SECRET_ASSIGNMENT\]/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Redaction summary/i)).toBeInTheDocument();
    expect(
      screen.getByText(
        /Secret-like assignment and private path fragments were removed before display/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/Exact binding refs/i)).toBeInTheDocument();
    expect(screen.getAllByText("file-review-packet:mock_001").length).toBeGreaterThan(0);
    expect(screen.getByText("redacted-file-preview-output:mock_001")).toBeInTheDocument();
    expect(screen.getByText("file-review-redaction-summary:mock_001")).toBeInTheDocument();
    expect(screen.getByText("file-ref:mock_review_001")).toBeInTheDocument();
    expect(
      screen.getByText("filesystem-preview-path:safe-root_m36/docs/review-summary.md"),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Approval gate contract status/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/exact_binding_ready/i)).toBeInTheDocument();
    expect(screen.getByText(/Receipt plan metadata/i)).toBeInTheDocument();
    expect(screen.getByText(/raw content stored: no/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /approve review-only/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /deny review-only/i })).toBeInTheDocument();
    expect(
      screen.getByText(
        /captures a review-only approval record bound to this exact redacted packet/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(
        /does not grant raw file access, context proposal, context injection, memory writes, export, or execution/i,
      ).length,
    ).toBeGreaterThan(0);
  });

  it("keeps M37 approval capture review-only without raw or authority controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/files/review");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /File Review Surface/i }),
    ).toBeInTheDocument();
    const reviewButtons = screen.getAllByRole("button", { name: /view review packet/i });
    expect(reviewButtons.length).toBeGreaterThan(1);
    fireEvent.click(reviewButtons[1]);

    expect(
      screen.getAllByRole("heading", { name: "file-review-packet:mock_002" }).length,
    ).toBeGreaterThan(0);
    expect(screen.getByRole("article", { name: /file-review-packet:mock_002/i })).toHaveAttribute(
      "aria-current",
      "true",
    );
    expect(screen.getByText("file-ref:mock_review_002")).toBeInTheDocument();
    expect(
      screen.getByText("filesystem-preview-path:safe-root_m36/docs/alternate-review.md"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Review approval capture is review-only persistence/i).length,
    ).toBeGreaterThan(0);

    for (const label of [
      /^approve raw/i,
      /^deny raw/i,
      /^submit$/i,
      /^save$/i,
      /mark reviewed/i,
      /mark-reviewed/i,
      /^export$/i,
      /^download$/i,
      /copy raw/i,
      /file picker/i,
      /browse/i,
      /upload/i,
      /root selector/i,
      /open raw file/i,
      /context proposal/i,
      /inject/i,
      /write memory/i,
      /^execute$/i,
      /^run$/i,
      /run tool/i,
      /call model/i,
    ]) {
      expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    }
    expect(screen.getByRole("button", { name: /approve review-only/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /deny review-only/i })).toBeInTheDocument();
    expect(screen.queryByText(/raw_content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/full_file_content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/unredacted_preview/i)).not.toBeInTheDocument();
    expect(screen.queryByText(new RegExp("/Users/", "i"))).not.toBeInTheDocument();
    expect(screen.queryByText(/\/home\//i)).not.toBeInTheDocument();
    expect(screen.queryByText(/supersecretvalue123/i)).not.toBeInTheDocument();
  });

  it("captures a mock M37 review-only decision without authority", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/files/review");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /File Review Surface/i }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /approve review-only/i }));

    expect(screen.getByText(/approved_for_review_only/i)).toBeInTheDocument();
    expect(screen.getByText(/capture persisted: yes/i)).toBeInTheDocument();
    expect(screen.getByText(/raw access authorized: no/i)).toBeInTheDocument();
    expect(screen.getByText(/context proposal authorized: no/i)).toBeInTheDocument();
    expect(screen.getByText(/memory write authorized: no/i)).toBeInTheDocument();
    expect(screen.getByText(/export authorized: no/i)).toBeInTheDocument();
    expect(screen.getByText(/execution authorized: no/i)).toBeInTheDocument();
  });

  it("does not carry review-only capture state across packet selection", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/files/review");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /File Review Surface/i }),
    ).toBeInTheDocument();

    // Approve review-only on the first (default-selected) packet.
    fireEvent.click(screen.getByRole("button", { name: /approve review-only/i }));
    expect(screen.getByText(/approved_for_review_only/i)).toBeInTheDocument();

    // Switching to a different packet must reset the capture state to that
    // packet's own value rather than leaking the first packet's approval.
    const reviewButtons = screen.getAllByRole("button", { name: /view review packet/i });
    fireEvent.click(reviewButtons[1]);

    expect(
      screen.getByRole("article", { name: /file-review-packet:mock_002/i }),
    ).toHaveAttribute("aria-current", "true");
    expect(screen.queryByText(/approved_for_review_only/i)).not.toBeInTheDocument();
    expect(screen.getAllByText(/not_captured/i).length).toBeGreaterThan(0);

    fireEvent.click(reviewButtons[0]);

    expect(
      screen.getByRole("article", { name: /file-review-packet:mock_001/i }),
    ).toHaveAttribute("aria-current", "true");
    expect(screen.getByText(/approved_for_review_only/i)).toBeInTheDocument();
    expect(screen.getByText(/capture persisted: yes/i)).toBeInTheDocument();
  });

  it("keeps M37 binding refs safe and free of private path shapes", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/files/review");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /File Review Surface/i }),
    ).toBeInTheDocument();

    const documentText = document.body.textContent ?? "";
    for (const safeRef of [
      "file-review-packet:mock_001",
      "redacted-file-preview-output:mock_001",
      "file-review-redaction-summary:mock_001",
      "file-ref:mock_review_001",
      "filesystem-preview-path:safe-root_m36/docs/review-summary.md",
    ]) {
      expect(documentText).toContain(safeRef);
    }

    for (const unsafeFragment of [
      "/Users/",
      "/home/",
      "C:\\",
      "../",
      "absolute_path",
      "raw_absolute_path",
      "raw file path",
    ]) {
      expect(documentText.toLowerCase()).not.toContain(unsafeFragment.toLowerCase());
    }

    expect(screen.getAllByText(/safe refs only/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Only the review approval capture route may persist safe refs/i).length,
    ).toBeGreaterThan(0);
  });

  it("renders M39 context proposals as read-only safe proposal summaries", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/context/proposals");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Context Proposal Surface/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/M39 CCC context proposal surface/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/mock and non-authoritative/i)).toBeInTheDocument();
    expect(screen.getAllByText(/proposal-only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/NO_PRODUCTION_AUTHORITY/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Safe proposal sections/i)).toBeInTheDocument();
    expect(screen.getByText(/Redacted review excerpt/i)).toBeInTheDocument();
    expect(
      screen.getByText(
        /M39 surface displays redacted proposal text with \[REDACTED:SECRET_ASSIGNMENT\]/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/Source chain refs/i)).toBeInTheDocument();
    expect(screen.getAllByText("safe-context-proposal:mock_001").length).toBeGreaterThan(0);
    expect(screen.getAllByText("file-review-approval-capture:mock_001").length).toBeGreaterThan(0);
    expect(screen.getAllByText("file-review-packet:mock_001").length).toBeGreaterThan(0);
    expect(screen.getAllByText("redacted-file-preview-output:mock_001").length).toBeGreaterThan(0);
    expect(screen.getAllByText("file-review-redaction-summary:mock_001").length).toBeGreaterThan(0);
    expect(screen.getAllByText("file-ref:mock_review_001").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("filesystem-preview-path:safe-root_m39/docs/review-summary.md").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("user:mock_reviewer_001").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Decision status/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/proposal_ready_for_review/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Receipt plan metadata/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/context injected: no/i)).toBeInTheDocument();
    expect(screen.getByText(/OpenWebUI handoff authorized: no/i)).toBeInTheDocument();
    expect(screen.getByText(/memory write authorized: no/i)).toBeInTheDocument();
    expect(screen.getByText(/export authorized: no/i)).toBeInTheDocument();
    expect(screen.getByText(/execution authorized: no/i)).toBeInTheDocument();
  });

  it("keeps M39 proposal selection read-only without handoff injection or mutation controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/context/proposals");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Context Proposal Surface/i }),
    ).toBeInTheDocument();
    const proposalButtons = screen.getAllByRole("button", { name: /view context proposal/i });
    expect(proposalButtons.length).toBeGreaterThan(1);
    fireEvent.click(proposalButtons[1]);

    expect(
      screen.getAllByRole("heading", { name: "safe-context-proposal:mock_002" }).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("article", { name: /safe-context-proposal:mock_002/i }),
    ).toHaveAttribute("aria-current", "true");
    expect(
      screen.getAllByText("safe-context-proposal-section:mock_002:redacted-preview").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("file-ref:mock_review_002").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("filesystem-preview-path:safe-root_m39/docs/alternate-review.md").length,
    ).toBeGreaterThan(0);

    for (const label of [
      /^approve$/i,
      /^deny$/i,
      /^submit$/i,
      /^save$/i,
      /^export$/i,
      /^download$/i,
      /copy raw/i,
      /send to openwebui/i,
      /handoff/i,
      /inject/i,
      /write memory/i,
      /^execute$/i,
      /^run$/i,
      /run tool/i,
      /call model/i,
      /open raw file/i,
      /file picker/i,
      /browse/i,
      /upload/i,
      /root selector/i,
    ]) {
      expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw_content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/full_file_content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/unredacted_preview/i)).not.toBeInTheDocument();
    expect(screen.queryByText(new RegExp("/Users/", "i"))).not.toBeInTheDocument();
    expect(screen.queryByText(/\/home\//i)).not.toBeInTheDocument();
    expect(screen.queryByText(/supersecretvalue123/i)).not.toBeInTheDocument();
    expect(screen.getAllByText(/Control Center output is not authority/i).length).toBeGreaterThan(
      0,
    );
  });

  it("renders M17 memory summaries as recall and never authority", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/memory");
    render(<App />);

    expect(await screen.findByRole("heading", { name: /Memory Viewer/i })).toBeInTheDocument();
    expect(screen.getByText(/Memory is recall, not authority/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Canonical files and governed source systems outrank memory/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText("mock_memory_ref_001").length).toBeGreaterThan(0);
    // Each memory row reflects its own item's staleness/conflict, not a hardcoded placeholder.
    expect(screen.getAllByText(/Marked stale/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Review freshness/i)).toBeInTheDocument();
    expect(screen.queryByText(/source conflict flagged/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Conflict indicator/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Memory detail is redacted summary metadata only/i),
    ).toBeInTheDocument();

    for (const label of [
      /edit memory/i,
      /delete memory/i,
      /save memory/i,
      /learn this/i,
      /forget this/i,
    ]) {
      expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw memory content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/authoritative truth/i)).not.toBeInTheDocument();
  });

  it("keeps alternate M17 metadata selection read-only and redacted", async () => {
    for (const route of ["/evidence", "/files", "/memory"]) {
      cleanup();
      mockFetchWithFallback();
      window.history.pushState({}, "", route);
      render(<App />);

      await waitFor(() => {
        expect(screen.getAllByRole("button", { name: /view metadata/i }).length).toBeGreaterThan(1);
      });
      const metadataButtons = screen.getAllByRole("button", { name: /view metadata/i });
      fireEvent.click(metadataButtons[1]);

      const expectedRef =
        route === "/evidence"
          ? "mock_evidence_ref_002"
          : route === "/files"
            ? "mock_file_ref_002"
            : "mock_memory_ref_002";
      expect(screen.getAllByRole("heading", { name: expectedRef }).length).toBeGreaterThan(0);
      expect(screen.getByRole("article", { name: new RegExp(expectedRef, "i") })).toHaveAttribute(
        "aria-current",
        "true",
      );
      expect(screen.getAllByText(/redacted_summary_only/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);

      for (const label of [
        /^execute$/i,
        /^run$/i,
        /write file/i,
        /delete file/i,
        /browse filesystem/i,
        /edit memory/i,
        /delete memory/i,
        /reveal raw/i,
        /show raw/i,
      ]) {
        expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
      }
      expect(screen.queryByText(/raw evidence payload/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/raw file content/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/raw memory content/i)).not.toBeInTheDocument();
      expect(screen.queryByText(new RegExp("/Users/", "i"))).not.toBeInTheDocument();
      expect(screen.queryByText(/\/home\//i)).not.toBeInTheDocument();
    }
  });

  it("renders M18 local runtime status as read-only validation-only metadata", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/runtime/local");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Local Runtime Status/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/M18 local runtime surface/i)).toBeInTheDocument();
    expect(screen.getByText(/Local runtime status is read-only/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Runtime readiness report/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/manual_loopback_smoke/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/NO_RUNTIME_EXECUTION/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText(
        /No local runtime is started, stopped, connected, or executed from this UI/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/Model output remains non-authoritative/i)).toBeInTheDocument();

    for (const label of [
      /^execute$/i,
      /^run$/i,
      /^start$/i,
      /^stop$/i,
      /^connect$/i,
      /^launch$/i,
      /^call model$/i,
    ]) {
      expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw response/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider payload/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/supersecretvalue123/i)).not.toBeInTheDocument();
  });

  it("renders M18 manual smoke report handling without execution or raw report display", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/runtime/manual-smoke");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Manual Smoke Control Surface/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/validation-only report surface/i)).toBeInTheDocument();
    expect(screen.getByText(/Manual smoke reports are safe summaries/i)).toBeInTheDocument();
    expect(screen.getByText(/mock_manual_smoke_report_ref_001/i)).toBeInTheDocument();
    expect(screen.getByText(/fixed prompt hash/i)).toBeInTheDocument();
    expect(screen.getByText(/response preview shown: no/i)).toBeInTheDocument();
    expect(
      screen.getByText(
        /Manual smoke execution remains CLI-only, fixed-prompt-only, approval-gated/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/REDACTED_SUMMARY_ONLY/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/VALIDATION_ONLY/i).length).toBeGreaterThan(0);

    for (const label of [
      /^execute$/i,
      /^run$/i,
      /^start$/i,
      /^stop$/i,
      /^connect$/i,
      /^launch$/i,
      /^send$/i,
    ]) {
      expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw response body/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw transcript/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/api_key/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/token=/i)).not.toBeInTheDocument();
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
              metadata: { executed: false },
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      throw new Error("backend unavailable");
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/action-preview");
    render(<App />);

    expect(await screen.findByText(/Preview only action request/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Risk level/i)).toBeInTheDocument();
    expect(
      screen.getByText(/High and critical previews remain non-execution decisions/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /Blocked execution action/i })).toBeDisabled();
    fireEvent.click(await screen.findByRole("button", { name: /preview action/i }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(API_ENDPOINTS.actionPreview, expect.any(Object)),
    );
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
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/dashboard");
    render(<App />);

    expect(await screen.findByText("Backend online")).toBeInTheDocument();
    expect(
      screen.getByText(/Live data came from local read-only\/preview-only backend API routes/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Mock fallback active/i)).not.toBeInTheDocument();
  });

  it("shows degraded local backend state when only part of the read set succeeds", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (String(url).includes(API_ENDPOINTS.runtimeCapabilityMatrix)) {
        throw new Error("capability matrix unavailable");
      }
      return new Response(JSON.stringify(envelopeForReadEndpoint(String(url))), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/dashboard");
    render(<App />);

    expect(await screen.findByText("Backend degraded")).toBeInTheDocument();
    expect(screen.getByText(/Some local backend summaries were unavailable/i)).toBeInTheDocument();
    expect(
      screen.getByText(/non-authoritative mock fallback filled missing panels/i),
    ).toBeInTheDocument();
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
            metadata: { executed: false },
          },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/action-preview");
    render(<App />);

    fireEvent.change(await screen.findByLabelText(/Target reference/i), {
      target: { value: "remote-workers/dispatch/job" },
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
      target: { value: "token=supersecretvalue123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /preview action/i }));

    expect(await screen.findByText(/Secret-like input was redacted/i)).toBeInTheDocument();
    expect(screen.queryByText(/supersecretvalue123/i)).not.toBeInTheDocument();
  });

  it("redacts secret-like backend preview errors before display", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              ok: false,
              error: {
                code: "SAFE_REJECTION",
                message: "Preview rejected because token=supersecretvalue123 was invalid.",
              },
            }),
            { status: 400, headers: { "Content-Type": "application/json" } },
          ),
      ),
    );
    window.history.pushState({}, "", "/action-preview");
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: /preview action/i }));

    expect(
      await screen.findByText(/Preview rejected because \[redacted\] was invalid/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/supersecretvalue123/i)).not.toBeInTheDocument();
  });

  it("keeps read endpoints separate from the single preview POST endpoint", () => {
    expect(READ_ENDPOINTS).not.toContain(API_ENDPOINTS.actionPreview);
    expect(READ_ENDPOINTS).not.toContain(API_ENDPOINTS.runtimeSmokeReportValidate);
    expect(API_ENDPOINTS.actionPreview).toBe("/control-center/actions/preview");
    expect(API_ENDPOINTS.runtimeSmokeReportValidate).toBe("/runtime/smoke-reports/validate");
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
      version: "0.20.1",
    },
    [API_ENDPOINTS.controlCenterDashboard]: {
      ...mockApiData.dashboard,
      baseline_version: "0.20.1",
    },
    [API_ENDPOINTS.controlCenterStatus]: mockApiData.status,
    [API_ENDPOINTS.controlCenterRoutes]: mockApiData.routes,
    [API_ENDPOINTS.runtimeReadiness]: {
      ...mockApiData.runtimeReadiness,
      baseline_version: "0.20.1",
    },
    [API_ENDPOINTS.runtimeCapabilityMatrix]: {
      ...mockApiData.capabilityMatrix,
      baseline_version: "0.20.1",
    },
  };
  const endpoint = Object.keys(data).find((candidate) => url.endsWith(candidate));
  return { ok: true, result: data[endpoint as keyof typeof data] };
}

const mockApiData = {
  manifest: {
    manifest_id: "test_manifest",
    version: "0.20.1",
    generated_at: "2026-01-01T00:00:00Z",
    declared_capabilities: ["control_center_read_only_dashboard"],
    blocked_capabilities: [
      "runtime_execution",
      "remote_dispatch",
      "mobile_sensor_access",
      "plugin_enablement",
    ],
    api_route_refs: ["/control-center/dashboard", "/control-center/actions/preview"],
    metadata: { read_only: true, preview_only: true, production_control_center: false },
    surfaces: [],
  },
  dashboard: {
    snapshot_id: "test_dashboard",
    baseline_version: "0.20.1",
    generated_at: "2026-01-01T00:00:00Z",
    system_status: {
      label: "Control Center",
      status: "read_only",
      summary: "Read-only local backend summary.",
    },
    foundation_gate_summary: {
      status: "passed",
      passed_count: 1,
      failed_count: 0,
      summary: "Gate summary only.",
    },
    runtime_readiness_summary: {
      status: "report_only",
      production_ready: false,
      real_model_runtime_ready: false,
      remote_execution_ready: false,
      mobile_sensor_ready: false,
      plugin_or_native_build_ready: false,
    },
    approval_summary: {
      pending_count: 0,
      approval_grants_created: false,
      arbitrary_approval_ref_authority: false,
      summary: "Read-only approval summary.",
    },
    api_summary: {
      route_count: 93,
      control_center_route_count: 8,
      operation_ids_unique: true,
      execution_routes_present: false,
    },
    remote_worker_summary: {
      status: "dry_run_only",
      execution_enabled: false,
      dispatch_enabled: false,
    },
    private_mesh_summary: {
      status: "planned_disabled",
      headscale_integrated: false,
      tailscale_integrated: false,
      wireguard_integrated: false,
    },
    mobile_planning_summary: {
      status: "planned_disabled",
      sensor_access_enabled: false,
      mobile_app_implemented: false,
    },
    plugin_governance_summary: {
      status: "planned_disabled",
      plugin_enablement_allowed: false,
      native_build_tools_enabled: false,
    },
    warnings: [],
    blockers: [],
    next_recommended_action: "review_local_backend_status",
    metadata: { read_only: true, preview_only: true },
  },
  status: {
    status: "available",
    read_only: true,
    preview_only: true,
    frontend_shell: true,
    production_authority: false,
    message: "Local backend status only.",
  },
  routes: {
    route_count: 8,
    routes: [
      {
        path: "/control-center/dashboard",
        methods: ["GET"],
        operation_id: "get_control_center_dashboard",
        tags: ["control-center"],
        validation_only: true,
      },
    ],
  },
  runtimeReadiness: {
    report_id: "test_readiness",
    baseline_version: "0.20.1",
    status: "report_only",
    production_ready: false,
    real_model_runtime_ready: false,
    remote_execution_ready: false,
    mobile_sensor_ready: false,
    plugin_or_native_build_ready: false,
    capability_matrix_ref: "test_matrix",
    warnings: [],
    blockers: [],
    metadata: { model_output_authoritative: false },
  },
  capabilityMatrix: {
    matrix_id: "test_matrix",
    baseline_version: "0.20.1",
    metadata: { no_model_was_called: true },
    entries: [],
  },
  m15Review: {
    status: "mock_preview_only",
    readOnly: true,
    previewOnly: true,
    mock: true,
    nonAuthoritative: true,
    authorityBoundary:
      "Approval Authority handles final decision; Control Center displays summaries only.",
    warningCodes: ["MOCK_DATA_ONLY", "REDACTED_SUMMARY_ONLY"],
    approvalQueue: [
      {
        approvalRef: "mock_approval_ref_001",
        status: "pending_review",
        riskLevel: "medium",
        dataClassification: "internal",
        actorSummary: "Local developer session summary",
        requestedActionSummary: "Preview-only policy review for a proposed local workspace change.",
        subjectSummary: "Mock local review subject; no file body or prompt body is shown.",
        reasonCodes: ["CONTROL_CENTER_REVIEW_REQUIRED"],
        createdAt: "2026-01-01T00:00:00Z",
        expiresAt: "2026-01-01T01:00:00Z",
        requiredNextAction: "Review in Python Agent Core approval authority.",
        safeMessage: "No approval was granted from this UI.",
        previewOutcomeSummary: "Grant or denial outcome is preview-only and non-authoritative.",
        relatedRefs: ["mock_receipt_ref_001", "mock_event_ref_001"],
        previewOnly: true,
        readOnly: true,
        mock: true,
      },
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
        safeMessage:
          "Receipt is a redacted summary; no receipt mutation is available from this UI.",
        timestamp: "2026-01-01T00:02:00Z",
        relatedRefs: ["mock_approval_ref_001"],
        previewOnly: true,
        readOnly: true,
        mock: true,
      },
    ],
    events: [
      {
        eventRef: "mock_event_ref_001",
        eventType: "approval_review_preview",
        actorSummary: "Local developer session summary",
        sourceSurface: "CCC Web mock surface",
        resultStatus: "summary_recorded",
        reasonCodes: ["CONTROL_CENTER_REVIEW_REQUIRED"],
        timestamp: "2026-01-01T00:02:00Z",
        relatedRefs: ["mock_approval_ref_001", "mock_receipt_ref_001"],
        redactionStatus: "redacted_summary_only",
        safeMessage: "No event action is available from this UI.",
        previewOnly: true,
        readOnly: true,
        mock: true,
      },
    ],
  },
};
