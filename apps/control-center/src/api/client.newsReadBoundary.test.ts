import { afterEach, describe, expect, it, vi } from "vitest";
import { loadControlCenterData, loadNewsSignalsAdoptionWorkspace } from "./client";
import { workspace } from "../test/newsSignalsAdoptionFixture";

const binding = {
  snapshotRef: "proof-ref:q34:read-boundary",
  backendRevisionRef: "commit-ref:git:q34-read-boundary",
  backendInstanceRef: "backend-instance-ref:q34-read-boundary",
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("News read ownership and deadline", () => {
  it.each(["missing", "different"])("rejects a %s backend owner on the workspace read", async (posture) => {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (posture === "different") {
      headers["X-UAA-Backend-Revision-Ref"] = binding.backendRevisionRef;
      headers["X-UAA-Backend-Instance-Ref"] = "backend-instance-ref:replacement";
    }
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ data: workspace, ok: true }), { headers })));
    await expect(loadNewsSignalsAdoptionWorkspace({}, binding)).rejects.toThrow();
  });

  it("accepts the workspace only from its expected current backend owner", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ data: workspace, ok: true }), {
      headers: {
        "Content-Type": "application/json",
        "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
        "X-UAA-Backend-Instance-Ref": binding.backendInstanceRef,
      },
    })));
    await expect(loadNewsSignalsAdoptionWorkspace({}, binding)).resolves.toEqual(workspace);
  });

  it("bounds queued handoff reads by one deadline and never starts expired requests", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "performance"] });
    const fetchMock = vi.fn().mockImplementation(() => new Promise(() => {}));
    vi.stubGlobal("fetch", fetchMock);
    const outcome = loadControlCenterData(binding, "news-handoff").then(() => "unexpected", () => "rejected");
    await vi.advanceTimersByTimeAsync(8001);
    expect(await outcome).toBe("rejected");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0]?.[1]?.signal.aborted).toBe(true);
    await vi.advanceTimersByTimeAsync(80_000);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("includes response-body parsing in the same handoff deadline", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "performance"] });
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({
        "X-UAA-Backend-Revision-Ref": binding.backendRevisionRef,
        "X-UAA-Backend-Instance-Ref": binding.backendInstanceRef,
      }),
      json: () => new Promise(() => {}),
    });
    vi.stubGlobal("fetch", fetchMock);
    const outcome = loadControlCenterData(binding, "news-handoff").then(() => "unexpected", () => "rejected");
    await vi.advanceTimersByTimeAsync(8001);
    expect(await outcome).toBe("rejected");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0]?.[1]?.signal.aborted).toBe(true);
  });
});
