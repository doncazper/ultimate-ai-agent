import assert from "node:assert/strict";
import test from "node:test";

import { executeMatrixSyncAdapter } from "../src/sync-adapter.mjs";
import { validateSyncAdapterInput } from "../src/sync-input-contract.mjs";

function input(operation = "sync_read", overrides = {}) {
  return {
    schema_version: "uaa-matrix-sync-adapter-request.v1",
    operation,
    request_fingerprint_ref: "request-fingerprint-ref:matrix-sync:test",
    account_ref: "account-ref:matrix:test",
    session_generation_ref: "session-generation-ref:matrix:test:1",
    base_url: "http://127.0.0.1:18008",
    max_events: 50,
    max_bytes: 1024 * 1024,
    max_duration_ms: 10_000,
    credential_fd: 3,
    room_ids: [],
    event_types: ["m.room.message"],
    allow_harness: true,
    ...overrides,
  };
}

function jsonResponse(value) {
  return new Response(JSON.stringify(value), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

test("one-shot sync is GET-only, offline-presence, and bearer-bound", async () => {
  const calls = [];
  const result = await executeMatrixSyncAdapter(
    input("sync_read", { since_token: "private-sync-token" }),
    "private-access-token",
    {
      fetchImpl: async (target, init) => {
        calls.push({ target: new URL(String(target)), init });
        return jsonResponse({ next_batch: "private-next-token", rooms: {} });
      },
    },
  );
  assert.equal(result.next_batch, "private-next-token");
  assert.equal(calls.length, 1);
  assert.equal(calls[0].target.pathname, "/_matrix/client/v3/sync");
  assert.equal(calls[0].target.searchParams.get("timeout"), "0");
  assert.equal(calls[0].target.searchParams.get("set_presence"), "offline");
  assert.equal(calls[0].target.searchParams.get("since"), "private-sync-token");
  assert.deepEqual(JSON.parse(calls[0].target.searchParams.get("filter")), {
    presence: { types: [] },
    account_data: { types: ["m.direct"] },
    room: {
      timeline: { types: ["m.room.message"], limit: 50 },
      state: { types: ["m.room.message"] },
      ephemeral: { types: ["m.room.message"] },
      account_data: { types: [] },
    },
  });
  assert.equal(new Headers(calls[0].init.headers).get("authorization"), "Bearer private-access-token");
});

test("one-shot sync binds exact room and event filters server-side", async () => {
  const calls = [];
  await executeMatrixSyncAdapter(
    input("sync_read", {
      room_ids: ["!private-room:example.invalid"],
      event_types: ["m.room.encrypted", "m.room.message"],
      max_events: 1,
    }),
    "private-access-token",
    {
      fetchImpl: async (target, init) => {
        calls.push({ target: new URL(String(target)), init });
        return jsonResponse({ next_batch: "private-next-token", rooms: {} });
      },
    },
  );
  assert.deepEqual(JSON.parse(calls[0].target.searchParams.get("filter")), {
    presence: { types: [] },
    account_data: { types: ["m.direct"] },
    room: {
      rooms: ["!private-room:example.invalid"],
      timeline: { types: ["m.room.encrypted", "m.room.message"], limit: 1 },
      state: { types: ["m.room.encrypted", "m.room.message"] },
      ephemeral: { types: ["m.room.encrypted", "m.room.message"] },
      account_data: { types: [] },
    },
  });
});

test("request-specific response byte limit fails closed", async () => {
  await assert.rejects(
    () => executeMatrixSyncAdapter(
      input("sync_read", { max_bytes: 32 }),
      "private-access-token",
      {
        fetchImpl: async () => jsonResponse({
          next_batch: "private-next-token",
          rooms: {},
        }),
      },
    ),
    /MATRIX_HTTP_RESPONSE_TOO_LARGE/,
  );
});

test("pagination binds one encoded room and one backwards page token", async () => {
  const calls = [];
  const result = await executeMatrixSyncAdapter(
    input("timeline_paginate_read", {
      room_id: "!private-room:example.invalid",
      pagination_token: "private-page-token",
    }),
    "private-access-token",
    {
      fetchImpl: async (target, init) => {
        calls.push({ target: new URL(String(target)), init });
        return jsonResponse({ start: "private-page-token", end: "private-end", chunk: [] });
      },
    },
  );
  assert.deepEqual(result.chunk, []);
  assert.equal(calls.length, 1);
  assert.match(calls[0].target.pathname, /^\/_matrix\/client\/v3\/rooms\//);
  assert.equal(calls[0].target.searchParams.get("dir"), "b");
  assert.equal(calls[0].target.searchParams.get("from"), "private-page-token");
  assert.equal(calls[0].target.searchParams.get("limit"), "50");
  assert.deepEqual(JSON.parse(calls[0].target.searchParams.get("filter")), {
    types: ["m.room.message"],
  });
});

test("loopback harness is denied unless the exact test opt-in is present", async () => {
  let calls = 0;
  await assert.rejects(
    () => executeMatrixSyncAdapter(
      input("sync_read", { allow_harness: false }),
      "private-access-token",
      { fetchImpl: async () => { calls += 1; return jsonResponse({}); } },
    ),
    /MATRIX_TARGET_HTTPS_REQUIRED/,
  );
  assert.equal(calls, 0);
});

test("sync input denies raw credential fields and scope drift", () => {
  assert.throws(
    () => validateSyncAdapterInput(input("sync_read", { access_token: "private" })),
    /MATRIX_SYNC_ADAPTER_INPUT_FIELD_DENIED/,
  );
  assert.throws(
    () => validateSyncAdapterInput(input("sync_read", { room_id: "!room:example" })),
    /MATRIX_SYNC_ADAPTER_TRANSIENT_SCOPE_INVALID/,
  );
  assert.throws(
    () => validateSyncAdapterInput(input("timeline_paginate_read")),
    /MATRIX_SYNC_ADAPTER_TRANSIENT_SCOPE_INVALID/,
  );
  assert.throws(
    () => validateSyncAdapterInput(input("sync_read", { event_types: ["m.room.power_levels"] })),
    /MATRIX_SYNC_ADAPTER_EVENT_SCOPE_INVALID/,
  );
  assert.throws(
    () => validateSyncAdapterInput(input("sync_read", { room_ids: ["!room:x", "!room:x"] })),
    /MATRIX_SYNC_ADAPTER_ROOM_SCOPE_INVALID/,
  );
  assert.equal(
    validateSyncAdapterInput(input("sync_read", { credential_fd: 1025 })).credential_fd,
    1025,
  );
  assert.throws(
    () => validateSyncAdapterInput(input("sync_read", { credential_fd: 2_147_483_648 })),
    /MATRIX_SYNC_ADAPTER_CREDENTIAL_FD_INVALID/,
  );
  assert.throws(
    () => validateSyncAdapterInput(input("sync_read", { room_ids: [`!${"r".repeat(254)}:x`] })),
    /MATRIX_SYNC_ADAPTER_ROOM_SCOPE_INVALID/,
  );
  const roomSuffix = ":example.invalid";
  const roomAtLimit = `!${"r".repeat(255 - 1 - Buffer.byteLength(roomSuffix))}${roomSuffix}`;
  assert.equal(
    validateSyncAdapterInput(input("timeline_paginate_read", {
      room_id: roomAtLimit,
      pagination_token: "private-page-token",
    })).room_id,
    roomAtLimit,
  );
  const roomOverLimit = `!${"r".repeat(256 - 1 - Buffer.byteLength(roomSuffix))}${roomSuffix}`;
  assert.throws(
    () => validateSyncAdapterInput(input("timeline_paginate_read", {
      room_id: roomOverLimit,
      pagination_token: "private-page-token",
    })),
    /MATRIX_SYNC_ADAPTER_TRANSIENT_SCOPE_INVALID/,
  );
});

test("maximum declared room scope remains inside the sync query envelope", async () => {
  let calls = 0;
  const roomIds = Array.from(
    { length: 128 },
    (_, index) => `!${String(index).padStart(3, "0")}${"r".repeat(220)}:example.invalid`,
  );
  const value = validateSyncAdapterInput(input("sync_read", { room_ids: roomIds }));
  await executeMatrixSyncAdapter(value, "private-access-token", {
    fetchImpl: async () => {
      calls += 1;
      return jsonResponse({ next_batch: "private-next-token", rooms: {} });
    },
  });
  assert.equal(calls, 1);
});

test("query and method drift are denied before transport", async () => {
  const { createBoundedFetch } = await import("../src/target-policy.mjs");
  let calls = 0;
  const transport = createBoundedFetch({
    allowHarness: true,
    allowedRequests: ["GET /_matrix/client/v3/sync"],
    allowedQueryKeysByPath: { "/_matrix/client/v3/sync": ["timeout", "since"] },
    fetchImpl: async () => { calls += 1; return jsonResponse({}); },
  });
  await assert.rejects(
    () => transport("http://127.0.0.1:18008/_matrix/client/v3/sync?access_token=private"),
    /MATRIX_HTTP_QUERY_SCOPE_DENIED/,
  );
  await assert.rejects(
    () => transport("http://127.0.0.1:18008/_matrix/client/v3/sync?timeout=0", { method: "POST" }),
    /MATRIX_HTTP_METHOD_DENIED/,
  );
  assert.equal(calls, 0);
});

test("redirect, media, send, typing, and receipt requests remain denied", async () => {
  const { createBoundedFetch } = await import("../src/target-policy.mjs");
  const transport = createBoundedFetch({
    allowHarness: true,
    allowedRequests: ["GET /_matrix/client/v3/sync"],
    allowedQueryKeysByPath: { "/_matrix/client/v3/sync": ["timeout"] },
    fetchImpl: async () => jsonResponse({}),
  });
  for (const [method, path] of [
    ["POST", "/_matrix/client/v3/rooms/r/send/m.room.message/t"],
    ["PUT", "/_matrix/client/v3/rooms/r/typing/u"],
    ["POST", "/_matrix/client/v3/rooms/r/receipt/m.read/e"],
    ["GET", "/_matrix/media/v3/download/s/m"],
  ]) {
    await assert.rejects(
      () => transport(`http://127.0.0.1:18008${path}`, { method }),
      /MATRIX_HTTP_(METHOD|OPERATION_SCOPE)_DENIED/,
    );
  }
});
