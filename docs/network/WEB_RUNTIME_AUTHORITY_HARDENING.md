# Web Runtime Authority Hardening

Status: contract-first hardening lane, no runtime authority

Scope: typed contracts, safe-ref audit posture, side-effect ledger blockers,
approval linkage fields, operator-facing state labels, provider diagnostics,
catalog/manifest visibility boundaries, and verification lanes.

Non-goals: live web fetching, browser automation, provider SDK calls, POST,
click, form, download, upload, mutation execution, callable runtime authority,
new API routes, or route side-effect reclassification.

## Canonical Runtime Nouns

All future agent-facing public-web runtime work must use these nouns:

- `web_request`
- `web_observation`
- `web_evidence`
- `web_approval`
- `web_action_plan`
- `web_audit_record`

These nouns are contracts, not execution authority. They name the artifacts that
must exist before later milestones can discuss promotion.

## Audit First

Durable audit storage comes before provider or browser execution.

Any future `web_audit_record` must store safe refs and redacted summaries only.
It must not contain raw prompt content, raw response content, provider exchange
content, raw local paths, raw logs, usernames, hostnames, environment dumps,
credentials, or secrets.

The durable audit posture is append-only, redacted, and verification-bound. A
missing audit store keeps runtime execution blocked.

## Side-Effect Ledger

The side-effect ledger must carry blocked states before any of these can be
promoted:

| Side effect | Required state |
|---|---|
| `POST` | `blocked_pending_durable_audit` |
| `click` | `blocked_pending_durable_audit` |
| `form` | `blocked_pending_durable_audit` |
| `download` | `blocked_pending_durable_audit` |
| `upload` | `blocked_pending_durable_audit` |

`web_action_plan` artifacts may describe a future reviewed plan, but they do
not execute side effects.

## Approval Linkage

`web_approval` records may link approval refs to request, evidence, audit, and
scope refs. Approval refs remain identifiers only.

Presence of an approval ref does not authorize scoped execution. Exact scope
validation through the approval authority is required before any later scoped
execution milestone can proceed.

## Operator Labels

Operator-facing surfaces must use explicit labels:

- Blocked: execution is unavailable until required evidence gates pass.
- Degraded: metadata is inspectable, but runtime authority is unavailable.
- Partial: the boundary exists, but promotion gates are incomplete.

These labels are allowed in UI/docs. They must not be softened into ready,
enabled, or available wording unless a later accepted milestone provides
evidence and tests.

## Verification Lanes

Every promotion step has a named verification lane:

| Promotion step | Verification lane |
|---|---|
| canonical runtime nouns | `verification-lane:web-runtime-authority:canonical-nouns` |
| durable web audit storage | `verification-lane:web-runtime-authority:durable-audit-storage` |
| side-effect ledger states | `verification-lane:web-runtime-authority:side-effect-ledger` |
| approval linkage fields | `verification-lane:web-runtime-authority:approval-linkage` |
| operator labels | `verification-lane:web-runtime-authority:operator-labels` |
| provider diagnostics | `verification-lane:web-runtime-authority:provider-diagnostics` |
| catalog/manifest visibility | `verification-lane:web-runtime-authority:catalog-manifest-visibility` |

Promotion is blocked when a lane is missing, failing, or not yet implemented.

## Provider Diagnostics

Provider diagnostics are diagnostic-only.

They may expose safe provider manifest refs, blocked health posture, and
operator-visible degraded or blocked labels. They do not perform provider
network calls, use provider SDKs, validate credentials, create sessions, or
grant provider authority.

## Catalog And Manifest Visibility

Catalog and manifest visibility is metadata-only.

Read-only catalog or manifest entries can help an operator understand what is
known, configured, partial, blocked, or missing. Visibility does not imply a
callable runtime, runtime import, provider authority, browser authority, or
execution authority.

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_web_runtime_authority_contract.py
.venv/bin/python scripts/verify_web_runtime_authority.py
```

These checks fail if canonical nouns are missing, audit records accept
raw/private/provider exchange content, side effects are not blocked, approval
refs imply authority, provider diagnostics imply provider authority, catalog or
manifest visibility is treated as callable runtime, or promotion steps lack
named verification lanes.
