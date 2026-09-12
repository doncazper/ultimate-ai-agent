import { useCallback, useEffect, useMemo, useState } from "react";
import {
  captureNewsSignalsAdoptionApproval,
  commitNewsSignalsAdoptionMutation,
  loadNewsSignalsAdoptionWorkspace,
  previewNewsSignalsAdoptionMutation,
} from "../api/client";
import type {
  NewsSignalReadItem,
  NewsSignalSourceKind,
  NewsSignalsAdoptionMutationPreview,
  NewsSignalsAdoptionMutationRequest,
  NewsSignalsAdoptionView,
  NewsSignalsSummary,
} from "../api/types";
import { useBackendTruthMutationBinding } from "../backendTruthMutationBinding";
import { NorthStarIcon, type IconReference } from "./NorthStarIcon";

type SignalFilter = "for-you" | "brief" | "official" | "community";
type IntakeMode = "signal" | "source";

const FILTERS: Array<{ id: SignalFilter; label: string }> = [
  { id: "for-you", label: "For you" },
  { id: "brief", label: "Brief candidates" },
  { id: "official", label: "Official sources" },
  { id: "community", label: "Community" },
];

const SOURCE_ICONS: Record<NewsSignalSourceKind, IconReference> = {
  official: "badge-check",
  community: "message-circle",
  rss: "rss",
  public_social: "signal",
  local: "database",
};

function newIdempotencyRef(action: string): string {
  const suffix =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID().replaceAll("-", "")
      : `${Date.now()}${Math.random().toString(16).slice(2)}`;
  return `idempotency-ref:news-signals-adoption-ui:${action.replaceAll("_", "-")}:${suffix}`;
}

function currentLocalDateTime(): string {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60_000)
    .toISOString()
    .slice(0, 16);
}

export function NewsSignalsPreviewPanel() {
  const mutationBinding = useBackendTruthMutationBinding();
  const [workspace, setWorkspace] = useState<NewsSignalsAdoptionView | null>(null);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "failed">(
    "loading",
  );
  const [activeFilter, setActiveFilter] = useState<SignalFilter>("for-you");
  const [selectedRef, setSelectedRef] = useState<string | null>(null);
  const [selectedSourceRef, setSelectedSourceRef] = useState<string | null>(null);
  const [intakeMode, setIntakeMode] = useState<IntakeMode>("source");
  const [sourceLabel, setSourceLabel] = useState("");
  const [sourceKind, setSourceKind] = useState<NewsSignalSourceKind>("local");
  const [signalTitle, setSignalTitle] = useState("");
  const [signalSummary, setSignalSummary] = useState("");
  const [signalTopic, setSignalTopic] = useState("");
  const [signalPublishedAt, setSignalPublishedAt] = useState(currentLocalDateTime);
  const [pending, setPending] = useState<{
    request: NewsSignalsAdoptionMutationRequest;
    preview: NewsSignalsAdoptionMutationPreview;
    idempotencyRef: string;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const summary = workspace?.summary ?? null;

  const acceptWorkspace = useCallback((value: NewsSignalsAdoptionView) => {
    setWorkspace(value);
    setSelectedRef((current) =>
      value.summary.items.some((item) => item.signal_ref === current)
        ? current
        : (value.summary.items[0]?.signal_ref ?? null),
    );
    setSelectedSourceRef((current) =>
      value.summary.source_readiness.some(
        (source) => source.source_ref === current && source.state === "ready",
      )
        ? current
        : (value.summary.source_readiness.find(
            (source) => source.state === "ready",
          )?.source_ref ?? null),
    );
    setLoadState("ready");
  }, []);

  const refresh = useCallback(async () => {
    const value = await loadNewsSignalsAdoptionWorkspace();
    acceptWorkspace(value);
  }, [acceptWorkspace]);

  useEffect(() => {
    let active = true;
    loadNewsSignalsAdoptionWorkspace()
      .then((value) => {
        if (!active) return;
        acceptWorkspace(value);
      })
      .catch(() => {
        if (!active) return;
        setWorkspace(null);
        setLoadState("failed");
      });
    return () => {
      active = false;
    };
  }, [acceptWorkspace]);

  const visibleItems = useMemo(
    () =>
      (summary?.items ?? []).filter((item) => {
        if (activeFilter === "brief") return item.briefing_candidate;
        if (activeFilter === "official") return item.source_kind === "official";
        if (activeFilter === "community") {
          return item.source_kind === "community";
        }
        return true;
      }),
    [activeFilter, summary],
  );
  const selectedItem =
    visibleItems.find((item) => item.signal_ref === selectedRef) ??
    visibleItems[0];
  const briefCandidateCount =
    summary?.morning_briefing_projection.candidate_refs.length ?? 0;
  const readySources =
    summary?.source_readiness.filter((source) => source.state === "ready") ?? [];
  const readySource =
    readySources.find((source) => source.source_ref === selectedSourceRef) ??
    readySources[0];
  const firstSource = summary?.source_readiness[0];
  const selectedPreference = workspace?.preferences.find(
    (preference) => preference.topic_ref === selectedItem?.topic_ref,
  );

  const runPreview = async (request: NewsSignalsAdoptionMutationRequest) => {
    setBusy(true);
    setError("");
    setNotice("");
    const idempotencyRef = newIdempotencyRef(request.action);
    try {
      const preview = await previewNewsSignalsAdoptionMutation(
        request,
        idempotencyRef,
      );
      setPending({ request, preview, idempotencyRef });
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The local News preview failed safely.",
      );
    } finally {
      setBusy(false);
    }
  };

  const confirmPending = async () => {
    if (!pending) return;
    setBusy(true);
    setError("");
    try {
      await captureNewsSignalsAdoptionApproval(
        pending.request,
        pending.preview,
        pending.idempotencyRef,
        mutationBinding,
      );
      await commitNewsSignalsAdoptionMutation(
        pending.request,
        pending.preview,
        pending.idempotencyRef,
        mutationBinding,
      );
      setPending(null);
      setNotice("The reviewed local News change was saved.");
      if (pending.request.action === "register_source") {
        setSourceLabel("");
        setIntakeMode("signal");
      }
      if (pending.request.action === "ingest_signal") {
        setSignalTitle("");
        setSignalSummary("");
        setSignalTopic("");
        setSignalPublishedAt(currentLocalDateTime());
      }
      await refresh();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The local News change was not saved.",
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="news-signals-preview" aria-labelledby="news-signals-heading">
      <header className="news-signals-header">
        <div className="news-signals-title-group">
          <span className="news-signals-title-icon" aria-hidden="true">
            <NorthStarIcon name="signal" />
          </span>
          <div>
            <div className="news-signals-kicker-row">
              <p className="eyebrow">Curated intelligence</p>
              <span className="news-preview-badge">Backend-owned read model</span>
            </div>
            <h1 id="news-signals-heading">News &amp; Signals</h1>
            <p>
              Redacted source artifacts ranked with visible freshness,
              confidence, and provenance boundaries.
            </p>
          </div>
        </div>
        <div className="news-signals-metrics" aria-label="Signal stream summary">
          <PreviewMetric label="Signals" value={String(summary?.items.length ?? 0)} />
          <PreviewMetric
            label="Ready sources"
            value={String(
              summary?.source_readiness.filter((source) => source.state === "ready")
                .length ?? 0,
            )}
          />
          <PreviewMetric label="Brief picks" value={String(briefCandidateCount)} />
        </div>
      </header>

      <AuthorityNotice loadState={loadState} summary={summary} />

      {error ? <p className="news-adoption-feedback error" role="alert">{error}</p> : null}
      {notice ? <p className="news-adoption-feedback" role="status">{notice}</p> : null}

      <section className="news-adoption-controls" aria-label="Local News intake">
        <div>
          <p className="eyebrow">Local intake</p>
          <h2>
            {intakeMode === "signal" && readySource
              ? "Add a reviewed signal"
              : readySource
                ? "Add another source"
                : "Add your first source"}
          </h2>
          <p>
            Enter already-redacted details only. This does not visit a website,
            connect an account, or call a model.
          </p>
          {readySource ? (
            <div className="news-intake-mode" aria-label="Local intake type">
              <button
                aria-pressed={intakeMode === "signal"}
                onClick={() => setIntakeMode("signal")}
                type="button"
              >
                Signal
              </button>
              <button
                aria-pressed={intakeMode === "source"}
                onClick={() => setIntakeMode("source")}
                type="button"
              >
                Source
              </button>
            </div>
          ) : null}
        </div>
        {intakeMode === "signal" && readySource ? (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (!workspace || !signalTitle.trim() || !signalSummary.trim() || !signalTopic.trim()) return;
              void runPreview({
                action: "ingest_signal",
                expected_revision: workspace.revision,
                signal_draft: {
                  source_ref: readySource.source_ref,
                  title: signalTitle.trim(),
                  safe_summary: signalSummary.trim(),
                  topic_label: signalTopic.trim(),
                  cluster_label: signalTitle.trim().slice(0, 80),
                  claim_label: `${signalTopic.trim()} reviewed`,
                  published_at: new Date(signalPublishedAt).toISOString(),
                  confidence_percent: 80,
                  evidence_class: "primary",
                  claim_stance: "unknown",
                },
              });
            }}
          >
            <label>
              Source
              <select
                onChange={(event) => setSelectedSourceRef(event.target.value)}
                value={readySource.source_ref}
              >
                {readySources.map((source) => (
                  <option key={source.source_ref} value={source.source_ref}>
                    {source.safe_label}
                  </option>
                ))}
              </select>
            </label>
            <label>Headline<input maxLength={140} onChange={(event) => setSignalTitle(event.target.value)} required value={signalTitle} /></label>
            <label>Redacted summary<input maxLength={320} onChange={(event) => setSignalSummary(event.target.value)} required value={signalSummary} /></label>
            <label>Topic<input maxLength={60} onChange={(event) => setSignalTopic(event.target.value)} required value={signalTopic} /></label>
            <label>Published<input onChange={(event) => setSignalPublishedAt(event.target.value)} required type="datetime-local" value={signalPublishedAt} /></label>
            <button disabled={busy} type="submit">Review signal</button>
          </form>
        ) : (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (!workspace || !sourceLabel.trim()) return;
              void runPreview({
                action: "register_source",
                expected_revision: workspace.revision,
                source_draft: {
                  safe_label: sourceLabel.trim(),
                  source_kind: sourceKind,
                  freshness_ttl_seconds: 86_400,
                },
              });
            }}
          >
            <label>Source name<input maxLength={80} onChange={(event) => setSourceLabel(event.target.value)} required value={sourceLabel} /></label>
            <label>
              Source type
              <select
                onChange={(event) =>
                  setSourceKind(event.target.value as NewsSignalSourceKind)
                }
                value={sourceKind}
              >
                <option value="official">Official</option>
                <option value="community">Community</option>
                <option value="rss">RSS artifact</option>
                <option value="public_social">Public commentary</option>
                <option value="local">Local artifact</option>
              </select>
            </label>
            <button disabled={busy} type="submit">Review source</button>
          </form>
        )}
        {workspace?.can_undo ? (
          <button
            disabled={busy}
            onClick={() => void runPreview({ action: "undo", expected_revision: workspace.revision })}
            type="button"
          >
            Review undo
          </button>
        ) : null}
        {workspace && readySource ? (
          <button
            disabled={busy}
            onClick={() => void runPreview({
              action: "set_source_state",
              expected_revision: workspace.revision,
              target_ref: readySource.source_ref,
              source_state: "safe_disabled",
            })}
            type="button"
          >
            Review safe-disable
          </button>
        ) : null}
        {workspace && !readySource && firstSource?.state === "safe_disabled" ? (
          <button
            disabled={busy}
            onClick={() => void runPreview({
              action: "set_source_state",
              expected_revision: workspace.revision,
              target_ref: firstSource.source_ref,
              source_state: "ready",
            })}
            type="button"
          >
            Review source recovery
          </button>
        ) : null}
      </section>

      {workspace?.archived_items.length ? (
        <section className="news-archived-items" aria-label="Archived News items">
          <div>
            <p className="eyebrow">Recovery</p>
            <h2>Archived signals</h2>
          </div>
          {workspace.archived_items.map((item) => (
            <button
              disabled={busy}
              key={item.signal_ref}
              onClick={() => void runPreview({
                action: "recover_signal",
                expected_revision: workspace.revision,
                target_ref: item.signal_ref,
              })}
              type="button"
            >
              Recover {item.title}
            </button>
          ))}
        </section>
      ) : null}

      {pending ? (
        <section className="news-adoption-review" aria-label="Review local News change">
          <div>
            <p className="eyebrow">Confirmation</p>
            <h2>Review this one local change</h2>
            <p>{pending.preview.safe_summary}</p>
            <small>Revision {pending.preview.expected_revision} → {pending.preview.resulting_revision}. No external action will run.</small>
          </div>
          <div>
            <button disabled={busy} onClick={() => setPending(null)} type="button">Cancel</button>
            <button disabled={busy || mutationBinding === null} onClick={() => void confirmPending()} type="button">Confirm and save</button>
          </div>
        </section>
      ) : null}

      <div className="news-signals-toolbar">
        <div className="news-filter-group" aria-label="News and Signals filters">
          {FILTERS.map((filter) => (
            <button
              aria-pressed={activeFilter === filter.id}
              className={activeFilter === filter.id ? "active" : ""}
              key={filter.id}
              onClick={() => setActiveFilter(filter.id)}
              type="button"
            >
              {filter.label}
            </button>
          ))}
        </div>
        <p>
          <span className="news-freshness-dot" /> {freshnessLabel(summary)}
        </p>
      </div>

      <div className="news-signals-workspace">
        <div className="news-signal-stream" aria-label="Curated signal stream">
          <div className="news-stream-heading">
            <div>
              <p className="eyebrow">Ranked for review</p>
              <h2>{filterHeading(activeFilter)}</h2>
            </div>
            <span>{visibleItems.length} items</span>
          </div>
          {loadState === "loading" ? (
            <EmptyStream title="Loading backend read model" />
          ) : visibleItems.length === 0 ? (
            <EmptyStream title={emptyStateLabel(summary, activeFilter)} />
          ) : (
            <div className="news-story-list">
              {visibleItems.map((item) => (
                <button
                  aria-label={`Inspect signal: ${item.title}`}
                  aria-pressed={selectedItem?.signal_ref === item.signal_ref}
                  className={`news-story-row source-${item.source_kind}`}
                  key={item.signal_ref}
                  onClick={() => setSelectedRef(item.signal_ref)}
                  type="button"
                >
                  <span className="news-story-source-icon" aria-hidden="true">
                    <NorthStarIcon name={SOURCE_ICONS[item.source_kind]} />
                  </span>
                  <span className="news-story-copy">
                    <span className="news-story-meta">
                      <strong>{item.source_label}</strong>
                      <span>{item.freshness_state}</span>
                      <span>{item.coverage_count} sources</span>
                    </span>
                    <strong className="news-story-title">{item.title}</strong>
                    <span className="news-story-summary">{item.safe_summary}</span>
                    <span className="news-story-footer">
                      <span>{safeRefLabel(item.topic_ref)}</span>
                      <span>{item.confidence_percent}% confidence</span>
                      <span className={item.briefing_candidate ? "brief-ready" : "watch"}>
                        {item.briefing_candidate ? "Brief candidate" : "Review only"}
                      </span>
                    </span>
                  </span>
                  <NorthStarIcon className="news-story-chevron" name="chevron-right" />
                </button>
              ))}
            </div>
          )}
        </div>

        {selectedItem ? (
          <SignalInspector
            busy={busy}
            item={selectedItem}
            onArchive={() => workspace && void runPreview({ action: "archive_signal", expected_revision: workspace.revision, target_ref: selectedItem.signal_ref })}
            onClearPreference={selectedPreference ? () => workspace && void runPreview({ action: "remove_preference", expected_revision: workspace.revision, topic_ref: selectedItem.topic_ref }) : undefined}
            onPrefer={() => workspace && void runPreview({ action: "set_preference", expected_revision: workspace.revision, topic_ref: selectedItem.topic_ref, preference_weight: 10 })}
          />
        ) : (
          <aside className="news-signal-inspector" aria-label="Signal detail">
            <p className="eyebrow">No selected signal</p>
            <h2>No source artifact is available for review</h2>
            <p className="news-inspector-summary">
              The UI does not substitute sample stories when backend evidence is
              missing, stale, blocked, or unavailable.
            </p>
          </aside>
        )}
      </div>
    </section>
  );
}

function AuthorityNotice({
  loadState,
  summary,
}: {
  loadState: "loading" | "ready" | "failed";
  summary: NewsSignalsSummary | null;
}) {
  let message = "Loading local backend truth. No source access is being attempted.";
  if (loadState === "failed") {
    message = "Backend read unavailable. No sample stories are shown as a fallback.";
  } else if (summary?.status === "blocked_no_graduated_source") {
    message = "No graduated news source. The stream remains empty until a separately accepted read-only lane supplies redacted artifacts.";
  } else if (summary) {
    message = "Read-only local artifacts only; external content is untrusted. No live fetch, account access, model summary, write, or action authority is enabled.";
  }
  return (
    <div className="news-preview-notice" role="status">
      <NorthStarIcon name="shield-check" />
      <span>{message}</span>
      <a href="/briefing">Open Morning Briefing</a>
    </div>
  );
}

function PreviewMetric({ label, value }: { label: string; value: string }) {
  return (
    <span className="news-preview-metric">
      <strong>{value}</strong>
      <small>{label}</small>
    </span>
  );
}

function EmptyStream({ title }: { title: string }) {
  return (
    <div className="news-deferred-controls">
      <strong>{title}</strong>
      <span>
        Review source readiness and blocked-state refs before relying on this
        surface.
      </span>
    </div>
  );
}

function SignalInspector({
  busy,
  item,
  onArchive,
  onClearPreference,
  onPrefer,
}: {
  busy: boolean;
  item: NewsSignalReadItem;
  onArchive: () => void;
  onClearPreference?: () => void;
  onPrefer: () => void;
}) {
  return (
    <aside className="news-signal-inspector" aria-label="Signal detail">
      <div className="news-inspector-heading">
        <div>
          <p className="eyebrow">Selected signal</p>
          <span className={item.briefing_candidate ? "brief-ready" : "watch"}>
            {item.briefing_candidate ? "Brief candidate" : "Review only"}
          </span>
        </div>
        <span className="news-source-kind">{sourceKindLabel(item.source_kind)}</span>
      </div>
      <h2>{item.title}</h2>
      <p className="news-inspector-summary">{item.safe_summary}</p>

      <section className="news-inspector-section emphasized">
        <h3>Truth posture</h3>
        <p>
          {item.evidence_class} evidence · {item.freshness_state} · {item.conflict_state}
        </p>
      </section>
      <section className="news-inspector-section">
        <h3>Why this was selected</h3>
        <ul>
          {item.rank_reason_refs.map((reason) => (
            <li key={reason}>
              <NorthStarIcon name="circle-check" />
              <span>{safeRefLabel(reason)}</span>
            </li>
          ))}
        </ul>
      </section>
      <section className="news-inspector-section">
        <h3>Coverage</h3>
        <div className="news-coverage-list">
          {item.coverage_source_refs.map((sourceRef) => (
            <span key={sourceRef}>{sourceRef}</span>
          ))}
        </div>
      </section>
      <dl className="news-signal-provenance">
        <div>
          <dt>Freshness</dt>
          <dd>{item.freshness_state}</dd>
        </div>
        <div>
          <dt>Safe ref</dt>
          <dd>{item.signal_ref}</dd>
        </div>
      </dl>
      <div className="news-deferred-controls">
        <strong>External content is untrusted evidence</strong>
        <span>
          Local ranking and archive choices cannot mint source, account, model,
          or execution authority.
        </span>
        <span className="news-inspector-actions">
          {onClearPreference ? (
            <button disabled={busy} onClick={onClearPreference} type="button">Clear topic preference</button>
          ) : (
            <button disabled={busy} onClick={onPrefer} type="button">Prefer this topic</button>
          )}
          <button disabled={busy} onClick={onArchive} type="button">Review archive</button>
        </span>
      </div>
    </aside>
  );
}

function filterHeading(filter: SignalFilter): string {
  if (filter === "brief") return "Morning brief candidates";
  if (filter === "official") return "Official source updates";
  if (filter === "community") return "Community signals";
  return "For you";
}

function sourceKindLabel(kind: NewsSignalSourceKind): string {
  const labels: Record<NewsSignalSourceKind, string> = {
    official: "Primary source",
    community: "Community",
    rss: "RSS artifact",
    public_social: "Public commentary",
    local: "Local artifact",
  };
  return labels[kind];
}

function freshnessLabel(summary: NewsSignalsSummary | null): string {
  if (!summary) return "Backend freshness unknown";
  return `${summary.freshness_counts.fresh} fresh · ${summary.freshness_counts.stale} stale · ${summary.freshness_counts.unknown} unknown`;
}

function emptyStateLabel(
  summary: NewsSignalsSummary | null,
  filter: SignalFilter,
): string {
  if (!summary) return "Backend read unavailable";
  if (summary.status === "blocked_no_graduated_source") {
    return "No graduated news source";
  }
  if (summary.status === "blocked_source_unavailable") {
    return "Configured sources are blocked or unavailable";
  }
  if (filter !== "for-you") return "No items match this filter";
  return "Ready source lanes have no current artifacts";
}

function safeRefLabel(ref: string): string {
  return ref.split(":").at(-1)?.replaceAll("-", " ") ?? ref;
}
