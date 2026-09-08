import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchChatWorkspace } from "./client";


const thread = {
  contract_ref: "contract-ref:chat-content-free-workspace:v1",
  thread_ref: "chat-thread:local-test",
  display_name: "Conversation 1",
  state: "active",
  revision: 1,
  draft_present: true,
  draft_character_count: 24,
  draft_fingerprint_ref: "draft-fingerprint-ref:chat:local-a001c0250539fdc1",
  draft_recovery_state: "metadata_only_reentry_required",
  draft_body_stored: false,
  created_at: "2026-09-07T12:00:00Z",
  updated_at: "2026-09-07T12:01:00Z",
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
});
