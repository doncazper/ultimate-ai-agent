# News & Signals V1 North-Star Render

Status: accepted visual direction; planning-only target
Accepted: 2026-07-13
Repository baseline: v0.104.0 / 0.104.0
Route: `/news`
Global navigation label: **News & Signals**

`01-news-signals-home.png` is the accepted desktop front-page direction for
UAA News & Signals. It is a generated design target, not a screenshot of the
implemented Control Center and not evidence of live source ingestion.

Artifact metadata:

- dimensions: `1576 x 998`;
- SHA-256:
  `961bc6ff66055796ec9495d85e8fc66da44a3054951d0615a11e30f19052d85a`;
- built-in image-generation workflow;
- visual references: accepted UAA Today, Work Board, CRM, Communications, and
  Social north-star surfaces;
- the earlier `renders/target-v2/15-news-v1.png` remains preserved as a
  superseded exploration.

## Locked Front-Page Hierarchy

The accepted hierarchy answers four operator questions in order:

1. **What kind of news is this?** Familiar category navigation groups Top, AI,
   Technology, Business, Politics, World, Sports, Science, and Culture.
2. **What matters now?** `Top stories for you` provides a personalized lead
   story plus category-labeled secondary headlines with source and freshness.
3. **What will UAA carry forward?** `Morning Brief queue` shows a bounded
   selection, pagination across the review pool, and a visible path to the full
   Morning Briefing.
4. **What did my chosen sources find?** Separate Reddit Scanner, X Watchlist,
   and Newsletter Bulletin cards preserve source-specific context instead of
   hiding it inside an abstract cluster.

The `Also monitoring` strip makes Discord, RSS, official blogs, YouTube,
podcasts, and later exact adapters visible as source families without turning
the home page into a configuration screen.

## Locked Interaction Intent

- `For You` is the default front page.
- `Categories` opens category-first browsing.
- `Source Feeds` opens source-specific scanner and subscription views.
- `Saved` and `Sources` remain distinct: saved items are operator review state;
  sources are readiness, permissions, retention, and coverage posture.
- Category controls filter or navigate; they do not mutate durable work.
- Story rows open bounded sourced detail.
- Morning Brief pagination browses the candidate pool; `Open full Morning
  Briefing` opens the canonical briefing surface.
- Scanner and subscription cards keep source identity, source-local label,
  freshness, and a `View all` path.
- The persistent UAA composer may compare coverage, explain a signal, or open a
  safe source ref. It may not treat fetched content as instructions.

## Authority And Truth Boundary

Every visible story, count, source, timestamp, score, and status in the render
is illustrative. The render grants no Reddit, X, email, Discord, RSS, official
blog, YouTube, podcast, search, browser, connector, or background polling
authority.

The current `/news` implementation remains a sample-record-only preview and
does not yet implement this full composition. Any real source adapter must be
separately accepted, exact-scoped, read-only, policy-checked, audited,
safe-disableable, retention-bounded, and routed through the approved gateway or
connector boundary. One source adapter never grants authority for another.

The page must continue to distinguish primary reporting, community evidence,
public commentary, and newsletter summaries. Ranking is inspectable context,
not truth. News & Signals is not completable work and cannot mint action,
connector, provider, browser, or execution authority.

## Implementation Notes

- Preserve the accepted UAA shell and spacing grammar.
- Keep categories and source feeds as separate organizing dimensions.
- Do not reintroduce an abstract signal radar or duplicate topic-analysis
  panels on the front page.
- Avoid a generic endless feed. Internal panes may paginate or scroll while the
  reference desktop composition remains contained.
- Morning Briefing consumes a bounded ranked projection rather than duplicating
  the full News & Signals pool.
- Social continues to own owned-channel performance, audience, campaign, and
  publishing-rhythm interpretation. News & Signals owns outside context and
  watched public-source intake.
