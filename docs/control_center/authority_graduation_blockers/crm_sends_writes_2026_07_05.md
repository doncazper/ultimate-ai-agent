# CRM Sends And Writes Blocker

Date: 2026-07-05
Status: blocked pending exact AuthorityLease domain/capability support

## Blocked Capability

CRM sends and writes remain blocked. CRM M2 can record exact local mutation
receipts only after idempotency and exact LocalApprovalAuthority validation. It
cannot send messages, write external CRMs, update accounts, create contacts,
merge contacts, schedule calendar events, archive or label messages, or mutate
external systems.

## Required Before Unblock

- Exact domain/capability definition for one write or send action, not a broad
  CRM-write flag.
- Target test account or local-only harness with no production target.
- Draft/review envelope with exact subject, target ref, payload summary ref,
  risk class, side-effect class, approval scope ref, and expected receipt ref.
- PolicyEngine and LocalApprovalAuthority validation for the exact capability.
- Idempotency, replay/conflict behavior, safe-disable posture, and rollback or
  rollback-readiness posture.
- Durable redacted receipt with no raw body, contact detail, account material,
  provider payload, path, log, credential, or secret-like value.
- CLI/API/Control Center parity and no UI-only authority.
- OpenAPI, route classification, docs, tests, and verifier coverage.

## Still Denied

Broad connector write authority, unattended sends, background campaigns,
account sync, contact import commit, silent merge, browser automation,
provider/model authority, production targets, public beta, public release,
production readiness, and production authority remain denied.
