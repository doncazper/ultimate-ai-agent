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
