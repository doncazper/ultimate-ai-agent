# FIN-003 Synthetic In-App Workflow

Status: bounded synthetic in-app implementation merged in PR #481 at
`f269cc8e9f9ba8a0e7c752e6bfcb6f08a172dda6`, with post-merge qualification and
owned cleanup recorded by its completed queue child. FIN-003 and Q26 remain
incomplete. The separately admitted
[normal startup continuation](UAA_FINANCE_FIN003_NORMAL_STARTUP.md) preserves
explicit configuration through the launchers and guards stale runtime reuse.

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

### Local setup and shared command path

Build the existing native helper using
[`tools/macos/matrix-protected-cache-helper/README.md`](../../tools/macos/matrix-protected-cache-helper/README.md).
Use an owner-only installed copy and its verified SHA-256. Explicitly configure
the backend process with `UAA_FINANCE_SYNTHETIC_REPOSITORY_DIR` (an absolute,
private sample-book location), `UAA_FINANCE_NATIVE_HELPER_PATH` (an absolute
helper location) and `UAA_FINANCE_NATIVE_HELPER_SHA256` (64 lowercase hexadecimal
characters). Do not reuse a real-data directory. Missing/invalid configuration
never creates a book. `UAA_FINANCE_SAFE_DISABLE=1` blocks new mutations;
unrecognized values also fail closed. The native implementation is macOS-only.

Open `/finance` in the authenticated Control Center. Preview sample-book
creation, confirm it, preview and confirm the fixed two-transaction sample
import, then inspect a transaction and confirm/reject/defer its review. Every
change has a separate preview and confirmation; undo appends compensation.
Reload saved history to inspect durable state. Displayed samples are not a
real-data promotion or an accounting-completion claim.

The CLI uses the same process configuration and Core implementation:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_finance.py workspace
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_finance.py workspace-prepare --help
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_finance.py workspace-run --help
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_finance.py workspace-refresh --help
```

Prepared bundles must be retained privately (owner-only regular files, mode
`0600`) and inspected before `workspace-run --bundle PATH --confirmed`.
`workspace-refresh --bundle PATH` only re-presents the same review/undo intent
or a create/import attempt retained by the Core;
it does not confirm, recover, or save. Fresh confirmation remains required.
Legacy Finance commands and their exact authority contracts remain supported.
After a browser restart, `workspace` exposes `recovery` for the last confirmed
attempt, including create/import and failures before encrypted staging. It
contains the exact retained intent, a fresh presentation of the same payload,
and an optional historical Core-returned receipt. It never proves that the
current book is readable or still at that receipt's revision. Missing result
evidence remains uncertain; only a separately confirmed exact retry can settle
it through normal Core replay. A different intent cannot replace an unresolved
attempt. Opening the view or refreshing the same action never retries it.

For interruptions predating this recovery index, `workspace` exposes a
`pending_review.preparation`
only when the existing encrypted pending review generation can be fully bound
to the current book, original request and exact decision/undo. This preparation
may be retained in a private bundle and separately confirmed using the same
`workspace-run` command. Inspection never promotes a generation or grants a lease.

### Exact API boundary

| Method and route | Effect and binding |
|---|---|
| `GET /control-center/finance/workspace` | Protected read; items/history independently paged at 1–100 records; cannot recover a pending write. |
| `POST /control-center/finance/workspace/preview` | Non-mutating exact preparation from server configuration and the allowlisted synthetic intent. |
| `POST /control-center/finance/workspace/refresh` | Non-mutating fresh presentation of a review/undo or an exact Core-retained create/import preparation. |
| `POST /control-center/finance/workspace/commit` | Exact-confirmed local mutation; durable replay owned by protected Finance receipts, not the global header middleware. |

All POST routes require the current backend revision, instance and truth refs,
`X-UAA-Control-Center-Mutation-Binding: backend-truth.v1`, and an idempotency
header matching the request exactly. Commit additionally requires the literal
`X-UAA-Operator-Confirmed: true`. Local bearer protection, loopback-only CORS,
no-store responses, a shared 30-per-60-second POST budget, and 128-KiB/32-level
pre-decode UTF-8 input limits apply. OpenAPI publishes the structured `413`
response. Classification is `local_sensitive` for reads/preparations and
`mutating_requires_authority` for commit; side effects are
`local_dev_workspace_only`, with production blocked.

OpenAPI's operation-level `x-uaa-idempotency` extension publishes the
at-least-one-header schema: either accepted alias is required; both, if supplied,
must agree with each other and the body's identifier. The manifest marks preview
and refresh as requiring exact request binding without granting mutation
authority. An exact Finance commit rejected by the shared limiter carries a
typed, backend-bound `429` response proving that this invocation stopped before
the commit handler. A generic, malformed or foreign response is not such proof,
and rejection of a retry never settles an earlier uncertain invocation.

The browser preserves a confirmed receipt independently of a failed reload.
An unconfirmed save retains its exact preparation for explicit same-action
retry, including when the reload fails. A read never silently recovers state.
An expired preview that has never been submitted can be closed and prepared
again without sending a save. Once an attempted save is uncertain, expiry alone
does not prove that nothing changed and cannot discard the retained request.
Safe-disable makes the sample import unavailable; it does not mean an import
was recorded. The CLI, Core preparations and OpenAPI share the API-compatible
8–200-character idempotency shape; a non-callable identifier is rejected before
preparation or persistence.
If the server rejects an invocation during non-mutating preparation validation
(including the browser/server expiry race), the Core marks that invocation
`not_attempted`. The API preserves this phase distinction; the browser accepts
only a bounded error response bound to the current backend before enabling
close/reprepare. Error-code text alone is not proof of the phase. Failures after
entering confirmation remain unconfirmed, and a rejected retry never settles
an earlier uncertain attempt or permits its retained identity to be discarded.
The Core retains one bounded, content-free confirmed-attempt record in its
existing private, repository-bound authority directory. It is atomically written
after exact confirmation/current preparation/safe-disable checks and before
authority issuance or book writes. A process lock serializes attempts; an
unresolved identity cannot be replaced by a different request. This record is a
transport-recovery index, not a second ledger or an authority grant. Its private
file checks and deterministic bindings are not cryptographic authentication.
No raw financial values, input content, paths or keys are stored in it. A
secondary result-recording failure cannot erase the Core's returned success;
the retained unresolved identity remains available for exact receipt replay.

After the browser closes, a valid staged review or undo can also be re-presented
from its existing encrypted pending generation. The Core reconstructs and
checks the predecessor snapshot, exact preview, appended record, receipt and
payload fingerprint, including partially promoted generations. The UI requires
`Review interrupted save` and a separate explicit confirmation under current
authority. No browser storage, second book journal or automatic recovery is added.
Invalid or unrelated pending data remains outcome-uncertain. A retained
create/import is presented as that same operation, never as a review decision.
Its staged promotion must authenticate the encrypted state, bind the exact
request/idempotency/payload and revision transition, and revalidate current
authority immediately before promotion. Reads cannot complete it, and a fresh
presentation does not revive a revoked or expired lease. Residual native keys
after a failed create rollback remain an explicit blocked state; recovery never
automatically deletes or replaces them.

### Qualification status

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
