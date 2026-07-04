import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
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

function withProofRunDetail(record: ControlCenterProofRecord): ControlCenterProofRecord {
  const kind = record.proof_kind.replaceAll("_", "-");
  const runRef = record.run_refs[0] ?? "run-ref:proof-test";
  return {
    ...record,
    run_detail: {
      ...record.run_detail!,
      source: "python_core_control_center_proof_run_detail",
      run_detail_ref: `run-detail-ref:proof-test:${kind}`,
      proof_ref: record.proof_ref,
      proof_kind: record.proof_kind,
      run_ref: runRef,
      status: record.status,
      title: record.title,
      safe_summary:
        "Proof test Run Detail ties proof, run, receipt, evidence, approval, rollback, and blocked authority refs.",
      authority_posture: record.authority_posture,
      route_refs: record.route_refs,
      backend_route_refs: [
        ...record.backend_route_refs,
        "GET /control-center/proof/{proof_ref}",
      ],
      related_run_refs: [runRef],
      operator_run_event_refs: [`operator-run-event-ref:proof:${kind}:test`],
      receipt_refs: record.receipt_refs,
      evidence_refs: record.evidence_refs,
      audit_refs: record.audit_refs,
      approval_refs: record.approval_refs,
      rollback_refs: record.rollback_refs,
      safe_disable_refs: record.safe_disable_refs,
      memory_candidate_refs: record.memory_candidate_refs,
      blocked_authority_refs: record.blocked_authority_refs,
      exact_promotion_path_refs: [
        "promotion-path-ref:proof-run-spine:detail-route-parity",
        "promotion-path-ref:proof-run-spine:receipt-evidence-binding",
        "promotion-path-ref:proof-run-spine:rollback-safe-disable-binding",
        "promotion-path-ref:proof-run-spine:cli-inspection-parity",
        `promotion-path-ref:proof-run-spine:${kind}`,
      ],
      next_safe_action: record.next_safe_action,
    },
  };
}

const webProofRecord: ControlCenterProofRecord = withProofRunDetail({
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
});

const proofIndex: ControlCenterProofIndex = {
  ...mockControlCenterData.proofIndex,
  source: "python_core_control_center_proof_index",
  status: "implemented_backend_owned_universal_proof_index",
  backend_owned: true,
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
  safe_url_ref: "http-fetch-url:example-org/path-0000000000000000",
  host_ref: "http-fetch-host:example-org",
  transport_ref: "http-fetch-transport:fake-web-evidence",
  web_access_request_ref: "web-access-request:test",
  web_access_audit_ref: "web-access-audit:test",
  web_access_audit_summary: {
    schema_version: "web-access-audit-summary.v1",
    request_ref: "web-access-request:test",
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
  web_access_gateway_required: true,
  configured_host_allowlist_required: true,
  operator_supplied_host_scope_required: true,
  request_ref_payload_idempotency: true,
  request_ref_idempotency_ref: "idempotency-ref:web-evidence-product-slice:test",
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
  beforeEach(() => {
    vi.clearAllMocks();
  });

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
    expect(screen.getAllByText("Run Detail").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("run-detail-ref:proof-test:web-evidence").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("python_core_control_center_proof_run_detail"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("GET /control-center/proof/{proof_ref}").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText("python scripts/dev/uaa_founder_loop.py inspect-proof"),
    ).toBeInTheDocument();
    expect(screen.getByText("Full Strength Goal")).toBeInTheDocument();
    expect(screen.getByText(/Every action, approval/)).toBeInTheDocument();
    expect(screen.getByText("Repo-Safe Scope")).toBeInTheDocument();
    expect(screen.getByText(/Backend-owned safe refs/)).toBeInTheDocument();
    expect(screen.getByText("Next Safe Action")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /inspect proof web evidence/i }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("web-access-audit:test")).toBeInTheDocument();
    expect(screen.getByText("Public launch status.")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^send$/i }),
    ).not.toBeInTheDocument();
    expect(screen.getByText("configured allowlist")).toBeInTheDocument();
    expect(screen.getByText("GET only")).toBeInTheDocument();
    expect(
      screen.getByText("blocked-state:web-evidence-receipt:browser-automation"),
    ).toBeInTheDocument();
  });

  it("blocks attach when the proof index is not authoritative", () => {
    const mockedSubmit = vi.mocked(submitWebEvidenceAttachment);
    render(<ProofDetailPanel authoritative={false} proofIndex={proofIndex} />);

    const form = screen
      .getByRole("button", { name: /attach preview/i })
      .closest("form");
    expect(form).not.toBeNull();
    fireEvent.submit(form as HTMLFormElement);

    expect(mockedSubmit).not.toHaveBeenCalled();
    expect(screen.getByLabelText("HTTPS URL")).toBeDisabled();
    expect(screen.getByLabelText("Allowed host")).toBeDisabled();
    expect(screen.getByRole("button", { name: /attach preview/i })).toBeDisabled();
    expect(
      screen.getByRole("alert"),
    ).toHaveTextContent("Backend proof is required before attach.");
    expect(
      screen.getAllByText("Backend proof is required before attach.").length,
    ).toBeGreaterThanOrEqual(1);
  });
});
