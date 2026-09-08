import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { BackendTruthReadBinding } from "../api/client";
import type {
  ChatThreadMutationReceipt,
  ChatThreadReadModel,
  ChatWorkspaceReadModel,
} from "../api/types";
import { BackendTruthMutationBindingProvider } from "../backendTruthMutationBinding";
import { ChatWorkspacePanel } from "./ChatWorkspacePanel";


const apiMocks = vi.hoisted(() => ({
  checkpointChatDraft: vi.fn(),
  fetchChatWorkspace: vi.fn(),
  updateChatThreadLifecycle: vi.fn(),
}));

vi.mock("../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api/client")>()),
  ...apiMocks,
}));

const binding: BackendTruthReadBinding = {
  snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
  backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
  backendInstanceRef:
    "backend-instance-ref:control-center:22222222222222222222222222222222",
};

const thread: ChatThreadReadModel = {
  contract_ref: "contract-ref:chat-content-free-workspace:v1",
  thread_ref: "chat-thread:local-default",
  display_name: "Conversation 1",
  state: "active",
  revision: 1,
  draft_present: true,
  draft_character_count: 24,
  draft_fingerprint_ref:
    "draft-fingerprint-ref:chat:local-a001c0250539fdc1a001c0250539fdc1",
  draft_recovery_state: "metadata_only_reentry_required",
  draft_body_stored: false,
  created_at: "2026-09-08T01:00:00+00:00",
  updated_at: "2026-09-08T01:00:00+00:00",
};

const cleanWorkspace: ChatWorkspaceReadModel = {
  schema_version: "chat-content-free-workspace.v1",
  contract_ref: "contract-ref:chat-content-free-workspace:v1",
  source: "python_core_chat_content_free_workspace",
  status: "safe_demo_ready",
  threads: [],
  active_thread_ref: null,
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
  safe_summary: "Content-free Chat workspace.",
  next_safe_action: "Start a local draft.",
  draft_body_stored: false,
  model_call_enabled: false,
  send_enabled: false,
  tool_execution_enabled: false,
  connector_write_enabled: false,
  production_authority_enabled: false,
};

const savedWorkspace: ChatWorkspaceReadModel = {
  ...cleanWorkspace,
  status: "workspace_ready",
  threads: [thread],
  active_thread_ref: thread.thread_ref,
};

const receipt: ChatThreadMutationReceipt = {
  contract_ref: "contract-ref:chat-content-free-workspace:v1",
  mutation_kind: "draft_checkpoint",
  lifecycle_action: null,
  thread,
  receipt_ref: "receipt:chat-workspace:draft_checkpoint:aaaaaaaaaaaaaaaa:revision-1",
  audit_ref: "audit:chat-workspace:draft_checkpoint:aaaaaaaaaaaaaaaa:revision-1",
  evidence_ref:
    "evidence-ref:chat-workspace:draft_checkpoint:aaaaaaaaaaaaaaaa:revision-1",
  idempotency_key_ref: "idempotency-ref:chat-workspace:test",
  payload_fingerprint_ref: `payload-fingerprint:chat-workspace:${"a".repeat(64)}`,
  approval_ref: `approval-ref:chat-workspace:sha256:${"b".repeat(32)}`,
  exact_approval_scope_ref:
    `approval-scope-ref:chat-workspace:sha256:${"b".repeat(32)}`,
  approval_validation_ref:
    `approval-validation-ref:chat-workspace:sha256:${"b".repeat(32)}`,
  safe_summary: "Content-free checkpoint recorded.",
  raw_draft_received: false,
  draft_body_stored: false,
  model_call_performed: false,
  tool_execution_performed: false,
  connector_write_performed: false,
  replayed: false,
  created_at: "2026-09-08T01:00:00+00:00",
};

function renderPanel() {
  return render(
    <BackendTruthMutationBindingProvider binding={binding}>
      <ChatWorkspacePanel />
    </BackendTruthMutationBindingProvider>,
  );
}

describe("ChatWorkspacePanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.checkpointChatDraft.mockResolvedValue(receipt);
    apiMocks.updateChatThreadLifecycle.mockResolvedValue({
      ...receipt,
      mutation_kind: "lifecycle",
      lifecycle_action: "archive",
    });
  });

  it("supports clean-start drafting and keeps the body in component state", async () => {
    apiMocks.fetchChatWorkspace
      .mockResolvedValueOnce(cleanWorkspace)
      .mockImplementation(async () => {
        const request = apiMocks.checkpointChatDraft.mock.calls.at(-1)?.[1];
        return {
          ...savedWorkspace,
          threads: [
            {
              ...thread,
              draft_fingerprint_ref:
                request?.draft_fingerprint_ref ?? thread.draft_fingerprint_ref,
            },
          ],
        };
      });
    renderPanel();

    expect(await screen.findByText("clean start")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send unavailable" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Draft"), {
      target: { value: "x".repeat(24) },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Save draft checkpoint" }),
    );

    await waitFor(() =>
      expect(apiMocks.checkpointChatDraft).toHaveBeenCalledWith(
        "chat-thread:local-default",
        expect.objectContaining({
          confirmed: true,
          expected_revision: 0,
          draft_present: true,
          draft_character_count: 24,
        }),
        binding,
      ),
    );
    const request = apiMocks.checkpointChatDraft.mock.calls[0][1];
    expect(request).not.toHaveProperty("draft_body");
    expect(
      await screen.findByText(/saved without sending or storing the draft body/i),
    ).toBeInTheDocument();

    expect(await screen.findByDisplayValue("x".repeat(24))).toBeInTheDocument();
    expect(screen.getByText("Draft restored in this tab")).toBeInTheDocument();
  });

  it("keeps an unsaved conversation reachable after starting another", async () => {
    apiMocks.fetchChatWorkspace.mockResolvedValue(cleanWorkspace);
    renderPanel();

    await screen.findByText("clean start");
    fireEvent.change(screen.getByLabelText("Draft"), {
      target: { value: "reachable local draft" },
    });
    fireEvent.click(screen.getByRole("button", { name: "New conversation" }));

    const unsaved = screen.getByRole("button", {
      name: /Unsaved conversation 1.*Unsaved in this tab/i,
    });
    expect(unsaved).toBeInTheDocument();
    expect(screen.getByLabelText("Draft")).toHaveValue("");
    fireEvent.click(unsaved);
    expect(screen.getByLabelText("Draft")).toHaveValue("reachable local draft");
  });

  it("records archive and recovery through the backend-owned lifecycle", async () => {
    const archivedThread = { ...thread, state: "archived" as const, revision: 2 };
    const archivedWorkspace = {
      ...savedWorkspace,
      threads: [archivedThread],
      active_thread_ref: null,
    };
    apiMocks.fetchChatWorkspace
      .mockResolvedValueOnce(savedWorkspace)
      .mockResolvedValueOnce(archivedWorkspace)
      .mockResolvedValue(savedWorkspace);
    apiMocks.updateChatThreadLifecycle
      .mockResolvedValueOnce({
        ...receipt,
        mutation_kind: "lifecycle",
        lifecycle_action: "archive",
        thread: archivedThread,
      })
      .mockResolvedValueOnce({
        ...receipt,
        mutation_kind: "lifecycle",
        lifecycle_action: "recover",
      });
    renderPanel();

    fireEvent.click(await screen.findByRole("button", { name: "Archive" }));
    await waitFor(() =>
      expect(apiMocks.updateChatThreadLifecycle).toHaveBeenCalledWith(
        thread.thread_ref,
        expect.objectContaining({ action: "archive", expected_revision: 1 }),
        binding,
      ),
    );
    fireEvent.click(await screen.findByRole("button", { name: "Recover" }));
    await waitFor(() =>
      expect(apiMocks.updateChatThreadLifecycle).toHaveBeenLastCalledWith(
        thread.thread_ref,
        expect.objectContaining({ action: "recover", expected_revision: 2 }),
        binding,
      ),
    );
  });
});
