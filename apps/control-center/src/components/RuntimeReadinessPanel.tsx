import type {
  RuntimeCapabilityMatrix,
  RuntimeCapabilityDiscoveryReadModel,
  RuntimeDelegationAdapterReadModel,
  RuntimeReadinessReport,
} from "../api/types";
import { EmptyState } from "./DataState";
import { OperatorSurfaceStates } from "./OperatorSurfaceStates";

export function RuntimeReadinessPanel({
  report,
  matrix,
  delegationAdapter,
  capabilityDiscovery,
}: {
  report: RuntimeReadinessReport;
  matrix: RuntimeCapabilityMatrix;
  delegationAdapter: RuntimeDelegationAdapterReadModel;
  capabilityDiscovery: RuntimeCapabilityDiscoveryReadModel;
}) {
  const booleans = [
    ["Production readiness claim", report.production_ready],
    ["Reviewed local model runtime evidence", report.real_model_runtime_ready],
    ["Remote execution claim", report.remote_execution_ready],
    ["Mobile sensor claim", report.mobile_sensor_ready],
    ["Plugin/native build claim", report.plugin_or_native_build_ready],
  ];
  return (
    <section className="panel" aria-labelledby="runtime-readiness-heading">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Runtime boundary</p>
          <h2 id="runtime-readiness-heading">Runtime readiness</h2>
        </div>
        <span>{report.status}</span>
      </div>
      <p className="section-copy">
        Scoped runtime pilot state. The implemented lane is exact Action Inbox approval for
        focused pytest through RuntimeGateway; arbitrary shell, browser, connector, plugin,
        remote, public beta, and production authority remain blocked.
      </p>
      <OperatorSurfaceStates surface="Runtime" />
      <div className="flag-list">
        {booleans.map(([label, value]) => (
          <div key={label.toString()}>
            <span>{label}</span>
            <strong>{value ? "yes" : "no"}</strong>
          </div>
        ))}
      </div>
      <div className="panel-grid two">
        <article className="info-card">
          <div className="panel-heading compact-heading">
            <div>
              <p className="eyebrow">Delegated runtime</p>
              <h3>{delegationAdapter.runtime_label}</h3>
            </div>
            <span className="status-pill compact">
              {delegationAdapter.authority_mode}
            </span>
          </div>
          <p>{delegationAdapter.safe_summary}</p>
          <dl className="detail-grid">
            <div>
              <dt>Route</dt>
              <dd>{delegationAdapter.route_ref}</dd>
            </div>
            <div>
              <dt>CLI</dt>
              <dd>{delegationAdapter.cli_ref}</dd>
            </div>
            <div>
              <dt>Endpoint configured</dt>
              <dd>
                {delegationAdapter.endpoint_posture.endpoint_configured
                  ? "yes"
                  : "no"}
              </dd>
            </div>
            <div>
              <dt>Live submission</dt>
              <dd>
                {delegationAdapter.live_run_submission_enabled
                  ? "enabled"
                  : "blocked"}
              </dd>
            </div>
          </dl>
        </article>
        <article className="info-card">
          <h3>Delegation blockers</h3>
          <ul className="compact-list">
            {delegationAdapter.blocked_reason_refs.slice(0, 6).map((ref) => (
              <li key={ref}>{ref}</li>
            ))}
          </ul>
          <h3>Next safe actions</h3>
          <ul className="compact-list">
            {delegationAdapter.next_safe_action_refs.map((ref) => (
              <li key={ref}>{ref}</li>
            ))}
          </ul>
        </article>
      </div>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Capability discovery</p>
            <h3>Static capability snapshot</h3>
          </div>
          <span className="status-pill compact">
            {capabilityDiscovery.freshness_status}
          </span>
        </div>
        <p>{capabilityDiscovery.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{capabilityDiscovery.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{capabilityDiscovery.cli_ref}</dd>
          </div>
          <div>
            <dt>Live discovery</dt>
            <dd>
              {capabilityDiscovery.live_discovery_performed
                ? "performed"
                : "not performed"}
            </dd>
          </div>
          <div>
            <dt>UAA authorized execution</dt>
            <dd>{capabilityDiscovery.uaa_authorized_capability_count}</dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Capability</th>
                <th>Runtime support</th>
                <th>UAA authorization</th>
                <th>Trust label</th>
              </tr>
            </thead>
            <tbody>
              {capabilityDiscovery.capability_groups.map((group) => (
                <tr key={group.group_ref}>
                  <td>{group.group_kind}</td>
                  <td>{group.runtime_support_status}</td>
                  <td>{group.uaa_authorization_status}</td>
                  <td>{group.trust_label}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
      <h3>Capability Matrix</h3>
      {matrix.entries.length > 0 ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Surface</th>
                <th>Status</th>
                <th>Risk</th>
                <th>Model call</th>
                <th>Cloud</th>
              </tr>
            </thead>
            <tbody>
              {matrix.entries.map((entry) => (
                <tr key={entry.surface}>
                  <td>{entry.surface}</td>
                  <td>{entry.status}</td>
                  <td>{entry.risk_class}</td>
                  <td>{entry.real_model_call_allowed ? "yes" : "no"}</td>
                  <td>{entry.cloud_allowed ? "yes" : "no"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          title="No runtime surfaces listed"
          message="The local runtime matrix returned no entries."
        />
      )}
    </section>
  );
}
