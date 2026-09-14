import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FinanceWorkspacePanel } from "./FinanceWorkspacePanel";
import { financeBinding, financeCommit, financePreparation, financeSetup, financeView } from "../test/financeWorkspaceFixture";

const api = vi.hoisted(() => ({ loadFinance: vi.fn(), prepareFinance: vi.fn(), commitFinance: vi.fn(), refreshFinance: vi.fn() }));
vi.mock("../api/financeWorkspace", () => api);
vi.mock("../backendTruthMutationBinding", () => ({ useBackendTruthMutationBinding: () => financeBinding }));

describe("Finance workspace", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    api.loadFinance.mockResolvedValue(financeView);
    api.prepareFinance.mockImplementation(async intent => financePreparation(intent));
    api.commitFinance.mockImplementation(async prepared => financeCommit(prepared));
  });

  it("opens saved state without preparing or saving on mount", async () => {
    render(<FinanceWorkspacePanel />);
    expect(await screen.findByRole("button", { name: "Confirm review" })).toBeEnabled();
    expect(api.prepareFinance).not.toHaveBeenCalled(); expect(api.commitFinance).not.toHaveBeenCalled();
  });
  it("previews setup, then separately confirms creation", async () => {
    api.loadFinance.mockResolvedValue(financeSetup);
    render(<FinanceWorkspacePanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Preview sample book" }));
    expect(await screen.findByRole("heading", { name: "Review before saving" })).toHaveFocus();
    expect(api.prepareFinance).toHaveBeenCalledWith(expect.objectContaining({ operation: "create", expected_revision: 0 }), financeView.configuration_ref, financeBinding);
    expect(api.commitFinance).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Confirm and save" }));
    expect(await screen.findByRole("heading", { name: "Saved receipt" })).toBeInTheDocument();
    expect(api.commitFinance).toHaveBeenCalledTimes(1);
  });
  it("keeps confirmed receipt when the subsequent read fails", async () => {
    api.loadFinance.mockResolvedValueOnce(financeView).mockRejectedValue(new Error("private read detail"));
    render(<FinanceWorkspacePanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Confirm review" }));
    fireEvent.click(await screen.findByRole("button", { name: "Confirm and save" }));
    expect(await screen.findByText(/save receipt is confirmed, but the refreshed view is unavailable/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Saved receipt" })).toBeInTheDocument();
    expect(screen.queryByText("private read detail")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirm review" })).toBeDisabled();
  });
  it("retries the exact reviewed payload after an unknown save and failed reload", async () => {
    api.loadFinance.mockResolvedValueOnce(financeView).mockRejectedValue(new Error("read failure"));
    api.commitFinance.mockRejectedValueOnce(new Error("unknown save")).mockImplementation(async prepared => financeCommit(prepared));
    render(<FinanceWorkspacePanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Defer review" }));
    fireEvent.click(await screen.findByRole("button", { name: "Confirm and save" }));
    const retry = await screen.findByRole("button", { name: "Retry same reviewed save" });
    await waitFor(() => expect(retry).toBeEnabled());
    expect(screen.getByRole("button", { name: "Close preview without saving" })).toBeDisabled();
    fireEvent.click(retry);
    await waitFor(() => expect(api.commitFinance).toHaveBeenCalledTimes(2));
    expect(api.commitFinance.mock.calls[1][0]).toBe(api.commitFinance.mock.calls[0][0]);
    expect(api.prepareFinance).toHaveBeenCalledTimes(1);
  });
  it("requires a separate confirmation after refreshing the same review", async () => {
    api.refreshFinance.mockImplementation(async (_prepared, intent) => financePreparation(intent));
    render(<FinanceWorkspacePanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Reject review" }));
    fireEvent.click(await screen.findByRole("button", { name: "Refresh same review" }));
    expect(await screen.findByText(/same review intent has a fresh preview/)).toBeInTheDocument();
    expect(api.commitFinance).not.toHaveBeenCalled();
  });
  it("binds undo to the current effective decision", async () => {
    api.loadFinance.mockResolvedValue({ ...financeView, review_items: [{ ...financeView.review_items[0], state: "confirmed", effective_decision_ref: "event-ref:finance:prior" }] });
    render(<FinanceWorkspacePanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Preview undo" }));
    await screen.findByRole("heading", { name: "Review before saving" });
    expect(api.prepareFinance).toHaveBeenCalledWith(expect.objectContaining({ operation: "review_undo", compensates_event_ref: "event-ref:finance:prior" }), financeView.configuration_ref, financeBinding);
  });
  it("shows missing configuration without synthetic success or enabled creation", async () => {
    api.loadFinance.mockResolvedValue({ ...financeSetup, status: "configuration_missing", configuration_ref: null });
    render(<FinanceWorkspacePanel />);
    expect(await screen.findByText(/Finance setup is missing/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Preview sample book" })).not.toBeInTheDocument();
    expect(api.prepareFinance).not.toHaveBeenCalled();
  });
  it("safe-disable blocks saves but preserves read access", async () => {
    api.loadFinance.mockResolvedValue({ ...financeView, safe_disable_engaged: true });
    render(<FinanceWorkspacePanel />);
    expect(await screen.findByText(/Finance safe-disable is engaged/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirm review" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Reload saved book" })).toBeEnabled();
  });
  it("reopens an interrupted review without browser state and requires fresh confirmation", async () => {
    const intent = { operation: "review_decision" as const, expected_revision: 2,
      request_ref: "request-ref:finance:interrupted", idempotency_ref: "idempotency-ref:finance:interrupted",
      review_item_ref: financeView.review_items[0].review_item_ref, decision: "defer" as const };
    const preparation = financePreparation(intent);
    api.loadFinance.mockResolvedValue({ ...financeSetup, status: "outcome_uncertain", revision: null,
      pending_review: { intent, preparation } });
    render(<FinanceWorkspacePanel />);
    const review = await screen.findByRole("button", { name: "Review interrupted save" });
    expect(api.prepareFinance).not.toHaveBeenCalled(); expect(api.commitFinance).not.toHaveBeenCalled();
    fireEvent.click(review);
    expect(await screen.findByRole("heading", { name: "Retry Defer review" })).toBeInTheDocument();
    expect(api.commitFinance).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Retry same reviewed save" }));
    await waitFor(() => expect(api.commitFinance).toHaveBeenCalledWith(preparation, financeBinding));
    expect(api.prepareFinance).not.toHaveBeenCalled();
  });
});
