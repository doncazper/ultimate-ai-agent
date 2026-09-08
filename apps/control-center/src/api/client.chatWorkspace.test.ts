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


function stubCheckpointReceipt(overrides: Record<string, unknown> = {}) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (_url: string, init?: RequestInit) => {
      const idempotencyRef = new Headers(init?.headers).get(
        "X-UAA-Idempotency-Key",
      );
      const receipt = {
        contract_ref: "contract-ref:chat-content-free-workspace:v1",
        mutation_kind: "draft_checkpoint",
        lifecycle_action: null,
        thread,
        receipt_ref:
          "receipt:chat-workspace:draft_checkpoint:5f614fab2c0aeaf9:revision-1",
        audit_ref:
          "audit:chat-workspace:draft_checkpoint:5f614fab2c0aeaf9:revision-1",
        evidence_ref:
          "evidence-ref:chat-workspace:draft_checkpoint:5f614fab2c0aeaf9:revision-1",
        idempotency_key_ref: idempotencyRef,
        payload_fingerprint_ref: `payload-fingerprint:chat-workspace:${"a".repeat(64)}`,
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
        headers: { "Content-Type": "application/json" },
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
  ])("rejects %s on mutation response", async (_label, overrides) => {
    stubCheckpointReceipt(overrides);

    await expect(
      checkpointChatDraft(
        thread.thread_ref,
        {
          expected_revision: 0,
          draft_present: true,
          draft_character_count: 24,
          draft_fingerprint_ref: thread.draft_fingerprint_ref,
        },
        binding,
      ),
    ).rejects.toThrow("Chat workspace state was not recorded safely.");
  });
});
