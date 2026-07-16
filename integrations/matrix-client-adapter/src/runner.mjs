#!/usr/bin/env node
import fs from "node:fs";

import { executeMatrixAdapter, stableRef } from "./adapter.mjs";
import { validateAdapterInput } from "./input-contract.mjs";

const MAX_INPUT_BYTES = 128 * 1024;

function monitorParentLiveness() {
  const expectedParentPid = process.ppid;
  const timer = setInterval(() => {
    if (process.ppid <= 1 || process.ppid !== expectedParentPid) process.exit(70);
  }, 100);
  timer.unref();
}

function safeFailure(operation, code) {
  const safeCode = /^[A-Z][A-Z0-9_]{2,127}$/.test(code) ? code : "MATRIX_ADAPTER_FAILURE";
  return {
    schema_version: "uaa-matrix-client-adapter-response.v1",
    ok: false,
    operation,
    runtime_status: "blocked",
    result_ref: stableRef("adapter-result-ref:matrix-session", { operation, code: safeCode }),
    error_code: safeCode,
    redaction_status: "safe_refs_only",
  };
}

async function main() {
  monitorParentLiveness();
  const raw = fs.readFileSync(0);
  if (raw.byteLength > MAX_INPUT_BYTES) throw new Error("MATRIX_ADAPTER_INPUT_TOO_LARGE");
  const request = validateAdapterInput(JSON.parse(raw.toString("utf8")));
  const operation = typeof request.operation === "string" ? request.operation : "unknown";
  try {
    const data = await executeMatrixAdapter(request);
    fs.writeSync(1, JSON.stringify({
      schema_version: "uaa-matrix-client-adapter-response.v1",
      ok: true,
      operation,
      result_ref: stableRef("adapter-result-ref:matrix-session", data),
      redaction_status: "safe_refs_only",
      ...data,
    }));
    return 0;
  } catch (error) {
    const code = typeof error?.code === "string" ? error.code : String(error?.message || "MATRIX_ADAPTER_FAILURE");
    fs.writeSync(1, JSON.stringify(safeFailure(operation, code)));
    return 2;
  }
}

main().then((code) => process.exit(code)).catch(() => {
  fs.writeSync(1, JSON.stringify(safeFailure("unknown", "MATRIX_ADAPTER_FAILURE")));
  process.exit(2);
});
