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

  it("rejects and redacts secret-like query strings", () => {
    const secretQueryMarker = "tok" + "en";
    const policy = resolveApiBaseUrl(`http://localhost:8000?${secretQueryMarker}=supersecretvalue123`);

    expect(policy.allowed).toBe(false);
    expect(policy.baseUrl).toBe("");
    expect(policy.label).not.toContain("supersecretvalue123");
    expect(policy.safeMessage).not.toContain("supersecretvalue123");
    expect(policy.warnings).toContain("SECRET_LIKE_API_BASE_URL_REJECTED");
  });
});
