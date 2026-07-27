import { type FormEvent, useEffect, useRef, useState } from "react";
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
  RuntimeMessagingGatewayPostureReadModel,
  RuntimeMcpCatalogFilteringReadModel,
  RuntimePluginMetadataPostureReadModel,
  RuntimeSkillMarketplacePostureReadModel,
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
  RuntimeRemoteExecutionPostureReadModel,
  RuntimeResultClassificationReadModel,
  RuntimeSlashCommandRegistryReadModel,
  RuntimeUsageCostAnalyticsReadModel,
  RuntimeVirtualProviderMoaReadModel,
  RuntimeVoiceMediaPostureReadModel,
  RuntimeWorktreePerAgentReadModel,
  RuntimeGoalTransitionKind,
} from "../api/types";
import {
  createRuntimeGoal,
  editRuntimeGoal,
  fetchRuntimeRunEvents,
  transitionRuntimeGoal,
} from "../api/client";
import { useBackendTruthMutationBinding } from "../backendTruthMutationBinding";
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
  voiceMediaPosture,
  messagingGatewayPosture,
  remoteExecutionPosture,
  pluginMetadataPosture,
  skillMarketplacePosture,
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
  voiceMediaPosture: RuntimeVoiceMediaPostureReadModel;
  messagingGatewayPosture: RuntimeMessagingGatewayPostureReadModel;
  remoteExecutionPosture: RuntimeRemoteExecutionPostureReadModel;
  pluginMetadataPosture: RuntimePluginMetadataPostureReadModel;
  skillMarketplacePosture: RuntimeSkillMarketplacePostureReadModel;
}) {
  const mutationBinding = useBackendTruthMutationBinding();
  const [runtimeGoalEvents, setRuntimeGoalEvents] = useState(runEvents);
  const [goalObjective, setGoalObjective] = useState("");
  const [goalOutcome, setGoalOutcome] = useState("");
  const [goalSuccessCriterion, setGoalSuccessCriterion] = useState("");
  const [goalStopCondition, setGoalStopCondition] = useState("");
  const [selectedGoalRef, setSelectedGoalRef] = useState(
    runEvents.goal_lifecycle.goals[0]?.goal_ref ?? "",
  );
  const [editedObjective, setEditedObjective] = useState("");
  const [goalMutationBusy, setGoalMutationBusy] = useState(false);
  const pendingGoalCreateIdempotencyRef = useRef<string | null>(null);
  const [goalNotice, setGoalNotice] = useState(
    "Goal mutations require the exact local backend and a current truth binding.",
  );
  useEffect(() => {
    setRuntimeGoalEvents(runEvents);
    const firstGoalRef = runEvents.goal_lifecycle.goals[0]?.goal_ref ?? "";
    setSelectedGoalRef((current) =>
      runEvents.goal_lifecycle.goals.some(
        (goal) => goal.goal_ref === current,
      )
        ? current
        : firstGoalRef,
    );
  }, [runEvents]);
  const selectedGoal = runtimeGoalEvents.goal_lifecycle.goals.find(
    (goal) => goal.goal_ref === selectedGoalRef,
  );
  const availableGoalTransitions: RuntimeGoalTransitionKind[] =
    selectedGoal === undefined
      ? []
      : selectedGoal.state === "active"
        ? ["pause", "block", "wait", "request_completion", "cancel", "clear"]
        : selectedGoal.state === "paused"
          ? ["resume", "cancel", "clear"]
          : selectedGoal.state === "blocked"
            ? ["resume", "wait", "cancel", "clear"]
            : selectedGoal.state === "waiting"
              ? ["resume", "block", "cancel", "clear"]
              : selectedGoal.state === "complete_requested"
                ? ["resume", "block", "cancel", "clear"]
                : selectedGoal.state === "verified_complete" ||
                    selectedGoal.state === "cancelled"
                  ? ["clear"]
                  : selectedGoal.state === "cleared"
                    ? ["restore"]
                  : [];

  async function refreshGoalState() {
    setRuntimeGoalEvents(await fetchRuntimeRunEvents());
  }

  async function createGoal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (mutationBinding === null) {
      setGoalNotice("Goal creation is blocked until backend truth is current.");
      return;
    }
    const idempotencyRef =
      pendingGoalCreateIdempotencyRef.current ??
      `idempotency-ref:control-center-goal-create:${Date.now()}`;
    pendingGoalCreateIdempotencyRef.current = idempotencyRef;
    setGoalMutationBusy(true);
    try {
      const result = await createRuntimeGoal(
        {
          objective: goalObjective,
          desired_outcome: goalOutcome,
          success_criteria: [goalSuccessCriterion],
          constraints: [
            "No external execution, standing authority, or unverified completion.",
          ],
          in_scope_resource_refs: [],
          stop_condition: goalStopCondition,
          budget: {
            operation_limit: 25,
            cost_budget_microusd: 0,
          },
          links: {
            plan_refs: [],
            run_refs: [],
            action_inbox_refs: [],
            work_board_refs: [],
          },
          evidence_refs: [],
        },
        idempotencyRef,
        mutationBinding,
      );
      try {
        await refreshGoalState();
      } catch {
        setSelectedGoalRef(result.goal.goal_ref);
        setGoalNotice(
          "Goal creation was accepted, but the authoritative refresh failed. " +
            "Retrying this form will replay the same idempotency ref.",
        );
        return;
      }
      pendingGoalCreateIdempotencyRef.current = null;
      setSelectedGoalRef(result.goal.goal_ref);
      setGoalObjective("");
      setGoalOutcome("");
      setGoalSuccessCriterion("");
      setGoalStopCondition("");
      setGoalNotice(
        `Goal created at version ${result.goal.version}; no runtime work was started.`,
      );
    } catch (error) {
      setGoalNotice(
        error instanceof Error
          ? error.message
          : "Goal creation failed safely.",
      );
    } finally {
      setGoalMutationBusy(false);
    }
  }

  async function saveGoalObjective() {
    if (mutationBinding === null || selectedGoal === undefined) {
      setGoalNotice("Goal editing is blocked until backend truth is current.");
      return;
    }
    const nonce = Date.now();
    setGoalMutationBusy(true);
    try {
      const result = await editRuntimeGoal(
        selectedGoal.goal_ref,
        {
          expected_version: selectedGoal.version,
          objective: editedObjective,
          evidence_refs: [
            `evidence-ref:control-center-goal-edit:${nonce}`,
          ],
        },
        `idempotency-ref:control-center-goal-edit:${nonce}`,
        mutationBinding,
      );
      await refreshGoalState();
      setEditedObjective("");
      setGoalNotice(`Goal objective saved at version ${result.goal.version}.`);
    } catch (error) {
      setGoalNotice(
        error instanceof Error ? error.message : "Goal edit failed safely.",
      );
    } finally {
      setGoalMutationBusy(false);
    }
  }

  async function transitionGoal(transition: RuntimeGoalTransitionKind) {
    if (mutationBinding === null || selectedGoal === undefined) {
      setGoalNotice(
        "Goal transition is blocked until backend truth is current.",
      );
      return;
    }
    const nonce = Date.now();
    setGoalMutationBusy(true);
    try {
      const result = await transitionRuntimeGoal(
        selectedGoal.goal_ref,
        {
          expected_version: selectedGoal.version,
          transition,
          reason_ref: `reason-ref:control-center-goal-${transition}:${nonce}`,
          evidence_refs: [
            `evidence-ref:control-center-goal-${transition}:${nonce}`,
          ],
        },
        `idempotency-ref:control-center-goal-${transition}:${nonce}`,
        mutationBinding,
      );
      await refreshGoalState();
      setGoalNotice(
        `Goal moved to ${result.goal.state} at version ${result.goal.version}.`,
      );
    } catch (error) {
      setGoalNotice(
        error instanceof Error
          ? error.message
          : "Goal transition failed safely.",
      );
    } finally {
      setGoalMutationBusy(false);
    }
  }

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
            <dt>Authority state</dt>
            <dd>{capabilityDiscovery.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Authority mapping</dt>
            <dd>{capabilityDiscovery.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>{capabilityDiscovery.authority_state_decision_outcome}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{capabilityDiscovery.authority_state_decision_ref}</dd>
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
        <dl className="detail-grid">
          <div>
            <dt>Unsupported adapters</dt>
            <dd>
              <ul className="compact-list">
                {capabilityDiscovery.unsupported_adapter_refs
                  .slice(0, 4)
                  .map((ref) => (
                    <li key={ref}>{ref}</li>
                  ))}
              </ul>
            </dd>
          </div>
          <div>
            <dt>Authority reason</dt>
            <dd>
              <ul className="compact-list">
                {capabilityDiscovery.authority_state_reason_refs.map((ref) => (
                  <li key={ref}>{ref}</li>
                ))}
              </ul>
            </dd>
          </div>
        </dl>
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
            <p className="eyebrow">Skill marketplace</p>
            <h3>Signal review posture</h3>
          </div>
          <span className="status-pill compact">
            {skillMarketplacePosture.status}
          </span>
        </div>
        <p>{skillMarketplacePosture.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{skillMarketplacePosture.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{skillMarketplacePosture.cli_ref}</dd>
          </div>
          <div>
            <dt>Authority</dt>
            <dd>{skillMarketplacePosture.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{skillMarketplacePosture.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>{skillMarketplacePosture.authority_state_decision_outcome}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{skillMarketplacePosture.authority_state_decision_ref}</dd>
          </div>
          <div>
            <dt>Catalog freshness</dt>
            <dd>{skillMarketplacePosture.catalog_freshness.status}</dd>
          </div>
          <div>
            <dt>Catalog display</dt>
            <dd>{skillMarketplacePosture.catalog_freshness.display_status}</dd>
          </div>
          <div>
            <dt>Freshness checked</dt>
            <dd>{skillMarketplacePosture.catalog_freshness.checked_at}</dd>
          </div>
          <div>
            <dt>Freshness expires</dt>
            <dd>{skillMarketplacePosture.catalog_freshness.expires_at}</dd>
          </div>
          <div>
            <dt>Stages</dt>
            <dd>{skillMarketplacePosture.stage_count}</dd>
          </div>
          <div>
            <dt>Review required</dt>
            <dd>{skillMarketplacePosture.review_required_count}</dd>
          </div>
          <div>
            <dt>Execution blocks</dt>
            <dd>{skillMarketplacePosture.blocked_execution_count}</dd>
          </div>
          <div>
            <dt>Popularity as trust</dt>
            <dd>
              {skillMarketplacePosture.external_popularity_is_trust
                ? "trusted"
                : "not trust"}
            </dd>
          </div>
          <div>
            <dt>External code</dt>
            <dd>
              {skillMarketplacePosture.external_code_execution_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Install/import</dt>
            <dd>
              {skillMarketplacePosture.direct_marketplace_install_enabled ||
              skillMarketplacePosture.runtime_import_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Provider/browser</dt>
            <dd>
              {skillMarketplacePosture.provider_call_enabled ||
              skillMarketplacePosture.browser_automation_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Raw marketplace</dt>
            <dd>
              {skillMarketplacePosture.raw_marketplace_payload_persisted
                ? "stored"
                : "omitted"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Stage</th>
                <th>Status</th>
                <th>Signal</th>
                <th>Review</th>
                <th>Adaptation</th>
                <th>Receipt</th>
              </tr>
            </thead>
            <tbody>
              {skillMarketplacePosture.stages.map((stage) => (
                <tr key={stage.stage_ref}>
                  <td>{stage.display_label}</td>
                  <td>{stage.status}</td>
                  <td>{stage.signal_policy_ref}</td>
                  <td>{stage.review_ref}</td>
                  <td>{stage.adaptation_ref}</td>
                  <td>{stage.receipt_plan_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h4>Unsupported adapters</h4>
        <ul className="compact-list">
          {skillMarketplacePosture.unsupported_adapter_refs
            .slice(0, 6)
            .map((ref) => (
              <li key={ref}>{ref}</li>
            ))}
        </ul>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {skillMarketplacePosture.blocked_authority_refs
            .slice(0, 6)
            .map((ref) => (
              <li key={ref}>{ref}</li>
            ))}
        </ul>
        <h4>Authority reason</h4>
        <ul className="compact-list">
          {skillMarketplacePosture.authority_state_reason_refs.map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
        <h4>Catalog freshness reason</h4>
        <ul className="compact-list">
          {skillMarketplacePosture.catalog_freshness.reason_refs.map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
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
            <p className="eyebrow">Remote execution</p>
            <h3>Posture inspection</h3>
          </div>
          <span className="status-pill compact">
            {remoteExecutionPosture.status}
          </span>
        </div>
        <p>{remoteExecutionPosture.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{remoteExecutionPosture.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{remoteExecutionPosture.cli_ref}</dd>
          </div>
          <div>
            <dt>Authority</dt>
            <dd>{remoteExecutionPosture.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{remoteExecutionPosture.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>{remoteExecutionPosture.authority_state_decision_outcome}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{remoteExecutionPosture.authority_state_decision_ref}</dd>
          </div>
          <div>
            <dt>Backends</dt>
            <dd>{remoteExecutionPosture.backend_count}</dd>
          </div>
          <div>
            <dt>Blocked backends</dt>
            <dd>{remoteExecutionPosture.blocked_backend_count}</dd>
          </div>
          <div>
            <dt>Remote execution</dt>
            <dd>
              {remoteExecutionPosture.remote_execution_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Host/cloud access</dt>
            <dd>
              {remoteExecutionPosture.ssh_enabled ||
              remoteExecutionPosture.cloud_sandbox_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>File sync</dt>
            <dd>
              {remoteExecutionPosture.file_sync_enabled ? "enabled" : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Credential material</dt>
            <dd>
              {remoteExecutionPosture.credential_material_persisted
                ? "stored"
                : "omitted"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Backend</th>
                <th>Status</th>
                <th>Boundary</th>
                <th>Network</th>
                <th>Receipt</th>
                <th>Kill switch</th>
              </tr>
            </thead>
            <tbody>
              {remoteExecutionPosture.backends.map((backend) => (
                <tr key={backend.backend_ref}>
                  <td>{backend.display_label}</td>
                  <td>{backend.status}</td>
                  <td>{backend.workspace_boundary_ref}</td>
                  <td>{backend.network_policy_ref}</td>
                  <td>{backend.receipt_plan_ref}</td>
                  <td>{backend.kill_switch_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h4>Unsupported adapters</h4>
        <ul className="compact-list">
          {remoteExecutionPosture.unsupported_adapter_refs
            .slice(0, 6)
            .map((ref) => (
              <li key={ref}>{ref}</li>
            ))}
        </ul>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {remoteExecutionPosture.blocked_authority_refs
            .slice(0, 6)
            .map((ref) => (
              <li key={ref}>{ref}</li>
            ))}
        </ul>
        <h4>Authority reason</h4>
        <ul className="compact-list">
          {remoteExecutionPosture.authority_state_reason_refs.map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Plugin metadata</p>
            <h3>Posture inspection</h3>
          </div>
          <span className="status-pill compact">
            {pluginMetadataPosture.status}
          </span>
        </div>
        <p>{pluginMetadataPosture.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{pluginMetadataPosture.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{pluginMetadataPosture.cli_ref}</dd>
          </div>
          <div>
            <dt>Authority</dt>
            <dd>{pluginMetadataPosture.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{pluginMetadataPosture.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>{pluginMetadataPosture.authority_state_decision_outcome}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{pluginMetadataPosture.authority_state_decision_ref}</dd>
          </div>
          <div>
            <dt>Surfaces</dt>
            <dd>{pluginMetadataPosture.surface_count}</dd>
          </div>
          <div>
            <dt>Blocked surfaces</dt>
            <dd>{pluginMetadataPosture.blocked_surface_count}</dd>
          </div>
          <div>
            <dt>Runtime imports</dt>
            <dd>
              {pluginMetadataPosture.runtime_import_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Installs/hooks</dt>
            <dd>
              {pluginMetadataPosture.package_install_enabled ||
              pluginMetadataPosture.hook_execution_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Connector/provider</dt>
            <dd>
              {pluginMetadataPosture.connector_write_enabled ||
              pluginMetadataPosture.provider_call_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Raw manifest</dt>
            <dd>
              {pluginMetadataPosture.raw_manifest_persisted
                ? "stored"
                : "omitted"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Surface</th>
                <th>Status</th>
                <th>Manifest</th>
                <th>Static scan</th>
                <th>Activation</th>
                <th>Receipt</th>
              </tr>
            </thead>
            <tbody>
              {pluginMetadataPosture.surfaces.map((surface) => (
                <tr key={surface.surface_ref}>
                  <td>{surface.display_label}</td>
                  <td>{surface.status}</td>
                  <td>{surface.reviewed_manifest_ref}</td>
                  <td>{surface.static_scan_ref}</td>
                  <td>{surface.activation_grant_ref}</td>
                  <td>{surface.receipt_plan_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h4>Unsupported adapters</h4>
        <ul className="compact-list">
          {pluginMetadataPosture.unsupported_adapter_refs
            .slice(0, 6)
            .map((ref) => (
              <li key={ref}>{ref}</li>
            ))}
        </ul>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {pluginMetadataPosture.blocked_authority_refs
            .slice(0, 6)
            .map((ref) => (
              <li key={ref}>{ref}</li>
            ))}
        </ul>
        <h4>Authority reason</h4>
        <ul className="compact-list">
          {pluginMetadataPosture.authority_state_reason_refs.map((ref) => (
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
            <dt>Authority</dt>
            <dd>
              {managedScopePolicy.authority_state_decision_outcome} /{" "}
              {managedScopePolicy.authority_state_status}
            </dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{managedScopePolicy.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{managedScopePolicy.authority_state_decision_ref}</dd>
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
        <h4>Unsupported adapters</h4>
        <ul className="compact-list">
          {managedScopePolicy.unsupported_adapter_refs.slice(0, 6).map((ref) => (
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
            <dt>Authority</dt>
            <dd>
              {doctorDiagnostics.authority_state_decision_outcome} /{" "}
              {doctorDiagnostics.authority_state_status}
            </dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{doctorDiagnostics.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{doctorDiagnostics.authority_state_decision_ref}</dd>
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
        <h4>Unsupported adapters</h4>
        <ul className="compact-list">
          {doctorDiagnostics.unsupported_adapter_refs.slice(0, 6).map((ref) => (
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
            <dt>Authority</dt>
            <dd>
              {sessionContinuity.authority_state_decision_outcome} /{" "}
              {sessionContinuity.authority_state_status}
            </dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{sessionContinuity.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{sessionContinuity.authority_state_decision_ref}</dd>
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
        <h4>Unsupported adapters</h4>
        <ul className="compact-list">
          {sessionContinuity.unsupported_adapter_refs.slice(0, 6).map((ref) => (
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
            <dt>Authority</dt>
            <dd>
              {mcpCatalogFiltering.authority_state_decision_outcome} /{" "}
              {mcpCatalogFiltering.authority_state_status}
            </dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{mcpCatalogFiltering.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{mcpCatalogFiltering.authority_state_decision_ref}</dd>
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
        <h4>Unsupported adapters</h4>
        <ul className="compact-list">
          {mcpCatalogFiltering.unsupported_adapter_refs.slice(0, 6).map((ref) => (
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
            <dt>Authority</dt>
            <dd>{interruptRedirect.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{interruptRedirect.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>{interruptRedirect.authority_state_decision_outcome}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{interruptRedirect.authority_state_decision_ref}</dd>
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
        <h4>Authority reason</h4>
        <ul className="compact-list">
          {interruptRedirect.authority_state_reason_refs.map((ref) => (
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
            <p className="eyebrow">Voice and media</p>
            <h3>Posture inspection</h3>
          </div>
          <span className="status-pill compact">
            {voiceMediaPosture.status}
          </span>
        </div>
        <p>{voiceMediaPosture.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{voiceMediaPosture.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{voiceMediaPosture.cli_ref}</dd>
          </div>
          <div>
            <dt>Authority</dt>
            <dd>{voiceMediaPosture.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{voiceMediaPosture.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>{voiceMediaPosture.authority_state_decision_outcome}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{voiceMediaPosture.authority_state_decision_ref}</dd>
          </div>
          <div>
            <dt>Lanes</dt>
            <dd>{voiceMediaPosture.lane_count}</dd>
          </div>
          <div>
            <dt>Blocked lanes</dt>
            <dd>{voiceMediaPosture.blocked_lane_count}</dd>
          </div>
          <div>
            <dt>Microphone</dt>
            <dd>
              {voiceMediaPosture.microphone_access_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Generation</dt>
            <dd>
              {voiceMediaPosture.media_generation_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Provider</dt>
            <dd>
              {voiceMediaPosture.provider_calls_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Media material</dt>
            <dd>{voiceMediaPosture.raw_media_persisted ? "stored" : "omitted"}</dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Lane</th>
                <th>Status</th>
                <th>Consent</th>
                <th>Receipt</th>
                <th>Safe disable</th>
              </tr>
            </thead>
            <tbody>
              {voiceMediaPosture.lanes.map((lane) => (
                <tr key={lane.lane_ref}>
                  <td>{lane.display_label}</td>
                  <td>{lane.status}</td>
                  <td>{lane.consent_ref}</td>
                  <td>{lane.receipt_plan_ref}</td>
                  <td>{lane.safe_disable_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h4>Unsupported adapters</h4>
        <ul className="compact-list">
          {voiceMediaPosture.unsupported_adapter_refs.slice(0, 6).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {voiceMediaPosture.blocked_authority_refs.slice(0, 6).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
        <h4>Authority reason</h4>
        <ul className="compact-list">
          {voiceMediaPosture.authority_state_reason_refs.map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </article>
      <article className="info-card">
        <div className="panel-heading compact-heading">
          <div>
            <p className="eyebrow">Messaging gateways</p>
            <h3>Posture inspection</h3>
          </div>
          <span className="status-pill compact">
            {messagingGatewayPosture.status}
          </span>
        </div>
        <p>{messagingGatewayPosture.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{messagingGatewayPosture.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{messagingGatewayPosture.cli_ref}</dd>
          </div>
          <div>
            <dt>Authority</dt>
            <dd>{messagingGatewayPosture.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{messagingGatewayPosture.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>{messagingGatewayPosture.authority_state_decision_outcome}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{messagingGatewayPosture.authority_state_decision_ref}</dd>
          </div>
          <div>
            <dt>Platforms</dt>
            <dd>{messagingGatewayPosture.platform_count}</dd>
          </div>
          <div>
            <dt>Blocked platforms</dt>
            <dd>{messagingGatewayPosture.blocked_platform_count}</dd>
          </div>
          <div>
            <dt>Connector runtime</dt>
            <dd>
              {messagingGatewayPosture.connector_runtime_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Sends</dt>
            <dd>{messagingGatewayPosture.send_enabled ? "enabled" : "blocked"}</dd>
          </div>
          <div>
            <dt>OAuth/webhooks</dt>
            <dd>
              {messagingGatewayPosture.oauth_enabled ||
              messagingGatewayPosture.webhook_exposure_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Message material</dt>
            <dd>
              {messagingGatewayPosture.raw_message_persisted
                ? "stored"
                : "omitted"}
            </dd>
          </div>
        </dl>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Platform</th>
                <th>Status</th>
                <th>Inbound</th>
                <th>Outbound</th>
                <th>OAuth</th>
                <th>Webhook</th>
              </tr>
            </thead>
            <tbody>
              {messagingGatewayPosture.platforms.map((platform) => (
                <tr key={platform.platform_ref}>
                  <td>{platform.display_label}</td>
                  <td>{platform.status}</td>
                  <td>{platform.inbound_readiness_ref}</td>
                  <td>{platform.outbound_write_label_ref}</td>
                  <td>{platform.oauth_label_ref}</td>
                  <td>{platform.webhook_label_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <h4>Unsupported adapters</h4>
        <ul className="compact-list">
          {messagingGatewayPosture.unsupported_adapter_refs
            .slice(0, 6)
            .map((ref) => (
              <li key={ref}>{ref}</li>
            ))}
        </ul>
        <h4>Blocked authority</h4>
        <ul className="compact-list">
          {messagingGatewayPosture.blocked_authority_refs
            .slice(0, 6)
            .map((ref) => (
              <li key={ref}>{ref}</li>
            ))}
        </ul>
        <h4>Authority reason</h4>
        <ul className="compact-list">
          {messagingGatewayPosture.authority_state_reason_refs.map((ref) => (
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
            <dt>Authority</dt>
            <dd>
              {hardlineCommandBlocklist.authority_state_decision_outcome} /{" "}
              {hardlineCommandBlocklist.authority_state_status}
            </dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{hardlineCommandBlocklist.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{hardlineCommandBlocklist.authority_state_decision_ref}</dd>
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
          <div>
            <dt>Unsupported adapters</dt>
            <dd>
              <ul className="compact-list">
                {hardlineCommandBlocklist.unsupported_adapter_refs
                  .slice(0, 5)
                  .map((ref) => (
                    <li key={ref}>{ref}</li>
                  ))}
              </ul>
            </dd>
          </div>
          <div>
            <dt>Authority reason</dt>
            <dd>
              <ul className="compact-list">
                {hardlineCommandBlocklist.authority_state_reason_refs
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
            <dt>Authority</dt>
            <dd>
              {promptStabilityTiers.authority_state_decision_outcome} /{" "}
              {promptStabilityTiers.authority_state_status}
            </dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{promptStabilityTiers.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{promptStabilityTiers.authority_state_decision_ref}</dd>
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
          <div>
            <dt>Unsupported adapters</dt>
            <dd>
              <ul className="compact-list">
                {promptStabilityTiers.unsupported_adapter_refs
                  .slice(0, 5)
                  .map((ref) => (
                    <li key={ref}>{ref}</li>
                  ))}
              </ul>
            </dd>
          </div>
          <div>
            <dt>Authority reason</dt>
            <dd>
              <ul className="compact-list">
                {promptStabilityTiers.authority_state_reason_refs
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
            <dt>Authority</dt>
            <dd>
              {contextBudgetPressure.authority_state_decision_outcome} /{" "}
              {contextBudgetPressure.authority_state_status}
            </dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{contextBudgetPressure.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{contextBudgetPressure.authority_state_decision_ref}</dd>
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
          <div>
            <dt>Unsupported adapters</dt>
            <dd>
              <ul className="compact-list">
                {contextBudgetPressure.unsupported_adapter_refs
                  .slice(0, 5)
                  .map((ref) => (
                    <li key={ref}>{ref}</li>
                  ))}
              </ul>
            </dd>
          </div>
          <div>
            <dt>Authority reason</dt>
            <dd>
              <ul className="compact-list">
                {contextBudgetPressure.authority_state_reason_refs
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
            <dt>Authority</dt>
            <dd>
              {usageCostAnalytics.authority_state_decision_outcome} /{" "}
              {usageCostAnalytics.authority_state_status}
            </dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{usageCostAnalytics.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{usageCostAnalytics.authority_state_decision_ref}</dd>
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
          <div>
            <dt>Unsupported adapters</dt>
            <dd>
              <ul className="compact-list">
                {usageCostAnalytics.unsupported_adapter_refs
                  .slice(0, 5)
                  .map((ref) => (
                    <li key={ref}>{ref}</li>
                  ))}
              </ul>
            </dd>
          </div>
          <div>
            <dt>Authority reason</dt>
            <dd>
              <ul className="compact-list">
                {usageCostAnalytics.authority_state_reason_refs
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
            <dt>Authority</dt>
            <dd>
              {virtualProviderMoa.authority_state_decision_outcome} /{" "}
              {virtualProviderMoa.authority_state_status}
            </dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{virtualProviderMoa.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{virtualProviderMoa.authority_state_decision_ref}</dd>
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
          <div>
            <dt>Unsupported adapters</dt>
            <dd>
              <ul className="compact-list">
                {virtualProviderMoa.unsupported_adapter_refs
                  .slice(0, 5)
                  .map((ref) => (
                    <li key={ref}>{ref}</li>
                  ))}
              </ul>
            </dd>
          </div>
          <div>
            <dt>Authority reason</dt>
            <dd>
              <ul className="compact-list">
                {virtualProviderMoa.authority_state_reason_refs
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
            <dt>Authority</dt>
            <dd>{toolRegistry.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{toolRegistry.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>{toolRegistry.authority_state_decision_outcome}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{toolRegistry.authority_state_decision_ref}</dd>
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
        <dl className="detail-grid">
          <div>
            <dt>Unsupported adapters</dt>
            <dd>
              <ul className="compact-list">
                {toolRegistry.unsupported_adapter_refs.slice(0, 4).map((ref) => (
                  <li key={ref}>{ref}</li>
                ))}
              </ul>
            </dd>
          </div>
          <div>
            <dt>Authority reason</dt>
            <dd>
              <ul className="compact-list">
                {toolRegistry.authority_state_reason_refs.map((ref) => (
                  <li key={ref}>{ref}</li>
                ))}
              </ul>
            </dd>
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
            <h3>Proof-backed goals and durable replay</h3>
          </div>
          <span className="status-pill compact">{runtimeGoalEvents.status}</span>
        </div>
        <p>{runtimeGoalEvents.safe_summary}</p>
        <dl className="detail-grid">
          <div>
            <dt>Route</dt>
            <dd>{runtimeGoalEvents.route_ref}</dd>
          </div>
          <div>
            <dt>CLI</dt>
            <dd>{runtimeGoalEvents.cli_ref}</dd>
          </div>
          <div>
            <dt>Authority</dt>
            <dd>{runtimeGoalEvents.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{runtimeGoalEvents.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>{runtimeGoalEvents.authority_state_decision_outcome}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{runtimeGoalEvents.authority_state_decision_ref}</dd>
          </div>
          <div>
            <dt>Approval waits</dt>
            <dd>{runtimeGoalEvents.approval_wait_count}</dd>
          </div>
          <div>
            <dt>Goals</dt>
            <dd>{runtimeGoalEvents.goal_lifecycle.goal_count}</dd>
          </div>
          <div>
            <dt>Verified goals</dt>
            <dd>{runtimeGoalEvents.goal_lifecycle.verified_complete_count}</dd>
          </div>
          <div>
            <dt>Durable streams</dt>
            <dd>{runtimeGoalEvents.stream_count}</dd>
          </div>
          <div>
            <dt>Retained events</dt>
            <dd>{runtimeGoalEvents.retained_event_count}</dd>
          </div>
          <div>
            <dt>Completed runs</dt>
            <dd>{runtimeGoalEvents.completed_run_count}</dd>
          </div>
          <div>
            <dt>Create route</dt>
            <dd>{runtimeGoalEvents.create_run_route_enabled ? "enabled" : "blocked"}</dd>
          </div>
          <div>
            <dt>Stop route</dt>
            <dd>{runtimeGoalEvents.stop_run_route_enabled ? "enabled" : "blocked"}</dd>
          </div>
          <div>
            <dt>Approval resolution</dt>
            <dd>
              {runtimeGoalEvents.approval_resolution_route_enabled
                ? "enabled"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Live event stream</dt>
            <dd>{runtimeGoalEvents.live_event_stream_enabled ? "enabled" : "blocked"}</dd>
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
              {runtimeGoalEvents.lifecycle_mappings.slice(0, 6).map((mapping) => (
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
        <h4>Goal lifecycle controls</h4>
        <p className="section-copy">
          These controls mutate local goal metadata only. They do not start a
          run, mint standing authority, or verify completion without an exact
          durable receipt and proof.
        </p>
        <form className="preview-form" onSubmit={createGoal}>
          <label>
            Objective
            <input
              required
              maxLength={1200}
              value={goalObjective}
              onChange={(event) => setGoalObjective(event.target.value)}
            />
          </label>
          <label>
            Desired outcome
            <input
              required
              maxLength={1200}
              value={goalOutcome}
              onChange={(event) => setGoalOutcome(event.target.value)}
            />
          </label>
          <label>
            Success criterion
            <input
              required
              maxLength={1200}
              value={goalSuccessCriterion}
              onChange={(event) =>
                setGoalSuccessCriterion(event.target.value)
              }
            />
          </label>
          <label>
            Stop condition
            <input
              required
              maxLength={1200}
              value={goalStopCondition}
              onChange={(event) => setGoalStopCondition(event.target.value)}
            />
          </label>
          <button
            type="submit"
            disabled={goalMutationBusy || mutationBinding === null}
          >
            Create local goal
          </button>
        </form>
        <div className="preview-form">
          <label>
            Selected durable goal
            <select
              value={selectedGoalRef}
              onChange={(event) => {
                setSelectedGoalRef(event.target.value);
                setEditedObjective("");
              }}
            >
              <option value="">No goal selected</option>
              {runtimeGoalEvents.goal_lifecycle.goals.map((goal) => (
                <option key={goal.goal_ref} value={goal.goal_ref}>
                  {goal.state} · v{goal.version} · {goal.objective}
                </option>
              ))}
            </select>
          </label>
          <label>
            Refined objective
            <input
              maxLength={1200}
              placeholder={selectedGoal?.objective ?? "Select a goal"}
              value={editedObjective}
              onChange={(event) => setEditedObjective(event.target.value)}
            />
          </label>
          <button
            type="button"
            disabled={
              goalMutationBusy ||
              mutationBinding === null ||
              selectedGoal === undefined ||
              editedObjective.trim().length === 0
            }
            onClick={saveGoalObjective}
          >
            Save objective
          </button>
          {availableGoalTransitions.map((transition) => (
            <button
              key={transition}
              type="button"
              disabled={goalMutationBusy || mutationBinding === null}
              onClick={() => transitionGoal(transition)}
            >
              {transition.replaceAll("_", " ")}
            </button>
          ))}
        </div>
        <p className="form-message" role="status">
          {goalNotice}
        </p>
        {selectedGoal?.state === "complete_requested" ? (
          <p className="section-copy">
            Verified completion is intentionally unavailable as a generic UI
            button. Supply the exact linked run, receipt, proof, Evidence, and
            deterministic verifier refs through the typed API or CLI.
          </p>
        ) : null}
        <h4>Durable goals</h4>
        <ul className="compact-list">
          {runtimeGoalEvents.goal_lifecycle.goals.length === 0 ? (
            <li>No durable goals recorded.</li>
          ) : null}
          {runtimeGoalEvents.goal_lifecycle.goals.map((goal) => (
            <li key={goal.goal_ref}>
              {goal.goal_ref}: {goal.state}; version {goal.version}; runs{" "}
              {goal.links.run_refs.length}
            </li>
          ))}
        </ul>
        <h4>Durable event replay</h4>
        <ul className="compact-list">
          {runtimeGoalEvents.event_previews.length === 0 ? (
            <li>No accepted local run events recorded.</li>
          ) : null}
          {runtimeGoalEvents.event_previews.map((event) => (
            <li key={event.event_ref}>
              {event.sequence ?? "?"}. {event.event_kind}: {event.event_ref}{" "}
              {" -> "} {event.proof_ref}
            </li>
          ))}
        </ul>
        <h4>Unsupported adapters</h4>
        <ul className="compact-list">
          {runtimeGoalEvents.unsupported_adapter_refs.slice(0, 5).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
        <h4>Authority reason</h4>
        <ul className="compact-list">
          {runtimeGoalEvents.authority_state_reason_refs.slice(0, 3).map((ref) => (
            <li key={ref}>{ref}</li>
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
            <dt>Replay route</dt>
            <dd>{streamingProgress.replay_route_ref}</dd>
          </div>
          <div>
            <dt>Replay CLI</dt>
            <dd>{streamingProgress.replay_cli_ref}</dd>
          </div>
          <div>
            <dt>Authority</dt>
            <dd>{streamingProgress.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{streamingProgress.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>{streamingProgress.authority_state_decision_outcome}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{streamingProgress.authority_state_decision_ref}</dd>
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
            <dt>Read-only preview replay</dt>
            <dd>
              {streamingProgress.readonly_sse_replay_enabled
                ? "local preview replay available"
                : "blocked"}
            </dd>
          </div>
          <div>
            <dt>Replay source</dt>
            <dd>
              {streamingProgress.readonly_sse_replay_durable_event_source
                ? "durable events"
                : streamingProgress.readonly_sse_replay_source_posture.replaceAll(
                    "_",
                    " ",
                  )}
            </dd>
          </div>
          <div>
            <dt>Replay control</dt>
            <dd>
              {streamingProgress.readonly_sse_replay_control_messages_accepted ||
              streamingProgress.readonly_sse_replay_mutation_enabled
                ? "enabled"
                : "blocked (read-only)"}
            </dd>
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
            <dt>Live SSE/WebSocket</dt>
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
        <h4>Unsupported adapters</h4>
        <ul className="compact-list">
          {streamingProgress.unsupported_adapter_refs.slice(0, 5).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
        <h4>Authority reason</h4>
        <ul className="compact-list">
          {streamingProgress.authority_state_reason_refs
            .slice(0, 3)
            .map((ref) => (
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
            <dt>Authority</dt>
            <dd>
              {profiles.authority_state_decision_outcome} /{" "}
              {profiles.authority_state_status}
            </dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{profiles.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{profiles.authority_state_decision_ref}</dd>
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
        <h4>Unsupported adapters</h4>
        <ul className="compact-list">
          {profiles.unsupported_adapter_refs.slice(0, 8).map((ref) => (
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
            <dt>Authority</dt>
            <dd>{approvalBridge.authority_state_route_ref}</dd>
          </div>
          <div>
            <dt>Capability mapping</dt>
            <dd>{approvalBridge.authority_state_mapping_ref}</dd>
          </div>
          <div>
            <dt>Decision</dt>
            <dd>{approvalBridge.authority_state_decision_outcome}</dd>
          </div>
          <div>
            <dt>Decision ref</dt>
            <dd>{approvalBridge.authority_state_decision_ref}</dd>
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
        <h4>Unsupported adapters</h4>
        <ul className="compact-list">
          {approvalBridge.unsupported_adapter_refs.slice(0, 5).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
        <h4>Authority reason</h4>
        <ul className="compact-list">
          {approvalBridge.authority_state_reason_refs.slice(0, 3).map((ref) => (
            <li key={ref}>{ref}</li>
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
