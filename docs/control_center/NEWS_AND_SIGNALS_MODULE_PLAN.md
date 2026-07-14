# News & Signals Module Plan

Status: accepted front-page design target; implemented sample UI remains partial
Baseline: v0.104.0 / 0.104.0
Reviewed: 2026-07-13

This plan refines the existing News destination into **News & Signals**. It
records product ownership and the intended operator experience. The current
`/news` Control Center surface is an illustrative, sample-record-only preview.
It does not add a backend route, source ingestion, account access, storage,
background polling, model summarization, connector runtime, browser automation,
external action, public release, or production authority.

## Executive Decision

News & Signals is designed as UAA's external situational-intelligence
workspace. A later backend-owned milestone may gather authorized outside
context, preserve source and confidence posture, rank it against explicit user
interests, and identify the few items worth carrying into Morning Briefing.

The target product loop is:

```text
Authorized sources -> source-specific feeds -> normalize + preserve provenance
                                                    |
                                                    v
                          categories + preferences -> ranked front page
                                                    |
                                review pool --------+-> Morning Brief candidate
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

Morning Briefing will consume only the highest-ranked, reviewable News &
Signals items after a backend-owned projection is separately accepted. It will
not duplicate the entire stream.

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

## Refinement Pass 3: Analytical Intelligence Desk

The third pass explored an editorial lead signal, topic radar, story clusters,
and a Morning Brief queue. It improved hierarchy but over-indexed on analytical
abstractions. `Signal radar`, `What changed today`, and `Topics worth opening`
overlapped and required the operator to interpret UAA's model before reading
the news.

That composition is not the accepted front-page target.

## Refinement Pass 4: Personalized News Front Page

The accepted direction starts with familiar news-consumption questions:

1. What happened in the categories I care about?
2. Which stories matter to me now?
3. What did each source scanner or subscription find?
4. Which items are entering Morning Briefing?

The accepted visual target is:

`docs/design/control_center_north_star/renders/news-signals-v1/01-news-signals-home.png`

Its detailed truth and interaction contract is recorded in:

`docs/design/control_center_north_star/renders/news-signals-v1/README.md`

## Current Preview And Accepted Target

### Implemented sample preview

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

### Accepted target composition

The later implemented front page should provide:

- primary tabs for `For You`, `Categories`, `Source Feeds`, `Saved`, and
  `Sources`;
- familiar category grouping for Top, AI, Technology, Business, Politics,
  World, Sports, Science, Culture, and user-configurable additions;
- `Top stories for you` with visible category, source, freshness, source count,
  and an inspectable reason the item was selected;
- a bounded `Morning Brief queue` with candidate-pool pagination and a stable
  path to the full Morning Briefing;
- separate source-specific previews for Reddit findings, watched X accounts,
  email newsletter bulletins, and later Discord, RSS, official blog, YouTube,
  podcast, and other exact read-only adapters;
- source-specific `View all` paths so curated intake does not erase where an
  item came from;
- a calm contained desktop composition rather than an endless feed or
  analytics dashboard.

The listed source families are an extensible product taxonomy, not a claim
that every source is implemented or permitted. Readiness and authority must be
shown per exact adapter.

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
