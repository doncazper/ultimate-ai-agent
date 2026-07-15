import assert from "node:assert/strict";
import test from "node:test";

import { executeMatrixAdapter } from "../src/adapter.mjs";

function jsonResponse(value, status = 200) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function discoveryFetch(input, init = {}) {
  const target = new URL(String(input));
  const method = String(init.method || "GET").toUpperCase();
  if (target.pathname === "/.well-known/matrix/client") {
    return Promise.resolve(jsonResponse({ "m.homeserver": { base_url: "http://127.0.0.1:18008" } }));
  }
  if (target.pathname === "/_matrix/client/versions") {
    return Promise.resolve(jsonResponse({ versions: ["v1.11"] }));
  }
  if (target.pathname.endsWith("/login") && method === "GET") {
    return Promise.resolve(jsonResponse({ flows: [{ type: "m.login.password" }, { type: "m.login.sso" }] }));
  }
  throw new Error("UNEXPECTED_MATRIX_TEST_REQUEST");
}

test("discovery returns a safe delegated homeserver observation without crossing the lease-bound origin", async () => {
  const result = await executeMatrixAdapter({
    operation: "discovery_read",
    discovery_origin: "http://127.0.0.1:18008",
    endpoint_class_ref: "endpoint-class-ref:matrix:local-harness",
  }, { fetchImpl: discoveryFetch });
  assert.equal(result.runtime_status, "discovered");
  assert.match(result.homeserver_observation_ref, /^observation-ref:matrix-homeserver:sha256:/);
  assert.match(result.discovery_freshness_ref, /^freshness-ref:matrix-discovery:sha256:/);
  assert.equal(result.versions_ref, undefined);
  const serialized = JSON.stringify(result);
  assert.equal(serialized.includes("base_url"), false);
  assert.equal(serialized.includes("127.0.0.1"), false);
});

test("auth method inspection binds versions, login flows, and current OAuth metadata to one exact origin", async () => {
  const fetchImpl = async (input, init = {}) => {
    const target = new URL(String(input));
    const method = String(init.method || "GET").toUpperCase();
    if (target.pathname === "/_matrix/client/versions") {
      return jsonResponse({ versions: ["v1.15"] });
    }
    if (target.pathname.endsWith("/login") && method === "GET") {
      return jsonResponse({ flows: [{ type: "m.login.password" }] });
    }
    if (target.pathname === "/_matrix/client/v1/auth_metadata") {
      return jsonResponse({
        issuer: "https://auth.example.test/",
        authorization_endpoint: "https://auth.example.test/auth",
        token_endpoint: "https://auth.example.test/token",
        revocation_endpoint: "https://auth.example.test/revoke",
        response_types_supported: ["code"],
        grant_types_supported: ["authorization_code"],
        code_challenge_methods_supported: ["S256"],
      });
    }
    throw new Error("UNEXPECTED_MATRIX_TEST_REQUEST");
  };
  const result = await executeMatrixAdapter({
    operation: "auth_methods_read",
    base_url: "http://127.0.0.1:18008",
    endpoint_class_ref: "endpoint-class-ref:matrix:local-harness",
  }, { fetchImpl });
  assert.equal(result.runtime_status, "ready_for_authentication");
  assert.deepEqual(result.capabilities, {
    credential_auth: true,
    browser_sso: false,
    oauth: true,
  });
  assert.match(result.auth_metadata_ref, /^auth-metadata-ref:matrix-homeserver:sha256:/);
  assert.equal(JSON.stringify(result).includes("auth.example.test"), false);
});

test("discovery rejects path aliases and never probes a delegated homeserver before a new exact request", async () => {
  let calls = 0;
  let lookups = 0;
  const fetchImpl = async (input) => {
    calls += 1;
    const target = new URL(String(input));
    if (target.pathname === "/.well-known/matrix/client") {
      return jsonResponse({ "m.homeserver": { base_url: "https://delegated.example.org" } });
    }
    throw new Error("UNBOUND_DELEGATED_TARGET_PROBED");
  };
  const result = await executeMatrixAdapter({
    operation: "discovery_read",
    discovery_origin: "http://127.0.0.1:18008",
    endpoint_class_ref: "endpoint-class-ref:matrix:local-harness",
  }, {
    fetchImpl,
    lookup: async () => {
      lookups += 1;
      return [{ address: "93.184.216.34", family: 4 }];
    },
  });
  assert.equal(result.runtime_status, "discovered");
  assert.equal(calls, 1);
  assert.equal(lookups, 0);
  await assert.rejects(
    () => executeMatrixAdapter({
      operation: "discovery_read",
      discovery_origin: "http://127.0.0.1:18008/alias",
      endpoint_class_ref: "endpoint-class-ref:matrix:local-harness",
    }, { fetchImpl }),
    /MATRIX_DISCOVERY_ORIGIN_SCOPE_INVALID|MATRIX_TARGET_/,
  );
});

test("implemented read lanes deny sync, room, media, and POST transport drift", async () => {
  let calls = 0;
  const fetchImpl = async () => {
    calls += 1;
    return jsonResponse({});
  };
  const { createBoundedFetch } = await import("../src/target-policy.mjs");
  const discoveryTransport = createBoundedFetch({
    fetchImpl,
    allowHarness: true,
    allowedRequests: ["GET /.well-known/matrix/client"],
  });
  for (const [method, path] of [
    ["GET", "/_matrix/client/v3/sync"],
    ["POST", "/_matrix/client/v3/rooms/room/send/m.room.message/one"],
    ["GET", "/_matrix/media/v3/download/server/media"],
    ["POST", "/.well-known/matrix/client"],
  ]) {
    await assert.rejects(
      () => discoveryTransport(`http://127.0.0.1:18008${path}`, { method }),
      /MATRIX_HTTP_(METHOD|OPERATION_SCOPE)_DENIED/,
    );
  }
  assert.equal(calls, 0);
});

test("all session mutations fail inside the adapter before any dependency is invoked", async () => {
  const blocked = [
    "credential_auth_create",
    "sso_launch",
    "sso_callback_consume",
    "refresh",
    "logout",
    "revoke_all",
    "credential_store_rotate",
    "credential_delete",
  ];
  let dependencyCalls = 0;
  const dependencies = {
    fetchImpl() { dependencyCalls += 1; throw new Error("NETWORK_CALLED"); },
    lookup() { dependencyCalls += 1; throw new Error("DNS_CALLED"); },
    openBrowser() { dependencyCalls += 1; throw new Error("BROWSER_CALLED"); },
    credentialHelper: {
      store() { dependencyCalls += 1; throw new Error("KEYCHAIN_STORE_CALLED"); },
      delete() { dependencyCalls += 1; throw new Error("KEYCHAIN_DELETE_CALLED"); },
    },
  };
  for (const operation of blocked) {
    await assert.rejects(
      () => executeMatrixAdapter({ operation }, dependencies),
      /MATRIX_ADAPTER_OPERATION_BLOCKED_PENDING_AUTHENTICATED_BROKER/,
    );
  }
  assert.equal(dependencyCalls, 0);
});

test("unknown operations fail closed", async () => {
  await assert.rejects(
    () => executeMatrixAdapter({ operation: "sync" }),
    /MATRIX_ADAPTER_OPERATION_UNSUPPORTED/,
  );
});
