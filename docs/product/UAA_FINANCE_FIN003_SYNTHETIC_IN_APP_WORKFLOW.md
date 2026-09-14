# FIN-003 Synthetic In-App Workflow

Status: implementation in progress in the separately admitted synthetic in-app
lane. This document is a development contract, not completed product evidence.
FIN-003 and Q26 remain incomplete.

## Bounded operator journey

The accepted slice exposes the existing synthetic Finance kernel through one
Python-owned workflow shared by CLI and authenticated local Control Center:
inspect setup, preview and confirm sample-book creation, preview and confirm
the allowlisted sample import, review an exact item, preview and confirm its
disposition, reopen the saved history, and preview and confirm compensating undo.
No HTTP input chooses a repository path, helper executable, encryption backend,
arbitrary input file, account, provider, or external destination.

The server must explicitly configure the private repository and pinned native
helper. Missing configuration, unavailable keys, unsupported hardware, stale
source, revoked authority and uncertain persistence are visible states. There is
no in-memory crypto or mock-success fallback in the running application. Native
availability on one macOS host is not Windows or multi-computer qualification.

Preview does not create a book, key, authority store or lease. Confirmation is
exact and separate, invoking PolicyEngine, LocalApprovalAuthority and an active
scope-bound lease through the existing Finance service. The browser is a shell,
not the issuer of authority. Backend identity and idempotency bindings remain
mandatory. Read-only inspection cannot recover an interrupted write.

## Pre-implementation invariant matrix

| Class | Applicability and required evidence |
|---|---|
| Authority and provenance | Applicable: only server-configured native storage; exact current Core preview and operator confirmation; stored approval, lease and policy revalidation at promotion. Tests reject foreign repository, injected operation, altered preview, expired/revoked authority and safe-disable. |
| Atomicity and recovery | Applicable: use existing encrypted generations and retained receipts; no second persistence implementation. Tests exercise same-intent retry, separate-process reopen, uncertain outcome and append-only undo. |
| Concurrency and generations | Applicable: preserve existing writer-lock order and current revision binding; concurrent or stale submissions cannot silently replace another decision. |
| Tampering and substitution | Applicable: bind operation, item, source revision, compensation, request/idempotency and preparation; test cross-operation, cross-book, substituted decision and changed server configuration. |
| Capacity and retention | Applicable: bound raw bytes and JSON nesting before decode, typed fields and lists before materialization, and paginate displayed history/items. Existing history and encrypted-store limits remain unchanged. |
| Failure truth | Applicable: distinguish setup missing, unavailable, ready, not started, committed, stale and outcome uncertain. Preserve a committed receipt when subsequent projection fails; do not convert unavailable state into empty success. |
| Cross-surface parity | Applicable: Python workflow, CLI, API/OpenAPI, route manifest and Control Center share exact request/receipt contracts. Verify authenticated routes, no-store/CORS, backend identity and rendered setup/import/save/reopen/undo. |

## Verification and remaining boundaries

Focused authority/recovery tests, API/schema/manifest tests and rendered desktop
and narrow-screen journeys are required before qualification. Final publication
also requires broad verification, an exact-head security scan, independent review,
hosted CI and Supply Chain, normal merge, post-merge proof and owned-workspace
cleanup. Planned checks are not recorded as passed.

This slice does not add real financial data, categorization, corrections,
transfer linking, split/allocation, rules/learning, bulk writes, documents/OCR,
connector/provider/model calls, payment, filing, external writes, production or
distribution authority. Confirm/reject/defer change review disposition only;
accounting entries remain unchanged. The full implementation plan remains the
authority for subsequent Finance work and independent real-data promotion.
