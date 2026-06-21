import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
  waitFor,
} from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { App } from "./App";
import {
  API_ENDPOINTS,
  isAllowedReadEndpoint,
  isPreviewEndpoint,
  READ_ENDPOINTS,
} from "./api/endpoints";
import { EmptyState, ErrorState, LoadingState } from "./components/DataState";
import { mockControlCenterData } from "./mocks/controlCenterData";
import { primaryNavItems, supportingNavItems } from "./routes";

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
      screen.getByText(
        /Backend unavailable; showing non-authoritative mock fallback data/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/API base: relative local API/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Overview" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Today" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Inbox" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Actions" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Setup" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Runtime" })).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Foundation Gate" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "API Routes" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Action Preview" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Runtime readiness")).toBeInTheDocument();
    expect(screen.getByText("API boundary")).toBeInTheDocument();
    expect(
      screen.getByText(/No authority to run actions/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /execute/i }),
    ).not.toBeInTheDocument();
  });

  it("prioritizes the Founder Loop while keeping supporting routes reachable", async () => {
    expect(primaryNavItems.map((item) => item.label)).toEqual([
      "Today",
      "Inbox",
      "Plans",
      "Actions",
      "Memory",
      "Evidence",
      "Settings",
    ]);
    expect(supportingNavItems.map((item) => item.label)).toEqual(
      expect.arrayContaining([
        "Setup",
        "Dashboard",
        "Operator Loop",
        "Runtime",
        "API Routes",
        "Differentiators",
        "Action Preview",
      ]),
    );

    mockFetchWithFallback();
    window.history.pushState({}, "", "/today");
    render(<App />);

    await screen.findByRole("heading", { name: /^Today$/i });
    const navigation = screen.getByLabelText(/Control Center navigation/i);
    const labels = within(navigation)
      .getAllByRole("link")
      .map((link) => link.getAttribute("aria-label"));
    expect(labels.slice(0, 7)).toEqual([
      "Today",
      "Inbox",
      "Plans",
      "Actions",
      "Memory",
      "Evidence",
      "Settings",
    ]);
    expect(within(navigation).getByText("Supporting Surfaces")).toBeInTheDocument();
    expect(within(navigation).getByRole("link", { name: "Setup" })).toBeInTheDocument();
    expect(within(navigation).getByRole("link", { name: "API Routes" })).toBeInTheDocument();
    expect(within(navigation).getByRole("link", { name: "Differentiators" })).toBeInTheDocument();
    expect(within(navigation).getByText("blocked/planned")).toBeInTheDocument();
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
    expect(
      screen.getByText(/Plugin enablement allowed: no/i),
    ).toBeInTheDocument();
  });

  it("renders clear headings for every local shell page", async () => {
    const expectedHeadings = [
      ["/", /Dashboard overview/i],
      ["/today", /^Today$/i],
      ["/inbox", /^Inbox$/i],
      ["/actions", /^Actions$/i],
      ["/briefing", /Morning Briefing/i],
      ["/setup", /macOS Setup Assistant/i],
      ["/dashboard", /Dashboard overview/i],
      ["/operator-loop", /Operator Loop/i],
      ["/differentiators", /Control Center Differentiators/i],
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
      ["/memory", /^Memory Review$/i],
      ["/storage", /^Storage$/i],
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
      expect(
        await screen.findByRole("heading", { name: heading }),
      ).toBeInTheDocument();
      unmount();
      vi.unstubAllGlobals();
    }
  });

  it("renders Inbox as a blocked planned triage surface without connector authority", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/inbox");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Inbox$/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("blocked/planned").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /Route posture/i })).toBeInTheDocument();
    expect(screen.getByText("not scoped")).toBeInTheDocument();
    expect(screen.getByText("/inbox")).toBeInTheDocument();
    expect(screen.getByText("none in this slice")).toBeInTheDocument();
    expect(screen.getByText("local UI state only")).toBeInTheDocument();
    expect(
      screen.getByText(/future connector or draft actions require exact scoped approval/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/define read-only email\/calendar metadata contracts/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/docs\/control_center\/OPERATOR_SHELL_GAP_MAP.md/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/docs\/strategy\/FOUNDER_COMMAND_CENTER_MVP_SPEC.md/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/email\/calendar connector runtime is not scoped/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/draft-only response proposal contract is not implemented/i),
    ).toBeInTheDocument();

    for (const label of [
      /^send$/i,
      /^archive$/i,
      /^delete$/i,
      /^connect$/i,
      /^write$/i,
      /^approve$/i,
      /^run$/i,
      /^install$/i,
    ]) {
      expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    }
  });

  it("renders Action Inbox approval-envelope posture without mutation controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/actions");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Actions$/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /State posture/i })).toBeInTheDocument();
    expect(screen.getByText("/control-center/actions/inbox")).toBeInTheDocument();
    expect(screen.getByText("Exact backend approval contract required")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Local prerequisites/i })).toBeInTheDocument();
    expect(screen.getByText("GET /control-center/storage/status")).toBeInTheDocument();
    expect(screen.getByText("status-ref:control-center-route-manifest")).toBeInTheDocument();
    expect(screen.getByText("capability-ref:local-approval-authority")).toBeInTheDocument();

    expect(screen.getByText("approval-envelope:founder-loop:mock-setup-hardening")).toBeInTheDocument();
    expect(screen.getByText("dry_run_ref_available")).toBeInTheDocument();
    expect(screen.getByText("contract-ref:founder-loop:mock-setup-hardening")).toBeInTheDocument();
    expect(screen.getByText("blocked_pending_scoped_mutation_contract")).toBeInTheDocument();
    expect(screen.getByText("receipt-plan:founder-loop:mock-setup-hardening")).toBeInTheDocument();
    expect(screen.getByText("audit-plan:founder-loop:mock-setup-hardening")).toBeInTheDocument();
    expect(screen.getByText("idempotency-ref:founder-loop:mock-setup-hardening")).toBeInTheDocument();
    expect(screen.getByText("rollback-plan:founder-loop:mock-setup-hardening")).toBeInTheDocument();
    expect(screen.getByText("safe-disable:founder-loop:mock-setup-hardening")).toBeInTheDocument();
    expect(
      screen.getByText(/Review refs only; request a scoped state-change milestone/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Receipt refs: missing until scoped contract")).toBeInTheDocument();
    expect(screen.getByText("no_approval_grant_capture_route")).toBeInTheDocument();
    expect(screen.getByText("no_state_change_contract_route")).toBeInTheDocument();

    for (const label of [
      /^approve$/i,
      /^send$/i,
      /^run$/i,
      /^install$/i,
      /^connect$/i,
      /^write$/i,
    ]) {
      expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    }
  });

  it("renders Morning Briefing source-readiness posture without source controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/briefing");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Morning Briefing/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Source posture/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Missing contracts/i })).toBeInTheDocument();
    expect(
      screen.getAllByText("/control-center/morning-briefing/summary").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("blocked_missing_email_calendar_notification_contracts"),
    ).toBeInTheDocument();
    expect(screen.getByText("status-ref:control-center-route-manifest")).toBeInTheDocument();
    expect(screen.getAllByText("contract-ref:email-read-only-missing").length).toBeGreaterThan(0);
    expect(screen.getAllByText("contract-ref:calendar-read-only-missing").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("contract-ref:notification-delivery-missing").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("source-ref:control-center-route-status")).toBeInTheDocument();
    expect(screen.getByText("local_status_refs_only")).toBeInTheDocument();
    expect(screen.getByText("recheck_route_status_before_briefing_use")).toBeInTheDocument();
    expect(
      screen.getByText(/No email, calendar, or notification source evidence is bound/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Use route and storage refs only; define source contracts before refresh/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText("no_background_refresh").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_notification_delivery").length).toBeGreaterThan(0);

    for (const label of [
      /^refresh$/i,
      /^send$/i,
      /^connect$/i,
      /^write$/i,
      /^approve$/i,
      /^run$/i,
      /^notify$/i,
    ]) {
      expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    }
  });

  it("searches route and disabled action entries through the command palette", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/dashboard");
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: /find route or action/i }));

    const palette = screen.getByRole("dialog", { name: /command palette/i });
    expect(palette).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/search routes and actions/i), {
      target: { value: "storage" },
    });

    expect(palette).toHaveTextContent("Storage");
    expect(palette).toHaveTextContent("local state");

    fireEvent.change(screen.getByLabelText(/search routes and actions/i), {
      target: { value: "state change" },
    });
    expect(palette).toHaveTextContent("Action state change");
    expect(palette).toHaveTextContent("Scoped backend contract required");
    expect(
      screen.queryByRole("button", { name: /^run$/i }),
    ).not.toBeInTheDocument();
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

      expect(
        await screen.findByRole("heading", { name: check.heading }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: check.stateHeading }),
      ).toBeInTheDocument();
      expect(screen.getByText(check.blocked)).toBeInTheDocument();
      expect(screen.getByText(check.denied)).toBeInTheDocument();
      expect(screen.getAllByRole("status").length).toBeGreaterThanOrEqual(4);
      expect(screen.getAllByRole("alert").length).toBeGreaterThanOrEqual(1);
      expect(
        screen.getAllByText(/Next safe action:/i).length,
      ).toBeGreaterThanOrEqual(5);
      expect(
        screen.queryByRole("button", { name: /^run$/i }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /^send$/i }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /^approve$/i }),
      ).not.toBeInTheDocument();

      unmount();
      vi.unstubAllGlobals();
    }
  });

  it("renders priority operator flows instead of placeholder-first screens", async () => {
    const priorityFlowChecks = [
      {
        path: "/chat",
        heading: /^Chat Shell$/,
        marker: /UAA \/v1 model route/i,
        route: API_ENDPOINTS.localChatCompletions,
      },
      {
        path: "/plans",
        heading: /^Plans$/,
        marker: /Task decomposition route posture/i,
        route: "/task-decomposition/classify",
      },
      {
        path: "/models",
        heading: /^Models$/,
        marker: /Local model readiness/i,
        route: API_ENDPOINTS.localModels,
      },
      {
        path: "/evidence",
        heading: /^Evidence Viewer$/,
        marker: /Evidence lanes/i,
        route: "/task-decomposition/audit",
      },
      {
        path: "/settings",
        heading: /^Settings$/,
        marker: /Provider credential readiness/i,
        route: /OpenWebUI/i,
      },
    ] as const;

    for (const check of priorityFlowChecks) {
      mockFetchWithFallback();
      window.history.pushState({}, "", check.path);
      const { unmount } = render(<App />);

      expect(
        await screen.findByRole("heading", { name: check.heading }),
      ).toBeInTheDocument();
      expect(screen.getAllByText(check.marker).length).toBeGreaterThan(0);
      if (typeof check.route === "string") {
        expect(screen.getAllByText(check.route).length).toBeGreaterThan(0);
      } else {
        expect(screen.getAllByText(check.route).length).toBeGreaterThan(0);
      }
      expect(
        screen.queryByText(/v0\.43\.0 M39 context proposal surface/i),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /^send$/i }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /^run$/i }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /^approve$/i }),
      ).not.toBeInTheDocument();

      unmount();
      vi.unstubAllGlobals();
    }
  });

  it("shows governed provider credential readiness without credential collection", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/settings");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Settings$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Provider credential readiness/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/reference_readiness_only/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Provider invocation/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText(/Raw key collection/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Credential material stored/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText(/Vault adapter/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Credential adapter readiness/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Credential enrollment/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Validation readiness/i)).toBeInTheDocument();
    expect(screen.getByText(/External validation/i)).toBeInTheDocument();
    expect(screen.getByText(/Provider response persistence allowed/i)).toBeInTheDocument();
    expect(screen.getByText(/Invocation readiness/i)).toBeInTheDocument();
    expect(screen.getByText(/Vault adapter contract/i)).toBeInTheDocument();
    expect(screen.getByText(/Credential enrollment contract/i)).toBeInTheDocument();
    expect(screen.getByText(/Provider validation contract/i)).toBeInTheDocument();
    expect(
      screen.getAllByText(/Governed provider invocation/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/VAULT_ADAPTER_NOT_SCOPED/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getByText(/PROVIDER_KEY_VALIDATION_NOT_SCOPED/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/CREDENTIAL_ENROLLMENT_NOT_SCOPED/i)).toBeInTheDocument();
    expect(
      screen.getByText(/TRANSIENT_SECRET_INTAKE_NOT_APPROVED/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/APPROVED_VAULT_BACKEND_REQUIRED/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/POLICY_APPROVAL_AUDIT_RECEIPT_REQUIRED/i),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/OpenAI-compatible provider/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/provider auth ref status/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getAllByText(/consent-ref:/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/policy-ref:/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/revocation-ref:/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/PROVIDER_INVOCATION_NOT_SCOPED/i).length,
    ).toBeGreaterThan(0);

    expect(
      screen.queryByRole("textbox", { name: /api key|secret|token/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /save key|connect provider/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /test provider|call provider/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /enroll credential|add credential|store credential|resolve credential/i,
      }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /validate provider|invoke provider/i,
      }),
    ).not.toBeInTheDocument();
  });

  it("renders macOS setup assistant preview without installer authority", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/setup");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /macOS Setup Assistant/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Visual setup preview/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Local prerequisites/i })).toBeInTheDocument();
    expect(screen.getByText(/existing local status routes only/i)).toBeInTheDocument();
    expect(screen.getAllByText("/runtime/readiness").length).toBeGreaterThan(0);
    expect(screen.getAllByText("/runtime/capability-matrix").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /Blocked setup authority/i })).toBeInTheDocument();
    expect(screen.getByText("macos-setup-bridge-enablement")).toBeInTheDocument();
    expect(screen.getByText("macos-setup-rollback-execution")).toBeInTheDocument();
    expect(screen.getByText("macos-setup-signed-distribution")).toBeInTheDocument();
    expect(screen.getByText("macos-setup-production-authority")).toBeInTheDocument();
    expect(screen.getByText(/First launch setup/i)).toBeInTheDocument();
    expect(screen.getByText(/Runtime health/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Local model readiness/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Model selection/i)).toBeInTheDocument();
    expect(screen.getByText(/Fast local chat/i)).toBeInTheDocument();
    expect(screen.getByText(/Balanced local assistant/i)).toBeInTheDocument();
    expect(screen.getByText(/Coding local assistant/i)).toBeInTheDocument();
    expect(
      screen.getAllByText(/approval-ref:macos-setup-model-selection/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: /Dry-run approval envelopes/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("macos-setup-approval-envelope:model-selection").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("idempotency-ref:macos-setup-model-selection").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("scope-ref:macos-setup-model-selection")).toBeInTheDocument();
    expect(screen.getByText(/approval refs are identifiers only/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Preview only\. Raw logs, raw paths/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/macos-setup-receipt-plan:foundation/i)).toBeInTheDocument();
    expect(screen.getByText(/macos-setup-rollback-plan:foundation/i)).toBeInTheDocument();
    expect(screen.getAllByText(/OpenWebUI bridge/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Mattermost Agent Rooms/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Verify the model choices/i)).toBeInTheDocument();
    expect(screen.getAllByText(/no command executed/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Installer side effects/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: /^run$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^install$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^approve$/i }),
    ).not.toBeInTheDocument();
  });

  it("covers first product loop browser smoke readiness with truthful backend-bound states", async () => {
    const firstLoopStates = {
      openControlCenter: "mock_fallback",
      inspectRuntimeHealthAndModelReadiness: "route_ready",
      selectOrApproveLocalGgufModel: "backend_gated",
      chatShellThroughUaaV1: "gateway_gated",
      createTaskDecompositionPlan: "backend_gated",
      approveSafeRegisteredCapability: "backend_authority",
      inspectReceiptAuditLatencyRollback: "inspection_ready",
    };

    expect(firstLoopStates).toEqual({
      openControlCenter: "mock_fallback",
      inspectRuntimeHealthAndModelReadiness: "route_ready",
      selectOrApproveLocalGgufModel: "backend_gated",
      chatShellThroughUaaV1: "gateway_gated",
      createTaskDecompositionPlan: "backend_gated",
      approveSafeRegisteredCapability: "backend_authority",
      inspectReceiptAuditLatencyRollback: "inspection_ready",
    });

    mockFetchWithFallback();
    window.history.pushState({}, "", "/dashboard");
    const dashboard = render(<App />);
    expect(
      await screen.findByRole("heading", { name: /Dashboard overview/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByRole("heading", { name: /Operator Loop/i }).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Runtime health/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Local model readiness/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Chat through UAA \/v1/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Task decomposition plan/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/One safe capability approval/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(/Receipt, audit, latency, rollback/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Frontend authority/i).length).toBeGreaterThan(
      0,
    );
    expect(screen.getByText(/Mutation allowed/i)).toBeInTheDocument();
    expect(screen.getByText(/Production readiness claim/i)).toBeInTheDocument();
    expect(screen.getByText(/Model output authoritative/i)).toBeInTheDocument();
    expect(screen.getByText(/Prompt content recording/i)).toBeInTheDocument();
    expect(screen.getByText(/Provider payload recording/i)).toBeInTheDocument();
    expect(
      screen.getByText(/inspect_local_backend_loop_routes/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Mock fallback active")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Backend unavailable; showing non-authoritative mock fallback data/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/API base: relative local API/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/No authority to run actions/i),
    ).toBeInTheDocument();
    dashboard.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/runtime");
    const runtime = render(<App />);
    expect(
      await screen.findByRole("heading", { name: /Runtime readiness/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Production readiness claim/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Reviewed local model runtime evidence/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Local contract state only/i)).toBeInTheDocument();
    runtime.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/runtime/local");
    const localRuntime = render(<App />);
    expect(
      await screen.findByRole("heading", { name: /Local Runtime Status/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/NO_RUNTIME_EXECUTION/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getByText(/Model output remains non-authoritative/i),
    ).toBeInTheDocument();
    localRuntime.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/runtime/manual-smoke");
    const manualSmoke = render(<App />);
    expect(
      await screen.findByRole("heading", {
        name: /Manual Smoke Control Surface/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Manual smoke reports are safe summaries/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/no smoke attempt was performed/i),
    ).toBeInTheDocument();
    manualSmoke.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/action-preview");
    const actionPreview = render(<App />);
    expect(
      await screen.findByText(/Preview only action request/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /never runs, enables, grants, deploys, or dispatches anything/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/approval reference is never treated as authority/i),
    ).toBeInTheDocument();
    actionPreview.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/approvals");
    const approvals = render(<App />);
    expect(
      await screen.findByRole("heading", { name: /Approval Queue/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/No approval was granted from this UI/i),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(
        /Python Agent Core remains the only approval authority/i,
      ).length,
    ).toBeGreaterThan(0);
    approvals.unmount();
    vi.unstubAllGlobals();

    mockFetchWithFallback();
    window.history.pushState({}, "", "/events/timeline");
    const evidence = render(<App />);
    expect(
      await screen.findByRole("heading", { name: /Event Timeline/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Trace detail is redacted summary metadata only/i),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Foundation Gate evidence summary/i).length,
    ).toBeGreaterThan(0);
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
      expect(
        screen.queryByRole("button", { name: forbidden }),
      ).not.toBeInTheDocument();
    }
  });

  it("renders the UAA-P1-011 operator loop as one readable proof chain", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/operator-loop");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Operator Loop/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/First product loop proof/i)).toBeInTheDocument();
    expect(screen.getByText(/Steps surfaced/i)).toBeInTheDocument();
    expect(screen.getByText(/Routes surfaced/i)).toBeInTheDocument();
    expect(screen.getByText(/Blocked prerequisites/i)).toBeInTheDocument();
    expect(screen.getByText(/Approval and evidence proof/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Approval refs are identifiers only/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Route side-effect classes/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Side-effect class/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/local_dev_workspace_only/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/validation_only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/receipt_refs/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/audit_refs/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/rollback_refs/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/capability_latency_metrics/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Model output authority/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: /^run$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^execute$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^approve$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^send$/i }),
    ).not.toBeInTheDocument();
  });

  it("renders UAA-P1-054 differentiator screens without adding authority controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/differentiators");
    render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: /Control Center Differentiators/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/safe-ref \/ redacted-first/i)).toBeInTheDocument();
    expect(screen.getByText(/OpenAPI, \/api\/manifest, PolicyEngine/i)).toBeInTheDocument();

    const routePanel = screen
      .getByRole("heading", { name: /Route Authority/i })
      .closest("article");
    expect(routePanel).not.toBeNull();
    expect(within(routePanel!).getByText(/OpenAPI path count/i)).toBeInTheDocument();
    expect(within(routePanel!).getByText("112")).toBeInTheDocument();
    expect(within(routePanel!).getByText(/Operation IDs unique/i)).toBeInTheDocument();
    expect(within(routePanel!).getAllByText(/Contract truth/i).length).toBeGreaterThan(0);
    expect(within(routePanel!).getAllByText(/Side-effect class/i).length).toBeGreaterThan(0);
    expect(within(routePanel!).getAllByText(/Owner \/ service/i).length).toBeGreaterThan(0);
    expect(within(routePanel!).getByText(/docs\/api\/openapi_contract.md/i)).toBeInTheDocument();

    const approvalPanel = screen
      .getByRole("heading", { name: /Approval State/i })
      .closest("article");
    expect(approvalPanel).not.toBeNull();
    expect(within(approvalPanel!).getByText(/Approval ref/i)).toBeInTheDocument();
    expect(within(approvalPanel!).getByText(/Exact scope/i)).toBeInTheDocument();
    expect(within(approvalPanel!).getByText(/Stale \/ expiry/i)).toBeInTheDocument();
    expect(within(approvalPanel!).getByText(/refs are identifiers only/i)).toBeInTheDocument();
    expect(within(approvalPanel!).getByText(/mock_receipt_ref_001/i)).toBeInTheDocument();

    const receiptPanel = screen
      .getByRole("heading", { name: /Evidence Receipts/i })
      .closest("article");
    expect(receiptPanel).not.toBeNull();
    expect(within(receiptPanel!).getByText(/Foundation Gate refs/i)).toBeInTheDocument();
    expect(within(receiptPanel!).getByText(/foundation-gate-ref:latest-report/i)).toBeInTheDocument();
    expect(within(receiptPanel!).getByText(/Latency refs/i)).toBeInTheDocument();
    expect(within(receiptPanel!).getByText(/latency-ref:foundation-gate:latest-report/i)).toBeInTheDocument();
    expect(within(receiptPanel!).getByText(/Rollback refs/i)).toBeInTheDocument();

    const workspacePanel = screen
      .getByRole("heading", { name: /Safe Workspace Preview/i })
      .closest("article");
    expect(workspacePanel).not.toBeNull();
    expect(within(workspacePanel!).getByText(/bounded preview/i)).toBeInTheDocument();
    expect(within(workspacePanel!).getByText(/Path posture/i)).toBeInTheDocument();
    expect(within(workspacePanel!).getByText(/redacted_safe_label_only/i)).toBeInTheDocument();
    expect(within(workspacePanel!).getByText(/patch apply, rollback execution/i)).toBeInTheDocument();

    const modelPanel = screen
      .getByRole("heading", { name: /Local Model \/ M167 Status/i })
      .closest("article");
    expect(modelPanel).not.toBeNull();
    expect(within(modelPanel!).getByText(/Runtime readiness/i)).toBeInTheDocument();
    expect(within(modelPanel!).getByText(/OpenWebUI shell/i)).toBeInTheDocument();
    expect(within(modelPanel!).getByText(/output is not production authority/i)).toBeInTheDocument();
    expect(within(modelPanel!).getByText(/model download, GGUF approval/i)).toBeInTheDocument();

    const observabilityPanel = screen
      .getByRole("heading", { name: /M167 Observability Timeline/i })
      .closest("article");
    expect(observabilityPanel).not.toBeNull();
    expect(within(observabilityPanel!).getByText(/Session \/ run ref/i)).toBeInTheDocument();
    expect(within(observabilityPanel!).getByText(/Client-error posture/i)).toBeInTheDocument();
    expect(within(observabilityPanel!).getByText(/unredacted forensic mode is blocked/i)).toBeInTheDocument();
    expect(within(observabilityPanel!).getByText(/External telemetry/i)).toBeInTheDocument();

    for (const label of [
      /^approve$/i,
      /^deny$/i,
      /^grant$/i,
      /^revoke$/i,
      /^execute$/i,
      /^run$/i,
      /^send$/i,
      /^write$/i,
      /^download$/i,
      /^upload$/i,
      /^export$/i,
      /^start$/i,
      /^stop$/i,
      /^install$/i,
      /^load$/i,
      /^browse$/i,
    ]) {
      expect(screen.queryByRole("button", { name: label })).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider payload content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/environment dump/i)).not.toBeInTheDocument();
  });

  it("renders loading and empty states with safe operational copy", () => {
    const { rerender } = render(<LoadingState />);
    expect(screen.getByRole("status")).toHaveTextContent(
      /loading local control center/i,
    );
    expect(
      screen.getByText(/checking local backend connection state/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/read-only/i)).toBeInTheDocument();

    rerender(
      <EmptyState
        title="No routes listed"
        message="No API routes were returned by the local mock."
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent(/No routes listed/i);
    expect(
      screen.getByText(/No API routes were returned/i),
    ).toBeInTheDocument();

    rerender(
      <ErrorState message="Control Center data could not be loaded safely." />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      /Control Center data unavailable/i,
    );
    expect(
      screen.getByText(/Next safe action: verify the local backend/i),
    ).toBeInTheDocument();
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
    expect(
      screen.queryByRole("button", { name: /execute/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /approve/i }),
    ).not.toBeInTheDocument();
  });

  it("renders M15 approval queue as read-only preview-only summaries", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/approvals");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Approval Queue/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/read-only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/preview-only/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Approval Authority handles final decision/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_approval_ref_001").length).toBeGreaterThan(
      0,
    );
    expect(screen.getByText(/risk: medium/i)).toBeInTheDocument();
    expect(screen.getByText(/data: internal/i)).toBeInTheDocument();
    expect(
      screen.getByText(/CONTROL_CENTER_REVIEW_REQUIRED/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/No approval was granted from this UI/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^approve$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^deny$/i }),
    ).not.toBeInTheDocument();
  });

  it("makes approval detail authority boundaries explicit without dark-pattern action language", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/approvals");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Approval Queue/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(
        /This UI cannot grant, deny, execute, or bypass approvals/i,
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        /Approval refs are identifiers only and never authority/i,
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        /Python Agent Core remains the only approval authority/i,
      ).length,
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
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
  });

  it("renders M15 receipt summaries and details without raw sensitive content", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/receipts");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Receipt Viewer/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/redacted summary-only receipt records/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText("mock_receipt_ref_001").length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText(/redacted_summary_only/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/No receipt mutation is available from this UI/i)
        .length,
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

    expect(
      await screen.findByRole("heading", { name: /Event Viewer/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/redacted event summaries/i)).toBeInTheDocument();
    expect(screen.getAllByText("mock_event_ref_001").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/source: CCC Web mock surface/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(/No event action is available from this UI/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Event detail is redacted summary metadata only/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw file/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw memory/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/credential/i)).not.toBeInTheDocument();
  });

  it("renders M16 event timeline and run receipt trace summaries without raw payloads", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/events/timeline");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Event Timeline/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/M16 trace surface/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Timeline and trace views are read-only/i),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/redacted summary-only/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_run_ref_001").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("mock_correlation_ref_001").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_event_ref_001").length).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_receipt_ref_001").length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByText("mock_evidence_ref_gate_001").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Foundation Gate evidence summary/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(/No trace export or external telemetry is available/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Trace detail is redacted summary metadata only/i),
    ).toBeInTheDocument();

    for (const label of [
      /^execute$/i,
      /^run$/i,
      /^export$/i,
      /^send$/i,
      /^deploy$/i,
      /^enable$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
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

    expect(
      await screen.findByRole("heading", { name: /Event Timeline/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByRole("heading", { name: "mock_event_ref_001" }).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("article", { name: /mock_event_ref_001/i }),
    ).toHaveAttribute("aria-current", "true");

    const traceButtons = screen.getAllByRole("button", { name: /view trace/i });
    fireEvent.click(traceButtons[1]);

    expect(
      screen.getAllByRole("heading", { name: "mock_event_ref_002" }).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("article", { name: /mock_event_ref_002/i }),
    ).toHaveAttribute("aria-current", "true");
    expect(
      screen.getByText(/Trace detail is redacted summary metadata only/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/NO_PRODUCTION_AUTHORITY/i).length,
    ).toBeGreaterThan(0);

    for (const label of [
      /^execute$/i,
      /^run$/i,
      /^export$/i,
      /^send$/i,
      /^write$/i,
      /^deploy$/i,
      /^enable$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
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

    expect(
      await screen.findByRole("heading", { name: /Evidence Viewer/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/M17 knowledge surface/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Evidence views are read-only/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/REDACTED_SUMMARY_ONLY/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("mock_evidence_ref_001").length).toBeGreaterThan(
      0,
    );
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
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw secret/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw file/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw memory/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider payload/i)).not.toBeInTheDocument();
  });

  it("renders FCC-P1-006 Evidence Timeline as readable safe refs", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/evidence");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Evidence Timeline/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("storage_backed_redacted_refs")).toBeInTheDocument();
    expect(
      screen.getAllByText("GET /control-center/today/summary").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/Private source artifacts/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Approval refs are identifiers only/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/rollback refs do not perform rollback/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Foundation Gate refs do not confer release authority/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/latency refs are measurement evidence only/i),
    ).toBeInTheDocument();

    for (const marker of [
      "receipt_audit_rollback_ref",
      "plan_evidence_ref",
      "memory_review_evidence_ref",
      "source_readiness_evidence_ref",
      "foundation_gate_latency_ref",
      "receipt-plan:founder-loop:mock-setup-hardening",
      "audit-plan:founder-loop:mock-setup-hardening",
      "replay-ref:founder-loop:action-inbox",
      "rollback-plan:founder-loop:mock-setup-hardening",
      "latency-ref:foundation-gate:latest-report",
      "foundation-gate-ref:latest-report",
      "rollback_execution_not_scoped",
      "no_raw_evidence_display",
      "approval_refs_are_identifiers_only",
      "foundation_gate_refs_not_production_authority",
      "latency_refs_not_authority",
      "connector_source_runtime_blocked",
    ]) {
      expect(screen.getAllByText(marker).length).toBeGreaterThan(0);
    }

    for (const label of [
      /^execute$/i,
      /^run$/i,
      /^write$/i,
      /^delete$/i,
      /^rollback$/i,
      /^approve$/i,
      /^send$/i,
      /^sync$/i,
      /^reveal raw$/i,
      /^show raw$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw response/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider payload/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw path/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw log/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/environment dump/i)).not.toBeInTheDocument();
  });

  it("renders M17 file ref summaries without raw file contents or filesystem controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/files");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /File Reference Viewer/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/File ref views are read-only/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText("mock_file_ref_001").length).toBeGreaterThan(0);
    expect(screen.getByText(/Safe filename/i)).toBeInTheDocument();
    expect(
      screen.getByText(/File writes are not available from this UI/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/No filesystem browsing is available/i),
    ).toBeInTheDocument();

    for (const label of [
      /open file/i,
      /delete file/i,
      /write file/i,
      /browse filesystem/i,
      /^execute$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw file content/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(new RegExp("/Users/", "i")),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/\/home\//i)).not.toBeInTheDocument();
  });

  it("renders M37 file review packets with review-only approval capture controls", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/files/review");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /File Review Surface/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/M37 review approval capture/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/mock and non-authoritative/i)).toBeInTheDocument();
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/NO_PRODUCTION_AUTHORITY/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/Review-only surface/i)).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /^Redacted preview$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Reviewed change summary mentions \[REDACTED:SECRET_ASSIGNMENT\]/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/Redaction summary/i)).toBeInTheDocument();
    expect(
      screen.getByText(
        /Secret-like assignment and private path fragments were removed before display/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/Exact binding refs/i)).toBeInTheDocument();
    expect(
      screen.getAllByText("file-review-packet:mock_001").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("redacted-file-preview-output:mock_001"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("file-review-redaction-summary:mock_001"),
    ).toBeInTheDocument();
    expect(screen.getByText("file-ref:mock_review_001")).toBeInTheDocument();
    expect(
      screen.getByText(
        "filesystem-preview-path:safe-root_m36/docs/review-summary.md",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Approval gate contract status/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/exact_binding_ready/i)).toBeInTheDocument();
    expect(screen.getByText(/Receipt plan metadata/i)).toBeInTheDocument();
    expect(screen.getByText(/raw content stored: no/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /approve review-only/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /deny review-only/i }),
    ).toBeInTheDocument();
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
    const reviewButtons = screen.getAllByRole("button", {
      name: /view review packet/i,
    });
    expect(reviewButtons.length).toBeGreaterThan(1);
    fireEvent.click(reviewButtons[1]);

    expect(
      screen.getAllByRole("heading", { name: "file-review-packet:mock_002" })
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("article", { name: /file-review-packet:mock_002/i }),
    ).toHaveAttribute("aria-current", "true");
    expect(screen.getByText("file-ref:mock_review_002")).toBeInTheDocument();
    expect(
      screen.getByText(
        "filesystem-preview-path:safe-root_m36/docs/alternate-review.md",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Review approval capture is review-only persistence/i)
        .length,
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
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(
      screen.getByRole("button", { name: /approve review-only/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /deny review-only/i }),
    ).toBeInTheDocument();
    expect(screen.queryByText(/raw_content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/full_file_content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/unredacted_preview/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(new RegExp("/Users/", "i")),
    ).not.toBeInTheDocument();
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
    fireEvent.click(
      screen.getByRole("button", { name: /approve review-only/i }),
    );

    expect(screen.getByText(/approved_for_review_only/i)).toBeInTheDocument();
    expect(screen.getByText(/capture persisted: yes/i)).toBeInTheDocument();
    expect(screen.getByText(/raw access authorized: no/i)).toBeInTheDocument();
    expect(
      screen.getByText(/context proposal authorized: no/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/memory write authorized: no/i),
    ).toBeInTheDocument();
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
    fireEvent.click(
      screen.getByRole("button", { name: /approve review-only/i }),
    );
    expect(screen.getByText(/approved_for_review_only/i)).toBeInTheDocument();

    // Switching to a different packet must reset the capture state to that
    // packet's own value rather than leaking the first packet's approval.
    const reviewButtons = screen.getAllByRole("button", {
      name: /view review packet/i,
    });
    fireEvent.click(reviewButtons[1]);

    expect(
      screen.getByRole("article", { name: /file-review-packet:mock_002/i }),
    ).toHaveAttribute("aria-current", "true");
    expect(
      screen.queryByText(/approved_for_review_only/i),
    ).not.toBeInTheDocument();
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
      expect(documentText.toLowerCase()).not.toContain(
        unsafeFragment.toLowerCase(),
      );
    }

    expect(screen.getAllByText(/safe refs only/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        /Only the review approval capture route may persist safe refs/i,
      ).length,
    ).toBeGreaterThan(0);
  });

  it("renders M39 context proposals as read-only safe proposal summaries", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/context/proposals");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Context Proposal Surface/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/M39 CCC context proposal surface/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/mock and non-authoritative/i)).toBeInTheDocument();
    expect(screen.getAllByText(/proposal-only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/NO_PRODUCTION_AUTHORITY/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/Safe proposal sections/i)).toBeInTheDocument();
    expect(screen.getByText(/Redacted review excerpt/i)).toBeInTheDocument();
    expect(
      screen.getByText(
        /M39 surface displays redacted proposal text with \[REDACTED:SECRET_ASSIGNMENT\]/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/Source chain refs/i)).toBeInTheDocument();
    expect(
      screen.getAllByText("safe-context-proposal:mock_001").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("file-review-approval-capture:mock_001").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("file-review-packet:mock_001").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("redacted-file-preview-output:mock_001").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("file-review-redaction-summary:mock_001").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("file-ref:mock_review_001").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "filesystem-preview-path:safe-root_m39/docs/review-summary.md",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("user:mock_reviewer_001").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Decision status/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/proposal_ready_for_review/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Receipt plan metadata/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/context injected: no/i)).toBeInTheDocument();
    expect(
      screen.getByText(/OpenWebUI handoff authorized: no/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/memory write authorized: no/i),
    ).toBeInTheDocument();
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
    const proposalButtons = screen.getAllByRole("button", {
      name: /view context proposal/i,
    });
    expect(proposalButtons.length).toBeGreaterThan(1);
    fireEvent.click(proposalButtons[1]);

    expect(
      screen.getAllByRole("heading", { name: "safe-context-proposal:mock_002" })
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("article", { name: /safe-context-proposal:mock_002/i }),
    ).toHaveAttribute("aria-current", "true");
    expect(
      screen.getAllByText(
        "safe-context-proposal-section:mock_002:redacted-preview",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("file-ref:mock_review_002").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "filesystem-preview-path:safe-root_m39/docs/alternate-review.md",
      ).length,
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
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw_content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/full_file_content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/unredacted_preview/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(new RegExp("/Users/", "i")),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/\/home\//i)).not.toBeInTheDocument();
    expect(screen.queryByText(/supersecretvalue123/i)).not.toBeInTheDocument();
    expect(
      screen.getAllByText(/Control Center output is not authority/i).length,
    ).toBeGreaterThan(0);
  });

  it("renders Memory Review as a review-only inbox with explicit memory authority blockers", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/memory");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /^Memory Review$/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Review posture/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Missing contracts/i })).toBeInTheDocument();
    expect(screen.getByText("/memory")).toBeInTheDocument();
    expect(
      screen.getByText("GET /control-center/today/summary"),
    ).toBeInTheDocument();
    expect(screen.getByText("storage_backed_review_queue")).toBeInTheDocument();
    expect(
      screen.getByText("founder-loop-storage:mock-local-sqlite-jsonl"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Memory writes").nextElementSibling,
    ).toHaveTextContent("disabled");
    expect(
      screen.getByText("Memory deletes").nextElementSibling,
    ).toHaveTextContent("disabled");
    expect(
      screen.getByText("Context injection").nextElementSibling,
    ).toHaveTextContent("disabled");
    expect(
      screen.getByText(
        /Review-only memory candidates; recall is not truth/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Memory review is inspection-only/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText("memory-review:founder-loop-preferences"),
    ).toBeInTheDocument();
    expect(screen.getByText("operator_preference")).toBeInTheDocument();
    expect(screen.getAllByText("review_needed").length).toBeGreaterThan(0);
    expect(
      screen.getByText("correction_requires_scoped_memory_write_contract"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("rejection_is_review_state_only_until_capture_contract"),
    ).toBeInTheDocument();
    expect(screen.getByText("retention_policy_not_bound")).toBeInTheDocument();
    expect(screen.getByText("delete_execution_not_scoped")).toBeInTheDocument();
    expect(screen.getByText("safe_summary_unverified")).toBeInTheDocument();
    expect(
      screen.getByText("recheck_source_refs_before_memory_use"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("provenance-ref:founder-loop-memory:mock-preferences"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("source-ref:founder-loop-storage").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("contract-ref:memory-write-policy-binding-missing").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("contract-ref:memory-retention-delete-missing").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("contract-ref:memory-review-decision-capture-missing").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("contract-ref:context-injection-missing").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("no_memory_write").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_context_injection").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_memory_delete").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_raw_source_display").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_connector_write").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("no_model_provider_authority").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("no_background_sync").length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Review provenance and evidence refs/i),
    ).toBeInTheDocument();

    for (const label of [
      /^accept$/i,
      /^correct$/i,
      /^reject$/i,
      /^retain$/i,
      /^delete$/i,
      /^write$/i,
      /^inject$/i,
      /^approve$/i,
      /^run$/i,
      /^sync$/i,
      /^export$/i,
      /^save$/i,
      /learn this/i,
      /forget this/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/raw memory content/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw transcript/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw prompt/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/raw source/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/authoritative truth/i)).not.toBeInTheDocument();
  });

  it("keeps alternate M17 metadata selection read-only and redacted", async () => {
    for (const route of ["/evidence", "/files"]) {
      cleanup();
      mockFetchWithFallback();
      window.history.pushState({}, "", route);
      render(<App />);

      await waitFor(() => {
        expect(
          screen.getAllByRole("button", { name: /view metadata/i }).length,
        ).toBeGreaterThan(1);
      });
      const metadataButtons = screen.getAllByRole("button", {
        name: /view metadata/i,
      });
      fireEvent.click(metadataButtons[1]);

      const expectedRef =
        route === "/evidence"
          ? "mock_evidence_ref_002"
          : "mock_file_ref_002";
      expect(
        screen.getAllByRole("heading", { name: expectedRef }).length,
      ).toBeGreaterThan(0);
      expect(
        screen.getByRole("article", { name: new RegExp(expectedRef, "i") }),
      ).toHaveAttribute("aria-current", "true");
      expect(
        screen.getAllByText(/redacted_summary_only/i).length,
      ).toBeGreaterThan(0);
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
        expect(
          screen.queryByRole("button", { name: label }),
        ).not.toBeInTheDocument();
      }
      expect(
        screen.queryByText(/raw evidence payload/i),
      ).not.toBeInTheDocument();
      expect(screen.queryByText(/raw file content/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/raw memory content/i)).not.toBeInTheDocument();
      expect(
        screen.queryByText(new RegExp("/Users/", "i")),
      ).not.toBeInTheDocument();
      expect(screen.queryByText(/\/home\//i)).not.toBeInTheDocument();
    }
    expect(mockControlCenterData.m17Knowledge.memories[1].memoryRef).toBe(
      "mock_memory_ref_002",
    );
  });

  it("renders M18 local runtime status as read-only validation-only metadata", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/runtime/local");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Local Runtime Status/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/M18 local runtime surface/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Local runtime status is read-only/i),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/Runtime readiness report/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/manual_loopback_smoke/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/MOCK_DATA_ONLY/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/NO_RUNTIME_EXECUTION/i).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getByText(
        /No local runtime is started, stopped, connected, or executed from this UI/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Model output remains non-authoritative/i),
    ).toBeInTheDocument();

    for (const label of [
      /^execute$/i,
      /^run$/i,
      /^start$/i,
      /^stop$/i,
      /^connect$/i,
      /^launch$/i,
      /^call model$/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
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
      await screen.findByRole("heading", {
        name: /Manual Smoke Control Surface/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/validation-only report surface/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Manual smoke reports are safe summaries/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/mock_manual_smoke_report_ref_001/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/fixed prompt hash/i)).toBeInTheDocument();
    expect(screen.getByText(/response preview shown: no/i)).toBeInTheDocument();
    expect(
      screen.getByText(
        /Manual smoke execution remains CLI-only, fixed-prompt-only, approval-gated/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/REDACTED_SUMMARY_ONLY/i).length,
    ).toBeGreaterThan(0);
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
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
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
              safe_message:
                "Control Center preview is allowed. No action was executed.",
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

    expect(
      await screen.findByText(/Preview only action request/i),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/Risk level/i)).toBeInTheDocument();
    expect(
      screen.getByText(
        /High and critical previews remain non-execution decisions/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /Blocked execution action/i }),
    ).toBeDisabled();
    fireEvent.click(
      await screen.findByRole("button", { name: /preview action/i }),
    );

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        API_ENDPOINTS.actionPreview,
        expect.any(Object),
      ),
    );
    const [, options] =
      fetchMock.mock.calls.find((call) => call[1]?.method === "POST") ?? [];
    expect(options?.method).toBe("POST");
    expect(
      screen.queryByRole("button", { name: /execute/i }),
    ).not.toBeInTheDocument();
  });

  it("shows live local backend connection state only when every read request succeeds", async () => {
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      if (options?.method === "POST") {
        throw new Error("unexpected preview request");
      }
      return new Response(
        JSON.stringify(envelopeForReadEndpoint(String(url))),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/dashboard");
    render(<App />);

    expect(await screen.findByText("Backend online")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Live data came from local read-only\/preview-only backend API routes/i,
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Mock fallback active/i)).not.toBeInTheDocument();
  });

  it("renders setup assistant summary from the local backend when available", async () => {
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      if (options?.method === "POST") {
        throw new Error("unexpected preview request");
      }
      return new Response(
        JSON.stringify(envelopeForReadEndpoint(String(url))),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/setup");
    render(<App />);

    expect(await screen.findByText("Backend online")).toBeInTheDocument();
    expect(
      screen.getByText("Backend API setup timeline"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("control-center:setup-assistant-api-test"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("macos-setup-approval-envelope:api-summary").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("idempotency-ref:macos-setup-api-summary").length,
    ).toBeGreaterThan(0);
  });

  it("shows degraded local backend state when only part of the read set succeeds", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (String(url).includes(API_ENDPOINTS.runtimeCapabilityMatrix)) {
        throw new Error("capability matrix unavailable");
      }
      return new Response(
        JSON.stringify(envelopeForReadEndpoint(String(url))),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/dashboard");
    render(<App />);

    expect(await screen.findByText("Backend degraded")).toBeInTheDocument();
    expect(
      screen.getByText(/Some local backend summaries were unavailable/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /non-authoritative mock fallback filled missing panels/i,
      ),
    ).toBeInTheDocument();
  });

  it("does not expose dangerous action control labels", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/action-preview");
    render(<App />);

    await screen.findByText(/Preview only action request/i);

    for (const label of [
      /execute/i,
      /^run$/i,
      /send/i,
      /deploy/i,
      /enable/i,
      /approve/i,
    ]) {
      expect(
        screen.queryByRole("button", { name: label }),
      ).not.toBeInTheDocument();
    }
  });

  it("renders unsafe preview decisions as blocked without claiming execution", async () => {
    const fetchMock = vi.fn(async (_url: string, options?: RequestInit) => {
      const body = JSON.parse(String(options?.body ?? "{}")) as {
        target_ref?: string;
      };
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
            safe_message:
              "Control Center preview was blocked by read-only policy.",
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

    expect((await screen.findAllByText("blocked")).length).toBeGreaterThan(0);
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

    expect(
      await screen.findByText(/Secret-like input was redacted/i),
    ).toBeInTheDocument();
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
                message:
                  "Preview rejected because token=supersecretvalue123 was invalid.",
              },
            }),
            { status: 400, headers: { "Content-Type": "application/json" } },
          ),
      ),
    );
    window.history.pushState({}, "", "/action-preview");
    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", { name: /preview action/i }),
    );

    expect(
      await screen.findByText(
        /Preview rejected because \[redacted\] was invalid/i,
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/supersecretvalue123/i)).not.toBeInTheDocument();
  });

  it("keeps read endpoints separate from the single preview POST endpoint", () => {
    expect(READ_ENDPOINTS).not.toContain(API_ENDPOINTS.actionPreview);
    expect(READ_ENDPOINTS).not.toContain(
      API_ENDPOINTS.runtimeSmokeReportValidate,
    );
    expect(API_ENDPOINTS.actionPreview).toBe("/control-center/actions/preview");
    expect(API_ENDPOINTS.runtimeSmokeReportValidate).toBe(
      "/runtime/smoke-reports/validate",
    );
    expect(isPreviewEndpoint(API_ENDPOINTS.actionPreview)).toBe(true);
    expect(isAllowedReadEndpoint(API_ENDPOINTS.controlCenterDashboard)).toBe(
      true,
    );
    expect(isAllowedReadEndpoint(API_ENDPOINTS.founderTodaySummary)).toBe(
      true,
    );
    expect(isAllowedReadEndpoint(API_ENDPOINTS.founderActionsInbox)).toBe(
      true,
    );
    expect(isAllowedReadEndpoint(API_ENDPOINTS.founderMorningBriefing)).toBe(
      true,
    );
    expect(isAllowedReadEndpoint(API_ENDPOINTS.founderStorageStatus)).toBe(
      true,
    );
    expect(isAllowedReadEndpoint("/control-center/actions/execute")).toBe(
      false,
    );
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
    [API_ENDPOINTS.setupAssistantSummary]: mockApiData.setupAssistantSummary,
    [API_ENDPOINTS.founderTodaySummary]: mockApiData.founderToday,
    [API_ENDPOINTS.founderActionsInbox]: mockApiData.founderActionsInbox,
    [API_ENDPOINTS.founderMorningBriefing]:
      mockApiData.founderMorningBriefing,
    [API_ENDPOINTS.founderStorageStatus]: mockApiData.founderStorageStatus,
  };
  const endpoint = Object.keys(data).find((candidate) =>
    url.endsWith(candidate),
  );
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
    api_route_refs: [
      "/control-center/dashboard",
      "/control-center/actions/preview",
    ],
    metadata: {
      read_only: true,
      preview_only: true,
      production_control_center: false,
    },
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
      route_count: 112,
      control_center_route_count: 13,
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
    route_count: 13,
    routes: [
      {
        path: "/control-center/dashboard",
        methods: ["GET"],
        operation_id: "get_control_center_dashboard",
        tags: ["control-center"],
        validation_only: true,
        route_group: "control-center",
        owner: "Python Agent Core",
        service_module: "control_center_service",
        side_effect_class: "read_only",
        risk_class: "low",
        release_status: "implemented",
        auth_posture: "local-dev unauthenticated; production auth future",
        blocked_from_production: true,
        evidence_refs: [
          "docs/control_center/route_status_manifest.json",
          "tests/test_control_center_api_routes.py",
        ],
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
  setupAssistantSummary: {
    plan_ref: "macos-setup-plan:api-test",
    status: "dry_run_only",
    macos_first: true,
    local_first: true,
    disabled_by_default: true,
    native_macos_app_ready: false,
    control_center_preview_ready: true,
    setup_question_assistant_enabled: false,
    model_output_authoritative: false,
    installer_side_effects_enabled: false,
    visual_shell_ref: "control-center:setup-assistant-api-test",
    steps: [
      {
        step_id: "macos-setup-step:api-summary",
        label: "Backend API setup timeline",
        kind: "first_launch",
        status: "dry_run_only",
        safe_summary: "Read-only setup summary from backend test fixture.",
        route_refs: ["/control-center/setup-assistant/summary"],
        detail_preview: ["bounded setup preview only"],
        log_preview: ["no command executed"],
        approval_required: true,
        approval_ref: "approval-ref:macos-setup-api-summary",
        receipt_ref: "receipt-plan:macos-setup-api-summary",
        rollback_ref: "rollback-plan:macos-setup-api-summary",
        latency_ref: "latency-ref:macos-setup-api-summary",
        reason_codes: ["MACOS_SETUP_SUMMARY_API_TEST"],
        next_safe_action: "inspect_setup_plan",
      },
    ],
    model_recommendations: [
      {
        recommendation_ref: "macos-setup-model-rec:api-test",
        model_ref: "local-model-option:api-test",
        display_name: "API test model class",
        fit_summary: "Recommendation class only.",
        recommended_for: "Frontend mapper test.",
        memory_bucket: "ram:test",
        disk_bucket: "disk:test",
        privacy_summary: "No model call is made.",
        approval_required_before_download: true,
        selected_by_default: true,
        reason_codes: ["MACOS_SETUP_MODEL_RECOMMENDATION_ONLY"],
      },
    ],
    bridge_previews: [
      {
        bridge_ref: "macos-setup-bridge:api-test",
        label: "API test bridge",
        status: "approval_required",
        safe_summary: "Bridge preview only.",
        enablement_default: "disabled",
        approval_required: true,
        reason_codes: ["MACOS_SETUP_BRIDGE_DISABLED_BY_DEFAULT"],
      },
    ],
    approval_envelopes: [
      {
        envelope_ref: "macos-setup-approval-envelope:api-summary",
        status: "approval_required",
        setup_step_id: "macos-setup-step:api-summary",
        setup_step_kind: "first_launch",
        safe_summary:
          "Dry-run approval envelope from backend test fixture; no setup mutation is enabled.",
        requested_scope_refs: ["scope-ref:macos-setup-api-summary"],
        approval_request_ref: "approval-ref:macos-setup-api-summary",
        expected_receipt_ref: "receipt-plan:macos-setup-api-summary",
        rollback_plan_ref: "rollback-plan:macos-setup-api-summary",
        idempotency_key_ref: "idempotency-ref:macos-setup-api-summary",
        risk_class: "medium",
        side_effect_class: "validation_only",
        not_scoped_actions: ["setup-mutation"],
        blocked_runtime_authority: ["installer-authority"],
        evidence_refs: ["docs-ref:uaa-setup-assistant-plan"],
        verifier_refs: ["vitest:control-center-app"],
        operator_next_action: "inspect_setup_plan",
        stale_state_handling: "Stale if backend setup summary fixture changes.",
        redaction_summary:
          "Safe refs only; raw logs, paths, prompts, and credentials are omitted.",
        dry_run_only: true,
        approval_required: true,
        approval_ref_is_identifier_only: true,
        exact_scope_required: true,
        idempotency_required: true,
        rollback_required: true,
        redaction_required: true,
        disabled_by_default: true,
        reason_codes: ["MACOS_SETUP_APPROVAL_ENVELOPE_DRY_RUN_ONLY"],
      },
    ],
    receipt_plan: {
      receipt_plan_ref: "macos-setup-receipt-plan:api-test",
      audit_ref: "macos-setup-audit:api-test",
      latency_ref: "macos-setup-latency:api-test",
      safe_summary: "Receipt preview only.",
      receipt_created: false,
      audit_event_created: false,
      raw_log_stored: false,
      raw_prompt_stored: false,
      raw_provider_payload_stored: false,
      credential_material_stored: false,
    },
    rollback_plan: {
      rollback_plan_ref: "macos-setup-rollback-plan:api-test",
      uninstall_ref: "macos-setup-uninstall:api-test",
      safe_summary: "Rollback preview only.",
      rollback_available_after_approval: true,
      rollback_executed: false,
    },
    blocked_capabilities: ["macos-setup-model-download"],
    next_steps: ["Review setup summary."],
    morning_review_checklist: ["Confirm setup summary is dry-run only."],
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
        requestedActionSummary:
          "Preview-only policy review for a proposed local workspace change.",
        subjectSummary:
          "Mock local review subject; no file body or prompt body is shown.",
        reasonCodes: ["CONTROL_CENTER_REVIEW_REQUIRED"],
        createdAt: "2026-01-01T00:00:00Z",
        expiresAt: "2026-01-01T01:00:00Z",
        requiredNextAction: "Review in Python Agent Core approval authority.",
        safeMessage: "No approval was granted from this UI.",
        previewOutcomeSummary:
          "Grant or denial outcome is preview-only and non-authoritative.",
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
  founderToday: {
    schema_version: "founder_loop_storage.v1",
    status: "storage_backed_partial_loop",
    surface: "Today",
    storage_ref: "founder-loop-storage:test",
    side_effect_class: "local_dev_workspace_only",
    approval_required_before_mutation: true,
    sections: {
      action_inbox_count: 1,
      plan_count: 1,
      memory_review_count: 1,
      briefing_count: 1,
      evidence_timeline_count: 5,
    },
    actions: [
      {
        item_ref: "founder-action:test",
        title: "Storage-backed action",
        safe_summary: "Bounded action summary.",
        surface: "Actions",
        priority: "high",
        risk_class: "high",
        status: "review_ready",
        side_effect_class: "validation_only",
        authority_boundary:
          "Review-only display; Python Agent Core and LocalApprovalAuthority must validate exact scope before mutation.",
        approval_required: true,
        approval_envelope_ref: "approval-envelope:founder-loop:test",
        approval_envelope_status: "dry_run_ref_available",
        state_change_contract_ref: "contract-ref:founder-loop:test",
        state_change_readiness: "blocked_pending_scoped_mutation_contract",
        blocked_state: "Scoped backend contract required",
        evidence_refs: ["evidence-ref:founder-loop:test-action"],
        receipt_refs: ["receipt-plan:founder-loop:test"],
        audit_refs: ["audit-plan:founder-loop:test"],
        idempotency_key_ref: "idempotency-ref:founder-loop:test",
        expires_at: "review_required_before_mutation",
        stale_state: "recheck_action_summary_before_mutation",
        rollback_ref: "rollback-plan:founder-loop:test",
        safe_disable_ref: "safe-disable:founder-loop:test",
        next_safe_action:
          "Review refs only; request a scoped state-change milestone before mutation.",
      },
    ],
    plans: [
      {
        plan_ref: "plan-summary:test",
        title: "Founder Loop test plan",
        status: "partial_backend_not_product_ready",
        safe_summary: "Bounded plan summary.",
        next_step_summary: "Review route-backed summaries.",
        evidence_refs: ["evidence-ref:founder-loop:test-plan"],
      },
    ],
    memory_review_queue: [
      {
        review_ref: "memory-review:test",
        title: "Memory review",
        safe_summary: "Bounded memory summary.",
        candidate_kind: "operator_preference",
        priority: "high",
        status: "review_needed",
        review_state: "review_needed",
        side_effect_class: "local_dev_workspace_only",
        authority_boundary:
          "Review-only memory candidate; recall is not truth, and writes, deletes, and context injection remain unscoped.",
        provenance_refs: ["provenance-ref:founder-loop-memory:test"],
        source_refs: ["source-ref:founder-loop-storage"],
        missing_contract_refs: [
          "contract-ref:memory-write-policy-binding-missing",
          "contract-ref:memory-retention-delete-missing",
          "contract-ref:memory-review-decision-capture-missing",
          "contract-ref:context-injection-missing",
        ],
        correction_posture: "correction_requires_scoped_memory_write_contract",
        rejection_posture: "rejection_is_review_state_only_until_capture_contract",
        retention_posture: "retention_policy_not_bound",
        delete_posture: "delete_execution_not_scoped",
        confidence_posture: "safe_summary_unverified",
        stale_state: "recheck_source_refs_before_memory_use",
        blocked_states: [
          "no_memory_write",
          "no_context_injection",
          "no_memory_delete",
          "no_raw_source_display",
          "no_connector_write",
          "no_model_provider_authority",
          "no_background_sync",
        ],
        next_safe_action:
          "Review provenance and evidence refs; keep writes blocked until a scoped memory policy milestone.",
        evidence_refs: ["evidence-ref:founder-loop:test-memory"],
      },
    ],
    memory_review_route_ref: "/memory",
    memory_review_backend_route_ref: "GET /control-center/today/summary",
    memory_review_status: "storage_backed_review_queue",
    memory_review_authority_boundary:
      "Review-only memory candidates; recall is not truth, and writes, deletes, context injection, connector writes, model/provider calls, and background sync are unscoped.",
    memory_write_enabled: false,
    memory_delete_enabled: false,
    context_injection_enabled: false,
    memory_review_missing_contract_refs: [
      "contract-ref:memory-write-policy-binding-missing",
      "contract-ref:memory-retention-delete-missing",
      "contract-ref:memory-review-decision-capture-missing",
      "contract-ref:context-injection-missing",
    ],
    memory_review_blocked_states: [
      "no_memory_write",
      "no_context_injection",
      "no_memory_delete",
      "no_raw_source_display",
      "no_connector_write",
      "no_model_provider_authority",
      "no_background_sync",
    ],
    briefing_items: [
      {
        briefing_ref: "briefing:test",
        title: "Briefing item",
        safe_summary: "Bounded briefing summary.",
        priority: "high",
        status: "active",
        side_effect_class: "local_dev_workspace_only",
        authority_boundary:
          "Review-only briefing summary; source reads and delivery remain unscoped.",
        source_readiness: "local_status_refs_only",
        source_refs: ["source-ref:control-center-route-status"],
        missing_contract_refs: [
          "contract-ref:email-read-only-missing",
          "contract-ref:calendar-read-only-missing",
          "contract-ref:notification-delivery-missing",
        ],
        blocked_states: [
          "no_email_calendar_source_contract",
          "no_background_refresh",
        ],
        stale_state: "recheck_route_status_before_briefing_use",
        evidence_gap: "No email, calendar, or notification source evidence is bound.",
        next_safe_action:
          "Use route and storage refs only; define source contracts before refresh.",
        evidence_refs: ["evidence-ref:founder-loop:test-briefing"],
      },
    ],
    evidence_timeline: [
      {
        timeline_item_ref: "evidence-timeline:action/founder-action/test",
        item_kind: "receipt_audit_rollback_ref",
        title: "Storage-backed action",
        safe_summary:
          "Action evidence is shown as receipt, audit, idempotency, rollback, and safe-disable refs only; mutation stays blocked.",
        source_refs: ["founder-action:test"],
        status_refs: ["status-ref:founder-loop-action-inbox"],
        related_route_refs: ["GET /control-center/actions/inbox", "/actions"],
        side_effect_class: "validation_only",
        authority_posture:
          "Review-only display; Python Agent Core and LocalApprovalAuthority must validate exact scope before mutation.",
        approval_posture: "dry_run_ref_available",
        receipt_refs: ["receipt-plan:founder-loop:test"],
        audit_refs: ["audit-plan:founder-loop:test"],
        replay_refs: ["replay-ref:founder-loop:action-inbox"],
        rollback_refs: ["rollback-plan:founder-loop:test"],
        rollback_blockers: [],
        latency_refs: [],
        foundation_gate_refs: [],
        redaction_status: "redacted_summary_only",
        stale_state: "recheck_action_summary_before_mutation",
        missing_evidence_posture: "receipt_refs_available",
        blocked_states: [
          "blocked_pending_scoped_mutation_contract",
          "approval_refs_are_identifiers_only",
        ],
        next_safe_action:
          "Review refs only; request a scoped state-change milestone before mutation.",
      },
      {
        timeline_item_ref: "evidence-timeline:plan/plan-summary/test",
        item_kind: "plan_evidence_ref",
        title: "Founder Loop test plan",
        safe_summary:
          "Plan evidence is a bounded summary ref and does not create execution authority or a durable run by itself.",
        source_refs: ["plan-summary:test"],
        status_refs: ["status-ref:founder-loop-plan-summary"],
        related_route_refs: ["/plans", "/task-decomposition/status"],
        side_effect_class: "validation_only",
        authority_posture:
          "Plan summary is inspection-only and not execution authority.",
        approval_posture: "approval_required_before_execution_scope",
        receipt_refs: [],
        audit_refs: [],
        replay_refs: ["replay-ref:founder-loop:plan-summary"],
        rollback_refs: [],
        rollback_blockers: ["rollback_not_applicable_for_plan_summary"],
        latency_refs: [],
        foundation_gate_refs: [],
        redaction_status: "redacted_summary_only",
        stale_state: "recheck_plan_refs_before_execution_claims",
        missing_evidence_posture: "run_receipt_missing_until_execution_contract",
        blocked_states: ["no_plan_execution_from_evidence_timeline"],
        next_safe_action: "Review route-backed summaries.",
      },
      {
        timeline_item_ref: "evidence-timeline:memory/memory-review/test",
        item_kind: "memory_review_evidence_ref",
        title: "Memory review",
        safe_summary:
          "Memory evidence is recall metadata only. Memory is not truth, not approval, and not context-injection authority.",
        source_refs: ["memory-review:test", "source-ref:founder-loop-storage"],
        status_refs: [
          "status-ref:founder-loop-memory-review",
          "contract-ref:memory-write-policy-binding-missing",
          "contract-ref:memory-retention-delete-missing",
          "contract-ref:memory-review-decision-capture-missing",
          "contract-ref:context-injection-missing",
        ],
        related_route_refs: ["GET /control-center/today/summary", "/memory"],
        side_effect_class: "local_dev_workspace_only",
        authority_posture:
          "Review-only memory candidate; recall is not truth, and writes, deletes, and context injection remain unscoped.",
        approval_posture: "memory_review_refs_do_not_authorize_writes",
        receipt_refs: [],
        audit_refs: [],
        replay_refs: ["replay-ref:founder-loop:memory-review"],
        rollback_refs: [],
        rollback_blockers: ["memory_write_or_delete_rollback_not_scoped"],
        latency_refs: [],
        foundation_gate_refs: [],
        redaction_status: "redacted_summary_only",
        stale_state: "recheck_source_refs_before_memory_use",
        missing_evidence_posture:
          "memory_contract_refs_missing_until_scoped_review_contracts",
        blocked_states: [
          "no_memory_write",
          "no_context_injection",
          "no_memory_delete",
        ],
        next_safe_action:
          "Review provenance and evidence refs; keep writes blocked until a scoped memory policy milestone.",
      },
      {
        timeline_item_ref: "evidence-timeline:briefing/briefing/test",
        item_kind: "source_readiness_evidence_ref",
        title: "Briefing item",
        safe_summary:
          "Briefing evidence is source-readiness posture only. Email, calendar, connector, refresh, and notification runtime stay blocked.",
        source_refs: ["briefing:test", "source-ref:control-center-route-status"],
        status_refs: ["evidence-timeline:briefing-status/local_status_refs_only"],
        related_route_refs: [
          "GET /control-center/morning-briefing/summary",
          "/briefing",
        ],
        side_effect_class: "local_dev_workspace_only",
        authority_posture:
          "Review-only briefing summary; source reads and delivery remain unscoped.",
        approval_posture: "source_refs_do_not_authorize_connector_runtime",
        receipt_refs: [],
        audit_refs: [],
        replay_refs: ["replay-ref:founder-loop:morning-briefing"],
        rollback_refs: [],
        rollback_blockers: ["source_refresh_rollback_not_scoped"],
        latency_refs: [],
        foundation_gate_refs: [],
        redaction_status: "redacted_summary_only",
        stale_state: "recheck_route_status_before_briefing_use",
        missing_evidence_posture:
          "missing_source_contract_refs_until_read_only_runtime_milestone",
        blocked_states: [
          "no_email_calendar_source_contract",
          "no_background_refresh",
        ],
        next_safe_action:
          "Use route and storage refs only; define source contracts before refresh.",
      },
      {
        timeline_item_ref: "evidence-timeline:foundation-gate/latency",
        item_kind: "foundation_gate_latency_ref",
        title: "Foundation Gate and latency posture",
        safe_summary:
          "Foundation Gate and latency refs are status evidence only; they do not grant production authority or runtime authority.",
        source_refs: ["status-ref:foundation-gate-summary"],
        status_refs: ["status-ref:foundation-gate-report"],
        related_route_refs: [
          "GET /control-center/foundation-gate/summary",
          "/foundation-gate",
        ],
        side_effect_class: "validation_only",
        authority_posture:
          "Foundation Gate status and latency measurements are evidence, not production authority.",
        approval_posture: "approval_refs_are_identifiers_only_not_authority",
        receipt_refs: [],
        audit_refs: ["audit-ref:foundation-gate:latest"],
        replay_refs: ["replay-ref:foundation-gate:latest"],
        rollback_refs: [],
        rollback_blockers: ["rollback_execution_not_scoped"],
        latency_refs: [
          "latency-ref:foundation-gate:latest-report",
          "performance-ref:release-latency-baseline",
        ],
        foundation_gate_refs: ["foundation-gate-ref:latest-report"],
        redaction_status: "safe_refs_only",
        stale_state: "recheck_foundation_gate_report_before_release_claim",
        missing_evidence_posture:
          "release_evidence_packet_missing_until_scoped_release",
        blocked_states: [
          "foundation_gate_refs_not_production_authority",
          "latency_refs_not_authority",
          "no_release_authority",
        ],
        next_safe_action:
          "Inspect Foundation Gate and latency refs; keep production claims blocked until release evidence is scoped.",
      },
    ],
    evidence_timeline_route_ref: "/evidence",
    evidence_timeline_backend_route_ref: "GET /control-center/today/summary",
    evidence_timeline_status: "storage_backed_redacted_refs",
    evidence_timeline_authority_boundary:
      "Evidence Timeline is safe-ref and redacted-summary only. It does not expose private content, grant approval, perform rollback, or confer production authority.",
    evidence_timeline_blocked_states: [
      "no_raw_evidence_display",
      "no_rollback_execution",
      "approval_refs_are_identifiers_only",
      "foundation_gate_refs_not_production_authority",
      "latency_refs_not_authority",
      "connector_source_runtime_blocked",
    ],
    evidence_refs: ["evidence-ref:founder-loop:test-today"],
    blocked_states: ["no_action_execution_route"],
  },
  founderActionsInbox: {
    schema_version: "founder_loop_storage.v1",
    status: "storage_backed_review_queue",
    surface: "Actions",
    storage_ref: "founder-loop-storage:test",
    side_effect_class: "local_dev_workspace_only",
    route_ref: "/control-center/actions/inbox",
    read_only_route_refs: [
      "GET /control-center/actions/inbox",
      "GET /control-center/storage/status",
      "GET /control-center/routes",
      "GET /control-center/runtime-readiness/summary",
      "GET /control-center/foundation-gate/summary",
    ],
    local_prerequisite_refs: [
      "status-ref:founder-loop-storage",
      "status-ref:control-center-route-manifest",
      "capability-ref:local-approval-authority",
    ],
    items: [
      {
        item_ref: "founder-action:test",
        title: "Storage-backed action",
        safe_summary: "Bounded action summary.",
        surface: "Actions",
        priority: "high",
        risk_class: "high",
        status: "review_ready",
        side_effect_class: "validation_only",
        authority_boundary:
          "Review-only display; Python Agent Core and LocalApprovalAuthority must validate exact scope before mutation.",
        approval_required: true,
        approval_envelope_ref: "approval-envelope:founder-loop:test",
        approval_envelope_status: "dry_run_ref_available",
        state_change_contract_ref: "contract-ref:founder-loop:test",
        state_change_readiness: "blocked_pending_scoped_mutation_contract",
        blocked_state: "Scoped backend contract required",
        evidence_refs: ["evidence-ref:founder-loop:test-action"],
        receipt_refs: ["receipt-plan:founder-loop:test"],
        audit_refs: ["audit-plan:founder-loop:test"],
        idempotency_key_ref: "idempotency-ref:founder-loop:test",
        expires_at: "review_required_before_mutation",
        stale_state: "recheck_action_summary_before_mutation",
        rollback_ref: "rollback-plan:founder-loop:test",
        safe_disable_ref: "safe-disable:founder-loop:test",
        next_safe_action:
          "Review refs only; request a scoped state-change milestone before mutation.",
      },
    ],
    approval_required_before_mutation: true,
    mutating_controls_enabled: false,
    disabled_state_label: "Exact backend approval contract required",
    evidence_refs: ["evidence-ref:founder-loop:test-inbox"],
    blocked_states: [
      "no_action_execution_route",
      "no_approval_grant_capture_route",
      "no_state_change_contract_route",
    ],
  },
  founderMorningBriefing: {
    schema_version: "founder_loop_storage.v1",
    status: "storage_backed_briefing_skeleton",
    surface: "Morning Briefing",
    storage_ref: "founder-loop-storage:test",
    side_effect_class: "local_dev_workspace_only",
    route_ref: "/control-center/morning-briefing/summary",
    read_only_route_refs: [
      "GET /control-center/morning-briefing/summary",
      "GET /control-center/storage/status",
      "GET /control-center/routes",
      "GET /control-center/runtime-readiness/summary",
      "GET /control-center/foundation-gate/summary",
    ],
    local_prerequisite_refs: [
      "status-ref:founder-loop-storage",
      "status-ref:control-center-route-manifest",
      "contract-ref:email-read-only-missing",
      "contract-ref:calendar-read-only-missing",
      "contract-ref:notification-delivery-missing",
    ],
    source_readiness: "blocked_missing_email_calendar_notification_contracts",
    authority_boundary:
      "Read-only briefing summary; no email, calendar, connector, refresh, notification, model, memory, or delivery authority.",
    bounded_preview_only: true,
    refresh_enabled: false,
    notification_delivery_enabled: false,
    missing_contract_refs: [
      "contract-ref:email-read-only-missing",
      "contract-ref:calendar-read-only-missing",
      "contract-ref:notification-delivery-missing",
    ],
    items: [
      {
        briefing_ref: "briefing:test",
        title: "Briefing item",
        safe_summary: "Bounded briefing summary.",
        priority: "high",
        status: "active",
        side_effect_class: "local_dev_workspace_only",
        authority_boundary:
          "Review-only briefing summary; source reads and delivery remain unscoped.",
        source_readiness: "local_status_refs_only",
        source_refs: ["source-ref:control-center-route-status"],
        missing_contract_refs: [
          "contract-ref:email-read-only-missing",
          "contract-ref:calendar-read-only-missing",
          "contract-ref:notification-delivery-missing",
        ],
        blocked_states: [
          "no_email_calendar_source_contract",
          "no_background_refresh",
        ],
        stale_state: "recheck_route_status_before_briefing_use",
        evidence_gap: "No email, calendar, or notification source evidence is bound.",
        next_safe_action:
          "Use route and storage refs only; define source contracts before refresh.",
        evidence_refs: ["evidence-ref:founder-loop:test-briefing"],
      },
    ],
    evidence_refs: ["evidence-ref:founder-loop:test-briefing"],
    blocked_states: [
      "no_email_read_authority",
      "no_calendar_read_authority",
      "no_connector_runtime",
      "no_background_refresh",
      "no_notification_delivery",
    ],
  },
  founderStorageStatus: {
    schema_version: "founder_loop_storage.v1",
    migration_version: "founder_loop_storage.v1",
    storage_ref: "founder-loop-storage:test",
    sqlite_state_ref: "founder-loop-sqlite:test",
    jsonl_log_refs: {
      audit: "founder-loop-log:audit",
      transcript: "founder-loop-log:transcript",
      realtime: "founder-loop-log:realtime",
      receipt: "founder-loop-log:receipt",
    },
    counts: {
      action_inbox: 1,
      briefing_items: 1,
      plan_summaries: 1,
      memory_review_queue: 1,
      idempotency_keys: 0,
      route_state_snapshots: 0,
      evidence_refs: 1,
    },
    safe_refs_only: true,
    raw_content_stored: false,
    postgres_sync_required: false,
    postgres_sync_status: "adapter_boundary_only",
    backup_manifest_ref: "backup-manifest:founder-loop-minimum-set",
    backup_manifest: {
      schema_version: "founder_loop_storage.v1",
      manifest_ref: "backup-manifest:founder-loop-minimum-set",
      required_artifact_refs: ["founder-loop-sqlite:test"],
      raw_paths_included: false,
      raw_logs_included: false,
      safe_refs_only: true,
    },
    updated_at: "2026-01-01T00:00:00Z",
  },
};
