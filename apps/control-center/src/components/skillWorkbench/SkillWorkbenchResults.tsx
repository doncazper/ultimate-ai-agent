import type { RuntimeSkillMarketplaceCatalogEntry } from "../../api/types";
import { NorthStarIcon } from "../NorthStarIcon";

export type SkillWorkbenchViewMode = "grid" | "list";

interface SkillWorkbenchResultsProps {
  entries: RuntimeSkillMarketplaceCatalogEntry[];
  selectedSkillRef?: string;
  viewMode: SkillWorkbenchViewMode;
  onSelect: (skillRef: string) => void;
}

export function SkillWorkbenchResults({
  entries,
  selectedSkillRef,
  viewMode,
  onSelect,
}: SkillWorkbenchResultsProps) {
  if (entries.length === 0) {
    return (
      <div className="skill-empty-state" role="status">
        <NorthStarIcon name="search" size="xl" tone="muted" />
        <strong>No source-derived skill metadata matches these filters</strong>
        <span>
          Clear a filter or inspect the source snapshot posture. UAA does not
          invent missing marketplace records.
        </span>
      </div>
    );
  }

  if (viewMode === "grid") {
    return (
      <div className="skill-card-grid" aria-label="Skill idea grid">
        {entries.map((entry) => (
          <SkillCard
            entry={entry}
            key={entry.skill_ref}
            onSelect={onSelect}
            selected={entry.skill_ref === selectedSkillRef}
          />
        ))}
      </div>
    );
  }

  return (
    <div className="skill-list" aria-label="Skill idea list">
      <div className="skill-list-header" aria-hidden="true">
        <span>Skill</span>
        <span>Category</span>
        <span>Source</span>
        <span>Rank</span>
        <span>Source signal</span>
        <span>Popularity</span>
        <span>Updated</span>
      </div>
      <div className="skill-list-body">
        {entries.map((entry) => (
          <SkillListRow
            entry={entry}
            key={entry.skill_ref}
            onSelect={onSelect}
            selected={entry.skill_ref === selectedSkillRef}
          />
        ))}
      </div>
    </div>
  );
}

function SkillCard({
  entry,
  selected,
  onSelect,
}: {
  entry: RuntimeSkillMarketplaceCatalogEntry;
  selected: boolean;
  onSelect: (skillRef: string) => void;
}) {
  return (
    <button
      aria-pressed={selected}
      className={`skill-card${selected ? " selected" : ""}`}
      onClick={() => onSelect(entry.skill_ref)}
      type="button"
    >
      <span className="skill-card-main">
        <SkillGlyph entry={entry} />
        <span className="skill-card-copy">
          <strong>{entry.display_name}</strong>
          <span>{entry.safe_summary}</span>
          <small>
            {entry.category} <span aria-hidden="true">·</span>{" "}
            <SourceLabel entry={entry} />
          </small>
        </span>
      </span>
      <span className="skill-card-signals">
        <span>{entry.rank_label}</span>
        <span>{sourceScore(entry)}</span>
        <span>{popularity(entry)}</span>
      </span>
      <span className="skill-card-foot">
        <span>Metadata snapshot</span>
        <span>License: {entry.license_label}</span>
        <span>Updated {formatDate(entry.source_updated_at)}</span>
      </span>
    </button>
  );
}

function SkillListRow({
  entry,
  selected,
  onSelect,
}: {
  entry: RuntimeSkillMarketplaceCatalogEntry;
  selected: boolean;
  onSelect: (skillRef: string) => void;
}) {
  return (
    <button
      aria-pressed={selected}
      className={`skill-list-row${selected ? " selected" : ""}`}
      onClick={() => onSelect(entry.skill_ref)}
      type="button"
    >
      <span className="skill-list-identity">
        <SkillGlyph entry={entry} />
        <span>
          <strong>{entry.display_name}</strong>
          <small>{entry.safe_summary}</small>
        </span>
      </span>
      <span className="skill-list-category">{entry.category}</span>
      <span className="skill-list-source">
        <SourceLabel entry={entry} />
      </span>
      <span className="skill-list-rank">{entry.rank_label}</span>
      <span className="skill-list-score">{sourceScore(entry)}</span>
      <span className="skill-list-popularity">{popularity(entry)}</span>
      <span className="skill-list-updated">
        {formatDate(entry.source_updated_at)}
      </span>
    </button>
  );
}

function SkillGlyph({
  entry,
}: {
  entry: RuntimeSkillMarketplaceCatalogEntry;
}) {
  const icon = entry.source_kind === "clawhub" ? "file-text" : "bookmark";
  return (
    <span className="skill-glyph" aria-hidden="true">
      <NorthStarIcon name={icon} size="lg" />
    </span>
  );
}

function SourceLabel({
  entry,
}: {
  entry: RuntimeSkillMarketplaceCatalogEntry;
}) {
  return (
    <span className={`skill-source-label ${entry.source_kind}`}>
      <span aria-hidden="true" className="skill-source-dot" />
      {entry.source_label}
    </span>
  );
}

export function sourceScore(
  entry: RuntimeSkillMarketplaceCatalogEntry,
): string {
  if (entry.average_rating !== null && entry.rating_count !== null) {
    return `★ ${entry.average_rating.toFixed(1)} · ${entry.rating_count.toLocaleString()} ratings`;
  }
  if (entry.star_count !== null) {
    return `★ ${entry.star_count.toLocaleString()} stars`;
  }
  return "No source rating";
}

export function popularity(
  entry: RuntimeSkillMarketplaceCatalogEntry,
): string {
  if (entry.download_count !== null) {
    return `${formatCompactNumber(entry.download_count)} downloads`;
  }
  return "Official bundled";
}

export function formatCompactNumber(value: number): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 1,
    notation: "compact",
  }).format(value);
}

export function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Unknown";
  }
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}
