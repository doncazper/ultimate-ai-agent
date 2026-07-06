import type {
  RuntimeCapabilityMatrix,
  RuntimeApprovalBridgeReadModel,
  RuntimeCapabilityDiscoveryReadModel,
  RuntimeDelegationAdapterReadModel,
  RuntimeRunEventsReadModel,
  RuntimeStreamingProgressReadModel,
  RuntimeProfileIsolationReadModel,
  RuntimeReadinessReport,
} from "../api/types";
import { EmptyState } from "./DataState";
import { OperatorSurfaceStates } from "./OperatorSurfaceStates";

export function RuntimeReadinessPanel({
  report,
  matrix,
  delegationAdapter,
  capabilityDiscovery,
  runEvents,
  approvalBridge,
  streamingProgress,
  profiles,
}: {
  report: RuntimeReadinessReport;
  matrix: RuntimeCapabilityMatrix;
  delegationAdapter: RuntimeDelegationAdapterReadModel;
  capabilityDiscovery: RuntimeCapabilityDiscoveryReadModel;
  runEvents: RuntimeRunEventsReadModel;
  approvalBridge: RuntimeApprovalBridgeReadModel;
  streamingProgress: RuntimeStreamingProgressReadModel;
  profiles: RuntimeProfileIsolationReadModel;
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
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Runs and events</p>
            <h3>Approval-wait proposal lane</h3>
          </div>
          <span className="status-pill compact">{runEvents.status}</span>
        </div>
        <p>{runEvents.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{runEvents.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{runEvents.cli_ref}</dd>
          </div>
          <div>
            <dt>Approval waits</dt>
            <dd>{runEvents.approval_wait_count}</dd>
          </div>
          <div>
            <dt>Completed runs</dt>
            <dd>{runEvents.completed_run_count}</dd>
          </div>
          <div>
            <dt>Create route</dt>
            <dd>{runEvents.create_run_route_enabled ? "enabled" : "blocked"}</dd>
          </div>
          <div>
            <dt>Stop route</dt>
            <dd>{runEvents.stop_run_route_enabled ? "enabled" : "blocked"}</dd>
          </div>
          <div>
            <dt>Approval resolution</dt>
            <dd>
              {runEvents.approval_resolution_route_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Live event stream</dt>
            <dd>{runEvents.live_event_stream_enabled ? "enabled" : "blocked"}</dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Runtime state</th>
                <th>UAA run state</th>
                <th>Receipt required</th>
                <th>Meaning</th>
              </tr>
            </thead>
            <tbody>
              {runEvents.lifecycle_mappings.slice(0, 6).map((mapping) => (
                <tr key={`${mapping.runtime_state}-${mapping.uaa_durable_run_state}`}>
                  <td>{mapping.runtime_state}</td>
                  <td>{mapping.uaa_durable_run_state}</td>
                  <td>{mapping.receipt_required_before_claim ? "yes" : "no"}</td>
                  <td>{mapping.safe_summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h4>Run proposals</h4>
        <ul className="compact-list">
          {runEvents.run_proposals.map((proposal) => (
            <li key={proposal.proposal_ref}>
              {proposal.runtime_run_ref}: {proposal.uaa_durable_run_state}; stop{" "}
              {proposal.stop_posture}; approval{" "}
              {proposal.approval_resolution_posture}
            </li>
          ))}
        </ul>
        <h4>Event previews</h4>
        <ul className="compact-list">
          {runEvents.event_previews.map((event) => (
            <li key={event.event_ref}>
              {event.event_kind}: {event.event_ref} {" -> "} {event.proof_ref}
            </li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Streaming progress</p>
            <h3>Redacted event previews</h3>
          </div>
          <span className="status-pill compact">
            {streamingProgress.stream_state}
          </span>
        </div>
        <p>{streamingProgress.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{streamingProgress.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{streamingProgress.cli_ref}</dd>
          </div>
          <div>
            <dt>Events</dt>
            <dd>{streamingProgress.event_count}</dd>
          </div>
          <div>
            <dt>Stale stream</dt>
            <dd>{streamingProgress.stale_stream ? "yes" : "no"}</dd>
          </div>
          <div>
            <dt>Live subscription</dt>
            <dd>
              {streamingProgress.live_subscription_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>SSE/WebSocket</dt>
            <dd>
              {streamingProgress.sse_transport_enabled ||
              streamingProgress.websocket_transport_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Seq</th>
                <th>Event</th>
                <th>Proof</th>
                <th>Hash</th>
              </tr>
            </thead>
            <tbody>
              {streamingProgress.event_previews.map((event) => (
                <tr key={event.event_ref}>
                  <td>{event.sequence}</td>
                  <td>{event.event_kind}</td>
                  <td>{event.proof_ref}</td>
                  <td>{event.event_hash_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h4>Blocked transport</h4>
        <ul className="compact-list">
          {streamingProgress.blocked_authority_refs.slice(0, 5).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Runtime profiles</p>
            <h3>Isolated profile metadata</h3>
          </div>
          <span className="status-pill compact">{profiles.status}</span>
        </div>
        <p>{profiles.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{profiles.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{profiles.cli_ref}</dd>
          </div>
          <div>
            <dt>Profiles</dt>
            <dd>{profiles.profile_count}</dd>
          </div>
          <div>
            <dt>Configured</dt>
            <dd>{profiles.configured_profile_count}</dd>
          </div>
          <div>
            <dt>Profile mutation</dt>
            <dd>
              {profiles.profile_creation_enabled ||
              profiles.runtime_config_write_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Cross-profile authority</dt>
            <dd>
              {profiles.cross_profile_authority_bleed_allowed
                ? "allowed"
                : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Profile</th>
                <th>Role</th>
                <th>Health</th>
                <th>Authority</th>
              </tr>
            </thead>
            <tbody>
              {profiles.profiles.map((profile) => (
                <tr key={profile.profile_ref}>
                  <td>{profile.display_label}</td>
                  <td>{profile.role}</td>
                  <td>{profile.profile_health}</td>
                  <td>{profile.authority_profile}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h4>Isolation blockers</h4>
        <ul className="compact-list">
          {profiles.blocked_authority_refs.slice(0, 5).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Approval bridge</p>
            <h3>Runtime request, UAA review</h3>
          </div>
          <span className="status-pill compact">{approvalBridge.status}</span>
        </div>
        <p>{approvalBridge.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{approvalBridge.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{approvalBridge.cli_ref}</dd>
          </div>
          <div>
            <dt>Runtime requested</dt>
            <dd>{approvalBridge.pending_runtime_approval_count}</dd>
          </div>
          <div>
            <dt>UAA approved</dt>
            <dd>
              {approvalBridge.envelopes.some(
                (envelope) => envelope.uaa_approval_recorded,
              )
                ? "yes"
                : "no"}
            </dd>
          </div>
          <div>
            <dt>Runtime resolutions sent</dt>
            <dd>{approvalBridge.runtime_resolution_sent_count}</dd>
          </div>
          <div>
            <dt>Approval route</dt>
            <dd>
              {approvalBridge.approval_resolution_route_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Timeout posture</dt>
            <dd>{approvalBridge.timeout_preview_count} default-deny preview</dd>
          </div>
          <div>
            <dt>Scope validation</dt>
            <dd>{approvalBridge.scope_validation.status}</dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Action Inbox item</th>
                <th>Status</th>
                <th>Approval controls</th>
                <th>Runtime controls</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{approvalBridge.action_inbox_projection.action_inbox_item_ref}</td>
                <td>{approvalBridge.action_inbox_projection.status}</td>
                <td>
                  {approvalBridge.action_inbox_projection.approval_controls_visible
                    ? "visible"
                    : "blocked"}
                </td>
                <td>
                  {approvalBridge.action_inbox_projection
                    .runtime_resolution_controls_visible
                    ? "visible"
                    : "blocked"}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <h4>Decision previews</h4>
        <ul className="compact-list">
          {approvalBridge.decision_previews.map((preview) => (
            <li key={preview.decision_ref}>
              {preview.decision_kind}: {preview.receipt_ref}; runtime send{" "}
              {preview.runtime_resolution_sent ? "sent" : "blocked"}
            </li>
          ))}
        </ul>
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
