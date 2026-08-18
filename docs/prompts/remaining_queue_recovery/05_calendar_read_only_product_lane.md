# Calendar Read-Only Product Lane Recovery Contract

Status: triage-ready recovery source. The existing metadata envelope is
contract-only; this recovery lane does not itself authorize account access.

## Outcome

Turn the existing safe calendar metadata contract into an honest UAA product
lane through a backend-owned read model, CLI/API parity, and a separately
reviewed test-account adapter admission path.

## In Scope

- Calendar source-readiness, safe metadata projection, provenance, and stale
  state behavior.
- Exact AuthorityLease and test-account prerequisites for a later read-only
  adapter.
- Today, Briefing, Action Inbox, and Calendar projection contracts.

## Out Of Scope

- Production account authentication, raw event bodies, calendar writes,
  invitations, background polling, downloads, or standing access.

## Acceptance

- Product surfaces never imply live data before the exact adapter gate passes.
- Read models and receipts contain safe refs only and expose missing/stale
  source truth.
- Any networked test-account adapter is a separate reviewed authority lane.
