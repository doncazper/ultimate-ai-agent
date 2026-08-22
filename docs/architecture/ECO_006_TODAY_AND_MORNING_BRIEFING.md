# ECO-006 Today And Morning Briefing Projection

Status: accepted bounded projection core on 2026-08-21. This is not a product
surface cutover, source connector, notification service, public release, or
production authority.

## Accepted behavior

ECO-006 adds one deterministic backend projection over already-authoritative
source results. Today remains an ecosystem home, not another database. It does
not copy source records, refresh a source, rank work, execute a proposal, or
mutate canonical truth.

The projection accepts an exact workspace, aware `as_of` timestamp, and IANA
time zone together with bounded canonical result objects from Tasks, Calendar,
and first-class private CRM. Typed supplemental inputs may represent a current
Plan milestone, reviewed Inbox source proposal, explicit blocker, or recent
receipt. Each projected item preserves:

- the canonical owner application and canonical record ref;
- the exact source-result refs that produced it;
- safe why-shown refs, evidence or receipt posture, and freshness;
- due or scheduled time when applicable; and
- the complete visible ordering factors used by the projection.

No raw task title, event title, CRM follow-up title, relationship detail,
provider payload, prompt, response, or log is copied into the output.

## Visible ordering, freshness, and evidence

The accepted ordering contract is
`contract-ref:eco-006-visible-ordering:v1`: lane ordinal, urgency ordinal,
optional scheduled/due time, then canonical ref. These factors are present on
every item. There is no score, personalization model, hidden ranking, or
fixture-owned primary truth.

Each source status is bound to the requested workspace and distinguishes
`current`, `stale`, `missing`, and `blocked`. Current status requires an exact
source result ref. Task results within five minutes of the projection request
are current; older or farther-future snapshots are stale. The accepted CRM read
model has no capture timestamp, so CRM source statuses and items conservatively
report stale rather than claiming current freshness. Non-current task-backed
Calendar projections are omitted from daily commitments. Items separately
expose `present`, `missing`, or `not_applicable` evidence posture. Result refs
bind the request, ordered item refs, source-status refs, and carry-forward
proposal refs, so a source result or freshness change changes the projection
proof.

## Privacy and canonical ownership

Tasks owns Task truth, Calendar owns occurrence truth, CRM owns follow-up
metadata, Plans owns milestones, Inbox owns source proposals, and Governance
owns blocker and recent-receipt summaries. A supplemental candidate with the
wrong owner is rejected. Duplicate owner/ref items or sources fail closed.

CRM inclusion is evaluated independently for Today and Morning Briefing. A CRM
workspace excluded from both surfaces leaves no item, source status, proposal,
or result-ref trace. Private Relationships keeps its ECO-005 fail-closed
defaults. A source or candidate from another ECO-001 workspace is rejected.

## Carry-forward posture

Open Tasks and permitted CRM follow-ups overdue before the local day produce a
deterministic carry-forward proposal. The proposal records the canonical owner,
record ref, original due time, proposed local date, and why-proposed ref. It
always reports `mutation_authorized=false` and
`background_work_started=false`. Today and Briefing proposals are composed
separately as inspectable bounded objects so surface-specific CRM privacy cannot
leak through proposal details or refs.

## Compatibility and deferred work

Existing Founder Loop Today and Morning Briefing routes/read models remain the
current compatibility product surfaces. ECO-006 does not replace, migrate, or
cut them over, and it adds no API route, CLI command, or Control Center UI.

Deferred behind separately accepted lanes: route/CLI/UI integration, time-block
or daily-plan mutation, source refresh, notifications, scheduling, connector or
account reads/writes, external data movement, provider/model calls, browser or
web execution, background autonomy, production key/path backends, public
distribution, and production authority.

## Verification

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_eco_006_today.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_eco_006_today.py tests/test_eco_006_verifier.py
```

The focused proof covers deterministic ordering, canonical ownership, source
freshness and missing-source visibility, exact result binding, proposal-only
carry-forward, surface-specific CRM privacy, no-trace Private Relationships,
workspace isolation, raw-content exclusion, duplicate rejection, and static
denial of network or subprocess runtime.
