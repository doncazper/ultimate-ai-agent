import type {
  RuntimeCapabilityMatrix,
  RuntimeApprovalBridgeReadModel,
  RuntimeBackgroundJobsReadModel,
  RuntimeCapabilityDiscoveryReadModel,
  RuntimeContextBudgetPressureReadModel,
  RuntimeDelegationAdapterReadModel,
  RuntimeDoctorDiagnosticsReadModel,
  RuntimeInterfaceModeReadModel,
  HermesContextPackReadModel,
  RuntimeHardlineCommandBlocklistReadModel,
  RuntimeInterruptRedirectReadModel,
  RuntimeLoggingProfileReadModel,
  RuntimeLspDiagnosticsReadModel,
  RuntimeManagedScopePolicyReadModel,
  RuntimeMcpCatalogFilteringReadModel,
  RuntimeSubagentIsolationReadModel,
  RuntimeSessionContinuityReadModel,
  RuntimeToolRegistryAvailabilityReadModel,
  RuntimeRunEventsReadModel,
  RuntimeStagedOrchestrationReadModel,
  RuntimeStreamingProgressReadModel,
  RuntimeProfileIsolationReadModel,
  RuntimePromptStabilityTiersReadModel,
  RuntimePreviewRailReadModel,
  RuntimeReadinessReport,
  RuntimeResultClassificationReadModel,
  RuntimeSlashCommandRegistryReadModel,
  RuntimeUsageCostAnalyticsReadModel,
  RuntimeVirtualProviderMoaReadModel,
  RuntimeWorktreePerAgentReadModel,
} from "../api/types";
import { EmptyState } from "./DataState";
import { OperatorSurfaceStates } from "./OperatorSurfaceStates";

export function RuntimeReadinessPanel({
  report,
  matrix,
  delegationAdapter,
  interfaceMode,
  hermesContextPack,
  capabilityDiscovery,
  runEvents,
  approvalBridge,
  streamingProgress,
  profiles,
  toolRegistry,
  virtualProviderMoa,
  usageCostAnalytics,
  promptStabilityTiers,
  contextBudgetPressure,
  hardlineCommandBlocklist,
  managedScopePolicy,
  doctorDiagnostics,
  sessionContinuity,
  mcpCatalogFiltering,
  backgroundJobs,
  subagentIsolation,
  worktreePerAgent,
  stagedOrchestration,
  lspDiagnostics,
  previewRail,
  slashCommandRegistry,
  interruptRedirect,
  loggingProfile,
  resultClassification,
}: {
  report: RuntimeReadinessReport;
  matrix: RuntimeCapabilityMatrix;
  delegationAdapter: RuntimeDelegationAdapterReadModel;
  interfaceMode: RuntimeInterfaceModeReadModel;
  hermesContextPack: HermesContextPackReadModel;
  capabilityDiscovery: RuntimeCapabilityDiscoveryReadModel;
  runEvents: RuntimeRunEventsReadModel;
  approvalBridge: RuntimeApprovalBridgeReadModel;
  streamingProgress: RuntimeStreamingProgressReadModel;
  profiles: RuntimeProfileIsolationReadModel;
  toolRegistry: RuntimeToolRegistryAvailabilityReadModel;
  virtualProviderMoa: RuntimeVirtualProviderMoaReadModel;
  usageCostAnalytics: RuntimeUsageCostAnalyticsReadModel;
  promptStabilityTiers: RuntimePromptStabilityTiersReadModel;
  contextBudgetPressure: RuntimeContextBudgetPressureReadModel;
  hardlineCommandBlocklist: RuntimeHardlineCommandBlocklistReadModel;
  managedScopePolicy: RuntimeManagedScopePolicyReadModel;
  doctorDiagnostics: RuntimeDoctorDiagnosticsReadModel;
  sessionContinuity: RuntimeSessionContinuityReadModel;
  mcpCatalogFiltering: RuntimeMcpCatalogFilteringReadModel;
  backgroundJobs: RuntimeBackgroundJobsReadModel;
  subagentIsolation: RuntimeSubagentIsolationReadModel;
  worktreePerAgent: RuntimeWorktreePerAgentReadModel;
  stagedOrchestration: RuntimeStagedOrchestrationReadModel;
  lspDiagnostics: RuntimeLspDiagnosticsReadModel;
  previewRail: RuntimePreviewRailReadModel;
  slashCommandRegistry: RuntimeSlashCommandRegistryReadModel;
  interruptRedirect: RuntimeInterruptRedirectReadModel;
  loggingProfile: RuntimeLoggingProfileReadModel;
  resultClassification: RuntimeResultClassificationReadModel;
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
              <p className="eyebrow">Interface mode</p>
              <h3>{interfaceMode.active_mode}</h3>
            </div>
            <span className="status-pill compact">{interfaceMode.status}</span>
          </div>
          <p>{interfaceMode.safe_summary}</p>
          <dl className="detail-grid">
            <div>
              <dt>Route</dt>
              <dd>{interfaceMode.route_ref}</dd>
            </div>
            <div>
              <dt>CLI</dt>
              <dd>{interfaceMode.cli_ref}</dd>
            </div>
            <div>
              <dt>UAA-native agent</dt>
              <dd>{interfaceMode.uaa_execution_enabled ? "enabled" : "off"}</dd>
            </div>
            <div>
              <dt>Memory updates</dt>
              <dd>{interfaceMode.memory_update_policy}</dd>
            </div>
          </dl>
          <ul className="compact-list">
            {interfaceMode.mode_profiles.map((profile) => (
              <li key={profile.mode}>
                {profile.mode}:{" "}
                {profile.mode === "disabled"
                  ? "disabled"
                  : profile.external_handoff_only
                    ? "external only"
                    : "guarded"}
                ; UAA execution off
              </li>
            ))}
          </ul>
        </article>
        <article className="info-card">
          <div className="panel-heading compact-heading">
            <div>
              <p className="eyebrow">Hermes CLI</p>
              <h3>{interfaceMode.hermes_cli_posture.status}</h3>
            </div>
            <span className="status-pill compact">
              {interfaceMode.hermes_cli_posture.discovery_source}
            </span>
          </div>
          <p>{interfaceMode.hermes_cli_posture.safe_summary}</p>
          <dl className="detail-grid">
            <div>
              <dt>Status argv</dt>
              <dd>{interfaceMode.hermes_cli_posture.readiness_command_shape_ref}</dd>
            </div>
            <div>
              <dt>Chat argv</dt>
              <dd>{interfaceMode.hermes_cli_posture.chat_command_shape_ref}</dd>
            </div>
            <div>
              <dt>Exact argv only</dt>
              <dd>{interfaceMode.hermes_cli_posture.exact_argv_only ? "yes" : "no"}</dd>
            </div>
            <div>
              <dt>Unsafe modes</dt>
              <dd>
                {interfaceMode.hermes_cli_posture.yolo_allowed ||
                interfaceMode.hermes_cli_posture.oneshot_allowed
                  ? "allowed"
                  : "blocked"}
              </dd>
            </div>
          </dl>
        </article>
      </div>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Hermes context bridge</p>
            <h3>{hermesContextPack.context_pack_ref}</h3>
          </div>
          <span className="status-pill compact">{hermesContextPack.status}</span>
        </div>
        <p>{hermesContextPack.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{hermesContextPack.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{hermesContextPack.cli_ref}</dd>
          </div>
          <div>
            <dt>Sections</dt>
            <dd>{hermesContextPack.section_count}</dd>
          </div>
          <div>
            <dt>Projection</dt>
            <dd>{hermesContextPack.projection_enabled ? "enabled" : "disabled"}</dd>
          </div>
          <div>
            <dt>Raw database access</dt>
            <dd>
              {hermesContextPack.hermes_receives_raw_database_access
                ? "exposed"
                : "not exposed"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Source</th>
                <th>Projection</th>
                <th>Why shown</th>
              </tr>
            </thead>
            <tbody>
              {hermesContextPack.sections.length > 0 ? (
                hermesContextPack.sections.map((section) => (
                  <tr key={section.section_ref}>
                    <td>{section.source_surface}</td>
                    <td>{section.projected_to_hermes ? "Hermes-projected" : "UAA-native only"}</td>
                    <td>{section.why_shown_refs[0]}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td>UAA-native context</td>
                  <td>Hermes projection disabled</td>
                  <td>UAA is not acting as a Hermes frontend.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </article>
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
        <div className="panel-heading compact-heading subsection-heading">
          <div>
            <p className="eyebrow">Toolset posture</p>
            <h3>Runtime support vs UAA allowance</h3>
          </div>
          <span className="status-pill compact">
            {capabilityDiscovery.toolset_posture.status}
          </span>
        </div>
        <p>{capabilityDiscovery.toolset_posture.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Toolsets</dt>
            <dd>{capabilityDiscovery.toolset_posture.toolset_count}</dd>
          </div>
          <div>
            <dt>Runtime supported</dt>
            <dd>{capabilityDiscovery.toolset_posture.runtime_supported_count}</dd>
          </div>
          <div>
            <dt>UAA execution allowed</dt>
            <dd>
              {capabilityDiscovery.toolset_posture.uaa_allowed_execution_count}
            </dd>
          </div>
          <div>
            <dt>Approval-required future</dt>
            <dd>
              {capabilityDiscovery.toolset_posture.approval_required_future_count}
            </dd>
          </div>
          <div>
            <dt>Blocked</dt>
            <dd>{capabilityDiscovery.toolset_posture.blocked_count}</dd>
          </div>
          <div>
            <dt>Unsupported</dt>
            <dd>{capabilityDiscovery.toolset_posture.unsupported_count}</dd>
          </div>
          <div>
            <dt>Tool invocation</dt>
            <dd>
              {capabilityDiscovery.toolset_posture.live_tool_invocation_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Config mutation</dt>
            <dd>
              {capabilityDiscovery.toolset_posture.toolset_config_mutation_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Toolset</th>
                <th>Runtime support</th>
                <th>UAA allowance</th>
                <th>Side effect</th>
              </tr>
            </thead>
            <tbody>
              {capabilityDiscovery.toolset_posture.records.map((record) => (
                <tr key={record.toolset_ref}>
                  <td>{record.display_label}</td>
                  <td>{record.runtime_support_status}</td>
                  <td>{record.uaa_allowance_status}</td>
                  <td>{record.side_effect_class}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Proof</dt>
            <dd>
              <ul className="compact-list">
                {capabilityDiscovery.toolset_posture.proof_refs
                  .slice(0, 3)
                  .map((ref) => (
                    <li key={ref}>{ref}</li>
                  ))}
              </ul>
            </dd>
          </div>
          <div>
            <dt>Blocked authority</dt>
            <dd>
              <ul className="compact-list">
                {capabilityDiscovery.toolset_posture.blocked_authority_refs
                  .slice(0, 3)
                  .map((ref) => (
                    <li key={ref}>{ref}</li>
                  ))}
              </ul>
            </dd>
          </div>
        </dl>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Staged orchestration</p>
            <h3>Authority-scoped plan</h3>
          </div>
          <span className="status-pill compact">
            {stagedOrchestration.plan.status}
          </span>
        </div>
        <p>{stagedOrchestration.plan.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{stagedOrchestration.api_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{stagedOrchestration.cli_ref}</dd>
          </div>
          <div>
            <dt>Validation</dt>
            <dd>{stagedOrchestration.validation.status}</dd>
          </div>
          <div>
            <dt>Checkpoint</dt>
            <dd>{stagedOrchestration.latest_checkpoint_ref ?? "none"}</dd>
          </div>
          <div>
            <dt>Read authority</dt>
            <dd>
              <span>{stagedOrchestration.authority_state_decision_outcome}</span>
              <br />
              <span>{stagedOrchestration.authority_state_decision_ref}</span>
            </dd>
          </div>
          <div>
            <dt>Runtime command</dt>
            <dd>
              <span>
                {stagedOrchestration.runtime_command_authority_state_decision_outcome}
              </span>
              <br />
              <span>
                {stagedOrchestration.runtime_command_authority_state_decision_ref}
              </span>
            </dd>
          </div>
        </dl>
        <div className="flag-list">
          <div>
            <span>Stages</span>
            <strong>{stagedOrchestration.progress.total_stage_count}</strong>
          </div>
          <div>
            <span>Steps</span>
            <strong>{stagedOrchestration.progress.total_step_count}</strong>
          </div>
          <div>
            <span>Waiting</span>
            <strong>{stagedOrchestration.progress.waiting_count}</strong>
          </div>
          <div>
            <span>Degraded</span>
            <strong>{stagedOrchestration.progress.degraded_count}</strong>
          </div>
          <div>
            <span>Execution</span>
            <strong>
              {stagedOrchestration.execution_performed ? "performed" : "not run"}
            </strong>
          </div>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Stage</th>
                <th>Status</th>
                <th>Steps</th>
                <th>Checkpoint</th>
              </tr>
            </thead>
            <tbody>
              {stagedOrchestration.plan.stages.map((stage) => (
                <tr key={stage.stage_ref}>
                  <td>{stage.stage_ref}</td>
                  <td>{stage.status}</td>
                  <td>{stage.step_refs.length}</td>
                  <td>{stage.checkpoint_refs[0] ?? "none"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {stagedOrchestration.plan.blocked_authority_refs.slice(0, 6).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Managed scope</p>
            <h3>Local policy profile</h3>
          </div>
          <span className="status-pill compact">{managedScopePolicy.status}</span>
        </div>
        <p>{managedScopePolicy.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{managedScopePolicy.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{managedScopePolicy.cli_ref}</dd>
          </div>
          <div>
            <dt>Policy profile</dt>
            <dd>{managedScopePolicy.policy_profile_ref}</dd>
          </div>
          <div>
            <dt>Pinned sources</dt>
            <dd>{managedScopePolicy.pinned_source_count}</dd>
          </div>
          <div>
            <dt>Drift warnings</dt>
            <dd>{managedScopePolicy.drift_warning_count}</dd>
          </div>
          <div>
            <dt>Config writes</dt>
            <dd>
              {managedScopePolicy.system_config_write_enabled ||
              managedScopePolicy.privileged_write_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>MDM delivery</dt>
            <dd>
              {managedScopePolicy.mdm_delivery_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Production enforcement</dt>
            <dd>
              {managedScopePolicy.production_enforcement_claimed
                ? "claimed"
                : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Source</th>
                <th>Kind</th>
                <th>Precedence</th>
                <th>Drift</th>
              </tr>
            </thead>
            <tbody>
              {managedScopePolicy.pinned_sources.map((source) => (
                <tr key={source.source_ref}>
                  <td>{source.display_label}</td>
                  <td>{source.source_kind}</td>
                  <td>{source.precedence}</td>
                  <td>{source.drift_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h4>Drift warnings</h4>
        <ul className="compact-list">
          {managedScopePolicy.drift_warnings.map((warning) => (
            <li key={warning.warning_ref}>
              {warning.warning_ref}: {warning.status}
            </li>
          ))}
        </ul>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {managedScopePolicy.blocked_authority_refs.slice(0, 5).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Doctor</p>
            <h3>Setup diagnostics</h3>
          </div>
          <span className="status-pill compact">{doctorDiagnostics.status}</span>
        </div>
        <p>{doctorDiagnostics.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{doctorDiagnostics.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{doctorDiagnostics.cli_ref}</dd>
          </div>
          <div>
            <dt>Diagnostics</dt>
            <dd>{doctorDiagnostics.diagnostic_count}</dd>
          </div>
          <div>
            <dt>Review</dt>
            <dd>{doctorDiagnostics.review_count}</dd>
          </div>
          <div>
            <dt>Blocked</dt>
            <dd>{doctorDiagnostics.blocked_count}</dd>
          </div>
          <div>
            <dt>Installs</dt>
            <dd>{doctorDiagnostics.install_enabled ? "enabled" : "blocked"}</dd>
          </div>
          <div>
            <dt>Service starts</dt>
            <dd>
              {doctorDiagnostics.service_start_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Config mutation</dt>
            <dd>
              {doctorDiagnostics.runtime_config_mutation_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Domain</th>
                <th>Status</th>
                <th>Summary</th>
              </tr>
            </thead>
            <tbody>
              {doctorDiagnostics.diagnostics.map((item) => (
                <tr key={item.diagnostic_ref}>
                  <td>{item.display_label}</td>
                  <td>{item.status}</td>
                  <td>{item.safe_summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {doctorDiagnostics.blocked_authority_refs.slice(0, 5).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Continuity</p>
            <h3>Session continuity</h3>
          </div>
          <span className="status-pill compact">{sessionContinuity.status}</span>
        </div>
        <p>{sessionContinuity.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{sessionContinuity.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{sessionContinuity.cli_ref}</dd>
          </div>
          <div>
            <dt>Primary session</dt>
            <dd>{sessionContinuity.primary_session_ref}</dd>
          </div>
          <div>
            <dt>Surfaces</dt>
            <dd>{sessionContinuity.surface_count}</dd>
          </div>
          <div>
            <dt>Stale</dt>
            <dd>{sessionContinuity.stale_count}</dd>
          </div>
          <div>
            <dt>Conflict</dt>
            <dd>{sessionContinuity.conflict_count}</dd>
          </div>
          <div>
            <dt>Account sync</dt>
            <dd>{sessionContinuity.account_sync_enabled ? "enabled" : "blocked"}</dd>
          </div>
          <div>
            <dt>Remote session</dt>
            <dd>
              {sessionContinuity.remote_session_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Surface</th>
                <th>State</th>
                <th>Summary</th>
              </tr>
            </thead>
            <tbody>
              {sessionContinuity.surfaces.map((surface) => (
                <tr key={surface.surface_ref}>
                  <td>{surface.source_label}</td>
                  <td>{surface.continuity_state}</td>
                  <td>{surface.safe_summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {sessionContinuity.blocked_authority_refs.slice(0, 5).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">MCP</p>
            <h3>MCP catalog filtering</h3>
          </div>
          <span className="status-pill compact">
            {mcpCatalogFiltering.status}
          </span>
        </div>
        <p>{mcpCatalogFiltering.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{mcpCatalogFiltering.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{mcpCatalogFiltering.cli_ref}</dd>
          </div>
          <div>
            <dt>Servers</dt>
            <dd>{mcpCatalogFiltering.server_count}</dd>
          </div>
          <div>
            <dt>Tool slices</dt>
            <dd>{mcpCatalogFiltering.tool_slice_count}</dd>
          </div>
          <div>
            <dt>Filtered</dt>
            <dd>{mcpCatalogFiltering.filtered_blocked_tool_count}</dd>
          </div>
          <div>
            <dt>Grant required</dt>
            <dd>{mcpCatalogFiltering.grant_required_tool_count}</dd>
          </div>
          <div>
            <dt>Server install</dt>
            <dd>{mcpCatalogFiltering.install_enabled ? "enabled" : "blocked"}</dd>
          </div>
          <div>
            <dt>Tool invocation</dt>
            <dd>
              {mcpCatalogFiltering.tool_invocation_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Server</th>
                <th>State</th>
                <th>Tools</th>
                <th>Summary</th>
              </tr>
            </thead>
            <tbody>
              {mcpCatalogFiltering.servers.map((server) => (
                <tr key={server.server_ref}>
                  <td>{server.display_label}</td>
                  <td>{server.catalog_state}</td>
                  <td>{server.tool_count}</td>
                  <td>{server.safe_summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Tool slice</th>
                <th>Filter</th>
                <th>Risk</th>
                <th>Invocation</th>
              </tr>
            </thead>
            <tbody>
              {mcpCatalogFiltering.servers.flatMap((server) =>
                server.tool_slices.map((tool) => (
                  <tr key={tool.tool_ref}>
                    <td>{tool.display_label}</td>
                    <td>{tool.filter_state}</td>
                    <td>{tool.risk_label}</td>
                    <td>{tool.invocation_enabled ? "enabled" : "blocked"}</td>
                  </tr>
                )),
              )}
            </tbody>
          </table>
        </div>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {mcpCatalogFiltering.blocked_authority_refs.slice(0, 6).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Background</p>
            <h3>Background job model</h3>
          </div>
          <span className="status-pill compact">{backgroundJobs.status}</span>
        </div>
        <p>{backgroundJobs.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{backgroundJobs.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{backgroundJobs.cli_ref}</dd>
          </div>
          <div>
            <dt>AuthorityState</dt>
            <dd>{backgroundJobs.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability</dt>
            <dd>{backgroundJobs.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>
              <span>{backgroundJobs.authority_state_decision_outcome}</span>
              <br />
              <span>{backgroundJobs.authority_state_decision_ref}</span>
            </dd>
          </div>
          <div>
            <dt>Reason</dt>
            <dd>{backgroundJobs.authority_state_reason_refs[0] ?? "none"}</dd>
          </div>
          <div>
            <dt>Jobs</dt>
            <dd>{backgroundJobs.job_count}</dd>
          </div>
          <div>
            <dt>Reviewable</dt>
            <dd>{backgroundJobs.reviewable_job_count}</dd>
          </div>
          <div>
            <dt>Paused</dt>
            <dd>{backgroundJobs.paused_count}</dd>
          </div>
          <div>
            <dt>Execution blocked</dt>
            <dd>{backgroundJobs.execution_blocked_count}</dd>
          </div>
          <div>
            <dt>Scheduler</dt>
            <dd>{backgroundJobs.scheduler_enabled ? "enabled" : "blocked"}</dd>
          </div>
          <div>
            <dt>Worker</dt>
            <dd>
              {backgroundJobs.background_worker_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Job</th>
                <th>Status</th>
                <th>Schedule</th>
                <th>Receipt</th>
              </tr>
            </thead>
            <tbody>
              {backgroundJobs.jobs.map((job) => (
                <tr key={job.job_ref}>
                  <td>{job.display_label}</td>
                  <td>{job.status}</td>
                  <td>{job.schedule_policy}</td>
                  <td>{job.receipt_plan_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Run now</dt>
            <dd>{backgroundJobs.run_now_enabled ? "enabled" : "blocked"}</dd>
          </div>
          <div>
            <dt>Autonomous retry</dt>
            <dd>
              {backgroundJobs.autonomous_retry_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
          <div>
            <dt>External delivery</dt>
            <dd>
              {backgroundJobs.external_delivery_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Connector write</dt>
            <dd>
              {backgroundJobs.connector_write_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
        </dl>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {backgroundJobs.blocked_authority_refs.slice(0, 6).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Subagents</p>
            <h3>Isolation model</h3>
          </div>
          <span className="status-pill compact">{subagentIsolation.status}</span>
        </div>
        <p>{subagentIsolation.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{subagentIsolation.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{subagentIsolation.cli_ref}</dd>
          </div>
          <div>
            <dt>AuthorityState</dt>
            <dd>{subagentIsolation.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability</dt>
            <dd>{subagentIsolation.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>
              <span>{subagentIsolation.authority_state_decision_outcome}</span>
              <br />
              <span>{subagentIsolation.authority_state_decision_ref}</span>
            </dd>
          </div>
          <div>
            <dt>Reason</dt>
            <dd>
              {subagentIsolation.authority_state_reason_refs[0] ?? "none"}
            </dd>
          </div>
          <div>
            <dt>Roles</dt>
            <dd>{subagentIsolation.role_count}</dd>
          </div>
          <div>
            <dt>Review artifacts</dt>
            <dd>{subagentIsolation.review_artifact_count}</dd>
          </div>
          <div>
            <dt>Contract ready</dt>
            <dd>{subagentIsolation.contract_ready_count}</dd>
          </div>
          <div>
            <dt>Dispatch blocked</dt>
            <dd>{subagentIsolation.blocked_dispatch_count}</dd>
          </div>
          <div>
            <dt>Live dispatch</dt>
            <dd>
              {subagentIsolation.live_dispatch_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Fan-out</dt>
            <dd>
              {subagentIsolation.background_fanout_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Role</th>
                <th>Status</th>
                <th>Context</th>
                <th>Receipt</th>
              </tr>
            </thead>
            <tbody>
              {subagentIsolation.roles.map((role) => (
                <tr key={role.role_ref}>
                  <td>{role.display_label}</td>
                  <td>{role.readiness_status}</td>
                  <td>{role.context_pack_ref}</td>
                  <td>{role.receipt_plan_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Artifact</th>
                <th>Kind</th>
                <th>Executable</th>
              </tr>
            </thead>
            <tbody>
              {subagentIsolation.review_artifacts.map((artifact) => (
                <tr key={artifact.artifact_ref}>
                  <td>{artifact.display_label}</td>
                  <td>{artifact.artifact_kind}</td>
                  <td>
                    {artifact.executable_authority ? "enabled" : "blocked"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Tool sharing</dt>
            <dd>
              {subagentIsolation.tool_sharing_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Memory transfer</dt>
            <dd>
              {subagentIsolation.cross_agent_memory_transfer_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Provider call</dt>
            <dd>
              {subagentIsolation.provider_call_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Connector write</dt>
            <dd>
              {subagentIsolation.connector_write_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
        </dl>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {subagentIsolation.blocked_authority_refs.slice(0, 6).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Worktrees</p>
            <h3>Per-agent posture</h3>
          </div>
          <span className="status-pill compact">{worktreePerAgent.status}</span>
        </div>
        <p>{worktreePerAgent.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{worktreePerAgent.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{worktreePerAgent.cli_ref}</dd>
          </div>
          <div>
            <dt>Lanes</dt>
            <dd>{worktreePerAgent.lane_count}</dd>
          </div>
          <div>
            <dt>Mutation blocked</dt>
            <dd>{worktreePerAgent.mutation_blocked_count}</dd>
          </div>
          <div>
            <dt>Authority state</dt>
            <dd>{worktreePerAgent.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Authority decisions</dt>
            <dd>
              {worktreePerAgent.authority_state_allowed_count} allow /{" "}
              {worktreePerAgent.authority_state_degraded_count} draft /{" "}
              {worktreePerAgent.authority_state_denied_count} deny
            </dd>
          </div>
          <div>
            <dt>Worktree create</dt>
            <dd>
              {worktreePerAgent.git_worktree_create_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Branch mutation</dt>
            <dd>
              {worktreePerAgent.branch_mutation_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Commit</dt>
            <dd>{worktreePerAgent.commit_enabled ? "enabled" : "blocked"}</dd>
          </div>
          <div>
            <dt>Push</dt>
            <dd>{worktreePerAgent.push_enabled ? "enabled" : "blocked"}</dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Lane</th>
                <th>Status</th>
                <th>Authority</th>
                <th>Branch</th>
                <th>Rollback</th>
              </tr>
            </thead>
            <tbody>
              {worktreePerAgent.lanes.map((lane) => (
                <tr key={lane.lane_ref}>
                  <td>{lane.display_label}</td>
                  <td>{lane.lane_status}</td>
                  <td>
                    {lane.authority_state_decision_outcome}
                    <br />
                    {lane.authority_state_decision_ref}
                  </td>
                  <td>{lane.branch_proposal_ref}</td>
                  <td>{lane.rollback_plan_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>File write</dt>
            <dd>
              {worktreePerAgent.file_write_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Shell</dt>
            <dd>
              {worktreePerAgent.shell_execution_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Provider call</dt>
            <dd>
              {worktreePerAgent.provider_call_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Raw path</dt>
            <dd>{worktreePerAgent.raw_path_persisted ? "stored" : "omitted"}</dd>
          </div>
        </dl>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {worktreePerAgent.blocked_authority_refs.slice(0, 6).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Diagnostics</p>
            <h3>Semantic proof posture</h3>
          </div>
          <span className="status-pill compact">{lspDiagnostics.status}</span>
        </div>
        <p>{lspDiagnostics.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{lspDiagnostics.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{lspDiagnostics.cli_ref}</dd>
          </div>
          <div>
            <dt>AuthorityState</dt>
            <dd>{lspDiagnostics.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability</dt>
            <dd>{lspDiagnostics.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>
              <span>{lspDiagnostics.authority_state_decision_outcome}</span>
              <br />
              <span>{lspDiagnostics.authority_state_decision_ref}</span>
            </dd>
          </div>
          <div>
            <dt>Reason</dt>
            <dd>{lspDiagnostics.authority_state_reason_refs[0] ?? "none"}</dd>
          </div>
          <div>
            <dt>Diagnostics</dt>
            <dd>{lspDiagnostics.diagnostic_count}</dd>
          </div>
          <div>
            <dt>Proof ready</dt>
            <dd>{lspDiagnostics.proof_ready_count}</dd>
          </div>
          <div>
            <dt>Server launch</dt>
            <dd>
              {lspDiagnostics.language_server_started ? "enabled" : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Install</dt>
            <dd>
              {lspDiagnostics.dependency_install_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Shell</dt>
            <dd>
              {lspDiagnostics.shell_execution_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
          <div>
            <dt>File read</dt>
            <dd>{lspDiagnostics.file_read_enabled ? "enabled" : "blocked"}</dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Diagnostic</th>
                <th>Status</th>
                <th>Evidence</th>
                <th>Receipt</th>
              </tr>
            </thead>
            <tbody>
              {lspDiagnostics.diagnostics.map((diagnostic) => (
                <tr key={diagnostic.diagnostic_ref}>
                  <td>{diagnostic.display_label}</td>
                  <td>{diagnostic.status}</td>
                  <td>{diagnostic.evidence_ref}</td>
                  <td>{diagnostic.receipt_plan_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Raw payload</dt>
            <dd>
              {lspDiagnostics.raw_diagnostic_payload_persisted
                ? "stored"
                : "omitted"}
            </dd>
          </div>
          <div>
            <dt>Raw path</dt>
            <dd>{lspDiagnostics.raw_path_persisted ? "stored" : "omitted"}</dd>
          </div>
          <div>
            <dt>Provider call</dt>
            <dd>
              {lspDiagnostics.provider_call_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Promotion</dt>
            <dd>
              {lspDiagnostics.allowlisted_server_required_for_promotion
                ? "allowlisted server required"
                : "not ready"}
            </dd>
          </div>
        </dl>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {lspDiagnostics.blocked_authority_refs.slice(0, 6).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Preview rail</p>
            <h3>Right rail posture</h3>
          </div>
          <span className="status-pill compact">{previewRail.status}</span>
        </div>
        <p>{previewRail.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{previewRail.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{previewRail.cli_ref}</dd>
          </div>
          <div>
            <dt>AuthorityState</dt>
            <dd>{previewRail.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability</dt>
            <dd>{previewRail.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>
              <span>{previewRail.authority_state_decision_outcome}</span>
              <br />
              <span>{previewRail.authority_state_decision_ref}</span>
            </dd>
          </div>
          <div>
            <dt>Reason</dt>
            <dd>{previewRail.authority_state_reason_refs[0] ?? "none"}</dd>
          </div>
          <div>
            <dt>Slots</dt>
            <dd>{previewRail.slot_count}</dd>
          </div>
          <div>
            <dt>Safe refs</dt>
            <dd>{previewRail.safe_ref_ready_count}</dd>
          </div>
          <div>
            <dt>Bounded placeholders</dt>
            <dd>{previewRail.bounded_preview_placeholder_count}</dd>
          </div>
          <div>
            <dt>Execution blocked</dt>
            <dd>{previewRail.execution_blocked_count}</dd>
          </div>
          <div>
            <dt>Browser automation</dt>
            <dd>
              {previewRail.browser_automation_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Screenshot capture</dt>
            <dd>
              {previewRail.screenshot_capture_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Slot</th>
                <th>Status</th>
                <th>Source</th>
                <th>Preview</th>
                <th>Proof</th>
              </tr>
            </thead>
            <tbody>
              {previewRail.slots.map((slot) => (
                <tr key={slot.slot_ref}>
                  <td>{slot.display_label}</td>
                  <td>{slot.slot_status}</td>
                  <td>{slot.source_classification_ref}</td>
                  <td>{slot.bounded_preview_ref}</td>
                  <td>{slot.proof_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Operator attach</dt>
            <dd>{previewRail.operator_attach_visible ? "planned" : "hidden"}</dd>
          </div>
          <div>
            <dt>Redaction</dt>
            <dd>
              {previewRail.redaction_policy_visible ? "visible" : "missing"}
            </dd>
          </div>
          <div>
            <dt>File read</dt>
            <dd>{previewRail.file_read_enabled ? "enabled" : "blocked"}</dd>
          </div>
          <div>
            <dt>Raw runtime payload</dt>
            <dd>
              {previewRail.raw_runtime_payload_persisted ? "stored" : "omitted"}
            </dd>
          </div>
        </dl>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {previewRail.blocked_authority_refs.slice(0, 6).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Slash commands</p>
            <h3>Governed registry</h3>
          </div>
          <span className="status-pill compact">
            {slashCommandRegistry.status}
          </span>
        </div>
        <p>{slashCommandRegistry.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{slashCommandRegistry.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{slashCommandRegistry.cli_ref}</dd>
          </div>
          <div>
            <dt>AuthorityState</dt>
            <dd>{slashCommandRegistry.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability</dt>
            <dd>{slashCommandRegistry.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>
              <span>
                {slashCommandRegistry.authority_state_decision_outcome}
              </span>
              <br />
              <span>{slashCommandRegistry.authority_state_decision_ref}</span>
            </dd>
          </div>
          <div>
            <dt>Reason</dt>
            <dd>
              {slashCommandRegistry.authority_state_reason_refs[0] ?? "none"}
            </dd>
          </div>
          <div>
            <dt>Commands</dt>
            <dd>{slashCommandRegistry.command_count}</dd>
          </div>
          <div>
            <dt>Metadata ready</dt>
            <dd>{slashCommandRegistry.metadata_ready_count}</dd>
          </div>
          <div>
            <dt>Disabled</dt>
            <dd>{slashCommandRegistry.disabled_count}</dd>
          </div>
          <div>
            <dt>Blocked</dt>
            <dd>{slashCommandRegistry.blocked_count}</dd>
          </div>
          <div>
            <dt>Chat execution</dt>
            <dd>
              {slashCommandRegistry.chat_trigger_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Runtime invocation</dt>
            <dd>
              {slashCommandRegistry.runtime_invocation_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Command</th>
                <th>Status</th>
                <th>Authority</th>
                <th>Side effect</th>
                <th>Receipt</th>
              </tr>
            </thead>
            <tbody>
              {slashCommandRegistry.commands.map((command) => (
                <tr key={command.command_ref}>
                  <td>
                    {command.trigger_label} {command.display_label}
                  </td>
                  <td>{command.command_status}</td>
                  <td>{command.authority_class}</td>
                  <td>{command.side_effect_class}</td>
                  <td>{command.receipt_plan_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Approval policy</dt>
            <dd>
              {slashCommandRegistry.approval_policy_visible
                ? "visible"
                : "missing"}
            </dd>
          </div>
          <div>
            <dt>Idempotency</dt>
            <dd>
              {slashCommandRegistry.idempotency_policy_visible
                ? "visible"
                : "missing"}
            </dd>
          </div>
          <div>
            <dt>State mutation</dt>
            <dd>
              {slashCommandRegistry.state_mutation_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Raw prompt</dt>
            <dd>
              {slashCommandRegistry.raw_prompt_persisted ? "stored" : "omitted"}
            </dd>
          </div>
        </dl>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {slashCommandRegistry.blocked_authority_refs
            .slice(0, 6)
            .map((ref) => (
              <li key={ref}>{ref}</li>
            ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Run control</p>
            <h3>Interrupt and redirect</h3>
          </div>
          <span className="status-pill compact">
            {interruptRedirect.status}
          </span>
        </div>
        <p>{interruptRedirect.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{interruptRedirect.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{interruptRedirect.cli_ref}</dd>
          </div>
          <div>
            <dt>Actions</dt>
            <dd>{interruptRedirect.proposal_count}</dd>
          </div>
          <div>
            <dt>Proposal only</dt>
            <dd>{interruptRedirect.read_only_proposal_count}</dd>
          </div>
          <div>
            <dt>Future approval</dt>
            <dd>{interruptRedirect.approval_required_future_lane_count}</dd>
          </div>
          <div>
            <dt>Blocked</dt>
            <dd>{interruptRedirect.blocked_count}</dd>
          </div>
          <div>
            <dt>Live stop</dt>
            <dd>
              {interruptRedirect.live_stop_post_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Process kill</dt>
            <dd>
              {interruptRedirect.process_kill_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Action</th>
                <th>Status</th>
                <th>Side effect</th>
                <th>Receipt</th>
                <th>Recovery</th>
              </tr>
            </thead>
            <tbody>
              {interruptRedirect.proposals.map((proposal) => (
                <tr key={proposal.action_ref}>
                  <td>{proposal.display_label}</td>
                  <td>{proposal.action_status}</td>
                  <td>{proposal.side_effect_class}</td>
                  <td>{proposal.receipt_plan_ref}</td>
                  <td>{proposal.recovery_state_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Run ownership</dt>
            <dd>
              {interruptRedirect.run_ownership_visible ? "visible" : "missing"}
            </dd>
          </div>
          <div>
            <dt>Cancellation receipt</dt>
            <dd>
              {interruptRedirect.cancellation_receipt_visible
                ? "visible"
                : "missing"}
            </dd>
          </div>
          <div>
            <dt>Runtime mutation</dt>
            <dd>
              {interruptRedirect.runtime_mutation_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Raw runtime payload</dt>
            <dd>
              {interruptRedirect.raw_runtime_payload_persisted
                ? "stored"
                : "omitted"}
            </dd>
          </div>
        </dl>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {interruptRedirect.blocked_authority_refs.slice(0, 6).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Logging</p>
            <h3>Verbose detail posture</h3>
          </div>
          <span className="status-pill compact">{loggingProfile.status}</span>
        </div>
        <p>{loggingProfile.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{loggingProfile.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{loggingProfile.cli_ref}</dd>
          </div>
          <div>
            <dt>Authority</dt>
            <dd>{loggingProfile.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{loggingProfile.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>{loggingProfile.authority_state_decision_outcome}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{loggingProfile.authority_state_decision_ref}</dd>
          </div>
          <div>
            <dt>Active profile</dt>
            <dd>{loggingProfile.active_profile_ref}</dd>
          </div>
          <div>
            <dt>Profiles</dt>
            <dd>{loggingProfile.profile_count}</dd>
          </div>
          <div>
            <dt>Flagged profile</dt>
            <dd>{loggingProfile.disabled_until_flagged_count}</dd>
          </div>
          <div>
            <dt>Raw detail blocked</dt>
            <dd>{loggingProfile.blocked_raw_detail_count}</dd>
          </div>
          <div>
            <dt>Verbose enabled</dt>
            <dd>{loggingProfile.verbose_logging_enabled ? "enabled" : "disabled"}</dd>
          </div>
          <div>
            <dt>Remote telemetry</dt>
            <dd>
              {loggingProfile.remote_telemetry_export_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Profile</th>
                <th>Status</th>
                <th>Retention</th>
                <th>TTL</th>
                <th>Redaction</th>
              </tr>
            </thead>
            <tbody>
              {loggingProfile.profiles.map((profile) => (
                <tr key={profile.profile_ref}>
                  <td>{profile.display_label}</td>
                  <td>{profile.profile_status}</td>
                  <td>{profile.retention_class}</td>
                  <td>{profile.ttl_policy_ref}</td>
                  <td>{profile.redaction_verifier_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Flag scope</dt>
            <dd>{loggingProfile.flag_scope_visible ? "visible" : "missing"}</dd>
          </div>
          <div>
            <dt>Safe disable</dt>
            <dd>{loggingProfile.safe_disable_visible ? "visible" : "missing"}</dd>
          </div>
          <div>
            <dt>Raw logs</dt>
            <dd>{loggingProfile.raw_logs_persisted ? "stored" : "omitted"}</dd>
          </div>
          <div>
            <dt>Provider payload</dt>
            <dd>
              {loggingProfile.provider_payload_persisted ? "stored" : "omitted"}
            </dd>
          </div>
        </dl>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {loggingProfile.blocked_authority_refs.slice(0, 6).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
        <h4>Authority reason</h4>
        <ul className="compact-list">
          {loggingProfile.authority_state_reason_refs.map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Result labels</p>
            <h3>Tool result classification</h3>
          </div>
          <span className="status-pill compact">
            {resultClassification.status}
          </span>
        </div>
        <p>{resultClassification.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{resultClassification.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{resultClassification.cli_ref}</dd>
          </div>
          <div>
            <dt>Authority</dt>
            <dd>{resultClassification.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{resultClassification.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>{resultClassification.authority_state_decision_outcome}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{resultClassification.authority_state_decision_ref}</dd>
          </div>
          <div>
            <dt>Classes</dt>
            <dd>{resultClassification.classification_count}</dd>
          </div>
          <div>
            <dt>Evidence</dt>
            <dd>{resultClassification.evidence_count}</dd>
          </div>
          <div>
            <dt>Mutation</dt>
            <dd>{resultClassification.mutation_count}</dd>
          </div>
          <div>
            <dt>Untrusted</dt>
            <dd>{resultClassification.untrusted_data_count}</dd>
          </div>
          <div>
            <dt>Output as truth</dt>
            <dd>
              {resultClassification.tool_output_as_truth_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Action authority</dt>
            <dd>
              {resultClassification.action_authority_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Class</th>
                <th>Status</th>
                <th>Provenance</th>
                <th>Receipt</th>
                <th>Proof</th>
              </tr>
            </thead>
            <tbody>
              {resultClassification.classifications.map((item) => (
                <tr key={item.classification_ref}>
                  <td>{item.display_label}</td>
                  <td>{item.verification_status}</td>
                  <td>{item.provenance_policy_ref}</td>
                  <td>{item.receipt_requirement_ref}</td>
                  <td>{item.proof_binding_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Labels</dt>
            <dd>{resultClassification.labels_visible ? "visible" : "missing"}</dd>
          </div>
          <div>
            <dt>Proof binding</dt>
            <dd>
              {resultClassification.proof_binding_visible
                ? "visible"
                : "missing"}
            </dd>
          </div>
          <div>
            <dt>Raw output</dt>
            <dd>
              {resultClassification.raw_output_persisted ? "stored" : "omitted"}
            </dd>
          </div>
          <div>
            <dt>Provider payload</dt>
            <dd>
              {resultClassification.provider_payload_persisted
                ? "stored"
                : "omitted"}
            </dd>
          </div>
        </dl>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {resultClassification.blocked_authority_refs
            .slice(0, 6)
            .map((ref) => (
              <li key={ref}>{ref}</li>
            ))}
        </ul>
        <h4>Authority reason</h4>
        <ul className="compact-list">
          {resultClassification.authority_state_reason_refs.map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Command floor</p>
            <h3>Hardline blocklist</h3>
          </div>
          <span className="status-pill compact">
            {hardlineCommandBlocklist.non_overridable_floor
              ? "non-overridable"
              : "blocked"}
          </span>
        </div>
        <p>{hardlineCommandBlocklist.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{hardlineCommandBlocklist.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{hardlineCommandBlocklist.cli_ref}</dd>
          </div>
          <div>
            <dt>Classifications</dt>
            <dd>{hardlineCommandBlocklist.classification_count}</dd>
          </div>
          <div>
            <dt>Denied</dt>
            <dd>{hardlineCommandBlocklist.denied_classification_count}</dd>
          </div>
          <div>
            <dt>Allowed</dt>
            <dd>{hardlineCommandBlocklist.allowed_classification_count}</dd>
          </div>
          <div>
            <dt>Override bypass</dt>
            <dd>
              {hardlineCommandBlocklist.override_bypass_permitted
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Candidate</th>
                <th>Status</th>
                <th>Category</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {hardlineCommandBlocklist.classifications
                .slice(0, 8)
                .map((classification) => (
                  <tr key={classification.candidate_ref}>
                    <td>{classification.candidate_ref}</td>
                    <td>{classification.status}</td>
                    <td>{classification.denial_category}</td>
                    <td>{classification.denial_reason_ref}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Foundation gate</dt>
            <dd>{hardlineCommandBlocklist.foundation_gate_ref}</dd>
          </div>
          <div>
            <dt>Blocked authority</dt>
            <dd>
              <ul className="compact-list">
                {hardlineCommandBlocklist.blocked_authority_refs
                  .slice(0, 4)
                  .map((ref) => (
                    <li key={ref}>{ref}</li>
                  ))}
              </ul>
            </dd>
          </div>
        </dl>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Prompt stability</p>
            <h3>Tier contract posture</h3>
          </div>
          <span className="status-pill compact">
            {promptStabilityTiers.status}
          </span>
        </div>
        <p>{promptStabilityTiers.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{promptStabilityTiers.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{promptStabilityTiers.cli_ref}</dd>
          </div>
          <div>
            <dt>Tiers</dt>
            <dd>{promptStabilityTiers.tier_count}</dd>
          </div>
          <div>
            <dt>Cache candidates</dt>
            <dd>{promptStabilityTiers.stable_cache_candidate_count}</dd>
          </div>
          <div>
            <dt>Raw prompts</dt>
            <dd>
              {promptStabilityTiers.raw_prompt_persistence_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Hidden injection</dt>
            <dd>
              {promptStabilityTiers.hidden_prompt_injection_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Model calls</dt>
            <dd>
              {promptStabilityTiers.model_call_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Cache writes</dt>
            <dd>
              {promptStabilityTiers.cache_write_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Tier</th>
                <th>Kind</th>
                <th>Stability</th>
                <th>Manifest</th>
                <th>Hash</th>
              </tr>
            </thead>
            <tbody>
              {promptStabilityTiers.tiers.map((tier) => (
                <tr key={tier.tier_ref}>
                  <td>{tier.display_label}</td>
                  <td>{tier.tier_kind}</td>
                  <td>{tier.stability_class}</td>
                  <td>{tier.manifest_ref}</td>
                  <td>{tier.tier_hash_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Proof</dt>
            <dd>
              <ul className="compact-list">
                {promptStabilityTiers.proof_refs.slice(0, 3).map((ref) => (
                  <li key={ref}>{ref}</li>
                ))}
              </ul>
            </dd>
          </div>
          <div>
            <dt>Blocked authority</dt>
            <dd>
              <ul className="compact-list">
                {promptStabilityTiers.blocked_authority_refs
                  .slice(0, 4)
                  .map((ref) => (
                    <li key={ref}>{ref}</li>
                  ))}
              </ul>
            </dd>
          </div>
        </dl>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Context budget</p>
            <h3>Pressure posture</h3>
          </div>
          <span className="status-pill compact">
            {contextBudgetPressure.pressure_level}
          </span>
        </div>
        <p>{contextBudgetPressure.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{contextBudgetPressure.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{contextBudgetPressure.cli_ref}</dd>
          </div>
          <div>
            <dt>Budget units</dt>
            <dd>
              {contextBudgetPressure.estimated_token_count} /{" "}
              {contextBudgetPressure.token_budget_limit}
            </dd>
          </div>
          <div>
            <dt>Remaining</dt>
            <dd>{contextBudgetPressure.token_budget_remaining}</dd>
          </div>
          <div>
            <dt>Warnings</dt>
            <dd>{contextBudgetPressure.warning_count}</dd>
          </div>
          <div>
            <dt>Critical</dt>
            <dd>{contextBudgetPressure.critical_count}</dd>
          </div>
          <div>
            <dt>Proposals</dt>
            <dd>{contextBudgetPressure.proposal_count}</dd>
          </div>
          <div>
            <dt>Hidden compression</dt>
            <dd>{contextBudgetPressure.blocked_hidden_compression_label}</dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Segment</th>
                <th>Pressure</th>
                <th>Units</th>
                <th>Proposal refs</th>
              </tr>
            </thead>
            <tbody>
              {contextBudgetPressure.segments.map((segment) => (
                <tr key={segment.segment_ref}>
                  <td>{segment.display_label}</td>
                  <td>{segment.pressure_level}</td>
                  <td>
                    {segment.token_estimate} / {segment.token_budget_limit}
                  </td>
                  <td>{segment.proposal_refs.length}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Proposal</th>
                <th>Kind</th>
                <th>Delta</th>
                <th>Approval</th>
              </tr>
            </thead>
            <tbody>
              {contextBudgetPressure.proposals.map((proposal) => (
                <tr key={proposal.proposal_ref}>
                  <td>{proposal.display_label}</td>
                  <td>{proposal.proposal_kind}</td>
                  <td>{proposal.expected_token_delta}</td>
                  <td>{proposal.approval_required ? "required" : "blocked"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Proof</dt>
            <dd>
              <ul className="compact-list">
                {contextBudgetPressure.proof_refs.slice(0, 3).map((ref) => (
                  <li key={ref}>{ref}</li>
                ))}
              </ul>
            </dd>
          </div>
          <div>
            <dt>Blocked authority</dt>
            <dd>
              <ul className="compact-list">
                {contextBudgetPressure.blocked_authority_refs
                  .slice(0, 4)
                  .map((ref) => (
                    <li key={ref}>{ref}</li>
                  ))}
              </ul>
            </dd>
          </div>
        </dl>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Usage and cost</p>
            <h3>Redacted accounting posture</h3>
          </div>
          <span className="status-pill compact">
            {usageCostAnalytics.status}
          </span>
        </div>
        <p>{usageCostAnalytics.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{usageCostAnalytics.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{usageCostAnalytics.cli_ref}</dd>
          </div>
          <div>
            <dt>Records</dt>
            <dd>{usageCostAnalytics.record_count}</dd>
          </div>
          <div>
            <dt>Usage units</dt>
            <dd>{usageCostAnalytics.total_estimated_tokens}</dd>
          </div>
          <div>
            <dt>Minor cost units</dt>
            <dd>{usageCostAnalytics.total_estimated_cost_minor_units}</dd>
          </div>
          <div>
            <dt>Billing action</dt>
            <dd>
              {usageCostAnalytics.billing_action_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Provider calls</dt>
            <dd>
              {usageCostAnalytics.provider_call_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Operator export</dt>
            <dd>
              {usageCostAnalytics.operator_export_available
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Record</th>
                <th>Source</th>
                <th>Status</th>
                <th>Runtime</th>
                <th>Usage</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {usageCostAnalytics.records.map((record) => (
                <tr key={record.record_ref}>
                  <td>{record.display_label}</td>
                  <td>{record.source_kind}</td>
                  <td>{record.status}</td>
                  <td>{record.runtime_ref}</td>
                  <td>{record.estimated_total_tokens}</td>
                  <td>{record.estimated_cost_minor_units}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Proof</dt>
            <dd>
              <ul className="compact-list">
                {usageCostAnalytics.proof_refs.slice(0, 3).map((ref) => (
                  <li key={ref}>{ref}</li>
                ))}
              </ul>
            </dd>
          </div>
          <div>
            <dt>Blocked authority</dt>
            <dd>
              <ul className="compact-list">
                {usageCostAnalytics.blocked_authority_refs
                  .slice(0, 4)
                  .map((ref) => (
                    <li key={ref}>{ref}</li>
                  ))}
              </ul>
            </dd>
          </div>
        </dl>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Virtual provider</p>
            <h3>Multi-agent preset posture</h3>
          </div>
          <span className="status-pill compact">
            {virtualProviderMoa.status}
          </span>
        </div>
        <p>{virtualProviderMoa.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{virtualProviderMoa.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{virtualProviderMoa.cli_ref}</dd>
          </div>
          <div>
            <dt>Presets</dt>
            <dd>{virtualProviderMoa.preset_count}</dd>
          </div>
          <div>
            <dt>Agent slots</dt>
            <dd>{virtualProviderMoa.agent_slot_count}</dd>
          </div>
          <div>
            <dt>Live fan-out</dt>
            <dd>
              {virtualProviderMoa.live_model_fanout_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Provider SDK</dt>
            <dd>
              {virtualProviderMoa.provider_sdk_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Preset</th>
                <th>Status</th>
                <th>Slots</th>
                <th>Trace</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {virtualProviderMoa.presets.map((preset) => (
                <tr key={preset.preset_ref}>
                  <td>{preset.display_label}</td>
                  <td>{preset.status}</td>
                  <td>{preset.slot_count}</td>
                  <td>{preset.route_decision_trace_ref}</td>
                  <td>{preset.cost_estimate_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h4>Agent slots</h4>
        <ul className="compact-list">
          {virtualProviderMoa.presets.flatMap((preset) =>
            preset.slots.map((slot) => (
              <li key={slot.slot_ref}>
                {slot.display_label}: {slot.role}; output{" "}
                {slot.output_authoritative ? "authoritative" : "proposal only"}
              </li>
            )),
          )}
        </ul>
        <dl className="detail-grid">
          <div>
            <dt>Proof</dt>
            <dd>
              <ul className="compact-list">
                {virtualProviderMoa.proof_refs.slice(0, 3).map((ref) => (
                  <li key={ref}>{ref}</li>
                ))}
              </ul>
            </dd>
          </div>
          <div>
            <dt>Blocked authority</dt>
            <dd>
              <ul className="compact-list">
                {virtualProviderMoa.blocked_authority_refs
                  .slice(0, 4)
                  .map((ref) => (
                    <li key={ref}>{ref}</li>
                  ))}
              </ul>
            </dd>
          </div>
        </dl>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Tool registry</p>
            <h3>Availability and authority</h3>
          </div>
          <span className="status-pill compact">{toolRegistry.status}</span>
        </div>
        <p>{toolRegistry.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{toolRegistry.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{toolRegistry.cli_ref}</dd>
          </div>
          <div>
            <dt>Tools</dt>
            <dd>{toolRegistry.tool_count}</dd>
          </div>
          <div>
            <dt>Preview available</dt>
            <dd>{toolRegistry.preview_available_count}</dd>
          </div>
          <div>
            <dt>Invocation enabled</dt>
            <dd>{toolRegistry.tool_invocation_enabled ? "enabled" : "blocked"}</dd>
          </div>
          <div>
            <dt>Remote discovery</dt>
            <dd>{toolRegistry.remote_discovery_enabled ? "enabled" : "blocked"}</dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Tool</th>
                <th>Origin</th>
                <th>Availability</th>
                <th>Authority</th>
                <th>Risk</th>
              </tr>
            </thead>
            <tbody>
              {toolRegistry.entries.map((entry) => (
                <tr key={entry.tool_ref}>
                  <td>{entry.display_label}</td>
                  <td>{entry.origin}</td>
                  <td>{entry.availability_status}</td>
                  <td>{entry.authority_class}</td>
                  <td>{entry.risk_class}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Proof</dt>
            <dd>
              <ul className="compact-list">
                {toolRegistry.proof_refs.slice(0, 3).map((ref) => (
                  <li key={ref}>{ref}</li>
                ))}
              </ul>
            </dd>
          </div>
          <div>
            <dt>Blocked authority</dt>
            <dd>
              <ul className="compact-list">
                {toolRegistry.blocked_authority_refs.slice(0, 3).map((ref) => (
                  <li key={ref}>{ref}</li>
                ))}
              </ul>
            </dd>
          </div>
        </dl>
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
            <dd>
              {approvalBridge.timeout_preview_count} default-deny preview;{" "}
              {approvalBridge.fail_closed_timeout_posture.status}
            </dd>
          </div>
          <div>
            <dt>Ambiguous waits</dt>
            <dd>
              {approvalBridge.fail_closed_timeout_posture
                .ambiguous_waits_default_to_deny
                ? "default deny"
                : "unsafe"}
            </dd>
          </div>
          <div>
            <dt>Approve all</dt>
            <dd>
              {approvalBridge.fail_closed_timeout_posture.approve_all_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Standing authority</dt>
            <dd>
              {approvalBridge.fail_closed_timeout_posture
                .standing_broad_authority_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Expired grants</dt>
            <dd>
              {approvalBridge.fail_closed_timeout_posture
                .expired_grant_reuse_enabled
                ? "reused"
                : "not reused"}
            </dd>
          </div>
          <div>
            <dt>Scope validation</dt>
            <dd>{approvalBridge.scope_validation.status}</dd>
          </div>
        </dl>
        <p>{approvalBridge.fail_closed_timeout_posture.safe_summary}</p>
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
