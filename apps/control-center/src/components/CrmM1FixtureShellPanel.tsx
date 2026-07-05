import { useMemo, useState } from "react";
import type {
  CrmFollowUpReadModel,
  CrmLocalCommandCenterReadModel,
  CrmOpportunityReadModel,
  CrmRelationshipReadModel,
} from "../api/types";

export function CrmM1FixtureShellPanel({
  crm,
}: {
  crm: CrmLocalCommandCenterReadModel;
}) {
  const [selectedRef, setSelectedRef] = useState(
    crm.relationships[0]?.relationship_ref ?? "",
  );
  const selected =
    crm.relationships.find((item) => item.relationship_ref === selectedRef) ??
    crm.relationships[0];
  const selectedFollowUps = useMemo(
    () =>
      selected
        ? crm.follow_ups.filter((item) =>
            selected.follow_up_refs.includes(item.follow_up_ref),
          )
        : [],
    [crm.follow_ups, selected],
  );
  const selectedTimeline = useMemo(
    () =>
      selected
        ? crm.timeline_events.filter((item) =>
            selected.timeline_event_refs.includes(item.event_ref),
          )
        : [],
    [crm.timeline_events, selected],
  );
  const connectorReadiness = crm.connector_read_lanes;
  const connectorReadinessStatus =
    connectorReadiness.readiness_status ?? "blocked_missing_exact_authority";
  const connectorLanes = connectorReadiness.lanes ?? [];
  const connectorMissingPrerequisites =
    connectorReadiness.missing_prerequisite_refs ?? [];
  const connectorCliInspectionRef =
    connectorReadiness.cli_inspection_ref ??
    "repo-local-command:uaa-crm:inspect-connector-read-lanes";
  const connectorSafeDisableRef =
    connectorReadiness.safe_disable_ref ??
    "safe-disable-ref:crm-connector-read:disable-lane:v1";
  const connectorProofRef =
    connectorReadiness.proof_ref ??
    "proof-ref:crm-connector-read-readiness:v1";

  return (
    <section
      aria-labelledby="crm-local-heading"
      className="page-section crm-command-center"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">CRM Local Command Center</p>
          <h2 id="crm-local-heading">UAA CRM local command center</h2>
        </div>
        <span className="status-pill compact">
          {crm.backend_owned ? "backend-owned" : "mock fallback"}
        </span>
      </div>
      <p className="section-copy">
        Local-first relationship command surface backed by Python Core read
        models, safe refs, exact local mutation receipts, and blocked external
        authority posture.
      </p>

      {!crm.backend_owned ? (
        <section className="panel warning" aria-label="CRM fallback posture">
          <p>
            CRM is showing non-authoritative fallback refs because the live
            local endpoint was unavailable or unsafe.
          </p>
        </section>
      ) : null}

      <div className="panel-grid crm-command-grid">
        <MetricCard label="Relationships" value={crm.relationships.length} />
        <MetricCard label="Follow-ups" value={crm.follow_ups.length} />
        <MetricCard label="Smart lists" value={crm.smart_lists.length} />
        <MetricCard label="Reports" value={crm.reports.length} />
      </div>

      <div className="crm-command-layout">
        <section className="status-card" aria-label="CRM relationship list">
          <div className="status-card-header">
            <h3>Relationships</h3>
            <span>{crm.storage_status.state}</span>
          </div>
          <div className="crm-relationship-list">
            {crm.relationships.map((relationship) => (
              <button
                className={
                  relationship.relationship_ref === selected?.relationship_ref
                    ? "crm-selector active"
                    : "crm-selector"
                }
                key={relationship.relationship_ref}
                onClick={() => setSelectedRef(relationship.relationship_ref)}
                type="button"
              >
                <strong>{relationship.safe_display_label}</strong>
                <span>{relationship.health_state}</span>
              </button>
            ))}
          </div>
        </section>

        <RelationshipInspector
          followUps={selectedFollowUps}
          relationship={selected}
          timeline={selectedTimeline}
        />
      </div>

      <div className="crm-command-layout">
        <section className="status-card" aria-label="CRM follow-up queue">
          <div className="status-card-header">
            <h3>Follow-up queue</h3>
            <span>proposal refs</span>
          </div>
          <div className="crm-stack">
            {crm.follow_ups.map((followUp) => (
              <FollowUpCard followUp={followUp} key={followUp.follow_up_ref} />
            ))}
          </div>
        </section>

        <section className="status-card" aria-label="CRM pipeline board">
          <div className="status-card-header">
            <h3>Pipeline</h3>
            <span>local preview</span>
          </div>
          <div className="crm-pipeline">
            {crm.pipelines[0]?.stages.map((stage) => (
              <div className="crm-stage" key={stage.stage_ref}>
                <h4>{stage.safe_label}</h4>
                {stage.opportunity_refs.map((opportunityRef) => {
                  const opportunity = crm.opportunities.find(
                    (item) => item.opportunity_ref === opportunityRef,
                  );
                  return opportunity ? (
                    <OpportunityTile
                      key={opportunity.opportunity_ref}
                      opportunity={opportunity}
                    />
                  ) : null;
                })}
              </div>
            ))}
          </div>
          <p className="safe-ref">
            {crm.pipelines[0]?.persisted_reorder_requires_exact_mutation
              ? "Persisted stage changes require exact local mutation receipts."
              : "Pipeline persistence is unavailable."}
          </p>
        </section>
      </div>

      <div className="crm-command-layout">
        <section className="status-card" aria-label="CRM smart lists">
          <div className="status-card-header">
            <h3>Smart lists</h3>
            <span>deterministic</span>
          </div>
          <div className="crm-chip-grid">
            {crm.smart_lists.slice(0, 10).map((list) => (
              <span className="status-pill compact" key={list.smart_list_ref}>
                {list.safe_label}
              </span>
            ))}
          </div>
        </section>

        <section className="status-card" aria-label="CRM reports">
          <div className="status-card-header">
            <h3>Reports</h3>
            <span>safe labels</span>
          </div>
          <dl className="crm-report-list">
            {crm.reports.slice(0, 6).map((report) => (
              <div key={report.report_ref}>
                <dt>{report.safe_label}</dt>
                <dd>{report.value_label}</dd>
              </div>
            ))}
          </dl>
        </section>
      </div>

      <section className="panel" aria-labelledby="crm-authority-heading">
        <div className="panel-heading">
          <h3 id="crm-authority-heading">Authority boundary</h3>
          <span>local-only</span>
        </div>
        <div className="panel-grid">
          <MetricCard
            label="Control Center authority"
            value={
              crm.authority_posture.control_center_grants_authority
                ? "enabled"
                : "blocked"
            }
          />
          <MetricCard
            label="External writes"
            value={
              crm.authority_posture.external_crm_write_enabled
                ? "enabled"
                : "blocked"
            }
          />
          <MetricCard
            label="Provider calls"
            value={
              crm.authority_posture.provider_model_call_enabled
                ? "enabled"
                : "blocked"
            }
          />
          <MetricCard
            label="Live web"
            value={crm.authority_posture.live_web_enabled ? "enabled" : "blocked"}
          />
        </div>
        <ul className="safe-ref-list">
          {crm.blocked_authority_refs.slice(0, 10).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </section>

      <section
        className="panel"
        aria-labelledby="crm-connector-readiness-heading"
      >
        <div className="panel-heading">
          <h3 id="crm-connector-readiness-heading">
            Connector read readiness
          </h3>
          <span>{connectorReadinessStatus}</span>
        </div>
        <p className="section-copy">
          CRM connector reads remain disabled until an exact single-source
          gateway lane, policy decision, approval scope, audit receipt,
          redaction contract, and route classification are graduated.
        </p>
        <div className="panel-grid">
          <MetricCard
            label="Runtime read"
            value={
              connectorReadiness.live_connector_read_performed
                ? "unsafe"
                : "blocked"
            }
          />
          <MetricCard
            label="Account auth"
            value={
              connectorReadiness.external_account_auth_enabled
                ? "unsafe"
                : "blocked"
            }
          />
          <MetricCard
            label="Polling"
            value={
              connectorReadiness.background_polling_enabled
                ? "unsafe"
                : "blocked"
            }
          />
          <MetricCard
            label="Provider calls"
            value={
              connectorReadiness.provider_model_call_enabled
                ? "unsafe"
                : "blocked"
            }
          />
        </div>
        <div className="crm-command-layout">
          <div>
            <h4>Current lanes</h4>
            <ul className="safe-ref-list">
              {connectorLanes.map((lane) => (
                <li key={lane.lane_ref}>
                  <strong>{lane.status}</strong> {lane.lane_ref}
                  <span> - {lane.safe_summary}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4>Missing prerequisites</h4>
            <ul className="safe-ref-list">
              {connectorMissingPrerequisites.length > 0 ? (
                connectorMissingPrerequisites.map((ref) => (
                  <li key={ref}>{ref}</li>
                ))
              ) : (
                <li>missing-ref:crm-connector-read:backend-contract-refresh-required</li>
              )}
            </ul>
          </div>
        </div>
        <dl className="crm-report-list">
          <div>
            <dt>CLI inspection</dt>
            <dd>{connectorCliInspectionRef}</dd>
          </div>
          <div>
            <dt>Safe disable</dt>
            <dd>{connectorSafeDisableRef}</dd>
          </div>
          <div>
            <dt>Proof</dt>
            <dd>{connectorProofRef}</dd>
          </div>
          <div>
            <dt>Unblock prompt</dt>
            <dd>{crm.connector_read_lanes.unblock_prompt_ref}</dd>
          </div>
        </dl>
      </section>

      <section className="panel" aria-labelledby="crm-cli-heading">
        <div className="panel-heading">
          <h3 id="crm-cli-heading">CLI parity</h3>
          <span>inspectable</span>
        </div>
        <ul className="safe-ref-list">
          {crm.cli_refs.map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </section>
    </section>
  );
}

function RelationshipInspector({
  relationship,
  followUps,
  timeline,
}: {
  relationship: CrmRelationshipReadModel | undefined;
  followUps: CrmFollowUpReadModel[];
  timeline: Array<{ event_ref: string; safe_summary: string }>;
}) {
  if (!relationship) {
    return (
      <section className="status-card">
        <div className="status-card-header">
          <h3>Relationship inspector</h3>
          <span>empty</span>
        </div>
        <p>No relationship refs are available.</p>
      </section>
    );
  }
  return (
    <section className="status-card" aria-label="CRM relationship inspector">
      <div className="status-card-header">
        <h3>{relationship.safe_display_label}</h3>
        <span>{relationship.stale_state}</span>
      </div>
      <p>{relationship.safe_summary}</p>
      <p className="safe-ref">{relationship.why_shown}</p>
      <dl className="metric-grid">
        <Metric label="Follow-ups" value={String(followUps.length)} />
        <Metric label="Timeline" value={String(timeline.length)} />
        <Metric label="Evidence" value={String(relationship.evidence_refs.length)} />
        <Metric
          label="Memory refs"
          value={String(relationship.memory_provenance_refs.length)}
        />
      </dl>
      <div className="crm-stack">
        {timeline.map((event) => (
          <p className="safe-ref" key={event.event_ref}>
            {event.safe_summary}
          </p>
        ))}
      </div>
    </section>
  );
}

function FollowUpCard({ followUp }: { followUp: CrmFollowUpReadModel }) {
  return (
    <article className="crm-item">
      <div>
        <strong>{followUp.status}</strong>
        <p>{followUp.safe_summary}</p>
      </div>
      <span>{followUp.priority}</span>
    </article>
  );
}

function OpportunityTile({ opportunity }: { opportunity: CrmOpportunityReadModel }) {
  return (
    <article className="crm-item">
      <div>
        <strong>{opportunity.stage_label}</strong>
        <p>{opportunity.safe_summary}</p>
      </div>
    </article>
  );
}

function MetricCard({ label, value }: { label: string; value: number | string }) {
  return (
    <article className="metric-card" role="status">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card" role="status">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
