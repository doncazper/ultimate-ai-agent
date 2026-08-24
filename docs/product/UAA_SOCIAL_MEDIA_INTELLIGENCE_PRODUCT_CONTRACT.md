# UAA Social Media Intelligence Product Contract

Status: accepted product direction; planning-only, read-only MVP
Baseline: v0.104.0 / 0.104.0
Accepted: 2026-07-13
Parent plan:
`docs/implementation/UAA_COHERENT_APP_ECOSYSTEM_IMPLEMENTATION_PLAN.md`

This contract locks the product purpose, naming, information architecture,
cross-app ownership, initial functions, authority boundary, and README-ready
language for UAA Social Media Intelligence. It does not add a route, frontend
control, storage model, connector, account authentication, source ingestion,
provider/model call, browser automation, publishing, reply, scheduling write,
background polling, public release, or production authority.

## Executive Decision

UAA will have a first-class **Social** destination built for creators and
founder-operators who need to understand performance, protect a consistent
publishing rhythm, notice important conversations, and turn audience feedback
into governed work.

Social is an intelligence and coordination layer. It does not ship a second
calendar, a second Kanban board, a second messenger, a second CRM, or a second
asset editor.

The accepted ownership statement is:

> Social owns interpretation. Calendar owns time. Work Board owns production.
> Communications owns conversations. CRM owns relationships. Studio owns
> assets. Evidence owns proof.

The initial product posture is read-only. UAA may organize, compare, rank, and
explain authorized social data. It may open the canonical owning app with the
relevant source-linked context. It may not publish, reply, delete, reschedule,
follow, unfollow, moderate, change an account, or perform any external social
action.

## Product Promise

Social gives a creator one calm operating loop for answering five questions:

1. What changed?
2. Why did it change?
3. What deserves attention now?
4. Where should the resulting work happen?
5. What did we learn for the next cycle?

The loop is:

```text
Measure -> Explain -> Prioritize -> Route context -> Review -> Learn
              |             |             |
              |             |             +-> Communications / CRM
              |             +----------------> Calendar / Work Board / Studio
              +------------------------------> Evidence / Trust
```

## Accepted Naming And Navigation

### Primary destination

- Global navigation label: **Social**
- Product name in descriptive copy: **Social Media Intelligence**
- Proposed route name: `/social` only after a separately accepted route and
  backend contract milestone

`Social Media Manager` is reserved for a later product stage that can prove
exact, separately authorized publishing or reply capabilities. The read-only
MVP uses `Social Media Intelligence` so its name does not overstate external
management authority.

### Social-local navigation

The accepted top-level Social tabs are:

1. **Overview**
2. **Performance**
3. **Audience**
4. **Campaigns**
5. **Sources**

Social does not have Calendar, Content, or Engage tabs. Those labels would
duplicate canonical applications.

### Communications integration

- Communications tab: **Social Media**
- Selected priority view inside that tab: **Needs attention**
- Additional filters: High-signal questions, Support risks, Potential leads,
  channel, person, campaign, freshness, and review state

`Social Media` names the destination. `Needs attention` names the current
filter. `Social Attention` is not an accepted destination label.

### Saved views in owning applications

- Calendar: **Social publishing**
- Work Board: **Social Content**
- Communications: **Social Media**

These are projections and saved views, not new copies of events, tasks, cards,
threads, people, or assets.

## Read-Only MVP Functions

### 1. Source readiness and coverage

Social shows the state of every configured or proposed source without implying
that an account is connected:

- source or channel label;
- configuration state;
- authority state;
- read scope;
- freshness;
- coverage window;
- partial, stale, blocked, or missing-data posture;
- last successful evidence ref where available;
- retention and privacy posture.

The MVP may use deterministic fixtures, reviewed manual imports, or a later
separately authorized read-only connector lane. A source card cannot present a
mock, fixture, proposal, or unavailable connector as live account data.

### 2. Performance overview

Social summarizes authorized cross-channel performance without hiding source
differences:

- total engagement;
- engagement rate;
- reach or impressions where the source provides them;
- audience growth;
- content and channel contribution;
- time-window comparison;
- cadence health;
- data freshness and completeness;
- source-linked explanations for normalized or unavailable metrics.

Cross-channel totals must distinguish comparable metrics from channel-specific
metrics. Missing source data is visible rather than silently treated as zero.

### 3. Performance analysis

The Performance tab helps an operator understand patterns:

- trend charts by channel, campaign, content pillar, and format;
- post-level comparison;
- breakout and underperforming content signals;
- conversion or profile-visit signals when an authorized source exposes them;
- retention drop-off or watch-time observations where available;
- time-of-day and publishing-frequency comparisons;
- repeatable angle and format hypotheses;
- explicit confidence, freshness, and evidence refs.

An observation is not a fact or an instruction. The UI must explain why a
signal was surfaced and what data is missing.

### 4. Daily social briefing

The Overview ranks a small, reviewable briefing instead of showing an endless
analytics dashboard. Candidate briefing items include:

- high-signal unanswered questions;
- repeated support or reputation risks;
- potential creator, customer, partner, or lead relationships;
- unusual performance changes;
- cadence gaps or over-posting risk;
- campaign drift;
- reusable content opportunities;
- stale sources or incomplete coverage;
- evidence gaps that make a conclusion unsafe.

Every item shows why it appears, the affected channel or app, freshness,
confidence or uncertainty, and source/evidence refs.

### 5. Audience intelligence

The Audience tab supports creator-focused learning without pretending to know
more than the connected sources provide:

- audience growth and loss trends;
- returning and newly engaged audience cohorts;
- topics, formats, and campaigns associated with engagement changes;
- high-relevance people and organizations linked to CRM candidates;
- repeated questions, objections, praise, and requests;
- geography, platform, or demographic summaries only when authorized and
  privacy-eligible;
- explicit unsupported, partial, and stale states.

Audience observations do not silently create CRM contacts, enrich people,
merge identities, or add reviewed Memory.

### 6. Campaign intelligence

Campaigns groups source-linked content, calendar slots, board work, Studio
assets, goals, and observed outcomes:

- campaign overview and time window;
- participating channels and content;
- stated goal and selected metrics;
- output cadence and coverage;
- performance summary;
- audience and conversation signals;
- linked Calendar, Work Board, Communications, CRM, Studio, and Evidence refs;
- lessons and follow-up candidates.

Social owns the campaign interpretation and projection. The owning app retains
canonical control of each linked event, task/card, thread, relationship, and
asset.

### 7. Cadence and publishing-rhythm intelligence

Social compares observed or reviewed planned output with an operator-defined
content rhythm:

- planned versus observed slots;
- gaps by channel, campaign, content pillar, or format;
- frequency and spacing warnings;
- upcoming linked Calendar events;
- linked production readiness from Work Board and Studio;
- explanation of why a slot or gap matters.

Calendar remains the only owner of schedule truth. Social cannot edit a time,
create an event, or represent an external schedule as committed unless the
Calendar record proves that state.

### 8. Conversation prioritization

Social identifies conversation signals; Communications owns the conversation
experience:

- unanswered questions;
- repeated questions or issue clusters;
- potential leads or collaborators;
- high-relevance creator relationships;
- support and reputation risks;
- praise, wins, and reusable testimonials with consent posture;
- linked originating content and campaign context.

Selecting a signal opens **Communications > Social Media** with the appropriate
filter, thread, relationship context, product-truth guidance, and safe refs.
The read-only MVP has no send, copy-to-send, queue, moderation, or reply action.

### 9. Search, filtering, and saved views

Social supports scoped search and filters over authorized metadata and indexed
local projections:

- channel or source;
- content, campaign, pillar, and format;
- person or CRM relationship ref;
- time window and freshness;
- signal kind and priority;
- review state;
- source coverage and confidence;
- linked owning app.

Search results show owner app, why shown, freshness, source posture, and
allowed next navigation. Search does not bypass workspace or field sensitivity.

### 10. Evidence, correction, and learning

Every durable Social observation must be correctable and source-linked:

- inspect supporting refs;
- see normalization or comparison method;
- mark a signal useful, irrelevant, stale, or incorrectly grouped;
- record a correction candidate;
- distinguish observed data, derived interpretation, reviewed conclusion, and
  planned hypothesis;
- offer reviewed Memory candidates only through the existing Memory review
  boundary.

Social metrics and model-generated interpretations never become authority by
appearing in a chart or briefing.

## Cross-App Integration Contract

| Surface | Canonical ownership | What Social contributes | What Social must not duplicate |
|---|---|---|---|
| Today | Cross-app projection | A bounded social briefing, urgent risks, cadence variance, and stale-source posture | A second Social dashboard or raw feed |
| Calendar | Events and schedule truth | Social publishing saved view, cadence context, performance evidence, and originating insight refs | Events, recurrence, external schedule state, or calendar writes |
| Work Board | Board membership, layout, ordering, and subject projections | Social Content saved view, originating signal, campaign, evidence, and schedule links | A second Kanban engine or copied task lifecycle |
| Communications | Source artifacts, threads, communication items, and drafts | Social Media tab, Needs attention filter, prioritization, campaign context, and response briefing | Threads, messages, drafts, replies, or send state |
| CRM | Relationships, organizations, roles, and opportunities | Engagement context and reviewed relationship candidates | Contacts, identity merges, enrichment, or relationship truth |
| Studio | Draft and media asset lifecycle | Performance context, campaign goal, format opportunity, and linked board/calendar refs | Media assets, versions, editing, or publishing state |
| Evidence and Trust | Proof, source, policy, authority, and receipt posture | Social signal provenance, freshness, normalization, corrections, and blocked-state explanation | Approval, authority, or execution receipts |
| Memory | Reviewed recall and provenance | Reviewed learning candidates and operator feedback refs | Automatic memory truth or context injection |

## Conceptual Data Nouns

These nouns are planning vocabulary, not implemented schemas:

- `SocialSourceRef`
- `SocialAccountProjection`
- `SocialContentRef`
- `SocialMetricSnapshot`
- `SocialPerformanceComparison`
- `SocialSignal`
- `SocialCadenceAssessment`
- `SocialAudienceObservation`
- `SocialCampaignProjection`
- `SocialBriefingItem`
- `SocialCorrectionCandidate`

External source artifacts and conversation items remain owned by
Inbox/Communications. Calendar events, board subjects, CRM relationships,
Studio assets, Evidence refs, and reviewed Memory remain owned by their
canonical applications. Before implementation, a later contract milestone must
map each Social noun to ADR-0054 ownership or explicitly accept an ADR update.

## What This Does For UAA

### For creators

- Replaces scattered analytics checks with one prioritized daily briefing.
- Connects performance learning to the actual production and publishing loop.
- Makes unanswered audience intent and relationship value harder to miss.
- Preserves the full path from signal to content work, schedule, conversation,
  result, and lesson.
- Keeps the product useful in observation mode before any publishing authority
  exists.

### For the UAA product

- Demonstrates why an integrated local-first command center is more useful than
  a collection of disconnected dashboards.
- Gives Calendar, Work Board, Communications, CRM, Studio, Evidence, and Memory
  a high-value shared workflow without weakening canonical ownership.
- Creates a creator-focused wedge that is broader than scheduling and more
  actionable than analytics alone.
- Makes governance visible in a familiar workflow: source scope, freshness,
  explanation, review, correction, and blocked external action.
- Produces a strong README feature story while product language remains honest
  about planned versus implemented behavior.

## Explicit Read-Only MVP Non-Goals

The first Social milestone must not include:

- account OAuth or credential collection without a separate connector lane;
- live social API fetching without accepted exact read authority;
- browser scraping or browser automation;
- background polling, webhooks, or recurring sync;
- post creation, publishing, scheduling writes, rescheduling, or deletion;
- replies, direct messages, reactions, follows, moderation, or queueing;
- automatic contact creation, identity merge, enrichment, or CRM writes;
- automatic task, event, board, Studio, Evidence, or Memory writes;
- provider/model calls or generated production copy;
- raw social content in durable evidence, logs, tests, docs, or support exports;
- claims of complete channel coverage, production readiness, or public release.

## Authority Sequence

Each stage requires its own accepted milestone, contracts, tests, safe-disable
posture, redaction, and product-truth update.

1. **Accepted product contract and deterministic concept** — this document.
2. **Fixture/manual-import read model** — local, redacted, CLI/API parity, no
   external account access.
3. **Exact selected-source metadata reads** — separately authorized source and
   field scope, freshness, retention, revocation, and receipts.
4. **Exact bounded content and metric reads** — separately authorized content
   scope with untrusted-content handling and cursor/conflict posture.
5. **Cross-app local proposals** — reviewable Calendar, Work Board,
   Communications, CRM, or Studio proposals; no external action.
6. **Exact external writes** — future-only, one resource/action kind at a time,
   never granted by this contract.
7. **Bounded recurring workflows** — future-only after separate background,
   standing-approval, revocation, rate, cost, and kill-switch evidence.

Graduating one channel or action kind does not grant another. A read permission
does not grant a write. A publishing approval does not grant reply, delete,
moderation, account, or recurring authority.

## Future Work Recommendation Gate

Recommendation state: **deferred**.

When the operator asks UAA "what's next?", UAA must not recommend Social Media
Intelligence until Work Board, CRM, and Communications pass
`contract-ref:social-read-only-foundation-profile:v1`. This profile proves
only the backend-owned read interfaces, API/CLI parity, tested Control Center
projections, visual evidence, and truthful source/freshness states required by
the first read-only Social milestone. It does not establish standalone product
completion, production readiness, external connector authority, sending
authority, or general mutation authority. A planning document, concept render,
fixture-only view, isolated route, or partial UI does not pass the profile.

The current profile is documented in
`docs/product/UAA_SOCIAL_READ_ONLY_FOUNDATION_PROFILE.md` and remains partial.

Once the profile passes, Social Media Intelligence becomes an **eligible next
candidate**, not an automatic priority. UAA must still reconcile the active
roadmap, current board, operator pain, and any higher-priority safety or product
work. The stored execution prompt is
`docs/prompts/implement_social_media_intelligence_after_foundation_gates.prompt.md`;
the accepted visual target is
`docs/design/control_center_north_star/renders/social-media-v1/README.md`.

## MVP Acceptance Criteria

The initial implementation milestone is not complete until it proves:

- Social route and navigation truth are backend-owned and classified;
- Overview, Performance, Audience, Campaigns, and Sources have readable empty,
  fixture, stale, partial, blocked, and success states;
- every displayed metric identifies its source, window, freshness, and missing
  coverage;
- every briefing item exposes why shown and evidence refs;
- Calendar, Work Board, and Communications open typed projections rather than
  duplicate records;
- Communications uses **Social Media** as the tab and **Needs attention** as a
  filter;
- all external social actions are absent or visibly blocked;
- no raw private content enters durable evidence or fixtures;
- CLI inspection and API read contracts expose the same redacted posture;
- OpenAPI, route classification, product-language, accessibility, frontend,
  focused unit, and visual regression checks pass;
- docs describe the feature as planned or partial until those proofs exist.

## README-Ready Copy

The following copy is approved for a future README update only when it is
introduced with an explicit status label.

### Short feature row

> **Social Media Intelligence — Planned:** A creator-focused command view for
> cross-channel performance, audience signals, campaigns, publishing cadence,
> and high-value conversations. Social explains what changed and routes context
> into UAA Calendar, Work Board, Communications, CRM, Studio, and Evidence;
> publishing and replies remain blocked until separately authorized.

### Product narrative

> UAA Social Media Intelligence turns scattered social metrics into a governed
> creator operating loop. It highlights performance changes, audience intent,
> cadence gaps, campaign lessons, and conversations that deserve attention,
> then opens the canonical UAA app where the work belongs. Calendar owns the
> schedule, Work Board owns production, Communications owns the thread, CRM
> owns the relationship, Studio owns the asset, and Evidence preserves why the
> insight was shown. The first milestone is read-only and does not publish,
> reply, or change external accounts.

## Locked Decisions

- The primary global destination is **Social**.
- The descriptive product name is **Social Media Intelligence**.
- The Social tabs are Overview, Performance, Audience, Campaigns, and Sources.
- Communications uses **Social Media**, not Social Attention, as its tab label.
- Communications uses **Needs attention** as the active priority filter.
- Calendar and Work Board integration occurs through saved views and typed
  projections.
- The MVP is read-only.
- Social is an intelligence layer, not a replacement for existing UAA apps.
- Later connector reads, proposals, writes, and recurring workflows require
  separate authority milestones.
