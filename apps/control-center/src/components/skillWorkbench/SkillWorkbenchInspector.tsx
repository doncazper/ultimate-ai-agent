import type {
  RuntimeSkillMarketplaceCatalogEntry,
  RuntimeSkillMarketplacePostureReadModel,
} from "../../api/types";
import { formatCompactNumber, formatDate } from "./SkillWorkbenchResults";

export function SkillInspector({
  entry,
  posture,
}: {
  entry?: RuntimeSkillMarketplaceCatalogEntry;
  posture: RuntimeSkillMarketplacePostureReadModel;
}) {
  if (!entry) {
    return (
      <aside className="skill-inspector" aria-label="Skill details">
        <h2>No source record selected</h2>
        <p>
          The backend did not return a validated catalog entry. UAA will not
          substitute fabricated marketplace data.
        </p>
      </aside>
    );
  }
  return (
    <aside className="skill-inspector" aria-label="Skill details">
      <h2>{entry.display_name}</h2>
      <section>
        <h3>Why it may fit</h3>
        <p>{entry.safe_summary}</p>
      </section>
      <section>
        <h3>Source signals</h3>
        <InspectorRow label="Source" value={entry.source_label} />
        <InspectorRow label="Rank" value={entry.rank_label} />
        <InspectorRow label="Stars" value={formatOptional(entry.star_count)} />
        <InspectorRow
          label="Average rating"
          value={
            entry.average_rating === null
              ? "Not provided"
              : entry.average_rating.toFixed(1)
          }
        />
        <InspectorRow
          label="Rating count"
          value={formatOptional(entry.rating_count)}
        />
        <InspectorRow
          label="Downloads"
          value={
            entry.download_count === null
              ? "Not provided"
              : formatCompactNumber(entry.download_count)
          }
        />
        <InspectorRow
          label="Comments"
          value={formatOptional(entry.comment_count)}
        />
        <InspectorRow
          label="Updated"
          value={formatDate(entry.source_updated_at)}
        />
        <InspectorRow label="License" value={entry.license_label} />
      </section>
      <section>
        <h3>Permissions & review</h3>
        <InspectorRow label="External code" value="Not imported" />
        <InspectorRow label="Data access" value="Not assessed" />
        <InspectorRow label="Permissions" value="Review required" />
        <InspectorRow label="Risk" value="Not assessed" />
      </section>
      <section>
        <h3>UAA posture</h3>
        <InspectorRow label="Adaptation" value="Not started" />
        <InspectorRow label="Safeguards" value="External code blocked" />
        <InspectorRow label="Review" value="Required before adaptation" />
        <p className="skill-posture-summary">{posture.safe_summary}</p>
      </section>
      <div className="skill-inspector-actions">
        <button
          disabled
          title="Saved ideas require a backend-owned persistence lane"
          type="button"
        >
          Save idea
        </button>
        <a href="/runtime">Review adoption path</a>
        <button
          disabled
          title="Adaptation proposal writes are not authorized in this lane"
          type="button"
        >
          Adapt for UAA
        </button>
      </div>
    </aside>
  );
}

function InspectorRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="skill-inspector-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatOptional(value: number | null): string {
  return value === null ? "Not provided" : value.toLocaleString();
}
