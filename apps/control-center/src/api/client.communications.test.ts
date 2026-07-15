import { afterEach, describe, expect, it, vi } from "vitest";
import {
  loadCommunicationsProviders,
  loadCommunicationsReceipt,
  loadCommunicationsRooms,
  loadCommunicationsSessionPosture,
  loadMatrixCryptoPosture,
  loadMatrixSyncPosture,
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

const partialProvider = {
  ...provider,
  adapter_ref: "adapter-ref:communications:matrix-session-v1",
  capability_ref: "capability-ref:communications:matrix-session-v1",
  provider_status: "partial",
  availability: {
    ...provider.availability,
    snapshot_ref: "snapshot-ref:communications:matrix-session-v1",
    capability_ref: "capability-ref:communications:matrix-session-v1",
    adapter_ref: "adapter-ref:communications:matrix-session-v1",
    catalog_status: "supported",
    compatibility_status: "supported",
    configuration_status: "configured",
    authority_posture: "lease_required",
    resource_status: "available",
    cost_posture: "not_metered",
    safe_disable_status: "inactive",
    declared_or_observed_version_ref: "version-ref:matrix-js-sdk:41-9-0",
    reason_codes: ["MATRIX_DISCOVERY_EXACT_LANE_IMPLEMENTED"],
    blocker_codes: ["MATRIX_ACCOUNT_SESSION_NOT_CONFIGURED"],
    evidence_refs: ["evidence-ref:communications:matrix-session-sdk-pin"],
    source_ref: "source-ref:communications:matrix-session-runtime",
    safe_summary: "Matrix discovery and authentication-method inspection are partial.",
  },
  reason_codes: ["MATRIX_DISCOVERY_EXACT_LANE_IMPLEMENTED"],
  blocker_codes: ["MATRIX_ACCOUNT_SESSION_NOT_CONFIGURED"],
  evidence_refs: ["evidence-ref:communications:matrix-session-sdk-pin"],
  safe_summary: "Matrix discovery and authentication-method inspection are partial.",
};

const matrixCryptoPosture = {
  schema_version: "uaa-matrix-crypto-posture.v1",
  posture_ref: "posture-ref:matrix-crypto:adapter-required-v1",
  runtime_status: "adapter_required",
  freshness: "unknown",
  authority_lane_refs: Array.from(
    { length: 17 },
    (_, index) => `authority-lane-ref:matrix-crypto:lane-${index}`,
  ),
  accepted_authority_operation_refs: Array.from(
    { length: 17 },
    (_, index) => `operation-ref:matrix-crypto:accepted-${index}`,
  ),
  live_executor_operation_refs: [],
  blocked_operation_refs: Array.from(
    { length: 17 },
    (_, index) => `operation-ref:matrix-crypto:blocked-${index}`,
  ),
  provider_ref: "provider-ref:communications:matrix",
  runtime_ref: "runtime-ref:matrix-rust-crypto:adapter-required-v1",
  store_backend_ref:
    "crypto-store-backend-ref:matrix:persistent-rust-store-required-v1",
  key_backend_ref:
    "credential-backend-ref:matrix:device-only-keychain-crypto-v1",
  backup_backend_ref:
    "backup-backend-ref:matrix:dedicated-wrapping-key-required-v1",
  reason_refs: ["reason-ref:matrix-crypto:exact-authority-contracts-accepted"],
  blocker_refs: ["blocker-ref:matrix-crypto:persistent-rust-backend-required"],
  evidence_refs: ["evidence-ref:matrix-crypto:authority-contract-tests"],
  single_owner_required: true,
  request_scoped_evaluation_required: true,
  recovery_material_included: false,
  raw_crypto_payload_included: false,
  element_interoperability_status: "external_facility_required",
  desktop_only: true,
  safe_summary:
    "Exact crypto authority exists, while the live executor remains blocked.",
  redaction_status: "safe_refs_only",
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

  it("accepts only the exact partial Matrix session tuple", async () => {
    respond([partialProvider]);
    const result = await loadCommunicationsProviders();
    expect(result[0]?.provider_status).toBe("partial");

    respond([
      {
        ...partialProvider,
        availability: {
          ...partialProvider.availability,
          compatibility_status: "unsupported",
        },
      },
    ]);
    await expect(loadCommunicationsProviders()).rejects.toThrow(
      "failed safe validation",
    );
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

  it("accepts only content-free backend-owned Matrix sync posture", async () => {
    respond({
      schema_version: "uaa-matrix-sync-posture.v1",
      provider_ref: "provider-ref:communications:matrix",
      adapter_ref: "adapter-ref:communications:matrix-sync-v1",
      runtime_status: "configuration_required",
      freshness: "unavailable",
      credential_posture_ref:
        "credential-posture-ref:matrix:one-use-broker-not-enrolled",
      cache_posture_ref:
        "cache-posture-ref:matrix:protected-cache-helper-not-installed",
      authority_lane_refs: [
        "sync-read",
        "timeline-paginate-read",
        "room-state-read",
        "receipt-project-read",
        "typing-project-read",
        "cache-read",
        "cache-write",
        "cache-migrate",
        "cache-purge",
        "cache-key-create",
        "cache-key-rotate",
        "cache-key-delete",
      ].map((name) => `authority-lane-ref:matrix-${name}`),
      concrete_transport_operation_refs: [
        "operation-ref:matrix-sync:sync-read",
        "operation-ref:matrix-sync:timeline-paginate-read",
      ],
      uncomposed_executor_operation_refs: [
        "room_state_read",
        "receipt_project_read",
        "typing_project_read",
        "cache_read",
        "cache_write",
        "cache_migrate",
        "cache_purge",
        "cache_key_create",
        "cache_key_rotate",
        "cache_key_delete",
      ].map((name) => `operation-ref:matrix-sync:${name.replaceAll("_", "-")}`),
      blocker_refs: [
        "blocker-ref:matrix-sync:credential-broker-enrollment-required",
      ],
      evidence_refs: ["evidence-ref:matrix-sync:loopback-tests"],
      safe_summary: "Matrix sync requires local configuration.",
      sync_enabled: false,
      connector_writes_enabled: false,
      message_sends_enabled: false,
      browser_automation_enabled: false,
      encrypted_content_materialization_enabled: false,
      content_untrusted: true,
      not_instruction_authority: true,
      raw_content_included: false,
      desktop_only: true,
    });

    const result = await loadMatrixSyncPosture();
    expect(result.runtime_status).toBe("configuration_required");
    expect(result.sync_enabled).toBe(false);
  });

  it("rejects Matrix sync posture that claims readiness or carries content", async () => {
    respond({
      schema_version: "uaa-matrix-sync-posture.v1",
      provider_ref: "provider-ref:communications:matrix",
      adapter_ref: "adapter-ref:communications:matrix-sync-v1",
      runtime_status: "configuration_required",
      freshness: "unavailable",
      credential_posture_ref:
        "credential-posture-ref:matrix:one-use-broker-not-enrolled",
      cache_posture_ref:
        "cache-posture-ref:matrix:protected-cache-helper-not-installed",
      authority_lane_refs: [
        "sync-read",
        "timeline-paginate-read",
        "room-state-read",
        "receipt-project-read",
        "typing-project-read",
        "cache-read",
        "cache-write",
        "cache-migrate",
        "cache-purge",
        "cache-key-create",
        "cache-key-rotate",
        "cache-key-delete",
      ].map((name) => `authority-lane-ref:matrix-${name}`),
      concrete_transport_operation_refs: [
        "operation-ref:matrix-sync:sync-read",
        "operation-ref:matrix-sync:timeline-paginate-read",
      ],
      uncomposed_executor_operation_refs: [
        "room_state_read",
        "receipt_project_read",
        "typing_project_read",
        "cache_read",
        "cache_write",
        "cache_migrate",
        "cache_purge",
        "cache_key_create",
        "cache_key_rotate",
        "cache_key_delete",
      ].map((name) => `operation-ref:matrix-sync:${name.replaceAll("_", "-")}`),
      blocker_refs: [
        "blocker-ref:matrix-sync:credential-broker-enrollment-required",
      ],
      evidence_refs: ["evidence-ref:matrix-sync:loopback-tests"],
      safe_summary: "Matrix sync requires local configuration.",
      sync_enabled: true,
      connector_writes_enabled: false,
      message_sends_enabled: false,
      browser_automation_enabled: false,
      encrypted_content_materialization_enabled: false,
      content_untrusted: true,
      not_instruction_authority: true,
      raw_content_included: false,
      desktop_only: true,
      body: "private message text",
    });

    await expect(loadMatrixSyncPosture()).rejects.toThrow(
      "failed safe validation",
    );
  });

  it("accepts only a blocked content-free Matrix crypto posture", async () => {
    respond(matrixCryptoPosture);
    const result = await loadMatrixCryptoPosture();
    expect(result.runtime_status).toBe("adapter_required");
    expect(result.authority_lane_refs).toHaveLength(17);
    expect(result.live_executor_operation_refs).toEqual([]);
    expect(result.recovery_material_included).toBe(false);
  });

  it("rejects Matrix crypto readiness drift and recovery material", async () => {
    respond({
      ...matrixCryptoPosture,
      runtime_status: "ready",
      live_executor_operation_refs: [
        "operation-ref:matrix-crypto:verification-confirm",
      ],
      recovery_material_included: true,
    });
    await expect(loadMatrixCryptoPosture()).rejects.toThrow(
      "failed safe validation",
    );
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
