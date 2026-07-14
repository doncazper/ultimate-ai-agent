import { useMemo, useState } from "react";
import type {
  RuntimeSkillMarketplaceCatalogEntry,
  RuntimeSkillMarketplacePostureReadModel,
} from "../../api/types";
import { NorthStarIcon } from "../NorthStarIcon";
import {
  SkillWorkbenchResults,
  type SkillWorkbenchViewMode,
  formatDate,
} from "./SkillWorkbenchResults";
import {
  StudioComposer,
  StudioRail,
  StudioStatusBand,
  WorkbenchHeader,
} from "./SkillWorkbenchChrome";
import { SkillInspector } from "./SkillWorkbenchInspector";
import { Pagination } from "./SkillWorkbenchPagination";
import "./skillWorkbench.css";

type SortMode = "relevance" | "trending" | "stars" | "newest";

interface SkillWorkbenchProps {
  authoritative: boolean;
  posture: RuntimeSkillMarketplacePostureReadModel;
}

const WORKBENCH_TABS = [
  "Discover",
  "For You",
  "Categories",
  "Saved",
  "Adaptations",
  "Local Skills",
] as const;
const EMPTY_SKILL_ENTRIES: RuntimeSkillMarketplaceCatalogEntry[] = [];

export function SkillWorkbench({
  authoritative,
  posture,
}: SkillWorkbenchProps) {
  const catalog = authoritative ? posture.catalog : undefined;
  const entries = catalog?.entries ?? EMPTY_SKILL_ENTRIES;
  const [viewMode, setViewMode] =
    useState<SkillWorkbenchViewMode>("list");
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("all");
  const [category, setCategory] = useState("all");
  const [freshness, setFreshness] = useState("any");
  const [sortMode, setSortMode] = useState<SortMode>("relevance");
  const [pageSize, setPageSize] = useState(25);
  const [page, setPage] = useState(1);
  const [selectedSkillRef, setSelectedSkillRef] = useState<string>();

  const categories = useMemo(
    () => [...new Set(entries.map((entry) => entry.category))].sort(),
    [entries],
  );
  const visibleEntries = useMemo(
    () =>
      filterAndSortEntries(entries, {
        category,
        freshness,
        query,
        snapshotAt: catalog?.captured_at,
        sortMode,
        source,
      }),
    [
      catalog?.captured_at,
      category,
      entries,
      freshness,
      query,
      sortMode,
      source,
    ],
  );
  const pageCount = Math.max(1, Math.ceil(visibleEntries.length / pageSize));
  const currentPage = Math.min(page, pageCount);
  const pageStart = (currentPage - 1) * pageSize;
  const pageEntries = visibleEntries.slice(pageStart, pageStart + pageSize);
  const selectedEntry =
    pageEntries.find((entry) => entry.skill_ref === selectedSkillRef) ??
    pageEntries[0];
  const hasActiveFilters =
    query !== "" ||
    source !== "all" ||
    category !== "all" ||
    freshness !== "any";

  const resetPage = () => setPage(1);
  const clearFilters = () => {
    setQuery("");
    setSource("all");
    setCategory("all");
    setFreshness("any");
    setPage(1);
  };

  return (
    <div className="studio-skill-shell">
      <StudioRail />
      <section className="skill-workspace">
        <WorkbenchHeader authoritative={authoritative} />
        <nav className="skill-tabs" aria-label="Skill Workbench sections">
          {WORKBENCH_TABS.map((tab) =>
            tab === "Discover" ? (
              <button
                aria-current="page"
                className="active"
                key={tab}
                type="button"
              >
                {tab}
              </button>
            ) : (
              <button
                disabled
                key={tab}
                title={`${tab} requires a later backend-owned lane`}
                type="button"
              >
                {tab}
              </button>
            ),
          )}
        </nav>
        <div className="skill-center-layout">
          <main className="skill-browser">
            <div className="skill-search-row">
              <NorthStarIcon name="search" size="lg" tone="muted" />
              <input
                aria-label="Search skill ideas"
                onChange={(event) => {
                  setQuery(event.target.value);
                  resetPage();
                }}
                placeholder="Search source-derived skill metadata..."
                type="search"
                value={query}
              />
            </div>
            <div className="skill-filter-row" aria-label="Skill filters">
              <label>
                <span className="sr-only">Source</span>
                <select
                  aria-label="Source"
                  onChange={(event) => {
                    setSource(event.target.value);
                    resetPage();
                  }}
                  value={source}
                >
                  <option value="all">Source: All</option>
                  <option value="clawhub">Source: ClawHub</option>
                  <option value="hermes">Source: Hermes</option>
                </select>
              </label>
              <label>
                <span className="sr-only">Category</span>
                <select
                  aria-label="Category"
                  onChange={(event) => {
                    setCategory(event.target.value);
                    resetPage();
                  }}
                  value={category}
                >
                  <option value="all">Category: All</option>
                  {categories.map((option) => (
                    <option key={option} value={option}>
                      Category: {option}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span className="sr-only">Freshness</span>
                <select
                  aria-label="Freshness"
                  onChange={(event) => {
                    setFreshness(event.target.value);
                    resetPage();
                  }}
                  value={freshness}
                >
                  <option value="any">Freshness: Any</option>
                  <option value="30">Updated within 30 days</option>
                  <option value="60">Updated within 60 days</option>
                  <option value="90">Updated within 90 days</option>
                </select>
              </label>
              <button
                className="skill-clear-filters"
                disabled={!hasActiveFilters}
                onClick={clearFilters}
                type="button"
              >
                Clear
              </button>
            </div>
            <div className="skill-results-toolbar">
              <div>
                <strong>
                  {visibleEntries.length} skill idea
                  {visibleEntries.length === 1 ? "" : "s"}
                </strong>
                <small>
                  {authoritative
                    ? `Sanitized snapshot · ${catalog ? formatDate(catalog.captured_at) : "unavailable"}`
                    : "Catalog unavailable · no invented fallback rows"}
                </small>
              </div>
              <div className="skill-toolbar-actions">
                <label className="skill-sort-control">
                  <span>Sort by:</span>
                  <select
                    aria-label="Sort skills"
                    onChange={(event) => {
                      setSortMode(event.target.value as SortMode);
                      resetPage();
                    }}
                    value={sortMode}
                  >
                    <option value="relevance">Relevance</option>
                    <option value="trending">Trending rank</option>
                    <option value="stars">Most starred</option>
                    <option value="newest">Newest</option>
                  </select>
                </label>
                <span className="skill-view-toggle" aria-label="Results view">
                  <button
                    aria-label="Grid view"
                    aria-pressed={viewMode === "grid"}
                    onClick={() => setViewMode("grid")}
                    type="button"
                  >
                    <NorthStarIcon name="table-2" size="md" />
                  </button>
                  <button
                    aria-label="List view"
                    aria-pressed={viewMode === "list"}
                    onClick={() => setViewMode("list")}
                    type="button"
                  >
                    <NorthStarIcon name="list-filter" size="md" />
                  </button>
                </span>
              </div>
            </div>
            <div className="skill-results-viewport">
              <SkillWorkbenchResults
                entries={pageEntries}
                onSelect={setSelectedSkillRef}
                selectedSkillRef={selectedEntry?.skill_ref}
                viewMode={viewMode}
              />
            </div>
            <Pagination
              currentPage={currentPage}
              pageCount={pageCount}
              pageSize={pageSize}
              pageStart={pageStart}
              setPage={setPage}
              setPageSize={(size) => {
                setPageSize(size);
                setPage(1);
              }}
              total={visibleEntries.length}
            />
            <StudioComposer />
          </main>
          <SkillInspector entry={selectedEntry} posture={posture} />
        </div>
      </section>
      <StudioStatusBand authoritative={authoritative} />
    </div>
  );
}

function filterAndSortEntries(
  entries: RuntimeSkillMarketplaceCatalogEntry[],
  options: {
    category: string;
    freshness: string;
    query: string;
    snapshotAt?: string;
    sortMode: SortMode;
    source: string;
  },
): RuntimeSkillMarketplaceCatalogEntry[] {
  const normalizedQuery = options.query.trim().toLowerCase();
  const snapshotTime = options.snapshotAt
    ? new Date(options.snapshotAt).getTime()
    : Number.NaN;
  const freshnessDays = Number(options.freshness);
  const filtered = entries.filter((entry) => {
    const matchesQuery =
      normalizedQuery === "" ||
      [entry.display_name, entry.safe_summary, entry.category, entry.source_label]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery);
    const matchesSource =
      options.source === "all" || entry.source_kind === options.source;
    const matchesCategory =
      options.category === "all" || entry.category === options.category;
    const updatedTime = new Date(entry.source_updated_at).getTime();
    const ageMs = snapshotTime - updatedTime;
    const matchesFreshness =
      options.freshness === "any" ||
      (!Number.isNaN(snapshotTime) &&
        !Number.isNaN(updatedTime) &&
        ageMs >= 0 &&
        ageMs <= freshnessDays * 86_400_000);
    return matchesQuery && matchesSource && matchesCategory && matchesFreshness;
  });
  return [...filtered].sort((left, right) => {
    if (options.sortMode === "trending") {
      return (left.source_rank ?? Number.MAX_SAFE_INTEGER) -
        (right.source_rank ?? Number.MAX_SAFE_INTEGER);
    }
    if (options.sortMode === "stars") {
      return (right.star_count ?? -1) - (left.star_count ?? -1);
    }
    if (options.sortMode === "newest") {
      return (
        new Date(right.source_updated_at).getTime() -
        new Date(left.source_updated_at).getTime()
      );
    }
    return entries.indexOf(left) - entries.indexOf(right);
  });
}
