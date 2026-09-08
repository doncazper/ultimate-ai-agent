import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { BackendTruthReadBinding } from "../api/client";
import type { MacOSSetupAssistantData } from "../api/types";
import { mockControlCenterData } from "../mocks/controlCenterData";

const mocked = vi.hoisted(() => ({
  load: vi.fn<
    (binding: BackendTruthReadBinding | null) =>
      Promise<MacOSSetupAssistantData>
  >(),
}));

vi.mock("../api/client", () => ({
  loadMacOSSetupAssistantRoute: mocked.load,
}));

import { useMacOSSetupAssistant } from "./useMacOSSetupAssistant";

function binding(
  snapshotRef: string,
  backendInstanceRef =
    "backend-instance-ref:control-center:11111111111111111111111111111111",
): BackendTruthReadBinding {
  return {
    snapshotRef,
    backendRevisionRef: "commit-ref:git:revision",
    backendInstanceRef,
  };
}

beforeEach(() => {
  mocked.load.mockReset();
});

describe("useMacOSSetupAssistant", () => {
  it("keeps ready Setup data when only the truth snapshot rotates", async () => {
    mocked.load.mockResolvedValueOnce(
      mockControlCenterData.macosSetupAssistant,
    );
    const { result, rerender } = renderHook(
      ({ snapshotRef }) =>
        useMacOSSetupAssistant(true, binding(snapshotRef)),
      { initialProps: { snapshotRef: "proof-ref:truth:one" } },
    );

    await waitFor(() => expect(result.current.status).toBe("ready"));
    rerender({ snapshotRef: "proof-ref:truth:two" });

    expect(result.current.status).toBe("ready");
    expect(mocked.load).toHaveBeenCalledTimes(1);
  });

  it("hides prior Setup data when backend provenance changes", async () => {
    let resolveSecond:
      | ((value: MacOSSetupAssistantData) => void)
      | undefined;
    mocked.load
      .mockResolvedValueOnce(mockControlCenterData.macosSetupAssistant)
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveSecond = resolve;
          }),
      );
    const { result, rerender } = renderHook(
      ({ backendInstanceRef }) =>
        useMacOSSetupAssistant(
          true,
          binding("proof-ref:truth:current", backendInstanceRef),
        ),
      {
        initialProps: {
          backendInstanceRef:
            "backend-instance-ref:control-center:11111111111111111111111111111111",
        },
      },
    );
    await waitFor(() => expect(result.current.status).toBe("ready"));

    rerender({
      backendInstanceRef:
        "backend-instance-ref:control-center:22222222222222222222222222222222",
    });

    expect(result.current.status).toBe("loading");
    expect(result.current.data).toBeNull();
    act(() =>
      resolveSecond?.(mockControlCenterData.macosSetupAssistant),
    );
    await waitFor(() => expect(result.current.status).toBe("ready"));
  });
});
