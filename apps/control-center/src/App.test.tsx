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
        "Trial Packet",
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
    expect(screen.getByRole("heading", { name: /Product spine contract/i })).toBeInTheDocument();
    expect(screen.getByText("contract-ref:today-product-spine:v1")).toBeInTheDocument();
    expect(screen.getByText("Loop visibility sufficient").nextElementSibling).toHaveTextContent("no");
    expect(screen.getByText("Standalone completion").nextElementSibling).toHaveTextContent("blocked");
    expect(screen.getByRole("heading", { name: /Today required signals/i })).toBeInTheDocument();
    expect(screen.getByText("priorities")).toBeInTheDocument();
    expect(screen.getByText("stale_source_posture")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Plan\/action state/i })).toBeInTheDocument();
    expect(
      screen.getAllByText("implemented_reviewable_action_envelopes_execution_blocked").length,
    ).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /Memory-to-loop binding/i })).toBeInTheDocument();
    expect(screen.getAllByText("contract-ref:memory-to-loop-binding:v1").length).toBeGreaterThan(0);
    expect(screen.getByText("Loop items").nextElementSibling).toHaveTextContent("4");
    expect(screen.getByText("Memory-derived actions").nextElementSibling).toHaveTextContent("1");
    expect(screen.getByText("Accepted recall").nextElementSibling).toHaveTextContent("display-only");
    expect(screen.getByRole("heading", { name: /Private beta-readiness gate/i })).toBeInTheDocument();
    expect(screen.getAllByText("contract-ref:private-beta-readiness-gate:v1").length).toBeGreaterThan(0);
    expect(screen.getByText("Evidence packet").nextElementSibling).toHaveTextContent(
      "evidence-packet:private-beta-readiness:local-founder-loop",
    );
    expect(screen.getByText("Public beta").nextElementSibling).toHaveTextContent("blocked");
    expect(screen.getByRole("heading", { name: /Beta-test criteria/i })).toBeInTheDocument();
    expect(screen.getByText(/CRM-Lite Follow-Ups: blocked/i)).toBeInTheDocument();
    expect(screen.getAllByText("blocked-state:no-public-beta").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /User intent understanding/i })).toBeInTheDocument();
    expect(screen.getAllByText("contract-ref:user-intent-understanding:v1").length).toBeGreaterThan(0);
    expect(screen.getByText("Low confidence").nextElementSibling).toHaveTextContent("asks user");
    expect(screen.getByText("Hidden authority").nextElementSibling).toHaveTextContent("blocked");
    expect(screen.getByText(/clarify_chat_to_plan_handoff: low confidence/i)).toBeInTheDocument();
    expect(screen.getByText(/resolve_conflicting_crm_follow_up: conflicting confidence/i)).toBeInTheDocument();
    expect(screen.getAllByText("blocked-state:no-hidden-intent-authority").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /Weekly CEO Review/i })).toBeInTheDocument();
    expect(
      screen.getAllByText("weekly-review-ref:memory-to-loop-binding").length,
    ).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /Memory loop states/i })).toBeInTheDocument();
    expect(screen.getByText(/Action Inbox: follow_up_commitment/i)).toBeInTheDocument();
    expect(
      screen.getAllByText("accepted-recall-ref:not-authorized:memory-review-founder-loop-preferences").length,
    ).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /Action envelope contract/i })).toBeInTheDocument();
    expect(screen.getAllByText("contract-ref:plans-action-envelope:v1").length).toBeGreaterThan(0);
    expect(screen.getAllByText("blocked-state:no-action-execution").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /Module feed contract/i })).toBeInTheDocument();
    expect(screen.getByText(/Chat: implemented_local_operator_surface_contract/i)).toBeInTheDocument();
    expect(screen.getByText(/Code: implemented_governed_code_workbench_contract_apply_blocked/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Stale-source posture/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /approve|run|send|write|sync|execute/i })).not.toBeInTheDocument();
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
      ["/private-trial", /Private Operator Trial/i],
      ["/setup", /macOS Setup Assistant/i],
      ["/dashboard", /Dashboard overview/i],
      ["/operator-loop", /Operator Loop/i],
      ["/differentiators", /Control Center Differentiators/i],
      ["/chat", /^Chat Local Operator$/i],
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

  it("renders API route classification posture", async () => {
    window.history.pushState({}, "", "/api-routes");
    render(<App />);

    expect(await screen.findByText("API Routes")).toBeInTheDocument();
    expect(screen.getByText("Classification")).toBeInTheDocument();
    expect(screen.getAllByText(/local_readonly/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Classification is posture evidence only/i),
    ).toBeInTheDocument();
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

  it("renders Private Trial packet as local safe refs without full beta claims", async () => {
    mockFetchWithFallback();
    window.history.pushState({}, "", "/private-trial");
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /Private Operator Trial/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("local/private only")).toBeInTheDocument();
    expect(screen.getByText("milestone:uaa-p1-087.2a")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Full UAA-P1-087.2 still needs accepted or revised local\/private findings later/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("contract-ref:private-operator-ui-functional-tuning:v1"),
    ).toBeInTheDocument();
    expect(screen.getByText("milestone:uaa-p1-087.2b")).toBeInTheDocument();
    expect(
      screen.getAllByText("ledger-ref:private-operator-trial-acceptance:v1").length,
    ).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /Acceptance ledger/i })).toBeInTheDocument();
    expect(screen.getByText("operator_review_ready")).toBeInTheDocument();
    expect(screen.getByText("manual-smoke-step:private-trial:boot-control-center")).toBeInTheDocument();
    expect(screen.getByText("acceptance-question:private-trial:memory-confidence")).toBeInTheDocument();
    expect(screen.getByText("tuning-decision:private-trial:pending-memory-review-emphasis")).toBeInTheDocument();
    expect(
      screen.getByText("finding-ref:private-trial:pending:crm-lite-follow-ups"),
    ).toBeInTheDocument();
    expect(screen.getByText("milestone:uaa-p1-087.2c")).toBeInTheDocument();
    expect(
      screen.getByText("scaffold-ref:private-operator-trial-manual-review:v1"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("manual_review_deferred_pending_implementation"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("unanswered_pending_manual_review").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("pending-answer:private-trial:crm-lite-follow-ups"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "missing-implementation:founder-loop:action-decision-receipts",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("launcher-command:uaa-trial-boot")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Authority boundary/i })).toBeInTheDocument();
    expect(screen.getByText("blocked-state:no-public-beta")).toBeInTheDocument();
    expect(screen.getByText("blocked-state:no-production-authority")).toBeInTheDocument();
    expect(screen.getByText("blocked-state:openwebui-secondary-only")).toBeInTheDocument();
    expect(screen.getByText("private-trial-check:local-boot")).toBeInTheDocument();
    expect(screen.getByText("private-trial-check:crm-lite-follow-ups")).toBeInTheDocument();
    expect(screen.getAllByText("friction-ref:private-trial:blocked-state-language").length).toBeGreaterThan(0);
    expect(screen.getByText("gap-ref:private-trial:crm-lite-local-follow-up-store")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /approve|run|send|write|sync|execute/i }),
    ).not.toBeInTheDocument();
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
    expect(
      screen.getAllByText("receipt-plan:founder-loop:mock-setup-hardening").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("audit-plan:founder-loop:mock-setup-hardening")).toBeInTheDocument();
    expect(screen.getByText("idempotency-ref:founder-loop:mock-setup-hardening")).toBeInTheDocument();
    expect(screen.getByText("rollback-plan:founder-loop:mock-setup-hardening")).toBeInTheDocument();
    expect(screen.getByText("safe-disable:founder-loop:mock-setup-hardening")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Action envelope contract/i })).toBeInTheDocument();
    expect(screen.getAllByText("contract-ref:plans-action-envelope:v1").length).toBeGreaterThan(0);
    expect(screen.getAllByText("action-envelope:plans:founder-action-mock-setup-hardening").length).toBeGreaterThan(0);
    expect(screen.getAllByText("scope-ref:plans-action-envelope:founder-action-mock-setup-hardening").length).toBeGreaterThan(0);
    expect(screen.getAllByText("blocked-state:no-approval-grant-capture").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /Memory-derived proposals/i })).toBeInTheDocument();
    expect(
      screen.getAllByText("memory-derived-action-proposal:memory-review-founder-loop-preferences").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("memory-loop-binding:today:business-memory-candidate-preference-memory-review-founder-loop-preferences").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("approval_required_before_any_memory_derived_action").length).toBeGreaterThan(0);
    expect(screen.getAllByText("blocked-state:no-memory-write").length).toBeGreaterThan(0);
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
        heading: /^Chat Local Operator$/,
        stateHeading: /Chat Local Operator states/i,
        blocked: /Blocked: local chat authority withheld/i,
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
        heading: /^Chat Local Operator$/,
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
      if (check.path === "/chat") {
        expect(
          screen.getAllByText("contract-ref:chat-local-operator-surface:v1").length,
        ).toBeGreaterThan(0);
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
    expect(
      screen.getByText("storage_backed_redacted_history_grammar_refs"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("GET /control-center/today/summary").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("Evidence history grammar")).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:evidence-history-grammar:v1").length,
    ).toBeGreaterThan(0);
    for (const question of [
      "What was proposed?",
      "What was approved?",
      "What happened?",
      "What changed?",
      "What can be undone?",
      "What is stale?",
      "What remains blocked?",
    ]) {
      expect(screen.getAllByText(question).length).toBeGreaterThan(0);
    }
    expect(screen.getAllByText(/Approval ref authority/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Rollback execution/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Memory truth authority/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Raw evidence included/i).length).toBeGreaterThan(0);
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
      "plan_action_envelope_ref",
      "memory_review_evidence_ref",
      "source_readiness_evidence_ref",
      "foundation_gate_latency_ref",
      "receipt-plan:founder-loop:mock-setup-hardening",
      "audit-plan:founder-loop:mock-setup-hardening",
      "replay-ref:founder-loop:action-inbox",
      "rollback-plan:founder-loop:mock-setup-hardening",
      "receipt-plan:plans-action-envelope:plan-summary-founder-loop-v1",
      "rollback-plan:plans-action-envelope:plan-summary-founder-loop-v1",
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
    expect(
      screen.getByText(
        "storage_backed_review_queue_with_business_quality_and_loop_binding_metadata",
      ),
    ).toBeInTheDocument();
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
      screen.getAllByText("Context injection")[0].nextElementSibling,
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
    expect(screen.getAllByText("preference").length).toBeGreaterThan(0);
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
      screen.getByText("provenance-ref:manual-note:mock-preferences"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("source-ref:manual-note:founder-loop-storage").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("contract-ref:memory-write-policy-binding-missing").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("contract-ref:memory-retention-delete-missing").length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByText("contract-ref:business-memory-quality-controls-missing"),
    ).not.toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:context-injection-missing").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("no_memory_write").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_context_injection").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_memory_delete").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_memory_export").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_raw_source_display").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_external_crm_write").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_account_sync").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_automatic_recall").length).toBeGreaterThan(0);
    expect(screen.getAllByText("no_connector_write").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("no_model_provider_authority").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("no_background_sync").length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Review provenance and evidence refs/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Review decisions/i })).toBeInTheDocument();
    expect(screen.getAllByText("contract-ref:memory-review-decision:v1").length).toBeGreaterThan(0);
    expect(screen.getAllByText("review_needed_no_decision_captured").length).toBeGreaterThan(0);
    expect(screen.getAllByText("actor-ref:local-operator-review-required").length).toBeGreaterThan(0);
    expect(screen.getAllByText("blocked-state:no-memory-write").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /Business memory/i })).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:business-memory-quality-controls:v1").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("business-memory-quality:blocked").length).toBeGreaterThan(0);
    expect(screen.getAllByText("business-memory-quality:low-confidence").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("business-memory-candidate:preference:memory-review-founder-loop-preferences").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("manual_note").length).toBeGreaterThan(0);
    expect(screen.getAllByText("untrusted_until_reviewed").length).toBeGreaterThan(0);
    expect(screen.getAllByText("redacted_summary_only").length).toBeGreaterThan(0);
    expect(screen.getAllByText("blocked-state:no-external-crm-write").length).toBeGreaterThan(0);
    expect(screen.getAllByText("blocked-state:no-account-sync").length).toBeGreaterThan(0);
    expect(screen.getAllByText("blocked-state:no-connector-runtime").length).toBeGreaterThan(0);
    expect(screen.getAllByText("blocked-state:no-model-provider-authority").length).toBeGreaterThan(0);
    expect(screen.getAllByText("weekly-review-ref:business-memory-carry-forward").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /Memory intake/i })).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:cross-surface-memory-intake:v1").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("memory-intake-proposal:local-coding").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("memory-intake-proposal:external-assistant-review").length,
    ).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /Memory-to-loop/i })).toBeInTheDocument();
    expect(
      screen.getAllByText("contract-ref:memory-to-loop-binding:v1").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("memory-loop-binding:today:business-memory-candidate-preference-memory-review-founder-loop-preferences").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("follow-up-commitment-ref:memory-review-founder-loop-preferences").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("memory-derived-action-proposal:memory-review-founder-loop-preferences").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("Local Coding").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("External Assistant Review").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("missing_safe_evidence_until_reviewed").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("recheck_source_refs_before_memory_intake").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("blocked-state:no-shell-history-import").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("blocked-state:no-raw-file-import").length,
    ).toBeGreaterThan(0);

    for (const label of [
      /^accept$/i,
      /^correct$/i,
      /^reject$/i,
      /^retain$/i,
      /^delete$/i,
      /^write$/i,
      /^inject$/i,
      /^approve$/i,
      /^merge$/i,
      /^supersede$/i,
      /^defer$/i,
      /^run$/i,
      /^sync$/i,
      /^crm sync$/i,
      /^dedupe$/i,
      /^resolve conflict$/i,
      /^mark reviewed$/i,
      /^promote to recall$/i,
      /^accept recall$/i,
      /^bind memory$/i,
      /^create follow-up$/i,
      /^create action$/i,
      /^use in context$/i,
      /^inject context$/i,
      /^resolve blocker$/i,
      /^mark accepted$/i,
      /^import$/i,
      /^quality control$/i,
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
    [API_ENDPOINTS.founderTodaySummary]: mockControlCenterData.founderToday,
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
        route_classification: "local_readonly",
        protected_route: true,
        classification_reason:
          "local read-only route inventory or status surface; protected in production posture",
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
    product_spine_contract_ref: "contract-ref:today-product-spine:v1",
    required_loop_surfaces: ["Today", "Actions", "Evidence", "Memory"],
    required_today_signals: [
      {
        signal: "priorities",
        source: "action_and_briefing_priority_fields",
        required: true,
      },
      {
        signal: "blockers",
        source: "blocked_states_and_missing_contract_refs",
        required: true,
      },
      {
        signal: "follow_ups",
        source: "next_safe_action_fields",
        required: true,
      },
      {
        signal: "plan_action_state",
        source: "plans_actions_and_approval_posture",
        required: true,
      },
      {
        signal: "memory_review_count",
        source: "sections.memory_review_count",
        required: true,
      },
      {
        signal: "stale_source_posture",
        source: "stale_state_fields",
        required: true,
      },
      {
        signal: "next_safe_actions",
        source: "next_safe_actions",
        required: true,
      },
    ],
    module_feed_contract: [
      {
        module: "Today",
        status: "implemented_storage_backed_partial_loop",
        required_loop_outputs: ["today_state", "action_state", "evidence_state", "memory_state"],
        current_feed_refs: [
          "GET /control-center/today/summary",
          "evidence-ref:founder-loop:today-summary",
        ],
        standalone_complete_allowed: false,
      },
      {
        module: "Actions",
        status: "implemented_review_queue_execution_blocked",
        required_loop_outputs: [
          "today_priority_or_blocker",
          "action_envelope_or_blocked_state",
          "evidence_ref",
          "memory_review_or_blocked_state",
        ],
        current_feed_refs: [
          "GET /control-center/actions/inbox",
          "evidence-ref:founder-loop:action-inbox",
        ],
        standalone_complete_allowed: false,
      },
      {
        module: "Plans",
        status: "implemented_reviewable_action_envelope_contract",
        required_loop_outputs: [
          "today_plan_state",
          "action_envelope_or_blocked_state",
          "plan_evidence_ref",
          "memory_candidate_or_blocked_state",
        ],
        current_feed_refs: [
          "status-ref:founder-loop-plan-summary",
          "contract-ref:plans-action-envelope:v1",
        ],
        standalone_complete_allowed: false,
      },
      {
        module: "Memory",
        status: "implemented_review_queue_quality_intake_and_loop_binding_contract",
        required_loop_outputs: [
          "today_memory_review_count",
          "action_or_follow_up_candidate",
          "memory_evidence_ref",
          "reviewed_recall_or_blocked_state",
        ],
        current_feed_refs: [
          "status-ref:founder-loop-memory-review",
          "contract-ref:memory-review-decision:v1",
          "contract-ref:business-memory-quality-controls:v1",
          "contract-ref:cross-surface-memory-intake:v1",
          "contract-ref:memory-to-loop-binding:v1",
        ],
        standalone_complete_allowed: false,
      },
      {
        module: "Evidence",
        status: "implemented_redacted_history_grammar_contract_partial",
        required_loop_outputs: [
          "today_evidence_state",
          "action_receipt_or_blocked_state",
          "evidence_timeline_ref",
          "memory_evidence_or_blocked_state",
        ],
        current_feed_refs: [
          "GET /control-center/today/summary",
          "contract-ref:evidence-history-grammar:v1",
        ],
        standalone_complete_allowed: false,
      },
      {
        module: "Morning Briefing",
        status: "implemented_skeleton_source_contracts_missing",
        required_loop_outputs: [
          "today_priority_or_blocker",
          "follow_up_or_action_candidate",
          "source_readiness_evidence_ref",
          "memory_candidate_or_blocked_state",
        ],
        current_feed_refs: [
          "GET /control-center/morning-briefing/summary",
          "contract-ref:calendar-read-only-missing",
        ],
        standalone_complete_allowed: false,
      },
      {
        module: "Chat",
        status: "implemented_local_operator_surface_contract",
        required_loop_outputs: [
          "today_chat_state",
          "plan_or_action_handoff_state",
          "chat_evidence_ref",
          "memory_candidate_or_blocked_state",
        ],
        current_feed_refs: [
          "contract-ref:chat-local-operator-surface:v1",
          "/v1/chat/completions",
        ],
        standalone_complete_allowed: false,
      },
      {
        module: "Code",
        status: "implemented_governed_code_workbench_contract_apply_blocked",
        required_loop_outputs: [
          "today_code_state",
          "action_or_apply_blocked_state",
          "diff_validation_evidence_ref",
          "memory_candidate_or_blocked_state",
        ],
        current_feed_refs: ["contract-ref:governed-code-workbench:v1"],
        standalone_complete_allowed: false,
      },
    ],
    module_completion_contract: {
      visibility_requirement:
        "Module state must be visible in Today, Actions, Evidence, and Memory before completion can be claimed.",
      visibility_is_sufficient_for_completion: false,
      standalone_module_complete_allowed: false,
      required_done_gates: [
        "definition_of_done",
        "schema_or_typed_contract",
        "focused_tests",
        "redaction_checks",
        "policy_approval_boundary",
        "openapi_api_manifest_when_routes_change",
        "cli_or_repo_local_inspection_path",
      ],
    },
    business_memory_quality_contract_ref:
      "contract-ref:business-memory-quality-controls:v1",
    business_memory_candidate_kinds: [
      "profile",
      "project",
      "relationship",
      "organization",
      "deal",
      "opportunity",
      "promise",
      "follow_up",
      "preference",
      "decision",
      "commitment",
    ].map((candidateKind) => ({
      candidate_kind: candidateKind,
      candidate_kind_ref: `business-memory-kind:${candidateKind.replaceAll("_", "-")}`,
      review_required: true,
      safe_summary_only: true,
      source_refs_required: true,
      provenance_refs_required: true,
      evidence_refs_required: true,
      quality_posture_required: true,
      correction_path_required: true,
      retention_delete_export_posture_required: true,
      crm_write_authorized: false,
      account_sync_authorized: false,
      context_injection_authorized: false,
      accepted_as_recall: false,
    })),
    business_memory_quality_states: [
      "duplicate",
      "conflict",
      "stale_expired",
      "low_confidence",
      "source_missing",
      "evidence_missing",
      "blocked",
      "reviewed",
    ].map((qualityState) => ({
      quality_state: qualityState,
      quality_state_ref: `business-memory-quality:${qualityState.replaceAll("_", "-")}`,
      blocks_unreviewed_recall: true,
      requires_operator_review: true,
      requires_safe_refs: true,
      requires_correction_path: [
        "duplicate",
        "conflict",
        "stale_expired",
        "low_confidence",
      ].includes(qualityState),
      is_blocking_posture: qualityState !== "reviewed",
      authorizes_memory_write: false,
      authorizes_crm_write: false,
      authorizes_context_injection: false,
    })),
    business_memory_required_ref_fields: [
      "review_ref",
      "candidate_ref",
      "source_refs",
      "provenance_refs",
      "evidence_refs",
      "quality_state_refs",
      "related_entity_refs",
      "blocker_refs",
    ],
    business_memory_surface_bindings: [
      {
        surface: "Today",
        feed_status: "implemented_safe_ref_quality_summary",
        feed_ref: "today-ref:memory-review-business-quality",
        authority_boundary:
          "Quality posture can create blockers and follow-up refs only.",
      },
      {
        surface: "Action Inbox",
        feed_status: "implemented_follow_up_candidate_refs_only",
        feed_ref: "action-inbox-ref:memory-follow-up-candidates",
        authority_boundary:
          "Promises and follow-ups are review candidates, not execution tasks.",
      },
      {
        surface: "Evidence Timeline",
        feed_status: "implemented_history_refs_only",
        feed_ref: "evidence-ref:memory-business-quality-history",
        authority_boundary:
          "Quality changes must read as history with safe refs only.",
      },
      {
        surface: "Weekly CEO Review",
        feed_status: "implemented_carry_forward_refs_only",
        feed_ref: "weekly-review-ref:business-memory-carry-forward",
        authority_boundary:
          "Weekly review can carry decisions and blockers, not sync accounts.",
      },
    ],
    business_memory_authority_posture: {
      safe_refs_only: true,
      review_required_before_recall: true,
      memory_write_authorized: false,
      memory_delete_authorized: false,
      memory_export_authorized: false,
      automatic_memory_write_authorized: false,
      context_injection_authorized: false,
      external_crm_write_authorized: false,
      account_sync_authorized: false,
      connector_runtime_enabled: false,
      account_auth_enabled: false,
      provider_or_model_authority_allowed: false,
      source_truth_authority: false,
      accepted_as_recall: false,
      public_beta_claim_enabled: false,
      public_distribution_claim_enabled: false,
      production_authority_enabled: false,
    },
    business_memory_status:
      "implemented_review_queue_safe_ref_quality_metadata_contract",
    chat_local_operator_contract_ref:
      "contract-ref:chat-local-operator-surface:v1",
    chat_local_operator_status: "implemented_local_turn_truth_surface",
    chat_local_operator_turn_ref: "chat-turn:local-operator:local-chat-gateway",
    chat_local_operator_route_ref: "/v1/chat/completions",
    chat_local_operator_model_ref: "model-ref:local-chat-gateway",
    chat_local_operator_runtime_truth: "runtime-readiness-gated",
    chat_local_operator_auth_truth: "local-bearer-required",
    chat_local_operator_tool_denial_truth: "tools-functions-streaming-denied",
    chat_local_operator_tool_denial_ref:
      "tool-denial-ref:chat-local-operator:local-chat-gateway",
    chat_local_operator_safe_evidence_refs: [
      "evidence-ref:chat-local-operator:today",
    ],
    chat_local_operator_plans_handoff_ref:
      "handoff-ref:chat-to-plans:local-chat-gateway",
    chat_local_operator_actions_handoff_ref:
      "handoff-ref:chat-to-actions:local-chat-gateway",
    chat_local_operator_required_truth_fields: [
      "turn_ref",
      "route_ref",
      "model_ref",
      "runtime_truth",
      "auth_truth",
      "tool_denial_truth",
      "safe_evidence_refs",
      "plans_handoff_ref",
      "actions_handoff_ref",
      "blocked_state_refs",
    ],
    chat_local_operator_required_blocked_refs: [
      "blocked-state:no-model-output-authority",
      "blocked-state:no-tool-execution",
      "blocked-state:no-memory-write",
      "blocked-state:no-context-injection",
      "blocked-state:no-provider-sdk-call",
      "blocked-state:no-web-fetch",
      "blocked-state:no-connector-write",
      "blocked-state:no-shell-subprocess-execution",
      "blocked-state:no-action-execution",
      "blocked-state:no-approval-grant-capture",
      "blocked-state:no-production-authority",
    ],
    chat_local_operator_surface_bindings: [
      {
        surface: "Today",
        feed_status: "implemented_local_operator_turn_truth_refs",
        feed_ref: "contract-ref:chat-local-operator-surface:v1",
        authority_boundary: "Chat state is safe operator-turn metadata only.",
      },
    ],
    chat_local_operator_authority_posture: {
      safe_refs_only: true,
      response_visible: false,
      prompt_body_visible: false,
      completion_body_visible: false,
      model_output_authority: false,
      tool_execution_enabled: false,
      memory_write_authorized: false,
      context_injection_authorized: false,
      provider_sdk_call_enabled: false,
      web_fetch_enabled: false,
      connector_write_enabled: false,
      shell_subprocess_execution_enabled: false,
      action_execution_enabled: false,
      approval_grant_capture_enabled: false,
      production_authority_enabled: false,
    },
    chat_local_operator_blocked_state_refs: [
      "blocked-state:no-model-output-authority",
      "blocked-state:no-tool-execution",
      "blocked-state:no-memory-write",
      "blocked-state:no-context-injection",
      "blocked-state:no-provider-sdk-call",
      "blocked-state:no-web-fetch",
      "blocked-state:no-connector-write",
      "blocked-state:no-shell-subprocess-execution",
      "blocked-state:no-action-execution",
      "blocked-state:no-approval-grant-capture",
      "blocked-state:no-production-authority",
    ],
    governed_code_workbench_contract_ref:
      "contract-ref:governed-code-workbench:v1",
    governed_code_workbench_status:
      "implemented_reviewable_repo_local_diff_contract_apply_blocked",
    governed_code_workbench_proposal_ref:
      "code-proposal:founder-loop-safe-diff",
    governed_code_workbench_repo_scope_ref:
      "repo-scope:governed-code:code-proposal-founder-loop-safe-diff",
    governed_code_workbench_safe_diff_summary_ref:
      "diff-summary-ref:governed-code:code-proposal-founder-loop-safe-diff",
    governed_code_workbench_validation_plan_ref:
      "validation-plan-ref:governed-code:code-proposal-founder-loop-safe-diff",
    governed_code_workbench_validation_result_refs: [
      "validation-result-ref:governed-code:not-run",
    ],
    governed_code_workbench_approval_requirement_ref:
      "approval-requirement:governed-code:code-proposal-founder-loop-safe-diff",
    governed_code_workbench_expected_apply_receipt_ref:
      "receipt-plan:governed-code-apply:code-proposal-founder-loop-safe-diff",
    governed_code_workbench_expected_rollback_receipt_ref:
      "rollback-receipt-plan:governed-code:code-proposal-founder-loop-safe-diff",
    governed_code_workbench_evidence_refs: [
      "evidence-ref:governed-code:today",
    ],
    governed_code_workbench_idempotency_key_ref:
      "idempotency-ref:governed-code:code-proposal-founder-loop-safe-diff",
    governed_code_workbench_safe_summary:
      "Governed Code proposal records repo-local scope, safe diff summary, validation plan, approval requirement, expected apply receipt, and rollback receipt refs; apply remains blocked.",
    governed_code_workbench_validation_plan_summary:
      "Run focused tests and verifiers before any exact approval-bound apply.",
    governed_code_workbench_required_ref_fields: [
      "proposal_ref",
      "repo_scope_ref",
      "safe_diff_summary_ref",
      "validation_plan_ref",
      "validation_result_refs",
      "approval_requirement_ref",
      "expected_apply_receipt_ref",
      "expected_rollback_receipt_ref",
      "evidence_refs",
      "idempotency_key_ref",
      "blocked_state_refs",
    ],
    governed_code_workbench_required_blocked_refs: [
      "blocked-state:no-unapproved-mutation",
      "blocked-state:no-apply-execution",
      "blocked-state:no-approval-grant-capture",
      "blocked-state:no-unrestricted-shell",
      "blocked-state:no-shell-subprocess-execution",
      "blocked-state:no-remote-execution",
      "blocked-state:no-broad-coding-agent-autonomy",
      "blocked-state:no-provider-sdk-call",
      "blocked-state:no-web-fetch",
      "blocked-state:no-connector-write",
      "blocked-state:no-diff-body-storage",
      "blocked-state:no-production-authority",
    ],
    governed_code_workbench_surface_bindings: [
      {
        surface: "Today",
        feed_status: "implemented_governed_code_proposal_refs",
        feed_ref: "contract-ref:governed-code-workbench:v1",
        authority_boundary: "Code state is safe proposal metadata only.",
      },
    ],
    governed_code_workbench_authority_posture: {
      safe_refs_only: true,
      repo_local_scope_required: true,
      safe_diff_summary_only: true,
      validation_required_before_apply: true,
      approval_required_before_apply: true,
      atomic_apply_required: true,
      rollback_receipt_required: true,
      audit_required: true,
      redaction_required: true,
      apply_execution_enabled: false,
      approval_grant_capture_enabled: false,
      direct_file_write_enabled: false,
      unrestricted_shell_enabled: false,
      shell_subprocess_execution_enabled: false,
      remote_execution_enabled: false,
      broad_coding_agent_autonomy_enabled: false,
      provider_sdk_call_enabled: false,
      web_fetch_enabled: false,
      connector_write_enabled: false,
      diff_body_storage_enabled: false,
      production_authority_enabled: false,
    },
    governed_code_workbench_blocked_state_refs: [
      "blocked-state:no-unapproved-mutation",
      "blocked-state:no-apply-execution",
      "blocked-state:no-approval-grant-capture",
      "blocked-state:no-unrestricted-shell",
      "blocked-state:no-shell-subprocess-execution",
      "blocked-state:no-remote-execution",
      "blocked-state:no-broad-coding-agent-autonomy",
      "blocked-state:no-provider-sdk-call",
      "blocked-state:no-web-fetch",
      "blocked-state:no-connector-write",
      "blocked-state:no-diff-body-storage",
      "blocked-state:no-production-authority",
    ],
    plans_action_envelope_contract_ref:
      "contract-ref:plans-action-envelope:v1",
    plans_action_envelope_review_postures: [
      "approve",
      "edit",
      "reject",
      "defer",
    ].map((reviewAction) => ({
      review_action: reviewAction,
      review_posture_ref: `review-posture:plans-action-envelope:${reviewAction}`,
      exact_scope_required: true,
      safe_refs_required: true,
      receipt_refs_required: true,
      grants_execution_authority: false,
      captures_approval_grant: false,
    })),
    plans_action_envelope_required_ref_fields: [
      "action_envelope_ref",
      "source_plan_ref",
      "scope_ref",
      "side_effect_class",
      "risk_class",
      "approval_requirement_ref",
      "review_posture_refs",
      "evidence_refs",
      "expected_receipt_refs",
      "idempotency_key_ref",
      "expires_at",
      "rollback_ref",
      "safe_disable_ref",
      "blocked_state_refs",
    ],
    plans_action_envelope_required_blocked_refs: [
      "blocked-state:no-action-execution",
      "blocked-state:no-approval-grant-capture",
      "blocked-state:approval-refs-identifiers-only",
      "blocked-state:no-connector-write",
      "blocked-state:no-shell-subprocess-execution",
      "blocked-state:no-model-provider-authority",
      "blocked-state:no-public-beta-or-distribution",
      "blocked-state:no-production-authority",
    ],
    plans_action_envelope_surface_bindings: [
      {
        surface: "Today",
        feed_status: "implemented_plan_action_state_contract",
        feed_ref: "today-ref:plans-action-envelope-state",
        authority_boundary:
          "Today can show envelope posture but cannot execute actions.",
      },
    ],
    plans_action_envelope_authority_posture: {
      safe_refs_only: true,
      exact_scope_required: true,
      approval_required_before_mutation: true,
      approval_ref_authority: false,
      approval_grant_capture_enabled: false,
      action_execution_enabled: false,
      state_change_enabled: false,
      connector_write_enabled: false,
      shell_subprocess_execution_enabled: false,
      model_provider_authority_allowed: false,
      memory_write_authorized: false,
      context_injection_authorized: false,
      public_beta_claim_enabled: false,
      public_distribution_claim_enabled: false,
      production_authority_enabled: false,
    },
    plans_action_envelope_status:
      "implemented_reviewable_action_envelopes_execution_blocked",
    priority_refs: [
      "priority-ref:action:high:founder-action-test",
      "priority-ref:briefing:medium:briefing-test",
    ],
    blocker_refs: [
      "blocked-state:no_action_execution_route",
      "blocked-state:no_connector_write_route",
      "blocked-state:no_runtime_model_call_route",
    ],
    follow_up_refs: [
      "follow-up-ref:actions:founder-action-test",
      "follow-up-ref:plans:plan-summary-test",
    ],
    plan_action_state: {
      action_count: 1,
      plan_count: 1,
      approval_required_before_mutation: true,
      mutating_controls_enabled: false,
      execution_authorized: false,
      action_envelope_contract_status:
        "implemented_reviewable_action_envelopes_execution_blocked",
      action_envelope_contract_ref: "contract-ref:plans-action-envelope:v1",
      review_actions: ["approve", "edit", "reject", "defer"],
      approval_grant_capture_enabled: false,
      state_change_enabled: false,
    },
    stale_source_posture: {
      status: "recheck_required_before_action_or_source_use",
      source_refresh_enabled: false,
      connector_runtime_enabled: false,
      stale_state_refs: [
        "stale-ref:action:founder-action-test",
        "stale-ref:memory:memory-review-test",
      ],
    },
    next_safe_actions: [
      {
        surface: "Actions",
        source_ref: "founder-action:test",
        safe_summary:
          "Review refs only; request a scoped state-change milestone before mutation.",
      },
      {
        surface: "Plans",
        source_ref: "plan-summary:test",
        safe_summary: "Review route-backed summaries.",
      },
    ],
    sections: {
      action_inbox_count: 1,
      plan_count: 1,
      memory_review_count: 1,
      briefing_count: 1,
      evidence_timeline_count: 8,
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
        action_envelope_contract_ref: "contract-ref:plans-action-envelope:v1",
        action_envelope_ref: "action-envelope:plans:founder-action-test",
        action_envelope_status: "review_ready_execution_blocked",
        action_envelope_safe_summary:
          "Action item is available as safe review metadata with exact-scope, receipt, idempotency, rollback, and safe-disable refs.",
        action_scope_ref: "scope-ref:plans-action-envelope:founder-action-test",
        action_approval_requirement_ref:
          "approval-requirement:plans-action-envelope:founder-action-test",
        action_review_actions: ["approve", "edit", "reject", "defer"],
        action_review_posture_refs: [
          "review-posture:plans-action-envelope:approve",
          "review-posture:plans-action-envelope:edit",
          "review-posture:plans-action-envelope:reject",
          "review-posture:plans-action-envelope:defer",
        ],
        action_expected_receipt_refs: ["receipt-plan:founder-loop:test"],
        action_idempotency_key_ref:
          "idempotency-ref:plans-action-envelope:founder-action-test",
        action_expires_at: "review_required_before_mutation",
        action_stale_state: "recheck_plan_and_action_refs_before_mutation",
        action_rollback_ref:
          "rollback-plan:plans-action-envelope:founder-action-test",
        action_safe_disable_ref:
          "safe-disable:plans-action-envelope:founder-action-test",
        action_blocked_state_refs: [
          "blocked-state:no-action-execution",
          "blocked-state:no-approval-grant-capture",
          "blocked-state:approval-refs-identifiers-only",
          "blocked-state:no-connector-write",
          "blocked-state:no-shell-subprocess-execution",
          "blocked-state:no-model-provider-authority",
          "blocked-state:no-public-beta-or-distribution",
          "blocked-state:no-production-authority",
        ],
        action_authority_boundary:
          "Reviewable Action envelope only; execution and approval grant capture remain blocked until exact scoped LocalApprovalAuthority validation exists.",
        action_exact_scope_required: true,
        action_envelope_approval_ref_authority: false,
        action_envelope_grant_capture_enabled: false,
        action_envelope_execution_enabled: false,
        action_envelope_connector_write_enabled: false,
        action_envelope_shell_execution_enabled: false,
        action_envelope_model_provider_authority_allowed: false,
        action_envelope_safe_refs_only: true,
        action_envelope_raw_content_included: false,
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
        action_envelope_contract_ref: "contract-ref:plans-action-envelope:v1",
        action_envelope_ref: "action-envelope:plans:plan-summary-test",
        action_envelope_status: "review_ready_execution_blocked",
        action_envelope_safe_summary:
          "Plan summary has a reviewable Action envelope with exact-scope, receipt, idempotency, rollback, and safe-disable refs; execution remains blocked.",
        scope_ref: "scope-ref:plans-action-envelope:plan-summary-test",
        side_effect_class: "validation_only",
        risk_class: "medium",
        approval_required: true,
        approval_requirement_ref:
          "approval-requirement:plans-action-envelope:plan-summary-test",
        review_actions: ["approve", "edit", "reject", "defer"],
        review_posture_refs: [
          "review-posture:plans-action-envelope:approve",
          "review-posture:plans-action-envelope:edit",
          "review-posture:plans-action-envelope:reject",
          "review-posture:plans-action-envelope:defer",
        ],
        expected_receipt_refs: [
          "receipt-plan:plans-action-envelope:plan-summary-test",
        ],
        idempotency_key_ref:
          "idempotency-ref:plans-action-envelope:plan-summary-test",
        expires_at: "review_required_before_mutation",
        stale_state: "recheck_plan_and_action_refs_before_mutation",
        rollback_ref: "rollback-plan:plans-action-envelope:plan-summary-test",
        safe_disable_ref: "safe-disable:plans-action-envelope:plan-summary-test",
        blocked_state_refs: [
          "blocked-state:no-action-execution",
          "blocked-state:no-approval-grant-capture",
          "blocked-state:approval-refs-identifiers-only",
          "blocked-state:no-connector-write",
          "blocked-state:no-shell-subprocess-execution",
          "blocked-state:no-model-provider-authority",
          "blocked-state:no-public-beta-or-distribution",
          "blocked-state:no-production-authority",
        ],
        authority_boundary:
          "Reviewable Action envelope only; execution and approval grant capture remain blocked until exact scoped LocalApprovalAuthority validation exists.",
        exact_scope_required: true,
        approval_ref_authority: false,
        approval_grant_capture_enabled: false,
        action_execution_enabled: false,
        connector_write_enabled: false,
        shell_subprocess_execution_enabled: false,
        model_provider_authority_allowed: false,
        safe_refs_only: true,
        raw_content_included: false,
        plan_action_envelope_ref: "action-envelope:plans:plan-summary-test",
        plan_action_scope_ref: "scope-ref:plans-action-envelope:plan-summary-test",
        plan_action_approval_requirement_ref:
          "approval-requirement:plans-action-envelope:plan-summary-test",
        plan_action_review_posture_refs: [
          "review-posture:plans-action-envelope:approve",
          "review-posture:plans-action-envelope:edit",
          "review-posture:plans-action-envelope:reject",
          "review-posture:plans-action-envelope:defer",
        ],
        plan_action_expected_receipt_refs: [
          "receipt-plan:plans-action-envelope:plan-summary-test",
        ],
        plan_action_blocked_state_refs: [
          "blocked-state:no-action-execution",
          "blocked-state:no-approval-grant-capture",
        ],
        plan_action_authority_boundary:
          "Reviewable Action envelope only; execution and approval grant capture remain blocked until exact scoped LocalApprovalAuthority validation exists.",
      },
    ],
    memory_review_queue: [
      {
        review_ref: "memory-review:test",
        title: "Memory review",
        safe_summary: "Bounded memory summary.",
        candidate_kind: "preference",
        priority: "high",
        status: "review_needed",
        review_state: "review_needed",
        side_effect_class: "local_dev_workspace_only",
        authority_boundary:
          "Review-only memory candidate; recall is not truth, and writes, deletes, and context injection remain unscoped.",
        provenance_refs: ["provenance-ref:manual-note:test"],
        source_refs: ["source-ref:manual-note:test"],
        missing_contract_refs: [
          "contract-ref:memory-write-policy-binding-missing",
          "contract-ref:memory-retention-delete-missing",
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
          "no_memory_export",
          "no_raw_source_display",
          "no_external_crm_write",
          "no_account_sync",
          "no_automatic_recall",
          "no_connector_write",
          "no_model_provider_authority",
          "no_background_sync",
        ],
        next_safe_action:
          "Review provenance and evidence refs; keep writes blocked until a scoped memory policy milestone.",
        evidence_refs: ["evidence-ref:founder-loop:test-memory"],
        source_policy_ref: "contract-ref:memory-source-provenance:v1",
        source_kind: "manual_note",
        source_kind_ref: "memory-source-kind:manual-note",
        source_refs_status: "safe_source_refs_present",
        provenance_refs_status: "safe_provenance_refs_present",
        source_review_required: true,
        source_trust_posture: "untrusted_until_reviewed",
        safe_summary_only: true,
        source_truth_authority: false,
        memory_write_authorized: false,
        automatic_memory_write_authorized: false,
        context_injection_authorized: false,
        account_auth_enabled: false,
        public_beta_claim_enabled: false,
        public_distribution_claim_enabled: false,
        production_authority_enabled: false,
        source_payload_storage_allowed: false,
        prompt_body_storage_allowed: false,
        response_body_storage_allowed: false,
        provider_body_storage_allowed: false,
        path_body_storage_allowed: false,
        log_body_storage_allowed: false,
        account_ref_storage_allowed: false,
        private_content_storage_allowed: false,
        connector_runtime_allowed: false,
        provider_or_model_authority_allowed: false,
        accepted_as_truth: false,
        decision_contract_ref: "contract-ref:memory-review-decision:v1",
        available_decision_states: [
          "accept",
          "correct",
          "reject",
          "defer",
          "merge",
          "supersede",
          "forget_request",
        ],
        decision_capture_status: "review_needed_no_decision_captured",
        decision_required_ref_fields: [
          "actor_ref",
          "source_refs",
          "provenance_refs",
          "evidence_refs",
          "stale_state",
          "retention_posture",
          "audit_refs",
          "receipt_refs",
          "blocked_state_refs",
        ],
        decision_actor_ref: "actor-ref:local-operator-review-required",
        decision_source_provenance_contract_ref:
          "contract-ref:memory-source-provenance:v1",
        decision_source_kind: "manual_note",
        decision_source_trust_posture: "untrusted_until_reviewed",
        decision_redaction_status: "redacted_summary_only",
        decision_audit_refs: ["audit-plan:memory-review:test"],
        decision_receipt_refs: ["receipt-plan:memory-review:test"],
        decision_blocked_state_refs: [
          "blocked-state:no-memory-write",
          "blocked-state:no-memory-delete",
          "blocked-state:no-memory-export",
          "blocked-state:no-context-injection",
          "blocked-state:no-connector-runtime",
          "blocked-state:no-account-auth",
          "blocked-state:no-model-provider-authority",
          "blocked-state:no-public-beta-or-production-authority",
        ],
        decision_stale_state: "recheck_source_refs_before_memory_use",
        decision_retention_posture: "retention_policy_not_bound",
        decision_correction_posture: "correction_requires_scoped_memory_write_contract",
        decision_authority_boundary:
          "Memory review decisions are review metadata only; writes, deletes, exports, context injection, connector runtime, account auth, and production authority remain unscoped.",
        decision_review_only: true,
        memory_delete_authorized: false,
        memory_export_authorized: false,
        retention_execution_authorized: false,
        business_memory_quality_contract_ref:
          "contract-ref:business-memory-quality-controls:v1",
        business_memory_candidate_ref:
          "business-memory-candidate:preference:memory-review-test",
        business_memory_candidate_kind: "preference",
        business_memory_candidate_kind_ref: "business-memory-kind:preference",
        business_memory_source_provenance_contract_ref:
          "contract-ref:memory-source-provenance:v1",
        business_memory_source_kind: "manual_note",
        business_memory_source_trust_posture: "untrusted_until_reviewed",
        business_memory_redaction_status: "redacted_summary_only",
        business_memory_quality_state_refs: [
          "business-memory-quality:blocked",
          "business-memory-quality:low-confidence",
        ],
        business_memory_quality_posture: "review_required_quality_blocked",
        business_memory_review_state: "review_needed",
        business_memory_correction_path:
          "correction_requires_scoped_memory_write_contract",
        business_memory_stale_state: "recheck_source_refs_before_memory_use",
        business_memory_retention_posture: "retention_policy_not_bound",
        business_memory_delete_posture: "delete_execution_not_scoped",
        business_memory_export_posture: "export_execution_not_scoped",
        business_memory_related_entity_refs: [
          "business-memory-entity:preference:memory-review-test",
        ],
        business_memory_duplicate_of_refs: [],
        business_memory_conflict_with_refs: [],
        business_memory_blocker_refs: [
          "blocked-state:no-memory-write",
          "blocked-state:no-memory-delete",
          "blocked-state:no-memory-export",
          "blocked-state:no-context-injection",
          "blocked-state:no-external-crm-write",
          "blocked-state:no-account-sync",
          "blocked-state:no-automatic-recall",
          "blocked-state:no-connector-runtime",
          "blocked-state:no-account-auth",
          "blocked-state:no-model-provider-authority",
          "blocked-state:no-source-truth-authority",
          "blocked-state:no-raw-source-display",
          "blocked-state:no-public-beta-or-distribution",
          "blocked-state:no-production-authority",
        ],
        business_memory_surface_refs: [
          "today-ref:memory-review-business-quality",
          "action-inbox-ref:memory-follow-up-candidates",
          "evidence-ref:memory-business-quality-history",
          "weekly-review-ref:business-memory-carry-forward",
        ],
        business_memory_next_safe_action:
          "Review quality posture and safe refs; keep memory writes, CRM sync, and context injection blocked until scoped policy milestones exist.",
        business_memory_safe_refs_only: true,
        business_memory_review_required_before_recall: true,
        business_memory_accepted_as_recall: false,
        business_memory_write_authorized: false,
        business_memory_delete_authorized: false,
        business_memory_export_authorized: false,
        business_memory_crm_write_authorized: false,
        business_memory_account_sync_authorized: false,
        business_memory_context_injection_authorized: false,
        business_memory_authority_boundary:
          "Business memory quality is review metadata only; external CRM writes, account sync, automatic recall, memory mutation, and context injection remain unscoped.",
      },
    ],
    memory_review_route_ref: "/memory",
    memory_review_backend_route_ref: "GET /control-center/today/summary",
    memory_review_status:
      "storage_backed_review_queue_with_business_quality_and_loop_binding_metadata",
    memory_review_authority_boundary:
      "Review-only memory candidates; recall is not truth, and writes, deletes, context injection, connector writes, model/provider calls, and background sync are unscoped.",
    memory_write_enabled: false,
    memory_delete_enabled: false,
    context_injection_enabled: false,
    memory_review_missing_contract_refs: [
      "contract-ref:memory-write-policy-binding-missing",
      "contract-ref:memory-retention-delete-missing",
      "contract-ref:context-injection-missing",
    ],
    memory_review_blocked_states: [
      "no_memory_write",
      "no_context_injection",
      "no_memory_delete",
      "no_memory_export",
      "no_raw_source_display",
      "no_external_crm_write",
      "no_account_sync",
      "no_automatic_recall",
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
        item_kind: "plan_action_envelope_ref",
        title: "Founder Loop test plan",
        safe_summary:
          "Plan evidence includes a reviewable Action envelope ref with exact scope, expected receipts, idempotency, rollback, and safe-disable posture; execution remains blocked.",
        source_refs: ["plan-summary:test"],
        status_refs: [
          "status-ref:founder-loop-plan-summary",
          "contract-ref:plans-action-envelope:v1",
          "action-envelope:plans:plan-summary-test",
        ],
        related_route_refs: ["/plans", "/task-decomposition/status"],
        side_effect_class: "validation_only",
        authority_posture:
          "Reviewable Action envelope only; execution and approval grant capture remain blocked until exact scoped LocalApprovalAuthority validation exists.",
        approval_posture:
          "approval-requirement:plans-action-envelope:plan-summary-test",
        receipt_refs: ["receipt-plan:plans-action-envelope:plan-summary-test"],
        audit_refs: [],
        replay_refs: ["replay-ref:founder-loop:plan-summary"],
        rollback_refs: ["rollback-plan:plans-action-envelope:plan-summary-test"],
        rollback_blockers: ["rollback_execution_not_scoped"],
        latency_refs: [],
        foundation_gate_refs: [],
        redaction_status: "redacted_summary_only",
        stale_state: "recheck_plan_and_action_refs_before_mutation",
        missing_evidence_posture:
          "execution_receipt_missing_until_scoped_action_contract",
        blocked_states: [
          "blocked-state:no-action-execution",
          "blocked-state:no-approval-grant-capture",
          "blocked-state:approval-refs-identifiers-only",
          "blocked-state:no-connector-write",
          "blocked-state:no-shell-subprocess-execution",
          "blocked-state:no-model-provider-authority",
          "blocked-state:no-public-beta-or-distribution",
          "blocked-state:no-production-authority",
        ],
        next_safe_action: "Review route-backed summaries.",
      },
      {
        timeline_item_ref: "evidence-timeline:memory/memory-review/test",
        item_kind: "memory_review_evidence_ref",
        title: "Memory review",
        safe_summary:
          "Memory evidence is recall metadata only. Memory is not truth, not approval, and not context-injection authority.",
        source_refs: ["memory-review:test", "source-ref:manual-note:test"],
        status_refs: [
          "status-ref:founder-loop-memory-review",
          "contract-ref:memory-write-policy-binding-missing",
          "contract-ref:memory-retention-delete-missing",
          "contract-ref:business-memory-quality-controls:v1",
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
    evidence_timeline_status: "storage_backed_redacted_history_grammar_refs",
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
