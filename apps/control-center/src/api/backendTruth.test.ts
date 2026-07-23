import { describe, expect, it } from "vitest";
import {
  BackendTruthValidationError,
  canonicalJson,
  isCriticalControlCenterPath,
  validateControlCenterBackendTruth,
} from "./backendTruth";

const HASH = "a".repeat(64);
const integrityRef = `proof-ref:backend-truth-envelope:sha256:${HASH}`;

function fixture(overrides: Record<string, unknown> = {}) {
  const generatedAt = "2026-07-22T18:00:00Z";
  const validUntil = "2026-07-22T18:00:45Z";
  const refs = [
    ["start-here", "Start Here", ["/start"], ["GET /control-center/start-here/summary"]],
    ["today", "Today", ["/", "/today", "/workspace", "/workspace/today"], ["GET /control-center/today/summary"]],
    ["plans", "Plans", ["/plans"], ["GET /control-center/today/summary"]],
    ["action-inbox", "Action Inbox", ["/actions", "/workspace/decisions"], ["GET /control-center/actions/inbox"]],
    ["approvals", "Approvals", ["/approvals", "/workspace/decisions"], ["GET /control-center/approvals/queue"]],
    ["work-board", "Work Board", ["/work-board", "/workspace/work-board"], ["GET /control-center/work-board"]],
    ["morning-briefing", "Morning Briefing", ["/briefing", "/morning-briefing", "/workspace", "/workspace/today"], ["GET /control-center/morning-briefing/summary"]],
    ["memory", "Memory", ["/memory", "/workspace/knowledge"], ["GET /control-center/memory/review"]],
    ["evidence-proof", "Evidence and Proof", ["/proof", "/evidence", "/workspace/activity-trust"], ["GET /control-center/proof/index", "GET /control-center/evidence/timeline", "GET /control-center/runs/observability"]],
    ["setup", "Setup", ["/setup", "/workspace/onboarding"], ["GET /control-center/setup-assistant/summary"]],
    ["chat-handoff", "Chat handoff", ["/chat"], ["GET /control-center/agent-loop/thread"]],
    ["active-run", "Active run", ["/runs", "/workspace/activity-trust"], ["GET /control-center/runs/observability"]],
  ] as const;
  return {
    schema_version: "uaa-control-center-backend-truth.v1",
    source_ref: "source-ref:python-core:control-center-backend-truth",
    generated_at: generatedAt,
    valid_until: validUntil,
    backend_revision_ref: `commit-ref:git:${"1".repeat(40)}`,
    source_revision_bound: true,
    critical_surfaces: refs.map(([ref, label, frontendPaths, backendRouteRefs]) => ({
      surface_ref: `critical-surface:${ref}`,
      label,
      frontend_paths: frontendPaths,
      backend_route_refs: backendRouteRefs,
      contract_status: "backend_contract_declared",
    })),
    evidence_binding: {
      status: "unverified_incomplete",
      acceptance_schema_version: "dogfood-live-loop-acceptance.v1",
      acceptance_integrity_ref: `proof-ref:dogfood-live-loop:sha256:${"2".repeat(64)}`,
      action_refs: [],
      run_refs: [],
      proof_refs: [],
      receipt_refs: [],
      evidence_refs: [],
      memory_candidate_refs: [],
      issue_refs: ["issue-ref:dogfood-live-loop-durable-proof-unavailable"],
    },
    authority_posture: {
      mode_ref: "authority-mode-ref:read-only-local",
      approval_refs_are_identifiers_only: true,
      control_center_grants_authority: false,
      runtime_model_call_enabled: false,
      browser_or_web_execution_enabled: false,
      connector_write_enabled: false,
      shell_subprocess_execution_enabled: false,
      background_autonomy_enabled: false,
      production_authority_enabled: false,
    },
    cli_ref: "python scripts/dev/uaa_founder_loop.py inspect-backend-truth",
    safe_refs_only: true,
    redacted_summaries_only: true,
    raw_content_included: false,
    raw_paths_included: false,
    envelope_integrity_ref: integrityRef,
    ...overrides,
  };
}

const options = {
  now: new Date("2026-07-22T18:00:10Z"),
  sha256: async () => HASH,
};

describe("backend truth validation", () => {
  it("accepts the exact current backend-owned envelope", async () => {
    const value = fixture();
    const validated = await validateControlCenterBackendTruth(value, options);

    expect(validated.backend_revision_ref).toMatch(/^commit-ref:git:/);
    expect(validated.critical_surfaces).toHaveLength(12);
    expect(validated.evidence_binding.status).toBe("unverified_incomplete");
  });

  it("accepts invalid durable evidence only with bounded issue and receipt refs", async () => {
    const base = fixture();
    const value = fixture({
      evidence_binding: {
        ...base.evidence_binding,
        status: "invalid_evidence",
        receipt_refs: ["receipt-ref:corrupt-durable-proof"],
      },
    });

    const validated = await validateControlCenterBackendTruth(value, options);

    expect(validated.evidence_binding.status).toBe("invalid_evidence");
  });

  const invalidCases: Array<[string, unknown, string, Date?]> = [
    ["malformed", null, "BACKEND_TRUTH_MALFORMED"],
    ["schema", fixture({ schema_version: "backend-truth.v0" }), "BACKEND_TRUTH_SCHEMA_MISMATCH"],
    [
      "unbound source revision",
      fixture({ source_revision_bound: false }),
      "BACKEND_TRUTH_REVISION_UNBOUND",
    ],
    ["stale", fixture(), "BACKEND_TRUTH_STALE", new Date("2026-07-22T18:01:00Z")],
    [
      "future",
      fixture({ generated_at: "2026-07-22T18:01:00Z", valid_until: "2026-07-22T18:01:45Z" }),
      "BACKEND_TRUTH_FROM_FUTURE",
    ],
    [
      "partial surface set",
      fixture({ critical_surfaces: fixture().critical_surfaces.slice(0, 11) }),
      "BACKEND_TRUTH_CRITICAL_SURFACES_INCOMPLETE",
    ],
    [
      "out-of-order surfaces",
      fixture({ critical_surfaces: [...fixture().critical_surfaces].reverse() }),
      "BACKEND_TRUTH_CRITICAL_SURFACE_INVALID",
    ],
    [
      "authority promotion",
      fixture({
        authority_posture: {
          ...fixture().authority_posture,
          production_authority_enabled: true,
        },
      }),
      "BACKEND_TRUTH_AUTHORITY_POSTURE_INVALID",
    ],
    [
      "optimistic completion",
      fixture({
        evidence_binding: {
          ...fixture().evidence_binding,
          status: "verified_complete",
        },
      }),
      "BACKEND_TRUTH_OPTIMISTIC_COMPLETION_REJECTED",
    ],
    [
      "invalid evidence without receipt provenance",
      fixture({
        evidence_binding: {
          ...fixture().evidence_binding,
          status: "invalid_evidence",
        },
      }),
      "BACKEND_TRUTH_INVALID_EVIDENCE_PROVENANCE_REQUIRED",
    ],
    [
      "wrapper hash",
      fixture({ envelope_integrity_ref: `${integrityRef}0` }),
      "BACKEND_TRUTH_INTEGRITY_MISMATCH",
    ],
  ];

  it.each(invalidCases)("rejects %s", async (_label, value, code, nowOverride) => {
    await expect(
      validateControlCenterBackendTruth(value, {
        ...options,
        now: (nowOverride as Date | undefined) ?? options.now,
      }),
    ).rejects.toMatchObject({ code });
  });

  it("uses stable key ordering for the cross-language integrity input", () => {
    expect(canonicalJson({ z: [2, 1], a: { y: false, x: "ref" } })).toBe(
      '{"a":{"x":"ref","y":false},"z":[2,1]}',
    );
  });

  it("identifies only the critical product truth routes", () => {
    expect(isCriticalControlCenterPath("/today")).toBe(true);
    expect(isCriticalControlCenterPath("/workspace/activity-trust")).toBe(true);
    expect(isCriticalControlCenterPath("/workspace/crm")).toBe(false);
    expect(isCriticalControlCenterPath("/news")).toBe(false);
  });
});
