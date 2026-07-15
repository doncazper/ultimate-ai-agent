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
  const mockFallback = surface.read_model_ref.includes(":mock");
  const sourceTruthReady =
    !mockFallback &&
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
          {mockFallback
            ? "fallback shape only"
            : sourceTruthReady
              ? "source truth current"
              : "source truth gap"}
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

      {!sourceTruthReady && !mockFallback ? (
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

      <section className="panel" aria-labelledby="capability-maturity-heading">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Evidence-gated maturity</p>
            <h3 id="capability-maturity-heading">Capability score evidence</h3>
          </div>
          <span className="status-pill compact">
            {operatorLabel(surface.maturity.verification_posture)}
          </span>
        </div>
        <p>{surface.maturity.safe_summary}</p>
        <div className="panel-grid">
          <MetricCard
            label="Accepted baseline"
            value={surface.maturity.verified_weighted_score}
          />
          <MetricCard
            label="Unaccepted target"
            value={surface.maturity.target_weighted_score}
          />
          <MetricCard
            label="Automated evidence ready"
            value={surface.maturity.automated_evidence_ready_count}
          />
          <MetricCard
            label="Targets still held"
            value={surface.maturity.uplift_target_count - surface.maturity.uplift_proven_count}
          />
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Component</th>
                <th>Baseline</th>
                <th>Target</th>
                <th>Verified</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {surface.maturity.components.map((component) => (
                <tr key={component.component_id}>
                  <td>
                    <strong>{component.label}</strong>
                    <small>{component.component_id}</small>
                  </td>
                  <td>{component.baseline_score}</td>
                  <td>{component.target_score}</td>
                  <td>{component.verified_score}</td>
                  <td>
                    {operatorLabel(component.evidence_status)}
                    {component.blocker_codes.length > 0 ? (
                      <small>{component.blocker_codes.join(", ")}</small>
                    ) : null}
                    <small>
                      Gates: {component.gates.filter((gate) => gate.status === "satisfied").length}/
                      {component.gates.length}
                    </small>
                    <small>Next proof: {component.next_acceptance_ref}</small>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="callout blocked">
          <strong>Scores never mint authority</strong>
          <p>
            Passing automated checks advances evidence readiness, not the score.
            A target remains at baseline until runtime, failure/recovery,
            operator-surface, and trusted independent acceptance all pass. A
            self-hashed acceptance ref cannot advance a score.
          </p>
        </div>
      </section>

      <section className="panel" aria-labelledby="web-hybrid-heading">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Governed external evidence</p>
            <h3 id="web-hybrid-heading">Web search and extraction</h3>
          </div>
          <span className="status-pill compact">read-only evidence</span>
        </div>
        <p>{surface.web_hybrid.safe_summary}</p>
        <dl className="detail-list compact">
          <div>
            <dt>Read model</dt>
            <dd>{surface.web_hybrid.read_model_ref}</dd>
          </div>
          <div>
            <dt>Human CLI</dt>
            <dd>{surface.web_hybrid.cli_path}</dd>
          </div>
          <div>
            <dt>Current observations</dt>
            <dd>not injected by this read-only surface</dd>
          </div>
        </dl>
        <div className="panel-grid">
          <MetricCard
            label="Implemented exact lanes"
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
                    <small>{lane.capability_ref}</small>
                    <small>{lane.adapter_ref}</small>
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
            mission-scoped AuthorityLease, complete request fingerprint, start
            deadline, and request budget evaluation remain mandatory at final start.
          </p>
        </div>
        <div className="callout">
          <strong>Bounded cited research</strong>
          <p>{surface.web_hybrid.research_aggregation.safe_summary}</p>
          <p>
            Deterministic cited aggregation is implemented for injected safe
            observations. This read-only surface performed no retrieval, so current
            citations are {surface.web_hybrid.research_aggregation.current_citation_count};
            zero means no current observation, not a live empty result. Provider
            readiness, latency, cost, context, routing, exclusions, and redaction are
            explicit.
          </p>
          <p>
            Proof refs: {surface.web_hybrid.research_aggregation.proof_refs.join(", ")}.
          </p>
          <p>
            Blockers:{" "}
            {surface.web_hybrid.research_aggregation.blocker_codes.join(", ")}.
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
