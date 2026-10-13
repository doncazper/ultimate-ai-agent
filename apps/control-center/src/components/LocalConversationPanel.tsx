import { useEffect, useRef, useSyncExternalStore, type ReactNode } from "react";

import {
  LOCAL_CONVERSATION_CHARACTER_LIMIT,
  LOCAL_CONVERSATION_MESSAGE_LIMIT,
  requestLocalConversationTurn,
  type LocalConversationMessage,
} from "../api/client";
import type { LocalModelsInspectionStatus } from "../api/types";
import { NorthStarIcon } from "./NorthStarIcon";

// Transient input and returned display text only. The Python gateway owns the
// turn contract, model authorization and safety receipt. Never persist bodies.
interface ConversationDisplay {
  modelId: string;
  messages: LocalConversationMessage[];
  draft: string;
  sending: boolean;
  notice: string;
}

const emptyConversation = (): ConversationDisplay => ({
  modelId: "", messages: [], draft: "", sending: false, notice: "",
});
let tabConversation = emptyConversation();
const listeners = new Set<() => void>();
function replaceConversation(next: ConversationDisplay) {
  tabConversation = next;
  listeners.forEach((listener) => listener());
}
function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}
function snapshot() { return tabConversation; }

export function resetLocalConversationForTests() {
  replaceConversation(emptyConversation());
}

export function LocalConversationPanel({
  models, onReconnect, children,
}: {
  models: LocalModelsInspectionStatus;
  onReconnect: () => void;
  children?: ReactNode;
}) {
  const conversation = useSyncExternalStore(subscribe, snapshot);
  const transcript = useRef<HTMLDivElement>(null);
  const modelId = conversation.modelId || models.selectedModelId || models.modelIds[0] || "";
  const ready = models.state === "ready" && models.modelIds.includes(modelId);
  const canSend = ready && !conversation.sending && Boolean(conversation.draft.trim());
  useEffect(() => {
    if (transcript.current) transcript.current.scrollTop = transcript.current.scrollHeight;
  }, [conversation.messages.length, conversation.sending]);

  async function send() {
    // Synchronous tab-owned lock also covers rapid clicks and route remounts.
    const current = snapshot();
    if (current.sending || !ready || !current.draft.trim()) return;
    const messages: LocalConversationMessage[] = [
      ...current.messages, { role: "user", content: current.draft },
    ];
    if (
      messages.length > LOCAL_CONVERSATION_MESSAGE_LIMIT ||
      messages.reduce((count, message) => count + message.content.length, 0) >
        LOCAL_CONVERSATION_CHARACTER_LIMIT
    ) {
      replaceConversation({ ...current, notice: "This chat is full. Start a new conversation or shorten your message." });
      return;
    }
    replaceConversation({ ...current, modelId, sending: true, notice: "" });
    try {
      const reply = await requestLocalConversationTurn(modelId, messages);
      replaceConversation({
        modelId, messages: [...messages, reply.message], draft: "", sending: false,
        notice: reply.finishReason === "length"
          ? "Reply reached the response limit. You can ask the model to continue."
          : reply.finishReason === "content_filter"
            ? "The model limited this reply." : "",
      });
    } catch (error) {
      replaceConversation({
        ...current, modelId, sending: false,
        notice: error instanceof Error ? error.message : "The turn did not finish. Your message is still here.",
      });
    }
  }

  return (
    <section className="local-conversation" aria-label="Local conversation">
      <div className="local-conversation-toolbar">
        <button
          className="secondary-button" type="button" disabled={conversation.sending}
          onClick={() => replaceConversation(emptyConversation())}
        >
          <NorthStarIcon name="plus" size="lg" /> New chat
        </button>
        <button className="secondary-button" type="button" disabled={conversation.sending} onClick={onReconnect}>
          <NorthStarIcon name="refresh-cw" size="sm" /> Reconnect
        </button>
      </div>
      {!ready ? <p className="chat-connection-notice" role="status">{models.safeMessage}</p> : null}
      <div ref={transcript} className="local-conversation-messages" role="log" aria-label="Conversation" aria-live="polite" tabIndex={0}>
        {conversation.messages.length === 0 ? (
          <div className="chat-empty-state">
            <h1>Talk to your model</h1>
            <p>A clear space to think, ask, and work things through.</p>
          </div>
        ) : conversation.messages.map((message, index) => (
          <article className={"local-conversation-message " + message.role} key={index}>
            <strong>{message.role === "user" ? "You" : "Model"}</strong>
            <div>{message.content}</div>
          </article>
        ))}
        {conversation.sending ? <p className="chat-pending" role="status">Waiting for your local model…</p> : null}
      </div>
      <div className="chat-compose-area">
        {conversation.notice ? <p className="chat-turn-notice" role="alert">{conversation.notice}</p> : null}
        <div className="chat-composer">
          <label className="chat-sr-only" htmlFor="conversation-message">Message</label>
          <textarea
            id="conversation-message" rows={2} maxLength={32_000}
            value={conversation.draft} disabled={conversation.sending}
            placeholder="What would you like help with?"
            aria-describedby="chat-keyboard-hint"
            onChange={(event) => replaceConversation({ ...conversation, draft: event.target.value })}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
                event.preventDefault();
                void send();
              }
            }}
          />
          <div className="chat-composer-controls">
            <div className="chat-model-choice">
              <span className={`chat-connection-dot ${ready ? "ready" : ""}`} aria-hidden="true" />
              <label className="chat-sr-only" htmlFor="conversation-model">Local model</label>
              <select
                id="conversation-model" value={modelId} title={modelId || "No model connected"}
                disabled={conversation.sending || conversation.messages.length > 0}
                onChange={(event) => replaceConversation({ ...conversation, modelId: event.target.value })}
              >
                {models.modelIds.length === 0 ? <option value="">No model connected</option> : null}
                {models.modelIds.map((id) => <option key={id} value={id}>{id === "qwen/qwen3.8-27b" ? "Qwen 3.8 27B" : id}</option>)}
              </select>
              <span className="chat-sr-only">{ready ? "Connected locally" : "Connection needed"}</span>
            </div>
            <span className="chat-keyboard-hint" id="chat-keyboard-hint">
              Enter to send<span className="chat-sr-only"> · Shift+Enter for a new line</span>
            </span>
            <button
              className="chat-send-button" type="button" disabled={!canSend}
              aria-label={conversation.sending ? "Sending…" : "Send"}
              title={conversation.sending ? "Sending…" : "Send"} onClick={() => void send()}
            >
              <NorthStarIcon name={conversation.sending ? "loader-circle" : "send"} size="lg" motion={conversation.sending ? "spin" : "none"} />
            </button>
          </div>
        </div>
        <div className="chat-footer">
          <span>This tab only <span aria-hidden="true">·</span> No tools or external actions</span>
          <details className="chat-details">
            <summary>Details <NorthStarIcon name="chevron-down" size="sm" /></summary>
            <div className="chat-details-content">
              <p>This conversation stays in this tab and is lost on reload. Replies are model output, not verified facts. No tools, memory writes, or external actions run.</p>
              <p>Only messages in this chat are sent to your local model. Start a new chat to switch models.</p>
              {children}
            </div>
          </details>
        </div>
      </div>
    </section>
  );
}
