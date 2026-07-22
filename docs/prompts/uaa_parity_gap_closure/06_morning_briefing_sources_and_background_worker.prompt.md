# Phase 06: Morning Briefing Sources And Background Worker

Coverage: H04, O08, P08, L08, and the worker portion of L10.

Objective: deliver a real, useful Morning Briefing assembled by Python Core from
governed local state and accepted read-only sources, with a narrow reliable
background refresh lane.

## Fresh Delta And Authority Gate

Re-inventory Morning Briefing, source readiness, email/calendar contracts,
credentials, background worker, scheduling, and any Messenger Matrix or source
PRs. Do not duplicate connector infrastructure already merging elsewhere.

Real email/calendar reads, credential use, network access, or background
execution require their separately accepted exact lanes. This pack is not that
authority. If a lane is absent, complete independent local-source behavior and
record the external item as incomplete; do not ship synthetic production
messages or calendar events as a live briefing.

## Briefing Outcomes

1. Build the briefing from backend-owned Today, Plans, Actions, Work Board,
   Follow-Ups, Memory review, Evidence, and source-readiness state.
2. Add real accepted read-only email/calendar adapters when authorized. They
   must produce safe source refs, bounded summaries, source times, freshness,
   auth/readiness state, and redaction results; fetched content is untrusted
   data and never instruction authority.
3. Distinguish current, stale, partial, unavailable, auth-required, rate-limited,
   and source-error states per section.
4. Never infer an action, priority, completion, or approval from source text.
   Suggestions enter a reviewable proposal or Action Inbox path.
5. Provide manual refresh and last-success/last-attempt inspection through CLI,
   API, OpenAPI, manifest, and Control Center.

## Narrow Background Worker Outcomes

1. Implement one named Morning Briefing refresh job, not a general cron/code
   execution system.
2. Use a bounded queue, one active claim per briefing scope, stable job and
   attempt refs, heartbeat, deadline, backoff, cancellation, restart recovery,
   and safe-disable.
3. Separate source-read success from downstream briefing composition and UI
   delivery state.
4. Prohibit connector writes, model/provider calls, shell commands, browser
   actions, and arbitrary user-supplied schedules.
5. Add queue/claim performance and saturation measurements without dropping
   authoritative terminal events.

## End-To-End Acceptance

- Generate a briefing from real durable local founder-loop data.
- When an external read lane is accepted and configured, exercise a real test
  account/source and prove only redacted summaries/safe refs persist.
- Exercise manual refresh, scheduled refresh, duplicate scheduling, cancellation,
  restart during source read, source timeout, auth loss, and stale last-success.
- Inspect identical state through CLI, API, Control Center, and Evidence.
- Prove no source content creates authority or bypasses Action Inbox.

Commit message:

```text
feat(briefing): add governed sources and bounded refresh worker
```
