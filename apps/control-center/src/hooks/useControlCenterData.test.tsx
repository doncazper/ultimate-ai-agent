import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ControlCenterData } from "../api/types";
import { mockControlCenterData } from "../mocks/controlCenterData";

const mocked = vi.hoisted(() => ({
  load: vi.fn<() => Promise<ControlCenterData>>(),
}));

vi.mock("../api/client", () => ({
  loadControlCenterData: mocked.load,
}));

import { useControlCenterData } from "./useControlCenterData";

function backendData(label: string): ControlCenterData {
  const data = structuredClone(mockControlCenterData) as ControlCenterData;
  data.connection.state = "online";
  data.connection.usingMockData = false;
  data.connection.safeMessage = label;
  data.connection.warnings = [];
  return data;
}

beforeEach(() => {
  mocked.load.mockReset();
});

describe("useControlCenterData", () => {
  it("does not reload every route read model when only the truth snapshot rotates", async () => {
    mocked.load.mockResolvedValueOnce(backendData("snapshot one"));
    const { result, rerender } = renderHook(
      ({ snapshotRef }) =>
        useControlCenterData(true, {
          snapshotRef,
          backendRevisionRef: "commit-ref:git:revision",
          backendInstanceRef:
            "backend-instance-ref:control-center:11111111111111111111111111111111",
        }),
      { initialProps: { snapshotRef: "proof-ref:truth:one" } },
    );

    await waitFor(() => expect(result.current.status).toBe("ready"));
    expect(result.current.data?.connection.safeMessage).toBe("snapshot one");

    rerender({ snapshotRef: "proof-ref:truth:two" });
    expect(result.current.status).toBe("ready");
    expect(result.current.data?.connection.safeMessage).toBe("snapshot one");
    expect(result.current.snapshotRef).toBe("proof-ref:truth:one");
    expect(mocked.load).toHaveBeenCalledTimes(1);
  });

  it("hides prior data when backend provenance changes", async () => {
    let resolveSecond: ((value: ControlCenterData) => void) | undefined;
    mocked.load
      .mockResolvedValueOnce(backendData("instance one"))
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveSecond = resolve;
          }),
      );
    const { result, rerender } = renderHook(
      ({ backendInstanceRef }) =>
        useControlCenterData(true, {
          snapshotRef: "proof-ref:truth:current",
          backendRevisionRef: "commit-ref:git:revision",
          backendInstanceRef,
        }),
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

    await waitFor(() => expect(result.current.status).toBe("loading"));
    expect(result.current.data).toBeNull();

    act(() => resolveSecond?.(backendData("instance two")));
    await waitFor(() =>
      expect(result.current.data?.connection.safeMessage).toBe("instance two"),
    );
  });

  it("retries the route read models on explicit operator request", async () => {
    mocked.load
      .mockResolvedValueOnce(backendData("initial"))
      .mockResolvedValueOnce(backendData("recovered"));
    const { result } = renderHook(() =>
      useControlCenterData(true, {
        snapshotRef: "proof-ref:truth:current",
        backendRevisionRef: "commit-ref:git:revision",
        backendInstanceRef:
          "backend-instance-ref:control-center:11111111111111111111111111111111",
      }),
    );
    await waitFor(() => expect(result.current.status).toBe("ready"));

    act(() => result.current.retry());

    await waitFor(() =>
      expect(result.current.data?.connection.safeMessage).toBe("recovered"),
    );
    expect(mocked.load).toHaveBeenCalledTimes(2);
  });

});
