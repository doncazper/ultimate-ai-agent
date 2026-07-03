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
  const availableRows = matrix.lanes.filter(
    (lane) => lane.authority_state === "available_now",
  );
  const approvalRows = matrix.lanes.filter(
    (lane) => lane.authority_state === "approval_required",
  );
  const blockedRows = matrix.lanes.filter(
    (lane) =>
      lane.authority_state === "blocked" || lane.authority_state === "planned",
  );
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
          <p className="eyebrow">What UAA can do now</p>
          <h3>{matrix.doctrine}</h3>
          <p className="muted">{matrix.operator_summary}</p>
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
          value={String(matrix.available_now_lane_refs.length)}
        />
        <MetricCard
          label="Needs approval"
          tone="orange"
          value={String(matrix.approval_required_lane_refs.length)}
        />
        <MetricCard
          label="Planned"
          tone="blue"
          value={String(matrix.planned_lane_refs.length)}
        />
        <MetricCard
          label="Blocked"
          tone="blue"
          value={String(matrix.blocked_lane_refs.length)}
        />
      </div>

      <div className="stacked-list" aria-label="Usable authority tiers">
        {matrix.tier_summaries.map((tier) => (
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
          title="Available Now"
          tone="available"
        />
        <LaneColumn
          lanes={approvalRows}
          title="Requires Approval"
          tone="approval"
        />
      </div>
      <LaneColumn lanes={blockedRows} title="Still Planned Or Blocked" tone="blocked" />

      <div className="two-column-grid">
        <div className="panel-card">
          <h3>Proof And Verifiers</h3>
          <RefList refs={[...matrix.proof_refs, ...matrix.verifier_refs]} />
        </div>
        <div className="panel-card">
          <h3>Blocked Authority</h3>
          <RefList refs={matrix.blocked_authority_refs} />
        </div>
      </div>
      <p className="muted">{matrix.next_safe_action}</p>
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
  tone: "available" | "approval" | "blocked";
}) {
  return (
    <div className="panel-card">
      <h3>{title}</h3>
      <div className="stacked-list compact">
        {lanes.slice(0, 8).map((lane) => (
          <article className="list-card compact" key={lane.lane_ref}>
            <div className="list-card-header">
              <div>
                <strong>{lane.label}</strong>
                <p>{lane.operator_can_do_now}</p>
              </div>
              <span className="status-pill compact">
                {stateLabel(lane.authority_state)}
              </span>
            </div>
            <div className="detail-grid compact">
              <DetailTerm label="Tier" value={`${lane.tier}: ${lane.tier_label}`} />
              <DetailTerm label="Kind" value={lane.lane_kind} />
              <DetailTerm
                label="Approval"
                value={lane.requires_exact_approval ? "exact required" : "not required"}
              />
              <DetailTerm label="Next" value={lane.next_safe_action} />
            </div>
            {tone === "blocked" ? (
              <RefList refs={lane.blocked_authority_refs} />
            ) : (
              <RefList refs={[...lane.route_refs, ...lane.proof_refs]} />
            )}
          </article>
        ))}
      </div>
    </div>
  );
}

function stateLabel(state: TrustAuthorityState): string {
  return state.replaceAll("_", " ");
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
