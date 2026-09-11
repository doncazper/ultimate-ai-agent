import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { BackendTruthReadBinding } from "../api/client";
import type {
  CalendarAdoptionMutationPreview,
  CalendarAdoptionMutationReceipt,
  CalendarAdoptionWorkspaceView,
} from "../api/types";
import { BackendTruthMutationBindingProvider } from "../backendTruthMutationBinding";
import { mockControlCenterData } from "../mocks/controlCenterData";
import { CalendarSurface } from "../northstar/PrimarySurfaces";
import { CalendarAdoptionWorkspace } from "./CalendarAdoptionWorkspace";

const apiMocks = vi.hoisted(() => ({
  captureCalendarAdoptionApproval: vi.fn(),
  captureCalendarAdoptionRestoreApproval: vi.fn(),
  commitCalendarAdoptionMutation: vi.fn(),
  commitCalendarAdoptionRestore: vi.fn(),
  createCalendarAdoptionBackup: vi.fn(),
  loadCalendarAdoptionWorkspace: vi.fn(),
  previewCalendarAdoptionMutation: vi.fn(),
  previewCalendarAdoptionRestore: vi.fn(),
}));

vi.mock("../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api/client")>()),
  ...apiMocks,
}));

const workspace: CalendarAdoptionWorkspaceView = {
  schema_version: "uaa-calendar-adoption-read-model.v1",
  contract_ref: "contract-ref:queue-v2-q33-calendar-adoption:v1",
  status: "ready",
  workspace_ref: "workspace-ref:founder-private-calendar",
  calendar_set_ref: "calendar-set-ref:founder-private",
  revision: 4,
  current_state_ref: "state-ref:calendar-adoption:sha256:test",
  calendar_set_name: "My Calendar",
  calendars: [
    {
      calendar_ref: "calendar-ref:q33:personal",
      name: "Personal",
      timezone: "America/Los_Angeles",
      color_ref: "color-ref:q33:blue",
      archived: false,
    },
  ],
  occurrence_items: [
    {
      event: {
        event_ref: "calendar-event-ref:q33:briefing",
        calendar_ref: "calendar-ref:q33:personal",
        title: "Founder briefing",
        description: "Review the private plan.",
        location: "Office",
        starts_at: "2026-09-14T16:00:00Z",
        ends_at: "2026-09-14T17:00:00Z",
        timezone: "America/Los_Angeles",
        all_day: false,
        participant_items: [],
        reminder_items: [],
        recurrence: null,
        task_ref: null,
        archived: false,
      },
      occurrence: {
        occurrence_ref: "calendar-occurrence-ref:q33:briefing",
        event_ref: "calendar-event-ref:q33:briefing",
        calendar_ref: "calendar-ref:q33:personal",
        starts_at: "2026-09-14T16:00:00Z",
        ends_at: "2026-09-14T17:00:00Z",
        timezone: "America/Los_Angeles",
      },
      canonical_owner_ref: "canonical-owner-ref:calendar",
      field_provenance_refs: ["calendar-event-ref:q33:briefing"],
      projection_state: "current",
    },
  ],
  archived_events: [],
  conflict_items: [],
  view: "week",
  timezone: "America/Los_Angeles",
  range_starts_at: "2026-09-14T07:00:00Z",
  range_ends_at: "2026-09-21T07:00:00Z",
  result_ref: "calendar-view-result-ref:q33:test",
  can_undo: true,
  next_safe_action: "Create or edit an event.",
  backend_owned: true,
  local_only: true,
  exact_approval_required: true,
  backup_restore_available: true,
  external_calendar_write_enabled: false,
  connector_read_enabled: false,
  connector_write_enabled: false,
  provider_model_call_enabled: false,
  browser_automation_enabled: false,
  shell_subprocess_execution_enabled: false,
  background_scheduling_enabled: false,
  notification_delivery_enabled: false,
  production_authority_enabled: false,
};

const preview: CalendarAdoptionMutationPreview = {
  schema_version: "uaa-calendar-adoption-mutation-preview.v1",
  contract_ref: workspace.contract_ref,
  action: "create_event",
  expected_revision: 4,
  resulting_revision: 5,
  target_ref: null,
  payload_fingerprint_ref: "payload-fingerprint-ref:calendar-adoption:test",
  preview_ref: "preview-ref:calendar-adoption:test",
  approval_ref: "approval-ref:calendar-adoption:test",
  operation_ref: "operation-ref:calendar-adoption:test",
  safe_summary: "Apply one exact private local Calendar lifecycle change.",
  mutation_performed: false,
  external_write_performed: false,
};

const receipt: CalendarAdoptionMutationReceipt = {
  schema_version: "uaa-calendar-adoption-mutation-receipt.v1",
  contract_ref: workspace.contract_ref,
  action: "create_event",
  target_ref: null,
  before_revision: 4,
  after_revision: 5,
  idempotency_ref: "idempotency-ref:calendar-adoption-ui:create:test",
  payload_fingerprint_ref: preview.payload_fingerprint_ref,
  preview_ref: preview.preview_ref,
  approval_ref: preview.approval_ref,
  approval_validation_ref: "appr_dec_123456789abc",
  approval_expires_at: "2026-09-11T20:00:00Z",
  authority_decision_ref: "authority-policy-decision-ref:calendar:test",
  authority_lease_ref: "authority-lease-ref:calendar:test",
  operation_ref: preview.operation_ref,
  receipt_ref: "receipt-ref:calendar-adoption:test",
  operation_receipt_refs: ["operation-receipt-ref:calendar:test"],
  backup_fingerprint_ref: null,
  state_ref: "state-ref:calendar-adoption-receipt:test",
  rollback_ref: "rollback-ref:calendar-adoption:test",
  safe_disable_ref: "safe-disable-ref:calendar-adoption-local-write:deny",
  replayed: false,
  local_calendar_write_performed: true,
  external_calendar_write_performed: false,
  connector_write_performed: false,
  provider_model_call_performed: false,
  shell_subprocess_execution_performed: false,
  browser_automation_performed: false,
  background_scheduling_performed: false,
  notification_delivery_performed: false,
  production_authority_enabled: false,
};

const binding: BackendTruthReadBinding = {
  snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
  backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
  backendInstanceRef:
    "backend-instance-ref:control-center:22222222222222222222222222222222",
};

describe("CalendarAdoptionWorkspace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.loadCalendarAdoptionWorkspace.mockResolvedValue(workspace);
    apiMocks.previewCalendarAdoptionMutation.mockResolvedValue(preview);
    apiMocks.captureCalendarAdoptionApproval.mockResolvedValue({});
    apiMocks.commitCalendarAdoptionMutation.mockResolvedValue(receipt);
  });

  it("mounts the private Calendar before the legacy synthetic reference", async () => {
    render(<CalendarSurface data={structuredClone(mockControlCenterData)} />);

    expect(await screen.findByRole("heading", { name: "Your Calendar" })).toBeVisible();
    expect(screen.getByText("Legacy synthetic Calendar layout reference").closest("details")).not.toHaveAttribute("open");
    expect(screen.getByText(/No account, connector, notification, or external calendar is touched/i)).toBeVisible();
  });

  it("switches readable views using backend-owned projections", async () => {
    render(<CalendarAdoptionWorkspace />);
    await screen.findAllByText("Founder briefing");
    fireEvent.click(screen.getByRole("button", { name: "month" }));
    await waitFor(() => expect(apiMocks.loadCalendarAdoptionWorkspace).toHaveBeenLastCalledWith("month", expect.any(String), expect.any(String)));
  });

  it("previews and confirms one exact local event change", async () => {
    render(<BackendTruthMutationBindingProvider binding={binding}><CalendarAdoptionWorkspace /></BackendTruthMutationBindingProvider>);
    await screen.findAllByText("Founder briefing");
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Review acquisition pipeline" } });
    fireEvent.click(screen.getByRole("button", { name: "Review new event" }));
    expect(await screen.findByRole("dialog", { name: "Review this Calendar change" })).toBeVisible();
    expect(screen.getByText(/Only the encrypted local Calendar will change/i)).toBeVisible();

    const [request] = apiMocks.previewCalendarAdoptionMutation.mock.calls[0];
    expect(request).toMatchObject({ action: "create_event", expected_revision: 4, event: { title: "Review acquisition pipeline", calendar_ref: "calendar-ref:q33:personal" } });
    fireEvent.click(screen.getByRole("button", { name: "Confirm one local change" }));
    await waitFor(() => expect(apiMocks.commitCalendarAdoptionMutation).toHaveBeenCalledTimes(1));
    expect(apiMocks.captureCalendarAdoptionApproval).toHaveBeenCalledWith(request, preview, expect.stringMatching(/^idempotency-ref:calendar-adoption-ui:create-event:/), binding);
  });
});
