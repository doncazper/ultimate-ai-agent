import type { ReactNode } from "react";
import type {
  FounderLoopActionsInbox,
  FounderLoopActionItem,
  FounderLoopBriefingItem,
  FounderLoopMorningBriefing,
  FounderLoopPlanSummary,
  FounderLoopStorageStatus,
  FounderLoopTodaySummary,
} from "../api/types";

export function TodaySurfacePanel({ today }: { today: FounderLoopTodaySummary }) {
  return (
    <section className="page-section" aria-labelledby="today-surface-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Founder Loop</p>
          <h2 id="today-surface-heading">Today</h2>
        </div>
        <span className="status-pill compact">{today.status}</span>
      </div>
      <div className="metric-grid">
        <Metric label="Actions" value={today.sections.action_inbox_count} />
        <Metric label="Plans" value={today.sections.plan_count} />
        <Metric label="Memory" value={today.sections.memory_review_count} />
        <Metric label="Briefing" value={today.sections.briefing_count} />
      </div>
      <div className="founder-loop-grid">
        <LoopPanel title="Action inbox" route="/actions">
          {today.actions.map((item) => (
            <ActionItemCard item={item} key={item.item_ref} />
          ))}
        </LoopPanel>
        <LoopPanel title="Plans" route="/plans">
          {today.plans.map((plan) => (
            <PlanCard plan={plan} key={plan.plan_ref} />
          ))}
        </LoopPanel>
        <LoopPanel title="Morning Briefing" route="/briefing">
          {today.briefing_items.map((item) => (
            <BriefingCard item={item} key={item.briefing_ref} />
          ))}
        </LoopPanel>
        <LoopPanel title="Memory review" route="/memory">
          {today.memory_review_queue.map((item) => (
            <article className="review-card" key={item.review_ref}>
              <div className="review-card-heading">
                <h3>{item.title}</h3>
                <span>{item.status}</span>
              </div>
              <p>{item.safe_summary}</p>
              <RefList refs={item.evidence_refs} />
            </article>
          ))}
        </LoopPanel>
      </div>
      <BlockedStateList states={today.blocked_states} />
    </section>
  );
}

export function InboxSurfacePanel() {
  const blockedStates = [
    "email/calendar connector runtime is not scoped",
    "account authentication and credential handling are not scoped",
    "message send, archive, delete, label, move, or account write controls are absent",
    "raw message bodies, subjects, participants, attachment names, and calendar details are not displayed",
    "draft-only response proposal contract is not implemented in this slice",
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
          <h2 id="inbox-surface-heading">Inbox</h2>
        </div>
        <span className="status-pill compact">blocked/planned</span>
      </div>
      <p className="section-copy">
        Inbox is visible as the Founder Command Center triage slot, but no
        backend email, calendar, draft, or connector contract is enabled here.
        This surface is presentation-only posture until a scoped milestone adds
        read-only metadata contracts and tests.
      </p>
      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Route posture</h3>
            <span>not scoped</span>
          </div>
          <dl className="detail-list">
            <DetailTerm label="Frontend route" value="/inbox" />
            <DetailTerm label="Backend route" value="none in this slice" />
            <DetailTerm label="Side effect" value="local UI state only" />
            <DetailTerm
              label="Approval"
              value="future connector or draft actions require exact scoped approval"
            />
          </dl>
          <p>
            Next safe action: define read-only email/calendar metadata contracts
            before adding source status, draft proposal, or triage controls.
          </p>
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

export function ActionInboxSurfacePanel({
  inbox,
}: {
  inbox: FounderLoopActionsInbox;
}) {
  return (
    <section className="page-section" aria-labelledby="actions-surface-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Founder Loop</p>
          <h2 id="actions-surface-heading">Actions</h2>
        </div>
        <span className="status-pill compact">{inbox.status}</span>
      </div>
      <article className="status-card">
        <div className="status-card-header">
          <h3>State posture</h3>
          <span>{inbox.side_effect_class}</span>
        </div>
        <dl className="detail-list">
          <DetailTerm label="Storage ref" value={inbox.storage_ref} />
          <DetailTerm
            label="Mutation controls"
            value={inbox.mutating_controls_enabled ? "scoped" : "disabled"}
          />
          <DetailTerm label="Disabled state" value={inbox.disabled_state_label} />
        </dl>
      </article>
      <div className="review-grid">
        {inbox.items.map((item) => (
          <ActionItemCard item={item} key={item.item_ref} />
        ))}
      </div>
    </section>
  );
}

export function MorningBriefingPanel({
  briefing,
}: {
  briefing: FounderLoopMorningBriefing;
}) {
  return (
    <section className="page-section" aria-labelledby="briefing-surface-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Founder Loop</p>
          <h2 id="briefing-surface-heading">Morning Briefing</h2>
        </div>
        <span className="status-pill compact">{briefing.status}</span>
      </div>
      <div className="review-grid">
        {briefing.items.map((item) => (
          <BriefingCard item={item} key={item.briefing_ref} />
        ))}
      </div>
      <BlockedStateList states={briefing.blocked_states} />
    </section>
  );
}

export function FounderLoopStoragePanel({
  storage,
}: {
  storage: FounderLoopStorageStatus;
}) {
  return (
    <section className="page-section" aria-labelledby="storage-surface-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Founder Loop</p>
          <h2 id="storage-surface-heading">Storage</h2>
        </div>
        <span className="status-pill compact">{storage.postgres_sync_status}</span>
      </div>
      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Repository</h3>
            <span>{storage.schema_version}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm label="Storage ref" value={storage.storage_ref} />
            <DetailTerm label="SQLite ref" value={storage.sqlite_state_ref} />
            <DetailTerm
              label="Safe refs"
              value={storage.safe_refs_only ? "yes" : "blocked"}
            />
            <DetailTerm
              label="Raw content stored"
              value={storage.raw_content_stored ? "blocked" : "no"}
            />
          </dl>
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Backup minimum set</h3>
            <span>{storage.backup_manifest_ref}</span>
          </div>
          <RefList
            refs={storage.backup_manifest?.required_artifact_refs ?? []}
          />
        </article>
      </div>
      <div className="metric-grid">
        {Object.entries(storage.counts).map(([label, value]) => (
          <Metric key={label} label={label.replaceAll("_", " ")} value={value} />
        ))}
      </div>
      <RefList refs={Object.values(storage.jsonl_log_refs)} />
    </section>
  );
}

function LoopPanel({
  children,
  route,
  title,
}: {
  children: ReactNode;
  route: string;
  title: string;
}) {
  return (
    <article className="status-card loop-panel">
      <div className="status-card-header">
        <h3>{title}</h3>
        <a className="text-link" href={route}>
          View
        </a>
      </div>
      <div className="compact-stack">{children}</div>
    </article>
  );
}

function ActionItemCard({ item }: { item: FounderLoopActionItem }) {
  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>{item.title}</h3>
        <span>{item.priority}</span>
      </div>
      <p>{item.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Item ref" value={item.item_ref} />
        <DetailTerm label="Status" value={item.status} />
        <DetailTerm label="Side effect" value={item.side_effect_class} />
        <DetailTerm
          label="Approval before mutation"
          value={item.approval_required ? "required" : "not required"}
        />
      </dl>
      {item.blocked_state ? <p className="muted">{item.blocked_state}</p> : null}
      <RefList refs={item.evidence_refs} />
    </article>
  );
}

function PlanCard({ plan }: { plan: FounderLoopPlanSummary }) {
  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>{plan.title}</h3>
        <span>{plan.status}</span>
      </div>
      <p>{plan.safe_summary}</p>
      <p className="muted">{plan.next_step_summary}</p>
      <RefList refs={plan.evidence_refs} />
    </article>
  );
}

function BriefingCard({ item }: { item: FounderLoopBriefingItem }) {
  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>{item.title}</h3>
        <span>{item.status}</span>
      </div>
      <p>{item.safe_summary}</p>
      <RefList refs={item.evidence_refs} />
    </article>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <article className="status-card metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
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
      {refs.map((ref) => (
        <li key={ref}>{ref}</li>
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
