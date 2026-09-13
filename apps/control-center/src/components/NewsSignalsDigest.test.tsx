import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { NewsSignalsSummary } from "../api/types";
import { mockControlCenterData } from "../mocks/controlCenterData";
import { TodaySurface } from "../northstar/PrimarySurfaces";
import { renderRoute } from "../routes";
import { workspace } from "../test/newsSignalsAdoptionFixture";
import { NewsSignalsDigest } from "./NewsSignalsDigest";
import { useBackendTruthMutationBinding } from "../backendTruthMutationBinding";

vi.mock("../backendTruthMutationBinding", () => ({ useBackendTruthMutationBinding: vi.fn() }));
const binding = {
  snapshotRef: "proof-ref:q34:digest",
  backendRevisionRef: "commit-ref:git:q34-digest",
  backendInstanceRef: "backend-instance-ref:q34-digest",
};

const apiMocks = vi.hoisted(() => ({ loadNewsSignalsSummary: vi.fn() }));
vi.mock("../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api/client")>()),
  ...apiMocks,
}));

function summary(): NewsSignalsSummary {
  return {
    ...structuredClone(workspace.summary),
    status: "ready",
    observed_at: "2026-09-13T10:00:00Z",
    source_readiness: [{
      source_ref: "source-ref:q34:release",
      source_kind: "official",
      safe_label: "Reviewed project notes",
      state: "ready",
      observed_at: "2026-09-13T10:00:00Z",
      freshness_ttl_seconds: 86400,
      adapter_ref: "adapter-ref:q34:local",
      provenance_ref: "provenance-ref:q34:reviewed",
      retention_ref: "retention-ref:q34:local",
      reason_refs: [],
      external_network_read_performed: false,
      account_authority_granted: false,
    }],
    items: [{
      signal_ref: "signal-ref:q34:release",
      title: "Reviewed local release note",
      safe_summary: "A local milestone is awaiting review.",
      source_ref: "source-ref:q34:release",
      source_label: "Reviewed project notes",
      source_state: "ready",
      source_kind: "official",
      source_revision_ref: "source-revision-ref:q34:release",
      content_digest_ref: "content-digest-ref:q34:release",
      topic_ref: "topic-ref:q34:release",
      cluster_ref: "cluster-ref:q34:release",
      claim_ref: "claim-ref:q34:release",
      published_at: "2026-09-13T09:00:00Z",
      observed_at: "2026-09-13T10:00:00Z",
      freshness_state: "fresh",
      confidence_state: "high",
      confidence_percent: 91,
      evidence_class: "primary",
      conflict_state: "none",
      coverage_source_refs: ["source-ref:q34:release"],
      coverage_count: 1,
      provenance_refs: ["approval-ref:q34:release"],
      rank_score: 91,
      rank_reason_refs: ["reason-ref:q34:reviewed"],
      briefing_candidate: true,
      external_content_untrusted: true,
      action_authority_granted: false,
    }],
    today_projection: {
      projection_ref: "projection-ref:q24:today",
      storage_status: "ready",
      item_refs: ["signal-ref:q34:release"],
      bounded_limit: 3,
      read_only: true,
    },
    morning_briefing_projection: {
      projection_ref: "projection-ref:q24:morning-briefing",
      storage_status: "ready",
      candidate_refs: ["signal-ref:q34:release"],
      bounded_limit: 5,
      read_only: true,
      review_required: true,
    },
  };
}

describe("NewsSignalsDigest", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useBackendTruthMutationBinding).mockReturnValue(binding);
    apiMocks.loadNewsSignalsSummary.mockResolvedValue(summary());
  });

  it("renders selected records independently of the ranked summary page", async () => {
    const value = summary();
    value.projection_items = value.items;
    value.items = [];
    apiMocks.loadNewsSignalsSummary.mockResolvedValue(value);
    render(<NewsSignalsDigest authoritative surface="briefing" />);
    expect(await screen.findByText("Reviewed local release note")).toBeVisible();
    expect(screen.queryByText(/News is unavailable/)).not.toBeInTheDocument();
  });

  it("replaces the Today placeholder with the backend-selected News snapshot", async () => {
    const data = structuredClone(mockControlCenterData);
    data.connection.state = "online";
    data.connection.usingMockData = false;
    data.routeStates["/today"].state = "backend_owned";
    render(<TodaySurface data={data} />);
    expect(await screen.findByText("Reviewed local release note")).toBeVisible();
    expect(screen.queryByText("No sourced news items are attached to the Today read model.")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open News for inspection" })).toHaveAttribute("href", "/news");
    expect(screen.getByText(/Fresh when checked/)).toBeVisible();
    expect(apiMocks.loadNewsSignalsSummary).toHaveBeenCalledWith(binding);
  });

  it("does not read News without an exact backend binding", () => {
    vi.mocked(useBackendTruthMutationBinding).mockReturnValue(null);
    render(<NewsSignalsDigest authoritative surface="today" />);
    expect(screen.getByText(/News is unavailable/)).toBeVisible();
    expect(apiMocks.loadNewsSignalsSummary).not.toHaveBeenCalled();
  });

  it("hides the old snapshot immediately when backend identity changes", async () => {
    const { rerender } = render(<NewsSignalsDigest authoritative surface="today" />);
    expect(await screen.findByText("Reviewed local release note")).toBeVisible();
    apiMocks.loadNewsSignalsSummary.mockReturnValue(new Promise(() => {}));
    vi.mocked(useBackendTruthMutationBinding).mockReturnValue({ ...binding, backendInstanceRef: "backend-instance-ref:q34-restarted" });
    rerender(<NewsSignalsDigest authoritative surface="today" />);
    expect(screen.queryByText("Reviewed local release note")).not.toBeInTheDocument();
    expect(screen.getByText(/Loading reviewed local News/)).toBeVisible();
  });

  it("uses the exact surface projection and preserves backend order", async () => {
    const value = summary();
    value.items.push({ ...value.items[0], signal_ref: "signal-ref:q34:second", title: "Second reviewed note", rank_score: 1 });
    value.today_projection.item_refs = ["signal-ref:q34:second", "signal-ref:q34:release"];
    value.morning_briefing_projection.candidate_refs = ["signal-ref:q34:release"];
    apiMocks.loadNewsSignalsSummary.mockResolvedValue(value);
    const { rerender } = render(<NewsSignalsDigest authoritative surface="today" />);
    await screen.findByText("Second reviewed note");
    expect(screen.getAllByRole("heading").map((item) => item.textContent)).toEqual(["Second reviewed note", "Reviewed local release note"]);
    rerender(<NewsSignalsDigest authoritative surface="briefing" />);
    expect(screen.queryByText("Second reviewed note")).not.toBeInTheDocument();
    expect(screen.getByText(/Candidates need review in News/)).toBeVisible();
    expect(apiMocks.loadNewsSignalsSummary).toHaveBeenCalledTimes(1);
  });

  it.each(["/today", "/briefing", "/morning-briefing"])(
    "wires the readable News handoff through the actual %s route",
    async (route) => {
      const data = structuredClone(mockControlCenterData);
      data.connection.state = "online";
      data.connection.usingMockData = false;
      data.routeStates[route === "/today" ? "/today" : "/briefing"].state = "backend_owned";
      render(renderRoute(route, data));
      expect(await screen.findByText("Reviewed local release note")).toBeVisible();
      expect(screen.getByRole("link", { name: "Open News for inspection" })).toHaveAttribute("href", "/news");
    },
  );

  it("does not read or display News while backend ownership is unavailable", () => {
    render(<NewsSignalsDigest authoritative={false} surface="today" />);
    expect(apiMocks.loadNewsSignalsSummary).not.toHaveBeenCalled();
    expect(screen.getByRole("status")).toHaveTextContent("News is unavailable");
    expect(screen.getByRole("button", { name: "Refresh News" })).toBeDisabled();
  });

  it("discards an in-flight response after ownership is lost", async () => {
    let finish!: (value: NewsSignalsSummary) => void;
    apiMocks.loadNewsSignalsSummary.mockReturnValue(new Promise<NewsSignalsSummary>((resolve) => { finish = resolve; }));
    const { rerender } = render(<NewsSignalsDigest authoritative surface="today" />);
    rerender(<NewsSignalsDigest authoritative={false} surface="today" />);
    await act(async () => { finish(summary()); });
    expect(screen.queryByText("Reviewed local release note")).not.toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("News is unavailable");
  });

  it("hides a loaded snapshot immediately when ownership is lost", async () => {
    const { rerender } = render(<NewsSignalsDigest authoritative surface="today" />);
    await screen.findByText("Reviewed local release note");
    rerender(<NewsSignalsDigest authoritative={false} surface="today" />);
    expect(screen.queryByText("Reviewed local release note")).not.toBeInTheDocument();
  });

  it("shows a fixed unavailable state for a failed refresh instead of stale items or raw errors", async () => {
    render(<NewsSignalsDigest authoritative surface="today" />);
    await screen.findByText("Reviewed local release note");
    apiMocks.loadNewsSignalsSummary.mockRejectedValue(new Error("private detail must not render"));
    fireEvent.click(screen.getByRole("button", { name: "Refresh News" }));
    expect(screen.queryByText("Reviewed local release note")).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("News is unavailable"));
    expect(screen.queryByText(/private detail/)).not.toBeInTheDocument();
  });

  it("refreshes safe-disable and recovery without an automatic write or poll", async () => {
    render(<NewsSignalsDigest authoritative surface="briefing" />);
    await screen.findByText("Reviewed local release note");
    const disabled = summary();
    disabled.status = "blocked_source_unavailable";
    disabled.source_readiness[0].state = "safe_disabled";
    disabled.items = [];
    disabled.today_projection.item_refs = [];
    disabled.morning_briefing_projection.candidate_refs = [];
    apiMocks.loadNewsSignalsSummary.mockResolvedValue(disabled);
    fireEvent.click(screen.getByRole("button", { name: "Refresh News" }));
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("safe-disabled"));
    expect(screen.queryByText("Reviewed local release note")).not.toBeInTheDocument();
    apiMocks.loadNewsSignalsSummary.mockResolvedValue(summary());
    fireEvent.click(screen.getByRole("button", { name: "Refresh News" }));
    expect(await screen.findByText("Reviewed local release note")).toBeVisible();
    expect(apiMocks.loadNewsSignalsSummary).toHaveBeenCalledTimes(3);
  });

  it("distinguishes valid empty eligibility from missing source setup", async () => {
    const value = summary();
    value.morning_briefing_projection.candidate_refs = [];
    apiMocks.loadNewsSignalsSummary.mockResolvedValue(value);
    const { rerender } = render(<NewsSignalsDigest authoritative surface="briefing" />);
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("No News candidates are eligible"));
    rerender(<NewsSignalsDigest authoritative surface="today" />);
    expect(within(screen.getByRole("list")).getByText("Reviewed local release note")).toBeVisible();
    apiMocks.loadNewsSignalsSummary.mockResolvedValue(workspace.summary);
    fireEvent.click(screen.getByRole("button", { name: "Refresh News" }));
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("No reviewed local News sources yet"));
  });

  it("rejects unresolved projection identities instead of claiming an empty stream", async () => {
    const value = summary();
    value.today_projection.item_refs = ["signal-ref:q34:missing"];
    apiMocks.loadNewsSignalsSummary.mockResolvedValue(value);
    render(<NewsSignalsDigest authoritative surface="today" />);
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("News is unavailable"));
  });

  it("rejects duplicate projected identities", async () => {
    const value = summary();
    value.today_projection.item_refs.push("signal-ref:q34:release");
    apiMocks.loadNewsSignalsSummary.mockResolvedValue(value);
    render(<NewsSignalsDigest authoritative surface="today" />);
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("News is unavailable"));
  });

  it("rejects a briefing candidate inconsistent with its source state", async () => {
    const value = summary();
    value.source_readiness[0].state = "safe_disabled";
    apiMocks.loadNewsSignalsSummary.mockResolvedValue(value);
    render(<NewsSignalsDigest authoritative surface="briefing" />);
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("News is unavailable"));
  });

  it("rejects an ineligible briefing candidate", async () => {
    const value = summary();
    value.items[0].briefing_candidate = false;
    apiMocks.loadNewsSignalsSummary.mockResolvedValue(value);
    render(<NewsSignalsDigest authoritative surface="briefing" />);
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("News is unavailable"));
  });
});
