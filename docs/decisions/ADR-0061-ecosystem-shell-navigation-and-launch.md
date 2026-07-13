# ADR-0061: Ecosystem Shell, Navigation, Deep Links, And Launch Direction

Status: Planned information architecture accepted; no routes or packaging are
implemented by ECO-000.

## Decision

Control Center remains the first product container and Python Agent Core
remains truth. Planned primary destinations are Today, Inbox, Calendar, Tasks,
Boards, Plans, CRM, Action Inbox, Memory, Evidence, and Settings. Trust and
runtime inspection remain visible through Settings/inspectors without losing
their current accepted deep links during migration.

Each primary app must support a direct deep link, app-local navigation, search,
quick capture, settings, import/export posture, and standalone local/manual
workflow. Global search and command return owner app, workspace, why shown,
provenance, privacy, and allowed proposal actions. Commands create drafts or
proposals; they do not bypass the owning app.

Narrow navigation prioritizes Today, agenda, capture, tasks, and people while
preserving risk. Wallboard navigation is view-only and privacy-filtered.
Separate binaries, signing, notarization, app-store distribution, mobile apps,
and collaboration are later decisions.

## Rejected

React-owned domain truth, fake routes, route renaming without compatibility,
and hiding authority or privacy state in secondary developer panels were
rejected.
