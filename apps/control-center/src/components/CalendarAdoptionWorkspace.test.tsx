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
import {
  CalendarAdoptionWorkspace,
  shiftCalendarAnchor,
} from "./CalendarAdoptionWorkspace";

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
    apiMocks.previewCalendarAdoptionRestore.mockResolvedValue({
      expected_revision: 0,
      resulting_revision: 1,
      calendar_count: 1,
      event_count: 1,
      rollback_available: false,
      impact_status: "empty_target",
      preview_ref: "preview-ref:calendar-adoption-restore:test",
      approval_ref: "approval-ref:calendar-adoption-restore:test",
    });
    apiMocks.captureCalendarAdoptionRestoreApproval.mockResolvedValue({});
    apiMocks.commitCalendarAdoptionRestore.mockResolvedValue({
      ...receipt,
      action: "restore_backup",
      after_revision: 1,
    });
  });

  it("mounts the private Calendar before the legacy synthetic reference", async () => {
    render(<CalendarSurface data={structuredClone(mockControlCenterData)} />);

    expect(
      await screen.findByRole("heading", { name: "Your Calendar" }),
    ).toBeVisible();
    expect(
      screen
        .getByText("Legacy synthetic Calendar layout reference")
        .closest("details"),
    ).not.toHaveAttribute("open");
    expect(
      screen.getByText(
        /No account, connector, notification, or external calendar is touched/i,
      ),
    ).toBeVisible();
  });

  it("switches readable views using backend-owned projections", async () => {
    render(<CalendarAdoptionWorkspace />);
    await screen.findAllByText("Founder briefing");
    fireEvent.click(screen.getByRole("button", { name: "month" }));
    await waitFor(() =>
      expect(apiMocks.loadCalendarAdoptionWorkspace).toHaveBeenLastCalledWith(
        "month",
        expect.any(String),
        expect.any(String),
      ),
    );
  });

  it("previews and confirms one exact local event change", async () => {
    render(
      <BackendTruthMutationBindingProvider binding={binding}>
        <CalendarAdoptionWorkspace />
      </BackendTruthMutationBindingProvider>,
    );
    await screen.findAllByText("Founder briefing");
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Review acquisition pipeline" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Review new event" }));
    expect(
      await screen.findByRole("dialog", {
        name: "Review this Calendar change",
      }),
    ).toBeVisible();
    expect(
      screen.getByText(/Only the encrypted local Calendar will change/i),
    ).toBeVisible();
    expect(
      screen.getByText(/Calendar: calendar-ref:q33:personal/),
    ).toBeVisible();
    expect(screen.getByText(/All day: no/)).toBeVisible();
    expect(screen.getByText(/Location: none; Notes: none/)).toBeVisible();
    expect(screen.getByText(/Repeats: none/)).toBeVisible();

    const [request] = apiMocks.previewCalendarAdoptionMutation.mock.calls[0];
    expect(request).toMatchObject({
      action: "create_event",
      expected_revision: 4,
      event: {
        title: "Review acquisition pipeline",
        calendar_ref: "calendar-ref:q33:personal",
      },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Confirm one local change" }),
    );
    await waitFor(() =>
      expect(apiMocks.commitCalendarAdoptionMutation).toHaveBeenCalledTimes(1),
    );
    expect(apiMocks.captureCalendarAdoptionApproval).toHaveBeenCalledWith(
      request,
      preview,
      expect.stringMatching(
        /^idempotency-ref:calendar-adoption-ui:create-event:/,
      ),
      binding,
    );
  });

  it("preserves all-day and event-timezone values during an edit", async () => {
    const tokyo = structuredClone(workspace);
    tokyo.occurrence_items[0].event.timezone = "Asia/Tokyo";
    tokyo.occurrence_items[0].event.starts_at = "2026-09-14T00:00:00Z";
    tokyo.occurrence_items[0].event.ends_at = "2026-09-14T01:00:00Z";
    tokyo.occurrence_items[0].event.all_day = true;
    tokyo.occurrence_items[0].occurrence.starts_at = "2026-09-14T00:00:00Z";
    tokyo.occurrence_items[0].occurrence.ends_at = "2026-09-14T01:00:00Z";
    apiMocks.loadCalendarAdoptionWorkspace.mockResolvedValue(tokyo);

    render(<CalendarAdoptionWorkspace />);
    fireEvent.click(
      await screen.findByRole("button", { name: /Founder briefing/ }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    expect(screen.getByLabelText("Starts")).toHaveValue("2026-09-14T09:00");
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Updated founder briefing" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Review update" }));

    expect(
      await screen.findByText(
        /Starts: Sep 14, 2026, 9:00 AM \(Asia\/Tokyo\); Ends: Sep 14, 2026, 10:00 AM \(Asia\/Tokyo\)/,
      ),
    ).toBeVisible();

    await waitFor(() =>
      expect(apiMocks.previewCalendarAdoptionMutation).toHaveBeenCalled(),
    );
    const [request] = apiMocks.previewCalendarAdoptionMutation.mock.calls[0];
    expect(request.event).toMatchObject({
      all_day: true,
      timezone: "Asia/Tokyo",
      starts_at: "2026-09-14T00:00:00Z",
      ends_at: "2026-09-14T01:00:00Z",
    });
  });

  it("preserves the chosen offset when editing a repeated local wall time", async () => {
    const repeated = structuredClone(workspace);
    repeated.occurrence_items[0].event.starts_at = "2026-11-01T09:30:00Z";
    repeated.occurrence_items[0].event.ends_at = "2026-11-01T10:30:00Z";
    repeated.occurrence_items[0].occurrence.starts_at = "2026-11-01T09:30:00Z";
    repeated.occurrence_items[0].occurrence.ends_at = "2026-11-01T10:30:00Z";
    apiMocks.loadCalendarAdoptionWorkspace.mockResolvedValue(repeated);

    render(<CalendarAdoptionWorkspace />);
    fireEvent.click(
      await screen.findByRole("button", { name: /Founder briefing/ }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    expect(screen.getByLabelText("Starts")).toHaveValue("2026-11-01T01:30");
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Repeated-hour title edit" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Review update" }));

    await waitFor(() =>
      expect(apiMocks.previewCalendarAdoptionMutation).toHaveBeenCalled(),
    );
    const [request] = apiMocks.previewCalendarAdoptionMutation.mock.calls[0];
    expect(request.event.starts_at).toBe("2026-11-01T09:30:00Z");
    expect(request.event.ends_at).toBe("2026-11-01T10:30:00Z");
  });

  it("preserves multi-day weekly recurrence on unrelated edits", async () => {
    const recurring = structuredClone(workspace);
    recurring.occurrence_items[0].event.recurrence = {
      frequency: "weekly",
      interval: 1,
      weekdays: [0, 2],
      timezone: "America/Los_Angeles",
    };
    apiMocks.loadCalendarAdoptionWorkspace.mockResolvedValue(recurring);

    render(<CalendarAdoptionWorkspace />);
    fireEvent.click(
      await screen.findByRole("button", { name: /Founder briefing/ }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Updated multi-day series" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Review update" }));

    await waitFor(() =>
      expect(apiMocks.previewCalendarAdoptionMutation).toHaveBeenCalled(),
    );
    const [request] = apiMocks.previewCalendarAdoptionMutation.mock.calls[0];
    expect(request.event.recurrence.weekdays).toEqual([0, 2]);
    expect(
      await screen.findByText(
        /Repeats: weekly; interval 1; timezone America\/Los_Angeles; weekdays Monday \(0\), Wednesday \(2\); month day none; count none; until none/,
      ),
    ).toBeVisible();
  });

  it("resets a cancelled edit to the first active calendar", async () => {
    const mixed = structuredClone(workspace);
    mixed.calendars = [
      { ...mixed.calendars[0], archived: true },
      {
        ...mixed.calendars[0],
        calendar_ref: "calendar-ref:q33:active",
        name: "Active",
        archived: false,
      },
    ];
    apiMocks.loadCalendarAdoptionWorkspace.mockResolvedValue(mixed);

    render(<CalendarAdoptionWorkspace />);
    fireEvent.click(
      await screen.findByRole("button", { name: /Founder briefing/ }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    fireEvent.click(screen.getByRole("button", { name: "Cancel edit" }));

    expect(screen.getByLabelText("Calendar")).toHaveValue(
      "calendar-ref:q33:active",
    );
  });

  it("recomputes weekly recurrence after the start date changes", async () => {
    render(<CalendarAdoptionWorkspace />);
    await screen.findAllByText("Founder briefing");
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Tuesday planning" },
    });
    fireEvent.change(screen.getByLabelText("Repeats"), {
      target: { value: "weekly" },
    });
    fireEvent.change(screen.getByLabelText("Starts"), {
      target: { value: "2026-09-15T09:00" },
    });
    fireEvent.change(screen.getByLabelText("Ends"), {
      target: { value: "2026-09-15T10:00" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Review new event" }));

    await waitFor(() =>
      expect(apiMocks.previewCalendarAdoptionMutation).toHaveBeenCalled(),
    );
    const [request] = apiMocks.previewCalendarAdoptionMutation.mock.calls[0];
    expect(request.event.recurrence.weekdays).toEqual([1]);
  });

  it("submits new-event wall times in the selected Calendar timezone", async () => {
    const hostOptions = new Intl.DateTimeFormat().resolvedOptions();
    const timezoneSpy = vi
      .spyOn(Intl.DateTimeFormat.prototype, "resolvedOptions")
      .mockReturnValue({ ...hostOptions, timeZone: "UTC" });
    try {
      render(<CalendarAdoptionWorkspace />);
      await screen.findAllByText("Founder briefing");
      fireEvent.change(screen.getByLabelText("Calendar timezone"), {
        target: { value: "America/Los_Angeles" },
      });
      fireEvent.click(screen.getByRole("button", { name: "Apply timezone" }));
      fireEvent.change(screen.getByLabelText("Title"), {
        target: { value: "Los Angeles planning" },
      });
      fireEvent.change(screen.getByLabelText("Starts"), {
        target: { value: "2026-09-15T09:00" },
      });
      fireEvent.change(screen.getByLabelText("Ends"), {
        target: { value: "2026-09-15T10:00" },
      });
      fireEvent.click(screen.getByRole("button", { name: "Review new event" }));

      await waitFor(() =>
        expect(apiMocks.previewCalendarAdoptionMutation).toHaveBeenCalled(),
      );
      const [request] = apiMocks.previewCalendarAdoptionMutation.mock.calls[0];
      expect(request.event).toMatchObject({
        timezone: "America/Los_Angeles",
        starts_at: "2026-09-15T16:00:00.000Z",
        ends_at: "2026-09-15T17:00:00.000Z",
      });
    } finally {
      timezoneSpy.mockRestore();
    }
  });

  it("keeps the clicked recurrence occurrence in the inspector", async () => {
    const recurring = structuredClone(workspace);
    recurring.occurrence_items.push({
      ...structuredClone(recurring.occurrence_items[0]),
      occurrence: {
        ...structuredClone(recurring.occurrence_items[0].occurrence),
        occurrence_ref: "calendar-occurrence-ref:q33:briefing:second",
        starts_at: "2026-09-21T16:00:00Z",
        ends_at: "2026-09-21T17:00:00Z",
      },
    });
    apiMocks.loadCalendarAdoptionWorkspace.mockResolvedValue(recurring);

    render(<CalendarAdoptionWorkspace />);
    const occurrences = await screen.findAllByRole("button", {
      name: /Founder briefing/,
    });
    fireEvent.click(occurrences[1]);

    expect(screen.getByText(/Sep 21, 2026/)).toBeVisible();
  });

  it("labels the final included date and clamps month navigation", async () => {
    const hostOptions = new Intl.DateTimeFormat().resolvedOptions();
    const timezoneSpy = vi
      .spyOn(Intl.DateTimeFormat.prototype, "resolvedOptions")
      .mockReturnValue({
        ...hostOptions,
        timeZone: "America/Los_Angeles",
      });
    try {
      render(<CalendarAdoptionWorkspace />);

      expect(await screen.findByText(/through Sep 20/)).toBeVisible();
      expect(
        shiftCalendarAnchor(
          "2026-01-31T20:00:00Z",
          "month",
          1,
          "America/Los_Angeles",
        ),
      ).toBe("2026-02-28T20:00:00.000Z");
      expect(
        shiftCalendarAnchor(
          "2026-03-31T19:00:00Z",
          "month",
          -1,
          "America/Los_Angeles",
        ),
      ).toBe("2026-02-28T20:00:00.000Z");
    } finally {
      timezoneSpy.mockRestore();
    }
  });

  it("normalizes period navigation across a nonexistent local wall time", () => {
    expect(
      shiftCalendarAnchor(
        "2026-03-07T10:30:00Z",
        "day",
        1,
        "America/Los_Angeles",
      ),
    ).toBe("2026-03-08T19:00:00.000Z");
  });

  it("clears a stale load error after a successful refresh", async () => {
    apiMocks.loadCalendarAdoptionWorkspace
      .mockRejectedValueOnce(new Error("Calendar load failed safely."))
      .mockResolvedValueOnce(workspace);

    render(<CalendarAdoptionWorkspace />);
    expect(
      await screen.findByText("Calendar load failed safely."),
    ).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));

    expect(await screen.findAllByText("Founder briefing")).not.toHaveLength(0);
    expect(
      screen.queryByText("Calendar load failed safely."),
    ).not.toBeInTheDocument();
  });

  it.each(["onboarding", "setup_incomplete", "recovery_required"] as const)(
    "offers encrypted restore while the workspace is %s",
    async (status) => {
      apiMocks.loadCalendarAdoptionWorkspace.mockResolvedValue({
        ...structuredClone(workspace),
        status,
        calendars: [],
        occurrence_items: [],
      });

      render(<CalendarAdoptionWorkspace />);

      expect(await screen.findByLabelText("Open backup")).toBeVisible();
      expect(
        screen.queryByRole("button", { name: "Download encrypted backup" }),
      ).not.toBeInTheDocument();
    },
  );

  it("allows setup initialization to resume from setup_incomplete", async () => {
    apiMocks.loadCalendarAdoptionWorkspace.mockResolvedValue({
      ...structuredClone(workspace),
      status: "setup_incomplete",
      revision: 0,
      calendars: [],
      occurrence_items: [],
    });

    render(<CalendarAdoptionWorkspace />);
    expect(
      await screen.findByRole("heading", {
        name: "Finish your private calendar setup",
      }),
    ).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Review setup" }));

    await waitFor(() =>
      expect(apiMocks.previewCalendarAdoptionMutation).toHaveBeenCalled(),
    );
    expect(apiMocks.previewCalendarAdoptionMutation.mock.calls[0][0]).toMatchObject({
      action: "initialize",
      expected_revision: 0,
    });
  });

  it("resets a stale event draft after restore replaces its calendar", async () => {
    const restored = structuredClone(workspace);
    restored.revision = 1;
    restored.calendars[0].calendar_ref = "calendar-ref:q33:restored";
    restored.occurrence_items[0].event.calendar_ref =
      "calendar-ref:q33:restored";
    apiMocks.loadCalendarAdoptionWorkspace
      .mockResolvedValueOnce(workspace)
      .mockResolvedValueOnce(restored);

    render(<CalendarAdoptionWorkspace />);
    await screen.findAllByText("Founder briefing");
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Stale draft" },
    });
    const file = new File(
      [JSON.stringify({ encrypted: true })],
      "calendar.json",
      {
        type: "application/json",
      },
    );
    fireEvent.change(screen.getByLabelText("Open backup"), {
      target: { files: [file] },
    });
    fireEvent.change(screen.getByLabelText("Backup or restore passphrase"), {
      target: { value: "a safe test passphrase" },
    });
    fireEvent.click(
      await screen.findByRole("button", { name: "Preview restore" }),
    );
    fireEvent.click(
      await screen.findByRole("button", { name: "Confirm private restore" }),
    );

    await waitFor(() =>
      expect(apiMocks.commitCalendarAdoptionRestore).toHaveBeenCalled(),
    );
    await waitFor(() =>
      expect(screen.getByLabelText("Calendar")).toHaveValue(
        "calendar-ref:q33:restored",
      ),
    );
    expect(screen.getByLabelText("Title")).toHaveValue("");
  });

  it("warns when restore replaces state without retaining undo", async () => {
    apiMocks.previewCalendarAdoptionRestore.mockResolvedValue({
      expected_revision: 4,
      resulting_revision: 5,
      calendar_count: 1,
      event_count: 1,
      rollback_available: false,
      impact_status: "exact",
      preview_ref: "preview-ref:calendar-adoption-restore:test",
      approval_ref: "approval-ref:calendar-adoption-restore:test",
    });

    render(<CalendarAdoptionWorkspace />);
    await screen.findAllByText("Founder briefing");
    const file = new File(
      [JSON.stringify({ encrypted: true })],
      "calendar.json",
      { type: "application/json" },
    );
    fireEvent.change(screen.getByLabelText("Open backup"), {
      target: { files: [file] },
    });
    fireEvent.change(screen.getByLabelText("Backup or restore passphrase"), {
      target: { value: "a safe test passphrase" },
    });
    fireEvent.click(
      await screen.findByRole("button", { name: "Preview restore" }),
    );

    expect(
      await screen.findByText(
        "This will replace existing local Calendar state, and undo will not be available.",
        { exact: false },
      ),
    ).toBeVisible();
    expect(screen.queryByText(/The target is empty/)).not.toBeInTheDocument();
  });
});
