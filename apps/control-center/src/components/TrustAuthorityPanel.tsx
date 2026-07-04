import type {
  TrustAuthorityLane,
  TrustAuthorityMatrix,
  TrustAuthorityState,
} from "../api/types";

interface TrustAuthorityPanelProps {
  matrix: TrustAuthorityMatrix;
  authoritative: boolean;
}

export function TrustAuthorityPanel({
  authoritative,
  matrix,
}: TrustAuthorityPanelProps) {
  const laneRows = authoritative ? matrix.lanes : [];
  const availableRows = laneRows.filter(
    (lane) => lane.authority_state === "available_now",
  );
  const approvalRows = laneRows.filter(
    (lane) => lane.authority_state === "approval_required",
  );
  const plannedRows = laneRows.filter((lane) => lane.authority_state === "planned");
  const blockedRows = laneRows.filter((lane) => lane.authority_state === "blocked");
  const fallbackLaneRefs = matrix.lanes.map((lane) => lane.lane_ref);
  return (
    <section className="page-section" aria-labelledby="trust-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Authority by tier</p>
          <h2 id="trust-heading">Trust</h2>
        </div>
        <span className="status-pill compact">
          {authoritative ? matrix.status : "mock fallback"}
        </span>
      </div>

      <div className="hero-panel">
        <div>
          <p className="eyebrow">
            {authoritative ? "Repo-safe authority map" : "Fallback posture only"}
          </p>
          <h3>
            {authoritative
              ? matrix.doctrine
              : "Reconnect to the local backend before relying on Trust"}
          </h3>
          <p className="muted">
            {authoritative
              ? matrix.operator_summary
              : "Mock fallback data is non-authoritative; no lane is available until Python Core returns the backend-owned Trust matrix."}
          </p>
        </div>
        <div className="detail-grid compact">
          <DetailTerm label="Route" value={matrix.route_ref} />
          <DetailTerm label="CLI" value={matrix.cli_ref} />
          <DetailTerm
            label="Control Center grants authority"
            value={matrix.control_center_grants_authority ? "yes" : "no"}
          />
          <DetailTerm
            label="Production authority"
            value={matrix.production_authority_enabled ? "enabled" : "blocked"}
          />
        </div>
      </div>

      <div className="metric-grid">
        <MetricCard
          label="Available now"
          tone="green"
          value={authoritative ? String(matrix.available_now_lane_refs.length) : "0"}
        />
        <MetricCard
          label="Needs approval"
          tone="orange"
          value={
            authoritative ? String(matrix.approval_required_lane_refs.length) : "0"
          }
        />
        <MetricCard
          label="Planned"
          tone="blue"
          value={authoritative ? String(matrix.planned_lane_refs.length) : "0"}
        />
        <MetricCard
          label="Blocked"
          tone="blue"
          value={
            authoritative
              ? String(matrix.blocked_lane_refs.length)
              : String(fallbackLaneRefs.length)
          }
        />
      </div>

      <div className="stacked-list" aria-label="Usable authority tiers">
        {(authoritative ? matrix.tier_summaries : []).map((tier) => (
          <article className="list-card" key={tier.tier_id}>
            <div className="list-card-header">
              <div>
                <strong>
                  Tier {tier.tier}: {tier.label}
                </strong>
                <p>{tier.operator_summary}</p>
              </div>
              <span className="status-pill compact">
                {tier.available_now_count} now
              </span>
            </div>
          </article>
        ))}
      </div>

      <div className="two-column-grid">
        <LaneColumn
          lanes={availableRows}
          title={authoritative ? "Available Now" : "Fallback Lanes Hidden"}
          tone="available"
        />
        <LaneColumn
          lanes={approvalRows}
          title="Requires Approval"
          tone="approval"
        />
      </div>
      <div className="two-column-grid">
        <LaneColumn lanes={plannedRows} title="Planned" tone="planned" />
        <LaneColumn lanes={blockedRows} title="Blocked" tone="blocked" />
      </div>
      {!authoritative ? (
        <div className="panel-card">
          <h3>Mock Fallback Lane Refs</h3>
          <p className="muted">
            These refs show fallback shape only. Python Core must return the
            Trust read model before any lane can be treated as enabled,
            approval-ready, planned, or blocked product truth.
          </p>
          <RefList refs={fallbackLaneRefs} />
        </div>
      ) : null}

      <div className="two-column-grid">
        <div className="panel-card">
          <h3>Proof And Verifiers</h3>
          <RefList
            refs={authoritative ? [...matrix.proof_refs, ...matrix.verifier_refs] : []}
          />
        </div>
        <div className="panel-card">
          <h3>Blocked Authority</h3>
          <RefList refs={authoritative ? matrix.blocked_authority_refs : []} />
        </div>
      </div>
      <p className="muted">
        {authoritative
          ? matrix.next_safe_action
          : "Reconnect to the local backend before using Trust to choose a next safe action."}
      </p>
    </section>
  );
}

function LaneColumn({
  lanes,
  title,
  tone,
}: {
  lanes: TrustAuthorityLane[];
  title: string;
  tone: "available" | "approval" | "planned" | "blocked";
}) {
  return (
    <div className="panel-card">
      <h3>{title}</h3>
      <div className="stacked-list compact">
        {lanes.map((lane) => (
          <article className="list-card compact" key={lane.lane_ref}>
            <div className="list-card-header">
              <div>
                <strong>{lane.label}</strong>
                <p>{lane.current_posture}</p>
              </div>
              <span className="status-pill compact">
                {lane.authority_state_label || stateLabel(lane.authority_state)}
              </span>
            </div>
            <div className="detail-grid compact">
              <DetailTerm label="Tier" value={`${lane.tier}: ${lane.tier_label}`} />
              <DetailTerm label="Kind" value={formatTrustLabel(lane.lane_kind)} />
              <DetailTerm
                label="Posture"
                value={formatTrustLabel(lane.operator_posture)}
              />
              <DetailTerm
                label="Approval"
                value={lane.requires_exact_approval ? "exact required" : "not required"}
              />
              <DetailTerm
                label="Safe disable"
                value={lane.requires_safe_disable ? "required" : "not required"}
              />
              <DetailTerm
                label="Rollback"
                value={
                  lane.requires_rollback_posture
                    ? "posture required"
                    : lane.rollback_execution_enabled
                      ? "execution enabled"
                      : "execution blocked"
                }
              />
            </div>
            <p className="muted">{lane.operator_can_do_now}</p>
            <p className="muted">{lane.approval_posture}</p>
            <p className="muted">{lane.next_safe_action}</p>
            <RefGroup title="Routes and proof" refs={[...lane.route_refs, ...lane.proof_refs]} />
            <RefGroup
              title="CLI and verifiers"
              refs={[...lane.cli_inspection_refs, ...lane.verifier_refs]}
            />
            <RefGroup
              title="Safe-disable and rollback"
              refs={[...lane.safe_disable_refs, ...lane.rollback_refs]}
            />
            <RefGroup title="Promotion path" refs={lane.promotion_path_refs} />
            {(tone === "blocked" || lane.blocked_authority_refs.length > 0) ? (
              <RefGroup title="Blocked authority" refs={lane.blocked_authority_refs} />
            ) : null}
          </article>
        ))}
        {lanes.length === 0 ? <p className="muted">none</p> : null}
      </div>
    </div>
  );
}

function stateLabel(state: TrustAuthorityState): string {
  return state.replaceAll("_", " ");
}

function formatTrustLabel(value: string): string {
  return value.replaceAll("_", " ");
}

function DetailTerm({ label, value }: { label: string; value: string }) {
  return (
    <div className="detail-term">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function MetricCard({
  label,
  tone,
  value,
}: {
  label: string;
  tone: "blue" | "green" | "orange";
  value: string;
}) {
  return (
    <div className={`metric-card ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RefList({ refs }: { refs: string[] }) {
  if (refs.length === 0) {
    return <p className="muted">none</p>;
  }
  return (
    <ul className="ref-list compact">
      {refs.slice(0, 10).map((ref, index) => (
        <li key={`${ref}-${index}`}>{ref}</li>
      ))}
    </ul>
  );
}

function RefGroup({ refs, title }: { refs: string[]; title: string }) {
  return (
    <div className="compact-stack">
      <p className="muted">{title}</p>
      <RefList refs={refs} />
    </div>
  );
}
