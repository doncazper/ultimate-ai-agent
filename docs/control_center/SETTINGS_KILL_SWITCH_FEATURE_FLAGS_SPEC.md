# Settings Kill-Switch And Feature-Flag Spec

Status: FCC-P1-011 spec foundation
Baseline: v0.102.3 / 0.102.3
Scope: Founder Command Center Settings posture, feature-flag vocabulary,
kill-switch posture, scoped permission-mode vocabulary, and future Settings
contract requirements

This document is a contract/spec artifact. It does not add backend routes,
frontend controls, Settings mutation, feature-flag writes, kill-switch
execution, revocation execution, credential collection, background jobs,
connector runtime or writes, model/provider calls, memory writes, context
injection, shell/subprocess execution, browser automation, dependencies, public
distribution claims, public beta claims, or production authority.

## Purpose

The Founder Command Center Settings surface is a local-first inspection and
safety posture surface. In this slice it may explain safe local setup,
disabled-by-default authority, feature-flag posture, kill-switch posture,
revocation posture, blocked states, and next safe actions. It is not an
authority console.

Any future setting that enables runtime authority, persistence, local lifecycle
behavior, connector access, writes, account access, or mutation requires a
separately accepted milestone with:

- PolicyEngine classification.
- LocalApprovalAuthority scope where approval is required.
- Route manifest and OpenAPI truth for any route changes.
- Redacted evidence, audit refs, receipt refs, revocation refs, and
  rollback/safe-disable refs.
- Idempotency and stale-state posture.
- Focused backend/frontend tests and documentation integrity checks.

Approval refs are identifiers only. Naming an approval ref, feature flag,
permission mode, kill-switch posture, or safe-disable posture does not grant
runtime authority.

## Safe Defaults

Settings defaults are conservative:

- Local-only by default.
- Runtime authority disabled by default.
- Connector runtime and connector writes disabled by default.
- Model/provider authority disabled by default.
- Memory writes and context injection disabled by default.
- Background jobs disabled by default.
- Local lifecycle controls disabled by default.
- Redacted summaries and safe refs only.
- Human-readable posture first; raw JSON is never the primary Settings UI.

Settings UI, docs fixtures, tests, reports, and durable evidence must not store
or display raw prompts, responses, provider payloads, local paths, logs,
transcripts, connector payloads, usernames, hostnames, environment dumps,
credentials, tokens, session material, or secret-like values.

## Feature-Flag Posture

Feature-flag states are readable posture labels in this slice. They are not
runtime toggles and they do not create feature-flag write authority.

Allowed posture labels:

| Label | Meaning | Authority result |
|---|---|---|
| `missing` | No accepted flag contract exists. | Blocked until scoped. |
| `planned` | A future milestone may define the flag. | No runtime authority. |
| `blocked` | Safety, evidence, route, or approval requirements are unmet. | No runtime authority. |
| `disabled` | The feature is intentionally off. | No runtime authority. |
| `inspection-only` | The surface may show status or refs. | Read/review posture only. |
| `validation-only` | The contract may validate an envelope or plan. | No execution authority. |
| `enabled-by-config` | A repo/local config may expose a status-only posture. | No write authority from UI. |
| `approval-required` | Future mutation would require exact scoped approval. | No authority until a matching grant is validated. |
| `deprecated` | The flag should not be used for new work. | No new authority. |
| `stale` | Evidence or state is old or untrusted. | Requires refresh/review before reliance. |

Every future feature flag must name:

- Owner and route/service module, if any.
- Scope and default state.
- Side-effect class and risk class.
- Route/API impact, operation ID impact, and manifest/OpenAPI impact.
- PolicyEngine and LocalApprovalAuthority posture.
- Audit refs, evidence refs, receipt refs, revocation refs, and
  rollback/safe-disable refs.
- Stale-state behavior, blocked states, and next safe action.
- Tests and verifiers.

## Kill-Switch Posture

Kill-switch states are readable posture labels in this slice. They do not add
kill-switch execution, revocation execution, process stop, service stop,
connector disablement, lifecycle control, shell/subprocess execution, or any
other mutation.

Allowed posture labels:

| Label | Meaning | Authority result |
|---|---|---|
| `missing` | No accepted kill-switch contract exists. | Blocked until scoped. |
| `planned` | A future milestone may define status or execution. | No runtime authority. |
| `blocked` | Preconditions, route truth, approval, or evidence are missing. | No runtime authority. |
| `not-configured` | No reviewed local kill-switch status is available. | No runtime authority. |
| `armed-by-config` | A reviewed config may indicate readiness posture. | Status only in this slice. |
| `triggered` | A future status route may report a prior trigger. | Report-only unless separately scoped. |
| `stale` | Status evidence is too old or incomplete. | Requires review before reliance. |
| `unknown` | The system cannot determine posture safely. | Treat as blocked. |

Future kill-switch implementation must be exact-scoped, policy-gated,
approval-aware where applicable, idempotent, auditable, receipt-backed,
revocation-aware, redacted, rollback/safe-disable-aware, and tested. Future
status routes may summarize posture, but execution remains a separate mutating
milestone.

## Scoped Permission Modes

These names are planning vocabulary shared by product surfaces. They are not
approval refs, standing grants, background sessions, connector writes,
execution rights, revocation actions, kill-switch actions, or production
authority.

| Mode | PolicyEngine posture | LocalApprovalAuthority posture | Side-effect posture | Evidence requirements | Blocked unless |
|---|---|---|---|---|---|
| Observe | Inspect existing safe status or refs. | No approval for read-only inspection. | `none` or `validation_only`. | Source refs, evidence refs, stale-state posture. | Route/core contract and redaction are present. |
| Draft | Create a non-authoritative proposal. | No execution approval. | `validation_only`. | Proposal refs, evidence refs, blocked execution state. | Draft cannot send, write, persist, or inject context. |
| Propose | Validate a future action envelope. | Approval need may be described only. | `validation_only`. | Risk, side-effect class, approval need, receipt/rollback refs. | No mutation path is exposed. |
| Approve once | Future exact one-time approval. | Requires matching active unexpired grant. | Exact scoped class only. | Audit, receipt, expiry, replay, revocation, rollback refs. | Accepted milestone implements the authority path. |
| Approve rule | Future narrow recurring approval rule. | Requires separate rule contract and revocation. | Exact scoped class only. | Rule scope, audit, receipts, replay, revocation, safe-disable refs. | Standing grant policy is accepted and tested. |
| Autopilot micro-scope | Future bounded autonomous micro-scope. | Requires separate autonomy milestone. | Exact scoped class only. | Session refs, limits, receipts, audit, stop/safe-disable refs. | Autonomy contract, tests, and rollback exist. |
| Kill switch | Future status or execution contract. | Execution requires separate scoped authority. | Status now; mutation later only if scoped. | Status refs, audit refs, safe-disable refs, stale posture. | Execution contract is accepted and tested. |

## Disabled Authority Boundaries

The following remain blocked or not implemented by FCC-P1-011:

- Settings mutation.
- Feature-flag writes.
- Kill-switch execution.
- Revocation execution.
- Account auth or credential collection.
- Connector runtime or connector writes.
- Provider/model authority.
- Background jobs.
- Memory writes or context injection.
- Local service lifecycle controls.
- Shell/subprocess execution.
- Public beta, public distribution, or production authority.

Settings copy must keep these states visible as blocked, missing, not scoped, or
future-scoped. It must not describe them as complete or available.

## Future Route Posture

No Settings route is added by FCC-P1-011. Current Settings behavior remains a
local UI state surface that can point to existing safe status refs such as
Control Center status, runtime readiness, capability matrix, and API manifest
summaries.

Future route candidates require separate scoped approval and may include:

- Read-only Settings summary.
- Validation-only feature-flag status.
- Validation-only kill-switch status.
- Loopback auth-token setup/status summary.
- Reviewed local runtime settings summary.

Future route work must preserve route paths, operation IDs, side-effect classes,
API manifest truth, OpenAPI truth, auth posture, and Control Center route status
truth. `src/ultimate_ai_agent/api/manifest.py` remains authoritative for
side-effect classes.

## Operator-Readable Behavior

A future Settings UI should show human-readable posture before developer
details:

- Current posture.
- Disabled authority boundaries.
- Blocked states.
- Missing prerequisites.
- Stale-state posture.
- Approval needs.
- Evidence refs.
- Audit refs.
- Receipt refs.
- Revocation refs.
- Rollback/safe-disable refs.
- Next safe action.

Developer payloads, if present in a future scoped implementation, must be
secondary to the readable summary and must be redacted and bounded.

## Validation

FCC-P1-011 validation is documentation-only:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
git diff --check
```

Frontend checks are required only if frontend code changes. OpenAPI and API
manifest checks are required only if route/API contracts change. Approval tests
are required only if approval policy contracts are materially changed.

## Rollback

Rollback for this spec is to remove this document and the cross-links/currentness
updates that reference FCC-P1-011. No runtime state, route, settings value,
approval grant, credential, connector state, local service, memory record, or
durable evidence is changed by this spec.
