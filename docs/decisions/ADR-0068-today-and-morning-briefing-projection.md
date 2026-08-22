# ADR-0068: Today And Morning Briefing Are Deterministic Projections

- Status: Accepted for bounded ECO-006 projection core
- Date: 2026-08-21

## Context

ECO-002 through ECO-005 establish canonical Tasks, Boards, Calendar, and private
CRM truth. The ecosystem plan requires one readable daily home without creating
a second store of events, tasks, milestones, follow-ups, source proposals, or
evidence. Existing Founder Loop Today and Morning Briefing surfaces remain
compatibility product read models and cannot be silently replaced.

## Decision

Implement ECO-006 as a pure, deterministic projection over exact canonical
source-result objects. Bind every request to one workspace, aware timestamp,
and IANA time zone. Preserve canonical owner/ref, source-result refs,
why-shown refs, evidence/receipt posture, freshness, and explicit ordering
factors on every projected item.

Order only by the published
`contract-ref:eco-006-visible-ordering:v1` factors: lane, urgency, time, and
canonical ref. Perform no hidden scoring or ranking. Treat supplemental Plan,
Inbox, blocker, and receipt candidates as typed bounded inputs whose owner must
match the canonical ownership map.

Expose current, stale, missing, and blocked source status without attempting a
refresh. Reject cross-workspace sources, candidates, and statuses. Reject
duplicate owner/ref items and source statuses.

Apply CRM surface privacy before emitting any item, status, proposal, or proof
ref. A workspace excluded from Today and Briefing leaves no projection trace.
Keep carry-forward proposal-only, separately compose it for each surface, and
grant neither mutation nor background-work authority.

Do not cut over the existing Today or Morning Briefing product routes. Add no
storage, API, CLI, Control Center UI, connector, model/provider, web/browser,
notification, scheduler, or background runtime in this decision.

## Consequences

Today can assemble canonical daily truth while ownership remains in each source
application. Operators and later UIs can inspect exactly why an item appeared,
which proof produced it, whether the source is stale or missing, and how it was
ordered. Privacy changes are enforced before result refs are derived, and an
overdue item produces only an inspectable proposal.

Product integration, source acquisition, approved mutations, public release,
and production authority remain separate decisions with their own acceptance
evidence.
