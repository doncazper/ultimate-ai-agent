import { afterEach, describe, expect, it, vi } from "vitest";

import {
  decideGovernedRuntimeInvocation,
  executeGovernedRuntimeInvocation,
  requestGovernedRuntimeCommand,
  requestGovernedRuntimeLocalModelProposal,
  safeDisableGovernedRuntime,
} from "./client";
import { API_ENDPOINTS } from "./endpoints";

const binding = {
  snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
  backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
  backendInstanceRef:
    "backend-instance-ref:control-center:22222222222222222222222222222222",
};

describe("governed runtime Control Center mutations", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("calls only the exact backend mutation routes with idempotency", async () => {
    const requests: Array<{ url: string; init?: RequestInit }> = [];
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      requests.push({ url: String(url), init });
      return new Response(
        JSON.stringify({
          success: true,
          data: {
            record: { invocation_ref: "runtime-invocation-ref:control-test" },
            receipt_ref: "runtime-receipt-ref:control-test",
          },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    await requestGovernedRuntimeLocalModelProposal(
      {
        base_url: "http://127.0.0.1:8080",
        model_ref: "uaa-local-runtime",
        messages: [{ role: "user", content: "transient prompt" }],
        requested_profile: "local-runtime",
        safe_summary: "Use the loopback model as an untrusted proposal.",
        allow_bounded_preview: false,
        max_preview_chars: 0,
        timeout_seconds: 10,
        max_response_bytes: 16000,
        metadata_refs: ["metadata-ref:runtime-control-test"],
      },
      binding,
    );
    await requestGovernedRuntimeCommand(
      {
        intent: "git_status",
        requested_profile: "local-runtime",
        target_refs: ["target-ref:runtime-control-test"],
        safe_summary: "Run the exact read-only status lane.",
        timeout_seconds: 10,
        output_byte_limit: 4096,
        metadata_refs: ["metadata-ref:runtime-control-test"],
      },
      binding,
    );
    const envelope = {
      approval_ref: "approval-ref:runtime-control-test",
      action_envelope_ref: "action-envelope-ref:runtime-control-test",
      exact_scope_ref: "exact-scope-ref:runtime-control-test",
      payload_fingerprint_ref: "payload-fingerprint-ref:runtime-control-test",
      policy_decision_ref: "policy-decision-ref:runtime-control-test",
      adapter_id: "governed-command-runtime",
      command_intent: "focused_pytest" as const,
      rollback_ref: "rollback-ref:runtime-control-test",
      safe_disable_ref: "safe-disable-ref:runtime-control-test",
      safe_disable_posture_ref:
        "safe-disable-posture-ref:runtime-control-test",
    };
    await decideGovernedRuntimeInvocation(
      "runtime-invocation-ref:control-test",
      "approve",
      envelope,
      binding,
    );
    await executeGovernedRuntimeInvocation(
      "runtime-invocation-ref:control-test",
      envelope,
      binding,
    );
    await safeDisableGovernedRuntime(binding);

    expect(requests.map(({ url }) => url)).toEqual([
      expect.stringContaining(API_ENDPOINTS.runtimeLocalModelCall),
      expect.stringContaining(API_ENDPOINTS.runtimeCommandRun),
      expect.stringContaining(
        "/api/runtime/invocations/runtime-invocation-ref%3Acontrol-test/approve",
      ),
      expect.stringContaining(
        "/api/runtime/invocations/runtime-invocation-ref%3Acontrol-test/execute",
      ),
      expect.stringContaining(API_ENDPOINTS.runtimeSafeDisable),
    ]);
    for (const { init } of requests) {
      expect(init?.method).toBe("POST");
      expect(new Headers(init?.headers).get("X-UAA-Idempotency-Key")).toMatch(
        /^idempotency-ref:control-center-governed-runtime:/,
      );
    }
  });

  it("returns a bounded blocked posture without exposing response content", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            success: false,
            data: {
              record: {
                invocation_ref: "runtime-invocation-ref:blocked-test",
              },
              response_preview: "raw model output must not reach the control result",
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    const result = await requestGovernedRuntimeCommand(
      {
        intent: "repo_doctor",
        requested_profile: "operator-approved",
        target_refs: ["target-ref:runtime-blocked-test"],
        safe_summary: "Prepare the exact doctor lane.",
        timeout_seconds: 30,
        output_byte_limit: 4096,
        metadata_refs: ["metadata-ref:runtime-blocked-test"],
      },
      binding,
    );

    expect(result.status).toBe("blocked");
    expect(result.safeMessage).not.toContain("raw model output");
    expect(result).not.toHaveProperty("responsePreview");
  });
});
