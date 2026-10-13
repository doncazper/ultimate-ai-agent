import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  requestLocalConversationTurn as requestBoundTurn, setLocalApiBearerForSession,
  inspectLocalModelsRoute,
  type LocalConversationMessage,
} from "./client";

const modelId = "fixture-local-model";
const binding = {
  snapshotRef: "proof-ref:local-conversation",
  backendRevisionRef: "commit-ref:git:local-conversation",
  backendInstanceRef: "backend-instance-ref:local-conversation",
};
function requestLocalConversationTurn(model: string, history: readonly LocalConversationMessage[]) {
  return requestBoundTurn(model, history, binding);
}
const messages: LocalConversationMessage[] = [{ role: "user", content: "x".repeat(8) }];
function completion() {
  return {
    model: modelId,
    choices: [{ message: { role: "assistant", content: "y".repeat(12) }, finish_reason: "stop" }],
    uaa_safety: {
      model: modelId, message_count: 1, loopback_forward_performed: true,
      tools_enabled: false, functions_enabled: false, streaming_enabled: false,
      raw_prompt_logged: false, memory_written: false, context_injected: false,
      production_authority_granted: false, backend_fields_allowlisted: true,
    },
  };
}
function stubReply(value = completion(), status = 200) {
  const fetcher = vi.fn(async () => new Response(JSON.stringify(value), {
    status, headers: { "Content-Type": "application/json" },
  }));
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}
beforeEach(() => setLocalApiBearerForSession("fixture-session-value"));
afterEach(() => {
  setLocalApiBearerForSession(null);
  vi.unstubAllGlobals();
});
describe("explicit local conversation turn", () => {
  it("uses the existing authenticated gateway once and displays only its assistant text", async () => {
    const fetcher = stubReply();
    expect(await requestLocalConversationTurn(modelId, messages)).toEqual({
      modelId, message: { role: "assistant", content: "y".repeat(12) }, finishReason: "stop",
    });
    expect(fetcher).toHaveBeenCalledTimes(1);
    const [url, init] = fetcher.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/v1/chat/completions");
    expect(new Headers(init.headers).has("Authorization")).toBe(true);
    expect(new Headers(init.headers).get("X-UAA-Expected-Backend-Instance-Ref")).toBe(binding.backendInstanceRef);
    expect(new Headers(init.headers).get("X-UAA-Expected-Backend-Truth-Ref")).toBe(binding.snapshotRef);
    expect(new Headers(init.headers).get("X-UAA-Idempotency-Key"))
      .toMatch(/^idempotency-ref:control-center-chat:/);
    expect(JSON.parse(String(init.body))).toEqual({
      model: modelId, messages, max_tokens: 1024, stream: false,
    });
  });
  it("does not contact any endpoint without a local session bearer", async () => {
    const fetcher = stubReply();
    setLocalApiBearerForSession(null);
    await expect(requestLocalConversationTurn(modelId, messages)).rejects.toThrow(/authenticated local launcher/);
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("requires backend provenance before sending and separates M151 from M164 readiness", async () => {
    const fetcher = stubReply();
    await expect(requestBoundTurn(modelId, messages, null)).rejects.toThrow(/authenticated/);
    expect(fetcher).not.toHaveBeenCalled();
    const models = { data: [{ id: modelId }], uaa_safety: {
      milestone: "M164", loopback_only: true, tools_enabled: false,
      functions_enabled: false, streaming_enabled: false, openwebui_is_agent_brain: false,
    } };
    const headers = {
      "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
      "X-UAA-Backend-Instance-Ref": binding.backendInstanceRef,
    };
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(models), { headers })));
    expect((await inspectLocalModelsRoute(binding)).conversationContract).toBe("m164");
    models.uaa_safety.tools_enabled = true;
    expect((await inspectLocalModelsRoute(binding)).conversationContract).toBe("unavailable");
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({
      data: [{ id: "uaa-safe-local" }], uaa_safety: { milestone_ref: "M151" },
    }), { headers })));
    expect((await inspectLocalModelsRoute(binding)).conversationContract).toBe("mock_only");
  });
  it.each(["missing", "instance", "revision"])("rejects %s model-response binding before readiness", async (invalid) => {
    const headers: Record<string, string> = {
      "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
      "X-UAA-Backend-Instance-Ref": binding.backendInstanceRef,
    };
    if (invalid === "missing") {
      delete headers["X-UAA-Backend-Instance-Ref"];
      delete headers["X-UAA-Backend-Revision-Ref"];
    } else {
      headers[invalid === "instance" ? "X-UAA-Backend-Instance-Ref" : "X-UAA-Backend-Revision-Ref"] = "ref:substituted";
    }
    const readBody = vi.fn();
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, headers: new Headers(headers), json: readBody })));

    const status = await inspectLocalModelsRoute(binding);

    expect(status.state).toBe("unavailable");
    expect(status.modelIds).toEqual([]);
    expect(status.conversationContract).not.toBe("m164");
    expect(readBody).not.toHaveBeenCalled();
  });
  it("never grants conversation readiness to an unbound model-list inspection", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({
      data: [{ id: modelId }], uaa_safety: {
        milestone: "M164", loopback_only: true, tools_enabled: false,
        functions_enabled: false, streaming_enabled: false, openwebui_is_agent_brain: false,
      },
    }))));

    expect((await inspectLocalModelsRoute(null)).conversationContract).toBe("unavailable");
  });
  it.each([401, 403, 422, 429, 500])("keeps HTTP %s errors content-free without retry", async (status) => {
    const reply = completion();
    reply.choices[0].message.content = "private-fixture-marker";
    const fetcher = stubReply(reply, status);
    await expect(requestLocalConversationTurn(modelId, messages)).rejects.not.toThrow("private-fixture-marker");
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it.each([
    "tools_enabled", "functions_enabled", "streaming_enabled", "raw_prompt_logged",
    "memory_written", "context_injected", "production_authority_granted",
  ])("rejects unsafe returned %s posture", async (field) => {
    const reply = completion();
    (reply.uaa_safety as Record<string, unknown>)[field] = true;
    stubReply(reply);
    await expect(requestLocalConversationTurn(modelId, messages)).rejects.toThrow(/contract/);
  });
  it("rejects model substitution and empty or oversized replies", async () => {
    for (const content of ["", " ".repeat(3), "y".repeat(4097)]) {
      const reply = completion();
      reply.choices[0].message.content = content;
      stubReply(reply);
      await expect(requestLocalConversationTurn(modelId, messages)).rejects.toThrow(/contract/);
    }
    stubReply({ ...completion(), model: "different-model" });
    await expect(requestLocalConversationTurn(modelId, messages)).rejects.toThrow(/contract/);
  });
  it("refuses an oversized context before sending", async () => {
    const fetcher = stubReply();
    await expect(requestLocalConversationTurn(modelId, [{ role: "user", content: "x".repeat(64_001) }]))
      .rejects.toThrow(/limit/);
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("does not retry uncertain network outcomes or surface raw transport errors", async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error("private-network-detail"));
    vi.stubGlobal("fetch", fetcher);
    await expect(requestLocalConversationTurn(modelId, messages)).rejects.toThrow(/may still have processed/);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
