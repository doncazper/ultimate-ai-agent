import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { BackendTruthReadBinding } from "../api/client";
import type {
  CrmAdoptionMutationPreview,
  CrmAdoptionMutationReceipt,
  CrmAdoptionWorkspaceView,
  CrmPortableBackup,
  CrmPortableRestorePreview,
} from "../api/types";
import { BackendTruthMutationBindingProvider } from "../backendTruthMutationBinding";
import { mockControlCenterData } from "../mocks/controlCenterData";
import { CrmSurface } from "../northstar/PrimarySurfaces";
import {
  CrmAdoptionWorkspace,
  crmLocalDateTimeInputValue,
} from "./CrmAdoptionWorkspace";
import { CrmM1FixtureShellPanel } from "./CrmM1FixtureShellPanel";

const apiMocks = vi.hoisted(() => ({
  captureCrmAdoptionMutationApproval: vi.fn(),
  captureCrmPortableRestoreApproval: vi.fn(),
  commitCrmAdoptionMutation: vi.fn(),
  commitCrmPortableRestore: vi.fn(),
  createCrmPortableBackup: vi.fn(),
  loadCrmAdoptionWorkspace: vi.fn(),
  previewCrmAdoptionMutation: vi.fn(),
  previewCrmPortableRestore: vi.fn(),
}));

vi.mock("../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api/client")>()),
  ...apiMocks,
}));

const workspace: CrmAdoptionWorkspaceView = {
  schema_version: "uaa-crm-adoption-workspace.v1",
  contract_ref: "contract-ref:queue-v2-q32-crm-adoption:v1",
  foundation_contract_ref: "uaa-eco-005-crm-private-portfolio.v1",
  storage_state: "ready",
  revision: 4,
  workspace_name: "Founder private CRM",
  workspace_preset: "founder_private",
  records: [
    {
      record_ref: "crm-record-ref:person:test",
      record_kind: "person",
      display_name: "Example Contact",
      subtitle: "Example Organization",
      email: "contact@example.test",
      phone: null,
      website: null,
      notes: "Synthetic fixture note.",
      tags: ["warm"],
      status: "active",
      related_refs: [],
      due_at: null,
      occurred_at: null,
      amount_minor: null,
      currency: "USD",
      priority: "medium",
      archived: false,
      version: 1,
      created_at: "2026-09-06T17:00:00+00:00",
      updated_at: "2026-09-06T17:00:00+00:00",
    },
  ],
  counts: {
    person: 1,
    organization: 0,
    property: 0,
    relationship: 0,
    opportunity: 0,
    activity: 0,
    follow_up: 0,
  },
  can_undo: true,
  next_safe_action: "Capture or review a local CRM record.",
  private_values_included: true,
  private_values_confined_to_local_response: true,
  raw_paths_included: false,
  fixture_primary_truth: false,
  connector_runtime_enabled: false,
  external_crm_write_enabled: false,
  send_enabled: false,
  provider_model_call_enabled: false,
  production_authority_enabled: false,
};

const preview: CrmAdoptionMutationPreview = {
  schema_version: "uaa-crm-adoption-mutation-preview.v1",
  contract_ref: workspace.contract_ref,
  action: "create",
  expected_revision: 4,
  payload_fingerprint_ref: "payload-fingerprint-ref:crm:test",
  preview_ref: "crm-mutation-preview-ref:test",
  approval_ref: "approval-ref:crm:test",
  affected_count: 1,
  duplicate_candidate_count: 0,
  safe_summary: "Create one local CRM record.",
  private_preview_labels: ["New Example"],
  local_only: true,
  external_write_enabled: false,
  provider_model_call_enabled: false,
};

const receipt: CrmAdoptionMutationReceipt = {
  schema_version: "uaa-crm-adoption-mutation-receipt.v1",
  contract_ref: workspace.contract_ref,
  receipt_ref: "crm-mutation-receipt-ref:test",
  action: "create",
  target_ref: "crm-record-ref:person:new",
  idempotency_ref: "idempotency-ref:crm-adoption-ui:create:test",
  payload_fingerprint_ref: preview.payload_fingerprint_ref,
  preview_ref: preview.preview_ref,
  approval_ref: preview.approval_ref,
  approval_validation_ref: "approval-decision-ref:crm:test",
  authority_lease_ref: "authority-lease-ref:crm:test",
  authority_decision_ref: "authority-decision-ref:crm:test",
  before_revision: 4,
  after_revision: 5,
  rollback_ref: "rollback-ref:crm-adoption:test",
  safe_summary: "One private CRM change was committed locally.",
  replayed: false,
  local_write_performed: true,
  external_write_performed: false,
  raw_private_values_included: false,
  approval_authority_granted: true,
};

const portableBackup = {
  schema_version: "uaa-crm-adoption-portable-backup.v1",
  contract_ref: workspace.contract_ref,
  salt: "c2FsdC1zYWx0LXNhbHQtc2FsdA==",
  nonce: "bm9uY2Utbm9uY2U=",
  ciphertext: "ZW5jcnlwdGVkLWJhY2t1cC1wYXlsb2Fk",
  ciphertext_fingerprint_ref: "fingerprint-ref:crm-backup:test",
  created_at: "2026-09-06T17:00:00+00:00",
  private_values_encrypted: true,
  key_material_included: false,
  raw_paths_included: false,
} satisfies CrmPortableBackup;

const restorePreview = {
  schema_version: "uaa-crm-adoption-restore-preview.v1",
  contract_ref: workspace.contract_ref,
  preview_ref: "preview-ref:crm-restore:test",
  approval_ref: "approval-ref:crm-restore:test",
  current_state_ref: "state-ref:crm:test",
  backup_revision: 4,
  record_count: 1,
  affected_count: 1,
  impact_status: "exact",
  counts: workspace.counts,
  integrity_status: "ok",
  private_values_included: false,
  restore_performed: false,
} satisfies CrmPortableRestorePreview;

const mutationBinding: BackendTruthReadBinding = {
  snapshotRef: `proof-ref:backend-truth-envelope:sha256:${"8".repeat(64)}`,
  backendRevisionRef: `commit-ref:git:${"1".repeat(40)}`,
  backendInstanceRef:
    "backend-instance-ref:control-center:22222222222222222222222222222222",
};

describe("CrmAdoptionWorkspace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.loadCrmAdoptionWorkspace.mockResolvedValue(workspace);
    apiMocks.previewCrmAdoptionMutation.mockResolvedValue(preview);
    apiMocks.captureCrmAdoptionMutationApproval.mockResolvedValue({
      schema_version: "uaa-crm-adoption-approval-receipt.v1",
    });
    apiMocks.commitCrmAdoptionMutation.mockResolvedValue(receipt);
    apiMocks.previewCrmPortableRestore.mockResolvedValue(restorePreview);
  });

  it("mounts founder-private CRM adoption on the primary CRM surface", async () => {
    render(<CrmSurface data={structuredClone(mockControlCenterData)} />);

    const heading = screen.getByRole("heading", { name: "Your CRM" });
    expect(heading).toBeVisible();
    expect(heading.closest(".ns-crm")).toHaveClass("ns-scroll-surface");
    expect(screen.getByText("Founder-private workspace")).toBeVisible();
    await waitFor(() =>
      expect(apiMocks.loadCrmAdoptionWorkspace).toHaveBeenCalledTimes(1),
    );
  });

  it("keeps the mutating adoption workspace off the legacy CRM route", () => {
    render(
      <CrmM1FixtureShellPanel
        crm={structuredClone(mockControlCenterData.crmLocalCommandCenter)}
      />,
    );

    expect(screen.queryByText("Founder-private workspace")).not.toBeInTheDocument();
    expect(apiMocks.loadCrmAdoptionWorkspace).not.toHaveBeenCalled();
  });

  it("renders real private records while keeping external authority off", async () => {
    render(<CrmAdoptionWorkspace />);

    expect(await screen.findAllByText("Example Contact")).toHaveLength(2);
    expect(screen.getByText("contact@example.test")).toBeInTheDocument();
    expect(
      screen.getByText(/Sends, external CRM writes, and model calls stay off/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Undo last change" })).toBeEnabled();
  });

  it("submits one deliberate private search instead of querying per keystroke", async () => {
    render(<CrmAdoptionWorkspace />);
    await screen.findAllByText("Example Contact");
    apiMocks.loadCrmAdoptionWorkspace.mockClear();

    const search = screen.getByLabelText("Search private CRM");
    fireEvent.change(search, { target: { value: "P" } });
    fireEvent.change(search, { target: { value: "Private" } });
    fireEvent.change(search, { target: { value: "Private Person" } });
    expect(apiMocks.loadCrmAdoptionWorkspace).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    await waitFor(() =>
      expect(apiMocks.loadCrmAdoptionWorkspace).toHaveBeenCalledTimes(1),
    );
    expect(apiMocks.loadCrmAdoptionWorkspace).toHaveBeenCalledWith(
      "Private Person",
      "",
      false,
    );
  });

  it("previews and explicitly confirms a new local record", async () => {
    render(
      <BackendTruthMutationBindingProvider binding={mutationBinding}>
        <CrmAdoptionWorkspace />
      </BackendTruthMutationBindingProvider>,
    );
    await screen.findAllByText("Example Contact");

    fireEvent.change(screen.getByLabelText("Name or title"), {
      target: { value: "New Example" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Review new record" }));

    await waitFor(() =>
      expect(apiMocks.previewCrmAdoptionMutation).toHaveBeenCalledWith(
        expect.objectContaining({
          action: "create",
          expected_revision: 4,
          record: expect.objectContaining({ display_name: "New Example" }),
        }),
        expect.stringMatching(/^idempotency-ref:crm-adoption-ui:create:/),
      ),
    );
    expect(
      await screen.findByRole("dialog", { name: "Review this local CRM change" }),
    ).toBeInTheDocument();
    expect(screen.getByText("New Example")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Confirm and save locally" }),
    );
    await waitFor(() =>
      expect(apiMocks.captureCrmAdoptionMutationApproval).toHaveBeenCalledWith(
        expect.objectContaining({ action: "create" }),
        preview,
        expect.stringMatching(/^idempotency-ref:crm-adoption-ui:create:/),
        mutationBinding,
      ),
    );
    await waitFor(() =>
      expect(apiMocks.commitCrmAdoptionMutation).toHaveBeenCalledWith(
        expect.objectContaining({ action: "create" }),
        preview,
        expect.stringMatching(/^idempotency-ref:crm-adoption-ui:create:/),
        mutationBinding,
      ),
    );
    expect(
      await screen.findByText(/Saved locally at CRM revision 5/i),
    ).toBeInTheDocument();
  });

  it("converts stored UTC timestamps to local wall time before editing", () => {
    const spies = [
      vi.spyOn(Date.prototype, "getFullYear").mockReturnValue(2026),
      vi.spyOn(Date.prototype, "getMonth").mockReturnValue(8),
      vi.spyOn(Date.prototype, "getDate").mockReturnValue(6),
      vi.spyOn(Date.prototype, "getHours").mockReturnValue(10),
      vi.spyOn(Date.prototype, "getMinutes").mockReturnValue(0),
      vi.spyOn(Date.prototype, "getSeconds").mockReturnValue(45),
      vi.spyOn(Date.prototype, "getMilliseconds").mockReturnValue(123),
    ];

    expect(crmLocalDateTimeInputValue("2026-09-06T17:00:45.123Z")).toBe(
      "2026-09-06T10:00:45.123",
    );
    spies.forEach((spy) => spy.mockRestore());
  });

  it("preserves exact timestamp precision during an unrelated edit", async () => {
    const exactTimestamp = "2026-09-06T17:00:45.123456+00:00";
    apiMocks.loadCrmAdoptionWorkspace.mockResolvedValue({
      ...workspace,
      records: [{ ...workspace.records[0], due_at: exactTimestamp }],
    });
    render(<CrmAdoptionWorkspace />);
    await screen.findAllByText("Example Contact");

    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    fireEvent.change(screen.getByLabelText("Name or title"), {
      target: { value: "Corrected Contact" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Review update" }));

    await waitFor(() =>
      expect(apiMocks.previewCrmAdoptionMutation).toHaveBeenCalledWith(
        expect.objectContaining({
          action: "update",
          patch: expect.objectContaining({
            display_name: "Corrected Contact",
            due_at: exactTimestamp,
          }),
        }),
        expect.stringMatching(/^idempotency-ref:crm-adoption-ui:update:/),
      ),
    );
  });

  it("preserves exact timestamp precision when a filter hides the edited record", async () => {
    const exactTimestamp = "2026-09-06T17:00:45.123456+00:00";
    const originalWorkspace = {
      ...workspace,
      records: [{ ...workspace.records[0], due_at: exactTimestamp }],
    };
    apiMocks.loadCrmAdoptionWorkspace
      .mockResolvedValueOnce(originalWorkspace)
      .mockResolvedValueOnce({ ...originalWorkspace, records: [] });
    render(<CrmAdoptionWorkspace />);
    await screen.findAllByText("Example Contact");

    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    fireEvent.change(screen.getByLabelText("Record type"), {
      target: { value: "organization" },
    });
    await waitFor(() =>
      expect(apiMocks.loadCrmAdoptionWorkspace).toHaveBeenLastCalledWith(
        "",
        "organization",
        false,
      ),
    );
    fireEvent.change(screen.getByLabelText("Name or title"), {
      target: { value: "Corrected Contact" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Review update" }));

    await waitFor(() =>
      expect(apiMocks.previewCrmAdoptionMutation).toHaveBeenCalledWith(
        expect.objectContaining({
          action: "update",
          patch: expect.objectContaining({ due_at: exactTimestamp }),
        }),
        expect.stringMatching(/^idempotency-ref:crm-adoption-ui:update:/),
      ),
    );
  });

  it("changes only the primary relationship and retains additional links", async () => {
    const relatedRecords = [
      {
        ...workspace.records[0],
        record_ref: "crm-record-ref:organization:primary",
        record_kind: "organization" as const,
        display_name: "Primary Organization",
      },
      {
        ...workspace.records[0],
        record_ref: "crm-record-ref:person:retained",
        display_name: "Retained Person",
      },
      {
        ...workspace.records[0],
        record_ref: "crm-record-ref:property:replacement",
        record_kind: "property" as const,
        display_name: "Replacement Property",
      },
    ];
    apiMocks.loadCrmAdoptionWorkspace.mockResolvedValue({
      ...workspace,
      records: [
        {
          ...workspace.records[0],
          related_refs: [
            relatedRecords[0].record_ref,
            relatedRecords[1].record_ref,
          ],
        },
        ...relatedRecords,
      ],
    });
    render(<CrmAdoptionWorkspace />);
    await screen.findAllByText("Example Contact");

    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    fireEvent.change(screen.getByLabelText(/Primary related record/), {
      target: { value: relatedRecords[2].record_ref },
    });
    fireEvent.click(screen.getByRole("button", { name: "Review update" }));

    await waitFor(() =>
      expect(apiMocks.previewCrmAdoptionMutation).toHaveBeenCalledWith(
        expect.objectContaining({
          action: "update",
          patch: expect.objectContaining({
            related_refs: [
              relatedRecords[2].record_ref,
              relatedRecords[1].record_ref,
            ],
          }),
        }),
        expect.stringMatching(/^idempotency-ref:crm-adoption-ui:update:/),
      ),
    );
    expect(screen.getByText("Other linked records are retained.")).toBeVisible();
  });

  it("preserves imported nullable fields when editing another value", async () => {
    apiMocks.loadCrmAdoptionWorkspace.mockResolvedValue({
      ...workspace,
      records: [{ ...workspace.records[0], currency: null, priority: null }],
    });
    render(<CrmAdoptionWorkspace />);
    await screen.findAllByText("Example Contact");

    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    expect(screen.getByLabelText("Priority")).toHaveValue("");
    fireEvent.change(screen.getByLabelText("Name or title"), {
      target: { value: "Corrected Contact" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Review update" }));

    await waitFor(() =>
      expect(apiMocks.previewCrmAdoptionMutation).toHaveBeenCalledWith(
        expect.objectContaining({
          action: "update",
          patch: expect.objectContaining({
            display_name: "Corrected Contact",
            currency: null,
            priority: null,
          }),
        }),
        expect.stringMatching(/^idempotency-ref:crm-adoption-ui:update:/),
      ),
    );
  });

  it("shows every reviewed bulk-import label before approval", async () => {
    const labels = Array.from(
      { length: 25 },
      (_, index) => `Candidate ${index + 1}`,
    );
    apiMocks.previewCrmAdoptionMutation.mockResolvedValueOnce({
      ...preview,
      action: "import_contacts",
      affected_count: labels.length,
      private_preview_labels: labels,
    });
    const file = {
      size: 256,
      text: vi.fn().mockResolvedValue(
        `name,email\n${labels
          .map((label, index) => `${label},candidate-${index + 1}@example.test`)
          .join("\n")}`,
      ),
    } as unknown as File;
    render(<CrmAdoptionWorkspace />);
    await screen.findAllByText("Example Contact");

    fireEvent.change(screen.getByLabelText("Preview contacts CSV"), {
      target: { files: [file] },
    });

    expect(await screen.findByText("All 25 reviewed items are shown below.")).toBeVisible();
    expect(screen.getByText("Candidate 1")).toBeVisible();
    expect(screen.getByText("Candidate 25")).toBeVisible();
  });

  it("shows recovery-required state without pretending ordinary edits are safe", async () => {
    apiMocks.loadCrmAdoptionWorkspace.mockResolvedValue({
      ...workspace,
      storage_state: "recovery_required",
      records: [],
      can_undo: false,
      next_safe_action: "Restore a verified encrypted backup.",
    });

    render(<CrmAdoptionWorkspace />);

    expect(
      await screen.findAllByText("Restore a verified encrypted backup."),
    ).toHaveLength(2);
    expect(screen.getByLabelText("Preview contacts CSV")).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Download encrypted backup" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Review new record" }),
    ).toBeDisabled();
    expect(screen.getByLabelText("Name or title")).toBeDisabled();
    expect(screen.getByLabelText("Open backup to restore")).toBeEnabled();
  });

  it("blocks restore when local storage is explicitly unsafe", async () => {
    apiMocks.loadCrmAdoptionWorkspace.mockResolvedValue({
      ...workspace,
      storage_state: "blocked_unsafe",
      records: [],
      can_undo: false,
      next_safe_action:
        "Inspect and repair the unsafe local CRM storage before restore.",
    });
    render(<CrmAdoptionWorkspace />);

    expect(
      await screen.findAllByText(
        "Inspect and repair the unsafe local CRM storage before restore.",
      ),
    ).toHaveLength(2);
    expect(screen.getByLabelText("Open backup to restore")).toBeDisabled();
  });

  it("blocks changes and restore when the local audit log needs rotation", async () => {
    apiMocks.loadCrmAdoptionWorkspace.mockResolvedValue({
      ...workspace,
      storage_state: "blocked_audit_capacity",
      records: workspace.records,
      can_undo: false,
      next_safe_action:
        "Back up this workspace, then rotate the local CRM audit log before another change.",
    });
    render(<CrmAdoptionWorkspace />);

    expect(
      await screen.findAllByText(
        "Back up this workspace, then rotate the local CRM audit log before another change.",
      ),
    ).toHaveLength(1);
    expect(screen.getAllByText("Example Contact")).toHaveLength(2);
    expect(screen.getByLabelText("Name or title")).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Download encrypted backup" }),
    ).toBeEnabled();
    expect(screen.getByLabelText("Open backup to restore")).toBeDisabled();
  });

  it("discloses the exact current-record impact before restore", async () => {
    const file = {
      size: 256,
      text: vi.fn().mockResolvedValue(JSON.stringify(portableBackup)),
    } as unknown as File;
    render(<CrmAdoptionWorkspace />);
    await screen.findAllByText("Example Contact");
    fireEvent.change(screen.getByLabelText("Backup passphrase"), {
      target: { value: "correct horse battery staple" },
    });

    fireEvent.change(screen.getByLabelText("Open backup to restore"), {
      target: { files: [file] },
    });

    expect(
      await screen.findByText(
        /1 current record will be added, removed, or changed; the backup contains 1 record at revision 4/i,
      ),
    ).toBeInTheDocument();
  });

  it("does not promise Undo when restoring an unreadable workspace", async () => {
    apiMocks.loadCrmAdoptionWorkspace.mockResolvedValue({
      ...workspace,
      storage_state: "recovery_required",
      records: [],
      can_undo: false,
    });
    apiMocks.previewCrmPortableRestore.mockResolvedValue({
      ...restorePreview,
      affected_count: null,
      impact_status: "unknown_current_state",
    });
    const file = {
      size: 256,
      text: vi.fn().mockResolvedValue(JSON.stringify(portableBackup)),
    } as unknown as File;
    render(<CrmAdoptionWorkspace />);
    await screen.findByText("recovery_required");
    fireEvent.change(screen.getByLabelText("Backup passphrase"), {
      target: { value: "correct horse battery staple" },
    });

    fireEvent.change(screen.getByLabelText("Open backup to restore"), {
      target: { files: [file] },
    });

    expect(
      await screen.findByText(
        "Replace the active CRM view with the verified backup. No readable current snapshot will be retained for Undo.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Impact on current records is unknown because the active workspace is unreadable/i,
      ),
    ).toBeInTheDocument();
  });

  it("contains a failed manual refresh and keeps the failure actionable", async () => {
    apiMocks.loadCrmAdoptionWorkspace
      .mockRejectedValueOnce(new Error("Initial CRM read failed safely."))
      .mockRejectedValueOnce(new Error("Retry CRM read failed safely."));

    render(<CrmAdoptionWorkspace />);

    expect(
      await screen.findByText("Initial CRM read failed safely."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));

    expect(
      await screen.findByText("Retry CRM read failed safely."),
    ).toBeInTheDocument();
    expect(apiMocks.loadCrmAdoptionWorkspace).toHaveBeenCalledTimes(2);
  });

  it("rejects oversized CSV before reading it", async () => {
    const text = vi.fn();
    const file = { size: 2_000_001, text } as unknown as File;
    render(<CrmAdoptionWorkspace />);
    await screen.findAllByText("Example Contact");

    fireEvent.change(screen.getByLabelText("Preview contacts CSV"), {
      target: { files: [file] },
    });

    expect(
      await screen.findByText("Choose a contacts CSV no larger than 2 MB."),
    ).toBeInTheDocument();
    expect(text).not.toHaveBeenCalled();
    expect(apiMocks.previewCrmAdoptionMutation).not.toHaveBeenCalled();
  });

  it("rejects oversized backup before reading it", async () => {
    const text = vi.fn();
    const file = { size: 48 * 1024 * 1024 + 1, text } as unknown as File;
    render(<CrmAdoptionWorkspace />);
    await screen.findAllByText("Example Contact");
    fireEvent.change(screen.getByLabelText("Backup passphrase"), {
      target: { value: "correct horse battery staple" },
    });

    fireEvent.change(screen.getByLabelText("Open backup to restore"), {
      target: { files: [file] },
    });

    expect(
      await screen.findByText(
        "Choose an encrypted CRM backup no larger than 48 MB.",
      ),
    ).toBeInTheDocument();
    expect(text).not.toHaveBeenCalled();
    expect(apiMocks.previewCrmPortableRestore).not.toHaveBeenCalled();
  });

  it("does not expose malformed backup fragments in parser errors", async () => {
    const privateMarker = "PRIVATE_BACKUP_FRAGMENT";
    const file = {
      size: 64,
      text: vi.fn().mockResolvedValue(`${privateMarker}{`),
    } as unknown as File;
    render(<CrmAdoptionWorkspace />);
    await screen.findAllByText("Example Contact");
    fireEvent.change(screen.getByLabelText("Backup passphrase"), {
      target: { value: "correct horse battery staple" },
    });

    fireEvent.change(screen.getByLabelText("Open backup to restore"), {
      target: { files: [file] },
    });

    expect(
      await screen.findByText(
        "The encrypted backup could not be opened safely.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(new RegExp(privateMarker))).not.toBeInTheDocument();
    expect(apiMocks.previewCrmPortableRestore).not.toHaveBeenCalled();
  });
});
