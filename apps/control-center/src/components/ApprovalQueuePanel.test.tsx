import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ApprovalQueuePanel } from "./ApprovalQueuePanel";
import { mockControlCenterData } from "../mocks/controlCenterData";

describe("ApprovalQueuePanel", () => {
  it("renders backend-owned approval summary without approval authority controls", () => {
    render(
      <ApprovalQueuePanel
        review={mockControlCenterData.m15Review}
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
});
