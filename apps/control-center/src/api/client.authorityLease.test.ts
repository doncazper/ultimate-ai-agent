import { afterEach, describe, expect, it, vi } from "vitest";

import { approveAndIssueAuthorityLease } from "./client";
import { API_ENDPOINTS } from "./endpoints";

describe("approveAndIssueAuthorityLease", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("rejects receipt-free partial capture data with the redacted backend error", async () => {
    const safeMessage =
      "The backend-owned approval was captured, but authority lease persistence was not confirmed; no success is reported.";
    const approvalRef = "approval-ref:authority-lease:test-partial-capture";
    const fetchMock = vi.fn(async () =>
      new Response(
        JSON.stringify({
          ok: true,
          success: false,
          error: {
            code: "APPROVAL_BACKEND_STATE_INVALID",
            category: "security_blocked",
            safe_message: safeMessage,
            retryable: false,
            details_redacted: true,
          },
          data: {
            lease: null,
            approval_captured: true,
            approval_ref: approvalRef,
            approval_scope_ref:
              "approval-scope-ref:authority-lease:test-partial-capture",
            approval_grant_payload_persisted: false,
            backend_approval_state_persisted: true,
            lease_persistence_confirmed: false,
            execution_performed: false,
            unknown_authority_default: "deny",
          },
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    let caught: unknown;
    try {
      await approveAndIssueAuthorityLease(
        {
          lease_issue_request: {
            mode: "ask_before_changes",
            requested_domains: { workspace: ["execute"] },
            decision_reason_ref: "reason-ref:control-center-partial-capture",
            safe_summary:
              "Render a safe partial-capture failure without treating it as a mutation result.",
          },
        },
        {
          snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
          backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
          backendInstanceRef:
            "backend-instance-ref:control-center:22222222222222222222222222222222",
        },
      );
    } catch (error) {
      caught = error;
    }

    expect(caught).toBeInstanceOf(Error);
    const message = caught instanceof Error ? caught.message : "";
    expect(message).toBe(safeMessage);
    expect(message).not.toContain(approvalRef);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(
        API_ENDPOINTS.runtimeAuthorityLeasesApproveAndIssue,
      ),
      expect.objectContaining({ method: "POST" }),
    );
  });
});
