import { afterEach, describe, expect, it, vi } from "vitest";
import { loadNewsSignalsSummary } from "./client";


const emptySummary = {
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
  observed_at: "2026-08-22T16:00:00Z",
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
  safe_summary:
    "Backend-owned News and Signals projection from already-redacted local artifacts; external source content remains untrusted.",
  blocked_state_refs: ["blocked-state-ref:q24:no-graduated-news-source"],
  evidence_refs: [
    "evidence-ref:q24:safe-refs-and-bounded-summaries-only",
    "evidence-ref:q24:no-network-auth-model-write-or-action",
  ],
};


afterEach(() => {
  vi.unstubAllGlobals();
});


function stubSummary(value: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      new Response(JSON.stringify({ success: true, data: value }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
}


describe("News and Signals API boundary", () => {
  it("accepts the bounded backend-owned empty state", async () => {
    stubSummary(emptySummary);

    await expect(loadNewsSignalsSummary()).resolves.toEqual(emptySummary);
  });

  it("rejects authority promotion", async () => {
    stubSummary({ ...emptySummary, live_fetch_enabled: true });

    await expect(loadNewsSignalsSummary()).rejects.toThrow(
      "NEWS_SIGNALS_RESPONSE_INVALID",
    );
  });

  it("rejects undeclared raw payload fields", async () => {
    stubSummary({ ...emptySummary, raw_source_content: "hidden payload" });

    await expect(loadNewsSignalsSummary()).rejects.toThrow(
      "NEWS_SIGNALS_RESPONSE_INVALID",
    );
  });
});
