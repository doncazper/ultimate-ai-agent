import {
  boundedJson,
  createBoundedFetch,
  validateMatrixTarget,
} from "./target-policy.mjs";
import { buildSyncFilter } from "./sync-input-contract.mjs";

const MAX_QUERY_VALUE_BYTES = 64 * 1024;

function targetDependencies(input, dependencies) {
  return {
    ...dependencies,
    allowHarness: input.allow_harness === true &&
      input.base_url === "http://127.0.0.1:18008",
  };
}

function authorization(accessToken) {
  if (typeof accessToken !== "string" || !accessToken || Buffer.byteLength(accessToken, "utf8") > 8192) {
    throw new Error("MATRIX_SYNC_CREDENTIAL_UNAVAILABLE");
  }
  return { Authorization: `Bearer ${accessToken}` };
}

async function syncRead(input, accessToken, dependencies) {
  const targetPolicy = targetDependencies(input, dependencies);
  const base = await validateMatrixTarget(input.base_url, targetPolicy);
  const fetchFn = createBoundedFetch({
    ...targetPolicy,
    allowedRequests: ["GET /_matrix/client/v3/sync"],
    allowedQueryKeysByPath: {
      "/_matrix/client/v3/sync": ["filter", "timeout", "set_presence", "since"],
    },
    maximumResponseBytes: input.max_bytes,
    maximumQueryValueBytes: MAX_QUERY_VALUE_BYTES,
  });
  const target = new URL("/_matrix/client/v3/sync", base.origin);
  target.searchParams.set("timeout", "0");
  target.searchParams.set("set_presence", "offline");
  target.searchParams.set("filter", JSON.stringify(buildSyncFilter(input)));
  if (input.since_token) target.searchParams.set("since", input.since_token);
  return boundedJson(
    await fetchFn(target, { headers: authorization(accessToken) }),
    input.max_bytes,
  );
}

async function paginateRead(input, accessToken, dependencies) {
  const targetPolicy = targetDependencies(input, dependencies);
  const base = await validateMatrixTarget(input.base_url, targetPolicy);
  const roomSegment = encodeURIComponent(input.room_id);
  const path = `/_matrix/client/v3/rooms/${roomSegment}/messages`;
  const fetchFn = createBoundedFetch({
    ...targetPolicy,
    allowedPathPatterns: [
      { method: "GET", pattern: /^\/_matrix\/client\/v3\/rooms\/[^/]+\/messages$/ },
    ],
    allowedQueryKeysByPath: { [path]: ["dir", "filter", "from", "limit"] },
    maximumResponseBytes: input.max_bytes,
  });
  const target = new URL(path, base.origin);
  target.searchParams.set("dir", "b");
  target.searchParams.set("from", input.pagination_token);
  target.searchParams.set("limit", String(Math.min(input.max_events, 50)));
  target.searchParams.set("filter", JSON.stringify({ types: input.event_types }));
  return boundedJson(
    await fetchFn(target, { headers: authorization(accessToken) }),
    input.max_bytes,
  );
}

export async function executeMatrixSyncAdapter(input, accessToken, dependencies = {}) {
  switch (input.operation) {
    case "sync_read": return syncRead(input, accessToken, dependencies);
    case "timeline_paginate_read": return paginateRead(input, accessToken, dependencies);
    default: throw new Error("MATRIX_SYNC_ADAPTER_OPERATION_DENIED");
  }
}
