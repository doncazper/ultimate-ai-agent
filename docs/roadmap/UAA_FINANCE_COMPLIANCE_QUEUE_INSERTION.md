# UAA Finance & Compliance Queue Insertion

Status: proposed durable queue placement; planning-only authority
Baseline: v0.104.0 / 0.104.0
Date: 2026-08-16
Product contract: `docs/product/UAA_FINANCE_COMPLIANCE_PRODUCT_CONTRACT.md`
Workflow case study: `docs/product/UAA_FINANCE_WORKFLOW_CASE_STUDY_001.md`
Implementation plan:
`docs/implementation/UAA_FINANCE_COMPLIANCE_IMPLEMENTATION_PLAN.md`
Threat model: `docs/security/UAA_FINANCE_COMPLIANCE_THREAT_MODEL.md`
FIN-000 matrix: `docs/product/UAA_FINANCE_FIN000_ACCEPTANCE_MATRIX.md`

## Decision

Finance & Compliance is a first-class future product program inside the UAA
coherent app ecosystem. It is important enough to preserve now, but it does not
interrupt the active Founder Command Center spine or the foundational Kanban,
Calendar, Today, Action Inbox, and shared-data work.

The queue rule is:

```text
now: FIN-000 product contract, threat model, and UAA-style render acceptance

then:
ECO-001 shared local data/security foundation
-> ECO-002 Tasks
-> ECO-003 Boards/Kanban
-> ECO-004 Calendar
-> ECO-006 Today/Briefing
-> ECO-007 Action Inbox
-> ECO-008 cross-app ChangeSets
-> FIN-001..FIN-008 + COMP-001 local Finance & Compliance product
-> ECO-009 exact read-only connector foundation
-> FIN-CONN-001 / COMP-CONN-001 exact named read adapters
-> FIN-CPA-001 accountant collaboration
-> FIN-FILE-001 optional professional filing handoff
```

`ECO-005` CRM can progress in parallel where its accepted dependencies and WIP
limits allow. Finance implementation is promoted only by the active board after
the listed foundation gates pass.

## Why This Placement

- Boards/Kanban is needed for close, tax-readiness, renewal, and cleanup
  workflows.
- Calendar is needed for recurring payments, estimated taxes, closes, licenses,
  and sourced obligation projections.
- Today and Action Inbox are needed for daily review, missing context, rule
  approval, reconciliation exceptions, and deadline decisions.
- ChangeSets are needed for preview, exact consequences, idempotency, receipts,
  conflicts, rollback, and multi-surface coherence.
- The local book must prove useful before connectors make the data boundary and
  failure modes harder.
- Optional Social and other expansion lanes do not need to block the local
  Finance program once these core dependencies are accepted; the active board
  chooses one lane under WIP limits.

## Relationship To The Immutable Remaining Queue

`docs/roadmap/UAA_REMAINING_QUEUE_MANIFEST.json` records a separately accepted,
hash-protected execution sequence derived from an earlier ordered prompt pack.
This insertion does not edit, reorder, reinterpret, or supersede that manifest.

Finance is queued through the coherent app ecosystem plan and the active
Founder Command Center/current boards. If the immutable manifest later needs a
new successor version, that is a separate governance change with updated
hashes, verifiers, and explicit approval—not an incidental documentation edit.

## Priority And WIP Policy

- `FIN-000` is `P2` planning/design work and may be reviewed without runtime
  authority.
- `FIN-001` becomes eligible for synthetic-only implementation after the
  dependency gate and founder private-dogfood direction acceptance, normally
  ahead of optional broad ecosystem expansion because continuous financial
  readiness is a core founder/operator workflow.
- Eligibility is not activation. The current board must name the milestone in
  progress and retire or pause another lane under WIP limits.
- Connector, collaboration, and filing milestones are never bundled into the
  local MVP to make the feature appear complete.

## Board Representation

The active records are:

- `FIN-000` and the future Finance program card in
  `docs/kanban/current_board.md`;
- `FCC-FINANCE-001` in the deferred future product lanes of
  `docs/kanban/founder_command_center_board.md`;
- the detailed work-package sequence in
  `docs/implementation/UAA_FINANCE_COMPLIANCE_IMPLEMENTATION_PLAN.md`.

The boards carry short operational summaries. This document and the product
contract remain the durable source for placement and vision, preventing a
future queue cleanup from reducing Finance to “connect banks and categorize
transactions.”

## Activation Checklist

Before `FIN-001` moves to `In Progress`, record:

- accepted `FIN-000` contract, threat model, architecture decision, and either
  founder private-dogfood render direction for synthetic-only FIN-001 or the
  stricter independent pack acceptance for later real-data promotion;
- accepted dependencies through `ECO-008` or an explicit reviewed exception
  proving the same ownership/ChangeSet guarantees;
- exact first runtime slice and non-goals;
- protected data, key, migration, backup/restore, deletion, and redaction plan;
- CLI/API/UI parity and focused verifier plan;
- rollback/safe-disable and synthetic evidence plan;
- no live connector or professional-service claim.

Before any connector or filing milestone starts, repeat the checklist for that
exact named capability. Acceptance of Finance never grants standing financial,
compliance, payment, filing, browser, provider, or external-write authority.

The checklist above is recorded for the synthetic-only FIN-001 slice in
`docs/product/UAA_FINANCE_FIN001_ACTIVATION_RECORD.md` and
`docs/product/finance_fin001_activation_v1.json`. The current board explicitly
promotes that bounded package into the otherwise-empty `product_surface` WIP
lane. This closes the activation prerequisite only; it does not implement the
kernel or satisfy the independent real-data promotion gate.
