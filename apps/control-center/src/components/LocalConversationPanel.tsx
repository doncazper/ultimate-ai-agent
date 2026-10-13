import { useSyncExternalStore } from "react";

import {
  LOCAL_CONVERSATION_CHARACTER_LIMIT,
  LOCAL_CONVERSATION_MESSAGE_LIMIT,
  requestLocalConversationTurn,
  type LocalConversationMessage,
} from "../api/client";
import type { LocalModelsInspectionStatus } from "../api/types";

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
  models, onReconnect,
}: {
  models: LocalModelsInspectionStatus;
  onReconnect: () => void;
}) {
  const conversation = useSyncExternalStore(subscribe, snapshot);
  const modelId = conversation.modelId || models.selectedModelId || models.modelIds[0] || "";
  const ready = models.state === "ready" && models.modelIds.includes(modelId);
  const canSend = ready && !conversation.sending && Boolean(conversation.draft.trim());

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
    <section className="panel local-conversation" aria-labelledby="local-conversation-heading">
      <div className="panel-heading">
        <h2 id="local-conversation-heading">Talk to your model</h2>
        <span>{conversation.sending ? "Thinking…" : ready ? "Connected locally" : "Connection needed"}</span>
      </div>
      <div className="local-conversation-toolbar">
        <label className="field-label" htmlFor="conversation-model">Local model</label>
        <select
          id="conversation-model" value={modelId}
          disabled={conversation.sending || conversation.messages.length > 0}
          onChange={(event) => replaceConversation({ ...conversation, modelId: event.target.value })}
        >
          {models.modelIds.length === 0 ? <option value="">No model connected</option> : null}
          {models.modelIds.map((id) => <option key={id} value={id}>{id}</option>)}
        </select>
        <button className="secondary-button" type="button" disabled={conversation.sending} onClick={onReconnect}>
          Reconnect
        </button>
        <button
          className="secondary-button" type="button" disabled={conversation.sending}
          onClick={() => replaceConversation(emptyConversation())}
        >
          New chat
        </button>
      </div>
      {!ready ? <p role="status">{models.safeMessage}</p> : null}
      <div className="local-conversation-messages" role="log" aria-label="Conversation" aria-live="polite">
        {conversation.messages.length === 0 ? (
          <p className="muted-copy">Ask a question to begin. Only messages in this chat are sent to your local model.</p>
        ) : conversation.messages.map((message, index) => (
          <article className={"local-conversation-message " + message.role} key={index}>
            <strong>{message.role === "user" ? "You" : "Model"}</strong>
            <div>{message.content}</div>
          </article>
        ))}
        {conversation.sending ? <p role="status">Waiting for your local model…</p> : null}
      </div>
      <label className="field-label" htmlFor="conversation-message">Message</label>
      <textarea
        id="conversation-message" rows={4} maxLength={32_000}
        value={conversation.draft} disabled={conversation.sending}
        placeholder="What would you like help with?"
        onChange={(event) => replaceConversation({ ...conversation, draft: event.target.value })}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
            event.preventDefault();
            void send();
          }
        }}
      />
      <div className="decision-button-row">
        <button className="primary-button" type="button" disabled={!canSend} onClick={() => void send()}>
          {conversation.sending ? "Sending…" : "Send"}
        </button>
        <span className="muted-copy">Enter to send · Shift+Enter for a new line</span>
      </div>
      {conversation.notice ? <p role="alert">{conversation.notice}</p> : null}
      <p className="muted-copy">
        This conversation stays in this tab and is lost on reload. Replies are model output, not verified facts.
        No tools, memory writes, or external actions run.
      </p>
    </section>
  );
}
