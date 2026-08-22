import type { FounderLoopSourceReadiness } from "../api/types";

export function ConnectorReadPlatformCard({
  posture,
}: {
  posture: FounderLoopSourceReadiness["connector_read_platform"];
}) {
  return (
    <article className="review-card" aria-label="ECO-009 connector read platform">
      <div className="review-card-heading">
        <h3>Exact calendar metadata snapshot</h3>
        <span>{posture.status}</span>
      </div>
      <p>{posture.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Adapter" value={posture.adapter_ref} />
        <DetailTerm
          label="Configured snapshots"
          value={String(posture.configured_source_count)}
        />
        <DetailTerm
          label="Input boundary"
          value={
            posture.fixture_or_caller_supplied_snapshot_only
              ? "caller-supplied redacted snapshot only"
              : "unavailable"
          }
        />
        <DetailTerm
          label="Live account"
          value={posture.live_account_connected ? "connected" : "not connected"}
        />
        <DetailTerm
          label="Network access"
          value={posture.network_access_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Account auth"
          value={posture.account_auth_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Background sync"
          value={posture.background_sync_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Safe disable"
          value={posture.safe_disable_active ? "active" : "available"}
        />
        <DetailTerm
          label="Raw content"
          value={posture.raw_content_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Connector writes"
          value={posture.connector_write_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm label="Next safe action" value={posture.next_safe_action} />
      </dl>
      <RefListWithFallback
        emptyLabel="Configured snapshot refs: none"
        refs={posture.source_refs}
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
