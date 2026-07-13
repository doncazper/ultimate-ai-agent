# ADR-0054: Canonical Application Object Ownership

Status: Accepted for ECO-000 contract and design work; no runtime migration is
authorized.

## Decision

Every ecosystem entity kind has exactly one canonical owner. Identity owns
people and workspaces; Calendar owns events; Tasks owns tasks and commitments;
Plans owns projects and plans; Boards owns boards and projections; CRM owns
relationship and pipeline records; Inbox owns source artifacts and drafts;
Organizer owns lists and routines; Governance owns ChangeSets and receipts;
Memory owns reviewed recall and provenance only.

The executable ownership map is
`ultimate_ai_agent.core.ecosystem.ownership.CANONICAL_OWNER_BY_ENTITY_KIND`.
Today, search, timelines, Boards, and CRM relationship views consume typed refs
and projections. They do not copy another owner's domain state.

## Consequences

- A CRM meeting links to a Calendar Event. CRM cannot own an Event duplicate.
- A CRM follow-up links to a Task when accountable work is created.
- A Task or Opportunity board card is a projection; standalone `BoardItem` is
  the only Boards-owned subject.
- Existing records remain untouched until compatibility readers, migration
  previews, backups, replay tests, and cutover receipts exist.
- Memory and model output are never canonical app truth.

## Rejected

Shared untyped objects, UI-owned records, duplicate per-app tasks/events, and a
single catch-all database table were rejected because they create ambiguous
authority, deletion, migration, and conflict semantics.
