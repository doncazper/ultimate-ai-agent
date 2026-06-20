import type { OperatorLoopSummary, OperatorLoopStepSummary } from "../api/types";
import { EmptyState } from "./DataState";

const fallbackOperatorLoopSummary: OperatorLoopSummary = {
  loop_id: "operator_loop_summary_missing",
  milestone_ref: "UAA-P1-011",
  status: "summary_missing",
  safe_summary: "Operator loop summary is unavailable from the local backend.",
  backend_authority: "Python Agent Core and LocalApprovalAuthority remain authoritative.",
  frontend_authority: false,
  production_ready: false,
  read_only_dashboard: true,
  control_center_mutation_allowed: false,
  model_output_authoritative: false,
  prompt_content_recording_allowed: false,
  provider_payload_recording_allowed: false,
  steps: [],
  blocked_prerequisites: ["OPERATOR_LOOP_SUMMARY_MISSING"],
  inspection_route_refs: [],
  next_safe_action: "inspect_local_backend_dashboard_response",
  metadata: { backend_authority_only: true },
};

export function OperatorLoopPanel({ summary }: { summary?: OperatorLoopSummary }) {
  const safeSummary = summary ?? fallbackOperatorLoopSummary;

  return (
    <section className="page-section" aria-labelledby="operator-loop-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">UAA-P1-011</p>
          <h2 id="operator-loop-heading">Operator Loop</h2>
        </div>
        <span className="status-pill compact">{safeSummary.status}</span>
      </div>
      <p className="section-copy">
        {safeSummary.safe_summary}
      </p>
      <p className="safe-copy">{safeSummary.backend_authority}</p>

      <div className="panel-grid" aria-label="Operator loop authority boundaries">
        <BoundaryPanel label="Frontend authority" enabled={safeSummary.frontend_authority} />
        <BoundaryPanel
          label="Mutation allowed"
          enabled={safeSummary.control_center_mutation_allowed}
        />
        <BoundaryPanel
          label="Production readiness claim"
          enabled={safeSummary.production_ready}
        />
        <BoundaryPanel
          label="Model output authoritative"
          enabled={safeSummary.model_output_authoritative}
        />
        <BoundaryPanel
          label="Prompt content recording"
          enabled={safeSummary.prompt_content_recording_allowed}
        />
        <BoundaryPanel
          label="Provider payload recording"
          enabled={safeSummary.provider_payload_recording_allowed}
        />
      </div>

      {safeSummary.steps.length > 0 ? (
        <div className="review-list" aria-label="Operator loop steps">
          {safeSummary.steps.map((step) => (
            <OperatorLoopStepCard key={step.step_id} step={step} />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No operator loop steps"
          message="No first product loop summary steps were returned by the local contract."
        />
      )}

      <div className="note-list" aria-label="Operator loop route refs">
        {safeSummary.inspection_route_refs.map((routeRef) => (
          <span key={routeRef}>{routeRef}</span>
        ))}
      </div>
      <div className="note-list" aria-label="Operator loop prerequisites">
        {safeSummary.blocked_prerequisites.map((prerequisite) => (
          <span key={prerequisite}>{prerequisite}</span>
        ))}
      </div>
      <p className="safe-copy">Next safe action: {safeSummary.next_safe_action}</p>
    </section>
  );
}

function BoundaryPanel({ label, enabled }: { label: string; enabled: boolean }) {
  return (
    <article className="panel">
      <div className="panel-heading">
        <h3>{label}</h3>
        <span>{enabled ? "yes" : "no"}</span>
      </div>
      <p>
        {enabled
          ? "Backend alignment is required before this can be treated as authority."
          : "This Control Center surface exposes inspection metadata only."}
      </p>
    </article>
  );
}

function OperatorLoopStepCard({ step }: { step: OperatorLoopStepSummary }) {
  return (
    <article className="panel" aria-label={`${step.label} operator loop step`}>
      <div className="panel-heading">
        <h3>{step.label}</h3>
        <span>{step.status}</span>
      </div>
      <p>{step.safe_summary}</p>
      <dl className="metadata-list">
        <div>
          <dt>Step ref</dt>
          <dd>{step.step_id}</dd>
        </div>
        <div>
          <dt>Boundary</dt>
          <dd>{step.authority_boundary}</dd>
        </div>
        <div>
          <dt>Routes</dt>
          <dd>{step.route_refs.length > 0 ? step.route_refs.join(", ") : "none"}</dd>
        </div>
        <div>
          <dt>Evidence refs</dt>
          <dd>{step.evidence_refs.length > 0 ? step.evidence_refs.join(", ") : "none"}</dd>
        </div>
        <div>
          <dt>Backend authority required</dt>
          <dd>{step.backend_authority_required ? "yes" : "no"}</dd>
        </div>
        <div>
          <dt>Approval required</dt>
          <dd>{step.approval_required ? "yes" : "no"}</dd>
        </div>
        <div>
          <dt>Frontend authority</dt>
          <dd>{step.frontend_authority ? "yes" : "no"}</dd>
        </div>
        <div>
          <dt>Next safe action</dt>
          <dd>{step.next_safe_action}</dd>
        </div>
      </dl>
    </article>
  );
}
