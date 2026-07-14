import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  window.history.replaceState({}, "", "/");
});

describe("Control Center backend policy", () => {
  it("keeps fallback mode explicit for local development", async () => {
    const policy = await import("./runtimePolicy");

    expect(policy.controlCenterBackendMode()).toBe("fallback");
    expect(policy.resolveControlCenterBackendMode("fallback", true)).toBe(
      "strict",
    );
    expect(policy.resolveControlCenterBackendMode(undefined, true)).toBe(
      "strict",
    );
  });

  it("requires a visible failure for fallback data in strict mode", async () => {
    const policy = await import("./runtimePolicy");

    expect(policy.strictBackendDataFailureRequired(true, "strict")).toBe(true);
    expect(policy.strictBackendDataFailureRequired(false, "strict")).toBe(false);
    expect(policy.strictBackendDataFailureRequired(true, "fallback")).toBe(false);
    const failure = new policy.StrictBackendDataError();
    expect(failure.code).toBe(policy.STRICT_BACKEND_ERROR_CODE);
    expect(JSON.stringify(failure)).not.toContain("backend unavailable");
  });

  it("consumes the launcher bearer into memory and removes it from the URL", async () => {
    vi.resetModules();
    const client = await import("./client");
    window.history.replaceState(
      {},
      "",
      "/today?view=focus#uaa-session-bearer=local-session-value&panel=proof",
    );

    expect(client.consumeLocalApiBearerFromLocation()).toBe(true);
    expect(window.location.pathname).toBe("/today");
    expect(window.location.search).toBe("?view=focus");
    expect(window.location.hash).toBe("#panel=proof");
    expect(window.location.href).not.toContain("local-session-value");
  });
});
