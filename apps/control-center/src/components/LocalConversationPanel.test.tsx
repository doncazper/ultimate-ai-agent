import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { LocalModelsInspectionStatus } from "../api/types";
import { LocalConversationPanel, resetLocalConversationForTests } from "./LocalConversationPanel";

const api = vi.hoisted(() => ({ requestLocalConversationTurn: vi.fn() }));
vi.mock("../api/client", async (original) => ({
  ...(await original<typeof import("../api/client")>()), ...api,
}));
const ready: LocalModelsInspectionStatus = {
  state: "ready", routeRef: "/v1/models", checkedAt: "2026-10-13T00:00:00Z",
  safeMessage: "Local model ready.", modelIds: ["fixture-local-model"],
  selectedModelId: "fixture-local-model", reasonCodes: ["LOCAL_MODELS_ROUTE_READY"],
};
const reply = {
  modelId: "fixture-local-model", message: { role: "assistant", content: "y".repeat(12) },
  finishReason: "stop",
};
function setup(models = ready) {
  return render(<LocalConversationPanel models={models} onReconnect={vi.fn()} />);
}
function enter(value: string) {
  fireEvent.change(screen.getByLabelText("Message"), { target: { value } });
}
beforeEach(() => {
  resetLocalConversationForTests();
  vi.clearAllMocks();
  api.requestLocalConversationTurn.mockResolvedValue(reply);
});
describe("main local conversation", () => {
  it("keeps safety details reachable without crowding the initial conversation", () => {
    render(<LocalConversationPanel models={ready} onReconnect={vi.fn()}><h2>Diagnostic proof</h2></LocalConversationPanel>);
    expect(screen.getByRole("heading", { name: "Talk to your model" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Diagnostic proof" })).not.toBeVisible();
    fireEvent.click(screen.getByText("Details", { selector: "summary" }));
    expect(screen.getByRole("heading", { name: "Diagnostic proof" })).toBeVisible();
    expect(screen.getByText(/lost on reload/)).toBeVisible();
    expect(api.requestLocalConversationTurn).not.toHaveBeenCalled();
  });
  it("reconnects only on command and uses the real namespaced model value", () => {
    const reconnect = vi.fn();
    render(<LocalConversationPanel models={{ ...ready, selectedModelId: "qwen/qwen3.8-27b", modelIds: ["qwen/qwen3.8-27b"] }} onReconnect={reconnect} />);
    expect(screen.getByLabelText("Local model")).toHaveValue("qwen/qwen3.8-27b");
    expect(screen.getByRole("option", { name: "Qwen 3.8 27B" })).toBeInTheDocument();
    expect(reconnect).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Reconnect" }));
    expect(reconnect).toHaveBeenCalledTimes(1);
    expect(api.requestLocalConversationTurn).not.toHaveBeenCalled();
  });
  it("does not send while an input-method composition is active", () => {
    setup();
    enter("x".repeat(8));
    fireEvent.keyDown(screen.getByLabelText("Message"), { key: "Enter", isComposing: true });
    expect(api.requestLocalConversationTurn).not.toHaveBeenCalled();
  });
  it("does not call a model on mount or while drafting", () => {
    setup();
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    enter("x".repeat(8));
    expect(screen.getByRole("button", { name: "Send" })).toBeEnabled();
    expect(api.requestLocalConversationTurn).not.toHaveBeenCalled();
  });
  it("sends one explicit turn, shows the reply and retains follow-up context", async () => {
    setup();
    enter("x".repeat(8));
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(await screen.findByText(reply.message.content)).toBeInTheDocument();
    expect(screen.getByLabelText("Message")).toHaveValue("");
    enter("z".repeat(6));
    fireEvent.keyDown(screen.getByLabelText("Message"), { key: "Enter" });
    await waitFor(() => expect(api.requestLocalConversationTurn).toHaveBeenCalledTimes(2));
    expect(api.requestLocalConversationTurn.mock.calls[1]).toEqual([
      "fixture-local-model",
      [{ role: "user", content: "x".repeat(8) }, reply.message, { role: "user", content: "z".repeat(6) }],
    ]);
  });
  it("keeps the draft on failure and never retries automatically", async () => {
    api.requestLocalConversationTurn.mockRejectedValue(new Error("Local connection needs attention."));
    setup();
    enter("x".repeat(8));
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Local connection needs attention");
    expect(screen.getByLabelText("Message")).toHaveValue("x".repeat(8));
    expect(api.requestLocalConversationTurn).toHaveBeenCalledTimes(1);
  });
  it("locks pending turns across rapid clicks and route remounts", async () => {
    let finish!: (value: typeof reply) => void;
    api.requestLocalConversationTurn.mockImplementation(() => new Promise((resolve) => { finish = resolve; }));
    const view = setup();
    enter("x".repeat(8));
    const send = screen.getByRole("button", { name: "Send" });
    fireEvent.click(send);
    fireEvent.click(send);
    view.unmount();
    setup();
    expect(screen.getByRole("button", { name: "Sending…" })).toBeDisabled();
    await act(async () => finish(reply));
    expect(await screen.findByText(reply.message.content)).toBeInTheDocument();
    expect(api.requestLocalConversationTurn).toHaveBeenCalledTimes(1);
  });
  it("renders model output as text, not executable markup", async () => {
    const content = "<img src=x onerror=alert(1)>";
    api.requestLocalConversationTurn.mockResolvedValue({ ...reply, message: { role: "assistant", content } });
    setup();
    enter("x".repeat(8));
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(await screen.findByText(content)).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
  it("keeps disconnected chat blocked and Shift+Enter local", () => {
    setup({ ...ready, state: "blocked", modelIds: [], selectedModelId: undefined });
    enter("x".repeat(8));
    fireEvent.keyDown(screen.getByLabelText("Message"), { key: "Enter", shiftKey: true });
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    expect(api.requestLocalConversationTurn).not.toHaveBeenCalled();
  });
  it("new chat clears only this tab's transient conversation", async () => {
    setup();
    enter("x".repeat(8));
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await screen.findByText(reply.message.content);
    fireEvent.click(screen.getByRole("button", { name: "New chat" }));
    expect(screen.queryByText(reply.message.content)).not.toBeInTheDocument();
    expect(screen.getByLabelText("Message")).toHaveValue("");
  });
});
