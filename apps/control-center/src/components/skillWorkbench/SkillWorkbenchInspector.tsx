import type {
  RuntimeSkillMarketplaceCatalogEntry,
  RuntimeSkillMarketplacePostureReadModel,
} from "../../api/types";
import { formatCompactNumber, formatDate } from "./SkillWorkbenchResults";

export function SkillInspector({
  backendValidated,
  entry,
  posture,
}: {
  backendValidated: boolean;
  entry?: RuntimeSkillMarketplaceCatalogEntry;
  posture: RuntimeSkillMarketplacePostureReadModel;
}) {
  return (
    <aside className="skill-inspector" aria-label="Skill details">
      <h2>{entry?.display_name ?? "No source record selected"}</h2>
      <section className="skill-authority-posture">
        <h3>Backend authority & freshness</h3>
        <InspectorRow
          label="Backend"
          value={backendValidated ? "Validated" : "Unavailable"}
        />
        {backendValidated ? (
          <>
            <InspectorRow
              label="Decision"
              value={formatPostureToken(
                posture.authority_state_decision_outcome,
              )}
            />
            <InspectorRow
              label="Authority status"
              value={formatPostureToken(posture.authority_state_status)}
            />
            <InspectorRow
              label="Catalog"
              value={formatPostureToken(
                posture.catalog_freshness.display_status,
              )}
            />
            <InspectorRow
              label="Checked"
              value={formatDate(posture.catalog_freshness.checked_at)}
            />
            <InspectorRow
              label="Expires"
              value={formatDate(posture.catalog_freshness.expires_at)}
            />
            <p className="skill-posture-summary">
              {posture.authority_state_operator_message}
            </p>
            <ReferenceList
              label="Authority reasons"
              refs={posture.authority_state_reason_refs}
            />
            <ReferenceList
              label="Freshness reasons"
              refs={posture.catalog_freshness.reason_refs}
            />
            <ReferenceList
              label="Blocked authority"
              refs={posture.blocked_authority_refs}
            />
            <ReferenceList
              label="Unsupported adapters"
              refs={posture.unsupported_adapter_refs}
            />
            <ReferenceList
              label="Proof and verifier refs"
              refs={[
                posture.snapshot_ref,
                posture.snapshot_hash_ref,
                posture.snapshot_hash_algorithm_ref,
                ...posture.proof_refs,
                ...posture.verifier_refs,
              ]}
            />
          </>
        ) : (
          <p className="skill-posture-summary">
            Backend validation is unavailable. UAA is not displaying an
            authority decision, lease posture, proof ref, or catalog claim.
          </p>
        )}
      </section>
      {entry ? (
        <>
          <section>
            <h3>Why it may fit</h3>
            <p>{entry.safe_summary}</p>
          </section>
          <section>
            <h3>Source signals</h3>
            <InspectorRow label="Source" value={entry.source_label} />
            <InspectorRow label="Rank" value={entry.rank_label} />
            <InspectorRow
              label="Stars"
              value={formatOptional(entry.star_count)}
            />
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
        </>
      ) : (
        <p>
          The backend did not return a displayable catalog entry. UAA will not
          substitute fabricated marketplace data.
        </p>
      )}
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

function ReferenceList({ label, refs }: { label: string; refs: string[] }) {
  return (
    <details className="skill-reference-list">
      <summary>
        {label} ({refs.length})
      </summary>
      <ul>
        {refs.map((ref) => (
          <li key={ref}>
            <code>{ref}</code>
          </li>
        ))}
      </ul>
    </details>
  );
}

function formatPostureToken(value: string): string {
  return value
    .split("_")
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(" ");
}
