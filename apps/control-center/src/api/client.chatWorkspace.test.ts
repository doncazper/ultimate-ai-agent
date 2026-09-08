import { afterEach, describe, expect, it, vi } from "vitest";

import { checkpointChatDraft, fetchChatWorkspace } from "./client";
import type { BackendTruthReadBinding } from "./client";


const thread = {
  contract_ref: "contract-ref:chat-content-free-workspace:v1",
  thread_ref: "chat-thread:local-test",
  display_name: "Conversation 1",
  state: "active",
  revision: 1,
  draft_present: true,
  draft_character_count: 24,
  draft_fingerprint_ref:
    "draft-fingerprint-ref:chat:local-a001c0250539fdc1a001c0250539fdc1",
  draft_recovery_state: "metadata_only_reentry_required",
  draft_body_stored: false,
  created_at: "2026-09-07T12:00:00Z",
  updated_at: "2026-09-07T12:01:00Z",
};

const binding: BackendTruthReadBinding = {
  snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
  backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
  backendInstanceRef:
    "backend-instance-ref:control-center:22222222222222222222222222222222",
};

const workspace = {
  schema_version: "chat-content-free-workspace.v1",
  contract_ref: "contract-ref:chat-content-free-workspace:v1",
  source: "python_core_chat_content_free_workspace",
  status: "workspace_ready",
  threads: [thread],
  active_thread_ref: thread.thread_ref,
  route_refs: [
    "GET /control-center/chat/workspace",
    "POST /control-center/chat/threads/{thread_ref}/approval",
    "POST /control-center/chat/threads/{thread_ref}/draft-checkpoint",
    "POST /control-center/chat/threads/{thread_ref}/lifecycle",
  ],
  blocked_state_refs: [
    "blocked-state:chat-workspace:no-draft-body-persistence",
    "blocked-state:chat-workspace:no-model-call",
    "blocked-state:chat-workspace:no-tool-execution",
    "blocked-state:chat-workspace:no-memory-write",
    "blocked-state:chat-workspace:no-connector-write",
    "blocked-state:chat-workspace:no-production-authority",
  ],
  safe_summary: "Conversation metadata is available without draft content.",
  next_safe_action: "Continue the local draft without a model.",
  draft_body_stored: false,
  model_call_enabled: false,
  send_enabled: false,
  tool_execution_enabled: false,
  connector_write_enabled: false,
  production_authority_enabled: false,
};


afterEach(() => {
  vi.unstubAllGlobals();
});


function stubWorkspace(value: unknown) {
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


function stubCheckpointReceipt(
  overrides: Record<string, unknown> = {},
  includeResponseBinding = true,
  expectedThreadRef = thread.thread_ref,
  approvalOverrides: Record<string, unknown> = {},
) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const idempotencyRef = new Headers(init?.headers).get(
        "X-UAA-Idempotency-Key",
      );
      const submitted = JSON.parse(String(init?.body)) as Record<string, unknown>;
      const request = (url.endsWith("/approval")
        ? submitted.draft_checkpoint
        : submitted) as {
        confirmed: true;
        expected_revision: number;
        draft_present: boolean;
        draft_character_count: number;
        draft_fingerprint_ref: string;
        metadata_refs?: string[];
      };
      const canonicalPayload = JSON.stringify({
        confirmed: request.confirmed,
        draft_character_count: request.draft_character_count,
        draft_fingerprint_ref: request.draft_fingerprint_ref,
        draft_present: request.draft_present,
        expected_revision: request.expected_revision,
        metadata_refs: request.metadata_refs ?? [],
        thread_ref: expectedThreadRef,
      });
      const payloadDigest = await globalThis.crypto.subtle.digest(
        "SHA-256",
        new TextEncoder().encode(canonicalPayload),
      );
      const payloadFingerprintRef = `payload-fingerprint:chat-workspace:${Array.from(
        new Uint8Array(payloadDigest),
        (byte) => byte.toString(16).padStart(2, "0"),
      ).join("")}`;
      const approvalDigestBytes = await globalThis.crypto.subtle.digest(
        "SHA-256",
        new TextEncoder().encode(
          JSON.stringify({
            contract_ref: "contract-ref:chat-content-free-workspace:v1",
            idempotency_key_ref: idempotencyRef,
            lifecycle_action: null,
            mutation_kind: "draft_checkpoint",
            payload_fingerprint_ref: payloadFingerprintRef,
            thread_ref: expectedThreadRef,
          }),
        ),
      );
      const approvalSuffix = Array.from(
        new Uint8Array(approvalDigestBytes),
        (byte) => byte.toString(16).padStart(2, "0"),
      )
        .join("")
        .slice(0, 32);
      const threadDigestBytes = await globalThis.crypto.subtle.digest(
        "SHA-256",
        new TextEncoder().encode(expectedThreadRef),
      );
      const threadSuffix = Array.from(
        new Uint8Array(threadDigestBytes),
        (byte) => byte.toString(16).padStart(2, "0"),
      )
        .join("")
        .slice(0, 16);
      const approvalRef = `approval-ref:chat-workspace:sha256:${approvalSuffix}`;
      const responseBindingHeaders: Record<string, string> = includeResponseBinding
        ? {
            "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
            "X-UAA-Backend-Instance-Ref": binding.backendInstanceRef,
          }
        : {};
      if (url.endsWith("/approval")) {
        const approvalReceipt = {
          contract_ref: "contract-ref:chat-content-free-workspace:v1",
          mutation_kind: "draft_checkpoint",
          lifecycle_action: null,
          thread_ref: expectedThreadRef,
          idempotency_key_ref: idempotencyRef,
          payload_fingerprint_ref: payloadFingerprintRef,
          approval_request_ref:
            `approval-request-ref:chat-workspace:sha256:${approvalSuffix}`,
          approval_ref: approvalRef,
          exact_approval_scope_ref:
            `approval-scope-ref:chat-workspace:sha256:${approvalSuffix}`,
          approval_validation_ref:
            `approval-validation-ref:chat-workspace:sha256:${approvalSuffix}`,
          expires_at: "2026-09-07T12:06:00Z",
          exact_scope_granted: true,
          mutation_performed: false,
          raw_draft_received: false,
          ...approvalOverrides,
        };
        return new Response(
          JSON.stringify({ success: true, data: approvalReceipt }),
          {
            status: 200,
            headers: {
              "Content-Type": "application/json",
              ...responseBindingHeaders,
            },
          },
        );
      }
      const receipt = {
        contract_ref: "contract-ref:chat-content-free-workspace:v1",
        mutation_kind: "draft_checkpoint",
        lifecycle_action: null,
        thread: { ...thread, thread_ref: expectedThreadRef },
        receipt_ref:
          `receipt:chat-workspace:draft_checkpoint:${threadSuffix}:revision-1`,
        audit_ref:
          `audit:chat-workspace:draft_checkpoint:${threadSuffix}:revision-1`,
        evidence_ref:
          `evidence-ref:chat-workspace:draft_checkpoint:${threadSuffix}:revision-1`,
        idempotency_key_ref: idempotencyRef,
        payload_fingerprint_ref: payloadFingerprintRef,
        approval_ref: approvalRef,
        exact_approval_scope_ref:
          `approval-scope-ref:chat-workspace:sha256:${approvalSuffix}`,
        approval_validation_ref:
          `approval-validation-ref:chat-workspace:sha256:${approvalSuffix}`,
        safe_summary: "Content-free checkpoint recorded.",
        raw_draft_received: false,
        draft_body_stored: false,
        model_call_performed: false,
        tool_execution_performed: false,
        connector_write_performed: false,
        replayed: false,
        created_at: "2026-09-07T12:01:00Z",
        ...overrides,
      };
      return new Response(JSON.stringify({ success: true, data: receipt }), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          ...responseBindingHeaders,
        },
      });
    }),
  );
}


describe("content-free Chat workspace API boundary", () => {
  it("accepts the exact bounded backend-owned contract", async () => {
    stubWorkspace(workspace);

    await expect(fetchChatWorkspace(null)).resolves.toEqual(workspace);
  });

  it.each([
    ["authority promotion", { ...workspace, send_enabled: true }],
    ["undeclared raw body", { ...workspace, raw_draft_body: "hidden" }],
    [
      "invalid content fingerprint",
      {
        ...workspace,
        threads: [
          {
            ...thread,
            draft_fingerprint_ref: "draft-fingerprint-ref:chat:not-bound",
          },
        ],
      },
    ],
    [
      "active ref rebound to archived state",
      { ...workspace, threads: [{ ...thread, state: "archived" }] },
    ],
    [
      "forged recovery state",
      { ...workspace, threads: [{ ...thread, draft_recovery_state: "empty" }] },
    ],
  ])("rejects %s", async (_label, value) => {
    stubWorkspace(value);

    await expect(fetchChatWorkspace(null)).rejects.toThrow(
      "Chat workspace metadata was rejected safely.",
    );
  });

  it("binds a mutation receipt to the exact thread, revision, and idempotency key", async () => {
    stubCheckpointReceipt();

    await expect(
      checkpointChatDraft(
        thread.thread_ref,
        {
          confirmed: true,
          expected_revision: 0,
          draft_present: true,
          draft_character_count: 24,
          draft_fingerprint_ref: thread.draft_fingerprint_ref,
        },
        binding,
      ),
    ).resolves.toMatchObject({
      thread,
      mutation_kind: "draft_checkpoint",
    });
    const fetchMock = vi.mocked(globalThis.fetch);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(String(fetchMock.mock.calls[0]?.[0])).toContain("/approval");
    const approvalReceiptHeader = new Headers(
      fetchMock.mock.calls[1]?.[1]?.headers,
    ).get("X-UAA-Approval-Ref");
    expect(approvalReceiptHeader).toMatch(
      /^approval-ref:chat-workspace:sha256:[0-9a-f]{32}$/,
    );
  });

  it("keeps idempotency refs bounded for the longest valid thread ref", async () => {
    const longThreadRef = `chat-thread:${"a".repeat(188)}`;
    stubCheckpointReceipt({}, true, longThreadRef);

    await checkpointChatDraft(
      longThreadRef,
      {
        confirmed: true,
        expected_revision: 0,
        draft_present: true,
        draft_character_count: 24,
        draft_fingerprint_ref: thread.draft_fingerprint_ref,
      },
      binding,
    );
    const fetchMock = vi.mocked(globalThis.fetch);
    const headers = new Headers(fetchMock.mock.calls[0]?.[1]?.headers);

    expect(headers.get("X-UAA-Idempotency-Key")?.length).toBeLessThanOrEqual(200);
    expect(headers.get("X-UAA-Idempotency-Key")).toMatch(
      /^idempotency-ref:control-center-chat-draft:[0-9a-f]{32}:[0-9a-f]{32}$/,
    );
  });

  it("binds distinct checkpoint requests to collision-resistant digests", async () => {
    stubCheckpointReceipt();
    const firstRequest = {
      confirmed: true as const,
      expected_revision: 0,
      draft_present: true,
      draft_character_count: 24,
      draft_fingerprint_ref: thread.draft_fingerprint_ref,
    };

    await checkpointChatDraft(thread.thread_ref, firstRequest, binding);
    const fetchMock = vi.mocked(globalThis.fetch);
    const firstKey = new Headers(fetchMock.mock.calls[0]?.[1]?.headers).get(
      "X-UAA-Idempotency-Key",
    );

    await checkpointChatDraft(
      thread.thread_ref,
      {
        ...firstRequest,
        metadata_refs: ["metadata-ref:chat-workspace:distinct-request"],
      },
      binding,
    );
    const secondKey = new Headers(fetchMock.mock.calls[2]?.[1]?.headers).get(
      "X-UAA-Idempotency-Key",
    );

    expect(firstKey).toMatch(
      /^idempotency-ref:control-center-chat-draft:[0-9a-f]{32}:[0-9a-f]{32}$/,
    );
    expect(secondKey).toMatch(
      /^idempotency-ref:control-center-chat-draft:[0-9a-f]{32}:[0-9a-f]{32}$/,
    );
    expect(secondKey).not.toBe(firstKey);
  });

  it("fails closed before approval capture when a strong digest is unavailable", async () => {
    vi.stubGlobal("crypto", {});
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      checkpointChatDraft(
        thread.thread_ref,
        {
          confirmed: true,
          expected_revision: 0,
          draft_present: true,
          draft_character_count: 24,
          draft_fingerprint_ref: thread.draft_fingerprint_ref,
        },
        binding,
      ),
    ).rejects.toThrow("CHAT_WORKSPACE_IDEMPOTENCY_DIGEST_UNAVAILABLE");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it.each([
    [
      "rebound receipt thread digest",
      {
        receipt_ref:
          "receipt:chat-workspace:draft_checkpoint:aaaaaaaaaaaaaaaa:revision-1",
      },
    ],
    ["rebound thread", { thread: { ...thread, thread_ref: "chat-thread:other" } }],
    ["wrong revision", { thread: { ...thread, revision: 2 } }],
    ["wrong idempotency key", { idempotency_key_ref: "idempotency-ref:wrong" }],
    [
      "wrong payload fingerprint",
      {
        payload_fingerprint_ref: `payload-fingerprint:chat-workspace:${"a".repeat(64)}`,
      },
    ],
    [
      "different valid checkpoint metadata",
      { thread: { ...thread, draft_character_count: 23 } },
    ],
  ])("rejects %s on mutation response", async (_label, overrides) => {
    stubCheckpointReceipt(overrides);

    await expect(
      checkpointChatDraft(
        thread.thread_ref,
        {
          confirmed: true,
          expected_revision: 0,
          draft_present: true,
          draft_character_count: 24,
          draft_fingerprint_ref: thread.draft_fingerprint_ref,
        },
        binding,
      ),
    ).rejects.toThrow("Chat workspace state was not recorded safely.");
  });

  it("rejects a rebound approval capture before attempting mutation", async () => {
    stubCheckpointReceipt({}, true, thread.thread_ref, {
      mutation_performed: true,
    });

    await expect(
      checkpointChatDraft(
        thread.thread_ref,
        {
          confirmed: true,
          expected_revision: 0,
          draft_present: true,
          draft_character_count: 24,
          draft_fingerprint_ref: thread.draft_fingerprint_ref,
        },
        binding,
      ),
    ).rejects.toThrow("Chat workspace approval was not captured safely.");
    expect(vi.mocked(globalThis.fetch)).toHaveBeenCalledTimes(1);
  });

  it("rejects a mutation response without exact backend provenance", async () => {
    stubCheckpointReceipt({}, false);

    await expect(
      checkpointChatDraft(
        thread.thread_ref,
        {
          confirmed: true,
          expected_revision: 0,
          draft_present: true,
          draft_character_count: 24,
          draft_fingerprint_ref: thread.draft_fingerprint_ref,
        },
        binding,
      ),
    ).rejects.toThrow("BACKEND_RESPONSE_PROVENANCE_MISMATCH");
  });
});
