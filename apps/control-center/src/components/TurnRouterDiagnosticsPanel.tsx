import { FormEvent, useEffect, useMemo, useState } from "react";
import { submitTurnRouterPreview } from "../api/client";
import { containsSecretLike, sanitizeForDisplay } from "../api/redaction";
import type {
  TurnRouterNoEffectProof,
  TurnRouterPolicySummary,
  TurnRouterPreviewReadModel,
  TurnRouterPreviewSampleId,
} from "../api/types";
import { SafeAlert } from "./SafeAlert";

type PreviewSource = "backend_owned" | "mock_fallback";

const samples: Array<{
  id: TurnRouterPreviewSampleId;
  label: string;
  expectedContract: string;
  summary: string;
}> = [
  {
    id: "diy-desk",
    label: "DIY desk",
    expectedContract: "answer_directly",
    summary: "Lightweight direct answer with no memory, tools, planner, approval, or state.",
  },
  {
    id: "office-memory",
    label: "Office memory",
    expectedContract: "answer_with_reviewed_memory",
    summary: "Reviewed-memory posture with safe refs only and no memory write.",
  },
  {
    id: "shopping-list",
    label: "Shopping list",
    expectedContract: "draft_or_plan",
    summary: "Draft/proposal posture with no checkout or external side effect.",
  },
  {
    id: "current-lumber-prices",
    label: "Current lumber prices",
    expectedContract: "prepare_tool_or_action",
    summary: "Read-only tool-prep posture; no web fetch or action execution from the UI.",
  },
  {
    id: "order-materials",
    label: "Order materials",
    expectedContract: "approval_required",
    summary: "Exact approval boundary; no execution occurs from this diagnostic.",
  },
  {
    id: "card-pickup",
    label: "Card and pickup",
    expectedContract: "approval_required",
    summary: "Payment, credential, and booking risks require explicit approval.",
  },
  {
    id: "base-answer-bypass",
    label: "Base-answer bypass",
    expectedContract: "approval_required",
    summary: "Low-ceremony answer paths cannot bypass payment or action safety.",
  },
];

const proofLabels: Array<[keyof TurnRouterNoEffectProof, string]> = [
  ["no_runtime_model_call_performed", "Runtime model call"],
  ["no_provider_call_performed", "Provider call"],
  ["no_tool_execution_performed", "Tool execution"],
  ["no_action_execution_performed", "Action execution"],
  ["no_memory_content_retrieved", "Memory body retrieval"],
  ["no_memory_write_performed", "Memory write"],
  ["no_shell_subprocess_performed", "Shell or subprocess"],
  ["no_browser_network_performed", "Browser or network"],
  ["no_connector_write_performed", "Connector write"],
];

export function TurnRouterDiagnosticsPanel() {
  const [selectedSample, setSelectedSample] =
    useState<TurnRouterPreviewSampleId>("diy-desk");
  const [preview, setPreview] = useState<TurnRouterPreviewReadModel>(
    fallbackPreview("diy-desk"),
  );
  const [previewSource, setPreviewSource] =
    useState<PreviewSource>("mock_fallback");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string>();
  const [ephemeralText, setEphemeralText] = useState("");

  useEffect(() => {
    let cancelled = false;
    setPending(true);
    setError(undefined);
    void submitTurnRouterPreview({ sample_id: selectedSample })
      .then((result) => {
        if (!cancelled) {
          setPreview(result);
          setPreviewSource("backend_owned");
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setPreview(fallbackPreview(selectedSample));
          setPreviewSource("mock_fallback");
          setError(
            sanitizeForDisplay(
              caught instanceof Error
                ? caught.message
                : "Turn router preview unavailable.",
            ),
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setPending(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [selectedSample]);

  async function submitEphemeralText(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = ephemeralText.trim();
    if (text.length === 0) {
      return;
    }
    if (containsSecretLike({ text })) {
      setEphemeralText("");
      setError("Secret-like text was cleared before preview and was not submitted.");
      return;
    }
    setPending(true);
    setError(undefined);
    setEphemeralText("");
    try {
      const result = await submitTurnRouterPreview({ text });
      setPreview(result);
      setPreviewSource("backend_owned");
    } catch (caught) {
      setPreview(fallbackPreview(selectedSample));
      setPreviewSource("mock_fallback");
      setError(
        sanitizeForDisplay(
          caught instanceof Error
            ? caught.message
            : "Turn router preview unavailable.",
        ),
      );
    } finally {
      setPending(false);
    }
  }

  const activeSample = useMemo(
    () => samples.find((sample) => sample.id === selectedSample) ?? samples[0],
    [selectedSample],
  );
  const policy = preview.policy_summary;
  const posture = postureSummary(policy);
  const sourceTitle =
    previewSource === "backend_owned"
      ? "Backend-owned router preview"
      : "Non-authoritative mock fallback";
  const sourceMessage =
    previewSource === "backend_owned"
      ? "This panel is rendering the Python Core no-effect preview route. It is diagnostic only and does not grant execution authority."
      : "The backend preview route is unavailable; displayed sample posture is mock-only and cannot be used as product truth.";

  return (
    <section
      className="panel turn-router-diagnostics"
      aria-labelledby="turn-router-diagnostics-heading"
    >
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Turn contract router</p>
          <h2 id="turn-router-diagnostics-heading">Router Diagnostics</h2>
        </div>
        <span>POST /control-center/turn-router/preview</span>
      </div>

      <SafeAlert
        title={sourceTitle}
        message={error ? `${sourceMessage} Latest safe note: ${error}` : sourceMessage}
        tone={previewSource === "backend_owned" ? "info" : "warning"}
      />

      <div className="router-sample-grid" aria-label="Protected router samples">
        {samples.map((sample) => (
          <button
            className={
              sample.id === selectedSample
                ? "router-sample-button active"
                : "router-sample-button"
            }
            disabled={pending}
            key={sample.id}
            onClick={() => setSelectedSample(sample.id)}
            type="button"
          >
            <strong>{sample.label}</strong>
            <span>{sample.expectedContract}</span>
          </button>
        ))}
      </div>

      <form className="preview-form router-ephemeral-form" onSubmit={submitEphemeralText}>
        <label>
          Ephemeral one-shot text
          <input
            aria-label="Ephemeral one-shot router text"
            maxLength={500}
            onChange={(event) => setEphemeralText(event.target.value)}
            placeholder="Preview a local turn without saving raw text"
            value={ephemeralText}
          />
        </label>
        <button disabled={pending || ephemeralText.trim().length === 0} type="submit">
          {pending ? "Previewing" : "Preview turn"}
        </button>
      </form>

      <div className="router-result-grid">
        <article className="router-contract-card">
          <span>{preview.request_kind === "sample" ? activeSample.label : "Ephemeral text"}</span>
          <strong>{preview.selected_turn_contract}</strong>
          <p>{preview.request_kind === "sample" ? activeSample.summary : preview.safe_summary}</p>
          <small>
            Confidence {Math.round(preview.confidence * 100)} percent; raw text omitted:{" "}
            {preview.ephemeral_request_text_omitted ? "yes" : "no"}
          </small>
        </article>

        <article className="router-posture-card">
          <h3>{posture.title}</h3>
          <p>{posture.message}</p>
          <dl className="metadata-list">
            <div>
              <dt>Memory</dt>
              <dd>{policy.memory_scope}; write {enabledLabel(policy.memory_write_allowed)}</dd>
            </div>
            <div>
              <dt>Tools</dt>
              <dd>{policy.tool_policy}; execution {enabledLabel(policy.tool_execution_allowed)}</dd>
            </div>
            <div>
              <dt>State</dt>
              <dd>{policy.state_policy}; durable {enabledLabel(policy.durable_state)}</dd>
            </div>
            <div>
              <dt>Approval</dt>
              <dd>{policy.approval_policy}; required {enabledLabel(policy.approval_required)}</dd>
            </div>
          </dl>
        </article>
      </div>

      <div className="panel-grid">
        <article className="router-subpanel">
          <div className="panel-heading">
            <h3>Why</h3>
            <span>{preview.preview_ref}</span>
          </div>
          <div className="note-list" aria-label="Turn router reason refs">
            {preview.reason_refs.map((ref) => (
              <span key={ref}>{ref}</span>
            ))}
            {preview.risk_flags.map((flag) => (
              <span key={flag}>{flag}</span>
            ))}
          </div>
        </article>

        <article className="router-subpanel">
          <div className="panel-heading">
            <h3>No-effect proof</h3>
            <span>compiled only</span>
          </div>
          <dl className="metadata-list">
            {proofLabels.map(([key, label]) => (
              <div key={key}>
                <dt>{label}</dt>
                <dd>{preview.no_effect_proof[key] ? "not performed" : "unsafe flag"}</dd>
              </div>
            ))}
          </dl>
        </article>
      </div>

      <article className="router-blocked-card">
        <div className="panel-heading">
          <h3>Blocked Authority</h3>
          <span>diagnostic only</span>
        </div>
        <div className="note-list" aria-label="Turn router blocked authority refs">
          {preview.blocked_authority_refs.slice(0, 10).map((ref) => (
            <span key={ref}>{ref}</span>
          ))}
        </div>
      </article>
    </section>
  );
}

function postureSummary(policy: TurnRouterPolicySummary): {
  title: string;
  message: string;
} {
  if (policy.approval_required) {
    return {
      title: "Approval boundary",
      message:
        "The selected contract requires exact approval posture before any future consequential action. This diagnostic does not execute.",
    };
  }
  if (policy.memory_read_allowed) {
    return {
      title: "Reviewed-memory posture",
      message:
        "Reviewed memory refs may guide the answer, but memory bodies and writes stay out of this diagnostic surface.",
    };
  }
  if (policy.tool_policy !== "none") {
    return {
      title: "Read-only preparation",
      message:
        "The turn is routed toward preparation or proposal posture; runtime fetching and tools remain unavailable here.",
    };
  }
  return {
    title: "Lightweight answer posture",
    message:
      "Ordinary informational answers stay low ceremony with no memory, tools, planner, durable state, approval, or side effects.",
  };
}

function enabledLabel(value: boolean): string {
  return value ? "yes" : "no";
}

function fallbackPreview(sampleId: TurnRouterPreviewSampleId): TurnRouterPreviewReadModel {
  const sample = samples.find((candidate) => candidate.id === sampleId) ?? samples[0];
  const approvalRequired = sample.expectedContract === "approval_required";
  const memoryRead = sample.expectedContract === "answer_with_reviewed_memory";
  const toolPrep = sample.expectedContract === "prepare_tool_or_action";
  return {
    contract_ref: "contract-ref:turn-router-preview:v1",
    preview_ref: `turn-router-preview:mock:${sample.id}`,
    request_ref: `turn-router-preview-request:sample:${sample.id}`,
    request_kind: "sample",
    sample_id: sample.id,
    selected_turn_contract: sample.expectedContract,
    confidence: 0.91,
    reason_refs: [`reason-ref:turn-router-preview:mock:${sample.id}`],
    risk_flags: approvalRequired ? ["risk-flag:approval-boundary"] : [],
    policy_summary: {
      turn_contract: sample.expectedContract,
      memory_scope: memoryRead ? "reviewed_refs_only" : "none",
      memory_read_allowed: memoryRead,
      memory_write_allowed: false,
      tool_policy: toolPrep ? "read_only_tool_prep" : "none",
      tool_choice: "none",
      tool_execution_allowed: false,
      action_execution_allowed: false,
      workflow_execution_allowed: false,
      context_injection_allowed: false,
      approval_policy: approvalRequired ? "approval_required" : "not_required",
      approval_required: approvalRequired,
      planner: sample.expectedContract === "draft_or_plan",
      durable_state: false,
      state_policy: "none",
      prompt_profile: "diagnostic_preview",
      output_contract: "safe_summary_only",
      runtime_model_call_allowed: false,
      provider_call_allowed: false,
      shell_subprocess_allowed: false,
      browser_network_allowed: false,
      connector_write_allowed: false,
      side_effects_allowed: false,
      execution_ready: false,
    },
    no_effect_proof: {
      authority_granted: false,
      execution_permitted: false,
      no_runtime_model_call_performed: true,
      no_provider_call_performed: true,
      no_tool_execution_performed: true,
      no_action_execution_performed: true,
      no_workflow_execution_performed: true,
      no_context_injection_performed: true,
      no_memory_content_retrieved: true,
      no_memory_write_performed: true,
      no_durable_state_write_performed: true,
      no_shell_subprocess_performed: true,
      no_browser_network_performed: true,
      no_connector_write_performed: true,
      invocation_policy_compiled_only: true,
      raw_request_text_persisted: false,
    },
    blocked_authority_refs: [
      "blocked-state:turn-router-preview:no-runtime-model-call",
      "blocked-state:turn-router-preview:no-provider-call",
      "blocked-state:turn-router-preview:no-tool-execution",
      "blocked-state:turn-router-preview:no-action-execution",
      "blocked-state:turn-router-preview:no-memory-write",
      "blocked-state:turn-router-preview:no-shell-subprocess",
      "blocked-state:turn-router-preview:no-browser-network",
      "blocked-state:turn-router-preview:no-connector-write",
    ],
    lane_result_refs: [`turn-preflight-lane-result:mock:${sample.id}`],
    source_refs: ["source-ref:turn-router-preview:mock-fallback"],
    evidence_refs: ["evidence-ref:turn-router-preview:mock-fallback"],
    route_refs: ["/control-center/turn-router/preview"],
    redactions_applied: ["ephemeral_request_text_omitted"],
    safe_summary:
      "Non-authoritative fallback preview mirrors protected sample posture only.",
    raw_content_included: false,
    ephemeral_request_text_omitted: true,
  };
}
