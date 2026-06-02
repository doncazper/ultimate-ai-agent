import { useState } from "react";
import type { EventSummaryItem, M15ReviewData } from "../api/types";
import { EmptyState } from "./DataState";

export function EventViewerPanel({ review }: { review: M15ReviewData }) {
  const [selectedRef, setSelectedRef] = useState(review.events[0]?.eventRef ?? "");
  const selected = review.events.find((item) => item.eventRef === selectedRef) ?? review.events[0];

  return (
    <section className="page-section" aria-labelledby="event-viewer-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">M15 review surface</p>
          <h2 id="event-viewer-heading">Event Viewer</h2>
        </div>
        <span className="status-pill compact">redacted summary-only</span>
      </div>
      <p className="section-copy">
        This view displays redacted event summaries for audit review. It does not expose event bodies or create event
        authority.
      </p>
      <div className="note-list" aria-label="Event viewer warnings">
        {review.warningCodes.map((code) => (
          <span key={code}>{code}</span>
        ))}
      </div>
      {review.events.length > 0 && selected ? (
        <div className="review-layout">
          <div className="review-list" aria-label="Event summaries">
            {review.events.map((item) => (
              <EventRow
                key={item.eventRef}
                item={item}
                selected={item.eventRef === selected.eventRef}
                onSelect={setSelectedRef}
              />
            ))}
          </div>
          <EventDetail item={selected} />
        </div>
      ) : (
        <EmptyState title="No event summaries" message="No redacted event summaries are available." />
      )}
    </section>
  );
}

function EventRow({
  item,
  selected,
  onSelect
}: {
  item: EventSummaryItem;
  selected: boolean;
  onSelect: (eventRef: string) => void;
}) {
  return (
    <article className={`review-card${selected ? " selected" : ""}`}>
      <div className="review-card-heading">
        <h3>{item.eventRef}</h3>
        <span>{item.resultStatus}</span>
      </div>
      <p>{item.eventType}</p>
      <p className="review-meta">source: {item.sourceSurface}</p>
      <button type="button" className="secondary-button" onClick={() => onSelect(item.eventRef)}>
        View details
      </button>
    </article>
  );
}

function EventDetail({ item }: { item: EventSummaryItem }) {
  return (
    <article className="panel review-detail" aria-label="Event detail">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Selected event</p>
          <h3>{item.eventRef}</h3>
        </div>
        <span>{item.resultStatus}</span>
      </div>
      <dl className="detail-grid">
        <div>
          <dt>Event type</dt>
          <dd>{item.eventType}</dd>
        </div>
        <div>
          <dt>Actor</dt>
          <dd>{item.actorSummary}</dd>
        </div>
        <div>
          <dt>Source surface</dt>
          <dd>{item.sourceSurface}</dd>
        </div>
        <div>
          <dt>Redaction status</dt>
          <dd>{item.redactionStatus}</dd>
        </div>
        <div>
          <dt>Timestamp</dt>
          <dd>{item.timestamp}</dd>
        </div>
      </dl>
      <TagList label="Reason codes" values={item.reasonCodes} />
      <TagList label="Related refs" values={item.relatedRefs} />
      <p className="safe-copy">Event detail is redacted summary metadata only.</p>
      <p className="safe-copy">{item.safeMessage}</p>
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
