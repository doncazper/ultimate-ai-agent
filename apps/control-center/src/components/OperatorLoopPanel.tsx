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

const LOOP_STAGE_ORDER = [
  "runtime_health",
  "local_model_readiness",
  "uaa_v1_chat",
  "task_decomposition_plan",
  "safe_capability_approval",
  "receipt_audit_latency_rollback",
];

export function OperatorLoopPanel({ summary }: { summary?: OperatorLoopSummary }) {
  const safeSummary = summary ?? fallbackOperatorLoopSummary;
  const orderedSteps = orderOperatorLoopSteps(safeSummary.steps);
  const routeRefs = uniqueRouteRefs(orderedSteps, safeSummary.inspection_route_refs);
  const sideEffectClasses = uniqueSideEffectClasses(orderedSteps);
  const approvalStep = orderedSteps.find(
    (step) => step.step_id === "safe_capability_approval",
  );
  const evidenceStep = orderedSteps.find(
    (step) => step.step_id === "receipt_audit_latency_rollback",
  );

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

      <div className="panel-heading">
        <h3>First product loop proof</h3>
        <span>{safeSummary.milestone_ref}</span>
      </div>
      <div className="panel-grid" aria-label="First product loop proof">
        <ProofPanel
          label="Steps surfaced"
          value={String(orderedSteps.length)}
          detail="Readable loop sequence from runtime readiness through receipts and rollback inspection."
        />
        <ProofPanel
          label="Routes surfaced"
          value={String(routeRefs.length)}
          detail="Existing local API refs only; this panel does not introduce route authority."
        />
        <ProofPanel
          label="Blocked prerequisites"
          value={String(safeSummary.blocked_prerequisites.length)}
          detail="Blocked states stay visible so the next safe action is explicit."
        />
      </div>

      <div className="panel-grid" aria-label="Operator loop authority boundaries">
        <BoundaryPanel label="Frontend authority" enabled={safeSummary.frontend_authority} />
        <BoundaryPanel
          label="Frontend/generic mutation authority"
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

      <div className="panel-grid" aria-label="Approval and evidence proof">
        <article className="panel">
          <div className="panel-heading">
            <h3>Approval and evidence proof</h3>
            <span>inspection only</span>
          </div>
          <p>
            Approval refs are identifiers only. LocalApprovalAuthority-backed backend routes
            remain the only grant path for the safe capability approval step.
          </p>
          <dl className="metadata-list">
            <div>
              <dt>Approval step</dt>
              <dd>{approvalStep?.status ?? "not surfaced"}</dd>
            </div>
            <div>
              <dt>Approval route refs</dt>
              <dd>{approvalStep ? formatList(approvalStep.route_refs) : "none"}</dd>
            </div>
            <div>
              <dt>Receipt and audit refs</dt>
              <dd>{evidenceStep ? formatList(evidenceStep.evidence_refs) : "none"}</dd>
            </div>
            <div>
              <dt>Rollback inspection</dt>
              <dd>
                {evidenceStep?.evidence_refs.includes("rollback_refs")
                  ? "rollback_refs surfaced for inspection"
                  : "rollback refs not surfaced"}
              </dd>
            </div>
          </dl>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <h3>Route side-effect classes</h3>
            <span>{sideEffectClasses.length}</span>
          </div>
          <p>
            Every visible step keeps the route boundary readable before the user reaches any
            backend-owned action path.
          </p>
          <div className="note-list">
            {sideEffectClasses.map((sideEffectClass) => (
              <span key={sideEffectClass}>{sideEffectClass}</span>
            ))}
          </div>
        </article>
      </div>

      {orderedSteps.length > 0 ? (
        <div className="review-list" aria-label="Operator loop steps">
          {orderedSteps.map((step) => (
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

function ProofPanel({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <article className="panel">
      <div className="panel-heading">
        <h3>{label}</h3>
        <span>{value}</span>
      </div>
      <p>{detail}</p>
    </article>
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
  const sideEffectClass = sideEffectClassForRoutes(step.route_refs);

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
          <dd>{formatList(step.route_refs)}</dd>
        </div>
        <div>
          <dt>Side-effect class</dt>
          <dd>{sideEffectClass}</dd>
        </div>
        <div>
          <dt>Evidence refs</dt>
          <dd>{formatList(step.evidence_refs)}</dd>
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
          <dt>Control Center mutation</dt>
          <dd>{step.frontend_authority ? "backend alignment required" : "no"}</dd>
        </div>
        <div>
          <dt>Model output authority</dt>
          <dd>no</dd>
        </div>
        <div>
          <dt>Next safe action</dt>
          <dd>{step.next_safe_action}</dd>
        </div>
      </dl>
    </article>
  );
}

function orderOperatorLoopSteps(steps: OperatorLoopStepSummary[]) {
  const orderedStepIds = new Map(
    LOOP_STAGE_ORDER.map((stepId, index) => [stepId, index]),
  );
  return [...steps].sort((first, second) => {
    const firstIndex = orderedStepIds.get(first.step_id) ?? Number.MAX_SAFE_INTEGER;
    const secondIndex = orderedStepIds.get(second.step_id) ?? Number.MAX_SAFE_INTEGER;
    return firstIndex - secondIndex || first.label.localeCompare(second.label);
  });
}

function uniqueRouteRefs(
  steps: OperatorLoopStepSummary[],
  inspectionRouteRefs: string[],
) {
  return Array.from(
    new Set([
      ...inspectionRouteRefs,
      ...steps.flatMap((step) => step.route_refs),
    ]),
  ).sort();
}

function uniqueSideEffectClasses(steps: OperatorLoopStepSummary[]) {
  const classes = Array.from(
    new Set(steps.map((step) => sideEffectClassForRoutes(step.route_refs))),
  ).sort();
  return classes.length > 0 ? classes : ["none"];
}

function sideEffectClassForRoutes(routeRefs: string[]) {
  if (routeRefs.length === 0) {
    return "none";
  }

  const routeClasses = Array.from(new Set(routeRefs.map(sideEffectClassForRoute))).sort();
  return routeClasses.length === 1 ? routeClasses[0] : routeClasses.join(" + ");
}

function sideEffectClassForRoute(routeRef: string) {
  if (routeRef.startsWith("/task-decomposition/")) {
    return "local_dev_workspace_only";
  }
  if (routeRef.startsWith("/v1/")) {
    return "local_dev_workspace_only";
  }
  if (routeRef.startsWith("/runtime/")) {
    return "validation_only";
  }
  if (
    routeRef === "/health" ||
    routeRef === "/version" ||
    routeRef === "/control-center/dashboard"
  ) {
    return "none";
  }
  return "inspection_only";
}

function formatList(values: string[]) {
  return values.length > 0 ? values.join(", ") : "none";
}
