import type {
  FounderLoopSourceReadiness,
  FounderLoopSourceReadinessProposalCandidate,
} from "../api/types";

export function InboxSurfacePanel({
  sourceReadiness,
}: {
  sourceReadiness: FounderLoopSourceReadiness;
}) {
  const blockedStates = [
    "email/calendar connector runtime is not scoped",
    "account authentication and credential handling are not scoped",
    "message send, archive, delete, label, move, or account write controls are absent",
    "raw message bodies, subjects, participants, attachment names, and calendar details are not displayed",
    "connector draft proposals are review-only safe refs; send and write remain blocked",
    "memory writes, context injection, model/provider calls, and background fetch remain blocked",
  ];
  const evidenceRefs = [
    "docs/control_center/OPERATOR_SHELL_GAP_MAP.md#surface-matrix",
    "docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md#inbox-surface",
  ];

  return (
    <section className="page-section" aria-labelledby="inbox-surface-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Founder Loop</p>
          <h2 id="inbox-surface-heading">Source Inbox</h2>
        </div>
        <span className="status-pill compact">blocked/planned</span>
      </div>
      <p className="section-copy">
        Inbox is visible as the Founder Loop triage slot. A dedicated backend
        Source Readiness route reports read-only source posture, while live
        email, calendar, account, polling, and connector runtime behavior
        remain blocked.
      </p>
      <div className="panel-grid">
        <SourceReadinessCards
          items={sourceReadiness.source_readiness_items}
          posture={sourceReadiness.source_readiness_posture}
          sourceReadiness={sourceReadiness}
        />
        <ConnectorDraftProposalCards
          draftProposals={sourceReadiness.connector_draft_proposals}
        />
        <article className="status-card">
          <div className="status-card-header">
            <h3>Route posture</h3>
            <span>{sourceReadiness.status}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm label="Frontend route" value="/inbox" />
            <DetailTerm label="Backend route" value={sourceReadiness.route_ref} />
            <DetailTerm label="Side effect" value="local_dev_workspace_only" />
            <DetailTerm
              label="Approval"
              value="not required for read-only source readiness"
            />
          </dl>
          <p>Next safe action: {sourceReadiness.next_safe_action}</p>
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Evidence refs</h3>
            <span>docs only</span>
          </div>
          <p>
            These refs explain the planned boundary. They are not connector
            receipts, account proofs, or completion evidence.
          </p>
          <RefList refs={evidenceRefs} />
        </article>
      </div>
      <BlockedStateList states={blockedStates} />
    </section>
  );
}

function SourceReadinessCards({
  items,
  posture,
  sourceReadiness,
}: {
  items: FounderLoopSourceReadiness["source_readiness_items"];
  posture?: FounderLoopSourceReadiness["source_readiness_posture"];
  sourceReadiness?: FounderLoopSourceReadiness;
}) {
  if (items.length === 0) {
    return null;
  }
  return (
    <article className="status-card">
      <div className="status-card-header">
        <h3>Source readiness states</h3>
        <span>{items.length}</span>
      </div>
      {posture ? (
        <>
          <p className="muted">
            {posture.backend_owned
              ? `Backend-owned source readiness posture from ${posture.source}. This is read-only metadata; connector runtime, refresh, notifications, and delivery remain blocked.`
              : `Non-authoritative source readiness fallback from ${posture.source}. This describes UI shape only; reconnect the backend before treating source readiness as Python-core truth.`}
          </p>
          <dl aria-label="Source readiness posture" className="detail-list">
            <DetailTerm label="Source" value={posture.source} />
            <DetailTerm
              label="Backend owned"
              value={posture.backend_owned ? "yes" : "no"}
            />
            <DetailTerm label="Status" value={posture.status} />
            <DetailTerm
              label="Ready sources"
              value={`${posture.ready_source_count}/${posture.source_count}`}
            />
            <DetailTerm
              label="Blocked sources"
              value={String(posture.blocked_source_count)}
            />
            <DetailTerm
              label="Metadata-only sources"
              value={String(posture.metadata_only_source_count)}
            />
            <DetailTerm
              label="Not configured sources"
              value={String(posture.not_configured_source_count)}
            />
            <DetailTerm
              label="Connector runtime"
              value={posture.connector_runtime_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Source refresh"
              value={posture.source_refresh_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Notifications"
              value={
                posture.notification_delivery_enabled ? "enabled" : "blocked"
              }
            />
            <DetailTerm
              label="Next safe action"
              value={posture.next_safe_action}
            />
          </dl>
          <RefListWithFallback
            emptyLabel="Missing source contracts: none"
            refs={posture.missing_contract_refs}
          />
          <RefListWithFallback
            emptyLabel="Source posture blockers: none"
            refs={posture.blocked_state_refs}
          />
          <InlineListWithFallback
            emptyLabel="Supported source states: missing"
            items={posture.supported_statuses}
          />
        </>
      ) : null}
      {sourceReadiness ? (
        <>
          <dl aria-label="Dedicated source readiness route" className="detail-list">
            <DetailTerm label="Route" value={sourceReadiness.route_ref} />
            <DetailTerm
              label="Read model"
              value={sourceReadiness.backend_owned ? "backend-owned" : "mock-only"}
            />
            <DetailTerm
              label="Account auth"
              value={sourceReadiness.account_auth_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Raw source ingestion"
              value={
                sourceReadiness.raw_source_ingestion_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
            <DetailTerm
              label="Write authority"
              value={sourceReadiness.write_authority_enabled ? "enabled" : "blocked"}
            />
          </dl>
          <RefListWithFallback
            emptyLabel="Dedicated readiness route refs: none"
            refs={sourceReadiness.route_refs}
          />
          <RefListWithFallback
            emptyLabel="Blocked source authorities: none"
            refs={sourceReadiness.blocked_authority_refs}
          />
          <SourceReadinessProposalCards
            proposals={sourceReadiness.source_readiness_proposal_candidates ?? []}
          />
        </>
      ) : null}
      <ul className="ref-list">
        {items.map((item) => (
          <li key={item.source_ref}>
            {item.source_kind}: {item.status}; {item.safe_summary}
          </li>
        ))}
      </ul>
      <RefListWithFallback
        emptyLabel="Source evidence refs: none"
        refs={items.flatMap((item) => item.evidence_refs)}
      />
      <RefListWithFallback
        emptyLabel="Source readiness blockers: none"
        refs={items.flatMap((item) => item.blocked_state_refs)}
      />
    </article>
  );
}

function SourceReadinessProposalCards({
  proposals,
}: {
  proposals: FounderLoopSourceReadinessProposalCandidate[];
}) {
  if (proposals.length === 0) {
    return (
      <p className="muted">
        Source readiness proposal candidates are unavailable until the backend
        read model supplies proposal-only refs.
      </p>
    );
  }
  return (
    <div className="review-grid" aria-label="Source readiness proposal candidates">
      {proposals.map((proposal) => (
        <article className="review-card" key={proposal.proposal_ref}>
          <div className="review-card-heading">
            <h3>{proposal.title}</h3>
            <span>{proposal.proposal_classification}</span>
          </div>
          <p>{proposal.safe_summary}</p>
          <dl className="detail-list">
            <DetailTerm label="Proposal ref" value={proposal.proposal_ref} />
            <DetailTerm label="Action item ref" value={proposal.action_item_ref} />
            <DetailTerm label="Source kind" value={proposal.source_kind} />
            <DetailTerm
              label="Source readiness ref"
              value={proposal.source_readiness_ref}
            />
            <DetailTerm
              label="Missing contract"
              value={proposal.missing_contract_ref}
            />
            <DetailTerm label="Proposal kind" value={proposal.proposal_kind} />
            <DetailTerm
              label="Backend owned"
              value={proposal.backend_owned ? "yes" : "unavailable"}
            />
            <DetailTerm
              label="Local task eligibility"
              value={proposal.local_task_commit_eligible ? "eligible" : "blocked"}
            />
            <DetailTerm
              label="Connector runtime"
              value={proposal.connector_runtime_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Account auth"
              value={proposal.account_auth_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Raw source ingestion"
              value={
                proposal.raw_source_ingestion_enabled ? "enabled" : "blocked"
              }
            />
            <DetailTerm
              label="Write authority"
              value={proposal.write_authority_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm label="Next safe action" value={proposal.next_safe_action} />
          </dl>
          <RefListWithFallback
            emptyLabel="Blocked proposal authorities: none"
            refs={proposal.blocked_authority_refs}
          />
          <RefListWithFallback
            emptyLabel="Proposal evidence refs: missing"
            refs={proposal.evidence_refs}
          />
        </article>
      ))}
    </div>
  );
}

function ConnectorDraftProposalCards({
  draftProposals,
}: {
  draftProposals?: FounderLoopSourceReadiness["connector_draft_proposals"];
}) {
  if (!draftProposals) {
    return (
      <article className="status-card">
        <div className="status-card-header">
          <h3>Connector draft proposals</h3>
          <span>missing</span>
        </div>
        <p className="muted">
          Backend-owned connector draft proposals are unavailable; sends and
          writes remain blocked.
        </p>
      </article>
    );
  }

  return (
    <article className="status-card">
      <div className="status-card-header">
        <h3>Connector draft proposals</h3>
        <span>{draftProposals.status}</span>
      </div>
      <p className="muted">
        {draftProposals.backend_owned
          ? `${draftProposals.source} supplies review-only draft refs. No connector runtime, send, write, account auth, background sync, provider/model call, memory write, or context injection is enabled.`
          : `${draftProposals.source} supplies mock-only draft shape. Reconnect the backend before treating drafts as Python-core truth.`}
      </p>
      <dl className="detail-list">
        <DetailTerm label="Source" value={draftProposals.source} />
        <DetailTerm label="Contract" value={draftProposals.contract_ref} />
        <DetailTerm label="Route" value={draftProposals.route_ref} />
        <DetailTerm label="CLI" value={draftProposals.cli_ref} />
        <DetailTerm
          label="Backend owned"
          value={draftProposals.backend_owned ? "yes" : "no"}
        />
        <DetailTerm
          label="Draft proposals"
          value={String(draftProposals.proposal_count)}
        />
        <DetailTerm
          label="Connector runtime"
          value={draftProposals.connector_runtime_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Account auth"
          value={draftProposals.account_auth_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Connector sends"
          value={draftProposals.connector_sends_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Connector writes"
          value={draftProposals.connector_writes_enabled ? "enabled" : "blocked"}
        />
      </dl>
      <div className="review-grid" aria-label="Connector draft proposal refs">
        {draftProposals.proposals.map((proposal) => (
          <article className="review-card" key={proposal.proposal_ref}>
            <div className="review-card-heading">
              <h3>{proposal.draft_kind}</h3>
              <span>{proposal.status}</span>
            </div>
            <p>{proposal.safe_summary}</p>
            <dl className="detail-list">
              <DetailTerm label="Proposal ref" value={proposal.proposal_ref} />
              <DetailTerm label="Draft ref" value={proposal.draft_ref} />
              <DetailTerm label="Source" value={proposal.source_kind} />
              <DetailTerm label="Connector" value={proposal.connector_ref} />
              <DetailTerm label="Channel" value={proposal.channel_ref} />
              <DetailTerm
                label="Target session"
                value={proposal.target_session_ref}
              />
              <DetailTerm label="Delivery state" value={proposal.delivery_state} />
              <DetailTerm
                label="Approval to draft"
                value={
                  proposal.approval_required_to_draft ? "required" : "not required"
                }
              />
              <DetailTerm
                label="Approval to send/write"
                value={
                  proposal.approval_required_to_send
                    ? "required later"
                    : "not required"
                }
              />
              <DetailTerm
                label="Send performed"
                value={proposal.connector_send_performed ? "yes" : "no"}
              />
              <DetailTerm
                label="Write performed"
                value={proposal.connector_write_performed ? "yes" : "no"}
              />
            </dl>
            <InlineListWithFallback
              emptyLabel="Draft outline refs: none"
              items={proposal.redacted_outline}
            />
            <RefListWithFallback
              emptyLabel="Source metadata refs: none"
              refs={proposal.source_metadata_refs}
            />
            <RefListWithFallback
              emptyLabel="Blocked send/write refs: none"
              refs={proposal.blocked_send_write_reason_refs}
            />
            <RefListWithFallback
              emptyLabel="Draft proof refs: none"
              refs={proposal.proof_refs}
            />
          </article>
        ))}
      </div>
      <RefListWithFallback
        emptyLabel="Connector draft blockers: none"
        refs={draftProposals.blocked_authority_refs}
      />
    </article>
  );
}

function BlockedStateList({ states }: { states: string[] }) {
  if (states.length === 0) {
    return null;
  }
  return (
    <article className="status-card">
      <div className="status-card-header">
        <h3>Blocked states</h3>
        <span>explicit</span>
      </div>
      <ul className="ref-list">
        {states.map((state) => (
          <li key={state}>{state}</li>
        ))}
      </ul>
    </article>
  );
}

function RefList({ refs }: { refs: string[] }) {
  if (refs.length === 0) {
    return null;
  }
  return (
    <ul className="ref-list">
      {refs.map((ref, index) => (
        <li key={`${ref}-${index}`}>{ref}</li>
      ))}
    </ul>
  );
}

function RefListWithFallback({
  emptyLabel,
  refs,
}: {
  emptyLabel: string;
  refs?: string[];
}) {
  const safeRefs = refs ?? [];
  if (safeRefs.length === 0) {
    return <p className="muted">{emptyLabel}</p>;
  }
  return <RefList refs={safeRefs} />;
}

function InlineListWithFallback({
  emptyLabel,
  items,
}: {
  emptyLabel: string;
  items?: string[];
}) {
  const safeItems = items ?? [];
  if (safeItems.length === 0) {
    return <p className="muted">{emptyLabel}</p>;
  }
  return (
    <ul className="ref-list">
      {safeItems.map((item, index) => (
        <li key={`${item}-${index}`}>{item}</li>
      ))}
    </ul>
  );
}

function DetailTerm({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  );
}
