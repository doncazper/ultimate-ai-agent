import type {
  ApprovalSummary,
  MobilePlanningSummary,
  PluginGovernanceSummary,
  PrivateMeshSummary,
  RemoteWorkerSummary
} from "../api/types";
import { StatusCard } from "./StatusCard";

export function ApprovalSummaryPanel({ summary }: { summary: ApprovalSummary }) {
  return (
    <section className="panel" aria-labelledby="approvals-heading">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Authority boundary</p>
          <h2 id="approvals-heading">Approvals</h2>
        </div>
        <span>{summary.pending_count} pending</span>
      </div>
      <p>{summary.summary}</p>
      <p>Arbitrary approval refs: {summary.arbitrary_approval_ref_authority ? "authority" : "not authority"}</p>
    </section>
  );
}

export function RemoteWorkerSummaryPanel({
  remote,
  privateMesh
}: {
  remote: RemoteWorkerSummary;
  privateMesh: PrivateMeshSummary;
}) {
  return (
    <section className="page-section" aria-labelledby="remote-worker-boundary-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Remote planning</p>
          <h2 id="remote-worker-boundary-heading">Remote worker boundary</h2>
        </div>
        <span className="status-pill compact">metadata only</span>
      </div>
      <p className="section-copy">Remote workers and private mesh entries are summaries only. No dispatch path is exposed.</p>
      <div className="panel-grid">
        <StatusCard
          label="Remote workers"
          status={remote.status}
          summary={`Execution enabled: ${remote.execution_enabled ? "yes" : "no"}. Dispatch enabled: ${
            remote.dispatch_enabled ? "yes" : "no"
          }.`}
        />
        <StatusCard
          label="Private mesh"
          status={privateMesh.status}
          summary={`Headscale: ${privateMesh.headscale_integrated ? "yes" : "no"}. Tailscale: ${
            privateMesh.tailscale_integrated ? "yes" : "no"
          }. WireGuard: ${privateMesh.wireguard_integrated ? "yes" : "no"}.`}
        />
      </div>
    </section>
  );
}

export function MobilePlanningPanel({ summary }: { summary: MobilePlanningSummary }) {
  return (
    <section className="panel" aria-labelledby="mobile-planning-heading">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Future companion</p>
          <h2 id="mobile-planning-heading">Mobile planning</h2>
        </div>
        <span>{summary.status}</span>
      </div>
      <p>Sensor access enabled: {summary.sensor_access_enabled ? "yes" : "no"}</p>
      <p>Mobile app implemented: {summary.mobile_app_implemented ? "yes" : "no"}</p>
    </section>
  );
}

export function PluginGovernancePanel({ summary }: { summary: PluginGovernanceSummary }) {
  return (
    <section className="panel" aria-labelledby="plugin-governance-heading">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Tool boundary</p>
          <h2 id="plugin-governance-heading">Plugin governance</h2>
        </div>
        <span>{summary.status}</span>
      </div>
      <p>Plugin enablement allowed: {summary.plugin_enablement_allowed ? "yes" : "no"}</p>
      <p>Native build tools enabled: {summary.native_build_tools_enabled ? "yes" : "no"}</p>
    </section>
  );
}
