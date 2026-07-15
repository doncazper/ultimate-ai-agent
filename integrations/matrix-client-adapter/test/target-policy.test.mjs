import assert from "node:assert/strict";
import test from "node:test";

import {
  createBoundedFetch,
  isForbiddenAddress,
  validateMatrixDelegatedOrigin,
  validateMatrixTarget,
} from "../src/target-policy.mjs";

test("target policy permits public HTTPS and the one exact harness origin", async () => {
  const publicTarget = await validateMatrixTarget("https://matrix.example.org", {
    lookup: async () => [{ address: "93.184.216.34", family: 4 }],
  });
  assert.equal(publicTarget.origin, "https://matrix.example.org");
  const harness = await validateMatrixTarget("http://127.0.0.1:18008/_matrix/client/versions", { allowHarness: true });
  assert.equal(harness.origin, "http://127.0.0.1:18008");
});

test("target origins require canonical ASCII authority and compressed bracketed IPv6", () => {
  assert.equal(validateMatrixDelegatedOrigin("https://xn--mnich-kva.example").origin, "https://xn--mnich-kva.example");
  assert.equal(
    validateMatrixDelegatedOrigin("https://[2606:4700:4700:0:0:0:0:1111]").origin,
    "https://[2606:4700:4700::1111]",
  );
  for (const raw of [
    "https://münich.example",
    "https://faß.de",
    "https://οσ.example",
    "https://a‍b.example",
    "https://%65xample.com",
  ]) {
    assert.throws(() => validateMatrixDelegatedOrigin(raw), /MATRIX_TARGET_HOSTNAME_NONCANONICAL/);
  }
});

test("target policy rejects private, metadata, credentialed, and substituted loopback targets", async () => {
  for (const raw of [
    "http://127.0.0.1:18009",
    "https://127.0.0.1",
    "https://169.254.169.254",
    "https://[64:ff9b::a9fe:a9fe]",
    "https://[64:ff9b:1::a9fe:a9fe]",
    "https://[::7f00:1]",
    "https://user:material@example.org",
    "https://localhost",
  ]) {
    await assert.rejects(() => validateMatrixTarget(raw), /MATRIX_TARGET_/);
  }
  await assert.rejects(
    () => validateMatrixTarget("https://matrix.example.org", {
      lookup: async () => [{ address: "10.0.0.8", family: 4 }],
    }),
    /MATRIX_TARGET_DNS_SCOPE_DENIED/,
  );
  assert.equal(isForbiddenAddress("100.64.0.1"), true);
  assert.equal(isForbiddenAddress("::ffff:127.0.0.1"), true);
  assert.equal(isForbiddenAddress("64:ff9b::a9fe:a9fe"), true);
  assert.equal(isForbiddenAddress("64:ff9b::a00:1"), true);
  assert.equal(isForbiddenAddress("64:ff9b:1::a9fe:a9fe"), true);
  assert.equal(isForbiddenAddress("::a9fe:a9fe"), true);
  assert.equal(isForbiddenAddress("::7f00:1"), true);
  assert.equal(isForbiddenAddress("fec0::1"), true);
  assert.equal(isForbiddenAddress("8.8.8.8"), false);
  assert.equal(isForbiddenAddress("2606:4700:4700::1111"), false);
  for (const address of [
    "64:ff9b::a9fe:a9fe",
    "64:ff9b::a00:1",
    "64:ff9b:1::a9fe:a9fe",
    "::a9fe:a9fe",
    "::7f00:1",
  ]) {
    await assert.rejects(
      () => validateMatrixTarget("https://matrix.example.org", {
        lookup: async () => [{ address, family: 6 }],
      }),
      /MATRIX_TARGET_DNS_SCOPE_DENIED/,
    );
  }
});

test("bounded fetch rejects redirects and disallowed methods", async () => {
  const redirecting = createBoundedFetch({
    fetchImpl: async () => new Response(null, { status: 302, headers: { location: "https://other.example" } }),
    allowHarness: true,
    allowedRequests: ["GET /_matrix/client/versions"],
  });
  await assert.rejects(
    () => redirecting("http://127.0.0.1:18008/_matrix/client/versions"),
    /MATRIX_HTTP_REDIRECT_DENIED/,
  );
  await assert.rejects(
    () => redirecting("http://127.0.0.1:18008/_matrix/client/versions", { method: "DELETE" }),
    /MATRIX_HTTP_METHOD_DENIED/,
  );
  await assert.rejects(
    () => redirecting("http://127.0.0.1:18008/_matrix/client/versions", { method: "POST" }),
    /MATRIX_HTTP_METHOD_DENIED/,
  );
});
