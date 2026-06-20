import type {
  ApiRouteSummary,
  ControlCenterData,
} from "../api/types";
import type { ReactNode } from "react";

type SummaryItem = {
  label: string;
  value: string | number | boolean | null | undefined;
};

const FALLBACK_TEXT = "not returned by this read model";

export function DifferentiatorScreensPanel({
  data,
}: {
  data: ControlCenterData;
}) {
  const routeGroups = Array.from(
    new Set(
      data.routes.routes.flatMap((route) =>
        route.route_group ? [route.route_group] : (route.tags ?? []),
      ),
    ),
  );
  const routeSample = data.routes.routes.slice(0, 4);
  const approvalItem = data.m15Review.approvalQueue[0];
  const receipt = data.m15Review.receipts[0];
  const event = data.m15Review.events[0];
  const fileRef = data.m17Knowledge.fileRefs[0];
  const evidenceItem = data.founderToday.evidence_timeline?.[0];
  const foundationTimeline = data.founderToday.evidence_timeline?.find(
    (item) => item.item_kind === "foundation_gate_latency_ref",
  );
  const localModelSurface =
    data.m18Runtime.localRuntimeSurfaces.find((surface) =>
      surface.surfaceRef.includes("runtime_capability"),
    ) ?? data.m18Runtime.localRuntimeSurfaces[0];
  const smokeReport = data.m18Runtime.manualSmokeReports[0];
  const timelineEvent = data.m16Trace.timelineEvents[0];
  const foundationEvidence = data.m16Trace.foundationGateEvidence[0];

  return (
    <section
      className="page-section"
      aria-labelledby="differentiator-screens-heading"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">Operator proof cockpit</p>
          <h2 id="differentiator-screens-heading">
            Control Center Differentiators
          </h2>
        </div>
        <span className="status-pill compact">safe-ref / redacted-first</span>
      </div>
      <p className="section-copy">
        These screens consolidate existing route, approval, evidence, workspace,
        local model, and observability refs into readable operator state. The
        Control Center remains a shell: OpenAPI, /api/manifest, PolicyEngine,
        LocalApprovalAuthority, and Foundation Gate remain the authority
        boundaries.
      </p>

      <div className="differentiator-grid">
        <ProofPanel title="Route Authority" status="contract truth">
          <ProofMetricGrid
            items={[
              {
                label: "OpenAPI path count",
                value: data.dashboard.api_summary.route_count,
              },
              {
                label: "Visible route refs",
                value: data.routes.route_count,
              },
              {
                label: "Operation IDs unique",
                value: yesNo(data.dashboard.api_summary.operation_ids_unique),
              },
              {
                label: "Execution routes",
                value: data.dashboard.api_summary.execution_routes_present
                  ? "present"
                  : "none reported",
              },
            ]}
          />
          <dl className="metadata-list">
            <MetadataRow label="Contract truth" value="OpenAPI and /api/manifest describe the API boundary; this screen does not execute routes." />
            <MetadataRow
              label="Route groups"
              value={formatList(routeGroups, "manifest-owned route groups")}
            />
            <MetadataRow
              label="Owner posture"
              value="UAA-P1-021 and UAA-P1-052 map owner/service-module intent; runtime authority is not inferred."
            />
            <MetadataRow
              label="Production posture"
              value="blocked for production claims until scoped release evidence exists"
            />
          </dl>
          {routeSample.length > 0 ? (
            <div className="proof-route-list" aria-label="Route authority rows">
              {routeSample.map((route) => (
                <RouteAuthorityRow key={route.operation_id} route={route} />
              ))}
            </div>
          ) : (
            <p>No route rows were returned by the read-only route inventory.</p>
          )}
          <RefList
            label="Evidence refs"
            values={[
              "docs/api/openapi_contract.md",
              "docs/api/route_inventory.md",
              "docs/control_center/route_status_manifest.json",
              "tests/test_route_module_ownership.py",
            ]}
          />
        </ProofPanel>

        <ProofPanel title="Approval State" status="inspection-only">
          <ProofMetricGrid
            items={[
              {
                label: "Pending approvals",
                value: data.dashboard.approval_summary.pending_count,
              },
              {
                label: "Approval grants",
                value: data.dashboard.approval_summary.approval_grants_created
                  ? "created"
                  : "not created",
              },
              {
                label: "Arbitrary ref authority",
                value: data.dashboard.approval_summary
                  .arbitrary_approval_ref_authority
                  ? "present"
                  : "denied",
              },
              {
                label: "Review model",
                value: data.m15Review.previewOnly ? "preview-only" : "summary",
              },
            ]}
          />
          <dl className="metadata-list">
            <MetadataRow
              label="Approval ref"
              value={approvalItem?.approvalRef ?? FALLBACK_TEXT}
            />
            <MetadataRow
              label="Exact scope"
              value="required before any state change; refs are identifiers only"
            />
            <MetadataRow
              label="Stale / expiry"
              value={approvalItem?.expiresAt ?? "recheck required before mutation"}
            />
            <MetadataRow
              label="Next safe action"
              value={
                approvalItem?.requiredNextAction ??
                "Inspect Python Agent Core approval authority state."
              }
            />
            <MetadataRow
              label="Blocked mutation"
              value="approve, deny, grant, revoke, and execution controls are absent"
            />
          </dl>
          <RefList
            label="Receipt and audit refs"
            values={[
              ...(approvalItem?.relatedRefs ?? []),
              ...(data.founderToday.actions[0]?.receipt_refs ?? []),
              ...(data.founderToday.actions[0]?.audit_refs ?? []),
            ]}
          />
        </ProofPanel>

        <ProofPanel title="Evidence Receipts" status="readable refs">
          <ProofMetricGrid
            items={[
              {
                label: "Receipt summaries",
                value: data.m15Review.receipts.length,
              },
              {
                label: "Event summaries",
                value: data.m15Review.events.length,
              },
              {
                label: "Timeline refs",
                value: data.founderToday.sections.evidence_timeline_count ?? 0,
              },
              {
                label: "Redaction",
                value: receipt?.redactionStatus ?? "safe refs only",
              },
            ]}
          />
          <dl className="metadata-list">
            <MetadataRow
              label="Receipt ref"
              value={receipt?.receiptRef ?? FALLBACK_TEXT}
            />
            <MetadataRow
              label="Event ref"
              value={event?.eventRef ?? FALLBACK_TEXT}
            />
            <MetadataRow
              label="Rollback refs"
              value={formatList(evidenceItem?.rollback_refs)}
            />
            <MetadataRow
              label="Foundation Gate refs"
              value={formatList(foundationTimeline?.foundation_gate_refs)}
            />
            <MetadataRow
              label="Latency refs"
              value={formatList(foundationTimeline?.latency_refs)}
            />
            <MetadataRow
              label="Missing evidence"
              value={
                foundationTimeline?.missing_evidence_posture ??
                "missing evidence remains a next-action state"
              }
            />
          </dl>
          <p>
            Summaries are bounded and redacted; private content, provider
            internals, local identifiers, machine details, credentials, and
            secret-like values are not display material.
          </p>
        </ProofPanel>

        <ProofPanel title="Safe Workspace Preview" status="bounded preview">
          <ProofMetricGrid
            items={[
              {
                label: "File refs",
                value: data.m17Knowledge.fileRefs.length,
              },
              {
                label: "Preview mode",
                value: fileRef?.previewOnly ? "preview-only" : "summary-only",
              },
              {
                label: "Redaction",
                value: fileRef?.redactionStatus ?? "redacted_summary_only",
              },
              {
                label: "Review packets",
                value: data.m36FileReview.packets.length,
              },
            ]}
          />
          <dl className="metadata-list">
            <MetadataRow
              label="Workspace ref"
              value={fileRef?.fileRef ?? FALLBACK_TEXT}
            />
            <MetadataRow
              label="Safe label"
              value={fileRef?.safeFilename ?? FALLBACK_TEXT}
            />
            <MetadataRow
              label="Path posture"
              value={fileRef?.pathDisclosure ?? "safe-label only"}
            />
            <MetadataRow
              label="Approval requirement"
              value="required before file mutation, patch application, rollback, or export"
            />
            <MetadataRow
              label="Rollback posture"
              value={
                data.m36FileReview.packets[0]?.receiptPlan.receiptPlanRef ??
                "receipt plan not returned"
              }
            />
            <MetadataRow
              label="Blocked mutation"
              value="file browser, path entry, upload, export, patch apply, rollback execution, and shell controls are absent"
            />
          </dl>
          <RefList
            label="Workspace evidence refs"
            values={[
              ...(fileRef?.evidenceRefs ?? []),
              ...(fileRef?.receiptRefs ?? []),
              ...(fileRef?.eventRefs ?? []),
            ]}
          />
        </ProofPanel>

        <ProofPanel title="Local Model / M167 Status" status="status only">
          <ProofMetricGrid
            items={[
              {
                label: "Runtime readiness",
                value: data.runtimeReadiness.status,
              },
              {
                label: "Release claim",
                value: yesNo(data.runtimeReadiness.production_ready),
              },
              {
                label: "Model calls allowed",
                value: yesNo(
                  data.capabilityMatrix.entries.some(
                    (entry) => entry.real_model_call_allowed,
                  ),
                ),
              },
              {
                label: "Smoke output authority",
                value: smokeReport?.modelOutputAuthoritative ? "yes" : "no",
              },
            ]}
          />
          <dl className="metadata-list">
            <MetadataRow
              label="M167 posture"
              value="readiness and evidence refs only; reviewed local evidence remains the gate"
            />
            <MetadataRow
              label="Gateway status"
              value={localModelSurface?.sourceRoute ?? "/v1 status refs only"}
            />
            <MetadataRow
              label="OpenWebUI shell"
              value="shell posture only; output is not production authority"
            />
            <MetadataRow
              label="Lifecycle controls"
              value="model download, GGUF approval, server start/stop, tools, streaming, and provider authority are blocked"
            />
            <MetadataRow
              label="Next safe action"
              value="inspect readiness, provenance checklist, and M167 evidence refs"
            />
          </dl>
          <RefList
            label="Readiness refs"
            values={[
              data.runtimeReadiness.capability_matrix_ref,
              ...(localModelSurface?.guardrailRefs ?? []),
              ...(smokeReport?.reasonCodes ?? []),
            ]}
          />
        </ProofPanel>

        <ProofPanel title="M167 Observability Timeline" status="redacted summary">
          <ProofMetricGrid
            items={[
              {
                label: "Timeline events",
                value: data.m16Trace.timelineEvents.length,
              },
              {
                label: "Trace relations",
                value: data.m16Trace.traceRelations.length,
              },
              {
                label: "Foundation evidence",
                value: data.m16Trace.foundationGateEvidence.length,
              },
              {
                label: "External telemetry",
                value: "blocked",
              },
            ]}
          />
          <dl className="metadata-list">
            <MetadataRow
              label="Session / run ref"
              value={timelineEvent?.runRef ?? FALLBACK_TEXT}
            />
            <MetadataRow
              label="Event ref"
              value={timelineEvent?.eventRef ?? FALLBACK_TEXT}
            />
            <MetadataRow
              label="Client-error posture"
              value="summary refs only; unredacted forensic mode is blocked"
            />
            <MetadataRow
              label="Source route / status"
              value={
                timelineEvent?.sourceSurface ??
                data.m16Trace.boundarySummary
              }
            />
            <MetadataRow
              label="Duration / status"
              value={timelineEvent?.status ?? "summary-only"}
            />
            <MetadataRow
              label="Evidence ref"
              value={foundationEvidence?.evidenceRef ?? FALLBACK_TEXT}
            />
          </dl>
          <RefList
            label="Receipt and evidence refs"
            values={[
              ...(timelineEvent?.receiptRefs ?? []),
              ...(timelineEvent?.evidenceRefs ?? []),
              ...(foundationEvidence?.receiptRefs ?? []),
            ]}
          />
        </ProofPanel>
      </div>
    </section>
  );
}

function ProofPanel({
  title,
  status,
  children,
}: {
  title: string;
  status: string;
  children: ReactNode;
}) {
  return (
    <article className="status-card differentiator-panel">
      <div className="status-card-header">
        <h3>{title}</h3>
        <span>{status}</span>
      </div>
      {children}
    </article>
  );
}

function ProofMetricGrid({ items }: { items: SummaryItem[] }) {
  return (
    <div className="proof-metric-grid">
      {items.map((item) => (
        <div key={item.label}>
          <span>{item.label}</span>
          <strong>{formatValue(item.value)}</strong>
        </div>
      ))}
    </div>
  );
}

function MetadataRow({ label, value }: SummaryItem) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{formatValue(value)}</dd>
    </div>
  );
}

function RouteAuthorityRow({ route }: { route: ApiRouteSummary }) {
  return (
    <div className="proof-route-row">
      <div>
        <strong>{route.operation_id}</strong>
        <span>{route.path}</span>
      </div>
      <dl className="detail-list">
        <dt>Group</dt>
        <dd>{route.route_group ?? formatList(route.tags)}</dd>
        <dt>Methods</dt>
        <dd>{formatList(route.methods)}</dd>
        <dt>Side-effect class</dt>
        <dd>{route.side_effect_class ?? "manifest-owned"}</dd>
        <dt>Risk / release</dt>
        <dd>
          {route.risk_class ?? "risk mapped"} /{" "}
          {route.release_status ?? "release status mapped"}
        </dd>
        <dt>Auth posture</dt>
        <dd>{route.auth_posture ?? "manifest-owned"}</dd>
        <dt>Owner / service</dt>
        <dd>
          {route.owner ?? "route owner mapped"} /{" "}
          {route.service_module ?? "service module mapped"}
        </dd>
      </dl>
    </div>
  );
}

function RefList({ label, values }: { label: string; values: string[] }) {
  const refs = values.filter(Boolean);
  if (refs.length === 0) {
    return (
      <div className="tag-list" aria-label={label}>
        <strong>{label}</strong>
        <div>
          <span>missing ref; inspect source contract</span>
        </div>
      </div>
    );
  }
  return (
    <div className="tag-list" aria-label={label}>
      <strong>{label}</strong>
      <div>
        {refs.slice(0, 8).map((ref, index) => (
          <span key={`${ref}-${index}`}>{ref}</span>
        ))}
      </div>
    </div>
  );
}

function formatList(values?: string[], fallback = "refs not returned") {
  return values && values.length > 0 ? values.join(", ") : fallback;
}

function yesNo(value: boolean) {
  return value ? "yes" : "no";
}

function formatValue(value: SummaryItem["value"]) {
  if (value === null || value === undefined || value === "") {
    return FALLBACK_TEXT;
  }
  if (typeof value === "boolean") {
    return yesNo(value);
  }
  return String(value);
}
