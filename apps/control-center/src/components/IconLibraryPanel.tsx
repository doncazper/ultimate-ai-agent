import { useMemo, useState } from "react";
import {
  ICON_CATEGORIES,
  ICON_DEFINITIONS,
  getIconDefinition,
  searchIconDefinitions,
  type IconCategory,
  type IconName,
} from "../icons/iconRegistry";
import {
  ICON_TONES,
  NorthStarIcon,
  NorthStarIconBadge,
  type IconTone,
} from "./NorthStarIcon";

type GalleryTheme = "dark" | "light";
type GalleryTone = Exclude<IconTone, "current">;

const galleryTones = ICON_TONES.filter(
  (tone): tone is GalleryTone => tone !== "current",
);

export function IconLibraryPanel() {
  const [category, setCategory] = useState<IconCategory | "all">("all");
  const [query, setQuery] = useState("");
  const [selectedName, setSelectedName] = useState<IconName>("sparkles");
  const [theme, setTheme] = useState<GalleryTheme>("light");
  const [tone, setTone] = useState<GalleryTone>("accent");
  const definitions = useMemo(
    () => searchIconDefinitions({ category, query }),
    [category, query],
  );
  const selected = getIconDefinition(selectedName);

  return (
    <section
      aria-labelledby="icon-library-title"
      className="icon-library page-section"
      data-icon-theme={theme}
    >
      <div className="section-heading icon-library-heading">
        <div>
          <p className="eyebrow">Design resource</p>
          <h2 id="icon-library-title">Control Center icon library</h2>
          <p className="section-copy">
            {ICON_DEFINITIONS.length} scalable vector icons with typed names,
            semantic color, light and dark previews, accessibility metadata,
            and legacy aliases. This compile-time catalog needs no database and
            grants no runtime authority.
          </p>
        </div>
        <span className="status-pill compact">Vector · 24 px grid · SVG</span>
      </div>

      <div className="icon-library-controls" aria-label="Icon library filters">
        <label className="icon-library-search">
          <span>Find an icon</span>
          <span className="icon-search-field">
            <NorthStarIcon name="search" tone="muted" />
            <input
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search names, aliases, and keywords"
              type="search"
              value={query}
            />
          </span>
        </label>

        <fieldset className="icon-segmented-control">
          <legend>Preview theme</legend>
          <div>
            {(["light", "dark"] as const).map((option) => (
              <button
                aria-pressed={theme === option}
                className={theme === option ? "active" : ""}
                key={option}
                onClick={() => setTheme(option)}
                type="button"
              >
                <NorthStarIcon
                  name={option === "light" ? "sun" : "moon"}
                  size="sm"
                />
                {option === "light" ? "Light" : "Dark"}
              </button>
            ))}
          </div>
        </fieldset>

        <fieldset className="icon-tone-control">
          <legend>Semantic color</legend>
          <div>
            {galleryTones.map((option) => (
              <button
                aria-label={`${option} icon tone`}
                aria-pressed={tone === option}
                className={tone === option ? "active" : ""}
                key={option}
                onClick={() => setTone(option)}
                title={option}
                type="button"
              >
                <span className={`icon-tone-swatch icon-tone-${option}`} />
              </button>
            ))}
          </div>
        </fieldset>
      </div>

      <div className="icon-category-bar" aria-label="Icon categories">
        <button
          aria-pressed={category === "all"}
          className={category === "all" ? "active" : ""}
          onClick={() => setCategory("all")}
          type="button"
        >
          All <span>{ICON_DEFINITIONS.length}</span>
        </button>
        {ICON_CATEGORIES.map((option) => {
          const count = searchIconDefinitions({ category: option }).length;
          return (
            <button
              aria-pressed={category === option}
              className={category === option ? "active" : ""}
              key={option}
              onClick={() => setCategory(option)}
              type="button"
            >
              {humanize(option)} <span>{count}</span>
            </button>
          );
        })}
      </div>

      <div className="icon-library-layout">
        <aside className="icon-detail-card" aria-label="Selected icon details">
          <div className="icon-detail-preview-row">
            <NorthStarIconBadge
              decorative={false}
              icon={selected.name}
              label={`${selected.label} icon`}
              size="2xl"
              tone={tone}
              variant="soft"
            />
            <NorthStarIconBadge
              icon={selected.name}
              size="2xl"
              tone={tone}
              variant="outline"
            />
            <NorthStarIconBadge
              icon={selected.name}
              size="2xl"
              tone={tone}
              variant="solid"
            />
          </div>
          <div>
            <p className="eyebrow">Selected icon</p>
            <h3>{selected.label}</h3>
            <code>{selected.name}</code>
          </div>
          <dl className="icon-detail-metadata">
            <div>
              <dt>Categories</dt>
              <dd>{selected.categories.map(humanize).join(", ")}</dd>
            </div>
            <div>
              <dt>Aliases</dt>
              <dd>
                {selected.aliases.length > 0
                  ? selected.aliases.join(", ")
                  : "None"}
              </dd>
            </div>
            <div>
              <dt>Direction-aware</dt>
              <dd>{selected.directional ? "Mirrors in RTL" : "No mirroring"}</dd>
            </div>
          </dl>
          <code className="icon-usage-code">
            {`<NorthStarIcon name="${selected.name}" tone="${tone}" />`}
          </code>
          <p className="icon-detail-note">
            Use an accessible text label on every icon-only button. Keep the
            icon decorative when adjacent text already names the action.
          </p>
        </aside>

        <div className="icon-catalog-region">
          <div className="icon-catalog-summary" role="status">
            <span>
              Showing <strong>{definitions.length}</strong> icons
            </span>
            {query ? <span>matching “{query}”</span> : null}
          </div>
          {definitions.length > 0 ? (
            <div className="icon-catalog-grid">
              {definitions.map((definition) => (
                <button
                  aria-pressed={selectedName === definition.name}
                  className={
                    selectedName === definition.name ? "selected" : ""
                  }
                  key={definition.name}
                  onClick={() => setSelectedName(definition.name)}
                  type="button"
                >
                  <NorthStarIcon
                    name={definition.name}
                    size="xl"
                    tone={tone}
                  />
                  <span>{definition.label}</span>
                  <code>{definition.name}</code>
                </button>
              ))}
            </div>
          ) : (
            <div className="icon-library-empty" role="status">
              <NorthStarIcon name="search" size="2xl" tone="muted" />
              <strong>No icons match this filter</strong>
              <span>Try another name, alias, or category.</span>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function humanize(value: string): string {
  return value
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
