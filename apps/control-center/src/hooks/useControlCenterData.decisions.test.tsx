import { renderHook, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { ControlCenterData } from "../api/types";
import { mockControlCenterData } from "../mocks/controlCenterData";

const mocked = vi.hoisted(() => ({
  loadDecisions: vi.fn<() => Promise<ControlCenterData>>(),
  load: vi.fn<() => Promise<ControlCenterData>>(),
}));

vi.mock("../api/client", () => ({
  loadControlCenterData: mocked.load,
  loadNorthStarDecisionsData: mocked.loadDecisions,
}));

import { useControlCenterData } from "./useControlCenterData";

it("loads only the bounded Decisions contracts for North Star Decisions", async () => {
  const data = structuredClone(mockControlCenterData) as ControlCenterData;
  data.connection.state = "online";
  data.connection.usingMockData = false;
  data.connection.safeMessage = "decisions and authority only";
  data.connection.warnings = [];
  mocked.loadDecisions.mockResolvedValueOnce(data);
  const binding = {
    snapshotRef: "proof-ref:truth:decisions",
    backendRevisionRef: "commit-ref:git:revision",
    backendInstanceRef:
      "backend-instance-ref:control-center:33333333333333333333333333333333",
  };

  const { result } = renderHook(() =>
    useControlCenterData(true, binding, "north-star-decisions"),
  );

  await waitFor(() => expect(result.current.status).toBe("ready"));
  expect(result.current.data?.connection.safeMessage).toBe(
    "decisions and authority only",
  );
  expect(mocked.loadDecisions).toHaveBeenCalledWith(binding);
  expect(mocked.load).not.toHaveBeenCalled();
});
