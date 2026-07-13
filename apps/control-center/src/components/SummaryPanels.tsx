import type {
  ApprovalSummary,
  MobilePlanningSummary,
  PluginGovernanceSummary,
  PrivateMeshSummary,
  RemoteWorkerSummary,
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
      <p>
        Arbitrary approval refs:{" "}
        {summary.arbitrary_approval_ref_authority ? "authority" : "not authority"}
      </p>
    </section>
  );
}

export function RemoteWorkerSummaryPanel({
  remote,
  privateMesh,
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
      <p className="section-copy">
        Remote workers and private mesh entries are summaries only. No dispatch path is exposed.
      </p>
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
          <h2 id="mobile-planning-heading">Mobile Planning</h2>
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
          <h2 id="plugin-governance-heading">Plugin Governance</h2>
        </div>
        <span>{summary.status}</span>
      </div>
      <p>Plugin enablement allowed: {summary.plugin_enablement_allowed ? "yes" : "no"}</p>
      <p>Native build tools enabled: {summary.native_build_tools_enabled ? "yes" : "no"}</p>
      <p>Inspectable catalog entries: {summary.catalog_entry_count}</p>
      <p>Capability availability snapshots: {summary.availability_snapshot_count}</p>
      <p>
        Developer metadata validation: {summary.developer_validation_count - summary.blocked_validation_count} validated, {summary.blocked_validation_count} blocked
      </p>
      <p>Catalog visibility grants authority: {summary.catalog_visibility_grants_authority ? "yes" : "no"}</p>
      <p>Fresh request-scoped invocation decision required: {summary.request_scoped_invocation_decision_required ? "yes" : "no"}</p>
      <p>Plugin metadata boundary: {summary.plugin_metadata_boundary_ref}</p>
      <p>Skill marketplace boundary: {summary.skill_marketplace_boundary_ref}</p>
      <p>MCP catalog boundary: {summary.mcp_catalog_boundary_ref}</p>
      <p>Skill bundle proposals: {summary.skill_bundle_proposal_count}</p>
      <p>Skill bundle activation enabled: {summary.skill_bundle_activation_enabled ? "yes" : "no"}</p>
      <p>Skill bundle tool execution enabled: {summary.skill_bundle_tool_execution_enabled ? "yes" : "no"}</p>
      {summary.skill_bundle_proposal_refs.length > 0 ? (
        <ul className="summary-list">
          {summary.skill_bundle_proposal_refs.map((proposalRef) => (
            <li key={proposalRef}>{proposalRef}</li>
          ))}
        </ul>
      ) : null}
      {summary.blocker_codes.length > 0 ? (
        <>
          <h3>Blocked reasons</h3>
          <ul className="summary-list">
            {summary.blocker_codes.map((code) => <li key={code}>{code}</li>)}
          </ul>
        </>
      ) : null}
      {summary.extension_entries.length > 0 ? (
        <ul className="summary-list" aria-label="Extension ecosystem posture">
          {summary.extension_entries.map((entry) => (
            <li key={entry.package_ref}>
              <strong>{entry.package_ref}</strong>
              <span>
                {entry.validation_status}; compatibility {entry.compatibility_status}; configuration {entry.configuration_status}; health {entry.health_status}; authority {entry.authority_posture}; budget {entry.resource_status}; safe-disable {entry.safe_disable_status}
              </span>
              <span>
                provenance {entry.provenance_status}; pinned hashes {entry.hashes_verified_against_pinned_values ? "verified" : "unverified"}; signature {entry.signature_status}
              </span>
              <span>{entry.safe_disable_ref}</span>
              <span>{entry.rollback_ref}</span>
            </li>
          ))}
        </ul>
      ) : null}
      <p className="muted">Inspectable extensions are never globally callable.</p>
    </section>
  );
}
