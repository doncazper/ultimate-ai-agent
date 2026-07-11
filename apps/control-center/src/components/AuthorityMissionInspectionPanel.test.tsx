import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type {
  AuthorityMissionWorkerJob,
  AuthorityMissionWorkerReadModel,
} from "../api/types";
import { AuthorityMissionInspectionPanel } from "./AuthorityMissionInspectionPanel";

function job(
  suffix: string,
  overrides: Partial<AuthorityMissionWorkerJob>,
): AuthorityMissionWorkerJob {
  return {
    job_safe_ref: `mission-worker-job-safe-ref:sha256:${suffix}`,
    plan_safe_ref: `mission-worker-plan-safe-ref:sha256:${suffix}`,
    mission_safe_ref: `mission-worker-mission-safe-ref:sha256:${suffix}`,
    run_safe_ref: `mission-worker-run-safe-ref:sha256:${suffix}`,
    durable_status: "pending",
    recovery_status: "pending",
    generation: 0,
    latest_event: "enqueued",
    latest_event_at: "2026-07-11T12:00:00Z",
    last_heartbeat_at: null,
    heartbeat_freshness: "not_observed",
    worker_safe_ref: null,
    claim_safe_ref: null,
    claim_expires_at: null,
    retry_not_before: null,
    deadline: "2026-07-11T13:00:00Z",
    steps: [
      {
        step_safe_ref: `mission-worker-step-safe-ref:sha256:${suffix}`,
        status: "pending",
        claim_freshness: "not_claimed",
        generation: 0,
        reason_refs: [],
        evidence_refs: [],
        adapter_reinvocation_allowed: false,
      },
    ],
    reason_refs: [],
    evidence_refs: [],
    request_payload_persisted: false,
    request_scoped_authority_required_before_resume: true,
    ...overrides,
  };
}

const readModel: AuthorityMissionWorkerReadModel = {
  schema_version: "uaa-local-mission-worker.v1",
  inspection_ref: "mission-worker-inspection-ref:sha256:panel",
  configuration_enabled: true,
  canonical_platform: "macos",
  observed_platform: "macos",
  platform_execution_supported: true,
  linux_surface_posture: "render_placeholder",
  windows_surface_posture: "render_placeholder",
  queue_capacity: 16,
  queued_job_count: 2,
  total_job_count: 4,
  omitted_terminal_job_count: 0,
  active_claim_count: 0,
  stale_claim_count: 0,
  kill_switch_engaged: false,
  jobs: [
    job("approval", {
      durable_status: "approval_wait",
      recovery_status: "approval_wait",
      steps: [
        {
          step_safe_ref: "mission-worker-step-safe-ref:sha256:approval",
          status: "approval_wait",
          claim_freshness: "not_claimed",
          generation: 1,
          reason_refs: ["reason-ref:mission-step:approval-required"],
          evidence_refs: ["approval-request-safe-ref:sha256:approval"],
          adapter_reinvocation_allowed: false,
        },
      ],
    }),
    job("retry", {
      durable_status: "retry_pending",
      recovery_status: "retry_pending",
      retry_not_before: "2026-07-11T12:01:00Z",
      steps: [
        {
          step_safe_ref: "mission-worker-step-safe-ref:sha256:retry",
          status: "retry_pending",
          claim_freshness: "not_claimed",
          generation: 1,
          reason_refs: ["reason-ref:mission-step:retry-scheduled"],
          evidence_refs: ["receipt-ref:authority-dispatch:retry"],
          adapter_reinvocation_allowed: false,
        },
      ],
    }),
    job("dead-letter", {
      durable_status: "failed",
      recovery_status: "failed",
      latest_event: "completed",
      steps: [
        {
          step_safe_ref: "mission-worker-step-safe-ref:sha256:dead-letter",
          status: "failed",
          claim_freshness: "not_claimed",
          generation: 2,
          reason_refs: ["reason-ref:mission-step:retry-attempts-exhausted"],
          evidence_refs: ["receipt-ref:authority-dispatch:dead-letter"],
          adapter_reinvocation_allowed: false,
        },
      ],
    }),
    job("cancelled", {
      durable_status: "cancelled",
      recovery_status: "cancelled",
      latest_event: "completed",
      steps: [
        {
          step_safe_ref: "mission-worker-step-safe-ref:sha256:cancelled",
          status: "cancelled",
          claim_freshness: "not_claimed",
          generation: 1,
          reason_refs: ["reason-ref:mission-step:mission-cancelled"],
          evidence_refs: ["mission-control-receipt-ref:cancelled"],
          adapter_reinvocation_allowed: false,
        },
      ],
    }),
  ],
  checked_at: "2026-07-11T12:00:00Z",
  operator_summary:
    "Local macOS mission worker inspection reports durable safe references only.",
  local_only: true,
  execution_authority_granted: false,
  approval_or_lease_minted: false,
  remote_queue_enabled: false,
  daemon_enabled: false,
  raw_task_input_persisted: false,
  raw_paths_included: false,
  raw_logs_included: false,
  raw_provider_payloads_included: false,
  redactions_applied: ["raw_task_inputs", "raw_paths", "raw_logs"],
};

describe("AuthorityMissionInspectionPanel", () => {
  it("renders backend mission lifecycle truth without mutation controls", async () => {
    const loadWorkerState = vi.fn().mockResolvedValue(readModel);
    render(
      <AuthorityMissionInspectionPanel loadWorkerState={loadWorkerState} />,
    );

    const panel = await screen.findByRole("region", {
      name: "Authority mission worker",
    });
    expect(within(panel).getAllByText("approval wait").length).toBeGreaterThan(0);
    expect(within(panel).getAllByText("retry pending").length).toBeGreaterThan(0);
    expect(within(panel).getByText("Dead letter")).toBeInTheDocument();
    expect(within(panel).getAllByText("cancelled").length).toBeGreaterThan(0);
    expect(within(panel).getByText("macOS")).toBeInTheDocument();
    expect(within(panel).getAllByText("render placeholder")).toHaveLength(2);
    expect(
      within(panel).getByText("Authority granted").nextSibling,
    ).toHaveTextContent("no");
    expect(within(panel).queryByRole("button")).not.toBeInTheDocument();
    expect(loadWorkerState).toHaveBeenCalledTimes(1);
  });

  it("fails closed without rendering mock mission truth", async () => {
    render(
      <AuthorityMissionInspectionPanel
        loadWorkerState={vi.fn().mockRejectedValue(new Error("offline"))}
      />,
    );

    expect(
      await screen.findByRole("alert", {
        name: "Authority mission inspection data unavailable",
      }),
    ).toHaveTextContent("No mission capability is treated as active");
    expect(screen.queryByText("approval wait")).not.toBeInTheDocument();
  });
});
