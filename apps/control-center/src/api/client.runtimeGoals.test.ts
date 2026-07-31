import { afterEach, describe, expect, it, vi } from "vitest";
import {
  createRuntimeGoal,
  editRuntimeGoal,
  fetchRuntimeRunEvents,
  isRuntimeGoalMutationTerminalRejectionError,
  isRuntimeGoalMutationValidationError,
  decideRuntimeGoalMutationApproval,
  prepareRuntimeGoalMutationApproval,
  prepareRuntimeGoalCreateSubmission,
  prepareRuntimeGoalUpdateSubmission,
  revokeRuntimeGoalMutationApproval,
  runtimeGoalMutationIdempotencyRef,
  transitionRuntimeGoal,
  type BackendTruthReadBinding,
} from "./client";
import { API_ENDPOINTS } from "./endpoints";
import { mockControlCenterData } from "../mocks/controlCenterData";
import type {
  RuntimeGoalCreateRequest,
  RuntimeGoalMutationApprovalRequestSpec,
  RuntimeGoalMutationResult,
  RuntimeGoalMutationSubmissionRecoveryRecord,
} from "./types";

const binding: BackendTruthReadBinding = {
  snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
  backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
  backendInstanceRef:
    "backend-instance-ref:control-center:22222222222222222222222222222222",
};
const approvalRef = `approval-ref:goal-mutation:sha256:${"3".repeat(64)}`;

const request: RuntimeGoalCreateRequest = {
  text_redaction_posture: "operator_authored_redacted_summary_only",
  objective: "Deliver one bounded local outcome.",
  desired_outcome: "A durable proof-backed goal.",
  success_criteria: ["A linked receipt and proof exist."],
  constraints: ["No external execution."],
  in_scope_resource_refs: ["resource-ref:goal-client-test"],
  stop_condition: "Stop when evidence is unavailable.",
  budget: {
    operation_limit: 25,
    cost_budget_microusd: 0,
  },
  links: {
    plan_refs: ["plan-ref:goal-client-test"],
    run_refs: ["run-ref:goal-client-test"],
    action_inbox_refs: ["action-inbox-ref:goal-client-test"],
    work_board_refs: ["work-board-ref:goal-client-test"],
  },
  evidence_refs: ["evidence-ref:goal-client-test"],
};

function pendingGoalRecoveryRecord(
  posture: "pending" | "approved" | "expired" | "denied" | "revoked",
): RuntimeGoalMutationSubmissionRecoveryRecord {
  const submissionEvidenceRef =
    `evidence-ref:control-center-goal-create-submission:sha256:${"a".repeat(64)}`;
  const idempotencyRef = "idempotency-ref:goal-recovery-authoritative";
  const approvalRequest: RuntimeGoalMutationApprovalRequestSpec = {
    schema_version: "goal_mutation_approval_request.v2",
    operation: "create",
    subject_ref: "goal-ref:new",
    idempotency_ref: idempotencyRef,
    request_fingerprint_ref:
      `request-fingerprint-ref:goal-mutation:sha256:${"1".repeat(64)}`,
    mutation_request_fingerprint_ref:
      `request-fingerprint-ref:goal-create:sha256:${"2".repeat(64)}`,
    exact_scope_ref:
      `exact-scope-ref:goal-mutation:sha256:${"3".repeat(64)}`,
    approval_request_ref:
      `approval-request-ref:goal-mutation:sha256:${"4".repeat(64)}`,
    approval_ref:
      `approval-ref:goal-mutation:sha256:${"5".repeat(64)}`,
    operator_actor_ref: "operator-ref:local-user",
    requested_at: "2026-07-28T00:00:00Z",
    expires_at: "2026-07-28T00:30:00Z",
  };
  const decisionStatus = posture === "expired" ? "approved" : posture;
  const decidedAt =
    decisionStatus === "pending" ? null : "2026-07-28T00:01:00Z";
  const decisionActor =
    decisionStatus === "pending" ? null : "operator-ref:local-user";
  const approvalGrant =
    decisionStatus === "approved" || decisionStatus === "revoked"
      ? {
          approval_ref: approvalRequest.approval_ref,
          approval_request_id: approvalRequest.approval_request_ref,
          run_id:
            `run-ref:goal-mutation:sha256:${"6".repeat(64)}`,
          subject_type: "kernel_task" as const,
          subject_id: approvalRequest.subject_ref,
          granted_to_actor_id: approvalRequest.operator_actor_ref,
          approved_by_actor_id: decisionActor as string,
          approved_actions: ["goal_mutation_create"],
          approved_resource_refs: [
            approvalRequest.subject_ref,
            approvalRequest.exact_scope_ref,
            approvalRequest.request_fingerprint_ref,
            approvalRequest.mutation_request_fingerprint_ref,
            approvalRequest.idempotency_ref,
          ],
          risk_level: "low" as const,
          data_classification: {
            classification: "user_private" as const,
            source: "goal-runtime-exact-local-mutation" as const,
            reason: "Goal metadata remains local and redacted." as const,
            allowed_sinks: ["local-goal-journal"] as ["local-goal-journal"],
            forbidden_sinks: [
              "provider",
              "network",
              "runtime-execution",
            ] as ["provider", "network", "runtime-execution"],
            requires_redaction: true as const,
          },
          purpose:
            "Record one exact local proof-backed goal metadata mutation; runtime execution and standing authority remain disabled.",
          status:
            decisionStatus === "revoked"
              ? ("revoked" as const)
              : ("granted" as const),
          created_at: decidedAt as string,
          expires_at: approvalRequest.expires_at,
          revoked_at:
            decisionStatus === "revoked" ? "2026-07-28T00:02:00Z" : null,
          event_ref:
            `event-ref:goal-mutation-approval:sha256:${"7".repeat(64)}`,
          trace_id: approvalRequest.approval_request_ref,
          metadata: { approval_mode: "local_dev" as const },
        }
      : null;
  return {
    schema_version: "goal_mutation_submission_recovery.v1",
    submission_ref: "submission-ref:goal-recovery-authoritative",
    operation: "create",
    goal_ref: null,
    request_payload: {
      ...request,
      evidence_refs: [submissionEvidenceRef],
    },
    idempotency_ref: idempotencyRef,
    submission_evidence_ref: submissionEvidenceRef,
    request_fingerprint_ref:
      `request-fingerprint-ref:goal-recovery:sha256:${"8".repeat(64)}`,
    recorded_at: "2026-07-28T00:00:00Z",
    status: "pending",
    committed_goal_ref: null,
    rejection_reason_ref: null,
    resolved_at: null,
    approval_recovery: {
      schema_version: "goal_mutation_approval_recovery.v1",
      posture,
      authoritative_current: true,
      approval_request: approvalRequest,
      latest_decision: decisionStatus === "pending" ? null : {
        schema_version: "goal_mutation_approval_ledger.v2",
        spec: approvalRequest,
        status: decisionStatus,
        approval_grant: approvalGrant,
        decision_reason_ref: "reason-ref:cli-goal-mutation-approval",
        decision_actor_ref: decisionActor,
        decided_at: decidedAt,
        previous_entry_hash_ref:
          `entry-hash-ref:goal-mutation-approval:sha256:${"9".repeat(64)}`,
        entry_hash_ref:
          `entry-hash-ref:goal-mutation-approval:sha256:${"b".repeat(64)}`,
      },
    },
  };
}

const mutationResult: RuntimeGoalMutationResult = {
  goal: {
    schema_version: "persistent_goal.v1",
    contract_ref: "contract-ref:proof-backed-goals-durable-events:v1",
    goal_ref: `goal-ref:sha256:${"2".repeat(64)}`,
    text_redaction_posture: "operator_authored_redacted_summary_only",
    objective: request.objective,
    desired_outcome: request.desired_outcome,
    success_criteria: request.success_criteria,
    constraints: request.constraints,
    in_scope_resource_refs: request.in_scope_resource_refs,
    stop_condition: request.stop_condition,
    state: "active",
    budget: request.budget,
    links: request.links,
    version: 1,
    created_at: "2026-07-25T00:00:00Z",
    updated_at: "2026-07-25T00:00:00Z",
    evidence_refs: request.evidence_refs,
    completion_criterion_proof_refs: [],
    completion_source_goal_version: null,
    completion_criterion_verifier_bindings: [],
    safe_refs_only: true,
    model_output_authoritative: false,
  },
  approval_binding: {
    schema_version: "goal_mutation_approval_binding.v1",
    approval_ref: approvalRef,
    approval_request_ref:
      `approval-request-ref:goal-mutation:sha256:${"4".repeat(64)}`,
    approval_decision_ref:
      `approval-decision-ref:goal-mutation:sha256:${"5".repeat(64)}`,
    approval_ledger_entry_hash_ref:
      `entry-hash-ref:goal-mutation-approval:sha256:${"9".repeat(64)}`,
    exact_scope_ref:
      `exact-scope-ref:goal-mutation:sha256:${"6".repeat(64)}`,
    request_fingerprint_ref:
      `request-fingerprint-ref:goal-mutation:sha256:${"7".repeat(64)}`,
    operator_actor_ref: "operator-ref:local-user",
    approval_validated: true,
    standing_authority_granted: false,
  },
};

describe("proof-backed runtime goal mutations", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("keeps prepare, decision, and mutation as distinct exact authority steps", async () => {
    const approvalRequest = {
      schema_version: "goal_mutation_approval_request.v2" as const,
      operation: "create",
      subject_ref: "goal-ref:new",
      idempotency_ref: "idempotency-ref:goal-client-create",
      request_fingerprint_ref:
        `request-fingerprint-ref:goal-mutation:sha256:${"1".repeat(64)}`,
      mutation_request_fingerprint_ref:
        `request-fingerprint-ref:goal-create:sha256:${"3".repeat(64)}`,
      exact_scope_ref:
        `exact-scope-ref:goal-mutation:sha256:${"2".repeat(64)}`,
      approval_request_ref:
        `approval-request-ref:goal-mutation:sha256:${"4".repeat(64)}`,
      approval_ref: approvalRef,
      operator_actor_ref: "operator-ref:local-user",
      requested_at: "2026-07-25T00:00:00Z",
      expires_at: "2026-07-25T00:30:00Z",
    };
    const decision = {
      schema_version: "goal_mutation_approval_ledger.v2" as const,
      spec: approvalRequest,
      status: "approved" as const,
      approval_grant: {},
      decision_reason_ref: "reason-ref:goal-client-explicit-approval",
      decision_actor_ref: "operator-ref:local-user",
      decided_at: "2026-07-25T00:01:00Z",
      previous_entry_hash_ref:
        `entry-hash-ref:goal-mutation-approval:sha256:${"8".repeat(64)}`,
      entry_hash_ref:
        `entry-hash-ref:goal-mutation-approval:sha256:${"9".repeat(64)}`,
    };
    const revoked = { ...decision, status: "revoked" as const };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: true,
            data: { approval_request: approvalRequest },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: true,
            data: { approval_decision: decision },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: true,
            data: { approval_decision: revoked },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    const prepared = await prepareRuntimeGoalMutationApproval(
      { operation: "create", goalRef: null, request },
      approvalRequest.idempotency_ref,
      "submission-ref:goal-client-create",
      binding,
    );
    expect(prepared).toEqual(approvalRequest);
    await decideRuntimeGoalMutationApproval(
      approvalRequest.approval_request_ref,
      "approve",
      decision.decision_reason_ref,
      binding,
    );
    await revokeRuntimeGoalMutationApproval(
      approvalRequest.approval_ref,
      "reason-ref:goal-client-explicit-revocation",
      binding,
    );

    const prepareHeaders = fetchMock.mock.calls[0][1]
      ?.headers as Record<string, string>;
    const decisionHeaders = fetchMock.mock.calls[1][1]
      ?.headers as Record<string, string>;
    const revokeHeaders = fetchMock.mock.calls[2][1]
      ?.headers as Record<string, string>;
    expect(prepareHeaders["X-UAA-Idempotency-Key"]).toBe(
      approvalRequest.idempotency_ref,
    );
    expect(prepareHeaders["X-UAA-Goal-Submission-Ref"]).toBe(
      "submission-ref:goal-client-create",
    );
    expect(decisionHeaders["X-UAA-Idempotency-Key"]).toBe(
      `idempotency-ref:goal-approval-decision:${approvalRequest.approval_request_ref}`,
    );
    expect(revokeHeaders["X-UAA-Idempotency-Key"]).toBe(
      `idempotency-ref:goal-approval-revoke:${approvalRequest.approval_ref}`,
    );
    expect(JSON.parse(String(fetchMock.mock.calls[1][1]?.body))).toEqual({
      decision: "approve",
      decision_reason_ref: decision.decision_reason_ref,
    });
  });

  it("blocks every goal approval write before fetch for a rejected API base", async () => {
    vi.stubEnv("VITE_UAA_API_BASE_URL", "https://example.invalid");
    vi.resetModules();
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    try {
      const blockedClient = await import("./client");
      const blockedCalls = [
        () => blockedClient.prepareRuntimeGoalMutationApproval(
          { operation: "create", goalRef: null, request },
          "idempotency-ref:goal-client-create",
          "submission-ref:goal-client-create",
          binding,
        ),
        () => blockedClient.decideRuntimeGoalMutationApproval(
          `approval-request-ref:goal-mutation:sha256:${"4".repeat(64)}`,
          "approve",
          "reason-ref:goal-client-explicit-approval",
          binding,
        ),
        () => blockedClient.revokeRuntimeGoalMutationApproval(
          approvalRef,
          "reason-ref:goal-client-explicit-revocation",
          binding,
        ),
      ];

      for (const blockedCall of blockedCalls) {
        await expect(blockedCall()).rejects.toThrow(
          "API base URL is not allowed",
        );
      }
      expect(fetchMock).not.toHaveBeenCalled();
    } finally {
      vi.unstubAllEnvs();
      vi.resetModules();
    }
  });

  it("binds create to exact backend truth and idempotency", async () => {
    const fetchMock = vi.fn(
      async (_url: string | URL | Request, _init?: RequestInit) =>
        new Response(
          JSON.stringify({ success: true, data: mutationResult }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await createRuntimeGoal(
      request,
      "idempotency-ref:goal-client-create",
      approvalRef,
      binding,
    );
    const [url, init] = fetchMock.mock.calls[0];
    const headers = init?.headers as Record<string, string>;

    expect(result.goal.goal_ref).toBe(mutationResult.goal.goal_ref);
    expect(url).toBe(API_ENDPOINTS.runtimeGoals);
    expect(headers["X-UAA-Idempotency-Key"]).toBe(
      "idempotency-ref:goal-client-create",
    );
    expect(headers["X-UAA-Expected-Backend-Truth-Ref"]).toBe(
      binding.snapshotRef,
    );
  });

  it("encodes the exact goal ref for a transition", async () => {
    const fetchMock = vi.fn(
      async (_url: string | URL | Request, _init?: RequestInit) =>
        new Response(
          JSON.stringify({
            success: true,
            data: {
              ...mutationResult,
              goal: { ...mutationResult.goal, state: "paused", version: 2 },
            },
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await transitionRuntimeGoal(
      mutationResult.goal.goal_ref,
      {
        expected_version: 1,
        transition: "pause",
        reason_ref: "reason-ref:goal-client-pause",
      },
      "idempotency-ref:goal-client-pause",
      approvalRef,
      binding,
    );

    expect(fetchMock.mock.calls[0][0]).toBe(
      `/api/runtime/goals/${encodeURIComponent(
        mutationResult.goal.goal_ref,
      )}/transition`,
    );
  });

  it("forwards typed budget and link edits without dropping fields", async () => {
    const fetchMock = vi.fn(
      async (_url: string | URL | Request, _init?: RequestInit) =>
        new Response(
          JSON.stringify({
            success: true,
            data: {
              ...mutationResult,
              goal: {
                ...mutationResult.goal,
                version: 2,
                budget: {
                  operation_limit: 50,
                  cost_budget_microusd: 0,
                },
                links: {
                  ...mutationResult.goal.links,
                  run_refs: ["run-ref:goal-client-edited"],
                },
              },
            },
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await editRuntimeGoal(
      mutationResult.goal.goal_ref,
      {
        expected_version: 1,
        budget: {
          operation_limit: 50,
          cost_budget_microusd: 0,
        },
        links: {
          ...mutationResult.goal.links,
          run_refs: ["run-ref:goal-client-edited"],
        },
      },
      "idempotency-ref:goal-client-edit-links",
      approvalRef,
      binding,
    );

    const requestInit = fetchMock.mock.calls[0][1];
    expect(JSON.parse(String(requestInit?.body))).toEqual({
      expected_version: 1,
      budget: {
        operation_limit: 50,
        cost_budget_microusd: 0,
      },
      links: {
        ...mutationResult.goal.links,
        run_refs: ["run-ref:goal-client-edited"],
      },
    });
  });

  it("rejects standing authority and missing truth bindings", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            success: true,
            data: {
              ...mutationResult,
              approval_binding: {
                ...mutationResult.approval_binding,
                standing_authority_granted: true,
              },
            },
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      ),
    );
    await expect(
      createRuntimeGoal(
        request,
        "idempotency-ref:goal-client-standing",
        approvalRef,
        binding,
      ),
    ).rejects.toThrow("proof-backed goal mutation failed safely");
    await expect(
      createRuntimeGoal(
        request,
        "idempotency-ref:goal-client-no-binding",
        approvalRef,
        null,
      ),
    ).rejects.toThrow("BACKEND_TRUTH_MUTATION_BINDING_REQUIRED");
  });

  it("classifies only HTTP 422 as a deterministic client-only rejection", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            ok: false,
            error: { message: "Request validation failed safely." },
          }),
          {
            status: 422,
            headers: { "Content-Type": "application/json" },
          },
        ),
      ),
    );
    const error = await createRuntimeGoal(
      request,
      "idempotency-ref:goal-client-validation",
      approvalRef,
      binding,
    ).catch((caught: unknown) => caught);
    expect(isRuntimeGoalMutationValidationError(error)).toBe(true);
  });

  it.each([
    ["GOAL_VERSION_CONFLICT", "conflict", 409],
    ["GOAL_NOT_FOUND", "not_found", 404],
    ["GOAL_MUTATION_APPROVAL_EXPIRED", "authorization_error", 403],
    ["GOAL_REQUEST_REF_INVALID", "validation_error", 400],
  ])(
    "classifies durable terminal failure %s for authoritative recovery regardless of HTTP %s",
    async (code, category, status) => {
      vi.stubGlobal(
        "fetch",
        vi.fn(async () =>
          new Response(
            JSON.stringify({
              success: false,
              error: {
                code,
                category,
                safe_message: "The proof-backed goal operation failed safely.",
                retryable: false,
              },
            }),
            {
              status,
              headers: { "Content-Type": "application/json" },
            },
          ),
        ),
      );
      const error = await createRuntimeGoal(
        request,
        `idempotency-ref:goal-client-terminal-${code.toLowerCase()}`,
        approvalRef,
        binding,
        "submission-ref:goal-client-terminal",
      ).catch((caught: unknown) => caught);
      expect(isRuntimeGoalMutationTerminalRejectionError(error)).toBe(true);
      expect(error).toMatchObject({ code });
    },
  );

  it.each([
    ["GOAL_SUBMISSION_REJECTION_PERSISTENCE_FAILED", "validation_error"],
    ["RUN_EVENT_TRUSTED_SOURCE_PROVENANCE_MISMATCH", "internal_error"],
  ])(
    "keeps HTTP 200 non-durable failure %s ambiguous",
    async (code, category) => {
      vi.stubGlobal(
        "fetch",
        vi.fn(async () =>
          new Response(
            JSON.stringify({
              success: false,
              error: {
                code,
                category,
                safe_message: "The proof-backed goal operation failed safely.",
                retryable: false,
              },
            }),
            {
              status: 200,
              headers: { "Content-Type": "application/json" },
            },
          ),
        ),
      );
      const error = await createRuntimeGoal(
        request,
        `idempotency-ref:goal-client-nondurable-${code.toLowerCase()}`,
        approvalRef,
        binding,
        "submission-ref:goal-client-nondurable",
      ).catch((caught: unknown) => caught);
      expect(error).toBeInstanceOf(Error);
      expect(isRuntimeGoalMutationTerminalRejectionError(error)).toBe(false);
    },
  );

  it.each([409, 429, 500])(
    "keeps HTTP %s goal failures ambiguous for durable recovery",
    async (status) => {
      vi.stubGlobal(
        "fetch",
        vi.fn(async () =>
          new Response(
            JSON.stringify({
              ok: false,
              error: { message: "Goal mutation outcome requires recovery." },
            }),
            {
              status,
              headers: { "Content-Type": "application/json" },
            },
          ),
        ),
      );
      const error = await createRuntimeGoal(
        request,
        `idempotency-ref:goal-client-ambiguous-${status}`,
        approvalRef,
        binding,
      ).catch((caught: unknown) => caught);
      expect(error).toBeInstanceOf(Error);
      expect(isRuntimeGoalMutationValidationError(error)).toBe(false);
    },
  );

  it.each([
    [
      "network failure",
      vi.fn(async () => {
        throw new Error("network outcome unknown");
      }),
    ],
    [
      "invalid success envelope",
      vi.fn(async () =>
        new Response(JSON.stringify({ ok: true, result: null }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    ],
  ])("keeps a %s ambiguous for durable recovery", async (_label, fetcher) => {
    vi.stubGlobal("fetch", fetcher);
    const error = await createRuntimeGoal(
      request,
      "idempotency-ref:goal-client-ambiguous-envelope",
      approvalRef,
      binding,
    ).catch((caught: unknown) => caught);
    expect(error).toBeInstanceOf(Error);
    expect(isRuntimeGoalMutationValidationError(error)).toBe(false);
  });

  it.each([
    ["null result", null],
    ["primitive result", "accepted"],
    ["missing approval binding", { goal: mutationResult.goal }],
  ])("fails safely for a malformed %s", async (_label, data) => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(
      createRuntimeGoal(
        request,
        "idempotency-ref:goal-client-malformed",
        approvalRef,
        binding,
      ),
    ).rejects.toThrow("proof-backed goal mutation failed safely");
  });

  it("rejects a persistent goal version above the durable maximum", async () => {
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      goal_lifecycle: {
        ...mockControlCenterData.runtimeRunEvents.goal_lifecycle,
        goals: [{ ...mutationResult.goal, version: 4097 }],
        goal_count: 1,
        active_count: 1,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(fetchRuntimeRunEvents()).rejects.toThrow(
      "Runtime goal/event state failed safe validation.",
    );
  });

  it.each([
    [
      "backend-shaped edit with null optionals",
      {
        expected_version: 1,
        text_redaction_posture: null,
        objective: null,
        desired_outcome: null,
        success_criteria: null,
        constraints: null,
        in_scope_resource_refs: null,
        stop_condition: null,
        budget: null,
        links: null,
        evidence_refs: [
          `evidence-ref:control-center-goal-update-submission:edit:sha256:${"a".repeat(64)}`,
        ],
      },
      "edit",
      `evidence-ref:control-center-goal-update-submission:edit:sha256:${"a".repeat(64)}`,
    ],
    [
      "backend-shaped transition with null completion evidence",
      {
        expected_version: 1,
        transition: "pause",
        reason_ref: "reason-ref:goal-recovery-pause",
        evidence_refs: [
          `evidence-ref:control-center-goal-update-submission:transition:sha256:${"b".repeat(64)}`,
        ],
        completion_evidence: null,
      },
      "transition",
      `evidence-ref:control-center-goal-update-submission:transition:sha256:${"b".repeat(64)}`,
    ],
    [
      "backend-shaped rejected completion verification",
      {
        expected_version: 2,
        transition: "verify_completion",
        reason_ref: "reason-ref:goal-recovery-verify",
        evidence_refs: [
          `evidence-ref:control-center-goal-update-submission:transition:sha256:${"c".repeat(64)}`,
        ],
        completion_evidence: {
          goal_ref: mutationResult.goal.goal_ref,
          goal_version: 2,
          run_ref: "run-ref:goal-recovery-verify",
          receipt_ref: "receipt-ref:goal-recovery-verify",
          proof_ref: "proof-ref:goal-recovery-verify",
          criterion_proof_refs: ["proof-ref:goal-recovery-criterion"],
          evidence_ref: "evidence-ref:goal-recovery-verify",
          verifier_ref: "verifier-ref:goal-recovery-verify",
        },
      },
      "transition",
      `evidence-ref:control-center-goal-update-submission:transition:sha256:${"c".repeat(64)}`,
    ],
  ])("accepts %s from durable recovery", async (
    _label,
    requestPayload,
    operation,
    submissionEvidenceRef,
  ) => {
    const record = {
      schema_version: "goal_mutation_submission_recovery.v1",
      submission_ref: "submission-ref:goal-recovery-backend-shaped",
      operation,
      goal_ref: mutationResult.goal.goal_ref,
      request_payload: requestPayload,
      idempotency_ref: "idempotency-ref:goal-recovery-backend-shaped",
      submission_evidence_ref: submissionEvidenceRef,
      request_fingerprint_ref:
        `request-fingerprint-ref:goal-recovery:sha256:${"d".repeat(64)}`,
      recorded_at: "2026-07-28T00:00:00Z",
      status: "rejected",
      committed_goal_ref: null,
      rejection_reason_ref: "reason-ref:goal-recovery-rejected",
      resolved_at: "2026-07-28T00:01:00Z",
      approval_recovery: {
        schema_version: "goal_mutation_approval_recovery.v1",
        posture: "missing",
        authoritative_current: true,
        approval_request: null,
        latest_decision: null,
      },
    };
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      goal_mutation_submissions: {
        ...mockControlCenterData.runtimeRunEvents.goal_mutation_submissions,
        records: [record],
        pending_count: 0,
        committed_count: 0,
        rejected_count: 1,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(fetchRuntimeRunEvents()).resolves.toEqual(data);
  });

  it.each(["pending", "approved", "expired", "denied", "revoked"] as const)(
    "accepts an exact authoritative %s approval recovery posture",
    async (posture) => {
      const record = pendingGoalRecoveryRecord(posture);
      const data = {
        ...mockControlCenterData.runtimeRunEvents,
        goal_mutation_submissions: {
          ...mockControlCenterData.runtimeRunEvents.goal_mutation_submissions,
          records: [record],
          pending_count: 1,
          committed_count: 0,
          rejected_count: 0,
        },
      };
      vi.stubGlobal(
        "fetch",
        vi.fn(async () =>
          new Response(JSON.stringify({ success: true, data }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        ),
      );

      await expect(fetchRuntimeRunEvents()).resolves.toEqual(data);
    },
  );

  it("accepts the exact backend expiration-recovery actor", async () => {
    const record = pendingGoalRecoveryRecord("expired");
    if (!record.approval_recovery?.latest_decision) {
      throw new Error("expected an approval decision fixture");
    }
    record.approval_recovery.latest_decision.status = "expired";
    record.approval_recovery.latest_decision.approval_grant = null;
    record.approval_recovery.latest_decision.decision_actor_ref =
      "operator-ref:goal-runtime-expiration-recovery";
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      goal_mutation_submissions: {
        ...mockControlCenterData.runtimeRunEvents.goal_mutation_submissions,
        records: [record],
        pending_count: 1,
        committed_count: 0,
        rejected_count: 0,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(fetchRuntimeRunEvents()).resolves.toEqual(data);
  });

  it.each([
    [
      "non-authoritative state",
      (record: RuntimeGoalMutationSubmissionRecoveryRecord) => {
        if (record.approval_recovery) {
          record.approval_recovery.authoritative_current = false;
        }
      },
    ],
    [
      "cross-idempotency request",
      (record: RuntimeGoalMutationSubmissionRecoveryRecord) => {
        if (record.approval_recovery?.approval_request) {
          record.approval_recovery.approval_request.idempotency_ref =
            "idempotency-ref:goal-recovery-substituted";
        }
      },
    ],
    [
      "cross-bound latest decision",
      (record: RuntimeGoalMutationSubmissionRecoveryRecord) => {
        if (record.approval_recovery?.latest_decision) {
          record.approval_recovery.latest_decision.spec.approval_ref =
            `approval-ref:goal-mutation:sha256:${"c".repeat(64)}`;
        }
      },
    ],
    [
      "approved posture with denied decision",
      (record: RuntimeGoalMutationSubmissionRecoveryRecord) => {
        if (record.approval_recovery?.latest_decision) {
          record.approval_recovery.latest_decision.status = "denied";
          record.approval_recovery.latest_decision.approval_grant = null;
        }
      },
    ],
    [
      "substituted approved resource scope",
      (record: RuntimeGoalMutationSubmissionRecoveryRecord) => {
        const grant =
          record.approval_recovery?.latest_decision?.approval_grant;
        if (grant) {
          grant.approved_resource_refs = [
            ...grant.approved_resource_refs.slice(0, -1),
            "idempotency-ref:goal-recovery-substituted",
          ];
        }
      },
    ],
  ])("fails closed for approval recovery with %s", async (_label, mutate) => {
    const record = pendingGoalRecoveryRecord("approved");
    mutate(record);
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      goal_mutation_submissions: {
        ...mockControlCenterData.runtimeRunEvents.goal_mutation_submissions,
        records: [record],
        pending_count: 1,
        committed_count: 0,
        rejected_count: 0,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(fetchRuntimeRunEvents()).rejects.toThrow(
      "Runtime goal/event state failed safe validation.",
    );
  });

  it.each([
    ["operation budget overflow", { operation_limit: 10_001 }],
    ["cost budget overflow", { cost_budget_microusd: 10_000_000_001 }],
  ])("rejects recovery with %s", async (_label, budgetOverride) => {
    const submissionEvidenceRef =
      `evidence-ref:control-center-goal-create-submission:sha256:${"e".repeat(64)}`;
    const record = {
      schema_version: "goal_mutation_submission_recovery.v1",
      submission_ref: "submission-ref:goal-recovery-budget-overflow",
      operation: "create",
      goal_ref: null,
      request_payload: {
        ...request,
        budget: { ...request.budget, ...budgetOverride },
        evidence_refs: [submissionEvidenceRef],
      },
      idempotency_ref: "idempotency-ref:goal-recovery-budget-overflow",
      submission_evidence_ref: submissionEvidenceRef,
      request_fingerprint_ref:
        `request-fingerprint-ref:goal-recovery:sha256:${"f".repeat(64)}`,
      recorded_at: "2026-07-28T00:00:00Z",
      status: "pending",
      committed_goal_ref: null,
      rejection_reason_ref: null,
      resolved_at: null,
    };
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      goal_mutation_submissions: {
        ...mockControlCenterData.runtimeRunEvents.goal_mutation_submissions,
        records: [record],
        pending_count: 1,
        committed_count: 0,
        rejected_count: 0,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(fetchRuntimeRunEvents()).rejects.toThrow(
      "Runtime goal/event state failed safe validation.",
    );
  });

  it.each([
    ["missing links", { links: undefined }],
    ["missing budget", { budget: undefined }],
    [
      "malformed criterion binding",
      { completion_criterion_verifier_bindings: [null] },
    ],
    [
      "substituted contract ref",
      { contract_ref: "contract-ref:substituted-goal-runtime:v1" },
    ],
  ])("rejects a persistent goal with %s", async (_label, replacement) => {
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      goal_lifecycle: {
        ...mockControlCenterData.runtimeRunEvents.goal_lifecycle,
        goals: [{ ...mutationResult.goal, ...replacement }],
        goal_count: 1,
        active_count: 1,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(fetchRuntimeRunEvents()).rejects.toThrow(
      "Runtime goal/event state failed safe validation.",
    );
  });

  it("accepts an active linked goal without premature completion-plan provenance", async () => {
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      goal_lifecycle: {
        ...mockControlCenterData.runtimeRunEvents.goal_lifecycle,
        goals: [mutationResult.goal],
        goal_count: 1,
        active_count: 1,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    const result = await fetchRuntimeRunEvents();
    expect(result.goal_lifecycle.goals[0]).toMatchObject({
      state: "active",
      links: { plan_refs: request.links.plan_refs },
    });
    expect(result.goal_lifecycle.goals[0]).not.toHaveProperty(
      "completion_plan_ref",
    );
  });

  it.each([
    [
      "missing criterion proof binding",
      {
        completion_criterion_proof_refs: [],
      },
    ],
    [
      "unlinked plan substitution",
      {
        completion_plan_ref: "plan-ref:substituted",
        completion_criterion_proof_refs: ["proof-ref:goal-client:criterion"],
      },
    ],
  ])("rejects verified completion with %s", async (_label, replacement) => {
    const verifiedGoal = Object.assign(
      {
        ...mutationResult.goal,
        state: "verified_complete" as const,
        version: 3,
        completion_run_ref: "run-ref:goal-client-test",
        completion_plan_ref: request.links.plan_refs[0],
        completion_evidence_ref: "evidence-ref:goal-client:completion",
        completion_receipt_ref: "receipt-ref:goal-client:completion",
        completion_proof_ref: "proof-ref:goal-client:completion",
        completion_criterion_proof_refs: [
          "proof-ref:goal-client:criterion",
        ],
        completion_verifier_ref: "verifier-ref:goal-client:completion",
      },
      replacement,
    );
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            success: true,
            data: {
              ...mutationResult,
              goal: verifiedGoal,
            },
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      ),
    );

    await expect(
      createRuntimeGoal(
        request,
        "idempotency-ref:goal-client-invalid-completion",
        approvalRef,
        binding,
      ),
    ).rejects.toThrow("proof-backed goal mutation failed safely");
  });

  it("binds post-mutation run-event refreshes to the selected backend", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            success: true,
            data: mockControlCenterData.runtimeRunEvents,
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      ),
    );

    await expect(fetchRuntimeRunEvents(binding)).rejects.toThrow(
      "BACKEND_RESPONSE_PROVENANCE_MISMATCH",
    );
  });

  it("derives the same durable create identity across canonical key order and remount", async () => {
    const reorderedRequest: RuntimeGoalCreateRequest = {
      evidence_refs: [...request.evidence_refs],
      links: {
        work_board_refs: [...request.links.work_board_refs],
        action_inbox_refs: [...request.links.action_inbox_refs],
        run_refs: [...request.links.run_refs],
        plan_refs: [...request.links.plan_refs],
      },
      budget: {
        cost_budget_microusd: request.budget.cost_budget_microusd,
        operation_limit: request.budget.operation_limit,
      },
      stop_condition: request.stop_condition,
      in_scope_resource_refs: [...request.in_scope_resource_refs],
      constraints: [...request.constraints],
      success_criteria: [...request.success_criteria],
      desired_outcome: request.desired_outcome,
      objective: request.objective,
      text_redaction_posture: request.text_redaction_posture,
    };
    const storageRead = vi.spyOn(Storage.prototype, "getItem");
    const storageWrite = vi.spyOn(Storage.prototype, "setItem");

    const submissionRef =
      "submission-ref:control-center-goal-mutation:stable-remount";
    const beforeUnmount = await prepareRuntimeGoalCreateSubmission(
      request,
      submissionRef,
    );
    const afterRemount = await prepareRuntimeGoalCreateSubmission(
      JSON.parse(JSON.stringify(reorderedRequest)),
      submissionRef,
    );

    expect(afterRemount).toEqual(beforeUnmount);
    expect(beforeUnmount.idempotencyRef).toMatch(
      /^idempotency-ref:control-center-goal-create:sha256:[a-f0-9]{64}$/,
    );
    expect(storageRead).not.toHaveBeenCalled();
    expect(storageWrite).not.toHaveBeenCalled();
  });

  it("allocates collision-resistant create identities without stale snapshot ordinals", async () => {
    const firstSubmission =
      await prepareRuntimeGoalCreateSubmission(request);
    const concurrentSubmission =
      await prepareRuntimeGoalCreateSubmission(request);
    const exactRetry = await prepareRuntimeGoalCreateSubmission(
      request,
      firstSubmission.submissionRef,
    );

    expect(concurrentSubmission.submissionRef).not.toBe(
      firstSubmission.submissionRef,
    );
    expect(concurrentSubmission.submissionEvidenceRef).not.toBe(
      firstSubmission.submissionEvidenceRef,
    );
    expect(concurrentSubmission.idempotencyRef).not.toBe(
      firstSubmission.idempotencyRef,
    );
    expect(exactRetry).toEqual(firstSubmission);
  });

  it("binds edit and transition retry evidence to the exact update request", async () => {
    const editRequest = {
      expected_version: 4,
      text_redaction_posture:
        "operator_authored_redacted_summary_only" as const,
      objective: "Refine one bounded local outcome.",
      evidence_refs: [],
    };
    const edit = await prepareRuntimeGoalUpdateSubmission(
      "edit",
      mutationResult.goal.goal_ref,
      editRequest,
    );
    const editRetry = await prepareRuntimeGoalUpdateSubmission(
      "edit",
      mutationResult.goal.goal_ref,
      editRequest,
      edit.submissionRef,
    );
    const transition = await prepareRuntimeGoalUpdateSubmission(
      "transition",
      mutationResult.goal.goal_ref,
      {
        expected_version: 4,
        transition: "pause",
        reason_ref: "reason-ref:goal-client-pause",
        evidence_refs: ["evidence-ref:goal-client-pause"],
      },
    );

    expect(editRetry).toEqual(edit);
    expect(edit.request.evidence_refs).toContain(edit.submissionEvidenceRef);
    expect(edit.submissionEvidenceRef).toMatch(
      /^evidence-ref:control-center-goal-update-submission:edit:sha256:[a-f0-9]{64}$/,
    );
    expect(transition.request.evidence_refs).toContain(
      transition.submissionEvidenceRef,
    );
    expect(transition.submissionEvidenceRef).toMatch(
      /^evidence-ref:control-center-goal-update-submission:transition:sha256:[a-f0-9]{64}$/,
    );
    expect(transition.idempotencyRef).not.toBe(edit.idempotencyRef);
  });

  it("domain-separates materially distinct mutation payloads, operations, and goals", async () => {
    const createIdentity = await runtimeGoalMutationIdempotencyRef({
      operation: "create",
      goalRef: null,
      request,
    });
    const changedCreateIdentity = await runtimeGoalMutationIdempotencyRef({
      operation: "create",
      goalRef: null,
      request: {
        ...request,
        desired_outcome: "A materially different durable outcome.",
      },
    });
    const editRequest = {
      expected_version: 1,
      objective: request.objective,
      evidence_refs: request.evidence_refs,
    };
    const editIdentity = await runtimeGoalMutationIdempotencyRef({
      operation: "edit",
      goalRef: mutationResult.goal.goal_ref,
      request: editRequest,
    });
    const otherGoalIdentity = await runtimeGoalMutationIdempotencyRef({
      operation: "edit",
      goalRef: `goal-ref:sha256:${"9".repeat(64)}`,
      request: editRequest,
    });
    const transitionIdentity = await runtimeGoalMutationIdempotencyRef({
      operation: "transition",
      goalRef: mutationResult.goal.goal_ref,
      request: {
        expected_version: 1,
        transition: "pause",
        reason_ref: "reason-ref:goal-client-pause",
      },
    });

    expect(
      new Set([
        createIdentity,
        changedCreateIdentity,
        editIdentity,
        otherGoalIdentity,
        transitionIdentity,
      ]).size,
    ).toBe(5);
  });

  it("fails closed when canonical mutation digesting is unavailable", async () => {
    vi.stubGlobal("crypto", undefined);

    await expect(
      runtimeGoalMutationIdempotencyRef({
        operation: "create",
        goalRef: null,
        request,
      }),
    ).rejects.toThrow("RUNTIME_GOAL_MUTATION_DIGEST_UNAVAILABLE");
  });

  it("rejects an unknown goal lifecycle state from runtime JSON", async () => {
    const invalidGoal = {
      ...mutationResult.goal,
      state: "production_ready",
    };
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      goal_lifecycle: {
        ...mockControlCenterData.runtimeRunEvents.goal_lifecycle,
        goals: [invalidGoal],
        goal_count: 1,
        active_count: 0,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(fetchRuntimeRunEvents()).rejects.toThrow(
      "Runtime goal/event state failed safe validation.",
    );
  });

  it("rejects terminal controls from durable goal summaries", async () => {
    const invalidGoal = {
      ...mutationResult.goal,
      objective: "Bounded\u001bforged operator summary.",
    };
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      goal_lifecycle: {
        ...mockControlCenterData.runtimeRunEvents.goal_lifecycle,
        goals: [invalidGoal],
        goal_count: 1,
        active_count: 1,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(fetchRuntimeRunEvents()).rejects.toThrow(
      "Runtime goal/event state failed safe validation.",
    );
  });

  it("accepts the backend synthesized presence proof for a valid nonterminal durable event", async () => {
    const event = {
      event_ref: "runtime-run-event-ref:goal-client:started",
      event_kind: "run_started" as const,
      runtime_run_ref: "runtime-run-ref:goal-client:test",
      uaa_durable_run_ref: "runtime-run-ref:goal-client:test",
      proof_ref: "proof-ref:runtime-run-events:redacted-event-presence",
      redaction_status: "redacted_safe_ref_only" as const,
      safe_summary: "A durable local run started with content omitted.",
      sequence: 1,
      recorded_at: "2026-07-25T00:00:00Z",
      predecessor_hash_ref: null,
      event_hash_ref: "event-hash-ref:goal-client:started",
      proof_refs: [],
      receipt_refs: [],
      criterion_verifier_bindings: [],
      goal_ref: null,
      plan_ref: null,
      runtime_payload_persisted: false,
      raw_log_persisted: false,
      raw_prompt_persisted: false,
      raw_response_persisted: false,
    };
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      event_previews: [event],
      stream_summaries: [
        {
          run_ref: event.runtime_run_ref,
          run_type: "local_read_task" as const,
          first_retained_sequence: 1,
          last_sequence: 1,
          retained_event_count: 1,
          retention_anchor_hash_ref: null,
          successful_receipt_recorded: false,
          terminal_event_kind: null,
        },
      ],
      stream_count: 1,
      retained_event_count: 1,
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(fetchRuntimeRunEvents()).resolves.toEqual(data);
  });

  it("preserves receipt-backed completion after later evidence metadata", async () => {
    const receipt = {
      event_ref: "runtime-run-event-ref:goal-client:receipt",
      event_kind: "receipt_recorded" as const,
      runtime_run_ref: "runtime-run-ref:goal-client:receipt",
      uaa_durable_run_ref: "runtime-run-ref:goal-client:receipt",
      proof_ref: "proof-ref:goal-client:receipt",
      redaction_status: "redacted_safe_ref_only" as const,
      safe_summary: "A successful bounded local receipt was recorded.",
      sequence: 1,
      recorded_at: "2026-07-25T00:00:00Z",
      predecessor_hash_ref: null,
      event_hash_ref: "event-hash-ref:goal-client:receipt",
      proof_refs: ["proof-ref:goal-client:receipt"],
      receipt_refs: ["receipt-ref:goal-client:receipt"],
      criterion_verifier_bindings: [],
      goal_ref: null,
      plan_ref: null,
      runtime_payload_persisted: false,
      raw_log_persisted: false,
      raw_prompt_persisted: false,
      raw_response_persisted: false,
    };
    const evidence = {
      ...receipt,
      event_ref: "runtime-run-event-ref:goal-client:evidence",
      event_kind: "evidence_linked" as const,
      proof_ref: "proof-ref:goal-client:evidence",
      safe_summary: "Later bounded evidence metadata was linked.",
      sequence: 2,
      recorded_at: "2026-07-25T00:00:01Z",
      predecessor_hash_ref: receipt.event_hash_ref,
      event_hash_ref: "event-hash-ref:goal-client:evidence",
      proof_refs: ["proof-ref:goal-client:evidence"],
      receipt_refs: [],
    };
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      event_previews: [receipt, evidence],
      stream_summaries: [
        {
          run_ref: receipt.runtime_run_ref,
          run_type: "local_read_task" as const,
          first_retained_sequence: 1,
          last_sequence: 2,
          retained_event_count: 2,
          retention_anchor_hash_ref: null,
          successful_receipt_recorded: true,
          terminal_event_kind: null,
        },
      ],
      stream_count: 1,
      retained_event_count: 2,
      completed_run_count: 1,
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(fetchRuntimeRunEvents()).resolves.toEqual(data);
  });

  it.each([
    ["goal_linked", "goal_ref"],
    ["plan_linked", "plan_ref"],
  ] as const)(
    "rejects %s durable events when the required %s binding is missing",
    async (eventKind, _requiredBinding) => {
      const event = {
        event_ref: `runtime-run-event-ref:goal-client:${eventKind}`,
        event_kind: eventKind,
        runtime_run_ref: "runtime-run-ref:goal-client:test",
        uaa_durable_run_ref: "runtime-run-ref:goal-client:test",
        proof_ref: "proof-ref:goal-client:semantic-binding",
        redaction_status: "redacted_safe_ref_only" as const,
        safe_summary: "A durable semantic link was recorded with safe refs.",
        sequence: 1,
        recorded_at: "2026-07-25T00:00:00Z",
        predecessor_hash_ref: null,
        event_hash_ref: `event-hash-ref:goal-client:${eventKind}`,
        proof_refs: ["proof-ref:goal-client:semantic-binding"],
        receipt_refs: [],
        criterion_verifier_bindings: [],
        goal_ref: null,
        plan_ref: null,
        runtime_payload_persisted: false,
        raw_log_persisted: false,
        raw_prompt_persisted: false,
        raw_response_persisted: false,
      };
      const data = {
        ...mockControlCenterData.runtimeRunEvents,
        event_previews: [event],
        stream_summaries: [
          {
            run_ref: event.runtime_run_ref,
            run_type: "local_read_task" as const,
            first_retained_sequence: 1,
            last_sequence: 1,
            retained_event_count: 1,
            retention_anchor_hash_ref: null,
            successful_receipt_recorded: false,
            terminal_event_kind: null,
          },
        ],
        stream_count: 1,
        retained_event_count: 1,
      };
      vi.stubGlobal(
        "fetch",
        vi.fn(async () =>
          new Response(JSON.stringify({ success: true, data }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        ),
      );

      await expect(fetchRuntimeRunEvents()).rejects.toThrow(
        "Runtime goal/event state failed safe validation.",
      );
    },
  );

  it.each([
    ["event_kind", "invented_event"],
    ["event_ref", "unsafe"],
    ["runtime_run_ref", "unsafe"],
    ["proof_ref", "unsafe"],
    ["proof_ref", "proof-ref:goal-client:substituted"],
    ["safe_summary", ["token", "raw-secret"].join("=")],
    ["safe_summary", "Bounded\u001bforged event summary."],
    ["redaction_status", "raw"],
    ["redaction_status", "redacted_safe_refs_only"],
    ["sequence", 0],
    ["event_hash_ref", "unsafe"],
    ["proof_refs", ["unsafe"]],
    ["proof_refs", []],
    ["receipt_refs", ["unsafe"]],
    ["receipt_refs", []],
    ["goal_ref", "unsafe"],
    ["plan_ref", "unsafe"],
    ["runtime_payload_persisted", true],
  ])("rejects malformed durable event field %s", async (field, replacement) => {
    const event = {
      event_ref: "runtime-run-event-ref:goal-client:test",
      event_kind: "receipt_recorded" as const,
      runtime_run_ref: "runtime-run-ref:goal-client:test",
      uaa_durable_run_ref: "runtime-run-ref:goal-client:test",
      proof_ref: "proof-ref:goal-client:test",
      redaction_status: "redacted_safe_ref_only",
      safe_summary: "A durable receipt was recorded with bounded safe refs.",
      sequence: 1,
      recorded_at: "2026-07-25T00:00:00Z",
      predecessor_hash_ref: null,
      event_hash_ref: "event-hash-ref:goal-client:test",
      proof_refs: ["proof-ref:goal-client:test"],
      receipt_refs: ["receipt-ref:goal-client:test"],
      criterion_verifier_bindings: [],
      goal_ref: "goal-ref:goal-client:test",
      plan_ref: "plan-ref:goal-client:test",
      runtime_payload_persisted: false,
      raw_log_persisted: false,
      raw_prompt_persisted: false,
      raw_response_persisted: false,
    };
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      event_previews: [{ ...event, [field]: replacement }],
      stream_summaries: [
        {
          run_ref: event.runtime_run_ref,
          run_type: "local_read_task" as const,
          first_retained_sequence: 1,
          last_sequence: 1,
          retained_event_count: 1,
          retention_anchor_hash_ref: null,
          successful_receipt_recorded: true,
          terminal_event_kind: null,
        },
      ],
      stream_count: 1,
      retained_event_count: 1,
      completed_run_count: 1,
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(fetchRuntimeRunEvents()).rejects.toThrow(
      "Runtime goal/event state failed safe validation.",
    );
  });

  it("accepts the Python safe-ref grammar including at-sign versions", async () => {
    const goal = {
      ...mutationResult.goal,
      evidence_refs: ["evidence-ref:artifact@v1"],
    };
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      goal_lifecycle: {
        ...mockControlCenterData.runtimeRunEvents.goal_lifecycle,
        goals: [goal],
        goal_count: 1,
        active_count: 1,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(fetchRuntimeRunEvents()).resolves.toEqual(data);
  });

  it.each([
    "Review path:/workspace/private.txt.",
    "Inspect artifact:/opt/company/private.txt.",
    "Inspect artifact-ref:bounded:/workspace/private.txt.",
    "Inspect artifact-ref:bounded://root/private.txt.",
    ...Array.from("!\"#$%&'()*+,-.;<=>?@[\\]^_`{|}~").map(
      (delimiter) =>
        `Inspect artifact${delimiter}/home/operator/private.txt.`,
    ),
    String.raw`Inspect artifact|C:\Users\operator\private.txt.`,
    String.raw`Inspect artifact!\\server\share\private.txt.`,
  ])("rejects punctuated absolute paths in durable text", async (objective) => {
    const goal = {
      ...mutationResult.goal,
      objective,
    };
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      goal_lifecycle: {
        ...mockControlCenterData.runtimeRunEvents.goal_lifecycle,
        goals: [goal],
        goal_count: 1,
        active_count: 1,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(fetchRuntimeRunEvents()).rejects.toThrow(
      "Runtime goal/event state failed safe validation.",
    );
  });

  it.each([
    "Reviewed https://example.test/bounded-evidence.",
    "Recorded artifact-ref:bounded/path.",
    "Recorded artifact-ref:bounded./path.",
    "Recorded artifact-ref:bounded-/path.",
    "Recorded artifact-ref:bounded@/path.",
    "Recorded artifact-ref:bounded_/path.",
  ])("preserves network URI and canonical safe-ref text", async (objective) => {
    const goal = {
      ...mutationResult.goal,
      objective,
    };
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      goal_lifecycle: {
        ...mockControlCenterData.runtimeRunEvents.goal_lifecycle,
        goals: [goal],
        goal_count: 1,
        active_count: 1,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(fetchRuntimeRunEvents()).resolves.toEqual(data);
  });

  it("uses Unicode code-point bounds that match the Python contract", async () => {
    const goal = {
      ...mutationResult.goal,
      objective: "😀".repeat(1200),
    };
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      goal_lifecycle: {
        ...mockControlCenterData.runtimeRunEvents.goal_lifecycle,
        goals: [goal],
        goal_count: 1,
        active_count: 1,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(fetchRuntimeRunEvents()).resolves.toEqual(data);
  });

  it("rejects durable text above the Unicode code-point bound", async () => {
    const goal = {
      ...mutationResult.goal,
      objective: "😀".repeat(1201),
    };
    const data = {
      ...mockControlCenterData.runtimeRunEvents,
      goal_lifecycle: {
        ...mockControlCenterData.runtimeRunEvents.goal_lifecycle,
        goals: [goal],
        goal_count: 1,
        active_count: 1,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ success: true, data }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(fetchRuntimeRunEvents()).rejects.toThrow(
      "Runtime goal/event state failed safe validation.",
    );
  });
});
