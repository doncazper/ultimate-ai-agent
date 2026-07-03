import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { submitWebEvidenceAttachment } from "../api/client";
import type {
  ControlCenterProofIndex,
  ControlCenterProofRecord,
  WebEvidenceProductSliceReceipt,
} from "../api/types";
import { mockControlCenterData } from "../mocks/controlCenterData";
import { ProofDetailPanel } from "./ProofDetailPanel";

vi.mock("../api/client", () => ({
  submitWebEvidenceAttachment: vi.fn(),
}));

const webProofRecord: ControlCenterProofRecord = {
  ...mockControlCenterData.proofIndex.records[0],
  proof_ref: "proof-ref:web-evidence:product-slice",
  proof_kind: "web_evidence",
  status: "implemented_route_ready_no_web_evidence_attached",
  title: "Web Evidence",
  safe_summary:
    "The web evidence product slice route is ready, but no local web evidence receipt has been attached yet.",
  backend_route_refs: ["POST /control-center/web-evidence/attach"],
  blocked_authority_refs: [
    "blocked-state:web-evidence:no-unrestricted-browsing",
    "blocked-state:web-evidence:no-browser-actions",
  ],
};

const proofIndex: ControlCenterProofIndex = {
  ...mockControlCenterData.proofIndex,
  proof_count: 1,
  proof_refs: [webProofRecord.proof_ref],
  records: [webProofRecord],
};

const webEvidenceReceipt: WebEvidenceProductSliceReceipt = {
  schema_version: "control-center-web-evidence-product-slice-receipt.v1",
  contract_ref: "contract-ref:web-evidence-product-slice:v1",
  source: "python_core_web_evidence_product_slice",
  status: "preview_attached_to_founder_loop",
  route_ref: "POST /control-center/web-evidence/attach",
  cli_ref: "python scripts/dev/uaa_founder_loop.py attach-web-evidence",
  request_ref: "web-evidence-request:control-center-test",
  attach_to_ref: "founder-loop:daily-loop",
  attachment_ref: "web-evidence-attachment:test",
  receipt_ref: "receipt:web-evidence-product-slice:test",
  evidence_ref: "evidence-ref:web-evidence-product-slice:test",
  proof_ref: "proof-ref:web-evidence:product-slice",
  preview_ref: "web-evidence-preview:test",
  safe_url_ref: "http-fetch-url:example-org/status",
  host_ref: "http-fetch-host:example-org",
  transport_ref: "http-fetch-transport:fake-web-evidence",
  web_access_request_ref: "web-access-request:test",
  web_access_audit_ref: "web-access-audit:test",
  payload_fingerprint_ref: "payload-fingerprint:web-evidence-product-slice:test",
  status_code: 200,
  content_type: "text/plain",
  redacted_preview: "Public launch status.",
  preview_truncated: false,
  preview_limit_bytes: 2048,
  response_bytes_read: 21,
  redaction_count: 0,
  redaction_posture_ref:
    "redaction-posture:web-evidence:no-sensitive-patterns-detected",
  receipt_refs: ["receipt:web-evidence-product-slice:test"],
  evidence_refs: ["evidence-ref:web-evidence-product-slice:test"],
  audit_refs: ["web-access-audit:test"],
  rollback_refs: ["rollback:web-evidence-product-slice:suppress-local-receipt"],
  safe_disable_refs: ["safe-disable:web-evidence-product-slice:env-and-route-off"],
  blocked_authority_refs: [
    "blocked-state:web-evidence:no-unrestricted-browsing",
    "blocked-state:web-evidence:no-browser-actions",
  ],
  authority_posture:
    "Tier 1 allowlisted HTTPS GET evidence preview through WebAccessGateway.",
  next_safe_action: "Inspect the receipt in Evidence or Proof.",
  safe_refs_only_for_durable_surfaces: true,
  redacted_preview_returned_to_requester: true,
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
  durable_record_ref: "web-evidence-attachment:test",
};

describe("ProofDetailPanel web evidence", () => {
  it("submits web evidence through the backend helper and renders receipt refs", async () => {
    const mockedSubmit = vi.mocked(submitWebEvidenceAttachment);
    mockedSubmit.mockResolvedValueOnce(webEvidenceReceipt);

    render(<ProofDetailPanel authoritative proofIndex={proofIndex} />);

    fireEvent.change(screen.getByLabelText("HTTPS URL"), {
      target: { value: "https://example.org/status" },
    });
    fireEvent.change(screen.getByLabelText("Allowed host"), {
      target: { value: "example.org" },
    });
    fireEvent.click(screen.getByRole("button", { name: /attach preview/i }));

    expect(mockedSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        url: "https://example.org/status",
        allowed_host: "example.org",
        attach_to_ref: "founder-loop:daily-loop",
      }),
    );
    expect(
      await screen.findByText("receipt:web-evidence-product-slice:test"),
    ).toBeInTheDocument();
    expect(screen.getByText("web-access-audit:test")).toBeInTheDocument();
    expect(screen.getByText("Public launch status.")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^send$/i }),
    ).not.toBeInTheDocument();
  });

  it("disables attach when the proof index is not authoritative", () => {
    render(<ProofDetailPanel authoritative={false} proofIndex={proofIndex} />);

    expect(screen.getByRole("button", { name: /attach preview/i })).toBeDisabled();
    expect(
      screen.getByText("Backend proof is required before attach."),
    ).toBeInTheDocument();
  });
});
