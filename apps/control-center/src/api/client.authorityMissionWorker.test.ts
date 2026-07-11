import { afterEach, describe, expect, it, vi } from "vitest";

import type { AuthorityMissionWorkerReadModel } from "./types";
import {
  fetchAuthorityMissionWorkerState,
  resetControlCenterReadLimiterForTests,
} from "./client";
import { API_ENDPOINTS } from "./endpoints";

const safeReadModel: AuthorityMissionWorkerReadModel = {
  schema_version: "uaa-local-mission-worker.v1",
  inspection_ref: "mission-worker-inspection-ref:sha256:client-test",
  configuration_enabled: false,
  canonical_platform: "macos",
  observed_platform: "macos",
  platform_execution_supported: true,
  linux_surface_posture: "render_placeholder",
  windows_surface_posture: "render_placeholder",
  queue_capacity: 16,
  queued_job_count: 0,
  total_job_count: 0,
  omitted_terminal_job_count: 0,
  active_claim_count: 0,
  stale_claim_count: 0,
  kill_switch_engaged: false,
  jobs: [],
  checked_at: "2026-07-11T12:00:00Z",
  operator_summary:
    "Local mission worker is disabled by default and has no observed jobs.",
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

describe("authority mission worker client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    resetControlCenterReadLimiterForTests();
  });

  it("reads the protected backend-owned worker inspection endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ success: true, data: safeReadModel }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchAuthorityMissionWorkerState()).resolves.toEqual(
      safeReadModel,
    );
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(API_ENDPOINTS.runtimeAuthorityMissionWorkerState),
      expect.objectContaining({
        headers: expect.objectContaining({ Accept: "application/json" }),
      }),
    );
  });

  it("rejects unsafe or authority-minting payloads", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            success: true,
            data: {
              ...safeReadModel,
              execution_authority_granted: true,
              raw_paths_included: true,
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    await expect(fetchAuthorityMissionWorkerState()).rejects.toThrow(
      "unsafe or incompatible",
    );
  });
});
