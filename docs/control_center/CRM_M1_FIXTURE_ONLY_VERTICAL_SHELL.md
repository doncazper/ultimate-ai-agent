# CRM M1 Fixture-Only Vertical Shell

Status: fixture_only Control Center shell proof
Baseline: v0.104.0 / 0.104.0
Source prompt pack: `docs/prompts/crm_product_sequence.md`
Python contract: `src/ultimate_ai_agent/core/crm/fixtures.py`
Verifier: `scripts/verify_crm_m1_fixture_only_vertical_shell.py`

## Purpose

CRM M1 shapes the first screen-ready CRM product lane without adding runtime
authority. It turns the accepted CRM + Communications Spine M0 preset packs
into deterministic fixture-only vertical fixtures and a `/crm` Control Center
shell that presents those refs as screen structure only.

This artifact adds the `/crm` Control Center route as fixture-only
presentation. It adds no backend CRM endpoints, no backend CRM read model, no
connector runtime, no connector writes, no external CRM writes, no account
sync, no contact import, no sends, no calendar writes, no provider/model
calls, no live web, no browser automation, no hidden context injection, no
public beta, no public release, no production readiness claims, and no
production authority.

## Allowed M1 Boundary

Allowed now:

- Deterministic Python-core fixture map for five CRM verticals.
- Fixture-only `/crm` Control Center shell route and route-status manifest
  entry using `route-ref:control-center:crm-fixture-only-shell`.
- Safe refs and redacted fixture labels only.
- Screen-ready fixture metadata for navigation, object kinds, work queues,
  pipelines, inspector sections, communications metadata placeholders,
  evidence refs, memory provenance refs, next safe action refs, and blocked
  authority refs.
- State labels limited to `fixture_only`, `read_only`, `proposal_only`, and
  `blocked`.
- Focused tests and verifier coverage proving the fixture-only boundary.

Not allowed in M1:

- Backend CRM routes or route-status promotion beyond fixture-only blocked
  posture.
- Backend CRM read models or read-only API routes.
- Connector runtime or connector writes.
- External CRM writes, account sync, contact import, silent contact creation,
  or silent identity merge.
- Email/message sends or calendar writes.
- Provider/model calls, live web, scraping, browser automation, or enrichment
  runtime.
- Hidden context injection, automatic memory truth, public beta, public
  release, production readiness claims, or production authority.

## Prompt Execution Posture

| Prompt | Outcome | Reason |
|---|---|---|
| Prompt 01 | implemented as fixture_only scope proof | This document is the M1 entry point and records the exact no-go posture. |
| Prompt 02 | implemented as Python fixture contract | `build_crm_m1_fixture_map()` converts M0 preset packs into screen-ready deterministic fixtures. |
| Prompt 03 | implemented as fixture-only route/status proof | The `/crm` Control Center shell route is accepted only as presentation over fixture refs with blocked backend authority. |
| Prompt 04 | implemented as fixture shell rendering | Real Estate/Realtor fixture sections render through `/crm` with no write controls. |
| Prompt 05 | implemented as fixture shell rendering | Healthcare fixture sections render through `/crm` with no connector/runtime controls. |
| Prompt 06 | implemented as fixture shell rendering | Finance/Insurance fixture sections render through `/crm` with no provider/model or billing authority. |
| Prompt 07 | implemented as fixture shell rendering | Retail/E-commerce fixture sections render through `/crm` with no commerce sync, sends, or live tracking. |
| Prompt 08 | implemented as fixture shell rendering | Professional Services fixture sections render through `/crm` with no external CRM write, send, calendar, or account authority. |
| Prompt 09 | planned, backend blocked | CRM M2 backend read models and API routes remain future gated work. |
| Prompt 10 | planned, connector blocked | Inbox communications metadata remains planned until accepted read-only authority exists. |
| Prompt 11 | planned, review-only blocked | Work queues, signals, and relationship graph stay fixture/read-only planning surfaces. |
| Prompt 12 | planned, writes blocked | Proposal lanes and exact local-write ladder remain future gated authority work. |

## Vertical Fixture Map

| Vertical | Fixture focus | Implemented now | Still blocked |
|---|---|---|---|
| Real Estate/Realtor | Leads, buyers, sellers, listings, showings, offers, closings, follow-ups, relationship context, and next safe actions. | Pipeline, relationship inspector, property/listing context refs, follow-up queue refs, communications metadata placeholder refs, evidence refs, memory provenance refs, and blocked-authority refs. | MLS fetch, enrichment, contact import, outbound send, calendar write, external CRM sync, and account auth. |
| Healthcare | Referral relationships, intake-style pipeline objects, care-team coordination metadata, follow-up obligations, and evidence-backed next safe actions. | Referral/intake pipeline refs, organization/provider relationship refs, handoff queue refs, consent posture refs, communications metadata placeholder refs, evidence refs, memory provenance refs, and blocked-authority refs. | PHI ingestion, EHR integration, medical advice, appointment writes, contact sync, account auth, sends, and connector runtime. |
| Finance/Insurance | Prospects, households or organizations by safe ref, policy/opportunity pipeline, renewal follow-ups, risk review posture, and proposal-only next actions. | Opportunity/renewal pipeline refs, relationship and household/org inspector refs, follow-up/review queue refs, communications metadata placeholder refs, evidence refs, memory provenance refs, and compliance blocker refs. | Financial advice, underwriting automation, account sync, external CRM write, contact import, sends, calendar writes, and provider/model authority. |
| Retail/E-commerce | Customer cohorts by safe ref, order/support metadata placeholders, campaign ideas as proposals, retention follow-ups, and evidence-backed blocked states. | Customer/opportunity pipeline refs, cohort and relationship inspector refs, retention queue refs, communications metadata placeholder refs, evidence refs, memory provenance refs, and blocked-authority refs. | Commerce-platform sync, order import, marketing send, customer data ingestion, account auth, external CRM write, and live tracking. |
| Professional Services | Leads, clients, projects, proposals, commitments, account health, relationship memory, and follow-up obligations. | Lead/proposal/project pipeline refs, client and stakeholder inspector refs, promise/follow-up queue refs, communications metadata placeholder refs, evidence refs, memory provenance refs, and blocked-authority refs. | Invoice/payment integration, external CRM write, email send, calendar write, account auth, connector runtime, and hidden context injection. |

## M2 And Later Plan

M2 may add backend-owned CRM read models and read-only routes only after a
separate accepted milestone updates OpenAPI, API manifest, route-status
manifests, CLI or repo-local inspection, tests, product language, and
rollback/safe-disable posture.

M3 may place CRM communications metadata in Inbox only as safe refs and
metadata-only items. Raw bodies, account auth, background polling, sends,
calendar writes, and connector reads or writes remain blocked until exact
authority is accepted.

M4 and M5 may add review-only work queues, signals, and relationship graph
posture. Identity match candidates must remain review candidates, not silent
merges. Follow-up handoff to Action Inbox remains proposal_only unless a later
exact lane is accepted.

M6 and later proposal/write lanes need exact approval scope, idempotency,
receipt refs, evidence refs, rollback posture, safe-disable posture, and
tests. External CRM writes, sends, calendar writes, connector writes, account
sync, and production authority remain blocked until separately accepted.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_crm_m1_fixture_only_vertical_shell.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_crm_m1_fixture_only_vertical_shell.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_crm_communications_spine_contracts.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_crm_communications_spine_m0.py
cd apps/control-center && npm test -- --run src/App.test.tsx
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_frontend.py
.venv/bin/python scripts/verify_documentation_integrity.py
git diff --check
```
