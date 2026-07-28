import { afterEach, describe, expect, it, vi } from "vitest";
import {
  createRuntimeGoal,
  editRuntimeGoal,
  fetchRuntimeRunEvents,
  transitionRuntimeGoal,
  type BackendTruthReadBinding,
} from "./client";
import { API_ENDPOINTS } from "./endpoints";
import { mockControlCenterData } from "../mocks/controlCenterData";
import type {
  RuntimeGoalCreateRequest,
  RuntimeGoalMutationResult,
} from "./types";

const binding: BackendTruthReadBinding = {
  snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
  backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
  backendInstanceRef:
    "backend-instance-ref:control-center:22222222222222222222222222222222",
};

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
    safe_refs_only: true,
    model_output_authoritative: false,
  },
  approval_binding: {
    schema_version: "goal_mutation_approval_binding.v1",
    approval_ref: `approval-ref:goal-mutation:sha256:${"3".repeat(64)}`,
    approval_request_ref:
      `approval-request-ref:goal-mutation:sha256:${"4".repeat(64)}`,
    approval_decision_ref:
      `approval-decision-ref:goal-mutation:sha256:${"5".repeat(64)}`,
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
    vi.unstubAllGlobals();
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
        binding,
      ),
    ).rejects.toThrow("proof-backed goal mutation failed safely");
    await expect(
      createRuntimeGoal(
        request,
        "idempotency-ref:goal-client-no-binding",
        null,
      ),
    ).rejects.toThrow("BACKEND_TRUTH_MUTATION_BINDING_REQUIRED");
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

  it.each([
    ["event_kind", "invented_event"],
    ["event_ref", "unsafe"],
    ["runtime_run_ref", "unsafe"],
    ["proof_ref", "unsafe"],
    ["safe_summary", ["token", "raw-secret"].join("=")],
    ["redaction_status", "raw"],
    ["sequence", 0],
    ["event_hash_ref", "unsafe"],
    ["proof_refs", ["unsafe"]],
    ["receipt_refs", ["unsafe"]],
    ["runtime_payload_persisted", true],
  ])("rejects malformed durable event field %s", async (field, replacement) => {
    const event = {
      event_ref: "runtime-run-event-ref:goal-client:test",
      event_kind: "receipt_recorded" as const,
      runtime_run_ref: "runtime-run-ref:goal-client:test",
      uaa_durable_run_ref: "runtime-run-ref:goal-client:test",
      proof_ref: "proof-ref:goal-client:test",
      redaction_status: "redacted_safe_refs_only",
      safe_summary: "A durable receipt was recorded with bounded safe refs.",
      sequence: 1,
      recorded_at: "2026-07-25T00:00:00Z",
      predecessor_hash_ref: null,
      event_hash_ref: "event-hash-ref:goal-client:test",
      proof_refs: ["proof-ref:goal-client:test"],
      receipt_refs: ["receipt-ref:goal-client:test"],
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
  });
});
