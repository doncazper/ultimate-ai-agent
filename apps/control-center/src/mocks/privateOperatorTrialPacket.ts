export type PrivateOperatorTrialChecklistItem = {
  itemRef: string;
  surface: string;
  trialState: "pass" | "partial" | "blocked" | "needs_operator_review";
  safeSummary: string;
  evidenceRefs: string[];
  frictionRefs: string[];
  uiCopyTaskRefs: string[];
  nextSafeAction: string;
};

export type PrivateOperatorTrialPacket = {
  contractRef: string;
  milestoneRef: string;
  status: string;
  trialScopeRef: string;
  bootCommandRef: string;
  checklistItems: PrivateOperatorTrialChecklistItem[];
  frictionFindingRefs: string[];
  uiCopyTaskRefs: string[];
  coreLoopGapRefs: string[];
  evidenceRefs: string[];
  blockedStateRefs: string[];
  nextSafeAction: string;
};

export type PrivateOperatorTrialSurfaceReview = {
  reviewRef: string;
  surface: string;
  reviewState:
    | "pending_operator_review"
    | "accepted"
    | "revised"
    | "blocked"
    | "needs_follow_up";
  reviewerRef: string;
  findingRefs: string[];
  frictionRefs: string[];
  uiCopyTaskRefs: string[];
  evidenceRefs: string[];
  blockerRefs: string[];
  nextSafeAction: string;
};

export type PrivateOperatorTrialAcceptanceLedger = {
  ledgerRef: string;
  contractRef: string;
  milestoneRef: string;
  status: string;
  sourcePacketRef: string;
  trialRunState:
    | "not_started"
    | "operator_review_ready"
    | "in_review"
    | "accepted_with_changes"
    | "needs_revision"
    | "blocked";
  surfaceReviews: PrivateOperatorTrialSurfaceReview[];
  manualSmokeStepRefs: string[];
  acceptanceQuestionRefs: string[];
  tuningDecisionRefs: string[];
  evidenceRefs: string[];
  blockedStateRefs: string[];
  nextSafeAction: string;
};

export const privateOperatorTrialPacket: PrivateOperatorTrialPacket = {
  contractRef: "contract-ref:private-operator-ui-functional-tuning:v1",
  milestoneRef: "milestone:uaa-p1-087.2a",
  status: "implemented_private_trial_packet_ui_surface_authority_blocked",
  trialScopeRef: "trial-scope:private-operator-ui-functional-tuning",
  bootCommandRef: "launcher-command:uaa-trial-boot",
  checklistItems: [
    {
      itemRef: "private-trial-check:local-boot",
      surface: "Local Boot",
      trialState: "pass",
      safeSummary:
        "The repo-local trial boot path opens Control Center first and keeps OpenWebUI secondary or blocked.",
      evidenceRefs: ["evidence-ref:private-trial:local-boot"],
      frictionRefs: ["friction-ref:private-trial:local-boot"],
      uiCopyTaskRefs: ["ui-copy-task:private-trial:local-boot"],
      nextSafeAction:
        "Confirm launcher status, log refs, and secondary-shell blocked state before trial use.",
    },
    {
      itemRef: "private-trial-check:today",
      surface: "Today",
      trialState: "partial",
      safeSummary:
        "Today exposes product spine, action, memory, evidence, intent, and readiness refs in one surface.",
      evidenceRefs: ["evidence-ref:private-trial:today"],
      frictionRefs: ["friction-ref:private-trial:today"],
      uiCopyTaskRefs: ["ui-copy-task:private-trial:today"],
      nextSafeAction:
        "Use trial findings to reduce scanning friction before broader product claims.",
    },
    {
      itemRef: "private-trial-check:actions",
      surface: "Actions",
      trialState: "partial",
      safeSummary:
        "Actions shows reviewable envelopes and memory-derived proposals while mutation remains disabled.",
      evidenceRefs: ["evidence-ref:private-trial:actions"],
      frictionRefs: ["friction-ref:private-trial:actions"],
      uiCopyTaskRefs: ["ui-copy-task:private-trial:actions"],
      nextSafeAction:
        "Keep approve/edit/reject/defer as next backend-owned receipt work.",
    },
    {
      itemRef: "private-trial-check:memory",
      surface: "Memory",
      trialState: "partial",
      safeSummary:
        "Memory shows source, provenance, quality, decision, intake, and loop refs without writes.",
      evidenceRefs: ["evidence-ref:private-trial:memory"],
      frictionRefs: ["friction-ref:private-trial:memory"],
      uiCopyTaskRefs: ["ui-copy-task:private-trial:memory"],
      nextSafeAction:
        "Focus the next memory work on real review decisions and durable receipts.",
    },
    {
      itemRef: "private-trial-check:evidence",
      surface: "Evidence",
      trialState: "partial",
      safeSummary:
        "Evidence reads as history with proposed, approved, happened, changed, undoable, stale, and blocked refs.",
      evidenceRefs: ["evidence-ref:private-trial:evidence"],
      frictionRefs: ["friction-ref:private-trial:evidence"],
      uiCopyTaskRefs: ["ui-copy-task:private-trial:evidence"],
      nextSafeAction:
        "Keep evidence summaries compact enough for repeated operator review.",
    },
    {
      itemRef: "private-trial-check:chat-plans-handoff",
      surface: "Chat/Plans Handoff",
      trialState: "blocked",
      safeSummary:
        "Chat and Plans handoff proof remains local-gated and review-only; output is not authority.",
      evidenceRefs: ["evidence-ref:private-trial:chat-plans-handoff"],
      frictionRefs: ["friction-ref:private-trial:chat-plans-handoff"],
      uiCopyTaskRefs: ["ui-copy-task:private-trial:chat-plans-handoff"],
      nextSafeAction:
        "Do not promote Chat until durable receipts and handoff refs are real.",
    },
    {
      itemRef: "private-trial-check:blocked-state-language",
      surface: "Blocked State Language",
      trialState: "partial",
      safeSummary:
        "Blocked-state labels are visible, but trial copy still needs consistency review across core surfaces.",
      evidenceRefs: ["evidence-ref:private-trial:blocked-state-language"],
      frictionRefs: ["friction-ref:private-trial:blocked-state-language"],
      uiCopyTaskRefs: ["ui-copy-task:private-trial:blocked-state-language"],
      nextSafeAction:
        "Tune copy toward next safe action instead of compliance-only wording.",
    },
    {
      itemRef: "private-trial-check:crm-lite-follow-ups",
      surface: "CRM-Lite Follow-Ups",
      trialState: "blocked",
      safeSummary:
        "CRM-lite follow-ups appear as safe memory/action refs only; local business state is not implemented.",
      evidenceRefs: ["evidence-ref:private-trial:crm-lite-follow-ups"],
      frictionRefs: ["friction-ref:private-trial:crm-lite-follow-ups"],
      uiCopyTaskRefs: ["ui-copy-task:private-trial:crm-lite-follow-ups"],
      nextSafeAction:
        "Plan local CRM-lite records after memory review and action receipts are durable.",
    },
  ],
  frictionFindingRefs: [
    "friction-ref:private-trial:blocked-state-language",
    "friction-ref:private-trial:chat-plan-handoff-proof",
    "friction-ref:private-trial:crm-lite-follow-up-gap",
  ],
  uiCopyTaskRefs: [
    "ui-copy-task:private-trial:show-first-party-surface",
    "ui-copy-task:private-trial:name-secondary-openwebui",
    "ui-copy-task:private-trial:surface-next-safe-action",
  ],
  coreLoopGapRefs: [
    "gap-ref:private-trial:memory-decision-execution",
    "gap-ref:private-trial:action-decision-receipts",
    "gap-ref:private-trial:first-party-chat-receipts",
    "gap-ref:private-trial:crm-lite-local-follow-up-store",
  ],
  evidenceRefs: [
    "evidence-ref:private-trial:launcher-boot-readiness",
    "evidence-ref:private-trial:control-center-render-smoke",
    "evidence-ref:private-trial:manual-smoke-checklist",
    "evidence-ref:private-trial:ui-copy-task-ledger",
  ],
  blockedStateRefs: [
    "blocked-state:no-public-beta",
    "blocked-state:no-public-distribution",
    "blocked-state:no-production-readiness-claim",
    "blocked-state:no-production-authority",
    "blocked-state:no-connector-write",
    "blocked-state:no-provider-model-authority",
    "blocked-state:no-unrestricted-shell",
    "blocked-state:no-shell-subprocess-execution",
    "blocked-state:no-remote-execution",
    "blocked-state:no-account-sync",
    "blocked-state:no-crm-write",
    "blocked-state:no-memory-write",
    "blocked-state:no-action-execution",
    "blocked-state:no-code-apply-execution",
    "blocked-state:openwebui-secondary-only",
  ],
  nextSafeAction:
    "Use the private-trial packet to run local/private UI tuning for acceptance review, then keep UAA-P1-087.3 source-only until native boot cockpit scope is accepted.",
};

export const privateOperatorTrialAcceptanceLedger: PrivateOperatorTrialAcceptanceLedger = {
  ledgerRef: "ledger-ref:private-operator-trial-acceptance:v1",
  contractRef: "contract-ref:private-operator-ui-functional-tuning:v1",
  milestoneRef: "milestone:uaa-p1-087.2b",
  status: "implemented_private_trial_acceptance_ledger_authority_blocked",
  sourcePacketRef: "packet-ref:private-operator-trial:v1",
  trialRunState: "operator_review_ready",
  surfaceReviews: [
    {
      reviewRef: "surface-review:private-trial:local-boot",
      surface: "Local Boot",
      reviewState: "pending_operator_review",
      reviewerRef: "operator-ref:local-private-reviewer",
      findingRefs: ["finding-ref:private-trial:pending:local-boot"],
      frictionRefs: ["friction-ref:private-trial:local-boot"],
      uiCopyTaskRefs: ["ui-copy-task:private-trial:local-boot"],
      evidenceRefs: ["evidence-ref:private-trial:local-boot"],
      blockerRefs: ["blocker-ref:private-trial:local-boot"],
      nextSafeAction:
        "Confirm first-party launch, secondary-shell posture, and safe log refs.",
    },
    {
      reviewRef: "surface-review:private-trial:today",
      surface: "Today",
      reviewState: "pending_operator_review",
      reviewerRef: "operator-ref:local-private-reviewer",
      findingRefs: ["finding-ref:private-trial:pending:today"],
      frictionRefs: ["friction-ref:private-trial:today"],
      uiCopyTaskRefs: ["ui-copy-task:private-trial:today"],
      evidenceRefs: ["evidence-ref:private-trial:today"],
      blockerRefs: ["blocker-ref:private-trial:today"],
      nextSafeAction: "Review whether Today makes the next operator step obvious.",
    },
    {
      reviewRef: "surface-review:private-trial:actions",
      surface: "Actions",
      reviewState: "pending_operator_review",
      reviewerRef: "operator-ref:local-private-reviewer",
      findingRefs: ["finding-ref:private-trial:pending:actions"],
      frictionRefs: ["friction-ref:private-trial:actions"],
      uiCopyTaskRefs: ["ui-copy-task:private-trial:actions"],
      evidenceRefs: ["evidence-ref:private-trial:actions"],
      blockerRefs: ["blocker-ref:private-trial:actions"],
      nextSafeAction:
        "Review envelope clarity while approve/edit/reject/defer remains blocked.",
    },
    {
      reviewRef: "surface-review:private-trial:memory",
      surface: "Memory",
      reviewState: "pending_operator_review",
      reviewerRef: "operator-ref:local-private-reviewer",
      findingRefs: ["finding-ref:private-trial:pending:memory"],
      frictionRefs: ["friction-ref:private-trial:memory"],
      uiCopyTaskRefs: ["ui-copy-task:private-trial:memory"],
      evidenceRefs: ["evidence-ref:private-trial:memory"],
      blockerRefs: ["blocker-ref:private-trial:memory"],
      nextSafeAction:
        "Review provenance, quality, and decision refs before memory writes exist.",
    },
    {
      reviewRef: "surface-review:private-trial:evidence",
      surface: "Evidence",
      reviewState: "pending_operator_review",
      reviewerRef: "operator-ref:local-private-reviewer",
      findingRefs: ["finding-ref:private-trial:pending:evidence"],
      frictionRefs: ["friction-ref:private-trial:evidence"],
      uiCopyTaskRefs: ["ui-copy-task:private-trial:evidence"],
      evidenceRefs: ["evidence-ref:private-trial:evidence"],
      blockerRefs: ["blocker-ref:private-trial:evidence"],
      nextSafeAction:
        "Review whether history reads as proposed, approved, happened, changed, undoable.",
    },
    {
      reviewRef: "surface-review:private-trial:chat-plans-handoff",
      surface: "Chat/Plans Handoff",
      reviewState: "pending_operator_review",
      reviewerRef: "operator-ref:local-private-reviewer",
      findingRefs: ["finding-ref:private-trial:pending:chat-plans-handoff"],
      frictionRefs: ["friction-ref:private-trial:chat-plans-handoff"],
      uiCopyTaskRefs: ["ui-copy-task:private-trial:chat-plans-handoff"],
      evidenceRefs: ["evidence-ref:private-trial:chat-plans-handoff"],
      blockerRefs: ["blocker-ref:private-trial:chat-plans-handoff"],
      nextSafeAction:
        "Review handoff clarity while Chat output stays non-authoritative.",
    },
    {
      reviewRef: "surface-review:private-trial:blocked-state-language",
      surface: "Blocked State Language",
      reviewState: "pending_operator_review",
      reviewerRef: "operator-ref:local-private-reviewer",
      findingRefs: ["finding-ref:private-trial:pending:blocked-state-language"],
      frictionRefs: ["friction-ref:private-trial:blocked-state-language"],
      uiCopyTaskRefs: ["ui-copy-task:private-trial:blocked-state-language"],
      evidenceRefs: ["evidence-ref:private-trial:blocked-state-language"],
      blockerRefs: ["blocker-ref:private-trial:blocked-state-language"],
      nextSafeAction: "Review blocked copy for next safe action and low friction.",
    },
    {
      reviewRef: "surface-review:private-trial:crm-lite-follow-ups",
      surface: "CRM-Lite Follow-Ups",
      reviewState: "pending_operator_review",
      reviewerRef: "operator-ref:local-private-reviewer",
      findingRefs: ["finding-ref:private-trial:pending:crm-lite-follow-ups"],
      frictionRefs: ["friction-ref:private-trial:crm-lite-follow-ups"],
      uiCopyTaskRefs: ["ui-copy-task:private-trial:crm-lite-follow-ups"],
      evidenceRefs: ["evidence-ref:private-trial:crm-lite-follow-ups"],
      blockerRefs: ["blocker-ref:private-trial:crm-lite-follow-ups"],
      nextSafeAction:
        "Review follow-up positioning without claiming local CRM state.",
    },
  ],
  manualSmokeStepRefs: [
    "manual-smoke-step:private-trial:boot-control-center",
    "manual-smoke-step:private-trial:review-today-spine",
    "manual-smoke-step:private-trial:review-actions-memory-evidence",
    "manual-smoke-step:private-trial:review-chat-plans-handoff",
    "manual-smoke-step:private-trial:record-blocked-follow-ups",
  ],
  acceptanceQuestionRefs: [
    "acceptance-question:private-trial:first-screen-orientation",
    "acceptance-question:private-trial:today-scan-friction",
    "acceptance-question:private-trial:memory-confidence",
    "acceptance-question:private-trial:action-review-clarity",
    "acceptance-question:private-trial:evidence-history-readability",
    "acceptance-question:private-trial:blocked-state-next-action",
  ],
  tuningDecisionRefs: [
    "tuning-decision:private-trial:pending-copy-trim",
    "tuning-decision:private-trial:pending-surface-order",
    "tuning-decision:private-trial:pending-memory-review-emphasis",
    "tuning-decision:private-trial:pending-crm-lite-positioning",
  ],
  evidenceRefs: [
    "evidence-ref:private-trial:acceptance-ledger-v1",
    "evidence-ref:private-trial:manual-smoke-runbook",
    "evidence-ref:private-trial:pending-operator-findings",
  ],
  blockedStateRefs: privateOperatorTrialPacket.blockedStateRefs,
  nextSafeAction:
    "Run local/private operator review against this ledger, record accepted or revised safe refs, then complete full UAA-P1-087.2 only after findings exist.",
};
