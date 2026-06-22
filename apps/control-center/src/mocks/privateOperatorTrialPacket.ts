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
