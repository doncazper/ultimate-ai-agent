import { useState } from "react";
import type {
  FoundationGateEvidenceSummaryItem,
  M16TraceData,
  TimelineEventSummaryItem,
  TraceRelationSummaryItem,
} from "../api/types";
import { EmptyState } from "./DataState";

export function EventTimelineTracePanel({ trace }: { trace: M16TraceData }) {
  const [selectedRef, setSelectedRef] = useState(trace.timelineEvents[0]?.eventRef ?? "");
  const selected =
    trace.timelineEvents.find((item) => item.eventRef === selectedRef) ?? trace.timelineEvents[0];
  const relations = selected
    ? trace.traceRelations.filter(
        (relation) =>
          relation.fromRef === selected.eventRef || relation.toRef === selected.eventRef,
      )
    : [];
  const evidence = selected
    ? trace.foundationGateEvidence.filter((item) => item.eventRefs.includes(selected.eventRef))
    : trace.foundationGateEvidence;

  return (
    <section className="page-section" aria-labelledby="event-timeline-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">M16 trace surface</p>
          <h2 id="event-timeline-heading">Event Timeline</h2>
        </div>
        <span className="status-pill compact">redacted summary-only</span>
      </div>
      <p className="section-copy">
        Timeline and trace views are read-only. They show safe refs, relationship summaries, and
        receipt/evidence links without execution authority.
      </p>
      <p className="safe-copy">
        No trace export or external telemetry is available. {trace.boundarySummary}
      </p>
      <div className="note-list" aria-label="Timeline trace warnings">
        {trace.warningCodes.map((code) => (
          <span key={code}>{code}</span>
        ))}
      </div>
      {trace.timelineEvents.length > 0 && selected ? (
        <div className="review-layout">
          <div className="review-list" aria-label="Event timeline summaries">
            {trace.timelineEvents.map((item) => (
              <TimelineEventRow
                key={item.eventRef}
                item={item}
                selected={item.eventRef === selected.eventRef}
                onSelect={setSelectedRef}
              />
            ))}
          </div>
          <div className="trace-column">
            <TraceDetail item={selected} />
            <TraceRelationsPanel relations={relations} />
            <FoundationGateEvidencePanel evidence={evidence} />
          </div>
        </div>
      ) : (
        <EmptyState
          title="No timeline summaries"
          message="No redacted timeline summaries are available."
        />
      )}
    </section>
  );
}

function TimelineEventRow({
  item,
  selected,
  onSelect,
}: {
  item: TimelineEventSummaryItem;
  selected: boolean;
  onSelect: (eventRef: string) => void;
}) {
  return (
    <article
      className={`review-card${selected ? " selected" : ""}`}
      aria-current={selected ? "true" : undefined}
      aria-label={`${item.eventRef} timeline event`}
    >
      <div className="review-card-heading">
        <h3>{item.eventRef}</h3>
        <span>{item.status}</span>
      </div>
      <p>{item.eventType}</p>
      <p className="review-meta">source: {item.sourceSurface}</p>
      <p className="review-meta">
        run: {item.runRef} | correlation: {item.correlationRef}
      </p>
      <button type="button" className="secondary-button" onClick={() => onSelect(item.eventRef)}>
        View trace
      </button>
    </article>
  );
}

function TraceDetail({ item }: { item: TimelineEventSummaryItem }) {
  return (
    <article className="panel review-detail" aria-label="Run receipt trace detail">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Selected trace</p>
          <h3>{item.eventRef}</h3>
        </div>
        <span>{item.status}</span>
      </div>
      <dl className="detail-grid">
        <div>
          <dt>Event type</dt>
          <dd>{item.eventType}</dd>
        </div>
        <div>
          <dt>Source</dt>
          <dd>{item.sourceSurface}</dd>
        </div>
        <div>
          <dt>Actor</dt>
          <dd>{item.actorSummary}</dd>
        </div>
        <div>
          <dt>Timestamp</dt>
          <dd>{item.timestamp}</dd>
        </div>
        <div>
          <dt>Run id</dt>
          <dd>{item.runRef}</dd>
        </div>
        <div>
          <dt>Correlation id</dt>
          <dd>{item.correlationRef}</dd>
        </div>
        <div>
          <dt>Redaction status</dt>
          <dd>{item.redactionStatus}</dd>
        </div>
      </dl>
      <TagList label="Receipt refs" values={item.receiptRefs} />
      <TagList label="Evidence refs" values={item.evidenceRefs} />
      <TagList label="Child event refs" values={item.childEventRefs} />
      {item.parentEventRef ? (
        <TagList label="Parent event refs" values={[item.parentEventRef]} />
      ) : null}
      <p className="safe-copy">Trace detail is redacted summary metadata only.</p>
      <p className="safe-copy">{item.safeMessage}</p>
    </article>
  );
}

function TraceRelationsPanel({ relations }: { relations: TraceRelationSummaryItem[] }) {
  return (
    <article className="panel review-detail" aria-label="Event relation refs">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Relation refs</p>
          <h3>Run/receipt trace links</h3>
        </div>
        <span>read-only</span>
      </div>
      {relations.length > 0 ? (
        <div className="stacked-list">
          {relations.map((relation) => (
            <div key={relation.relationRef} className="trace-row">
              <strong>{relation.relationRef}</strong>
              <span>{relation.relationType}</span>
              <p>
                {relation.fromRef} {"->"} {relation.toRef}
              </p>
              <p>{relation.safeSummary}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="safe-copy">No relation summaries are available for the selected event.</p>
      )}
    </article>
  );
}

function FoundationGateEvidencePanel({
  evidence,
}: {
  evidence: FoundationGateEvidenceSummaryItem[];
}) {
  return (
    <article className="panel review-detail" aria-label="Foundation Gate evidence summary">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Evidence refs</p>
          <h3>Foundation Gate evidence summary</h3>
        </div>
        <span>summary-only</span>
      </div>
      {evidence.length > 0 ? (
        <div className="stacked-list">
          {evidence.map((item) => (
            <div key={item.evidenceRef} className="trace-row">
              <strong>{item.evidenceRef}</strong>
              <span>{item.status}</span>
              <p>{item.criterionRef}</p>
              <p>{item.safeSummary}</p>
              <TagList label={`${item.evidenceRef} receipt refs`} values={item.receiptRefs} />
            </div>
          ))}
        </div>
      ) : (
        <p className="safe-copy">
          No Foundation Gate evidence summaries are linked to the selected event.
        </p>
      )}
    </article>
  );
}

function TagList({ label, values }: { label: string; values: string[] }) {
  return (
    <div className="tag-list" aria-label={label}>
      <strong>{label}</strong>
      <div>
        {values.map((value) => (
          <span key={value}>{value}</span>
        ))}
      </div>
    </div>
  );
}
