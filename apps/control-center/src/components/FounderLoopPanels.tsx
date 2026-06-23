import { useState, type ReactNode } from "react";
import {
  commitLocalTask,
  recordMemoryReviewDecision,
  submitActionDecision,
  submitTodayActionEnvelope,
} from "../api/client";
import type {
  FounderLoopActionDecisionKind,
  FounderLoopActionDecisionReceipt,
  FounderLoopActionEnvelopePromotionReceipt,
  FounderLoopActionGroupId,
  FounderLoopActionGroupSummary,
  FounderLoopActionsInbox,
  FounderLoopActionItem,
  FounderLoopBriefingItem,
  FounderLoopEvidenceTimelineEvent,
  FounderLoopEvidenceTimelineIndex,
  FounderLoopEvidenceTimelineItem,
  FounderLoopLocalTaskCommitReceipt,
  FounderLoopMemoryContextPackProposal,
  FounderLoopMemoryContextPacks,
  FounderLoopMemoryReviewItem,
  FounderLoopMorningBriefing,
  FounderLoopPlanSummary,
  FounderLoopStorageStatus,
  FounderLoopTodaySummary,
  ControlCenterSettingsStatus,
  MemoryReviewDecisionKind,
  MemoryReviewDecisionReceipt,
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

const actionGroupFallbacks: FounderLoopActionGroupSummary[] = [
  {
    group_id: "ready_for_decision",
    label: "Ready for decision",
    safe_summary:
      "Items with backend-known exact scope that can record approve, edit, reject, or defer receipts without executing work.",
    available_action: "Record a backend-owned decision receipt.",
    count: 0,
  },
  {
    group_id: "approved_local_task_lane",
    label: "Approved local task lane",
    safe_summary:
      "Exact-approved local_task_create items that can be committed only through the typed local task route.",
    available_action: "Inspect approval posture or commit the local task lane.",
    count: 0,
  },
  {
    group_id: "blocked_by_authority",
    label: "Blocked by authority",
    safe_summary:
      "Items blocked by missing authority, missing exact scope, policy posture, or disallowed external capability.",
    available_action: "Inspect blockers; no decision or commit control is exposed.",
    count: 0,
  },
  {
    group_id: "expired_stale",
    label: "Expired/stale",
    safe_summary:
      "Items whose approval window, evidence, or state is no longer fresh enough for a decision.",
    available_action: "Recheck source and evidence refs before any decision.",
    count: 0,
  },
  {
    group_id: "receipt_recorded",
    label: "Receipt recorded",
    safe_summary:
      "Items with backend decision, commit, or evidence receipts already recorded.",
    available_action: "Inspect receipt and evidence refs.",
    count: 0,
  },
  {
    group_id: "proposal_only_no_execution_path",
    label: "Proposal-only / no execution path",
    safe_summary:
      "Planning, documentation, or review-only items without a validated core/API/CLI execution path.",
    available_action: "Review proposal refs only.",
    count: 0,
  },
];

const pythonCoreActionReadModelSource = "python_core_action_inbox_read_model";
const unavailableReceiptStates = [
  "pending",
  "missing",
  "not_applicable",
  "unavailable",
  "unknown",
  "planned",
  "backend_read_model_unavailable",
  "mock_only_backend_read_model_unavailable",
];

type FounderLoopPrimarySurface =
  | "Today"
  | "Inbox"
  | "Plans"
  | "Actions"
  | "Memory"
  | "Evidence"
  | "Settings";

type FounderLoopSpineItem = {
  surface: FounderLoopPrimarySurface;
  path: string;
  status: string;
  posture: "implemented" | "partial" | "blocked" | "receipt-backed" | "authority-gated";
  summary: string;
  nextSafeAction: string;
  refs: string[];
};

export function FounderLoopSpinePanel({
  activeSurface,
  evidence,
  inbox,
  settingsStatus,
  today,
}: {
  activeSurface: FounderLoopPrimarySurface;
  evidence?: FounderLoopEvidenceTimelineIndex;
  inbox?: FounderLoopActionsInbox;
  settingsStatus?: ControlCenterSettingsStatus;
  today: FounderLoopTodaySummary;
}) {
  const items = buildFounderLoopSpineItems({
    evidence,
    inbox,
    settingsStatus,
    today,
  });
  const localTaskSummary = summarizeLocalTaskLane(inbox?.items ?? today.actions);

  return (
    <section
      aria-labelledby="founder-loop-spine-heading"
      className="loop-spine"
    >
      <div className="loop-spine-header">
        <div>
          <p className="eyebrow">Founder Command Center</p>
          <h2 id="founder-loop-spine-heading">Founder daily loop</h2>
        </div>
        <span className="status-pill compact">
          {today.daily_loop_summary?.status ?? today.status}
        </span>
      </div>
      <p className="section-copy">
        Morning Briefing and Today are the local home, then Inbox, Plans,
        Actions, Memory, Evidence, and Settings stay visible as one backend-bound
        loop. No generic execution is available; the only mutating FCC authority
        shown here is the exact local task lane after backend approval.
      </p>
      <div aria-label="Founder daily loop modules" className="loop-spine-grid">
        {items.map((item) => (
          <a
            aria-current={activeSurface === item.surface ? "page" : undefined}
            className={`loop-spine-card ${item.posture}`}
            href={item.path}
            key={item.surface}
          >
            <span className="loop-spine-card-topline">
              <strong>{item.surface}</strong>
              <small>{item.posture}</small>
            </span>
            <span className="loop-spine-status">{item.status}</span>
            <span className="loop-spine-summary">{item.summary}</span>
            <span className="loop-spine-next">{item.nextSafeAction}</span>
            <span className="loop-spine-ref">{item.refs[0] ?? "safe refs pending"}</span>
          </a>
        ))}
      </div>
      <div
        aria-label="Founder Loop authority boundaries"
        className="loop-authority-strip"
      >
        <span>No generic execution</span>
        <span>Local task authority gated by backend approval</span>
        <span>{localTaskSummary}</span>
        <span>Connector writes blocked</span>
        <span>Shell/subprocess blocked</span>
        <span>Provider/model authority blocked</span>
        <span>Memory writes and context injection blocked</span>
        <span>Production authority blocked</span>
      </div>
    </section>
  );
}

function buildFounderLoopSpineItems({
  evidence,
  inbox,
  settingsStatus,
  today,
}: {
  evidence?: FounderLoopEvidenceTimelineIndex;
  inbox?: FounderLoopActionsInbox;
  settingsStatus?: ControlCenterSettingsStatus;
  today: FounderLoopTodaySummary;
}): FounderLoopSpineItem[] {
  const sourceReadiness = today.source_readiness_items ?? [];
  const reviewGroups = today.review_queue_groups ?? [];
  const inboxSource = sourceReadiness.find((item) => item.source_kind === "inbox");
  const sections = today.sections ?? {
    action_inbox_count: 0,
    briefing_count: 0,
    memory_review_count: 0,
    plan_count: 0,
  };
  const actionItems = inbox?.items ?? today.actions ?? [];
  const localTaskEligible = actionItems.filter(
    (item) =>
      item.action_kind === "local_task_create" &&
      item.local_task_commit_eligible,
  ).length;
  const localTaskReceipts = actionItems.filter(
    (item) => item.local_task_commit_receipt_ref,
  ).length;
  const memoryReviewGroup = reviewGroups.find((group) => group.kind === "memory");
  const evidenceEvents =
    evidence?.event_count ??
    sections.evidence_timeline_count ??
    (today.evidence_timeline ?? []).length;

  return [
    {
      surface: "Today",
      path: "/today",
      status: today.daily_loop_summary?.home_surface ?? today.status,
      posture: "partial",
      summary:
        today.daily_loop_summary?.today_plan_summary ??
        `${sections.plan_count} plans and ${sections.action_inbox_count} actions in local review.`,
      nextSafeAction:
        today.daily_loop_summary?.next_safe_action ??
        "Review Today before opening deeper surfaces.",
      refs: [
        today.daily_loop_summary?.loop_ref,
        today.product_spine_contract_ref,
        today.storage_ref,
      ].filter(isPresent),
    },
    {
      surface: "Inbox",
      path: "/inbox",
      status: inboxSource?.status ?? "blocked/planned",
      posture: "blocked",
      summary:
        inboxSource?.safe_summary ??
        "Email and calendar metadata contracts are not enabled in this slice.",
      nextSafeAction:
        inboxSource?.next_safe_action ??
        "Define read-only source metadata before connector runtime.",
      refs: [
        inboxSource?.source_ref,
        ...(inboxSource?.blocked_state_refs ?? []),
      ].filter(isPresent),
    },
    {
      surface: "Plans",
      path: "/plans",
      status: today.plans_action_envelope_status ?? "partial_backend_not_product_ready",
      posture: "partial",
      summary: `${sections.plan_count} plan refs are visible with approval and evidence posture.`,
      nextSafeAction:
        today.plan_action_state?.review_actions?.[0] ??
        "Keep browser plan execution blocked until a scoped backend lane exists.",
      refs: [
        today.plans_action_envelope_contract_ref,
        ...(today.plans_action_envelope_required_blocked_refs ?? []),
      ].filter(isPresent),
    },
    {
      surface: "Actions",
      path: "/actions",
      status:
        localTaskReceipts > 0
          ? "local_task_receipt_recorded"
          : localTaskEligible > 0
            ? "local_task_authority_gated"
            : inbox?.status ?? "reviewable_actions",
      posture:
        localTaskEligible > 0 || localTaskReceipts > 0
          ? "authority-gated"
          : "receipt-backed",
      summary: `${actionItems.length} action refs; ${localTaskEligible} eligible local task lane; ${localTaskReceipts} local task receipts.`,
      nextSafeAction:
        actionItems.find((item) => item.local_task_commit_next_safe_action)
          ?.local_task_commit_next_safe_action ??
        "Record only supported receipts or commit the approved local task lane.",
      refs: [
        inbox?.route_ref,
        inbox?.decision_state_contract_ref,
        actionItems.find((item) => item.local_task_commit_contract_ref)
          ?.local_task_commit_contract_ref,
      ].filter(isPresent),
    },
    {
      surface: "Memory",
      path: "/memory",
      status: today.memory_review_status ?? "review_queue_status_unknown",
      posture: "receipt-backed",
      summary: `${sections.memory_review_count} reviewed memory refs are visible as recall, not truth authority.`,
      nextSafeAction:
        memoryReviewGroup?.next_safe_action ??
        "Record safe memory review decisions without memory write authority.",
      refs: [
        today.memory_review_decision_contract_ref,
        today.memory_to_loop_binding_contract_ref,
        ...(today.memory_review_decision_receipt_refs ?? []),
      ].filter(isPresent),
    },
    {
      surface: "Evidence",
      path: "/evidence",
      status:
        evidence?.status ??
        today.evidence_timeline_status ??
        "storage_backed_redacted_history_grammar_refs",
      posture: "implemented",
      summary: `${evidenceEvents} safe-ref evidence events expose what was proposed, approved, changed, and blocked.`,
      nextSafeAction:
        today.weekly_review_narrative?.next_safe_action ??
        "Inspect receipts and evidence refs before claiming completion.",
      refs: [
        evidence?.route_ref,
        evidence?.contract_ref,
        today.evidence_history_contract_ref,
      ].filter(isPresent),
    },
    {
      surface: "Settings",
      path: "/settings",
      status: settingsStatus?.status ?? "read_only_status_unavailable",
      posture: "blocked",
      summary:
        settingsStatus?.safe_summary ??
        "Settings expose backend-owned read-only posture without browser mutation controls.",
      nextSafeAction:
        "Inspect backend-owned settings status before scoping any settings mutation.",
      refs: [
        settingsStatus?.route_ref,
        settingsStatus?.maturity_manifest_ref,
        "docs/control_center/SETTINGS_KILL_SWITCH_FEATURE_FLAGS_SPEC.md",
        "docs/control_center/PRODUCT_LANGUAGE_RULES.md",
      ].filter(isPresent),
    },
  ];
}

function summarizeLocalTaskLane(items: FounderLoopActionItem[]): string {
  const eligible = items.filter(
    (item) =>
      item.action_kind === "local_task_create" &&
      item.local_task_commit_eligible,
  ).length;
  const receipts = items.filter((item) => item.local_task_commit_receipt_ref).length;
  if (receipts > 0) {
    return `${receipts} local task receipt refs`;
  }
  if (eligible > 0) {
    return `${eligible} approved local task lane`;
  }
  return "Local task lane blocked unless exact approval exists";
}

function isPresent(value: string | null | undefined): value is string {
  return Boolean(value);
}

export function TodaySurfacePanel({
  actionReadModelAuthoritative,
  today,
}: {
  actionReadModelAuthoritative: boolean;
  today: FounderLoopTodaySummary;
}) {
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
      <DailyLoopProductBehaviorPanel today={today} />
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
            <h3>Memory-to-loop binding</h3>
            <span>{today.memory_to_loop_binding_status}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Contract ref"
              value={today.memory_to_loop_binding_contract_ref}
            />
            <DetailTerm
              label="Loop items"
              value={String(today.memory_to_loop_item_count)}
            />
            <DetailTerm
              label="Memory-derived actions"
              value={String(today.memory_derived_action_proposal_count)}
            />
            <DetailTerm
              label="Accepted recall"
              value={
                today.memory_to_loop_authority_posture.automatic_recall_enabled
                  ? "enabled"
                  : "display-only"
              }
            />
            <DetailTerm
              label="Execution"
              value={
                today.memory_to_loop_authority_posture.action_execution_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
          </dl>
          <RefListWithFallback
            emptyLabel="Memory candidates: none"
            refs={today.memory_candidate_refs}
          />
          <RefListWithFallback
            emptyLabel="Accepted recall refs: none"
            refs={today.accepted_recall_refs}
          />
          <RefListWithFallback
            emptyLabel="Follow-up commitments: none"
            refs={today.follow_up_commitment_refs}
          />
          <RefListWithFallback
            emptyLabel="Missing evidence blockers: none"
            refs={today.missing_evidence_blocker_refs}
          />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Private beta-readiness gate</h3>
            <span>{today.private_beta_readiness_overall_state}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Contract ref"
              value={today.private_beta_readiness_contract_ref}
            />
            <DetailTerm
              label="Evidence packet"
              value={today.private_beta_readiness_evidence_packet_ref}
            />
            <DetailTerm
              label="Criteria"
              value={String(today.private_beta_readiness_criterion_count)}
            />
            <DetailTerm
              label="Local/private only"
              value={today.private_beta_readiness_local_private_only ? "yes" : "no"}
            />
            <DetailTerm
              label="Execution"
              value={
                today.private_beta_readiness_execution_authorized
                  ? "authorized"
                  : "blocked"
              }
            />
            <DetailTerm
              label="Public beta"
              value={
                today.private_beta_readiness_authority_posture
                  .public_beta_claim_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
          </dl>
          <InlineListWithFallback
            emptyLabel="Acceptance states: missing"
            items={today.private_beta_readiness_acceptance_states}
          />
          <div className="status-card-header">
            <h3>Beta-test criteria</h3>
            <span>{today.private_beta_readiness_criteria.length}</span>
          </div>
          <ul className="ref-list">
            {today.private_beta_readiness_criteria.map((criterion) => (
              <li key={criterion.criterion_ref}>
                {criterion.surface}: {criterion.gate_state};{" "}
                {criterion.next_safe_action}
              </li>
            ))}
          </ul>
          <RefListWithFallback
            emptyLabel="Missing evidence: none"
            refs={today.private_beta_readiness_missing_evidence_refs}
          />
          <RefList refs={today.private_beta_readiness_required_blocked_refs} />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>User intent understanding</h3>
            <span>{today.user_intent_understanding_status}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Contract ref"
              value={today.user_intent_understanding_contract_ref}
            />
            <DetailTerm
              label="Proposals"
              value={String(today.user_intent_proposal_count)}
            />
            <DetailTerm
              label="Low confidence"
              value={
                today.user_intent_low_confidence_asks_user
                  ? "asks user"
                  : "unsafe"
              }
            />
            <DetailTerm
              label="Conflicts"
              value={
                today.user_intent_conflicting_intent_asks_user
                  ? "asks user"
                  : "unsafe"
              }
            />
            <DetailTerm
              label="Hidden authority"
              value={
                today.user_intent_hidden_authority_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
            <DetailTerm
              label="Action execution"
              value={
                today.user_intent_action_execution_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
          </dl>
          <InlineListWithFallback
            emptyLabel="Routing decisions: missing"
            items={today.user_intent_routing_decisions}
          />
          <RefListWithFallback
            emptyLabel="Intent dependencies: missing"
            refs={today.user_intent_required_dependency_refs}
          />
          <ul className="ref-list">
            {today.user_intent_proposals.map((proposal) => (
              <li key={proposal.proposal_ref}>
                {proposal.intent_label}: {proposal.confidence_band} confidence;{" "}
                {proposal.ambiguity_posture}; route {proposal.routing_decision}
              </li>
            ))}
          </ul>
          <RefList refs={today.user_intent_required_blocked_refs} />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Weekly CEO Review</h3>
            <span>{today.weekly_ceo_review_summary.weekly_review_ref}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Next safe action"
              value={today.weekly_ceo_review_summary.next_safe_action}
            />
            <DetailTerm
              label="Authority"
              value={today.weekly_ceo_review_summary.authority_boundary}
            />
          </dl>
          <RefListWithFallback
            emptyLabel="Carry-forward tasks: none"
            refs={today.weekly_ceo_review_summary.carry_forward_task_refs}
          />
          <RefListWithFallback
            emptyLabel="Unresolved blockers: none"
            refs={today.weekly_ceo_review_summary.unresolved_blocker_refs}
          />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Action envelope contract</h3>
            <span>{today.plans_action_envelope_status}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Contract ref"
              value={today.plans_action_envelope_contract_ref}
            />
            <DetailTerm
              label="Exact scope"
              value={
                today.plans_action_envelope_authority_posture.exact_scope_required
                  ? "required"
                  : "missing"
              }
            />
            <DetailTerm
              label="Grant capture"
              value={
                today.plans_action_envelope_authority_posture
                  .approval_grant_capture_enabled
                  ? "enabled"
                  : "disabled"
              }
            />
            <DetailTerm
              label="Execution"
              value={
                today.plans_action_envelope_authority_posture
                  .action_execution_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
          </dl>
          <InlineListWithFallback
            emptyLabel="Review actions: missing"
            items={today.plans_action_envelope_review_postures.map(
              (posture) => posture.review_action,
            )}
          />
          <RefList refs={today.plans_action_envelope_required_blocked_refs} />
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
            <h3>Memory loop states</h3>
            <span>{today.memory_to_loop_items.length}</span>
          </div>
          <ul className="ref-list">
            {today.memory_to_loop_items.map((item) => (
              <li key={item.loop_item_ref}>
                {item.surface}: {item.loop_binding_state}; {item.next_safe_action}
              </li>
            ))}
          </ul>
        </article>
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
            <ActionItemCard
              actionReadModelAuthoritative={actionReadModelAuthoritative}
              item={item}
              key={item.item_ref}
            />
          ))}
        </LoopPanel>
        <LoopPanel title="Plans" route="/plans">
          {today.plans.map((plan) => (
            <PlanCard plan={plan} key={plan.plan_ref} />
          ))}
        </LoopPanel>
        <LoopPanel title="Morning Briefing" route="/briefing">
          {today.briefing_items.map((item) => (
            <BriefingCard
              allowActionEnvelopePromotion
              item={item}
              key={item.briefing_ref}
            />
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

function DailyLoopProductBehaviorPanel({
  today,
}: {
  today: FounderLoopTodaySummary;
}) {
  const hasDailyLoop =
    today.daily_loop_summary ||
    today.source_readiness_items?.length ||
    today.crm_lite_followups?.length ||
    today.memory_why_shown_items?.length ||
    today.review_queue_groups?.length ||
    today.weekly_review_narrative ||
    today.dogfood_capture;

  if (!hasDailyLoop) {
    return null;
  }

  return (
    <>
      <div className="panel-grid">
        <DailyLoopSummaryCard summary={today.daily_loop_summary} />
        <SourceReadinessCards items={today.source_readiness_items ?? []} />
        <ReviewQueueGroupCards groups={today.review_queue_groups ?? []} />
        <CrmLiteFollowUpCards items={today.crm_lite_followups ?? []} />
        <MemoryWhyShownCards items={today.memory_why_shown_items ?? []} />
        <DogfoodCaptureCard capture={today.dogfood_capture} />
      </div>
      <WeeklyReviewNarrativeCard narrative={today.weekly_review_narrative} />
    </>
  );
}

function DailyLoopSummaryCard({
  summary,
}: {
  summary?: FounderLoopTodaySummary["daily_loop_summary"];
}) {
  if (!summary) {
    return null;
  }
  return (
    <article className="status-card">
      <div className="status-card-header">
        <h3>Daily command loop</h3>
        <span>{summary.status}</span>
      </div>
      <p>{summary.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Home" value={summary.home_surface} />
        <DetailTerm label="Decision view" value={summary.decision_surface} />
        <DetailTerm label="Today plan" value={summary.today_plan_summary} />
        <DetailTerm label="Review queue" value={summary.review_queue_summary} />
        <DetailTerm
          label="Action execution"
          value={summary.action_execution_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Connector runtime"
          value={summary.connector_runtime_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="External writes"
          value={summary.external_write_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Runtime model calls"
          value={summary.runtime_model_calls_enabled ? "enabled" : "blocked"}
        />
      </dl>
      <p>{summary.next_safe_action}</p>
      <RefListWithFallback
        emptyLabel="Source readiness refs: none"
        refs={summary.source_readiness_state_refs}
      />
      <RefListWithFallback
        emptyLabel="CRM follow-up refs: none"
        refs={summary.crm_follow_up_refs}
      />
      <RefListWithFallback
        emptyLabel="Memory reason refs: none"
        refs={summary.memory_reason_refs}
      />
    </article>
  );
}

function SourceReadinessCards({
  items,
}: {
  items: NonNullable<FounderLoopTodaySummary["source_readiness_items"]>;
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

function CrmLiteFollowUpCards({
  items,
}: {
  items: NonNullable<FounderLoopTodaySummary["crm_lite_followups"]>;
}) {
  if (items.length === 0) {
    return null;
  }
  return (
    <article className="status-card">
      <div className="status-card-header">
        <h3>CRM-lite follow-ups</h3>
        <span>{items.length}</span>
      </div>
      <ul className="ref-list">
        {items.map((item) => (
          <li key={item.follow_up_ref}>
            {item.follow_up_ref}: {item.status}; {item.why_now}
          </li>
        ))}
      </ul>
      <dl className="detail-list">
        <DetailTerm
          label="CRM sync"
          value={items.some((item) => item.crm_sync_enabled) ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="CRM writes"
          value={items.some((item) => item.crm_write_enabled) ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="External writes"
          value={
            items.some((item) => item.external_write_enabled) ? "enabled" : "blocked"
          }
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Memory refs: none"
        refs={items.flatMap((item) => item.memory_refs)}
      />
      <RefListWithFallback
        emptyLabel="CRM-lite blockers: none"
        refs={items.flatMap((item) => item.blocked_state_refs)}
      />
    </article>
  );
}

function MemoryWhyShownCards({
  items,
}: {
  items: NonNullable<FounderLoopTodaySummary["memory_why_shown_items"]>;
}) {
  if (items.length === 0) {
    return null;
  }
  return (
    <article className="status-card">
      <div className="status-card-header">
        <h3>Memory why shown</h3>
        <span>{items.length}</span>
      </div>
      <ul className="ref-list">
        {items.map((item) => (
          <li key={item.loop_item_ref}>
            {item.surface}: {item.review_state}; {item.why_shown}
          </li>
        ))}
      </ul>
      <dl className="detail-list">
        <DetailTerm
          label="Reviewed recall only"
          value={items.every((item) => item.reviewed_recall_only) ? "yes" : "missing"}
        />
        <DetailTerm
          label="Context injection"
          value={
            items.some((item) => item.context_injection_authorized)
              ? "enabled"
              : "blocked"
          }
        />
        <DetailTerm
          label="Memory truth"
          value={items.some((item) => item.memory_truth_authority) ? "enabled" : "blocked"}
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Missing evidence refs: none"
        refs={items.flatMap((item) => item.missing_evidence_refs)}
      />
    </article>
  );
}

function ReviewQueueGroupCards({
  groups,
}: {
  groups: NonNullable<FounderLoopTodaySummary["review_queue_groups"]>;
}) {
  if (groups.length === 0) {
    return null;
  }
  return (
    <article className="status-card">
      <div className="status-card-header">
        <h3>Review queue groups</h3>
        <span>{groups.length}</span>
      </div>
      <ul className="ref-list">
        {groups.map((group) => (
          <li key={group.group_ref}>
            {group.kind}: {group.count}; {group.status}; {group.safe_summary}
          </li>
        ))}
      </ul>
      <RefListWithFallback
        emptyLabel="Group blockers: none"
        refs={groups.flatMap((group) => group.blocked_state_refs)}
      />
    </article>
  );
}

function DogfoodCaptureCard({
  capture,
}: {
  capture?: FounderLoopTodaySummary["dogfood_capture"];
}) {
  if (!capture) {
    return null;
  }
  return (
    <article className="status-card">
      <div className="status-card-header">
        <h3>Dogfood capture</h3>
        <span>{capture.status}</span>
      </div>
      <p>{capture.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm
          label="Local/private"
          value={capture.local_private_only ? "yes" : "no"}
        />
        <DetailTerm
          label="Safe refs only"
          value={capture.safe_refs_only ? "yes" : "no"}
        />
        <DetailTerm
          label="Public beta claim"
          value={capture.public_beta_claim_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Production readiness"
          value={
            capture.production_readiness_claim_enabled ? "enabled" : "blocked"
          }
        />
        <DetailTerm
          label="Auto-apply"
          value={capture.auto_apply_enabled ? "enabled" : "blocked"}
        />
      </dl>
      <InlineListWithFallback
        emptyLabel="Capture events: none"
        items={capture.capture_event_kinds}
      />
      <RefListWithFallback
        emptyLabel="Recommendation candidates: none"
        refs={capture.recommendation_candidate_refs}
      />
    </article>
  );
}

function WeeklyReviewNarrativeCard({
  narrative,
}: {
  narrative?: FounderLoopTodaySummary["weekly_review_narrative"];
}) {
  if (!narrative) {
    return null;
  }
  return (
    <article className="status-card">
      <div className="status-card-header">
        <h3>Weekly Review narrative</h3>
        <span>{narrative.status}</span>
      </div>
      <p>{narrative.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Next safe action" value={narrative.next_safe_action} />
        <DetailTerm label="Authority" value={narrative.authority_boundary} />
      </dl>
      <RefListWithFallback
        emptyLabel="Proposed refs: none"
        refs={narrative.proposed_refs}
      />
      <RefListWithFallback
        emptyLabel="Carry-forward refs: none"
        refs={narrative.carry_forward_refs}
      />
      <RefListWithFallback
        emptyLabel="Missing source refs: none"
        refs={narrative.missing_source_refs}
      />
      <RefListWithFallback
        emptyLabel="Dogfood refs: none"
        refs={narrative.dogfood_refs}
      />
    </article>
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
  actionReadModelAuthoritative,
  inbox,
}: {
  actionReadModelAuthoritative: boolean;
  inbox: FounderLoopActionsInbox;
}) {
  const actionGroups = buildActionLaneGroups(inbox);

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
          <DetailTerm
            label="Decision contract"
            value={inbox.decision_state_contract_ref ?? "missing"}
          />
          <DetailTerm
            label="Action execution"
            value={inbox.action_execution_enabled ? "enabled" : "blocked"}
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
      <article className="status-card">
        <div className="status-card-header">
          <h3>Action envelope contract</h3>
          <span>{inbox.action_envelope_contract_ref ?? "missing"}</span>
        </div>
        <dl className="detail-list">
          <DetailTerm
            label="Exact scope"
            value={
              inbox.action_envelope_authority_posture?.exact_scope_required
                ? "required"
                : "missing"
            }
          />
          <DetailTerm
            label="Grant capture"
            value={
              inbox.action_envelope_authority_posture?.approval_grant_capture_enabled
                ? "enabled"
                : "disabled"
            }
          />
          <DetailTerm
            label="Execution"
            value={
              inbox.action_envelope_authority_posture?.action_execution_enabled
                ? "enabled"
                : "blocked"
            }
          />
        </dl>
        <InlineListWithFallback
          emptyLabel="Review postures: missing"
          items={(inbox.action_envelope_review_postures ?? []).map(
            (posture) => posture.review_action,
          )}
        />
        <RefList refs={inbox.action_envelope_required_ref_fields ?? []} />
      </article>
      <article className="status-card">
        <div className="status-card-header">
          <h3>Memory-derived proposals</h3>
          <span>{inbox.memory_to_loop_binding_status ?? "read-only"}</span>
        </div>
        <dl className="detail-list">
          <DetailTerm
            label="Contract ref"
            value={inbox.memory_to_loop_binding_contract_ref ?? "missing"}
          />
          <DetailTerm
            label="Execution"
            value={
              inbox.memory_to_loop_authority_posture?.action_execution_enabled
                ? "enabled"
                : "blocked"
            }
          />
          <DetailTerm
            label="Approval capture"
            value={
              inbox.memory_to_loop_authority_posture?.approval_grant_capture_enabled
                ? "enabled"
                : "blocked"
            }
          />
        </dl>
        <RefListWithFallback
          emptyLabel="Memory-derived proposal refs: none"
          refs={(inbox.memory_derived_action_proposals ?? []).map(
            (proposal) => proposal.proposal_ref,
          )}
        />
      </article>
      <article className="status-card">
        <div className="status-card-header">
          <h3>Beta-readiness action gate</h3>
          <span>{inbox.private_beta_readiness_overall_state ?? "partial"}</span>
        </div>
        <dl className="detail-list">
          <DetailTerm
            label="Contract ref"
            value={inbox.private_beta_readiness_contract_ref ?? "missing"}
          />
          <DetailTerm
            label="Criteria"
            value={String(inbox.private_beta_readiness_criteria?.length ?? 0)}
          />
          <DetailTerm
            label="Action execution"
            value={
              inbox.private_beta_readiness_authority_posture?.action_execution_enabled
                ? "enabled"
                : "blocked"
            }
          />
          <DetailTerm
            label="Public beta"
            value={
              inbox.private_beta_readiness_authority_posture
                ?.public_beta_claim_enabled
                ? "enabled"
                : "blocked"
            }
          />
        </dl>
        <RefListWithFallback
          emptyLabel="Beta-readiness blockers: missing"
          refs={inbox.private_beta_readiness_blocked_state_refs ?? []}
        />
      </article>
      <article className="status-card">
        <div className="status-card-header">
          <h3>Intent action gate</h3>
          <span>{inbox.user_intent_understanding_status ?? "missing"}</span>
        </div>
        <dl className="detail-list">
          <DetailTerm
            label="Contract ref"
            value={inbox.user_intent_understanding_contract_ref ?? "missing"}
          />
          <DetailTerm
            label="Proposals"
            value={String(inbox.user_intent_proposals?.length ?? 0)}
          />
          <DetailTerm
            label="Low confidence"
            value={
              inbox.user_intent_authority_posture?.low_confidence_asks_user
                ? "asks user"
                : "missing"
            }
          />
          <DetailTerm
            label="Action execution"
            value={
              inbox.user_intent_authority_posture?.action_execution_enabled
                ? "enabled"
                : "blocked"
            }
          />
        </dl>
        <RefListWithFallback
          emptyLabel="Intent blockers: missing"
          refs={inbox.user_intent_blocked_state_refs ?? []}
        />
      </article>
      {inbox.source_readiness_items?.length ||
      inbox.crm_lite_followups?.length ||
      inbox.memory_why_shown_items?.length ||
      inbox.review_queue_groups?.length ||
      inbox.dogfood_capture ? (
        <div className="panel-grid">
          <SourceReadinessCards items={inbox.source_readiness_items ?? []} />
          <ReviewQueueGroupCards groups={inbox.review_queue_groups ?? []} />
          <CrmLiteFollowUpCards items={inbox.crm_lite_followups ?? []} />
          <MemoryWhyShownCards items={inbox.memory_why_shown_items ?? []} />
          <DogfoodCaptureCard capture={inbox.dogfood_capture} />
        </div>
      ) : null}
      <div className="review-grid">
        {(inbox.memory_derived_action_proposals ?? []).map((proposal) => (
          <MemoryDerivedActionProposalCard
            key={proposal.proposal_ref}
            proposal={proposal}
          />
        ))}
      </div>
      <div className="action-lane-stack" aria-label="Action Inbox queue lanes">
        {actionGroups.map((group) => (
          <ActionLaneSection
            actionReadModelAuthoritative={actionReadModelAuthoritative}
            group={group}
            key={group.summary.group_id}
          />
        ))}
      </div>
      <BlockedStateList states={inbox.blocked_states ?? []} />
    </section>
  );
}

type ActionLaneGroup = {
  summary: FounderLoopActionGroupSummary;
  items: FounderLoopActionItem[];
};

function buildActionLaneGroups(inbox: FounderLoopActionsInbox): ActionLaneGroup[] {
  const summaryById = new Map<FounderLoopActionGroupId, FounderLoopActionGroupSummary>();
  for (const summary of actionGroupFallbacks) {
    summaryById.set(summary.group_id, { ...summary });
  }
  for (const summary of inbox.action_groups ?? []) {
    summaryById.set(summary.group_id, summary);
  }
  const groupOrder = inbox.action_group_order?.length
    ? inbox.action_group_order
    : actionGroupFallbacks.map((group) => group.group_id);
  return groupOrder.map((groupId) => {
    const fallback =
      summaryById.get(groupId) ??
      actionGroupFallbacks.find((group) => group.group_id === groupId) ??
      actionGroupFallbacks[actionGroupFallbacks.length - 1];
    const items = inbox.items.filter(
      (item) =>
        (item.action_group_id ?? "proposal_only_no_execution_path") === groupId,
    );
    return {
      summary: {
        ...fallback,
        count: items.length,
      },
      items,
    };
  });
}

function ActionLaneSection({
  actionReadModelAuthoritative,
  group,
}: {
  actionReadModelAuthoritative: boolean;
  group: ActionLaneGroup;
}) {
  const headingId = `action-lane-${group.summary.group_id}`;
  return (
    <section
      aria-labelledby={headingId}
      className={`action-lane ${group.summary.group_id}`}
    >
      <div className="action-lane-header">
        <div>
          <p className="eyebrow">Queue lane</p>
          <h3 id={headingId}>{group.summary.label}</h3>
        </div>
        <span className="status-pill compact">{group.summary.count}</span>
      </div>
      <p className="section-copy">{group.summary.safe_summary}</p>
      <p className="muted">{group.summary.available_action}</p>
      {group.items.length ? (
        <div className="review-grid">
          {group.items.map((item) => (
            <ActionItemCard
              actionReadModelAuthoritative={actionReadModelAuthoritative}
              item={item}
              key={item.item_ref}
            />
          ))}
        </div>
      ) : (
        <p className="empty-state">
          No Action Inbox items are currently classified in this lane.
        </p>
      )}
    </section>
  );
}

function MemoryDerivedActionProposalCard({
  proposal,
}: {
  proposal: NonNullable<
    FounderLoopActionsInbox["memory_derived_action_proposals"]
  >[number];
}) {
  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>{proposal.proposal_ref}</h3>
        <span>{proposal.side_effect_class}</span>
      </div>
      <p>{proposal.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Source memory" value={proposal.source_memory_ref} />
        <DetailTerm label="Source loop item" value={proposal.source_loop_item_ref} />
        <DetailTerm label="Approval posture" value={proposal.approval_posture} />
        <DetailTerm label="Risk" value={proposal.risk_class} />
        <DetailTerm
          label="Execution"
          value={proposal.action_execution_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Context injection"
          value={proposal.context_injection_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm label="Next safe action" value={proposal.next_safe_action} />
      </dl>
      <RefListWithFallback
        emptyLabel="Source refs: missing"
        refs={proposal.source_refs}
      />
      <RefListWithFallback
        emptyLabel="Evidence refs: missing"
        refs={proposal.evidence_refs}
      />
      <RefListWithFallback
        emptyLabel="Blocked states: missing"
        refs={proposal.blocked_state_refs}
      />
    </article>
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
      <BriefingDailyLoopPanel briefing={briefing} />
      <div className="review-grid">
        {briefing.items.map((item) => (
          <BriefingCard item={item} key={item.briefing_ref} />
        ))}
      </div>
      <BlockedStateList states={briefing.blocked_states ?? []} />
    </section>
  );
}

function BriefingDailyLoopPanel({
  briefing,
}: {
  briefing: FounderLoopMorningBriefing;
}) {
  const hasDailyLoop =
    briefing.daily_loop_summary ||
    briefing.daily_loop_sections?.length ||
    briefing.source_readiness_items?.length ||
    briefing.crm_lite_followups?.length ||
    briefing.memory_why_shown_items?.length ||
    briefing.review_queue_groups?.length ||
    briefing.weekly_review_narrative ||
    briefing.dogfood_capture;

  if (!hasDailyLoop) {
    return null;
  }

  return (
    <>
      <div className="panel-grid">
        <BriefingSectionCards sections={briefing.daily_loop_sections ?? []} />
        <DailyLoopSummaryCard summary={briefing.daily_loop_summary} />
        <SourceReadinessCards items={briefing.source_readiness_items ?? []} />
        <ReviewQueueGroupCards groups={briefing.review_queue_groups ?? []} />
        <CrmLiteFollowUpCards items={briefing.crm_lite_followups ?? []} />
        <MemoryWhyShownCards items={briefing.memory_why_shown_items ?? []} />
        <DogfoodCaptureCard capture={briefing.dogfood_capture} />
      </div>
      <WeeklyReviewNarrativeCard narrative={briefing.weekly_review_narrative} />
    </>
  );
}

function BriefingSectionCards({
  sections,
}: {
  sections: NonNullable<FounderLoopMorningBriefing["daily_loop_sections"]>;
}) {
  if (sections.length === 0) {
    return null;
  }
  return (
    <article className="status-card">
      <div className="status-card-header">
        <h3>Briefing daily loop</h3>
        <span>{sections.length}</span>
      </div>
      <ul className="ref-list">
        {sections.map((section) => (
          <li key={section.section_ref}>
            {section.title}: {section.status}; {section.safe_summary}
          </li>
        ))}
      </ul>
      <RefListWithFallback
        emptyLabel="Briefing section evidence refs: none"
        refs={sections.flatMap((section) => section.evidence_refs)}
      />
      <RefListWithFallback
        emptyLabel="Briefing section blockers: none"
        refs={sections.flatMap((section) => section.blocked_state_refs)}
      />
    </article>
  );
}

export function MemoryReviewSurfacePanel({
  contextPacks,
  today,
}: {
  contextPacks: FounderLoopMemoryContextPacks;
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
            Memory review can record safe accept, correction, and reject
            receipts. Retain, delete, write, connector sync, action execution,
            and context injection remain blocked.
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
        <article className="status-card">
          <div className="status-card-header">
            <h3>Review decisions</h3>
            <span>{today.memory_review_decision_states.length}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Contract ref"
              value={today.memory_review_decision_contract_ref}
            />
            <DetailTerm
              label="Review-only"
              value={
                today.memory_review_decision_authority_posture.review_only
                  ? "yes"
                  : "no"
              }
            />
            <DetailTerm
              label="Write authority"
              value={
                today.memory_review_decision_authority_posture.memory_write_authorized
                  ? "enabled"
                  : "disabled"
              }
            />
            <DetailTerm
              label="Recall authority"
              value={
                today.memory_review_decision_authority_posture.accepted_as_recall
                  ? "enabled"
                  : "disabled"
              }
            />
          </dl>
          <InlineListWithFallback
            emptyLabel="Decision labels: metadata only"
            items={today.memory_review_decision_states.map(
              (state) => state.decision_state,
            )}
          />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Decision receipts</h3>
            <span>{today.memory_review_decision_receipt_refs?.length ?? 0}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Receipt status"
              value={
                today.memory_review_decision_status ??
                "backend_receipts_not_loaded"
              }
            />
            <DetailTerm
              label="FCC contract"
              value={
                today.fcc_memory_review_decision_contract_ref ??
                "contract-ref:fcc-v1-005-memory-review-decisions:v1"
              }
            />
          </dl>
          <RefListWithFallback
            emptyLabel="Decision receipt refs: none recorded"
            refs={today.memory_review_decision_receipt_refs ?? []}
          />
          <RefListWithFallback
            emptyLabel="Decision routes: missing"
            refs={today.fcc_memory_review_decision_route_refs ?? []}
          />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Business memory</h3>
            <span>{today.business_memory_quality_states.length}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Contract ref"
              value={today.business_memory_quality_contract_ref}
            />
            <DetailTerm
              label="Status"
              value={today.business_memory_status}
            />
            <DetailTerm
              label="Review before recall"
              value={
                today.business_memory_authority_posture
                  .review_required_before_recall
                  ? "required"
                  : "missing"
              }
            />
            <DetailTerm
              label="CRM writes"
              value={
                today.business_memory_authority_posture
                  .external_crm_write_authorized
                  ? "enabled"
                  : "disabled"
              }
            />
            <DetailTerm
              label="Account sync"
              value={
                today.business_memory_authority_posture.account_sync_authorized
                  ? "enabled"
                  : "disabled"
              }
            />
            <DetailTerm
              label="Accepted as recall"
              value={
                today.business_memory_authority_posture.accepted_as_recall
                  ? "yes"
                  : "no"
              }
            />
          </dl>
          <InlineListWithFallback
            emptyLabel="Business memory kinds: missing"
            items={today.business_memory_candidate_kinds.map(
              (kind) => kind.candidate_kind,
            )}
          />
          <InlineListWithFallback
            emptyLabel="Quality states: missing"
            items={today.business_memory_quality_states.map(
              (state) => state.quality_state,
            )}
          />
          <RefList
            refs={today.business_memory_surface_bindings.map(
              (binding) => binding.feed_ref,
            )}
          />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Memory intake</h3>
            <span>{today.cross_surface_memory_intake_status}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Contract ref"
              value={today.cross_surface_memory_intake_contract_ref}
            />
            <DetailTerm
              label="Proposal count"
              value={String(today.cross_surface_memory_intake_proposal_count)}
            />
            <DetailTerm
              label="Review required"
              value={
                today.cross_surface_memory_intake_authority_posture.review_required
                  ? "yes"
                  : "missing"
              }
            />
            <DetailTerm
              label="Memory write"
              value={
                today.cross_surface_memory_intake_authority_posture
                  .memory_write_authorized
                  ? "enabled"
                  : "blocked"
              }
            />
            <DetailTerm
              label="Context injection"
              value={
                today.cross_surface_memory_intake_authority_posture
                  .context_injection_authorized
                  ? "enabled"
                  : "blocked"
              }
            />
          </dl>
          <InlineListWithFallback
            emptyLabel="Intake surfaces: missing"
            items={today.cross_surface_memory_intake_required_surfaces}
          />
          <RefList refs={today.cross_surface_memory_intake_required_blocked_refs} />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Memory-to-loop</h3>
            <span>{today.memory_to_loop_binding_status}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Contract ref"
              value={today.memory_to_loop_binding_contract_ref}
            />
            <DetailTerm
              label="Loop items"
              value={String(today.memory_to_loop_item_count)}
            />
            <DetailTerm
              label="Memory-derived actions"
              value={String(today.memory_derived_action_proposal_count)}
            />
            <DetailTerm
              label="Accepted recall"
              value={
                today.memory_to_loop_authority_posture.automatic_recall_enabled
                  ? "enabled"
                  : "display-only"
              }
            />
            <DetailTerm
              label="Execution"
              value={
                today.memory_to_loop_authority_posture.action_execution_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
          </dl>
          <RefListWithFallback
            emptyLabel="Memory loop refs: none"
            refs={today.memory_to_loop_items.map((item) => item.loop_item_ref)}
          />
          <RefListWithFallback
            emptyLabel="Accepted recall refs: none"
            refs={today.accepted_recall_refs}
          />
          <RefListWithFallback
            emptyLabel="Follow-up commitments: none"
            refs={today.follow_up_commitment_refs}
          />
          <RefListWithFallback
            emptyLabel="Memory-derived proposal refs: none"
            refs={today.memory_derived_action_proposal_refs}
          />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Context-pack proposals</h3>
            <span>{contextPacks.status}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm label="Backend route" value={contextPacks.route_ref} />
            <DetailTerm label="Contract ref" value={contextPacks.contract_ref} />
            <DetailTerm
              label="Proposal count"
              value={String(contextPacks.context_pack_count)}
            />
            <DetailTerm
              label="Proposal-only"
              value={contextPacks.proposal_only ? "yes" : "no"}
            />
            <DetailTerm
              label="Context injection"
              value={
                contextPacks.context_injection_authorized ? "enabled" : "blocked"
              }
            />
            <DetailTerm
              label="Provider/model call"
              value={
                contextPacks.provider_model_call_performed
                  ? "performed"
                  : "blocked"
              }
            />
            <DetailTerm
              label="Connector write"
              value={
                contextPacks.connector_write_authorized ? "enabled" : "blocked"
              }
            />
          </dl>
          <p>
            Context packs are inspectable proposal refs only. They cannot write
            prompt context, call a model or provider, sync connectors, or inject
            memory into a runtime.
          </p>
          <RefListWithFallback
            emptyLabel="Context-pack blockers: none"
            refs={contextPacks.blocked_state_refs}
          />
        </article>
      </div>
      <div className="review-grid">
        {contextPacks.proposals.map((proposal) => (
          <MemoryContextPackProposalCard
            key={proposal.context_pack_ref}
            proposal={proposal}
          />
        ))}
      </div>
      <div className="review-grid">
        {today.cross_surface_memory_intake_proposals.map((proposal) => (
          <MemoryIntakeProposalCard
            key={proposal.proposal_ref}
            proposal={proposal}
          />
        ))}
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

function MemoryContextPackProposalCard({
  proposal,
}: {
  proposal: FounderLoopMemoryContextPackProposal;
}) {
  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>{proposal.context_pack_ref}</h3>
        <span>{proposal.status ?? "proposal_only"}</span>
      </div>
      <p>{proposal.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Proposal ref" value={proposal.proposal_ref} />
        <DetailTerm label="Query ref" value={proposal.query_ref ?? "none"} />
        <DetailTerm
          label="Approval posture"
          value={proposal.approval_posture ?? "approval_required_before_use"}
        />
        <DetailTerm label="Risk" value={proposal.risk_class ?? "medium"} />
        <DetailTerm
          label="Action proposal status"
          value={
            proposal.phase6_1_internal_action_proposal_status ?? "not_recorded"
          }
        />
        <DetailTerm
          label="Next safe action"
          value={
            proposal.next_safe_action ??
            "Inspect safe refs only; keep context injection blocked."
          }
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Source memory refs: none"
        refs={proposal.source_memory_record_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="L1/L2/L3 supporting refs: none"
        refs={[
          ...(proposal.l1_preview_refs ?? []),
          ...(proposal.l2_projection_refs ?? []),
          ...(proposal.l3_representation_refs ?? []),
        ]}
      />
      <RefListWithFallback
        emptyLabel="Evidence refs: none"
        refs={proposal.evidence_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Blocked states: context injection remains unscoped"
        refs={proposal.blocked_state_refs ?? []}
      />
    </article>
  );
}

function MemoryIntakeProposalCard({
  proposal,
}: {
  proposal: FounderLoopTodaySummary["cross_surface_memory_intake_proposals"][number];
}) {
  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>{proposal.surface}</h3>
        <span>{proposal.candidate_kind}</span>
      </div>
      <p>{proposal.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Proposal ref" value={proposal.proposal_ref} />
        <DetailTerm label="Candidate ref" value={proposal.candidate_ref} />
        <DetailTerm label="Source kind" value={proposal.source_kind} />
        <DetailTerm label="Trust posture" value={proposal.source_trust_posture} />
        <DetailTerm label="Confidence" value={proposal.confidence_posture} />
        <DetailTerm label="Missing evidence" value={proposal.missing_evidence_posture} />
        <DetailTerm label="Stale-state" value={proposal.stale_state} />
        <DetailTerm label="Next safe action" value={proposal.next_safe_action} />
        <DetailTerm
          label="Memory write"
          value={proposal.memory_write_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Context injection"
          value={proposal.context_injection_authorized ? "enabled" : "blocked"}
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Source refs: missing"
        refs={proposal.source_refs}
      />
      <RefListWithFallback
        emptyLabel="Evidence refs: missing"
        refs={proposal.evidence_refs}
      />
      <RefListWithFallback
        emptyLabel="Missing evidence refs: none"
        refs={proposal.missing_evidence_refs}
      />
    </article>
  );
}

export function EvidenceTimelineSurfacePanel({
  evidence,
  today,
}: {
  evidence?: FounderLoopEvidenceTimelineIndex;
  today: FounderLoopTodaySummary;
}) {
  const timeline = today.evidence_timeline;
  const events = evidence?.events ?? [];
  const groups = evidence?.groups ?? [];

  return (
    <section className="page-section" aria-labelledby="evidence-timeline-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Founder Loop</p>
          <h2 id="evidence-timeline-heading">Evidence Timeline</h2>
        </div>
        <span className="status-pill compact">
          {evidence?.status ??
            today.evidence_timeline_status ??
            "storage_backed_redacted_history_grammar_refs"}
        </span>
      </div>
      <div className="metric-grid">
        <Metric
          label="Evidence events"
          value={evidence?.event_count ?? timeline.length}
        />
        <Metric label="Groups" value={evidence?.group_count ?? 0} />
        <Metric
          label="Receipt/audit refs"
          value={
            evidence
              ? evidence.receipt_refs.length + countEventRefs(events, ["audit_refs"])
              : countTimelineRefs(timeline, ["receipt_refs", "audit_refs"])
          }
        />
        <Metric
          label="Idempotency refs"
          value={
            evidence
              ? evidence.idempotency_refs.length
              : countTimelineRefs(timeline, ["idempotency_refs"])
          }
        />
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
                  evidence?.route_ref ??
                  today.evidence_timeline_backend_route_ref ??
                  "GET /control-center/today/summary"
                }
              />
            <DetailTerm
              label="Contract ref"
              value={
                evidence?.contract_ref ??
                today.evidence_timeline_productization_contract_ref ??
                today.evidence_history_contract_ref
              }
            />
            <DetailTerm label="Storage ref" value={evidence?.storage_ref ?? today.storage_ref} />
            <DetailTerm
              label="Authority boundary"
              value={
                evidence?.authority_boundary ??
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
        <WeeklyReviewNarrativeCard narrative={today.weekly_review_narrative} />
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
            items={evidence?.blocked_states ?? today.evidence_timeline_blocked_states ?? []}
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
      {events.length > 0 ? (
        <div className="compact-stack">
          {groups.map((group) => {
            const groupEvents = events.filter(
              (event) => event.group_ref === group.group_ref,
            );
            return (
              <article className="status-card" key={group.group_ref}>
                <div className="status-card-header">
                  <h3>{group.group_label}</h3>
                  <span>{group.group_kind}</span>
                </div>
                <dl className="detail-list">
                  <DetailTerm label="Group ref" value={group.group_ref} />
                  <DetailTerm label="Events" value={String(group.event_count)} />
                  <DetailTerm label="Rollback posture" value={group.rollback_posture} />
                </dl>
                <InlineListWithFallback
                  emptyLabel="Event types: none recorded"
                  items={group.event_types}
                />
                <RefListWithFallback
                  emptyLabel="Receipt refs: not recorded"
                  refs={group.receipt_refs}
                />
                <RefListWithFallback
                  emptyLabel="Approval refs: identifiers only or not present"
                  refs={group.approval_refs}
                />
                <RefListWithFallback
                  emptyLabel="Idempotency refs: not recorded"
                  refs={group.idempotency_refs}
                />
                <InlineListWithFallback
                  emptyLabel="Group blockers: evidence remains inspection-only"
                  items={group.blocked_states}
                />
                <div className="review-grid">
                  {groupEvents.map((event) => (
                    <EvidenceTimelineEventCard event={event} key={event.event_ref} />
                  ))}
                </div>
              </article>
            );
          })}
        </div>
      ) : timeline.length === 0 ? (
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
    | "idempotency_refs"
    | "rollback_refs"
    | "latency_refs"
    | "foundation_gate_refs"
  >,
) {
  return timeline.reduce(
    (count, item) =>
      count +
      fields.reduce(
        (fieldCount, field) => fieldCount + (item[field] ?? []).length,
        0,
      ),
    0,
  );
}

function countEventRefs(
  events: FounderLoopEvidenceTimelineEvent[],
  fields: Array<"audit_refs">,
) {
  return events.reduce(
    (count, event) =>
      count +
      fields.reduce((fieldCount, field) => fieldCount + event[field].length, 0),
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

function EvidenceTimelineEventCard({
  event,
}: {
  event: FounderLoopEvidenceTimelineEvent;
}) {
  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>{event.title}</h3>
        <span>{event.event_type}</span>
      </div>
      <p>{event.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Event ref" value={event.event_ref} />
        <DetailTerm label="Event type ref" value={event.event_type_ref} />
        <DetailTerm label="Timeline ref" value={event.timeline_item_ref} />
        <DetailTerm label="Group ref" value={event.group_ref} />
        <DetailTerm label="Side effect" value={event.item_kind} />
        <DetailTerm label="Authority posture" value={event.authority_posture} />
        <DetailTerm label="Rollback posture" value={event.rollback_posture} />
        <DetailTerm
          label="Approval ref authority"
          value={event.approval_ref_authority ? "yes" : "no"}
        />
        <DetailTerm
          label="Rollback execution"
          value={event.rollback_execution_enabled ? "enabled" : "not scoped"}
        />
        <DetailTerm
          label="Memory truth authority"
          value={event.memory_truth_authority ? "yes" : "no"}
        />
        <DetailTerm
          label="Context injection"
          value={event.context_injection_authorized ? "authorized" : "not authorized"}
        />
        <DetailTerm
          label="Raw evidence included"
          value={event.raw_evidence_included ? "yes" : "no"}
        />
        <DetailTerm label="Redaction" value={event.redaction_status} />
      </dl>
      <div>
        <div className="status-card-header">
          <h4>History answers</h4>
          <span>{evidenceHistoryKeys.length}</span>
        </div>
        <ul className="ref-list">
          {evidenceHistoryKeys.map((key) => {
            const answer = event.history_answers[key];
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
        refs={event.source_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Status refs: missing until status binding exists"
        refs={event.status_refs ?? []}
      />
      <InlineListWithFallback
        emptyLabel="Route refs: no route binding available"
        items={event.related_route_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Receipt refs: not available for this event"
        refs={event.receipt_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Approval refs: identifiers only or not present"
        refs={event.approval_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Idempotency refs: not available for this event"
        refs={event.idempotency_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Audit refs: not available for this event"
        refs={event.audit_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Rollback refs: not available for this event"
        refs={event.rollback_refs ?? []}
      />
      <InlineListWithFallback
        emptyLabel="Rollback blockers: rollback remains inspection-only"
        items={event.rollback_blockers ?? []}
      />
      <InlineListWithFallback
        emptyLabel="Event blockers: evidence remains inspection-only"
        items={event.blocked_states ?? []}
      />
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
        emptyLabel="Idempotency refs: not available for this item"
        refs={item.idempotency_refs ?? []}
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

function isBackendOwnedEnvelope(
  envelope: FounderLoopActionItem["approval_envelope"],
): boolean {
  return (
    envelope.backend_owned === true &&
    envelope.source === pythonCoreActionReadModelSource
  );
}

function isBackendOwnedReceiptVisibility(
  visibility: FounderLoopActionItem["receipt_visibility"],
): boolean {
  return (
    visibility.backend_owned === true &&
    visibility.source === pythonCoreActionReadModelSource
  );
}

function hasAuthoritativeActionReadModel(item: FounderLoopActionItem): boolean {
  return (
    isBackendOwnedEnvelope(item.approval_envelope) &&
    isBackendOwnedReceiptVisibility(item.receipt_visibility)
  );
}

function canShowLocalTaskCommitControl(
  item: FounderLoopActionItem,
  actionReadModelAuthoritative: boolean,
): boolean {
  return (
    actionReadModelAuthoritative &&
    hasAuthoritativeActionReadModel(item) &&
    item.local_task_commit_eligible === true &&
    item.action_kind === "local_task_create" &&
    Boolean(item.local_task_commit_approval_ref)
  );
}

function committedSafeRef(value: string | null | undefined): string | null {
  if (!value || unavailableReceiptStates.includes(value)) {
    return null;
  }
  return value;
}

function ActionItemCard({
  actionReadModelAuthoritative,
  item,
}: {
  actionReadModelAuthoritative: boolean;
  item: FounderLoopActionItem;
}) {
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
  const actionEnvelopeRef = item.action_envelope_ref ?? "missing until scoped contract";
  const actionScopeRef = item.action_scope_ref ?? "scope ref missing";
  const actionApprovalRequirement =
    item.action_approval_requirement_ref ?? "approval requirement ref missing";
  const actionGroupId = item.action_group_id ?? "proposal_only_no_execution_path";
  const actionGroupLabel = item.action_group_label ?? "Proposal-only / no execution path";
  const actionGroupReason =
    item.action_group_reason ??
    "No backend-classified execution path is available for this item.";
  const availableAction =
    item.action_group_available_action ?? "Review proposal refs only.";
  const backendReadModelAvailable = hasAuthoritativeActionReadModel(item);
  const committedLocalTaskRef = committedSafeRef(
    item.receipt_visibility.local_task_ref,
  );
  const localTaskRefLabel = committedLocalTaskRef
    ? "Local task ref"
    : "Local task target ref";
  const localTaskRefValue =
    committedLocalTaskRef ??
    (item.local_task_ref ? `target only: ${item.local_task_ref}` : "pending");
  const localTaskReceiptValue =
    item.receipt_visibility.local_task_commit_receipt_ref ??
    item.local_task_commit_receipt_ref ??
    "missing";
  const localTaskEligibilityValue =
    backendReadModelAvailable && actionReadModelAuthoritative
      ? item.local_task_commit_eligible
        ? "eligible"
        : "blocked"
      : "backend_read_model_unavailable";

  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>{item.title}</h3>
        <span>{actionGroupLabel}</span>
      </div>
      <p>{item.safe_summary}</p>
      <p className="muted">
        {actionGroupReason} Available operator action: {availableAction}
      </p>
      <ApprovalEnvelopeCard envelope={item.approval_envelope} />
      <ReceiptVisibilityCard visibility={item.receipt_visibility} />
      <dl className="detail-list">
        <DetailTerm label="Item ref" value={item.item_ref} />
        <DetailTerm label="Queue lane" value={actionGroupId} />
        <DetailTerm label="Status" value={item.status} />
        <DetailTerm label="Priority" value={item.priority} />
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
        <DetailTerm
          label="Action envelope contract"
          value={item.action_envelope_contract_ref ?? "missing"}
        />
        <DetailTerm label="Action envelope" value={actionEnvelopeRef} />
        <DetailTerm
          label="Action envelope status"
          value={item.action_envelope_status ?? "missing"}
        />
        <DetailTerm label="Exact scope" value={actionScopeRef} />
        <DetailTerm
          label="Approval requirement"
          value={actionApprovalRequirement}
        />
        <DetailTerm
          label="Envelope execution"
          value={item.action_envelope_execution_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Grant capture"
          value={
            item.action_envelope_grant_capture_enabled ? "enabled" : "disabled"
          }
        />
        <DetailTerm
          label="Decision contract"
          value={item.state_change_contract_ref ?? "missing until recorded"}
        />
        <DetailTerm label="Action kind" value={item.action_kind ?? "review_only"} />
        <DetailTerm
          label="Local task contract"
          value={item.local_task_commit_contract_ref ?? "not a local task lane"}
        />
        <DetailTerm
          label="Local task route"
          value={item.local_task_commit_route_ref ?? "not a local task lane"}
        />
        <DetailTerm
          label="Local task eligibility"
          value={localTaskEligibilityValue}
        />
        <DetailTerm
          label="Local task approval"
          value={item.local_task_commit_approval_status ?? "missing"}
        />
        <DetailTerm
          label="Local task approval ref"
          value={item.local_task_commit_approval_ref ?? "missing"}
        />
        <DetailTerm
          label={localTaskRefLabel}
          value={localTaskRefValue}
        />
        <DetailTerm
          label="Local task receipt"
          value={localTaskReceiptValue}
        />
        <DetailTerm label="Next safe action" value={nextSafeAction} />
      </dl>
      {actionGroupId === "ready_for_decision" &&
      backendReadModelAvailable &&
      actionReadModelAuthoritative ? (
        <ActionDecisionControls item={item} />
      ) : null}
      {actionGroupId === "ready_for_decision" &&
      (!backendReadModelAvailable || !actionReadModelAuthoritative) ? (
        <p className="muted">
          Decision controls unavailable until the local backend supplies an
          authoritative Action Inbox read model.
        </p>
      ) : null}
      {actionGroupId === "approved_local_task_lane" ? (
        <LocalTaskCommitControls
          actionReadModelAuthoritative={actionReadModelAuthoritative}
          item={item}
        />
      ) : null}
      {item.blocked_state ? <p className="muted">{item.blocked_state}</p> : null}
      <InlineListWithFallback
        emptyLabel="Review actions: missing"
        items={item.action_review_actions ?? []}
      />
      <RefListWithFallback
        emptyLabel="Action expected receipt refs: missing until scoped contract"
        refs={item.action_expected_receipt_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Action envelope blockers: missing"
        refs={item.action_blocked_state_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Local task commit blockers: not a local task lane"
        refs={item.local_task_commit_blocked_reasons ?? []}
      />
      <RefListWithFallback
        emptyLabel="Local task external authority blockers: missing"
        refs={item.local_task_commit_external_authority_blocked_refs ?? []}
      />
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

function ApprovalEnvelopeCard({
  envelope,
}: {
  envelope: FounderLoopActionItem["approval_envelope"];
}) {
  const backendOwned = isBackendOwnedEnvelope(envelope);
  return (
    <section
      aria-label={backendOwned ? "Approval Envelope Card" : "Approval Envelope Unavailable"}
      className={`approval-envelope-card${backendOwned ? "" : " unavailable"}`}
    >
      <div className="review-card-heading compact">
        <h4>{backendOwned ? "Approval Envelope Card" : "Approval Envelope Unavailable"}</h4>
        <span>{envelope.contract_ref}</span>
      </div>
      {backendOwned ? (
        <p className="muted">
          Backend-owned grammar from {envelope.source}; React renders this read
          model but does not mint authority, grants, scope, risk, side effects,
          or approval requirements.
        </p>
      ) : (
        <p className="muted">
          Mock-only fallback from {envelope.source}; backend read model is
          unavailable, and React does not mint authority, grants, scope, risk,
          side effects, or approval requirements.
        </p>
      )}
      <dl className="detail-list">
        <DetailTerm label="Action kind" value={envelope.action_kind} />
        <DetailTerm label="Exact scope" value={envelope.exact_scope} />
        <DetailTerm label="Risk class" value={envelope.risk_class} />
        <DetailTerm label="Side-effect class" value={envelope.side_effect_class} />
        <DetailTerm
          label="Approval requirement"
          value={envelope.approval_requirement}
        />
        <DetailTerm
          label="Expiry/staleness"
          value={envelope.expiry_or_staleness}
        />
        <DetailTerm label="Idempotency ref" value={envelope.idempotency_ref} />
        <DetailTerm
          label="Rollback/safe-disable"
          value={envelope.rollback_safe_disable_posture}
        />
        <DetailTerm
          label="Backend owned"
          value={backendOwned ? "yes" : "unavailable"}
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Expected receipt refs: missing"
        refs={envelope.expected_receipt_refs}
      />
      <RefListWithFallback
        emptyLabel="Blocked authority refs: not applicable"
        refs={envelope.blocked_authority_refs}
      />
      <RefListWithFallback
        emptyLabel="Evidence refs: missing"
        refs={envelope.evidence_refs}
      />
      <InlineListWithFallback
        emptyLabel="Missing field states: none"
        items={envelope.missing_field_states}
      />
    </section>
  );
}

function ReceiptVisibilityCard({
  visibility,
}: {
  visibility: FounderLoopActionItem["receipt_visibility"];
}) {
  const backendOwned = isBackendOwnedReceiptVisibility(visibility);
  return (
    <section
      aria-label={backendOwned ? "Receipt Visibility" : "Receipt Visibility Unavailable"}
      className={`receipt-visibility-card${backendOwned ? "" : " unavailable"}`}
    >
      <div className="review-card-heading compact">
        <h4>{backendOwned ? "Receipt Visibility" : "Receipt Visibility Unavailable"}</h4>
        <span>{visibility.contract_ref}</span>
      </div>
      {backendOwned ? (
        <p className="muted">
          Backend-owned receipt visibility from {visibility.source}; React renders
          safe refs and explicit states but does not create receipts, replay
          state, conflicts, eligibility, or authority.
        </p>
      ) : (
        <p className="muted">
          Mock-only fallback from {visibility.source}; backend receipt visibility
          is unavailable, and React does not create receipts, replay state,
          conflicts, eligibility, or authority.
        </p>
      )}
      <dl className="detail-list">
        <DetailTerm
          label="Decision receipt ref"
          value={visibility.decision_receipt_ref}
        />
        <DetailTerm label="Local task ref" value={visibility.local_task_ref} />
        <DetailTerm
          label="Local task commit receipt ref"
          value={visibility.local_task_commit_receipt_ref}
        />
        <DetailTerm
          label="Evidence Timeline event ref"
          value={visibility.evidence_timeline_event_ref}
        />
        <DetailTerm label="Replay posture" value={visibility.replay_posture} />
        <DetailTerm
          label="Conflict posture"
          value={visibility.conflict_posture}
        />
        <DetailTerm
          label="Backend owned"
          value={backendOwned ? "yes" : "unavailable"}
        />
      </dl>
      <InlineListWithFallback
        emptyLabel="Receipt visibility missing states: none"
        items={visibility.missing_field_states}
      />
    </section>
  );
}

const actionDecisionLabels: Record<FounderLoopActionDecisionKind, string> = {
  approve: "Record approval",
  edit: "Record edit",
  reject: "Record rejection",
  defer: "Record defer",
};

function ActionDecisionControls({ item }: { item: FounderLoopActionItem }) {
  const [state, setState] = useState<{
    status: "idle" | "pending" | "recorded" | "failed";
    decision?: FounderLoopActionDecisionKind;
    receipt?: FounderLoopActionDecisionReceipt;
    message?: string;
  }>({ status: "idle" });
  const pending = state.status === "pending";

  async function recordDecision(decision: FounderLoopActionDecisionKind) {
    setState({ status: "pending", decision });
    try {
      const receipt = await submitActionDecision(item.item_ref, decision, {
        decision_reason_ref: `decision-reason-ref:control-center:${decision}`,
        edited_envelope_ref:
          decision === "edit"
            ? (item.action_envelope_ref ?? item.approval_envelope_ref ?? null)
            : undefined,
        defer_until_ref:
          decision === "defer"
            ? "defer-until-ref:operator-selected-later"
            : undefined,
        metadata_refs: [
          `metadata-ref:control-center-action-decision:${decision}`,
          item.item_ref,
        ],
      });
      setState({
        status: "recorded",
        decision,
        receipt,
        message: `${receipt.status}: ${receipt.safe_summary}`,
      });
    } catch (error) {
      setState({
        status: "failed",
        decision,
        message:
          error instanceof Error
            ? error.message
            : "Action decision receipt was not recorded safely.",
      });
    }
  }

  return (
    <div className="decision-controls" aria-label={`${item.title} decisions`}>
      <div className="decision-button-row">
        {(
          ["approve", "edit", "reject", "defer"] as FounderLoopActionDecisionKind[]
        ).map((decision) => (
          <button
            className="secondary-button"
            disabled={pending}
            key={decision}
            onClick={() => void recordDecision(decision)}
            type="button"
          >
            {pending && state.decision === decision
              ? "Recording"
              : actionDecisionLabels[decision]}
          </button>
        ))}
      </div>
      {state.message ? <p className="muted">{state.message}</p> : null}
      {state.receipt ? (
        <dl className="detail-list">
          <DetailTerm label="Receipt" value={state.receipt.receipt_ref} />
          <DetailTerm label="Audit" value={state.receipt.audit_ref} />
          <DetailTerm
            label="Action executed"
            value={state.receipt.action_executed ? "yes" : "no"}
          />
          <DetailTerm
            label="Connector write"
            value={state.receipt.connector_write_performed ? "yes" : "no"}
          />
        </dl>
      ) : null}
    </div>
  );
}

function LocalTaskCommitControls({
  actionReadModelAuthoritative,
  item,
}: {
  actionReadModelAuthoritative: boolean;
  item: FounderLoopActionItem;
}) {
  const [state, setState] = useState<{
    status: "idle" | "pending" | "recorded" | "failed";
    receipt?: FounderLoopLocalTaskCommitReceipt;
    message?: string;
  }>({ status: "idle" });
  const approvalRef = item.local_task_commit_approval_ref;
  if (!canShowLocalTaskCommitControl(item, actionReadModelAuthoritative)) {
    return null;
  }
  const commitApprovalRef = approvalRef as string;
  const pending = state.status === "pending";

  async function recordLocalTaskCommit() {
    setState({ status: "pending" });
    try {
      const receipt = await commitLocalTask(item.item_ref, {
        approval_ref: commitApprovalRef,
        decision_reason_ref:
          "decision-reason-ref:control-center:local-task-commit",
        metadata_refs: [
          "metadata-ref:control-center-local-task-commit",
          item.item_ref,
        ],
      });
      setState({
        status: "recorded",
        receipt,
        message: `${receipt.status}: ${receipt.safe_summary}`,
      });
    } catch (error) {
      setState({
        status: "failed",
        message:
          error instanceof Error
            ? error.message
            : "Local task commit receipt was not recorded safely.",
      });
    }
  }

  return (
    <div className="decision-controls" aria-label={`${item.title} local task`}>
      <div className="decision-button-row">
        <button
          className="secondary-button"
          disabled={pending}
          onClick={() => void recordLocalTaskCommit()}
          type="button"
        >
          {pending ? "Committing" : "Commit local task"}
        </button>
      </div>
      <p className="muted">
        Local-only task commit. Connector writes, shell, model authority,
        memory writes, context injection, and production authority remain blocked.
      </p>
      {state.message ? <p className="muted">{state.message}</p> : null}
      {state.receipt ? (
        <dl className="detail-list">
          <DetailTerm label="Local task" value={state.receipt.local_task_ref} />
          <DetailTerm label="Receipt" value={state.receipt.receipt_ref} />
          <DetailTerm label="Audit" value={state.receipt.audit_ref} />
          <DetailTerm
            label="Evidence Timeline event"
            value={state.receipt.evidence_timeline_event_ref}
          />
          <DetailTerm
            label="Replay"
            value={state.receipt.replayed ? "yes" : "no"}
          />
          <DetailTerm
            label="Connector write"
            value={state.receipt.connector_write_performed ? "yes" : "no"}
          />
          <DetailTerm
            label="External side effect"
            value={state.receipt.external_side_effect_performed ? "yes" : "no"}
          />
        </dl>
      ) : null}
    </div>
  );
}

function PlanCard({ plan }: { plan: FounderLoopPlanSummary }) {
  const actionEnvelopeRef = plan.action_envelope_ref ?? "missing until scoped contract";
  const scopeRef = plan.scope_ref ?? "scope ref missing";
  const approvalRequirement =
    plan.approval_requirement_ref ?? "approval requirement ref missing";

  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>{plan.title}</h3>
        <span>{plan.status}</span>
      </div>
      <p>{plan.safe_summary}</p>
      <p className="muted">{plan.next_step_summary}</p>
      <dl className="detail-list">
        <DetailTerm
          label="Action envelope contract"
          value={plan.action_envelope_contract_ref ?? "missing"}
        />
        <DetailTerm label="Action envelope" value={actionEnvelopeRef} />
        <DetailTerm
          label="Envelope status"
          value={plan.action_envelope_status ?? "missing"}
        />
        <DetailTerm label="Exact scope" value={scopeRef} />
        <DetailTerm label="Side effect" value={plan.side_effect_class ?? "missing"} />
        <DetailTerm label="Risk" value={plan.risk_class ?? "missing"} />
        <DetailTerm
          label="Approval before mutation"
          value={plan.approval_required ? "required" : "not required"}
        />
        <DetailTerm label="Approval requirement" value={approvalRequirement} />
        <DetailTerm
          label="Idempotency"
          value={plan.idempotency_key_ref ?? "missing until scoped contract"}
        />
        <DetailTerm
          label="Expiry posture"
          value={plan.expires_at ?? "review required before mutation"}
        />
        <DetailTerm label="Rollback" value={plan.rollback_ref ?? "missing"} />
        <DetailTerm
          label="Safe disable"
          value={plan.safe_disable_ref ?? "missing"}
        />
        <DetailTerm
          label="Execution"
          value={plan.action_execution_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Grant capture"
          value={plan.approval_grant_capture_enabled ? "enabled" : "disabled"}
        />
      </dl>
      <InlineListWithFallback
        emptyLabel="Review actions: missing"
        items={plan.review_actions ?? []}
      />
      <RefListWithFallback
        emptyLabel="Expected receipt refs: missing until scoped contract"
        refs={plan.expected_receipt_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Action envelope blockers: missing"
        refs={plan.blocked_state_refs ?? []}
      />
      <RefList refs={plan.evidence_refs} />
    </article>
  );
}

function BriefingCard({
  allowActionEnvelopePromotion = false,
  item,
}: {
  allowActionEnvelopePromotion?: boolean;
  item: FounderLoopBriefingItem;
}) {
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
      {allowActionEnvelopePromotion ? (
        <TodayActionEnvelopeControls item={item} />
      ) : null}
    </article>
  );
}

const memoryDecisionLabels: Record<MemoryReviewDecisionKind, string> = {
  accept: "Record accept receipt",
  correct: "Record correction receipt",
  reject: "Record reject receipt",
};

const memoryReviewDecisionBlockedRefs = [
  "blocked-state:no-memory-write",
  "blocked-state:no-memory-delete",
  "blocked-state:no-memory-export",
  "blocked-state:no-context-injection",
  "blocked-state:no-connector-write",
  "blocked-state:no-external-crm-sync",
  "blocked-state:no-automatic-action-execution",
  "blocked-state:no-model-provider-authority",
  "blocked-state:no-public-beta-or-production-authority",
];

type MemoryDecisionControlState = {
  status: "idle" | "pending" | "recorded" | "replayed" | "failed";
  decision?: MemoryReviewDecisionKind;
  receipt?: MemoryReviewDecisionReceipt;
  message?: string;
};

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
  const decisionCaptureStatus =
    item.decision_capture_status ?? "review_needed_no_decision_captured";
  const businessQualityPosture =
    item.business_memory_quality_posture ?? "review_required_quality_blocked";
  const businessAuthorityBoundary =
    item.business_memory_authority_boundary ??
    "Business memory quality is review metadata only; external CRM writes, account sync, automatic recall, memory mutation, and context injection remain unscoped.";
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
        <DetailTerm
          label="Business candidate"
          value={item.business_memory_candidate_ref}
        />
        <DetailTerm
          label="Business quality"
          value={businessQualityPosture}
        />
        <DetailTerm
          label="Business review"
          value={item.business_memory_review_state}
        />
        <DetailTerm
          label="Business source"
          value={item.business_memory_source_kind}
        />
        <DetailTerm
          label="Business source trust"
          value={item.business_memory_source_trust_posture}
        />
        <DetailTerm
          label="Business redaction"
          value={item.business_memory_redaction_status}
        />
        <DetailTerm label="Source kind" value={sourceKind} />
        <DetailTerm label="Source trust" value={sourceTrustPosture} />
        <DetailTerm label="Decision capture" value={decisionCaptureStatus} />
        <DetailTerm label="Decision actor" value={item.decision_actor_ref} />
        <DetailTerm
          label="Decision source kind"
          value={item.decision_source_kind}
        />
        <DetailTerm
          label="Decision source trust"
          value={item.decision_source_trust_posture}
        />
        <DetailTerm
          label="Decision review-only"
          value={item.decision_review_only ? "yes" : "no"}
        />
        <DetailTerm
          label="Delete authority"
          value={item.memory_delete_authorized ? "yes" : "no"}
        />
        <DetailTerm
          label="Export authority"
          value={item.memory_export_authorized ? "yes" : "no"}
        />
        <DetailTerm
          label="CRM write authority"
          value={item.business_memory_crm_write_authorized ? "yes" : "no"}
        />
        <DetailTerm
          label="Account sync authority"
          value={item.business_memory_account_sync_authorized ? "yes" : "no"}
        />
        <DetailTerm
          label="Business recall"
          value={item.business_memory_accepted_as_recall ? "yes" : "no"}
        />
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
        <DetailTerm
          label="Export posture"
          value={item.business_memory_export_posture}
        />
        <DetailTerm label="Confidence posture" value={confidencePosture} />
        <DetailTerm label="Stale-state posture" value={staleState} />
        <DetailTerm
          label="Business boundary"
          value={businessAuthorityBoundary}
        />
        <DetailTerm label="Next safe action" value={nextSafeAction} />
        <DetailTerm
          label="Business next action"
          value={item.business_memory_next_safe_action}
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Business quality refs: missing"
        refs={item.business_memory_quality_state_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Business related refs: missing"
        refs={item.business_memory_related_entity_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Business surface refs: missing"
        refs={item.business_memory_surface_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Business blocker refs: memory and CRM mutation remain unscoped"
        refs={item.business_memory_blocker_refs ?? []}
      />
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
      <RefListWithFallback
        emptyLabel="Decision audit refs: missing until review capture contract"
        refs={item.decision_audit_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Decision receipt refs: missing until review capture contract"
        refs={item.decision_receipt_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Decision blocked refs: memory mutation remains unscoped"
        refs={item.decision_blocked_state_refs ?? []}
      />
      <MemoryReviewDecisionControls item={item} />
      <InlineListWithFallback
        emptyLabel="Decision labels only: accept, correct, reject, defer, merge, supersede, forget request"
        items={item.available_decision_states ?? []}
      />
      <InlineListWithFallback
        emptyLabel="Item blockers: memory write and context injection not scoped"
        items={item.blocked_states ?? []}
      />
      <RefList refs={item.evidence_refs ?? []} />
    </article>
  );
}

function MemoryReviewDecisionControls({
  item,
}: {
  item: FounderLoopMemoryReviewItem;
}) {
  const [state, setState] = useState<MemoryDecisionControlState>({
    status: "idle",
  });
  const pending = state.status === "pending";
  const candidateRef = item.business_memory_candidate_ref || item.review_ref;

  async function recordDecision(decision: MemoryReviewDecisionKind) {
    setState({ status: "pending", decision });
    try {
      const safeCandidateSuffix = safeRefSuffix(candidateRef);
      const receipt = await recordMemoryReviewDecision(candidateRef, decision, {
        reviewer_ref: "actor-ref:control-center-memory-review",
        corrected_summary_ref:
          decision === "correct"
            ? `safe-summary-ref:control-center-memory-correction:${safeCandidateSuffix}`
            : undefined,
        source_refs: item.source_refs ?? [],
        evidence_refs: item.evidence_refs ?? [],
        metadata_refs: [
          `metadata-ref:control-center-memory-review:${decision}`,
          item.review_ref,
        ],
        blocked_state_refs: memoryReviewDecisionBlockedRefs,
      });
      const status = receipt.replayed ? "replayed" : "recorded";
      setState({
        status,
        decision,
        receipt,
        message: `${status}: ${receipt.safe_summary_ref}`,
      });
    } catch (error) {
      setState({
        status: "failed",
        decision,
        message:
          error instanceof Error
            ? error.message
            : "Memory Review decision receipt was not recorded safely.",
      });
    }
  }

  return (
    <div className="decision-controls" aria-label={`${item.title} memory decisions`}>
      <div className="decision-button-row">
        {(["accept", "correct", "reject"] as MemoryReviewDecisionKind[]).map(
          (decision) => (
            <button
              className="secondary-button"
              disabled={pending}
              key={decision}
              onClick={() => void recordDecision(decision)}
              type="button"
            >
              {pending && state.decision === decision
                ? "Recording"
                : memoryDecisionLabels[decision]}
            </button>
          ),
        )}
      </div>
      {state.message ? <p className="muted">{state.message}</p> : null}
      {state.receipt ? (
        <dl className="detail-list">
          <DetailTerm label="Decision state" value={state.status} />
          <DetailTerm label="Receipt" value={state.receipt.receipt_ref} />
          <DetailTerm
            label="Recall record"
            value={state.receipt.reviewed_recall_record_ref ?? "not created"}
          />
          <DetailTerm label="Audit" value={state.receipt.audit_ref} />
          <DetailTerm
            label="Evidence event"
            value={state.receipt.evidence_timeline_event_ref}
          />
          <DetailTerm
            label="Context injection"
            value={
              state.receipt.context_injection_authorized
                ? "enabled"
                : "blocked"
            }
          />
          <DetailTerm
            label="Connector write"
            value={
              state.receipt.connector_write_authorized ? "enabled" : "blocked"
            }
          />
          <DetailTerm
            label="Action execution"
            value={
              state.receipt.automatic_action_execution_authorized
                ? "enabled"
                : "blocked"
            }
          />
        </dl>
      ) : null}
    </div>
  );
}

function safeRefSuffix(value: string): string {
  return (
    value
      .toLowerCase()
      .replace(/[^a-z0-9_.:-]+/g, "-")
      .replace(/^-+|-+$/g, "") || "missing"
  );
}

function TodayActionEnvelopeControls({
  item,
}: {
  item: FounderLoopBriefingItem;
}) {
  const [state, setState] = useState<{
    status: "idle" | "pending" | "recorded" | "failed";
    receipt?: FounderLoopActionEnvelopePromotionReceipt;
    message?: string;
  }>({ status: "idle" });
  const pending = state.status === "pending";

  async function createEnvelope() {
    setState({ status: "pending" });
    try {
      const receipt = await submitTodayActionEnvelope({
        today_item_ref: item.briefing_ref,
        actor_context: "control_center_today_surface",
        decision_reason_ref: "decision-reason-ref:today-action-envelope",
        risk_class: "medium",
        priority: item.priority === "high" ? "high" : "medium",
        metadata_refs: [
          "metadata-ref:control-center-today-action-envelope",
          item.briefing_ref,
        ],
      });
      setState({
        status: "recorded",
        receipt,
        message: `${receipt.status}: ${receipt.safe_summary}`,
      });
    } catch (error) {
      setState({
        status: "failed",
        message:
          error instanceof Error
            ? error.message
            : "Today action envelope receipt was not recorded safely.",
      });
    }
  }

  return (
    <div className="decision-controls" aria-label={`${item.title} action envelope`}>
      <button
        className="secondary-button"
        disabled={pending}
        onClick={() => void createEnvelope()}
        type="button"
      >
        {pending ? "Creating" : "Create Action envelope"}
      </button>
      {state.message ? <p className="muted">{state.message}</p> : null}
      {state.receipt ? (
        <dl className="detail-list">
          <DetailTerm label="Action envelope" value={state.receipt.action_envelope_ref} />
          <DetailTerm label="Receipt" value={state.receipt.receipt_ref} />
          <DetailTerm label="Audit" value={state.receipt.audit_ref} />
          <DetailTerm
            label="Evidence event"
            value={state.receipt.evidence_timeline_event_ref}
          />
          <DetailTerm
            label="Action executed"
            value={state.receipt.action_executed ? "yes" : "no"}
          />
        </dl>
      ) : null}
    </div>
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
      {items.map((item, index) => (
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
