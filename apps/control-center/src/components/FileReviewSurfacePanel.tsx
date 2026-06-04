import { useState } from "react";
import type { FileReviewPacketSummary, M36FileReviewData } from "../api/types";
import { EmptyState } from "./DataState";

export function FileReviewSurfacePanel({ review }: { review: M36FileReviewData }) {
  const [selectedRef, setSelectedRef] = useState(review.packets[0]?.reviewPacketRef ?? "");
  const selected = review.packets.find((packet) => packet.reviewPacketRef === selectedRef) ?? review.packets[0];

  return (
    <section className="page-section" aria-labelledby="file-review-surface-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">M36 file review surface</p>
          <h2 id="file-review-surface-heading">File Review Surface</h2>
        </div>
        <span className="status-pill compact">review-only</span>
      </div>
      <p className="section-copy">
        Redacted file review packets are shown for local inspection only. The surface displays safe refs,
        redaction summaries, decision status, gate contract status, and receipt-plan metadata without adding approval capture.
      </p>
      <p className="safe-copy">{review.boundarySummary}</p>
      <div className="note-list" aria-label="M36 file review warnings">
        {review.warningCodes.map((code) => (
          <span key={code}>{code}</span>
        ))}
      </div>

      {review.packets.length > 0 && selected ? (
        <div className="review-layout">
          <div className="review-list" aria-label="File review packets">
            {review.packets.map((packet) => (
              <FileReviewPacketRow
                key={packet.reviewPacketRef}
                packet={packet}
                selected={packet.reviewPacketRef === selected.reviewPacketRef}
                onSelect={setSelectedRef}
              />
            ))}
          </div>
          <FileReviewPacketDetail packet={selected} />
        </div>
      ) : (
        <EmptyState title="No file review packets" message="No redacted file review packets are available." />
      )}
    </section>
  );
}

function FileReviewPacketRow({
  packet,
  selected,
  onSelect
}: {
  packet: FileReviewPacketSummary;
  selected: boolean;
  onSelect: (reviewPacketRef: string) => void;
}) {
  return (
    <article
      className={`review-card${selected ? " selected" : ""}`}
      aria-current={selected ? "true" : undefined}
      aria-label={`${packet.reviewPacketRef} file review packet`}
    >
      <div className="review-card-heading">
        <h3>{packet.reviewPacketRef}</h3>
        <span>{packet.status}</span>
      </div>
      <p>{packet.actorSummary}</p>
      <p className="review-meta">
        {packet.redactionStatus} | {packet.dataClassification}
      </p>
      <button type="button" className="secondary-button" onClick={() => onSelect(packet.reviewPacketRef)}>
        View review packet
      </button>
    </article>
  );
}

function FileReviewPacketDetail({ packet }: { packet: FileReviewPacketSummary }) {
  return (
    <article className="panel review-detail" aria-label="File review packet detail">
      <div className="section-heading compact-heading">
        <div>
          <p className="eyebrow">Selected review packet</p>
          <h3>{packet.reviewPacketRef}</h3>
        </div>
        <span className="status-pill compact">Review-only surface</span>
      </div>
      <p className="safe-copy">
        Review decisions are display-only and cannot capture approval. M37 approval capture remains future.
      </p>

      <section aria-labelledby="redacted-preview-heading">
        <h4 id="redacted-preview-heading">Redacted preview</h4>
        <p>{packet.redactedPreview}</p>
      </section>

      <section aria-labelledby="redaction-summary-heading">
        <h4 id="redaction-summary-heading">Redaction summary</h4>
        <p>{packet.redactionSummary}</p>
      </section>

      <section aria-labelledby="binding-refs-heading">
        <h4 id="binding-refs-heading">Exact binding refs</h4>
        <dl className="detail-grid">
          <DetailTerm label="review_packet_ref" value={packet.bindingRefs.reviewPacketRef} />
          <DetailTerm label="preview_result_ref" value={packet.bindingRefs.previewResultRef} />
          <DetailTerm label="redaction_summary_ref" value={packet.bindingRefs.redactionSummaryRef} />
          <DetailTerm label="file_ref" value={packet.bindingRefs.fileRef} />
          <DetailTerm label="safe_path_ref" value={packet.bindingRefs.safePathRef} />
        </dl>
      </section>

      <dl className="detail-grid">
        <DetailTerm label="Review-only decision status" value={packet.reviewDecisionStatus} />
        <DetailTerm label="Approval gate contract status" value={packet.approvalGateContractStatus} />
        <DetailTerm label="Receipt plan ref" value={packet.receiptPlan.receiptPlanRef} />
        <DetailTerm label="raw content stored" value={yesNo(packet.receiptPlan.rawContentStored)} includeInlineText />
        <DetailTerm label="unredacted preview stored" value={yesNo(packet.receiptPlan.unredactedPreviewStored)} />
        <DetailTerm label="raw absolute path stored" value={yesNo(packet.receiptPlan.rawAbsolutePathStored)} />
        <DetailTerm label="approval captured" value={yesNo(packet.receiptPlan.approvalCaptured)} />
        <DetailTerm label="approval persisted" value={yesNo(packet.receiptPlan.approvalPersisted)} />
        <DetailTerm label="context proposal created" value={yesNo(packet.receiptPlan.contextProposalCreated)} />
        <DetailTerm label="context injection performed" value={yesNo(packet.receiptPlan.contextInjectionPerformed)} />
        <DetailTerm label="memory write performed" value={yesNo(packet.receiptPlan.memoryWritePerformed)} />
        <DetailTerm label="export performed" value={yesNo(packet.receiptPlan.exportPerformed)} />
        <DetailTerm label="execution performed" value={yesNo(packet.receiptPlan.executionPerformed)} />
        <DetailTerm label="Receipt plan metadata" value={packet.receiptPlan.safeSummary} />
      </dl>

      <TagList label="Reason codes" values={packet.reasonCodes} />
      <TagList label="Authority boundary warnings" values={packet.authorityWarnings} />
    </article>
  );
}

function DetailTerm({ label, value, includeInlineText = false }: { label: string; value: string; includeInlineText?: boolean }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>
        {value}
        {includeInlineText ? <span className="visually-hidden">{`${label}: ${value}`}</span> : null}
      </dd>
    </div>
  );
}

function TagList({ label, values }: { label: string; values: string[] }) {
  return (
    <div className="tag-section">
      <h4>{label}</h4>
      <div className="note-list" aria-label={label}>
        {values.map((value) => (
          <span key={value}>{value}</span>
        ))}
      </div>
    </div>
  );
}

function yesNo(value: boolean): string {
  return value ? "yes" : "no";
}
