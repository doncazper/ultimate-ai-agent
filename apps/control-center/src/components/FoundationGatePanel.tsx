import type { GateSummary } from "../api/types";

export function FoundationGatePanel({ summary }: { summary: GateSummary }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Foundation Gate</h2>
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
