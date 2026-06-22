import type { ReactNode } from "react";
import type {
  FounderLoopActionsInbox,
  FounderLoopActionItem,
  FounderLoopBriefingItem,
  FounderLoopEvidenceTimelineItem,
  FounderLoopMemoryReviewItem,
  FounderLoopMorningBriefing,
  FounderLoopPlanSummary,
  FounderLoopStorageStatus,
  FounderLoopTodaySummary,
} from "../api/types";

const evidenceHistoryKeys = [
  "proposed",
  "approved",
  "happened",
  "changed",
  "undoable",
  "stale",
  "blocked",
] as const;

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
      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Product spine contract</h3>
            <span>read-only</span>
          </div>
          <dl className="detail-list">
            <DetailTerm label="Contract ref" value={today.product_spine_contract_ref} />
            <DetailTerm
              label="Loop visibility sufficient"
              value={
                today.module_completion_contract.visibility_is_sufficient_for_completion
                  ? "yes"
                  : "no"
              }
            />
            <DetailTerm
              label="Standalone completion"
              value={
                today.module_completion_contract.standalone_module_complete_allowed
                  ? "allowed"
                  : "blocked"
              }
            />
            <DetailTerm
              label="Execution authorized"
              value={today.plan_action_state.execution_authorized ? "yes" : "no"}
            />
            <DetailTerm
              label="Source refresh"
              value={today.stale_source_posture.source_refresh_enabled ? "enabled" : "blocked"}
            />
          </dl>
          <p>{today.module_completion_contract.visibility_requirement}</p>
          <RefList refs={today.required_loop_surfaces} />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Today required signals</h3>
            <span>{today.required_today_signals.length}</span>
          </div>
          <InlineListWithFallback
            emptyLabel="Required signals missing from Today contract"
            items={today.required_today_signals.map((signal) => signal.signal)}
          />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Plan/action state</h3>
            <span>{today.plan_action_state.action_envelope_contract_status}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Action count"
              value={String(today.plan_action_state.action_count)}
            />
            <DetailTerm
              label="Plan count"
              value={String(today.plan_action_state.plan_count)}
            />
            <DetailTerm
              label="Mutation controls"
              value={today.plan_action_state.mutating_controls_enabled ? "enabled" : "blocked"}
            />
          </dl>
          <RefList refs={today.follow_up_refs} />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Next safe actions</h3>
            <span>{today.next_safe_actions.length}</span>
          </div>
          <ul className="ref-list">
            {today.next_safe_actions.map((item) => (
              <li key={`${item.surface}:${item.source_ref}`}>
                {item.surface}: {item.safe_summary}
              </li>
            ))}
          </ul>
        </article>
      </div>
      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Module feed contract</h3>
            <span>{today.module_feed_contract.length}</span>
          </div>
          <ul className="ref-list">
            {today.module_feed_contract.map((feed) => (
              <li key={feed.module}>
                {feed.module}: {feed.status}; standalone complete{" "}
                {feed.standalone_complete_allowed ? "allowed" : "blocked"}
              </li>
            ))}
          </ul>
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Stale-source posture</h3>
            <span>{today.stale_source_posture.status}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Connector runtime"
              value={today.stale_source_posture.connector_runtime_enabled ? "enabled" : "blocked"}
            />
          </dl>
          <RefList refs={today.stale_source_posture.stale_state_refs} />
        </article>
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
            <MemoryReviewCard item={item} key={item.review_ref} />
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
          <DetailTerm
            label="Backend route"
            value={inbox.route_ref ?? "/control-center/actions/inbox"}
          />
          <DetailTerm label="Storage ref" value={inbox.storage_ref} />
          <DetailTerm
            label="Approval before mutation"
            value={inbox.approval_required_before_mutation ? "required" : "not required"}
          />
          <DetailTerm
            label="Mutation controls"
            value={inbox.mutating_controls_enabled ? "scoped" : "disabled"}
          />
          <DetailTerm label="Disabled state" value={inbox.disabled_state_label} />
        </dl>
      </article>
      <article className="status-card">
        <div className="status-card-header">
          <h3>Local prerequisites</h3>
          <span>read-only refs</span>
        </div>
        <p>
          These refs expose readiness only. They do not grant approval, state
          changes, connector writes, or model/provider authority.
        </p>
        <RefList refs={inbox.read_only_route_refs ?? []} />
        <RefList refs={inbox.local_prerequisite_refs ?? []} />
      </article>
      <div className="review-grid">
        {inbox.items.map((item) => (
          <ActionItemCard item={item} key={item.item_ref} />
        ))}
      </div>
      <BlockedStateList states={inbox.blocked_states ?? []} />
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
      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Source posture</h3>
            <span>{briefing.side_effect_class}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Backend route"
              value={briefing.route_ref ?? "/control-center/morning-briefing/summary"}
            />
            <DetailTerm label="Storage ref" value={briefing.storage_ref} />
            <DetailTerm
              label="Source readiness"
              value={
                briefing.source_readiness ??
                "blocked_missing_email_calendar_notification_contracts"
              }
            />
            <DetailTerm
              label="Bounded preview"
              value={briefing.bounded_preview_only ? "yes" : "blocked"}
            />
            <DetailTerm
              label="Refresh"
              value={briefing.refresh_enabled ? "scoped" : "disabled"}
            />
            <DetailTerm
              label="Notifications"
              value={briefing.notification_delivery_enabled ? "scoped" : "disabled"}
            />
            <DetailTerm
              label="Authority boundary"
              value={
                briefing.authority_boundary ??
                "Read-only briefing summary; source reads and delivery remain unscoped."
              }
            />
          </dl>
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Missing contracts</h3>
            <span>explicit blockers</span>
          </div>
          <p>
            Briefing uses local safe refs only. Email, calendar, refresh, and
            notification source contracts remain blocked in this slice.
          </p>
          <RefList refs={briefing.read_only_route_refs ?? []} />
          <RefList refs={briefing.local_prerequisite_refs ?? []} />
          <RefList refs={briefing.missing_contract_refs ?? []} />
        </article>
      </div>
      <div className="review-grid">
        {briefing.items.map((item) => (
          <BriefingCard item={item} key={item.briefing_ref} />
        ))}
      </div>
      <BlockedStateList states={briefing.blocked_states ?? []} />
    </section>
  );
}

export function MemoryReviewSurfacePanel({
  today,
}: {
  today: FounderLoopTodaySummary;
}) {
  return (
    <section className="page-section" aria-labelledby="memory-review-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Founder Loop</p>
          <h2 id="memory-review-heading">Memory Review</h2>
        </div>
        <span className="status-pill compact">
          {today.memory_review_status ?? "storage_backed_review_queue"}
        </span>
      </div>
      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Review posture</h3>
            <span>{today.side_effect_class}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Frontend route"
              value={today.memory_review_route_ref ?? "/memory"}
            />
            <DetailTerm
              label="Backend route"
              value={
                today.memory_review_backend_route_ref ??
                "GET /control-center/today/summary"
              }
            />
            <DetailTerm label="Storage ref" value={today.storage_ref} />
            <DetailTerm
              label="Memory writes"
              value={today.memory_write_enabled ? "scoped" : "disabled"}
            />
            <DetailTerm
              label="Memory deletes"
              value={today.memory_delete_enabled ? "scoped" : "disabled"}
            />
            <DetailTerm
              label="Context injection"
              value={today.context_injection_enabled ? "scoped" : "disabled"}
            />
            <DetailTerm
              label="Authority boundary"
              value={
                today.memory_review_authority_boundary ??
                "Review-only memory candidates; recall is not truth."
              }
            />
          </dl>
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Missing contracts</h3>
            <span>explicit blockers</span>
          </div>
          <p>
            Memory review is inspection-only. Accept, correct, reject, retain,
            delete, write, and context-injection decisions require later scoped
            contracts.
          </p>
          <RefList refs={today.memory_review_missing_contract_refs ?? []} />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Source provenance</h3>
            <span>{today.memory_source_required_kinds.length}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Contract ref"
              value={today.memory_source_provenance_contract_ref}
            />
            <DetailTerm
              label="Review before recall"
              value={
                today.memory_source_review_posture.review_required_before_recall
                  ? "required"
                  : "missing"
              }
            />
            <DetailTerm
              label="Connector runtime"
              value={
                today.memory_source_review_posture.connector_runtime_enabled
                  ? "enabled"
                  : "disabled"
              }
            />
            <DetailTerm
              label="Production authority"
              value={
                today.memory_source_review_posture.production_authority_enabled
                  ? "enabled"
                  : "disabled"
              }
            />
          </dl>
          <RefList refs={today.memory_source_denied_content_refs ?? []} />
        </article>
      </div>
      <div className="review-grid">
        {today.memory_review_queue.map((item) => (
          <MemoryReviewCard item={item} key={item.review_ref} />
        ))}
      </div>
      <BlockedStateList states={today.memory_review_blocked_states ?? []} />
    </section>
  );
}

export function EvidenceTimelineSurfacePanel({
  today,
}: {
  today: FounderLoopTodaySummary;
}) {
  const timeline = today.evidence_timeline;

  return (
    <section className="page-section" aria-labelledby="evidence-timeline-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Founder Loop</p>
          <h2 id="evidence-timeline-heading">Evidence Timeline</h2>
        </div>
        <span className="status-pill compact">
          {today.evidence_timeline_status ?? "storage_backed_redacted_history_grammar_refs"}
        </span>
      </div>
      <div className="metric-grid">
        <Metric
          label="Timeline items"
          value={today.sections.evidence_timeline_count ?? timeline.length}
        />
        <Metric label="Receipt/audit refs" value={countTimelineRefs(timeline, ["receipt_refs", "audit_refs"])} />
        <Metric label="Rollback refs" value={countTimelineRefs(timeline, ["rollback_refs"])} />
        <Metric label="Latency/Gate refs" value={countTimelineRefs(timeline, ["latency_refs", "foundation_gate_refs"])} />
      </div>
      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Evidence history grammar</h3>
            <span>read-only</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Contract ref"
              value={today.evidence_history_contract_ref}
            />
            <DetailTerm
              label="Required questions"
              value={String(today.evidence_history_required_questions.length)}
            />
          </dl>
          <RefList refs={today.evidence_history_required_states} />
          <ul className="ref-list">
            {today.evidence_history_required_questions.map((question) => (
              <li key={question.key}>{question.question}</li>
            ))}
          </ul>
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Timeline posture</h3>
            <span>{today.side_effect_class}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Frontend route"
              value={today.evidence_timeline_route_ref ?? "/evidence"}
            />
            <DetailTerm
              label="Backend route"
              value={
                today.evidence_timeline_backend_route_ref ??
                "GET /control-center/today/summary"
              }
            />
            <DetailTerm label="Storage ref" value={today.storage_ref} />
            <DetailTerm
              label="Authority boundary"
              value={
                today.evidence_timeline_authority_boundary ??
                "Evidence Timeline is safe-ref and redacted-summary only."
              }
            />
          </dl>
          <p>
            Timeline entries are readable inspection summaries. Private source
            artifacts, prompts, responses, logs, local identifiers, auth
            material, and secret-like values stay omitted.
          </p>
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Blocked authority</h3>
            <span>safe refs only</span>
          </div>
          <p>
            Approval refs are identifiers only, rollback refs do not perform
            rollback, Foundation Gate refs do not confer release authority, and
            latency refs are measurement evidence only.
          </p>
          <InlineListWithFallback
            emptyLabel="Timeline blockers: evidence remains inspection-only"
            items={today.evidence_timeline_blocked_states ?? []}
          />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Surface bindings</h3>
            <span>{today.evidence_history_surface_bindings.length}</span>
          </div>
          <ul className="ref-list">
            {today.evidence_history_surface_bindings.map((binding) => (
              <li key={binding.surface}>
                {binding.surface}: {binding.current_status}
              </li>
            ))}
          </ul>
        </article>
      </div>
      {timeline.length === 0 ? (
        <article className="status-card">
          <div className="status-card-header">
            <h3>No timeline refs</h3>
            <span>missing</span>
          </div>
          <p>
            Evidence Timeline data is missing from the current summary. Keep
            evidence review blocked until storage-backed safe refs are present.
          </p>
        </article>
      ) : (
        <div className="review-grid">
          {timeline.map((item) => (
            <EvidenceTimelineCard item={item} key={item.timeline_item_ref} />
          ))}
        </div>
      )}
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

function countTimelineRefs(
  timeline: FounderLoopEvidenceTimelineItem[],
  fields: Array<
    | "receipt_refs"
    | "audit_refs"
    | "rollback_refs"
    | "latency_refs"
    | "foundation_gate_refs"
  >,
) {
  return timeline.reduce(
    (count, item) =>
      count +
      fields.reduce((fieldCount, field) => fieldCount + item[field].length, 0),
    0,
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

function EvidenceTimelineCard({
  item,
}: {
  item: FounderLoopEvidenceTimelineItem;
}) {
  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>{item.title}</h3>
        <span>{item.item_kind}</span>
      </div>
      <p>{item.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Timeline ref" value={item.timeline_item_ref} />
        <DetailTerm label="History contract" value={item.history_contract_ref} />
        <DetailTerm label="Side effect" value={item.side_effect_class} />
        <DetailTerm label="Authority posture" value={item.authority_posture} />
        <DetailTerm label="Approval posture" value={item.approval_posture} />
        <DetailTerm
          label="Approval ref authority"
          value={item.approval_ref_authority ? "yes" : "no"}
        />
        <DetailTerm
          label="Rollback execution"
          value={item.rollback_execution_enabled ? "enabled" : "not scoped"}
        />
        <DetailTerm
          label="Memory truth authority"
          value={item.memory_truth_authority ? "yes" : "no"}
        />
        <DetailTerm
          label="Context injection"
          value={item.context_injection_authorized ? "authorized" : "not authorized"}
        />
        <DetailTerm
          label="Raw evidence included"
          value={item.raw_evidence_included ? "yes" : "no"}
        />
        <DetailTerm label="Redaction" value={item.redaction_status} />
        <DetailTerm label="Stale-state posture" value={item.stale_state} />
        <DetailTerm
          label="Missing evidence posture"
          value={item.missing_evidence_posture}
        />
        <DetailTerm label="Next safe action" value={item.next_safe_action} />
      </dl>
      <div>
        <div className="status-card-header">
          <h4>History answers</h4>
          <span>{evidenceHistoryKeys.length}</span>
        </div>
        <ul className="ref-list">
          {evidenceHistoryKeys.map((key) => {
            const answer = item.history_answers[key];
            return (
              <li key={key}>
                {answer.question}: {answer.answer} ({answer.status})
              </li>
            );
          })}
        </ul>
      </div>
      <RefListWithFallback
        emptyLabel="Source refs: missing until evidence binding exists"
        refs={item.source_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Status refs: missing until status binding exists"
        refs={item.status_refs ?? []}
      />
      <InlineListWithFallback
        emptyLabel="Route refs: no route binding available"
        items={item.related_route_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Receipt refs: not available for this item"
        refs={item.receipt_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Audit refs: not available for this item"
        refs={item.audit_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Replay refs: not available for this item"
        refs={item.replay_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Rollback refs: not available for this item"
        refs={item.rollback_refs ?? []}
      />
      <InlineListWithFallback
        emptyLabel="Rollback blockers: rollback remains inspection-only"
        items={item.rollback_blockers ?? []}
      />
      <RefListWithFallback
        emptyLabel="Latency refs: not available for this item"
        refs={item.latency_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Foundation Gate refs: not available for this item"
        refs={item.foundation_gate_refs ?? []}
      />
      <InlineListWithFallback
        emptyLabel="Item blockers: evidence remains inspection-only"
        items={item.blocked_states ?? []}
      />
    </article>
  );
}

function ActionItemCard({ item }: { item: FounderLoopActionItem }) {
  const riskClass = item.risk_class ?? "unspecified";
  const authorityBoundary =
    item.authority_boundary ?? "review-only; exact backend contract required";
  const approvalEnvelopeValue = item.approval_envelope_ref
    ? item.approval_envelope_ref
    : "missing until scoped contract";
  const stateChangeContractValue = item.state_change_contract_ref
    ? item.state_change_contract_ref
    : "missing until scoped contract";
  const idempotencyValue = item.idempotency_key_ref
    ? item.idempotency_key_ref
    : "missing until scoped contract";
  const expiryValue = item.expires_at ?? "review required before mutation";
  const rollbackValue = item.rollback_ref ?? "missing until scoped contract";
  const safeDisableValue = item.safe_disable_ref ?? "missing until scoped contract";
  const envelopeStatus =
    item.approval_envelope_status ?? "missing_until_scoped_contract";
  const stateChangeReadiness =
    item.state_change_readiness ?? "blocked_missing_backend_contract";
  const staleState = item.stale_state ?? "recheck_required_before_mutation";
  const nextSafeAction =
    item.next_safe_action ??
    "Review the safe summary and keep mutation blocked until a scoped backend contract exists.";

  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>{item.title}</h3>
        <span>{item.priority} / {riskClass}</span>
      </div>
      <p>{item.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Item ref" value={item.item_ref} />
        <DetailTerm label="Status" value={item.status} />
        <DetailTerm label="Risk" value={riskClass} />
        <DetailTerm label="Side effect" value={item.side_effect_class} />
        <DetailTerm label="Authority boundary" value={authorityBoundary} />
        <DetailTerm
          label="Approval before mutation"
          value={item.approval_required ? "required" : "not required"}
        />
        <DetailTerm label="Approval envelope" value={approvalEnvelopeValue} />
        <DetailTerm label="Envelope status" value={envelopeStatus} />
        <DetailTerm label="State-change contract" value={stateChangeContractValue} />
        <DetailTerm label="State-change readiness" value={stateChangeReadiness} />
        <DetailTerm label="Idempotency" value={idempotencyValue} />
        <DetailTerm label="Expiry posture" value={expiryValue} />
        <DetailTerm label="Stale-state posture" value={staleState} />
        <DetailTerm label="Rollback" value={rollbackValue} />
        <DetailTerm label="Safe disable" value={safeDisableValue} />
        <DetailTerm label="Next safe action" value={nextSafeAction} />
      </dl>
      {item.blocked_state ? <p className="muted">{item.blocked_state}</p> : null}
      <RefListWithFallback
        emptyLabel="Receipt refs: missing until scoped contract"
        refs={item.receipt_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Audit refs: missing until scoped contract"
        refs={item.audit_refs ?? []}
      />
      <RefList refs={item.evidence_refs ?? []} />
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
  const priority = item.priority ?? "medium";
  const sourceReadiness =
    item.source_readiness ?? "blocked_missing_source_contract";
  const sideEffect = item.side_effect_class ?? "local_dev_workspace_only";
  const authorityBoundary =
    item.authority_boundary ??
    "Review-only briefing summary; source reads and delivery remain unscoped.";
  const staleState =
    item.stale_state ?? "recheck_required_before_source_contract";
  const evidenceGap =
    item.evidence_gap ??
    "No source connector evidence is bound in this briefing slice.";
  const nextSafeAction =
    item.next_safe_action ??
    "Define read-only source contracts before source reads or refresh.";

  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>{item.title}</h3>
        <span>{priority} / {item.status}</span>
      </div>
      <p>{item.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Briefing ref" value={item.briefing_ref} />
        <DetailTerm label="Priority" value={priority} />
        <DetailTerm label="Status" value={item.status} />
        <DetailTerm label="Side effect" value={sideEffect} />
        <DetailTerm label="Source readiness" value={sourceReadiness} />
        <DetailTerm label="Authority boundary" value={authorityBoundary} />
        <DetailTerm label="Stale-state posture" value={staleState} />
        <DetailTerm label="Evidence gap" value={evidenceGap} />
        <DetailTerm label="Next safe action" value={nextSafeAction} />
      </dl>
      <RefListWithFallback
        emptyLabel="Source refs: missing until read-only source contract"
        refs={item.source_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Missing contracts: email, calendar, notification"
        refs={item.missing_contract_refs ?? []}
      />
      <InlineListWithFallback
        emptyLabel="Item blockers: source contracts not scoped"
        items={item.blocked_states ?? []}
      />
      <RefList refs={item.evidence_refs ?? []} />
    </article>
  );
}

function MemoryReviewCard({ item }: { item: FounderLoopMemoryReviewItem }) {
  const candidateKind = item.candidate_kind ?? "memory_candidate";
  const priority = item.priority ?? "medium";
  const reviewState = item.review_state ?? item.status;
  const sideEffect = item.side_effect_class ?? "local_dev_workspace_only";
  const authorityBoundary =
    item.authority_boundary ??
    "Review-only memory candidate; memory writes and context injection remain unscoped.";
  const correctionPosture =
    item.correction_posture ??
    "correction_requires_scoped_memory_write_contract";
  const rejectionPosture =
    item.rejection_posture ?? "rejection_is_review_state_only";
  const retentionPosture =
    item.retention_posture ?? "retention_policy_not_bound";
  const deletePosture = item.delete_posture ?? "delete_execution_not_scoped";
  const confidencePosture =
    item.confidence_posture ?? "safe_summary_unverified";
  const staleState =
    item.stale_state ?? "recheck_source_refs_before_memory_use";
  const sourceKind = item.source_kind ?? "manual_note";
  const sourceTrustPosture =
    item.source_trust_posture ?? "untrusted_until_reviewed";
  const nextSafeAction =
    item.next_safe_action ??
    "Review provenance and evidence refs; keep writes blocked until a scoped memory policy milestone.";

  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>{item.title}</h3>
        <span>{priority} / {reviewState}</span>
      </div>
      <p>{item.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Review ref" value={item.review_ref} />
        <DetailTerm label="Candidate kind" value={candidateKind} />
        <DetailTerm label="Source kind" value={sourceKind} />
        <DetailTerm label="Source trust" value={sourceTrustPosture} />
        <DetailTerm label="Source ref status" value={item.source_refs_status} />
        <DetailTerm
          label="Provenance ref status"
          value={item.provenance_refs_status}
        />
        <DetailTerm label="Accepted as truth" value={item.accepted_as_truth ? "yes" : "no"} />
        <DetailTerm
          label="Memory write authority"
          value={item.memory_write_authorized ? "yes" : "no"}
        />
        <DetailTerm
          label="Context injection authority"
          value={item.context_injection_authorized ? "yes" : "no"}
        />
        <DetailTerm label="Status" value={item.status} />
        <DetailTerm label="Review state" value={reviewState} />
        <DetailTerm label="Side effect" value={sideEffect} />
        <DetailTerm label="Authority boundary" value={authorityBoundary} />
        <DetailTerm label="Correction posture" value={correctionPosture} />
        <DetailTerm label="Rejection posture" value={rejectionPosture} />
        <DetailTerm label="Retention posture" value={retentionPosture} />
        <DetailTerm label="Delete posture" value={deletePosture} />
        <DetailTerm label="Confidence posture" value={confidencePosture} />
        <DetailTerm label="Stale-state posture" value={staleState} />
        <DetailTerm label="Next safe action" value={nextSafeAction} />
      </dl>
      <RefListWithFallback
        emptyLabel="Provenance refs: missing until memory review contract"
        refs={item.provenance_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Source refs: missing until reviewed source binding"
        refs={item.source_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Missing contracts: memory write, retention/delete, context injection"
        refs={item.missing_contract_refs ?? []}
      />
      <InlineListWithFallback
        emptyLabel="Item blockers: memory write and context injection not scoped"
        items={item.blocked_states ?? []}
      />
      <RefList refs={item.evidence_refs ?? []} />
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

function RefListWithFallback({
  emptyLabel,
  refs,
}: {
  emptyLabel: string;
  refs: string[];
}) {
  if (refs.length === 0) {
    return <p className="muted">{emptyLabel}</p>;
  }
  return <RefList refs={refs} />;
}

function InlineListWithFallback({
  emptyLabel,
  items,
}: {
  emptyLabel: string;
  items: string[];
}) {
  if (items.length === 0) {
    return <p className="muted">{emptyLabel}</p>;
  }
  return (
    <ul className="ref-list">
      {items.map((item) => (
        <li key={item}>{item}</li>
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
