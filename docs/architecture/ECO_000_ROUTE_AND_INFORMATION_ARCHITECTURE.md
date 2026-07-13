# ECO-000 Planned Route And Information Architecture

Status: accepted planning target only. No listed future route is implemented or
authorized by ECO-000. Current route and operation-ID contracts remain intact.

## Shell reconciliation

The accepted static shell remains the compatibility baseline: Start Here,
Today, Source Inbox, Plans, Work Board, Action Inbox, Proof, Trust, Memory,
Evidence, and Settings. Ecosystem work evolves that shell incrementally rather
than renaming or removing routes in one migration.

| Planned primary destination | Planned route family | Current compatibility entry | App-local navigation |
|---|---|---|---|
| Today | `/today` | current Today and Morning Briefing | Home, Briefing, Agenda, Focus, Weekly Review |
| Inbox | `/inbox` | Source Inbox and readiness inspectors | Sources, Threads, Proposals, Drafts, Conflicts |
| Calendar | `/calendar` | calendar readiness under source/settings inspection | Day, Week, Month, Agenda, Calendars, Conflicts |
| Tasks | `/tasks` | Action Inbox local-task and Work Board task projections | Inbox, Today, Upcoming, Projects, Waiting, Reviews |
| Boards | `/boards` | `/work-board` compatibility deep link | Boards, Templates, Views, Filters, Archived |
| Plans | `/plans` | current Plans | Active, Milestones, Dependencies, Archived |
| CRM | `/crm` | current partial CRM Local Command Center | Home, People, Sales, Real Estate, Networks, Reports |
| Action Inbox | `/actions` | current Action Inbox | Needs review, Scheduled posture, Decisions, Receipts |
| Memory | `/memory` | current Memory Review/Workbench | Review, Search, Context, Quality, Maintenance |
| Evidence | `/evidence` | Evidence and Proof compatibility entries | Timeline, Receipts, Verification, Exports |
| Settings | `/settings` | Settings plus Trust/runtime inspectors | General, Privacy, Sources, Authority, Runtime, Storage, Export/Delete |

`/proof`, `/trust`, `/models`, `/runtime`, and detailed source-readiness routes
remain valid compatibility deep links until a separately accepted route
migration proves redirects, bookmarks, OpenAPI/manifest inventory, CLI parity,
and operator discoverability. Their long-term primary placement is Evidence or
Settings, but inspection truth must not be hidden.

## Global interaction ownership

| Concern | Owner and planned behavior |
|---|---|
| Global search | Python backend read model; returns canonical ref, owner app, workspace, why shown, provenance, privacy, freshness, and permitted proposal actions. |
| Command palette | Shell presentation over backend contracts; may navigate or create drafts/proposals, never mint authority or bypass owning app. |
| Recent items | Backend-owned safe-ref projection with workspace/privacy filtering; no browser-local domain truth. |
| Cross-app linking | Typed EntityLink preview and explicit link mutation contract in a later milestone. |
| Direct-app launch | Deep link selects app workspace; app remains inside Control Center initially. Separate binaries are deferred. |
| Notifications | Governance-owned delivery posture; source apps produce notification candidates, not delivery authority. |
| Settings | Owns app preferences, source configuration, privacy, authority inspection, storage, export/delete posture; app-local settings deep link here with app context. |
| Privacy/authority status | Persistent shell indicator sourced from backend truth; visible in review, partial failure, wallboard, and narrow states. |

## Deep-link grammar target

```text
/{app}
/{app}/{workspace_ref}
/{app}/{workspace_ref}/{view}
/{app}/{workspace_ref}/{entity_kind}/{entity_ref}
/settings/{section}?app={app}&source={source_ref}
/evidence/receipts/{receipt_ref}
```

Refs remain opaque, safe, bounded identifiers. Private values never enter URLs.
Search queries use protected POST contracts when later implemented so private
query text does not enter browser history or access logs.

## Narrow and wallboard navigation

Narrow mode exposes Today, Agenda, Capture, Tasks, and People plus an app
switcher. It never hides approval risk, expiry, private scope, or destructive
posture. Wallboard mode exposes privacy-filtered Today, schedule, routines, and
lists; it is view-only, locked by default, has no private relationship detail,
and offers no approval or mutation control.

## Route implementation gate

Every future route needs a stable unique operation ID, local auth posture,
side-effect/risk classification, idempotency and rate limit where mutating,
API-manifest declaration, CLI parity, evidence/redaction contract, product-
language review, focused tests, and migration/rollback plan. `/api/manifest`
remains stable declaration metadata rather than live app health.
