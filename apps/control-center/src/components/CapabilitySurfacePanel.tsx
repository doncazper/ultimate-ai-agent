import type { ControlCenterCapabilitySurfaceReadModel } from "../api/types";
import { EmptyState } from "./DataState";

const STATUS_LABELS: Record<string, string> = {
  ui_api_cli_wired: "UI + API + CLI",
  partial_surface_coverage: "Partial",
  backend_or_cli_only: "Backend/CLI",
  mock_or_static_only: "Mock/static",
  blocked_intentionally: "Blocked",
};

export function CapabilitySurfacePanel({
  surface,
}: {
  surface: ControlCenterCapabilitySurfaceReadModel;
}) {
  const rows = surface.rows;
  const sourceTruthReady =
    surface.summary.missing_release_routes.length === 0 &&
    surface.summary.missing_visible_actions.length === 0;

  return (
    <section className="page-section" aria-labelledby="capability-surface-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Coverage cockpit</p>
          <h2 id="capability-surface-heading">Capabilities</h2>
        </div>
        <span className="status-pill compact">
          {sourceTruthReady ? "source truth current" : "source truth gap"}
        </span>
      </div>
      <p className="section-copy">{surface.safe_summary}</p>

      <div className="panel-grid">
        <MetricCard label="Capabilities" value={surface.summary.capability_count} />
        <MetricCard label="UI routes" value={surface.summary.ui_route_count} />
        <MetricCard label="Visible actions" value={surface.summary.visible_action_count} />
        <MetricCard label="API refs" value={surface.summary.api_route_count} />
      </div>

      <div className="panel-grid">
        <SummaryList
          title="Status"
          values={surface.summary.status_counts}
          labelFor={(key) => STATUS_LABELS[key] ?? key}
        />
        <SummaryList
          title="Source Truth"
          values={surface.summary.source_truth_status_counts}
        />
      </div>

      {!sourceTruthReady ? (
        <div className="callout blocked">
          <strong>Coverage gap</strong>
          <p>
            Missing routes:{" "}
            {surface.summary.missing_release_routes.join(", ") || "none"}.
            Missing actions:{" "}
            {surface.summary.missing_visible_actions.join(", ") || "none"}.
          </p>
        </div>
      ) : null}

      <section className="panel" aria-labelledby="web-hybrid-heading">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Governed external evidence</p>
            <h3 id="web-hybrid-heading">Web search and extraction</h3>
          </div>
          <span className="status-pill compact">read-only evidence</span>
        </div>
        <p>{surface.web_hybrid.safe_summary}</p>
        <div className="panel-grid">
          <MetricCard
            label="Active exact lanes"
            value={surface.web_hybrid.lanes.length}
          />
          <MetricCard
            label="Fallback ceiling"
            value={surface.web_hybrid.routing_attempt_ceiling}
          />
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Lane</th>
                <th>Availability</th>
                <th>Authority</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {surface.web_hybrid.lanes.map((lane) => (
                <tr key={lane.lane_ref}>
                  <td>
                    <strong>{lane.display_label}</strong>
                    <small>{lane.provider_ref}</small>
                  </td>
                  <td>{operatorLabel(lane.runtime_availability)}</td>
                  <td>{operatorLabel(lane.approval_posture)}</td>
                  <td>{operatorLabel(lane.cost_posture)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="callout blocked">
          <strong>Current runtime truth is not inferred</strong>
          <p>
            Credits: {operatorLabel(surface.web_hybrid.current_credit_snapshot_status)}.
            Circuit: {operatorLabel(surface.web_hybrid.circuit_state)}. Exact approval,
            AuthorityLease, and request budget evaluation remain mandatory.
          </p>
        </div>
        <div className="callout">
          <strong>External content is untrusted</strong>
          <p>
            Evidence cannot become instructions, memory writes, hidden context,
            browser actions, or production authority. Paid usage, Keyless, and
            cloud-first routing remain denied.
          </p>
        </div>
      </section>

      {rows.length > 0 ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Capability</th>
                <th>Status</th>
                <th>Authority</th>
                <th>Surfaces</th>
                <th>Gap</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.capability_id}>
                  <td>
                    <strong>{row.label}</strong>
                    <small>{row.capability_id}</small>
                    <small>{row.source_truth_status}</small>
                  </td>
                  <td>{STATUS_LABELS[row.status] ?? row.status}</td>
                  <td>{row.authority_posture}</td>
                  <td>
                    <small>
                      UI: {row.ui_routes.map((route) => route.path).join(", ") || "none"}
                    </small>
                    <small>
                      API: {row.api_routes.map((route) => route.route_ref).join(", ") || "none"}
                    </small>
                    <small>CLI: {row.cli_paths.join(", ") || "none"}</small>
                  </td>
                  <td>{row.missing_reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          title="No capability rows"
          message="The backend capability-surface read model returned no rows."
        />
      )}

      <div className="callout">
        <strong>Authority boundary</strong>
        <p>{surface.blocked_authority_refs.join(", ")}</p>
      </div>
    </section>
  );
}

function operatorLabel(value: string): string {
  return value.replaceAll("_", " ");
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <article className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function SummaryList({
  title,
  values,
  labelFor = (key) => key,
}: {
  title: string;
  values: Record<string, number>;
  labelFor?: (key: string) => string;
}) {
  return (
    <article className="panel compact-panel">
      <div className="panel-heading">
        <h3>{title}</h3>
      </div>
      <ul className="summary-list">
        {Object.entries(values).map(([key, value]) => (
          <li key={key}>
            <span>{labelFor(key)}</span>
            <strong>{value}</strong>
          </li>
        ))}
      </ul>
    </article>
  );
}
