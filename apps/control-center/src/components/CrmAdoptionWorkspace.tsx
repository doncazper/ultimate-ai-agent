import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  captureCrmAdoptionMutationApproval,
  captureCrmPortableRestoreApproval,
  commitCrmAdoptionMutation,
  commitCrmPortableRestore,
  createCrmPortableBackup,
  loadCrmAdoptionWorkspace,
  previewCrmAdoptionMutation,
  previewCrmPortableRestore,
} from "../api/client";
import type {
  CrmAdoptionMutationPreview,
  CrmAdoptionMutationRequest,
  CrmAdoptionRecord,
  CrmAdoptionRecordDraft,
  CrmAdoptionRecordKind,
  CrmAdoptionWorkspaceView,
  CrmPortableBackup,
  CrmPortableRestorePreview,
} from "../api/types";
import { useBackendTruthMutationBinding } from "../backendTruthMutationBinding";

const CRM_ADOPTION_MAX_IMPORT_FILE_BYTES = 2_000_000;
const CRM_ADOPTION_MAX_BACKUP_FILE_BYTES = 48 * 1024 * 1024;
const CRM_ADOPTION_MAX_AMOUNT_MINOR = 90_071_992_547_409;
const CRM_ADOPTION_MAX_AMOUNT_MAJOR = CRM_ADOPTION_MAX_AMOUNT_MINOR / 100;
const CRM_ADOPTION_BACKUP_OPEN_ERROR =
  "The encrypted backup could not be opened safely.";
const CRM_ADOPTION_IMPORT_UTF8_ERROR =
  "Choose a contacts CSV saved as valid UTF-8 text.";

const RECORD_KINDS: Array<{ value: CrmAdoptionRecordKind; label: string }> = [
  { value: "person", label: "Person" },
  { value: "organization", label: "Organization" },
  { value: "property", label: "Property" },
  { value: "relationship", label: "Relationship" },
  { value: "opportunity", label: "Opportunity" },
  { value: "activity", label: "Activity" },
  { value: "follow_up", label: "Follow-up" },
];

const EMPTY_DRAFT: CrmAdoptionRecordDraft = {
  record_kind: "person",
  display_name: "",
  subtitle: "",
  email: "",
  phone: "",
  website: "",
  notes: "",
  tags: [],
  status: "active",
  related_refs: [],
  due_at: null,
  occurred_at: null,
  amount_minor: null,
  currency: "USD",
  priority: "medium",
};

type PendingMutation = {
  request: CrmAdoptionMutationRequest;
  preview: CrmAdoptionMutationPreview;
  idempotencyRef: string;
  commitAttempted: boolean;
};

type PendingRestore = {
  backup: CrmPortableBackup;
  passphrase: string;
  preview: CrmPortableRestorePreview;
  idempotencyRef: string;
};

function newIdempotencyRef(action: string): string {
  const suffix =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID().replaceAll("-", "")
      : `${Date.now()}${Math.random().toString(16).slice(2)}`;
  return `idempotency-ref:crm-adoption-ui:${action}:${suffix}`;
}

function optional(value: string | null | undefined): string | null {
  const normalized = value?.trim() ?? "";
  return normalized || null;
}

async function readUtf8File(file: File, safeError: string): Promise<string> {
  try {
    return new TextDecoder("utf-8", { fatal: true }).decode(
      await file.arrayBuffer(),
    );
  } catch {
    throw new Error(safeError);
  }
}

function crmRecordContentToken(record: CrmAdoptionRecord): string {
  return JSON.stringify([
    record.record_ref,
    record.record_kind,
    record.display_name,
    record.subtitle,
    record.email,
    record.phone,
    record.website,
    record.notes,
    record.tags,
    record.status,
    record.related_refs,
    record.due_at,
    record.occurred_at,
    record.amount_minor,
    record.currency,
    record.priority,
    record.archived,
    record.version,
    record.created_at,
    record.updated_at,
  ]);
}

export function crmLocalDateTimeInputValue(
  value: string | null | undefined,
): string {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "";
  const part = (number: number) => String(number).padStart(2, "0");
  const milliseconds = parsed.getMilliseconds();
  const fraction = milliseconds
    ? `.${String(milliseconds).padStart(3, "0")}`
    : "";
  return `${parsed.getFullYear()}-${part(parsed.getMonth() + 1)}-${part(
    parsed.getDate(),
  )}T${part(parsed.getHours())}:${part(parsed.getMinutes())}:${part(
    parsed.getSeconds(),
  )}${fraction}`;
}

function isoDate(value: string | null | undefined): string | null {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    throw new Error("Use a valid date and time before reviewing this record.");
  }
  return parsed.toISOString();
}

export function CrmAdoptionWorkspace() {
  const mutationBinding = useBackendTruthMutationBinding();
  const [workspace, setWorkspace] = useState<CrmAdoptionWorkspaceView | null>(
    null,
  );
  const [recordDirectory, setRecordDirectory] = useState<CrmAdoptionRecord[]>(
    [],
  );
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [kindFilter, setKindFilter] = useState<CrmAdoptionRecordKind | "">("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [selectedRef, setSelectedRef] = useState("");
  const [draft, setDraft] = useState<CrmAdoptionRecordDraft>(() => ({
    ...EMPTY_DRAFT,
  }));
  const [editingRef, setEditingRef] = useState<string | null>(null);
  const [editingOriginal, setEditingOriginal] =
    useState<CrmAdoptionRecord | null>(null);
  const [pending, setPending] = useState<PendingMutation | null>(null);
  const [pendingRestore, setPendingRestore] = useState<PendingRestore | null>(
    null,
  );
  const [backupPassphrase, setBackupPassphrase] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const loadWorkspaceSnapshot = useCallback(async () => {
    const next = await loadCrmAdoptionWorkspace(
      submittedQuery,
      kindFilter,
      includeArchived,
    );
    const visibleRefs = new Set(next.records.map((item) => item.record_ref));
    const hasHiddenRelatedRecord = next.records.some((item) =>
      item.related_refs.some((ref) => !visibleRefs.has(ref)),
    );
    const directoryView =
      submittedQuery || kindFilter || hasHiddenRelatedRecord
        ? await loadCrmAdoptionWorkspace("", "", true)
        : next;
    return {
      next,
      directory:
        directoryView.revision === next.revision &&
        directoryView.current_state_ref === next.current_state_ref
          ? directoryView.records
          : next.records,
    };
  }, [includeArchived, kindFilter, submittedQuery]);

  const acceptWorkspaceSnapshot = useCallback(
    (next: CrmAdoptionWorkspaceView, directory: CrmAdoptionRecord[]) => {
      setWorkspace(next);
      setRecordDirectory(directory);
      setSelectedRef((current) =>
        next.records.some((item) => item.record_ref === current)
          ? current
          : (next.records[0]?.record_ref ?? ""),
      );
    },
    [],
  );

  const refresh = useCallback(async () => {
    setError("");
    const { next, directory } = await loadWorkspaceSnapshot();
    acceptWorkspaceSnapshot(next, directory);
  }, [acceptWorkspaceSnapshot, loadWorkspaceSnapshot]);

  useEffect(() => {
    let cancelled = false;
    setError("");
    loadWorkspaceSnapshot()
      .then(({ next, directory }) => {
        if (cancelled) return;
        acceptWorkspaceSnapshot(next, directory);
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setError(
            reason instanceof Error
              ? reason.message
              : "The private CRM could not be loaded.",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [acceptWorkspaceSnapshot, loadWorkspaceSnapshot]);

  const selected = useMemo(
    () => workspace?.records.find((item) => item.record_ref === selectedRef),
    [selectedRef, workspace?.records],
  );
  useEffect(() => {
    if (!workspace || !editingRef || !editingOriginal) return;
    const refreshedRecord = workspace.records.find(
      (item) => item.record_ref === editingRef,
    );
    if (
      !refreshedRecord ||
      crmRecordContentToken(refreshedRecord) !==
        crmRecordContentToken(editingOriginal)
    ) {
      setEditingRef(null);
      setEditingOriginal(null);
      setDraft({ ...EMPTY_DRAFT });
      setPending(null);
      setNotice(
        "This record changed or is no longer visible, so the stale draft was cleared.",
      );
    }
  }, [editingOriginal, editingRef, workspace]);
  const relatedOptions = useMemo(
    () =>
      recordDirectory.filter(
        (item) => item.record_ref !== editingRef && !item.archived,
      ),
    [editingRef, recordDirectory],
  );
  const workspaceWritable =
    workspace?.storage_state === "empty" || workspace?.storage_state === "ready";

  const runPreview = useCallback(
    async (request: CrmAdoptionMutationRequest, actionLabel: string) => {
      setBusy(true);
      setError("");
      setNotice("");
      const idempotencyRef = newIdempotencyRef(actionLabel);
      try {
        const preview = await previewCrmAdoptionMutation(
          request,
          idempotencyRef,
        );
        setPending({ request, preview, idempotencyRef, commitAttempted: false });
      } catch (reason) {
        setError(
          reason instanceof Error
            ? reason.message
            : "The local change preview failed safely.",
        );
      } finally {
        setBusy(false);
      }
    },
    [],
  );

  const submitDraft = useCallback(async () => {
    if (!workspace || !workspaceWritable || !draft.display_name.trim()) return;
    if (
      draft.amount_minor !== null &&
      draft.amount_minor !== undefined &&
      (!Number.isSafeInteger(draft.amount_minor) ||
        draft.amount_minor < 0 ||
        draft.amount_minor > CRM_ADOPTION_MAX_AMOUNT_MINOR)
    ) {
      setError("Use an amount within the supported exact-cent range.");
      return;
    }
    const editingRecord =
      editingOriginal?.record_ref === editingRef ? editingOriginal : undefined;
    const preserveTimestamp = (
      value: string | null | undefined,
      original: string | null | undefined,
    ) =>
      original && value === crmLocalDateTimeInputValue(original)
        ? original
        : isoDate(value);
    let normalized: CrmAdoptionRecordDraft;
    try {
      normalized = {
        ...draft,
        display_name: draft.display_name.trim(),
        subtitle: optional(draft.subtitle),
        email: optional(draft.email),
        phone: optional(draft.phone),
        website: optional(draft.website),
        notes: optional(draft.notes),
        status: optional(draft.status),
        tags: draft.tags ?? [],
        related_refs: draft.related_refs ?? [],
        due_at: preserveTimestamp(draft.due_at, editingRecord?.due_at),
        occurred_at: preserveTimestamp(
          draft.occurred_at,
          editingRecord?.occurred_at,
        ),
        currency: optional(draft.currency),
      };
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The record contains an invalid date or time.",
      );
      return;
    }
    const request: CrmAdoptionMutationRequest = editingRef
      ? {
          action: "update",
          expected_revision: workspace.revision,
          target_ref: editingRef,
          patch: {
            display_name: normalized.display_name,
            subtitle: normalized.subtitle,
            email: normalized.email,
            phone: normalized.phone,
            website: normalized.website,
            notes: normalized.notes,
            tags: normalized.tags,
            status: normalized.status,
            related_refs: normalized.related_refs,
            due_at: normalized.due_at,
            occurred_at: normalized.occurred_at,
            amount_minor: normalized.amount_minor,
            currency: normalized.currency,
            priority: normalized.priority,
          },
        }
      : {
          action: "create",
          expected_revision: workspace.revision,
          record: normalized,
        };
    await runPreview(request, editingRef ? "update" : "create");
  }, [
    draft,
    editingOriginal,
    editingRef,
    runPreview,
    workspace,
    workspaceWritable,
  ]);

  const confirmMutation = useCallback(async () => {
    if (!pending) return;
    setBusy(true);
    setError("");
    try {
      await captureCrmAdoptionMutationApproval(
        pending.request,
        pending.preview,
        pending.idempotencyRef,
        mutationBinding,
      );
      setPending((current) =>
        current?.idempotencyRef === pending.idempotencyRef
          ? { ...current, commitAttempted: true }
          : current,
      );
      const receipt = await commitCrmAdoptionMutation(
        pending.request,
        pending.preview,
        pending.idempotencyRef,
        mutationBinding,
      );
      setPending(null);
      setEditingRef(null);
      setEditingOriginal(null);
      setDraft({ ...EMPTY_DRAFT });
      setNotice(
        `Saved locally at CRM revision ${receipt.after_revision}. No external write occurred.`,
      );
      await refresh();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The private CRM change failed safely.",
      );
    } finally {
      setBusy(false);
    }
  }, [mutationBinding, pending, refresh]);

  const startEdit = useCallback((record: CrmAdoptionRecord) => {
    setEditingRef(record.record_ref);
    setEditingOriginal(record);
    setDraft({
      record_kind: record.record_kind,
      display_name: record.display_name,
      subtitle: record.subtitle ?? "",
      email: record.email ?? "",
      phone: record.phone ?? "",
      website: record.website ?? "",
      notes: record.notes ?? "",
      tags: record.tags,
      status: record.status ?? "",
      related_refs: record.related_refs,
      due_at: crmLocalDateTimeInputValue(record.due_at),
      occurred_at: crmLocalDateTimeInputValue(record.occurred_at),
      amount_minor: record.amount_minor ?? null,
      currency: record.currency,
      priority: record.priority,
    });
  }, []);

  const previewLifecycle = useCallback(
    (action: "archive" | "restore") => {
      if (!workspace || !selected) return;
      void runPreview(
        {
          action,
          expected_revision: workspace.revision,
          target_ref: selected.record_ref,
        },
        action,
      );
    },
    [runPreview, selected, workspace],
  );

  const previewUndo = useCallback(() => {
    if (!workspace) return;
    void runPreview(
      { action: "undo", expected_revision: workspace.revision },
      "undo",
    );
  }, [runPreview, workspace]);

  const previewImport = useCallback(
    async (file: File) => {
      if (!workspace) return;
      try {
        if (file.size > CRM_ADOPTION_MAX_IMPORT_FILE_BYTES) {
          throw new Error("Choose a contacts CSV no larger than 2 MB.");
        }
        const csvText = await readUtf8File(
          file,
          CRM_ADOPTION_IMPORT_UTF8_ERROR,
        );
        await runPreview(
          {
            action: "import_contacts",
            expected_revision: workspace.revision,
            csv_text: csvText,
          },
          "import",
        );
      } catch (reason) {
        setError(
          reason instanceof Error
            ? reason.message
            : "The contact import could not be previewed.",
        );
      }
    },
    [runPreview, workspace],
  );

  const downloadBackup = useCallback(async () => {
    if (backupPassphrase.length < 12) {
      setError("Use a backup passphrase with at least 12 characters.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const backup = await createCrmPortableBackup(
        backupPassphrase,
        newIdempotencyRef("backup"),
      );
      const blob = new Blob([JSON.stringify(backup, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `uaa-private-crm-backup-${new Date()
        .toISOString()
        .slice(0, 10)}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
      setNotice("Encrypted portable CRM backup downloaded.");
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The encrypted backup could not be created.",
      );
    } finally {
      setBackupPassphrase("");
      setBusy(false);
    }
  }, [backupPassphrase]);

  const prepareRestore = useCallback(
    async (file: File) => {
      if (backupPassphrase.length < 12) {
        setError("Enter the backup passphrase before choosing a backup.");
        return;
      }
      setBusy(true);
      setError("");
      try {
        if (file.size > CRM_ADOPTION_MAX_BACKUP_FILE_BYTES) {
          throw new Error("Choose an encrypted CRM backup no larger than 48 MB.");
        }
        const backupText = await readUtf8File(
          file,
          CRM_ADOPTION_BACKUP_OPEN_ERROR,
        );
        let backup: CrmPortableBackup;
        try {
          backup = JSON.parse(backupText) as CrmPortableBackup;
        } catch {
          throw new Error(CRM_ADOPTION_BACKUP_OPEN_ERROR);
        }
        const idempotencyRef = newIdempotencyRef("restore");
        const preview = await previewCrmPortableRestore(
          backup,
          backupPassphrase,
          idempotencyRef,
        );
        setPendingRestore({
          backup,
          passphrase: backupPassphrase,
          preview,
          idempotencyRef,
        });
      } catch (reason) {
        setError(
          reason instanceof Error
            ? reason.message
            : CRM_ADOPTION_BACKUP_OPEN_ERROR,
        );
      } finally {
        setBackupPassphrase("");
        setBusy(false);
      }
    },
    [backupPassphrase],
  );

  const confirmRestore = useCallback(async () => {
    if (!pendingRestore) return;
    setBusy(true);
    setError("");
    try {
      await captureCrmPortableRestoreApproval(
        pendingRestore.backup,
        pendingRestore.passphrase,
        pendingRestore.preview,
        pendingRestore.idempotencyRef,
        mutationBinding,
      );
      const receipt = await commitCrmPortableRestore(
        pendingRestore.backup,
        pendingRestore.passphrase,
        pendingRestore.preview,
        pendingRestore.idempotencyRef,
        mutationBinding,
      );
      setPendingRestore(null);
      setEditingRef(null);
      setEditingOriginal(null);
      setDraft({ ...EMPTY_DRAFT });
      setNotice(`Backup restored at CRM revision ${receipt.after_revision}.`);
      await refresh();
    } catch (reason) {
      // A lost response can make restore success ambiguous. Invalidate all
      // pre-restore editor state so it cannot be replayed against a refreshed
      // restored revision; the operator can safely reopen the backup if the
      // commit did not reach the backend.
      setPendingRestore(null);
      setPending(null);
      setEditingRef(null);
      setEditingOriginal(null);
      setDraft({ ...EMPTY_DRAFT });
      setError(
        reason instanceof Error
          ? reason.message
          : "The encrypted backup restore failed safely.",
      );
    } finally {
      setBusy(false);
    }
  }, [mutationBinding, pendingRestore, refresh]);

  return (
    <section className="page-section crm-adoption" aria-labelledby="crm-adoption-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Founder-private workspace</p>
          <h2 id="crm-adoption-title">Your CRM</h2>
        </div>
        <span className="status-pill compact">
          {workspace?.storage_state ?? "loading"}
        </span>
      </div>
      <p className="section-copy">
        Capture people, organizations, properties, opportunities, activity, and
        follow-ups in encrypted local storage. Every change is previewed before
        it is saved. Sends, external CRM writes, and model calls stay off.
      </p>

      {error ? (
        <div className="panel danger" role="alert">
          <strong>CRM needs attention</strong>
          <p>{error}</p>
          <button
            type="button"
            onClick={() =>
              void refresh().catch((reason: unknown) => {
                setError(
                  reason instanceof Error
                    ? reason.message
                    : "The private CRM could not be loaded.",
                );
              })
            }
          >
            Refresh
          </button>
        </div>
      ) : null}
      {notice ? (
        <div className="panel success" role="status">
          {notice}
        </div>
      ) : null}

      <div className="crm-adoption-metrics" aria-label="CRM record counts">
        {RECORD_KINDS.slice(0, 5).map((kind) => (
          <article className="metric-card" key={kind.value}>
            <span>{kind.label}</span>
            <strong>{workspace?.counts[kind.value] ?? 0}</strong>
          </article>
        ))}
      </div>

      <div className="crm-adoption-toolbar">
        <form
          className="crm-adoption-search"
          onSubmit={(event) => {
            event.preventDefault();
            setSubmittedQuery(query);
          }}
        >
          <label>
            <span>Search private CRM</span>
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Name, address, company, note, tag…"
            />
          </label>
          <button type="submit" disabled={busy}>
            Search
          </button>
        </form>
        <label>
          <span>Record type</span>
          <select
            value={kindFilter}
            onChange={(event) =>
              setKindFilter(event.target.value as CrmAdoptionRecordKind | "")
            }
          >
            <option value="">Everything</option>
            {RECORD_KINDS.map((kind) => (
              <option key={kind.value} value={kind.value}>
                {kind.label}
              </option>
            ))}
          </select>
        </label>
        <label className="crm-adoption-check">
          <input
            type="checkbox"
            checked={includeArchived}
            onChange={(event) => setIncludeArchived(event.target.checked)}
          />
          <span>Show archived</span>
        </label>
        <button
          type="button"
          disabled={!workspaceWritable || !workspace?.can_undo || busy}
          onClick={previewUndo}
        >
          Undo last change
        </button>
      </div>

      <div className="crm-adoption-layout">
        <section className="status-card crm-adoption-list" aria-label="Private CRM records">
          <div className="status-card-header">
            <h3>Records</h3>
            <span>{workspace?.records.length ?? 0} shown</span>
          </div>
          {(workspace?.records.length ?? 0) > 0 ? (
            workspace?.records.map((record) => (
              <button
                type="button"
                className={
                  record.record_ref === selectedRef
                    ? "crm-adoption-row active"
                    : "crm-adoption-row"
                }
                key={record.record_ref}
                onClick={() => setSelectedRef(record.record_ref)}
              >
                <span>
                  <strong>{record.display_name}</strong>
                  <small>{record.subtitle || record.status || record.record_kind}</small>
                </span>
                <span className="status-pill compact">
                  {record.archived ? "archived" : record.record_kind.replace("_", " ")}
                </span>
              </button>
            ))
          ) : (
            <div className="crm-adoption-empty">
              <strong>No matching records</strong>
              <p>{workspace?.next_safe_action ?? "Loading your private CRM…"}</p>
            </div>
          )}
        </section>

        <RecordInspector
          record={selected}
          records={recordDirectory}
          onEdit={startEdit}
          onArchive={() => previewLifecycle("archive")}
          onRestore={() => previewLifecycle("restore")}
          busy={busy || !workspaceWritable}
        />
      </div>

      {workspace && !workspaceWritable ? (
        <div className="panel warning" role="status">
          <strong>Ordinary CRM changes are paused</strong>
          <p>{workspace.next_safe_action}</p>
        </div>
      ) : null}

      <RecordEditor
        draft={draft}
        editing={editingRef !== null}
        relatedOptions={relatedOptions}
        busy={busy}
        writable={workspaceWritable}
        onChange={setDraft}
        onCancel={() => {
          setEditingRef(null);
          setEditingOriginal(null);
          setDraft({ ...EMPTY_DRAFT });
        }}
        onSubmit={() => void submitDraft()}
      />

      <section className="panel crm-adoption-recovery" aria-labelledby="crm-recovery-title">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Import, backup, and recovery</p>
            <h3 id="crm-recovery-title">Move safely between your computers</h3>
          </div>
          <span>encrypted portable file</span>
        </div>
        <p className="section-copy">
          CSV imports are reviewed before commit and never silently merge.
          Portable backups are encrypted with a passphrase you choose; the
          passphrase and local encryption key are never included in receipts.
        </p>
        <div className="crm-adoption-recovery-grid">
          <label className="crm-adoption-file-button">
            <span>Preview contacts CSV</span>
            <input
              type="file"
              accept=".csv,text/csv"
              disabled={busy || !workspaceWritable}
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void previewImport(file);
                event.currentTarget.value = "";
              }}
            />
          </label>
          <label>
            <span>Backup passphrase</span>
            <input
              type="password"
              autoComplete="new-password"
              value={backupPassphrase}
              onChange={(event) => setBackupPassphrase(event.target.value)}
              placeholder="At least 12 characters"
            />
          </label>
          <button
            type="button"
            disabled={
              busy ||
              !workspace ||
              ![
                "ready",
                "blocked_audit_capacity",
                "blocked_audit_unreadable",
                "blocked_revision_exhausted",
              ].includes(
                workspace.storage_state,
              )
            }
            onClick={() => void downloadBackup()}
          >
            Download encrypted backup
          </button>
          <label className="crm-adoption-file-button">
            <span>Open backup to restore</span>
            <input
              type="file"
              accept=".json,application/json"
              disabled={
                busy ||
                workspace?.storage_state === "blocked_audit_capacity" ||
                workspace?.storage_state === "blocked_audit_unreadable" ||
                workspace?.storage_state === "blocked_revision_exhausted" ||
                workspace?.storage_state === "blocked_unsafe"
              }
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void prepareRestore(file);
                event.currentTarget.value = "";
              }}
            />
          </label>
        </div>
      </section>

      {pending ? (
        <ConfirmationPanel
          title="Review this local CRM change"
          summary={pending.preview.safe_summary}
          details={`${pending.preview.affected_count} record${pending.preview.affected_count === 1 ? "" : "s"} affected${pending.preview.duplicate_candidate_count ? `; ${pending.preview.duplicate_candidate_count} possible duplicate${pending.preview.duplicate_candidate_count === 1 ? "" : "s"} will be skipped` : ""}.`}
          labels={pending.preview.private_preview_labels}
          busy={busy}
          confirmLabel="Confirm and save locally"
          cancelLabel={
            pending.commitAttempted && pending.request.action === "create"
              ? "Stop and clear draft"
              : "Cancel"
          }
          onCancel={() => {
            if (pending.commitAttempted && pending.request.action === "create") {
              setEditingRef(null);
              setEditingOriginal(null);
              setDraft({ ...EMPTY_DRAFT });
            }
            setPending(null);
          }}
          onConfirm={() => void confirmMutation()}
        />
      ) : null}

      {pendingRestore ? (
        <ConfirmationPanel
          title="Review encrypted backup restore"
          summary={
            pendingRestore.preview.rollback_available
              ? "Replace the active CRM view with the verified backup. The current state remains available to Undo."
              : "Replace the active CRM view with the verified backup. No readable current snapshot will be retained for Undo."
          }
          details={
            pendingRestore.preview.impact_status === "exact"
              ? `${pendingRestore.preview.affected_count ?? 0} current record${pendingRestore.preview.affected_count === 1 ? "" : "s"} will be added, removed, or changed; the backup contains ${pendingRestore.preview.record_count} record${pendingRestore.preview.record_count === 1 ? "" : "s"} at revision ${pendingRestore.preview.backup_revision}. Integrity check passed.`
              : `Impact on current records is unknown because the active workspace is unreadable; the backup contains ${pendingRestore.preview.record_count} record${pendingRestore.preview.record_count === 1 ? "" : "s"} at revision ${pendingRestore.preview.backup_revision}. Integrity check passed.`
          }
          labels={[]}
          busy={busy}
          confirmLabel="Confirm restore"
          onCancel={() => {
            setPendingRestore(null);
            setBackupPassphrase("");
          }}
          onConfirm={() => void confirmRestore()}
        />
      ) : null}
    </section>
  );
}

function RecordInspector({
  record,
  records,
  onEdit,
  onArchive,
  onRestore,
  busy,
}: {
  record: CrmAdoptionRecord | undefined;
  records: CrmAdoptionRecord[];
  onEdit: (record: CrmAdoptionRecord) => void;
  onArchive: () => void;
  onRestore: () => void;
  busy: boolean;
}) {
  const labelsByRef = useMemo(
    () => new Map(records.map((item) => [item.record_ref, item.display_name])),
    [records],
  );
  if (!record) {
    return (
      <section className="status-card crm-adoption-inspector">
        <div className="status-card-header">
          <h3>Record details</h3>
          <span>nothing selected</span>
        </div>
        <p>Select a record or capture a new one below.</p>
      </section>
    );
  }
  return (
    <section className="status-card crm-adoption-inspector" aria-label="Private CRM record details">
      <div className="status-card-header">
        <div>
          <p className="eyebrow">{record.record_kind.replace("_", " ")}</p>
          <h3>{record.display_name}</h3>
        </div>
        <span>{record.archived ? "archived" : record.status || "active"}</span>
      </div>
      {record.subtitle ? <p className="crm-adoption-subtitle">{record.subtitle}</p> : null}
      <dl className="crm-adoption-details">
        {record.email ? <Detail label="Email" value={record.email} /> : null}
        {record.phone ? <Detail label="Phone" value={record.phone} /> : null}
        {record.website ? <Detail label="Website" value={record.website} /> : null}
        {record.due_at ? <Detail label="Due" value={new Date(record.due_at).toLocaleString()} /> : null}
        {record.occurred_at ? <Detail label="Occurred" value={new Date(record.occurred_at).toLocaleString()} /> : null}
        {record.amount_minor !== null && record.amount_minor !== undefined ? (
          <Detail
            label="Amount"
            value={
              record.currency
                ? `${record.currency} ${(record.amount_minor / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                : `${(record.amount_minor / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })} · currency unset`
            }
          />
        ) : null}
      </dl>
      {record.notes ? <p className="crm-adoption-notes">{record.notes}</p> : null}
      {record.tags.length ? (
        <div className="crm-adoption-tags" aria-label="Tags">
          {record.tags.map((tag) => <span key={tag}>{tag}</span>)}
        </div>
      ) : null}
      {record.related_refs.length ? (
        <div className="crm-adoption-related">
          <strong>Linked records</strong>
          <ul>
            {record.related_refs.map((ref) => <li key={ref}>{labelsByRef.get(ref) ?? "Unavailable record"}</li>)}
          </ul>
        </div>
      ) : null}
      <div className="crm-adoption-actions">
        <button type="button" disabled={busy || record.archived} onClick={() => onEdit(record)}>
          Edit
        </button>
        {record.archived ? (
          <button type="button" disabled={busy} onClick={onRestore}>Restore</button>
        ) : (
          <button type="button" disabled={busy} onClick={onArchive}>Archive</button>
        )}
      </div>
    </section>
  );
}

function RecordEditor({
  draft,
  editing,
  relatedOptions,
  busy,
  writable,
  onChange,
  onCancel,
  onSubmit,
}: {
  draft: CrmAdoptionRecordDraft;
  editing: boolean;
  relatedOptions: CrmAdoptionRecord[];
  busy: boolean;
  writable: boolean;
  onChange: (draft: CrmAdoptionRecordDraft) => void;
  onCancel: () => void;
  onSubmit: () => void;
}) {
  const set = <K extends keyof CrmAdoptionRecordDraft>(
    key: K,
    value: CrmAdoptionRecordDraft[K],
  ) => onChange({ ...draft, [key]: value });
  return (
    <section className="panel crm-adoption-editor" aria-labelledby="crm-editor-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">{editing ? "Correct record" : "Quick capture"}</p>
          <h3 id="crm-editor-title">{editing ? "Edit private record" : "Add to your CRM"}</h3>
        </div>
        <span>preview before save</span>
      </div>
      <fieldset className="crm-adoption-form-grid" disabled={busy || !writable}>
        <label>
          <span>Type</span>
          <select
            value={draft.record_kind}
            disabled={editing}
            onChange={(event) => set("record_kind", event.target.value as CrmAdoptionRecordKind)}
          >
            {RECORD_KINDS.map((kind) => <option key={kind.value} value={kind.value}>{kind.label}</option>)}
          </select>
        </label>
        <label>
          <span>Name or title</span>
          <input value={draft.display_name} onChange={(event) => set("display_name", event.target.value)} required />
        </label>
        <label>
          <span>Company, address, or subtitle</span>
          <input value={draft.subtitle ?? ""} onChange={(event) => set("subtitle", event.target.value)} />
        </label>
        <label>
          <span>Status or stage</span>
          <input value={draft.status ?? ""} onChange={(event) => set("status", event.target.value)} />
        </label>
        <label>
          <span>Email</span>
          <input type="email" value={draft.email ?? ""} onChange={(event) => set("email", event.target.value)} />
        </label>
        <label>
          <span>Phone</span>
          <input type="tel" value={draft.phone ?? ""} onChange={(event) => set("phone", event.target.value)} />
        </label>
        <label>
          <span>Website</span>
          <input type="url" value={draft.website ?? ""} onChange={(event) => set("website", event.target.value)} />
        </label>
        <label>
          <span>Tags, comma separated</span>
          <input
            value={(draft.tags ?? []).join(", ")}
            onChange={(event) => set("tags", event.target.value.split(",").map((item) => item.trim()).filter(Boolean))}
          />
        </label>
        <label>
          <span>Due date</span>
          <input type="datetime-local" step="0.001" value={crmLocalDateTimeInputValue(draft.due_at)} onChange={(event) => set("due_at", event.target.value || null)} />
        </label>
        <label>
          <span>Activity date</span>
          <input type="datetime-local" step="0.001" value={crmLocalDateTimeInputValue(draft.occurred_at)} onChange={(event) => set("occurred_at", event.target.value || null)} />
        </label>
        <label>
          <span>Amount</span>
          <input
            type="number"
            min="0"
            max={CRM_ADOPTION_MAX_AMOUNT_MAJOR}
            step="0.01"
            value={draft.amount_minor === null || draft.amount_minor === undefined ? "" : draft.amount_minor / 100}
            onChange={(event) => set("amount_minor", event.target.value ? Math.round(Number(event.target.value) * 100) : null)}
          />
        </label>
        <label>
          <span>Priority</span>
          <select
            value={draft.priority ?? ""}
            onChange={(event) =>
              set(
                "priority",
                event.target.value
                  ? (event.target.value as "high" | "medium" | "low")
                  : null,
              )
            }
          >
            <option value="">Not set</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </label>
        <label className="crm-adoption-span-2">
          <span>Primary related record</span>
          <select
            value={draft.related_refs?.[0] ?? ""}
            onChange={(event) => {
              const primaryRef = event.target.value;
              const retainedRefs = primaryRef
                ? (draft.related_refs ?? []).filter((ref) => ref !== primaryRef)
                : (draft.related_refs ?? []).slice(1);
              set(
                "related_refs",
                primaryRef ? [primaryRef, ...retainedRefs] : retainedRefs,
              );
            }}
          >
            <option value="">No linked record</option>
            {relatedOptions.map((item) => <option key={item.record_ref} value={item.record_ref}>{item.display_name} · {item.record_kind.replace("_", " ")}</option>)}
          </select>
          <small>Other linked records are retained.</small>
        </label>
        <label className="crm-adoption-span-2">
          <span>Private notes</span>
          <textarea rows={4} value={draft.notes ?? ""} onChange={(event) => set("notes", event.target.value)} />
        </label>
      </fieldset>
      <div className="crm-adoption-actions">
        <button type="button" disabled={busy || !writable || !draft.display_name.trim()} onClick={onSubmit}>
          {editing ? "Review update" : "Review new record"}
        </button>
        {editing ? <button type="button" disabled={busy} onClick={onCancel}>Cancel edit</button> : null}
      </div>
    </section>
  );
}

function ConfirmationPanel({
  title,
  summary,
  details,
  labels,
  busy,
  confirmLabel,
  cancelLabel = "Cancel",
  onCancel,
  onConfirm,
}: {
  title: string;
  summary: string;
  details: string;
  labels: string[];
  busy: boolean;
  confirmLabel: string;
  cancelLabel?: string;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="crm-adoption-confirm-backdrop" role="presentation">
      <section className="crm-adoption-confirm" role="dialog" aria-modal="true" aria-labelledby="crm-confirm-title">
        <p className="eyebrow">Exact local approval</p>
        <h3 id="crm-confirm-title">{title}</h3>
        <p>{summary}</p>
        <p className="section-copy">{details}</p>
        {labels.length ? (
          <>
            {labels.length > 12 ? (
              <p className="section-copy">
                All {labels.length} reviewed items are shown below.
              </p>
            ) : null}
            <ul aria-label="Reviewed CRM items">
              {labels.map((label, index) => (
                <li key={`${index}:${label}`}>{label}</li>
              ))}
            </ul>
          </>
        ) : null}
        <div className="crm-adoption-actions">
          <button type="button" disabled={busy} onClick={onConfirm}>{busy ? "Saving…" : confirmLabel}</button>
          <button type="button" disabled={busy} onClick={onCancel}>{cancelLabel}</button>
        </div>
      </section>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div><dt>{label}</dt><dd>{value}</dd></div>;
}
