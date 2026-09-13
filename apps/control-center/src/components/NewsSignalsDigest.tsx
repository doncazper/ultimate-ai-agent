import { useEffect, useState } from "react";
import { loadNewsSignalsSummary } from "../api/client";
import type { NewsSignalReadItem, NewsSignalsSummary } from "../api/types";
import { useBackendTruthMutationBinding } from "../backendTruthMutationBinding";

type DigestSurface = "today" | "briefing";
type DigestState =
  | { status: "loading" | "unavailable" }
  | { status: "ready"; summary: NewsSignalsSummary; bindingKey: string };

function projectedItems(
  summary: NewsSignalsSummary,
  surface: DigestSurface,
): NewsSignalReadItem[] | null {
  const refs = surface === "today"
    ? summary.today_projection.item_refs
    : summary.morning_briefing_projection.candidate_refs;
  const records = summary.projection_items ?? summary.items;
  const items = new Map(records.map((item) => [item.signal_ref, item]));
  const sources = new Map(summary.source_readiness.map((source) => [source.source_ref, source]));
  if (
    items.size !== records.length
    || sources.size !== summary.source_readiness.length
    || new Set(refs).size !== refs.length
    || !Number.isFinite(Date.parse(summary.observed_at))
    || refs.length > (surface === "today" ? 3 : 5)
    || refs.some((ref) => {
      const item = items.get(ref);
      return !item
        || item.source_state !== "ready"
        || sources.get(item.source_ref)?.state !== "ready"
        || (surface === "briefing" && !item.briefing_candidate);
    })
  ) {
    return null;
  }
  // Selection and order belong to the Python projection, not a UI ranker.
  return refs.map((ref) => items.get(ref)!);
}

export function NewsSignalsDigest({
  authoritative,
  surface,
}: {
  authoritative: boolean;
  surface: DigestSurface;
}) {
  const binding = useBackendTruthMutationBinding();
  const snapshotRef = binding?.snapshotRef ?? null;
  const backendRevisionRef = binding?.backendRevisionRef ?? null;
  const backendInstanceRef = binding?.backendInstanceRef ?? null;
  const bindingKey = JSON.stringify([snapshotRef, backendRevisionRef, backendInstanceRef]);
  const canRead = authoritative && Boolean(snapshotRef && backendRevisionRef && backendInstanceRef);
  const [state, setState] = useState<DigestState>({ status: "loading" });
  const [requestGeneration, setRequestGeneration] = useState(0);

  useEffect(() => {
    let active = true;
    if (!canRead || !snapshotRef || !backendRevisionRef || !backendInstanceRef) {
      setState({ status: "unavailable" });
      return () => { active = false; };
    }
    setState({ status: "loading" });
    loadNewsSignalsSummary({ snapshotRef, backendRevisionRef, backendInstanceRef }).then(
      (summary) => { if (active) setState({ status: "ready", summary, bindingKey }); },
      () => { if (active) setState({ status: "unavailable" }); },
    );
    return () => { active = false; };
  }, [canRead, snapshotRef, backendRevisionRef, backendInstanceRef, bindingKey, requestGeneration]);

  const summary = canRead && state.status === "ready" && state.bindingKey === bindingKey ? state.summary : null;
  const items = summary ? projectedItems(summary, surface) : null;
  const loading = canRead && (state.status === "loading" || (state.status === "ready" && state.bindingKey !== bindingKey));
  const unavailable = !canRead || state.status === "unavailable" || (summary !== null && items === null);

  return (
    <div className="news-signals-digest" aria-label={surface === "today" ? "Today News snapshot" : "Briefing News snapshot"}>
      {loading ? <p role="status">Loading reviewed local News…</p> : null}
      {unavailable ? <p role="status">News is unavailable. Verify the local backend or retry; no News items are being shown.</p> : null}
      {summary && items ? <>
        {items.length > 0 ? <ul className="news-signals-digest-list">
          {items.map((item) => <li key={item.signal_ref}>
            <h4>{item.title}</h4>
            <p>{item.safe_summary}</p>
            <small>{item.source_label} · {item.freshness_state === "fresh" ? "Fresh when checked" : item.freshness_state === "stale" ? "Stale when checked" : "Freshness unknown"} · {item.confidence_state} confidence</small>
            {item.conflict_state !== "none" ? <p>Conflicting source evidence — inspect in News.</p> : null}
          </li>)}
        </ul> : <p role="status">{summary.status === "blocked_no_graduated_source"
          ? "No reviewed local News sources yet. Add a source in News."
          : summary.status === "blocked_source_unavailable"
            ? "News sources are unavailable or safe-disabled. Review their status in News."
            : surface === "briefing"
              ? "No News candidates are eligible for this briefing."
              : "No News items are eligible for Today."}</p>}
        <p className="news-signals-digest-note">Snapshot checked <time dateTime={summary.observed_at}>{new Date(summary.observed_at).toLocaleString()}</time>. Local artifacts only; no live source fetch.</p>
        {surface === "briefing" && items.length > 0 ? <p className="news-signals-digest-note">Candidates need review in News; nothing is sent or executed.</p> : null}
      </> : null}
      <div className="news-signals-digest-actions">
        <a href="/news">Open News for inspection</a>
        <button disabled={!canRead || loading} onClick={() => {
          setState({ status: "loading" });
          setRequestGeneration((generation) => generation + 1);
        }} type="button">Refresh News</button>
      </div>
    </div>
  );
}
