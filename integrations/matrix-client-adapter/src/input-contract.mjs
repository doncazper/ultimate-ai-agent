const SAFE_REF_PATTERN = /^[A-Za-z][A-Za-z0-9._:/-]{2,255}$/;
const OPERATIONS = new Set([
  "discovery_read",
  "auth_methods_read",
  "credential_auth_create",
  "sso_launch",
  "sso_callback_consume",
  "refresh",
  "logout",
  "revoke_all",
  "credential_store_rotate",
  "credential_delete",
]);
const IMPLEMENTED_OPERATIONS = new Set(["discovery_read", "auth_methods_read"]);

const ALLOWED_KEYS = new Set([
  "schema_version", "operation", "request_ref", "task_ref", "mission_ref",
  "run_ref", "dispatch_ref", "idempotency_ref", "lease_ref", "homeserver_ref",
  "endpoint_class_ref", "discovery_observation_ref", "discovery_freshness_ref",
  "target_ref", "account_ref", "device_ref", "session_ref",
  "session_generation_ref", "redirect_target_ref", "credential_backend_ref",
  "credential_item_ref", "credential_version_ref", "crypto_store_ref",
  "callback_attempt_ref", "budget_ref", "kill_switch_ref", "safe_disable_ref",
  "readiness_ref", "target_refs", "start_deadline", "request_fingerprint_ref",
  "base_url", "discovery_origin", "next_credential_version_ref",
]);

const REQUIRED_BY_OPERATION = {
  discovery_read: ["discovery_origin"],
  auth_methods_read: ["base_url"],
};

export function validateAdapterInput(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("MATRIX_ADAPTER_INPUT_INVALID");
  }
  if (Object.getPrototypeOf(value) !== Object.prototype) {
    throw new Error("MATRIX_ADAPTER_INPUT_INVALID");
  }
  if (!OPERATIONS.has(value.operation)) throw new Error("MATRIX_ADAPTER_OPERATION_UNSUPPORTED");
  if (!IMPLEMENTED_OPERATIONS.has(value.operation)) {
    throw new Error("MATRIX_ADAPTER_OPERATION_BLOCKED_PENDING_AUTHENTICATED_BROKER");
  }
  if (!Object.keys(value).every((key) => ALLOWED_KEYS.has(key))) {
    throw new Error("MATRIX_ADAPTER_INPUT_FIELD_DENIED");
  }
  for (const key of REQUIRED_BY_OPERATION[value.operation]) {
    if (value[key] === undefined || value[key] === null || value[key] === "") {
      throw new Error("MATRIX_ADAPTER_INPUT_REQUIRED_FIELD_MISSING");
    }
  }
  for (const [key, item] of Object.entries(value)) {
    if (key.endsWith("_ref") && item !== null && !SAFE_REF_PATTERN.test(String(item))) {
      throw new Error("MATRIX_ADAPTER_REF_INVALID");
    }
    if (typeof item === "string" && Buffer.byteLength(item, "utf8") > 4096) {
      throw new Error("MATRIX_ADAPTER_INPUT_FIELD_TOO_LARGE");
    }
  }
  if (value.target_refs !== undefined && (
    !Array.isArray(value.target_refs) || value.target_refs.length > 16 ||
    !value.target_refs.every((item) => SAFE_REF_PATTERN.test(String(item)))
  )) {
    throw new Error("MATRIX_ADAPTER_TARGET_REFS_INVALID");
  }
  return value;
}
