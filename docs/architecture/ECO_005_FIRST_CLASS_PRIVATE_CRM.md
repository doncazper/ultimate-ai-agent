# ECO-005 First-Class Private CRM Foundation

Status: accepted bounded core scope on 2026-08-21. This is not product cutover,
external CRM sync, public release, or production authority.

## Accepted behavior

ECO-005 adds a versioned encrypted `PrivateCrmPortfolio` on the ECO-001 local
data platform. One portfolio shares private Person and Organization identity
truth across multiple strictly scoped CRM workspaces while workspace contexts
hold role, notes, tags, important dates, relationships, activities, follow-ups,
and pipeline participation.

The five accepted workspace presets are Personal Network, Private
Relationships, Sales, Real Estate, and Professional Network. Private
Relationships is fail-closed: it cannot participate in global search, Today,
Morning Briefing, Memory, or general export. The current repository blind index
contains only the constant portfolio entity term; it never indexes names,
contact values, notes, activity summaries, or other private content.

CRM mutation uses the exact repository-only `ecosystem.crm.apply` action with
approval scope, request-context binding, optimistic version checks, encrypted
idempotent receipts, a one-megabyte payload cap, and protected bounded undo.
Private values stay inside the encrypted payload; safe summaries expose refs,
versions, counts, and lifecycle state only.

## Canonical ownership

CRM owns:

- Person, Organization, ContactPoint, WorkspaceContext, and Relationship truth;
- CRM activity and follow-up metadata;
- pipeline identity and opportunity-specific metadata such as amount and target
  date; and
- ref-only links to canonical Tasks and Calendar events.

Reusable Boards owns:

- pipeline lanes/stages;
- card placement and ordering;
- WIP constraints; and
- the display title/description of the standalone pipeline card.

A CRM pipeline stores one Board ref. A pipeline object stores one exact Board
card ref, and that active card must be a standalone Board item whose subject ref
equals the pipeline-object ref. CRM stores no stage, lane, or ordering field.
The CRM workspace read model resolves current placement from Boards and binds
its result ref to current Board versions. Moving a Board card therefore changes
the projected pipeline stage without a CRM write or a second Kanban engine.

Tasks remains canonical for task truth and Calendar remains canonical for event
truth. CRM stores only optional refs; this slice deliberately does not copy or
mutate those records.

## Compatibility and deferred work

The existing CRM M0/M1 contracts and CRM Local Command Center M2 remain
compatibility/read-only surfaces. ECO-005 does not silently migrate or cut over
their JSONL records. A later accepted lane must provide bounded migration,
route/CLI parity, approval-preview UX, Control Center People and pipeline
surfaces, Today/Briefing projections respecting privacy policy, typed private
import/export, recovery evidence, accessibility proof, and production key/path
backends.

Also deferred and blocked: external CRM/account/contact sync; connector reads
or writes; email/message sends; calendar writes; provider/model calls; scoring
or outreach in Private Relationships; live web/browser behavior; background
workers; public distribution; and production authority.

## Verification

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_eco_005_private_crm.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_eco_005_private_crm.py tests/test_eco_005_verifier.py
```

The focused proof covers encrypted-at-rest private markers, exact replay,
repository-only mutation, workspace integrity, relationships, activities,
follow-up completion and undo, fail-closed Private Relationships defaults,
missing Board rejection, exact Board-card binding, and live Board-owned stage
projection.
