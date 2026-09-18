import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FinanceWorkspacePanel } from "./FinanceWorkspacePanel";
import { FinanceCommitNotAttemptedError } from "../api/client";
import type { FinanceView } from "../api/financeWorkspace";
import { financeBinding, financeCommit, financePreparation, financeSetup, financeView } from "../test/financeWorkspaceFixture";

const api = vi.hoisted(() => ({ loadFinance: vi.fn(), prepareFinance: vi.fn(), commitFinance: vi.fn(), refreshFinance: vi.fn() }));
vi.mock("../api/financeWorkspace", () => api);
vi.mock("../backendTruthMutationBinding", () => ({ useBackendTruthMutationBinding: () => financeBinding }));

function mockFinanceApi() {
  api.loadFinance.mockResolvedValue(financeView);
  api.prepareFinance.mockImplementation(async intent => financePreparation(intent));
  api.commitFinance.mockImplementation(async prepared => financeCommit(prepared));
}

describe("Finance workspace", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("opens saved state without preparing or saving on mount", async () => {
    mockFinanceApi();
    render(<FinanceWorkspacePanel />);
    expect(await screen.findByRole("button", { name: "Confirm review" })).toBeEnabled();
    expect(api.prepareFinance).not.toHaveBeenCalled(); expect(api.commitFinance).not.toHaveBeenCalled();
  });
  it("previews setup, then separately confirms creation", async () => {
    mockFinanceApi();
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
  it.each(["create", "import_commit"])("allows an expired unsubmitted %s preview to be closed and prepared again", async operation => {
    mockFinanceApi();
    api.loadFinance.mockResolvedValue(operation === "create" ? financeSetup : {
      ...financeSetup, status: "ready", revision: 1, snapshot_ref: financeView.snapshot_ref, import_available: true,
    });
    render(<FinanceWorkspacePanel />);
    const label = operation === "create" ? "Preview sample book" : "Preview sample import";
    fireEvent.click(await screen.findByRole("button", { name: label }));
    await screen.findByRole("heading", { name: "Review before saving" });
    const clock = vi.spyOn(Date, "now").mockReturnValue(Date.now() + 120_000);
    try {
      fireEvent.click(screen.getByRole("button", { name: "Confirm and save" }));
      expect(await screen.findByText(/preview expired before a save was requested/)).toBeInTheDocument();
      expect(api.commitFinance).not.toHaveBeenCalled();
      expect(screen.getByRole("button", { name: "Close preview without saving" })).toBeEnabled();
      fireEvent.click(screen.getByRole("button", { name: "Close preview without saving" }));
    } finally { clock.mockRestore(); }
    fireEvent.click(screen.getByRole("button", { name: label }));
    await screen.findByRole("heading", { name: "Review before saving" });
    expect(api.prepareFinance).toHaveBeenCalledTimes(2);
    expect(api.commitFinance).not.toHaveBeenCalled();
  });
  it("keeps confirmed receipt when the subsequent read fails", async () => {
    mockFinanceApi();
    api.loadFinance.mockResolvedValueOnce(financeView).mockRejectedValue(new Error("private read detail"));
    render(<FinanceWorkspacePanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Confirm review" }));
    fireEvent.click(await screen.findByRole("button", { name: "Confirm and save" }));
    expect(await screen.findByText(/save receipt is confirmed, but the refreshed view is unavailable/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Saved receipt" })).toBeInTheDocument();
    expect(screen.queryByText("private read detail")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirm review" })).toBeDisabled();
  });
  it.each(["create", "import_commit"])("can restart %s when only the server observes preview expiry", async operation => {
    mockFinanceApi();
    api.loadFinance.mockResolvedValue(operation === "create" ? financeSetup : {
      ...financeSetup, status: "ready", revision: 1, snapshot_ref: financeView.snapshot_ref, import_available: true,
    });
    api.commitFinance.mockRejectedValueOnce(new FinanceCommitNotAttemptedError());
    render(<FinanceWorkspacePanel />);
    const label = operation === "create" ? "Preview sample book" : "Preview sample import";
    fireEvent.click(await screen.findByRole("button", { name: label }));
    fireEvent.click(await screen.findByRole("button", { name: "Confirm and save" }));
    expect(await screen.findByText(/server rejected this save before any book write/)).toBeInTheDocument();
    const close = screen.getByRole("button", { name: "Close preview without saving" });
    await waitFor(() => expect(close).toBeEnabled());
    fireEvent.click(close);
    fireEvent.click(screen.getByRole("button", { name: label }));
    await screen.findByRole("heading", { name: "Review before saving" });
    expect(api.prepareFinance).toHaveBeenCalledTimes(2);
    expect(api.commitFinance).toHaveBeenCalledTimes(1);
    expect(api.prepareFinance.mock.calls[1][0].idempotency_ref).not.toBe(api.prepareFinance.mock.calls[0][0].idempotency_ref);
  });
  it("a rejected retry cannot erase an earlier uncertain save", async () => {
    mockFinanceApi();
    api.commitFinance.mockRejectedValueOnce(new Error("unknown save"))
      .mockRejectedValueOnce(new FinanceCommitNotAttemptedError());
    render(<FinanceWorkspacePanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Confirm review" }));
    fireEvent.click(await screen.findByRole("button", { name: "Confirm and save" }));
    const retry = await screen.findByRole("button", { name: "Retry same reviewed save" });
    await waitFor(() => expect(retry).toBeEnabled());
    fireEvent.click(retry);
    await waitFor(() => expect(api.commitFinance).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(retry).toBeEnabled());
    expect(screen.getByRole("button", { name: "Close preview without saving" })).toBeDisabled();
    expect(screen.queryByText(/server rejected this save before any book write/)).not.toBeInTheDocument();
    expect(api.commitFinance.mock.calls[1][0]).toBe(api.commitFinance.mock.calls[0][0]);
  });
  it("retries the exact reviewed payload after an unknown save and failed reload", async () => {
    mockFinanceApi();
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
    mockFinanceApi();
    api.refreshFinance.mockImplementation(async (_prepared, intent) => financePreparation(intent));
    render(<FinanceWorkspacePanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Reject review" }));
    fireEvent.click(await screen.findByRole("button", { name: "Fresh preview of same action" }));
    expect(await screen.findByText(/same action has a fresh preview/)).toBeInTheDocument();
    expect(api.commitFinance).not.toHaveBeenCalled();
  });
  it("does not discard an uncertain save merely because its preview later expires", async () => {
    mockFinanceApi();
    api.commitFinance.mockRejectedValue(new Error("unknown save"));
    render(<FinanceWorkspacePanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Confirm review" }));
    fireEvent.click(await screen.findByRole("button", { name: "Confirm and save" }));
    const retry = await screen.findByRole("button", { name: "Retry same reviewed save" });
    await waitFor(() => expect(retry).toBeEnabled());
    const reviewed = api.commitFinance.mock.calls[0][0];
    const clock = vi.spyOn(Date, "now").mockReturnValue(Date.now() + 120_000);
    try {
      expect(screen.getByRole("button", { name: "Close preview without saving" })).toBeDisabled();
      fireEvent.click(retry);
      await waitFor(() => expect(api.commitFinance).toHaveBeenCalledTimes(2));
      expect(api.commitFinance.mock.calls[1][0]).toBe(reviewed);
      expect(screen.queryByText(/nothing was sent for saving/)).not.toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Close preview without saving" })).toBeDisabled();
    } finally { clock.mockRestore(); }
  });
  it("binds undo to the current effective decision", async () => {
    mockFinanceApi();
    api.loadFinance.mockResolvedValue({ ...financeView, review_items: [{ ...financeView.review_items[0], state: "confirmed", effective_decision_ref: "event-ref:finance:prior" }] });
    render(<FinanceWorkspacePanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Preview undo" }));
    await screen.findByRole("heading", { name: "Review before saving" });
    expect(api.prepareFinance).toHaveBeenCalledWith(expect.objectContaining({ operation: "review_undo", compensates_event_ref: "event-ref:finance:prior" }), financeView.configuration_ref, financeBinding);
  });
  it("shows missing configuration without synthetic success or enabled creation", async () => {
    mockFinanceApi();
    api.loadFinance.mockResolvedValue({ ...financeSetup, status: "configuration_missing", configuration_ref: null });
    render(<FinanceWorkspacePanel />);
    expect(await screen.findByText(/Finance setup is missing/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Preview sample book" })).not.toBeInTheDocument();
    expect(api.prepareFinance).not.toHaveBeenCalled();
  });
  it("safe-disable blocks saves but preserves read access", async () => {
    mockFinanceApi();
    api.loadFinance.mockResolvedValue({ ...financeView, safe_disable_engaged: true });
    render(<FinanceWorkspacePanel />);
    expect(await screen.findByText(/Finance safe-disable is engaged/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirm review" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Reload saved book" })).toBeEnabled();
  });
  it("does not label a safe-disabled unimported book as imported", async () => {
    mockFinanceApi();
    api.loadFinance.mockResolvedValue({ ...financeSetup, status: "ready", revision: 1,
      snapshot_ref: financeView.snapshot_ref, safe_disable_engaged: true, import_available: false });
    render(<FinanceWorkspacePanel />);
    expect(await screen.findByText("Sample import unavailable while safe-disable is engaged")).toBeInTheDocument();
    expect(screen.queryByText("Sample import recorded")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Preview sample import" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reload saved book" })).toBeEnabled();
    expect(api.prepareFinance).not.toHaveBeenCalled();
    expect(api.commitFinance).not.toHaveBeenCalled();
  });
  it("reopens an interrupted review without browser state and requires fresh confirmation", async () => {
    mockFinanceApi();
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

  it.each(["create", "import_commit", "review_decision", "review_undo"] as const)("reopens a lost %s response using Core recovery and requires a separate confirmation", async operation => {
    mockFinanceApi();
    const initial: FinanceView = operation === "create" ? financeSetup : operation === "import_commit" ? {
      ...financeSetup, status: "ready", revision: 1, snapshot_ref: financeView.snapshot_ref, import_available: true,
    } : operation === "review_undo" ? {
      ...financeView, revision: 3, review_items: [{ ...financeView.review_items[0], state: "confirmed", effective_decision_ref: "event-ref:finance:prior" }],
    } : financeView;
    let currentView = initial;
    api.loadFinance.mockImplementation(async () => currentView);
    api.commitFinance.mockImplementationOnce(async preparation => {
      const intent = { review_item_ref: null, decision: null, compensates_event_ref: null, ...api.prepareFinance.mock.calls[0][0] };
      // The attempt is retained before any staged review or newer snapshot exists.
      currentView = { ...initial, recovery: { intent, preparation, result: null } };
      throw new Error("response lost");
    }).mockImplementation(async preparation => {
      const result = financeCommit(preparation);
      currentView = { ...currentView, recovery: { ...currentView.recovery!, result } };
      return result;
    });
    api.refreshFinance.mockImplementation(async (_preparation, intent) => financePreparation(intent));
    const firstMount = render(<FinanceWorkspacePanel />);
    const newActionLabel = operation === "create" ? "Preview sample book" : operation === "import_commit" ? "Preview sample import"
      : operation === "review_undo" ? "Preview undo" : "Confirm review";
    fireEvent.click(await screen.findByRole("button", { name: newActionLabel }));
    fireEvent.click(await screen.findByRole("button", { name: "Confirm and save" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Retry same reviewed save" })).toBeEnabled());
    const retainedPreparation = api.commitFinance.mock.calls[0][0];
    firstMount.unmount();

    render(<FinanceWorkspacePanel />);
    const review = await screen.findByRole("button", { name: "Review interrupted save" });
    expect(screen.getByRole("button", { name: newActionLabel })).toBeDisabled();
    expect(api.prepareFinance).toHaveBeenCalledTimes(1);
    expect(api.commitFinance).toHaveBeenCalledTimes(1);
    expect(api.refreshFinance).not.toHaveBeenCalled();
    fireEvent.click(review);
    expect(await screen.findByRole("heading", { name: "Review before saving" })).toHaveFocus();
    expect(screen.getByRole("button", { name: "Close preview without saving" })).toBeDisabled();
    expect(api.commitFinance).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Fresh preview of same action" }));
    await screen.findByText(/same action has a fresh preview/);
    expect(api.refreshFinance).toHaveBeenCalledWith(retainedPreparation, currentView.recovery!.intent, financeBinding);
    expect(api.commitFinance).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Retry same reviewed save" }));
    await screen.findByRole("heading", { name: "Saved receipt" });
    expect(api.commitFinance).toHaveBeenCalledTimes(2);
    expect(api.commitFinance.mock.calls[1][0].bundle.request.idempotency_ref)
      .toBe(retainedPreparation.bundle.request.idempotency_ref);
    expect(api.prepareFinance).toHaveBeenCalledTimes(1);
  });

  it("a rejected retry after reopening cannot erase the earlier uncertainty", async () => {
    mockFinanceApi();
    const intent = { operation: "create" as const, expected_revision: 0, request_ref: "request-ref:finance:retained",
      idempotency_ref: "idempotency-ref:finance:retained", review_item_ref: null, decision: null, compensates_event_ref: null };
    const preparation = financePreparation(intent);
    api.loadFinance.mockResolvedValue({ ...financeSetup, recovery: { intent, preparation, result: null } });
    api.commitFinance.mockRejectedValue(new FinanceCommitNotAttemptedError());
    render(<FinanceWorkspacePanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Review interrupted save" }));
    fireEvent.click(screen.getByRole("button", { name: "Retry same reviewed save" }));
    await screen.findByText(/save outcome is unconfirmed/);
    await waitFor(() => expect(screen.getByRole("button", { name: "Retry same reviewed save" })).toBeEnabled());
    expect(screen.getByRole("button", { name: "Close preview without saving" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Preview sample book" })).toBeDisabled();
    expect(screen.queryByText(/server rejected this save before any book write/)).not.toBeInTheDocument();
    expect(api.prepareFinance).not.toHaveBeenCalled();
  });

  it("restores a historical Core receipt even when the current book cannot be read", async () => {
    mockFinanceApi();
    const intent = { operation: "create" as const, expected_revision: 0, request_ref: "request-ref:finance:saved",
      idempotency_ref: "idempotency-ref:finance:saved", review_item_ref: null, decision: null, compensates_event_ref: null };
    const preparation = financePreparation(intent);
    api.loadFinance.mockResolvedValue({ ...financeSetup, status: "unavailable", revision: null,
      recovery: { intent, preparation, result: financeCommit(preparation) } });
    render(<FinanceWorkspacePanel />);
    expect(await screen.findByRole("heading", { name: "Saved receipt" })).toBeInTheDocument();
    expect(screen.getByText(/historical receipt confirms that exact saved action/)).toBeInTheDocument();
    expect(screen.getByText(/saved book could not be read safely/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Review interrupted save" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Confirm and save" })).not.toBeInTheDocument();
    expect(api.prepareFinance).not.toHaveBeenCalled(); expect(api.commitFinance).not.toHaveBeenCalled();
  });

  it("settles a lost response when the following read returns the exact Core receipt", async () => {
    mockFinanceApi();
    api.loadFinance.mockResolvedValueOnce(financeView).mockImplementation(async () => {
      const intent = { compensates_event_ref: null, ...api.prepareFinance.mock.calls[0][0] };
      const preparation = financePreparation(intent);
      return { ...financeView, recovery: { intent, preparation, result: financeCommit(preparation) } };
    });
    api.commitFinance.mockRejectedValue(new Error("response lost"));
    render(<FinanceWorkspacePanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Confirm review" }));
    fireEvent.click(await screen.findByRole("button", { name: "Confirm and save" }));
    await screen.findByRole("heading", { name: "Saved receipt" });
    expect(screen.queryByRole("button", { name: "Retry same reviewed save" })).not.toBeInTheDocument();
    expect(screen.queryByText(/save outcome is unconfirmed/)).not.toBeInTheDocument();
    expect(api.commitFinance).toHaveBeenCalledTimes(1);
  });

  it("shows retained recovery with an unavailable helper but disables confirmation", async () => {
    mockFinanceApi();
    const intent = { operation: "create" as const, expected_revision: 0, request_ref: "request-ref:finance:retained",
      idempotency_ref: "idempotency-ref:finance:retained", review_item_ref: null, decision: null, compensates_event_ref: null };
    api.loadFinance.mockResolvedValue({ ...financeSetup, status: "helper_unavailable", revision: null,
      recovery: { intent, preparation: financePreparation(intent), result: null } });
    render(<FinanceWorkspacePanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Review interrupted save" }));
    expect(screen.getByRole("button", { name: "Retry same reviewed save" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Fresh preview of same action" })).toBeDisabled();
    expect(api.commitFinance).not.toHaveBeenCalled();
  });
});
