import { afterEach, describe, expect, it, vi } from "vitest";
import { mockControlCenterData } from "../mocks/controlCenterData";
import { buildCompleteMacOSSetupPayload } from "../test/macosSetupAssistantFixture";
import {
  loadMacOSSetupAssistantRoute,
  type BackendTruthReadBinding,
} from "./client";

const binding: BackendTruthReadBinding = {
  snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
  backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
  backendInstanceRef: `backend-instance-ref:control-center:${"2".repeat(32)}`,
};

function response(data: unknown) {
  return new Response(JSON.stringify({ success: true, data }), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
      "X-UAA-Backend-Instance-Ref": binding.backendInstanceRef,
    },
  });
}

function completeBackendPayload(): Record<string, unknown> {
  return buildCompleteMacOSSetupPayload(
    mockControlCenterData.macosSetupAssistant,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("loadMacOSSetupAssistantRoute", () => {
  it("loads only the exact bound Setup summary", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        response(completeBackendPayload()),
      );
    vi.stubGlobal("fetch", fetchMock);

    const loaded = await loadMacOSSetupAssistantRoute(binding);
    expect(loaded.planRef).toBe(
      mockControlCenterData.macosSetupAssistant.planRef,
    );
    expect(loaded.steps).toHaveLength(14);
    expect(loaded.approvalEnvelopes).toHaveLength(7);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "/control-center/setup-assistant/summary",
      expect.objectContaining({
        headers: expect.objectContaining({ Accept: "application/json" }),
      }),
    );
  });

  it("fails closed instead of materializing invalid Setup fallback data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(response({ status: "ready" })),
    );

    await expect(loadMacOSSetupAssistantRoute(binding)).rejects.toThrow(
      "SETUP_ASSISTANT_RESPONSE_INVALID",
    );
  });

  it.each(["live_probe_performed", "state_change_performed"])(
    "rejects a complete Setup response with unsafe diagnostic %s",
    async (field) => {
    const payload = completeBackendPayload() as {
      diagnostics: Array<Record<string, unknown>>;
    };
      payload.diagnostics[0][field] = true;
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(payload)));

      await expect(loadMacOSSetupAssistantRoute(binding)).rejects.toThrow(
        "SETUP_ASSISTANT_RESPONSE_INVALID",
      );
    },
  );

  it.each([
    "native_macos_app_ready",
    "setup_question_assistant_enabled",
    "model_output_authoritative",
    "installer_side_effects_enabled",
  ])("rejects a complete Setup response claiming unsafe %s", async (field) => {
    const payload = completeBackendPayload();
    payload[field] = true;
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(payload)));

    await expect(loadMacOSSetupAssistantRoute(binding)).rejects.toThrow(
      "SETUP_ASSISTANT_RESPONSE_INVALID",
    );
  });

  it("rejects unsafe Setup display text before returning route data", async () => {
    const payload = completeBackendPayload() as {
      steps: Array<Record<string, unknown>>;
    };
    payload.steps[0].safe_summary = "Review /Users/operator/private.log";
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(payload)));

    await expect(loadMacOSSetupAssistantRoute(binding)).rejects.toThrow(
      "SETUP_ASSISTANT_RESPONSE_INVALID",
    );
  });
});
