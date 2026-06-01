import type { ControlCenterDashboardSnapshot } from "../api/types";
import { StatusCard } from "./StatusCard";

export function DashboardSummary({ dashboard }: { dashboard: ControlCenterDashboardSnapshot }) {
  return (
    <section className="panel-grid">
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
    </section>
  );
}
