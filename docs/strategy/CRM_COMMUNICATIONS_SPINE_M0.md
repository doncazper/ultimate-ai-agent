# CRM + Communications Spine M0

Status: contract-only M0
Baseline: v0.104.0 / 0.104.0
Primary contract: `src/ultimate_ai_agent/core/crm/contracts.py`
Verifier: `scripts/verify_crm_communications_spine_m0.py`

## Purpose

CRM is a first-class UAA product line, but M0 is only the contract and language
foundation. It preserves Founder Command Center as the Apple-like first-party
operator shell while giving CRM and Communications their own safe-ref contract
spine for later implementation.

The locked architecture is:

```text
Global Identity -> Workspace Context -> Pipeline Object -> Communications Spine -> Work Queue / Proposal -> Action Inbox / Evidence / Memory
```

This document and contract add no /crm UI, no backend endpoints, no connector
runtime, no connector writes, no sends, no calendar writes, no silent merges,
no silent contact creation, no provider/model calls, no live web, no browser
runtime, no account sync, no public beta, and no production authority.

## Relationship To FCC

Founder Command Center remains the product loop and first-party shell:
Morning Briefing, Today, Inbox, Plans, Actions, Memory, Evidence, Settings,
Chat, and Setup. CRM + Communications M0 is a product-line contract that can
feed those surfaces later through backend-owned read models and proposal refs.

CRM M0 must not reinterpret the Founder Command Center north-star visuals and
must not use them as CRM implementation evidence. CRM can become a primary
surface later only through an accepted milestone that adds the exact route,
read model, UI, tests, route manifests, CLI parity, and product-truth updates.

## Canonical Nouns

M0 defines typed contract nouns for:

- `Person`
- `Organization`
- `Workspace`
- `WorkspaceContext`
- `Relationship`
- `PipelineObject`
- `Activity`
- `CommunicationItem`
- `WorkQueue`
- `GovernedPlaybook`
- `EngagementSignal`
- `IdentityMatchCandidate`
- `CrmProposal`
- `ApprovalRecord`
- `EvidenceRef`
- `MemoryProvenance`
- `PresetPack`

These nouns are schema and product language anchors only. Being visible in a
catalog, manifest, fixture, preset pack, or read model does not grant runtime
authority.

## State Language

CRM and Communications copy must distinguish:

- `mock_only`
- `fixture_only`
- `read_only`
- `proposal_only`
- `blocked`
- `implemented`

Drafts are not sends. Calendar proposals are not calendar writes. Relationship
memory is recall, not truth or authority. Identity match candidates are review
candidates, not merges. Derived contacts are review candidates, not silent
contact creation.

## M0 Contract Scope

The Python contract exports:

- `CrmPerson` and `CrmOrganization` as global identity refs.
- `CrmWorkspace` and `CrmWorkspaceContext` as hard workspace boundaries for
  Real Estate, Finance/Insurance, Healthcare, Retail/E-commerce, and
  Professional Services.
- `CrmPipelineObject` for workspace-specific business objects.
- `CrmCommunicationItem` for safe metadata refs to email, text, call,
  calendar, message, note, and reminder items.
- `CrmWorkQueue`, `CrmGovernedPlaybook`, and `CrmEngagementSignal` for later
  review lanes.
- `CrmIdentityMatchCandidate`, `CrmProposal`, `CrmApprovalRecord`,
  `CrmEvidenceRef`, and `CrmMemoryProvenance` for review-only, receipt-backed
  future flows.
- `CrmPresetPack` for code-owned fixture-only preset posture.

The M0 builder returns all five first-class preset packs. Each is fixture_only
and blocked from customization runtime, import/export, schema migration,
connector runtime, account sync, writes, sends, calendar writes, or production
authority.

## Explicit Non-Goals

M0 does not add:

- `/crm` or any other new Control Center route.
- `/control-center/crm` or any backend CRM endpoint.
- CRM storage, account sync, contact import, contact creation, or contact
  merge execution.
- Inbox account auth, email fetch, message fetch, calendar fetch, source body
  ingestion, downloads, sends, archive/delete/label/move behavior, or calendar
  writes.
- Provider SDK calls, runtime model calls, live web, browser automation,
  scraping, enrichment, shell/subprocess execution, or connector writes.
- Chat context injection, model-output authority, automatic memory writes,
  silent CRM updates, silent identity merges, or silent contact creation.
- Public beta, public distribution, production readiness, or production
  authority.

## Future Milestones

Later milestones remain separately gated:

- M1: Beautiful CRM North Star shell with deterministic fixtures only.
- M2: Backend-owned CRM read model and read-only endpoints.
- M3: Communications Spine in the existing Inbox product surface.
- M4: Work queues, intake rules, and engagement signals.
- M5: Identity hygiene and Relationship Graph.
- M6: CRM proposal lane.
- M7: Chat-aware CRM proposals only.
- M8: Personal Ops substrate.
- M9: Exact local CRM writes.
- M10: Drafts, calendar writes, and sends as separate exact-approved lanes.
- M11: Versioned preset packs and controlled customization.

Each future milestone must carry its own route status, OpenAPI/API manifest
updates if applicable, CLI or repo-local inspection parity, redacted evidence,
tests, product-language updates, and rollback or safe-disable posture.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_crm_communications_spine_contracts.py
PYTHONPATH=src .venv/bin/python scripts/verify_crm_communications_spine_m0.py
.venv/bin/python scripts/verify_documentation_integrity.py
```
