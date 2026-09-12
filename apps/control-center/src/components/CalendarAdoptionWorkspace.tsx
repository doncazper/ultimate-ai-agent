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
  CalendarAdoptionCalendar,
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

function zonedParts(iso: string, timezone: string): Record<string, string> {
  return Object.fromEntries(new Intl.DateTimeFormat("en-CA", {
    timeZone: timezone, year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23",
  }).formatToParts(new Date(iso)).filter((part) => part.type !== "literal").map((part) => [part.type, part.value]));
}

function localInput(iso: string, timezone: string): string {
  const parts = zonedParts(iso, timezone);
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

function localInputToIso(value: string, timezone: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/.exec(value);
  if (!match) throw new Error("Enter a valid local date and time.");
  const [, year, month, day, hour, minute] = match;
  const desired = Date.UTC(Number(year), Number(month) - 1, Number(day), Number(hour), Number(minute));
  let instant = desired;
  for (let attempt = 0; attempt < 4; attempt += 1) {
    const parts = zonedParts(new Date(instant).toISOString(), timezone);
    const observed = Date.UTC(Number(parts.year), Number(parts.month) - 1, Number(parts.day), Number(parts.hour), Number(parts.minute));
    instant += desired - observed;
  }
  const iso = new Date(instant).toISOString();
  if (localInput(iso, timezone) !== value) throw new Error("That local time does not exist in the selected timezone.");
  return iso;
}

function initialTimes(timezone: string): { starts_at: string; ends_at: string } {
  const start = new Date();
  start.setMinutes(0, 0, 0);
  start.setHours(start.getHours() + 1);
  const end = new Date(start.getTime() + 60 * 60 * 1_000);
  return { starts_at: localInput(start.toISOString(), timezone), ends_at: localInput(end.toISOString(), timezone) };
}

function eventDraft(
  calendarRef: string,
  event?: CalendarAdoptionEvent,
): CalendarAdoptionEventDraft {
  const timezone = event?.timezone ?? localTimezone();
  const times = initialTimes(timezone);
  return {
    event_ref: event?.event_ref ?? newIdempotencyRef("event").replace("idempotency-ref", "calendar-event-ref"),
    calendar_ref: event?.calendar_ref ?? calendarRef,
    title: event?.title ?? "",
    description: event?.description ?? "",
    location: event?.location ?? "",
    starts_at: event ? localInput(event.starts_at, timezone) : times.starts_at,
    ends_at: event ? localInput(event.ends_at, timezone) : times.ends_at,
    timezone,
    all_day: event?.all_day ?? false,
    participant_items: event?.participant_items ?? [],
    reminder_items: event?.reminder_items ?? [],
    recurrence: event?.recurrence ?? null,
  };
}

function weekdayForLocalInput(value: string): number {
  const day = new Date(`${value.slice(0, 10)}T00:00:00Z`).getUTCDay();
  return day === 0 ? 6 : day - 1;
}

function networkEventDraft(draft: CalendarAdoptionEventDraft, original: CalendarAdoptionEvent | null = null): CalendarAdoptionEventDraft {
  const preserveOriginalOffset = original?.timezone === draft.timezone;
  const originalStartDate = original
    ? localInput(original.starts_at, draft.timezone).slice(0, 10)
    : null;
  const weeklyStartDateChanged = originalStartDate !== draft.starts_at.slice(0, 10);
  const startsAt = preserveOriginalOffset && localInput(original.starts_at, draft.timezone) === draft.starts_at
    ? original.starts_at
    : localInputToIso(draft.starts_at, draft.timezone);
  const endsAt = preserveOriginalOffset && localInput(original.ends_at, draft.timezone) === draft.ends_at
    ? original.ends_at
    : localInputToIso(draft.ends_at, draft.timezone);
  return {
    ...draft,
    title: draft.title.trim(),
    description: draft.description?.trim() || null,
    location: draft.location?.trim() || null,
    starts_at: startsAt,
    ends_at: endsAt,
    recurrence: draft.recurrence?.frequency === "weekly"
      ? {
          ...draft.recurrence,
          weekdays: weeklyStartDateChanged
            ? [weekdayForLocalInput(draft.starts_at)]
            : draft.recurrence.weekdays,
        }
      : draft.recurrence,
  };
}

function formatDate(iso: string, timezone: string, options: Intl.DateTimeFormatOptions): string {
  return new Intl.DateTimeFormat("en-US", { ...options, timeZone: timezone }).format(new Date(iso));
}

function recurrenceReview(event: CalendarAdoptionEventDraft): string {
  const recurrence = event.recurrence;
  if (!recurrence) return "none";
  const weekdayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
  const weekdays = recurrence.weekdays.length
    ? recurrence.weekdays.map((day) => `${weekdayNames[day] ?? "invalid"} (${day})`).join(", ")
    : "none";
  return `${recurrence.frequency}; interval ${recurrence.interval}; timezone ${recurrence.timezone}; weekdays ${weekdays}; month day ${recurrence.month_day ?? "none"}; count ${recurrence.count ?? "none"}; until ${recurrence.until ?? "none"}`;
}

export function shiftCalendarAnchor(anchor: string, view: CalendarAdoptionView, direction: -1 | 1, timezone: string): string {
  const wall = new Date(`${localInput(anchor, timezone)}:00Z`);
  if (view === "month") {
    const day = wall.getUTCDate();
    wall.setUTCDate(1);
    wall.setUTCMonth(wall.getUTCMonth() + direction);
    const lastDay = new Date(Date.UTC(wall.getUTCFullYear(), wall.getUTCMonth() + 1, 0)).getUTCDate();
    wall.setUTCDate(Math.min(day, lastDay));
  } else {
    wall.setUTCDate(wall.getUTCDate() + direction * (view === "day" ? 1 : view === "week" ? 7 : 30));
  }
  const shifted = wall.toISOString().slice(0, 16);
  try {
    return localInputToIso(shifted, timezone);
  } catch {
    return localInputToIso(`${shifted.slice(0, 10)}T12:00`, timezone);
  }
}

function inclusiveRangeEnd(iso: string): string {
  return new Date(new Date(iso).getTime() - 1).toISOString();
}

function reviewDetail(pending: PendingMutation): string {
  const { request, preview } = pending;
  const revision = `Revision ${preview.expected_revision} → ${preview.resulting_revision}.`;
  if (request.action === "create_event" || request.action === "update_event") {
    const event = request.event;
    if (!event) return `The event details are unavailable. ${revision}`;
    const recurrence = recurrenceReview(event);
    return `${request.action === "create_event" ? "Create" : "Update"} “${event.title}”. Event: ${event.event_ref}; Calendar: ${event.calendar_ref}; Starts: ${formatDate(event.starts_at, event.timezone, { dateStyle: "medium", timeStyle: "short" })} (${event.timezone}); Ends: ${formatDate(event.ends_at, event.timezone, { dateStyle: "medium", timeStyle: "short" })} (${event.timezone}); All day: ${event.all_day ? "yes" : "no"}; Location: ${event.location || "none"}; Notes: ${event.description || "none"}; Repeats: ${recurrence}; Participants: ${event.participant_items.length}; Reminders: ${event.reminder_items.length}. ${revision}`;
  }
  if (request.action === "initialize" || request.action === "create_calendar") {
    return `${request.action === "initialize" ? "Initialize Calendar with" : "Add"} “${request.calendar?.name ?? "calendar"}”. ${revision}`;
  }
  if (request.action === "archive_event" || request.action === "recover_event") {
    return `${request.action === "archive_event" ? "Archive" : "Recover"} ${request.target_ref}. ${revision}`;
  }
  if (request.action === "archive_calendar" || request.action === "recover_calendar") {
    return `${request.action === "archive_calendar" ? "Archive" : "Recover"} calendar ${request.target_ref}. ${revision}`;
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
      const refs = [...next.occurrence_items.map((item) => item.occurrence.occurrence_ref), ...next.archived_events.map((item) => item.event_ref)];
      return refs.includes(current) ? current : (next.occurrence_items[0]?.occurrence.occurrence_ref ?? next.archived_events[0]?.event_ref ?? "");
    });
    setDraft((current) => {
      const activeCalendarRefs = new Set(next.calendars.filter((item) => !item.archived).map((item) => item.calendar_ref));
      if (activeCalendarRefs.has(current.calendar_ref)) return current;
      return eventDraft(next.calendars.find((item) => !item.archived)?.calendar_ref ?? "");
    });
  }, []);

  const refresh = useCallback(async () => {
    setBusy(true); setError("");
    try {
      const next = await loadCalendarAdoptionWorkspace(view, anchor, timezone);
      acceptWorkspace(next);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The private Calendar could not be loaded.");
    } finally { setBusy(false); }
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
  const selectedOccurrence = workspace?.occurrence_items.find((item) => item.occurrence.occurrence_ref === selectedRef);
  const selected = selectedOccurrence?.event ?? events.find((item) => item.event_ref === selectedRef) ?? null;

  useEffect(() => {
    if (!editing || !workspace) return;
    const current = events.find((event) => event.event_ref === editing.event_ref);
    if (current && JSON.stringify(current) !== JSON.stringify(editing)) {
      setEditing(null);
      setDraft(eventDraft(workspace.calendars.find((item) => !item.archived)?.calendar_ref ?? ""));
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
      setPending(null); setEditing(null); setDraft(eventDraft(workspace?.calendars.find((item) => !item.archived)?.calendar_ref ?? ""));
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
    const initialization = workspace.status === "onboarding" || workspace.status === "setup_incomplete";
    void runPreview({
      action: initialization ? "initialize" : "create_calendar",
      expected_revision: workspace.revision,
      calendar: { ...calendarDraft, name: calendarDraft.name.trim(), timezone },
    }, initialization ? "initialize" : "create-calendar");
  }, [calendarDraft, runPreview, timezone, workspace]);

  const applyTimezone = useCallback(() => {
    const candidate = timezoneDraft.trim();
    try {
      Intl.DateTimeFormat("en-US", { timeZone: candidate }).format(new Date());
      setTimezone(candidate);
      if (!editing) {
        setDraft((value) => ({
          ...value,
          timezone: candidate,
          recurrence: value.recurrence
            ? { ...value.recurrence, timezone: candidate }
            : null,
        }));
      }
      setError("");
    } catch {
      setError("Enter a valid IANA timezone, such as America/Los_Angeles or UTC.");
    }
  }, [editing, timezoneDraft]);

  const submitEvent = useCallback(() => {
    if (!workspace || !draft.title.trim() || !draft.calendar_ref) return;
    let prepared: CalendarAdoptionEventDraft;
    try {
      const selectedDraft = editing
        ? draft
        : {
            ...draft,
            timezone,
            recurrence: draft.recurrence
              ? { ...draft.recurrence, timezone }
              : null,
          };
      prepared = networkEventDraft(selectedDraft, editing);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Enter valid event times.");
      return;
    }
    if (new Date(prepared.ends_at) <= new Date(prepared.starts_at)) {
      setError("End time must be after start time."); return;
    }
    void runPreview({
      action: editing ? "update_event" : "create_event",
      expected_revision: workspace.revision,
      ...(editing ? { target_ref: editing.event_ref } : {}),
      event: prepared,
    }, editing ? "update-event" : "create-event");
  }, [draft, editing, runPreview, timezone, workspace]);

  const startEdit = useCallback((event: CalendarAdoptionEvent) => {
    setEditing(event); setDraft(eventDraft(event.calendar_ref, event));
  }, []);

  const lifecycle = useCallback((action: "archive_event" | "recover_event", event: CalendarAdoptionEvent) => {
    if (!workspace) return;
    void runPreview({ action, expected_revision: workspace.revision, target_ref: event.event_ref }, action);
  }, [runPreview, workspace]);

  const calendarLifecycle = useCallback((action: "archive_calendar" | "recover_calendar", calendar: CalendarAdoptionCalendar) => {
    if (!workspace) return;
    void runPreview({ action, expected_revision: workspace.revision, target_ref: calendar.calendar_ref }, action);
  }, [runPreview, workspace]);

  const selectedCalendar = selected
    ? workspace?.calendars.find((item) => item.calendar_ref === selected.calendar_ref) ?? null
    : null;

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
      <button type="button" aria-label="Previous period" disabled={busy} onClick={() => setAnchor((value) => shiftCalendarAnchor(value, view, -1, timezone))}>←</button>
      <button type="button" aria-label="Next period" disabled={busy} onClick={() => setAnchor((value) => shiftCalendarAnchor(value, view, 1, timezone))}>→</button>
      <div className="calendar-adoption-view-switcher" aria-label="Calendar view">{VIEWS.map((item) => <button className={item === view ? "active" : ""} key={item} type="button" onClick={() => setView(item)}>{item}</button>)}</div>
      <label><span className="sr-only">Calendar timezone</span><input aria-label="Calendar timezone" value={timezoneDraft} onChange={(event) => setTimezoneDraft(event.target.value)} /></label>
      <button type="button" disabled={busy || timezoneDraft.trim() === timezone} onClick={applyTimezone}>Apply timezone</button>
      <span className="status-pill compact">revision {workspace?.revision ?? 0}</span>
    </div>

    {!workspace ? <div className="panel">Loading your local Calendar…</div> : workspace.status === "recovery_required" || workspace.status === "setup_incomplete" ? <div className="panel warning"><strong>Ordinary Calendar changes are paused</strong><p>{workspace.next_safe_action}</p></div> : null}

    {workspace?.status === "onboarding" || workspace?.status === "setup_incomplete" ? <section className="panel calendar-adoption-onboarding"><h3>{workspace.status === "setup_incomplete" ? "Finish your private calendar setup" : "Create your first private calendar"}</h3><p>This stays encrypted on this computer until you export an encrypted backup.</p><label>Name<input value={calendarDraft.name} onChange={(event) => setCalendarDraft((value) => ({ ...value, name: event.target.value }))} /></label><button type="button" disabled={busy || !calendarDraft.name.trim()} onClick={submitCalendar}>Review setup</button></section> : null}

    {workspace?.status === "onboarding" || workspace?.status === "setup_incomplete" || workspace?.status === "recovery_required" ? <section className="panel calendar-adoption-recovery"><h3>Restore encrypted Calendar</h3><p>Open a passphrase-encrypted backup from another one of your computers. There is no automatic sync.</p><label>Backup or restore passphrase<input type="password" autoComplete="new-password" value={passphrase} onChange={(event) => setPassphrase(event.target.value)} /></label><label className="calendar-adoption-file">Open backup<input type="file" accept="application/json,.json" onChange={(event) => { const file = event.target.files?.[0]; if (file) void openBackup(file); }} /></label>{restoreBackup ? <button type="button" disabled={busy || passphrase.length < 12} onClick={() => void prepareRestore()}>Preview restore</button> : null}</section> : null}

    {workspace?.status === "ready" ? <div className="calendar-adoption-layout">
      <section className="calendar-adoption-main">
        <div className="calendar-adoption-range"><div><strong>{formatDate(workspace.range_starts_at, timezone, { month: "long", day: "numeric", year: "numeric" })}</strong><span> through {formatDate(inclusiveRangeEnd(workspace.range_ends_at), timezone, { month: "short", day: "numeric" })}</span></div><label><span className="sr-only">Search Calendar</span><input aria-label="Search private Calendar" type="search" placeholder="Search title, notes, or place…" value={query} onChange={(event) => setQuery(event.target.value)} /></label></div>
        {workspace.conflict_items.length ? <div className="panel warning" role="status"><strong>{workspace.conflict_items.length} schedule conflict{workspace.conflict_items.length === 1 ? "" : "s"}</strong><p>Overlapping local events are highlighted for your review.</p></div> : null}
        <div className="calendar-adoption-days">{grouped.map(([day, items]) => <section key={day}><header><strong>{day}</strong><span>{items.length}</span></header>{items.map((item) => {
          const conflicted = workspace.conflict_items.some((conflict) => conflict.first_occurrence_ref === item.occurrence.occurrence_ref || conflict.second_occurrence_ref === item.occurrence.occurrence_ref);
          return <button className={`calendar-adoption-event${selectedRef === item.occurrence.occurrence_ref ? " selected" : ""}${conflicted ? " conflict" : ""}`} key={item.occurrence.occurrence_ref} type="button" onClick={() => setSelectedRef(item.occurrence.occurrence_ref)}><span>{formatDate(item.occurrence.starts_at, timezone, { hour: "numeric", minute: "2-digit" })}–{formatDate(item.occurrence.ends_at, timezone, { hour: "numeric", minute: "2-digit" })}</span><strong>{item.event.title}</strong><small>{workspace.calendars.find((calendar) => calendar.calendar_ref === item.event.calendar_ref)?.name ?? "Calendar"}{conflicted ? " · Conflict" : ""}</small></button>;
        })}</section>)}{!grouped.length ? <div className="calendar-adoption-empty"><strong>No events in this view</strong><p>Create one below or move to another period.</p></div> : null}</div>
      </section>
      <aside className="calendar-adoption-inspector"><h3>{selected?.title ?? "Event details"}</h3>{selected ? <><p>{selected.description || "No notes yet."}</p><dl><div><dt>When</dt><dd>{formatDate(selectedOccurrence?.occurrence.starts_at ?? selected.starts_at, selected.timezone, { dateStyle: "medium", timeStyle: "short" })} – {formatDate(selectedOccurrence?.occurrence.ends_at ?? selected.ends_at, selected.timezone, { dateStyle: "medium", timeStyle: "short" })}</dd></div><div><dt>Location</dt><dd>{selected.location || "None"}</dd></div><div><dt>Calendar</dt><dd>{selectedCalendar?.name ?? "Unknown"}</dd></div></dl><div className="calendar-adoption-actions">{selected.archived ? selectedCalendar?.archived ? <><p>Recover this calendar before recovering its events.</p><button type="button" disabled={busy} onClick={() => calendarLifecycle("recover_calendar", selectedCalendar)}>Recover calendar</button></> : <button type="button" disabled={busy} onClick={() => lifecycle("recover_event", selected)}>Recover event</button> : <><button type="button" disabled={busy} onClick={() => startEdit(selected)}>Edit</button><button type="button" disabled={busy} onClick={() => lifecycle("archive_event", selected)}>Archive</button></>}</div></> : <p>Select an event to inspect it.</p>}
        <div className="calendar-adoption-archive"><h4>Archive</h4>{workspace.archived_events.map((event) => <button key={event.event_ref} type="button" onClick={() => setSelectedRef(event.event_ref)}>{event.title}</button>)}{!workspace.archived_events.length ? <p>No archived events.</p> : null}</div>
      </aside>
    </div> : null}

    {workspace?.status === "ready" ? <div className="calendar-adoption-editor-grid"><section className="panel calendar-adoption-editor"><div className="panel-heading"><div><p className="eyebrow">{editing ? "Edit event" : "New event"}</p><h3>{editing ? editing.title : "Add to your calendar"}</h3></div>{editing ? <button type="button" onClick={() => { setEditing(null); setDraft(eventDraft(workspace.calendars.find((item) => !item.archived)?.calendar_ref ?? "")); }}>Cancel edit</button> : null}</div><div className="calendar-adoption-fields"><label>Title<input value={draft.title} onChange={(event) => setDraft((value) => ({ ...value, title: event.target.value }))} /></label><label>Calendar<select value={draft.calendar_ref} onChange={(event) => setDraft((value) => ({ ...value, calendar_ref: event.target.value }))}>{workspace.calendars.filter((item) => !item.archived).map((item) => <option key={item.calendar_ref} value={item.calendar_ref}>{item.name}</option>)}</select></label><label>Starts<input type="datetime-local" value={draft.starts_at} onChange={(event) => setDraft((value) => ({ ...value, starts_at: event.target.value }))} /></label><label>Ends<input type="datetime-local" value={draft.ends_at} onChange={(event) => setDraft((value) => ({ ...value, ends_at: event.target.value }))} /></label><label>Location<input value={draft.location ?? ""} onChange={(event) => setDraft((value) => ({ ...value, location: event.target.value }))} /></label><label>Repeats<select value={draft.recurrence?.frequency ?? "none"} onChange={(event) => setDraft((value) => ({ ...value, recurrence: event.target.value === "none" ? null : { frequency: event.target.value as "daily" | "weekly" | "monthly", interval: 1, timezone: value.timezone, weekdays: event.target.value === "weekly" ? [weekdayForLocalInput(value.starts_at)] : [] } }))}><option value="none">Does not repeat</option><option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option></select></label><label className="calendar-adoption-wide">Notes<textarea value={draft.description ?? ""} onChange={(event) => setDraft((value) => ({ ...value, description: event.target.value }))} /></label></div><button type="button" disabled={busy || !draft.title.trim() || !draft.calendar_ref} onClick={submitEvent}>Review {editing ? "update" : "new event"}</button></section>
      <section className="panel calendar-adoption-calendars"><h3>Calendars</h3>{workspace.calendars.map((item) => <div key={item.calendar_ref}><span className="calendar-adoption-dot" /><strong>{item.name}</strong><small>{item.timezone}{item.archived ? " · Archived" : ""}</small>{item.archived ? <button type="button" disabled={busy} onClick={() => calendarLifecycle("recover_calendar", item)}>Recover calendar</button> : null}</div>)}<label>Add another calendar<input placeholder="Calendar name" value={calendarDraft.name} onChange={(event) => setCalendarDraft((value) => ({ ...value, name: event.target.value }))} /></label><button type="button" disabled={busy || !calendarDraft.name.trim()} onClick={submitCalendar}>Review new calendar</button><button type="button" disabled={busy || !workspace.can_undo} onClick={() => void runPreview({ action: "undo", expected_revision: workspace.revision }, "undo")}>Undo last change</button></section>
      <section className="panel calendar-adoption-recovery"><h3>Encrypted continuity</h3><p>Move this private calendar between your own computers with a passphrase-encrypted file. There is no automatic sync.</p><label>Backup or restore passphrase<input type="password" autoComplete="new-password" value={passphrase} onChange={(event) => setPassphrase(event.target.value)} /></label><div><button type="button" disabled={busy || passphrase.length < 12} onClick={() => void downloadBackup()}>Download encrypted backup</button><label className="calendar-adoption-file">Open backup<input type="file" accept="application/json,.json" onChange={(event) => { const file = event.target.files?.[0]; if (file) void openBackup(file); }} /></label></div>{restoreBackup ? <button type="button" disabled={busy || passphrase.length < 12} onClick={() => void prepareRestore()}>Preview restore</button> : null}</section></div> : null}

    {pending ? <div className="calendar-adoption-confirm" role="dialog" aria-modal="true" aria-labelledby="calendar-change-review"><div className="panel warning"><p className="eyebrow">Exact local approval</p><h3 id="calendar-change-review">Review this Calendar change</h3><p>{reviewDetail(pending)}</p><p><strong>Only the encrypted local Calendar will change.</strong> No account, connector, model, notification, or external calendar write will occur.</p><div><button type="button" onClick={() => setPending(null)} disabled={busy}>Cancel</button><button type="button" onClick={() => void confirmMutation()} disabled={busy}>Confirm one local change</button></div></div></div> : null}
    {pendingRestore ? <div className="calendar-adoption-confirm" role="dialog" aria-modal="true" aria-labelledby="calendar-restore-review"><div className="panel warning"><p className="eyebrow">Exact restore approval</p><h3 id="calendar-restore-review">Review encrypted restore</h3><p>Restore {pendingRestore.preview.calendar_count} calendar{pendingRestore.preview.calendar_count === 1 ? "" : "s"} and {pendingRestore.preview.event_count} event{pendingRestore.preview.event_count === 1 ? "" : "s"}. {pendingRestore.preview.rollback_available ? "Undo will remain available." : pendingRestore.preview.impact_status === "empty_target" ? "The target is empty, so there is no earlier local state to undo." : "This will replace existing local Calendar state, and undo will not be available."}</p><div><button type="button" onClick={() => setPendingRestore(null)} disabled={busy}>Cancel</button><button type="button" onClick={() => void confirmRestore()} disabled={busy}>Confirm private restore</button></div></div></div> : null}
    <div className="calendar-adoption-receipt" aria-live="polite">Backend-owned encrypted Calendar · local-only manual changes · external reads, writes, sync, notifications, and scheduling remain blocked</div>
  </section>;
}
