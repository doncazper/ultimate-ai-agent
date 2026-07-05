# Unblock CRM Sends And Writes Prompt

Use this only after CRM M2 local command center is accepted and a separate
authority graduation is requested.

Implement the smallest exact-scoped CRM send or write lane that preserves UAA
authority invariants. Start from
`docs/control_center/authority_graduation_blockers/crm_sends_writes_2026_07_05.md`.

Requirements:

- Define one exact send/write action, one target class, one approval scope, and
  one receipt shape.
- Add draft/review envelope, PolicyEngine decision, exact
  LocalApprovalAuthority validation, idempotency, replay/conflict behavior,
  safe-disable posture, rollback or rollback-readiness posture, CLI/API/Control
  Center parity, OpenAPI, route classification, tests, docs, and verifier
  coverage.
- Store safe refs, bounded summaries, decision metadata, and redacted receipts
  only.
- Do not add broad connector write authority, background campaigns, account
  sync, contact import commit, silent merge, provider/model calls, browser
  automation, production targets, public beta, public release, production
  readiness, or production authority.

If the lane cannot be exact-scoped with redacted evidence and rollback posture,
stop with a blocker report instead of implementing send/write execution.
