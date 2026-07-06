import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { mockControlCenterData } from "../mocks/controlCenterData";
import { ActionInboxSurfacePanel } from "./FounderLoopPanels";

function cloneForTest<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

describe("ActionInboxSurfacePanel work queue", () => {
  it("shows scope, idempotency, and staleness posture from the backend work queue", () => {
    const inbox = cloneForTest(mockControlCenterData.founderActionsInbox);
    const workQueue = cloneForTest(inbox.action_inbox_work_queue_read_model!);
    workQueue.source = "python_core_action_inbox_work_queue_read_model";
    workQueue.backend_owned = true;
    inbox.action_inbox_work_queue_read_model = workQueue;

    render(
      <ActionInboxSurfacePanel
        actionReadModelAuthoritative
        inbox={inbox}
      />,
    );

    const queue = screen.getByLabelText("Action Inbox work queue");
    expect(within(queue).getAllByText("Exact scope").length).toBeGreaterThan(0);
    expect(within(queue).getAllByText("Idempotency").length).toBeGreaterThan(0);
    expect(within(queue).getAllByText("Expiry / stale").length).toBeGreaterThan(0);
    expect(
      within(queue).getAllByText("scope-ref:founder-loop:mock-local-task-review")
        .length,
    ).toBeGreaterThan(0);
    expect(
      within(queue).getAllByText(
        "idempotency-ref:founder-loop:mock-local-task-review",
      ).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: /^execute$/i }),
    ).not.toBeInTheDocument();
  });
});
