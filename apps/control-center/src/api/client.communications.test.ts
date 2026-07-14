import { afterEach, describe, expect, it, vi } from "vitest";
import {
  loadCommunicationsProviders,
  loadCommunicationsReceipt,
  loadCommunicationsRooms,
  loadCommunicationsSessionPosture,
} from "./client";

const provider = {
  schema_version: "uaa-communications.v1",
  provider_ref: "provider-ref:communications:matrix",
  adapter_ref: "adapter-ref:communications:matrix-disabled",
  capability_ref: "capability-ref:communications:matrix-inspection",
  provider_status: "unsupported",
  availability: {
    schema_version: "uaa-capability-availability.v1",
    snapshot_ref: "snapshot-ref:communications:matrix-disabled",
    capability_ref: "capability-ref:communications:matrix-inspection",
    provider_ref: "provider-ref:communications:matrix",
    adapter_ref: "adapter-ref:communications:matrix-disabled",
    catalog_status: "unsupported",
    compatibility_status: "unknown",
    configuration_status: "not_configured",
    health_status: "unknown",
    authority_posture: "blocked",
    resource_status: "unknown",
    cost_posture: "unknown",
    safe_disable_status: "unknown",
    runtime_readiness_status: "unknown",
    declared_or_observed_version_ref: null,
    checked_at: "2026-07-14T00:00:00Z",
    expires_at: null,
    freshness_status: "unknown",
    reason_codes: ["MATRIX_ADAPTER_DECLARATION_ONLY"],
    blocker_codes: ["MATRIX_RUNTIME_DISABLED"],
    evidence_refs: ["evidence-ref:communications:matrix-disabled-contract"],
    probe_refs: [],
    source_ref: "source-ref:communications:matrix-disabled-contract",
    safe_summary: "Matrix runtime is unavailable.",
  },
  reason_codes: ["MATRIX_ADAPTER_DECLARATION_ONLY"],
  blocker_codes: ["MATRIX_RUNTIME_DISABLED"],
  evidence_refs: ["evidence-ref:communications:matrix-disabled-contract"],
  safe_summary: "Matrix runtime is unavailable.",
};

function respond(data: unknown): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({ success: true, data }),
    })),
  );
}

describe("communications API bindings", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("accepts the exact disabled provider availability tuple", async () => {
    respond([provider]);
    const result = await loadCommunicationsProviders();
    expect(result[0]?.availability.authority_posture).toBe("blocked");
    expect(result[0]?.availability.runtime_readiness_status).toBe("unknown");
  });

  it("rejects provider authority drift and content-bearing fields", async () => {
    respond([
      {
        ...provider,
        availability: { ...provider.availability, authority_posture: "lease_required" },
        body: "private message text",
      },
    ]);
    await expect(loadCommunicationsProviders()).rejects.toThrow(
      "failed safe validation",
    );
  });

  it("rejects allowed-key value smuggling and unbounded provider lists", async () => {
    respond([
      {
        ...provider,
        safe_summary: "Contact private.example.ai for the private account.",
      },
    ]);
    await expect(loadCommunicationsProviders()).rejects.toThrow(
      "failed safe validation",
    );

    respond([
      {
        ...provider,
        safe_summary: "api_" + "key=abcdefghijklmnop",
      },
    ]);
    await expect(loadCommunicationsProviders()).rejects.toThrow(
      "failed safe validation",
    );

    respond(Array.from({ length: 17 }, () => provider));
    await expect(loadCommunicationsProviders()).rejects.toThrow(
      "failed safe validation",
    );
  });

  it("accepts only a blocked no-effect session posture", async () => {
    respond({
      provider_ref: "provider-ref:communications:matrix",
      session_ref: "session-ref:communications:matrix:not-configured",
      status: "not_configured",
      freshness: "unknown",
      account_refs: [],
      reason_codes: ["MATRIX_SESSION_DECLARATION_ONLY"],
      blocker_codes: ["MATRIX_ACCOUNT_SESSION_NOT_CONFIGURED"],
      safe_summary: "Matrix account and session runtime are not configured.",
      network_performed: false,
      authentication_performed: false,
      sync_performed: false,
    });
    const result = await loadCommunicationsSessionPosture();
    expect(result.status).toBe("not_configured");
    expect(result.network_performed).toBe(false);
  });

  it("rejects unbracketed IPv6 literals in safe refs", async () => {
    respond({
      provider_ref: "provider-ref:communications:matrix",
      session_ref: "session-ref:communications:matrix:not-configured",
      status: "not_configured",
      freshness: "unknown",
      account_refs: ["account-ref:communications:2001:db8::1"],
      reason_codes: ["MATRIX_SESSION_DECLARATION_ONLY"],
      blocker_codes: ["MATRIX_ACCOUNT_SESSION_NOT_CONFIGURED"],
      safe_summary: "Matrix account and session runtime are not configured.",
      network_performed: false,
      authentication_performed: false,
      sync_performed: false,
    });
    await expect(loadCommunicationsSessionPosture()).rejects.toThrow(
      "failed safe validation",
    );
  });

  it("rejects receipt execution drift", async () => {
    respond({
      receipt_ref: "receipt-ref:communications:contract-inspection",
      operation_ref: "operation-ref:communications:contract-inspection",
      request_ref: "request-ref:communications:contract-inspection",
      provider_ref: "provider-ref:communications:matrix",
      account_ref: null,
      conversation_ref: null,
      outcome: "not_executed",
      occurred_at: "2026-07-14T00:00:00Z",
      reason_codes: [],
      blocker_codes: ["MATRIX_RUNTIME_DISABLED"],
      evidence_refs: ["evidence-ref:communications:contract-inspection"],
      redaction_status: "safe_refs_only",
      safe_summary: "No provider operation was performed.",
      network_performed: true,
      authentication_performed: false,
      message_read_performed: false,
      message_sent: false,
      raw_content_stored: false,
      provider_payload_persisted: false,
      approval_or_lease_minted: false,
    });
    await expect(
      loadCommunicationsReceipt(
        "receipt-ref:communications:contract-inspection",
      ),
    ).rejects.toThrow("failed safe validation");
  });

  it("rejects identity smuggling inside an otherwise valid receipt", async () => {
    respond({
      receipt_ref: "receipt-ref:communications:contract-inspection",
      operation_ref: "operation-ref:communications:@private-user",
      request_ref: "request-ref:communications:contract-inspection",
      provider_ref: "provider-ref:communications:matrix",
      account_ref: null,
      conversation_ref: null,
      outcome: "not_executed",
      occurred_at: "2026-07-14T00:00:00Z",
      reason_codes: [],
      blocker_codes: ["MATRIX_RUNTIME_DISABLED"],
      evidence_refs: ["evidence-ref:communications:contract-inspection"],
      redaction_status: "safe_refs_only",
      safe_summary: "No provider operation was performed.",
      network_performed: false,
      authentication_performed: false,
      message_read_performed: false,
      message_sent: false,
      raw_content_stored: false,
      provider_payload_persisted: false,
      approval_or_lease_minted: false,
    });
    await expect(
      loadCommunicationsReceipt(
        "receipt-ref:communications:contract-inspection",
      ),
    ).rejects.toThrow("failed safe validation");
  });

  it("rejects unsafe room projections even under allowed field names", async () => {
    respond({
      items: [
        {
          conversation_ref: "conversation-ref:communications:test",
          account_ref: "account-ref:communications:test",
          provider_ref: "provider-ref:communications:matrix",
          kind: "room",
          member_refs: ["participant-ref:communications:@private-user"],
          unread_count: 1,
          freshness: "current",
          redaction_status: "safe_refs_only",
          evidence_refs: ["evidence-ref:communications:test"],
        },
      ],
      pagination: {
        page_size: 25,
        returned_count: 1,
        next_cursor_ref: null,
        bounded: true,
      },
      freshness: "current",
      reason_codes: ["COMMUNICATIONS_ROOM_INSPECTION_CONTRACT_AVAILABLE"],
      blocker_codes: ["MATRIX_RUNTIME_DISABLED"],
      safe_summary: "One safe room projection is available.",
      message_read_performed: false,
      raw_content_omitted: true,
    });
    await expect(loadCommunicationsRooms()).rejects.toThrow(
      "failed safe validation",
    );
  });
});
