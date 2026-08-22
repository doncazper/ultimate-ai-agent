import type { FounderLoopSourceReadiness } from "../api/types";

export function ConnectorReadPlatformCard({
  sourceReadiness,
}: {
  sourceReadiness: FounderLoopSourceReadiness;
}) {
  const calendarSource = sourceReadiness.source_readiness_items.find(
    (item) => item.source_kind === "calendar",
  );
  const calendarContract = sourceReadiness.read_only_metadata_contracts.find(
    (contract) => contract.source_kind === "calendar",
  );
  return (
    <article className="review-card" aria-label="ECO-009 connector read platform">
      <div className="review-card-heading">
        <h3>Exact calendar metadata snapshot</h3>
        <span>implemented_inactive_no_snapshot_source</span>
      </div>
      <p>
        {calendarSource?.safe_summary ??
          "Calendar source readiness is unavailable; no live access is claimed."}
      </p>
      <dl className="detail-list">
        <DetailTerm
          label="Adapter"
          value="connector-adapter-ref:eco-009:calendar-metadata-snapshot-v1"
        />
        <DetailTerm
          label="Backend source state"
          value={calendarSource?.status ?? "unavailable"}
        />
        <DetailTerm
          label="Input boundary"
          value={
            "caller-supplied redacted snapshot only"
          }
        />
        <DetailTerm
          label="Live account"
          value={
            calendarContract?.account_auth_enabled ? "connected" : "not connected"
          }
        />
        <DetailTerm
          label="Network access"
          value={calendarContract?.runtime_read_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Account auth"
          value={calendarContract?.account_auth_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Background sync"
          value={
            calendarContract?.background_collection_enabled ? "enabled" : "blocked"
          }
        />
        <DetailTerm label="Safe disable" value="available" />
        <DetailTerm
          label="Raw content"
          value={calendarContract?.raw_content_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Connector writes"
          value={calendarContract?.write_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Next safe action"
          value={calendarSource?.next_safe_action ?? sourceReadiness.next_safe_action}
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Configured snapshot refs: none"
        refs={[
          "contract-ref:eco-009-read-only-connector-platform:v1",
          ...(calendarSource?.source_refs ?? []),
        ]}
      />
    </article>
  );
}

function RefListWithFallback({
  emptyLabel,
  refs,
}: {
  emptyLabel: string;
  refs: string[];
}) {
  if (refs.length === 0) {
    return <p className="muted">{emptyLabel}</p>;
  }
  return (
    <ul className="ref-list">
      {refs.map((ref) => (
        <li key={ref}>{ref}</li>
      ))}
    </ul>
  );
}

function DetailTerm({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
