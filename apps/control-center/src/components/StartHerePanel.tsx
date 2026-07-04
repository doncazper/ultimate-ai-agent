import type { ControlCenterStartHereSummary } from "../api/types";

interface StartHerePanelProps {
  startHere: ControlCenterStartHereSummary;
  authoritative: boolean;
}

export function StartHerePanel({
  authoritative,
  startHere,
}: StartHerePanelProps) {
  const visibleSteps = startHere.steps.slice(0, 8);
  return (
    <section className="page-section" aria-labelledby="start-here-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Local governed loop</p>
          <h2 id="start-here-heading">Start Here</h2>
        </div>
        <span className="status-pill compact">
          {authoritative ? startHere.readiness_state : "mock fallback"}
        </span>
      </div>

      <div className="hero-panel">
        <div>
          <p className="eyebrow">Next safe action</p>
          <h3>{startHere.next_safe_action}</h3>
          <p className="muted">{startHere.operator_goal}</p>
        </div>
        <div className="detail-grid compact">
          <DetailTerm label="Loop status" value={startHere.local_loop_status} />
          <DetailTerm label="Action proposal" value={startHere.action_proposal_ref} />
          <DetailTerm label="Run" value={startHere.primary_run_ref} />
          <DetailTerm label="Proof" value={startHere.primary_proof_ref} />
        </div>
      </div>

      <div className="metric-grid start-here-metric-grid">
        <MetricCard
          label="Source"
          value={startHere.source}
          tone={authoritative ? "green" : "orange"}
        />
        <MetricCard
          label="Daily loop"
          value={
            authoritative && startHere.complete_daily_loop_available
              ? "repo-safe available"
              : "partial or blocked"
          }
          tone={
            authoritative && startHere.complete_daily_loop_available
              ? "green"
              : "orange"
          }
        />
        <MetricCard
          label="Runtime authority"
          value="not granted"
          tone="blue"
        />
      </div>

      {startHere.missing_prerequisite_refs.length > 0 && (
        <div className="callout-panel warning">
          <strong>Missing prerequisites</strong>
          <RefList refs={startHere.missing_prerequisite_refs} />
        </div>
      )}

      <div className="stacked-list">
        {visibleSteps.map((step) => (
          <article className="list-card" key={step.step_id}>
            <div className="list-card-header">
              <div>
                <strong>{step.label}</strong>
                <p>{step.safe_summary}</p>
              </div>
              <span className="status-pill compact">{step.status}</span>
            </div>
            <div className="detail-grid compact">
              <DetailTerm label="Route" value={step.route_ref} />
              <DetailTerm label="Backend" value={step.backend_route_ref} />
              <DetailTerm label="Proof" value={step.proof_ref} />
              <DetailTerm label="Next" value={step.next_safe_action} />
            </div>
          </article>
        ))}
      </div>

      <div className="two-column-grid">
        <div className="panel-card">
          <h3>Evidence</h3>
          <RefList refs={startHere.evidence_refs} />
        </div>
        <div className="panel-card">
          <h3>Still Blocked</h3>
          <RefList refs={startHere.blocked_authority_refs} />
        </div>
      </div>
    </section>
  );
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
      {refs.slice(0, 10).map((ref) => (
        <li key={ref}>{ref}</li>
      ))}
    </ul>
  );
}
