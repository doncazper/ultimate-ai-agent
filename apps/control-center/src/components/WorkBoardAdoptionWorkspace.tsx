import { useCallback, useEffect, useMemo, useState } from "react";
import {
  captureWorkBoardAdoptionApproval,
  captureWorkBoardAdoptionRestoreApproval,
  commitWorkBoardAdoptionMutation,
  commitWorkBoardAdoptionRestore,
  createWorkBoardAdoptionBackup,
  loadWorkBoardAdoptionWorkspace,
  previewWorkBoardAdoptionMutation,
  previewWorkBoardAdoptionRestore,
} from "../api/client";
import type {
  WorkBoardAdoptionCard,
  WorkBoardAdoptionCardDraft,
  WorkBoardAdoptionLaneRef,
  WorkBoardAdoptionMutationPreview,
  WorkBoardAdoptionMutationRequest,
  WorkBoardAdoptionPortableBackup,
  WorkBoardAdoptionRestorePreview,
  WorkBoardAdoptionWorkspaceView,
} from "../api/types";
import { useBackendTruthMutationBinding } from "../backendTruthMutationBinding";

const MAX_BACKUP_FILE_BYTES = 24 * 1024 * 1024;
const LANES: Array<{ ref: WorkBoardAdoptionLaneRef; label: string }> = [
  { ref: "work-board-lane:inbox", label: "Inbox" },
  { ref: "work-board-lane:planned", label: "Planned" },
  { ref: "work-board-lane:doing", label: "Doing" },
  { ref: "work-board-lane:done", label: "Done" },
];
const EMPTY_DRAFT: WorkBoardAdoptionCardDraft = {
  title: "",
  description: "",
  priority: "medium",
  lane_ref: "work-board-lane:inbox",
  tag_refs: [],
};

type PendingMutation = {
  request: WorkBoardAdoptionMutationRequest;
  preview: WorkBoardAdoptionMutationPreview;
  idempotencyRef: string;
};

type PendingRestore = {
  backup: WorkBoardAdoptionPortableBackup;
  passphrase: string;
  preview: WorkBoardAdoptionRestorePreview;
  idempotencyRef: string;
};

function newIdempotencyRef(action: string): string {
  const suffix =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID().replaceAll("-", "")
      : `${Date.now()}${Math.random().toString(16).slice(2)}`;
  return `idempotency-ref:work-board-adoption-ui:${action}:${suffix}`;
}

function displayTag(ref: string): string {
  return ref.replace(/^tag-ref:work-board:/, "").replaceAll("-", " ");
}

function tagRefs(value: string): string[] {
  return value
    .split(",")
    .map((item) =>
      item
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9_.:-]+/g, "-")
        .replace(/^-+|-+$/g, ""),
    )
    .filter(Boolean)
    .slice(0, 16)
    .map((item) => `tag-ref:work-board:${item}`)
    .filter((item, index, all) => all.indexOf(item) === index);
}

function cardToken(card: WorkBoardAdoptionCard): string {
  return JSON.stringify([
    card.card_ref,
    card.title,
    card.description,
    card.priority,
    card.lane_ref,
    card.tag_refs,
    card.archived,
  ]);
}

export function WorkBoardAdoptionWorkspace() {
  const mutationBinding = useBackendTruthMutationBinding();
  const [workspace, setWorkspace] =
    useState<WorkBoardAdoptionWorkspaceView | null>(null);
  const [query, setQuery] = useState("");
  const [selectedRef, setSelectedRef] = useState("");
  const [editingRef, setEditingRef] = useState<string | null>(null);
  const [editingOriginal, setEditingOriginal] =
    useState<WorkBoardAdoptionCard | null>(null);
  const [draft, setDraft] = useState<WorkBoardAdoptionCardDraft>({
    ...EMPTY_DRAFT,
  });
  const [tagInput, setTagInput] = useState("");
  const [pending, setPending] = useState<PendingMutation | null>(null);
  const [pendingRestore, setPendingRestore] =
    useState<PendingRestore | null>(null);
  const [restoreBackup, setRestoreBackup] =
    useState<WorkBoardAdoptionPortableBackup | null>(null);
  const [backupPassphrase, setBackupPassphrase] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const acceptWorkspace = useCallback((next: WorkBoardAdoptionWorkspaceView) => {
    setWorkspace(next);
    const all = [...next.active_cards, ...next.archived_cards];
    setSelectedRef((current) =>
      all.some((item) => item.card_ref === current)
        ? current
        : (next.active_cards[0]?.card_ref ?? next.archived_cards[0]?.card_ref ?? ""),
    );
  }, []);

  const refresh = useCallback(async () => {
    const next = await loadWorkBoardAdoptionWorkspace();
    acceptWorkspace(next);
  }, [acceptWorkspace]);

  useEffect(() => {
    let cancelled = false;
    setError("");
    loadWorkBoardAdoptionWorkspace()
      .then((next) => {
        if (!cancelled) acceptWorkspace(next);
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setError(
            reason instanceof Error
              ? reason.message
              : "The private Work Board could not be loaded.",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [acceptWorkspace]);

  useEffect(() => {
    if (!workspace || !editingRef || !editingOriginal) return;
    const refreshed = workspace.active_cards.find(
      (item) => item.card_ref === editingRef,
    );
    if (!refreshed || cardToken(refreshed) !== cardToken(editingOriginal)) {
      setEditingRef(null);
      setEditingOriginal(null);
      setDraft({ ...EMPTY_DRAFT });
      setTagInput("");
      setPending(null);
      setNotice("That card changed, so its stale edit draft was cleared.");
    }
  }, [editingOriginal, editingRef, workspace]);

  const normalizedQuery = query.trim().toLowerCase();
  const visibleCards = useMemo(
    () =>
      (workspace?.active_cards ?? []).filter((card) =>
        `${card.title} ${card.description ?? ""} ${card.tag_refs.join(" ")}`
          .toLowerCase()
          .includes(normalizedQuery),
      ),
    [normalizedQuery, workspace?.active_cards],
  );
  const selected = useMemo(
    () =>
      [...(workspace?.active_cards ?? []), ...(workspace?.archived_cards ?? [])].find(
        (item) => item.card_ref === selectedRef,
      ),
    [selectedRef, workspace?.active_cards, workspace?.archived_cards],
  );
  const writable = workspace?.status === "ready";

  const runPreview = useCallback(
    async (request: WorkBoardAdoptionMutationRequest, action: string) => {
      setBusy(true);
      setError("");
      setNotice("");
      const idempotencyRef = newIdempotencyRef(action);
      try {
        const preview = await previewWorkBoardAdoptionMutation(
          request,
          idempotencyRef,
        );
        setPending({ request, preview, idempotencyRef });
      } catch (reason) {
        setError(
          reason instanceof Error
            ? reason.message
            : "The Work Board preview failed safely.",
        );
      } finally {
        setBusy(false);
      }
    },
    [],
  );

  const submitDraft = useCallback(() => {
    if (!workspace || !writable || !draft.title.trim()) return;
    const normalized: WorkBoardAdoptionCardDraft = {
      ...draft,
      title: draft.title.trim(),
      description: draft.description?.trim() || null,
      tag_refs: tagRefs(tagInput),
    };
    void runPreview(
      editingRef
        ? {
            action: "update",
            expected_revision: workspace.revision,
            target_ref: editingRef,
            draft: normalized,
          }
        : {
            action: "create",
            expected_revision: workspace.revision,
            draft: normalized,
          },
      editingRef ? "update" : "create",
    );
  }, [draft, editingRef, runPreview, tagInput, workspace, writable]);

  const confirmMutation = useCallback(async () => {
    if (!pending) return;
    setBusy(true);
    setError("");
    try {
      await captureWorkBoardAdoptionApproval(
        pending.request,
        pending.preview,
        pending.idempotencyRef,
        mutationBinding,
      );
      const receipt = await commitWorkBoardAdoptionMutation(
        pending.request,
        pending.preview,
        pending.idempotencyRef,
        mutationBinding,
      );
      setPending(null);
      setEditingRef(null);
      setEditingOriginal(null);
      setDraft({ ...EMPTY_DRAFT });
      setTagInput("");
      setNotice(
        `Saved locally at Work Board revision ${receipt.after_revision}. No task was executed.`,
      );
      await refresh();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The Work Board change failed safely.",
      );
    } finally {
      setBusy(false);
    }
  }, [mutationBinding, pending, refresh]);

  const startEdit = useCallback((card: WorkBoardAdoptionCard) => {
    setEditingRef(card.card_ref);
    setEditingOriginal(card);
    setDraft({
      title: card.title,
      description: card.description ?? "",
      priority: card.priority,
      lane_ref: card.lane_ref,
      tag_refs: card.tag_refs,
    });
    setTagInput(card.tag_refs.map(displayTag).join(", "));
  }, []);

  const previewCardAction = useCallback(
    (
      action: "move" | "archive" | "recover",
      card: WorkBoardAdoptionCard,
      laneRef?: WorkBoardAdoptionLaneRef,
    ) => {
      if (!workspace || !writable) return;
      void runPreview(
        {
          action,
          expected_revision: workspace.revision,
          target_ref: card.card_ref,
          ...(action === "move" ? { lane_ref: laneRef } : {}),
        },
        action,
      );
    },
    [runPreview, workspace, writable],
  );

  const downloadBackup = useCallback(async () => {
    if (!backupPassphrase || backupPassphrase.length < 12) {
      setError("Use a backup passphrase with at least 12 characters.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const backup = await createWorkBoardAdoptionBackup(
        backupPassphrase,
        newIdempotencyRef("backup"),
      );
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(backup, null, 2)], {
          type: "application/json",
        }),
      );
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "uaa-work-board-backup.json";
      anchor.click();
      URL.revokeObjectURL(url);
      setNotice("Encrypted Work Board backup prepared for download.");
      setBackupPassphrase("");
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The encrypted backup could not be created.",
      );
    } finally {
      setBusy(false);
    }
  }, [backupPassphrase]);

  const openBackup = useCallback(async (file: File) => {
    setError("");
    try {
      if (file.size > MAX_BACKUP_FILE_BYTES) {
        throw new Error("Choose a Work Board backup no larger than 24 MB.");
      }
      const decoded = new TextDecoder("utf-8", { fatal: true }).decode(
        await file.arrayBuffer(),
      );
      setRestoreBackup(JSON.parse(decoded) as WorkBoardAdoptionPortableBackup);
      setNotice("Backup opened locally. Enter its passphrase to preview restore.");
    } catch {
      setRestoreBackup(null);
      setError("The encrypted Work Board backup could not be opened safely.");
    }
  }, []);

  const prepareRestore = useCallback(async () => {
    if (!restoreBackup || backupPassphrase.length < 12) return;
    setBusy(true);
    setError("");
    const idempotencyRef = newIdempotencyRef("restore");
    try {
      const preview = await previewWorkBoardAdoptionRestore(
        restoreBackup,
        backupPassphrase,
        idempotencyRef,
      );
      setPendingRestore({
        backup: restoreBackup,
        passphrase: backupPassphrase,
        preview,
        idempotencyRef,
      });
      setBackupPassphrase("");
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The encrypted backup could not be verified.",
      );
    } finally {
      setBusy(false);
    }
  }, [backupPassphrase, restoreBackup]);

  const confirmRestore = useCallback(async () => {
    if (!pendingRestore) return;
    setBusy(true);
    setError("");
    try {
      await captureWorkBoardAdoptionRestoreApproval(
        pendingRestore.backup,
        pendingRestore.passphrase,
        pendingRestore.preview,
        pendingRestore.idempotencyRef,
        mutationBinding,
      );
      const receipt = await commitWorkBoardAdoptionRestore(
        pendingRestore.backup,
        pendingRestore.passphrase,
        pendingRestore.preview,
        pendingRestore.idempotencyRef,
        mutationBinding,
      );
      setPendingRestore(null);
      setRestoreBackup(null);
      setNotice(`Backup restored locally at revision ${receipt.after_revision}.`);
      await refresh();
    } catch (reason) {
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
    <section
      className="page-section crm-adoption work-board-adoption"
      aria-labelledby="work-board-adoption-title"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">Founder-private workspace</p>
          <h2 id="work-board-adoption-title">Your Work Board</h2>
        </div>
        <span className="status-pill compact">
          {workspace?.status ?? "loading"}
        </span>
      </div>
      <p className="section-copy">
        Plan and move private work across four local lanes. Every save is
        previewed and confirmed. This board does not run tasks, call models, or
        write to connectors.
      </p>

      {error ? (
        <div className="panel danger" role="alert">
          <strong>Work Board needs attention</strong>
          <p>{error}</p>
          <button type="button" onClick={() => void refresh()}>
            Refresh
          </button>
        </div>
      ) : null}
      {notice ? (
        <div className="panel success" role="status">
          {notice}
        </div>
      ) : null}

      <div className="work-board-adoption-toolbar">
        <label>
          <span>Search your board</span>
          <input
            aria-label="Search your private Work Board"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Title, note, or tag…"
          />
        </label>
        <button
          type="button"
          disabled={!writable || !workspace?.can_undo || busy}
          onClick={() =>
            workspace &&
            void runPreview(
              { action: "undo", expected_revision: workspace.revision },
              "undo",
            )
          }
        >
          Undo last change
        </button>
        <span className="status-pill compact">
          revision {workspace?.revision ?? 0}
        </span>
      </div>

      {!writable && workspace ? (
        <div className="panel warning" role="status">
          <strong>Ordinary board changes are paused</strong>
          <p>{workspace.next_safe_action}</p>
        </div>
      ) : null}

      <div className="work-board-adoption-columns">
        {LANES.map((lane) => {
          const cards = visibleCards.filter((card) => card.lane_ref === lane.ref);
          return (
            <section className="work-board-adoption-lane" key={lane.ref}>
              <header>
                <strong>{lane.label}</strong>
                <span>{cards.length}</span>
              </header>
              {cards.map((card) => (
                <article
                  className={
                    selectedRef === card.card_ref
                      ? "work-board-adoption-card selected"
                      : "work-board-adoption-card"
                  }
                  key={card.card_ref}
                >
                  <button type="button" onClick={() => setSelectedRef(card.card_ref)}>
                    <small>{card.priority}</small>
                    <strong>{card.title}</strong>
                    {card.description ? <span>{card.description}</span> : null}
                  </button>
                  {card.tag_refs.length ? (
                    <div className="work-board-adoption-tags">
                      {card.tag_refs.map((tag) => (
                        <span key={tag}>{displayTag(tag)}</span>
                      ))}
                    </div>
                  ) : null}
                  <label>
                    <span>Move to</span>
                    <select
                      aria-label={`Move ${card.title}`}
                      disabled={busy || !writable}
                      value={card.lane_ref}
                      onChange={(event) =>
                        previewCardAction(
                          "move",
                          card,
                          event.target.value as WorkBoardAdoptionLaneRef,
                        )
                      }
                    >
                      {LANES.map((option) => (
                        <option key={option.ref} value={option.ref}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>
                </article>
              ))}
              {!cards.length ? <p>No matching cards.</p> : null}
            </section>
          );
        })}
      </div>

      <div className="work-board-adoption-lower-grid">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Card details</p>
              <h3>{selected?.title ?? "Select a card"}</h3>
            </div>
          </div>
          {selected ? (
            <>
              <p>{selected.description || "No description yet."}</p>
              <div className="crm-adoption-actions">
                {!selected.archived ? (
                  <>
                    <button type="button" disabled={busy} onClick={() => startEdit(selected)}>
                      Edit
                    </button>
                    <button
                      type="button"
                      disabled={busy || !writable}
                      onClick={() => previewCardAction("archive", selected)}
                    >
                      Archive
                    </button>
                  </>
                ) : (
                  <button
                    type="button"
                    disabled={busy || !writable}
                    onClick={() => previewCardAction("recover", selected)}
                  >
                    Recover
                  </button>
                )}
              </div>
            </>
          ) : (
            <p>{workspace?.next_safe_action ?? "Loading your board…"}</p>
          )}
          {(workspace?.archived_cards.length ?? 0) > 0 ? (
            <details>
              <summary>Archived cards ({workspace?.archived_cards.length})</summary>
              <div className="work-board-adoption-archive-list">
                {workspace?.archived_cards.map((card) => (
                  <button
                    type="button"
                    key={card.card_ref}
                    onClick={() => setSelectedRef(card.card_ref)}
                  >
                    {card.title}
                  </button>
                ))}
              </div>
            </details>
          ) : null}
        </section>

        <form
          className="panel work-board-adoption-editor"
          onSubmit={(event) => {
            event.preventDefault();
            submitDraft();
          }}
        >
          <div className="panel-heading">
            <div>
              <p className="eyebrow">{editingRef ? "Edit" : "Create"}</p>
              <h3>{editingRef ? "Update this card" : "Add a private card"}</h3>
            </div>
          </div>
          <fieldset disabled={busy || !writable}>
            <label>
              <span>Title</span>
              <input
                required
                maxLength={160}
                value={draft.title}
                onChange={(event) =>
                  setDraft((current) => ({ ...current, title: event.target.value }))
                }
              />
            </label>
            <label>
              <span>Description</span>
              <textarea
                maxLength={4000}
                value={draft.description ?? ""}
                onChange={(event) =>
                  setDraft((current) => ({
                    ...current,
                    description: event.target.value,
                  }))
                }
              />
            </label>
            <div className="work-board-adoption-editor-row">
              <label>
                <span>Priority</span>
                <select
                  value={draft.priority}
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      priority: event.target.value as WorkBoardAdoptionCardDraft["priority"],
                    }))
                  }
                >
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </label>
              <label>
                <span>Lane</span>
                <select
                  value={draft.lane_ref}
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      lane_ref: event.target.value as WorkBoardAdoptionLaneRef,
                    }))
                  }
                >
                  {LANES.map((lane) => (
                    <option key={lane.ref} value={lane.ref}>
                      {lane.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label>
              <span>Tags, separated by commas</span>
              <input value={tagInput} onChange={(event) => setTagInput(event.target.value)} />
            </label>
          </fieldset>
          <div className="crm-adoption-actions">
            <button type="submit" disabled={busy || !writable || !draft.title.trim()}>
              Review before saving
            </button>
            {editingRef ? (
              <button
                type="button"
                onClick={() => {
                  setEditingRef(null);
                  setEditingOriginal(null);
                  setDraft({ ...EMPTY_DRAFT });
                  setTagInput("");
                }}
              >
                Cancel edit
              </button>
            ) : null}
          </div>
        </form>
      </div>

      <section className="panel work-board-adoption-recovery">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Backup and recovery</p>
            <h3>Move safely between your Macs and Windows PCs</h3>
          </div>
          <span>encrypted portable file</span>
        </div>
        <p className="section-copy">
          Backups are encrypted with your passphrase. Restores are verified,
          previewed, and confirmed before replacing local board state.
        </p>
        <div className="crm-adoption-recovery-grid">
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
          <button type="button" disabled={busy || !writable} onClick={() => void downloadBackup()}>
            Download encrypted backup
          </button>
          <label className="crm-adoption-file-button">
            <span>Open backup to restore</span>
            <input
              type="file"
              accept=".json,application/json"
              disabled={busy}
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void openBackup(file);
                event.currentTarget.value = "";
              }}
            />
          </label>
          <button
            type="button"
            disabled={busy || !restoreBackup || backupPassphrase.length < 12}
            onClick={() => void prepareRestore()}
          >
            Preview restore
          </button>
        </div>
      </section>

      {pending ? (
        <ConfirmationDialog
          title="Review this Work Board change"
          summary={pending.preview.safe_summary}
          detail={`Revision ${pending.preview.expected_revision} → ${pending.preview.resulting_revision}`}
          confirmLabel="Confirm and save locally"
          busy={busy}
          onCancel={() => setPending(null)}
          onConfirm={() => void confirmMutation()}
        />
      ) : null}
      {pendingRestore ? (
        <ConfirmationDialog
          title="Review this encrypted restore"
          summary={pendingRestore.preview.safe_summary}
          detail={`${pendingRestore.preview.card_count} card${pendingRestore.preview.card_count === 1 ? "" : "s"}; ${pendingRestore.preview.rollback_available ? "undo will be available" : "current state is unreadable, so rollback is unavailable"}.`}
          confirmLabel="Confirm and restore locally"
          busy={busy}
          onCancel={() => setPendingRestore(null)}
          onConfirm={() => void confirmRestore()}
        />
      ) : null}
    </section>
  );
}

function ConfirmationDialog({
  title,
  summary,
  detail,
  confirmLabel,
  busy,
  onCancel,
  onConfirm,
}: {
  title: string;
  summary: string;
  detail: string;
  confirmLabel: string;
  busy: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="crm-adoption-confirm-backdrop" role="presentation">
      <section
        className="crm-adoption-confirm"
        role="dialog"
        aria-modal="true"
        aria-labelledby="work-board-confirm-title"
      >
        <h3 id="work-board-confirm-title">{title}</h3>
        <p>{summary}</p>
        <p>{detail}</p>
        <p>No task execution, model call, connector write, or external action will occur.</p>
        <div className="crm-adoption-actions">
          <button type="button" disabled={busy} onClick={onConfirm}>
            {confirmLabel}
          </button>
          <button type="button" disabled={busy} onClick={onCancel}>
            Cancel
          </button>
        </div>
      </section>
    </div>
  );
}
