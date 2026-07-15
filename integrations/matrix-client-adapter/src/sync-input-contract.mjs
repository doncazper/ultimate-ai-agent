const SAFE_REF_PATTERN = /^[A-Za-z][A-Za-z0-9._:/-]{2,255}$/;
const OPERATIONS = new Set(["sync_read", "timeline_paginate_read"]);
const ALLOWED_KEYS = new Set([
  "schema_version", "operation", "request_fingerprint_ref", "account_ref",
  "session_generation_ref", "base_url", "since_token", "room_id",
  "pagination_token", "max_events", "max_bytes", "max_duration_ms",
  "credential_fd", "room_ids", "event_types", "allow_harness",
]);
const EVENT_TYPES = new Set([
  "m.poll.start", "m.reaction", "m.receipt", "m.room.avatar",
  "m.room.encrypted", "m.room.message", "m.room.name", "m.room.redaction",
  "m.room.topic", "m.space.parent", "m.typing", "org.matrix.msc3381.poll.start",
]);
const MAX_CREDENTIAL_FD = 2_147_483_647;
const MAX_QUERY_VALUE_BYTES = 64 * 1024;
const MAX_ROOM_ID_BYTES = 255;

function validateBoundedStrings(
  value,
  key,
  maximum,
  allowedValues = null,
  maximumItemBytes = 4096,
) {
  if (!Array.isArray(value) || value.length > maximum ||
      !value.every((item) => typeof item === "string" && item &&
        Buffer.byteLength(item, "utf8") <= maximumItemBytes &&
        (!allowedValues || allowedValues.has(item))) ||
      new Set(value).size !== value.length) {
    throw new Error(`MATRIX_SYNC_ADAPTER_${key.toUpperCase()}_INVALID`);
  }
}

export function buildSyncFilter(value) {
  return {
    presence: { types: [] },
    account_data: { types: ["m.direct"] },
    room: {
      ...(value.room_ids.length ? { rooms: value.room_ids } : {}),
      timeline: {
        types: value.event_types,
        limit: Math.min(value.max_events, 50),
      },
      state: { types: value.event_types },
      ephemeral: { types: value.event_types },
      account_data: { types: [] },
    },
  };
}

export function validateSyncAdapterInput(value) {
  if (!value || typeof value !== "object" || Array.isArray(value) ||
      Object.getPrototypeOf(value) !== Object.prototype) {
    throw new Error("MATRIX_SYNC_ADAPTER_INPUT_INVALID");
  }
  if (value.schema_version !== "uaa-matrix-sync-adapter-request.v1") {
    throw new Error("MATRIX_SYNC_ADAPTER_SCHEMA_INVALID");
  }
  if (!OPERATIONS.has(value.operation)) throw new Error("MATRIX_SYNC_ADAPTER_OPERATION_DENIED");
  if (!Object.keys(value).every((key) => ALLOWED_KEYS.has(key))) {
    throw new Error("MATRIX_SYNC_ADAPTER_INPUT_FIELD_DENIED");
  }
  for (const key of ["request_fingerprint_ref", "account_ref", "session_generation_ref"]) {
    if (!SAFE_REF_PATTERN.test(String(value[key] || ""))) {
      throw new Error("MATRIX_SYNC_ADAPTER_REF_INVALID");
    }
  }
  if (typeof value.base_url !== "string" || Buffer.byteLength(value.base_url, "utf8") > 4096) {
    throw new Error("MATRIX_SYNC_ADAPTER_TARGET_INVALID");
  }
  for (const key of ["since_token", "pagination_token", "room_id"]) {
    const maximumBytes = key === "room_id" ? MAX_ROOM_ID_BYTES : 4096;
    if (value[key] !== undefined &&
        (typeof value[key] !== "string" || !value[key] ||
         Buffer.byteLength(value[key], "utf8") > maximumBytes)) {
      throw new Error("MATRIX_SYNC_ADAPTER_TRANSIENT_SCOPE_INVALID");
    }
  }
  validateBoundedStrings(value.room_ids, "room_scope", 128, null, MAX_ROOM_ID_BYTES);
  validateBoundedStrings(value.event_types, "event_scope", 32, EVENT_TYPES);
  if (!value.event_types.length || typeof value.allow_harness !== "boolean") {
    throw new Error("MATRIX_SYNC_ADAPTER_TRANSIENT_SCOPE_INVALID");
  }
  if (value.operation === "sync_read" && (value.room_id || value.pagination_token)) {
    throw new Error("MATRIX_SYNC_ADAPTER_TRANSIENT_SCOPE_INVALID");
  }
  if (value.operation === "timeline_paginate_read" &&
      (!value.room_id || !value.pagination_token || value.since_token || value.room_ids.length)) {
    throw new Error("MATRIX_SYNC_ADAPTER_TRANSIENT_SCOPE_INVALID");
  }
  if (!Number.isInteger(value.max_events) || value.max_events < 1 || value.max_events > 500 ||
      !Number.isInteger(value.max_bytes) || value.max_bytes < 1 || value.max_bytes > 1024 * 1024 ||
      !Number.isInteger(value.max_duration_ms) || value.max_duration_ms < 100 || value.max_duration_ms > 30_000) {
    throw new Error("MATRIX_SYNC_ADAPTER_BUDGET_INVALID");
  }
  if (!Number.isInteger(value.credential_fd) ||
      value.credential_fd < 3 || value.credential_fd > MAX_CREDENTIAL_FD) {
    throw new Error("MATRIX_SYNC_ADAPTER_CREDENTIAL_FD_INVALID");
  }
  if (value.operation === "sync_read" &&
      Buffer.byteLength(JSON.stringify(buildSyncFilter(value)), "utf8") > MAX_QUERY_VALUE_BYTES) {
    throw new Error("MATRIX_SYNC_ADAPTER_ROOM_SCOPE_INVALID");
  }
  return value;
}
