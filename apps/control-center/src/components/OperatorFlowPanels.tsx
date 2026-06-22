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
  LocalModelsInspectionStatus,
  OperatorLoopStepSummary,
  OperatorRouteInspectionState,
  ProviderCredentialReadinessSummary,
  RedactedLocalChatProbeStatus,
} from "../api/types";
import { EmptyState } from "./DataState";
import { EvidenceViewerPanel } from "./EvidenceFileMemoryViewerPanel";
import { OperatorSurfaceStates } from "./OperatorSurfaceStates";

const DEFAULT_MODEL_ID = "uaa-llama-cpp-local";
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
  const [handoffPending, setHandoffPending] =
    useState<ChatHandoffTarget>();
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
        heading="Chat Local Operator"
        status={statusLabel(models.state)}
        summary="Control Center can probe a redacted local turn through UAA /v1, record a durable receipt, and show model, runtime, auth, and tool-denial truth without treating output as authority."
      />

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
          {probePending ? "Probing local turn" : "Probe redacted local turn"}
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

      {handoffReceipt ? (
        <article className="panel">
          <div className="panel-heading">
            <h3>Handoff receipt</h3>
            <span>{handoffReceipt.handoff_target}</span>
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
              <dd>{handoffReceipt.action_executed ? "enabled" : "blocked"}</dd>
            </div>
            <div>
              <dt>Plan execution</dt>
              <dd>{handoffReceipt.plan_executed ? "enabled" : "blocked"}</dd>
            </div>
            <div>
              <dt>Memory write</dt>
              <dd>
                {handoffReceipt.memory_write_performed ? "enabled" : "blocked"}
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
  const localModelStep = useOperatorStep(data, "local_model_readiness");
  const modelEntry = data.capabilityMatrix.entries.find((entry) =>
    entry.surface.toLowerCase().includes("model"),
  );

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
        heading="Models"
        status={statusLabel(models.state)}
        summary="Model readiness is shown as local gateway and runtime evidence only. GGUF selection, llama.cpp lifecycle control, and provider authority stay outside this UI."
      />

      <div className="operator-flow-grid">
        <StatusPanel
          title="Local model readiness"
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

      <OperatorStepStrip steps={[localModelStep]} />
      <OperatorSurfaceStates surface="Models" />
    </section>
  );
}

export function EvidenceOperatorPanel({ data }: { data: ControlCenterData }) {
  const receiptStep = useOperatorStep(data, "receipt_audit_latency_rollback");
  const warningCount =
    data.dashboard.warnings.length + data.runtimeReadiness.warnings.length;

  return (
    <section
      className="page-section"
      aria-labelledby="evidence-operator-heading"
    >
      <OperatorHeader
        eyebrow="Local operator flow"
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
        heading="Settings"
        status="inspection only"
        summary="Settings show safe local setup status and configuration boundaries. There is no browser settings mutation path or credential collection form."
      />

      <div className="panel-grid">
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
              <strong>Inspect prerequisites</strong>
              <small>
                Use the local setup helper and review safe findings before
                starting services.
              </small>
            </li>
            <li>
              <strong>Start UAA locally</strong>
              <small>
                Use the launcher path documented for loopback-only backend and
                frontend.
              </small>
            </li>
            <li>
              <strong>Connect OpenWebUI</strong>
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
        aria-label="Disabled settings boundaries"
      >
        {disabledBoundaries.map(([label, state]) => (
          <article
            className="surface-state-card denied"
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

function ProviderCredentialReadinessPanel({
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
          <dd>{readiness.vault_adapter_configured ? "configured" : "not scoped"}</dd>
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
          <dd>{readiness.validation_readiness.external_validation_allowed ? "yes" : "no"}</dd>
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
      </dl>
      <div
        className="provider-readiness-list"
        aria-label="Provider credential readiness gates"
      >
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
              readiness.vault_adapter_readiness.credential_material_stored_by_repo
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
              readiness.enrollment_readiness.evidence_contains_credential_material
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
            [
              "Provider manifest ref",
              readiness.validation_readiness.provider_manifest_ref,
            ],
            [
              "Validation enabled",
              readiness.validation_readiness.validation_enabled ? "yes" : "no",
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
              readiness.invocation_readiness.provider_manifest_allowlist_required
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
              readiness.invocation_readiness.memory_write_enabled ? "yes" : "no",
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
      </div>
      <div
        className="provider-readiness-list"
        aria-label="Provider auth reference statuses"
      >
        {readiness.providers.map((provider) => (
          <section className="provider-readiness-item" key={provider.provider_id}>
            <div className="panel-heading compact-heading">
              <h4>{provider.provider_label}</h4>
              <span>{provider.readiness_status}</span>
            </div>
            <p>{provider.safe_summary}</p>
            <dl className="metadata-list">
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
        {details.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      <div className="note-list" aria-label={`${title} blocker codes`}>
        {blockerCodes.map((code) => (
          <span key={code}>{code}</span>
        ))}
      </div>
    </section>
  );
}

function OperatorHeader({
  eyebrow,
  heading,
  status,
  summary,
}: {
  eyebrow: string;
  heading: string;
  status: string;
  summary: string;
}) {
  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2>{heading}</h2>
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
        {details.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      {reasonCodes.length > 0 ? (
        <div className="note-list" aria-label={`${title} reason codes`}>
          {reasonCodes.map((reason) => (
            <span key={reason}>{reason}</span>
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
