import { useEffect, useMemo, useState } from "react";
import { loadNewsSignalsSummary } from "../api/client";
import type {
  NewsSignalReadItem,
  NewsSignalSourceKind,
  NewsSignalsSummary,
} from "../api/types";
import { NorthStarIcon, type IconReference } from "./NorthStarIcon";

type SignalFilter = "for-you" | "brief" | "official" | "community";

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

export function NewsSignalsPreviewPanel() {
  const [summary, setSummary] = useState<NewsSignalsSummary | null>(null);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "failed">(
    "loading",
  );
  const [activeFilter, setActiveFilter] = useState<SignalFilter>("for-you");
  const [selectedRef, setSelectedRef] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    loadNewsSignalsSummary()
      .then((value) => {
        if (!active) return;
        setSummary(value);
        setSelectedRef(value.items[0]?.signal_ref ?? null);
        setLoadState("ready");
      })
      .catch(() => {
        if (!active) return;
        setSummary(null);
        setLoadState("failed");
      });
    return () => {
      active = false;
    };
  }, []);

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
          <SignalInspector item={selectedItem} />
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

function SignalInspector({ item }: { item: NewsSignalReadItem }) {
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
          This read model cannot save, dismiss, recommend, execute, or mint source
          authority.
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
