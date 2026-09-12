import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  NewsSignalsAdoptionMutationPreview,
  NewsSignalsAdoptionView,
} from "../api/types";
import { NewsSignalsPreviewPanel } from "./NewsSignalsPreviewPanel";

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

const workspace: NewsSignalsAdoptionView = {
  schema_version: "uaa-news-signals-adoption.v1",
  contract_ref: "contract-ref:queue-v2-q34-news-signals-adoption:v1",
  status: "blocked_no_graduated_source",
  revision: 0,
  current_state_ref: "state-ref:news-signals-adoption:empty",
  can_undo: false,
  local_manual_intake_enabled: true,
  backend_owned: true,
  external_content_untrusted: true,
  live_fetch_enabled: false,
  authenticated_source_enabled: false,
  background_polling_enabled: false,
  model_summarization_enabled: false,
  connector_write_enabled: false,
  action_authority_granted: false,
  summary: {
    schema_version: "uaa-news-signals-read-model.v1",
    contract_ref: "contract-ref:queue-v2-q24-news-signals:v1",
    status: "blocked_no_graduated_source",
    backend_owned: true,
    read_only: true,
    local_artifact_snapshot_only: true,
    external_content_untrusted: true,
    live_fetch_enabled: false,
    authenticated_source_enabled: false,
    background_polling_enabled: false,
    model_summarization_enabled: false,
    connector_write_enabled: false,
    action_authority_granted: false,
    observed_at: "2026-09-09T12:00:00Z",
    source_readiness: [],
    items: [],
    freshness_counts: { fresh: 0, stale: 0, unknown: 0 },
    conflicting_claim_refs: [],
    today_projection: {
      projection_ref: "projection-ref:q24:today",
      item_refs: [],
      bounded_limit: 3,
      read_only: true,
    },
    morning_briefing_projection: {
      projection_ref: "projection-ref:q24:morning-briefing",
      candidate_refs: [],
      bounded_limit: 5,
      review_required: true,
      read_only: true,
    },
    safe_summary: "A bounded local News summary for review.",
    blocked_state_refs: ["blocked-state-ref:q24:no-graduated-news-source"],
    evidence_refs: ["evidence-ref:q24:safe-artifacts-only"],
  },
  preferences: [],
  archived_items: [],
  next_safe_action: "Register the first local redacted artifact source.",
  evidence_refs: ["evidence-ref:q34:local-redacted-intake-only"],
};

const preview: NewsSignalsAdoptionMutationPreview = {
  schema_version: "uaa-news-signals-adoption-preview.v1",
  contract_ref: "contract-ref:queue-v2-q34-news-signals-adoption:v1",
  action: "register_source",
  target_ref: null,
  source_ref: "source-ref:q34:official",
  signal_ref: null,
  expected_revision: 0,
  resulting_revision: 1,
  current_state_ref: workspace.current_state_ref,
  payload_fingerprint_ref: "payload-fingerprint-ref:q34:official",
  preview_ref: "preview-ref:q34:official",
  approval_ref: "approval-ref:q34:official",
  safe_summary: "Register one local redacted artifact source.",
  external_network_read_performed: false,
  authenticated_source_access_performed: false,
  model_call_performed: false,
  external_write_performed: false,
  production_authority_granted: false,
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
});
