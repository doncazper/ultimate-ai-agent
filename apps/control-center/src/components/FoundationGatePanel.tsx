import type { GateSummary } from "../api/types";

export function FoundationGatePanel({ summary }: { summary: GateSummary }) {
  return (
    <section className="panel" aria-labelledby="foundation-gate-heading">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Release safety</p>
          <h2 id="foundation-gate-heading">Foundation Gate</h2>
        </div>
        <span>{summary.status}</span>
      </div>
      <div className="metric-row">
        <div>
          <strong>{summary.passed_count}</strong>
          <span>passed</span>
        </div>
        <div>
          <strong>{summary.failed_count}</strong>
          <span>failed</span>
        </div>
      </div>
      <p>{summary.summary}</p>
    </section>
  );
}
