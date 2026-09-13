import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  NewsSignalsAdoptionMutationPreview,
  NewsSignalsAdoptionView,
} from "../api/types";
import { NewsSignalsPreviewPanel } from "./NewsSignalsPreviewPanel";
import { workspace, preview } from "../test/newsSignalsAdoptionFixture";

const apiMocks = vi.hoisted(() => ({
  captureNewsSignalsAdoptionApproval: vi.fn(),
  commitNewsSignalsAdoptionMutation: vi.fn(),
  loadNewsSignalsAdoptionWorkspace: vi.fn(),
  previewNewsSignalsAdoptionMutation: vi.fn(),
}));

vi.mock("../api/client", () => apiMocks);
vi.mock("../backendTruthMutationBinding", () => ({
  useBackendTruthMutationBinding: () => ({
    snapshotRef: "backend-truth-ref:test",
    backendRevisionRef: "backend-revision-ref:test",
    backendInstanceRef: "backend-instance-ref:test",
  }),
}));

const readySource = {
  source_ref: "source-ref:q34:official",
  source_kind: "official" as const,
  safe_label: "Official source",
  state: "ready" as const,
  observed_at: "2026-09-09T12:00:00Z",
  freshness_ttl_seconds: 86_400,
  adapter_ref: "connector-adapter-ref:q34:local",
  provenance_ref: "provenance-ref:q34:local",
  retention_ref: "retention-ref:q34:local",
  reason_refs: ["reason-ref:q34:local"],
  external_network_read_performed: false as const,
  account_authority_granted: false as const,
};

const activeItem = {
  signal_ref: "signal-ref:q34:governed",
  title: "Governed signal",
  safe_summary: "A bounded redacted summary for review.",
  source_ref: readySource.source_ref,
  source_label: readySource.safe_label,
  source_state: "ready" as const,
  topic_ref: "topic-ref:q34:governance",
  published_at: "2026-09-09T11:00:00Z",
  evidence_class: "primary" as const,
  claim_stance: "supports" as const,
  confidence_percent: 91,
  external_content_untrusted: true as const,
};

const readItem = {
  ...activeItem,
  cluster_ref: "cluster-ref:q34:governance",
  claim_ref: "claim-ref:q34:governance",
  source_kind: readySource.source_kind,
  source_revision_ref: "source-revision-ref:q34:governance",
  content_digest_ref: "content-digest-ref:q34:governance",
  observed_at: "2026-09-09T12:00:00Z",
  freshness_state: "fresh" as const,
  confidence_state: "high" as const,
  conflict_state: "none" as const,
  coverage_source_refs: [readySource.source_ref],
  coverage_count: 1,
  provenance_refs: [
    "provenance-ref:q34:operator-supplied",
    "approval-ref:q34:governance",
  ],
  rank_score: 91,
  rank_reason_refs: ["reason-ref:q34:fresh-primary-evidence"],
  briefing_candidate: true,
  action_authority_granted: false as const,
};

const readyWorkspace: NewsSignalsAdoptionView = {
  ...workspace,
  status: "ready",
  storage_status: "ready",
  revision: 2,
  current_state_ref: "state-ref:news-signals-adoption:ready",
  summary: {
    ...workspace.summary,
    status: "ready",
    source_readiness: [readySource],
    items: [readItem],
  },
  active_items_page: {
    offset: 0,
    limit: 100,
    total_items: 101,
    returned_items: 1,
    has_previous: false,
    has_next: true,
    search_applied: false,
    items: [activeItem],
  },
};

describe("NewsSignalsPreviewPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.loadNewsSignalsAdoptionWorkspace.mockResolvedValue(workspace);
    apiMocks.previewNewsSignalsAdoptionMutation.mockResolvedValue(preview);
    apiMocks.captureNewsSignalsAdoptionApproval.mockResolvedValue({});
    apiMocks.commitNewsSignalsAdoptionMutation.mockResolvedValue({});
  });

  it("reviews and confirms one exact local source registration", async () => {
    render(<NewsSignalsPreviewPanel />);

    const input = await screen.findByLabelText("Source name");
    fireEvent.change(input, { target: { value: "Official source" } });
    fireEvent.click(screen.getByRole("button", { name: "Review source" }));

    await waitFor(() =>
      expect(apiMocks.previewNewsSignalsAdoptionMutation).toHaveBeenCalledWith(
        expect.objectContaining({
          action: "register_source",
          expected_revision: 0,
          source_draft: expect.objectContaining({
            safe_label: "Official source",
          }),
        }),
        expect.stringMatching(/^idempotency-ref:news-signals-adoption-ui:/),
      ),
    );
    expect(
      await screen.findByRole("heading", { name: "Review this one local change" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Confirm and save" }));

    await waitFor(() =>
      expect(apiMocks.commitNewsSignalsAdoptionMutation).toHaveBeenCalledTimes(1),
    );
    expect(apiMocks.captureNewsSignalsAdoptionApproval).toHaveBeenCalledTimes(1);
    expect(
      await screen.findByText("The reviewed local News change was saved."),
    ).toBeInTheDocument();
  });

  it("shows backend setup guidance without approving or saving on mount", async () => {
    const nextSafeAction = "Review and confirm your first local source to initialize News storage.";
    apiMocks.loadNewsSignalsAdoptionWorkspace.mockResolvedValue({
      ...workspace,
      next_safe_action: nextSafeAction,
    });
    render(<NewsSignalsPreviewPanel />);

    expect(await screen.findByText(nextSafeAction)).toBeInTheDocument();
    expect(apiMocks.previewNewsSignalsAdoptionMutation).not.toHaveBeenCalled();
    expect(apiMocks.captureNewsSignalsAdoptionApproval).not.toHaveBeenCalled();
    expect(apiMocks.commitNewsSignalsAdoptionMutation).not.toHaveBeenCalled();
  });

  it("exposes the selected signal provenance refs", async () => {
    apiMocks.loadNewsSignalsAdoptionWorkspace.mockResolvedValue(readyWorkspace);
    render(<NewsSignalsPreviewPanel />);

    expect(
      await screen.findByText(
        "provenance-ref:q34:operator-supplied · approval-ref:q34:governance",
      ),
    ).toBeInTheDocument();
  });

  it("invalidates a pending review when a bound draft field changes", async () => {
    render(<NewsSignalsPreviewPanel />);

    const input = await screen.findByLabelText("Source name");
    fireEvent.change(input, { target: { value: "Official source" } });
    fireEvent.click(screen.getByRole("button", { name: "Review source" }));
    expect(
      await screen.findByRole("heading", { name: "Review this one local change" }),
    ).toBeInTheDocument();

    fireEvent.change(input, { target: { value: "Changed source" } });

    expect(
      screen.queryByRole("button", { name: "Confirm and save" }),
    ).not.toBeInTheDocument();
  });

  it("discards an in-flight preview when a bound draft field changes", async () => {
    let resolvePreview: ((value: NewsSignalsAdoptionMutationPreview) => void) | undefined;
    apiMocks.previewNewsSignalsAdoptionMutation.mockReturnValueOnce(
      new Promise<NewsSignalsAdoptionMutationPreview>((resolve) => {
        resolvePreview = resolve;
      }),
    );
    render(<NewsSignalsPreviewPanel />);

    const input = await screen.findByLabelText("Source name");
    fireEvent.change(input, { target: { value: "Official source" } });
    fireEvent.click(screen.getByRole("button", { name: "Review source" }));
    await waitFor(() =>
      expect(apiMocks.previewNewsSignalsAdoptionMutation).toHaveBeenCalledTimes(1),
    );

    fireEvent.change(input, { target: { value: "Changed while reviewing" } });
    resolvePreview?.(preview);

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Review source" })).toBeEnabled(),
    );
    expect(
      screen.queryByRole("button", { name: "Confirm and save" }),
    ).not.toBeInTheDocument();
  });

  it("keeps every safe-disabled source individually recoverable", async () => {
    apiMocks.loadNewsSignalsAdoptionWorkspace.mockResolvedValue({
      ...workspace,
      revision: 4,
      summary: {
        ...workspace.summary,
        status: "blocked_source_unavailable",
        source_readiness: [
          { ...readySource, state: "safe_disabled", safe_label: "First source" },
          {
            ...readySource,
            source_ref: "source-ref:q34:second",
            state: "safe_disabled",
            safe_label: "Second source",
          },
        ],
      },
    });
    render(<NewsSignalsPreviewPanel />);

    const recoveryButtons = await screen.findAllByRole("button", {
      name: "Review recovery",
    });
    expect(recoveryButtons).toHaveLength(2);
    fireEvent.click(recoveryButtons[1]);

    await waitFor(() =>
      expect(apiMocks.previewNewsSignalsAdoptionMutation).toHaveBeenCalledWith(
        expect.objectContaining({
          action: "set_source_state",
          target_ref: "source-ref:q34:second",
          source_state: "ready",
        }),
        expect.any(String),
      ),
    );
  });

  it("exposes normal source and signal correction flows", async () => {
    apiMocks.loadNewsSignalsAdoptionWorkspace.mockResolvedValue(readyWorkspace);
    render(<NewsSignalsPreviewPanel />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Edit Official source" }),
    );
    fireEvent.change(screen.getByLabelText("Source name"), {
      target: { value: "Renamed source" },
    });
    fireEvent.change(screen.getByLabelText("Freshness window (seconds)"), {
      target: { value: "172800" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Review source correction" }),
    );
    await waitFor(() =>
      expect(apiMocks.previewNewsSignalsAdoptionMutation).toHaveBeenCalledWith(
        expect.objectContaining({
          action: "update_source",
          target_ref: readySource.source_ref,
          source_draft: expect.objectContaining({
            safe_label: "Renamed source",
            freshness_ttl_seconds: 172_800,
          }),
        }),
        expect.any(String),
      ),
    );

    fireEvent.click(screen.getByRole("button", { name: "Edit Governed signal" }));
    fireEvent.change(
      screen.getByLabelText(
        "Topic correction (optional; blank preserves existing topic)",
      ),
      { target: { value: "Agent governance" } },
    );
    fireEvent.change(
      screen.getByLabelText(
        "Claim correction (optional; blank preserves existing claim)",
      ),
      {
      target: { value: "The reviewed governance milestone occurred" },
      },
    );
    fireEvent.change(screen.getByLabelText("Confidence percent"), {
      target: { value: "77" },
    });
    fireEvent.change(screen.getByLabelText("Evidence class"), {
      target: { value: "corroborating" },
    });
    fireEvent.change(screen.getByLabelText("Claim stance"), {
      target: { value: "disputes" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Review signal correction" }),
    );
    await waitFor(() =>
      expect(apiMocks.previewNewsSignalsAdoptionMutation).toHaveBeenCalledWith(
        expect.objectContaining({
          action: "update_signal",
          target_ref: activeItem.signal_ref,
          signal_draft: expect.objectContaining({
            title: activeItem.title,
            safe_summary: activeItem.safe_summary,
            claim_label: "The reviewed governance milestone occurred",
            confidence_percent: 77,
            evidence_class: "corroborating",
            claim_stance: "disputes",
          }),
        }),
        expect.any(String),
      ),
    );
  });

  it("invalidates signal review when evidence classification changes", async () => {
    apiMocks.loadNewsSignalsAdoptionWorkspace.mockResolvedValue(readyWorkspace);
    render(<NewsSignalsPreviewPanel />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Edit Governed signal" }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Review signal correction" }),
    );
    expect(
      await screen.findByRole("heading", { name: "Review this one local change" }),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Evidence class"), {
      target: { value: "commentary" },
    });

    expect(
      screen.queryByRole("button", { name: "Confirm and save" }),
    ).not.toBeInTheDocument();
  });

  it("preserves claim identity when an edit leaves claim correction blank", async () => {
    apiMocks.loadNewsSignalsAdoptionWorkspace.mockResolvedValue(readyWorkspace);
    render(<NewsSignalsPreviewPanel />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Edit Governed signal" }),
    );
    expect(
      screen.getByLabelText(
        "Topic correction (optional; blank preserves existing topic)",
      ),
    ).toHaveValue("");
    expect(
      screen.getByLabelText(
        "Claim correction (optional; blank preserves existing claim)",
      ),
    ).toHaveValue("");
    fireEvent.click(
      screen.getByRole("button", { name: "Review signal correction" }),
    );

    await waitFor(() =>
      expect(apiMocks.previewNewsSignalsAdoptionMutation).toHaveBeenCalledWith(
        expect.objectContaining({
          action: "update_signal",
          signal_draft: expect.not.objectContaining({
            claim_label: expect.anything(),
            topic_label: expect.anything(),
          }),
        }),
        expect.any(String),
      ),
    );
  });

  it.each([
    "2026-09-09T11:00:37.123456Z",
    "2026-09-09T11:00:37.123456789Z",
    "2026-09-09T04:00:37.654321-07:00",
  ])("preserves timestamp precision and grouping during a text edit: %s", async (publishedAt) => {
    apiMocks.loadNewsSignalsAdoptionWorkspace.mockResolvedValue({
      ...readyWorkspace,
      active_items_page: {
        ...readyWorkspace.active_items_page,
        items: [{ ...activeItem, published_at: publishedAt }],
      },
    });
    render(<NewsSignalsPreviewPanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Edit Governed signal" }));
    fireEvent.change(screen.getByLabelText("Redacted summary"), {
      target: { value: "A text-only correction." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Review signal correction" }));
    await waitFor(() => expect(apiMocks.previewNewsSignalsAdoptionMutation).toHaveBeenCalled());
    const request = apiMocks.previewNewsSignalsAdoptionMutation.mock.lastCall?.[0];
    expect(request.signal_draft.published_at).toBe(publishedAt);
    expect(request.signal_draft).not.toHaveProperty("cluster_label");
    expect(request.signal_draft).not.toHaveProperty("topic_label");
    expect(request.signal_draft).not.toHaveProperty("claim_label");

    const correctedDate = "2026-09-08T14:20:37.123";
    fireEvent.change(screen.getByLabelText("Published"), {
      target: { value: correctedDate },
    });
    expect(screen.queryByRole("button", { name: "Confirm and save" })).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(
      "Story group correction (optional; blank preserves existing group)",
    ), { target: { value: "Corrected story group" } });
    fireEvent.click(screen.getByRole("button", { name: "Review signal correction" }));
    await waitFor(() => expect(apiMocks.previewNewsSignalsAdoptionMutation).toHaveBeenCalledTimes(2));
    const corrected = apiMocks.previewNewsSignalsAdoptionMutation.mock.lastCall?.[0];
    expect(corrected.signal_draft.published_at).toBe(new Date(correctedDate).toISOString());
    expect(corrected.signal_draft.cluster_label).toBe("Corrected story group");
  });

  it("discards canceled correction fields before creating another signal", async () => {
    apiMocks.loadNewsSignalsAdoptionWorkspace.mockResolvedValue(readyWorkspace);
    render(<NewsSignalsPreviewPanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Edit Governed signal" }));
    fireEvent.change(screen.getByLabelText(
      "Story group correction (optional; blank preserves existing group)",
    ), { target: { value: "Canceled group" } });
    fireEvent.change(screen.getByLabelText("Confidence percent"), { target: { value: "11" } });
    fireEvent.click(screen.getByRole("button", { name: "Cancel signal edit" }));
    expect(screen.getByLabelText("Story group (optional; defaults to headline)")).toHaveValue("");
    fireEvent.change(screen.getByLabelText("Headline"), { target: { value: "New independent signal" } });
    fireEvent.change(screen.getByLabelText("Redacted summary"), { target: { value: "A new reviewed summary." } });
    fireEvent.change(screen.getByLabelText("Topic"), { target: { value: "New topic" } });
    fireEvent.change(screen.getByLabelText("Claim"), { target: { value: "New claim" } });
    fireEvent.click(screen.getByRole("button", { name: "Review signal" }));
    await waitFor(() => expect(apiMocks.previewNewsSignalsAdoptionMutation).toHaveBeenCalled());
    const request = apiMocks.previewNewsSignalsAdoptionMutation.mock.lastCall?.[0];
    expect(request.action).toBe("ingest_signal");
    expect(request.signal_draft.cluster_label).toBe("New independent signal");
    expect(request.signal_draft.confidence_percent).toBe(80);
    expect(request.signal_draft.published_at).not.toBe(activeItem.published_at);
  });

  it("reports a committed change accurately when the refresh fails", async () => {
    apiMocks.loadNewsSignalsAdoptionWorkspace
      .mockResolvedValueOnce(workspace)
      .mockRejectedValueOnce(new Error("refresh unavailable"));
    render(<NewsSignalsPreviewPanel />);

    const input = await screen.findByLabelText("Source name");
    fireEvent.change(input, { target: { value: "Official source" } });
    fireEvent.click(screen.getByRole("button", { name: "Review source" }));
    await screen.findByRole("heading", { name: "Review this one local change" });
    fireEvent.click(screen.getByRole("button", { name: "Confirm and save" }));

    expect(
      await screen.findByText(
        "The local News change was saved, but the workspace could not be refreshed. Reload before making another change.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByText("The local News change was not saved."),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(
        "Backend read unavailable. No sample stories are shown as a fallback.",
      ),
    ).toBeInTheDocument();
  });

  it("clears a prior review when a newer preview fails", async () => {
    apiMocks.loadNewsSignalsAdoptionWorkspace.mockResolvedValue(readyWorkspace);
    apiMocks.previewNewsSignalsAdoptionMutation
      .mockResolvedValueOnce(preview)
      .mockRejectedValueOnce(new Error("New preview failed safely."));
    render(<NewsSignalsPreviewPanel />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Review archive for Governed signal" }),
    );
    expect(
      await screen.findByRole("heading", { name: "Review this one local change" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Review safe-disable" }));
    expect(await screen.findByText("New preview failed safely.")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Confirm and save" }),
    ).not.toBeInTheDocument();
  });

  it("does not offer Q34 recovery for externally governed source states", async () => {
    apiMocks.loadNewsSignalsAdoptionWorkspace.mockResolvedValue({
      ...workspace,
      summary: {
        ...workspace.summary,
        status: "blocked_source_unavailable",
        source_readiness: [{ ...readySource, state: "revoked" }],
      },
    });
    render(<NewsSignalsPreviewPanel />);

    await screen.findByText("Official source · revoked");
    expect(
      screen.queryByRole("button", { name: "Review recovery" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Review safe-disable" }),
    ).not.toBeInTheDocument();
  });

  it("loads later pages and searches the complete active signal contract", async () => {
    apiMocks.loadNewsSignalsAdoptionWorkspace.mockResolvedValue(readyWorkspace);
    render(<NewsSignalsPreviewPanel />);

    fireEvent.click(await screen.findByRole("button", { name: "Next signals" }));
    await waitFor(() =>
      expect(apiMocks.loadNewsSignalsAdoptionWorkspace).toHaveBeenCalledWith({
        offset: 100,
        limit: 100,
      }),
    );

    fireEvent.change(screen.getByLabelText("Search active signals"), {
      target: { value: "governed" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    await waitFor(() =>
      expect(apiMocks.loadNewsSignalsAdoptionWorkspace).toHaveBeenCalledWith({
        offset: 0,
        limit: 100,
        searchQuery: "governed",
      }),
    );
  });
});
