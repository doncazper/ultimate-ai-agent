import { afterEach, describe, expect, it, vi } from "vitest";
import {
  captureNewsSignalsAdoptionApproval,
  commitNewsSignalsAdoptionMutation,
  loadNewsSignalsAdoptionWorkspace,
  previewNewsSignalsAdoptionMutation,
} from "./client";
import type {
  NewsSignalsAdoptionMutationRequest,
  NewsSignalsAdoptionView,
} from "./types";

const summary = {
  schema_version: "uaa-news-signals-read-model.v1" as const,
  contract_ref: "contract-ref:queue-v2-q24-news-signals:v1",
  status: "blocked_no_graduated_source" as const,
  backend_owned: true as const,
  read_only: true as const,
  local_artifact_snapshot_only: true as const,
  external_content_untrusted: true as const,
  live_fetch_enabled: false as const,
  authenticated_source_enabled: false as const,
  background_polling_enabled: false as const,
  model_summarization_enabled: false as const,
  connector_write_enabled: false as const,
  action_authority_granted: false as const,
  observed_at: "2026-09-09T12:00:00Z",
  source_readiness: [],
  items: [],
  freshness_counts: { fresh: 0, stale: 0, unknown: 0 },
  conflicting_claim_refs: [],
  today_projection: {
    projection_ref: "projection-ref:q24:today",
    item_refs: [],
    bounded_limit: 3 as const,
    read_only: true as const,
  },
  morning_briefing_projection: {
    projection_ref: "projection-ref:q24:morning-briefing",
    candidate_refs: [],
    bounded_limit: 5 as const,
    review_required: true as const,
    read_only: true as const,
  },
  safe_summary: "A bounded local News summary for review.",
  blocked_state_refs: ["blocked-state-ref:q24:no-graduated-news-source"],
  evidence_refs: ["evidence-ref:q24:safe-artifacts-only"],
};

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
  summary,
  active_items_page: {
    offset: 0,
    limit: 100,
    total_items: 0,
    returned_items: 0,
    has_previous: false,
    has_next: false,
    search_applied: false,
    items: [],
  },
  preferences: [],
  archived_items: [],
  next_safe_action: "Register the first local redacted artifact source.",
  evidence_refs: ["evidence-ref:q34:local-redacted-intake-only"],
};

const mutation: NewsSignalsAdoptionMutationRequest = {
  action: "register_source",
  expected_revision: 0,
  source_draft: {
    safe_label: "Official source",
    source_kind: "official",
    freshness_ttl_seconds: 86_400,
  },
};

const preview = {
  schema_version: "uaa-news-signals-adoption-preview.v1" as const,
  contract_ref: "contract-ref:queue-v2-q34-news-signals-adoption:v1" as const,
  action: "register_source" as const,
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
  external_network_read_performed: false as const,
  authenticated_source_access_performed: false as const,
  model_call_performed: false as const,
  external_write_performed: false as const,
  production_authority_granted: false as const,
};

const binding = {
  snapshotRef: "backend-truth-ref:test",
  backendRevisionRef: "backend-revision-ref:test",
  backendInstanceRef: "backend-instance-ref:test",
};
const responseHeaders = {
  "Content-Type": "application/json",
  "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
  "X-UAA-Backend-Instance-Ref": binding.backendInstanceRef,
};

afterEach(() => vi.unstubAllGlobals());

describe("News and Signals adoption API", () => {
  it("accepts the exact fail-closed workspace and rejects authority promotion", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ success: true, data: workspace }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ success: true, data: { ...workspace, live_fetch_enabled: true } }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(loadNewsSignalsAdoptionWorkspace()).resolves.toEqual(workspace);
    await expect(loadNewsSignalsAdoptionWorkspace()).rejects.toThrow(
      "NEWS_SIGNALS_ADOPTION_RESPONSE_INVALID",
    );
  });

  it("requests a bounded active-item page and rejects inconsistent page metadata", async () => {
    const invalidPage = {
      ...workspace,
      active_items_page: {
        ...workspace.active_items_page,
        returned_items: 1,
        items: [],
      },
    };
    const requestedPage = {
      ...workspace,
      active_items_page: {
        ...workspace.active_items_page,
        offset: 100,
        has_previous: true,
        search_applied: true,
      },
    };
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ success: true, data: requestedPage }), {
          status: 200,
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ success: true, data: invalidPage }), {
          status: 200,
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      loadNewsSignalsAdoptionWorkspace({
        offset: 100,
        limit: 100,
        searchQuery: "governed systems",
      }),
    ).resolves.toEqual(requestedPage);
    expect(String(fetchMock.mock.calls[0]?.[0])).toContain(
      "offset=100&limit=100&search_query=governed+systems",
    );
    await expect(loadNewsSignalsAdoptionWorkspace()).rejects.toThrow(
      "NEWS_SIGNALS_ADOPTION_RESPONSE_INVALID",
    );
  });

  it("binds preview approval and commit to one idempotent reviewed change", async () => {
    const idempotencyRef = "idempotency-ref:news-signals-adoption-ui:test";
    const approval = {
      schema_version: "uaa-news-signals-adoption-approval.v1",
      approval_ref: preview.approval_ref,
      approval_validation_ref: "approval-decision-ref:q34:test",
      preview_ref: preview.preview_ref,
      idempotency_ref: idempotencyRef,
      expires_at: "2026-09-09T12:05:00Z",
      safe_summary: "One exact local News change is approved.",
    };
    const receipt = {
      schema_version: "uaa-news-signals-adoption-receipt.v1",
      contract_ref: preview.contract_ref,
      action: preview.action,
      target_ref: null,
      source_ref: preview.source_ref,
      signal_ref: null,
      before_revision: 0,
      after_revision: 1,
      idempotency_ref: idempotencyRef,
      payload_fingerprint_ref: preview.payload_fingerprint_ref,
      preview_ref: preview.preview_ref,
      approval_ref: preview.approval_ref,
      approval_validation_ref: approval.approval_validation_ref,
      approval_expires_at: approval.expires_at,
      authority_decision_ref: "authority-decision-ref:q34:test",
      authority_lease_ref: "authority-lease-ref:q34:test",
      receipt_ref: "receipt-ref:q34:test",
      state_ref: "state-ref:q34:one",
      rollback_ref: "rollback-ref:q34:test",
      replayed: false,
      external_network_read_performed: false,
      authenticated_source_access_performed: false,
      model_call_performed: false,
      external_write_performed: false,
      production_authority_granted: false,
      safe_summary: "One exact local News change was persisted.",
    };
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ success: true, data: preview }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ success: true, data: approval }), { status: 200, headers: responseHeaders }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ success: true, data: receipt }), { status: 200, headers: responseHeaders }));
    vi.stubGlobal("fetch", fetchMock);

    const receivedPreview = await previewNewsSignalsAdoptionMutation(
      mutation,
      idempotencyRef,
    );
    await expect(
      captureNewsSignalsAdoptionApproval(
        mutation,
        receivedPreview,
        idempotencyRef,
        binding,
      ),
    ).resolves.toEqual(approval);
    await expect(
      commitNewsSignalsAdoptionMutation(
        mutation,
        receivedPreview,
        idempotencyRef,
        binding,
      ),
    ).resolves.toEqual(receipt);

    expect(fetchMock.mock.calls[1]?.[1]).toMatchObject({
      headers: expect.objectContaining({
        "X-UAA-Operator-Confirmed": "true",
        "X-UAA-Control-Center-Mutation-Binding": "backend-truth.v1",
      }),
    });
  });
});
