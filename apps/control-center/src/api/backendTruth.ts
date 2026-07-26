import type { ControlCenterBackendTruth } from "./types";

const SCHEMA_VERSION = "uaa-control-center-backend-truth.v1";
const SOURCE_REF = "source-ref:python-core:control-center-backend-truth";
const INTEGRITY_PREFIX = "proof-ref:backend-truth-envelope:sha256:";
const ACCEPTANCE_SCHEMA_VERSION = "founder-loop-durable-evidence.v1";
const ACCEPTANCE_INTEGRITY_PATTERN =
  /^proof-ref:founder-loop-durable-evidence:sha256:[0-9a-f]{64}$/;
const EXPECTED_SURFACES = [
  ["critical-surface:overview", "Overview", ["/"], ["GET /control-center/dashboard", "GET /control-center/settings/status"]],
  ["critical-surface:start-here", "Start Here", ["/start"], ["GET /control-center/start-here/summary"]],
  ["critical-surface:today", "Today", ["/today", "/workspace", "/workspace/today"], ["GET /control-center/today/summary"]],
  ["critical-surface:plans", "Plans", ["/plans"], ["GET /control-center/today/summary"]],
  ["critical-surface:action-inbox", "Action Inbox", ["/actions", "/workspace/decisions"], ["GET /control-center/actions/inbox"]],
  ["critical-surface:approvals", "Approvals", ["/approvals", "/workspace/decisions"], ["GET /control-center/approvals/queue"]],
  ["critical-surface:work-board", "Work Board", ["/work-board", "/workspace/work-board"], ["GET /control-center/work-board"]],
  ["critical-surface:morning-briefing", "Morning Briefing", ["/briefing", "/morning-briefing", "/workspace", "/workspace/today"], ["GET /control-center/morning-briefing/summary"]],
  ["critical-surface:memory", "Memory", ["/memory", "/workspace/knowledge"], ["GET /control-center/memory/review"]],
  ["critical-surface:evidence-proof", "Evidence and Proof", ["/proof", "/evidence", "/workspace/activity-trust"], ["GET /control-center/proof/index", "GET /control-center/evidence/timeline", "GET /control-center/runs/observability"]],
  ["critical-surface:setup", "Setup", ["/setup", "/workspace/onboarding"], ["GET /control-center/setup-assistant/summary"]],
  ["critical-surface:chat-handoff", "Chat handoff", ["/chat"], ["GET /control-center/agent-loop/thread"]],
  ["critical-surface:active-run", "Active run", ["/runs", "/workspace/activity-trust"], ["GET /control-center/runs/observability"]],
  ["critical-surface:settings", "Settings", ["/settings", "/workspace/settings"], ["GET /control-center/settings/status"]],
] as const;

const CRITICAL_FRONTEND_PATHS = new Set([
  "/",
  "/start",
  "/today",
  "/plans",
  "/actions",
  "/approvals",
  "/work-board",
  "/briefing",
  "/morning-briefing",
  "/memory",
  "/proof",
  "/evidence",
  "/setup",
  "/chat",
  "/runs",
  "/settings",
  "/workspace/settings",
  "/workspace",
  "/workspace/today",
  "/workspace/decisions",
  "/workspace/work-board",
  "/workspace/knowledge",
  "/workspace/activity-trust",
  "/workspace/onboarding",
]);

export class BackendTruthValidationError extends Error {
  constructor(public readonly code: string) {
    super(code);
    this.name = "BackendTruthValidationError";
  }
}

export function canonicalizeControlCenterPath(path: string): string {
  const pathname = path.split(/[?#]/, 1)[0] ?? "";
  const withLeadingSlash = pathname.startsWith("/") ? pathname : `/${pathname}`;
  const canonical = withLeadingSlash.replace(/\/+$/, "");
  return canonical === "" ? "/" : canonical;
}

export function isCriticalControlCenterPath(path: string): boolean {
  return CRITICAL_FRONTEND_PATHS.has(canonicalizeControlCenterPath(path));
}

export async function validateControlCenterBackendTruth(
  value: unknown,
  options: { now?: Date; sha256?: (value: string) => Promise<string> } = {},
): Promise<ControlCenterBackendTruth> {
  if (!isRecord(value)) fail("BACKEND_TRUTH_MALFORMED");
  if (value.schema_version !== SCHEMA_VERSION) fail("BACKEND_TRUTH_SCHEMA_MISMATCH");
  if (value.source_ref !== SOURCE_REF) fail("BACKEND_TRUTH_SOURCE_MISMATCH");
  if (
    value.safe_refs_only !== true ||
    value.redacted_summaries_only !== true ||
    value.raw_content_included !== false ||
    value.raw_paths_included !== false
  ) {
    fail("BACKEND_TRUTH_REDACTION_POSTURE_INVALID");
  }
  if (!safeString(value.backend_revision_ref) || typeof value.source_revision_bound !== "boolean") {
    fail("BACKEND_TRUTH_REVISION_INVALID");
  }
  if (
    value.source_revision_bound !== true ||
    !/^commit-ref:git:[0-9a-f]{40}(?:[0-9a-f]{24})?$/.test(value.backend_revision_ref)
  ) {
    fail("BACKEND_TRUTH_REVISION_UNBOUND");
  }
  if (
    typeof value.backend_instance_ref !== "string" ||
    !/^backend-instance-ref:control-center:[0-9a-f]{32}$/.test(
      value.backend_instance_ref,
    )
  ) {
    fail("BACKEND_TRUTH_INSTANCE_INVALID");
  }

  const generatedAt = parseTimestamp(value.generated_at);
  const validUntil = parseTimestamp(value.valid_until);
  const now = (options.now ?? new Date()).getTime();
  if (validUntil <= generatedAt || validUntil - generatedAt > 120_000) {
    fail("BACKEND_TRUTH_FRESHNESS_WINDOW_INVALID");
  }
  if (generatedAt > now + 5_000) fail("BACKEND_TRUTH_FROM_FUTURE");
  if (validUntil <= now) fail("BACKEND_TRUTH_STALE");

  if (!Array.isArray(value.critical_surfaces) || value.critical_surfaces.length !== 14) {
    fail("BACKEND_TRUTH_CRITICAL_SURFACES_INCOMPLETE");
  }
  value.critical_surfaces.forEach((surface, index) => {
    const expected = EXPECTED_SURFACES[index];
    if (
      !isRecord(surface) ||
      surface.surface_ref !== expected[0] ||
      surface.label !== expected[1] ||
      surface.contract_status !== "backend_contract_declared" ||
      !sameStringArray(surface.frontend_paths, expected[2]) ||
      !sameStringArray(surface.backend_route_refs, expected[3])
    ) {
      fail("BACKEND_TRUTH_CRITICAL_SURFACE_INVALID");
    }
  });

  validateEvidence(value.evidence_binding);
  validateAuthority(value.authority_posture);
  if (!safeString(value.cli_ref) || !safeString(value.envelope_integrity_ref)) {
    fail("BACKEND_TRUTH_PROVENANCE_INVALID");
  }
  const { envelope_integrity_ref: claimedIntegrity, ...unsigned } = value;
  const expectedIntegrity = await backendTruthIntegrityRef(
    unsigned,
    options.sha256,
  );
  if (claimedIntegrity !== expectedIntegrity) fail("BACKEND_TRUTH_INTEGRITY_MISMATCH");
  return value as unknown as ControlCenterBackendTruth;
}

export async function backendTruthIntegrityRef(
  unsigned: Record<string, unknown>,
  sha256: (value: string) => Promise<string> = sha256Hex,
): Promise<string> {
  return `${INTEGRITY_PREFIX}${await sha256(canonicalJson(unsigned))}`;
}

export function canonicalJson(value: unknown): string {
  if (value === null || typeof value === "boolean" || typeof value === "number") {
    return JSON.stringify(value);
  }
  if (typeof value === "string") {
    if (!/^[\u0020-\u007e]*$/.test(value)) fail("BACKEND_TRUTH_NON_ASCII_OR_CONTROL_TEXT");
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (isRecord(value)) {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
      .join(",")}}`;
  }
  fail("BACKEND_TRUTH_CANONICAL_VALUE_INVALID");
}

async function sha256Hex(value: string): Promise<string> {
  if (!globalThis.crypto?.subtle) fail("BACKEND_TRUTH_DIGEST_UNAVAILABLE");
  const digest = await globalThis.crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  );
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

function validateEvidence(value: unknown): void {
  if (!isRecord(value)) fail("BACKEND_TRUTH_EVIDENCE_MALFORMED");
  if (
    value.acceptance_schema_version !== ACCEPTANCE_SCHEMA_VERSION ||
    typeof value.acceptance_integrity_ref !== "string" ||
    !ACCEPTANCE_INTEGRITY_PATTERN.test(value.acceptance_integrity_ref)
  ) {
    fail("BACKEND_TRUTH_EVIDENCE_PROVENANCE_INVALID");
  }
  for (const field of [
    "action_refs",
    "run_refs",
    "proof_refs",
    "receipt_refs",
    "evidence_refs",
    "memory_candidate_refs",
    "issue_refs",
  ]) {
    if (!stringArray(value[field], safeString)) fail("BACKEND_TRUTH_EVIDENCE_REFS_INVALID");
  }
  if (value.status === "verified_complete") {
    if (
      (value.issue_refs as unknown[]).length !== 0 ||
      (value.proof_refs as unknown[]).length === 0 ||
      (value.receipt_refs as unknown[]).length === 0 ||
      (value.evidence_refs as unknown[]).length === 0
    ) {
      fail("BACKEND_TRUTH_OPTIMISTIC_COMPLETION_REJECTED");
    }
  } else if (value.status === "unverified_incomplete") {
    if ((value.issue_refs as unknown[]).length === 0) {
      fail("BACKEND_TRUTH_UNVERIFIED_ISSUES_REQUIRED");
    }
  } else if (value.status === "invalid_evidence") {
    if (
      (value.issue_refs as unknown[]).length === 0 ||
      (value.receipt_refs as unknown[]).length === 0
    ) {
      fail("BACKEND_TRUTH_INVALID_EVIDENCE_PROVENANCE_REQUIRED");
    }
  } else if (value.status === "storage_unavailable") {
    if (
      (value.issue_refs as unknown[]).length === 0 ||
      (value.receipt_refs as unknown[]).length !== 0
    ) {
      fail("BACKEND_TRUTH_STORAGE_UNAVAILABLE_PROVENANCE_INVALID");
    }
  } else {
    fail("BACKEND_TRUTH_EVIDENCE_STATUS_INVALID");
  }
}

function validateAuthority(value: unknown): void {
  if (
    !isRecord(value) ||
    value.mode_ref !== "authority-mode-ref:read-only-local" ||
    value.approval_refs_are_identifiers_only !== true ||
    value.control_center_grants_authority !== false ||
    value.runtime_model_call_enabled !== false ||
    value.browser_or_web_execution_enabled !== false ||
    value.connector_write_enabled !== false ||
    value.shell_subprocess_execution_enabled !== false ||
    value.background_autonomy_enabled !== false ||
    value.production_authority_enabled !== false
  ) {
    fail("BACKEND_TRUTH_AUTHORITY_POSTURE_INVALID");
  }
}

function parseTimestamp(value: unknown): number {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}T/.test(value)) {
    fail("BACKEND_TRUTH_TIMESTAMP_INVALID");
  }
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) fail("BACKEND_TRUTH_TIMESTAMP_INVALID");
  return parsed;
}

function stringArray(
  value: unknown,
  predicate: (item: string) => boolean,
): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string" && predicate(item));
}

function sameStringArray(
  value: unknown,
  expected: readonly string[],
): value is string[] {
  return (
    Array.isArray(value) &&
    value.length === expected.length &&
    value.every((item, index) => item === expected[index])
  );
}

function safeString(value: unknown): value is string {
  return typeof value === "string" && value.length > 0 && value.length <= 500 && /^[\u0020-\u007e]+$/.test(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function fail(code: string): never {
  throw new BackendTruthValidationError(code);
}
