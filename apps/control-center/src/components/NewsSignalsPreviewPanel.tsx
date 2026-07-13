import { useMemo, useState } from "react";
import { NorthStarIcon, type IconReference } from "./NorthStarIcon";

type SignalSourceKind = "official" | "community" | "discord" | "rss" | "social";
type SignalFilter = "for-you" | "brief" | "official" | "community";

type NewsSignalPreviewItem = {
  id: string;
  title: string;
  summary: string;
  quickTake: string;
  whyItMatters: string;
  sourceLabel: string;
  sourceKind: SignalSourceKind;
  freshness: string;
  relevance: string;
  topic: string;
  coverage: string[];
  whyShown: string[];
  briefCandidate: boolean;
  briefLabel: string;
  safeRef: string;
};

const SIGNAL_ITEMS: NewsSignalPreviewItem[] = [
  {
    id: "agent-control-release",
    title: "Agent platform update tightens tool-call controls",
    summary:
      "An official release note and two developer discussions point to safer approval boundaries becoming a baseline expectation.",
    quickTake:
      "The useful signal is not the feature list; it is the convergence around explicit tool scope, inspectable approvals, and safer defaults.",
    whyItMatters:
      "This overlaps directly with UAA's governed action model and may change how founders evaluate agent platforms this quarter.",
    sourceLabel: "Official product update",
    sourceKind: "official",
    freshness: "12m",
    relevance: "Very high",
    topic: "AI & agents",
    coverage: ["Official blog", "Developer forum", "Reddit"],
    whyShown: [
      "Matches your AI agent infrastructure watchlist",
      "Primary source is included",
      "Corroborated across three source types",
    ],
    briefCandidate: true,
    briefLabel: "Morning brief candidate",
    safeRef: "signal-ref:preview:agent-control-release",
  },
  {
    id: "discord-announcement",
    title: "Founder community announces a local-first workflow track",
    summary:
      "A followed Discord announcement introduces a focused discussion series on private, locally operated founder tooling.",
    quickTake:
      "The announcement is useful as a demand signal: local-first workflows are becoming a community topic rather than a niche implementation detail.",
    whyItMatters:
      "It may create a timely venue for positioning UAA, gathering language, and learning which founder workflows resonate most.",
    sourceLabel: "Followed Discord channel",
    sourceKind: "discord",
    freshness: "28m",
    relevance: "High",
    topic: "Founder systems",
    coverage: ["Discord announcement", "Event page"],
    whyShown: [
      "Channel is on your explicit follow list",
      "Matches local-first and founder-operator interests",
      "Announcement is new since your last review",
    ],
    briefCandidate: true,
    briefLabel: "Morning brief candidate",
    safeRef: "signal-ref:preview:discord-local-first-track",
  },
  {
    id: "reddit-migration-pattern",
    title: "Developers surface a repeated migration failure pattern",
    summary:
      "A high-signal Reddit thread groups several reports of configuration drift after an otherwise routine agent framework upgrade.",
    quickTake:
      "This is an early community signal, not verified product truth. The repeated failure shape is worth watching for release and migration design.",
    whyItMatters:
      "UAA's setup and upgrade experience should make configuration ownership and rollback posture more legible than the pattern described here.",
    sourceLabel: "Curated developer community",
    sourceKind: "community",
    freshness: "1h",
    relevance: "High",
    topic: "Developer experience",
    coverage: ["Reddit", "Issue tracker", "Community reply"],
    whyShown: [
      "Discussion crossed your minimum quality threshold",
      "Matches setup and migration interests",
      "Marked as community evidence, not a primary source",
    ],
    briefCandidate: true,
    briefLabel: "Morning brief candidate",
    safeRef: "signal-ref:preview:reddit-migration-pattern",
  },
  {
    id: "market-brief",
    title: "Enterprise buyers emphasize auditability in agent pilots",
    summary:
      "A small cluster of industry articles frames audit trails and operator control as purchasing criteria for new agent deployments.",
    quickTake:
      "The coverage is directional rather than conclusive, but its vocabulary closely matches UAA's proof and evidence posture.",
    whyItMatters:
      "This may help sharpen product language around governance as an operator benefit instead of presenting it only as a safety constraint.",
    sourceLabel: "Industry RSS cluster",
    sourceKind: "rss",
    freshness: "3h",
    relevance: "Medium",
    topic: "Market watch",
    coverage: ["Industry journal", "Analyst blog", "Company newsroom"],
    whyShown: [
      "Matches your company and market watchlist",
      "Three independent articles share the same theme",
      "Lower urgency; retained for trend context",
    ],
    briefCandidate: false,
    briefLabel: "Watch",
    safeRef: "signal-ref:preview:enterprise-auditability",
  },
  {
    id: "social-commentary",
    title: "Operator discussion shifts from autonomy to dependable handoffs",
    summary:
      "Several monitored social posts focus less on fully autonomous agents and more on reviewable delegation, continuity, and recovery.",
    quickTake:
      "The conversation is noisy, but the wording shift is notable and aligns with UAA's human-governed product direction.",
    whyItMatters:
      "This can influence messaging and the examples used to explain UAA's operator loop without treating social commentary as authority.",
    sourceLabel: "Monitored public accounts",
    sourceKind: "social",
    freshness: "5h",
    relevance: "Medium",
    topic: "Product language",
    coverage: ["Public post", "Quoted discussion"],
    whyShown: [
      "Accounts are on your explicit watchlist",
      "Matches product language interests",
      "Shown as commentary with limited confidence",
    ],
    briefCandidate: false,
    briefLabel: "Background",
    safeRef: "signal-ref:preview:dependable-handoffs",
  },
];

const FILTERS: Array<{ id: SignalFilter; label: string }> = [
  { id: "for-you", label: "For you" },
  { id: "brief", label: "Brief candidates" },
  { id: "official", label: "Official sources" },
  { id: "community", label: "Community" },
];

const SOURCE_ICONS: Record<SignalSourceKind, IconReference> = {
  official: "badge-check",
  community: "message-circle",
  discord: "message-square",
  rss: "rss",
  social: "signal",
};

export function NewsSignalsPreviewPanel() {
  const [activeFilter, setActiveFilter] = useState<SignalFilter>("for-you");
  const [selectedId, setSelectedId] = useState(SIGNAL_ITEMS[0].id);

  const visibleItems = useMemo(
    () =>
      SIGNAL_ITEMS.filter((item) => {
        if (activeFilter === "brief") return item.briefCandidate;
        if (activeFilter === "official") return item.sourceKind === "official";
        if (activeFilter === "community") {
          return item.sourceKind === "community" || item.sourceKind === "discord";
        }
        return true;
      }),
    [activeFilter],
  );
  const selectedItem =
    visibleItems.find((item) => item.id === selectedId) ?? visibleItems[0];
  const briefCandidateCount = SIGNAL_ITEMS.filter(
    (item) => item.briefCandidate,
  ).length;

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
              <span className="news-preview-badge">Illustrative preview</span>
            </div>
            <h1 id="news-signals-heading">News &amp; Signals</h1>
            <p>
              A calm stream of sourced context, ranked for you and distilled into
              the best items for Morning Briefing.
            </p>
          </div>
        </div>
        <div className="news-signals-metrics" aria-label="Preview stream summary">
          <PreviewMetric label="Signals" value={String(SIGNAL_ITEMS.length)} />
          <PreviewMetric label="Source types" value="5" />
          <PreviewMetric label="Brief picks" value={String(briefCandidateCount)} />
        </div>
      </header>

      <div className="news-preview-notice" role="status">
        <NorthStarIcon name="shield-check" />
        <span>
          Sample records only. No live fetching, account access, background polling,
          model summarization, or external action is enabled.
        </span>
        <a href="/briefing">Open Morning Briefing</a>
      </div>

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
          <span className="news-freshness-dot" /> Preview refreshed with sample data
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
          <div className="news-story-list">
            {visibleItems.map((item) => (
              <button
                aria-label={`Inspect signal: ${item.title}`}
                aria-pressed={selectedItem?.id === item.id}
                className={`news-story-row source-${item.sourceKind}`}
                key={item.id}
                onClick={() => setSelectedId(item.id)}
                type="button"
              >
                <span className="news-story-source-icon" aria-hidden="true">
                  <NorthStarIcon name={SOURCE_ICONS[item.sourceKind]} />
                </span>
                <span className="news-story-copy">
                  <span className="news-story-meta">
                    <strong>{item.sourceLabel}</strong>
                    <span>{item.freshness}</span>
                    <span>{item.coverage.length} sources</span>
                  </span>
                  <strong className="news-story-title">{item.title}</strong>
                  <span className="news-story-summary">{item.summary}</span>
                  <span className="news-story-footer">
                    <span>{item.topic}</span>
                    <span>{item.relevance} relevance</span>
                    <span className={item.briefCandidate ? "brief-ready" : "watch"}>
                      {item.briefLabel}
                    </span>
                  </span>
                </span>
                <NorthStarIcon className="news-story-chevron" name="chevron-right" />
              </button>
            ))}
          </div>
        </div>

        {selectedItem ? <SignalInspector item={selectedItem} /> : null}
      </div>
    </section>
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

function SignalInspector({ item }: { item: NewsSignalPreviewItem }) {
  return (
    <aside className="news-signal-inspector" aria-label="Signal detail">
      <div className="news-inspector-heading">
        <div>
          <p className="eyebrow">Selected signal</p>
          <span className={item.briefCandidate ? "brief-ready" : "watch"}>
            {item.briefLabel}
          </span>
        </div>
        <span className="news-source-kind">{sourceKindLabel(item.sourceKind)}</span>
      </div>
      <h2>{item.title}</h2>
      <p className="news-inspector-summary">{item.summary}</p>

      <section className="news-inspector-section">
        <h3>Quick take</h3>
        <p>{item.quickTake}</p>
      </section>
      <section className="news-inspector-section emphasized">
        <h3>Why it matters</h3>
        <p>{item.whyItMatters}</p>
      </section>
      <section className="news-inspector-section">
        <h3>Why this was selected</h3>
        <ul>
          {item.whyShown.map((reason) => (
            <li key={reason}>
              <NorthStarIcon name="circle-check" />
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      </section>
      <section className="news-inspector-section">
        <h3>Coverage</h3>
        <div className="news-coverage-list">
          {item.coverage.map((source) => (
            <span key={source}>{source}</span>
          ))}
        </div>
      </section>
      <dl className="news-signal-provenance">
        <div>
          <dt>Freshness</dt>
          <dd>{item.freshness}</dd>
        </div>
        <div>
          <dt>Safe ref</dt>
          <dd>{item.safeRef}</dd>
        </div>
      </dl>
      <div className="news-deferred-controls">
        <strong>Review controls are intentionally deferred</strong>
        <span>
          Save, dismiss, mute, and action-proposal controls require backend-owned
          contracts and receipt behavior before they appear here.
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

function sourceKindLabel(kind: SignalSourceKind): string {
  const labels: Record<SignalSourceKind, string> = {
    official: "Primary source",
    community: "Community",
    discord: "Discord",
    rss: "RSS cluster",
    social: "Public commentary",
  };
  return labels[kind];
}
