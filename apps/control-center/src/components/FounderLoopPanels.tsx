import { useEffect, useState, type ReactNode } from "react";
import {
  commitLocalTask,
  decideGovernedRuntimeInvocation,
  executeGovernedRuntimeInvocation,
  fetchActionReceipt,
  fetchFounderActionsInbox,
  fetchFounderMemoryContextPacks,
  recordManualMemoryCandidate,
  recordMemoryFeedback,
  recordMemoryContextPackActionProposal,
  recordMemoryReviewDecision,
  requestGovernedRuntimeCommand,
  requestGovernedRuntimeLocalModelProposal,
  safeDisableGovernedRuntime,
  submitActionDecision,
  submitTodayActionEnvelope,
} from "../api/client";
import type { GovernedRuntimeCommandIntent } from "../api/client";
import { useBackendTruthMutationBinding } from "../backendTruthMutationBinding";
import { ConnectorDeliveryReviewQueuePanel } from "./ConnectorDeliveryReviewQueuePanel";
import { ConnectorReadPlatformCard } from "./ConnectorReadPlatformCard";
import type {
  ActionToolCodeLaneCatalogReadModel,
  ActionToolCodeLaneEntry,
  FounderLoopAgentLoopThread,
  FounderLoopActionDecisionKind,
  FounderLoopActionDecisionReceipt,
  FounderLoopActionEnvelopePromotionReceipt,
  FounderLoopActionGroupId,
  FounderLoopActionGroupSummary,
  FounderLoopActionInboxDecisionLaneItem,
  FounderLoopActionInboxDecisionLaneReadModel,
  FounderLoopActionInboxWorkQueueReadModel,
  FounderLoopActionInboxWorkQueueWorkItem,
  FounderLoopActionsInbox,
  FounderLoopActionItem,
  FounderLoopBriefingItem,
  FounderLoopChatToLoopHandoffReadModel,
  FounderLoopEvidenceNarrativeEntry,
  FounderLoopEvidenceAuditReceiptSpine,
  FounderLoopEvidenceTimelineEvent,
  FounderLoopEvidenceTimelineIndex,
  FounderLoopEvidenceTimelineItem,
  FounderLoopEvidenceTimelineNarrativeReadModel,
  FounderLoopEvidenceMemoryLoopBindingReadModel,
  FounderLoopFollowUpTrackerReadModel,
  FounderLoopFusionRoutingDelegationReadModel,
  FounderLoopCacheContextEconomics,
  FounderLoopDelegationProposal,
  FounderLoopLocalTaskCommitReceipt,
  FounderLoopMemoryContextPackProposal,
  FounderLoopMemoryContextPackActionProposalReceipt,
  FounderLoopMemoryContextPacks,
  FounderLoopMemoryCitationIntegrity,
  FounderLoopMemoryContextManifest,
  FounderLoopMemoryMaintenanceRuns,
  FounderLoopMemoryQualityIssue,
  FounderLoopMemoryQualityIssues,
  FounderLoopMemoryReview,
  FounderLoopMemoryRetrievalDiagnostics,
  FounderLoopMemoryReviewItem,
  FounderLoopMemoryWorkbench,
  FounderLoopMemoryWorkbenchItem,
  FounderLoopMorningBriefing,
  FounderLoopMorningBriefingV1ReadModel,
  FounderLoopOperatorRunTimeline,
  FounderLoopPlanSummary,
  FounderLoopPlansToActionsBridgeReadModel,
  FounderLoopProductProofReadModel,
  FounderLoopRunsIntegrationReadModel,
  FounderLoopRunsIntegrationSurfaceId,
  FounderLoopRuntimeActionInboxBridgeReadModel,
  FounderLoopSourceReadiness,
  FounderLoopSourceReadinessProposalCandidate,
  FounderLoopStorageStatus,
  FounderLoopTodaySummary,
  FounderLoopUnifiedWorkThreadReadModel,
  FounderLoopWeeklyCeoReviewV1ReadModel,
  FounderLoopWorkClassification,
  ControlCenterSettingsStatus,
  MemoryReviewDecisionKind,
  MemoryReviewDecisionReceipt,
  ManualMemoryCandidateReceipt,
  MemoryFeedbackKind,
  MemoryFeedbackReceipt,
  ProviderCredentialReadinessSummary,
  RunAttachedApprovalQueue,
  RunObservabilityReadModel,
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

const memoryFeedbackBlockedRefs = [
  "blocked-state:memory-feedback-no-automatic-memory-write",
  "blocked-state:memory-feedback-no-context-injection",
  "blocked-state:memory-feedback-no-action-execution",
  "blocked-state:memory-feedback-no-production-authority",
];

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
    label: "Approved local-task create lane",
    safe_summary:
      "Exact-approved local_task_create items that can be committed only through the typed local task route.",
    available_action: "Inspect approval posture or commit the local-task create lane.",
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
  | "Start Here"
  | "Today"
  | "Briefing"
  | "Inbox"
  | "Plans"
  | "Actions"
  | "Proof"
  | "Memory"
  | "Evidence"
  | "Trust"
  | "Settings";

type FounderLoopSpineItem = {
  surface: FounderLoopPrimarySurface;
  label: string;
  path: string;
  status: string;
  posture: "implemented" | "partial" | "blocked" | "receipt-backed" | "authority-gated";
  summary: string;
  nextSafeAction: string;
  refs: string[];
};

export function FounderLoopSpinePanel({
  activeSurface,
  actionReadModelAuthoritative,
  evidence,
  inbox,
  settingsStatus,
  today,
}: {
  activeSurface: FounderLoopPrimarySurface;
  actionReadModelAuthoritative: boolean;
  evidence?: FounderLoopEvidenceTimelineIndex;
  inbox?: FounderLoopActionsInbox;
  settingsStatus?: ControlCenterSettingsStatus;
  today: FounderLoopTodaySummary;
}) {
  const productProof = today.founder_loop_v1_product_proof_read_model;
  const items =
    productProof?.productized_surface_bindings.length
      ? buildProductizedFounderLoopSpineItems(productProof)
      : buildFounderLoopSpineItems({
          evidence,
          inbox,
          settingsStatus,
          today,
        });
  const localTaskSummary = summarizeLocalTaskCapability(
    inbox?.items ?? today.actions,
  );
  const loopTruthCopy = actionReadModelAuthoritative
    ? "The spine is backed by the local backend read model."
    : "This spine is showing non-authoritative fallback shape until the backend read model is available.";
  const localTaskAuthorityCopy = actionReadModelAuthoritative
    ? "Local task authority gated by backend approval"
    : "Local task authority requires backend approval";

  return (
    <section
      aria-labelledby="founder-loop-spine-heading"
      className="loop-spine"
    >
      <div className="loop-spine-header">
        <div>
          <p className="eyebrow">Founder Loop</p>
          <h2 id="founder-loop-spine-heading">Founder daily loop</h2>
        </div>
        <span className="status-pill compact">
          {today.daily_loop_summary?.status ?? today.status}
        </span>
      </div>
      <p className="section-copy">
        Start Here, Today, Action Inbox, Proof, Evidence, Memory, Trust, and
        Settings stay visible as one repo-safe governed loop.
        {` ${loopTruthCopy} `}No generic execution is available; inside this
        spine, the exact local-task create lane is the only mutating lane shown
        and it still requires backend approval. Web Evidence remains a separate
        Tier 1 Proof attachment lane when rendered on Proof.
      </p>
      <FounderLoopProofPathPanel
        activeSurface={activeSurface}
        readModel={productProof}
      />
      <div aria-label="Founder daily loop modules" className="loop-spine-grid">
        {items.map((item) => (
          <a
            aria-current={activeSurface === item.surface ? "page" : undefined}
            className={`loop-spine-card ${item.posture}`}
            href={item.path}
            key={item.surface}
          >
            <span className="loop-spine-card-topline">
              <strong>{item.label}</strong>
              <small>{item.posture}</small>
            </span>
            <span className="loop-spine-status">{item.status}</span>
            <span className="loop-spine-summary">{item.summary}</span>
            <span className="loop-spine-next">{item.nextSafeAction}</span>
            <span className="loop-spine-ref">{item.refs[0] ?? "safe refs pending"}</span>
          </a>
        ))}
      </div>
      <OperatorRunTimelineSummary timeline={evidence?.operator_run_timeline} />
      <div
        aria-label="Founder Loop authority boundaries"
        className="loop-authority-strip"
      >
        <span>No generic execution</span>
        <span>{localTaskAuthorityCopy}</span>
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

function FounderLoopProofPathPanel({
  activeSurface,
  readModel,
}: {
  activeSurface: FounderLoopPrimarySurface;
  readModel?: FounderLoopProductProofReadModel;
}) {
  const activeStepId = activeProofStepForSurface(activeSurface);

  if (!readModel) {
    return (
      <section
        aria-label="Founder Loop proof path"
        className="proof-path-panel missing"
      >
        <div className="proof-path-summary">
          <div>
            <p className="eyebrow">Seeded loop proof</p>
            <h3>Backend proof path missing</h3>
          </div>
          <span className="status-pill compact">missing backend read model</span>
        </div>
        <p className="proof-path-copy">
          Control Center will not infer the Morning Briefing, Today, Action
          Inbox, Receipt, Evidence, Memory, and Weekly Review path from
          fallback-only state.
        </p>
      </section>
    );
  }

  return (
    <section
      aria-label="Founder Loop proof path"
      className="proof-path-panel"
    >
      <div className="proof-path-summary">
        <div>
          <p className="eyebrow">Seeded loop proof</p>
          <h3>Morning Briefing to Weekly Review</h3>
        </div>
        <span className="status-pill compact">backend-owned demo-safe</span>
      </div>
      <div
        aria-label="Founder Loop V1 proof order"
        className="north-star-loop-rail proof-path-rail"
      >
        {readModel.steps.map((step, index) => (
          <a
            aria-current={step.step_id === activeStepId ? "page" : undefined}
            className={`north-star-loop-step ${proofStepPosture(step)}`}
            href={proofStepRoute(step.step_id)}
            key={step.step_id}
          >
            <span>{index + 1}</span>
            <strong>{step.surface}</strong>
            <small>{proofStepCaption(step)}</small>
          </a>
        ))}
      </div>
      <dl className="detail-list compact">
        <DetailTerm label="Scenario" value={readModel.scenario_ref} />
        <DetailTerm label="Shared state" value={readModel.shared_state_ref} />
        <DetailTerm
          label="Decision receipts"
          value={proofStatusLabel(readModel.decision_receipt_status)}
        />
        <DetailTerm
          label="Memory review"
          value={proofStatusLabel(readModel.memory_review_status)}
        />
        <DetailTerm
          label="Weekly review"
          value={proofStatusLabel(readModel.weekly_review_status)}
        />
      </dl>
      <article className="status-card embedded">
        <div className="status-card-header">
          <h3>Daily loop productization</h3>
          <span>repo-safe</span>
        </div>
        <dl className="detail-list">
          <DetailTerm label="Full-strength version" value={readModel.full_strength_goal} />
          <DetailTerm label="Repo-safe version" value={readModel.repo_safe_scope} />
          <DetailTerm
            label="Blocked / needs authority"
            value={readModel.blocked_authority_summary}
          />
        </dl>
        <RefListWithFallback
          emptyLabel="Exact promotion path refs missing"
          refs={readModel.exact_promotion_path_refs}
        />
      </article>
      {activeStepId === null ? (
        <p className="proof-path-copy">
          This surface is adjacent to the seeded proof path; no proof step is
          marked current here.
        </p>
      ) : null}
      <div className="loop-authority-strip">
        <span>No provider/model calls</span>
        <span>No A2A/MCP runtime dispatch</span>
        <span>No browser/live web</span>
        <span>No connector writes</span>
        <span>No email/calendar sends</span>
        <span>No CRM/account sync</span>
        <span>No shell/subprocess execution</span>
        <span>No memory writes/context injection</span>
        <span>No background autonomy</span>
        <span>No production authority</span>
      </div>
    </section>
  );
}

function activeProofStepForSurface(
  activeSurface: FounderLoopPrimarySurface,
): FounderLoopProductProofReadModel["steps"][number]["step_id"] | null {
  const activeStepBySurface: Partial<
    Record<
      FounderLoopPrimarySurface,
      FounderLoopProductProofReadModel["steps"][number]["step_id"]
    >
  > = {
    Actions: "action_inbox",
    Briefing: "morning_briefing",
    Evidence: "evidence_timeline",
    Memory: "memory_review",
    Today: "today",
  };
  return activeStepBySurface[activeSurface] ?? null;
}

function proofStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    candidate_available: "candidate visible",
    decision_receipts_visible: "receipts visible",
    loop_ready_with_receipts: "loop ready with receipts",
    outcome_summary_visible: "outcome summary visible",
  };
  return labels[status] ?? status.replaceAll("_", " ");
}

function proofStepCaption(
  step: FounderLoopProductProofReadModel["steps"][number],
): string {
  if (step.receipt_refs.length > 0) {
    return "receipt-backed";
  }
  if (proofStepStatusIsBlocked(step)) {
    return "blocked visible";
  }
  return step.status.replaceAll("_", " ");
}

function proofStepPosture(
  step: FounderLoopProductProofReadModel["steps"][number],
): DailyLoopCommandItem["posture"] {
  if (step.receipt_refs.length > 0) {
    return "waiting";
  }
  if (step.step_id === "memory_review") {
    return "influence";
  }
  if (proofStepStatusIsBlocked(step)) {
    return "blocked";
  }
  if (step.step_id === "action_inbox" || step.step_id === "decision_receipt") {
    return "review";
  }
  return "today";
}

function proofStepStatusIsBlocked(
  step: FounderLoopProductProofReadModel["steps"][number],
): boolean {
  const status = step.status.toLowerCase();
  return (
    status.includes("blocked") ||
    status.includes("missing") ||
    status.includes("not_available")
  );
}

function proofStepRoute(
  stepId: FounderLoopProductProofReadModel["steps"][number]["step_id"],
): string {
  const routeByStep: Record<
    FounderLoopProductProofReadModel["steps"][number]["step_id"],
    string
  > = {
    action_inbox: "/actions",
    decision_receipt: "/actions",
    evidence_timeline: "/evidence",
    memory_review: "/memory",
    morning_briefing: "/briefing",
    today: "/today",
    weekly_review: "/today",
  };
  return routeByStep[stepId];
}

function buildProductizedFounderLoopSpineItems(
  readModel: FounderLoopProductProofReadModel,
): FounderLoopSpineItem[] {
  return readModel.productized_surface_bindings.map((binding) => ({
    surface: productizedSurfaceLabel(binding.surface_id),
    label: binding.surface,
    path: binding.frontend_route_ref,
    status: binding.status,
    posture: productizedSurfacePosture(binding),
    summary: binding.safe_summary,
    nextSafeAction: binding.next_safe_action,
    refs: [
      binding.primary_proof_ref,
      binding.shared_ref,
      ...binding.source_refs,
      ...binding.receipt_refs,
      ...binding.evidence_refs,
      ...binding.memory_candidate_refs,
    ],
  }));
}

function productizedSurfaceLabel(
  surfaceId: FounderLoopProductProofReadModel["productized_surface_bindings"][number]["surface_id"],
): FounderLoopPrimarySurface {
  const labels: Record<
    FounderLoopProductProofReadModel["productized_surface_bindings"][number]["surface_id"],
    FounderLoopPrimarySurface
  > = {
    action_inbox: "Actions",
    evidence: "Evidence",
    memory: "Memory",
    proof: "Proof",
    settings: "Settings",
    start_here: "Start Here",
    today: "Today",
    trust: "Trust",
  };
  return labels[surfaceId];
}

function productizedSurfacePosture(
  binding: FounderLoopProductProofReadModel["productized_surface_bindings"][number],
): FounderLoopSpineItem["posture"] {
  const text = `${binding.status} ${binding.product_posture}`.toLowerCase();
  if (text.includes("blocked") || text.includes("planned")) {
    return "blocked";
  }
  if (text.includes("receipt") || text.includes("proof")) {
    return "receipt-backed";
  }
  if (text.includes("queue") || text.includes("authority")) {
    return "authority-gated";
  }
  if (text.includes("entrypoint") || text.includes("home")) {
    return "partial";
  }
  return "implemented";
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
  const firstBriefing = today.briefing_items[0];
  const evidenceEvents =
    evidence?.event_count ??
    sections.evidence_timeline_count ??
    (today.evidence_timeline ?? []).length;

  return [
    {
      surface: "Today",
      label: "Today",
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
      surface: "Briefing",
      label: "Briefing",
      path: "/briefing",
      status: today.daily_loop_summary?.home_surface ?? "storage-backed",
      posture: "partial",
      summary:
        firstBriefing?.safe_summary ??
        "Morning Briefing starts the local loop with bounded preview refs.",
      nextSafeAction:
        firstBriefing?.next_safe_action ??
        today.daily_loop_summary?.next_safe_action ??
        "Read safe briefing refs before opening Today or Action Inbox.",
      refs: [
        firstBriefing?.briefing_ref,
        today.daily_loop_summary?.loop_ref,
        today.evidence_history_contract_ref,
      ].filter(isPresent),
    },
    {
      surface: "Inbox",
      label: "Source Inbox",
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
      label: "Plans",
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
      label: "Action Inbox",
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
      summary: `${actionItems.length} action refs; ${localTaskEligible} eligible local-task create lane; ${localTaskReceipts} local task receipts.`,
      nextSafeAction:
        actionItems.find((item) => item.local_task_commit_next_safe_action)
          ?.local_task_commit_next_safe_action ??
        "Record only supported receipts or the exact local-task commit receipt.",
      refs: [
        inbox?.route_ref,
        inbox?.decision_state_contract_ref,
        actionItems.find((item) => item.local_task_commit_contract_ref)
          ?.local_task_commit_contract_ref,
      ].filter(isPresent),
    },
    {
      surface: "Memory",
      label: "Memory",
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
      label: "Evidence",
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
      label: "Settings",
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

function summarizeLocalTaskCapability(items: FounderLoopActionItem[]): string {
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
    return `${eligible} approved local-task create capability`;
  }
  return "Local task capability blocked unless exact approval exists";
}

function isPresent<T>(value: T | null | undefined): value is T {
  return Boolean(value);
}

type DailyLoopCommandItem = {
  commandRef: string;
  question: string;
  surface: string;
  href: string;
  status: string;
  summary: string;
  whyShown: string;
  whatThisAffects: string;
  nextSafeAction: string;
  refs: string[];
  posture: "today" | "review" | "waiting" | "influence" | "blocked";
};

function buildDailyLoopCommandItems(
  today: FounderLoopTodaySummary,
): DailyLoopCommandItem[] {
  const loopReadModel = today.today_loop_read_model;
  if (!loopReadModel) {
    const missingSummary =
      "Today loop digest is missing; Control Center will not infer decision groups from fallback state.";
    const missingNextAction =
      "Wait for the backend-owned Today loop read model before treating refs as decision groups.";
    return [
      {
        commandRef: "daily-loop-command:what-matters-today",
        question: "What matters today",
        surface: "Today",
        href: "/today",
        status: "backend digest missing",
        summary: missingSummary,
        whyShown:
          "The Product Loop 003 digest is required before Today can order priority refs.",
        whatThisAffects: "Today, Briefing, Plans, Action Inbox",
        nextSafeAction: missingNextAction,
        refs: [today.product_spine_contract_ref].filter(isPresent),
        posture: "today",
      },
      {
        commandRef: "daily-loop-command:needs-review",
        question: "What needs review",
        surface: "Action Inbox",
        href: "/actions",
        status: "backend digest missing",
        summary: missingSummary,
        whyShown:
          "Control Center needs backend-owned review refs before showing a decision group.",
        whatThisAffects: "Actions, Plans, Evidence, Memory-derived follow-ups",
        nextSafeAction: missingNextAction,
        refs: [],
        posture: "review",
      },
      {
        commandRef: "daily-loop-command:changed",
        question: "What changed",
        surface: "Evidence",
        href: "/evidence",
        status: "backend digest missing",
        summary: missingSummary,
        whyShown:
          "Changed refs must come from the backend-owned Today loop read model.",
        whatThisAffects: "Evidence, Today, Weekly Review, Action Inbox",
        nextSafeAction: missingNextAction,
        refs: [],
        posture: "waiting",
      },
      {
        commandRef: "daily-loop-command:memory-evidence-influence",
        question: "What memory/evidence is influencing the loop",
        surface: "Memory and Evidence",
        href: "/memory",
        status: "backend digest missing",
        summary: missingSummary,
        whyShown:
          "Influence refs remain review-only and need backend grouping before display as loop posture.",
        whatThisAffects: "Memory, Evidence, Today, Actions, Briefing",
        nextSafeAction: missingNextAction,
        refs: [],
        posture: "influence",
      },
      {
        commandRef: "daily-loop-command:blocked-unsafe",
        question: "What is blocked or unsafe",
        surface: "Blocked states",
        href: "/evidence",
        status: "backend digest missing",
        summary: missingSummary,
        whyShown:
          "Blocked posture must be backend-owned so fallback refs cannot imply authority.",
        whatThisAffects: "All Founder Loop surfaces",
        nextSafeAction: missingNextAction,
        refs: [],
        posture: "blocked",
      },
    ];
  }
  const needsReviewRefs = loopReadModel.needs_review_refs;
  const changedRefs = loopReadModel.what_changed_refs;
  const blockedNowRefs = loopReadModel.blocked_now_refs;
  const whatMattersNowRefs = loopReadModel.what_matters_now_refs;
  const evidenceCount =
    today.sections.evidence_timeline_count ?? today.evidence_timeline.length;
  const memoryInfluence = today.memory_why_shown_items?.[0];
  const firstBriefing = today.briefing_items[0];
  const fallbackNextAction =
    today.next_safe_actions[0]?.safe_summary ??
    "Review the daily loop before opening deeper surfaces.";

  return [
    {
      commandRef: "daily-loop-command:what-matters-today",
      question: "What matters today",
      surface: "Today",
      href: "/today",
      status: today.daily_loop_summary?.status ?? today.status,
      summary:
        today.daily_loop_summary?.today_plan_summary ??
        firstBriefing?.safe_summary ??
        `${today.sections.plan_count} plans and ${today.sections.action_inbox_count} actions need local review.`,
      whyShown:
        "Today is the operator home because it binds priorities, blockers, follow-ups, plan/action state, memory, briefing, and next safe actions.",
      whatThisAffects: "Today, Briefing, Plans, Action Inbox",
      nextSafeAction: today.daily_loop_summary?.next_safe_action ?? fallbackNextAction,
      refs: [
        today.daily_loop_summary?.loop_ref,
        today.product_spine_contract_ref,
        ...whatMattersNowRefs.slice(0, 3),
      ].filter(isPresent),
      posture: "today",
    },
    {
      commandRef: "daily-loop-command:needs-review",
      question: "What needs review",
      surface: "Action Inbox",
      href: "/actions",
      status: `${needsReviewRefs.length} backend review refs`,
      summary:
        needsReviewRefs.length > 0
          ? "Backend-owned Today loop refs need review before any supported receipt."
          : "Review work is currently proposal-only, blocked, or already receipt-backed.",
      whyShown:
        "Action Inbox is shown when items require a recorded decision receipt, review posture, or explicit blocked-state inspection.",
      whatThisAffects: "Actions, Plans, Evidence, Memory-derived follow-ups",
      nextSafeAction:
        loopReadModel.next_safe_action ??
        "Record only supported receipts; proposal-only artifacts stay review-only.",
      refs: needsReviewRefs.slice(0, 4),
      posture: "review",
    },
    {
      commandRef: "daily-loop-command:changed",
      question: "What changed",
      surface: "Evidence",
      href: "/evidence",
      status: `${changedRefs.length} changed refs`,
      summary:
        changedRefs.length > 0
          ? "Backend-owned changed refs are visible for review before carry-forward."
          : "Evidence, receipts, and local review refs show what changed in the loop.",
      whyShown:
        "Changed refs come from backend-owned receipts, evidence history, and safe review posture.",
      whatThisAffects: "Evidence, Today, Weekly Review, Action Inbox",
      nextSafeAction:
        today.weekly_review_narrative?.next_safe_action ??
        "Inspect receipt and evidence refs before carrying changes forward.",
      refs: changedRefs.slice(0, 4),
      posture: "waiting",
    },
    {
      commandRef: "daily-loop-command:memory-evidence-influence",
      question: "What memory/evidence is influencing the loop",
      surface: "Memory and Evidence",
      href: "/memory",
      status: `${today.memory_to_loop_item_count} memory links, ${evidenceCount} evidence events`,
      summary:
        memoryInfluence?.why_shown ??
        `${today.accepted_recall_refs.length} accepted recall refs and ${evidenceCount} safe-ref evidence events are visible.`,
      whyShown:
        "Memory and Evidence are shown as influence and proof, not as truth authority or hidden context.",
      whatThisAffects: "Memory, Evidence, Today, Actions, Briefing",
      nextSafeAction:
        today.weekly_review_narrative?.next_safe_action ??
        "Inspect why-shown refs and receipt/evidence refs before relying on recall.",
      refs: [
        memoryInfluence?.memory_ref,
        ...today.accepted_recall_refs.slice(0, 2),
        today.evidence_history_contract_ref,
      ].filter(isPresent),
      posture: "influence",
    },
    {
      commandRef: "daily-loop-command:blocked-unsafe",
      question: "What is blocked or unsafe",
      surface: "Blocked states",
      href: "/evidence",
      status: `${blockedNowRefs.length} backend blocker refs`,
      summary:
        today.blocker_refs[0] ??
        today.blocked_states[0] ??
        "Hidden execution, connector writes, context injection, shell, browser, provider/model use, public beta, and production authority all remain blocked.",
      whyShown:
        "Blocked states are shown to prevent proposal-only refs, memory recall, or approval identifiers from becoming authority.",
      whatThisAffects: "All Founder Loop surfaces",
      nextSafeAction:
        "Keep unsafe or insufficiently scoped work blocked until an exact milestone grants authority.",
      refs: blockedNowRefs.slice(0, 6),
      posture: "blocked",
    },
  ];
}

function DailyLoopCommandDeck({
  actionReadModelAuthoritative,
  today,
}: {
  actionReadModelAuthoritative: boolean;
  today: FounderLoopTodaySummary;
}) {
  const commandItems = buildDailyLoopCommandItems(today);
  return (
    <section
      aria-label="Daily loop command deck"
      className="daily-loop-command-deck"
    >
      <div className="daily-loop-command-header">
        <div>
          <p className="eyebrow">Daily loop order</p>
          <h3>Scan: Today, Review, Changed, Influence, Blocked</h3>
          <p>
            This deck is presentation-only. It summarizes backend read-model
            refs and keeps proposal-only, memory, evidence, and approval
            posture visibly bounded.
          </p>
        </div>
        <span className="status-pill compact">
          {actionReadModelAuthoritative
            ? "backend read model"
            : "non-authoritative fallback"}
        </span>
      </div>
      <div className="daily-loop-command-grid">
        {commandItems.map((item, index) => (
          <article
            className={`daily-loop-command-card ${item.posture}`}
            key={item.commandRef}
          >
            <div className="daily-loop-command-card-heading">
              <span>{index + 1}</span>
              <div>
                <h4>{item.question}</h4>
                <p>{item.status}</p>
              </div>
            </div>
            <p>{item.summary}</p>
            <dl className="detail-list compact">
              <DetailTerm label="Surface" value={item.surface} />
              <DetailTerm label="Why shown" value={item.whyShown} />
              <DetailTerm label="What this affects" value={item.whatThisAffects} />
              <DetailTerm label="Next safe action" value={item.nextSafeAction} />
            </dl>
            <RefListWithFallback
              emptyLabel="Loop refs: none available"
              refs={item.refs}
            />
            <a className="text-link" href={item.href}>
              Open {item.surface}
            </a>
          </article>
        ))}
      </div>
      <div className="loop-authority-strip">
        <span>Proposal-only refs stay review-only</span>
        <span>No apply/use/execute control for proposals</span>
        <span>Memory recall is influence, not truth authority</span>
        <span>Evidence is safe-ref proof, not hidden context</span>
      </div>
    </section>
  );
}

function ActionInboxOperatorOverview({
  actionGroups,
  inbox,
}: {
  actionGroups: ActionLaneGroup[];
  inbox: FounderLoopActionsInbox;
}) {
  const countFor = (groupId: FounderLoopActionGroupId) =>
    actionGroups.find((group) => group.summary.group_id === groupId)?.summary.count ??
    0;
  return (
    <section
      aria-label="Action Inbox operator summary"
      className="operator-loop-summary"
    >
      <div className="operator-loop-summary-main">
        <p className="eyebrow">Review order</p>
        <h3>Decide what can receive a receipt, keep everything else bounded</h3>
        <p>
          The inbox is grouped by backend read-model posture. Ready items can
          record supported receipts, approved local-task create lanes stay
          exact-scoped, and proposal-only artifacts expose no apply/use/execute
          control.
        </p>
      </div>
      <div className="operator-loop-summary-grid">
        <Metric label="ready for decision" value={countFor("ready_for_decision")} />
        <Metric label="local-task create lane" value={countFor("approved_local_task_lane")} />
        <Metric label="proposal-only" value={countFor("proposal_only_no_execution_path")} />
        <Metric label="blocked" value={countFor("blocked_by_authority")} />
      </div>
      <dl className="detail-list compact">
        <DetailTerm
          label="Fallback posture"
          value={
            inbox.storage_ref.includes("mock")
              ? "non-authoritative fallback"
              : "backend-owned read model"
          }
        />
        <DetailTerm
          label="Review receipts"
          value={
            inbox.decision_receipts_required
              ? "required for supported decisions"
              : "not available"
          }
        />
        <DetailTerm
          label="Action execution"
          value={inbox.action_execution_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Proposal boundary"
          value="proposal-only refs stay review-only"
        />
      </dl>
    </section>
  );
}

function RuntimeActionInboxBridgePanel({
  contractRef,
  readModel: initialReadModel,
}: {
  contractRef?: string;
  readModel?: FounderLoopRuntimeActionInboxBridgeReadModel;
}) {
  const [readModel, setDisplayedReadModel] = useState(initialReadModel);
  useEffect(() => {
    setDisplayedReadModel(initialReadModel);
  }, [initialReadModel]);
  if (!readModel) {
    return (
      <article
        className="status-card"
        aria-label="Runtime Action Inbox execution bridge"
      >
        <div className="status-card-header">
          <h3>Runtime execution bridge</h3>
          <span>backend read model missing</span>
        </div>
        <p>
          Governed runtime execution posture is unavailable. The UI will not
          infer approvals, command scope, receipts, or execution state from
          local presentation data.
        </p>
        <dl className="detail-list">
          <DetailTerm label="Action execution" value="blocked" />
          <DetailTerm label="Arbitrary commands" value="blocked" />
          <DetailTerm label="Provider/model calls" value="blocked" />
        </dl>
      </article>
    );
  }

  return (
    <article
      className="status-card"
      aria-label="Runtime Action Inbox execution bridge"
    >
      <div className="status-card-header">
        <h3>Runtime execution bridge</h3>
        <span>backend-owned</span>
      </div>
      <p>{readModel.operator_summary}</p>
      <div className="operator-loop-summary-grid">
        <Metric label="envelopes" value={readModel.item_count} />
        <Metric label="pending" value={readModel.pending_approval_count} />
        <Metric
          label="approved"
          value={readModel.approved_pending_execution_count}
        />
        <Metric label="receipts" value={readModel.receipt_recorded_count} />
        <Metric label="blocked" value={readModel.blocked_count} />
      </div>
      <dl className="detail-list">
        <DetailTerm label="Contract" value={contractRef ?? readModel.contract_ref} />
        <DetailTerm label="Status" value={readModel.status} />
        <DetailTerm label="Route" value={readModel.route_ref} />
        <DetailTerm label="CLI" value={readModel.cli_ref} />
        <DetailTerm
          label="Parity loop API"
          value={readModel.runtime_parity_loop_api_ref}
        />
        <DetailTerm
          label="Parity loop CLI"
          value={readModel.runtime_parity_loop_cli_ref}
        />
        <DetailTerm
          label="Parity loop status"
          value={readModel.runtime_parity_loop_status}
        />
        <DetailTerm label="Runtime profile" value={readModel.runtime_profile_status} />
        <DetailTerm label="Local model" value={readModel.local_model_readiness} />
        <DetailTerm label="Command runtime" value={readModel.command_runtime_readiness} />
        <DetailTerm
          label="Safe-disable"
          value={readModel.safe_disable_active ? "active" : "inactive"}
        />
        <DetailTerm label="Safe-disable ref" value={readModel.safe_disable_ref} />
        <DetailTerm
          label="Exact governed controls"
          value={
            readModel.control_center_exact_runtime_mutations_enabled
              ? "enabled"
              : "blocked"
          }
        />
        <DetailTerm
          label="Broad action execution"
          value={readModel.action_execution_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Arbitrary commands"
          value={
            readModel.arbitrary_command_execution_enabled ? "enabled" : "blocked"
          }
        />
        <DetailTerm
          label="Browser/provider/connector"
          value={
            readModel.browser_execution_enabled ||
            readModel.provider_model_call_enabled ||
            readModel.connector_write_enabled
              ? "enabled"
              : "blocked"
          }
        />
        <DetailTerm
          label="Production authority"
          value={readModel.production_authority_enabled ? "enabled" : "blocked"}
        />
      </dl>
      <p className="muted">{readModel.next_safe_action}</p>
      <div className="operator-loop-summary-grid">
        <Metric label="timeline" value={readModel.evidence_timeline.length} />
        <Metric
          label="pending refs"
          value={readModel.pending_runtime_approval_refs.length}
        />
        <Metric
          label="results"
          value={readModel.execution_result_refs.length}
        />
        <Metric
          label="hash-integrity evidence"
          value={readModel.signed_evidence_refs.length}
        />
      </div>
      <dl className="detail-list">
        <DetailTerm label="Status CLI" value={readModel.status_cli_ref} />
        <DetailTerm label="Capabilities CLI" value={readModel.capabilities_cli_ref} />
        <DetailTerm label="Invocations CLI" value={readModel.invocations_cli_ref} />
        <DetailTerm label="Receipts CLI" value={readModel.receipts_cli_ref} />
        <DetailTerm label="Evidence CLI" value={readModel.signed_evidence_cli_ref} />
        <DetailTerm
          label="Verifier CLI"
          value={readModel.signed_evidence_verifier_cli_ref}
        />
        <DetailTerm label="Safe-disable CLI" value={readModel.safe_disable_cli_ref} />
      </dl>
      <p className="muted">{readModel.safe_disable_summary}</p>
      <GovernedRuntimeControlPanel
        onReadModel={setDisplayedReadModel}
        readModel={readModel}
      />
      <div className="review-grid">
        {readModel.items.map((item) => (
          <article className="review-card" key={item.invocation_ref}>
            <div className="review-card-heading">
              <h4>{item.command_intent ?? item.adapter_id}</h4>
              <span>{item.status}</span>
            </div>
            <p>{item.safe_summary}</p>
            <dl className="detail-list">
              <DetailTerm label="Invocation" value={item.invocation_ref} />
              <DetailTerm label="Envelope" value={item.action_envelope_ref} />
              <DetailTerm label="Adapter" value={item.adapter_id} />
              <DetailTerm label="Authority" value={item.requested_authority} />
              <DetailTerm label="Exact scope" value={item.exact_scope_ref} />
              <DetailTerm
                label="Approval validated"
                value={item.approval_validated ? "yes" : "no"}
              />
              <DetailTerm
                label="Authority scope"
                value={
                  item.authority_scope_required
                    ? item.authority_scope_allowed
                      ? "allowed by active lease"
                      : "requires active lease"
                    : "not required"
                }
              />
              <DetailTerm
                label="Authority outcome"
                value={String(item.authority_decision_outcome ?? "missing")}
              />
              <DetailTerm
                label="Authority lease"
                value={item.authority_lease_ref ?? "not active"}
              />
              <DetailTerm
                label="Authority domain"
                value={item.authority_domain_ref ?? "missing"}
              />
              <DetailTerm
                label="Authority capability"
                value={item.authority_capability_ref ?? "missing"}
              />
              <DetailTerm
                label="Required mode"
                value={item.authority_required_mode_ref ?? "missing"}
              />
              <DetailTerm
                label="Authority audit"
                value={item.authority_audit_ref ?? "missing"}
              />
              <DetailTerm
                label="Authority receipt"
                value={item.authority_policy_receipt_ref ?? "missing"}
              />
              <DetailTerm
                label="Execution performed"
                value={item.execution_performed ? "yes" : "no"}
              />
              <DetailTerm label="Receipt status" value={item.receipt_status} />
              <DetailTerm
                label="Hash-integrity evidence"
                value={item.signed_evidence_verification_status}
              />
              <DetailTerm
                label="Exit"
                value={item.exit_code === null || item.exit_code === undefined ? "none" : String(item.exit_code)}
              />
              <DetailTerm
                label="Timed out"
                value={item.timed_out ? "yes" : "no"}
              />
              <DetailTerm
                label="Output persisted"
                value={item.command_output_persisted ? "yes" : "no"}
              />
              <DetailTerm label="Rollback" value={item.rollback_ref} />
              <DetailTerm label="Safe disable" value={item.safe_disable_ref} />
              <DetailTerm
                label="Safe-disable posture"
                value={item.safe_disable_posture_ref}
              />
            </dl>
            <RefListWithFallback
              emptyLabel="Receipts: none"
              refs={item.receipt_refs}
            />
            <RefListWithFallback
              emptyLabel="Evidence refs: none"
              refs={item.evidence_refs}
            />
            <RefListWithFallback
              emptyLabel="Execution result refs: none"
              refs={
                item.execution_result_ref ? [item.execution_result_ref] : []
              }
            />
            <RefListWithFallback
              emptyLabel="Hash-integrity evidence refs: none"
              refs={
                item.signed_evidence_ref ? [item.signed_evidence_ref] : []
              }
            />
            <RefListWithFallback
              emptyLabel="Signed verifier refs: none"
              refs={
                item.signed_evidence_verifier_ref
                  ? [item.signed_evidence_verifier_ref]
                  : []
              }
            />
            <RefListWithFallback
              emptyLabel="Approval proof refs: none"
              refs={[
                item.approval_decision_ref,
                item.approval_validation_ref,
              ].filter((ref): ref is string => typeof ref === "string")}
            />
            <RefListWithFallback
              emptyLabel="Authority reason refs: none"
              refs={item.authority_reason_refs}
            />
            {item.authority_operator_message ? (
              <p className="muted">{item.authority_operator_message}</p>
            ) : null}
            <RefListWithFallback
              emptyLabel="Blocked reason refs: none"
              refs={item.blocked_reason_refs}
            />
          </article>
        ))}
      </div>
      <div className="review-grid">
        {readModel.evidence_timeline.map((event) => (
          <article className="review-card" key={event.event_ref}>
            <div className="review-card-heading">
              <h4>{event.event_kind}</h4>
              <span>{event.invocation_ref}</span>
            </div>
            <p>{event.safe_summary}</p>
            <dl className="detail-list">
              <DetailTerm label="Event" value={event.event_ref} />
              <DetailTerm
                label="Receipt"
                value={event.receipt_ref ?? "not recorded"}
              />
              <DetailTerm
                label="Policy"
                value={event.policy_decision_ref ?? "not recorded"}
              />
              <DetailTerm
                label="Envelope"
                value={event.action_envelope_ref ?? "not recorded"}
              />
            </dl>
            <RefListWithFallback
              emptyLabel="Timeline evidence refs: none"
              refs={event.evidence_refs}
            />
          </article>
        ))}
      </div>
      <RefListWithFallback
        emptyLabel="Runtime bridge receipts: none"
        refs={readModel.receipt_refs}
      />
      <RefListWithFallback
        emptyLabel="Runtime bridge approval envelopes: none"
        refs={readModel.approval_envelope_refs}
      />
      <RefListWithFallback
        emptyLabel="Runtime bridge pending approvals: none"
        refs={readModel.pending_runtime_approval_refs}
      />
      <RefListWithFallback
        emptyLabel="Runtime bridge execution results: none"
        refs={readModel.execution_result_refs}
      />
      <RefListWithFallback
        emptyLabel="Runtime bridge hash-integrity evidence refs: none"
        refs={readModel.signed_evidence_refs}
      />
      <RefListWithFallback
        emptyLabel="Runtime parity loop stage refs: none"
        refs={readModel.runtime_parity_loop_stage_refs}
      />
      <RefListWithFallback
        emptyLabel="Runtime bridge evidence refs: none"
        refs={readModel.evidence_refs}
      />
      <RefListWithFallback
        emptyLabel="Blocked authority refs: none"
        refs={readModel.blocked_authority_refs}
      />
    </article>
  );
}

const governedRuntimeCommandIntents: GovernedRuntimeCommandIntent[] = [
  "git_status",
  "focused_pytest",
  "repo_verifier",
  "frontend_check",
  "repo_doctor",
];

function governedRuntimeCommandIntent(
  value: string | null | undefined,
): GovernedRuntimeCommandIntent | null {
  return governedRuntimeCommandIntents.includes(
    value as GovernedRuntimeCommandIntent,
  )
    ? (value as GovernedRuntimeCommandIntent)
    : null;
}

function GovernedRuntimeControlPanel({
  onReadModel,
  readModel,
}: {
  onReadModel: (readModel: FounderLoopRuntimeActionInboxBridgeReadModel) => void;
  readModel: FounderLoopRuntimeActionInboxBridgeReadModel;
}) {
  const mutationBinding = useBackendTruthMutationBinding();
  const [localModelBaseUrl, setLocalModelBaseUrl] = useState(
    "http://127.0.0.1:8080",
  );
  const [localModelRef, setLocalModelRef] = useState("uaa-local-runtime");
  const [localModelPrompt, setLocalModelPrompt] = useState(
    "Summarize the current governed runtime posture as an untrusted proposal.",
  );
  const [commandIntent, setCommandIntent] =
    useState<GovernedRuntimeCommandIntent>("git_status");
  const [state, setState] = useState<{
    status: "idle" | "pending" | "recorded" | "blocked" | "failed";
    operation?: string;
    message?: string;
    invocationRef?: string;
    receiptRef?: string;
  }>({ status: "idle" });
  const pending = state.status === "pending";
  const exactControlsEnabled =
    readModel.control_center_exact_runtime_mutations_enabled &&
    !readModel.control_center_mints_authority &&
    mutationBinding !== null;

  async function runMutation(
    operation: string,
    mutation: () => Promise<{
      status: "recorded" | "blocked";
      safeMessage: string;
      invocationRef?: string;
      receiptRef?: string;
    }>,
  ) {
    setState({ status: "pending", operation });
    try {
      const result = await mutation();
      setState({
        status: result.status,
        operation,
        message: result.safeMessage,
        invocationRef: result.invocationRef,
        receiptRef: result.receiptRef,
      });
      const refreshedInbox = await fetchFounderActionsInbox(mutationBinding);
      const refreshedBridge =
        refreshedInbox.runtime_action_inbox_bridge_read_model;
      if (refreshedBridge) {
        onReadModel(refreshedBridge);
      }
    } catch (error) {
      setState({
        status: "failed",
        operation,
        message:
          error instanceof Error
            ? error.message
            : "The governed runtime request failed closed.",
      });
    }
  }

  function requestLocalModelProposal() {
    return runMutation("local model proposal", () =>
      requestGovernedRuntimeLocalModelProposal(
        {
          base_url: localModelBaseUrl.trim(),
          model_ref: localModelRef.trim(),
          messages: [{ role: "user", content: localModelPrompt.trim() }],
          requested_profile: "local-runtime",
          safe_summary:
            "Use the configured loopback local model as an untrusted proposal.",
          allow_bounded_preview: false,
          max_preview_chars: 0,
          timeout_seconds: 10,
          max_response_bytes: 16000,
          metadata_refs: [
            "metadata-ref:control-center-governed-runtime-local-model",
          ],
        },
        mutationBinding,
      ),
    );
  }

  function requestCommand() {
    return runMutation(`command ${commandIntent}`, () =>
      requestGovernedRuntimeCommand(
        {
          intent: commandIntent,
          requested_profile:
            commandIntent === "git_status" ? "local-runtime" : "operator-approved",
          target_refs: [
            `target-ref:control-center-governed-runtime:${commandIntent}`,
          ],
          safe_summary:
            commandIntent === "git_status"
              ? "Inspect the approved repository with the exact read-only git status lane."
              : "Prepare one exact governed utility command for approval-bound execution.",
          timeout_seconds: commandIntent === "git_status" ? 10 : 30,
          output_byte_limit: 4096,
          metadata_refs: [
            "metadata-ref:control-center-governed-runtime-command",
          ],
        },
        mutationBinding,
      ),
    );
  }

  return (
    <section
      aria-label="Governed runtime operator controls"
      className="decision-controls"
    >
      <div className="status-card-header">
        <div>
          <h4>Exact governed controls</h4>
          <p className="muted">
            Backend APIs own every mutation, policy check, approval envelope,
            execution receipt, and safe-disable transition. These controls do
            not mint an AuthorityLease or broaden the allowlist.
          </p>
        </div>
        <span>{state.status}</span>
      </div>
      <label className="field-label">
        Loopback model endpoint
        <input
          className="text-input"
          disabled={pending || readModel.safe_disable_active}
          onChange={(event) => setLocalModelBaseUrl(event.target.value)}
          spellCheck={false}
          value={localModelBaseUrl}
        />
      </label>
      <label className="field-label">
        Local model ref
        <input
          className="text-input"
          disabled={pending || readModel.safe_disable_active}
          onChange={(event) => setLocalModelRef(event.target.value)}
          spellCheck={false}
          value={localModelRef}
        />
      </label>
      <label className="field-label">
        Transient bounded prompt
        <textarea
          className="text-input"
          disabled={pending || readModel.safe_disable_active}
          maxLength={16000}
          onChange={(event) => setLocalModelPrompt(event.target.value)}
          rows={3}
          value={localModelPrompt}
        />
      </label>
      <button
        className="secondary-button"
        disabled={
          pending ||
          readModel.safe_disable_active ||
          !exactControlsEnabled ||
          !readModel.local_model_call_control_enabled ||
          !localModelBaseUrl.trim() ||
          !localModelRef.trim() ||
          !localModelPrompt.trim()
        }
        onClick={() => void requestLocalModelProposal()}
        type="button"
      >
        Request local model proposal
      </button>
      <label className="field-label">
        Exact command lane
        <select
          className="text-input"
          disabled={pending || readModel.safe_disable_active}
          onChange={(event) =>
            setCommandIntent(event.target.value as GovernedRuntimeCommandIntent)
          }
          value={commandIntent}
        >
          {governedRuntimeCommandIntents.map((intent) => (
            <option key={intent} value={intent}>
              {intent}
            </option>
          ))}
        </select>
      </label>
      <button
        className="secondary-button"
        disabled={
          pending ||
          readModel.safe_disable_active ||
          !exactControlsEnabled ||
          !readModel.command_request_control_enabled
        }
        onClick={() => void requestCommand()}
        type="button"
      >
        Prepare or run exact command lane
      </button>
      <div className="review-grid">
        {readModel.items.map((item) => {
          const exactCommandIntent = governedRuntimeCommandIntent(
            item.command_intent,
          );
          const exactEnvelope = {
            approval_ref: item.approval_ref,
            action_envelope_ref: item.action_envelope_ref,
            exact_scope_ref: item.exact_scope_ref,
            payload_fingerprint_ref: item.payload_fingerprint_ref,
            policy_decision_ref: item.policy_decision_ref,
            adapter_id: item.adapter_id,
            command_intent: exactCommandIntent,
            rollback_ref: item.rollback_ref,
            safe_disable_ref: item.safe_disable_ref,
            safe_disable_posture_ref: item.safe_disable_posture_ref,
          };
          return (
            <article className="review-card" key={`controls-${item.invocation_ref}`}>
              <div className="review-card-heading">
                <h5>{item.command_intent ?? item.adapter_id}</h5>
                <span>{item.status}</span>
              </div>
              <p className="muted">{item.exact_scope_ref}</p>
              <div className="decision-button-row">
                {item.status === "pending_approval" ? (
                  <>
                    <button
                      className="secondary-button"
                      disabled={
                        pending ||
                        readModel.safe_disable_active ||
                        !readModel.approval_decision_control_enabled
                      }
                      onClick={() =>
                        void runMutation("approve exact envelope", () =>
                          decideGovernedRuntimeInvocation(
                            item.invocation_ref,
                            "approve",
                            exactEnvelope,
                            mutationBinding,
                          ),
                        )
                      }
                      type="button"
                    >
                      Approve exact envelope
                    </button>
                    <button
                      className="secondary-button"
                      disabled={pending || !readModel.approval_decision_control_enabled}
                      onClick={() =>
                        void runMutation("deny exact envelope", () =>
                          decideGovernedRuntimeInvocation(
                            item.invocation_ref,
                            "deny",
                            exactEnvelope,
                            mutationBinding,
                          ),
                        )
                      }
                      type="button"
                    >
                      Deny exact envelope
                    </button>
                  </>
                ) : null}
                {item.status === "approved_pending_execution" ? (
                  <button
                    className="secondary-button"
                    disabled={
                      pending ||
                      readModel.safe_disable_active ||
                      !readModel.exact_envelope_execution_control_enabled
                    }
                    onClick={() =>
                      void runMutation("execute exact envelope", () =>
                        executeGovernedRuntimeInvocation(
                          item.invocation_ref,
                          exactEnvelope,
                          mutationBinding,
                        ),
                      )
                    }
                    type="button"
                  >
                    Execute exact envelope
                  </button>
                ) : null}
              </div>
            </article>
          );
        })}
      </div>
      <button
        className="secondary-button"
        disabled={
          pending ||
          readModel.safe_disable_active ||
          !exactControlsEnabled ||
          !readModel.safe_disable_control_enabled
        }
        onClick={() =>
          void runMutation("safe-disable", () =>
            safeDisableGovernedRuntime(mutationBinding),
          )
        }
        type="button"
      >
        Safe-disable governed runtime
      </button>
      {state.message ? <p className="muted">{state.message}</p> : null}
      {state.invocationRef || state.receiptRef ? (
        <dl className="detail-list">
          <DetailTerm
            label="Invocation"
            value={state.invocationRef ?? "not returned"}
          />
          <DetailTerm label="Receipt" value={state.receiptRef ?? "pending"} />
        </dl>
      ) : null}
    </section>
  );
}

function ActionToolCodeLaneCatalogPanel({
  contractRef,
  readModel,
}: {
  contractRef?: string;
  readModel?: ActionToolCodeLaneCatalogReadModel;
}) {
  if (!readModel) {
    return (
      <article className="status-card" aria-label="Action tool code catalog">
        <div className="status-card-header">
          <h3>Action/tool/code catalog</h3>
          <span>backend read model missing</span>
        </div>
        <p>
          Action, tool, runtime, and code-lane posture is unavailable. The UI
          will not infer callable tools, shell access, code apply authority, or
          provider execution from local presentation state.
        </p>
        <dl className="detail-list">
          <DetailTerm label="Generic tools" value="blocked" />
          <DetailTerm label="Unrestricted shell" value="blocked" />
          <DetailTerm
            label="Code apply"
            value="requires files/write AuthorityLease scope"
          />
          <DetailTerm label="Provider/browser/connector" value="blocked" />
        </dl>
      </article>
    );
  }

  const exactAuthorityCapabilityCount =
    readModel.exact_local_authority_capability_count +
    readModel.exact_runtime_authority_capability_count;
  const blockedAuthorityEnabled =
    readModel.generic_tool_execution_enabled ||
    readModel.unrestricted_shell_execution_enabled ||
    readModel.browser_automation_enabled ||
    readModel.connector_write_enabled ||
    readModel.plugin_runtime_import_enabled ||
    readModel.remote_execution_enabled ||
    readModel.provider_model_call_enabled ||
    readModel.background_autonomy_enabled ||
    readModel.production_authority_enabled;

  return (
    <article className="status-card" aria-label="Action tool code catalog">
      <div className="status-card-header">
        <h3>Action/tool/code catalog</h3>
        <span>{readModel.backend_owned ? "backend-owned" : "non-authoritative"}</span>
      </div>
      <p>{readModel.operator_summary}</p>
      <div className="operator-loop-summary-grid">
        <Metric label="capabilities" value={readModel.entry_count} />
        <Metric label="preview" value={readModel.preview_only_count} />
        <Metric label="exact" value={exactAuthorityCapabilityCount} />
        <Metric label="proposals" value={readModel.proposal_only_count} />
        <Metric label="blocked" value={readModel.blocked_count} />
      </div>
      <dl className="detail-list">
        <DetailTerm label="Contract" value={contractRef ?? readModel.contract_ref} />
        <DetailTerm label="Catalog" value={readModel.catalog_ref} />
        <DetailTerm label="Status" value={readModel.status} />
        <DetailTerm label="Route" value={readModel.route_ref} />
        <DetailTerm label="CLI" value={readModel.cli_ref} />
        <DetailTerm
          label="Presentation boundary"
          value={
            readModel.control_center_presentation_only
              ? "Control Center displays only"
              : "unsafe"
          }
        />
        <DetailTerm
          label="Raw content"
          value={readModel.raw_content_included ? "included" : "omitted"}
        />
        <DetailTerm
          label="Broad authority"
          value={blockedAuthorityEnabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Generic tool execution"
          value={readModel.generic_tool_execution_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Shell/provider/browser/connector"
          value={
            readModel.unrestricted_shell_execution_enabled ||
            readModel.provider_model_call_enabled ||
            readModel.browser_automation_enabled ||
            readModel.connector_write_enabled
              ? "enabled"
              : "blocked"
          }
        />
      </dl>
      <p className="muted">{readModel.next_safe_action}</p>
      <div className="review-grid">
        {readModel.entries.map((entry) => (
          <ActionToolCodeCapabilityEntryCard entry={entry} key={entry.lane_ref} />
        ))}
      </div>
      <div className="review-grid">
        {readModel.unblock_prompts.map((prompt) => (
          <article className="review-card" key={prompt.prompt_ref}>
            <div className="review-card-heading">
              <h4>{prompt.title}</h4>
              <span>authority capability prompt</span>
            </div>
            <p>{prompt.copy_ready_prompt}</p>
            <dl className="detail-list">
              <DetailTerm label="Prompt" value={prompt.prompt_ref} />
              <DetailTerm label="Target" value={prompt.target_capability_ref} />
            </dl>
            <RefListWithFallback
              emptyLabel="Blocked authority refs: none"
              refs={prompt.blocked_authority_refs}
            />
          </article>
        ))}
      </div>
      <RefListWithFallback
        emptyLabel="Catalog blocked authority refs: none"
        refs={readModel.blocked_authority_refs}
      />
    </article>
  );
}

function ActionToolCodeCapabilityEntryCard({
  entry,
}: {
  entry: ActionToolCodeLaneEntry;
}) {
  const broadAuthorityEnabled =
    entry.generic_tool_execution_enabled ||
    entry.unrestricted_shell_execution_enabled ||
    entry.browser_automation_enabled ||
    entry.connector_write_enabled ||
    entry.plugin_runtime_import_enabled ||
    entry.remote_execution_enabled ||
    entry.provider_model_call_enabled ||
    entry.background_autonomy_enabled ||
    entry.production_authority_enabled;

  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h4>{entry.label}</h4>
        <span>{entry.status}</span>
      </div>
      <p>{entry.eligibility_reason}</p>
      <dl className="detail-list">
        <DetailTerm label="Compatibility source" value={entry.lane_ref} />
        <DetailTerm label="Capability" value={entry.capability_ref} />
        <DetailTerm label="Surface" value={entry.surface} />
        <DetailTerm label="Kind" value={entry.capability_kind} />
        <DetailTerm label="Side effect" value={entry.side_effect_class} />
        <DetailTerm label="Approval" value={entry.required_approval_scope} />
        <DetailTerm label="Blocked reason" value={entry.blocked_reason} />
        <DetailTerm label="Receipt" value={entry.receipt_requirement} />
        <DetailTerm
          label="Rollback/safe-disable"
          value={entry.rollback_or_safe_disable_posture}
        />
        <DetailTerm
          label="Proposal only"
          value={entry.proposal_only ? "yes" : "no"}
        />
        <DetailTerm
          label="Exact local capability"
          value={entry.exact_local_mutation_available ? "available" : "blocked"}
        />
        <DetailTerm
          label="Exact runtime capability"
          value={entry.exact_runtime_lane_available ? "available" : "blocked"}
        />
        <DetailTerm
          label="Canonical mission dispatch"
          value={entry.canonical_mission_dispatch ? "verified" : "not promoted"}
        />
        <DetailTerm
          label="Availability snapshot"
          value={entry.availability_snapshot_ref ?? "not bound"}
        />
        <DetailTerm
          label="Execution path"
          value={entry.canonical_execution_path_ref ?? "not promoted"}
        />
        <DetailTerm
          label="Broad authority"
          value={broadAuthorityEnabled ? "unsafe" : "blocked"}
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Routes: none"
        refs={entry.route_refs}
      />
      <RefListWithFallback emptyLabel="CLI refs: none" refs={entry.cli_refs} />
      <RefListWithFallback
        emptyLabel="Receipt refs: none"
        refs={entry.receipt_refs}
      />
      <RefListWithFallback
        emptyLabel="Evidence refs: none"
        refs={entry.evidence_refs}
      />
      <RefListWithFallback
        emptyLabel="Proof refs: none"
        refs={entry.proof_refs}
      />
      <RefListWithFallback
        emptyLabel="Blocked authority refs: none"
        refs={entry.blocked_authority_refs}
      />
      <RefListWithFallback
        emptyLabel="Unblock prompt refs: none"
        refs={entry.unblock_prompt_refs}
      />
    </article>
  );
}

function ActionInboxWorkQueuePanel({
  readModel,
}: {
  readModel?: FounderLoopActionInboxWorkQueueReadModel;
}) {
  if (!readModel) {
    return (
      <article className="status-card" aria-label="Action Inbox work queue">
        <div className="status-card-header">
          <h3>Work queue</h3>
          <span>backend read model missing</span>
        </div>
        <p>
          Action Inbox queue posture is unavailable. The UI will not infer
          durable queue truth from filters, local state, or mock lane data.
        </p>
        <dl className="detail-list">
          <DetailTerm label="Action execution" value="blocked" />
          <DetailTerm label="Connector writes" value="blocked" />
          <DetailTerm label="Provider/model calls" value="blocked" />
        </dl>
      </article>
    );
  }
  const nextItem = readModel.next_item;
  const sourceLabel = readModel.backend_owned
    ? "backend-owned"
    : "mock fallback";
  return (
    <article className="status-card" aria-label="Action Inbox work queue">
      <div className="status-card-header">
        <h3>Work queue</h3>
        <span>{sourceLabel}</span>
      </div>
      <p>{readModel.operator_summary}</p>
      <div className="operator-loop-summary-grid">
        <Metric label="actionable" value={readModel.operator_actionable_count} />
        <Metric label="ready" value={readModel.ready_for_decision_count} />
        <Metric label="local task" value={readModel.approved_local_task_count} />
        <Metric label="proposals" value={readModel.proposal_only_count} />
        <Metric label="blocked" value={readModel.blocked_count} />
        <Metric label="receipts" value={readModel.receipt_recorded_count} />
      </div>
      <dl className="detail-list">
        <DetailTerm label="Status" value={readModel.status} />
        <DetailTerm label="Tier posture" value={readModel.tier_posture} />
        <DetailTerm
          label="Mutating controls"
          value={readModel.mutating_controls_posture}
        />
        <DetailTerm label="Route" value={readModel.route_ref} />
        <DetailTerm label="CLI" value={readModel.cli_ref} />
        <DetailTerm
          label="Action execution"
          value={readModel.action_execution_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Fake mutation controls"
          value={readModel.fake_mutation_controls_exposed ? "unsafe" : "none"}
        />
        <DetailTerm
          label="Unsafe refs omitted"
          value={String(readModel.unsafe_ref_omitted_count)}
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Unsafe-ref blockers: none"
        refs={readModel.unsafe_ref_blocked_state_refs}
      />
      {nextItem ? (
        <div className="hero-panel compact">
          <div>
            <p className="eyebrow">Next queue item</p>
            <h3>{nextItem.title}</h3>
            <p className="muted">{nextItem.next_safe_action}</p>
          </div>
          <dl className="detail-list compact">
            <DetailTerm label="Item" value={nextItem.item_ref} />
            <DetailTerm label="Lane" value={nextItem.lane_label} />
            <DetailTerm label="Status" value={nextItem.status} />
            <DetailTerm
              label="Exact scope"
              value={nextItem.exact_scope_ref ?? "not available"}
            />
            <DetailTerm
              label="Idempotency"
              value={nextItem.idempotency_ref ?? "not available"}
            />
            <DetailTerm
              label="Expiry / stale"
              value={nextItem.expiry_or_staleness}
            />
            <DetailTerm label="Can do now" value={nextItem.available_action} />
            <DetailTerm
              label="Approval"
              value={nextItem.approval_required ? "required" : "not required"}
            />
            <DetailTerm
              label="Local task record"
              value={nextItem.local_task_commit_eligible ? "eligible" : "blocked"}
            />
            <DetailTerm
              label="Local task route"
              value={nextItem.local_task_commit_route_ref ?? "not available"}
            />
            <DetailTerm
              label="Rollback"
              value={nextItem.rollback_ref ?? "not available"}
            />
            <DetailTerm
              label="Safe disable"
              value={nextItem.safe_disable_ref ?? "not available"}
            />
            <DetailTerm label="Proof" value={nextItem.proof_ref} />
          </dl>
          <RefListWithFallback
            emptyLabel="Expected receipts: none"
            refs={nextItem.expected_receipt_refs}
          />
          <RefListWithFallback
            emptyLabel="Evidence refs: none"
            refs={nextItem.evidence_refs}
          />
          <RefListWithFallback
            emptyLabel="Receipt refs: none"
            refs={nextItem.receipt_refs}
          />
          <RefListWithFallback
            emptyLabel="Blocked authority refs: none"
            refs={nextItem.blocked_authority_refs}
          />
        </div>
      ) : (
        <p className="empty-state">No Action Inbox item needs review right now.</p>
      )}
      <div aria-label="Action Inbox exact work items" className="review-grid">
        {readModel.work_items.map((item) => (
          <ActionInboxWorkQueueWorkItemCard item={item} key={item.item_ref} />
        ))}
      </div>
      <div className="review-grid">
        {readModel.lanes.map((lane) => (
          <article className="review-card" key={lane.lane_ref}>
            <div className="review-card-heading">
              <h4>{lane.label}</h4>
              <span>{lane.count}</span>
            </div>
            <p>{lane.safe_summary}</p>
            <dl className="detail-list">
              <DetailTerm label="Status" value={lane.status} />
              <DetailTerm label="Tier" value={lane.tier} />
              <DetailTerm label="Available action" value={lane.available_action} />
            </dl>
            <RefListWithFallback
              emptyLabel="Group item refs: none"
              refs={lane.item_refs}
            />
          </article>
        ))}
      </div>
      <RefListWithFallback
        emptyLabel="Blocked authority refs: none"
        refs={readModel.blocked_authority_refs}
      />
    </article>
  );
}

function ActionInboxWorkQueueWorkItemCard({
  item,
}: {
  item: FounderLoopActionInboxWorkQueueWorkItem;
}) {
  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h4>{item.title}</h4>
        <span>{item.lane_label}</span>
      </div>
      <p>{item.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Item" value={item.item_ref} />
        <DetailTerm label="Status" value={item.status} />
        <DetailTerm label="Kind" value={item.action_kind} />
        <DetailTerm label="Side effect" value={item.side_effect_class} />
        <DetailTerm
          label="Exact scope"
          value={item.exact_scope_ref ?? "not available"}
        />
        <DetailTerm
          label="Idempotency"
          value={item.idempotency_ref ?? "not available"}
        />
        <DetailTerm label="Expiry / stale" value={item.expiry_or_staleness} />
        <DetailTerm label="Approval posture" value={item.approval_posture} />
        <DetailTerm label="Receipt posture" value={item.receipt_posture} />
        <DetailTerm
          label="Operator action"
          value={item.operator_actionable ? "reviewable" : "inspect only"}
        />
        <DetailTerm
          label="Local task record"
          value={item.local_task_commit_eligible ? "eligible" : "blocked"}
        />
        <DetailTerm
          label="Mutation control"
          value={item.mutation_control_posture}
        />
        <DetailTerm
          label="Fake controls"
          value={item.fake_mutation_control_exposed ? "unsafe" : "none"}
        />
        <DetailTerm label="Proof" value={item.proof_ref} />
        <DetailTerm label="Approval envelope" value={item.approval_envelope_ref ?? "missing"} />
        <DetailTerm label="Rollback" value={item.rollback_ref ?? "not available"} />
        <DetailTerm
          label="Safe disable"
          value={item.safe_disable_ref ?? "not available"}
        />
        <DetailTerm label="Next safe action" value={item.next_safe_action} />
      </dl>
      <RefListWithFallback
        emptyLabel="Expected receipt refs: none"
        refs={item.expected_receipt_refs}
      />
      <RefListWithFallback
        emptyLabel="Receipt refs: none"
        refs={item.receipt_refs}
      />
      <RefListWithFallback
        emptyLabel="Evidence refs: none"
        refs={item.evidence_refs}
      />
      <RefListWithFallback
        emptyLabel="Blocked authority refs: none"
        refs={item.blocked_authority_refs}
      />
    </article>
  );
}

function BriefingOperatorSummary({
  briefing,
}: {
  briefing: FounderLoopMorningBriefing;
}) {
  return (
    <section
      aria-label="Briefing operator summary"
      className="operator-loop-summary"
    >
      <div className="operator-loop-summary-main">
        <p className="eyebrow">Morning context</p>
        <h3>Start with decisions, changes, blockers, and review groups</h3>
        <p>
          Briefing items are bounded previews over local safe refs. Open Today
          or Action Inbox to record supported receipts; source refresh,
          notifications, connector runtime, model/provider authority, memory
          writes, and context injection remain blocked.
        </p>
      </div>
      <div className="operator-loop-summary-grid">
        <Metric label="briefing items" value={briefing.items.length} />
        <Metric
          label="review groups"
          value={briefing.review_queue_groups?.length ?? 0}
        />
        <Metric
          label="memory reasons"
          value={briefing.memory_why_shown_items?.length ?? 0}
        />
        <Metric
          label="blocked states"
          value={briefing.blocked_states?.length ?? 0}
        />
      </div>
      <RefListWithFallback
        emptyLabel="Briefing blockers: none"
        refs={briefing.blocked_states ?? []}
      />
    </section>
  );
}

function MemoryOperatorSummary({
  authoritative,
  contextPacks,
  today,
  workbench,
}: {
  authoritative: boolean;
  contextPacks: FounderLoopMemoryContextPacks;
  today: FounderLoopTodaySummary;
  workbench: FounderLoopMemoryWorkbench;
}) {
  return (
    <section
      aria-label="Memory operator summary"
      className="operator-loop-summary"
    >
      <div className="operator-loop-summary-main">
        <p className="eyebrow">Memory review signals</p>
        <h3>Review recall, quality pressure, and follow-ups before using it</h3>
        <p>
          Memory is shown as reviewed recall and loop signal posture. It is not
          truth authority, hidden context, connector sync, automatic maintenance,
          or a write path.
        </p>
      </div>
      <div className="operator-loop-summary-grid">
        <Metric label="workbench items" value={workbench.items.length} />
        <Metric
          label="reviewed recall"
          value={workbench.health.reviewed_recall_count}
        />
        <Metric
          label="follow-up proposals"
          value={today.memory_derived_action_proposal_count}
        />
        <Metric
          label="context packs"
          value={contextPacks.context_pack_count}
        />
      </div>
      <dl className="detail-list compact">
        <DetailTerm
          label="Why shown"
          value={
            today.memory_why_shown_items?.[0]?.why_shown ??
            "Memory loop refs are shown when reviewed recall affects Today, Actions, Briefing, or Evidence."
          }
        />
        <DetailTerm
          label="What this affects"
          value="Today, Actions, Briefing, Evidence, Weekly Review"
        />
        <DetailTerm
          label="Context injection"
          value={workbench.context_injection_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Memory truth authority"
          value={workbench.memory_truth_authority ? "enabled" : "blocked"}
        />
      </dl>
    </section>
  );
}

function EvidenceOperatorSummary({
  evidence,
  today,
}: {
  evidence?: FounderLoopEvidenceTimelineIndex;
  today: FounderLoopTodaySummary;
}) {
  const eventCount = evidence?.event_count ?? today.evidence_timeline.length;
  const receiptCount =
    evidence?.receipt_refs.length ??
    countTimelineRefs(today.evidence_timeline, ["receipt_refs"]);
  return (
    <section
      aria-label="Evidence operator summary"
      className="operator-loop-summary"
    >
      <div className="operator-loop-summary-main">
        <p className="eyebrow">Proof before claims</p>
        <h3>Use evidence to answer what changed, what stayed blocked</h3>
        <p>
          Evidence is safe-ref history and receipt visibility. It does not
          include raw private content, hidden context, rollback execution, or
          release authority.
        </p>
      </div>
      <div className="operator-loop-summary-grid">
        <Metric label="events" value={eventCount} />
        <Metric label="groups" value={evidence?.group_count ?? 0} />
        <Metric label="receipt refs" value={receiptCount} />
        <Metric
          label="blocked states"
          value={
            evidence?.blocked_states.length ??
            today.evidence_timeline_blocked_states?.length ??
            0
          }
        />
      </div>
      <dl className="detail-list compact">
        <DetailTerm
          label="What changed"
          value="Read the timeline history answers and receipt refs."
        />
        <DetailTerm
          label="What stayed blocked"
          value="Approval authority, rollback execution, context injection, memory truth, provider/model authority."
        />
        <DetailTerm
          label="Fallback posture"
          value={evidence ? "backend evidence index" : "Today summary fallback"}
        />
      </dl>
    </section>
  );
}

function OperatorRunTimelineSummary({
  timeline,
}: {
  timeline?: FounderLoopOperatorRunTimeline;
}) {
  const usage = timeline?.frontier_ai_usage_summary;
  const control = timeline?.run_control_summary;
  return (
    <section
      aria-label="Operator Run Timeline"
      className="operator-loop-summary"
    >
      <div className="operator-loop-summary-main">
        <p className="eyebrow">Run control</p>
        <h3>Operator Run Timeline</h3>
        <p>
          Shared run state is projected from Evidence safe refs, with approval,
          completion, blocked-state, and frontier AI cost posture visible before
          broader authority exists.
        </p>
      </div>
      <div className="operator-loop-summary-grid">
        <Metric label="run events" value={timeline?.event_count ?? 0} />
        <Metric
          label="waiting"
          value={control?.waiting_for_approval_count ?? 0}
        />
        <Metric
          label="receipts"
          value={control?.receipt_recorded_count ?? 0}
        />
        <Metric label="cost USD x1000" value={Math.round((usage?.estimated_total_cost_usd ?? 0) * 1000)} />
      </div>
      <dl className="detail-list compact">
        <DetailTerm
          label="Contract ref"
          value={timeline?.contract_ref ?? "contract-ref:operator-run-timeline:v1"}
        />
        <DetailTerm
          label="Cost contract"
          value={
            usage?.contract_ref ??
            "contract-ref:frontier-ai-cost-usage-telemetry:v1"
          }
        />
        <DetailTerm
          label="Cost status"
          value={usage?.status ?? "accounting_slots_pending_backend"}
        />
        <DetailTerm
          label="Provider/model authority"
          value={timeline?.provider_model_authority_allowed ? "enabled" : "blocked"}
        />
      </dl>
      <InlineListWithFallback
        emptyLabel="Borrowed pattern refs pending"
        items={(timeline?.borrowed_patterns ?? []).map(
          (pattern) => `${pattern.pattern_id}: ${pattern.label}`,
        )}
      />
    </section>
  );
}

function OperatorRunTimelinePanel({
  timeline,
}: {
  timeline?: FounderLoopOperatorRunTimeline;
}) {
  const usage = timeline?.frontier_ai_usage_summary;
  const events = timeline?.run_events ?? [];
  const firstCostSlot = events[0]?.cost_usage;
  if (!timeline) {
    return (
      <article className="status-card">
        <div className="status-card-header">
          <h3>Operator Run Timeline</h3>
          <span>pending</span>
        </div>
        <p>
          Run timeline data is unavailable from the backend response; the
          Evidence Timeline remains the current safe-ref source.
        </p>
      </article>
    );
  }

  return (
    <div aria-label="Operator Run Timeline details" className="panel-grid">
      <article className="status-card">
        <div className="status-card-header">
          <h3>Operator Run Timeline</h3>
          <span>{timeline.status}</span>
        </div>
        <dl className="detail-list">
          <DetailTerm label="Contract ref" value={timeline.contract_ref} />
          <DetailTerm label="Source" value={timeline.source} />
          <DetailTerm label="Route" value={timeline.route_ref} />
          <DetailTerm
            label="Provider/model authority"
            value={timeline.provider_model_authority_allowed ? "enabled" : "blocked"}
          />
          <DetailTerm
            label="Runtime model calls"
            value={timeline.runtime_model_calls_enabled ? "enabled" : "blocked"}
          />
          <DetailTerm
            label="Prompt content stored"
            value={timeline.prompt_content_stored ? "yes" : "no"}
          />
          <DetailTerm
            label="Response content stored"
            value={timeline.response_content_stored ? "yes" : "no"}
          />
          <DetailTerm
            label="Provider exchange content stored"
            value={timeline.provider_exchange_content_stored ? "yes" : "no"}
          />
        </dl>
        <p>{timeline.authority_boundary}</p>
      </article>
      <article className="status-card">
        <div className="status-card-header">
          <h3>Five borrowed patterns</h3>
          <span>{timeline.borrowed_patterns.length}</span>
        </div>
        <ul className="ref-list">
          {timeline.borrowed_patterns.map((pattern) => (
            <li key={pattern.pattern_id}>
              <strong>{pattern.pattern_id}</strong>: {pattern.label}.{" "}
              {pattern.safe_summary}
            </li>
          ))}
        </ul>
      </article>
      <article className="status-card">
        <div className="status-card-header">
          <h3>Run control states</h3>
          <span>{timeline.run_control_summary.goal_completion_status}</span>
        </div>
        <dl className="detail-list">
          <DetailTerm
            label="Waiting"
            value={String(timeline.run_control_summary.waiting_for_approval_count)}
          />
          <DetailTerm
            label="Receipts"
            value={String(timeline.run_control_summary.receipt_recorded_count)}
          />
          <DetailTerm
            label="Blocked"
            value={String(timeline.run_control_summary.blocked_count)}
          />
          <DetailTerm
            label="Needs evidence"
            value={String(timeline.run_control_summary.needs_evidence_count)}
          />
          <DetailTerm
            label="Pause/resume"
            value={timeline.run_control_summary.pause_resume_status}
          />
        </dl>
        <RefListWithFallback
          emptyLabel="No run state refs recorded"
          refs={timeline.run_control_summary.state_refs}
        />
      </article>
      <article className="status-card">
        <div className="status-card-header">
          <h3>Frontier AI cost telemetry</h3>
          <span>{usage?.status ?? "not_reported"}</span>
        </div>
        <dl className="detail-list">
          <DetailTerm
            label="Contract ref"
            value={
              usage?.contract_ref ??
              "contract-ref:frontier-ai-cost-usage-telemetry:v1"
            }
          />
          <DetailTerm
            label="Estimated cost USD"
            value={formatCostUsd(usage?.estimated_total_cost_usd)}
          />
          <DetailTerm
            label="Captured cost USD"
            value={formatCostUsd(usage?.captured_total_cost_usd)}
          />
          <DetailTerm
            label="Provider ref"
            value={firstCostSlot?.provider_ref ?? "provider-ref:not-invoked"}
          />
          <DetailTerm
            label="Model profile"
            value={
              firstCostSlot?.model_profile_ref ?? "model-profile-ref:not-invoked"
            }
          />
          <DetailTerm
            label="Input metered units"
            value={String(usage?.input_metered_units ?? 0)}
          />
          <DetailTerm
            label="Output metered units"
            value={String(usage?.output_metered_units ?? 0)}
          />
          <DetailTerm label="Budget ref" value={usage?.budget_status_ref ?? "budget-status:pending"} />
          <DetailTerm
            label="Unknown paid cost"
            value={
              usage?.unknown_paid_cost_requires_approval_before_routing
                ? "approval required before routing"
                : "not reported"
            }
          />
        </dl>
        <RefListWithFallback
          emptyLabel="No cost event refs recorded"
          refs={usage?.cost_event_refs ?? []}
        />
      </article>
      <article className="status-card">
        <div className="status-card-header">
          <h3>Run events</h3>
          <span>{events.length}</span>
        </div>
        <ul className="ref-list">
          {events.slice(0, 6).map((event) => (
            <li key={event.run_event_ref}>
              <strong>{event.operator_state}</strong>: {event.event_kind} -{" "}
              {event.condensed_summary_ref} - {event.cost_usage.cost_capture_status}
            </li>
          ))}
        </ul>
        <RefListWithFallback
          emptyLabel="No run blockers recorded"
          refs={timeline.blocked_state_refs}
        />
      </article>
    </div>
  );
}

function RunObservabilityPanel({
  readModel,
}: {
  readModel?: RunObservabilityReadModel;
}) {
  if (!readModel) {
    return (
      <article className="status-card">
        <div className="status-card-header">
          <h3>Run Observability</h3>
          <span>pending</span>
        </div>
        <p>
          Run observability is unavailable from the backend response; Evidence
          remains inspectable through existing timeline refs.
        </p>
      </article>
    );
  }
  const sourceLabel =
    readModel.source === "python_core_run_observability_read_model"
      ? "backend-owned"
      : "mock fallback";
  const authorityStates = [
    `Cancel: ${readModel.cancel_control_status}`,
    `Resume: ${readModel.resume_control_status}`,
    `Streaming: ${readModel.streaming_status}`,
    `Background: ${readModel.background_worker_status}`,
    `Provider/model: ${readModel.provider_model_status}`,
    `Tool use: ${readModel.tool_execution_status}`,
    `Connector delivery: ${readModel.connector_execution_status}`,
    `Autonomy: ${readModel.autonomous_execution_status}`,
  ];

  return (
    <section aria-label="Run Observability details" className="compact-stack">
      <div className="section-heading compact-heading">
        <div>
          <p className="eyebrow">Evidence</p>
          <h3>Run Observability</h3>
        </div>
        <span className="status-pill compact">{readModel.status}</span>
      </div>
      <div className="metric-grid">
        <Metric label="Run events" value={readModel.event_count} />
        <Metric label="Progress events" value={readModel.progress_event_count} />
        <Metric label="Approvals" value={readModel.approval_item_count} />
        <Metric label="Coworker refs" value={readModel.coworker_event_count} />
        <Metric
          label="Connector refs"
          value={readModel.connector_delivery_count}
        />
        <Metric
          label="Delivery reviews"
          value={readModel.connector_delivery_review_count}
        />
      </div>
      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Run read model</h3>
            <span>{sourceLabel}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm label="Contract ref" value={readModel.contract_ref} />
            <DetailTerm label="Run ref" value={readModel.run_ref} />
            <DetailTerm
              label="Selected run"
              value={readModel.selected_run_ref ?? "none"}
            />
            <DetailTerm label="Route" value={readModel.route_ref} />
            <DetailTerm label="CLI" value={readModel.cli_ref} />
            <DetailTerm
              label="Proof posture"
              value={readModel.proof_detail_status}
            />
            <DetailTerm
              label="Control Center"
              value={
                readModel.control_center_presentation_only
                  ? "presentation only"
                  : "blocked"
              }
            />
          </dl>
          <p>{readModel.safe_summary}</p>
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Orchestration posture</h3>
            <span>{readModel.current_phase_status}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Current phase"
              value={readModel.current_phase_ref}
            />
            <DetailTerm
              label="Current step"
              value={readModel.current_step_ref}
            />
            <DetailTerm
              label="Step status"
              value={readModel.current_step_status}
            />
            <DetailTerm
              label="Approval wait"
              value={readModel.approval_wait_state.wait_state}
            />
            <DetailTerm
              label="Retry"
              value={readModel.retry_recovery_posture.retry_state}
            />
            <DetailTerm
              label="Recovery"
              value={readModel.retry_recovery_posture.recovery_state}
            />
            <DetailTerm
              label="Cancel"
              value={readModel.cancellation_dead_letter_state.cancellation_state}
            />
            <DetailTerm
              label="Dead letter"
              value={readModel.cancellation_dead_letter_state.dead_letter_state}
            />
          </dl>
          <p>
            Retry, recovery, cancellation, and resume are inspection posture
            only here; execution stays blocked until exact backend authority is
            implemented under active AuthorityLease scope.
          </p>
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Checkpoints and recovery</h3>
            <span>{readModel.checkpoint_summaries.length}</span>
          </div>
          <ul className="ref-list">
            {readModel.checkpoint_summaries.slice(0, 6).map((checkpoint) => (
              <li key={checkpoint.checkpoint_ref}>
                <strong>{checkpoint.checkpoint_status}</strong>:{" "}
                {checkpoint.safe_summary}{" "}
                <span>#{checkpoint.sequence}</span>
              </li>
            ))}
          </ul>
          <RefListWithFallback
            emptyLabel="Retry refs: none"
            refs={readModel.retry_recovery_posture.retry_refs}
          />
          <RefListWithFallback
            emptyLabel="Recovery refs: none"
            refs={readModel.retry_recovery_posture.recovery_refs}
          />
          <RefListWithFallback
            emptyLabel="Pending approvals: none"
            refs={readModel.approval_wait_state.pending_approval_refs}
          />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Failure posture</h3>
            <span>{readModel.redacted_error_summaries.length}</span>
          </div>
          <ul className="ref-list">
            {readModel.redacted_error_summaries.slice(0, 6).map((summary) => (
              <li key={summary.error_ref}>
                <strong>{summary.error_ref}</strong>: {summary.safe_summary}
              </li>
            ))}
          </ul>
          <RefListWithFallback
            emptyLabel="Cancellation refs: none"
            refs={readModel.cancellation_dead_letter_state.cancellation_refs}
          />
          <RefListWithFallback
            emptyLabel="Dead-letter refs: none"
            refs={readModel.cancellation_dead_letter_state.dead_letter_refs}
          />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Runtime controls</h3>
            <span>blocked/planned</span>
          </div>
          <InlineListWithFallback
            emptyLabel="Runtime controls remain blocked"
            items={authorityStates}
          />
          <dl className="detail-list">
            <DetailTerm
              label="UI mutation controls"
              value={readModel.ui_mutation_controls_enabled ? "enabled" : "disabled"}
            />
            <DetailTerm
              label="Cancel/resume"
              value={readModel.cancel_resume_controls_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Live streaming"
              value={readModel.live_streaming_runtime_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Provider/model calls"
              value={readModel.provider_model_calls_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Tool execution"
              value={readModel.tool_execution_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Connector writes"
              value={readModel.connector_writes_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Connector sends"
              value={readModel.connector_sends_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Background worker"
              value={readModel.background_worker_enabled ? "enabled" : "blocked"}
            />
          </dl>
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Run refs</h3>
            <span>{readModel.run_refs.length}</span>
          </div>
          <RefListWithFallback
            emptyLabel="Run refs: none"
            refs={readModel.run_refs}
          />
          <RefListWithFallback
            emptyLabel="Lifecycle event refs: none"
            refs={readModel.lifecycle_event_refs}
          />
          <RefListWithFallback
            emptyLabel="Progress event refs: none"
            refs={readModel.progress_event_refs}
          />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Review refs</h3>
            <span>{readModel.approval_refs.length}</span>
          </div>
          <RefListWithFallback
            emptyLabel="Approval refs: none"
            refs={readModel.approval_refs}
          />
          <RefListWithFallback
            emptyLabel="Coworker refs: none"
            refs={readModel.coworker_handoff_refs}
          />
          <RefListWithFallback
            emptyLabel="Connector delivery refs: none"
            refs={readModel.connector_delivery_refs}
          />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Evidence and proof refs</h3>
            <span>{readModel.proof_refs.length}</span>
          </div>
          <RefListWithFallback
            emptyLabel="Receipt refs: none"
            refs={readModel.receipt_refs}
          />
          <RefListWithFallback
            emptyLabel="Evidence refs: none"
            refs={readModel.evidence_refs}
          />
          <RefListWithFallback
            emptyLabel="Proof refs: none"
            refs={readModel.proof_refs}
          />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Blocked authority</h3>
            <span>{readModel.blocked_authority_refs.length}</span>
          </div>
          <RefListWithFallback
            emptyLabel="Blocked authority refs: none"
            refs={readModel.blocked_authority_refs}
          />
          <dl className="detail-list">
            <DetailTerm
              label="Safe refs"
              value={readModel.safe_refs_only ? "only" : "blocked"}
            />
            <DetailTerm
              label="Summaries"
              value={readModel.redacted_summaries_only ? "redacted only" : "blocked"}
            />
            <DetailTerm
              label="Payload persistence"
              value={readModel.raw_payloads_persisted ? "enabled" : "omitted"}
            />
            <DetailTerm
              label="Prompt stored"
              value={readModel.prompt_content_stored ? "yes" : "no"}
            />
            <DetailTerm
              label="Response stored"
              value={readModel.response_content_stored ? "yes" : "no"}
            />
            <DetailTerm
              label="Provider exchange stored"
              value={readModel.provider_payload_content_stored ? "yes" : "no"}
            />
            <DetailTerm
              label="Approval ref authority"
              value={readModel.approval_ref_grants_authority ? "enabled" : "blocked"}
            />
          </dl>
        </article>
      </div>
    </section>
  );
}

function EvidenceAuditReceiptSpineSection({
  readModel,
}: {
  readModel?: FounderLoopEvidenceAuditReceiptSpine;
}) {
  if (!readModel) {
    return (
      <article className="status-card">
        <div className="status-card-header">
          <h3>Evidence audit receipt spine</h3>
          <span>missing</span>
        </div>
        <p>
          Backend-owned audit grouping is unavailable from this response.
          Evidence remains read-only through the timeline and proof refs already
          present.
        </p>
      </article>
    );
  }

  return (
    <section className="nested-section" aria-labelledby="evidence-audit-spine-heading">
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Proof spine</p>
          <h3 id="evidence-audit-spine-heading">Evidence audit receipt spine</h3>
        </div>
        <span className="status-pill compact">{readModel.status}</span>
      </div>
      <div className="metric-grid">
        <Metric label="Groups" value={readModel.group_count} />
        <Metric label="Envelopes" value={readModel.envelope_count} />
        <Metric label="Missing receipts" value={readModel.missing_receipt_count} />
        <Metric label="Audit refs" value={readModel.audit_refs.length} />
      </div>
      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Receipt envelope contract</h3>
            <span>{readModel.contract_ref}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm label="Source" value={readModel.source} />
            <DetailTerm label="CLI" value={readModel.cli_ref} />
            <DetailTerm label="Portable evidence" value={readModel.portable_evidence_posture} />
            <DetailTerm label="Redaction" value={readModel.redaction_posture} />
            <DetailTerm label="Authority boundary" value={readModel.authority_boundary} />
            <DetailTerm label="Next safe action" value={readModel.next_safe_action} />
          </dl>
          <RefListWithFallback
            emptyLabel="Envelope fields: missing"
            refs={readModel.receipt_envelope_field_refs}
          />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Blocked authority</h3>
            <span>read-only</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Approval ref authority"
              value={readModel.approval_ref_authority ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Action execution"
              value={readModel.action_execution_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Provider/model call"
              value={readModel.provider_model_call_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Shell execution"
              value={
                readModel.shell_subprocess_execution_enabled ? "enabled" : "blocked"
              }
            />
            <DetailTerm
              label="Browser execution"
              value={readModel.browser_execution_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Production authority"
              value={readModel.production_authority_enabled ? "enabled" : "blocked"}
            />
          </dl>
          <RefListWithFallback
            emptyLabel="Blocked state refs: none"
            refs={readModel.blocked_state_refs}
          />
        </article>
      </div>
      <div className="review-grid">
        {readModel.groups.map((group) => (
          <article className="review-card" key={group.group_ref}>
            <div className="review-card-heading">
              <h3>{group.label}</h3>
              <span>{group.status}</span>
            </div>
            <p>{group.safe_summary}</p>
            <dl className="detail-list">
              <DetailTerm label="Group ref" value={group.group_ref} />
              <DetailTerm label="Kind" value={group.group_kind} />
              <DetailTerm label="Next safe action" value={group.next_safe_action} />
            </dl>
            <RefListWithFallback
              emptyLabel="Event refs: none"
              refs={group.event_refs}
            />
            <RefListWithFallback
              emptyLabel="Receipt refs: none recorded"
              refs={group.receipt_refs}
            />
            <RefListWithFallback
              emptyLabel="Missing receipt refs: none"
              refs={group.missing_receipt_refs}
            />
            <RefListWithFallback
              emptyLabel="Audit refs: none"
              refs={group.audit_refs}
            />
          </article>
        ))}
      </div>
      <div className="compact-stack">
        {readModel.receipt_envelopes.slice(0, 3).map((envelope) => (
          <article className="status-card" key={envelope.envelope_ref}>
            <div className="status-card-header">
              <h3>Receipt envelope</h3>
              <span>{envelope.receipt_recorded ? "recorded" : "missing"}</span>
            </div>
            <p>{envelope.safe_summary}</p>
            <dl className="detail-list">
              <DetailTerm label="Envelope ref" value={envelope.envelope_ref} />
              <DetailTerm label="Receipt ref" value={envelope.receipt_ref} />
              <DetailTerm label="Run ref" value={envelope.run_ref} />
              <DetailTerm label="Action ref" value={envelope.action_ref} />
              <DetailTerm label="Approval ref" value={envelope.approval_ref} />
              <DetailTerm
                label="Authority decision"
                value={envelope.authority_decision_ref}
              />
              <DetailTerm label="Artifact hash" value={envelope.artifact_hash_ref} />
              <DetailTerm label="Verifier" value={envelope.verifier_version_ref} />
              <DetailTerm label="Redaction" value={envelope.redaction_status} />
            </dl>
            <RefListWithFallback
              emptyLabel="Missing receipt refs: none"
              refs={envelope.missing_receipt_refs}
            />
            <RefListWithFallback
              emptyLabel="Evidence refs: none"
              refs={envelope.evidence_refs}
            />
          </article>
        ))}
      </div>
    </section>
  );
}

function EvidenceTimelineNarrativeSection({
  readModel,
}: {
  readModel?: FounderLoopEvidenceTimelineNarrativeReadModel;
}) {
  if (!readModel) {
    return (
      <article className="status-card">
        <div className="status-card-header">
          <h3>Evidence narrative</h3>
          <span>pending</span>
        </div>
        <p>
          Narrative entries are unavailable from the backend response. Evidence
          remains inspectable through existing safe refs only.
        </p>
      </article>
    );
  }

  return (
    <section
      aria-label="Evidence Timeline narrative"
      className="compact-stack"
    >
      <article className="status-card">
        <div className="status-card-header">
          <h3>Evidence narrative</h3>
          <span>{readModel.status}</span>
        </div>
        <dl className="detail-list">
          <DetailTerm label="Contract ref" value={readModel.contract_ref} />
          <DetailTerm label="Source" value={readModel.source} />
          <DetailTerm label="Entries" value={String(readModel.entry_count)} />
          <DetailTerm
            label="Narrative source"
            value={
              readModel.narrative_from_existing_refs_only
                ? "existing refs only"
                : "blocked"
            }
          />
          <DetailTerm
            label="Raw content"
            value={readModel.raw_content_included ? "included" : "omitted"}
          />
          <DetailTerm
            label="Approval authority"
            value={
              readModel.approval_ref_authority
                ? "enabled"
                : "approval refs are identifiers only"
            }
          />
          <DetailTerm
            label="Rollback execution"
            value={readModel.rollback_execution_enabled ? "enabled" : "blocked"}
          />
          <DetailTerm
            label="Provider/model calls"
            value={
              readModel.provider_model_call_enabled ||
              readModel.runtime_model_calls_enabled ||
              readModel.provider_sdk_call_enabled
                ? "enabled"
                : "blocked"
            }
          />
        </dl>
        <p>{readModel.authority_boundary}</p>
        <p>{readModel.next_safe_action}</p>
        <RefListWithFallback
          emptyLabel="No narrative refs recorded"
          refs={readModel.narrative_refs}
        />
      </article>
      <div className="review-grid">
        {readModel.entries.slice(0, 6).map((entry) => (
          <EvidenceNarrativeEntryCard entry={entry} key={entry.narrative_ref} />
        ))}
      </div>
    </section>
  );
}

function EvidenceNarrativeEntryCard({
  entry,
}: {
  entry: FounderLoopEvidenceNarrativeEntry;
}) {
  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>Narrative: {entry.title}</h3>
        <span>{entry.event_type}</span>
      </div>
      <dl className="detail-list">
        <DetailTerm label="Narrative ref" value={entry.narrative_ref} />
        <DetailTerm label="Event ref" value={entry.event_ref} />
        <DetailTerm label="Timeline ref" value={entry.timeline_item_ref} />
        <DetailTerm label="Group ref" value={entry.group_ref} />
        <DetailTerm label="What happened" value={entry.what_happened} />
        <DetailTerm label="Why recorded" value={entry.why_recorded} />
        <DetailTerm label="Approval posture" value={entry.approval_posture} />
        <DetailTerm label="Changed" value={entry.change_summary} />
        <DetailTerm label="Still blocked" value={entry.remaining_blocked} />
        <DetailTerm label="Inspect" value={entry.inspection_summary} />
        <DetailTerm
          label="Raw content"
          value={entry.raw_content_included ? "included" : "omitted"}
        />
        <DetailTerm
          label="Action execution"
          value={entry.action_execution_enabled ? "enabled" : "blocked"}
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Evidence refs: none recorded"
        refs={entry.evidence_refs}
      />
      <RefListWithFallback
        emptyLabel="Receipt refs: not recorded"
        refs={entry.receipt_refs}
      />
      <RefListWithFallback
        emptyLabel="Approval refs: identifiers only or not present"
        refs={entry.approval_refs}
      />
      <RefListWithFallback
        emptyLabel="Blocked refs: none recorded"
        refs={entry.blocked_state_refs}
      />
    </article>
  );
}

type TodayPriorityRow = {
  affects: string;
  href: string;
  item: string;
  status: string;
  tone: "green" | "gray" | "orange" | "red";
  whyShown: string;
};

function NorthStarTodayCockpit({
  actionReadModelAuthoritative,
  today,
}: {
  actionReadModelAuthoritative: boolean;
  today: FounderLoopTodaySummary;
}) {
  const commandItems = buildDailyLoopCommandItems(today);
  const priorityRows = buildTodayPriorityRows(today);
  const proposalOnlyCount =
    countProposalOnly(today.actions) +
    today.memory_derived_action_proposal_count +
    today.task_decomposition_proposal_count;
  const receiptBackedCount = countReceiptBacked(today);
  const blockedCount = countBlockedToday(today);
  const noActionCount = Math.max(
    0,
    today.sections.action_inbox_count +
      today.sections.plan_count +
      today.sections.memory_review_count +
      today.sections.briefing_count -
      proposalOnlyCount -
      receiptBackedCount -
      blockedCount,
  );
  const evidenceCount =
    today.sections.evidence_timeline_count ?? today.evidence_timeline.length;

  return (
    <section
      aria-label="North-star Today command deck"
      className="north-star-today"
    >
      <div className="north-star-section-title">
        <div>
          <p className="eyebrow">Daily Command Deck</p>
          <h3>Daily Status</h3>
        </div>
        <span className="status-pill compact">
          {actionReadModelAuthoritative
            ? "backend-owned read model"
            : "non-authoritative fallback"}
        </span>
      </div>
      <div className="north-star-status-grid">
        <TodayStatusTile
          detail="reviewable today"
          label="Actions Due"
          tone={today.sections.action_inbox_count > 0 ? "orange" : "green"}
          value={String(today.sections.action_inbox_count)}
        />
        <TodayStatusTile
          detail="no receipt yet"
          label="Proposal Only"
          tone={proposalOnlyCount > 0 ? "orange" : "gray"}
          value={String(proposalOnlyCount)}
        />
        <TodayStatusTile
          detail="source proof visible"
          label="Receipt-Backed"
          tone="green"
          value={String(receiptBackedCount)}
        />
        <TodayStatusTile
          detail="requires attention"
          label="Risks / Alerts"
          tone={blockedCount > 0 ? "red" : "green"}
          value={String(blockedCount)}
        />
        <TodayStatusTile
          detail={actionReadModelAuthoritative ? "backend current" : "fallback only"}
          label="Loop Health"
          tone={actionReadModelAuthoritative ? "green" : "orange"}
          value={actionReadModelAuthoritative ? "Live" : "Check"}
        />
      </div>
      <div className="north-star-loop-rail" aria-label="Daily loop order">
        {commandItems.map((item, index) => (
          <a
            className={`north-star-loop-step ${item.posture}`}
            href={item.href}
            key={item.commandRef}
          >
            <span>{index + 1}</span>
            <strong>{item.surface}</strong>
            <small>{northStarLoopCaption(index)}</small>
          </a>
        ))}
      </div>
      <div className="north-star-work-grid">
        <article className="north-star-panel north-star-priorities">
          <div className="north-star-panel-header">
            <h3>Top Priorities</h3>
            <span>{priorityRows.length}</span>
          </div>
          <div className="north-star-table-wrap">
            <table className="north-star-table">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Why shown</th>
                  <th>Affects</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {priorityRows.map((row) => (
                  <tr key={`${row.href}:${row.item}`}>
                    <td>
                      <a href={row.href}>{row.item}</a>
                    </td>
                    <td>{row.whyShown}</td>
                    <td>{row.affects}</td>
                    <td>
                      <span className={`north-star-state ${row.tone}`}>
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <a className="text-link" href="/actions">
            View Action Inbox
          </a>
        </article>
        <article className="north-star-panel">
          <div className="north-star-panel-header">
            <h3>Backend Truth Summary</h3>
            <span>{today.status}</span>
          </div>
          <div className="north-star-summary-list">
            <TodaySummaryRow label="Receipt-backed" tone="green" value={receiptBackedCount} />
            <TodaySummaryRow label="Proposal-only" tone="orange" value={proposalOnlyCount} />
            <TodaySummaryRow label="Blocked" tone="red" value={blockedCount} />
            <TodaySummaryRow label="No action needed" tone="gray" value={noActionCount} />
            <TodaySummaryRow label="Evidence added" tone="green" value={evidenceCount} />
          </div>
          <dl className="detail-list compact">
            <DetailTerm
              label="Why shown"
              value={
                today.daily_loop_summary?.safe_summary ??
                "Today aggregates backend-owned safe refs for the founder loop."
              }
            />
            <DetailTerm
              label="What this affects"
              value="Today, Briefing, Action Inbox, Plans, Memory, Evidence"
            />
            <DetailTerm
              label="Blocked authority"
              value="no generic execution, connector write, shell, provider/model, context injection, or production authority"
            />
          </dl>
          <a className="text-link" href="/evidence">
            View Evidence
          </a>
        </article>
      </div>
    </section>
  );
}

function TodayStatusTile({
  detail,
  label,
  tone,
  value,
}: {
  detail: string;
  label: string;
  tone: "green" | "gray" | "orange" | "red";
  value: string;
}) {
  return (
    <article className={`north-star-status-tile ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function TodaySummaryRow({
  label,
  tone,
  value,
}: {
  label: string;
  tone: "green" | "gray" | "orange" | "red";
  value: number;
}) {
  return (
    <div className="north-star-summary-row">
      <span className={`north-star-dot ${tone}`} />
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function northStarLoopCaption(index: number): string {
  return [
    "Start here",
    "Triage and prioritize",
    "Review and track",
    "Learn and improve",
    "Resolve and unlock",
  ][index] ?? "Inspect safely";
}

function buildTodayPriorityRows(today: FounderLoopTodaySummary): TodayPriorityRow[] {
  const actionRows = today.actions.slice(0, 5).map((action) => ({
    affects: action.surface,
    href: "/actions",
    item: action.title,
    status: action.blocked_state ?? action.approval_envelope_status ?? action.status,
    tone: toneForState(action.blocked_state ?? action.approval_envelope_status ?? action.status),
    whyShown: action.safe_summary,
  }));
  const planRows = today.plans.slice(0, Math.max(0, 5 - actionRows.length)).map((plan) => ({
    affects: "Plans",
    href: "/plans",
    item: plan.title,
    status: plan.action_envelope_status ?? plan.status,
    tone: toneForState(plan.action_envelope_status ?? plan.status),
    whyShown: plan.next_step_summary || plan.safe_summary,
  }));
  const briefingRows = today.briefing_items
    .slice(0, Math.max(0, 5 - actionRows.length - planRows.length))
    .map((item) => ({
      affects: "Briefing",
      href: "/briefing",
      item: item.title,
      status: item.status,
      tone: toneForState(item.status),
      whyShown: item.safe_summary,
    }));
  return [...actionRows, ...planRows, ...briefingRows].map((row) => ({
    ...row,
    status: compactLabel(row.status),
    whyShown: compactSentence(row.whyShown),
  }));
}

function countProposalOnly(actions: FounderLoopActionItem[]): number {
  return actions.filter((action) =>
    [
      action.status,
      action.approval_envelope_status,
      action.action_envelope_status,
      action.state_change_readiness,
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes("proposal")),
  ).length;
}

function countReceiptBacked(today: FounderLoopTodaySummary): number {
  const actionReceiptCount = today.actions.reduce(
    (count, action) => count + action.receipt_refs.length,
    0,
  );
  const evidenceReceiptCount = today.evidence_timeline.reduce(
    (count, item) => count + item.receipt_refs.length,
    0,
  );
  return actionReceiptCount + evidenceReceiptCount;
}

function countBlockedToday(today: FounderLoopTodaySummary): number {
  const blockedRefs = new Set([
    ...today.blocker_refs,
    ...today.memory_review_blocked_states,
    ...today.memory_to_loop_blocked_state_refs,
    ...today.private_beta_readiness_blocked_state_refs,
    ...today.task_decomposition_required_blocked_refs,
    ...today.actions.flatMap((action) =>
      action.blocked_state ? [action.blocked_state] : [],
    ),
  ]);
  return blockedRefs.size;
}

function toneForState(value: string | undefined | null): "green" | "gray" | "orange" | "red" {
  const lower = String(value ?? "").toLowerCase();
  if (lower.includes("blocked") || lower.includes("denied") || lower.includes("risk")) {
    return "red";
  }
  if (
    lower.includes("proposal") ||
    lower.includes("pending") ||
    lower.includes("review") ||
    lower.includes("partial")
  ) {
    return "orange";
  }
  if (
    lower.includes("receipt") ||
    lower.includes("implemented") ||
    lower.includes("ready") ||
    lower.includes("approved")
  ) {
    return "green";
  }
  return "gray";
}

function compactSentence(value: string): string {
  return value.length > 82 ? `${value.slice(0, 79).trim()}...` : value;
}

function compactLabel(value: string): string {
  return value.replaceAll("_", " ");
}

export function TodaySurfacePanel({
  actionReadModelAuthoritative,
  agentLoopThread,
  today,
}: {
  actionReadModelAuthoritative: boolean;
  agentLoopThread: FounderLoopAgentLoopThread;
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
      <NorthStarTodayCockpit
        actionReadModelAuthoritative={actionReadModelAuthoritative}
        today={today}
      />
      <TodayLoopReadModelPanel today={today} />
      <AgentLoopThreadPanel readModel={agentLoopThread} />
      <OperatorWorkspaceSpinePanel
        readModel={today.operator_workspace_spine_read_model}
      />
      <FounderLoopRunsIntegrationPanel
        focus="today"
        readModel={today.founder_loop_runs_integration_read_model}
      />
      <UnifiedWorkThreadPanel
        readModel={today.unified_work_thread_read_model}
      />
      <FounderLoopProductProofPanel
        readModel={today.founder_loop_v1_product_proof_read_model}
      />
      <FusionRoutingDelegationPanel
        readModel={today.fusion_routing_delegation_read_model}
      />
      <DailyLoopCommandDeck
        actionReadModelAuthoritative={actionReadModelAuthoritative}
        today={today}
      />
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
              label="Receipt/local-task controls"
              value={
                today.plan_action_state.mutating_controls_enabled
                  ? "receipt and exact local-task controls only"
                  : "blocked"
              }
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
              label="Full-strength version"
              value={today.private_beta_readiness_full_strength_goal}
            />
            <DetailTerm
              label="Repo-safe version"
              value={today.private_beta_readiness_repo_safe_scope}
            />
            <DetailTerm
              label="Blocked / needs authority"
              value={today.private_beta_readiness_blocked_authority_summary}
            />
            <DetailTerm
              label="Product-loop trial"
              value={today.private_beta_readiness_product_loop_trial_script_ref}
            />
            <DetailTerm
              label="Acceptance ledger"
              value={
                today.private_beta_readiness_private_operator_trial_ledger_ref
              }
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
            <h3>Exact promotion path</h3>
            <span>{today.private_beta_readiness_promotion_path_refs.length}</span>
          </div>
          <RefListWithFallback
            emptyLabel="Exact promotion path: missing"
            refs={today.private_beta_readiness_promotion_path_refs}
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
            <span>{today.plans_action_envelope_status ?? "backend bridge missing"}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Contract ref"
              value={today.plans_action_envelope_contract_ref ?? "missing"}
            />
            <DetailTerm
              label="Exact scope"
              value={
                today.plans_action_envelope_authority_posture?.exact_scope_required
                  ? "required"
                  : "missing"
              }
            />
            <DetailTerm
              label="Grant capture"
              value={
                today.plans_action_envelope_authority_posture
                  ?.approval_grant_capture_enabled
                  ? "unsafe"
                  : "disabled"
              }
            />
            <DetailTerm
              label="Execution"
              value={
                today.plans_action_envelope_authority_posture
                  ?.action_execution_enabled
                  ? "unsafe"
                  : "blocked"
              }
            />
          </dl>
          <InlineListWithFallback
            emptyLabel="Decision receipt options: missing"
            items={(today.plans_action_envelope_review_postures ?? []).map(
              (posture) => `decision receipt option: ${posture.review_action}`,
            )}
          />
          <RefList refs={today.plans_action_envelope_required_blocked_refs ?? []} />
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
          <ChatToLoopHandoffPanel
            compact
            readModel={today.chat_to_loop_handoff_read_model}
          />
          <FusionRoutingDelegationPanel
            compact
            readModel={today.fusion_routing_delegation_read_model}
          />
          <PlansToActionsBridgePanel
            contractRef={today.plans_to_actions_bridge_contract_ref}
            readModel={today.plans_to_actions_bridge_read_model}
          />
          {today.plans.map((plan) => (
            <PlanCard plan={plan} key={plan.plan_ref} />
          ))}
        </LoopPanel>
        <LoopPanel title="Morning Briefing" route="/briefing">
          {today.briefing_items.map((item) => (
            <BriefingCard
              allowActionEnvelopePromotion
              authoritative={actionReadModelAuthoritative}
              item={item}
              key={item.briefing_ref}
            />
          ))}
        </LoopPanel>
        <LoopPanel title="Memory review" route="/memory">
          <ChatToLoopHandoffPanel
            compact
            readModel={today.chat_to_loop_handoff_read_model}
          />
          {today.memory_review_queue.map((item) => (
            <MemoryReviewCard
              authoritative={actionReadModelAuthoritative}
              item={item}
              key={item.review_ref}
            />
          ))}
        </LoopPanel>
      </div>
      <BlockedStateList states={today.blocked_states} />
    </section>
  );
}

function PlansToActionsBridgePanel({
  contractRef,
  readModel,
}: {
  contractRef?: string;
  readModel?: FounderLoopPlansToActionsBridgeReadModel;
}) {
  if (!readModel) {
    return (
      <article className="status-card">
        <div className="status-card-header">
          <h3>Plans to Actions</h3>
          <span>backend bridge missing</span>
        </div>
        <p className="muted">
          Backend-owned Plans-to-Actions bridge posture is unavailable. Control
          Center will not infer plan envelopes, risks, receipts, rollback,
          safe-disable, or authority state from fallback-only data.
        </p>
        <dl className="detail-list">
          <DetailTerm label="Review posture" value="proposal-only" />
          <DetailTerm label="Action execution" value="blocked" />
          <DetailTerm label="Tool/workflow execution" value="blocked" />
          <DetailTerm label="Provider/browser/connector runtime" value="blocked" />
        </dl>
      </article>
    );
  }

  return (
    <section
      aria-label="Plans to reviewable Action envelopes"
      className="page-section embedded"
    >
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Product Loop 006</p>
          <h3>Plans to Actions</h3>
        </div>
        <span className="status-pill compact">{readModel.status}</span>
      </div>
      <p className="section-copy">
        Backend-owned bridge from plan proposals to reviewable Action envelopes.
        Risks, reasons, expected receipts, rollback, and safe-disable refs are
        visible; approval refs remain identifiers and decision receipts only.
      </p>
      <dl className="detail-list">
        <DetailTerm label="Contract" value={contractRef ?? readModel.contract_ref} />
        <DetailTerm label="Source" value={readModel.source} />
        <DetailTerm label="Item count" value={String(readModel.item_count)} />
        <DetailTerm
          label="Approval alone"
          value={readModel.approval_alone_executes ? "unsafe" : "does not execute"}
        />
        <DetailTerm
          label="Action execution"
          value={readModel.action_execution_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Tool/workflow execution"
          value={
            readModel.tool_execution_enabled || readModel.workflow_execution_enabled
              ? "unsafe"
              : "blocked"
          }
        />
        <DetailTerm
          label="Provider/browser/connector runtime"
          value={
            readModel.provider_model_call_enabled ||
            readModel.browser_execution_enabled ||
            readModel.connector_runtime_enabled
              ? "unsafe"
              : "blocked"
          }
        />
        <DetailTerm label="Next safe action" value={readModel.next_safe_action} />
      </dl>
      <RefListWithFallback
        emptyLabel="Bridge blockers: missing"
        refs={readModel.blocked_state_refs}
      />
      <div className="review-grid">
        {readModel.items.map((item) => (
          <article className="review-card" key={item.item_ref}>
            <div className="review-card-heading">
              <h4>{item.plan_title}</h4>
              <span>{item.plan_status}</span>
            </div>
            <p>{item.safe_summary}</p>
            <FusionRoutingMetadataCard
              cacheContext={item.cache_context_economics}
              delegation={item.delegation_proposal}
              workClassification={item.work_classification}
            />
            <dl className="detail-list">
              <DetailTerm label="Risk" value={item.risk_class} />
              <DetailTerm label="Why proposed" value={item.why_proposed} />
              <DetailTerm label="Action envelope" value={item.action_envelope_ref} />
              <DetailTerm label="Exact scope" value={item.action_scope_ref} />
              <DetailTerm
                label="Approval requirement"
                value={item.approval_requirement_ref}
              />
              <DetailTerm label="Rollback" value={item.rollback_ref} />
              <DetailTerm label="Safe disable" value={item.safe_disable_ref} />
              <DetailTerm
                label="Proposal posture"
                value={item.proposal_only ? "proposal-only" : "unsafe"}
              />
              <DetailTerm
                label="Execution authorized"
                value={item.execution_authorized ? "unsafe" : "blocked"}
              />
              <DetailTerm
                label="Provider calls"
                value={item.provider_model_call_enabled ? "unsafe" : "blocked"}
              />
              <DetailTerm label="Next safe action" value={item.next_safe_action} />
            </dl>
            <InlineListWithFallback
              emptyLabel="Decision receipt options: missing"
              items={item.review_receipt_labels.map(
                (label) => `decision receipt option: ${label}`,
              )}
            />
            <RefListWithFallback
              emptyLabel="Expected receipts: missing"
              refs={item.expected_receipt_refs}
            />
            <RefListWithFallback
              emptyLabel="Linked Action Inbox item: none"
              refs={item.linked_action_item_ref ? [item.linked_action_item_ref] : []}
            />
            <RefListWithFallback
              emptyLabel="Task decomposition steps: none"
              refs={item.step_refs}
            />
            <RefListWithFallback
              emptyLabel="Risk refs: none"
              refs={item.risk_refs}
            />
            <RefListWithFallback
              emptyLabel="Missing evidence refs: none"
              refs={item.missing_evidence_refs}
            />
            <RefListWithFallback
              emptyLabel="Blocked authority refs: missing"
              refs={item.blocked_authority_refs}
            />
          </article>
        ))}
      </div>
    </section>
  );
}

function FusionRoutingDelegationPanel({
  compact = false,
  readModel,
}: {
  compact?: boolean;
  readModel?: FounderLoopFusionRoutingDelegationReadModel;
}) {
  if (!readModel) {
    return null;
  }
  const visibleClassifications = compact
    ? readModel.work_classifications.slice(0, 2)
    : readModel.work_classifications;
  const visibleRoutes = compact
    ? readModel.route_decisions.slice(0, 2)
    : readModel.route_decisions;
  return (
    <article
      aria-label="Fusion routing and delegation readability"
      className="status-card"
    >
      <div className="status-card-header">
        <h3>Routing and Delegation</h3>
        <span>{readModel.status}</span>
      </div>
      <p className="section-copy">{readModel.authority_boundary}</p>
      <dl className="detail-list">
        <DetailTerm label="Contract" value={readModel.contract_ref} />
        <DetailTerm label="Source" value={readModel.source} />
        <DetailTerm
          label="Action execution"
          value={readModel.action_execution_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Sidekick execution"
          value={readModel.sidekick_execution_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Provider/model calls"
          value={readModel.provider_model_call_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Background dispatch"
          value={readModel.background_dispatch_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm label="Next safe action" value={readModel.next_safe_action} />
      </dl>
      <InlineListWithFallback
        emptyLabel="Work type summaries: none"
        items={visibleClassifications.map(
          (item) =>
            `Work type ${compactLabel(item.classification)}; review ${
              item.human_review_required ? "required" : "not required"
            }; confidence ${item.confidence_posture}`,
        )}
      />
      <InlineListWithFallback
        emptyLabel="Route decision summaries: none"
        items={visibleRoutes.map(
          (route) =>
            `${route.status}: ${route.operator_summary}; cost ${route.cost_posture_ref}`,
        )}
      />
      <RefListWithFallback
        emptyLabel="Routing/delegation blockers: missing"
        refs={readModel.blocked_state_refs}
      />
    </article>
  );
}

function FusionRoutingMetadataCard({
  cacheContext,
  delegation,
  workClassification,
}: {
  cacheContext?: FounderLoopCacheContextEconomics;
  delegation?: FounderLoopDelegationProposal;
  workClassification?: FounderLoopWorkClassification;
}) {
  if (!workClassification && !delegation && !cacheContext) {
    return null;
  }
  return (
    <section
      aria-label="Fusion routing metadata"
      className="approval-envelope-card"
    >
      <div className="review-card-heading compact">
        <h4>Routing metadata</h4>
        <span>review aid only</span>
      </div>
      <dl className="detail-list">
        <DetailTerm
          label="Work type"
          value={
            workClassification
              ? compactLabel(workClassification.classification)
              : "missing"
          }
        />
        <DetailTerm
          label="Human review"
          value={
            workClassification?.human_review_required
              ? "required"
              : "not required"
          }
        />
        <DetailTerm
          label="Proposed delegate"
          value={delegation?.proposed_delegate_kind ?? "none"}
        />
        <DetailTerm
          label="Delegation state"
          value={delegation?.proposal_state ?? "missing"}
        />
        <DetailTerm
          label="Worker execution"
          value={delegation?.worker_execution_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Context/cost posture"
          value={cacheContext?.estimated_context_cost_posture ?? "missing"}
        />
        <DetailTerm
          label="Runtime model switch"
          value={cacheContext?.runtime_model_switch_performed ? "unsafe" : "blocked"}
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Classification evidence refs: none"
        refs={workClassification?.evidence_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Delegation blockers: none"
        refs={delegation?.blocked_execution_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Context/cost blockers: none"
        refs={cacheContext?.cache_or_context_blocker_refs ?? []}
      />
    </section>
  );
}

function TodayLoopReadModelPanel({ today }: { today: FounderLoopTodaySummary }) {
  const readModel = today.today_loop_read_model;
  if (!readModel) {
    return (
      <article className="status-card">
        <div className="status-card-header">
          <h3>Today decisions first</h3>
          <span>backend digest missing</span>
        </div>
        <p className="muted">
          The backend did not return the Product Loop 003 Today read model.
          Control Center will not infer decisions, changed refs, blocked
          posture, or review lanes from fallback-only state.
        </p>
      </article>
    );
  }

  const lanes = readModel.lane_order
    .map((laneId) => readModel.lanes.find((lane) => lane.lane_id === laneId))
    .filter(isPresent);
  const digestItems = readModel.digest_items.slice(0, 8);

  return (
    <section
      aria-label="Backend-owned Today loop digest"
      className="page-section embedded"
    >
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Product Loop 003</p>
          <h3>Today decisions first</h3>
        </div>
        <span className="status-pill compact">{readModel.status}</span>
      </div>
      <p className="section-copy">
        Backend-owned local read models show what matters now, what changed,
        what is blocked, and what needs review. Receipts only; no execution,
        connector runtime, source refresh, provider/model call, memory write, or
        hidden context authority.
      </p>
      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Loop posture</h3>
            <span>{readModel.backend_owned ? "backend-owned" : "fallback"}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm label="Contract ref" value={readModel.contract_ref} />
            <DetailTerm label="Source" value={readModel.source} />
            <DetailTerm
              label="Safe refs only"
              value={readModel.safe_refs_only ? "yes" : "no"}
            />
            <DetailTerm
              label="Raw content"
              value={readModel.raw_content_included ? "included" : "omitted"}
            />
            <DetailTerm
              label="Action execution"
              value={readModel.action_execution_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Connector runtime"
              value={readModel.connector_runtime_enabled ? "enabled" : "blocked"}
            />
            <DetailTerm
              label="Runtime model calls"
              value={
                readModel.runtime_model_calls_enabled ? "enabled" : "blocked"
              }
            />
            <DetailTerm
              label="Memory/context authority"
              value={
                readModel.automatic_memory_write_authorized ||
                readModel.context_injection_authorized
                  ? "enabled"
                  : "blocked"
              }
            />
          </dl>
          <p>{readModel.next_safe_action}</p>
          <RefList refs={readModel.blocked_state_refs} />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Now refs</h3>
            <span>{readModel.what_matters_now_refs.length}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="What matters now"
              value={readModel.what_matters_now_refs.join(", ")}
            />
          </dl>
          <RefListWithFallback
            emptyLabel="What matters now: none"
            refs={readModel.what_matters_now_refs}
          />
          <RefListWithFallback
            emptyLabel="What changed: none"
            refs={readModel.what_changed_refs}
          />
          <RefListWithFallback
            emptyLabel="Blocked now: none"
            refs={readModel.blocked_now_refs}
          />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Review lanes</h3>
            <span>{lanes.length}</span>
          </div>
          <ul className="ref-list">
            {lanes.map((lane) => (
              <li key={lane.lane_id}>
                {lane.label}: {lane.count}; {lane.status}; {lane.next_safe_action}
              </li>
            ))}
          </ul>
          <RefListWithFallback
            emptyLabel="Needs review: none"
            refs={readModel.needs_review_refs}
          />
          <RefListWithFallback
            emptyLabel="Follow-ups: none"
            refs={readModel.follow_up_refs}
          />
          <RefListWithFallback
            emptyLabel="Stale or deferred: none"
            refs={readModel.stale_or_deferred_refs}
          />
        </article>
      </div>
      <article className="status-card">
        <div className="status-card-header">
          <h3>Decision digest</h3>
          <span>{digestItems.length}</span>
        </div>
        <ul className="ref-list">
          {digestItems.map((item) => (
            <li key={`${item.lane_id}:${item.item_ref}`}>
              <strong>{item.surface}</strong>: {item.title}; {item.state_label};{" "}
              {item.reason} Next: {item.next_safe_action}
              <RefListWithFallback
                emptyLabel="Digest refs: none"
                refs={[
                  item.item_ref,
                  ...item.source_refs,
                  ...item.evidence_refs,
                  ...item.receipt_refs,
                  ...item.blocked_state_refs,
                ]}
              />
            </li>
          ))}
        </ul>
      </article>
    </section>
  );
}

function AgentLoopThreadPanel({
  readModel,
}: {
  readModel: FounderLoopAgentLoopThread;
}) {
  const planSteps = readModel.plan.steps.slice(0, 6);
  const actions = readModel.proposed_actions.slice(0, 6);
  const bindings = readModel.surface_bindings.slice(0, 8);
  const decisionRows = readModel.operator_decision_matrix.rows.slice(0, 14);
  const highMaturityRows = readModel.high_maturity_spine_readiness.rows.slice(0, 13);
  const productCockpitRows =
    readModel.high_maturity_spine_readiness.founder_loop_product_cockpit_posture.rows.slice(
      0,
      4,
    );
  const truthLabel =
    readModel.backend_owned && readModel.source !== "mock_fallback_non_authoritative"
      ? "backend-owned"
      : "mock fallback";

  return (
    <section
      aria-label="Backend-owned Agent Loop thread"
      className="page-section embedded"
    >
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Runtime Capability Foundation 02 / 08</p>
          <h3>Agent Loop Thread</h3>
        </div>
        <span className="status-pill compact">{truthLabel}</span>
      </div>
      <p className="section-copy">
        One governed operator thread binds request, intent, plan, proposed
        actions, approval posture, evidence, proof, memory review, and the next
        safe decision from Python Core read models. It does not execute actions,
        call models, write memory, browse, run shell commands, dispatch
        connectors, or grant production authority.
      </p>
      <p className="safe-copy">
        macOS is the canonical operator surface. Linux and Windows remain render
        placeholders until separate porting work is authorized. External web
        content is untrusted evidence, never instructions or authority.
      </p>
      <article className="status-card">
        <div className="status-card-header">
          <h3>Operator decision matrix</h3>
          <span>{readModel.operator_decision_matrix.capability_status}</span>
        </div>
        <dl className="detail-list">
          <DetailTerm
            label="Contract"
            value={readModel.operator_decision_matrix.contract_ref}
          />
          <DetailTerm
            label="Route"
            value={readModel.operator_decision_matrix.route_ref}
          />
          <DetailTerm
            label="CLI"
            value={readModel.operator_decision_matrix.cli_ref}
          />
          <DetailTerm
            label="UI authority"
            value={
              readModel.operator_decision_matrix.ui_mints_authority
                ? "enabled"
                : "blocked"
            }
          />
        </dl>
        <ul className="ref-list decision-matrix-list">
          {decisionRows.map((row) => (
            <li key={`${row.surface}:${row.primary_ref}`}>
              <strong>{row.surface}</strong>: {row.operator_question}
              <dl className="detail-list compact">
                <DetailTerm label="Status" value={row.capability_status} />
                <DetailTerm label="Route" value={row.backend_route_ref} />
                <DetailTerm label="CLI" value={row.cli_ref} />
                <DetailTerm label="Approval" value={row.approval_posture} />
                <DetailTerm
                  label="Mutation"
                  value={row.mutation_enabled ? "enabled" : "blocked"}
                />
              </dl>
              <p className="muted">{row.safe_action}</p>
              <RefListWithFallback
                emptyLabel="Decision refs: none"
                refs={[
                  row.primary_ref,
                  ...row.evidence_refs,
                  ...row.proof_refs,
                  ...row.receipt_refs,
                  ...row.blocked_state_refs,
                ]}
              />
              <p className="safe-copy">{row.no_go_reason}</p>
            </li>
          ))}
        </ul>
        <p className="safe-copy">
          Next safe decision:{" "}
          {readModel.operator_decision_matrix.next_safe_operator_decision}
        </p>
      </article>
      <article className="status-card">
        <div className="status-card-header">
          <h3>High-Maturity Agent Spine</h3>
          <span>
            {readModel.high_maturity_spine_readiness.overall_projection_0_100}/100
          </span>
        </div>
        <p className="muted">
          W1-W13 coverage is derived from Python/API/CLI/docs/test evidence and
          stays read-only. It is a product truth map, not runtime authority.
        </p>
        <dl className="detail-list">
          <DetailTerm
            label="Contract"
            value={readModel.high_maturity_spine_readiness.contract_ref}
          />
          <DetailTerm
            label="CLI"
            value={readModel.high_maturity_spine_readiness.cli_ref}
          />
          <DetailTerm
            label="Coverage"
            value={readModel.high_maturity_spine_readiness.coverage_status}
          />
          <DetailTerm
            label="Usable or better"
            value={`${readModel.high_maturity_spine_readiness.usable_or_better_count}/${readModel.high_maturity_spine_readiness.weakness_count}`}
          />
        </dl>
        <ul className="ref-list decision-matrix-list">
          {highMaturityRows.map((row) => (
            <li key={row.weakness_id}>
              <strong>
                {row.weakness_id}: {row.component}
              </strong>{" "}
              <span>
                {row.status} / {row.maturity} / {row.score_0_10}/10
              </span>
              <p className="muted">{row.safe_summary}</p>
              <p className="safe-copy">Gap: {row.gap}</p>
              <p className="safe-copy">Next: {row.recommendation}</p>
              <RefListWithFallback
                emptyLabel="Spine evidence refs: none"
                refs={[...row.evidence_refs.slice(0, 3), ...row.test_refs.slice(0, 2)]}
              />
            </li>
          ))}
        </ul>
        <div
          className="detail-panel compact"
          aria-label="Founder Loop product cockpit posture"
        >
          <strong>Founder Loop Product Cockpit</strong>
          <dl className="detail-list compact">
            <DetailTerm
              label="Contract"
              value={
                readModel.high_maturity_spine_readiness
                  .founder_loop_product_cockpit_posture.contract_ref
              }
            />
            <DetailTerm
              label="Surfaces"
              value={`${readModel.high_maturity_spine_readiness.founder_loop_product_cockpit_posture.implemented_surface_count}/${readModel.high_maturity_spine_readiness.founder_loop_product_cockpit_posture.category_count}`}
            />
            <DetailTerm
              label="CLI"
              value={
                readModel.high_maturity_spine_readiness
                  .founder_loop_product_cockpit_posture.cli_ref
              }
            />
            <DetailTerm
              label="Mutation"
              value={
                readModel.high_maturity_spine_readiness
                  .founder_loop_product_cockpit_posture.mutation_controls_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
          </dl>
          <p className="safe-copy">
            {
              readModel.high_maturity_spine_readiness
                .founder_loop_product_cockpit_posture.safe_summary
            }
          </p>
          <ul className="ref-list decision-matrix-list">
            {productCockpitRows.map((row) => (
              <li key={row.category_id}>
                <strong>{row.label}</strong> <span>{row.status}</span>
                <p className="muted">{row.operator_decision_support}</p>
                <RefListWithFallback
                  emptyLabel="Product cockpit refs: none"
                  refs={[
                    ...row.route_refs.slice(0, 1),
                    ...row.cli_refs.slice(0, 1),
                    ...row.evidence_refs.slice(0, 1),
                    ...row.blocked_authority_refs.slice(0, 1),
                  ]}
                />
              </li>
            ))}
          </ul>
        </div>
        <div
          className="detail-panel compact"
          aria-label="Action and tool lane posture"
        >
          <strong>Action and Tool Lane Posture</strong>
          <dl className="detail-list compact">
            <DetailTerm
              label="Contract"
              value={
                readModel.high_maturity_spine_readiness.action_tool_lane_posture
                  .contract_ref
              }
            />
            <DetailTerm
              label="Exact runtime lanes"
              value={`${readModel.high_maturity_spine_readiness.action_tool_lane_posture.exact_runtime_lane_count}`}
            />
            <DetailTerm
              label="Exact local lanes"
              value={`${readModel.high_maturity_spine_readiness.action_tool_lane_posture.exact_local_mutation_count}`}
            />
            <DetailTerm
              label="Generic tools"
              value={
                readModel.high_maturity_spine_readiness.action_tool_lane_posture
                  .generic_tool_execution_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
          </dl>
          <p className="safe-copy">
            {
              readModel.high_maturity_spine_readiness.action_tool_lane_posture
                .safe_summary
            }
          </p>
          <ul className="ref-list decision-matrix-list">
            {readModel.high_maturity_spine_readiness.action_tool_lane_posture.rows
              .slice(0, 4)
              .map((row) => (
                <li key={row.capability_id}>
                  <strong>{row.label}</strong> <span>{row.status}</span>
                  <p className="muted">{row.blocked_reason}</p>
                  <RefListWithFallback
                    emptyLabel="Lane refs: none"
                    refs={[
                      row.lane_ref,
                      ...row.route_refs.slice(0, 1),
                      ...row.receipt_refs.slice(0, 1),
                      ...row.blocked_authority_refs.slice(0, 1),
                    ]}
                  />
                </li>
              ))}
          </ul>
        </div>
        <div
          className="detail-panel compact"
          aria-label="Durable orchestration posture"
        >
          <strong>Durable Orchestration Posture</strong>
          <dl className="detail-list compact">
            <DetailTerm
              label="Contract"
              value={
                readModel.high_maturity_spine_readiness
                  .durable_orchestration_posture.contract_ref
              }
            />
            <DetailTerm
              label="Exact runtime lanes"
              value={`${readModel.high_maturity_spine_readiness.durable_orchestration_posture.existing_exact_runtime_lane_count}`}
            />
            <DetailTerm
              label="Retry execution"
              value={
                readModel.high_maturity_spine_readiness
                  .durable_orchestration_posture.retry_execution_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
            <DetailTerm
              label="Scheduler"
              value={
                readModel.high_maturity_spine_readiness
                  .durable_orchestration_posture.scheduler_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
          </dl>
          <p className="safe-copy">
            {
              readModel.high_maturity_spine_readiness.durable_orchestration_posture
                .safe_summary
            }
          </p>
          <ul className="ref-list decision-matrix-list">
            {readModel.high_maturity_spine_readiness.durable_orchestration_posture.rows
              .slice(0, 4)
              .map((row) => (
                <li key={row.category_id}>
                  <strong>{row.label}</strong> <span>{row.status}</span>
                  <p className="muted">{row.safe_summary}</p>
                  <RefListWithFallback
                    emptyLabel="Orchestration refs: none"
                    refs={[
                      ...row.route_refs.slice(0, 1),
                      ...row.evidence_refs.slice(0, 2),
                      ...row.blocked_authority_refs.slice(0, 1),
                    ]}
                  />
                </li>
              ))}
          </ul>
        </div>
        <div
          className="detail-panel compact"
          aria-label="External information handling"
        >
          <strong>External Information Handling</strong>
          <dl className="detail-list compact">
            <DetailTerm
              label="Contract"
              value={
                readModel.high_maturity_spine_readiness
                  .external_information_handling.contract_ref
              }
            />
            <DetailTerm
              label="Exact network lanes"
              value={`${readModel.high_maturity_spine_readiness.external_information_handling.existing_exact_network_lane_count}`}
            />
            <DetailTerm
              label="Browser actions"
              value={
                readModel.high_maturity_spine_readiness
                  .external_information_handling.browser_action_execution_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
            <DetailTerm
              label="Unrestricted provider search"
              value={
                readModel.high_maturity_spine_readiness
                  .external_information_handling.provider_search_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
            <DetailTerm
              label="Exact bounded provider lanes"
              value={
                readModel.high_maturity_spine_readiness
                  .external_information_handling
                  .exact_bounded_provider_lanes_implemented
                  ? "implemented; request readiness required"
                  : "blocked"
              }
            />
          </dl>
          <p className="safe-copy">
            {
              readModel.high_maturity_spine_readiness.external_information_handling
                .safe_summary
            }
          </p>
          <ul className="ref-list decision-matrix-list">
            {readModel.high_maturity_spine_readiness.external_information_handling.rows
              .slice(0, 4)
              .map((row) => (
                <li key={row.category_id}>
                  <strong>{row.label}</strong> <span>{row.status}</span>
                  <p className="muted">{row.safe_summary}</p>
                  <RefListWithFallback
                    emptyLabel="External info refs: none"
                    refs={[
                      ...row.route_refs.slice(0, 1),
                      ...row.evidence_refs.slice(0, 2),
                      ...row.blocked_authority_refs.slice(0, 1),
                    ]}
                  />
                </li>
              ))}
          </ul>
        </div>
        <div
          className="detail-panel compact"
          aria-label="Model and provider posture"
        >
          <strong>Model and Provider Posture</strong>
          <dl className="detail-list compact">
            <DetailTerm
              label="Contract"
              value={
                readModel.high_maturity_spine_readiness.model_provider_management
                  .contract_ref
              }
            />
            <DetailTerm
              label="Model slots"
              value={`${readModel.high_maturity_spine_readiness.model_provider_management.model_slot_count}`}
            />
            <DetailTerm
              label="Tiny provider lane"
              value={
                readModel.high_maturity_spine_readiness.model_provider_management
                  .exact_tiny_provider_lane_available
                  ? "available"
                  : "blocked"
              }
            />
            <DetailTerm
              label="Provider SDK"
              value={
                readModel.high_maturity_spine_readiness.model_provider_management
                  .provider_sdk_call_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
          </dl>
          <p className="safe-copy">
            {
              readModel.high_maturity_spine_readiness.model_provider_management
                .safe_summary
            }
          </p>
          <ul className="ref-list decision-matrix-list">
            {readModel.high_maturity_spine_readiness.model_provider_management.rows
              .slice(0, 4)
              .map((row) => (
                <li key={row.category_id}>
                  <strong>{row.label}</strong> <span>{row.status}</span>
                  <p className="muted">{row.safe_summary}</p>
                  <RefListWithFallback
                    emptyLabel="Model/provider refs: none"
                    refs={[
                      ...row.route_refs.slice(0, 1),
                      ...row.evidence_refs.slice(0, 2),
                      ...row.blocked_authority_refs.slice(0, 1),
                    ]}
                  />
                </li>
              ))}
          </ul>
        </div>
        <div
          className="detail-panel compact"
          aria-label="System-level eval coverage"
        >
          <strong>System-Level Eval Coverage</strong>
          <dl className="detail-list compact">
            <DetailTerm
              label="Contract"
              value={
                readModel.high_maturity_spine_readiness.system_eval_coverage
                  .contract_ref
              }
            />
            <DetailTerm
              label="Coverage"
              value={`${readModel.high_maturity_spine_readiness.system_eval_coverage.implemented_count}/${readModel.high_maturity_spine_readiness.system_eval_coverage.category_count}`}
            />
            <DetailTerm
              label="Model scoring"
              value={
                readModel.high_maturity_spine_readiness.system_eval_coverage
                  .model_intelligence_scored
                  ? "enabled"
                  : "not scored"
              }
            />
          </dl>
          <p className="safe-copy">
            {
              readModel.high_maturity_spine_readiness.system_eval_coverage
                .safe_summary
            }
          </p>
          <ul className="ref-list decision-matrix-list">
            {readModel.high_maturity_spine_readiness.system_eval_coverage.rows
              .slice(0, 4)
              .map((row) => (
                <li key={row.category_id}>
                  <strong>{row.label}</strong> <span>{row.status}</span>
                  <p className="muted">{row.safe_summary}</p>
                  <RefListWithFallback
                    emptyLabel="Eval refs: none"
                    refs={[
                      ...row.evidence_refs.slice(0, 2),
                      ...row.test_refs.slice(0, 1),
                      ...row.invariant_refs.slice(0, 1),
                    ]}
                  />
                </li>
              ))}
          </ul>
        </div>
        <p className="safe-copy">
          {readModel.high_maturity_spine_readiness.next_safe_action}
        </p>
      </article>
      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Request and intent</h3>
            <span>{readModel.capability_status}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm label="Contract" value={readModel.contract_ref} />
            <DetailTerm label="Route" value={readModel.route_ref} />
            <DetailTerm label="CLI" value={readModel.cli_ref} />
            <DetailTerm
              label="Request"
              value={readModel.work_request.request_ref}
            />
            <DetailTerm
              label="Intent"
              value={readModel.intent.ambiguity_state}
            />
            <DetailTerm
              label="Confidence"
              value={readModel.intent.confidence_label}
            />
          </dl>
          <p>{readModel.work_request.safe_summary}</p>
          <div className="detail-panel compact">
            <strong>Reasoning truth</strong>
            <dl className="detail-list compact">
              <DetailTerm
                label="Intent ref"
                value={readModel.reasoning_truth.intent_ref}
              />
              <DetailTerm
                label="Fingerprint"
                value={readModel.reasoning_truth.intent_fingerprint_ref}
              />
              <DetailTerm
                label="Contradictions"
                value={readModel.reasoning_truth.contradiction_posture}
              />
              <DetailTerm
                label="Input posture"
                value={readModel.reasoning_truth.instruction_content_posture}
              />
              <DetailTerm
                label="Model assistance"
                value={readModel.reasoning_truth.model_assistance_posture}
              />
            </dl>
            <p className="muted">
              Input remains untrusted data. Reasoning truth does not grant
              approval, lease, tools, memory, or execution authority.
            </p>
          </div>
          <div className="detail-panel compact">
            <strong>Facts</strong>
            <ul className="ref-list">
              {readModel.reasoning_truth.facts.map((item) => (
                <li key={item.statement_ref}>
                  {item.safe_summary}
                  <RefListWithFallback
                    emptyLabel="Fact evidence: missing"
                    refs={[item.statement_ref, ...item.evidence_refs]}
                  />
                </li>
              ))}
            </ul>
            <strong>Assumptions</strong>
            <ul className="ref-list">
              {readModel.reasoning_truth.assumptions.map((item) => (
                <li key={item.statement_ref}>{item.safe_summary}</li>
              ))}
            </ul>
            <strong>Unknowns</strong>
            <ul className="ref-list">
              {readModel.reasoning_truth.unknowns.map((item) => (
                <li key={item.statement_ref}>{item.safe_summary}</li>
              ))}
            </ul>
            <strong>Questions requiring operator input</strong>
            <ul className="ref-list">
              {readModel.reasoning_truth.operator_questions.map((item) => (
                <li key={item.question_ref}>
                  {item.safe_question}
                  <RefListWithFallback
                    emptyLabel="Question refs: missing"
                    refs={[item.question_ref, ...item.resolves_refs]}
                  />
                </li>
              ))}
            </ul>
          </div>
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>Authority posture</h3>
            <span>
              {readModel.approval_posture.action_execution_enabled
                ? "execution enabled"
                : "proposal only"}
            </span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Python Core truth"
              value={
                readModel.authority_posture.python_core_owns_truth
                  ? "yes"
                  : "no"
              }
            />
            <DetailTerm
              label="Control Center authority"
              value={
                readModel.authority_posture.control_center_mints_authority
                  ? "enabled"
                  : "blocked"
              }
            />
            <DetailTerm
              label="Model calls"
              value={
                readModel.authority_posture.runtime_model_calls_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
            <DetailTerm
              label="Connector writes"
              value={
                readModel.authority_posture.connector_writes_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
            <DetailTerm
              label="Memory write authority"
              value={
                readModel.authority_posture.memory_write_authority_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
            <DetailTerm
              label="Production authority"
              value={
                readModel.authority_posture.production_authority_enabled
                  ? "enabled"
                  : "blocked"
              }
            />
          </dl>
          <RefListWithFallback
            emptyLabel="No blocked authority refs reported"
            refs={readModel.blocked_authority_refs.slice(0, 8)}
          />
        </article>
      </div>

      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Plan proposal</h3>
            <span>{readModel.plan.status}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Revision ref"
              value={readModel.plan_revision.revision_ref}
            />
            <DetailTerm
              label="Revision fingerprint"
              value={readModel.plan_revision.revision_fingerprint_ref}
            />
            <DetailTerm
              label="Decomposition fingerprint"
              value={
                readModel.plan_revision.decomposition
                  .decomposition_fingerprint_ref
              }
            />
            <DetailTerm
              label="Predecessor"
              value={
                readModel.plan_revision.predecessor_revision_ref ??
                "initial revision"
              }
            />
            <DetailTerm
              label="Revision authority"
              value={readModel.plan_revision.authority_posture}
            />
          </dl>
          <p className="muted">{readModel.plan_revision.safe_reason}</p>
          <ul className="ref-list">
            {planSteps.map((step) => (
              <li key={step.step_ref}>
                <strong>{step.title}</strong>: {step.status}; execution{" "}
                {step.execution_enabled ? "enabled" : "blocked"}
                <RefListWithFallback
                  emptyLabel="Step refs: none"
                  refs={[
                    step.step_ref,
                    ...step.evidence_refs,
                    ...step.blocked_state_refs,
                  ]}
                />
              </li>
            ))}
          </ul>
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>Proposed actions</h3>
            <span>{actions.length}</span>
          </div>
          {actions.length > 0 ? (
            <ul className="ref-list">
              {actions.map((action) => (
                <li key={action.action_ref}>
                  <strong>{action.title}</strong>: {action.status};{" "}
                  {action.approval_required
                    ? "approval required"
                    : "inspection only"}
                  <p className="muted">{action.next_safe_action}</p>
                  <RefListWithFallback
                    emptyLabel="Action refs: none"
                    refs={[
                      action.action_ref,
                      action.approval_envelope_ref,
                      ...action.receipt_refs,
                      ...action.evidence_refs,
                    ]}
                  />
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">
              No backend proposed actions were returned for this thread.
            </p>
          )}
        </article>
      </div>

      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Evidence and proof</h3>
            <span>{readModel.evidence.event_count}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Evidence route"
              value={readModel.evidence.route_ref}
            />
          </dl>
          <RefListWithFallback
            emptyLabel="Evidence refs: none"
            refs={readModel.evidence.evidence_refs}
          />
          <RefListWithFallback
            emptyLabel="Proof refs: none"
            refs={readModel.evidence.proof_refs}
          />
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>Memory review</h3>
            <span>{readModel.memory_review.candidate_count}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm
              label="Route"
              value={readModel.memory_review.route_ref}
            />
            <DetailTerm
              label="Automatic writes"
              value={
                readModel.memory_review.automatic_memory_write_authorized
                  ? "enabled"
                  : "blocked"
              }
            />
            <DetailTerm
              label="Context injection"
              value={
                readModel.memory_review.context_injection_authorized
                  ? "enabled"
                  : "blocked"
              }
            />
          </dl>
          <p>{readModel.memory_review.next_safe_action}</p>
          <RefListWithFallback
            emptyLabel="Memory candidate refs: none"
            refs={readModel.memory_review.candidate_refs}
          />
        </article>
      </div>

      <article className="status-card">
        <div className="status-card-header">
          <h3>Surface bindings</h3>
          <span>{bindings.length}</span>
        </div>
        <ul className="ref-list">
          {bindings.map((binding) => (
            <li key={`${binding.surface}:${binding.route_ref}`}>
              {binding.surface}: {binding.route_ref}
            </li>
          ))}
        </ul>
        <p className="safe-copy">
          Next safe decision:{" "}
          {readModel.current_state.next_safe_operator_decision}
        </p>
      </article>
    </section>
  );
}

function OperatorWorkspaceSpinePanel({
  readModel,
}: {
  readModel?: FounderLoopTodaySummary["operator_workspace_spine_read_model"];
}) {
  if (!readModel) {
    return (
      <article className="status-card">
        <div className="status-card-header">
          <h3>Operator Workspace Spine</h3>
          <span>backend read model missing</span>
        </div>
        <p className="muted">
          Control Center will not infer workspace, Git, preview, run-log, or
          coworker posture from UI fallback state.
        </p>
      </article>
    );
  }

  const orderedLanes = readModel.lane_order
    .map((laneKind) =>
      readModel.lanes.find((lane) => lane.lane_kind === laneKind),
    )
    .filter(isPresent);

  return (
    <section
      aria-label="Backend-owned Operator Workspace Spine"
      className="page-section embedded"
    >
      <div className="section-heading compact">
        <div>
          <p className="eyebrow">Beta 11</p>
          <h3>Operator Workspace Spine</h3>
        </div>
        <span className="status-pill compact">
          {readModel.backend_owned ? readModel.status : "mock fallback"}
        </span>
      </div>
      <p className="section-copy">
        Repo work as safe refs: scope, proposal, preview, run evidence, and
        handoff status. No editor, terminal, Git operation, runtime authority,
        or coworker dispatch is exposed here.
      </p>
      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Full Strength Goal</h3>
            <span>planned cockpit</span>
          </div>
          <p>{readModel.full_strength_goal}</p>
          <dl className="detail-list">
            <DetailTerm label="Workspace" value={readModel.workspace_ref} />
            <DetailTerm label="Git posture" value={readModel.git_posture_ref} />
            <DetailTerm
              label="Preview posture"
              value={readModel.preview_status_ref}
            />
          </dl>
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Repo-Safe Scope</h3>
            <span>{readModel.safe_refs_only ? "safe refs" : "unsafe"}</span>
          </div>
          <p>{readModel.repo_safe_scope}</p>
          <dl className="detail-list">
            <DetailTerm label="Source" value={readModel.source} />
            <DetailTerm label="Route" value={readModel.route_ref} />
            <DetailTerm label="CLI" value={readModel.cli_ref} />
          </dl>
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Blocked Authority</h3>
            <span>{readModel.blocked_authority_refs.length}</span>
          </div>
          <p>{readModel.blocked_authority_summary}</p>
          <dl className="detail-list">
            <DetailTerm
              label="File write"
              value={readModel.file_write_enabled ? "unsafe" : "blocked"}
            />
            <DetailTerm
              label="Git mutation"
              value={readModel.git_mutation_enabled ? "unsafe" : "blocked"}
            />
            <DetailTerm
              label="Shell/subprocess"
              value={
                readModel.shell_subprocess_execution_enabled
                  ? "unsafe"
                  : "blocked"
              }
            />
            <DetailTerm
              label="Browser automation"
              value={readModel.browser_automation_enabled ? "unsafe" : "blocked"}
            />
            <DetailTerm
              label="Dev-server lifecycle"
              value={readModel.dev_server_start_enabled ? "unsafe" : "blocked"}
            />
            <DetailTerm
              label="Coworker autonomy"
              value={readModel.background_autonomy_enabled ? "unsafe" : "blocked"}
            />
          </dl>
          <RefList refs={readModel.blocked_authority_refs.slice(0, 6)} />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Authority Readiness</h3>
            <span>mode/domain/lease</span>
          </div>
          <p>{readModel.next_safe_action}</p>
          <RefListWithFallback
            emptyLabel="Authority readiness refs: none"
            refs={readModel.promotion_path_refs}
          />
          <RefListWithFallback
            emptyLabel="Proof refs: none"
            refs={readModel.proof_refs}
          />
        </article>
      </div>
      <article className="status-card">
        <div className="status-card-header">
          <h3>Workspace lanes</h3>
          <span>{orderedLanes.length}</span>
        </div>
        <ul className="ref-list">
          {orderedLanes.map((lane) => (
            <li key={lane.lane_ref}>
              <strong>{lane.label}</strong>: {lane.status}; {lane.safe_summary}
              Next: {lane.next_safe_action}
              <dl className="detail-list compact">
                <DetailTerm label="Posture" value={lane.current_posture_ref} />
                <DetailTerm
                  label="Runtime"
                  value={lane.runtime_execution_enabled ? "unsafe" : "blocked"}
                />
                <DetailTerm
                  label="Mutation"
                  value={lane.mutation_enabled ? "unsafe" : "blocked"}
                />
                <DetailTerm
                  label="Raw content"
                  value={lane.raw_content_included ? "included" : "omitted"}
                />
              </dl>
              <RefListWithFallback
                emptyLabel="Capability refs: none"
                refs={[
                  lane.lane_ref,
                  ...lane.source_refs,
                  ...lane.evidence_refs,
                  ...lane.proof_refs,
                  ...lane.blocked_authority_refs,
                ]}
              />
            </li>
          ))}
        </ul>
      </article>
    </section>
  );
}

function FollowUpTrackerPanel({
  tracker,
}: {
  tracker?: FounderLoopFollowUpTrackerReadModel;
}) {
  if (!tracker) {
    return (
      <article className="status-card">
        <div className="status-card-header">
          <h3>Follow-up tracker</h3>
          <span>backend tracker missing</span>
        </div>
        <p className="muted">
          The backend did not return the Product Loop 004 follow-up tracker.
          Control Center will not infer promises, pending replies, deferred
          decisions, or relationship follow-ups from fallback-only state.
        </p>
      </article>
    );
  }

  const items = tracker.items.slice(0, 8);
  const categoryCounts = {
    relationship_follow_up: tracker.relationship_follow_up_refs.length,
    promise: tracker.promise_refs.length,
    open_loop: tracker.open_loop_refs.length,
    pending_reply: tracker.pending_reply_refs.length,
    deferred_decision: tracker.deferred_decision_refs.length,
  };
  const categoryLabels = {
    relationship_follow_up: "Relationship follow-ups",
    promise: "Promises",
    open_loop: "Open loops",
    pending_reply: "Pending replies",
    deferred_decision: "Deferred decisions",
  };
  return (
    <article className="status-card">
      <div className="status-card-header">
        <h3>Follow-up tracker</h3>
        <span>{tracker.status}</span>
      </div>
      <p>
        Review-only local follow-up refs from backend-owned memory and Founder
        Loop records. No reminders, messages, source fetches, connector runtime,
        task creation, provider calls, memory writes, context injection, action
        execution, or production authority are authorized.
      </p>
      <dl className="detail-list">
        <DetailTerm label="Contract" value={tracker.contract_ref} />
        <DetailTerm label="Source" value={tracker.source} />
        <DetailTerm
          label="Safe refs only"
          value={tracker.safe_refs_only ? "yes" : "no"}
        />
        <DetailTerm
          label="Raw content"
          value={tracker.raw_content_included ? "included" : "omitted"}
        />
        <DetailTerm
          label="Reminder scheduler"
          value={tracker.reminder_scheduler_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Message send"
          value={tracker.message_send_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Connector reads"
          value={tracker.connector_read_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Connector writes"
          value={tracker.connector_write_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Email/calendar fetch"
          value={tracker.email_calendar_fetch_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Task creation"
          value={
            tracker.automatic_task_creation_enabled ? "enabled" : "blocked"
          }
        />
        <DetailTerm
          label="Action execution"
          value={tracker.action_execution_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Runtime model calls"
          value={tracker.runtime_model_calls_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Hidden memory write"
          value={
            tracker.hidden_memory_write_authorized ? "enabled" : "blocked"
          }
        />
        <DetailTerm
          label="Context injection"
          value={tracker.context_injection_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Production authority"
          value={tracker.production_authority_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm label="Boundary" value={tracker.authority_boundary} />
      </dl>
      <ul className="ref-list">
        {tracker.category_order.map((category) => (
          <li key={category}>
            {categoryLabels[category]}: {categoryCounts[category]}
          </li>
        ))}
      </ul>
      <ul className="ref-list">
        {items.map((item) => (
          <li key={item.item_ref}>
            <strong>{item.title}</strong>: {item.status}; {item.why_shown} Next:{" "}
            {item.next_safe_action}
            <dl className="detail-list compact">
              <DetailTerm label="Category" value={item.category} />
              <DetailTerm label="Source state" value={item.source_state} />
              <DetailTerm
                label="Stale state"
                value={item.stale_state ?? "not marked stale"}
              />
              <DetailTerm
                label="No-source state"
                value={item.no_source_state ? "yes" : "no"}
              />
              <DetailTerm
                label="Review required"
                value={item.review_required ? "yes" : "no"}
              />
              <DetailTerm
                label="Local review only"
                value={item.local_review_only ? "yes" : "no"}
              />
              <DetailTerm label="Item boundary" value={item.authority_boundary} />
            </dl>
            <RefListWithFallback
              emptyLabel="Follow-up refs: none"
              refs={[
                item.item_ref,
                item.relationship_ref,
                item.promise_ref,
                item.opportunity_ref,
                item.action_ref,
                ...item.memory_refs,
                ...item.source_refs,
                ...item.evidence_refs,
                ...item.receipt_refs,
                ...item.blocked_state_refs,
              ].filter(isPresent)}
            />
          </li>
        ))}
      </ul>
      <RefListWithFallback
        emptyLabel="No-source follow-ups: none"
        refs={tracker.no_source_refs}
      />
      <RefListWithFallback
        emptyLabel="Stale follow-ups: none"
        refs={tracker.stale_refs}
      />
      <RefListWithFallback
        emptyLabel="Follow-up blocked refs: none"
        refs={tracker.blocked_state_refs}
      />
    </article>
  );
}

function DailyLoopProductBehaviorPanel({
  today,
}: {
  today: FounderLoopTodaySummary;
}) {
  const hasDailyLoop =
    today.daily_loop_summary ||
    today.follow_up_tracker ||
    today.source_readiness_items?.length ||
    today.crm_lite_followups?.length ||
    today.memory_why_shown_items?.length ||
    today.evidence_memory_loop_binding_read_model ||
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
        <SourceReadinessCards
          items={today.source_readiness_items ?? []}
          posture={today.source_readiness_posture}
        />
        <FollowUpTrackerPanel tracker={today.follow_up_tracker} />
        <ReviewQueueGroupCards groups={today.review_queue_groups ?? []} />
        <CrmLiteFollowUpCards items={today.crm_lite_followups ?? []} />
        <MemoryWhyShownCards items={today.memory_why_shown_items ?? []} />
        <EvidenceMemoryLoopBindingPanel
          compact
          readModel={today.evidence_memory_loop_binding_read_model}
        />
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
          <ConnectorReadPlatformCard
            sourceReadiness={sourceReadiness}
          />
          <SourceReadinessProposalCards
            proposals={sourceReadiness.source_readiness_proposal_candidates ?? []}
          />
          <ReadOnlyMetadataContractCards
            contracts={sourceReadiness.read_only_metadata_contracts ?? []}
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

function ReadOnlyMetadataContractCards({
  contracts,
}: {
  contracts: FounderLoopSourceReadiness["read_only_metadata_contracts"];
}) {
  if (contracts.length === 0) {
    return (
      <p className="muted">
        Read-only metadata contracts are unavailable until the backend Source
        Readiness read model supplies contract refs.
      </p>
    );
  }
  return (
    <>
      <p className="eyebrow">Read-only metadata contracts</p>
      <div className="review-grid" aria-label="Read-only metadata contracts">
        {contracts.map((contract) => (
          <article className="review-card" key={contract.contract_ref}>
            <div className="review-card-heading">
              <h3>{contract.source_kind} metadata contract</h3>
              <span>{contract.status}</span>
            </div>
            <p>{contract.safe_summary}</p>
            <dl className="detail-list">
              <DetailTerm label="Contract" value={contract.contract_ref} />
              <DetailTerm label="Route" value={contract.route_ref} />
              <DetailTerm
                label="Backend owned"
                value={contract.backend_owned ? "yes" : "no"}
              />
              <DetailTerm
                label="Contract only"
                value={contract.contract_only ? "yes" : "no"}
              />
              <DetailTerm
                label="Read only"
                value={contract.read_only ? "yes" : "no"}
              />
              <DetailTerm
                label="Metadata only"
                value={contract.metadata_only ? "yes" : "no"}
              />
              <DetailTerm
                label="Account auth"
                value={contract.account_auth_enabled ? "enabled" : "blocked"}
              />
              <DetailTerm
                label="Runtime read"
                value={contract.runtime_read_enabled ? "enabled" : "blocked"}
              />
              <DetailTerm
                label="Raw content"
                value={contract.raw_content_enabled ? "enabled" : "blocked"}
              />
              <DetailTerm
                label="Write"
                value={contract.write_enabled ? "enabled" : "blocked"}
              />
              <DetailTerm
                label="Background"
                value={
                  contract.background_collection_enabled ? "enabled" : "blocked"
                }
              />
              <DetailTerm
                label="Next safe action"
                value={contract.next_safe_action}
              />
            </dl>
            <RefListWithFallback
              emptyLabel="Metadata refs: none"
              refs={contract.metadata_refs}
            />
            <RefListWithFallback
              emptyLabel="Blocked runtime refs: none"
              refs={contract.blocked_runtime_refs}
            />
            <RefListWithFallback
              emptyLabel="Contract evidence refs: none"
              refs={contract.evidence_refs}
            />
          </article>
        ))}
      </div>
    </>
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
          label="Contract"
          value={items[0]?.contract_ref ?? "contract-ref:missing"}
        />
        <DetailTerm
          label="Relationship memory"
          value={items[0]?.relationship_memory_posture ?? "reviewed recall only"}
        />
        <DetailTerm
          label="Redaction"
          value={items[0]?.redaction_status ?? "redacted summary only"}
        />
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
        <DetailTerm
          label="Connector reads"
          value={
            items.some((item) => item.connector_read_authorized)
              ? "enabled"
              : "blocked"
          }
        />
        <DetailTerm
          label="Account sync"
          value={
            items.some((item) => item.account_sync_authorized)
              ? "enabled"
              : "blocked"
          }
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
          label="Hidden memory writes"
          value={
            items.some((item) => item.hidden_memory_write_authorized)
              ? "enabled"
              : "blocked"
          }
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Relationship refs: none"
        refs={items.flatMap((item) => [
          item.relationship_ref,
          item.person_ref,
          item.org_ref,
          item.project_ref,
        ])}
      />
      <RefListWithFallback
        emptyLabel="Opportunity and promise refs: none"
        refs={items.flatMap((item) => [item.opportunity_ref, item.promise_ref])}
      />
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

function EvidenceMemoryLoopBindingPanel({
  compact = false,
  readModel,
}: {
  compact?: boolean;
  readModel?: FounderLoopEvidenceMemoryLoopBindingReadModel;
}) {
  if (!readModel) {
    return (
      <article
        className={`status-card ${compact ? "compact-card" : ""}`}
        aria-label="Evidence and Memory loop binding unavailable"
      >
        <div className="status-card-header">
          <h3>Evidence/Memory loop binding</h3>
          <span>backend proof required</span>
        </div>
        <p>
          Evidence and Memory binding is unavailable until Python Core returns
          a safe backend-owned read model.
        </p>
        <RefListWithFallback
          emptyLabel="Blocked authority refs"
          refs={[
            "blocked-state:evidence-memory-loop:backend-read-model-required",
            "blocked-state:evidence-memory-loop:no-ui-only-truth",
          ]}
        />
      </article>
    );
  }
  const firstMemory = readModel.memory_bindings[0];
  const firstEvidence = readModel.evidence_bindings[0];
  return (
    <article
      className={`status-card ${compact ? "compact-card" : ""}`}
      aria-label="Evidence and Memory loop binding"
    >
      <div className="status-card-header">
        <h3>Evidence/Memory loop binding</h3>
        <span>backend-owned</span>
      </div>
      <p>{readModel.operator_summary}</p>
      <div className="operator-loop-summary-grid">
        <Metric label="evidence links" value={readModel.evidence_binding_count} />
        <Metric label="memory links" value={readModel.memory_binding_count} />
        <Metric label="shared actions" value={readModel.shared_action_refs.length} />
        <Metric label="proof refs" value={readModel.shared_proof_refs.length} />
        <Metric label="receipts" value={readModel.receipt_refs.length} />
      </div>
      <dl className="detail-list">
        <DetailTerm label="Status" value={readModel.status} />
        <DetailTerm label="CLI" value={readModel.cli_ref} />
        <DetailTerm label="Shared loop" value={readModel.shared_loop_ref} />
        <DetailTerm
          label="Reviewed write"
          value={
            readModel.reviewed_memory_write_authorized
              ? "active for accept/correct"
              : "not active"
          }
        />
        <DetailTerm
          label="Write scope"
          value={readModel.reviewed_memory_write_scope_ref}
        />
        <DetailTerm
          label="Broad memory write"
          value={readModel.broad_memory_write_blocked ? "blocked" : "enabled"}
        />
        <DetailTerm
          label="Memory truth"
          value={readModel.memory_truth_authority ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Context injection"
          value={readModel.context_injection_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Action execution"
          value={readModel.action_execution_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Safe disable"
          value={readModel.memory_write_safe_disable_ref}
        />
        <DetailTerm label="Rollback" value={readModel.memory_write_rollback_ref} />
      </dl>
      <RefListWithFallback
        emptyLabel="Shared action refs: none"
        refs={readModel.shared_action_refs}
      />
      <RefListWithFallback
        emptyLabel="Shared proof refs: none"
        refs={readModel.shared_proof_refs}
      />
      <RefListWithFallback
        emptyLabel="Receipt refs: none"
        refs={readModel.receipt_refs}
      />
      <RefListWithFallback
        emptyLabel="Evidence refs: none"
        refs={readModel.evidence_refs}
      />
      {firstMemory ? (
        <div className="compact-stack">
          <p className="muted">Why memory appeared</p>
          <p>{firstMemory.why_shown}</p>
          <dl className="detail-list compact">
            <DetailTerm label="Candidate" value={firstMemory.memory_candidate_ref} />
            <DetailTerm label="Review" value={firstMemory.review_ref} />
            <DetailTerm label="Write posture" value={firstMemory.write_posture} />
            <DetailTerm label="Context posture" value={firstMemory.context_posture} />
          </dl>
          <RefListWithFallback
            emptyLabel="Memory evidence refs: none"
            refs={firstMemory.related_evidence_refs}
          />
          <RefListWithFallback
            emptyLabel="Memory shared action refs: none"
            refs={firstMemory.shared_action_refs}
          />
          <RefListWithFallback
            emptyLabel="Memory shared proof refs: none"
            refs={firstMemory.shared_proof_refs}
          />
        </div>
      ) : null}
      {firstEvidence ? (
        <div className="compact-stack">
          <p className="muted">Why evidence appeared</p>
          <p>{firstEvidence.why_recorded}</p>
          <dl className="detail-list compact">
            <DetailTerm label="Event" value={firstEvidence.event_ref} />
            <DetailTerm label="Timeline item" value={firstEvidence.timeline_item_ref} />
            <DetailTerm label="Group" value={firstEvidence.group_ref} />
          </dl>
          <RefListWithFallback
            emptyLabel="Evidence proof refs: none"
            refs={firstEvidence.proof_refs}
          />
          <RefListWithFallback
            emptyLabel="Evidence action refs: none"
            refs={firstEvidence.action_refs}
          />
          <RefListWithFallback
            emptyLabel="Evidence receipt refs: none"
            refs={firstEvidence.receipt_refs}
          />
        </div>
      ) : null}
      <RefListWithFallback
        emptyLabel="Run refs: none"
        refs={readModel.run_refs}
      />
      <RefListWithFallback
        emptyLabel="Blocked authority refs: none"
        refs={readModel.blocked_authority_refs}
      />
      <RefListWithFallback
        emptyLabel="Authority readiness refs: none"
        refs={readModel.promotion_path_refs}
      />
      <p className="muted">{readModel.next_safe_action}</p>
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
        emptyLabel="Completed refs: none"
        refs={narrative.completed_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Deferred refs: none"
        refs={narrative.deferred_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Rejected refs: none"
        refs={narrative.rejected_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Planned refs: none"
        refs={narrative.planned_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Memory change refs: none"
        refs={narrative.memory_change_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="CRM movement refs: none"
        refs={narrative.crm_movement_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Draft refs: none"
        refs={narrative.draft_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Next-week priority refs: none"
        refs={narrative.next_week_priority_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Carry-forward refs: none"
        refs={narrative.carry_forward_refs}
      />
      <RefListWithFallback
        emptyLabel="Blocked refs: none"
        refs={narrative.blocked_refs}
      />
      <RefListWithFallback
        emptyLabel="Stale refs: none"
        refs={narrative.stale_refs}
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

function WeeklyCeoReviewV1Panel({
  readModel,
}: {
  readModel?: FounderLoopWeeklyCeoReviewV1ReadModel;
}) {
  if (!readModel) {
    return null;
  }
  return (
    <article
      aria-label="Backend-owned Weekly CEO Review V1 read model"
      className="status-card"
    >
      <div className="status-card-header">
        <h3>Weekly CEO Review V1</h3>
        <span>{readModel.status}</span>
      </div>
      <p className="eyebrow">Review artifact</p>
      <p className="section-copy">{readModel.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Contract" value={readModel.contract_ref} />
        <DetailTerm label="Source" value={readModel.source} />
        <DetailTerm label="Review period" value={readModel.review_period_ref} />
        <DetailTerm label="Completed" value={String(readModel.completed_count)} />
        <DetailTerm label="Deferred" value={String(readModel.deferred_count)} />
        <DetailTerm label="Rejected" value={String(readModel.rejected_count)} />
        <DetailTerm label="Blocked" value={String(readModel.blocked_count)} />
        <DetailTerm label="Stale" value={String(readModel.stale_count)} />
        <DetailTerm label="Unresolved" value={String(readModel.unresolved_count)} />
        <DetailTerm
          label="Action decisions"
          value={String(readModel.action_decision_count)}
        />
        <DetailTerm
          label="Memory decisions"
          value={String(readModel.memory_decision_count)}
        />
        <DetailTerm label="Follow-ups" value={String(readModel.follow_up_count)} />
        <DetailTerm
          label="Evidence events"
          value={String(readModel.evidence_event_count)}
        />
        <DetailTerm
          label="Connector runtime"
          value={readModel.connector_runtime_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Model summaries"
          value={readModel.model_summary_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Provider/model calls"
          value={readModel.provider_model_call_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Action execution"
          value={readModel.action_execution_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Production claim"
          value={readModel.production_claim_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm label="Authority" value={readModel.authority_boundary} />
        <DetailTerm label="Next safe action" value={readModel.next_safe_action} />
      </dl>
      <RefListWithFallback
        emptyLabel="Completed refs: none"
        refs={readModel.completed_refs}
      />
      <RefListWithFallback
        emptyLabel="Deferred refs: none"
        refs={readModel.deferred_refs}
      />
      <RefListWithFallback
        emptyLabel="Rejected refs: none"
        refs={readModel.rejected_refs}
      />
      <RefListWithFallback
        emptyLabel="Blocked refs: none"
        refs={readModel.blocked_refs}
      />
      <RefListWithFallback
        emptyLabel="Stale refs: none"
        refs={readModel.stale_refs}
      />
      <RefListWithFallback
        emptyLabel="Unresolved refs: none"
        refs={readModel.unresolved_refs}
      />
      <RefListWithFallback
        emptyLabel="Action decision refs: none"
        refs={readModel.action_decision_refs}
      />
      <RefListWithFallback
        emptyLabel="Memory decision refs: none"
        refs={readModel.memory_decision_refs}
      />
      <RefListWithFallback
        emptyLabel="Follow-up refs: none"
        refs={readModel.follow_up_refs}
      />
      <RefListWithFallback
        emptyLabel="Evidence refs: none"
        refs={readModel.evidence_refs}
      />
      <RefListWithFallback
        emptyLabel="Evidence event refs: none"
        refs={readModel.evidence_event_refs}
      />
      <RefListWithFallback
        emptyLabel="Receipt refs: none"
        refs={readModel.receipt_refs}
      />
      <RefListWithFallback
        emptyLabel="Missing source refs: none"
        refs={readModel.missing_source_refs}
      />
      <RefListWithFallback
        emptyLabel="Weekly review authority blockers: missing"
        refs={readModel.blocked_authority_refs}
      />
    </article>
  );
}

function FounderLoopProductProofPanel({
  readModel,
}: {
  readModel?: FounderLoopProductProofReadModel;
}) {
  if (!readModel) {
    return null;
  }
  return (
    <section
      aria-label="Founder Loop V1 product proof"
      className="compact-stack"
    >
      <article className="status-card">
        <div className="status-card-header">
          <h3>Founder Loop V1 product proof</h3>
          <span>{readModel.status}</span>
        </div>
        <p className="eyebrow">Backend-owned proof pass</p>
        <p className="section-copy">{readModel.safe_summary}</p>
        <dl className="detail-list">
          <DetailTerm label="Contract" value={readModel.contract_ref} />
          <DetailTerm label="Source" value={readModel.source} />
          <DetailTerm label="Scenario" value={readModel.scenario_ref} />
          <DetailTerm label="Shared state" value={readModel.shared_state_ref} />
          <DetailTerm
            label="Decision receipts"
            value={readModel.decision_receipt_status}
          />
          <DetailTerm
            label="Memory review"
            value={
              readModel.memory_review_status === "candidate_available"
                ? "candidate visible"
                : "none"
            }
          />
          <DetailTerm label="Weekly review" value={readModel.weekly_review_status} />
          <DetailTerm
            label="Provider/model calls"
            value={readModel.provider_model_call_enabled ? "unsafe" : "blocked"}
          />
          <DetailTerm
            label="Browser/live web"
            value={
              readModel.browser_execution_enabled || readModel.live_web_enabled
                ? "unsafe"
                : "blocked"
            }
          />
          <DetailTerm
            label="Connector writes"
            value={readModel.connector_write_enabled ? "unsafe" : "blocked"}
          />
          <DetailTerm
            label="Background autonomy"
            value={readModel.background_autonomy_enabled ? "unsafe" : "blocked"}
          />
          <DetailTerm
            label="Production authority"
            value={readModel.production_authority_enabled ? "unsafe" : "blocked"}
          />
          <DetailTerm label="Authority" value={readModel.authority_boundary} />
          <DetailTerm label="Next safe action" value={readModel.next_safe_action} />
        </dl>
        <InlineListWithFallback
          emptyLabel="Decision labels: approve, edit, reject, defer"
          items={readModel.supported_decision_actions.map(
            (decision) => `decision: ${decision}`,
          )}
        />
        <RefListWithFallback
          emptyLabel="Receipt refs: none recorded"
          refs={readModel.receipt_refs}
        />
        <RefListWithFallback
          emptyLabel="Memory review candidate: none"
          refs={readModel.memory_review_candidate_refs}
        />
        <RefListWithFallback
          emptyLabel="Evidence refs: none recorded"
          refs={readModel.evidence_refs}
        />
        <RefListWithFallback
          emptyLabel="Evidence event refs: none"
          refs={readModel.evidence_event_refs}
        />
        <RefListWithFallback
          emptyLabel="Blocked authority refs: missing"
          refs={readModel.blocked_authority_refs}
        />
      </article>
      <div className="review-grid">
        {readModel.steps.map((step, index) => (
          <article className="review-card" key={step.step_id}>
            <div className="review-card-heading">
              <h3>
                {index + 1}. {step.surface}
              </h3>
              <span>{step.status}</span>
            </div>
            <p>{step.safe_summary}</p>
            <dl className="detail-list">
              <DetailTerm label="Backend" value={step.backend_route_ref} />
              <DetailTerm label="Route" value={step.frontend_route_ref} />
              <DetailTerm label="Next" value={step.next_safe_action} />
            </dl>
            <RefListWithFallback
              emptyLabel="Source refs: none"
              refs={step.source_refs}
            />
            <RefListWithFallback
              emptyLabel="Receipt refs: none"
              refs={step.receipt_refs}
            />
            <RefListWithFallback
              emptyLabel="Evidence refs: none"
              refs={step.evidence_refs}
            />
            <RefListWithFallback
              emptyLabel="Blocked refs: none"
              refs={step.blocked_state_refs}
            />
          </article>
        ))}
      </div>
    </section>
  );
}

function FounderLoopRunsIntegrationPanel({
  compact = false,
  focus,
  readModel,
}: {
  compact?: boolean;
  focus?: FounderLoopRunsIntegrationSurfaceId;
  readModel?: FounderLoopRunsIntegrationReadModel;
}) {
  if (!readModel) {
    return null;
  }
  const focusedBinding = focus
    ? readModel.surface_bindings.find((binding) => binding.surface_id === focus)
    : undefined;
  const visibleBindings = compact
    ? readModel.surface_bindings.filter(
        (binding) => !focus || binding.surface_id === focus,
      )
    : readModel.surface_bindings;

  return (
    <section
      aria-label="Founder Loop run and proof refs"
      className="compact-stack founder-loop-runs-integration"
    >
      <article className="status-card">
        <div className="status-card-header">
          <h3>Run and proof refs</h3>
          <span>{readModel.status}</span>
        </div>
        <p className="eyebrow">Backend-owned provenance</p>
        <p className="section-copy">{readModel.authority_boundary}</p>
        <dl className="detail-list">
          <DetailTerm label="Contract" value={readModel.contract_ref} />
          <DetailTerm label="Source" value={readModel.source} />
          <DetailTerm label="Run" value={readModel.primary_run_ref} />
          <DetailTerm label="Proof" value={readModel.primary_proof_ref} />
          <DetailTerm label="UI truth" value={readModel.ui_truth_source} />
          <DetailTerm label="Action origin" value={readModel.action_origin_posture} />
          <DetailTerm
            label="Decision receipts"
            value={readModel.decision_receipt_posture}
          />
          <DetailTerm label="Evidence path" value={readModel.evidence_path_posture} />
          <DetailTerm label="Proof detail" value={readModel.proof_detail_posture} />
          <DetailTerm label="Memory" value={readModel.memory_candidate_posture} />
          <DetailTerm label="Weekly review" value={readModel.weekly_review_posture} />
          <DetailTerm
            label="Execution"
            value={readModel.action_execution_enabled ? "unsafe" : "blocked"}
          />
          <DetailTerm
            label="Approval authority"
            value={readModel.approval_authority_enabled ? "unsafe" : "blocked"}
          />
          <DetailTerm
            label="Provider/model calls"
            value={readModel.provider_model_call_enabled ? "unsafe" : "blocked"}
          />
          <DetailTerm
            label="Connector sends"
            value={readModel.connector_send_enabled ? "unsafe" : "blocked"}
          />
          <DetailTerm
            label="Production authority"
            value={readModel.production_authority_enabled ? "unsafe" : "blocked"}
          />
          <DetailTerm label="Next" value={readModel.next_safe_action} />
        </dl>
        <RefListWithFallback
          emptyLabel="Run refs: none"
          refs={readModel.run_refs}
        />
        <RefListWithFallback
          emptyLabel="Proof refs: none"
          refs={readModel.proof_refs}
        />
        <RefListWithFallback
          emptyLabel="Receipt refs: none recorded"
          refs={readModel.receipt_refs}
        />
        <RefListWithFallback
          emptyLabel="Evidence event refs: none"
          refs={readModel.evidence_event_refs}
        />
        <RefListWithFallback
          emptyLabel="Operator run event refs: none"
          refs={readModel.operator_run_event_refs}
        />
        <RefListWithFallback
          emptyLabel="Blocked authority refs: missing"
          refs={readModel.blocked_authority_refs}
        />
      </article>
      {focusedBinding ? (
        <article className="status-card">
          <div className="status-card-header">
            <h3>{focusedBinding.surface} trace</h3>
            <span>{focusedBinding.status}</span>
          </div>
          <p className="section-copy">{focusedBinding.safe_summary}</p>
          <dl className="detail-list">
            <DetailTerm label="This came from run" value={focusedBinding.run_ref} />
            <DetailTerm
              label="Proof detail"
              value={focusedBinding.proof_detail_ref}
            />
            <DetailTerm
              label="Proof route"
              value={focusedBinding.proof_detail_route_ref}
            />
            <DetailTerm label="Backend route" value={focusedBinding.backend_route_ref} />
            <DetailTerm label="Frontend route" value={focusedBinding.frontend_route_ref} />
            <DetailTerm label="Next" value={focusedBinding.next_safe_action} />
          </dl>
          <RefListWithFallback
            emptyLabel="Action source refs: none"
            refs={focusedBinding.action_source_refs}
          />
          <RefListWithFallback
            emptyLabel="Approval refs: identifiers only or none"
            refs={focusedBinding.approval_refs}
          />
          <RefListWithFallback
            emptyLabel="Receipt refs: none recorded"
            refs={focusedBinding.receipt_refs}
          />
          <RefListWithFallback
            emptyLabel="Evidence refs: none"
            refs={focusedBinding.evidence_refs}
          />
          <RefListWithFallback
            emptyLabel="Memory candidate refs: explicit none"
            refs={focusedBinding.memory_candidate_refs}
          />
        </article>
      ) : null}
      {!compact ? (
        <div className="review-grid">
          {visibleBindings.map((binding) => (
            <article className="review-card" key={binding.surface_id}>
              <div className="review-card-heading">
                <h3>{binding.surface}</h3>
                <span>{binding.status}</span>
              </div>
              <p>{binding.safe_summary}</p>
              <dl className="detail-list">
                <DetailTerm label="Run" value={binding.run_ref} />
                <DetailTerm label="Proof" value={binding.proof_ref} />
                <DetailTerm label="Proof detail" value={binding.proof_detail_ref} />
              </dl>
              <RefListWithFallback
                emptyLabel="Receipt refs: none"
                refs={binding.receipt_refs}
              />
              <RefListWithFallback
                emptyLabel="Evidence refs: none"
                refs={binding.evidence_refs}
              />
              <RefListWithFallback
                emptyLabel="Blocked refs: none"
                refs={binding.blocked_state_refs}
              />
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function UnifiedWorkThreadPanel({
  readModel,
}: {
  readModel?: FounderLoopUnifiedWorkThreadReadModel;
}) {
  if (!readModel) {
    return null;
  }
  return (
    <section
      aria-label="Unified Work Thread"
      className="compact-stack unified-work-thread"
    >
      <article className="status-card">
        <div className="status-card-header">
          <h3>Unified Work Thread</h3>
          <span>{readModel.status}</span>
        </div>
        <p className="eyebrow">Backend-owned read model</p>
        <p className="section-copy">{readModel.safe_summary}</p>
        <p className="section-copy">{readModel.authority_boundary}</p>
        <dl className="detail-list">
          <DetailTerm label="Contract" value={readModel.contract_ref} />
          <DetailTerm label="Source" value={readModel.source} />
          <DetailTerm label="Thread" value={readModel.thread_ref} />
          <DetailTerm label="Title" value={readModel.thread_title} />
          <DetailTerm
            label="Provider/model calls"
            value={readModel.provider_model_call_enabled ? "unsafe" : "blocked"}
          />
          <DetailTerm
            label="Connector read/write"
            value={
              readModel.connector_read_enabled || readModel.connector_write_enabled
                ? "unsafe"
                : "blocked"
            }
          />
          <DetailTerm
            label="Execution"
            value={readModel.action_execution_enabled ? "unsafe" : "blocked"}
          />
          <DetailTerm
            label="Memory/context"
            value={
              readModel.memory_write_authorized ||
              readModel.context_injection_authorized
                ? "unsafe"
                : "blocked"
            }
          />
          <DetailTerm
            label="Production authority"
            value={readModel.production_authority_enabled ? "unsafe" : "blocked"}
          />
          <DetailTerm label="Next safe action" value={readModel.next_safe_action} />
        </dl>
        <div className="loop-authority-strip">
          <span>No action execution</span>
          <span>No provider/model calls</span>
          <span>No A2A/MCP runtime dispatch</span>
          <span>No browser/live web</span>
          <span>No connector read/write</span>
          <span>No email/calendar sends</span>
          <span>No CRM/account sync</span>
          <span>No shell/subprocess execution</span>
          <span>No memory writes/context injection</span>
          <span>No background autonomy</span>
          <span>No public beta/release claims</span>
          <span>No production authority</span>
        </div>
        <RefListWithFallback
          emptyLabel="Thread receipt refs: none recorded"
          refs={readModel.receipt_refs}
        />
        <RefListWithFallback
          emptyLabel="Thread evidence refs: none recorded"
          refs={readModel.evidence_refs}
        />
        <RefListWithFallback
          emptyLabel="Memory Review candidate refs: none"
          refs={readModel.memory_review_candidate_refs}
        />
        <RefListWithFallback
          emptyLabel="Blocked authority refs: missing"
          refs={readModel.blocked_authority_refs}
        />
      </article>
      <div className="review-grid unified-work-thread-grid">
        {readModel.steps.map((step, index) => (
          <article className="review-card" key={step.step_id}>
            <div className="review-card-heading">
              <h3>
                {index + 1}. {step.surface}
              </h3>
              <span>{step.status}</span>
            </div>
            <p>{step.safe_summary}</p>
            <dl className="detail-list">
              <DetailTerm label="Route" value={step.frontend_route_ref} />
              <DetailTerm label="Backend" value={step.backend_route_ref} />
              <DetailTerm label="Next" value={step.next_safe_action} />
            </dl>
            <RefListWithFallback
              emptyLabel="Source refs: none"
              refs={step.source_refs}
            />
            <RefListWithFallback
              emptyLabel="Proposal refs: none"
              refs={step.proposal_refs}
            />
            <RefListWithFallback
              emptyLabel="Receipt refs: none"
              refs={step.receipt_refs}
            />
            <RefListWithFallback
              emptyLabel="Evidence refs: none"
              refs={step.evidence_refs}
            />
            <RefListWithFallback
              emptyLabel="Blocked refs: none"
              refs={step.blocked_authority_refs}
            />
          </article>
        ))}
      </div>
    </section>
  );
}

export function ChatToLoopHandoffPanel({
  compact = false,
  readModel,
}: {
  compact?: boolean;
  readModel?: FounderLoopChatToLoopHandoffReadModel;
}) {
  if (!readModel) {
    return null;
  }
  const visibleOutcomes = compact
    ? readModel.outcomes.slice(0, 3)
    : readModel.outcomes;
  return (
    <article
      aria-label="Backend-owned Chat to Loop handoff read model"
      className="status-card"
    >
      <div className="status-card-header">
        <h3>Chat to Loop Handoff</h3>
        <span>{readModel.status}</span>
      </div>
      <p className="eyebrow">Proposal-only</p>
      <p className="section-copy">{readModel.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Contract" value={readModel.contract_ref} />
        <DetailTerm label="Source" value={readModel.source} />
        <DetailTerm label="Outcomes" value={String(readModel.outcome_count)} />
        <DetailTerm
          label="Turn receipts"
          value={String(readModel.turn_receipt_count)}
        />
        <DetailTerm
          label="Handoff receipts"
          value={String(readModel.handoff_receipt_count)}
        />
        <DetailTerm
          label="Memory write"
          value={readModel.direct_memory_write_authorized ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Action execution"
          value={readModel.action_execution_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Model output authority"
          value={readModel.model_output_authority ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Next safe action"
          value={readModel.next_safe_action}
        />
      </dl>
      <div className="note-list" aria-label="Chat to Loop handoff outcomes">
        {visibleOutcomes.map((outcome) => (
          <span key={outcome.outcome_ref}>
            {outcome.safe_label}: {outcome.state}; {outcome.target_surface};{" "}
            {outcome.proposal_ref}
          </span>
        ))}
      </div>
      <RefListWithFallback
        emptyLabel="Outcome refs: none"
        refs={readModel.outcome_refs}
      />
      <RefListWithFallback
        emptyLabel="Handoff receipt refs: none"
        refs={readModel.handoff_receipt_refs}
      />
      <RefListWithFallback
        emptyLabel="Memory proposal refs: none"
        refs={readModel.memory_proposal_refs}
      />
      <RefListWithFallback
        emptyLabel="Chat-to-loop blockers: missing"
        refs={readModel.blocked_state_refs}
      />
    </article>
  );
}

export function ActionInboxSurfacePanel({
  actionReadModelAuthoritative,
  approvalReview,
  inbox,
  providerCredentialReadiness,
  today,
}: {
  actionReadModelAuthoritative: boolean;
  approvalReview?: RunAttachedApprovalQueue;
  inbox: FounderLoopActionsInbox;
  providerCredentialReadiness?: ProviderCredentialReadinessSummary;
  today?: FounderLoopTodaySummary;
}) {
  const [selectedActionGroup, setSelectedActionGroup] = useState<
    FounderLoopActionGroupId | "all"
  >("all");
  const [reconciledItemsByRef, setReconciledItemsByRef] = useState<
    Record<string, FounderLoopActionItem>
  >({});
  const inboxIdentity = inbox.items
    .map((item) => `${item.item_ref}:${item.updated_at ?? ""}`)
    .join("|");
  useEffect(() => {
    setReconciledItemsByRef({});
  }, [inbox.storage_ref, inboxIdentity]);
  const displayedInbox = {
    ...inbox,
    items: inbox.items.map((item) => reconciledItemsByRef[item.item_ref] ?? item),
  };
  const actionGroups = buildActionLaneGroups(displayedInbox);
  const visibleActionGroups =
    selectedActionGroup === "all"
      ? actionGroups
      : actionGroups.filter(
          (group) => group.summary.group_id === selectedActionGroup,
        );
  const selectedActionGroupSummary =
    selectedActionGroup === "all"
      ? null
      : actionGroups.find(
          (group) => group.summary.group_id === selectedActionGroup,
        ) ?? null;
  const selectedWorkQueueLane =
    selectedActionGroup === "all"
      ? null
      : displayedInbox.action_inbox_work_queue_read_model?.lanes.find(
          (lane) => lane.lane_id === selectedActionGroup,
        ) ?? null;
  const selectedActionGroupItems =
    selectedActionGroupSummary?.items ?? displayedInbox.items;
  const backendOwnedItemCount = selectedActionGroupItems.filter(
    hasAuthoritativeActionReadModel,
  ).length;
  const unavailableItemCount =
    selectedActionGroupItems.length - backendOwnedItemCount;

  function reconcileActionItem(item: FounderLoopActionItem) {
    setReconciledItemsByRef((current) => ({
      ...current,
      [item.item_ref]: item,
    }));
  }

  return (
    <section className="page-section" aria-labelledby="actions-surface-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Founder Loop</p>
          <h2 id="actions-surface-heading">Action Inbox</h2>
        </div>
        <span className="status-pill compact">{inbox.status}</span>
      </div>
      <ActionInboxOperatorOverview
        actionGroups={actionGroups}
        inbox={displayedInbox}
      />
      <ActionInboxWorkQueuePanel
        readModel={displayedInbox.action_inbox_work_queue_read_model}
      />
      <ActionToolCodeLaneCatalogPanel
        contractRef={displayedInbox.action_tool_code_lane_catalog_contract_ref}
        readModel={displayedInbox.action_tool_code_lane_catalog_read_model}
      />
      <RuntimeActionInboxBridgePanel
        contractRef={displayedInbox.runtime_action_inbox_bridge_contract_ref}
        readModel={displayedInbox.runtime_action_inbox_bridge_read_model}
      />
      <FounderLoopRunsIntegrationPanel
        compact
        focus="action_inbox"
        readModel={today?.founder_loop_runs_integration_read_model}
      />
      {approvalReview ? (
        <>
          <ActionInboxApprovalReviewStrip queue={approvalReview} />
          <ConnectorDeliveryReviewQueuePanel
            compact
            queue={approvalReview.connector_delivery_review_queue}
          />
        </>
      ) : null}
      <ActionInboxDecisionLanePanel
        contractRef={displayedInbox.action_inbox_decision_lane_contract_ref}
        readModel={displayedInbox.action_inbox_decision_lane_read_model}
      />
      <PlansToActionsBridgePanel
        contractRef={displayedInbox.plans_to_actions_bridge_contract_ref}
        readModel={displayedInbox.plans_to_actions_bridge_read_model}
      />
      {providerCredentialReadiness ? (
        <ActionInboxProviderCostPosture readiness={providerCredentialReadiness} />
      ) : null}
      <ChatToLoopHandoffPanel
        compact
        readModel={displayedInbox.chat_to_loop_handoff_read_model}
      />
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
            label="Receipt/local-task controls"
            value={
              inbox.mutating_controls_enabled
                ? "receipt and exact local-task controls only"
                : "disabled"
            }
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
            label="Full-strength version"
            value={
              inbox.private_beta_readiness_full_strength_goal ??
              "local-first operator workflow not available"
            }
          />
          <DetailTerm
            label="Repo-safe version"
            value={
              inbox.private_beta_readiness_repo_safe_scope ??
              "backend-owned safe refs unavailable"
            }
          />
          <DetailTerm
            label="Blocked / needs authority"
            value={
              inbox.private_beta_readiness_blocked_authority_summary ??
              "blocked authority summary unavailable"
            }
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
          <DetailTerm
            label="Distribution claim"
            value={
              inbox.private_beta_readiness_authority_posture
                ?.public_distribution_claim_enabled
                ? "enabled"
                : "blocked"
            }
          />
          <DetailTerm
            label="Production readiness"
            value={
              inbox.private_beta_readiness_authority_posture
                ?.production_readiness_claim_enabled
                ? "enabled"
                : "blocked"
            }
          />
          <DetailTerm
            label="Production authority"
            value={
              inbox.private_beta_readiness_authority_posture
                ?.production_authority_enabled
                ? "enabled"
                : "blocked"
            }
          />
        </dl>
        <div className="status-card-header">
          <h3>Exact promotion path</h3>
          <span>{inbox.private_beta_readiness_promotion_path_refs?.length ?? 0}</span>
        </div>
        <RefListWithFallback
          emptyLabel="Exact promotion path: missing"
          refs={inbox.private_beta_readiness_promotion_path_refs ?? []}
        />
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
      inbox.source_readiness_proposal_candidates?.length ||
      inbox.follow_up_tracker ||
      inbox.crm_lite_followups?.length ||
      inbox.memory_why_shown_items?.length ||
      inbox.review_queue_groups?.length ||
      inbox.dogfood_capture ? (
        <div className="panel-grid">
          <SourceReadinessCards items={inbox.source_readiness_items ?? []} />
          <article className="status-card">
            <div className="status-card-header">
              <h3>Source readiness proposals</h3>
              <span>{inbox.source_readiness_proposal_candidates?.length ?? 0}</span>
            </div>
            <p>
              Backend-owned proposal candidates from the dedicated source
              readiness read model. They are proposal-only and expose no
              connector, auth, ingestion, write, or execution authority.
            </p>
            <dl className="detail-list">
              <DetailTerm
                label="Binding contract"
                value={
                  inbox.source_readiness_proposal_binding_contract_ref ?? "missing"
                }
              />
              <DetailTerm
                label="Source readiness route"
                value={inbox.source_readiness_route_ref ?? "missing"}
              />
            </dl>
          </article>
          <FollowUpTrackerPanel tracker={inbox.follow_up_tracker} />
          <ReviewQueueGroupCards groups={inbox.review_queue_groups ?? []} />
          <CrmLiteFollowUpCards items={inbox.crm_lite_followups ?? []} />
          <MemoryWhyShownCards items={inbox.memory_why_shown_items ?? []} />
          <DogfoodCaptureCard capture={inbox.dogfood_capture} />
        </div>
      ) : null}
      <div className="review-grid">
        <SourceReadinessProposalCards
          proposals={inbox.source_readiness_proposal_candidates ?? []}
        />
        <TaskDecompositionProposalSummaryCard inbox={inbox} />
        {(inbox.memory_derived_action_proposals ?? []).map((proposal) => (
          <MemoryDerivedActionProposalCard
            key={proposal.proposal_ref}
            proposal={proposal}
          />
        ))}
      </div>
      <article
        aria-label="Action Inbox queue group filters and drilldown"
        className="status-card action-lane-filter-card"
      >
        <div className="status-card-header">
          <h3>Queue group filters</h3>
          <span>{selectedActionGroup === "all" ? "all" : selectedActionGroup}</span>
        </div>
        <div
          aria-label="Action Inbox queue group filters"
          className="action-lane-filter-row"
        >
          <button
            aria-pressed={selectedActionGroup === "all"}
            className="secondary-button"
            onClick={() => setSelectedActionGroup("all")}
            type="button"
          >
            Filter group: All groups ({displayedInbox.items.length})
          </button>
          {actionGroups.map((group) => (
            <button
              aria-pressed={selectedActionGroup === group.summary.group_id}
              className="secondary-button"
              key={group.summary.group_id}
              onClick={() => setSelectedActionGroup(group.summary.group_id)}
              type="button"
            >
              Filter group: {group.summary.label} ({group.summary.count})
            </button>
          ))}
        </div>
        <dl
          aria-label="Selected Action Inbox queue group drilldown"
          className="detail-list"
        >
          <DetailTerm
            label="Selected group"
            value={selectedActionGroup === "all" ? "all_groups" : selectedActionGroup}
          />
          <DetailTerm
            label="Visible items"
            value={String(selectedActionGroupItems.length)}
          />
          <DetailTerm
            label="Backend-owned read-model items"
            value={String(backendOwnedItemCount)}
          />
          <DetailTerm
            label="Unavailable/mock-only items"
            value={String(unavailableItemCount)}
          />
          <DetailTerm
            label="Available action"
            value={
              selectedActionGroupSummary?.summary.available_action ??
              "Inspect every backend-classified group without adding authority."
            }
          />
          <DetailTerm
            label="Group reason"
            value={
              selectedActionGroupSummary?.summary.safe_summary ??
              "All backend-classified groups are visible."
            }
          />
          <DetailTerm
            label="Work queue status"
            value={selectedWorkQueueLane?.status ?? "all_groups"}
          />
        </dl>
        <RefListWithFallback
          emptyLabel="Selected group blockers: none"
          refs={selectedWorkQueueLane?.blocked_authority_refs ?? []}
        />
        <p className="muted">
          Filters and drilldowns are presentation-only. Group membership,
          eligibility, envelope posture, and receipt visibility remain supplied
          by the backend Action Inbox read model.
        </p>
      </article>
      <div className="action-lane-stack" aria-label="Action Inbox queue groups">
        {visibleActionGroups.map((group) => (
          <ActionLaneSection
            actionReadModelAuthoritative={actionReadModelAuthoritative}
            group={group}
            key={group.summary.group_id}
            onReconciledItem={reconcileActionItem}
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

function ActionInboxApprovalReviewStrip({
  queue,
}: {
  queue: RunAttachedApprovalQueue;
}) {
  const review = queue.unified_review;
  const sourceLabel = review.backend_owned
    ? "backend-owned"
    : "mock-only / non-authoritative";
  return (
    <article className="status-card" aria-label="Action Inbox approval review">
      <div className="status-card-header">
        <h3>Approval review</h3>
        <span>{sourceLabel}</span>
      </div>
      <p>
        {review.safe_summary} Approval refs are identifiers only; this Action
        Inbox strip has no approve, deny, revoke, resume, execute, connector
        send, provider call, worker, or scheduler control.
      </p>
      <dl className="detail-list">
        <DetailTerm label="Review items" value={String(review.history_count)} />
        <DetailTerm label="Pending refs" value={String(review.pending_count)} />
        <DetailTerm label="Blocked refs" value={String(review.blocked_count)} />
        <DetailTerm label="Route" value={review.route_ref} />
        <DetailTerm label="CLI" value={review.cli_ref} />
      </dl>
      <RefList refs={review.blocked_authority_refs.slice(0, 8)} />
    </article>
  );
}

function ActionInboxDecisionLanePanel({
  contractRef,
  readModel,
}: {
  contractRef?: string;
  readModel?: FounderLoopActionInboxDecisionLaneReadModel;
}) {
  if (!readModel) {
    return (
      <article className="status-card">
        <div className="status-card-header">
          <h3>Decision groups</h3>
          <span>backend decision groups missing</span>
        </div>
        <p>
          Backend-owned decision-group posture is unavailable. The UI will not
          backfill cost, authority, approval, or receipt groups from mock data.
        </p>
        <dl className="detail-list">
          <DetailTerm
            label="Approval alone"
            value="does not execute without exact backend scope"
          />
          <DetailTerm label="Action execution" value="blocked" />
          <DetailTerm label="Provider/model calls" value="blocked" />
        </dl>
      </article>
    );
  }
  const laneById = new Map(readModel.lanes.map((lane) => [lane.lane_id, lane]));
  return (
    <>
      <article className="status-card">
        <div className="status-card-header">
          <h3>Decision groups</h3>
          <span>{readModel.status}</span>
        </div>
        <p>
          Backend-owned groups show approval, cost, provider/model, evidence,
          and expected receipt posture before any operator decision. Approval
          alone does not execute work.
        </p>
        <dl className="detail-list">
          <DetailTerm
            label="Contract"
            value={contractRef ?? readModel.contract_ref}
          />
          <DetailTerm label="Source" value={readModel.source} />
          <DetailTerm
            label="Missing envelope fields"
            value={
              readModel.missing_envelope_fields_fail_safe
                ? "fail safe"
                : "unchecked"
            }
          />
          <DetailTerm
            label="Cost before approval"
            value={
              readModel.cost_posture_visible_before_approval
                ? "visible"
                : "missing"
            }
          />
          <DetailTerm
            label="Provider authority"
            value={
              readModel.provider_authority_visible_before_approval
                ? "visible"
                : "missing"
            }
          />
          <DetailTerm
            label="Cost labels"
            value="accounting readiness only; no provider calls"
          />
          <DetailTerm
            label="Approval alone"
            value={readModel.approval_alone_executes ? "unsafe" : "does not execute"}
          />
          <DetailTerm
            label="Action execution"
            value={readModel.action_execution_enabled ? "unsafe" : "blocked"}
          />
        </dl>
        <InlineListWithFallback
          emptyLabel="Decision states: missing"
          items={[
            "Cost blocked",
            "Cost approved",
            "Unknown paid cost",
            "No provider authority",
            "Approved / no execution",
          ]}
        />
        <RefListWithFallback
          emptyLabel="Decision-group blockers: missing"
          refs={readModel.blocked_state_refs}
        />
      </article>
      <div
        aria-label="Action Inbox decision groups"
        className="review-grid action-decision-lane-grid"
      >
        {readModel.lane_order.map((laneId) => {
          const lane = laneById.get(laneId);
          if (!lane) {
            return null;
          }
          return (
            <article className="review-card" key={lane.lane_id}>
              <div className="review-card-heading">
                <h3>{lane.label}</h3>
                <span>{lane.count}</span>
              </div>
              <p>{lane.safe_summary}</p>
              <dl className="detail-list">
                <DetailTerm label="Status" value={lane.status} />
                <DetailTerm
                  label="Approval alone"
                  value={lane.approval_alone_executes ? "unsafe" : "does not execute"}
                />
                <DetailTerm
                  label="Action execution"
                  value={lane.action_execution_enabled ? "unsafe" : "blocked"}
                />
                <DetailTerm label="Next safe action" value={lane.next_safe_action} />
              </dl>
              <RefListWithFallback
                emptyLabel="Group item refs: none"
                refs={lane.item_refs}
              />
              <RefListWithFallback
                emptyLabel="Group blockers: missing"
                refs={lane.blocked_state_refs}
              />
            </article>
          );
        })}
      </div>
      <div
        aria-label="Action Inbox decision group item details"
        className="review-grid action-decision-lane-items"
      >
        {readModel.items.map((item) => (
          <ActionInboxDecisionLaneItemCard item={item} key={item.item_ref} />
        ))}
      </div>
    </>
  );
}

function ActionInboxDecisionLaneItemCard({
  item,
}: {
  item: FounderLoopActionInboxDecisionLaneItem;
}) {
  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h4>{item.title}</h4>
        <span>{item.lane_label}</span>
      </div>
      <p>{item.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Status" value={item.status} />
        <DetailTerm label="Approval envelope" value={item.approval_envelope_ref ?? "missing"} />
        <DetailTerm label="Approval status" value={item.approval_envelope_status} />
        <DetailTerm label="Approval scope" value={item.approval_scope_ref ?? "missing"} />
        <DetailTerm label="Cost posture" value={item.cost_state_label} />
        <DetailTerm
          label="Unknown paid cost"
          value={
            item.unknown_paid_cost_requires_explicit_approval
              ? "requires explicit approval"
              : "not flagged"
          }
        />
        <DetailTerm
          label="Provider authority"
          value={item.provider_authority_state_label}
        />
        <DetailTerm
          label="Provider/model refs"
          value={`${item.provider_ref ?? "missing"} / ${item.model_profile_ref ?? "missing"}`}
        />
        <DetailTerm
          label="Estimated USD"
          value={item.estimated_cost_usd.toFixed(4)}
        />
        <DetailTerm
          label="Max approved USD"
          value={item.max_approved_cost_usd.toFixed(4)}
        />
        <DetailTerm
          label="Metered units"
          value={String(item.total_metered_units)}
        />
        <DetailTerm
          label="Approval alone"
          value={item.approval_alone_executes ? "unsafe" : "does not execute"}
        />
        <DetailTerm
          label="Action execution"
          value={item.action_execution_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm label="Next safe action" value={item.next_safe_action} />
      </dl>
      <h5>Expected receipts</h5>
      <RefListWithFallback
        emptyLabel="Expected receipts: missing"
        refs={item.expected_receipt_refs}
      />
      <h5>Missing envelope fields</h5>
      <RefListWithFallback
        emptyLabel="Missing envelope fields: none"
        refs={item.missing_envelope_field_states}
      />
      <h5>Cost receipt refs</h5>
      <RefListWithFallback
        emptyLabel="Cost receipt refs: missing"
        refs={item.cost_receipt_refs}
      />
      <h5>Evidence refs</h5>
      <RefListWithFallback
        emptyLabel="Evidence refs: missing"
        refs={item.evidence_refs}
      />
      <h5>Blocked authority</h5>
      <RefListWithFallback
        emptyLabel="Blocked authority refs: none"
        refs={item.blocked_authority_refs}
      />
    </article>
  );
}

function ActionInboxProviderCostPosture({
  readiness,
}: {
  readiness: ProviderCredentialReadinessSummary;
}) {
  return (
    <article className="status-card">
      <div className="status-card-header">
        <h3>Provider cost authority posture</h3>
        <span>
          {readiness.cost_governor_binding_required ? "cost blocked" : "missing"}
        </span>
      </div>
      <p>
        Provider-backed Action proposals remain review-only until provider/model
        refs, CostGovernor decisions, budget decisions, max-approved refs, and
        future receipt refs are present.
      </p>
      <dl className="detail-list">
        <DetailTerm
          label="Configured providers"
          value={String(readiness.posture_counts.configured)}
        />
        <DetailTerm
          label="Not configured providers"
          value={String(readiness.posture_counts.not_configured)}
        />
        <DetailTerm
          label="Revoked providers"
          value={String(readiness.posture_counts.revoked)}
        />
        <DetailTerm
          label="Blocked providers"
          value={String(readiness.posture_counts.blocked)}
        />
        <DetailTerm
          label="Unknown paid cost"
          value={
            readiness.unknown_paid_cost_requires_approval
              ? "approval required"
              : "blocked posture missing"
          }
        />
        <DetailTerm
          label="Usage claims"
          value={
            readiness.provider_usage_claim_requires_receipt_refs
              ? "receipt-bound"
              : "receipt posture missing"
          }
        />
        <DetailTerm
          label="Scoped provider capability"
          value={readiness.tiny_invocation_readiness.status}
        />
        <DetailTerm
          label="Provider authority"
          value={
            readiness.tiny_invocation_readiness.invocation_enabled
              ? "exact scope required"
              : "No provider authority"
          }
        />
        <DetailTerm
          label="Redacted receipts"
          value={
            readiness.tiny_invocation_readiness.redacted_receipts_only
              ? "required"
              : "receipt posture missing"
          }
        />
      </dl>
      <InlineListWithFallback
        emptyLabel="Provider cost blockers: missing"
        items={[
          ...readiness.blocker_codes.slice(0, 8),
          ...readiness.tiny_invocation_readiness.ui_states.filter(
            (state) =>
              ![
                "Usage captured",
                "Cost captured",
                "Cost incomplete",
                "Review required",
                "Further use blocked",
              ].includes(state),
          ),
        ]}
      />
    </article>
  );
}

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
  onReconciledItem,
}: {
  actionReadModelAuthoritative: boolean;
  group: ActionLaneGroup;
  onReconciledItem: (item: FounderLoopActionItem) => void;
}) {
  const headingId = `action-lane-${group.summary.group_id}`;
  return (
    <section
      aria-labelledby={headingId}
      className={`action-lane ${group.summary.group_id}`}
    >
      <div className="action-lane-header">
        <div>
          <p className="eyebrow">Queue group</p>
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
              onReconciledItem={onReconciledItem}
            />
          ))}
        </div>
      ) : (
        <p className="empty-state">
          No Action Inbox items are currently classified in this group.
        </p>
      )}
    </section>
  );
}

function TaskDecompositionProposalSummaryCard({
  inbox,
}: {
  inbox: FounderLoopActionsInbox;
}) {
  const summary = inbox.task_decomposition_proposal_summary;
  if (!summary) {
    return null;
  }
  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>Task decomposition proposals</h3>
        <span>{summary.status}</span>
      </div>
      <p>
        Backend-owned decomposition proposals from safe refs. These feed Plans
        and Action Inbox as review artifacts only.
      </p>
      <dl className="detail-list">
        <DetailTerm label="Contract" value={summary.contract_ref} />
        <DetailTerm label="Source" value={summary.source} />
        <DetailTerm label="Action kind" value={summary.action_kind} />
        <DetailTerm label="Proposal count" value={String(summary.proposal_count)} />
        <DetailTerm
          label="Local task commit"
          value={summary.local_task_commit_eligible ? "eligible" : "blocked"}
        />
        <DetailTerm
          label="Action execution"
          value={summary.action_execution_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Workflow execution"
          value={summary.workflow_execution_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Tool execution"
          value={summary.tool_execution_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Memory write"
          value={summary.memory_write_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Context injection"
          value={summary.context_injection_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Connector write"
          value={summary.connector_write_enabled ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Provider authority"
          value={summary.model_provider_authority_allowed ? "enabled" : "blocked"}
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Task decomposition proposal refs: none"
        refs={summary.proposal_refs}
      />
      <RefListWithFallback
        emptyLabel="Task decomposition Action Inbox refs: none"
        refs={summary.action_item_refs}
      />
      <RefListWithFallback
        emptyLabel="Task decomposition blockers: none"
        refs={summary.blocked_authority_refs}
      />
    </article>
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
      <BriefingOperatorSummary briefing={briefing} />
      <MorningBriefingV1Panel
        contractRef={briefing.morning_briefing_v1_contract_ref}
        readModel={briefing.morning_briefing_v1_read_model}
      />
      <FounderLoopRunsIntegrationPanel
        compact
        focus="morning_briefing"
        readModel={briefing.founder_loop_runs_integration_read_model}
      />
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
      <article
        aria-label="Morning Briefing read-only source readiness metadata"
        className="status-card"
      >
        <div className="status-card-header">
          <h3>Read-only source readiness metadata</h3>
          <span>no connector runtime</span>
        </div>
        <p>
          Morning Briefing can display backend-owned local route/storage status
          and safe source refs. Email, calendar, connector runtime, background
          refresh, notification delivery, model/provider authority, and memory
          writes remain blocked until exact contracts exist.
        </p>
        <dl className="detail-list">
          <DetailTerm label="Source readiness" value={briefing.source_readiness} />
          <DetailTerm label="Summary route" value={briefing.route_ref} />
          <DetailTerm
            label="Refresh authority"
            value={briefing.refresh_enabled ? "scoped" : "blocked"}
          />
          <DetailTerm
            label="Notification authority"
            value={briefing.notification_delivery_enabled ? "scoped" : "blocked"}
          />
        </dl>
        <RefListWithFallback
          emptyLabel="Read-only route refs: missing"
          refs={briefing.read_only_route_refs ?? []}
        />
        <RefListWithFallback
          emptyLabel="Missing source contracts: none"
          refs={briefing.missing_contract_refs ?? []}
        />
        <InlineListWithFallback
          emptyLabel="Blocked briefing source states: none"
          items={briefing.blocked_states ?? []}
        />
      </article>
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

function MorningBriefingV1Panel({
  contractRef,
  readModel,
}: {
  contractRef?: string;
  readModel?: FounderLoopMorningBriefingV1ReadModel;
}) {
  if (!readModel) {
    return (
      <article className="status-card">
        <div className="status-card-header">
          <h3>Briefing V1 read model</h3>
          <span>backend read model missing</span>
        </div>
        <p className="muted">
          Backend-owned Morning Briefing V1 posture is unavailable. Control
          Center will not infer source readiness, repo/workbench status, or
          evidence posture from fallback-only data.
        </p>
        <dl className="detail-list">
          <DetailTerm label="Connector runtime" value="blocked" />
          <DetailTerm label="Email/calendar fetch" value="blocked" />
          <DetailTerm label="Provider/model calls" value="blocked" />
          <DetailTerm label="Action execution" value="blocked" />
        </dl>
      </article>
    );
  }
  return (
    <article
      aria-label="Backend-owned Morning Briefing V1 read model"
      className="status-card"
    >
      <div className="status-card-header">
        <h3>Briefing V1 read model</h3>
        <span>{readModel.status}</span>
      </div>
      <p className="eyebrow">Morning Briefing V1</p>
      <p className="muted">Backend-owned local briefing</p>
      <p className="section-copy">{readModel.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Contract" value={contractRef ?? readModel.contract_ref} />
        <DetailTerm label="Source" value={readModel.source} />
        <DetailTerm label="Briefing items" value={String(readModel.item_count)} />
        <DetailTerm label="Daily sections" value={String(readModel.section_count)} />
        <DetailTerm
          label="Open Action refs"
          value={String(readModel.open_action_count)}
        />
        <DetailTerm label="Follow-ups" value={String(readModel.follow_up_count)} />
        <DetailTerm
          label="Memory review"
          value={String(readModel.memory_review_count)}
        />
        <DetailTerm
          label="Source blockers"
          value={String(readModel.source_blocker_count)}
        />
        <DetailTerm
          label="Connector runtime"
          value={readModel.connector_runtime_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Email/calendar fetch"
          value={readModel.email_calendar_fetch_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Provider/model calls"
          value={readModel.provider_model_call_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Automatic recommendations"
          value={
            readModel.automatic_recommendations_enabled ? "unsafe" : "blocked"
          }
        />
        <DetailTerm
          label="Hidden memory write"
          value={readModel.hidden_memory_write_authorized ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Repo write"
          value={readModel.repo_write_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Workbench apply"
          value={readModel.workbench_apply_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Shell execution"
          value={
            readModel.shell_subprocess_execution_enabled ? "unsafe" : "blocked"
          }
        />
        <DetailTerm
          label="Browser execution"
          value={readModel.browser_execution_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm label="Authority boundary" value={readModel.authority_boundary} />
        <DetailTerm label="Next safe action" value={readModel.next_safe_action} />
      </dl>
      <RefListWithFallback
        emptyLabel="Open Action refs: none"
        refs={readModel.open_action_refs}
      />
      <RefListWithFallback
        emptyLabel="Follow-up refs: none"
        refs={readModel.follow_up_refs}
      />
      <RefListWithFallback
        emptyLabel="Memory review refs: none"
        refs={readModel.memory_review_refs}
      />
      <RefListWithFallback
        emptyLabel="Evidence refs: none"
        refs={readModel.evidence_refs}
      />
      <RefListWithFallback
        emptyLabel="Source readiness refs: missing"
        refs={readModel.source_readiness_refs}
      />
      <p className="muted">Repo/workbench status</p>
      <RefListWithFallback
        emptyLabel="Repo status refs: missing"
        refs={readModel.repo_status_refs}
      />
      <RefListWithFallback
        emptyLabel="Workbench status refs: missing"
        refs={readModel.workbench_status_refs}
      />
      <RefListWithFallback
        emptyLabel="Missing sources: none"
        refs={readModel.missing_source_refs}
      />
      <RefListWithFallback
        emptyLabel="Evidence timeline refs: none"
        refs={readModel.evidence_timeline_refs}
      />
      <RefListWithFallback
        emptyLabel="Morning Briefing V1 blockers: missing"
        refs={readModel.blocked_state_refs}
      />
    </article>
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
    briefing.follow_up_tracker ||
    briefing.source_readiness_items?.length ||
    briefing.crm_lite_followups?.length ||
    briefing.memory_why_shown_items?.length ||
    briefing.review_queue_groups?.length ||
    briefing.weekly_ceo_review_v1_read_model ||
    briefing.chat_to_loop_handoff_read_model ||
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
        <SourceReadinessCards
          items={briefing.source_readiness_items ?? []}
          posture={briefing.source_readiness_posture}
        />
        <FollowUpTrackerPanel tracker={briefing.follow_up_tracker} />
        <ReviewQueueGroupCards groups={briefing.review_queue_groups ?? []} />
        <CrmLiteFollowUpCards items={briefing.crm_lite_followups ?? []} />
        <MemoryWhyShownCards items={briefing.memory_why_shown_items ?? []} />
        <FounderLoopProductProofPanel
          readModel={briefing.founder_loop_v1_product_proof_read_model}
        />
        <ChatToLoopHandoffPanel
          compact
          readModel={briefing.chat_to_loop_handoff_read_model}
        />
        <DogfoodCaptureCard capture={briefing.dogfood_capture} />
      </div>
      <WeeklyCeoReviewV1Panel
        readModel={briefing.weekly_ceo_review_v1_read_model}
      />
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
  authoritative,
  citationIntegrity,
  contextPacks,
  contextManifest,
  maintenanceRuns,
  memoryReview,
  qualityIssues,
  retrievalDiagnostics,
  today,
  workbench,
}: {
  authoritative: boolean;
  citationIntegrity: FounderLoopMemoryCitationIntegrity;
  contextPacks: FounderLoopMemoryContextPacks;
  contextManifest: FounderLoopMemoryContextManifest;
  maintenanceRuns: FounderLoopMemoryMaintenanceRuns;
  memoryReview: FounderLoopMemoryReview;
  qualityIssues: FounderLoopMemoryQualityIssues;
  retrievalDiagnostics: FounderLoopMemoryRetrievalDiagnostics;
  today: FounderLoopTodaySummary;
  workbench: FounderLoopMemoryWorkbench;
}) {
  const workbenchItems = workbench.items.length > 0 ? workbench.items : [];
  const legacyReviewItems =
    workbenchItems.length === 0 ? today.memory_review_queue : [];

  return (
    <section className="page-section" aria-labelledby="memory-review-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Founder Loop</p>
          <h2 id="memory-review-heading">Memory Review</h2>
        </div>
        <span className="status-pill compact">
          {workbench.status ??
            today.memory_review_status ??
            "storage_backed_review_queue"}
        </span>
      </div>
      {!authoritative ? (
        <article className="status-card warning">
          <div className="status-card-header">
            <h3>Non-authoritative fallback</h3>
            <span>mutation controls disabled</span>
          </div>
          <p className="muted">
            Memory Review is showing fallback shape only. Receipt recording,
            manual intake, feedback, and context-pack Action proposal controls
            require the backend-owned local read model.
          </p>
        </article>
      ) : null}
      <MemoryWorkbenchHealthPanel
        memoryReview={memoryReview}
        workbench={workbench}
      />
      <MemoryLifecyclePosturePanel workbench={workbench} />
      <MemoryLearningPosturePanel workbench={workbench} />
      <MemoryBoundedPosturePanel workbench={workbench} />
      <MemoryRankingDiagnosticsPanel workbench={workbench} />
      <div className="panel-grid">
        <MemoryRetrievalDiagnosticsPanel diagnostics={retrievalDiagnostics} />
        <MemoryCitationIntegrityPanel citationIntegrity={citationIntegrity} />
      </div>
      <div className="panel-grid">
        <MemoryQualityIssuePanel
          authoritative={authoritative}
          qualityIssues={qualityIssues}
        />
        <MemoryMaintenanceRunPanel maintenanceRuns={maintenanceRuns} />
      </div>
      <MemoryContextManifestPanel contextManifest={contextManifest} />
      <MemoryOperatorSummary
        authoritative={authoritative}
        contextPacks={contextPacks}
        today={today}
        workbench={workbench}
      />
      <EvidenceMemoryLoopBindingPanel
        readModel={
          memoryReview.evidence_memory_loop_binding_read_model ??
          today.evidence_memory_loop_binding_read_model
        }
      />
      <FounderLoopRunsIntegrationPanel
        compact
        focus="memory_review"
        readModel={today.founder_loop_runs_integration_read_model}
      />
      <div className="panel-grid">
        <MemoryWorkbenchSearchPanel items={workbenchItems} />
        <ManualMemoryCandidatePanel authoritative={authoritative} />
      </div>
      <div className="review-grid">
        {workbenchItems.map((item) => (
          <MemoryWorkbenchItemCard
            authoritative={authoritative}
            item={item}
            key={item.review_ref}
          />
        ))}
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
              value={
                today.memory_write_enabled
                  ? "scoped"
                  : "general writes blocked; accept/correct may create receipt-bound recall-only records"
              }
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
            Memory review can record safe accept, correction, reject, defer,
            merge, supersede, expiry, and forget-request receipts. Delete/export
            execution, connector sync, action execution, and context injection
            remain blocked.
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
              label="General write authority"
              value={
                today.memory_review_decision_authority_posture.memory_write_authorized
                  ? "enabled"
                  : "blocked; receipt-bound recall-only records only"
              }
            />
            <DetailTerm
              label="Reviewed recall posture"
              value={
                today.memory_review_decision_authority_posture.accepted_as_recall
                  ? "local recall record after scoped receipt"
                  : "not authority"
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
              label="Founder Loop contract"
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
            authoritative={authoritative}
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
        {legacyReviewItems.map((item) => (
          <MemoryReviewCard
            authoritative={authoritative}
            item={item}
            key={item.review_ref}
          />
        ))}
      </div>
      <BlockedStateList states={today.memory_review_blocked_states ?? []} />
    </section>
  );
}

function MemoryRetrievalDiagnosticsPanel({
  diagnostics,
}: {
  diagnostics: FounderLoopMemoryRetrievalDiagnostics;
}) {
  return (
    <article className="status-card">
      <div className="status-card-header">
        <div>
          <h3>Retrieval Diagnostics</h3>
          <p className="muted">
            Safe-ref stats over ranking, source mix, pressure, cache posture,
            and blocked reasons.
          </p>
        </div>
        <span>{diagnostics.cache_hit ? "cache hit" : diagnostics.cache_status}</span>
      </div>
      <dl className="detail-list">
        <DetailTerm label="Route" value={diagnostics.route_ref} />
        <DetailTerm label="Contract" value={diagnostics.contract_ref} />
        <DetailTerm label="Candidates" value={String(diagnostics.candidate_count)} />
        <DetailTerm label="Included" value={String(diagnostics.included_count)} />
        <DetailTerm label="Token estimate" value={String(diagnostics.token_estimate)} />
        <DetailTerm label="Cache key" value={diagnostics.cache_key_ref} />
        <DetailTerm
          label="Context injection"
          value={diagnostics.context_injection_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Memory write"
          value={diagnostics.memory_write_authorized ? "enabled" : "blocked"}
        />
      </dl>
      <InlineListWithFallback
        emptyLabel="Source mix: none"
        items={diagnostics.source_mix.map(
          (source) => `${source.source_ref}: ${source.count}`,
        )}
      />
      <RefListWithFallback
        emptyLabel="Included refs: none"
        refs={diagnostics.included_refs}
      />
      <RefListWithFallback
        emptyLabel="Blocked reason refs: none"
        refs={diagnostics.blocked_reason_refs}
      />
    </article>
  );
}

function MemoryCitationIntegrityPanel({
  citationIntegrity,
}: {
  citationIntegrity: FounderLoopMemoryCitationIntegrity;
}) {
  return (
    <article className="status-card">
      <div className="status-card-header">
        <div>
          <h3>Citation Integrity</h3>
          <p className="muted">
            Context-pack refs must validate before future use; this panel grants
            no context injection or truth authority.
          </p>
        </div>
        <span>{citationIntegrity.status}</span>
      </div>
      <dl className="detail-list">
        <DetailTerm label="Route" value={citationIntegrity.route_ref} />
        <DetailTerm label="Contract" value={citationIntegrity.contract_ref} />
        <DetailTerm
          label="Valid proposals"
          value={String(citationIntegrity.valid_proposal_count)}
        />
        <DetailTerm
          label="Blocked proposals"
          value={String(citationIntegrity.blocked_proposal_count)}
        />
        <DetailTerm
          label="Context injection"
          value={
            citationIntegrity.context_injection_authorized ? "enabled" : "blocked"
          }
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Citation blockers: none"
        refs={citationIntegrity.blocked_state_refs}
      />
    </article>
  );
}

function MemoryQualityIssuePanel({
  authoritative,
  qualityIssues,
}: {
  authoritative: boolean;
  qualityIssues: FounderLoopMemoryQualityIssues;
}) {
  return (
    <article className="status-card">
      <div className="status-card-header">
        <div>
          <h3>Quality Issue Queue</h3>
          <p className="muted">
            Operator feedback becomes quality signals and ranking inputs only.
          </p>
        </div>
        <span>{qualityIssues.issue_count}</span>
      </div>
      <dl className="detail-list">
        <DetailTerm label="Route" value={qualityIssues.route_ref} />
        <DetailTerm label="Feedback route" value={qualityIssues.feedback_route_ref} />
        <DetailTerm label="Feedback receipts" value={String(qualityIssues.feedback_count)} />
        <DetailTerm
          label="Memory write"
          value={qualityIssues.memory_write_authorized ? "enabled" : "blocked"}
        />
      </dl>
      <InlineListWithFallback
        emptyLabel="Quality groups: none"
        items={qualityIssues.groups.map((group) => `${group.group_id}: ${group.count}`)}
      />
      <div className="memory-impact-list">
        {qualityIssues.issues.slice(0, 4).map((issue) => (
          <MemoryQualityIssueRow
            authoritative={authoritative}
            issue={issue}
            key={issue.issue_ref}
          />
        ))}
      </div>
      <RefListWithFallback
        emptyLabel="Quality blockers: none"
        refs={qualityIssues.blocked_state_refs}
      />
    </article>
  );
}

function MemoryQualityIssueRow({
  authoritative,
  issue,
}: {
  authoritative: boolean;
  issue: FounderLoopMemoryQualityIssue;
}) {
  return (
    <div className="memory-impact-row">
      <div className="review-card-heading compact">
        <h4>{issue.issue_ref}</h4>
        <span>{issue.issue_kind}</span>
      </div>
      <dl className="detail-list">
        <DetailTerm label="Target" value={issue.target_ref} />
        <DetailTerm label="Severity" value={issue.severity} />
        <DetailTerm label="Rank" value={String(issue.rank_score)} />
        <DetailTerm
          label="Memory write"
          value={issue.memory_write_authorized ? "enabled" : "blocked"}
        />
      </dl>
      <InlineListWithFallback emptyLabel="Groups: none" items={issue.group_ids} />
      <RefListWithFallback
        emptyLabel="Source signals: none"
        refs={issue.source_signal_refs}
      />
      <MemoryFeedbackControls authoritative={authoritative} issue={issue} />
    </div>
  );
}

function MemoryFeedbackControls({
  authoritative,
  issue,
}: {
  authoritative: boolean;
  issue: FounderLoopMemoryQualityIssue;
}) {
  const mutationBinding = useBackendTruthMutationBinding();
  const [state, setState] = useState<{
    status: "idle" | "pending" | "recorded" | "failed";
    feedbackKind?: MemoryFeedbackKind;
    receipt?: MemoryFeedbackReceipt;
    message?: string;
  }>({ status: "idle" });
  const pending = state.status === "pending";
  const feedbackKinds: MemoryFeedbackKind[] = [
    "useful",
    "stale",
    "wrong",
    "duplicate",
    "conflict",
    "irrelevant",
    "privacy_concern",
  ];

  async function recordFeedback(feedbackKind: MemoryFeedbackKind) {
    if (!authoritative) {
      setState({
        status: "failed",
        feedbackKind,
        message:
          "Backend-owned Memory Review read model required before recording feedback receipts.",
      });
      return;
    }
    setState({ status: "pending", feedbackKind });
    try {
      const receipt = await recordMemoryFeedback(
        {
          target_ref: issue.target_ref,
          target_kind:
            issue.target_kind === "impact_graph_node"
              ? "impact_graph_node"
              : "memory_candidate",
          feedback_kind: feedbackKind,
          reviewer_ref: "actor-ref:control-center-memory-review",
          reason_refs: [`reason-ref:control-center-memory-feedback:${feedbackKind}`],
          metadata_refs: [issue.issue_ref],
          blocked_state_refs: memoryFeedbackBlockedRefs,
        },
        mutationBinding,
      );
      setState({
        status: "recorded",
        feedbackKind,
        receipt,
        message: `${receipt.status}: ${receipt.receipt_ref}`,
      });
    } catch (error) {
      setState({
        status: "failed",
        feedbackKind,
        message:
          error instanceof Error
            ? error.message
            : "Memory feedback receipt was not recorded safely.",
      });
    }
  }

  return (
    <div className="decision-controls" aria-label={`${issue.issue_ref} feedback`}>
      <div className="decision-button-row">
        {feedbackKinds.map((feedbackKind) => (
          <button
            className="secondary-button"
            disabled={pending || !authoritative}
            key={feedbackKind}
            onClick={() => void recordFeedback(feedbackKind)}
            title={
              authoritative
                ? undefined
                : "Backend-owned Memory Review read model required"
            }
            type="button"
          >
            {pending && state.feedbackKind === feedbackKind
              ? "Recording"
              : feedbackKind.replace("_", " ")}
          </button>
        ))}
      </div>
      {state.message ? <p className="muted">{state.message}</p> : null}
      {state.receipt ? (
        <dl className="detail-list">
          <DetailTerm label="Feedback receipt" value={state.receipt.receipt_ref} />
          <DetailTerm label="Quality issue" value={state.receipt.quality_issue_ref} />
          <DetailTerm
            label="Memory write"
            value={state.receipt.memory_write_performed ? "performed" : "blocked"}
          />
          <DetailTerm
            label="Context injection"
            value={state.receipt.context_injection_authorized ? "enabled" : "blocked"}
          />
        </dl>
      ) : null}
    </div>
  );
}

function MemoryMaintenanceRunPanel({
  maintenanceRuns,
}: {
  maintenanceRuns: FounderLoopMemoryMaintenanceRuns;
}) {
  return (
    <article className="status-card">
      <div className="status-card-header">
        <div>
          <h3>Memory Maintenance Proposals</h3>
          <p className="muted">
            Proposal-only maintenance; no merge, forget, or memory write is run
            from the UI.
          </p>
        </div>
        <span>{maintenanceRuns.proposal_count}</span>
      </div>
      <dl className="detail-list">
        <DetailTerm label="Route" value={maintenanceRuns.route_ref} />
        <DetailTerm label="Run ref" value={maintenanceRuns.run_ref} />
        <DetailTerm
          label="Auto merge"
          value={maintenanceRuns.auto_merge_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Context injection"
          value={maintenanceRuns.context_injection_authorized ? "enabled" : "blocked"}
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Maintenance blockers: none"
        refs={maintenanceRuns.blocked_state_refs}
      />
    </article>
  );
}

function MemoryContextManifestPanel({
  contextManifest,
}: {
  contextManifest: FounderLoopMemoryContextManifest;
}) {
  const governed = contextManifest.governed_context;
  return (
    <article className="status-card">
      <div className="status-card-header">
        <div>
          <h3>Memory Context Manifest</h3>
          <p className="muted">
            Preview of context refs only; no hidden context use or prompt
            injection is authorized.
          </p>
        </div>
        <span>{contextManifest.status}</span>
      </div>
      <dl className="detail-list">
        <DetailTerm label="Route" value={contextManifest.route_ref} />
        <DetailTerm label="Contract" value={contextManifest.contract_ref} />
        <DetailTerm label="Manifests" value={String(contextManifest.manifest_count)} />
        <DetailTerm
          label="Preview route"
          value={
            contextManifest.context_pack_preview_route_ref ??
            "GET /control-center/memory/context-packs/{context_pack_ref}/preview"
          }
        />
        <DetailTerm
          label="Context injection"
          value={contextManifest.context_injection_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Live injection"
          value={
            contextManifest.runtime_prompt_context_injection_authorized ||
            contextManifest.live_model_context_injection_authorized
              ? "enabled"
              : "blocked/planned"
          }
        />
        <DetailTerm
          label="Memory write"
          value={contextManifest.memory_write_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Governed context"
          value={governed?.status ?? "unavailable"}
        />
        <DetailTerm
          label="Selection budget"
          value={
            governed
              ? `${governed.budget.selected_items}/${governed.budget.max_items} refs`
              : "unavailable"
          }
        />
        <DetailTerm
          label="Capacity budget"
          value={
            governed
              ? `${governed.budget.used_tokens}/${governed.budget.max_tokens} estimated units`
              : "unavailable"
          }
        />
        <DetailTerm
          label="Included / excluded"
          value={
            governed
              ? `${governed.selection_count} / ${governed.exclusion_count}`
              : "unavailable"
          }
        />
        <DetailTerm
          label="Derived context receipt ref"
          value={governed?.context_receipt_ref ?? "unavailable"}
        />
        <DetailTerm
          label="Source scan"
          value={
            governed
              ? governed.source_scan_truncated
                ? "truncated / preview blocked"
                : "complete for bounded snapshot"
              : "unavailable"
          }
        />
      </dl>
      {governed ? (
        <>
          <RefListWithFallback
            emptyLabel="Included memory refs: none"
            refs={governed.selections.map((selection) => selection.memory_ref)}
          />
          <RefListWithFallback
            emptyLabel="Excluded memory reasons: none"
            refs={governed.exclusions.flatMap((exclusion) => exclusion.reason_refs)}
          />
        </>
      ) : null}
      <RefListWithFallback
        emptyLabel="Context manifest blockers: none"
        refs={contextManifest.blocked_state_refs}
      />
    </article>
  );
}

function MemoryWorkbenchHealthPanel({
  memoryReview,
  workbench,
}: {
  memoryReview: FounderLoopMemoryReview;
  workbench: FounderLoopMemoryWorkbench;
}) {
  const health = workbench.health;
  const metrics = [
    ["Pending review", health.pending_review_count],
    ["Stale", health.stale_count],
    ["Conflicts", health.conflict_count],
    ["Duplicates", health.duplicate_count],
    ["Missing evidence", health.missing_evidence_count],
    ["Reviewed recall", health.reviewed_recall_count],
    ["Rejected", health.rejected_count],
  ] as const;

  return (
    <article className="status-card">
      <div className="status-card-header">
        <div>
          <h3>Memory Workbench V1</h3>
          <p className="muted">
            Backend-owned review model over candidates, receipts, projections,
            context-pack proposals, and quality states.
          </p>
        </div>
        <span>{workbench.schema_version}</span>
      </div>
      <div className="metric-grid">
        {metrics.map(([label, value]) => (
          <div className="metric-card" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <dl className="detail-list">
        <DetailTerm label="Workbench route" value={workbench.route_ref} />
        <DetailTerm label="Workbench contract" value={workbench.contract_ref} />
        <DetailTerm label="Review route" value={memoryReview.route_ref} />
        <DetailTerm
          label="Lifecycle routes"
          value={String(memoryReview.decision_route_refs.length)}
        />
        <DetailTerm
          label="Safe refs only"
          value={workbench.safe_refs_only ? "yes" : "no"}
        />
        <DetailTerm
          label="Semantic/vector search"
          value={
            workbench.semantic_search_enabled ||
            workbench.vector_db_enabled ||
            workbench.embedding_search_enabled
              ? "enabled"
              : "blocked"
          }
        />
        <DetailTerm
          label="Context injection"
          value={workbench.context_injection_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Memory truth authority"
          value={workbench.memory_truth_authority ? "enabled" : "blocked"}
        />
      </dl>
      <InlineListWithFallback
        emptyLabel="Workbench groups: none"
        items={workbench.groups.map(
          (group) => `${group.group_id}: ${group.count}`,
        )}
      />
      <RefListWithFallback
        emptyLabel="Needs attention refs: none"
        refs={health.needs_attention_refs}
      />
      <RefListWithFallback
        emptyLabel="Workbench blockers: none"
        refs={workbench.blocked_state_refs}
      />
    </article>
  );
}

function MemoryLifecyclePosturePanel({
  workbench,
}: {
  workbench: FounderLoopMemoryWorkbench;
}) {
  const posture = workbench.lifecycle_posture;
  if (!posture) {
    return (
      <article aria-label="Memory lifecycle receipt posture" className="status-card">
        <div className="status-card-header">
          <h3>Memory lifecycle posture</h3>
          <span>backend posture missing</span>
        </div>
        <p>
          Merge, supersede, and forget-request posture must come from the backend
          workbench before lifecycle receipts are reviewed.
        </p>
      </article>
    );
  }

  const postureLanes = posture.lanes ?? [];
  const receiptRefs = Object.values(posture.decision_receipt_refs_by_kind ?? {})
    .flatMap((refs) => refs ?? [])
    .filter((ref, index, refs) => refs.indexOf(ref) === index);
  const laneSummaries = postureLanes.map((lane) => {
    const entryLabel = lane.count === 1 ? "entry" : "entries";
    const decisionLabel = lane.decision_kind
      ? memoryDecisionReceiptLabel(lane.decision_kind)
      : "decision receipt";
    return `${lane.label}: ${lane.count} ${entryLabel}; ${decisionLabel} ${
      lane.receipt_backed ? "present" : "awaiting"
    }`;
  });
  const laneRefs = postureLanes.flatMap((lane) => [
    lane.posture_ref,
    ...(lane.item_refs ?? []),
    ...(lane.receipt_refs ?? []),
  ]);

  return (
    <article aria-label="Memory lifecycle receipt posture" className="status-card">
      <div className="status-card-header">
        <div>
          <h3>Memory lifecycle posture</h3>
          <p className="muted">
            Duplicate, stale/recheck, conflict, corrected, merge, supersede, and
            forget-request entries are review posture signals. They become
            receipt-backed only when scoped receipt refs are present; they are
            not delete/export, context-injection, or truth authority.
          </p>
        </div>
        <span>{posture.status}</span>
      </div>
      <dl className="detail-list">
        <DetailTerm
          label="Contract ref"
          value={posture.contract_ref ?? "missing"}
        />
        <DetailTerm label="Schema" value={posture.schema_version ?? "missing"} />
        <DetailTerm
          label="Review-only"
          value={posture.review_only === true ? "yes" : "no"}
        />
        <DetailTerm
          label="Safe refs only"
          value={posture.safe_refs_only === true ? "yes" : "no"}
        />
        <DetailTerm
          label="Receipt bounds"
          value={posture.receipt_truncation_posture ?? "missing"}
        />
        <DetailTerm
          label="Lifecycle posture"
          value={posture.reversible_review_posture ?? "missing"}
        />
        <DetailTerm
          label="Hard delete"
          value={posture.hard_delete_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Export"
          value={posture.memory_export_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Automatic merge"
          value={posture.automatic_merge_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Automatic supersede"
          value={posture.automatic_supersede_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Automatic forget"
          value={posture.automatic_forget_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Hidden memory write"
          value={posture.hidden_memory_write_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Context injection"
          value={posture.context_injection_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Connector write"
          value={posture.connector_write_authorized ? "enabled" : "blocked"}
        />
      </dl>
      <InlineListWithFallback
        emptyLabel="Lifecycle lanes: none"
        items={laneSummaries}
      />
      <InlineListWithFallback
        emptyLabel="Receipt-backed lifecycle decisions: none"
        items={posture.receipt_backed_decision_kinds ?? []}
      />
      <RefListWithFallback
        emptyLabel="Lifecycle lane refs: none"
        refs={laneRefs}
      />
      <RefListWithFallback
        emptyLabel="Lifecycle receipt refs: none recorded"
        refs={receiptRefs}
      />
      <RefListWithFallback
        emptyLabel="Lifecycle blockers: none"
        refs={posture.blocked_state_refs ?? []}
      />
    </article>
  );
}

function MemoryLearningPosturePanel({
  workbench,
}: {
  workbench: FounderLoopMemoryWorkbench;
}) {
  const posture = workbench.learning_posture;
  if (!posture) {
    return (
      <article aria-label="Memory learning posture" className="status-card warning">
        <div className="status-card-header">
          <h3>Memory learning posture</h3>
          <span>backend posture missing</span>
        </div>
        <p>
          Learning, feedback, context-pack, and provenance posture must be loaded
          from the backend Memory Workbench before Control Center presents it as
          current product truth.
        </p>
      </article>
    );
  }

  const lifecycleItems = Object.entries(posture.lifecycle_state_counts).map(
    ([state, count]) => `${state}: ${count}`,
  );
  const feedbackSignals = [
    posture.feedback_receipts_supported ? "feedback receipts" : "feedback missing",
    posture.correction_receipts_supported
      ? "correction receipts"
      : "correction missing",
    posture.rejection_receipts_supported
      ? "rejection receipts"
      : "rejection missing",
    posture.forget_request_receipts_supported
      ? "forget-request receipts"
      : "forget-request missing",
  ];
  const receiptRefs = [
    ...posture.receipt_posture.accepted_receipt_refs,
    ...posture.receipt_posture.corrected_receipt_refs,
    ...posture.receipt_posture.rejected_receipt_refs,
    ...posture.receipt_posture.forget_request_receipt_refs,
    ...posture.receipt_posture.reviewed_recall_refs,
  ].filter((ref, index, refs) => refs.indexOf(ref) === index);

  return (
    <article aria-label="Memory learning posture" className="status-card">
      <div className="status-card-header">
        <div>
          <h3>Memory learning posture</h3>
          <p className="muted">
            Learning is reviewable recall context with provenance, feedback, and
            quality controls. It is not truth, context injection, connector
            write, model call, action execution, or production authority.
          </p>
        </div>
        <span>{posture.status}</span>
      </div>
      <dl className="detail-list">
        <DetailTerm label="Contract ref" value={posture.contract_ref} />
        <DetailTerm label="Source" value={posture.source} />
        <DetailTerm
          label="Backend-owned"
          value={posture.backend_owned ? "yes" : "no"}
        />
        <DetailTerm
          label="Proposal-first intake"
          value={posture.proposal_first_intake ? "yes" : "no"}
        />
        <DetailTerm
          label="Review before recall"
          value={posture.review_required_before_recall ? "yes" : "no"}
        />
        <DetailTerm
          label="Decision receipts"
          value={String(posture.receipt_posture.decision_receipt_count)}
        />
        <DetailTerm
          label="Context packs"
          value={`${posture.context_pack_posture.proposal_count} proposal refs`}
        />
        <DetailTerm
          label="Context injection"
          value={
            posture.context_pack_posture.context_injection_authorized
              ? "enabled"
              : "blocked"
          }
        />
        <DetailTerm
          label="Broad memory writes"
          value={posture.broad_memory_write_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Automatic memory writes"
          value={posture.automatic_memory_write_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Memory truth authority"
          value={posture.memory_truth_authority ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Provider/model call"
          value={posture.model_provider_call_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Delete/export"
          value={
            posture.hard_delete_authorized || posture.export_execution_authorized
              ? "enabled"
              : "blocked"
          }
        />
      </dl>
      <InlineListWithFallback
        emptyLabel="Lifecycle counts: none"
        items={lifecycleItems}
      />
      <InlineListWithFallback
        emptyLabel="Feedback flows: none"
        items={feedbackSignals}
      />
      <InlineListWithFallback
        emptyLabel="Quality controls: none"
        items={posture.quality_control_refs}
      />
      <RefListWithFallback
        emptyLabel="Context-pack refs: none"
        refs={posture.context_pack_posture.context_pack_refs}
      />
      <RefListWithFallback
        emptyLabel="Provenance refs: none"
        refs={posture.provenance_posture.provenance_refs}
      />
      <RefListWithFallback
        emptyLabel="Receipt and recall refs: none"
        refs={receiptRefs}
      />
      <RefListWithFallback
        emptyLabel="Learning posture blockers: none"
        refs={posture.blocked_state_refs}
      />
      <p>{posture.next_safe_action}</p>
    </article>
  );
}

function MemoryBoundedPosturePanel({
  workbench,
}: {
  workbench: FounderLoopMemoryWorkbench;
}) {
  const posture = workbench.bounded_memory_posture;
  if (!posture) {
    return (
      <article aria-label="Bounded memory posture" className="status-card warning">
        <div className="status-card-header">
          <h3>Bounded memory posture</h3>
          <span>backend posture missing</span>
        </div>
        <p>
          Capacity, target, staleness, source, why-shown, and correction or
          rejection posture must come from the backend Memory Workbench before
          Control Center presents bounded memory as current product truth.
        </p>
      </article>
    );
  }

  const capacityItems = [
    `visible items: ${posture.capacity_posture.visible_item_count}`,
    `candidate refs: ${posture.capacity_posture.candidate_count}`,
    `context-pack refs: ${posture.capacity_posture.context_pack_count}`,
    `token estimate: ${posture.capacity_posture.token_estimate}`,
  ];
  const sourceItems = [
    `source refs: ${posture.source_posture.source_ref_count}`,
    `provenance refs: ${posture.source_posture.provenance_ref_count}`,
    `evidence refs: ${posture.source_posture.evidence_ref_count}`,
    `receipt refs: ${posture.source_posture.receipt_ref_count}`,
  ];
  const qualitySignals = [
    posture.quality_review_posture.review_required_before_recall
      ? "review before recall"
      : "review missing",
    posture.quality_review_posture.correction_supported
      ? "correction receipts"
      : "correction missing",
    posture.quality_review_posture.rejection_supported
      ? "rejection receipts"
      : "rejection missing",
    posture.quality_review_posture.memory_write_requires_review_receipt
      ? "review receipt required"
      : "receipt missing",
  ];
  const deniedSignals = [
    `automatic writes: ${
      posture.automatic_memory_write_authorized ? "enabled" : "blocked"
    }`,
    `hidden prompt injection: ${
      posture.hidden_prompt_injection_authorized ? "enabled" : "blocked"
    }`,
    `external memory provider writes: ${
      posture.external_memory_provider_write_authorized ? "enabled" : "blocked"
    }`,
    `context injection: ${
      posture.context_injection_authorized ? "enabled" : "blocked"
    }`,
    `memory truth authority: ${
      posture.memory_truth_authority ? "enabled" : "blocked"
    }`,
  ];
  const reviewReceiptRefs = [
    ...posture.quality_review_posture.accepted_receipt_refs,
    ...posture.quality_review_posture.correction_receipt_refs,
    ...posture.quality_review_posture.rejection_receipt_refs,
  ].filter((ref, index, refs) => refs.indexOf(ref) === index);

  return (
    <article aria-label="Bounded memory posture" className="status-card">
      <div className="status-card-header">
        <div>
          <h3>Bounded memory posture</h3>
          <p className="muted">
            Bounded memory is a compact, safe-ref-only posture over capacity,
            targets, sources, staleness, why-shown refs, and review receipts. It
            does not write hidden context, call models, or sync external memory.
          </p>
        </div>
        <span>{posture.status}</span>
      </div>
      <dl className="detail-list">
        <DetailTerm label="Contract ref" value={posture.contract_ref} />
        <DetailTerm label="CLI parity" value={posture.cli_ref} />
        <DetailTerm label="Proof ref" value={posture.proof_ref} />
        <DetailTerm
          label="Backend-owned"
          value={posture.backend_owned ? "yes" : "no"}
        />
        <DetailTerm
          label="Safe refs only"
          value={posture.safe_refs_only ? "yes" : "no"}
        />
        <DetailTerm
          label="Raw content"
          value={posture.raw_content_included ? "included" : "omitted"}
        />
        <DetailTerm
          label="Target selection"
          value={
            posture.target_posture.operator_selected_context_required
              ? "operator selected"
              : "automatic"
          }
        />
        <DetailTerm
          label="Token budget"
          value={posture.capacity_posture.token_budget_state}
        />
        <DetailTerm
          label="Staleness"
          value={
            posture.staleness_posture.recheck_required_before_recall
              ? "recheck required"
              : "current"
          }
        />
        <DetailTerm
          label="Rollback posture"
          value={posture.quality_review_posture.rollback_posture}
        />
      </dl>
      <InlineListWithFallback
        emptyLabel="Capacity bounds: none"
        items={capacityItems}
      />
      <InlineListWithFallback
        emptyLabel="Source posture: none"
        items={sourceItems}
      />
      <InlineListWithFallback
        emptyLabel="Quality review posture: none"
        items={qualitySignals}
      />
      <InlineListWithFallback
        emptyLabel="Denied authority posture: none"
        items={deniedSignals}
      />
      <RefListWithFallback
        emptyLabel="Target refs: none"
        refs={posture.target_posture.target_refs}
      />
      <RefListWithFallback
        emptyLabel="Why-shown refs: none"
        refs={posture.why_shown_posture.why_shown_refs}
      />
      <RefListWithFallback
        emptyLabel="Included reason refs: none"
        refs={posture.why_shown_posture.included_reason_refs}
      />
      <RefListWithFallback
        emptyLabel="Stale item refs: none"
        refs={posture.staleness_posture.stale_item_refs}
      />
      <RefListWithFallback
        emptyLabel="Review receipt refs: none recorded"
        refs={reviewReceiptRefs}
      />
      <RefListWithFallback
        emptyLabel="Bounded memory blockers: none"
        refs={posture.blocked_state_refs}
      />
      <p>{posture.next_safe_action}</p>
    </article>
  );
}

function MemoryRankingDiagnosticsPanel({
  workbench,
}: {
  workbench: FounderLoopMemoryWorkbench;
}) {
  const ranking = workbench.ranking;
  const pressureItems = Object.entries(ranking.pressure_counts).map(
    ([label, value]) => `${label}: ${value}`,
  );
  const excludedReasonRefs = ranking.excluded_refs.flatMap(
    (entry) => entry.reason_refs,
  );
  return (
    <article
      aria-label="Ranked retrieval recall diagnostics"
      className="status-card"
    >
      <div className="status-card-header">
        <div>
          <h3>Ranked recall diagnostics</h3>
          <p className="muted">
            Why ranked is computed from lexical, tag, and safe-ref signals only.
            The rank is operator review posture, not context injection or memory
            write authority.
          </p>
        </div>
        <span>{ranking.schema_version}</span>
      </div>
      <dl className="detail-list">
        <DetailTerm label="Ranking contract" value={ranking.contract_ref} />
        <DetailTerm label="Candidate count" value={String(ranking.candidate_count)} />
        <DetailTerm
          label="Excluded from recall/context"
          value={String(ranking.excluded_ref_count)}
        />
        <DetailTerm
          label="Lexical/tag/ref only"
          value={ranking.lexical_tag_ref_only ? "yes" : "no"}
        />
        <DetailTerm
          label="Embeddings/vector/provider"
          value={
            ranking.embedding_search_enabled ||
            ranking.vector_db_enabled ||
            ranking.semantic_provider_enabled
              ? "enabled"
              : "blocked"
          }
        />
        <DetailTerm
          label="Context injection"
          value={ranking.context_injection_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Memory writes"
          value={ranking.memory_write_performed ? "performed" : "blocked"}
        />
        <DetailTerm
          label="Auto maintenance"
          value={ranking.auto_maintenance_performed ? "performed" : "blocked"}
        />
        <DetailTerm
          label="Action execution"
          value={ranking.action_execution_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm label="Cache key" value={ranking.cache_key} />
        <DetailTerm
          label="Cache hit"
          value={ranking.cache_hit ? "yes" : "no deterministic recompute"}
        />
        <DetailTerm label="Token estimate" value={String(ranking.token_estimate)} />
      </dl>
      <InlineListWithFallback
        emptyLabel="Pressure counts: none"
        items={pressureItems}
      />
      <InlineListWithFallback
        emptyLabel="Source mix: none"
        items={ranking.source_mix.map(
          (entry) => `${entry.source_ref}: ${entry.count}`,
        )}
      />
      <RefListWithFallback
        emptyLabel="Ranked candidate refs: none"
        refs={ranking.ranked_candidate_refs.slice(0, 8)}
      />
      <RefListWithFallback
        emptyLabel="Excluded reason refs: none"
        refs={excludedReasonRefs}
      />
      <RefListWithFallback
        emptyLabel="Ranking blocked authorities: none"
        refs={ranking.blocked_authority_refs}
      />
    </article>
  );
}

function MemoryWorkbenchSearchPanel({
  items,
}: {
  items: FounderLoopMemoryWorkbenchItem[];
}) {
  const [filter, setFilter] = useState("");
  const normalizedFilter = filter.trim().toLowerCase();
  const filteredItems = normalizedFilter
    ? items.filter((item) =>
        [
          item.title,
          item.safe_summary,
          item.candidate_kind,
          item.review_state,
          item.stale_state,
          item.conflict_state,
          item.memory_ref,
          item.review_ref,
          ...item.source_refs,
          ...item.related_entity_refs,
          ...item.tag_refs,
          ...item.quality_state_refs,
          ...item.why_ranked_refs,
          ...item.included_reason_refs,
          ...item.excluded_reason_refs,
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedFilter),
      )
    : items;

  return (
    <article className="status-card" aria-label="Memory Workbench read-only filter">
      <div className="status-card-header">
        <div>
          <h3>Search / Filter</h3>
          <p className="muted">
            Read-only filter over the loaded backend workbench; semantic search
            and vector DB remain blocked.
          </p>
        </div>
        <span>{filteredItems.length} shown</span>
      </div>
      <label className="field-label">
        Safe ref or review state
        <input
          className="text-input"
          onChange={(event) => setFilter(event.target.value)}
          placeholder="kind, source ref, quality state, review state..."
          value={filter}
        />
      </label>
      <dl className="detail-list">
        <DetailTerm label="Backend route" value="GET /control-center/memory/search" />
        <DetailTerm label="Total workbench items" value={String(items.length)} />
        <DetailTerm
          label="Semantic/vector search"
          value="blocked"
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Filtered refs: none"
        refs={filteredItems.slice(0, 8).map((item) => item.review_ref)}
      />
    </article>
  );
}

function ManualMemoryCandidatePanel({
  authoritative,
}: {
  authoritative: boolean;
}) {
  const mutationBinding = useBackendTruthMutationBinding();
  const [title, setTitle] = useState("Manual memory candidate");
  const [safeSummary, setSafeSummary] = useState(
    "Bounded safe summary for operator review only.",
  );
  const [candidateKind, setCandidateKind] = useState("preference");
  const [state, setState] = useState<{
    status: "idle" | "pending" | "recorded" | "failed";
    receipt?: ManualMemoryCandidateReceipt;
    message?: string;
  }>({ status: "idle" });
  const pending = state.status === "pending";

  async function submitManualCandidate() {
    if (!authoritative) {
      setState({
        status: "failed",
        message:
          "Backend-owned Memory Review read model required before recording manual candidates.",
      });
      return;
    }
    setState({ status: "pending" });
    try {
      const safeSuffix = safeRefSuffix(`${candidateKind}:${title}`);
      const receipt = await recordManualMemoryCandidate(
        {
          candidate_kind: candidateKind.trim(),
          title: title.trim(),
          safe_summary: safeSummary.trim(),
          priority: "medium",
          reviewer_ref: "actor-ref:control-center-memory-review",
          source_refs: [`source-ref:manual-note:${safeSuffix}`],
          provenance_refs: [`provenance-ref:manual-note:${safeSuffix}`],
          missing_evidence_refs: [`missing-evidence-ref:manual-note:${safeSuffix}`],
          tag_refs: ["tag-ref:manual-memory-candidate"],
          blocked_state_refs: manualMemoryCandidateBlockedRefs,
        },
        mutationBinding,
      );
      setState({
        status: "recorded",
        receipt,
        message: `recorded: ${receipt.receipt_ref}`,
      });
    } catch (error) {
      setState({
        status: "failed",
        message:
          error instanceof Error
            ? error.message
            : "Manual Memory candidate was not recorded safely.",
      });
    }
  }

  return (
    <article className="status-card" aria-label="Manual Memory candidate intake">
      <div className="status-card-header">
        <div>
          <h3>Manual Candidate Intake</h3>
          <p className="muted">
            Creates review queue state only; no recall record, delete, export,
            context injection, or connector write.
          </p>
        </div>
        <span>{state.status}</span>
      </div>
      <label className="field-label">
        Kind
        <input
          className="text-input"
          disabled={!authoritative}
          onChange={(event) => setCandidateKind(event.target.value)}
          value={candidateKind}
        />
      </label>
      <label className="field-label">
        Title
        <input
          className="text-input"
          disabled={!authoritative}
          onChange={(event) => setTitle(event.target.value)}
          value={title}
        />
      </label>
      <label className="field-label">
        Bounded safe summary
        <textarea
          className="text-input"
          disabled={!authoritative}
          onChange={(event) => setSafeSummary(event.target.value)}
          rows={3}
          value={safeSummary}
        />
      </label>
      <button
        className="secondary-button"
        disabled={pending || !authoritative}
        onClick={() => void submitManualCandidate()}
        title={
          authoritative
            ? undefined
            : "Backend-owned Memory Review read model required"
        }
        type="button"
      >
        {pending ? "Recording..." : "Record review candidate"}
      </button>
      {state.message ? <p className="muted">{state.message}</p> : null}
      {state.receipt ? (
        <dl className="detail-list">
          <DetailTerm label="Review ref" value={state.receipt.review_ref} />
          <DetailTerm label="Receipt ref" value={state.receipt.receipt_ref} />
          <DetailTerm
            label="Approval scope ref"
            value={state.receipt.approval_ref ?? "not returned"}
          />
          <DetailTerm
            label="Recall record"
            value={
              state.receipt.reviewed_recall_record_created
                ? "created"
                : "not created"
            }
          />
        </dl>
      ) : null}
      <RefListWithFallback
        emptyLabel="Manual intake blockers: none"
        refs={manualMemoryCandidateBlockedRefs}
      />
    </article>
  );
}

function MemoryWorkbenchItemCard({
  authoritative,
  item,
}: {
  authoritative: boolean;
  item: FounderLoopMemoryWorkbenchItem;
}) {
  const subject = memoryDecisionSubjectFromWorkbenchItem(item);
  const reviewLifecycleAvailable = item.source === "memory_review_queue";

  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>{item.title}</h3>
        <span>{item.priority} / {item.review_state}</span>
      </div>
      <p>{item.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Memory ref" value={item.memory_ref} />
        <DetailTerm label="Review ref" value={item.review_ref} />
        <DetailTerm label="Source" value={item.source} />
        <DetailTerm label="Kind" value={item.candidate_kind} />
        <DetailTerm label="Recall rank" value={String(item.rank_score)} />
        <DetailTerm label="Cache key" value={item.cache_key} />
        <DetailTerm label="Token estimate" value={String(item.token_estimate)} />
        <DetailTerm label="Stale posture" value={item.stale_state} />
        <DetailTerm label="Conflict posture" value={item.conflict_state} />
        <DetailTerm
          label="Lifecycle posture"
          value={
            item.reversible_review_posture ??
            "later_receipt_can_update_review_posture_no_rollback_execution"
          }
        />
        <DetailTerm
          label="Hard delete"
          value={item.hard_delete_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Automatic merge"
          value={item.automatic_merge_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Automatic supersede"
          value={item.automatic_supersede_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Automatic forget"
          value={item.automatic_forget_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm
          label="Hidden memory write"
          value={item.hidden_memory_write_authorized ? "enabled" : "blocked"}
        />
        <DetailTerm label="Side effect" value={item.side_effect_class} />
        <DetailTerm label="Boundary" value={item.authority_boundary} />
        <DetailTerm label="Next safe action" value={item.next_safe_action} />
      </dl>
      <InlineListWithFallback
        emptyLabel="Workbench groups: none"
        items={item.group_ids}
      />
      <InlineListWithFallback
        emptyLabel="Lifecycle state refs: none"
        items={item.lifecycle_state_refs}
      />
      <InlineListWithFallback
        emptyLabel="Available lifecycle decisions: none"
        items={item.available_lifecycle_decisions}
      />
      <RefListWithFallback
        emptyLabel="Duplicate posture refs: none"
        refs={item.duplicate_of_refs}
      />
      <RefListWithFallback
        emptyLabel="Conflict posture refs: none"
        refs={item.conflict_with_refs}
      />
      <RefListWithFallback
        emptyLabel="Lifecycle receipt refs: none"
        refs={item.lifecycle_receipt_refs}
      />
      <RefListWithFallback
        emptyLabel="Item authority blockers: none"
        refs={item.blocked_state_refs}
      />
      <InlineListWithFallback
        emptyLabel="Rank components: none"
        items={formatRankComponents(item.rank_components)}
      />
      <InlineListWithFallback
        emptyLabel="Source mix: none"
        items={item.source_mix.map(
          (entry) => `${entry.source_ref}: ${entry.count}`,
        )}
      />
      <RefListWithFallback
        emptyLabel="Why ranked refs: missing"
        refs={item.why_ranked_refs}
      />
      <RefListWithFallback
        emptyLabel="Included rank reason refs: missing"
        refs={item.included_reason_refs}
      />
      <RefListWithFallback
        emptyLabel="Excluded rank reason refs: none"
        refs={item.excluded_reason_refs}
      />
      <RefListWithFallback
        emptyLabel="Why shown refs: missing"
        refs={item.why_shown_refs}
      />
      <RefListWithFallback
        emptyLabel="Quality state refs: missing"
        refs={item.quality_state_refs}
      />
      <RefListWithFallback
        emptyLabel="Quality reason refs: missing"
        refs={item.quality_reason_refs}
      />
      <RefListWithFallback
        emptyLabel="Source refs: missing"
        refs={item.source_refs}
      />
      <RefListWithFallback
        emptyLabel="Provenance refs: missing"
        refs={item.provenance_refs}
      />
      <RefListWithFallback
        emptyLabel="Related entity refs: none"
        refs={item.related_entity_refs}
      />
      <RefListWithFallback
        emptyLabel="Evidence refs: none"
        refs={item.evidence_refs}
      />
      <RefListWithFallback
        emptyLabel="Missing evidence or contracts: none"
        refs={item.missing_contract_refs}
      />
      <RefListWithFallback
        emptyLabel="Ranking blocked authorities: none"
        refs={item.ranking_blocked_authority_refs}
      />
      {reviewLifecycleAvailable ? (
        <MemoryReviewDecisionControls
          authoritative={authoritative}
          subject={subject}
        />
      ) : (
        <p className="muted">
          Read-only projection. Lifecycle controls are available only for
          backend review-queue candidates.
        </p>
      )}
    </article>
  );
}

function MemoryContextPackProposalCard({
  authoritative,
  proposal,
}: {
  authoritative: boolean;
  proposal: FounderLoopMemoryContextPackProposal;
}) {
  const mutationBinding = useBackendTruthMutationBinding();
  const [displayedProposal, setDisplayedProposal] = useState(proposal);
  const [state, setState] = useState<{
    status: "idle" | "pending" | "recorded" | "failed";
    refreshStatus:
      | "idle"
      | "refreshing"
      | "reconciled"
      | "refresh_failed"
      | "refresh_pending_backend_read_model";
    receipt?: FounderLoopMemoryContextPackActionProposalReceipt;
    message?: string;
    refreshMessage?: string;
  }>({ status: "idle", refreshStatus: "idle" });
  useEffect(() => {
    setDisplayedProposal(proposal);
  }, [proposal]);

  const hasActionProposalReceipt =
    (displayedProposal.internal_action_receipt_refs?.length ?? 0) > 0 ||
    displayedProposal.phase6_1_internal_action_proposal_status ===
      "proposal_receipt_recorded_execution_blocked";
  const hasReviewedL3Refs =
    (displayedProposal.l3_representation_refs?.length ?? 0) > 0;
  const pending = state.status === "pending";
  const canCreateActionProposal =
    authoritative && !hasActionProposalReceipt && hasReviewedL3Refs;

  async function createActionProposal() {
    if (!authoritative) {
      setState({
        status: "failed",
        refreshStatus: "idle",
        message:
          "Backend-owned Memory Review read model required before recording context-pack Action proposal receipts.",
      });
      return;
    }
    setState({
      status: "pending",
      refreshStatus: "idle",
      message: "Recording backend-owned proposal receipt.",
    });
    try {
      const receipt = await recordMemoryContextPackActionProposal(
        displayedProposal.context_pack_ref,
        {
          decision_reason_ref:
            "decision-reason-ref:control-center-memory-context-pack-action-proposal",
          metadata_refs: [
            "metadata-ref:control-center-memory-context-pack-action-proposal",
            displayedProposal.context_pack_ref,
          ],
        },
        mutationBinding,
      );
      setState({
        status: "recorded",
        refreshStatus: "refreshing",
        receipt,
        message: `${receipt.status}: ${receipt.safe_summary}`,
        refreshMessage: "Refreshing Memory context-pack read model.",
      });
      try {
        const refreshed = await fetchFounderMemoryContextPacks(
          mutationBinding,
        );
        const refreshedProposal = refreshed.proposals.find(
          (candidate) =>
            candidate.context_pack_ref === displayedProposal.context_pack_ref,
        );
        if (refreshedProposal) {
          setDisplayedProposal(refreshedProposal);
          setState({
            status: "recorded",
            refreshStatus: "reconciled",
            receipt,
            message: `${receipt.status}: ${receipt.safe_summary}`,
            refreshMessage:
              "Backend read model refreshed; Action Inbox handoff refs come from the Memory context-pack API.",
          });
          return;
        }
        setState({
          status: "recorded",
          refreshStatus: "refresh_pending_backend_read_model",
          receipt,
          message: `${receipt.status}: ${receipt.safe_summary}`,
          refreshMessage:
            "Receipt recorded; backend read model has not yet returned the refreshed context-pack proposal.",
        });
      } catch (error) {
        setState({
          status: "recorded",
          refreshStatus: "refresh_failed",
          receipt,
          message: `${receipt.status}: ${receipt.safe_summary}`,
          refreshMessage:
            error instanceof Error
              ? `Backend read-model refresh failed safely: ${error.message}`
              : "Backend read-model refresh failed safely.",
        });
      }
    } catch (error) {
      setState({
        status: "failed",
        refreshStatus: "idle",
        message:
          error instanceof Error
            ? error.message
            : "Memory context-pack Action proposal receipt was not recorded safely.",
      });
    }
  }

  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>{displayedProposal.context_pack_ref}</h3>
        <span>{displayedProposal.status ?? "proposal_only"}</span>
      </div>
      <p>{displayedProposal.safe_summary}</p>
      <dl className="detail-list">
        <DetailTerm label="Proposal ref" value={displayedProposal.proposal_ref} />
        <DetailTerm label="Query ref" value={displayedProposal.query_ref ?? "none"} />
        <DetailTerm
          label="Approval posture"
          value={
            displayedProposal.approval_posture ?? "approval_required_before_use"
          }
        />
        <DetailTerm
          label="Risk"
          value={displayedProposal.risk_class ?? "medium"}
        />
        <DetailTerm
          label="Action proposal status"
          value={
            displayedProposal.phase6_1_internal_action_proposal_status ??
            "not_recorded"
          }
        />
        <DetailTerm
          label="Next safe action"
          value={
            displayedProposal.next_safe_action ??
            "Inspect safe refs only; keep context injection blocked."
          }
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Source memory refs: none"
        refs={displayedProposal.source_memory_record_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="L1/L2/L3 supporting refs: none"
        refs={[
          ...(displayedProposal.l1_preview_refs ?? []),
          ...(displayedProposal.l2_projection_refs ?? []),
          ...(displayedProposal.l3_representation_refs ?? []),
        ]}
      />
      <RefListWithFallback
        emptyLabel="Evidence refs: none"
        refs={displayedProposal.evidence_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Action Inbox handoff proposal refs: none"
        refs={displayedProposal.internal_action_proposal_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Action Inbox handoff receipt refs: none"
        refs={displayedProposal.internal_action_receipt_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Blocked states: context injection remains unscoped"
        refs={displayedProposal.blocked_state_refs ?? []}
      />
      <div className="decision-controls">
        <div className="decision-button-row">
          <button
            className="secondary-button"
            disabled={pending || !canCreateActionProposal}
            onClick={() => void createActionProposal()}
            title={
              authoritative
                ? undefined
                : "Backend-owned Memory Review read model required"
            }
            type="button"
          >
            {pending ? "Recording" : "Record Action Inbox proposal receipt"}
          </button>
        </div>
        {!hasReviewedL3Refs ? (
          <p className="muted">
            Handoff blocked: reviewed L3 safe refs are required before an Action
            Inbox proposal receipt can be recorded.
          </p>
        ) : null}
        {!authoritative ? (
          <p className="muted">
            Handoff blocked: backend-owned Memory Review read model is required
            before recording proposal receipts.
          </p>
        ) : null}
        {hasActionProposalReceipt ? (
          <p className="muted">
            Proposal receipt recorded; execution, context injection, connector
            writes, and memory writes remain blocked.
          </p>
        ) : null}
        {state.message ? <p className="muted">{state.message}</p> : null}
        {state.refreshMessage ? (
          <p className="muted">{state.refreshMessage}</p>
        ) : null}
        {state.receipt ? (
          <dl className="detail-list">
            <DetailTerm label="Receipt" value={state.receipt.receipt_ref} />
            <DetailTerm
              label="Action proposal ref"
              value={state.receipt.internal_action_proposal_ref}
            />
            <DetailTerm
              label="Action item ref"
              value={state.receipt.item_ref}
            />
            <DetailTerm
              label="Approval ref"
              value={state.receipt.approval_ref}
            />
            <DetailTerm
              label="Evidence event"
              value={state.receipt.evidence_timeline_event_ref}
            />
            <DetailTerm
              label="Read-model refresh"
              value={state.refreshStatus}
            />
            <DetailTerm
              label="Action executed"
              value={state.receipt.action_executed ? "yes" : "no"}
            />
            <DetailTerm
              label="Context injection"
              value={state.receipt.context_injection_performed ? "yes" : "no"}
            />
            <DetailTerm
              label="Memory write"
              value={state.receipt.memory_write_performed ? "yes" : "no"}
            />
            <DetailTerm
              label="Connector write"
              value={state.receipt.connector_write_performed ? "yes" : "no"}
            />
            <DetailTerm
              label="Provider/model call"
              value={state.receipt.provider_model_call_performed ? "yes" : "no"}
            />
          </dl>
        ) : null}
      </div>
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
  runObservability,
  today,
}: {
  evidence?: FounderLoopEvidenceTimelineIndex;
  runObservability?: RunObservabilityReadModel;
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
      <EvidenceOperatorSummary evidence={evidence} today={today} />
      <EvidenceAuditReceiptSpineSection
        readModel={evidence?.evidence_audit_receipt_spine}
      />
      <EvidenceMemoryLoopBindingPanel
        readModel={
          evidence?.evidence_memory_loop_binding_read_model ??
          today.evidence_memory_loop_binding_read_model
        }
      />
      <OperatorRunTimelinePanel timeline={evidence?.operator_run_timeline} />
      <FounderLoopRunsIntegrationPanel
        compact
        focus="evidence_timeline"
        readModel={
          evidence?.founder_loop_runs_integration_read_model ??
          today.founder_loop_runs_integration_read_model
        }
      />
      <RunObservabilityPanel readModel={runObservability} />
      <EvidenceTimelineNarrativeSection
        readModel={evidence?.narrative_read_model}
      />
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
        <WeeklyCeoReviewV1Panel
          readModel={today.weekly_ceo_review_v1_read_model}
        />
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
        {evidence?.review_answer_refs ? (
          <article className="status-card">
            <div className="status-card-header">
              <h3>Review answers</h3>
              <span>safe refs</span>
            </div>
            {Object.entries(evidence.review_answer_refs).map(([answer, refs]) => (
              <div key={answer}>
                <p className="muted">{answer}</p>
                <RefListWithFallback
                  emptyLabel={`${answer}: no refs recorded`}
                  refs={refs}
                />
              </div>
            ))}
          </article>
        ) : null}
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
              label="Migration version"
              value={storage.migration_version}
            />
            <DetailTerm
              label="Postgres sync required"
              value={storage.postgres_sync_required ? "yes" : "no"}
            />
            <DetailTerm label="Updated" value={storage.updated_at} />
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

const missingActionEnvelope: NonNullable<FounderLoopActionItem["approval_envelope"]> = {
  schema_version: "founder_loop_action_approval_envelope.v1",
  contract_ref: "contract-ref:founder-loop-action-approval-envelope:v1",
  source: "mock_fallback_non_authoritative",
  backend_owned: false,
  action_kind: "missing",
  exact_scope: "missing",
  risk_class: "missing",
  side_effect_class: "missing",
  approval_requirement: "missing",
  expiry_or_staleness: "missing",
  idempotency_ref: "missing",
  expected_receipt_refs: [],
  rollback_safe_disable_posture: "missing",
  estimated_cost_usd: 0,
  max_approved_cost_usd: 0,
  provider_ref: "provider-ref:not-invoked",
  model_profile_ref: "model-profile-ref:not-invoked",
  input_metered_units: 0,
  output_metered_units: 0,
  total_metered_units: 0,
  cost_estimate_ref: "cost-estimate-ref:not-invoked",
  captured_usage_ref: "usage-capture-ref:not-invoked",
  budget_decision_ref: "budget-decision-ref:not-invoked",
  cost_receipt_refs: [],
  cost_state_label: "Cost blocked",
  provider_authority_state_label: "No provider authority",
  unknown_paid_cost_requires_explicit_approval: true,
  frontier_usage_claimed: false,
  blocked_authority_refs: ["blocked-state:backend-owned-envelope-missing"],
  evidence_refs: [],
  missing_field_states: ["approval_envelope:missing"],
};

const missingReceiptVisibility: NonNullable<
  FounderLoopActionItem["receipt_visibility"]
> = {
  schema_version: "founder_loop_action_receipt_visibility.v1",
  contract_ref: "contract-ref:founder-loop-action-receipt-visibility:v1",
  source: "mock_fallback_non_authoritative",
  backend_owned: false,
  decision_receipt_ref: "missing",
  local_task_ref: "missing",
  local_task_commit_receipt_ref: "missing",
  evidence_timeline_event_ref: "missing",
  replay_posture: "missing",
  conflict_posture: "missing",
  missing_field_states: ["receipt_visibility:missing"],
};

function actionEnvelopeOrFallback(
  envelope: FounderLoopActionItem["approval_envelope"],
): NonNullable<FounderLoopActionItem["approval_envelope"]> {
  return envelope ?? missingActionEnvelope;
}

function receiptVisibilityOrFallback(
  visibility: FounderLoopActionItem["receipt_visibility"],
): NonNullable<FounderLoopActionItem["receipt_visibility"]> {
  return visibility ?? missingReceiptVisibility;
}

function isBackendOwnedEnvelope(
  envelope: FounderLoopActionItem["approval_envelope"] | null,
): boolean {
  return (
    envelope?.backend_owned === true &&
    envelope?.source === pythonCoreActionReadModelSource
  );
}

function isBackendOwnedReceiptVisibility(
  visibility: FounderLoopActionItem["receipt_visibility"] | null,
): boolean {
  return (
    visibility?.backend_owned === true &&
    visibility?.source === pythonCoreActionReadModelSource
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

type ActionCostGatePosture = {
  approved: boolean;
  summary: string;
  blockers: string[];
};

function uniqueText(values: string[]) {
  return values.filter((value, index) => value && values.indexOf(value) === index);
}

function actionCostGatePosture(item: FounderLoopActionItem): ActionCostGatePosture {
  const envelope = actionEnvelopeOrFallback(item.approval_envelope);
  const costStateLabel =
    item.action_envelope_cost_state_label ?? envelope.cost_state_label ?? "Cost blocked";
  const providerAuthorityStateLabel =
    item.action_envelope_provider_authority_state_label ??
    envelope.provider_authority_state_label ??
    "No provider authority";
  const providerRef =
    item.action_envelope_provider_ref ?? envelope.provider_ref ?? "provider-ref:not-invoked";
  const modelProfileRef =
    item.action_envelope_model_profile_ref ??
    envelope.model_profile_ref ??
    "model-profile-ref:not-invoked";
  const estimatedCostUsd =
    item.action_envelope_estimated_cost_usd ?? envelope.estimated_cost_usd;
  const maxApprovedCostUsd =
    item.action_envelope_max_approved_cost_usd ?? envelope.max_approved_cost_usd;
  const frontierUsageClaimed =
    item.action_envelope_frontier_usage_claimed ??
    envelope.frontier_usage_claimed ??
    false;
  const costReceiptRefs =
    item.action_envelope_cost_receipt_refs ?? envelope.cost_receipt_refs ?? [];
  const costBlockers =
    item.action_envelope_cost_blocked_state_refs ??
    envelope.cost_blocked_state_refs ??
    [];
  const blockers: string[] = [];

  if (costStateLabel === "Unknown paid cost") {
    blockers.push("Unknown paid cost");
  } else if (costStateLabel !== "Cost approved") {
    blockers.push("Cost blocked");
  }
  if (
    providerAuthorityStateLabel === "No provider authority" ||
    providerRef === "provider-ref:not-invoked" ||
    modelProfileRef === "model-profile-ref:not-invoked"
  ) {
    blockers.push("No provider authority");
  }
  if (
    typeof estimatedCostUsd !== "number" ||
    typeof maxApprovedCostUsd !== "number" ||
    estimatedCostUsd > maxApprovedCostUsd
  ) {
    blockers.push("Cost blocked");
  }
  if (costReceiptRefs.length === 0) {
    blockers.push("Cost blocked");
  }
  if (frontierUsageClaimed && costReceiptRefs.length === 0) {
    blockers.push("Cost blocked");
  }

  const activeBlockers = uniqueText(blockers);
  const refsSummary =
    costBlockers.length > 0 ? ` Cost refs: ${costBlockers.slice(0, 3).join(", ")}` : "";
  return {
    approved: activeBlockers.length === 0,
    summary:
      activeBlockers.length === 0
        ? "Cost approved"
        : `${activeBlockers.join(", ")}.${refsSummary}`.trim(),
    blockers: activeBlockers,
  };
}

function committedSafeRef(value: string | null | undefined): string | null {
  if (!value || unavailableReceiptStates.includes(value)) {
    return null;
  }
  return value;
}

function displayOptionalBoolean(value: boolean | null | undefined): string {
  if (typeof value !== "boolean") {
    return "missing";
  }
  return value ? "true" : "false";
}

function hasLocalTaskPosture(item: FounderLoopActionItem): boolean {
  return (
    item.action_kind === "local_task_create" ||
    Boolean(item.local_task_commit_contract_ref) ||
    Boolean(item.local_task_safe_disable_posture_ref) ||
    Boolean(item.local_task_rollback_ref)
  );
}

function ActionItemCard({
  actionReadModelAuthoritative,
  item,
  onReconciledItem,
}: {
  actionReadModelAuthoritative: boolean;
  item: FounderLoopActionItem;
  onReconciledItem?: (item: FounderLoopActionItem) => void;
}) {
  const displayedItem = item;
  const reconcileActionItem = onReconciledItem ?? (() => undefined);
  const [lastDecisionReceipt, setLastDecisionReceipt] =
    useState<FounderLoopActionDecisionReceipt | null>(null);
  const riskClass = displayedItem.risk_class ?? "unspecified";
  const authorityBoundary =
    displayedItem.authority_boundary ?? "review-only; exact backend contract required";
  const approvalEnvelopeValue = displayedItem.approval_envelope_ref
    ? displayedItem.approval_envelope_ref
    : "missing until scoped contract";
  const stateChangeContractValue = displayedItem.state_change_contract_ref
    ? displayedItem.state_change_contract_ref
    : "missing until scoped contract";
  const idempotencyValue = displayedItem.idempotency_key_ref
    ? displayedItem.idempotency_key_ref
    : "missing until scoped contract";
  const expiryValue = displayedItem.expires_at ?? "review required before mutation";
  const rollbackValue = displayedItem.rollback_ref ?? "missing until scoped contract";
  const safeDisableValue = displayedItem.safe_disable_ref ?? "missing until scoped contract";
  const envelopeStatus =
    displayedItem.approval_envelope_status ?? "missing_until_scoped_contract";
  const stateChangeReadiness =
    displayedItem.state_change_readiness ?? "blocked_missing_backend_contract";
  const staleState = displayedItem.stale_state ?? "recheck_required_before_mutation";
  const nextSafeAction =
    displayedItem.next_safe_action ??
    "Review the safe summary and keep mutation blocked until a scoped backend contract exists.";
  const actionEnvelopeRef =
    displayedItem.action_envelope_ref ?? "missing until scoped contract";
  const actionScopeRef = displayedItem.action_scope_ref ?? "scope ref missing";
  const actionApprovalRequirement =
    displayedItem.action_approval_requirement_ref ??
    "approval requirement ref missing";
  const actionGroupId =
    displayedItem.action_group_id ?? "proposal_only_no_execution_path";
  const actionGroupLabel =
    displayedItem.action_group_label ?? "Proposal-only / no execution path";
  const actionGroupReason =
    displayedItem.action_group_reason ??
    "No backend-classified execution path is available for this item.";
  const availableAction =
    displayedItem.action_group_available_action ?? "Review proposal refs only.";
  const backendReadModelAvailable = hasAuthoritativeActionReadModel(displayedItem);
  const approvalEnvelope = actionEnvelopeOrFallback(
    displayedItem.approval_envelope,
  );
  const receiptVisibility = receiptVisibilityOrFallback(
    displayedItem.receipt_visibility,
  );
  const committedLocalTaskRef = committedSafeRef(
    receiptVisibility.local_task_ref,
  );
  const localTaskRefLabel = committedLocalTaskRef
    ? "Local task ref"
    : "Local task target ref";
  const localTaskRefValue =
    committedLocalTaskRef ??
    (displayedItem.local_task_ref
      ? `target only: ${displayedItem.local_task_ref}`
      : "pending");
  const localTaskReceiptValue =
    receiptVisibility.local_task_commit_receipt_ref ??
    displayedItem.local_task_commit_receipt_ref ??
    "missing";
  const localTaskEligibilityValue =
    backendReadModelAvailable && actionReadModelAuthoritative
      ? displayedItem.local_task_commit_eligible
        ? "eligible"
        : "blocked"
      : "backend_read_model_unavailable";
  const costGate = actionCostGatePosture(displayedItem);
  const memoryProposalReviewOnly = isMemoryRecommendationProposal(displayedItem);

  return (
    <article className="review-card">
      <div className="review-card-heading">
        <h3>{displayedItem.title}</h3>
        <span>{actionGroupLabel}</span>
      </div>
      <p>{displayedItem.safe_summary}</p>
      <p className="muted">
        {actionGroupReason} Available operator action: {availableAction}
      </p>
      <ApprovalEnvelopeCard envelope={approvalEnvelope} />
      <ReceiptVisibilityCard
        actionId={displayedItem.item_ref}
        decisionReceipt={lastDecisionReceipt}
        visibility={receiptVisibility}
      />
      <FusionRoutingMetadataCard
        cacheContext={displayedItem.cache_context_economics}
        delegation={displayedItem.delegation_proposal}
        workClassification={displayedItem.work_classification}
      />
      <SourceReadinessProposalItemDetails item={displayedItem} />
      <HealthRecommendationItemDetails item={displayedItem} />
      <TaskDecompositionActionProposalDetails item={displayedItem} />
      <LocalTaskCommitPostureCard item={displayedItem} />
      <dl className="detail-list">
        <DetailTerm label="Item ref" value={displayedItem.item_ref} />
        <DetailTerm label="Queue group" value={actionGroupId} />
        <DetailTerm label="Status" value={displayedItem.status} />
        <DetailTerm label="Priority" value={displayedItem.priority} />
        <DetailTerm label="Risk" value={riskClass} />
        <DetailTerm label="Side effect" value={displayedItem.side_effect_class} />
        <DetailTerm label="Authority boundary" value={authorityBoundary} />
        <DetailTerm
          label="Approval before mutation"
          value={displayedItem.approval_required ? "required" : "not required"}
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
          value={displayedItem.action_envelope_contract_ref ?? "missing"}
        />
        <DetailTerm label="Action envelope" value={actionEnvelopeRef} />
        <DetailTerm
          label="Action envelope status"
          value={displayedItem.action_envelope_status ?? "missing"}
        />
        <DetailTerm label="Exact scope" value={actionScopeRef} />
        <DetailTerm
          label="Approval requirement"
          value={actionApprovalRequirement}
        />
        <DetailTerm
          label="Envelope execution"
          value={
            displayedItem.action_envelope_execution_enabled ? "enabled" : "blocked"
          }
        />
        <DetailTerm
          label="Grant capture"
          value={
            displayedItem.action_envelope_grant_capture_enabled
              ? "enabled"
              : "disabled"
          }
        />
        <DetailTerm
          label="Decision contract"
          value={displayedItem.state_change_contract_ref ?? "missing until recorded"}
        />
        <DetailTerm
          label="Action kind"
          value={displayedItem.action_kind ?? "review_only"}
        />
        <DetailTerm
          label="Local task contract"
          value={
            displayedItem.local_task_commit_contract_ref ?? "not a local-task create lane"
          }
        />
        <DetailTerm
          label="Local task route"
          value={
            displayedItem.local_task_commit_route_ref ?? "not a local-task create lane"
          }
        />
        <DetailTerm
          label="Local task eligibility"
          value={localTaskEligibilityValue}
        />
        <DetailTerm
          label="Local task approval"
          value={displayedItem.local_task_commit_approval_status ?? "missing"}
        />
        <DetailTerm
          label="Local task approval ref"
          value={displayedItem.local_task_commit_approval_ref ?? "missing"}
        />
        <DetailTerm label="Cost approval gate" value={costGate.summary} />
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
        <ActionDecisionControls
          item={displayedItem}
          onRecordedReceipt={setLastDecisionReceipt}
          onReconciledItem={reconcileActionItem}
        />
      ) : null}
      {actionGroupId === "ready_for_decision" &&
      (!backendReadModelAvailable || !actionReadModelAuthoritative) ? (
        <p className="muted">
          Decision controls unavailable until the local backend supplies an
          authoritative Action Inbox read model.
        </p>
      ) : null}
      {memoryProposalReviewOnly &&
      backendReadModelAvailable &&
      actionReadModelAuthoritative ? (
        <ActionDecisionControls
          decisions={["approve", "reject", "defer"]}
          item={displayedItem}
          onRecordedReceipt={setLastDecisionReceipt}
          onReconciledItem={reconcileActionItem}
        />
      ) : null}
      {memoryProposalReviewOnly &&
      (!backendReadModelAvailable || !actionReadModelAuthoritative) ? (
        <p className="muted">
          Memory proposal receipt controls require the local backend Action Inbox
          read model; no memory maintenance action is available from React state.
        </p>
      ) : null}
      {actionGroupId === "approved_local_task_lane" ? (
        <LocalTaskCommitControls
          actionReadModelAuthoritative={actionReadModelAuthoritative}
          item={displayedItem}
          onReconciledItem={reconcileActionItem}
        />
      ) : null}
      {displayedItem.blocked_state ? (
        <p className="muted">{displayedItem.blocked_state}</p>
      ) : null}
      <InlineListWithFallback
        emptyLabel="Review actions: missing"
        items={displayedItem.action_review_actions ?? []}
      />
      <RefListWithFallback
        emptyLabel="Action expected receipt refs: missing until scoped contract"
        refs={displayedItem.action_expected_receipt_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Action envelope blockers: missing"
        refs={displayedItem.action_blocked_state_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Local task commit blockers: not a local-task create lane"
        refs={displayedItem.local_task_commit_blocked_reasons ?? []}
      />
      <RefListWithFallback
        emptyLabel="Local task external authority blockers: missing"
        refs={displayedItem.local_task_commit_external_authority_blocked_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Receipt refs: missing until scoped contract"
        refs={displayedItem.receipt_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Audit refs: missing until scoped contract"
        refs={displayedItem.audit_refs ?? []}
      />
      <RefList refs={displayedItem.evidence_refs ?? []} />
    </article>
  );
}

function SourceReadinessProposalItemDetails({
  item,
}: {
  item: FounderLoopActionItem;
}) {
  if (!item.source_readiness_proposal_ref) {
    return null;
  }
  return (
    <section
      aria-label="Source readiness proposal detail"
      className="local-task-posture-card"
    >
      <div className="review-card-heading compact">
        <h4>Source readiness proposal</h4>
        <span>
          {item.source_readiness_proposal_classification ??
            "proposal_only_no_execution_path"}
        </span>
      </div>
      <p className="muted">
        Backend-owned source-readiness proposal metadata. React renders these
        refs but does not mint proposal truth, authority, blocked refs, or
        eligibility.
      </p>
      <dl className="detail-list">
        <DetailTerm
          label="Proposal ref"
          value={item.source_readiness_proposal_ref}
        />
        <DetailTerm
          label="Proposal kind"
          value={item.source_readiness_proposal_kind ?? "missing"}
        />
        <DetailTerm
          label="Missing contract"
          value={item.source_readiness_missing_contract_ref ?? "missing"}
        />
        <DetailTerm
          label="Source readiness ref"
          value={item.source_readiness_ref ?? "missing"}
        />
        <DetailTerm
          label="Source readiness route"
          value={item.source_readiness_route_ref ?? "missing"}
        />
        <DetailTerm
          label="Backend owned"
          value={item.source_readiness_backend_owned ? "yes" : "unavailable"}
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Source readiness proposal blockers: none"
        refs={item.source_readiness_blocked_authority_refs ?? []}
      />
    </section>
  );
}

function HealthRecommendationItemDetails({
  item,
}: {
  item: FounderLoopActionItem;
}) {
  if (!item.health_recommendation_ref) {
    return null;
  }
  return (
    <section
      aria-label="Self-healing recommendation detail"
      className="local-task-posture-card"
    >
      <div className="review-card-heading compact">
        <h4>Recommendation proposal</h4>
        <span>{item.health_recommendation_kind ?? "review_only"}</span>
      </div>
      <p className="muted">
        Backend-owned recommendation metadata. Review receipts can be recorded,
        but auto-code, auto-apply, maintenance execution, context injection,
        memory writes, and provider calls remain blocked.
      </p>
      <dl className="detail-list">
        <DetailTerm
          label="Recommendation ref"
          value={item.health_recommendation_ref}
        />
        <DetailTerm
          label="Lifecycle"
          value={item.health_recommendation_lifecycle_state ?? "queued_for_review"}
        />
        <DetailTerm
          label="Severity"
          value={item.health_recommendation_severity ?? "medium"}
        />
        <DetailTerm
          label="Auto apply"
          value={
            item.health_recommendation_auto_apply_authorized ? "enabled" : "blocked"
          }
        />
        <DetailTerm
          label="Memory write"
          value={
            item.health_recommendation_memory_write_authorized ? "enabled" : "blocked"
          }
        />
        <DetailTerm
          label="Context injection"
          value={
            item.health_recommendation_context_injection_authorized
              ? "enabled"
              : "blocked"
          }
        />
        <DetailTerm
          label="Action execution"
          value={
            item.health_recommendation_action_execution_authorized
              ? "enabled"
              : "blocked"
          }
        />
      </dl>
      <RefListWithFallback
        emptyLabel="Recommendation source signals: none"
        refs={item.health_recommendation_source_signal_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Recommendation route refs: none"
        refs={item.health_recommendation_source_route_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Recommendation validation refs: none"
        refs={item.health_recommendation_validation_plan_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Recommendation safe-disable refs: none"
        refs={item.health_recommendation_rollback_or_safe_disable_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Recommendation blocked authority refs: none"
        refs={item.health_recommendation_blocked_authority_refs ?? []}
      />
    </section>
  );
}

function isMemoryRecommendationProposal(item: FounderLoopActionItem): boolean {
  return (
    item.action_kind === "self_heal_recommendation" &&
    item.health_recommendation_kind === "memory_quality_issue" &&
    item.action_group_id === "proposal_only_no_execution_path"
  );
}

function TaskDecompositionActionProposalDetails({
  item,
}: {
  item: FounderLoopActionItem;
}) {
  if (!item.task_decomposition_proposal_ref) {
    return null;
  }
  return (
    <section
      aria-label="Task decomposition proposal detail"
      className="local-task-posture-card"
    >
      <div className="review-card-heading compact">
        <h4>Task decomposition proposal</h4>
        <span>
          {item.task_decomposition_proposal_only
            ? "proposal_only_review_required"
            : "posture_missing"}
        </span>
      </div>
      <p className="muted">
        Backend-owned decomposition metadata for planning review. React renders
        these refs without creating tasks, approvals, memory changes, context
        use, tool calls, connector writes, shell work, browser work, or provider
        calls.
      </p>
      <dl className="detail-list">
        <DetailTerm
          label="Proposal ref"
          value={item.task_decomposition_proposal_ref}
        />
        <DetailTerm
          label="Envelope ref"
          value={item.task_decomposition_review_envelope_ref ?? "missing"}
        />
        <DetailTerm
          label="Plans bridge"
          value={item.task_decomposition_plans_bridge_ref ?? "missing"}
        />
        <DetailTerm
          label="Action bridge"
          value={item.task_decomposition_action_inbox_bridge_ref ?? "missing"}
        />
        <DetailTerm
          label="Why proposed"
          value={item.task_decomposition_why_proposed ?? "missing"}
        />
        <DetailTerm
          label="Review posture"
          value={item.task_decomposition_review_only ? "review-only" : "missing"}
        />
        <DetailTerm
          label="Execution authorized"
          value={
            item.task_decomposition_execution_authorized ? "unsafe" : "blocked"
          }
        />
        <DetailTerm
          label="Action execution"
          value={
            item.task_decomposition_action_execution_enabled
              ? "unsafe"
              : "blocked"
          }
        />
        <DetailTerm
          label="Workflow execution"
          value={
            item.task_decomposition_workflow_execution_enabled
              ? "unsafe"
              : "blocked"
          }
        />
        <DetailTerm
          label="Tool execution"
          value={
            item.task_decomposition_tool_execution_enabled ? "unsafe" : "blocked"
          }
        />
        <DetailTerm
          label="Memory write"
          value={
            item.task_decomposition_memory_write_authorized
              ? "unsafe"
              : "blocked"
          }
        />
        <DetailTerm
          label="Context injection"
          value={
            item.task_decomposition_context_injection_authorized
              ? "unsafe"
              : "blocked"
          }
        />
        <DetailTerm
          label="Provider authority"
          value={
            item.task_decomposition_model_provider_authority_allowed
              ? "unsafe"
              : "blocked"
          }
        />
      </dl>
      <InlineListWithFallback
        emptyLabel="Affected surfaces: missing"
        items={item.task_decomposition_what_this_affects ?? []}
      />
      <RefListWithFallback
        emptyLabel="Task decomposition steps: missing"
        refs={item.task_decomposition_step_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Task decomposition dependencies: none"
        refs={item.task_decomposition_dependency_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Task decomposition ambiguity refs: none"
        refs={item.task_decomposition_ambiguity_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Task decomposition missing evidence refs: none"
        refs={item.task_decomposition_missing_evidence_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Task decomposition required approvals: missing"
        refs={item.task_decomposition_required_approvals ?? []}
      />
      <RefListWithFallback
        emptyLabel="Task decomposition blockers: missing"
        refs={item.task_decomposition_blocked_authority_refs ?? []}
      />
    </section>
  );
}

function LocalTaskCommitPostureCard({
  item,
}: {
  item: FounderLoopActionItem;
}) {
  if (!hasLocalTaskPosture(item)) {
    return null;
  }
  const posture = item.local_task_safe_disable_posture;
  const safeDisableActive =
    item.local_task_safe_disable_active ?? posture?.safe_disable_active;
  const safeDisablePostureRef =
    item.local_task_safe_disable_posture_ref ??
    posture?.safe_disable_posture_ref ??
    "missing";
  const rollbackRef =
    item.local_task_rollback_ref ?? posture?.rollback_ref ?? item.rollback_ref ?? "missing";
  const rollbackExecutionEnabled =
    item.local_task_rollback_execution_enabled ??
    posture?.rollback_execution_enabled;
  const rollbackBlockerRefs =
    item.local_task_rollback_blocker_refs ?? posture?.rollback_blocker_refs ?? [];
  const safeDisablePosture =
    posture === undefined
      ? "missing"
      : `backend_owned:${displayOptionalBoolean(posture.backend_owned)}; source:${posture.source}`;

  return (
    <section
      aria-label="Local task commit posture"
      className="local-task-posture-card"
    >
      <div className="review-card-heading compact">
        <h4>Local task commit posture</h4>
        <span>
          {item.local_task_commit_eligible === true ? "eligible" : "blocked"}
        </span>
      </div>
      <p className="muted">
        Backend-owned local_task_create posture rendered from the Action Inbox
        read model. React does not mint approval, eligibility, safe-disable,
        rollback, grants, scopes, or authority.
      </p>
      <dl className="detail-list">
        <DetailTerm
          label="local_task_commit_eligible"
          value={displayOptionalBoolean(item.local_task_commit_eligible)}
        />
        <DetailTerm
          label="local_task_commit_approval_status"
          value={item.local_task_commit_approval_status ?? "missing"}
        />
        <DetailTerm
          label="local_task_commit_approval_ref"
          value={item.local_task_commit_approval_ref ?? "missing"}
        />
        <DetailTerm
          label="local_task_commit_contract_ref"
          value={item.local_task_commit_contract_ref ?? "missing"}
        />
        <DetailTerm
          label="local_task_commit_route_ref"
          value={item.local_task_commit_route_ref ?? "missing"}
        />
        <DetailTerm
          label="local_task_commit_next_safe_action"
          value={item.local_task_commit_next_safe_action ?? "missing"}
        />
        <DetailTerm
          label="local_task_safe_disable_posture"
          value={safeDisablePosture}
        />
        <DetailTerm
          label="local_task_safe_disable_active"
          value={displayOptionalBoolean(safeDisableActive)}
        />
        <DetailTerm
          label="local_task_safe_disable_posture_ref"
          value={safeDisablePostureRef}
        />
        <DetailTerm label="local_task_rollback_ref" value={rollbackRef} />
        <DetailTerm
          label="local_task_rollback_execution_enabled"
          value={displayOptionalBoolean(rollbackExecutionEnabled)}
        />
      </dl>
      <p className="muted">local_task_commit_blocked_reasons</p>
      <InlineListWithFallback
        emptyLabel="local_task_commit_blocked_reasons: none"
        items={item.local_task_commit_blocked_reasons ?? []}
      />
      <p className="muted">external authority blockers</p>
      <RefListWithFallback
        emptyLabel="external authority blockers: none"
        refs={item.local_task_commit_external_authority_blocked_refs ?? []}
      />
      <p className="muted">local_task_rollback_blocker_refs</p>
      <RefListWithFallback
        emptyLabel="local_task_rollback_blocker_refs: none"
        refs={rollbackBlockerRefs}
      />
      <p className="muted">local_task_safe_disable blocked refs</p>
      <RefListWithFallback
        emptyLabel="local_task_safe_disable blocked refs: none"
        refs={posture?.blocked_state_refs ?? []}
      />
    </section>
  );
}

function ApprovalEnvelopeCard({
  envelope,
}: {
  envelope: NonNullable<FounderLoopActionItem["approval_envelope"]>;
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
          label="Cost state"
          value={envelope.cost_state_label}
        />
        <DetailTerm
          label="Estimated cost USD"
          value={formatCostUsd(envelope.estimated_cost_usd)}
        />
        <DetailTerm
          label="Max approved USD"
          value={formatCostUsd(envelope.max_approved_cost_usd)}
        />
        <DetailTerm label="Provider ref" value={envelope.provider_ref} />
        <DetailTerm label="Model profile" value={envelope.model_profile_ref} />
        <DetailTerm
          label="Input metered units"
          value={String(envelope.input_metered_units)}
        />
        <DetailTerm
          label="Output metered units"
          value={String(envelope.output_metered_units)}
        />
        <DetailTerm
          label="Unknown paid cost"
          value={
            envelope.unknown_paid_cost_requires_explicit_approval
              ? "explicit approval required"
              : "not required"
          }
        />
        <DetailTerm
          label="Provider authority"
          value={envelope.provider_authority_state_label}
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
        emptyLabel="Cost receipt refs: missing"
        refs={envelope.cost_receipt_refs}
      />
      <RefListWithFallback
        emptyLabel="Cost blockers: missing"
        refs={envelope.cost_blocked_state_refs ?? []}
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
  actionId,
  decisionReceipt,
  visibility,
}: {
  actionId: string;
  decisionReceipt?: FounderLoopActionDecisionReceipt | null;
  visibility: NonNullable<FounderLoopActionItem["receipt_visibility"]>;
}) {
  const backendOwned = isBackendOwnedReceiptVisibility(visibility);
  const decisionReceiptRef = committedSafeRef(visibility.decision_receipt_ref);
  const [fetchedDecisionReceipt, setFetchedDecisionReceipt] =
    useState<FounderLoopActionDecisionReceipt | null>(decisionReceipt ?? null);
  const [receiptFetchStatus, setReceiptFetchStatus] = useState<
    "idle" | "loading" | "loaded" | "failed"
  >("idle");
  useEffect(() => {
    if (decisionReceipt) {
      setFetchedDecisionReceipt(decisionReceipt);
      setReceiptFetchStatus("loaded");
      return;
    }
    if (!decisionReceiptRef) {
      setFetchedDecisionReceipt(null);
      setReceiptFetchStatus("idle");
      return;
    }
    let cancelled = false;
    setReceiptFetchStatus("loading");
    fetchActionReceipt(actionId)
      .then((receipt) => {
        if (cancelled) {
          return;
        }
        setFetchedDecisionReceipt(receipt);
        setReceiptFetchStatus(receipt ? "loaded" : "failed");
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        setFetchedDecisionReceipt(null);
        setReceiptFetchStatus("failed");
      });
    return () => {
      cancelled = true;
    };
  }, [actionId, decisionReceipt, decisionReceiptRef]);
  const visibleDecisionReceipt = decisionReceipt ?? fetchedDecisionReceipt;
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
        {visibleDecisionReceipt ? (
          <>
            <DetailTerm
              label="Authority outcome"
              value={visibleDecisionReceipt.authority_decision_outcome ?? "missing"}
            />
            <DetailTerm
              label="Authority lease"
              value={visibleDecisionReceipt.authority_lease_ref ?? "required"}
            />
            <DetailTerm
              label="Authority mode"
              value={visibleDecisionReceipt.authority_required_mode_ref ?? "missing"}
            />
            <DetailTerm
              label="Authority domain"
              value={visibleDecisionReceipt.authority_domain_ref ?? "missing"}
            />
            <DetailTerm
              label="Authority capability"
              value={visibleDecisionReceipt.authority_capability_ref ?? "missing"}
            />
            <DetailTerm
              label="Authority decision"
              value={visibleDecisionReceipt.authority_decision_ref ?? "missing"}
            />
            <DetailTerm
              label="Authority audit"
              value={visibleDecisionReceipt.authority_audit_ref ?? "missing"}
            />
            <DetailTerm
              label="Authority policy receipt"
              value={visibleDecisionReceipt.authority_receipt_ref ?? "missing"}
            />
          </>
        ) : null}
      </dl>
      {visibleDecisionReceipt ? (
        <RefListWithFallback
          emptyLabel="Authority reason refs: none"
          refs={visibleDecisionReceipt.authority_reason_refs ?? []}
        />
      ) : null}
      {receiptFetchStatus === "failed" ? (
        <p className="muted">
          Authority decision details are unavailable from the receipt route; the
          safe receipt ref remains visible.
        </p>
      ) : null}
      <InlineListWithFallback
        emptyLabel="Receipt visibility missing states: none"
        items={visibility.missing_field_states}
      />
    </section>
  );
}

const actionDecisionLabels: Record<FounderLoopActionDecisionKind, string> = {
  approve: "Record approval receipt",
  edit: "Record edit receipt",
  reject: "Record rejection receipt",
  defer: "Record defer receipt",
};

function ActionDecisionControls({
  decisions = ["approve", "edit", "reject", "defer"],
  item,
  onRecordedReceipt,
  onReconciledItem,
}: {
  decisions?: FounderLoopActionDecisionKind[];
  item: FounderLoopActionItem;
  onRecordedReceipt?: (receipt: FounderLoopActionDecisionReceipt) => void;
  onReconciledItem: (item: FounderLoopActionItem) => void;
}) {
  const mutationBinding = useBackendTruthMutationBinding();
  const [state, setState] = useState<{
    status: "idle" | "pending" | "recorded" | "failed";
    refreshStatus:
      | "idle"
      | "refreshing"
      | "reconciled"
      | "refresh_failed"
      | "refresh_pending_backend_read_model";
    decision?: FounderLoopActionDecisionKind;
    receipt?: FounderLoopActionDecisionReceipt;
    message?: string;
    refreshMessage?: string;
  }>({ status: "idle", refreshStatus: "idle" });
  const pending = state.status === "pending";
  const costGate = actionCostGatePosture(item);
  const displayedRevisionRef =
    item.action_revision_ref ?? item.expected_revision_ref;

  async function refreshDecisionActionItem(
    receipt: FounderLoopActionDecisionReceipt,
    decision: FounderLoopActionDecisionKind,
  ) {
    setState({
      status: "recorded",
      refreshStatus: "refreshing",
      decision,
      receipt,
      message: `${receipt.status}: ${receipt.safe_summary}`,
      refreshMessage: "Refreshing Action Inbox read model from the backend.",
    });
    try {
      const refreshedInbox = await fetchFounderActionsInbox(mutationBinding);
      const refreshedItem = refreshedInbox.items.find(
        (candidate) => candidate.item_ref === item.item_ref,
      );
      const receiptConfirmed =
        refreshedItem?.receipt_visibility?.decision_receipt_ref ===
          receipt.receipt_ref ||
        refreshedItem?.receipt_refs?.includes(receipt.receipt_ref);
      if (!refreshedItem || !hasAuthoritativeActionReadModel(refreshedItem)) {
        setState({
          status: "recorded",
          refreshStatus: "refresh_pending_backend_read_model",
          decision,
          receipt,
          message: `${receipt.status}: ${receipt.safe_summary}`,
          refreshMessage:
            "Backend read-model refresh is pending; the decision receipt is shown, but group membership has not changed until backend-owned Action Inbox data confirms it.",
        });
        return;
      }
      if (!receiptConfirmed) {
        setState({
          status: "recorded",
          refreshStatus: "refresh_pending_backend_read_model",
          decision,
          receipt,
          message: `${receipt.status}: ${receipt.safe_summary}`,
          refreshMessage:
            "Backend read-model refresh did not yet include the decision receipt; group membership remains pending until the backend read model catches up.",
        });
        return;
      }
      onReconciledItem(refreshedItem);
      setState({
        status: "recorded",
        refreshStatus: "reconciled",
        decision,
        receipt,
        message: `${receipt.status}: ${receipt.safe_summary}`,
        refreshMessage:
          "Backend read model refreshed; decision posture now comes from the Action Inbox API.",
      });
    } catch (error) {
      setState({
        status: "recorded",
        refreshStatus: "refresh_failed",
        decision,
        receipt,
        message: `${receipt.status}: ${receipt.safe_summary}`,
        refreshMessage:
          error instanceof Error
            ? `Backend read-model refresh failed safely: ${error.message}`
            : "Backend read-model refresh failed safely.",
      });
    }
  }

  async function recordDecision(decision: FounderLoopActionDecisionKind) {
    if (!displayedRevisionRef) {
      setState({
        status: "failed",
        refreshStatus: "idle",
        decision,
        message:
          "The displayed Action revision is unavailable. Refresh the authoritative Action Inbox before recording a decision.",
      });
      return;
    }
    setState({ status: "pending", refreshStatus: "idle", decision });
    try {
      const receipt = await submitActionDecision(
        item.item_ref,
        decision,
        {
          expected_revision_ref: displayedRevisionRef,
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
        },
        mutationBinding,
      );
      onRecordedReceipt?.(receipt);
      await refreshDecisionActionItem(receipt, decision);
    } catch (error) {
      setState({
        status: "failed",
        refreshStatus: "idle",
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
        {decisions.map((decision) => {
          const costBlocked = decision === "approve" && !costGate.approved;
          return (
            <button
              className="secondary-button"
              disabled={pending || costBlocked || !displayedRevisionRef}
              key={decision}
              onClick={() => void recordDecision(decision)}
              title={costBlocked ? costGate.summary : undefined}
              type="button"
            >
              {pending && state.decision === decision
                ? "Recording"
                : actionDecisionLabels[decision]}
            </button>
          );
        })}
      </div>
      {!costGate.approved ? (
        <p className="muted">Approval blocked by cost posture: {costGate.summary}</p>
      ) : null}
      {state.message ? <p className="muted">{state.message}</p> : null}
      {state.refreshMessage ? (
        <p className="muted">{state.refreshMessage}</p>
      ) : null}
      {state.receipt ? (
        <>
          <dl className="detail-list">
            <DetailTerm label="Receipt" value={state.receipt.receipt_ref} />
            <DetailTerm label="Audit" value={state.receipt.audit_ref} />
            <DetailTerm
              label="Approval ref"
              value={state.receipt.approval_ref ?? "not required"}
            />
            <DetailTerm
              label="Read-model refresh"
              value={state.refreshStatus}
            />
            <DetailTerm
              label="Authority outcome"
              value={state.receipt.authority_decision_outcome ?? "missing"}
            />
            <DetailTerm
              label="Authority lease"
              value={state.receipt.authority_lease_ref ?? "required"}
            />
            <DetailTerm
              label="Authority mode"
              value={state.receipt.authority_required_mode_ref ?? "missing"}
            />
            <DetailTerm
              label="Authority domain"
              value={state.receipt.authority_domain_ref ?? "missing"}
            />
            <DetailTerm
              label="Authority capability"
              value={state.receipt.authority_capability_ref ?? "missing"}
            />
            <DetailTerm
              label="Authority decision"
              value={state.receipt.authority_decision_ref ?? "missing"}
            />
            <DetailTerm
              label="Authority audit"
              value={state.receipt.authority_audit_ref ?? "missing"}
            />
            <DetailTerm
              label="Authority policy receipt"
              value={state.receipt.authority_receipt_ref ?? "missing"}
            />
            <DetailTerm
              label="Action executed"
              value={state.receipt.action_executed ? "yes" : "no"}
            />
            <DetailTerm
              label="Connector write"
              value={state.receipt.connector_write_performed ? "yes" : "no"}
            />
          </dl>
          <RefListWithFallback
            emptyLabel="Authority reason refs: none"
            refs={state.receipt.authority_reason_refs ?? []}
          />
        </>
      ) : null}
    </div>
  );
}

function LocalTaskCommitControls({
  actionReadModelAuthoritative,
  item,
  onReconciledItem,
}: {
  actionReadModelAuthoritative: boolean;
  item: FounderLoopActionItem;
  onReconciledItem: (item: FounderLoopActionItem) => void;
}) {
  const mutationBinding = useBackendTruthMutationBinding();
  const [state, setState] = useState<{
    status: "idle" | "pending" | "recorded" | "failed";
    refreshStatus:
      | "idle"
      | "refreshing"
      | "reconciled"
      | "refresh_failed"
      | "refresh_pending_backend_read_model";
    receipt?: FounderLoopLocalTaskCommitReceipt;
    message?: string;
    refreshMessage?: string;
  }>({ status: "idle", refreshStatus: "idle" });
  const approvalRef = item.local_task_commit_approval_ref;
  if (!canShowLocalTaskCommitControl(item, actionReadModelAuthoritative)) {
    return null;
  }
  const commitApprovalRef = approvalRef as string;
  const pending = state.status === "pending";
  const costGate = actionCostGatePosture(item);

  async function refreshCommittedActionItem(
    receipt: FounderLoopLocalTaskCommitReceipt,
  ) {
    setState({
      status: "recorded",
      refreshStatus: "refreshing",
      receipt,
      message: `${receipt.status}: ${receipt.safe_summary}`,
      refreshMessage: "Refreshing Action Inbox read model from the backend.",
    });
    try {
      const refreshedInbox = await fetchFounderActionsInbox(mutationBinding);
      const refreshedItem = refreshedInbox.items.find(
        (candidate) => candidate.item_ref === item.item_ref,
      );
      if (!refreshedItem || !hasAuthoritativeActionReadModel(refreshedItem)) {
        setState({
          status: "recorded",
          refreshStatus: "refresh_pending_backend_read_model",
          receipt,
          message: `${receipt.status}: ${receipt.safe_summary}`,
          refreshMessage:
            "Backend read-model refresh is pending; the POST receipt is shown, but the card has not moved until backend-owned Action Inbox data confirms it.",
        });
        return;
      }
      const receiptConfirmed =
        refreshedItem.receipt_visibility?.local_task_commit_receipt_ref ===
          receipt.receipt_ref ||
        refreshedItem.local_task_commit_receipt_ref === receipt.receipt_ref;
      if (!receiptConfirmed) {
        setState({
          status: "recorded",
          refreshStatus: "refresh_pending_backend_read_model",
          receipt,
          message: `${receipt.status}: ${receipt.safe_summary}`,
          refreshMessage:
            "Backend read-model refresh did not yet include the commit receipt; receipt visibility remains pending until the backend read model catches up.",
        });
        return;
      }
      onReconciledItem(refreshedItem);
      setState({
        status: "recorded",
        refreshStatus: "reconciled",
        receipt,
        message: `${receipt.status}: ${receipt.safe_summary}`,
        refreshMessage:
          "Backend read model refreshed; receipt visibility now comes from the Action Inbox API.",
      });
    } catch (error) {
      setState({
        status: "recorded",
        refreshStatus: "refresh_failed",
        receipt,
        message: `${receipt.status}: ${receipt.safe_summary}`,
        refreshMessage:
          error instanceof Error
            ? `Backend read-model refresh failed safely: ${error.message}`
            : "Backend read-model refresh failed safely.",
      });
    }
  }

  async function recordLocalTaskCommit() {
    setState({ status: "pending", refreshStatus: "idle" });
    try {
      const receipt = await commitLocalTask(
        item.item_ref,
        {
          approval_ref: commitApprovalRef,
          decision_reason_ref:
            "decision-reason-ref:control-center:local-task-commit",
          metadata_refs: [
            "metadata-ref:control-center-local-task-commit",
            item.item_ref,
          ],
        },
        mutationBinding,
      );
      await refreshCommittedActionItem(receipt);
    } catch (error) {
      setState({
        status: "failed",
        refreshStatus: "idle",
        message:
          error instanceof Error
            ? error.message
            : "Local task commit receipt was not recorded safely.",
      });
    }
  }

  return (
    <div className="decision-controls" aria-label={`${item.title} local task`}>
      {!state.receipt ? (
        <div className="decision-button-row">
          <button
            className="secondary-button"
            data-contract-label="Commit local task"
            disabled={pending || !costGate.approved}
            onClick={() => void recordLocalTaskCommit()}
            title={!costGate.approved ? costGate.summary : undefined}
            type="button"
          >
            {pending ? "Creating local task record" : "Create local task record"}
          </button>
        </div>
      ) : null}
      {!costGate.approved ? (
        <p className="muted">Commit blocked by cost posture: {costGate.summary}</p>
      ) : null}
      <p className="muted">
        Creates local task state only. No connector writes, shell/subprocess
        execution, browser execution, provider/model calls, memory writes,
        context injection, external side effects, rollback execution, or
        production authority.
      </p>
      {state.message ? <p className="muted">{state.message}</p> : null}
      {state.refreshMessage ? (
        <p className="muted">{state.refreshMessage}</p>
      ) : null}
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
            label="Read-model refresh"
            value={state.refreshStatus}
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
      <p className="muted">
        Plan envelope refs are review metadata only. Provider/model/cost refs do
        not invoke providers, tools, workflows, browser, shell, connectors, or
        action execution.
      </p>
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
          label="Execution flag"
          value={plan.action_execution_enabled ? "unsafe" : "blocked"}
        />
        <DetailTerm
          label="Grant capture flag"
          value={plan.approval_grant_capture_enabled ? "unsafe" : "disabled"}
        />
        <DetailTerm
          label="Cost state"
          value={plan.action_envelope_cost_state_label ?? "Cost blocked"}
        />
        <DetailTerm
          label="Estimated cost USD"
          value={formatCostUsd(plan.action_envelope_estimated_cost_usd)}
        />
        <DetailTerm
          label="Max approved USD"
          value={formatCostUsd(plan.action_envelope_max_approved_cost_usd)}
        />
        <DetailTerm
          label="Provider ref"
          value={plan.action_envelope_provider_ref ?? "provider-ref:not-invoked"}
        />
        <DetailTerm
          label="Model profile"
          value={
            plan.action_envelope_model_profile_ref ??
            "model-profile-ref:not-invoked"
          }
        />
        <DetailTerm
          label="Provider authority"
          value={
            plan.action_envelope_provider_authority_state_label ??
            "No provider authority"
          }
        />
        <DetailTerm
          label="Unknown paid cost"
          value={
            plan.action_envelope_unknown_paid_cost_requires_explicit_approval
              ? "explicit approval required"
              : "not required"
          }
        />
      </dl>
      <InlineListWithFallback
        emptyLabel="Decision receipt options: missing"
        items={(plan.review_actions ?? []).map(
          (label) => `decision receipt option: ${label}`,
        )}
      />
      <RefListWithFallback
        emptyLabel="Expected receipt refs: missing until scoped contract"
        refs={plan.expected_receipt_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Action envelope blockers: missing"
        refs={plan.blocked_state_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Cost receipt refs: missing"
        refs={plan.action_envelope_cost_receipt_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Cost blockers: missing"
        refs={plan.action_envelope_cost_blocked_state_refs ?? []}
      />
      <TaskDecompositionPlanDetails plan={plan} />
      <RefList refs={plan.evidence_refs} />
    </article>
  );
}

function TaskDecompositionPlanDetails({
  plan,
}: {
  plan: FounderLoopPlanSummary;
}) {
  if (!plan.task_decomposition_proposal_ref) {
    return null;
  }
  return (
    <section
      aria-label="Task decomposition plan detail"
      className="local-task-posture-card"
    >
      <div className="review-card-heading compact">
        <h4>Task decomposition proposal</h4>
        <span>{plan.task_decomposition_status ?? "proposal_only"}</span>
      </div>
      <p className="muted">
        Plan-facing decomposition output is an inspectable proposal. It keeps
        task execution, workflow execution, memory writes, context use, shell,
        browser, connector, and provider authority blocked.
      </p>
      <dl className="detail-list">
        <DetailTerm
          label="Contract"
          value={plan.task_decomposition_contract_ref ?? "missing"}
        />
        <DetailTerm
          label="Request ref"
          value={plan.task_decomposition_request_ref ?? "missing"}
        />
        <DetailTerm
          label="Original request"
          value={plan.task_decomposition_original_request_ref ?? "missing"}
        />
        <DetailTerm
          label="Proposal ref"
          value={plan.task_decomposition_proposal_ref}
        />
        <DetailTerm
          label="Review envelope"
          value={plan.task_decomposition_review_envelope_ref ?? "missing"}
        />
        <DetailTerm
          label="Risk"
          value={plan.task_decomposition_risk_class ?? "missing"}
        />
        <DetailTerm
          label="Why proposed"
          value={plan.task_decomposition_why_proposed ?? "missing"}
        />
        <DetailTerm
          label="Review posture"
          value={plan.task_decomposition_review_only ? "review-only" : "missing"}
        />
        <DetailTerm
          label="Proposal posture"
          value={plan.task_decomposition_proposal_only ? "proposal-only" : "missing"}
        />
        <DetailTerm
          label="Execution authorized"
          value={
            plan.task_decomposition_execution_authorized ? "unsafe" : "blocked"
          }
        />
        <DetailTerm
          label="Action execution"
          value={
            plan.task_decomposition_action_execution_enabled
              ? "unsafe"
              : "blocked"
          }
        />
        <DetailTerm
          label="Tool execution"
          value={
            plan.task_decomposition_tool_execution_enabled ? "unsafe" : "blocked"
          }
        />
        <DetailTerm
          label="Memory write"
          value={
            plan.task_decomposition_memory_write_authorized
              ? "unsafe"
              : "blocked"
          }
        />
        <DetailTerm
          label="Context injection"
          value={
            plan.task_decomposition_context_injection_authorized
              ? "unsafe"
              : "blocked"
          }
        />
      </dl>
      <TaskDecompositionStepList steps={plan.task_decomposition_steps ?? []} />
      <InlineListWithFallback
        emptyLabel="Affected surfaces: missing"
        items={plan.task_decomposition_what_this_affects ?? []}
      />
      <RefListWithFallback
        emptyLabel="Action Inbox proposal refs: missing"
        refs={plan.task_decomposition_suggested_action_inbox_proposal_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Task decomposition dependencies: none"
        refs={plan.task_decomposition_dependency_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Task decomposition ambiguity refs: none"
        refs={plan.task_decomposition_ambiguity_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Task decomposition missing evidence refs: none"
        refs={plan.task_decomposition_missing_evidence_refs ?? []}
      />
      <RefListWithFallback
        emptyLabel="Task decomposition required approvals: missing"
        refs={plan.task_decomposition_required_approvals ?? []}
      />
      <RefListWithFallback
        emptyLabel="Task decomposition blockers: missing"
        refs={plan.task_decomposition_blocked_authority_refs ?? []}
      />
    </section>
  );
}

function TaskDecompositionStepList({
  steps,
}: {
  steps: NonNullable<FounderLoopPlanSummary["task_decomposition_steps"]>;
}) {
  if (!steps.length) {
    return (
      <p className="empty-state">
        No task decomposition steps are available from the backend read model.
      </p>
    );
  }
  return (
    <ol className="ref-list">
      {steps.map((step) => (
        <li key={step.step_ref}>
          <strong>{step.title}</strong>: {step.safe_summary} Risk{" "}
          {step.risk_class}; {step.review_only ? "review-only" : "posture missing"}.
        </li>
      ))}
    </ol>
  );
}

function BriefingCard({
  allowActionEnvelopePromotion = false,
  authoritative = true,
  item,
}: {
  allowActionEnvelopePromotion?: boolean;
  authoritative?: boolean;
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
        <TodayActionEnvelopeControls
          authoritative={authoritative}
          item={item}
        />
      ) : null}
    </article>
  );
}

const memoryDecisionLabels: Record<MemoryReviewDecisionKind, string> = {
  accept: "Record accept receipt",
  correct: "Record correction receipt",
  reject: "Record reject receipt",
  defer: "Record defer receipt",
  merge: "Record merge receipt",
  supersede: "Record supersede receipt",
  expire: "Record expiry receipt",
  forget_request: "Record forget-request receipt",
};

function memoryDecisionReceiptLabel(decision: MemoryReviewDecisionKind): string {
  return memoryDecisionLabels[decision].replace(/^Record /, "");
}

const memoryDecisionOrder: MemoryReviewDecisionKind[] = [
  "accept",
  "correct",
  "reject",
  "defer",
  "merge",
  "supersede",
  "expire",
  "forget_request",
];

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

const manualMemoryCandidateBlockedRefs = [
  "blocked-state:manual-memory-intake-no-recall-record",
  "blocked-state:manual-memory-intake-no-context-injection",
  "blocked-state:manual-memory-intake-no-connector-write",
  "blocked-state:manual-memory-intake-no-delete-execution",
  "blocked-state:manual-memory-intake-no-export-execution",
  "blocked-state:manual-memory-intake-no-production-authority",
];

type MemoryDecisionControlState = {
  status: "idle" | "pending" | "recorded" | "replayed" | "failed";
  decision?: MemoryReviewDecisionKind;
  receipt?: MemoryReviewDecisionReceipt;
  message?: string;
};

type MemoryReviewDecisionSubject = {
  title: string;
  reviewRef: string;
  candidateRef: string;
  sourceRefs: string[];
  evidenceRefs: string[];
  duplicateRefs: string[];
  conflictRefs: string[];
  availableDecisionStates?: string[];
};

function formatRankComponents(components: Record<string, number>): string[] {
  return Object.entries(components)
    .filter(([, value]) => value > 0)
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .map(([label, value]) => `${label.replaceAll("_", " ")}: ${value}`);
}

function memoryDecisionSubjectFromReviewItem(
  item: FounderLoopMemoryReviewItem,
): MemoryReviewDecisionSubject {
  return {
    title: item.title,
    reviewRef: item.review_ref,
    candidateRef: item.business_memory_candidate_ref || item.review_ref,
    sourceRefs: item.source_refs ?? [],
    evidenceRefs: item.evidence_refs ?? [],
    duplicateRefs: item.business_memory_duplicate_of_refs ?? [],
    conflictRefs: item.business_memory_conflict_with_refs ?? [],
    availableDecisionStates: item.available_decision_states ?? [],
  };
}

function memoryDecisionSubjectFromWorkbenchItem(
  item: FounderLoopMemoryWorkbenchItem,
): MemoryReviewDecisionSubject {
  return {
    title: item.title,
    reviewRef: item.review_ref,
    candidateRef: item.memory_ref || item.review_ref,
    sourceRefs: item.source_refs ?? [],
    evidenceRefs: item.evidence_refs ?? [],
    duplicateRefs: item.duplicate_of_refs ?? [],
    conflictRefs: item.conflict_with_refs ?? [],
    availableDecisionStates: item.available_lifecycle_decisions ?? [],
  };
}

function isMemoryReviewDecisionKind(
  value: string,
): value is MemoryReviewDecisionKind {
  return (memoryDecisionOrder as string[]).includes(value);
}

function stableMemoryDecisionEvidenceRefs(refs: string[]): string[] {
  const mutablePrefixes = [
    "receipt:memory-review:",
    "evidence-ref:memory-review:accept:",
    "evidence-ref:memory-review:correct:",
    "evidence-ref:memory-review:reject:",
    "evidence-ref:memory-review:defer:",
    "evidence-ref:memory-review:merge:",
    "evidence-ref:memory-review:supersede:",
    "evidence-ref:memory-review:forget-request:",
  ];
  return refs.filter(
    (ref) => !mutablePrefixes.some((prefix) => ref.startsWith(prefix)),
  );
}

function MemoryReviewCard({
  authoritative,
  item,
}: {
  authoritative: boolean;
  item: FounderLoopMemoryReviewItem;
}) {
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
        <DetailTerm
          label="Truth authority"
          value={item.accepted_as_truth ? "enabled" : "blocked"}
        />
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
      <MemoryReviewDecisionControls
        authoritative={authoritative}
        subject={memoryDecisionSubjectFromReviewItem(item)}
      />
      <InlineListWithFallback
        emptyLabel="Decision labels only: accept, correct, reject, defer, merge, supersede, expire, forget request"
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
  authoritative,
  subject,
}: {
  authoritative: boolean;
  subject: MemoryReviewDecisionSubject;
}) {
  const mutationBinding = useBackendTruthMutationBinding();
  const [state, setState] = useState<MemoryDecisionControlState>({
    status: "idle",
  });
  const [correctedSummaryRef, setCorrectedSummaryRef] = useState(
    `safe-summary-ref:control-center-memory-correction:${safeRefSuffix(
      subject.candidateRef,
    )}`,
  );
  const [correctedSafeSummary, setCorrectedSafeSummary] = useState(
    "Corrected bounded safe summary for review-only recall.",
  );
  const pending = state.status === "pending";
  const availableDecisions =
    subject.availableDecisionStates
      ?.filter(isMemoryReviewDecisionKind)
      .filter((decision, index, decisions) => decisions.indexOf(decision) === index) ??
    memoryDecisionOrder;

  function blockedReason(decision: MemoryReviewDecisionKind): string | null {
    if (decision === "merge" && subject.duplicateRefs.length === 0) {
      return "Requires duplicate refs from the backend workbench.";
    }
    if (decision === "supersede" && subject.conflictRefs.length === 0) {
      return "Requires conflict or supersedable refs from the backend workbench.";
    }
    if (decision === "correct" && correctedSummaryRef.trim().length === 0) {
      return "Requires a corrected safe-summary ref.";
    }
    if (decision === "correct" && correctedSafeSummary.trim().length === 0) {
      return "Requires corrected bounded safe-summary text.";
    }
    return null;
  }

  async function recordDecision(decision: MemoryReviewDecisionKind) {
    if (!authoritative) {
      setState({
        status: "failed",
        decision,
        message:
          "Backend-owned Memory Review read model required before recording decision receipts.",
      });
      return;
    }
    const unavailable = blockedReason(decision);
    if (unavailable) {
      setState({ status: "failed", decision, message: unavailable });
      return;
    }

    setState({ status: "pending", decision });
    try {
      const receipt = await recordMemoryReviewDecision(
        subject.candidateRef,
        decision,
        {
          reviewer_ref: "actor-ref:control-center-memory-review",
          corrected_summary_ref:
            decision === "correct" ? correctedSummaryRef.trim() : undefined,
          corrected_safe_summary:
            decision === "correct" ? correctedSafeSummary.trim() : undefined,
          merge_refs:
            decision === "merge"
              ? subject.duplicateRefs
              : undefined,
          supersedes_refs:
            decision === "supersede" ? subject.conflictRefs : undefined,
          source_refs: subject.sourceRefs,
          evidence_refs: stableMemoryDecisionEvidenceRefs(subject.evidenceRefs),
          metadata_refs: [
            `metadata-ref:control-center-memory-review:${decision}`,
            subject.reviewRef,
          ],
          blocked_state_refs: memoryReviewDecisionBlockedRefs,
        },
        mutationBinding,
      );
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
    <div
      className="decision-controls"
      aria-label={`${subject.title} memory decisions`}
    >
      <label className="field-label">
        Corrected safe-summary ref
        <textarea
          className="text-input"
          disabled={!authoritative}
          onChange={(event) => setCorrectedSummaryRef(event.target.value)}
          rows={2}
          spellCheck={false}
          value={correctedSummaryRef}
        />
      </label>
      <label className="field-label">
        Corrected bounded safe summary
        <textarea
          className="text-input"
          disabled={!authoritative}
          onChange={(event) => setCorrectedSafeSummary(event.target.value)}
          rows={3}
          value={correctedSafeSummary}
        />
      </label>
      <div className="decision-button-row">
        {availableDecisions.map(
          (decision) => (
            <button
              className="secondary-button"
              disabled={
                pending || !authoritative || blockedReason(decision) !== null
              }
              key={decision}
              onClick={() => void recordDecision(decision)}
              title={
                authoritative
                  ? (blockedReason(decision) ?? undefined)
                  : "Backend-owned Memory Review read model required"
              }
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
            label="Approval scope ref"
            value={state.receipt.approval_ref ?? "not returned"}
          />
          <DetailTerm
            label="Suppressed recall refs"
            value={String(state.receipt.suppressed_recall_record_refs?.length ?? 0)}
          />
          <DetailTerm
            label="Defer ref"
            value={state.receipt.defer_ref ?? "not created"}
          />
          <DetailTerm
            label="Merge ref"
            value={state.receipt.merge_ref ?? "not created"}
          />
          <DetailTerm
            label="Supersede ref"
            value={state.receipt.supersede_ref ?? "not created"}
          />
          <DetailTerm
            label="Expiry ref"
            value={state.receipt.expire_ref ?? "not created"}
          />
          <DetailTerm
            label="Forget-request ref"
            value={state.receipt.forget_request_ref ?? "not created"}
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
  authoritative,
  item,
}: {
  authoritative: boolean;
  item: FounderLoopBriefingItem;
}) {
  const mutationBinding = useBackendTruthMutationBinding();
  const [state, setState] = useState<{
    status: "idle" | "pending" | "recorded" | "failed";
    receipt?: FounderLoopActionEnvelopePromotionReceipt;
    message?: string;
  }>({ status: "idle" });
  const pending = state.status === "pending";

  async function createEnvelope() {
    if (!authoritative) {
      setState({
        status: "failed",
        message:
          "Backend-owned Today read model required before recording Action-envelope receipts.",
      });
      return;
    }
    setState({ status: "pending" });
    try {
      const receipt = await submitTodayActionEnvelope(
        {
          today_item_ref: item.briefing_ref,
          actor_context: "control_center_today_surface",
          decision_reason_ref: "decision-reason-ref:today-action-envelope",
          risk_class: "medium",
          priority: item.priority === "high" ? "high" : "medium",
          metadata_refs: [
            "metadata-ref:control-center-today-action-envelope",
            item.briefing_ref,
          ],
        },
        mutationBinding,
      );
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
        disabled={pending || !authoritative}
        onClick={() => void createEnvelope()}
        title={
          authoritative
            ? undefined
            : "Backend-owned Today read model required"
        }
        type="button"
      >
        {pending ? "Recording receipt" : "Record Action-envelope receipt"}
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

function formatCostUsd(value?: number) {
  return typeof value === "number" ? `$${value.toFixed(6)}` : "missing";
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
