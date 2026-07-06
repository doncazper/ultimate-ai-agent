# Portfolio Current Status

Status: active portfolio current-state summary
Baseline: v0.104.0 / 0.104.0
Scope: documentation-only status summary

This document gives an external reviewer a compact view of what is implemented,
partial, planned, mock-only, blocked, and intentionally out of scope. It is a
readable companion to the product truth packet, not a competing roadmap.

Canonical sources remain:

- `README.md`
- `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- `docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md`
- `docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md`
- `docs/portfolio/PRODUCT_NORTH_STAR.md`

## North-Star Visual Target

The screenshots in [PRODUCT_NORTH_STAR.md](PRODUCT_NORTH_STAR.md) define the
current intended Founder Command Center cockpit direction. They are
north-star visual targets, not implementation evidence by themselves. The
current UI is not yet close to those images.

Existing implementation remains governed by current route/API contracts, test
evidence, verifiers, release-truth docs, and redacted evidence refs. Any gap
between the north-star visuals and implemented UI/API behavior must remain
labeled as partial, planned, blocked, mock-only, or intentionally out of scope
until it is implemented and verified.

## Implemented

These claims are for the exact repository scope only. They are not production,
public release, public beta, public distribution, or broad autonomy claims.

| Area | Implemented scope |
|---|---|
| Baseline | Active product/package baseline is `v0.104.0` / `0.104.0`. |
| API boundary | FastAPI/OpenAPI boundary with 151 paths, `/api/manifest`, route classification, auth posture, approval posture, idempotency posture, targeted local rate-limit posture, and route inventory checks. |
| Product language | Control Center product-language rules and operator readiness taxonomy distinguish shipped, partial, planned, blocked, skipped, mock-only, status-only, review-only, validation-only, and not-scoped states. |
| Founder Loop V1 proof lane | `FCC-V1-000` through `FCC-V1-007` are complete for bounded route-surface proof: release surface truth, API perimeter posture, Action decisions, Today-to-Action receipt loop, Chat receipts/handoff, Memory Review decisions, Evidence Timeline productization, and proofed `/actions`, `/chat`, `/memory`, and `/evidence` surfaces. |
| Action Inbox | Backend-owned approve/edit/reject/defer decision state, idempotency replay/conflict posture, local receipt refs, receipt visibility, and one exact approved `local_task_create` local task lane. |
| Chat | Durable safe Chat turn receipts and reviewable Actions/Plans handoff receipts. Handoff proposals do not execute. |
| Memory | Review receipts, reviewed recall-only records, L1/L2/L3 read-only indexes, Phase 5 proposal-only context-pack envelopes, and Phase 6.1 internal Action proposal receipts from reviewed context-pack refs. |
| Evidence | Backend-owned safe-ref Evidence Timeline events for proposals, decisions, Chat receipts, handoffs, memory-review decisions, and related proof surfaces. |
| Local model evidence | Local model smoke/readiness/inventory/CLI/status evidence lanes exist for inspection and readiness posture. They do not grant lifecycle authority. |

## Implemented With Narrow Scope

| Area | Narrow scope |
|---|---|
| Local task lane | The exact approved `local_task_create` lane can create local task state with receipts. It is not generic execution, connector write authority, shell/subprocess authority, provider/model authority, or external side-effect authority. |
| Memory Phase 6.1 | Internal Action proposal receipts can be created from reviewed context-pack refs after exact approval and idempotency validation. They do not execute actions or inject context. |
| Local `/v1` lane | Local model gateway surfaces are disabled by default, loopback/local-only, bearer-gated where scoped, and evidence-oriented. Model output remains non-authoritative. |

## Partial

| Area | Why partial |
|---|---|
| Today and Morning Briefing | The product spine and summaries exist, but the broader daily workflow is not complete. |
| Plans | Planning and action-envelope posture exist, but the broader product Plans workflow remains incomplete. |
| Settings | Backend-owned read-only status/proposal posture exists; mutating feature flags, kill-switch execution, and runtime settings changes remain future scoped. |
| Models | Read-only inventory/status and readiness posture exist; start/stop/switch/download/lifecycle controls remain blocked. |
| Runtime, Approvals, Files | Useful inspection and validation paths exist; broader operator workflows and product polish remain partial. |
| Private operator trial | Packet, ledger, and manual-review scaffold exist; full in-person private UI functional tuning is deferred. |
| Release evidence | Scaffolds and verifiers exist; populated release-candidate evidence remains candidate-specific. |

## Planned

| Area | Planned direction |
|---|---|
| Source readiness | Read-only or draft-only email/calendar/source contracts before any connector runtime. |
| CRM-lite memory | Professional memory for people, organizations, opportunities, commitments, stale follow-ups, and relationship context, with visible provenance and "why shown" explanations. |
| Weekly Review | Evidence-backed weekly summaries that distinguish completed, deferred, rejected, blocked, stale, planned, and missing-source states. |
| Self-healing recommendations | Verifier, docs-currentness, UI friction, blocked-state, and source-readiness findings as reviewable recommendations. |
| Dogfood harness | Local/private daily-use metrics and friction notes captured as safe refs before readiness claims change. |
| Native polish | Launcher/setup/native UX polish only after proven local loops and authority boundaries are preserved. |

## Mock-Only Or Presentation-Only

| Area | Boundary |
|---|---|
| Mock/degraded Control Center fallback data | Can show UI shape, but cannot claim backend-owned truth, approval eligibility, or local task commit readiness. |
| CRM `/crm` local command center | Partial backend-owned local CRM surface over Python-core read routes, CLI inspection, local storage posture, redacted import/export preview, deterministic proposal refs, and exact `contacts/write`-gated local mutation receipts. It does not have connector runtime, connector writes, external CRM writes, account sync, contact import commit, sends, calendar writes, provider/model calls, live web, browser runtime, public beta, public release, production readiness, or production authority. |
| React-only UI state | Limited to presentation concerns such as filters, selected tabs, expanded panels, selected rows, and layout preferences. |
| Preview/review-only controls | Can explain proposed state, validation posture, or review posture. They do not execute or grant authority. |

## Blocked

These are blocked until a later accepted milestone grants exact scope with
tests, receipts, evidence, redaction, CLI/core/API parity, and rollback or
safe-disable posture.

| Blocked class | Current posture |
|---|---|
| Public release/beta/distribution | Not claimed. |
| Production authority | Not claimed. |
| Broad autonomy | Not claimed. |
| Connector writes | Blocked. |
| Live email/calendar runtime | Blocked beyond contract/readiness planning. |
| Generic action execution | Blocked beyond the exact local task lane. |
| Shell/subprocess execution | Blocked. |
| Unrestricted browser/network authority | Blocked. |
| Provider/model authority | Blocked; model output is not authority. |
| Memory writes outside reviewed recall paths | Blocked. |
| Hidden context injection | Blocked. |
| Plugin runtime import/execution | Blocked. |
| Model lifecycle actions | Start, stop, switch, download, identity update, and lifecycle mutation remain blocked. |

## Intentionally Out Of Scope

- Hosted production deployment.
- Signed installer or public packaging claims.
- External service authority.
- Account authentication or credential handling for live connectors.
- Raw prompt, raw response, raw provider payload, raw local path, raw log,
  username, hostname, environment dump, credential, token, or secret-like
  material in durable evidence.
- Treating OpenWebUI, Control Center, model output, memory recall, preview
  output, or React state as production authority.
- Commercialization or public distribution claims without a separate accepted
  release packet.

## Quick Evaluation Path

For product state, read `README.md`, this file, and
`docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`.

For the portfolio demo path, read `docs/portfolio/PRODUCT_NORTH_STAR.md`,
`docs/portfolio/SCREENSHOTS.md`, and `docs/portfolio/GOLDEN_PATH_DEMO.md`.

For architecture, read `docs/api/README.md` and
`docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`.

For safety language, read `docs/control_center/PRODUCT_LANGUAGE_RULES.md`.

For route-surface proof, read
`docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md`.
