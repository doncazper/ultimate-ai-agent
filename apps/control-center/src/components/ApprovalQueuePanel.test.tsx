import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ApprovalQueuePanel } from "./ApprovalQueuePanel";
import { mockControlCenterData } from "../mocks/controlCenterData";

describe("ApprovalQueuePanel", () => {
  it("renders backend-owned approval summary without approval authority controls", () => {
    render(
      <ApprovalQueuePanel
        review={mockControlCenterData.m15Review}
        queue={mockControlCenterData.runAttachedApprovalQueue}
        summary={{
          ...mockControlCenterData.dashboard.approval_summary,
          pending_count: 3,
          summary: "Backend approval summary only; no approval is granted.",
        }}
      />,
    );

    const summary = screen.getByLabelText("Backend approval summary");
    expect(within(summary).getByText("Pending summaries")).toBeInTheDocument();
    expect(within(summary).getByText("3")).toBeInTheDocument();
    expect(
      within(summary).getByText("Backend grant records present"),
    ).toBeInTheDocument();
    expect(
      within(summary).getByText(
        "Backend approval summary only; no approval is granted.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^approve$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^grant approval$/i }),
    ).not.toBeInTheDocument();
  });

  it("renders run-attached queue refs as read-only backend state", () => {
    const backendOwnedQueue = {
      ...mockControlCenterData.runAttachedApprovalQueue,
      source: "python_core_run_attached_approval_queue_read_model" as const,
      backend_owned: true,
    };
    render(
      <ApprovalQueuePanel
        review={mockControlCenterData.m15Review}
        queue={backendOwnedQueue}
        summary={mockControlCenterData.dashboard.approval_summary}
      />,
    );

    const queueSummary = screen.getByLabelText("Run-attached approval queue summary");
    expect(within(queueSummary).getByText("Run-attached items")).toBeInTheDocument();
    const unifiedReview = screen.getByLabelText("Unified approval review");
    expect(
      within(unifiedReview).getByText("Approval Review Across Runs And Handoffs"),
    ).toBeInTheDocument();
    expect(
      within(unifiedReview).getByText("Provider/tool contract posture"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Unified approval review sources"),
    ).toBeInTheDocument();
    const connectorQueue = screen.getByLabelText(
      "Connector delivery review queue",
    );
    expect(
      within(connectorQueue).getByText("Connector Delivery Review Queue"),
    ).toBeInTheDocument();
    expect(
      within(connectorQueue).getByText(/delivery-ready metadata only \/ not sent/i),
    ).toBeInTheDocument();
    expect(
      within(connectorQueue).getByText("Delivery execution"),
    ).toBeInTheDocument();
    expect(within(connectorQueue).getByText("blocked/planned")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Backend-owned run-attached approval queue"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("approval request attached").length).toBeGreaterThan(0);
    expect(screen.getByText("Preview-only approval cards")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^deny$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^revoke$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^execute$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^send$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^deliver$/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^retry$/i }),
    ).not.toBeInTheDocument();
  });

  it("redacts unsafe connector delivery strings before rendering", () => {
    const unsafeQueue = {
      ...mockControlCenterData.runAttachedApprovalQueue,
      connector_delivery_review_queue: {
        ...mockControlCenterData.runAttachedApprovalQueue
          .connector_delivery_review_queue!,
        queue_items:
          mockControlCenterData.runAttachedApprovalQueue.connector_delivery_review_queue!.queue_items.map(
            (item) => ({
              ...item,
              delivery_ref: "connector-delivery-ref:raw message body bearer token",
              target_session_ref: "target-session-ref:founder@example.com",
              safe_summary: "raw message body includes provider payload",
              redacted_body_summary_refs: ["/Users/local/raw-message-body"],
              blocked_reason_refs: ["blocked-reason-ref:cookie-token"],
            }),
          ),
      },
    };
    render(
      <ApprovalQueuePanel
        review={mockControlCenterData.m15Review}
        queue={unsafeQueue}
        summary={mockControlCenterData.dashboard.approval_summary}
      />,
    );

    const connectorQueue = screen.getByLabelText("Connector delivery review queue");
    expect(
      within(connectorQueue).getAllByText("redacted-ref:connector-delivery-review")
        .length,
    ).toBeGreaterThan(0);
    expect(screen.queryByText(/raw message body/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/founder@example\.com/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/bearer token/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/provider payload/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\/Users\/local/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/cookie-token/i)).not.toBeInTheDocument();
  });

  it("labels mock approval queue fallback as non-authoritative", () => {
    render(
      <ApprovalQueuePanel
        review={mockControlCenterData.m15Review}
        queue={mockControlCenterData.runAttachedApprovalQueue}
        summary={mockControlCenterData.dashboard.approval_summary}
      />,
    );

    expect(
      screen.getByLabelText("Mock-only non-authoritative approval queue fallback"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("mock-only / non-authoritative").length).toBeGreaterThan(
      0,
    );
    expect(
      screen.queryByLabelText("Backend-owned run-attached approval queue"),
    ).not.toBeInTheDocument();
  });
});
