import { useState } from "react";
import type { M15ReviewData, ReceiptSummaryItem } from "../api/types";
import { EmptyState } from "./DataState";

export function ReceiptViewerPanel({ review }: { review: M15ReviewData }) {
  const [selectedRef, setSelectedRef] = useState(review.receipts[0]?.receiptRef ?? "");
  const selected = review.receipts.find((item) => item.receiptRef === selectedRef) ?? review.receipts[0];

  return (
    <section className="page-section" aria-labelledby="receipt-viewer-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">M15 review surface</p>
          <h2 id="receipt-viewer-heading">Receipt Viewer</h2>
        </div>
        <span className="status-pill compact">redacted summary-only</span>
      </div>
      <p className="section-copy">
        This view shows redacted summary-only receipt records for inspection. Receipts remain non-authoritative mock
        summaries unless a future reviewed backend contract provides safe live data.
      </p>
      <div className="note-list" aria-label="Receipt viewer warnings">
        {review.warningCodes.map((code) => (
          <span key={code}>{code}</span>
        ))}
      </div>
      {review.receipts.length > 0 && selected ? (
        <div className="review-layout">
          <div className="review-list" aria-label="Receipt summaries">
            {review.receipts.map((item) => (
              <ReceiptRow
                key={item.receiptRef}
                item={item}
                selected={item.receiptRef === selected.receiptRef}
                onSelect={setSelectedRef}
              />
            ))}
          </div>
          <ReceiptDetail item={selected} />
        </div>
      ) : (
        <EmptyState title="No receipt summaries" message="No redacted receipt summaries are available." />
      )}
    </section>
  );
}

function ReceiptRow({
  item,
  selected,
  onSelect
}: {
  item: ReceiptSummaryItem;
  selected: boolean;
  onSelect: (receiptRef: string) => void;
}) {
  return (
    <article className={`review-card${selected ? " selected" : ""}`}>
      <div className="review-card-heading">
        <h3>{item.receiptRef}</h3>
        <span>{item.status}</span>
      </div>
      <p>{item.actionTypeSummary}</p>
      <p className="review-meta">
        {item.redactionStatus} | {item.timestamp}
      </p>
      <button type="button" className="secondary-button" onClick={() => onSelect(item.receiptRef)}>
        View details
      </button>
    </article>
  );
}

function ReceiptDetail({ item }: { item: ReceiptSummaryItem }) {
  return (
    <article className="panel review-detail" aria-label="Receipt detail">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Selected receipt</p>
          <h3>{item.receiptRef}</h3>
        </div>
        <span>{item.status}</span>
      </div>
      <dl className="detail-grid">
        <div>
          <dt>Action type</dt>
          <dd>{item.actionTypeSummary}</dd>
        </div>
        <div>
          <dt>Actor</dt>
          <dd>{item.actorSummary}</dd>
        </div>
        <div>
          <dt>Risk</dt>
          <dd>{item.riskLevel}</dd>
        </div>
        <div>
          <dt>Data classification</dt>
          <dd>{item.dataClassification}</dd>
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
      <TagList label="Event refs" values={item.eventRefs} />
      <TagList label="Related refs" values={item.relatedRefs} />
      <p className="safe-copy">Receipt detail is redacted summary metadata only.</p>
      <p className="safe-copy">No receipt mutation is available from this UI. {item.safeMessage}</p>
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
