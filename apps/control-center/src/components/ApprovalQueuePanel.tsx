import { useState } from "react";
import type {
  ApprovalQueueItem,
  ApprovalSummary,
  M15ReviewData,
  RunAttachedApprovalQueue,
  RunAttachedApprovalQueueItem,
  UnifiedApprovalReview,
  UnifiedApprovalReviewItem,
} from "../api/types";
import { EmptyState } from "./DataState";
import { ConnectorDeliveryReviewQueuePanel } from "./ConnectorDeliveryReviewQueuePanel";
import { OperatorSurfaceStates } from "./OperatorSurfaceStates";

export function ApprovalQueuePanel({
  review,
  summary,
  queue,
}: {
  review: M15ReviewData;
  summary?: ApprovalSummary;
  queue?: RunAttachedApprovalQueue;
}) {
  const queueItems = queue?.queue_items ?? [];
  const [selectedQueueRef, setSelectedQueueRef] = useState(queueItems[0]?.item_ref ?? "");
  const selectedQueueItem =
    queueItems.find((item) => item.item_ref === selectedQueueRef) ?? queueItems[0];
  const queueTruthLabel = queue?.backend_owned
    ? "Backend-owned run-attached approval queue"
    : "Mock-only non-authoritative approval queue fallback";
  const emptyQueueMessage = queue?.backend_owned === false
    ? "Only mock-only non-authoritative approval queue fallback refs are available."
    : "No backend-owned run-attached approval queue refs are available yet.";
  const [selectedPreviewRef, setSelectedPreviewRef] = useState(review.approvalQueue[0]?.approvalRef ?? "");
  const selectedPreview =
    review.approvalQueue.find((item) => item.approvalRef === selectedPreviewRef) ??
    review.approvalQueue[0];

  return (
    <section className="page-section" aria-labelledby="approval-queue-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">M15 review surface</p>
          <h2 id="approval-queue-heading">Run-attached Approval Queue</h2>
        </div>
        <span className="status-pill compact">read-only / no approval authority</span>
      </div>
      <p className="section-copy">
        Shows approval request, grant, denial, expiry, revocation, receipt, and run refs attached to
        durable run state. This view cannot approve, deny, revoke, resume, execute, or bypass
        LocalApprovalAuthority.
      </p>
      <p className="safe-copy">
        This UI cannot grant, deny, execute, or bypass approvals. Approval refs are identifiers only and
        never authority. Python Agent Core remains the only approval authority.
      </p>
      {summary ? <ApprovalSummaryStrip summary={summary} /> : null}
      {queue ? <RunAttachedApprovalSummaryStrip queue={queue} /> : null}
      {queue?.unified_review ? (
        <UnifiedApprovalReviewPanel review={queue.unified_review} />
      ) : null}
      <ConnectorDeliveryReviewQueuePanel
        queue={queue?.connector_delivery_review_queue}
      />
      <OperatorSurfaceStates surface="Approvals" />
      <ReviewWarningBar codes={review.warningCodes} />
      {queueItems.length > 0 && selectedQueueItem ? (
        <div className="review-layout">
          <div
            className="review-list"
            aria-label={queueTruthLabel}
          >
            {queueItems.map((item) => (
              <RunAttachedApprovalQueueRow
                key={item.item_ref}
                item={item}
                selected={item.item_ref === selectedQueueItem.item_ref}
                onSelect={setSelectedQueueRef}
              />
            ))}
          </div>
          <RunAttachedApprovalQueueDetail item={selectedQueueItem} />
        </div>
      ) : (
        <EmptyState
          title="No run-attached approval refs"
          message={emptyQueueMessage}
        />
      )}
      {review.approvalQueue.length > 0 && selectedPreview ? (
        <section
          className="page-section compact-section"
          aria-label="Legacy approval preview rows"
        >
          <div className="section-heading">
            <div>
              <p className="eyebrow">Legacy reference</p>
              <h3>Preview-only approval cards</h3>
            </div>
            <span className="status-pill compact">mock / non-authoritative</span>
          </div>
          <p className="safe-copy">{review.authorityBoundary}</p>
          <div className="review-layout">
            <div
              className="review-list"
              aria-label="Preview-only approval request summaries"
            >
              {review.approvalQueue.map((item) => (
                <ApprovalQueueRow
                  key={item.approvalRef}
                  item={item}
                  selected={item.approvalRef === selectedPreview.approvalRef}
                  onSelect={setSelectedPreviewRef}
                />
              ))}
            </div>
            <ApprovalQueueDetail item={selectedPreview} />
          </div>
        </section>
      ) : (
        <EmptyState
          title="No preview approval cards"
          message="No legacy preview-only approval cards are available."
        />
      )}
    </section>
  );
}

function ApprovalSummaryStrip({ summary }: { summary: ApprovalSummary }) {
  return (
    <div className="panel-grid compact-grid" aria-label="Backend approval summary">
      <div className="metric-card">
        <span>Pending summaries</span>
        <strong>{summary.pending_count}</strong>
      </div>
      <div className="metric-card">
        <span>Backend grant records present</span>
        <strong>{summary.approval_grants_created ? "yes" : "no"}</strong>
      </div>
      <div className="metric-card">
        <span>Arbitrary ref authority</span>
        <strong>{summary.arbitrary_approval_ref_authority ? "yes" : "no"}</strong>
      </div>
      <p className="safe-copy">{summary.summary}</p>
    </div>
  );
}

function RunAttachedApprovalSummaryStrip({
  queue,
}: {
  queue: RunAttachedApprovalQueue;
}) {
  const sourceLabel = queue.backend_owned
    ? "backend-owned"
    : "mock-only / non-authoritative";
  return (
    <div className="panel-grid compact-grid" aria-label="Run-attached approval queue summary">
      <div className="metric-card">
        <span>Run-attached items</span>
        <strong>{queue.summary.queue_item_count}</strong>
      </div>
      <div className="metric-card">
        <span>Pending by run</span>
        <strong>{queue.summary.pending_count}</strong>
      </div>
      <div className="metric-card">
        <span>Missing attachment refs</span>
        <strong>{queue.summary.durable_attachment_missing_count}</strong>
      </div>
      <div className="metric-card">
        <span>Queue source</span>
        <strong>{sourceLabel}</strong>
      </div>
      <p className="safe-copy">{queue.summary.safe_summary}</p>
    </div>
  );
}

function UnifiedApprovalReviewPanel({
  review,
}: {
  review: UnifiedApprovalReview;
}) {
  const sourceLabel = review.backend_owned
    ? "backend-owned"
    : "mock-only / non-authoritative";
  return (
    <section className="page-section compact-section" aria-label="Unified approval review">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Unified review</p>
          <h3>Approval Review Across Runs And Handoffs</h3>
        </div>
        <span className="status-pill compact">{sourceLabel}</span>
      </div>
      <p className="safe-copy">{review.safe_summary}</p>
      <div className="panel-grid compact-grid" aria-label="Unified approval review counts">
        <div className="metric-card">
          <span>Review items</span>
          <strong>{review.history_count}</strong>
        </div>
        <div className="metric-card">
          <span>Pending refs</span>
          <strong>{review.pending_count}</strong>
        </div>
        <div className="metric-card">
          <span>Blocked refs</span>
          <strong>{review.blocked_count}</strong>
        </div>
        <div className="metric-card">
          <span>Mutation authority</span>
          <strong>{review.ui_mutation_controls_enabled ? "enabled" : "blocked"}</strong>
        </div>
      </div>
      <div className="review-list" aria-label="Unified approval review sources">
        {review.review_items.map((item) => (
          <UnifiedApprovalReviewRow key={item.item_ref} item={item} />
        ))}
      </div>
      <TagList label="Unified proof refs" values={review.proof_refs} />
      <TagList label="Unified blocked authority refs" values={review.blocked_authority_refs} />
      <p className="safe-copy">
        This unified review has no approve, deny, revoke, resume, execute, connector send, tool
        execution, provider call, worker, or scheduler control.
      </p>
    </section>
  );
}

function UnifiedApprovalReviewRow({
  item,
}: {
  item: UnifiedApprovalReviewItem;
}) {
  const sourceLabel = item.source_type.replaceAll("_", " ");
  return (
    <article className="review-card" aria-label={`Approval review source ${item.source_type}`}>
      <div className="review-card-heading">
        <h3>{item.title}</h3>
        <span>{stateLabel(item.approval_state)}</span>
      </div>
      <p>{item.safe_summary}</p>
      <p className="review-meta">
        source: {sourceLabel} | run: {item.run_ref}
      </p>
      <dl className="detail-grid compact-detail-grid">
        <div>
          <dt>Scope ref</dt>
          <dd>{item.requested_scope_ref}</dd>
        </div>
        <div>
          <dt>Proof ref</dt>
          <dd>{item.proof_refs[0] ?? "not recorded"}</dd>
        </div>
        <div>
          <dt>Next safe action</dt>
          <dd>{item.next_safe_action}</dd>
        </div>
      </dl>
      <TagList
        label={`${sourceLabel} authority blockers`}
        values={item.blocked_authority_refs}
      />
    </article>
  );
}

function RunAttachedApprovalQueueRow({
  item,
  selected,
  onSelect,
}: {
  item: RunAttachedApprovalQueueItem;
  selected: boolean;
  onSelect: (itemRef: string) => void;
}) {
  return (
    <article className={`review-card${selected ? " selected" : ""}`}>
      <div className="review-card-heading">
        <h3>{item.approval_request_ref}</h3>
        <span>{stateLabel(item.approval_state)}</span>
      </div>
      <p>{item.safe_summary}</p>
      <p className="review-meta">
        run: {item.run_ref} | attachment: {item.durable_attachment_status}
      </p>
      <button type="button" className="secondary-button" onClick={() => onSelect(item.item_ref)}>
        View details
      </button>
    </article>
  );
}

function RunAttachedApprovalQueueDetail({ item }: { item: RunAttachedApprovalQueueItem }) {
  return (
    <article className="panel review-detail" aria-label="Run-attached approval detail">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Run ref</p>
          <h3>{item.approval_request_ref}</h3>
        </div>
        <span>{stateLabel(item.approval_state)}</span>
      </div>
      <dl className="detail-grid">
        <div>
          <dt>Run ref</dt>
          <dd>{item.run_ref}</dd>
        </div>
        <div>
          <dt>Step ref</dt>
          <dd>{item.step_ref}</dd>
        </div>
        <div>
          <dt>Scope ref</dt>
          <dd>{item.requested_scope_ref}</dd>
        </div>
        <div>
          <dt>Event type</dt>
          <dd>{item.approval_event_type}</dd>
        </div>
        <div>
          <dt>Receipt ref</dt>
          <dd>{item.approval_receipt_ref ?? "not recorded"}</dd>
        </div>
        <div>
          <dt>Expiry ref</dt>
          <dd>{item.expiry_ref ?? "not provided"}</dd>
        </div>
        <div>
          <dt>Revocation ref</dt>
          <dd>{item.revocation_ref ?? "not provided"}</dd>
        </div>
        <div>
          <dt>Required next action</dt>
          <dd>{item.required_next_action}</dd>
        </div>
      </dl>
      <TagList label="Evidence refs" values={item.evidence_refs} />
      <TagList label="Blocked authority refs" values={item.blocked_authority_refs} />
      <TagList label="Durable receipt refs" values={item.receipt_refs} />
      <p className="safe-copy">
        Approval refs are identifiers only. This panel does not approve, deny, revoke, resume,
        execute, call tools, write connectors, or call models.
      </p>
    </article>
  );
}

function stateLabel(value: string): string {
  switch (value) {
    case "requested":
      return "approval request attached";
    case "approved":
      return "grant recorded / no execution";
    case "denied":
      return "denial recorded";
    case "expired":
      return "expired or stale";
    case "revoked":
      return "revoked";
    case "scope_mismatch_blocked":
      return "blocked: scope mismatch";
    case "blocked":
      return "blocked: missing backend authority";
    default:
      return value.replaceAll("_", " ");
  }
}

function ApprovalQueueRow({
  item,
  selected,
  onSelect,
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
      <p className="safe-copy">
        Approval refs are identifiers only and never authority; Python Agent Core remains the only
        approval authority.
      </p>
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
