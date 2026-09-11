import { useCallback, useEffect, useMemo, useState } from "react";
import {
  captureCalendarAdoptionApproval,
  captureCalendarAdoptionRestoreApproval,
  commitCalendarAdoptionMutation,
  commitCalendarAdoptionRestore,
  createCalendarAdoptionBackup,
  loadCalendarAdoptionWorkspace,
  previewCalendarAdoptionMutation,
  previewCalendarAdoptionRestore,
} from "../api/client";
import type {
  CalendarAdoptionCalendarDraft,
  CalendarAdoptionEvent,
  CalendarAdoptionEventDraft,
  CalendarAdoptionMutationPreview,
  CalendarAdoptionMutationRequest,
  CalendarAdoptionPortableBackup,
  CalendarAdoptionRestorePreview,
  CalendarAdoptionView,
  CalendarAdoptionWorkspaceView,
} from "../api/types";
import { useBackendTruthMutationBinding } from "../backendTruthMutationBinding";

const MAX_BACKUP_FILE_BYTES = 24 * 1024 * 1024;
const VIEWS: CalendarAdoptionView[] = ["day", "week", "month", "agenda"];

type PendingMutation = {
  request: CalendarAdoptionMutationRequest;
  preview: CalendarAdoptionMutationPreview;
  idempotencyRef: string;
};

type PendingRestore = {
  backup: CalendarAdoptionPortableBackup;
  passphrase: string;
  preview: CalendarAdoptionRestorePreview;
  idempotencyRef: string;
};

function newIdempotencyRef(action: string): string {
  const suffix =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID().replaceAll("-", "")
      : `${Date.now()}${Math.random().toString(16).slice(2)}`;
  return `idempotency-ref:calendar-adoption-ui:${action}:${suffix}`;
}

function localTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
}

function newCalendarDraft(name = ""): CalendarAdoptionCalendarDraft {
  return {
    calendar_ref: newIdempotencyRef("calendar").replace(
      "idempotency-ref",
      "calendar-ref",
    ),
    name,
    timezone: localTimezone(),
    color_ref: "color-ref:calendar:blue",
  };
}

function localInput(iso: string): string {
  const date = new Date(iso);
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

function initialTimes(): { starts_at: string; ends_at: string } {
  const start = new Date();
  start.setMinutes(0, 0, 0);
  start.setHours(start.getHours() + 1);
  const end = new Date(start.getTime() + 60 * 60 * 1_000);
  return { starts_at: localInput(start.toISOString()), ends_at: localInput(end.toISOString()) };
}

function eventDraft(
  calendarRef: string,
  event?: CalendarAdoptionEvent,
): CalendarAdoptionEventDraft {
  const times = initialTimes();
  return {
    event_ref: event?.event_ref ?? newIdempotencyRef("event").replace("idempotency-ref", "calendar-event-ref"),
    calendar_ref: event?.calendar_ref ?? calendarRef,
    title: event?.title ?? "",
    description: event?.description ?? "",
    location: event?.location ?? "",
    starts_at: event ? localInput(event.starts_at) : times.starts_at,
    ends_at: event ? localInput(event.ends_at) : times.ends_at,
    timezone: event?.timezone ?? localTimezone(),
    all_day: false,
    participant_items: event?.participant_items ?? [],
    reminder_items: event?.reminder_items ?? [],
    recurrence: event?.recurrence ?? null,
  };
}

function networkEventDraft(draft: CalendarAdoptionEventDraft): CalendarAdoptionEventDraft {
  return {
    ...draft,
    title: draft.title.trim(),
    description: draft.description?.trim() || null,
    location: draft.location?.trim() || null,
    starts_at: new Date(draft.starts_at).toISOString(),
    ends_at: new Date(draft.ends_at).toISOString(),
  };
}

function formatDate(iso: string, timezone: string, options: Intl.DateTimeFormatOptions): string {
  return new Intl.DateTimeFormat("en-US", { ...options, timeZone: timezone }).format(new Date(iso));
}

function shiftAnchor(anchor: string, view: CalendarAdoptionView, direction: -1 | 1): string {
  const next = new Date(anchor);
  if (view === "month") next.setMonth(next.getMonth() + direction);
  else next.setDate(next.getDate() + direction * (view === "day" ? 1 : view === "week" ? 7 : 30));
  return next.toISOString();
}

function reviewDetail(pending: PendingMutation): string {
  const { request, preview } = pending;
  const revision = `Revision ${preview.expected_revision} → ${preview.resulting_revision}.`;
  if (request.action === "create_event" || request.action === "update_event") {
    const event = request.event;
    return `${request.action === "create_event" ? "Create" : "Update"} “${event?.title ?? "event"}” from ${event ? new Date(event.starts_at).toLocaleString() : "unknown"} to ${event ? new Date(event.ends_at).toLocaleString() : "unknown"}. ${revision}`;
  }
  if (request.action === "initialize" || request.action === "create_calendar") {
    return `${request.action === "initialize" ? "Initialize Calendar with" : "Add"} “${request.calendar?.name ?? "calendar"}”. ${revision}`;
  }
  if (request.action === "archive_event" || request.action === "recover_event") {
    return `${request.action === "archive_event" ? "Archive" : "Recover"} ${request.target_ref}. ${revision}`;
  }
  return `Undo the latest local Calendar change. ${revision}`;
}

export function CalendarAdoptionWorkspace() {
  const mutationBinding = useBackendTruthMutationBinding();
  const [view, setView] = useState<CalendarAdoptionView>("week");
  const [anchor, setAnchor] = useState(() => new Date().toISOString());
  const [timezone, setTimezone] = useState(localTimezone);
  const [timezoneDraft, setTimezoneDraft] = useState(localTimezone);
  const [workspace, setWorkspace] = useState<CalendarAdoptionWorkspaceView | null>(null);
  const [selectedRef, setSelectedRef] = useState("");
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<CalendarAdoptionEvent | null>(null);
  const [draft, setDraft] = useState<CalendarAdoptionEventDraft>(() => eventDraft(""));
  const [calendarDraft, setCalendarDraft] =
    useState<CalendarAdoptionCalendarDraft>(() => newCalendarDraft("Personal"));
  const [pending, setPending] = useState<PendingMutation | null>(null);
  const [pendingRestore, setPendingRestore] = useState<PendingRestore | null>(null);
  const [restoreBackup, setRestoreBackup] = useState<CalendarAdoptionPortableBackup | null>(null);
  const [passphrase, setPassphrase] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const acceptWorkspace = useCallback((next: CalendarAdoptionWorkspaceView) => {
    setWorkspace(next);
    setSelectedRef((current) => {
      const refs = [...next.occurrence_items.map((item) => item.event.event_ref), ...next.archived_events.map((item) => item.event_ref)];
      return refs.includes(current) ? current : (next.occurrence_items[0]?.event.event_ref ?? next.archived_events[0]?.event_ref ?? "");
    });
    setDraft((current) => current.calendar_ref ? current : ({
      ...current,
      calendar_ref: next.calendars[0]?.calendar_ref ?? current.calendar_ref,
    }));
  }, []);

  const refresh = useCallback(async () => {
    const next = await loadCalendarAdoptionWorkspace(view, anchor, timezone);
    acceptWorkspace(next);
  }, [acceptWorkspace, anchor, timezone, view]);

  useEffect(() => {
    let cancelled = false;
    setError("");
    loadCalendarAdoptionWorkspace(view, anchor, timezone)
      .then((next) => { if (!cancelled) acceptWorkspace(next); })
      .catch((reason: unknown) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : "The private Calendar could not be loaded.");
      });
    return () => { cancelled = true; };
  }, [acceptWorkspace, anchor, timezone, view]);

  const events = useMemo(() => {
    const seen = new Map<string, CalendarAdoptionEvent>();
    for (const item of workspace?.occurrence_items ?? []) seen.set(item.event.event_ref, item.event);
    for (const item of workspace?.archived_events ?? []) seen.set(item.event_ref, item);
    return [...seen.values()];
  }, [workspace]);
  const selected = events.find((item) => item.event_ref === selectedRef) ?? null;

  useEffect(() => {
    if (!editing || !workspace) return;
    const current = events.find((event) => event.event_ref === editing.event_ref);
    if (!current || JSON.stringify(current) !== JSON.stringify(editing)) {
      setEditing(null);
      setDraft(eventDraft(workspace.calendars[0]?.calendar_ref ?? ""));
      setNotice("The selected event changed. Review the refreshed event before editing again.");
    }
  }, [editing, events, workspace]);
  const normalizedQuery = query.trim().toLowerCase();
  const visibleOccurrences = (workspace?.occurrence_items ?? []).filter(({ event }) =>
    `${event.title ?? ""} ${event.description ?? ""} ${event.location ?? ""}`.toLowerCase().includes(normalizedQuery),
  );
  const grouped = useMemo(() => {
    const result = new Map<string, typeof visibleOccurrences>();
    for (const item of visibleOccurrences) {
      const key = formatDate(item.occurrence.starts_at, timezone, { weekday: "long", month: "short", day: "numeric" });
      result.set(key, [...(result.get(key) ?? []), item]);
    }
    return [...result.entries()];
  }, [timezone, visibleOccurrences]);
  const writable = workspace?.status === "ready" || workspace?.status === "onboarding";

  const runPreview = useCallback(async (request: CalendarAdoptionMutationRequest, action: string) => {
    setBusy(true); setError(""); setNotice("");
    const idempotencyRef = newIdempotencyRef(action);
    try {
      const preview = await previewCalendarAdoptionMutation(request, idempotencyRef);
      setPending({ request, preview, idempotencyRef });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The Calendar preview failed safely.");
    } finally { setBusy(false); }
  }, []);

  const confirmMutation = useCallback(async () => {
    if (!pending) return;
    setBusy(true); setError("");
    try {
      await captureCalendarAdoptionApproval(pending.request, pending.preview, pending.idempotencyRef, mutationBinding);
      const receipt = await commitCalendarAdoptionMutation(pending.request, pending.preview, pending.idempotencyRef, mutationBinding);
      setPending(null); setEditing(null); setDraft(eventDraft(workspace?.calendars[0]?.calendar_ref ?? ""));
      if (pending.request.action === "initialize" || pending.request.action === "create_calendar") {
        setCalendarDraft(newCalendarDraft());
      }
      setNotice(`Saved privately at Calendar revision ${receipt.after_revision}. No external calendar was changed.`);
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The Calendar change failed safely.");
    } finally { setBusy(false); }
  }, [mutationBinding, pending, refresh, workspace?.calendars]);

  const submitCalendar = useCallback(() => {
    if (!workspace || !calendarDraft.name.trim()) return;
    void runPreview({
      action: workspace.status === "onboarding" ? "initialize" : "create_calendar",
      expected_revision: workspace.revision,
      calendar: { ...calendarDraft, name: calendarDraft.name.trim(), timezone },
    }, workspace.status === "onboarding" ? "initialize" : "create-calendar");
  }, [calendarDraft, runPreview, timezone, workspace]);

  const applyTimezone = useCallback(() => {
    const candidate = timezoneDraft.trim();
    try {
      Intl.DateTimeFormat("en-US", { timeZone: candidate }).format(new Date());
      setTimezone(candidate);
      setError("");
    } catch {
      setError("Enter a valid IANA timezone, such as America/Los_Angeles or UTC.");
    }
  }, [timezoneDraft]);

  const submitEvent = useCallback(() => {
    if (!workspace || !draft.title.trim() || !draft.calendar_ref) return;
    const prepared = networkEventDraft(draft);
    if (new Date(prepared.ends_at) <= new Date(prepared.starts_at)) {
      setError("End time must be after start time."); return;
    }
    void runPreview({
      action: editing ? "update_event" : "create_event",
      expected_revision: workspace.revision,
      ...(editing ? { target_ref: editing.event_ref } : {}),
      event: prepared,
    }, editing ? "update-event" : "create-event");
  }, [draft, editing, runPreview, workspace]);

  const startEdit = useCallback((event: CalendarAdoptionEvent) => {
    setEditing(event); setDraft(eventDraft(event.calendar_ref, event));
  }, []);

  const lifecycle = useCallback((action: "archive_event" | "recover_event", event: CalendarAdoptionEvent) => {
    if (!workspace) return;
    void runPreview({ action, expected_revision: workspace.revision, target_ref: event.event_ref }, action);
  }, [runPreview, workspace]);

  const downloadBackup = useCallback(async () => {
    if (passphrase.length < 12) { setError("Use a backup passphrase with at least 12 characters."); return; }
    setBusy(true); setError("");
    try {
      const backup = await createCalendarAdoptionBackup(passphrase, newIdempotencyRef("backup"));
      const url = URL.createObjectURL(new Blob([JSON.stringify(backup, null, 2)], { type: "application/json" }));
      const link = document.createElement("a"); link.href = url; link.download = "uaa-calendar-backup.json"; link.click(); URL.revokeObjectURL(url);
      setNotice("Encrypted Calendar backup prepared for download."); setPassphrase("");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Backup failed safely."); }
    finally { setBusy(false); }
  }, [passphrase]);

  const openBackup = useCallback(async (file: File) => {
    try {
      if (file.size > MAX_BACKUP_FILE_BYTES) throw new Error("Backup is too large.");
      const decoded = new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer());
      setRestoreBackup(JSON.parse(decoded) as CalendarAdoptionPortableBackup);
      setNotice("Encrypted backup opened locally. Enter its passphrase to preview restore.");
    } catch { setRestoreBackup(null); setError("The Calendar backup could not be opened safely."); }
  }, []);

  const prepareRestore = useCallback(async () => {
    if (!restoreBackup || passphrase.length < 12) return;
    setBusy(true); setError("");
    const idempotencyRef = newIdempotencyRef("restore");
    try {
      const preview = await previewCalendarAdoptionRestore(restoreBackup, passphrase, idempotencyRef);
      setPendingRestore({ backup: restoreBackup, passphrase, preview, idempotencyRef }); setPassphrase("");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Restore preview failed safely."); }
    finally { setBusy(false); }
  }, [passphrase, restoreBackup]);

  const confirmRestore = useCallback(async () => {
    if (!pendingRestore) return;
    setBusy(true); setError("");
    try {
      await captureCalendarAdoptionRestoreApproval(pendingRestore.backup, pendingRestore.passphrase, pendingRestore.preview, pendingRestore.idempotencyRef, mutationBinding);
      const receipt = await commitCalendarAdoptionRestore(pendingRestore.backup, pendingRestore.passphrase, pendingRestore.preview, pendingRestore.idempotencyRef, mutationBinding);
      setPendingRestore(null); setRestoreBackup(null); setNotice(`Calendar restored privately at revision ${receipt.after_revision}.`); await refresh();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Restore failed safely."); }
    finally { setBusy(false); }
  }, [mutationBinding, pendingRestore, refresh]);

  return <section className="page-section calendar-adoption" aria-labelledby="calendar-adoption-title">
    <div className="section-heading"><div><p className="eyebrow">Founder-private workspace</p><h2 id="calendar-adoption-title">Your Calendar</h2></div><span className="status-pill compact">{workspace?.status ?? "loading"}</span></div>
    <p className="section-copy">Plan local events across day, week, month, and agenda views. Every change is previewed and confirmed. No account, connector, notification, or external calendar is touched.</p>
    {error ? <div className="panel danger" role="alert"><strong>Calendar needs attention</strong><p>{error}</p><button type="button" onClick={() => void refresh()}>Refresh</button></div> : null}
    {notice ? <div className="panel success" role="status">{notice}</div> : null}

    <div className="calendar-adoption-toolbar">
      <button type="button" disabled={busy} onClick={() => setAnchor(new Date().toISOString())}>Today</button>
      <button type="button" aria-label="Previous period" disabled={busy} onClick={() => setAnchor((value) => shiftAnchor(value, view, -1))}>←</button>
      <button type="button" aria-label="Next period" disabled={busy} onClick={() => setAnchor((value) => shiftAnchor(value, view, 1))}>→</button>
      <div className="calendar-adoption-view-switcher" aria-label="Calendar view">{VIEWS.map((item) => <button className={item === view ? "active" : ""} key={item} type="button" onClick={() => setView(item)}>{item}</button>)}</div>
      <label><span className="sr-only">Calendar timezone</span><input aria-label="Calendar timezone" value={timezoneDraft} onChange={(event) => setTimezoneDraft(event.target.value)} /></label>
      <button type="button" disabled={busy || timezoneDraft.trim() === timezone} onClick={applyTimezone}>Apply timezone</button>
      <span className="status-pill compact">revision {workspace?.revision ?? 0}</span>
    </div>

    {!workspace ? <div className="panel">Loading your local Calendar…</div> : workspace.status === "recovery_required" || workspace.status === "setup_incomplete" ? <div className="panel warning"><strong>Ordinary Calendar changes are paused</strong><p>{workspace.next_safe_action}</p></div> : null}

    {workspace?.status === "onboarding" ? <section className="panel calendar-adoption-onboarding"><h3>Create your first private calendar</h3><p>This stays encrypted on this computer until you export an encrypted backup.</p><label>Name<input value={calendarDraft.name} onChange={(event) => setCalendarDraft((value) => ({ ...value, name: event.target.value }))} /></label><button type="button" disabled={busy || !calendarDraft.name.trim()} onClick={submitCalendar}>Review setup</button></section> : null}

    {workspace?.status === "ready" ? <div className="calendar-adoption-layout">
      <section className="calendar-adoption-main">
        <div className="calendar-adoption-range"><div><strong>{formatDate(workspace.range_starts_at, timezone, { month: "long", day: "numeric", year: "numeric" })}</strong><span> through {formatDate(workspace.range_ends_at, timezone, { month: "short", day: "numeric" })}</span></div><label><span className="sr-only">Search Calendar</span><input aria-label="Search private Calendar" type="search" placeholder="Search title, notes, or place…" value={query} onChange={(event) => setQuery(event.target.value)} /></label></div>
        {workspace.conflict_items.length ? <div className="panel warning" role="status"><strong>{workspace.conflict_items.length} schedule conflict{workspace.conflict_items.length === 1 ? "" : "s"}</strong><p>Overlapping local events are highlighted for your review.</p></div> : null}
        <div className="calendar-adoption-days">{grouped.map(([day, items]) => <section key={day}><header><strong>{day}</strong><span>{items.length}</span></header>{items.map((item) => {
          const conflicted = workspace.conflict_items.some((conflict) => conflict.first_occurrence_ref === item.occurrence.occurrence_ref || conflict.second_occurrence_ref === item.occurrence.occurrence_ref);
          return <button className={`calendar-adoption-event${selectedRef === item.event.event_ref ? " selected" : ""}${conflicted ? " conflict" : ""}`} key={item.occurrence.occurrence_ref} type="button" onClick={() => setSelectedRef(item.event.event_ref)}><span>{formatDate(item.occurrence.starts_at, timezone, { hour: "numeric", minute: "2-digit" })}–{formatDate(item.occurrence.ends_at, timezone, { hour: "numeric", minute: "2-digit" })}</span><strong>{item.event.title}</strong><small>{workspace.calendars.find((calendar) => calendar.calendar_ref === item.event.calendar_ref)?.name ?? "Calendar"}{conflicted ? " · Conflict" : ""}</small></button>;
        })}</section>)}{!grouped.length ? <div className="calendar-adoption-empty"><strong>No events in this view</strong><p>Create one below or move to another period.</p></div> : null}</div>
      </section>
      <aside className="calendar-adoption-inspector"><h3>{selected?.title ?? "Event details"}</h3>{selected ? <><p>{selected.description || "No notes yet."}</p><dl><div><dt>When</dt><dd>{new Date(selected.starts_at).toLocaleString()} – {new Date(selected.ends_at).toLocaleString()}</dd></div><div><dt>Location</dt><dd>{selected.location || "None"}</dd></div><div><dt>Calendar</dt><dd>{workspace.calendars.find((item) => item.calendar_ref === selected.calendar_ref)?.name ?? "Unknown"}</dd></div></dl><div className="calendar-adoption-actions">{selected.archived ? <button type="button" disabled={busy} onClick={() => lifecycle("recover_event", selected)}>Recover event</button> : <><button type="button" disabled={busy} onClick={() => startEdit(selected)}>Edit</button><button type="button" disabled={busy} onClick={() => lifecycle("archive_event", selected)}>Archive</button></>}</div></> : <p>Select an event to inspect it.</p>}
        <div className="calendar-adoption-archive"><h4>Archive</h4>{workspace.archived_events.map((event) => <button key={event.event_ref} type="button" onClick={() => setSelectedRef(event.event_ref)}>{event.title}</button>)}{!workspace.archived_events.length ? <p>No archived events.</p> : null}</div>
      </aside>
    </div> : null}

    {workspace?.status === "ready" ? <div className="calendar-adoption-editor-grid"><section className="panel calendar-adoption-editor"><div className="panel-heading"><div><p className="eyebrow">{editing ? "Edit event" : "New event"}</p><h3>{editing ? editing.title : "Add to your calendar"}</h3></div>{editing ? <button type="button" onClick={() => { setEditing(null); setDraft(eventDraft(workspace.calendars[0]?.calendar_ref ?? "")); }}>Cancel edit</button> : null}</div><div className="calendar-adoption-fields"><label>Title<input value={draft.title} onChange={(event) => setDraft((value) => ({ ...value, title: event.target.value }))} /></label><label>Calendar<select value={draft.calendar_ref} onChange={(event) => setDraft((value) => ({ ...value, calendar_ref: event.target.value }))}>{workspace.calendars.filter((item) => !item.archived).map((item) => <option key={item.calendar_ref} value={item.calendar_ref}>{item.name}</option>)}</select></label><label>Starts<input type="datetime-local" value={draft.starts_at} onChange={(event) => setDraft((value) => ({ ...value, starts_at: event.target.value }))} /></label><label>Ends<input type="datetime-local" value={draft.ends_at} onChange={(event) => setDraft((value) => ({ ...value, ends_at: event.target.value }))} /></label><label>Location<input value={draft.location ?? ""} onChange={(event) => setDraft((value) => ({ ...value, location: event.target.value }))} /></label><label>Repeats<select value={draft.recurrence?.frequency ?? "none"} onChange={(event) => setDraft((value) => ({ ...value, recurrence: event.target.value === "none" ? null : { frequency: event.target.value as "daily" | "weekly" | "monthly", interval: 1, timezone: value.timezone, weekdays: event.target.value === "weekly" ? [new Date(value.starts_at).getDay() === 0 ? 6 : new Date(value.starts_at).getDay() - 1] : [] } }))}><option value="none">Does not repeat</option><option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option></select></label><label className="calendar-adoption-wide">Notes<textarea value={draft.description ?? ""} onChange={(event) => setDraft((value) => ({ ...value, description: event.target.value }))} /></label></div><button type="button" disabled={busy || !draft.title.trim() || !draft.calendar_ref} onClick={submitEvent}>Review {editing ? "update" : "new event"}</button></section>
      <section className="panel calendar-adoption-calendars"><h3>Calendars</h3>{workspace.calendars.map((item) => <div key={item.calendar_ref}><span className="calendar-adoption-dot" /><strong>{item.name}</strong><small>{item.timezone}</small></div>)}<label>Add another calendar<input placeholder="Calendar name" value={calendarDraft.name} onChange={(event) => setCalendarDraft((value) => ({ ...value, name: event.target.value }))} /></label><button type="button" disabled={busy || !calendarDraft.name.trim()} onClick={submitCalendar}>Review new calendar</button><button type="button" disabled={busy || !workspace.can_undo} onClick={() => void runPreview({ action: "undo", expected_revision: workspace.revision }, "undo")}>Undo last change</button></section>
      <section className="panel calendar-adoption-recovery"><h3>Encrypted continuity</h3><p>Move this private calendar between your own computers with a passphrase-encrypted file. There is no automatic sync.</p><label>Backup passphrase<input type="password" autoComplete="new-password" value={passphrase} onChange={(event) => setPassphrase(event.target.value)} /></label><div><button type="button" disabled={busy || passphrase.length < 12} onClick={() => void downloadBackup()}>Download encrypted backup</button><label className="calendar-adoption-file">Open backup<input type="file" accept="application/json,.json" onChange={(event) => { const file = event.target.files?.[0]; if (file) void openBackup(file); }} /></label></div>{restoreBackup ? <button type="button" disabled={busy || passphrase.length < 12} onClick={() => void prepareRestore()}>Preview restore</button> : null}</section></div> : null}

    {pending ? <div className="calendar-adoption-confirm" role="dialog" aria-modal="true" aria-labelledby="calendar-change-review"><div className="panel warning"><p className="eyebrow">Exact local approval</p><h3 id="calendar-change-review">Review this Calendar change</h3><p>{reviewDetail(pending)}</p><p><strong>Only the encrypted local Calendar will change.</strong> No account, connector, model, notification, or external calendar write will occur.</p><div><button type="button" onClick={() => setPending(null)} disabled={busy}>Cancel</button><button type="button" onClick={() => void confirmMutation()} disabled={busy}>Confirm one local change</button></div></div></div> : null}
    {pendingRestore ? <div className="calendar-adoption-confirm" role="dialog" aria-modal="true" aria-labelledby="calendar-restore-review"><div className="panel warning"><p className="eyebrow">Exact restore approval</p><h3 id="calendar-restore-review">Review encrypted restore</h3><p>Restore {pendingRestore.preview.calendar_count} calendar{pendingRestore.preview.calendar_count === 1 ? "" : "s"} and {pendingRestore.preview.event_count} event{pendingRestore.preview.event_count === 1 ? "" : "s"}. {pendingRestore.preview.rollback_available ? "Undo will remain available." : "The target is empty, so there is no earlier local state to undo."}</p><div><button type="button" onClick={() => setPendingRestore(null)} disabled={busy}>Cancel</button><button type="button" onClick={() => void confirmRestore()} disabled={busy}>Confirm private restore</button></div></div></div> : null}
    <div className="calendar-adoption-receipt" aria-live="polite">Backend-owned encrypted Calendar · local-only manual changes · external reads, writes, sync, notifications, and scheduling remain blocked</div>
  </section>;
}
