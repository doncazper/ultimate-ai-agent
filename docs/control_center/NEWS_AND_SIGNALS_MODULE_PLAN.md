# News & Signals Module Plan

Status: refined design preview; planning-only beyond the local sample UI
Baseline: v0.104.0 / 0.104.0
Reviewed: 2026-07-13

This plan refines the existing News destination into **News & Signals**. It
records product ownership and the intended operator experience. The current
`/news` Control Center surface is an illustrative, sample-record-only preview.
It does not add a backend route, source ingestion, account access, storage,
background polling, model summarization, connector runtime, browser automation,
external action, public release, or production authority.

## Executive Decision

News & Signals is UAA's external situational-intelligence workspace. It gathers
authorized outside context, preserves source and confidence posture, ranks it
against explicit user interests, and identifies the few items worth carrying
into Morning Briefing.

The product loop is:

```text
Authorized sources -> normalize -> cluster -> rank -> review
                                               |        |
                                               |        +-> retain as context
                                               +-> Morning Briefing candidate
```

The global navigation label becomes **News & Signals** while the canonical
route remains `/news`. The rename broadens the existing News concept without
creating another attention queue or claiming live monitoring.

## Ownership Boundary

News & Signals owns:

- external articles, announcements, public discussions, and source updates;
- cross-source clustering and provenance;
- preference-based relevance and freshness;
- distinction between primary reporting, community evidence, and commentary;
- Morning Briefing candidacy.

It does not own:

- owned-channel performance, audience analysis, campaign interpretation, or
  social publishing rhythm; those remain with **Social** under
  `docs/product/UAA_SOCIAL_MEDIA_INTELLIGENCE_PRODUCT_CONTRACT.md`;
- messages or conversations; Communications owns those;
- tasks or approvals; Work Board and Action Inbox own those;
- durable truth or authority; Evidence, Trust, policy, and approval boundaries
  remain canonical.

Morning Briefing consumes only the highest-ranked, reviewable News & Signals
items. It does not duplicate the entire stream.

## Refinement Pass 1: Complete Review Workspace

The first pass proposed three persistent regions:

1. a source-and-interest filter rail;
2. a compact ranked story stream;
3. a selected-signal inspector with quick take, relevance, and coverage.

This established the right information hierarchy but added a second left rail
beside UAA's global navigation. On a realistic macOS window it reduced reading
width and made source controls feel more important than the intelligence.

## Refinement Pass 2: Calm Triage Surface

The second pass removed the persistent local rail and promoted only the
essential controls:

- a compact horizontal filter strip;
- one scrollable ranked stream;
- one scrollable detail inspector;
- a visible sample-only authority notice;
- a direct read-only handoff to Morning Briefing.

Save, dismiss, mute, and action-proposal controls were deliberately removed
from the preview. Those controls would imply backend-owned state changes and
receipt behavior that this milestone does not implement.

## Final Preview Contract

The sample `/news` surface demonstrates:

- `For you`, `Brief candidates`, `Official sources`, and `Community` filters;
- source type, freshness, topic, relevance, and coverage count on every row;
- an explicit Morning Briefing candidate label;
- selected-signal quick take, why-it-matters, selection reasons, coverage, and
  a safe preview ref;
- sample data that spans an official update, a followed Discord announcement,
  a curated community discussion, an RSS cluster, and monitored public
  commentary;
- honest disclosure that no live source or summarization capability is active.

Only filter and selection state are held in React. They are presentation state,
not product authority or durable workflow state.

## Future Contract Sequence

Any implementation after this preview must be separately accepted and should
progress in this order:

1. Define a backend-owned `SignalRecord`, source-readiness, provenance,
   clustering, preference, ranking, and Morning Briefing candidate contract.
2. Add deterministic fixture and CLI inspection paths with redacted safe refs.
3. Add read-only local storage and API/OpenAPI/manifest contracts with focused
   tests and route-side-effect classification.
4. Graduate exact source adapters one at a time through `WebAccessGateway`,
   policy, audit, terms/permission review, safe-disable posture, and bounded
   retention. An adapter for one source grants no authority for another.
5. Add backend-owned review decisions only with idempotency, receipts, CLI/API
   parity, and rollback or safe-disable behavior.
6. Bind selected candidates into Morning Briefing through an explicit read-only
   projection before considering action proposals.

Direct scraping, provider SDK calls, authenticated browsing, cookies, browser
automation, unrestricted fetching, and connector writes remain blocked by the
current repository baseline. Planning source coverage does not grant runtime
authority.

## Acceptance Criteria For A Later Implemented Milestone

- The UI never presents sample, stale, partial, community, or commentary data
  as primary-source truth.
- Every item has bounded provenance, freshness, confidence, and authority state.
- Personalization is inspectable and can explain why an item was shown.
- Morning Briefing receives a bounded ranked subset, not an unreviewed firehose.
- Social and News & Signals do not duplicate ownership.
- No UI control mints authority or stores operator-relevant workflow state only
  in React.
- Focused core, CLI, API/OpenAPI/manifest, frontend, redaction, and Foundation
  Gate verification passes for the exact implemented scope.
