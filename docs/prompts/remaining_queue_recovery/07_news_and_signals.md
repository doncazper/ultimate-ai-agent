# News And Signals Recovery Contract

Status: triage-ready recovery source. The current route is fixture-only and
does not fetch or summarize live sources.

## Outcome

Replace the illustrative News and Signals preview with a backend-owned,
provenance-first read model and separately graduated read-only source lanes.

## In Scope

- Safe-ref article, signal, source, freshness, confidence, and provenance
  contracts.
- CLI/API inspection and projections into Today and Morning Briefing.
- Explicit source readiness, stale, blocked, conflicting, and unknown states.

## Out Of Scope

- Unrestricted browsing, authenticated sources, automatic recommendations,
  hidden context injection, writes, or action execution.

## Acceptance

- No visible item is presented as live without source and freshness proof.
- External content is always treated as untrusted evidence.
- Backend, gateway-policy, CLI, API, frontend, redaction, and visual tests pass
  for each accepted read-only source lane.
