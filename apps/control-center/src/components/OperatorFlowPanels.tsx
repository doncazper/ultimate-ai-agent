import { useEffect, useMemo, useState } from "react";
import {
  fetchChatTurnReceipt,
  inspectLocalModelsRoute,
  recordChatHandoff,
  recordChatTurnReceipt,
  requestRedactedLocalChatProbe,
} from "../api/client";
import { API_ENDPOINTS } from "../api/endpoints";
import type {
  ChatHandoffReceipt,
  ChatHandoffTarget,
  ChatTurnReceipt,
  ChatTurnReceiptRequest,
  ControlCenterData,
  ControlCenterSettingsAuthorityPosture,
  ControlCenterSettingsFeatureFlagPosture,
  ControlCenterSettingsKillSwitchPosture,
  LocalModelsInspectionStatus,
  ModelProviderControlPlaneReadModel,
  OperatorLoopStepSummary,
  OperatorRouteInspectionState,
  ProviderCredentialReadinessSummary,
  ProviderSettingsDiagnosticsSummary,
  RedactedLocalChatProbeStatus,
} from "../api/types";
import { EmptyState } from "./DataState";
import { EvidenceViewerPanel } from "./EvidenceFileMemoryViewerPanel";
import { ChatToLoopHandoffPanel } from "./FounderLoopPanels";
import { OperatorSurfaceStates } from "./OperatorSurfaceStates";
import { ProviderCatalogPanel } from "./ProviderCatalogPanel";
import { TurnRouterDiagnosticsPanel } from "./TurnRouterDiagnosticsPanel";

const DEFAULT_MODEL_ID = "uaa-llama-cpp-local";
const SETTINGS_AUTHORITY_KEYS = [
  "web",
  "providers",
  "connectors",
  "memory_context_use",
  "model_runtime",
  "local_model_lifecycle",
  "platform_capabilities",
] as const;
const TASK_DECOMPOSITION_ROUTE_REFS = [
  "/task-decomposition/status",
  "/task-decomposition/catalog",
  "/task-decomposition/classify",
  "/task-decomposition/decompose",
  "/task-decomposition/plans/validate",
  "/task-decomposition/approvals",
  "/task-decomposition/audit",
  "/task-decomposition/metrics",
];

export function ChatOperatorPanel({ data }: { data: ControlCenterData }) {
  const today = data.founderToday;
  const [models, setModels] =
    useState<LocalModelsInspectionStatus>(initialModelsStatus);
  const [probe, setProbe] = useState<
    RedactedLocalChatProbeStatus | undefined
  >();
  const [chatReceipt, setChatReceipt] = useState<ChatTurnReceipt>();
  const [handoffReceipt, setHandoffReceipt] = useState<ChatHandoffReceipt>();
  const [probePending, setProbePending] = useState(false);
  const [receiptPending, setReceiptPending] = useState(false);
  const [handoffPending, setHandoffPending] = useState<ChatHandoffTarget>();
  const [receiptError, setReceiptError] = useState<string>();
  const chatStep = useOperatorStep(data, "uaa_v1_chat");
  const localModelStep = useOperatorStep(data, "local_model_readiness");
  const selectedModelId = models.selectedModelId ?? DEFAULT_MODEL_ID;
  const canRequestProbe = models.state === "ready" && !probePending;
  const canRecordHandoff = Boolean(chatReceipt) && handoffPending === undefined;
  const runtimeTruth =
    probe?.runtimeTruth ?? today.chat_local_operator_runtime_truth;
  const authTruth = probe?.authTruth ?? today.chat_local_operator_auth_truth;
  const toolDenialTruth =
    probe?.toolDenialTruth ?? today.chat_local_operator_tool_denial_truth;
  const evidenceRefs =
    probe?.evidenceRefs ?? today.chat_local_operator_safe_evidence_refs;
  const blockedRefs =
    probe?.blockedStateRefs ?? today.chat_local_operator_blocked_state_refs;
  const plansHandoffRef =
    probe?.plansHandoffRef ?? today.chat_local_operator_plans_handoff_ref;
  const actionsHandoffRef =
    probe?.actionsHandoffRef ?? today.chat_local_operator_actions_handoff_ref;
  const turnHarnessBinding =
    chatReceipt?.turn_harness_binding ?? probe?.turnHarnessBinding;

  useEffect(() => {
    let cancelled = false;
    void inspectLocalModelsRoute().then((status) => {
      if (!cancelled) {
        setModels(status);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleProbeRequest() {
    if (!canRequestProbe) {
      return;
    }
    setProbePending(true);
    setReceiptError(undefined);
    setChatReceipt(undefined);
    setHandoffReceipt(undefined);
    try {
      const nextProbe = await requestRedactedLocalChatProbe(selectedModelId);
      setProbe(nextProbe);
      if (nextProbe.state === "ready") {
        setReceiptPending(true);
        try {
          const recordedReceipt = await recordChatTurnReceipt(
            chatTurnReceiptRequestFromProbe(nextProbe),
          );
          const confirmedReceipt = await fetchChatTurnReceipt(
            recordedReceipt.turn_ref,
          ).catch(() => recordedReceipt);
          setChatReceipt(confirmedReceipt);
        } catch (error) {
          setReceiptError(
            error instanceof Error
              ? error.message
              : "Chat turn receipt was not recorded safely.",
          );
        } finally {
          setReceiptPending(false);
        }
      }
    } finally {
      setProbePending(false);
    }
  }

  async function handleHandoff(target: ChatHandoffTarget) {
    if (!chatReceipt || handoffPending !== undefined) {
      return;
    }
    setReceiptError(undefined);
    setHandoffPending(target);
    try {
      setHandoffReceipt(await recordChatHandoff(chatReceipt.turn_ref, target));
    } catch (error) {
      setReceiptError(
        error instanceof Error
          ? error.message
          : "Chat handoff receipt was not recorded safely.",
      );
    } finally {
      setHandoffPending(undefined);
    }
  }

  return (
    <section className="page-section" aria-labelledby="chat-shell-heading">
      <OperatorHeader
        eyebrow="Local operator flow"
        headingId="chat-shell-heading"
        heading="Chat Local Operator"
        status={statusLabel(models.state)}
        summary="Control Center can probe a redacted local turn through UAA /v1, record a durable receipt, and show model, runtime, auth, and tool-denial truth without treating output as authority."
      />

      <TurnRouterDiagnosticsPanel />

      <div className="operator-flow-grid">
        <StatusPanel
          title="UAA /v1 model route"
          state={models.state}
          message={models.safeMessage}
          details={[
            ["Route", models.routeRef],
            [
              "HTTP status",
              models.statusCode ? String(models.statusCode) : "not available",
            ],
            ["Selected model", selectedModelId],
            ["Visible response content", "no"],
          ]}
          reasonCodes={models.reasonCodes}
        />
        <StatusPanel
          title="Local chat turn"
          state={
            probe?.state ??
            (models.state === "ready" ? "blocked" : models.state)
          }
          message={
            probe?.safeMessage ??
            "The chat route is not contacted until model readiness is available. Streaming, tools, memory writes, provider authority, and context injection are not exposed here."
          }
          details={[
            ["Route", API_ENDPOINTS.localChatCompletions],
            ["Contract", today.chat_local_operator_contract_ref],
            ["Model ID", selectedModelId],
            ["Runtime truth", runtimeTruth],
            ["Auth truth", authTruth],
            ["Tool denial", toolDenialTruth],
            [
              "Harness contract",
              turnHarnessBinding?.turn_contract ?? "not bound",
            ],
            [
              "Harness approval",
              turnHarnessBinding
                ? turnHarnessBinding.approval_required
                  ? "required"
                  : "not required"
                : "not bound",
            ],
            ["Exchange body shown", "no"],
            ["Completion content shown", "no"],
            [
              "Duration",
              probe?.durationMs ? `${probe.durationMs} ms` : "not measured",
            ],
          ]}
          reasonCodes={probe?.reasonCodes ?? chatStep?.evidence_refs ?? []}
        />
      </div>

      <div className="panel-grid">
        <article className="panel">
          <div className="panel-heading">
            <h3>Safe evidence</h3>
            <span>{today.chat_local_operator_status}</span>
          </div>
          <dl className="metadata-list">
            <div>
              <dt>Turn ref</dt>
              <dd>{probe?.turnRef ?? today.chat_local_operator_turn_ref}</dd>
            </div>
            <div>
              <dt>Tool denial ref</dt>
              <dd>
                {probe?.toolDenialRef ??
                  today.chat_local_operator_tool_denial_ref}
              </dd>
            </div>
            <div>
              <dt>Model output authority</dt>
              <dd>
                {today.chat_local_operator_authority_posture
                  .model_output_authority
                  ? "enabled"
                  : "denied"}
              </dd>
            </div>
          </dl>
          <div className="note-list" aria-label="Chat safe evidence refs">
            {evidenceRefs.map((ref) => (
              <span key={ref}>{ref}</span>
            ))}
          </div>
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h3>Harness binding</h3>
            <span>router metadata</span>
          </div>
          <dl className="metadata-list">
            <div>
              <dt>Binding ref</dt>
              <dd>{turnHarnessBinding?.binding_ref ?? "not recorded"}</dd>
            </div>
            <div>
              <dt>Turn contract</dt>
              <dd>{turnHarnessBinding?.turn_contract ?? "not bound"}</dd>
            </div>
            <div>
              <dt>Memory scope</dt>
              <dd>{turnHarnessBinding?.memory_scope ?? "not bound"}</dd>
            </div>
            <div>
              <dt>Tool posture</dt>
              <dd>{turnHarnessBinding?.tool_policy ?? "not exposed"}</dd>
            </div>
            <div>
              <dt>No-effect scope</dt>
              <dd>
                {turnHarnessBinding?.no_effect_scope ?? "not recorded"}
              </dd>
            </div>
            <div>
              <dt>Execution tools</dt>
              <dd>
                {turnHarnessBinding?.execution_tools_exposed_count ??
                  "not recorded"}
              </dd>
            </div>
            <div>
              <dt>Action execution</dt>
              <dd>
                {turnHarnessBinding?.side_effects_allowed
                  ? "blocked (unsafe receipt flag)"
                  : "blocked"}
              </dd>
            </div>
          </dl>
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h3>Proposal handoff</h3>
            <span>safe refs only</span>
          </div>
          <dl className="metadata-list">
            <div>
              <dt>Plans</dt>
              <dd>{plansHandoffRef}</dd>
            </div>
            <div>
              <dt>Actions</dt>
              <dd>{actionsHandoffRef}</dd>
            </div>
            <div>
              <dt>Memory write</dt>
              <dd>
                {today.chat_local_operator_authority_posture
                  .memory_write_authorized
                  ? "enabled"
                  : "blocked"}
              </dd>
            </div>
          </dl>
          <div className="note-list" aria-label="Chat blocked refs">
            {blockedRefs.slice(0, 6).map((ref) => (
              <span key={ref}>{ref}</span>
            ))}
          </div>
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h3>Durable receipt</h3>
            <span>{today.chat_durable_receipt_status}</span>
          </div>
          <dl className="metadata-list">
            <div>
              <dt>Contract</dt>
              <dd>{today.chat_durable_receipt_contract_ref}</dd>
            </div>
            <div>
              <dt>Receipt ref</dt>
              <dd>{chatReceipt?.receipt_ref ?? "not recorded"}</dd>
            </div>
            <div>
              <dt>Evidence ref</dt>
              <dd>{chatReceipt?.evidence_ref ?? "not recorded"}</dd>
            </div>
            <div>
              <dt>Action execution</dt>
              <dd>
                {chatReceipt?.action_execution_enabled ? "enabled" : "blocked"}
              </dd>
            </div>
            <div>
              <dt>Memory write</dt>
              <dd>
                {chatReceipt?.memory_write_authorized ? "enabled" : "blocked"}
              </dd>
            </div>
            <div>
              <dt>Harness binding</dt>
              <dd>
                {chatReceipt?.turn_harness_binding?.binding_ref ??
                  "not recorded"}
              </dd>
            </div>
            <div>
              <dt>Harness no-effect</dt>
              <dd>
                {chatReceipt?.turn_harness_binding
                  ?.no_action_execution_performed
                  ? "proved"
                  : "not recorded"}
              </dd>
            </div>
            <div>
              <dt>Harness scope</dt>
              <dd>
                {chatReceipt?.turn_harness_binding?.no_effect_scope ??
                  "not recorded"}
              </dd>
            </div>
          </dl>
          <div className="note-list" aria-label="Chat durable receipt routes">
            {today.chat_durable_receipt_route_refs.map((ref) => (
              <span key={ref}>{ref}</span>
            ))}
          </div>
          {receiptPending ? (
            <p className="form-message">Recording durable receipt...</p>
          ) : null}
        </article>
      </div>

      <div
        className="operator-action-panel"
        aria-label="Redacted local chat readiness exchange"
      >
        <div>
          <h3>Redacted local turn</h3>
          <p>
            This request uses the UAA local chat route only after the model-list
            route answers. The Control Center does not display the exchange text
            or completion content.
          </p>
        </div>
        <button
          className="secondary-button"
          disabled={!canRequestProbe}
          onClick={() => void handleProbeRequest()}
          type="button"
        >
          {probePending
            ? "Probing local turn"
            : models.state === "checking"
              ? "Checking local model readiness"
              : "Probe redacted local turn"}
        </button>
      </div>

      <div
        className="operator-action-panel"
        aria-label="Chat receipt proposal handoff"
      >
        <div>
          <h3>Reviewable handoff</h3>
          <p>
            Handoff records proposal refs for Actions or Plans only. It does not
            execute work, write memory, or promote model output into authority.
          </p>
        </div>
        <div className="action-button-row">
          <button
            className="secondary-button"
            disabled={!canRecordHandoff}
            onClick={() => void handleHandoff("actions")}
            type="button"
          >
            {handoffPending === "actions"
              ? "Recording actions proposal"
              : "Record actions proposal"}
          </button>
          <button
            className="secondary-button"
            disabled={!canRecordHandoff}
            onClick={() => void handleHandoff("plans")}
            type="button"
          >
            {handoffPending === "plans"
              ? "Recording plans proposal"
              : "Record plans proposal"}
          </button>
        </div>
      </div>

      <ChatToLoopHandoffPanel
        readModel={today.chat_to_loop_handoff_read_model}
      />

      {handoffReceipt ? (
        <article className="panel">
          <div className="panel-heading">
            <h3>Handoff receipt</h3>
            <span>pending backend refresh</span>
          </div>
          <dl className="metadata-list">
            <div>
              <dt>Receipt ref</dt>
              <dd>{handoffReceipt.receipt_ref}</dd>
            </div>
            <div>
              <dt>Handoff ref</dt>
              <dd>{handoffReceipt.handoff_ref}</dd>
            </div>
            <div>
              <dt>Created ref</dt>
              <dd>{handoffReceipt.created_ref}</dd>
            </div>
            <div>
              <dt>Audit ref</dt>
              <dd>{handoffReceipt.audit_ref}</dd>
            </div>
            <div>
              <dt>Action execution</dt>
              <dd>{receiptDeniedLabel(handoffReceipt.action_executed)}</dd>
            </div>
            <div>
              <dt>Plan execution</dt>
              <dd>{receiptDeniedLabel(handoffReceipt.plan_executed)}</dd>
            </div>
            <div>
              <dt>Memory write</dt>
              <dd>
                {receiptDeniedLabel(handoffReceipt.memory_write_performed)}
              </dd>
            </div>
          </dl>
        </article>
      ) : null}
      {receiptError ? (
        <p className="form-error" role="alert">
          {receiptError}
        </p>
      ) : null}

      <OperatorStepStrip steps={[localModelStep, chatStep]} />
      <OperatorSurfaceStates surface="Chat Local Operator" />
    </section>
  );
}

function receiptDeniedLabel(value: boolean): string {
  return value ? "blocked (unsafe receipt flag)" : "blocked";
}

function chatTurnReceiptRequestFromProbe(
  probe: RedactedLocalChatProbeStatus,
): ChatTurnReceiptRequest {
  const safeModelRef = safeOperatorRefSuffix(probe.modelId);
  return {
    turn_ref: probe.turnRef,
    route_ref: probe.routeRef,
    model_ref: `model-ref:${safeModelRef}`,
    runtime_truth: probe.runtimeTruth,
    auth_truth: probe.authTruth,
    tool_denial_truth: probe.toolDenialTruth,
    safe_summary_ref: "safe-summary-ref:control-center-chat-probe",
    turn_harness_binding: probe.turnHarnessBinding,
    evidence_refs: uniqueRefs([
      "evidence-ref:control-center-chat-probe",
      ...probe.evidenceRefs,
    ]),
    metadata_refs: [`metadata-ref:control-center-chat:${safeModelRef}`],
  };
}

function uniqueRefs(values: string[]): string[] {
  return Array.from(new Set(values));
}

function safeOperatorRefSuffix(value: string): string {
  return (
    value
      .trim()
      .toLowerCase()
      .replaceAll(":", "-")
      .replace(/[^a-z0-9_.@-]+/g, "-")
      .replace(/^-+|-+$/g, "") || "missing"
  );
}

export function PlansOperatorPanel({ data }: { data: ControlCenterData }) {
  const planStep = useOperatorStep(data, "task_decomposition_plan");
  const approvalStep = useOperatorStep(data, "safe_capability_approval");
  const receiptStep = useOperatorStep(data, "receipt_audit_latency_rollback");

  return (
    <section className="page-section" aria-labelledby="plans-heading">
      <OperatorHeader
        eyebrow="Local operator flow"
        headingId="plans-heading"
        heading="Plans"
        status={planStep?.status ?? "backend gated"}
        summary="Plans expose the task decomposition route family, approval requirements, and durable evidence refs without implying plan execution from the browser."
      />

      <div className="panel-grid">
        <article className="panel">
          <div className="panel-heading">
            <h3>Task decomposition route posture</h3>
            <span>local authority required</span>
          </div>
          <p>
            Classify, decompose, validate, approval, audit, and metric routes
            are known backend contracts. This screen does not submit task text
            or execute handlers.
          </p>
          <div className="note-list" aria-label="Task decomposition routes">
            {TASK_DECOMPOSITION_ROUTE_REFS.map((route) => (
              <span key={route}>{route}</span>
            ))}
          </div>
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h3>Plan authority boundary</h3>
            <span>approval gated</span>
          </div>
          <p>
            Browser-visible plan state is inspection metadata. Exact-scope
            approval remains bound to LocalApprovalAuthority-backed backend
            contracts.
          </p>
          <dl className="metadata-list">
            <div>
              <dt>Plan creation</dt>
              <dd>
                {planStep?.status ??
                  "blocked until local authority is configured"}
              </dd>
            </div>
            <div>
              <dt>Approval required</dt>
              <dd>
                {approvalStep?.approval_required
                  ? "yes"
                  : "backend contract decides"}
              </dd>
            </div>
            <div>
              <dt>Evidence state</dt>
              <dd>
                {receiptStep?.status ?? "not available from local summary"}
              </dd>
            </div>
          </dl>
        </article>
      </div>

      <OperatorStepStrip steps={[planStep, approvalStep, receiptStep]} />
      <OperatorSurfaceStates surface="Plans" />
    </section>
  );
}

export function ModelsOperatorPanel({ data }: { data: ControlCenterData }) {
  const [models, setModels] =
    useState<LocalModelsInspectionStatus>(initialModelsStatus);
  const localModelsStatus = data.localModelsStatus;
  const localModelStep = useOperatorStep(data, "local_model_readiness");
  const modelEntry = data.capabilityMatrix.entries.find((entry) =>
    entry.surface.toLowerCase().includes("model"),
  );
  const optionalAdapterReadiness = localModelsStatus.adapter_readiness ?? [];
  const lifecycleBlocked = Object.values(
    localModelsStatus.lifecycle_actions,
  ).every((enabled) => enabled === false);

  useEffect(() => {
    let cancelled = false;
    void inspectLocalModelsRoute().then((status) => {
      if (!cancelled) {
        setModels(status);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="page-section" aria-labelledby="models-heading">
      <OperatorHeader
        eyebrow="Local operator flow"
        headingId="models-heading"
        heading="Models"
        status={localModelsStatus.status}
        summary="Local Models display backend-owned read-only inventory, gateway posture, and optional Ollama/MLX-LM readiness. Model pulls/downloads, switch, start/stop, runtime adapter execution, and provider/model authority stay blocked."
      />

      <ProviderCatalogPanel catalog={data.providerCatalog} mode="models" />
      <ModelProviderControlPlanePanel
        controlPlane={data.modelProviderControlPlane}
      />
      <ProviderCredentialReadinessPanel
        readiness={data.dashboard.provider_credential_readiness}
      />

      <div className="operator-flow-grid">
        <StatusPanel
          title="Backend-owned Local Models status"
          state="ready"
          message={localModelsStatus.safe_summary}
          details={[
            ["Route", localModelsStatus.route_ref],
            [
              "Inventory schema",
              statusRecordValue(localModelsStatus.inventory, "schema_version"),
            ],
            [
              "Local gateway enabled",
              statusRecordValue(
                localModelsStatus.gateway_posture,
                "local_gateway_enabled",
              ),
            ],
            [
              "Lifecycle actions",
              lifecycleBlocked ? "blocked" : "unexpected enabled",
            ],
            [
              "Proposal review only",
              localModelsStatus.proposal_review_only ? "yes" : "no",
            ],
          ]}
          reasonCodes={localModelsStatus.blocked_authorities}
        />
        <StatusPanel
          title="UAA /v1 model route inspection"
          state={models.state}
          message={models.safeMessage}
          details={[
            ["Route", models.routeRef],
            ["Selected model", models.selectedModelId ?? DEFAULT_MODEL_ID],
            ["Configured gateway", localModelStep?.status ?? "not reported"],
            ["Model output authority", "no"],
          ]}
          reasonCodes={models.reasonCodes}
        />
        <article className="panel">
          <div className="panel-heading">
            <h3>Runtime readiness</h3>
            <span>{data.runtimeReadiness.status}</span>
          </div>
          <dl className="metadata-list">
            <div>
              <dt>Real model runtime ready</dt>
              <dd>
                {data.runtimeReadiness.real_model_runtime_ready ? "yes" : "no"}
              </dd>
            </div>
            <div>
              <dt>Production readiness claim</dt>
              <dd>{data.runtimeReadiness.production_ready ? "yes" : "no"}</dd>
            </div>
            <div>
              <dt>Capability posture</dt>
              <dd>{modelEntry?.status ?? "not listed in capability matrix"}</dd>
            </div>
            <div>
              <dt>Expected local model ID</dt>
              <dd>{DEFAULT_MODEL_ID}</dd>
            </div>
          </dl>
        </article>
      </div>

      <div
        className="panel-grid local-model-adapter-grid"
        aria-label="Optional local model stack readiness"
      >
        {optionalAdapterReadiness.map((adapter) => (
          <article
            className="panel local-model-adapter-card"
            key={adapter.adapter_id}
          >
            <div className="panel-heading">
              <h3>{adapter.display_name}</h3>
              <span>{adapter.readiness_state}</span>
            </div>
            <p>{adapter.next_safe_action}</p>
            <dl className="metadata-list">
              <div>
                <dt>Install detection</dt>
                <dd>{adapter.install_detection_posture}</dd>
              </div>
              <div>
                <dt>Config detection</dt>
                <dd>{adapter.config_detection_posture}</dd>
              </div>
              <div>
                <dt>Runtime calls</dt>
                <dd>{adapter.runtime_calls_enabled ? "enabled" : "blocked"}</dd>
              </div>
              <div>
                <dt>Pulls/downloads</dt>
                <dd>
                  {adapter.model_pulls_enabled || adapter.model_downloads_enabled
                    ? "enabled"
                    : "blocked"}
                </dd>
              </div>
              <div>
                <dt>Lifecycle actions</dt>
                <dd>
                  {adapter.lifecycle_start_stop_switch_enabled
                    ? "enabled"
                    : "blocked"}
                </dd>
              </div>
              <div>
                <dt>Provider/model authority</dt>
                <dd>
                  {adapter.provider_model_authority_enabled
                    ? "enabled"
                    : "blocked"}
                </dd>
              </div>
            </dl>
            <div
              className="note-list"
              aria-label={`${adapter.display_name} blocked authorities`}
            >
              {adapter.blocked_authority_refs.map((authority, index) => (
                <span key={`${authority}-${index}`}>{authority}</span>
              ))}
            </div>
          </article>
        ))}
      </div>

      <OperatorStepStrip steps={[localModelStep]} />
      <OperatorSurfaceStates surface="Models" />
    </section>
  );
}

function ModelProviderControlPlanePanel({
  controlPlane,
}: {
  controlPlane: ModelProviderControlPlaneReadModel;
}) {
  const trace = controlPlane.router_traces[0];
  const researchPosture = controlPlane.model_provider_research_posture;
  const externalPosture = researchPosture.external_information;
  const firstProviderPosture = researchPosture.provider_postures[0];
  return (
    <article className="panel model-provider-control-plane-panel">
      <div className="panel-heading">
        <h3>Model/provider control plane</h3>
        <span>{controlPlane.status}</span>
      </div>
      <p>{controlPlane.safe_summary}</p>
      <dl className="metadata-list">
        <div>
          <dt>Backend owned</dt>
          <dd>{controlPlane.backend_owned ? "yes" : "no"}</dd>
        </div>
        <div>
          <dt>Broad provider runtime</dt>
          <dd>
            {controlPlane.authority.broad_provider_runtime_enabled
              ? "enabled"
              : "blocked"}
          </dd>
        </div>
        <div>
          <dt>Provider SDK calls</dt>
          <dd>
            {controlPlane.authority.provider_sdk_call_enabled
              ? "enabled"
              : "blocked"}
          </dd>
        </div>
        <div>
          <dt>Network by default</dt>
          <dd>
            {controlPlane.authority.live_provider_network_call_enabled_by_default
              ? "enabled"
              : "blocked"}
          </dd>
        </div>
        <div>
          <dt>Exact tiny live lane</dt>
          <dd>
            {controlPlane.authority.exact_tiny_provider_lane_available
              ? "wired, approval required"
              : "not available"}
          </dd>
        </div>
        <div>
          <dt>Credential validation lane</dt>
          <dd>
            {controlPlane.authority.exact_credential_validation_lane_available
              ? "wired, approval required"
              : "not available"}
          </dd>
        </div>
        <div>
          <dt>Provider router</dt>
          <dd>
            {controlPlane.authority.provider_router_dry_run_available
              ? "dry-run trace only"
              : "not available"}
          </dd>
        </div>
        <div>
          <dt>ModelRouter trace</dt>
          <dd>{trace?.status ?? "not available"}</dd>
        </div>
        <div>
          <dt>llama.cpp lifecycle</dt>
          <dd>{controlPlane.local_llama_cpp_lifecycle.status}</dd>
        </div>
        <div>
          <dt>Production authority</dt>
          <dd>
            {controlPlane.authority.production_authority_enabled
              ? "enabled"
              : "blocked"}
          </dd>
        </div>
      </dl>

      <div
        className="provider-readiness-list"
        aria-label="Model provider control plane details"
      >
        <ReadinessGateCard
          title="Live provider adapter lanes"
          status={`${controlPlane.provider_adapters.length} exact lanes`}
          summary="Provider adapters are wired as exact lanes with receipt-before-network, endpoint refs, credential refs, and CostGovernor posture."
          details={[
            ["First adapter", controlPlane.provider_adapters[0]?.adapter_ref ?? "not reported"],
            [
              "Default network",
              controlPlane.provider_adapters.some(
                (adapter) => adapter.network_call_enabled_by_default,
              )
                ? "enabled"
                : "blocked",
            ],
            [
              "Receipt before network",
              controlPlane.provider_adapters.every(
                (adapter) => adapter.receipt_store_required_before_network,
              )
                ? "required"
                : "missing",
            ],
            [
              "Provider payload persistence",
              controlPlane.provider_adapters.some(
                (adapter) => adapter.provider_payload_persistence_allowed,
              )
                ? "enabled"
                : "blocked",
            ],
          ]}
          blockerCodes={controlPlane.provider_adapters.map(
            (adapter) => adapter.adapter_ref,
          )}
        />
        <ReadinessGateCard
          title="Secret status"
          status={controlPlane.secret_status.status}
          summary={controlPlane.secret_status.safe_summary}
          details={[
            ["Vault adapter", controlPlane.secret_status.vault_adapter_status],
            [
              "Validation",
              controlPlane.secret_status.validation_readiness_status,
            ],
            ["Enrollment", controlPlane.secret_status.enrollment_status],
            [
              "Credential refs",
              String(
                Object.keys(controlPlane.secret_status.credential_ref_statuses)
                  .length,
              ),
            ],
            [
              "Raw key collection",
              controlPlane.secret_status.raw_key_collection_enabled
                ? "enabled"
                : "blocked",
            ],
          ]}
          blockerCodes={[
            "raw_credentials_omitted",
            "secret_material_not_persisted",
          ]}
        />
        <ReadinessGateCard
          title="Network allowlists"
          status={controlPlane.network_allowlists.status}
          summary={controlPlane.network_allowlists.safe_summary}
          details={[
            [
              "Endpoint refs",
              String(controlPlane.network_allowlists.endpoint_refs.length),
            ],
            [
              "Transport refs",
              String(controlPlane.network_allowlists.transport_refs.length),
            ],
            [
              "Default network",
              controlPlane.network_allowlists.default_network_denied
                ? "denied"
                : "enabled",
            ],
            [
              "Provider SDK network",
              controlPlane.network_allowlists.provider_sdk_network_enabled
                ? "enabled"
                : "blocked",
            ],
            [
              "Redirects",
              controlPlane.network_allowlists.redirects_blocked
                ? "blocked"
                : "allowed",
            ],
          ]}
          blockerCodes={controlPlane.network_allowlists.endpoint_refs}
        />
        <ReadinessGateCard
          title="Model metadata discovery"
          status={controlPlane.model_metadata_discovery.status}
          summary={controlPlane.model_metadata_discovery.safe_summary}
          details={[
            [
              "Provider catalog",
              controlPlane.model_metadata_discovery.provider_catalog_ref,
            ],
            [
              "Provider models",
              String(
                controlPlane.model_metadata_discovery.provider_model_refs
                  .length,
              ),
            ],
            [
              "Local inventory",
              controlPlane.model_metadata_discovery.local_inventory_status,
            ],
            [
              "Local gateway model",
              controlPlane.model_metadata_discovery.local_gateway_model_ref,
            ],
            [
              "Live provider discovery",
              controlPlane.model_metadata_discovery
                .live_provider_model_discovery_enabled
                ? "enabled"
                : "blocked",
            ],
          ]}
          blockerCodes={controlPlane.model_metadata_discovery.provider_model_refs}
        />
        <ReadinessGateCard
          title="Delegated runtime model catalog"
          status={controlPlane.delegated_runtime_model_catalog.status}
          summary={controlPlane.delegated_runtime_model_catalog.safe_summary}
          details={[
            [
              "Runtime profiles",
              String(
                controlPlane.delegated_runtime_model_catalog
                  .runtime_profile_count,
              ),
            ],
            [
              "Model refs",
              String(controlPlane.delegated_runtime_model_catalog.model_count),
            ],
            [
              "Runtime reports available",
              String(
                controlPlane.delegated_runtime_model_catalog
                  .runtime_reported_available_count,
              ),
            ],
            [
              "UAA authorized models",
              String(
                controlPlane.delegated_runtime_model_catalog
                  .uaa_authorized_model_count,
              ),
            ],
            [
              "Runtime says available",
              controlPlane.delegated_runtime_model_catalog
                .runtime_says_available_is_not_authority
                ? "not authority"
                : "unsafe",
            ],
            [
              "Provider SDK calls",
              controlPlane.delegated_runtime_model_catalog.provider_sdk_call_enabled
                ? "enabled"
                : "blocked",
            ],
          ]}
          blockerCodes={[
            ...controlPlane.delegated_runtime_model_catalog.proof_refs,
            ...controlPlane.delegated_runtime_model_catalog.blocked_authority_refs,
            controlPlane.delegated_runtime_model_catalog
              .runtime_profiles_route_ref,
            ...controlPlane.delegated_runtime_model_catalog.records.map(
              (record) =>
                `${record.display_label}: ${record.uaa_invocation_posture}`,
            ),
          ]}
        />
        <ReadinessGateCard
          title="Cost hooks"
          status={controlPlane.cost_hooks.status}
          summary={controlPlane.cost_hooks.safe_summary}
          details={[
            [
              "Cost posture",
              controlPlane.cost_hooks.cost_governor_posture_ref,
            ],
            [
              "Cost decision",
              controlPlane.cost_hooks.cost_governor_decision_ref,
            ],
            [
              "Unknown paid cost",
              controlPlane.cost_hooks.unknown_paid_cost_blocks
                ? "blocked"
                : "allowed",
            ],
            [
              "Actual usage/cost refs",
              controlPlane.cost_hooks.actual_usage_cost_refs_required
                ? "required"
                : "missing",
            ],
            [
              "Provider spend authority",
              controlPlane.cost_hooks.provider_spend_authority_granted
                ? "granted"
                : "not granted",
            ],
          ]}
          blockerCodes={[
            "UNKNOWN_PAID_COST_BLOCKS",
            "ACTUAL_USAGE_COST_REFS_REQUIRED",
          ]}
        />
        <ReadinessGateCard
          title="Local llama.cpp lifecycle"
          status={controlPlane.local_llama_cpp_lifecycle.status}
          summary={controlPlane.local_llama_cpp_lifecycle.safe_summary}
          details={[
            [
              "Supervisor",
              controlPlane.local_llama_cpp_lifecycle.supervisor_contract_ref,
            ],
            [
              "Gateway",
              controlPlane.local_llama_cpp_lifecycle.gateway_contract_ref,
            ],
            [
              "Gateway mode",
              statusRecordValue(
                controlPlane.local_llama_cpp_lifecycle.gateway_readiness,
                "gateway_mode",
              ),
            ],
            [
              "Process start",
              controlPlane.local_llama_cpp_lifecycle
                .process_start_performed_by_read_model
                ? "performed"
                : "not performed",
            ],
            [
              "Model call",
              controlPlane.local_llama_cpp_lifecycle
                .model_call_performed_by_read_model
                ? "performed"
                : "not performed",
            ],
          ]}
          blockerCodes={
            controlPlane.local_llama_cpp_lifecycle.cli_inspection_refs
          }
        />
        <ReadinessGateCard
          title="ModelRouter traces"
          status={trace?.status ?? "not available"}
          summary={
            trace?.safe_summary ??
            "ModelRouter trace was not available from the backend read model."
          }
          details={[
            ["Trace ref", trace?.trace_ref ?? "not reported"],
            [
              "Selected profile",
              trace?.selected_profile_ref ?? "not selected",
            ],
            ["Selected model", trace?.selected_model_ref ?? "not selected"],
            [
              "Provider router trace",
              trace?.provider_router_trace_ref ?? "not reported",
            ],
            [
              "Model execution",
              trace?.model_execution_performed ? "performed" : "not performed",
            ],
            [
              "Provider execution",
              trace?.provider_execution_performed
                ? "performed"
                : "not performed",
            ],
          ]}
          blockerCodes={trace?.reason_codes ?? ["NO_TRACE_AVAILABLE"]}
        />
        <ReadinessGateCard
          title="Model/provider research posture"
          status={researchPosture.status}
          summary={researchPosture.model_output_truth.safe_summary}
          details={[
            ["Contract", researchPosture.contract_ref],
            ["Providers summarized", String(researchPosture.provider_count)],
            [
              "First provider",
              firstProviderPosture?.provider_label ?? "not reported",
            ],
            [
              "First provider status",
              firstProviderPosture?.status ?? "not reported",
            ],
            [
              "Model output truth",
              researchPosture.model_output_truth.status,
            ],
            [
              "Memory/action escalation",
              researchPosture.memory_write_authorized ||
              researchPosture.action_execution_authorized
                ? "enabled"
                : "blocked",
            ],
          ]}
          blockerCodes={[
            researchPosture.model_output_truth.truth_boundary_ref,
            ...researchPosture.blocked_authority_refs.slice(0, 5),
          ]}
        />
        <ReadinessGateCard
          title="External information posture"
          status={externalPosture.status}
          summary={externalPosture.safe_summary}
          details={[
            [
              "Web runtime contract",
              externalPosture.web_runtime_authority_contract_ref,
            ],
            [
              "Gateway required",
              externalPosture.web_access_gateway_required ? "yes" : "no",
            ],
            [
              "Default policy",
              externalPosture.default_policy_denied ? "denied" : "open",
            ],
            [
              "Fetched content",
              externalPosture.fetched_content_untrusted
                ? "untrusted evidence"
                : "trusted",
            ],
            [
              "Browser action",
              externalPosture.browser_action_enabled_by_control_plane
                ? "enabled"
                : "blocked",
            ],
            [
              "Source metadata",
              externalPosture.source_metadata_required ? "required" : "missing",
            ],
          ]}
          blockerCodes={[
            ...externalPosture.allowed_current_lane_refs,
            ...externalPosture.blocked_authority_refs.slice(0, 5),
          ]}
        />
      </div>
      <div
        className="note-list"
        aria-label="Model provider control plane blocked authorities"
      >
        {controlPlane.blocked_authority_refs.map((ref) => (
          <span key={ref}>{ref}</span>
        ))}
      </div>
    </article>
  );
}

export function EvidenceOperatorPanel({ data }: { data: ControlCenterData }) {
  const receiptStep = useOperatorStep(data, "receipt_audit_latency_rollback");
  const warningCount =
    (data.dashboard.warnings ?? []).length +
    (data.runtimeReadiness.warnings ?? []).length;

  return (
    <section
      className="page-section"
      aria-labelledby="evidence-operator-heading"
    >
      <OperatorHeader
        eyebrow="Local operator flow"
        headingId="evidence-operator-heading"
        heading="Evidence"
        status="redacted summaries"
        summary="Evidence is presented as bounded safe refs, receipts, gate summaries, latency posture, and rollback status. Source material is not rendered as the primary interface."
      />

      <div className="panel-grid">
        <article className="panel">
          <div className="panel-heading">
            <h3>Evidence lanes</h3>
            <span>{data.dashboard.foundation_gate_summary.status}</span>
          </div>
          <dl className="metadata-list">
            <div>
              <dt>Foundation Gate</dt>
              <dd>{data.dashboard.foundation_gate_summary.summary}</dd>
            </div>
            <div>
              <dt>Known warnings</dt>
              <dd>{warningCount}</dd>
            </div>
            <div>
              <dt>Receipt/audit step</dt>
              <dd>
                {receiptStep?.status ?? "not available from local summary"}
              </dd>
            </div>
          </dl>
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h3>Inspection boundaries</h3>
            <span>bounded</span>
          </div>
          <p>
            This surface links safe refs only. It does not expose source bodies,
            transcript content, provider details, or local machine details.
          </p>
          <div className="note-list" aria-label="Evidence route refs">
            {(receiptStep?.route_refs.length
              ? receiptStep.route_refs
              : ["/receipts", "/events"]
            ).map((route) => (
              <span key={route}>{route}</span>
            ))}
          </div>
        </article>
      </div>

      <EvidenceViewerPanel knowledge={data.m17Knowledge} />
    </section>
  );
}

export function SettingsOperatorPanel({ data }: { data: ControlCenterData }) {
  const localModelStep = useOperatorStep(data, "local_model_readiness");
  const taskStep = useOperatorStep(data, "task_decomposition_plan");
  const settingsStatus = data.settingsStatus;
  const settingsStatusRecord = settingsStatus as unknown as Record<
    string,
    unknown
  >;
  const rawAuthorityPostures = Array.isArray(
    settingsStatusRecord.authority_postures,
  )
    ? settingsStatusRecord.authority_postures
    : [];
  const rawKillSwitchPostures = Array.isArray(
    settingsStatusRecord.kill_switch_postures,
  )
    ? settingsStatusRecord.kill_switch_postures
    : [];
  const rawFeatureFlagPostures = Array.isArray(
    settingsStatusRecord.feature_flag_postures,
  )
    ? settingsStatusRecord.feature_flag_postures
    : [];
  const safeAuthorityPostures = rawAuthorityPostures.filter(
    isSafeSettingsAuthorityPosture,
  );
  const authorityPosturesValid =
    safeAuthorityPostures.length === SETTINGS_AUTHORITY_KEYS.length &&
    safeAuthorityPostures.every(
      (posture, index) =>
        posture.capability_key === SETTINGS_AUTHORITY_KEYS[index],
    );
  const safeKillSwitchPostures = rawKillSwitchPostures.filter(
    isSafeSettingsKillSwitchPosture,
  );
  const safeFeatureFlagPostures = rawFeatureFlagPostures.filter(
    isSafeSettingsFeatureFlagPosture,
  );
  const disabledBoundaries = [
    ["Shell/subprocess authority", "not available from Control Center"],
    ["Browser/network automation", "not available from Control Center"],
    ["Connector writes", "not available from Control Center"],
    ["Plugin runtime import", "not available from Control Center"],
    ["Mobile control", "not available from Control Center"],
    ["Provider credential capture", "not collected by this screen"],
    ["Memory/context injection", "not available from Control Center"],
  ];

  return (
    <section className="page-section" aria-labelledby="settings-heading">
      <OperatorHeader
        eyebrow="Local operator flow"
        headingId="settings-heading"
        heading="Settings"
        status={settingsStatus.status}
        summary="Settings show backend-owned read-only maturity, feature-flag, kill-switch, route-safety, and blocked-authority posture. Mutation controls are not exposed."
      />

      <ProviderCatalogPanel catalog={data.providerCatalog} mode="settings" />

      <div className="panel-grid">
        <article className="panel">
          <div className="panel-heading">
            <h3>Backend-owned Settings status</h3>
            <span>{settingsStatus.maturity_gate_status}</span>
          </div>
          <p>{settingsStatus.safe_summary}</p>
          <dl className="metadata-list">
            <div>
              <dt>Route</dt>
              <dd>{settingsStatus.route_ref}</dd>
            </div>
            <div>
              <dt>Authority contract</dt>
              <dd>{settingsStatus.settings_authority_contract_ref}</dd>
            </div>
            <div>
              <dt>Feature flag posture</dt>
              <dd>{settingsStatus.feature_flag_posture}</dd>
            </div>
            <div>
              <dt>Kill switch posture</dt>
              <dd>{settingsStatus.kill_switch_posture}</dd>
            </div>
            <div>
              <dt>Route safety</dt>
              <dd>{settingsStatus.route_status_manifest_ref}</dd>
            </div>
            <div>
              <dt>Maturity manifest</dt>
              <dd>{settingsStatus.maturity_manifest_ref}</dd>
            </div>
            <div>
              <dt>Runtime matrix</dt>
              <dd>{settingsStatus.runtime_capability_matrix_ref}</dd>
            </div>
            <div>
              <dt>Platform snapshot</dt>
              <dd>{settingsStatus.platform_capability_snapshot_ref}</dd>
            </div>
            <div>
              <dt>Proposal review only</dt>
              <dd>{settingsStatus.proposal_review_only ? "yes" : "no"}</dd>
            </div>
          </dl>
          <div
            className="note-list"
            aria-label="Settings blocked authority classes"
          >
            {settingsStatus.blocked_authorities.map((authority, index) => (
              <span key={`${authority}-${index}`}>{authority}</span>
            ))}
          </div>
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h3>Local setup status</h3>
            <span>{data.connection.state}</span>
          </div>
          <dl className="metadata-list">
            <div>
              <dt>API base</dt>
              <dd>{data.connection.apiBaseLabel}</dd>
            </div>
            <div>
              <dt>Local gateway</dt>
              <dd>{localModelStep?.status ?? "not reported"}</dd>
            </div>
            <div>
              <dt>Task decomposition</dt>
              <dd>{taskStep?.status ?? "not reported"}</dd>
            </div>
            <div>
              <dt>Mock fallback</dt>
              <dd>{data.connection.usingMockData ? "yes" : "no"}</dd>
            </div>
          </dl>
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h3>Non-secret setup guidance</h3>
            <span>local only</span>
          </div>
          <ul className="compact-list">
            <li>
              <strong>Review prerequisites</strong>
              <small>
                Use the local setup helper and review safe findings before
                starting services.
              </small>
            </li>
            <li>
              <strong>Review local launcher path</strong>
              <small>
                Use the launcher path documented for loopback-only backend and
                frontend.
              </small>
            </li>
            <li>
              <strong>Review OpenWebUI loopback reference</strong>
              <small>
                Point OpenWebUI at UAA&apos;s local /v1 gateway with the
                configured local bearer.
              </small>
            </li>
          </ul>
        </article>
        <ProviderCredentialReadinessPanel
          readiness={data.dashboard.provider_credential_readiness}
        />
      </div>

      <div
        className="operator-boundary-list"
        aria-label="Settings authority posture labels"
      >
        {authorityPosturesValid ? (
          safeAuthorityPostures.map((posture) => (
            <article
              className={`surface-state-card ${settingsPostureClass(
                posture.state_label,
              )}`}
              aria-label={`${posture.label} ${posture.state_label}`}
              key={posture.capability_key}
              role="status"
            >
              <span className="surface-state-kind">{posture.state_label}</span>
              <strong>{posture.label}</strong>
              <p>{posture.safe_summary}</p>
              <div className="note-list" aria-label={`${posture.label} refs`}>
                {posture.source_refs.slice(0, 3).map((ref) => (
                  <span key={ref}>{ref}</span>
                ))}
              </div>
              <small>{posture.next_safe_action}</small>
            </article>
          ))
        ) : (
          <article
            aria-label="Settings authority posture blocked"
            className="surface-state-card blocked"
            role="status"
          >
            <span className="surface-state-kind">Blocked</span>
            <strong>Settings authority posture unavailable</strong>
            <p>
              Backend Settings authority rows failed validation. Runtime,
              provider, connector, memory, model, lifecycle, and platform
              authority remain blocked.
            </p>
            <small>
              Next safe action: inspect the backend Settings status route and
              verifier before trusting labels.
            </small>
          </article>
        )}
      </div>

      <div
        className="operator-boundary-list"
        aria-label="Settings kill-switch and feature-flag posture"
      >
        {safeKillSwitchPostures.map((posture) => (
          <article
            className="surface-state-card blocked"
            aria-label={`Kill switch: ${posture.label}`}
            key={posture.posture_ref}
            role="status"
          >
            <span className="surface-state-kind">{posture.state_label}</span>
            <strong>Kill switch: {posture.label}</strong>
            <p>{posture.safe_summary}</p>
            <div
              className="note-list"
              aria-label={`${posture.label} kill-switch refs`}
            >
              <span>{posture.revocation_ref}</span>
              <span>{posture.safe_disable_ref}</span>
            </div>
            <small>{posture.next_safe_action}</small>
          </article>
        ))}
        {safeFeatureFlagPostures.map((posture) => (
          <article
            className="surface-state-card denied"
            aria-label={`Feature flag: ${posture.label}`}
            key={posture.posture_ref}
            role="status"
          >
            <span className="surface-state-kind">{posture.state_label}</span>
            <strong>Feature flag: {posture.label}</strong>
            <p>{posture.safe_summary}</p>
            <div
              className="note-list"
              aria-label={`${posture.label} feature-flag refs`}
            >
              <span>{posture.owner_ref}</span>
              {posture.evidence_refs.slice(0, 2).map((ref) => (
                <span key={ref}>{ref}</span>
              ))}
            </div>
            <small>{posture.next_safe_action}</small>
          </article>
        ))}
      </div>

      <div
        className="operator-boundary-list"
        aria-label="Disabled settings boundaries"
      >
        {disabledBoundaries.map(([label, state]) => (
          <article
            className="surface-state-card denied"
            aria-label={`${label} disabled`}
            key={label}
            role="status"
          >
            <span className="surface-state-kind">disabled</span>
            <strong>{label}</strong>
            <p>{state}</p>
            <small>
              Next safe action: require a scoped milestone before this can
              change.
            </small>
          </article>
        ))}
      </div>

      <OperatorSurfaceStates surface="Settings" />
    </section>
  );
}

function settingsPostureClass(stateLabel: string) {
  if (stateLabel === "Blocked") {
    return "blocked";
  }
  if (stateLabel === "Metadata only") {
    return "denied";
  }
  if (stateLabel === "Degraded" || stateLabel === "Partial") {
    return "partial";
  }
  return "blocked";
}

function isSafeSettingsAuthorityPosture(
  posture: unknown,
): posture is ControlCenterSettingsAuthorityPosture {
  if (!isSettingsRecord(posture)) {
    return false;
  }
  const capabilityKey = posture.capability_key;
  return (
    typeof capabilityKey === "string" &&
    SETTINGS_AUTHORITY_KEYS.includes(
      capabilityKey as (typeof SETTINGS_AUTHORITY_KEYS)[number],
    ) &&
    isOneOfString(posture.state_label, [
      "Blocked",
      "Degraded",
      "Partial",
      "Metadata only",
    ]) &&
    isNonEmptyString(posture.label) &&
    isNonEmptyString(posture.safe_summary) &&
    isNonEmptyString(posture.next_safe_action) &&
    isStringArray(posture.source_refs) &&
    posture.source_refs.length > 0 &&
    isStringArray(posture.blocked_authority_refs) &&
    posture.blocked_authority_refs.length > 0 &&
    posture.callable_runtime_authority === false &&
    posture.setting_toggle_grants_authority === false &&
    posture.provider_configuration_enabled === false &&
    posture.connector_write_enabled === false &&
    posture.context_injection_enabled === false &&
    posture.model_call_enabled === false &&
    posture.local_lifecycle_enabled === false &&
    posture.installer_behavior_enabled === false &&
    posture.production_authority_enabled === false &&
    posture.authority_from_visibility === false
  );
}

function isSafeSettingsKillSwitchPosture(
  posture: unknown,
): posture is ControlCenterSettingsKillSwitchPosture {
  if (!isSettingsRecord(posture)) {
    return false;
  }
  return (
    isOneOfString(posture.state_label, [
      "Not configured",
      "Blocked",
      "Metadata only",
    ]) &&
    isNonEmptyString(posture.label) &&
    isNonEmptyString(posture.safe_summary) &&
    isNonEmptyString(posture.revocation_ref) &&
    isNonEmptyString(posture.safe_disable_ref) &&
    posture.execution_enabled === false &&
    posture.revocation_execution_enabled === false &&
    posture.approval_revocation_enabled === false &&
    posture.authority_granted === false &&
    posture.production_authority_enabled === false
  );
}

function isSafeSettingsFeatureFlagPosture(
  posture: unknown,
): posture is ControlCenterSettingsFeatureFlagPosture {
  if (!isSettingsRecord(posture)) {
    return false;
  }
  return (
    isOneOfString(posture.state_label, [
      "Metadata only",
      "Blocked",
      "Partial",
    ]) &&
    isNonEmptyString(posture.label) &&
    isNonEmptyString(posture.safe_summary) &&
    isNonEmptyString(posture.owner_ref) &&
    isStringArray(posture.evidence_refs) &&
    posture.evidence_refs.length > 0 &&
    posture.writable === false &&
    posture.toggle_enabled === false &&
    posture.runtime_activation_enabled === false &&
    posture.authority_granted === false &&
    posture.production_authority_enabled === false
  );
}

function isSettingsRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function isStringArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) && value.every((item) => typeof item === "string")
  );
}

function isOneOfString(value: unknown, allowed: string[]): value is string {
  return typeof value === "string" && allowed.includes(value);
}

export function ProviderCredentialReadinessPanel({
  readiness,
}: {
  readiness: ProviderCredentialReadinessSummary;
}) {
  return (
    <article className="panel provider-credential-readiness-panel">
      <div className="panel-heading">
        <h3>Provider credential readiness</h3>
        <span>{readiness.status}</span>
      </div>
      <p>{readiness.safe_summary}</p>
      <ProviderSettingsDiagnosticsPanel
        diagnostics={readiness.provider_settings_diagnostics}
      />
      <dl className="metadata-list">
        <div>
          <dt>Provider invocation</dt>
          <dd>{readiness.invocation_enabled ? "yes" : "no"}</dd>
        </div>
        <div>
          <dt>Raw key collection</dt>
          <dd>{readiness.raw_key_collection_enabled ? "yes" : "no"}</dd>
        </div>
        <div>
          <dt>Credential material stored</dt>
          <dd>{readiness.credential_material_stored ? "yes" : "no"}</dd>
        </div>
        <div>
          <dt>Vault adapter</dt>
          <dd>
            {readiness.vault_adapter_configured ? "configured" : "not scoped"}
          </dd>
        </div>
        <div>
          <dt>Configured providers</dt>
          <dd>{readiness.posture_counts.configured}</dd>
        </div>
        <div>
          <dt>Not configured providers</dt>
          <dd>{readiness.posture_counts.not_configured}</dd>
        </div>
        <div>
          <dt>Revoked providers</dt>
          <dd>{readiness.posture_counts.revoked}</dd>
        </div>
        <div>
          <dt>Blocked provider postures</dt>
          <dd>{readiness.posture_counts.blocked}</dd>
        </div>
        <div>
          <dt>CostGovernor binding</dt>
          <dd>
            {readiness.cost_governor_binding_required
              ? "required"
              : "blocked posture missing"}
          </dd>
        </div>
        <div>
          <dt>Unknown paid cost</dt>
          <dd>
            {readiness.unknown_paid_cost_requires_approval
              ? "approval required"
              : "blocked posture missing"}
          </dd>
        </div>
        <div>
          <dt>Above-budget estimate</dt>
          <dd>
            {readiness.estimated_cost_above_budget_blocks_use
              ? "blocked"
              : "blocked posture missing"}
          </dd>
        </div>
        <div>
          <dt>Future receipt refs</dt>
          <dd>
            {readiness.future_receipt_refs_required
              ? "required"
              : "receipt posture missing"}
          </dd>
        </div>
        <div>
          <dt>Provider usage claims</dt>
          <dd>
            {readiness.provider_usage_claim_requires_receipt_refs
              ? "receipt-bound"
              : "receipt posture missing"}
          </dd>
        </div>
        <div>
          <dt>Credential adapter readiness</dt>
          <dd>{readiness.vault_adapter_readiness.readiness_status}</dd>
        </div>
        <div>
          <dt>Credential enrollment</dt>
          <dd>{readiness.enrollment_readiness.readiness_status}</dd>
        </div>
        <div>
          <dt>Validation readiness</dt>
          <dd>{readiness.validation_readiness.readiness_status}</dd>
        </div>
        <div>
          <dt>External validation</dt>
          <dd>
            {readiness.validation_readiness.external_validation_allowed
              ? "yes"
              : "no"}
          </dd>
        </div>
        <div>
          <dt>Validation authority</dt>
          <dd>
            {readiness.validation_readiness.exact_approval_required
              ? "approval required"
              : "authority missing"}
          </dd>
        </div>
        <div>
          <dt>Provider response persistence allowed</dt>
          <dd>
            {readiness.validation_readiness
              .provider_response_persistence_allowed
              ? "yes"
              : "no"}
          </dd>
        </div>
        <div>
          <dt>Invocation readiness</dt>
          <dd>{readiness.invocation_readiness.readiness_status}</dd>
        </div>
        <div>
          <dt>Tiny provider lane</dt>
          <dd>{readiness.tiny_invocation_readiness.status}</dd>
        </div>
        <div>
          <dt>Provider router dry-run</dt>
          <dd>{readiness.router_dry_run_readiness.status}</dd>
        </div>
        <div>
          <dt>Router no-authority refs</dt>
          <dd>{readiness.router_dry_run_readiness.no_authority_refs.length}</dd>
        </div>
      </dl>
      <div
        className="provider-readiness-list"
        aria-label="Provider credential readiness gates"
      >
        <ReadinessGateCard
          title="CostGovernor binding"
          status={
            readiness.cost_governor_binding_required
              ? "required"
              : "blocked posture missing"
          }
          summary="Provider/model refs, cost estimate refs, budget decisions, max-approved refs, and future receipt refs are required before any paid provider use."
          details={[
            ["Posture ref", readiness.cost_governor_posture_ref],
            ["Decision ref", readiness.cost_governor_decision_ref],
            [
              "Provider/model refs",
              readiness.provider_model_refs_required
                ? "required"
                : "blocked posture missing",
            ],
            [
              "Cost estimate ref",
              readiness.cost_estimate_ref_required
                ? "required"
                : "blocked posture missing",
            ],
            [
              "Budget decision ref",
              readiness.budget_decision_ref_required
                ? "required"
                : "blocked posture missing",
            ],
            [
              "Max approved USD ref",
              readiness.max_approved_usd_ref_required
                ? "required"
                : "blocked posture missing",
            ],
            [
              "Future receipts",
              readiness.future_receipt_refs_required
                ? "required"
                : "receipt posture missing",
            ],
          ]}
          blockerCodes={[
            "UNKNOWN_PAID_COST_REQUIRES_APPROVAL",
            "PROVIDER_MODEL_REFS_REQUIRED",
            "COST_ESTIMATE_REF_REQUIRED",
            "BUDGET_DECISION_REF_REQUIRED",
            "MAX_APPROVED_USD_REF_REQUIRED",
            "FUTURE_RECEIPT_REFS_REQUIRED",
            "PROVIDER_USAGE_CLAIM_REQUIRES_RECEIPT_REFS",
          ]}
        />
        <ReadinessGateCard
          title="Vault adapter contract"
          status={readiness.vault_adapter_readiness.readiness_status}
          summary={readiness.vault_adapter_readiness.safe_summary}
          details={[
            [
              "Storage backend",
              readiness.vault_adapter_readiness.storage_backend_kind,
            ],
            [
              "Adapter available",
              readiness.vault_adapter_readiness.adapter_available
                ? "yes"
                : "no",
            ],
            [
              "Vault write capability status",
              readiness.vault_adapter_readiness.supports_write
                ? "available"
                : "disabled",
            ],
            [
              "Handle resolution allowed",
              readiness.vault_adapter_readiness.supports_read_handle
                ? "yes"
                : "no",
            ],
            [
              "Revocation capability status",
              readiness.vault_adapter_readiness.supports_revoke
                ? "available"
                : "disabled",
            ],
            [
              "Repo-stored credential material",
              readiness.vault_adapter_readiness
                .credential_material_stored_by_repo
                ? "yes"
                : "no",
            ],
            [
              "Adapter runtime",
              readiness.vault_adapter_readiness.adapter_runtime_enabled
                ? "enabled"
                : "disabled",
            ],
            [
              "Last validation ref",
              readiness.vault_adapter_readiness.last_validation_ref,
            ],
          ]}
          blockerCodes={readiness.vault_adapter_readiness.blocker_codes}
        />
        <ReadinessGateCard
          title="Credential enrollment contract"
          status={readiness.enrollment_readiness.readiness_status}
          summary={readiness.enrollment_readiness.safe_summary}
          details={[
            [
              "Provider manifest ref",
              readiness.enrollment_readiness.provider_manifest_ref,
            ],
            ["Credential ref", readiness.enrollment_readiness.credential_ref],
            ["Consent ref", readiness.enrollment_readiness.consent_ref],
            ["Policy ref", readiness.enrollment_readiness.policy_ref],
            ["Approval ref", readiness.enrollment_readiness.approval_ref],
            ["Revocation ref", readiness.enrollment_readiness.revocation_ref],
            [
              "Enrollment",
              readiness.enrollment_readiness.enrollment_enabled
                ? "enabled"
                : "disabled",
            ],
            [
              "Idempotency ref",
              readiness.enrollment_readiness.idempotency_key_ref,
            ],
            ["Audit ref", readiness.enrollment_readiness.audit_ref],
            ["Rollback ref", readiness.enrollment_readiness.rollback_ref],
            [
              "Safe-disable ref",
              readiness.enrollment_readiness.safe_disable_ref,
            ],
            [
              "Raw key collection",
              readiness.enrollment_readiness.raw_key_collection_enabled
                ? "yes"
                : "no",
            ],
            [
              "Repo-stored credential material",
              readiness.enrollment_readiness.credential_material_stored_by_repo
                ? "yes"
                : "no",
            ],
            [
              "Evidence contains credential material",
              readiness.enrollment_readiness
                .evidence_contains_credential_material
                ? "yes"
                : "no",
            ],
          ]}
          blockerCodes={readiness.enrollment_readiness.blocker_codes}
        />
        <ReadinessGateCard
          title="Provider validation contract"
          status={readiness.validation_readiness.readiness_status}
          summary={readiness.validation_readiness.safe_summary}
          details={[
            ["Route", readiness.validation_readiness.route_ref],
            [
              "Provider manifest ref",
              readiness.validation_readiness.provider_manifest_ref,
            ],
            [
              "Validation enabled",
              readiness.validation_readiness.validation_enabled ? "yes" : "no",
            ],
            [
              "Approval required",
              readiness.validation_readiness.exact_approval_required
                ? "yes"
                : "no",
            ],
            [
              "No provider authority",
              readiness.validation_readiness.ui_states.includes(
                "no provider authority",
              )
                ? "shown"
                : "missing",
            ],
            [
              "Validation receipt ref",
              readiness.validation_readiness.validation_receipt_ref,
            ],
          ]}
          blockerCodes={readiness.validation_readiness.blocker_codes}
        />
        <ReadinessGateCard
          title="Governed provider invocation"
          status={readiness.invocation_readiness.readiness_status}
          summary={readiness.invocation_readiness.safe_summary}
          details={[
            [
              "PolicyEngine required",
              readiness.invocation_readiness.policy_engine_required
                ? "yes"
                : "no",
            ],
            [
              "Local approval required",
              readiness.invocation_readiness.local_approval_required
                ? "yes"
                : "no",
            ],
            [
              "Credential ref required",
              readiness.invocation_readiness.credential_ref_required
                ? "yes"
                : "no",
            ],
            [
              "Provider allowlist required",
              readiness.invocation_readiness
                .provider_manifest_allowlist_required
                ? "yes"
                : "no",
            ],
            [
              "Redacted request summary only",
              readiness.invocation_readiness.redacted_request_summary_only
                ? "yes"
                : "no",
            ],
            [
              "Redacted response summary only",
              readiness.invocation_readiness.redacted_response_summary_only
                ? "yes"
                : "no",
            ],
            [
              "Receipt refs required",
              readiness.invocation_readiness.receipt_refs_required
                ? "yes"
                : "no",
            ],
            [
              "Audit refs required",
              readiness.invocation_readiness.audit_refs_required ? "yes" : "no",
            ],
            [
              "Rollback or safe-disable required",
              readiness.invocation_readiness.rollback_or_safe_disable_required
                ? "yes"
                : "no",
            ],
            [
              "Rate or budget boundary required",
              readiness.invocation_readiness.rate_budget_boundary_required
                ? "yes"
                : "no",
            ],
            [
              "Streaming exposed",
              readiness.invocation_readiness.streaming_enabled ? "yes" : "no",
            ],
            [
              "Tools/functions exposed",
              readiness.invocation_readiness.tools_functions_enabled
                ? "yes"
                : "no",
            ],
            [
              "Memory writes",
              readiness.invocation_readiness.memory_write_enabled
                ? "yes"
                : "no",
            ],
            [
              "Context injection",
              readiness.invocation_readiness.context_injection_enabled
                ? "yes"
                : "no",
            ],
            [
              "Browser/network automation",
              readiness.invocation_readiness.browser_network_automation_enabled
                ? "yes"
                : "no",
            ],
            [
              "Connector writes",
              readiness.invocation_readiness.connector_writes_enabled
                ? "yes"
                : "no",
            ],
            [
              "Model output authoritative",
              readiness.invocation_readiness.model_output_authoritative
                ? "yes"
                : "no",
            ],
          ]}
          blockerCodes={readiness.invocation_readiness.blocker_codes}
        />
        <ReadinessGateCard
          title="Tiny exact-approved provider lane"
          status={readiness.tiny_invocation_readiness.status}
          summary={readiness.tiny_invocation_readiness.safe_summary}
          details={[
            ["Lane ref", readiness.tiny_invocation_readiness.lane_ref],
            ["Route ref", readiness.tiny_invocation_readiness.route_ref],
            ["Provider ref", readiness.tiny_invocation_readiness.provider_ref],
            ["Model ref", readiness.tiny_invocation_readiness.model_ref],
            [
              "Provider scope refs",
              readiness.tiny_invocation_readiness.provider_scope_refs.join(", "),
            ],
            [
              "Model scope refs",
              readiness.tiny_invocation_readiness.model_scope_refs.join(", "),
            ],
            [
              "Policy scope refs",
              readiness.tiny_invocation_readiness.policy_scope_refs.join(", "),
            ],
            [
              "Adapter scope refs",
              readiness.tiny_invocation_readiness.adapter_scope_refs.join(", "),
            ],
            [
              "Exact approval",
              readiness.tiny_invocation_readiness.exact_approval_required
                ? "required"
                : "missing",
            ],
            [
              "Credential ref",
              readiness.tiny_invocation_readiness.credential_ref_required
                ? "required"
                : "missing",
            ],
            [
              "Cost estimate ref",
              readiness.tiny_invocation_readiness.cost_estimate_ref_required
                ? "required"
                : "missing",
            ],
            [
              "Budget decision ref",
              readiness.tiny_invocation_readiness.budget_decision_ref_required
                ? "required"
                : "missing",
            ],
            [
              "Max approved USD",
              readiness.tiny_invocation_readiness.max_approved_usd_required
                ? "required"
                : "missing",
            ],
            [
              "Unknown paid cost",
              readiness.tiny_invocation_readiness.unknown_paid_cost_blocks
                ? "blocked"
                : "missing",
            ],
            [
              "Redacted receipts",
              readiness.tiny_invocation_readiness.redacted_receipts_only
                ? "only"
                : "missing",
            ],
            [
              "Actual usage ref",
              readiness.tiny_invocation_readiness.actual_usage_ref_required
                ? "required"
                : "missing",
            ],
            [
              "Actual cost ref",
              readiness.tiny_invocation_readiness.actual_cost_ref_required
                ? "required"
                : "missing",
            ],
            [
              "Receipt completeness",
              readiness.tiny_invocation_readiness.receipt_completeness_required
                ? "required"
                : "missing",
            ],
            [
              "Receipt observation",
              readiness.tiny_invocation_readiness.receipt_state_source,
            ],
            [
              "Receipt observation ref",
              readiness.tiny_invocation_readiness.receipt_observation_ref,
            ],
            [
              "Receipt observation labels",
              readiness.tiny_invocation_readiness.receipt_observation_supported_states.join(
                ", ",
              ),
            ],
            [
              "Usage captured",
              readiness.tiny_invocation_readiness.usage_captured
                ? "receipt-backed"
                : "no receipt observed",
            ],
            [
              "Cost captured",
              readiness.tiny_invocation_readiness.cost_captured
                ? "receipt-backed"
                : "no receipt observed",
            ],
            [
              "Cost incomplete",
              readiness.tiny_invocation_readiness.cost_incomplete
                ? "review required"
                : "no receipt observed",
            ],
            [
              "Review required",
              readiness.tiny_invocation_readiness.review_required
                ? "required"
                : "no receipt observed",
            ],
            [
              "Further use blocked",
              readiness.tiny_invocation_readiness.further_use_blocked
                ? "blocked pending review"
                : "no receipt observed",
            ],
            [
              "Incomplete cost review",
              readiness.tiny_invocation_readiness.incomplete_cost_requires_review
                ? "required if cost incomplete observed"
                : "requires backend posture",
            ],
            [
              "Further provider use",
              readiness.tiny_invocation_readiness
                .incomplete_cost_blocks_further_use
                ? "blocks after incomplete cost"
                : "requires backend posture",
            ],
            [
              "Provider SDK",
              readiness.tiny_invocation_readiness.provider_sdk_call_enabled
                ? "blocked"
                : "disabled",
            ],
            [
              "Network call",
              readiness.tiny_invocation_readiness.network_call_enabled
                ? "scoped adapter only"
                : "disabled by default",
            ],
            [
              "Live adapter",
              readiness.tiny_invocation_readiness.ui_states.includes(
                "Live adapter blocked",
              )
                ? "blocked"
                : "not scoped",
            ],
            [
              "Live receipt",
              readiness.tiny_invocation_readiness.ui_states.includes(
                "Live receipt required",
              )
                ? "required"
                : "not recorded",
            ],
            [
              "Autonomous calls",
              readiness.tiny_invocation_readiness.autonomous_model_call_enabled
                ? "blocked"
                : "disabled",
            ],
            [
              "Billing authority",
              readiness.tiny_invocation_readiness.billing_authority_granted
                ? "blocked until exact billing scope"
                : "not granted",
            ],
            [
              "Provider authority label",
              readiness.tiny_invocation_readiness.invocation_enabled
                ? "exact scope required"
                : "No provider authority",
            ],
            [
              "Default execution label",
              readiness.tiny_invocation_readiness.status ===
              "approved_no_execution"
                ? "Approved no execution"
                : "Disabled no execution",
            ],
          ]}
          blockerCodes={[
            ...readiness.tiny_invocation_readiness.blocker_codes,
            ...readiness.tiny_invocation_readiness.ui_states.filter(
              (state) =>
                ![
                  "Usage captured",
                  "Cost captured",
                  "Cost incomplete",
                  "Review required",
                  "Further use blocked",
                ].includes(state),
            ),
          ]}
        />
        <ReadinessGateCard
          title="Provider router dry-run"
          status={readiness.router_dry_run_readiness.status}
          summary={readiness.router_dry_run_readiness.safe_summary}
          details={[
            ["Contract", readiness.router_dry_run_readiness.contract_ref],
            ["Route ref", readiness.router_dry_run_readiness.route_ref],
            ["Proposal ref", readiness.router_dry_run_readiness.proposal_ref],
            [
              "Recommended exact scope",
              readiness.router_dry_run_readiness
                .recommended_exact_approval_scope_ref,
            ],
            [
              "Exact-approval candidate refs",
              String(
                readiness.router_dry_run_readiness.eligible_provider_refs
                  .length,
              ),
            ],
            [
              "Blocked provider refs",
              String(
                readiness.router_dry_run_readiness.blocked_provider_refs
                  .length,
              ),
            ],
            [
              "Degraded provider refs",
              String(
                readiness.router_dry_run_readiness.degraded_provider_refs
                  .length,
              ),
            ],
            [
              "Missing credential refs",
              String(
                readiness.router_dry_run_readiness.missing_credential_refs
                  .length,
              ),
            ],
            [
              "Cost risky",
              String(readiness.router_dry_run_readiness.cost_risky_refs.length),
            ],
            [
              "Validation required",
              String(
                readiness.router_dry_run_readiness.validation_required_refs
                  .length,
              ),
            ],
            [
              "No provider authority",
              String(
                readiness.router_dry_run_readiness.no_authority_refs.length,
              ),
            ],
            [
              "No fallback execution",
              readiness.router_dry_run_readiness.fallback_execution_authorized
                ? "blocked"
                : "not authorized",
            ],
            [
              "Provider SDK",
              readiness.router_dry_run_readiness.provider_sdk_call_performed
                ? "blocked"
                : "not performed",
            ],
            [
              "Credential validation",
              readiness.router_dry_run_readiness.credential_validation_performed
                ? "blocked"
                : "not performed",
            ],
            [
              "Model invocation",
              readiness.router_dry_run_readiness.model_invocation_performed
                ? "blocked"
                : "not performed",
            ],
            [
              "Billing authority",
              readiness.router_dry_run_readiness.billing_authority_granted
                ? "blocked"
                : "not granted",
            ],
          ]}
          blockerCodes={[
            ...readiness.router_dry_run_readiness.blocker_codes,
            ...readiness.router_dry_run_readiness.ui_states,
          ]}
        />
      </div>
      <div
        className="provider-readiness-list"
        aria-label="Provider auth reference statuses"
      >
        {readiness.providers.map((provider) => (
          <section
            className="provider-readiness-item"
            key={provider.provider_id}
          >
            <div className="panel-heading compact-heading">
              <h4>{provider.provider_label}</h4>
              <span>{provider.readiness_posture}</span>
            </div>
            <p>{provider.safe_summary}</p>
            <dl className="metadata-list">
              <div>
                <dt>Readiness status</dt>
                <dd>{provider.readiness_status}</dd>
              </div>
              <div>
                <dt>Provider auth ref status</dt>
                <dd>{provider.credential_ref_status}</dd>
              </div>
              <div>
                <dt>Consent ref</dt>
                <dd>{provider.consent_ref}</dd>
              </div>
              <div>
                <dt>Policy ref</dt>
                <dd>{provider.policy_ref}</dd>
              </div>
              <div>
                <dt>Revocation ref</dt>
                <dd>{provider.revocation_ref}</dd>
              </div>
              <div>
                <dt>Approval ref</dt>
                <dd>{provider.approval_ref}</dd>
              </div>
              <div>
                <dt>Credential material visible</dt>
                <dd>{provider.raw_key_visible ? "yes" : "no"}</dd>
              </div>
              <div>
                <dt>Cost estimate ref</dt>
                <dd>{provider.cost_governor_binding.cost_estimate_ref}</dd>
              </div>
              <div>
                <dt>Budget decision ref</dt>
                <dd>{provider.cost_governor_binding.budget_decision_ref}</dd>
              </div>
              <div>
                <dt>Max approved USD ref</dt>
                <dd>{provider.cost_governor_binding.max_approved_usd_ref}</dd>
              </div>
              <div>
                <dt>Cost receipt ref</dt>
                <dd>{provider.cost_governor_binding.cost_receipt_ref}</dd>
              </div>
              <div>
                <dt>CostGovernor decision</dt>
                <dd>
                  {provider.cost_governor_binding.cost_governor_decision_ref}
                </dd>
              </div>
              <div>
                <dt>Model ref status</dt>
                <dd>{provider.cost_governor_binding.model_ref_status}</dd>
              </div>
            </dl>
            <div
              className="note-list"
              aria-label={`${provider.provider_label} blocker codes`}
            >
              {provider.blocker_codes.map((code) => (
                <span key={code}>{code}</span>
              ))}
            </div>
          </section>
        ))}
      </div>
    </article>
  );
}

function ProviderSettingsDiagnosticsPanel({
  diagnostics,
}: {
  diagnostics: ProviderSettingsDiagnosticsSummary;
}) {
  return (
    <section
      className="provider-settings-diagnostics"
      aria-label="Provider and Settings diagnostics"
    >
      <div className="panel-heading compact-heading">
        <h4>Provider and Settings diagnostics</h4>
        <span>{diagnostics.status}</span>
      </div>
      <p>{diagnostics.safe_summary}</p>
      <dl className="metadata-list">
        <div>
          <dt>Missing</dt>
          <dd>{diagnostics.state_counts.missing}</dd>
        </div>
        <div>
          <dt>Cost blocked</dt>
          <dd>{diagnostics.state_counts.cost_blocked}</dd>
        </div>
        <div>
          <dt>Disabled</dt>
          <dd>{diagnostics.state_counts.disabled}</dd>
        </div>
        <div>
          <dt>Future scoped</dt>
          <dd>{diagnostics.state_counts.future_scoped}</dd>
        </div>
        <div>
          <dt>Revoked</dt>
          <dd>{diagnostics.state_counts.revoked}</dd>
        </div>
        <div>
          <dt>Expired</dt>
          <dd>{diagnostics.state_counts.expired}</dd>
        </div>
      </dl>
      <div
        className="note-list"
        aria-label="Provider and Settings diagnostics CLI refs"
      >
        {diagnostics.cli_inspection_refs.map((ref) => (
          <span key={ref}>{ref}</span>
        ))}
      </div>
      <div
        className="provider-readiness-list"
        aria-label="Provider and Settings diagnostic items"
      >
        {diagnostics.items.map((item) => (
          <section
            className={`provider-readiness-item ${providerDiagnosticClass(
              item.state,
            )}`}
            key={item.diagnostic_ref}
          >
            <div className="panel-heading compact-heading">
              <h4>{item.label}</h4>
              <span>{item.state_label}</span>
            </div>
            <p>{item.safe_summary}</p>
            <dl className="metadata-list">
              <div>
                <dt>Provider ref</dt>
                <dd>{item.provider_ref}</dd>
              </div>
              <div>
                <dt>Credential ref</dt>
                <dd>{item.credential_ref}</dd>
              </div>
              <div>
                <dt>Next safe action</dt>
                <dd>{item.next_safe_action}</dd>
              </div>
            </dl>
            <div
              className="note-list"
              aria-label={`${item.label} diagnostic reason codes`}
            >
              {item.reason_codes.slice(0, 5).map((code) => (
                <span key={code}>{code}</span>
              ))}
            </div>
            <div
              className="note-list"
              aria-label={`${item.label} inspection refs`}
            >
              {item.cli_inspection_refs.slice(0, 3).map((ref) => (
                <span key={ref}>{ref}</span>
              ))}
            </div>
          </section>
        ))}
      </div>
      <p className="safe-copy">Next safe action: {diagnostics.next_safe_action}</p>
    </section>
  );
}

function providerDiagnosticClass(state: string) {
  if (state === "configured") {
    return "ready";
  }
  if (state === "degraded") {
    return "degraded";
  }
  if (state === "future_scoped") {
    return "planned";
  }
  return "blocked";
}

function ReadinessGateCard({
  title,
  status,
  summary,
  details,
  blockerCodes,
}: {
  title: string;
  status: string;
  summary: string;
  details: Array<[string, string]>;
  blockerCodes: string[];
}) {
  return (
    <section className="provider-readiness-item">
      <div className="panel-heading compact-heading">
        <h4>{title}</h4>
        <span>{status}</span>
      </div>
      <p>{summary}</p>
      <dl className="metadata-list">
        {details.map(([label, value], index) => (
          <div key={`${label}-${index}`}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      <div className="note-list" aria-label={`${title} blocker codes`}>
        {blockerCodes.map((code, index) => (
          <span key={`${code}-${index}`}>{code}</span>
        ))}
      </div>
    </section>
  );
}

function OperatorHeader({
  eyebrow,
  headingId,
  heading,
  status,
  summary,
}: {
  eyebrow: string;
  headingId?: string;
  heading: string;
  status: string;
  summary: string;
}) {
  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2 id={headingId}>{heading}</h2>
        </div>
        <span className="status-pill compact">{status}</span>
      </div>
      <p className="section-copy">{summary}</p>
    </>
  );
}

function StatusPanel({
  title,
  state,
  message,
  details,
  reasonCodes,
}: {
  title: string;
  state: OperatorRouteInspectionState;
  message: string;
  details: Array<[string, string]>;
  reasonCodes: string[];
}) {
  return (
    <article className={`panel operator-status-panel ${state}`}>
      <div className="panel-heading">
        <h3>{title}</h3>
        <span>{statusLabel(state)}</span>
      </div>
      <p>{message}</p>
      <dl className="metadata-list">
        {details.map(([label, value], index) => (
          <div key={`${label}-${index}`}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      {reasonCodes.length > 0 ? (
        <div className="note-list" aria-label={`${title} reason codes`}>
          {reasonCodes.map((reason, index) => (
            <span key={`${reason}-${index}`}>{reason}</span>
          ))}
        </div>
      ) : null}
    </article>
  );
}

function OperatorStepStrip({
  steps,
}: {
  steps: Array<OperatorLoopStepSummary | undefined>;
}) {
  const safeSteps = steps.filter((step): step is OperatorLoopStepSummary =>
    Boolean(step),
  );
  if (safeSteps.length === 0) {
    return (
      <EmptyState
        title="No local operator step summary"
        message="The local backend did not provide safe operator loop metadata for this screen."
      />
    );
  }
  return (
    <div
      className="operator-step-strip"
      aria-label="Related operator loop steps"
    >
      {safeSteps.map((step) => (
        <article className="review-card" key={step.step_id}>
          <div className="review-card-heading">
            <h3>{step.label}</h3>
            <span>{step.status}</span>
          </div>
          <p>{step.safe_summary}</p>
          <dl className="detail-grid">
            <div>
              <dt>Boundary</dt>
              <dd>{step.authority_boundary}</dd>
            </div>
            <div>
              <dt>Approval</dt>
              <dd>
                {step.approval_required
                  ? "required"
                  : "not required for inspection"}
              </dd>
            </div>
            <div>
              <dt>Routes</dt>
              <dd>
                {step.route_refs.length > 0
                  ? step.route_refs.join(", ")
                  : "none"}
              </dd>
            </div>
            <div>
              <dt>Evidence refs</dt>
              <dd>
                {step.evidence_refs.length > 0
                  ? step.evidence_refs.join(", ")
                  : "none"}
              </dd>
            </div>
          </dl>
          <p className="safe-copy">Next safe action: {step.next_safe_action}</p>
        </article>
      ))}
    </div>
  );
}

function useOperatorStep(
  data: ControlCenterData,
  stepId: string,
): OperatorLoopStepSummary | undefined {
  return useMemo(
    () =>
      data.dashboard.operator_loop_summary?.steps.find(
        (step) => step.step_id === stepId,
      ),
    [data.dashboard.operator_loop_summary?.steps, stepId],
  );
}

function statusLabel(state: OperatorRouteInspectionState): string {
  switch (state) {
    case "ready":
      return "ready";
    case "blocked":
      return "blocked";
    case "denied":
      return "denied";
    case "degraded":
      return "degraded";
    case "unavailable":
      return "unavailable";
    case "checking":
    default:
      return "checking";
  }
}

function statusRecordValue(
  record: Record<string, unknown>,
  key: string,
): string {
  const value = record[key];
  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }
  return "not reported";
}

const initialModelsStatus: LocalModelsInspectionStatus = {
  state: "checking",
  routeRef: API_ENDPOINTS.localModels,
  checkedAt: "",
  safeMessage:
    "Checking local model route readiness without loading or starting a model.",
  modelIds: [],
  selectedModelId: DEFAULT_MODEL_ID,
  reasonCodes: ["LOCAL_MODELS_CHECK_PENDING"],
};
