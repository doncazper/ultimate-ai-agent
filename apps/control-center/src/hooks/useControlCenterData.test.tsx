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
  it("reloads and hides the prior snapshot when the truth envelope changes", async () => {
    mocked.load
      .mockResolvedValueOnce(backendData("snapshot one"))
      .mockResolvedValueOnce(backendData("snapshot two"));
    const { result, rerender } = renderHook(
      ({ snapshotRef }) => useControlCenterData(true, snapshotRef),
      { initialProps: { snapshotRef: "proof-ref:truth:one" } },
    );

    await waitFor(() => expect(result.current.status).toBe("ready"));
    expect(result.current.data?.connection.safeMessage).toBe("snapshot one");

    rerender({ snapshotRef: "proof-ref:truth:two" });
    expect(result.current.status).toBe("loading");
    expect(result.current.data).toBeNull();

    await waitFor(() => expect(result.current.status).toBe("ready"));
    expect(result.current.snapshotRef).toBe("proof-ref:truth:two");
    expect(result.current.data?.connection.safeMessage).toBe("snapshot two");
    expect(mocked.load).toHaveBeenCalledTimes(2);
  });

  it("retries the route read models on explicit operator request", async () => {
    mocked.load
      .mockResolvedValueOnce(backendData("initial"))
      .mockResolvedValueOnce(backendData("recovered"));
    const { result } = renderHook(() =>
      useControlCenterData(true, "proof-ref:truth:current"),
    );
    await waitFor(() => expect(result.current.status).toBe("ready"));

    act(() => result.current.retry());

    await waitFor(() =>
      expect(result.current.data?.connection.safeMessage).toBe("recovered"),
    );
    expect(mocked.load).toHaveBeenCalledTimes(2);
  });

});
