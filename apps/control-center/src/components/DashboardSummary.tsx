import type { ControlCenterDashboardSnapshot } from "../api/types";
import { EmptyState } from "./DataState";
import { StatusCard } from "./StatusCard";

export function DashboardSummary({ dashboard }: { dashboard: ControlCenterDashboardSnapshot }) {
  return (
    <section className="page-section" aria-labelledby="dashboard-overview-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Local shell</p>
          <h2 id="dashboard-overview-heading">Dashboard overview</h2>
        </div>
        <span className="status-pill compact">{dashboard.baseline_version}</span>
      </div>
      <p className="section-copy">
        Read-only summaries for release readiness, runtime boundaries, API inventory, approvals, remote worker planning,
        mobile planning, and plugin governance.
      </p>
      <div className="panel-grid">
        <StatusCard
          label={dashboard.system_status.label}
          status={dashboard.system_status.status}
          summary={dashboard.system_status.summary}
        />
        <StatusCard
          label="Foundation Gate"
          status={dashboard.foundation_gate_summary.status}
          summary={dashboard.foundation_gate_summary.summary}
        />
        <StatusCard
          label="Runtime readiness"
          status={dashboard.runtime_readiness_summary.status}
          summary="Readiness report only; no production runtime authority is claimed."
        />
        <StatusCard
          label="API boundary"
          status={`${dashboard.api_summary.route_count} routes`}
          summary={
            dashboard.api_summary.execution_routes_present
              ? "Unsafe route inventory needs review."
              : "Route summary reports no execution routes."
          }
        />
      </div>
      {dashboard.warnings.length > 0 ? (
        <div className="note-list" aria-label="Dashboard warnings">
          {dashboard.warnings.map((warning) => (
            <span key={warning}>{warning}</span>
          ))}
        </div>
      ) : (
        <EmptyState title="No dashboard warnings" message="No warning summaries were returned by the local contract." />
      )}
    </section>
  );
}
