# UAA-P1-068 Today Product Spine Contract

Status: implemented contract/test/docs slice

UAA-P1-068 defines Today as the product spine for the Founder Command Center.
It does not add a new route, frontend mutation control, connector runtime,
account auth, background refresh, model/provider authority, automatic memory
write, context injection, public beta, public distribution, production
readiness, or production authority.

## Contract

The existing `GET /control-center/today/summary` route carries the Today
Product Spine contract through `product_spine_contract_ref`:

```text
contract-ref:today-product-spine:v1
```

Every module must feed the loop surfaces:

```text
Today
Actions
Evidence
Memory
```

Loop visibility is necessary but not sufficient for completion. A module cannot
claim completion just because it appears on Today. Normal Definition of Done,
typed contract or schema coverage, focused tests, redaction checks,
policy/approval boundaries, OpenAPI/API manifest checks when routes change, and
CLI or repo-local inspection paths still apply.

## Required Today Signals

Today must expose these signals as safe summaries or safe refs:

- priorities
- blockers
- follow-ups or follow-up posture refs
- plan/action state
- memory review count
- stale-source posture
- next safe actions

These signals are synthetic safe refs or bounded summaries only. They must not
store raw private content, account identifiers, usernames, hostnames, local
paths, raw logs, raw prompts, raw responses, provider payloads, credentials, or
secret-like values.

## Module Feed Rows

Each module feed row records:

- module name
- implemented, partial, planned, blocked, or missing status
- required loop outputs for Today, Actions, Evidence, and Memory
- current feed refs or missing contract refs
- `standalone_complete_allowed: false`

Chat and Code remain planned/blocked feed rows until their later milestones.
Plans remain partial until UAA-P1-073 action envelopes. Evidence remains
partial until UAA-P1-069 history grammar. Memory remains partial until source,
decision, quality, and loop-binding milestones.

## Safety

This contract is read-only state over the existing Founder Loop summary. It
does not grant approval, execution, connector writes, source refresh, memory
writes, context injection, model/provider calls, rollback execution, public
release, public beta, production readiness, or production authority.

## Evidence

- Backend payload: `src/ultimate_ai_agent/core/storage/founder_loop.py`
- Frontend type/render path: `apps/control-center/src/api/types.ts` and
  `apps/control-center/src/components/FounderLoopPanels.tsx`
- Schema: `docs/schemas/today_product_spine_contract.schema.json`
- Tests: `tests/test_founder_loop_storage.py`,
  `tests/test_control_center_founder_loop_api.py`, and
  `apps/control-center/src/App.test.tsx`
- Verifier: `scripts/verify_uaa_p1_068_today_product_spine_contract.py`
