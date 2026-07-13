# ECO-000 Initial Quality Budgets

Status: accepted targets, not measured claims. A target becomes evidence only
after the named method runs on a recorded machine/profile and synthetic tier.

## Synthetic dataset tiers

| Tier | Calendar | Tasks | Boards | CRM | Inbox/Organizer | Purpose |
|---|---:|---:|---:|---:|---:|---|
| Small | 2 calendars, 500 occurrences | 1,000 tasks | 5 boards, 250 cards | 1,000 people, 100 opportunities | 1,000 artifacts, 500 list items | Normal private use and browser interaction |
| Medium | 10 calendars, 10,000 occurrences | 25,000 tasks | 25 boards, 5,000 cards | 25,000 people, 2,500 opportunities | 25,000 artifacts, 10,000 list items | Release performance gate |
| Large | 50 calendars, 100,000 occurrences | 150,000 tasks | 100 boards, 25,000 cards | 150,000 people, 20,000 opportunities | 150,000 artifacts, 50,000 list items | Stress, degradation, and recovery truth |

All datasets are deterministic and synthetic. They contain no real contact,
message, calendar, path, account, credential, prompt, response, or transcript.

## Performance and reliability targets

| Area | Initial target | Verification method |
|---|---|---|
| Local cold startup | p95 <= 2.5 s to readable shell at small; <= 4.0 s at medium | Five clean launches; monotonic timer; median and p95 reported |
| Warm route interaction | p95 <= 150 ms read-model response; <= 250 ms visible navigation | Browser performance marks plus backend timing, 30 samples |
| Search | p95 <= 200 ms small, 500 ms medium, 1.5 s large; bounded results | Deterministic query suite with workspace/privacy isolation assertions |
| Calendar layout | p95 <= 100 ms week, 250 ms month at medium | Layout benchmark across DST, locale, all-day, overlap fixtures |
| Recurrence expansion | 10,000 bounded occurrences <= 500 ms and <= 2x result memory | Pure expansion benchmark with DST/exception matrix |
| Large task list | First useful render <= 500 ms medium; filter p95 <= 150 ms | Virtualized-list browser trace and keyboard traversal |
| Board render/drag | 60 fps target; input-to-preview p95 <= 100 ms; commit UI <= 250 ms | Browser trace with dense-board tier and keyboard alternative |
| CRM People/pipeline | First useful render <= 600 ms medium; filter p95 <= 200 ms | Browser trace plus backend query plan snapshot |
| ChangeSet preview | 64-operation DAG validate and diff p95 <= 250 ms | Pure validator benchmark; conflict/partial variants |
| Migration | Small <= 30 s, medium <= 5 min; large measured before claim | Preview and commit on copies; counts/fingerprints/replay verified |
| Backup/restore | Medium backup <= 3 min, restore preview <= 5 min | Encrypted backup drill with integrity and interruption cases |
| Memory | Shell <= 350 MiB steady small, <= 650 MiB medium; no >10% growth over 30 min idle | Process RSS samples; route and dense-view soak |
| Offline | All local/manual CRUD remains available; connector states degrade without blocking local apps | Network-disabled browser/core scenario and recovery test |
| Conflict/recovery | 100% stale writes conflict; zero duplicate commits; deterministic restart truth | Concurrent submission, crash boundary, replay, corrupt-state tests |

## Accessibility targets

- WCAG 2.2 AA automated violations: zero at milestone gate.
- Complete primary workflow by keyboard with visible focus and no trap.
- Screen-reader names, roles, states, errors, progress, and partial outcomes.
- 200% zoom and 320 CSS-pixel reflow without loss of risk/privacy controls.
- Reduced-motion mode removes nonessential motion and preserves state change.
- Text contrast >= 4.5:1; large/control contrast >= 3:1.
- Drag interactions have equivalent keyboard move/reorder commands and live
  announcements.

Methods: axe scan, Playwright keyboard scripts, macOS VoiceOver review,
contrast tooling, zoom/reflow screenshots, and manual acceptance ledger.

## Visual fidelity targets

- Zero unreviewed overlap, clipping, unreadable truncation, hidden focus, or
  missing authority/privacy indicator in accepted viewports.
- Pixel-diff threshold <= 0.5% for stable chrome and <= 2% for approved dynamic
  content masks; all changes reviewed, never auto-accepted.
- Desktop 1440x960, compact 1100x800, narrow 390x844, and wallboard 1920x1080
  reference viewports.
- Every render has surface/state, dataset, viewport, product-status, and review
  refs in the manifest.

## Gate discipline

Targets above are not product claims. ECO-001 must establish repeatable storage,
migration, backup, privacy, and recovery measurements. Each app milestone adds
its real results and investigates a >15% regression against comparable warm or
cold medians.
