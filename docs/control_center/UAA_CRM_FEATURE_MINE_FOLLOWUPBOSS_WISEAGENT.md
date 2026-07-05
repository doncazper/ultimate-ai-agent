# UAA CRM Feature Pattern Map

Status: implemented as non-proprietary category pattern notes
Contract ref: `contract-ref:crm-local-command-center:m2:v1`

## Boundary

This feature map records public CRM category patterns that UAA can implement in
its own local-first, governed style. It does not copy proprietary code, UI,
copy, templates, screenshots, data, branding, pricing logic, private workflows,
or private behavior from paid CRM products. No live web fetching was used for
this implementation.

The named comparison frame is only descriptive: paid CRMs commonly organize
people, relationships, follow-ups, pipelines, smart lists, communication
history, drafts, import/export, and reports. UAA implements those ideas as
safe-ref local contracts owned by Python core.

## Adopted Generic Patterns

| Category pattern | UAA local implementation |
|---|---|
| People and organizations | Safe person/org refs with display labels, tags, evidence refs, and memory provenance refs; no raw contact details. |
| Relationship context | Relationship refs with role, health, priority, next-safe-action labels, and evidence/memory refs. |
| Follow-up queue | Due/upcoming/stale/blocked/proposed/completed follow-up refs for review. |
| Pipeline board | Local opportunity refs and stage refs for founder/operator relationship work. |
| Smart lists | Deterministic list refs for due, stale, priority, opportunity, draft, blocked, and import-preview review. |
| Communication history | Timeline refs only; no raw email/message bodies and no connector fetch. |
| Draft assistance | Draft refs and review states only; no send, archive, label, move, or calendar write controls. |
| Proposal layer | Deterministic proposal refs only; no provider/model call and no model-output authority. |
| Import/export | Redacted local export and review-only import preview; commit remains future-gated. |
| Reporting | Safe counts, list refs, and blocker refs; no production analytics claims. |

## Rejected Or Future-Gated Patterns

- Live CRM sync or connector runtime.
- Account auth or OAuth.
- Contact merge or silent contact creation.
- CRM writeback.
- Email/SMS/social sends.
- Calendar scheduling/writes.
- Browser-based CRM automation.
- Background polling or source refresh.
- AI/provider-generated relationship conclusions as authority.
- Production/public release claims or production authority.

## Product Language

Allowed: "local CRM command center", "backend-owned CRM read model",
"safe-ref follow-up queue", "local exact mutation receipt", "proposal-only
draft refs", and "connector/sends blocked".

Blocked: "syncs your CRM", "sends follow-ups", "automates outreach", "imports
contacts", "AI-managed relationships", "production-ready CRM", "public beta",
or any wording that implies live connector, provider/model, browser, send, or
write authority.
