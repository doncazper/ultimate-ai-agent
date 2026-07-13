# News & Signals V1 Desktop Implementation Evidence

Status: implemented fixture-only desktop preview; not live source evidence
Captured: 2026-07-13
Repository baseline: v0.104.0 / 0.104.0
Route: `/news`
Global navigation label: **News & Signals**

This set records the implemented `/news` fixture preview at normal, compact,
narrow-desktop, and filtered states. The screenshots are implementation
evidence, not evidence of source ingestion, provider readiness, ranking,
background polling, or production authority. The broader future composition in
`CONTROL_CENTER_UI_UX_SPEC.md` remains a design target rather than implemented
runtime truth.

Artifact metadata:

- render `NEWS-01`, `01-news-signals-home.png`: default fixture preview,
  `1576 x 998`, SHA-256
  `d522b722da09de2a6beaf83cf670ce8fb30f5438f7f8f4607256962a88a231df`;
- render `NEWS-02`, `02-news-signals-compact.png`: compact desktop fixture
  preview, `1280 x 820`, SHA-256
  `e86b13478913420c684fb83a97ef1016641c06216b527ffa2aeab74f1446e36f`;
- render `NEWS-03`, `03-news-signals-narrow-desktop.png`: narrow desktop
  fixture preview, `1024 x 768`, SHA-256
  `eff955a3fdd62997ea19f328bf639ae6bcf614e934a2bbfda6d0d70bfa420d59`;
- render `NEWS-04`, `04-news-signals-community-filter.png`: Community filter
  selected, `1576 x 998`, SHA-256
  `3c631cb500208bd6749e0098955869a4a3f8fce39e778a1020fa1eb592ba653d`;
- capture posture: local Vite fixture route, 100% zoom, animations unchanged,
  sanitized static records, backend ownership unverified, no credentials;
- approval state: reviewed implementation evidence, not an accepted live-data
  or production-readiness claim;
- the earlier `renders/target-v2/15-news-v1.png` remains preserved as a
  superseded exploration.

## Implemented Preview Hierarchy

The current preview answers four operator questions in order:

1. **What is this surface?** The heading and permanent notice label it an
   illustrative sample-only preview.
2. **What is available?** Bounded fixture counts summarize the visible sample
   pool without claiming backend ownership.
3. **What should I inspect?** A ranked review list exposes safe summaries,
   source labels, freshness-shaped fixture values, and review posture.
4. **Why is an item present?** The selected-signal inspector shows rationale,
   coverage labels, and a safe preview ref while mutation controls stay absent.

## Implemented Interaction Intent

- `For you` is the default fixture view.
- `Brief candidates`, `Official sources`, and `Community` filter local
  presentation state only.
- Story rows select one bounded fixture record for inspection.
- `Open Morning Briefing` navigates to the existing briefing surface; it does
  not persist, rank, or promote any story.
- Save, dismiss, mute, action-proposal, source-management, and live retrieval
  controls remain absent until backend-owned contracts exist.

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
- In a later backend-owned composition, keep categories and source feeds as
  separate organizing dimensions.
- Do not reintroduce an abstract signal radar or duplicate topic-analysis
  panels on the front page.
- Avoid a generic endless feed. Internal panes may paginate or scroll while the
  reference desktop composition remains contained.
- Morning Briefing may consume a bounded backend-owned projection only after
  that projection is separately implemented and accepted.
- Social continues to own owned-channel performance, audience, campaign, and
  publishing-rhythm interpretation. A later News & Signals read model may own
  outside context and watched public-source intake after exact adapters exist.
