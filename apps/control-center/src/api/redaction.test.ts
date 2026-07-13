import { describe, expect, it } from "vitest";

import { safeApiErrorMessage } from "./redaction";

const unsafePath = ["", "Users", "private", "project", "file"].join("/");
const unsafePageRef = ["https:", "", "private.example", "page"].join("/");
const providerPayloadKey = ["provider", "payload"].join("_");

describe("safeApiErrorMessage", () => {
  const fallback = "Request failed safely.";

  it("accepts only a bounded backend-designated redacted summary", () => {
    expect(
      safeApiErrorMessage(
        {
          error: {
            safe_message: "The exact request was denied safely.",
            details_redacted: true,
          },
        },
        fallback,
      ),
    ).toBe("The exact request was denied safely.");
    expect(
      safeApiErrorMessage(
        {
          detail: {
            code: "EXACT_REQUEST_DENIED",
            safe_message: "The exact request was denied by policy.",
            raw_payload: "ignored private content",
          },
        },
        fallback,
      ),
    ).toBe("The exact request was denied by policy.");
  });

  it.each([
    { error: { message: "raw prompt: private task body" } },
    {
      error: {
        safe_message: "The request failed.",
        details_redacted: false,
        details: { raw_prompt: "private task body" },
      },
    },
    { detail: [{ input: "provider payload body" }] },
    { error: { safe_message: unsafePath, details_redacted: true } },
    {
      error: {
        safe_message: unsafePageRef,
        details_redacted: true,
      },
    },
    {
      error: {
        safe_message: ["token", "supersecretvalue123"].join("="),
        details_redacted: true,
      },
    },
    {
      error: {
        safe_message: "x".repeat(321),
        details_redacted: true,
      },
    },
  ])("fails closed for unsafe or untrusted error shapes", (payload) => {
    expect(safeApiErrorMessage(payload, fallback)).toBe(fallback);
  });

  it("does not inspect response data, result, details, metadata, or legacy messages", () => {
    const payload = {
      data: { raw_page: "private page body" },
      result: { [providerPayloadKey]: "private provider body" },
      error: {
        safe_message: "A safe operator summary.",
        details_redacted: true,
        message: "raw prompt: private task body",
        details: { local_path: unsafePath },
        metadata: { [providerPayloadKey]: "private provider body" },
      },
    };

    const message = safeApiErrorMessage(payload, fallback);
    expect(message).toBe("A safe operator summary.");
    expect(message).not.toContain("private");
  });
});
