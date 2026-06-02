import { useState } from "react";
import type { ApprovalQueueItem, M15ReviewData } from "../api/types";
import { EmptyState } from "./DataState";

export function ApprovalQueuePanel({ review }: { review: M15ReviewData }) {
  const [selectedRef, setSelectedRef] = useState(review.approvalQueue[0]?.approvalRef ?? "");
  const selected = review.approvalQueue.find((item) => item.approvalRef === selectedRef) ?? review.approvalQueue[0];

  return (
    <section className="page-section" aria-labelledby="approval-queue-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">M15 review surface</p>
          <h2 id="approval-queue-heading">Approval Queue</h2>
        </div>
        <span className="status-pill compact">read-only / preview-only</span>
      </div>
      <p className="section-copy">
        Approval request summaries are read-only and preview-only. {review.authorityBoundary}
      </p>
      <ReviewWarningBar codes={review.warningCodes} />
      {review.approvalQueue.length > 0 && selected ? (
        <div className="review-layout">
          <div className="review-list" aria-label="Approval request summaries">
            {review.approvalQueue.map((item) => (
              <ApprovalQueueRow
                key={item.approvalRef}
                item={item}
                selected={item.approvalRef === selected.approvalRef}
                onSelect={setSelectedRef}
              />
            ))}
          </div>
          <ApprovalQueueDetail item={selected} />
        </div>
      ) : (
        <EmptyState
          title="No approval summaries"
          message="No approval queue summaries are available from the local mock or backend."
        />
      )}
    </section>
  );
}

function ApprovalQueueRow({
  item,
  selected,
  onSelect
}: {
  item: ApprovalQueueItem;
  selected: boolean;
  onSelect: (approvalRef: string) => void;
}) {
  return (
    <article className={`review-card${selected ? " selected" : ""}`}>
      <div className="review-card-heading">
        <h3>{item.approvalRef}</h3>
        <span>{item.status}</span>
      </div>
      <p>{item.requestedActionSummary}</p>
      <p className="review-meta">
        risk: {item.riskLevel} | data: {item.dataClassification}
      </p>
      <button type="button" className="secondary-button" onClick={() => onSelect(item.approvalRef)}>
        View details
      </button>
    </article>
  );
}

function ApprovalQueueDetail({ item }: { item: ApprovalQueueItem }) {
  return (
    <article className="panel review-detail" aria-label="Approval request detail">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Selected request</p>
          <h3>{item.approvalRef}</h3>
        </div>
        <span>{item.status}</span>
      </div>
      <dl className="detail-grid">
        <div>
          <dt>Actor</dt>
          <dd>{item.actorSummary}</dd>
        </div>
        <div>
          <dt>Subject</dt>
          <dd>{item.subjectSummary}</dd>
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
          <dt>Created</dt>
          <dd>{item.createdAt}</dd>
        </div>
        <div>
          <dt>Expires</dt>
          <dd>{item.expiresAt ?? "not provided"}</dd>
        </div>
        <div>
          <dt>Required next action</dt>
          <dd>{item.requiredNextAction}</dd>
        </div>
        <div>
          <dt>Preview outcome</dt>
          <dd>{item.previewOutcomeSummary}</dd>
        </div>
      </dl>
      <TagList label="Reason codes" values={item.reasonCodes} />
      <TagList label="Related refs" values={item.relatedRefs} />
      <p className="safe-copy">{item.safeMessage}</p>
    </article>
  );
}

function ReviewWarningBar({ codes }: { codes: string[] }) {
  return (
    <div className="note-list" aria-label="M15 review warnings">
      {codes.map((code) => (
        <span key={code}>{code}</span>
      ))}
    </div>
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
