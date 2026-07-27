import { afterEach, describe, expect, it, vi } from "vitest";
import {
  createRuntimeGoal,
  editRuntimeGoal,
  transitionRuntimeGoal,
  type BackendTruthReadBinding,
} from "./client";
import { API_ENDPOINTS } from "./endpoints";
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
});
