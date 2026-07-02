import type {
  ConnectorDeliveryReviewQueue,
  ConnectorDeliveryReviewQueueItem,
} from "../api/types";
import { EmptyState } from "./DataState";

const UNSAFE_CONNECTOR_TEXT_RE =
  /(raw[\s_-]?(message|body|content|payload|prompt|response)|provider[\s_-]?payload|bearer\s+|cookie|token|secret|api[_-]?key|password|\/Users\/|\/home\/|[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})/i;

function safeConnectorText(value: string | null | undefined): string {
  if (!value) {
    return "not recorded";
  }
  if (UNSAFE_CONNECTOR_TEXT_RE.test(value)) {
    return "redacted-ref:connector-delivery-review";
  }
  return value;
}

function safeConnectorRefs(values: string[]): string[] {
  return values.map(safeConnectorText);
}

function connectorStateLabel(value: string): string {
  return safeConnectorText(value).replaceAll("_", " ");
}

export function ConnectorDeliveryReviewQueuePanel({
  compact = false,
  queue,
}: {
  compact?: boolean;
  queue?: ConnectorDeliveryReviewQueue;
}) {
  if (!queue) {
    return (
      <section
        className={`page-section${compact ? " compact-section" : ""}`}
        aria-label="Connector delivery review queue"
      >
        <EmptyState
          title="Connector delivery review unavailable"
          message="Backend-owned connector delivery review refs are not available; delivery execution remains blocked/planned."
        />
      </section>
    );
  }

  const sourceLabel = queue.backend_owned
    ? "backend-owned"
    : "mock-only / non-authoritative";
  return (
    <section
      className={`page-section${compact ? " compact-section" : ""}`}
      aria-label="Connector delivery review queue"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">Connector delivery</p>
          <h3>Connector Delivery Review Queue</h3>
        </div>
        <span className="status-pill compact">{sourceLabel}</span>
      </div>
      <p className="safe-copy">
        {safeConnectorText(queue.safe_summary)} No send, write, account sync, retry worker,
        scheduler, provider call, web runtime, browser runtime, shell runtime, or delivery
        execution is available from this surface.
      </p>
      <div className="panel-grid compact-grid" aria-label="Connector delivery review counts">
        <div className="metric-card">
          <span>Review deliveries</span>
          <strong>{queue.delivery_count}</strong>
        </div>
        <div className="metric-card">
          <span>Ready metadata only / not sent</span>
          <strong>{queue.delivery_ready_not_sent_count}</strong>
        </div>
        <div className="metric-card">
          <span>Blocked</span>
          <strong>{queue.blocked_count}</strong>
        </div>
        <div className="metric-card">
          <span>Delivery execution</span>
          <strong>{queue.delivery_execution_enabled ? "enabled" : "blocked/planned"}</strong>
        </div>
      </div>
      {queue.queue_items.length > 0 ? (
        <div className="review-list" aria-label="Connector delivery review rows">
          {queue.queue_items.map((item) => (
            <ConnectorDeliveryReviewCard item={item} key={item.item_ref} />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No connector delivery refs"
          message="No backend-owned connector delivery review refs are available yet."
        />
      )}
      <ConnectorRefList
        label="Connector delivery blocked authority refs"
        values={queue.blocked_authority_refs}
      />
    </section>
  );
}

function ConnectorDeliveryReviewCard({
  item,
}: {
  item: ConnectorDeliveryReviewQueueItem;
}) {
  return (
    <article className="review-card" aria-label={`Connector delivery review ${item.delivery_ref}`}>
      <div className="review-card-heading">
        <h3>{safeConnectorText(item.delivery_ref)}</h3>
        <span>{safeConnectorText(item.delivery_state_label)}</span>
      </div>
      <p>{safeConnectorText(item.safe_summary)}</p>
      <p className="review-meta">
        state: {connectorStateLabel(item.latest_state)} | run: {safeConnectorText(item.run_ref)}
      </p>
      <dl className="detail-grid compact-detail-grid">
        <div>
          <dt>Connector ref</dt>
          <dd>{safeConnectorText(item.connector_ref)}</dd>
        </div>
        <div>
          <dt>Channel ref</dt>
          <dd>{safeConnectorText(item.channel_ref)}</dd>
        </div>
        <div>
          <dt>Target/session ref</dt>
          <dd>{safeConnectorText(item.target_session_ref)}</dd>
        </div>
        <div>
          <dt>Execution posture</dt>
          <dd>{safeConnectorText(item.delivery_execution_posture)}</dd>
        </div>
        <div>
          <dt>Subject summary ref</dt>
          <dd>{safeConnectorText(item.redacted_subject_refs[0])}</dd>
        </div>
        <div>
          <dt>Body summary ref</dt>
          <dd>{safeConnectorText(item.redacted_body_summary_refs[0])}</dd>
        </div>
        <div>
          <dt>Next safe action</dt>
          <dd>{safeConnectorText(item.next_safe_action)}</dd>
        </div>
      </dl>
      <ConnectorRefList
        label="Outbound approval refs"
        values={item.outbound_approval_refs}
      />
      <ConnectorRefList
        label="Idempotency refs"
        values={item.idempotency_key_refs}
      />
      <ConnectorRefList
        label="Evidence and proof refs"
        values={[...item.evidence_refs, ...item.proof_refs]}
      />
      <ConnectorRefList
        label="Blocked reason refs"
        values={item.blocked_reason_refs}
      />
      <ConnectorRefList
        label="Blocked authority refs"
        values={item.blocked_authority_refs}
      />
    </article>
  );
}

function ConnectorRefList({
  label,
  values,
}: {
  label: string;
  values: string[];
}) {
  if (values.length === 0) {
    return null;
  }
  return (
    <div className="tag-list" aria-label={label}>
      <strong>{label}</strong>
      <div>
        {safeConnectorRefs(values).map((value, index) => (
          <span key={`${value}:${index}`}>{value}</span>
        ))}
      </div>
    </div>
  );
}
