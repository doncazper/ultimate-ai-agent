import { afterEach, describe, expect, it, vi } from "vitest";
import { mockControlCenterData } from "../mocks/controlCenterData";
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

function toBackendPayload(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(toBackendPayload);
  }
  if (typeof value !== "object" || value === null) {
    return value;
  }
  const keyAliases: Record<string, string> = {
    providerPayloadStored: "raw_provider_payload_stored",
    promptStored: "raw_prompt_stored",
    setupApprovalRef: "approval_ref",
    terminalLogStored: "raw_log_stored",
  };
  return Object.fromEntries(
    Object.entries(value).map(([key, nestedValue]) => [
      keyAliases[key] ??
        key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`),
      toBackendPayload(nestedValue),
    ]),
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
        response(toBackendPayload(mockControlCenterData.macosSetupAssistant)),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(loadMacOSSetupAssistantRoute(binding)).resolves.toEqual(
      mockControlCenterData.macosSetupAssistant,
    );
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
      const payload = toBackendPayload(
        mockControlCenterData.macosSetupAssistant,
      ) as { diagnostics: Array<Record<string, unknown>> };
      payload.diagnostics[0][field] = true;
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(payload)));

      await expect(loadMacOSSetupAssistantRoute(binding)).rejects.toThrow(
        "SETUP_ASSISTANT_RESPONSE_INVALID",
      );
    },
  );
});
