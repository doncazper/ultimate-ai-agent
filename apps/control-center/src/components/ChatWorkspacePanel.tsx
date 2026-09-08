import { useEffect, useMemo, useState } from "react";

import {
  checkpointChatDraft,
  fetchChatWorkspace,
  updateChatThreadLifecycle,
} from "../api/client";
import type {
  ChatThreadLifecycleAction,
  ChatThreadReadModel,
  ChatWorkspaceReadModel,
} from "../api/types";
import { useBackendTruthMutationBinding } from "../backendTruthMutationBinding";


const CHAT_DRAFT_SESSION_KEY = "uaa.chat.content-free-workspace.drafts.v1";
const EMPTY_DRAFT_FINGERPRINT_REF = "draft-fingerprint-ref:chat:empty";
const DEFAULT_THREAD_REF = "chat-thread:local-default";
const CHAT_THREAD_REF_PATTERN =
  /^chat-thread:[A-Za-z0-9][A-Za-z0-9_.:@-]{0,187}$/;
const CHAT_DRAFT_FINGERPRINT_PATTERN =
  /^draft-fingerprint-ref:chat:(?:empty|local-[0-9a-f]{32})$/;
const MAX_SESSION_DRAFTS = 100;

interface SessionDraft {
  body: string;
  fingerprintRef: string;
}


export function ChatWorkspacePanel() {
  const binding = useBackendTruthMutationBinding();
  const [workspace, setWorkspace] = useState<ChatWorkspaceReadModel>();
  const [activeThreadRef, setActiveThreadRef] = useState(DEFAULT_THREAD_REF);
  const [sessionDrafts, setSessionDrafts] = useState<Record<string, SessionDraft>>(
    readSessionDrafts,
  );
  const [search, setSearch] = useState("");
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState(
    "Start here safely. Drafting does not contact a model.",
  );

  useEffect(() => {
    let cancelled = false;
    void fetchChatWorkspace(binding)
      .then((nextWorkspace) => {
        if (!cancelled) {
          setWorkspace(nextWorkspace);
          setActiveThreadRef(
            nextWorkspace.active_thread_ref ?? DEFAULT_THREAD_REF,
          );
        }
      })
      .catch(() => {
        if (!cancelled) {
          setMessage(
            "Conversation history is unavailable. Drafting remains local to this tab.",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [binding]);

  const activeThread = workspace?.threads.find(
    (thread) => thread.thread_ref === activeThreadRef,
  );
  const draftEntry = sessionDrafts[activeThreadRef];
  const draft = draftEntry?.body ?? "";
  const visibleThreads = useMemo(() => {
    const query = search.trim().toLowerCase();
    return (workspace?.threads ?? []).filter(
      (thread) =>
        !query ||
        thread.display_name.toLowerCase().includes(query) ||
        thread.state.includes(query),
    );
  }, [search, workspace]);
  const recoveryLabel = draftRecoveryLabel(
    activeThread,
    draft,
    draftEntry?.fingerprintRef,
  );

  function updateDraft(value: string) {
    const bounded = value.slice(0, 32_000);
    let fingerprintRef = EMPTY_DRAFT_FINGERPRINT_REF;
    if (bounded) {
      try {
        fingerprintRef = newDraftFingerprintRef();
      } catch {
        setSessionDrafts(
          boundSessionDrafts({
            ...sessionDrafts,
            [activeThreadRef]: { body: bounded, fingerprintRef: "" },
          }),
        );
        setMessage(
          "Draft is held in this tab, but secure checkpoint identity is unavailable.",
        );
        return;
      }
    }
    const next = boundSessionDrafts({
      ...sessionDrafts,
      [activeThreadRef]: { body: bounded, fingerprintRef },
    });
    setSessionDrafts(next);
    writeSessionDrafts(next);
    setMessage("Draft is held in this browser tab. Save a safe checkpoint when ready.");
  }

  function startNewConversation() {
    const threadRef = `chat-thread:local-${Date.now().toString(36)}`;
    setActiveThreadRef(threadRef);
    setMessage("New conversation ready. No model or external service was contacted.");
  }

  async function saveCheckpoint() {
    if (pending) {
      return;
    }
    setPending(true);
    try {
      const fingerprint = draftEntry?.fingerprintRef ?? EMPTY_DRAFT_FINGERPRINT_REF;
      if (draft && !CHAT_DRAFT_FINGERPRINT_PATTERN.test(fingerprint)) {
        throw new Error(
          "Secure draft checkpoint identity is unavailable. The draft remains in this tab.",
        );
      }
      await checkpointChatDraft(
        activeThreadRef,
        {
          expected_revision: activeThread?.revision ?? 0,
          draft_present: draft.length > 0,
          draft_character_count: draft.length,
          draft_fingerprint_ref: fingerprint,
          metadata_refs: [
            `metadata-ref:chat-workspace:revision-${activeThread?.revision ?? 0}`,
          ],
        },
        binding,
      );
      const nextWorkspace = await fetchChatWorkspace(binding);
      setWorkspace(nextWorkspace);
      setActiveThreadRef(activeThreadRef);
      setMessage(
        "Draft checkpoint saved without sending or storing the draft body on the server.",
      );
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Draft checkpoint was not recorded safely.",
      );
    } finally {
      setPending(false);
    }
  }

  async function updateLifecycle(
    thread: ChatThreadReadModel,
    action: ChatThreadLifecycleAction,
  ) {
    if (pending) {
      return;
    }
    setPending(true);
    try {
      await updateChatThreadLifecycle(
        thread.thread_ref,
        {
          action,
          expected_revision: thread.revision,
          metadata_refs: [
            `metadata-ref:chat-workspace:revision-${thread.revision}`,
          ],
        },
        binding,
      );
      const nextWorkspace = await fetchChatWorkspace(binding);
      setWorkspace(nextWorkspace);
      if (action === "archive" && thread.thread_ref === activeThreadRef) {
        setActiveThreadRef(
          nextWorkspace.active_thread_ref ?? DEFAULT_THREAD_REF,
        );
      }
      setMessage(
        action === "archive"
          ? "Conversation archived. Its content-free checkpoint remains recoverable."
          : "Conversation recovered into the active rail.",
      );
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Conversation state was not updated safely.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <section
      className="chat-workspace-shell"
      aria-labelledby="chat-workspace-heading"
    >
      <aside className="panel chat-thread-rail" aria-label="Conversation rail">
        <div className="panel-heading">
          <h3 id="chat-workspace-heading">Conversations</h3>
          <span>{workspace?.status === "workspace_ready" ? "saved" : "clean start"}</span>
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={startNewConversation}
        >
          New conversation
        </button>
        <label className="field-label" htmlFor="chat-thread-search">
          Find conversation
        </label>
        <input
          id="chat-thread-search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search saved conversations"
        />
        <div className="chat-thread-list">
          {visibleThreads.map((thread) => (
            <div className="chat-thread-row" key={thread.thread_ref}>
              <button
                className={
                  thread.thread_ref === activeThreadRef
                    ? "chat-thread-button active"
                    : "chat-thread-button"
                }
                type="button"
                onClick={() => setActiveThreadRef(thread.thread_ref)}
              >
                <strong>{thread.display_name}</strong>
                <span>
                  {thread.state === "archived"
                    ? "Archived"
                    : thread.draft_present
                      ? "Draft checkpoint"
                      : "Empty"}
                </span>
              </button>
              <button
                className="secondary-button compact-button"
                type="button"
                disabled={pending}
                onClick={() =>
                  void updateLifecycle(
                    thread,
                    thread.state === "archived" ? "recover" : "archive",
                  )
                }
              >
                {thread.state === "archived" ? "Recover" : "Archive"}
              </button>
            </div>
          ))}
          {visibleThreads.length === 0 ? (
            <p className="muted-copy">No saved conversations match this view.</p>
          ) : null}
        </div>
      </aside>

      <article className="panel chat-draft-workspace">
        <div className="panel-heading">
          <h3>{activeThread?.display_name ?? "New conversation"}</h3>
          <span>private draft</span>
        </div>
        <p>
          Write before a model is ready. The draft body stays in this browser tab;
          the Python core stores only its size, fingerprint, and lifecycle state.
        </p>
        <label className="field-label" htmlFor="chat-draft-body">
          Draft
        </label>
        <textarea
          id="chat-draft-body"
          value={draft}
          maxLength={32_000}
          onChange={(event) => updateDraft(event.target.value)}
          placeholder="What would you like help with?"
          rows={7}
        />
        <div className="chat-draft-status" role="status">
          <span>{recoveryLabel}</span>
          <span>{draft.length.toLocaleString()} characters</span>
        </div>
        <div className="decision-button-row">
          <button
            className="secondary-button"
            type="button"
            disabled={pending || activeThread?.state === "archived"}
            onClick={() => void saveCheckpoint()}
          >
            {pending ? "Saving…" : "Save draft checkpoint"}
          </button>
          <button className="secondary-button" type="button" disabled>
            Send unavailable
          </button>
        </div>
        <p className="muted-copy" role="status">
          {message}
        </p>
        <p className="muted-copy">
          Next: confirm local model readiness below. Saving, archiving, or recovering
          a draft never runs a model, tool, memory write, or connector.
        </p>
      </article>
    </section>
  );
}


function readSessionDrafts(): Record<string, SessionDraft> {
  try {
    const value = window.sessionStorage.getItem(CHAT_DRAFT_SESSION_KEY);
    if (!value) {
      return {};
    }
    const parsed = JSON.parse(value) as unknown;
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return {};
    }
    return Object.fromEntries(
      Object.entries(parsed)
        .slice(0, MAX_SESSION_DRAFTS)
        .filter(
          ([key, draft]) => {
            if (
              !CHAT_THREAD_REF_PATTERN.test(key) ||
              !draft ||
              typeof draft !== "object" ||
              Array.isArray(draft)
            ) {
              return false;
            }
            const record = draft as Record<string, unknown>;
            return (
              Object.keys(record).length === 2 &&
              typeof record.body === "string" &&
              record.body.length <= 32_000 &&
              typeof record.fingerprintRef === "string" &&
              CHAT_DRAFT_FINGERPRINT_PATTERN.test(record.fingerprintRef) &&
              (record.body
                ? record.fingerprintRef !== EMPTY_DRAFT_FINGERPRINT_REF
                : record.fingerprintRef === EMPTY_DRAFT_FINGERPRINT_REF)
            );
          },
        )
        .map(([key, draft]) => [key, draft as SessionDraft]),
    );
  } catch {
    return {};
  }
}


function writeSessionDrafts(drafts: Record<string, SessionDraft>) {
  try {
    window.sessionStorage.setItem(
      CHAT_DRAFT_SESSION_KEY,
      JSON.stringify(boundSessionDrafts(drafts)),
    );
  } catch {
    // The UI still holds the transient draft if session storage is unavailable.
  }
}


function boundSessionDrafts(
  drafts: Record<string, SessionDraft>,
): Record<string, SessionDraft> {
  return Object.fromEntries(Object.entries(drafts).slice(-MAX_SESSION_DRAFTS));
}


function newDraftFingerprintRef(): string {
  const cryptoApi = globalThis.crypto;
  if (!cryptoApi?.getRandomValues) {
    throw new Error("CHAT_DRAFT_FINGERPRINT_IDENTITY_UNAVAILABLE");
  }
  const bytes = new Uint8Array(16);
  cryptoApi.getRandomValues(bytes);
  const suffix = Array.from(bytes, (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
  return `draft-fingerprint-ref:chat:local-${suffix}`;
}


function draftRecoveryLabel(
  thread: ChatThreadReadModel | undefined,
  draft: string,
  fingerprintRef: string | undefined,
): string {
  if (!thread?.draft_present) {
    return draft ? "Unsaved in this tab" : "No saved draft checkpoint";
  }
  if (
    draft &&
    thread.draft_fingerprint_ref === fingerprintRef
  ) {
    return "Draft restored in this tab";
  }
  return "Checkpoint found; draft body must be re-entered on this device";
}
