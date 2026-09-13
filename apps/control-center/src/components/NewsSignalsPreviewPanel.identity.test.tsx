import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { BackendTruthMutationBindingProvider } from "../backendTruthMutationBinding";
import type { NewsSignalsAdoptionView } from "../api/types";
import { workspace, preview } from "../test/newsSignalsAdoptionFixture";
import { NewsSignalsPreviewPanel } from "./NewsSignalsPreviewPanel";

const api = vi.hoisted(() => ({
  loadNewsSignalsAdoptionWorkspace: vi.fn(),
  previewNewsSignalsAdoptionMutation: vi.fn(),
  captureNewsSignalsAdoptionApproval: vi.fn(),
  commitNewsSignalsAdoptionMutation: vi.fn(),
}));
vi.mock("../api/client", () => api);

const binding = {
  snapshotRef: "proof-ref:q34:panel-owner",
  backendRevisionRef: "commit-ref:git:q34-panel-owner",
  backendInstanceRef: "backend-instance-ref:q34-panel-owner",
};
const replacement = { ...binding, backendInstanceRef: "backend-instance-ref:q34-replacement" };
const boundPanel = (owner = binding) => <BackendTruthMutationBindingProvider binding={owner}>
  <NewsSignalsPreviewPanel />
</BackendTruthMutationBindingProvider>;

function paginatedOnlyWorkspace(): NewsSignalsAdoptionView {
  const value = structuredClone(workspace);
  value.active_items_page = {
    offset: 0, limit: 100, total_items: 1, returned_items: 1,
    has_previous: false, has_next: false, search_applied: false,
    items: [{
      signal_ref: "artifact-ref:q34:hidden", title: "Paginated signal",
      safe_summary: "A reviewed signal outside the curated stream.",
      source_ref: "source-ref:q34:hidden", source_label: "Reviewed source",
      source_state: "ready", topic_ref: "topic-ref:q34:hidden",
      published_at: "2026-09-13T12:00:00Z", evidence_class: "primary",
      claim_stance: "unknown", confidence_percent: 90, external_content_untrusted: true,
    }],
  };
  return value;
}

async function startSourcePreview() {
  fireEvent.change(await screen.findByLabelText("Source name"), { target: { value: "Reviewed source" } });
  fireEvent.click(screen.getByRole("button", { name: "Review source" }));
  await screen.findByRole("button", { name: "Confirm and save" });
}

describe("News workspace owner lifecycle", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.loadNewsSignalsAdoptionWorkspace.mockResolvedValue(structuredClone(workspace));
    api.previewNewsSignalsAdoptionMutation.mockResolvedValue(preview);
    api.captureNewsSignalsAdoptionApproval.mockResolvedValue({});
    api.commitNewsSignalsAdoptionMutation.mockResolvedValue({});
  });

  it.each(["snapshotRef", "backendRevisionRef", "backendInstanceRef"] as const)(
    "invalidates the pending review when %s changes", async (field) => {
      const mounted = render(boundPanel());
      await startSourcePreview();
      const next = { ...binding, [field]: `${binding[field]}-next` };
      mounted.rerender(boundPanel(next));
      expect(screen.queryByRole("button", { name: "Confirm and save" })).not.toBeInTheDocument();
      if (field === "snapshotRef") {
        expect(api.loadNewsSignalsAdoptionWorkspace).toHaveBeenCalledTimes(1);
        expect(await screen.findByLabelText("Source name")).toHaveValue("Reviewed source");
      } else {
        await waitFor(() => expect(api.loadNewsSignalsAdoptionWorkspace).toHaveBeenLastCalledWith({ offset: 0, limit: 100 }, next));
        expect(await screen.findByLabelText("Source name")).toHaveValue("");
      }
      expect(api.captureNewsSignalsAdoptionApproval).not.toHaveBeenCalled();
      expect(api.commitNewsSignalsAdoptionMutation).not.toHaveBeenCalled();
    },
  );

  it("does not continue a pending approval into a replacement backend", async () => {
    let approve!: (result: object) => void;
    api.captureNewsSignalsAdoptionApproval.mockImplementationOnce(() => new Promise((resolve) => { approve = resolve; }));
    const mounted = render(boundPanel());
    await startSourcePreview();
    fireEvent.click(screen.getByRole("button", { name: "Confirm and save" }));
    await waitFor(() => expect(api.captureNewsSignalsAdoptionApproval).toHaveBeenCalledTimes(1));
    mounted.rerender(boundPanel(replacement));
    await act(async () => { approve({}); });
    expect(api.commitNewsSignalsAdoptionMutation).not.toHaveBeenCalled();
    expect(screen.queryByText("The reviewed local News change was saved.")).not.toBeInTheDocument();
  });

  it("keeps drafts and search across routine snapshot rotation and reviews with the fresh binding", async () => {
    const mounted = render(boundPanel());
    await startSourcePreview();
    fireEvent.change(screen.getByLabelText("Search active signals"), { target: { value: "Reviewed search" } });
    const next = { ...binding, snapshotRef: "proof-ref:q34:rotated-envelope" };
    mounted.rerender(boundPanel(next));
    expect(screen.getByLabelText("Source name")).toHaveValue("Reviewed source");
    expect(screen.getByLabelText("Search active signals")).toHaveValue("Reviewed search");
    expect(screen.queryByRole("button", { name: "Confirm and save" })).not.toBeInTheDocument();
    expect(api.loadNewsSignalsAdoptionWorkspace).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Review source" }));
    await screen.findByRole("button", { name: "Confirm and save" });
    expect(api.previewNewsSignalsAdoptionMutation).toHaveBeenLastCalledWith(expect.any(Object), expect.any(String), next);
  });

  it("does not continue an approval after its snapshot rotates", async () => {
    let approve!: (result: object) => void;
    api.captureNewsSignalsAdoptionApproval.mockImplementationOnce(() => new Promise((resolve) => { approve = resolve; }));
    const mounted = render(boundPanel());
    await startSourcePreview();
    fireEvent.click(screen.getByRole("button", { name: "Confirm and save" }));
    await waitFor(() => expect(api.captureNewsSignalsAdoptionApproval).toHaveBeenCalledTimes(1));
    mounted.rerender(boundPanel({ ...binding, snapshotRef: "proof-ref:q34:rotated-envelope" }));
    await act(async () => { approve({}); });
    expect(api.commitNewsSignalsAdoptionMutation).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Source name")).toHaveValue("Reviewed source");
    expect(screen.getByRole("button", { name: "Review source" })).toBeEnabled();
  });

  it("discards a preview that completes after its snapshot rotates", async () => {
    let finishPreview!: (value: typeof preview) => void;
    api.previewNewsSignalsAdoptionMutation.mockImplementationOnce(() => new Promise((resolve) => { finishPreview = resolve; }));
    const mounted = render(boundPanel());
    fireEvent.change(await screen.findByLabelText("Source name"), { target: { value: "Unfinished source" } });
    fireEvent.click(screen.getByRole("button", { name: "Review source" }));
    mounted.rerender(boundPanel({ ...binding, snapshotRef: "proof-ref:q34:rotated-envelope" }));
    await act(async () => { finishPreview(preview); });
    expect(screen.queryByRole("button", { name: "Confirm and save" })).not.toBeInTheDocument();
    expect(screen.getByLabelText("Source name")).toHaveValue("Unfinished source");
  });

  it("reports an already-sent commit after a routine snapshot rotation", async () => {
    let finishCommit!: (result: object) => void;
    api.commitNewsSignalsAdoptionMutation.mockImplementationOnce(() => new Promise((resolve) => { finishCommit = resolve; }));
    const mounted = render(boundPanel());
    await startSourcePreview();
    fireEvent.click(screen.getByRole("button", { name: "Confirm and save" }));
    await waitFor(() => expect(api.commitNewsSignalsAdoptionMutation).toHaveBeenCalledTimes(1));
    mounted.rerender(boundPanel({ ...binding, snapshotRef: "proof-ref:q34:rotated-envelope" }));
    await act(async () => { finishCommit({}); });
    expect(await screen.findByText("The reviewed local News change was saved.")).toBeInTheDocument();
    expect(api.commitNewsSignalsAdoptionMutation).toHaveBeenCalledTimes(1);
  });

  it("keeps the admitted source fixed while correcting a signal", async () => {
    const value = paginatedOnlyWorkspace();
    value.summary.source_readiness = ["hidden", "other"].map((suffix) => ({
      source_ref: `source-ref:q34:${suffix}`, source_kind: "official", safe_label: `Reviewed ${suffix}`,
      state: "ready", observed_at: "2026-09-13T12:00:00Z", freshness_ttl_seconds: 86400,
      adapter_ref: "adapter-ref:q34:local", provenance_ref: "provenance-ref:q34:local",
      retention_ref: "retention-ref:q34:local", reason_refs: [],
      external_network_read_performed: false, account_authority_granted: false,
    }));
    api.loadNewsSignalsAdoptionWorkspace.mockResolvedValue(value);
    render(boundPanel());
    fireEvent.click(await screen.findByRole("button", { name: "Edit Paginated signal" }));
    expect(screen.getByLabelText("Source")).toBeDisabled();
    expect(screen.getByLabelText("Source")).toHaveValue("source-ref:q34:hidden");
    expect(screen.getByText("A correction keeps the original source." )).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Review signal correction" }));
    await waitFor(() => expect(api.previewNewsSignalsAdoptionMutation).toHaveBeenCalledWith(
      expect.objectContaining({ action: "update_signal", signal_draft: expect.objectContaining({ source_ref: "source-ref:q34:hidden" }) }),
      expect.any(String), binding,
    ));
  });

  it("discards an old workspace response after the owner changes", async () => {
    let finishOldRead!: (value: NewsSignalsAdoptionView) => void;
    api.loadNewsSignalsAdoptionWorkspace.mockImplementationOnce(() => new Promise((resolve) => { finishOldRead = resolve; }));
    const mounted = render(boundPanel());
    mounted.rerender(boundPanel(replacement));
    await screen.findByLabelText("Source name");
    await act(async () => { finishOldRead(paginatedOnlyWorkspace()); });
    expect(screen.queryByText(/Paginated signal/)).not.toBeInTheDocument();
    expect(api.loadNewsSignalsAdoptionWorkspace).toHaveBeenLastCalledWith({ offset: 0, limit: 100 }, replacement);
  });

  it.each([false, true])("offers the full preference lifecycle outside the curated page (preferred=%s)", async (preferred) => {
    const value = paginatedOnlyWorkspace();
    if (preferred) value.preferences = [{ topic_ref: "topic-ref:q34:hidden", weight: 10, preference_ref: "preference-ref:q34:hidden" }];
    api.loadNewsSignalsAdoptionWorkspace.mockResolvedValue(value);
    render(boundPanel());
    const label = `${preferred ? "Clear topic preference for" : "Prefer topic for"} Paginated signal`;
    fireEvent.click(await screen.findByRole("button", { name: label }));
    await waitFor(() => expect(api.previewNewsSignalsAdoptionMutation).toHaveBeenCalledWith(
      {
        action: preferred ? "remove_preference" : "set_preference",
        expected_revision: value.revision,
        topic_ref: "topic-ref:q34:hidden",
        ...(preferred ? {} : { preference_weight: 10 }),
      },
      expect.stringMatching(/^idempotency-ref:news-signals-adoption-ui:/),
      binding,
    ));
    expect(api.commitNewsSignalsAdoptionMutation).not.toHaveBeenCalled();
  });
});
