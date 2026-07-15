import assert from "node:assert/strict";
import test from "node:test";

import { validateAdapterInput } from "../src/input-contract.mjs";

test("input contract rejects unknown fields and secret material outside its exact flow", () => {
  assert.throws(
    () => validateAdapterInput({ operation: "discovery_read", discovery_origin: "https://example.org", raw_payload: "x" }),
    /MATRIX_ADAPTER_INPUT_FIELD_DENIED/,
  );
  assert.throws(
    () => validateAdapterInput({ operation: "discovery_read", discovery_origin: "https://example.org", password: "x" }),
    /MATRIX_ADAPTER_INPUT_FIELD_DENIED/,
  );
});

test("input contract rejects every blocked mutation before accepting secret material", () => {
  for (const operation of [
    "credential_auth_create", "sso_launch", "sso_callback_consume", "refresh",
    "logout", "revoke_all", "credential_store_rotate", "credential_delete",
  ]) {
    assert.throws(
      () => validateAdapterInput({ operation, password: "transient-only" }),
      /MATRIX_ADAPTER_OPERATION_BLOCKED_PENDING_AUTHENTICATED_BROKER/,
    );
  }
});
