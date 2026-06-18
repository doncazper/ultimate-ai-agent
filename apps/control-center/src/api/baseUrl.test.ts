import { describe, expect, it } from "vitest";
import { resolveApiBaseUrl } from "./baseUrl";

describe("Control Center API base URL policy", () => {
  it("uses a safe relative base URL by default", () => {
    const policy = resolveApiBaseUrl("");

    expect(policy.allowed).toBe(true);
    expect(policy.baseUrl).toBe("");
    expect(policy.label).toBe("relative local API");
    expect(policy.warnings).toEqual([]);
  });

  it("accepts localhost, 127.0.0.1, and loopback IPv6 API bases", () => {
    expect(resolveApiBaseUrl("http://localhost:8000").allowed).toBe(true);
    expect(resolveApiBaseUrl("http://127.0.0.1:8000/").baseUrl).toBe("http://127.0.0.1:8000");
    expect(resolveApiBaseUrl("http://[::1]:8000").allowed).toBe(true);
  });

  it("blocks external absolute API hosts", () => {
    const policy = resolveApiBaseUrl("https://api.example.com");

    expect(policy.allowed).toBe(false);
    expect(policy.baseUrl).toBe("");
    expect(policy.label).toBe("blocked non-local API base");
    expect(policy.warnings).toContain("EXTERNAL_API_BASE_URL_BLOCKED");
  });

  it("blocks public, private LAN, and non-loopback absolute API hosts", () => {
    const blockedHosts = [
      "http://8.8.8.8:8000",
      "http://10.0.0.5:8000",
      "http://172.16.0.2:8000",
      "http://172.31.0.2:8000",
      "http://192.168.1.10:8000",
      "http://control-center.local:8000",
    ];

    for (const host of blockedHosts) {
      const policy = resolveApiBaseUrl(host);
      expect(policy.allowed).toBe(false);
      expect(policy.baseUrl).toBe("");
      expect(policy.label).toBe("blocked non-local API base");
      expect(policy.safeMessage).not.toContain(host);
      expect(policy.warnings).toContain("EXTERNAL_API_BASE_URL_BLOCKED");
    }
  });

  it("blocks API bases with URL credentials", () => {
    const policy = resolveApiBaseUrl("http://user:supersecretvalue123@localhost:8000");

    expect(policy.allowed).toBe(false);
    expect(policy.baseUrl).toBe("");
    expect(policy.label).toBe("blocked secret-like API base");
    expect(policy.safeMessage).not.toContain("supersecretvalue123");
    expect(policy.warnings).toContain("SECRET_LIKE_API_BASE_URL_REJECTED");
  });

  it("rejects and redacts secret-like query strings", () => {
    const secretQueryMarker = "tok" + "en";
    const policy = resolveApiBaseUrl(
      `http://localhost:8000?${secretQueryMarker}=supersecretvalue123`,
    );

    expect(policy.allowed).toBe(false);
    expect(policy.baseUrl).toBe("");
    expect(policy.label).not.toContain("supersecretvalue123");
    expect(policy.safeMessage).not.toContain("supersecretvalue123");
    expect(policy.warnings).toContain("SECRET_LIKE_API_BASE_URL_REJECTED");
  });

  it("rejects broad secret-like query parameter names", () => {
    const blockedParamNames = [
      "api_key",
      "auth",
      "credential",
      "key",
      "password",
      "secret",
      "token",
    ];

    for (const name of blockedParamNames) {
      const policy = resolveApiBaseUrl(`http://127.0.0.1:8000?${name}=supersecretvalue123`);
      expect(policy.allowed).toBe(false);
      expect(policy.baseUrl).toBe("");
      expect(policy.label).toBe("blocked secret-like API base");
      expect(policy.safeMessage).not.toContain("supersecretvalue123");
      expect(policy.warnings).toContain("SECRET_LIKE_API_BASE_URL_REJECTED");
    }
  });
});
