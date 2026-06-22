# FCC-V1-001 API Perimeter For Real Mutations

Status: implemented as contract and verifier coverage.

FCC-V1-001 closes the metadata and verification perimeter that must exist
before Founder Loop Action, Memory, or Chat mutations become real product
workflows. It consumes the implemented UAA-P1-080 through UAA-P1-086 API
boundary lane and adds Founder Loop-specific release pressure: no new mutation
can land invisibly, without route classification, auth posture, approval
posture, idempotency posture, rate-limit posture where required, tests, and
manifest visibility.

This milestone adds no backend route, middleware, dependency, durable replay
store, action execution, memory write, connector write, provider/model call,
browser automation, shell/subprocess path, public distribution, public beta
claim, production authority, or production readiness claim.

## What Is Implemented

- `/api/manifest` route items now expose `auth_posture` and
  `approval_posture` alongside `route_classification`, `side_effect_class`,
  `idempotency_posture`, and `rate_limit_posture`.
- `/api/manifest` exposes route-level auth and approval posture summaries.
- The frozen API route inventory fixture is updated to schema
  `uaa-api-route-inventory.v4` so every route projection includes auth and
  approval posture.
- The FCC-V1-001 perimeter manifest records the current 17 routes classified
  as `mutating_requires_authority`.
- `scripts/verify_fcc_v1_001_api_perimeter.py` fails if the manifest, fixture,
  targeted local rate-limit groups, or mutation posture drifts.
- Focused tests prove the verifier catches missing idempotency posture, unsafe
  replay/manual-review claims, and manifest overclaims.

## Duplicate Replay Contract

Duplicate replay behavior is defined here as a required route-owner contract.
FCC-V1-002 implements it for Action Inbox decision routes; other Founder Loop
mutation families remain future or blocked until their route owners add
append-first receipt storage.

Before a future Founder Loop mutation route can become a real product workflow:

- the same idempotency key with the same scoped payload must return the prior
  durable receipt;
- the same idempotency key with a conflicting payload must reject the request;
- the route owner must have append-first receipt storage that makes the replay
  decision inspectable;
- the route must preserve exact approval binding, rollback or safe-disable
  refs, redacted evidence refs, and Foundation Gate posture where applicable.

The current P1-084 idempotency header gate proves that mutating requests carry
an idempotency key or idempotency ref before the handler runs. It does not
provide durable dedupe storage, replay execution, or exactly-once execution.

## Rate Limits

Rate limits are local-first backpressure, not authentication.

FCC-V1-001 keeps the UAA-P1-085 targeted local fixed-window posture for the
first expensive or sensitive route groups: model/chat, task decomposition,
action preview/proposal, file approval capture, and local-model validation.
Action decision routes now declare `action_decision` rate-limit posture through
FCC-V1-002. Future memory decision and Chat handoff mutation routes must
declare rate-limit posture before they can land.

## Manual Review

Manual review remains deferred.

The UAA-P1-087.2b acceptance ledger and UAA-P1-087.2c manual review scaffold
remain useful planning and evidence scaffolds, but they do not provide accepted
or revised manual-review answers. FCC-V1-001 does not claim those answers are
complete.

## Founder Loop Mutation Families

The perimeter manifest records mutation families that must satisfy this gate
before runtime behavior is added:

- Today to Action envelope creation
- Action decision approve, edit, reject, defer, and expire
- Chat turn receipt and handoff to Plans or Actions
- Memory Review accept, correct, reject, retention, and delete decisions
- Evidence Timeline append/update records
- File proposal or approval capture flows

Action decision routes now have route-owner storage, idempotency replay,
exact approval validation where required, and receipt refs. The other families
remain planned or blocked until route-owner storage, idempotency replay, exact
approval binding, receipts, and evidence timeline updates exist for that route.

## Evidence

- `docs/control_center/founder_loop_api_perimeter_manifest.json`
- `docs/schemas/founder_loop_api_perimeter.schema.json`
- `scripts/verify_fcc_v1_001_api_perimeter.py`
- `tests/test_fcc_v1_001_api_perimeter.py`
- `src/ultimate_ai_agent/api/contracts.py`
- `src/ultimate_ai_agent/api/manifest.py`
- `tests/fixtures/api_route_inventory_117.json`
- `scripts/verify_uaa_p1_086_api_boundary_enforcement_tests.py`
- `tests/test_api_boundary_enforcement.py`
