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

function validateBoundedStrings(value, key, maximum, allowedValues = null) {
  if (!Array.isArray(value) || value.length > maximum ||
      !value.every((item) => typeof item === "string" && item &&
        Buffer.byteLength(item, "utf8") <= 4096 &&
        (!allowedValues || allowedValues.has(item))) ||
      new Set(value).size !== value.length) {
    throw new Error(`MATRIX_SYNC_ADAPTER_${key.toUpperCase()}_INVALID`);
  }
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
    if (value[key] !== undefined &&
        (typeof value[key] !== "string" || !value[key] || Buffer.byteLength(value[key], "utf8") > 4096)) {
      throw new Error("MATRIX_SYNC_ADAPTER_TRANSIENT_SCOPE_INVALID");
    }
  }
  validateBoundedStrings(value.room_ids, "room_scope", 128);
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
  if (!Number.isInteger(value.credential_fd) || value.credential_fd < 3 || value.credential_fd > 1024) {
    throw new Error("MATRIX_SYNC_ADAPTER_CREDENTIAL_FD_INVALID");
  }
  return value;
}
