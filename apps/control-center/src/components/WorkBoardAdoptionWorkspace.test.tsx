import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { BackendTruthReadBinding } from "../api/client";
import type {
  WorkBoardAdoptionMutationPreview,
  WorkBoardAdoptionMutationReceipt,
  WorkBoardAdoptionRestorePreview,
  WorkBoardAdoptionWorkspaceView,
} from "../api/types";
import { BackendTruthMutationBindingProvider } from "../backendTruthMutationBinding";
import { mockControlCenterData } from "../mocks/controlCenterData";
import { WorkBoardSurface } from "../northstar/PrimarySurfaces";
import {
  restoreReviewDetail,
  WorkBoardAdoptionWorkspace,
} from "./WorkBoardAdoptionWorkspace";

const apiMocks = vi.hoisted(() => ({
  captureWorkBoardAdoptionApproval: vi.fn(),
  captureWorkBoardAdoptionRestoreApproval: vi.fn(),
  commitWorkBoardAdoptionMutation: vi.fn(),
  commitWorkBoardAdoptionRestore: vi.fn(),
  createWorkBoardAdoptionBackup: vi.fn(),
  loadWorkBoardAdoptionWorkspace: vi.fn(),
  previewWorkBoardAdoptionMutation: vi.fn(),
  previewWorkBoardAdoptionRestore: vi.fn(),
}));

vi.mock("../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api/client")>()),
  ...apiMocks,
}));

const workspace: WorkBoardAdoptionWorkspaceView = {
  schema_version: "uaa-work-board-adoption-read-model.v1",
  contract_ref: "contract-ref:queue-v2-q33-work-board-adoption:v1",
  board_ref: "work-board-ref:founder-private",
  status: "ready",
  revision: 3,
  current_state_ref: "state-ref:work-board-adoption:sha256:test",
  active_cards: [
    {
      card_ref: "work-board-card-ref:founder-private:test",
      title: "Prepare founder briefing",
      description: "Review local evidence.",
      priority: "high",
      lane_ref: "work-board-lane:planned",
      tag_refs: ["tag-ref:work-board:founder"],
      archived: false,
    },
  ],
  archived_cards: [],
  lane_refs: [
    "work-board-lane:inbox",
    "work-board-lane:planned",
    "work-board-lane:doing",
    "work-board-lane:done",
  ],
  can_undo: true,
  latest_receipt_ref: "receipt-ref:work-board-adoption:test",
  next_safe_action: "Create or update a private card.",
  backend_owned: true,
  local_only: true,
  exact_approval_required: true,
  backup_restore_available: true,
  task_execution_enabled: false,
  connector_write_enabled: false,
  provider_model_call_enabled: false,
  shell_subprocess_execution_enabled: false,
  browser_automation_enabled: false,
  background_autonomy_enabled: false,
  production_authority_enabled: false,
};

const preview: WorkBoardAdoptionMutationPreview = {
  schema_version: "uaa-work-board-adoption-mutation-preview.v1",
  contract_ref: workspace.contract_ref,
  action: "create",
  expected_revision: 3,
  resulting_revision: 4,
  target_ref: null,
  card_ref: "work-board-card-ref:founder-private:new",
  payload_fingerprint_ref: "payload-fingerprint-ref:work-board-adoption:test",
  preview_ref: "preview-ref:work-board-adoption:test",
  approval_ref: "approval-ref:work-board-adoption:test",
  safe_summary: "Create one founder-private local Work Board item.",
  mutation_performed: false,
  external_write_performed: false,
};

const receipt: WorkBoardAdoptionMutationReceipt = {
  schema_version: "uaa-work-board-adoption-mutation-receipt.v1",
  contract_ref: workspace.contract_ref,
  action: "create",
  target_ref: null,
  card_ref: "work-board-card-ref:founder-private:new",
  before_revision: 3,
  after_revision: 4,
  idempotency_ref: "idempotency-ref:work-board-adoption-ui:create:test",
  payload_fingerprint_ref: preview.payload_fingerprint_ref,
  preview_ref: preview.preview_ref,
  approval_ref: preview.approval_ref,
  approval_validation_ref: "approval-decision-ref:work-board:test",
  approval_expires_at: "2026-09-11T10:00:00Z",
  authority_decision_ref: "authority-decision-ref:work-board:test",
  authority_lease_ref: "authority-lease-ref:work-board:test",
  receipt_ref: "receipt-ref:work-board-adoption:new",
  state_ref: "state-ref:work-board-adoption:new",
  rollback_ref: "rollback-ref:work-board-adoption:new",
  safe_disable_ref: "safe-disable-ref:work-board-adoption-local-write:deny",
  safe_summary: "One local Work Board change was persisted.",
  replayed: false,
  task_execution_performed: false,
  connector_write_performed: false,
  provider_model_call_performed: false,
  shell_subprocess_execution_performed: false,
  browser_automation_performed: false,
  background_autonomy_performed: false,
  production_authority_enabled: false,
};

const mutationBinding: BackendTruthReadBinding = {
  snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
  backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
  backendInstanceRef:
    "backend-instance-ref:control-center:22222222222222222222222222222222",
};

describe("WorkBoardAdoptionWorkspace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.loadWorkBoardAdoptionWorkspace.mockResolvedValue(workspace);
    apiMocks.previewWorkBoardAdoptionMutation.mockResolvedValue(preview);
    apiMocks.captureWorkBoardAdoptionApproval.mockResolvedValue({});
    apiMocks.commitWorkBoardAdoptionMutation.mockResolvedValue(receipt);
  });

  it("distinguishes an empty restore target from unreadable current state", () => {
    const restorePreview = {
      action: "restore_backup" as const,
      card_count: 1,
      rollback_available: false,
      impact_status: "exact" as const,
    } as WorkBoardAdoptionRestorePreview;

    expect(restoreReviewDetail(restorePreview)).toBe(
      "1 card; the current workspace is empty, so there is no prior state to undo.",
    );
    expect(
      restoreReviewDetail({
        ...restorePreview,
        impact_status: "unknown_current_state",
      }),
    ).toBe(
      "1 card; current state is unreadable, so rollback is unavailable.",
    );
  });

  it("mounts the writable private workspace before the legacy board", async () => {
    render(<WorkBoardSurface data={structuredClone(mockControlCenterData)} />);

    expect(
      await screen.findByRole("heading", { name: "Your Work Board" }),
    ).toBeVisible();
    expect(
      screen.getByText("Legacy Work Board compatibility cockpit").closest("details"),
    ).not.toHaveAttribute("open");
    expect(
      screen.getByText(/does not run tasks, call models, or write to connectors/i),
    ).toBeVisible();
  });

  it("previews, confirms, and commits one backend-owned card", async () => {
    render(
      <BackendTruthMutationBindingProvider binding={mutationBinding}>
        <WorkBoardAdoptionWorkspace />
      </BackendTruthMutationBindingProvider>,
    );
    await screen.findAllByText("Prepare founder briefing");

    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Plan customer interviews" },
    });
    fireEvent.change(screen.getByLabelText("Tags, separated by commas"), {
      target: { value: "research, founder" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Review before saving" }));

    await screen.findByRole("dialog", {
      name: "Review this Work Board change",
    });
    expect(
      screen.getByText(/Create new card .* Title: “Plan customer interviews”/),
    ).toBeVisible();
    expect(
      screen.getByText(/Priority: medium\. Lane: Inbox\. Tags: tag-ref:work-board:research, tag-ref:work-board:founder/),
    ).toBeVisible();
    const [request, idempotencyRef] =
      apiMocks.previewWorkBoardAdoptionMutation.mock.calls[0];
    expect(request).toMatchObject({
      action: "create",
      expected_revision: 3,
      draft: {
        title: "Plan customer interviews",
        tag_refs: [
          "tag-ref:work-board:research",
          "tag-ref:work-board:founder",
        ],
      },
    });

    fireEvent.click(
      screen.getByRole("button", { name: "Confirm and save locally" }),
    );
    await waitFor(() =>
      expect(apiMocks.commitWorkBoardAdoptionMutation).toHaveBeenCalledTimes(1),
    );
    expect(apiMocks.captureWorkBoardAdoptionApproval).toHaveBeenCalledWith(
      request,
      preview,
      idempotencyRef,
      mutationBinding,
    );
    expect(apiMocks.commitWorkBoardAdoptionMutation).toHaveBeenCalledWith(
      request,
      preview,
      idempotencyRef,
      mutationBinding,
    );
  });

  it("previews a lane move instead of changing presentation state only", async () => {
    render(<WorkBoardAdoptionWorkspace />);
    await screen.findAllByText("Prepare founder briefing");

    fireEvent.change(screen.getByLabelText("Move Prepare founder briefing"), {
      target: { value: "work-board-lane:doing" },
    });

    await waitFor(() =>
      expect(apiMocks.previewWorkBoardAdoptionMutation).toHaveBeenCalledWith(
        {
          action: "move",
          expected_revision: 3,
          target_ref: "work-board-card-ref:founder-private:test",
          lane_ref: "work-board-lane:doing",
        },
        expect.stringMatching(/^idempotency-ref:work-board-adoption-ui:move:/),
      ),
    );
    expect(
      screen.getByRole("dialog", { name: "Review this Work Board change" }),
    ).toBeVisible();
    expect(
      screen.getByText(
        /Move card work-board-card-ref:founder-private:test to Doing\. Revision 3 → 4\./,
      ),
    ).toBeVisible();
  });

  it("preserves backend-owned tag refs while editing another field", async () => {
    apiMocks.loadWorkBoardAdoptionWorkspace.mockResolvedValue({
      ...workspace,
      active_cards: [
        {
          ...workspace.active_cards[0],
          tag_refs: ["tag-ref:founder"],
        },
      ],
    });
    apiMocks.previewWorkBoardAdoptionMutation.mockResolvedValue({
      ...preview,
      action: "update",
      target_ref: workspace.active_cards[0].card_ref,
      card_ref: workspace.active_cards[0].card_ref,
    });
    render(<WorkBoardAdoptionWorkspace />);
    await screen.findAllByText("Prepare founder briefing");

    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    expect(screen.getByLabelText("Tags, separated by commas")).toHaveValue(
      "tag-ref:founder",
    );
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Prepare revised founder briefing" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Review before saving" }));

    await waitFor(() =>
      expect(apiMocks.previewWorkBoardAdoptionMutation).toHaveBeenCalledWith(
        expect.objectContaining({
          action: "update",
          draft: expect.objectContaining({
            title: "Prepare revised founder briefing",
            tag_refs: ["tag-ref:founder"],
          }),
        }),
        expect.stringMatching(/^idempotency-ref:work-board-adoption-ui:update:/),
      ),
    );
  });

  it("blocks ordinary edits while preserving the recovery controls", async () => {
    apiMocks.loadWorkBoardAdoptionWorkspace.mockResolvedValue({
      ...workspace,
      status: "recovery_required",
      active_cards: [],
      archived_cards: [],
      can_undo: false,
      next_safe_action: "Restore a verified encrypted backup.",
    });
    render(<WorkBoardAdoptionWorkspace />);

    expect(await screen.findByText("Ordinary board changes are paused")).toBeVisible();
    expect(screen.getByRole("button", { name: "Review before saving" })).toBeDisabled();
    expect(screen.getByText("Open backup to restore")).toBeVisible();
  });
});
