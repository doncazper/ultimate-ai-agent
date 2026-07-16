#!/usr/bin/env node
import fs from "node:fs";

import { executeMatrixSyncAdapter } from "./sync-adapter.mjs";
import { validateSyncAdapterInput } from "./sync-input-contract.mjs";

const MAX_INPUT_BYTES = 128 * 1024;
const MAX_CREDENTIAL_BYTES = 8 * 1024;
const SAFE_CODE = /^[A-Z][A-Z0-9_]{2,127}$/;

function monitorParentLiveness() {
  const expectedParentPid = process.ppid;
  const timer = setInterval(() => {
    if (process.ppid <= 1 || process.ppid !== expectedParentPid) process.exit(70);
  }, 100);
  timer.unref();
}

function safeError(error) {
  const candidate = String(error?.code || error?.message || "MATRIX_SYNC_ADAPTER_FAILURE");
  return SAFE_CODE.test(candidate) ? candidate : "MATRIX_SYNC_ADAPTER_FAILURE";
}

async function main() {
  monitorParentLiveness();
  const raw = fs.readFileSync(0);
  if (raw.byteLength > MAX_INPUT_BYTES) throw new Error("MATRIX_SYNC_ADAPTER_INPUT_TOO_LARGE");
  const request = validateSyncAdapterInput(JSON.parse(raw.toString("utf8")));
  const credential = fs.readFileSync(request.credential_fd);
  if (credential.byteLength < 1 || credential.byteLength > MAX_CREDENTIAL_BYTES) {
    throw new Error("MATRIX_SYNC_CREDENTIAL_UNAVAILABLE");
  }
  const result = await executeMatrixSyncAdapter(request, credential.toString("utf8"));
  const output = Buffer.from(JSON.stringify(result));
  if (output.byteLength > request.max_bytes) throw new Error("MATRIX_HTTP_RESPONSE_TOO_LARGE");
  fs.writeSync(1, output);
  return 0;
}

main().then((code) => process.exit(code)).catch((error) => {
  fs.writeSync(2, `${safeError(error)}\n`);
  process.exit(2);
});
