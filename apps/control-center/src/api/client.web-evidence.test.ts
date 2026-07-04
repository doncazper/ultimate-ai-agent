import { afterEach, describe, expect, it, vi } from "vitest";
import { submitWebEvidenceAttachment } from "./client";
import type {
  WebEvidenceProductSliceReceipt,
  WebEvidenceProductSliceRequest,
} from "./types";
import { API_ENDPOINTS } from "./endpoints";

const request: WebEvidenceProductSliceRequest = {
  request_ref: "web-evidence-request:client-test",
  url: "https://example.org/status",
  allowed_host: "example.org",
};

const receipt: WebEvidenceProductSliceReceipt = {
  schema_version: "control-center-web-evidence-product-slice-receipt.v1",
  contract_ref: "contract-ref:web-evidence-product-slice:v1",
  source: "python_core_web_evidence_product_slice",
  status: "preview_attached_to_founder_loop",
  route_ref: "POST /control-center/web-evidence/attach",
  cli_ref: "python scripts/dev/uaa_founder_loop.py attach-web-evidence",
  request_ref: "web-evidence-request:client-test",
  attach_to_ref: "founder-loop:daily-loop",
  attachment_ref: "web-evidence-attachment:client-test",
  receipt_ref: "receipt:web-evidence-product-slice:client-test",
  evidence_ref: "evidence-ref:web-evidence-product-slice:client-test",
  proof_ref: "proof-ref:web-evidence:product-slice",
  preview_ref: "web-evidence-preview:client-test",
  safe_url_ref: "http-fetch-url:example-org/path-0000000000000000",
  host_ref: "http-fetch-host:example-org",
  transport_ref: "http-fetch-transport:web-access-gateway-real-world-v1",
  web_access_request_ref: "web-access-request:client-test",
  web_access_audit_ref: "web-access-audit:client-test",
  web_access_audit_summary: {
    schema_version: "web-access-audit-summary.v1",
    request_ref: "web-access-request:client-test",
    safe_url_ref: "http-fetch-url:example-org/path-0000000000000000",
    host_ref: "http-fetch-host:example-org",
    timestamp: "2026-07-03T00:00:00+00:00",
    adapter_kind: "local_fetch",
    network_lane: "tool_runtime_read_only_fetch",
    authority_mode: "read_only",
    risk_class: "low",
    policy_status: "allowed",
    policy_reason_refs: ["policy-reason:web-access:phase-1-read-only-get-allowed"],
    source_metadata_refs: [
      "http-fetch-url:example-org/path-0000000000000000",
      "http-fetch-host:example-org",
      "source-metadata:web-access:content-untrusted",
    ],
    content_untrusted: true,
    raw_url_omitted: true,
    raw_headers_omitted: true,
    raw_body_omitted: true,
  },
  payload_fingerprint_ref: "payload-fingerprint:web-evidence-product-slice:client-test",
  status_code: 200,
  content_type: "text/plain",
  redacted_preview: "Public launch status.",
  preview_truncated: false,
  preview_limit_bytes: 2048,
  response_bytes_read: 21,
  redaction_count: 0,
  redaction_posture_ref:
    "redaction-posture:web-evidence:no-sensitive-patterns-detected",
  receipt_refs: ["receipt:web-evidence-product-slice:client-test"],
  evidence_refs: ["evidence-ref:web-evidence-product-slice:client-test"],
  audit_refs: ["web-access-audit:client-test"],
  rollback_refs: ["rollback:web-evidence-product-slice:suppress-local-receipt"],
  safe_disable_refs: ["safe-disable:web-evidence-product-slice:env-and-route-off"],
  blocked_authority_refs: [
    "blocked-state:web-evidence:no-unrestricted-browsing",
    "blocked-state:web-evidence:no-browser-actions",
    "blocked-state:web-evidence:no-auth-session-state",
    "blocked-state:web-evidence:no-downloads-or-uploads",
    "blocked-state:web-evidence:no-post-put-patch-delete",
    "blocked-state:web-evidence:no-raw-body-persistence",
    "blocked-state:web-evidence:no-context-injection",
    "blocked-state:web-evidence:no-memory-write",
    "blocked-state:web-evidence:no-provider-model-call",
    "blocked-state:web-evidence:no-connector-write",
    "blocked-state:web-evidence:no-production-authority",
  ],
  authority_posture:
    "Tier 1 allowlisted HTTPS GET evidence preview through WebAccessGateway.",
  next_safe_action: "Inspect the receipt in Evidence or Proof.",
  safe_refs_only_for_durable_surfaces: true,
  redacted_preview_returned_to_requester: true,
  web_access_gateway_required: true,
  configured_host_allowlist_required: true,
  operator_supplied_host_scope_required: true,
  request_ref_payload_idempotency: true,
  request_ref_idempotency_ref:
    "idempotency-ref:web-evidence-product-slice:client-test",
  raw_response_body_stored: false,
  raw_headers_stored: false,
  absolute_url_returned: false,
  query_string_returned: false,
  auth_session_state_used: false,
  request_body_sent: false,
  non_get_method_used: false,
  redirect_followed: false,
  download_performed: false,
  browser_automation_performed: false,
  context_injection_performed: false,
  memory_write_performed: false,
  model_call_performed: false,
  connector_write_performed: false,
  action_execution_performed: false,
  production_authority_granted: false,
  replayed: false,
};

describe("submitWebEvidenceAttachment", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends the request ref as the idempotency ref and returns safe receipts", async () => {
    const fetchMock = vi.fn(
      async (_url: string | URL | Request, _init?: RequestInit) =>
        new Response(JSON.stringify({ success: true, data: receipt }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await submitWebEvidenceAttachment(request);
    const [url, init] = fetchMock.mock.calls[0];
    const headers = init?.headers as Record<string, string>;

    expect(result.receipt_ref).toBe(receipt.receipt_ref);
    expect(url).toBe(API_ENDPOINTS.controlCenterWebEvidenceAttach);
    expect(headers["X-UAA-Idempotency-Ref"]).toBe(request.request_ref);
  });

  it("rejects unsuccessful envelopes even when data is present", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            success: false,
            data: receipt,
            error: { message: "Web evidence blocked safely." },
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      ),
    );

    await expect(submitWebEvidenceAttachment(request)).rejects.toThrow(
      "Web evidence blocked safely.",
    );
  });

  it("rejects receipts with denied authority flags", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            success: true,
            data: { ...receipt, download_performed: true },
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      ),
    );

    await expect(submitWebEvidenceAttachment(request)).rejects.toThrow(
      "Web evidence receipt was rejected safely.",
    );
  });
});
