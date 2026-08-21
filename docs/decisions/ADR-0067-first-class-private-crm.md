# ADR-0067: First-Class Private CRM On Shared Local Data And Boards

- Status: Accepted for bounded ECO-005 core scope
- Date: 2026-08-21

## Context

CRM M0-M2 established safe-ref contracts, fixtures, and a local Command Center
compatibility surface, but not an encrypted private product-truth repository.
The first-class CRM plan requires shared identity, strict workspace privacy,
relationships, activities, follow-ups, and pipelines without creating another
board engine or leaking private contact data into evidence.

## Decision

Store one encrypted, versioned private CRM portfolio aggregate per ECO-001
workspace. Identity is portfolio-wide; CRM context and work are bound to exact
CRM workspace refs. Private Relationships always excludes itself from global
search, Today, Briefing, Memory, and general export.

Reserve `module-ref:crm`, `record-kind-ref:crm-private-portfolio`, and the
repository-only `ecosystem.crm.apply` action. Durable governance metadata may
contain only safe refs, fingerprints, counts, versions, and lifecycle posture.

Reuse ECO-003 Boards for every pipeline. CRM retains a Board ref and an exact
card binding, but no lane, stage, position, WIP, title, or description copy.
Read models resolve current Board placement and bind results to Board versions.

Keep CRM M0-M2 intact. Migration and product cutover require later explicit
acceptance and are not implied by this decision.

## Consequences

This gives UAA a usable encrypted CRM domain foundation with exact local
mutations, replay, concurrency control, and undo while preserving canonical
ownership. Cross-record operations between Boards and CRM use separately
approved repository mutations in this slice; the CRM mutation fails closed
unless the referenced Board/card truth already exists.

The one-megabyte aggregate cap is intentionally bounded. Larger deployments,
fine-grained records, production key/path backends, migration, API/CLI/UI,
connector sync, sends/writes, model assistance, background work, public release,
and production authority remain separate decisions.
