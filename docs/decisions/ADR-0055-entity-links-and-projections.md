# ADR-0055: EntityLink And Projection Semantics

Status: Accepted. Bounded encrypted persistence is implemented by ADR-0071;
projection consumers and broader runtime use remain later work.

## Decision

Cross-app relationships use typed `EntityLink` records with canonical refs,
link kind, workspace/privacy scope, provenance, and deletion posture.
Projections contain only display/placement refs and the canonical subject ref.
They cannot claim domain authority or copy mutable domain state.

Private links cannot cross workspaces. Links are not hidden context injection,
and do not make a source eligible for search, export, briefing, memory, or model
context. Each consumer must independently evaluate privacy and eligibility.

Timeline entries are safe-summary projections owned by the originating app.
Evidence may cite their refs but does not receive raw private values.

## Consequences

Boards stores lane/order/view state, not Task or Opportunity truth. Today can
explain why an item is shown and link to its owner. Deleting a link does not
silently delete either entity; entity deletion must process link posture
explicitly.

## Rejected

Foreign-key-shaped strings without privacy metadata, denormalized card copies,
global graph visibility, and automatic context injection were rejected.
