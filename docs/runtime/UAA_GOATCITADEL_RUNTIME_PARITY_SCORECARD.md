# UAA GoatCitadel Runtime Parity Scorecard

Status: Phase 01 baseline for the UAA GoatCitadel runtime parity pack.
Scope: code-evidenced comparison and implementation lane map only.

This scorecard records where UAA stands against the GoatCitadel runtime
architecture patterns that are useful as read-only reference comparators. It is
not runtime authority, not copied from GoatCitadel, and does not change Control Center behavior.
It uses GoatCitadel as a read-only reference comparator while preserving UAA's
Python Agent Core, LocalApprovalAuthority, route classification, OpenAPI,
redaction, and Foundation Gate boundaries.

## Status Labels

Use these labels for every runtime-parity claim:

- implemented
- partial
- planned
- mock-only
- blocked
- deprecated
- contradicted
- unknown

Code and tests are stronger evidence than docs. Roadmaps and benchmark notes
can shape priority, but they do not prove UAA product readiness.

## Parity Target

Parity by this pack means a UAA-native, governed runtime loop where a turn can
be prepared, routed, attached to a durable run, placed into an approval state,
orchestrated through staged no-effect planning, inspected through CLI/API/Control
Center surfaces, and proven with receipts and safe refs. It does not mean broad
autonomy, unrestricted execution, production authority, or imported GoatCitadel
runtime behavior.

Blocked authority remains blocked unless a later accepted lane separately proves
exact scope, approval binding, idempotency, safe-disable/rollback posture,
receipt/proof refs, redaction, CLI/API/Core parity, route side-effect
classification, and focused verifier coverage.

## Source Files Inspected

UAA evidence refs:

- `AGENTS.md`
- `README.md`
- `VERSION.md`
- `SECURITY.md`
- `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
- `docs/control_center/AUTHORITY_GRADUATION_BOARD.md`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
- `docs/architecture/TURN_CONTRACT_ROUTER.md`
- `src/ultimate_ai_agent/core/decision_router/`
- `src/ultimate_ai_agent/core/runtime_gateway/contracts.py`
- `src/ultimate_ai_agent/core/runtime_gateway/storage.py`
- `src/ultimate_ai_agent/core/orchestration_efficiency/`
- `src/ultimate_ai_agent/core/providers/control_plane.py`
- `src/ultimate_ai_agent/core/providers/role_evidence.py`
- `scripts/dev/uaa_turn_router.py`
- `scripts/dev/uaa_runtime.py`
- `tests/test_turn_contract_router_harness_binding.py`
- `tests/test_governed_runtime_contracts.py`
- `tests/test_model_provider_control_plane.py`

GoatCitadel read-only reference refs:

- `../GoatCitadel/apps/gateway/src/routes/chat.messages.ts`
- `../GoatCitadel/apps/gateway/src/orchestration/engine.ts`
- `../GoatCitadel/apps/gateway/src/orchestration/model-selector.ts`
- `../GoatCitadel/apps/gateway/src/services/chat-turn-prep-service.ts`
- `../GoatCitadel/docs/CANONICAL_RUNTIME_STATE_MODEL.md`

These GoatCitadel refs are architectural evidence only. They are not imported
code, product dependency, package dependency, execution authority, or evidence
that UAA already has the same runtime capability.

## Component Scoreboard

| Runtime parity dimension | Current Score | Target Score | Confidence | Status | Strongest UAA evidence | Missing evidence | Exact implementation lane |
|---|---:|---:|---|---|---|---|---|
| Turn-contract clarity | 9 | 9 | High | implemented | `src/ultimate_ai_agent/core/decision_router/`, `PreparedTurn`, `scripts/dev/uaa_turn_router.py`, `tests/test_turn_contract_router_harness_binding.py`, and `docs/architecture/TURN_CONTRACT_ROUTER.md` prove `base_answer` handling, prepared-turn branches, preview routing, route binding, preflight posture, approval escalation, and executor fencing without model/provider calls. | Prepared turns are inspectable but not yet connected to live Control Center chat composition as a primary UI workflow. | Phase 08 Prompt: cockpit parity |
| Authority/safety boundary | 9 | 9 | High | implemented | `AGENTS.md`, `src/ultimate_ai_agent/core/runtime_gateway/contracts.py`, `docs/control_center/AUTHORITY_GRADUATION_BOARD.md`, and `tests/test_governed_runtime_contracts.py` preserve sealed/default posture, exact approval scopes, idempotency, redaction, and blocked authority refs. | Later phases must prove they do not route around LocalApprovalAuthority, route side-effect classification, OpenAPI, redaction, or Foundation Gate checks. | Phase 02 Prompt through Phase 08 Prompt: harden each new surface against authority creep |
| Execution readiness | 8 | 8 | Medium | implemented | RuntimeGateway contracts, Action Inbox approval envelopes, local loopback metadata receipts, focused pytest approval bridge posture, `RuntimeActionSignedEvidenceEnvelope`, signed evidence CLI/API/Control Center refs, and `tests/test_runtime_action_signed_evidence.py` show exact-lane execution scaffolding, idempotent replay, safe-disable, scope-drift blocking, redaction, and offline verification. | Signed evidence is implemented for the exact focused pytest lane only; broader action lanes still need separate approval, receipt, rollback, redaction, route classification, and verifier proof. | Phase 07 Prompt: mature action execution and signed evidence |
| Durable runtime integration | 8 | 8 | Medium | partial | Durable run/read-model work, RuntimeGateway invocation storage, Run Observability, `TurnRunApprovalChainReadModel`, and `StagedOrchestrationReadModel` show local durable state, replay posture, approval-wait posture, staged dependencies, degraded handoff posture, and read-only API/CLI inspection. | Prepared chat turns have not yet been attached to the route-decision -> durable run -> staged orchestration -> approval-wait path. | Phase 05 Prompt: chat turn preparation |
| Model/provider routing | 7 | 7 | Medium | implemented | `src/ultimate_ai_agent/core/providers/control_plane.py`, `src/ultimate_ai_agent/core/providers/role_evidence.py`, provider research posture docs/tests, router-dry-run posture, `scripts/dev/uaa_runtime.py inspect-role-provider-evidence`, and model/provider control-plane tests show read-only role-based provider/model evidence and dry-run routing. | Evidence is advisory/read-only and not yet a live execution router; remote provider calls, provider SDK calls, fallback execution, and provider-output authority remain blocked. | Phase 06 Prompt: role-based model/provider evidence |
| Operator inspectability | 9 | 8 | High | implemented | CLI/API/Control Center surfaces for Turn Router, RuntimeGateway, Evidence, Action Inbox, Provider posture, Work Board, Coding, and GoatCitadel catch-up cockpit parity expose safe refs and blocked states. Phase 08 adds `RuntimeParityLoopReadModel`, `GET /api/runtime/parity-loop`, `uaa runtime inspect-parity-loop`, and Control Center parity-loop stage refs so the runtime loop is inspectable as one backend-owned chain. | The cockpit still does not provide authority-bearing execute controls; this remains intentional until exact lanes are separately approved. | Phase 08 Prompt: cockpit/CLI/API parity and final hardening |
| Product usefulness today | 8 | 8 | Medium | partial | Today, Action Inbox, Evidence, Proof, Memory, Trust, Runtime readiness, Coding Cockpit, Work Board, PreparedTurn inspection, exact runtime receipts, signed evidence, and the Phase 08 parity-loop read model provide a local-first reviewable operation loop. | The primary chat UI still needs a seamless prepared chat turn -> exact action receipt -> proof narrative flow before UAA can claim full GoatCitadel-style product parity. | Phase 08 Prompt: cockpit/CLI/API parity and final hardening |
| Long-term safe foundation | 9 | 9 | High | implemented | Python Agent Core owns durable truth; Control Center is presentation/initiation only; OpenAPI/API manifest, PolicyEngine, LocalApprovalAuthority, route classifications, product truth, and verifiers are active gates. | Future runtime phases must avoid broad flags and preserve safe refs, bounded previews, hashes, receipts, and blocked-state language. | All phases preserve this foundation |

## Phase Lane Map

Phase 02 Prompt binds live route decisions to the governed turn path without
provider/model calls or action execution. Implemented evidence now lives in
`docs/runtime/UAA_GOATCITADEL_RUNTIME_ROUTE_DECISION_BINDING.md` and
`src/ultimate_ai_agent/core/decision_router/route_binding.py`.

Phase 03 Prompt adds the canonical Turn -> Durable Run -> Approval state model
with safe refs, replay posture, and approval-wait truth. Implemented evidence
now lives in
`docs/runtime/UAA_GOATCITADEL_RUNTIME_TURN_RUN_APPROVAL_CHAIN.md` and
`src/ultimate_ai_agent/core/execution/turn_run_approval_chain.py`.

Phase 04 Prompt is implemented as staged orchestration visibility and
dependency validation as no-effect planning/read-model truth only. Implemented evidence now lives in
`docs/runtime/UAA_GOATCITADEL_RUNTIME_STAGED_ORCHESTRATION_ENGINE.md`,
`src/ultimate_ai_agent/core/execution/staged_orchestration.py`, and
`GET /api/runtime/staged-orchestration`.

Phase 05 Prompt is implemented as backend-owned PreparedTurn context, route,
memory, tool/action readiness, orchestration, durable run, evidence, and
next-action posture without hidden context injection. Implemented evidence now
lives in `docs/runtime/UAA_GOATCITADEL_RUNTIME_PREPARED_TURN_LOOP.md`,
`src/ultimate_ai_agent/core/decision_router/prepared_turn.py`, and
`GET /api/runtime/prepared-turn`.

Phase 06 Prompt is implemented as backend-owned role-based model/provider
evidence inside the model/provider control plane. It ranks local and remote
candidate provider/model refs for answerer, planner, reviewer, synthesizer,
coder, extractor, and safety reviewer roles; records cost/latency visibility,
policy decision refs, fallback refs, disabled reason refs, redacted evidence
refs, and route trace refs; and exposes CLI/API/Control Center inspection
without provider SDK calls, live remote model calls, fallback execution, model
invocation, raw prompt/response/provider payload persistence, or provider
output authority. Implemented evidence now lives in
`docs/runtime/UAA_GOATCITADEL_RUNTIME_ROLE_PROVIDER_EVIDENCE.md`,
`src/ultimate_ai_agent/core/providers/role_evidence.py`,
`src/ultimate_ai_agent/core/providers/control_plane.py`, and
`scripts/dev/uaa_runtime.py inspect-role-provider-evidence`.

Phase 07 Prompt is implemented for the exact focused pytest Action Inbox lane.
It adds `RuntimeActionSignedEvidenceEnvelope`,
`verify_runtime_action_signed_evidence`, receipt-detail API evidence,
`scripts/dev/uaa_runtime.py receipts evidence`,
`scripts/dev/uaa_runtime.py receipts verify-evidence`, Control Center bridge signed evidence refs, and
tests for pass path, missing receipt/envelope, scope drift, idempotent replay,
safe-disable, redaction, and offline verification. It does not add generic tool
execution, unrestricted shell, connector writes, browser automation, provider
SDK calls, remote execution, plugin runtime import, production authority, public
notarization, or public release claims.

Phase 08 Prompt is implemented as final cockpit, CLI, API, docs, and verifier
inspection parity. It adds `RuntimeParityLoopReadModel`,
`GET /api/runtime/parity-loop`, `uaa runtime inspect-parity-loop`, Control
Center parity-loop API/CLI/stage refs in the Runtime Action Inbox bridge, and
`scripts/verify_uaa_goatcitadel_runtime_parity_final.py`. It keeps Control
Center as presentation/initiation only and does not add broad runtime authority.

## GoatCitadel Patterns Borrowed As UAA-Native Designs

- Route-decision preflight should be explicit before execution-sensitive work.
- Runtime state should separate prepared, approval-wait, running, completed,
  blocked, cancelled, retryable, and dead-letter posture.
- Staged orchestration should reject duplicate step refs, missing dependency
  refs, same-stage or future-stage dependencies, and cycles.
- Chat-turn preparation should gather bounded context, route decisions,
  orchestration posture, and approval requirements before any side effect.
- Model/provider selection should leave inspectable candidate, rejection,
  cost/latency, and safety evidence even when no provider call occurs.
- Evidence and receipts should be linked to turn, run, approval, action,
  verifier, and rollback/safe-disable refs.

## GoatCitadel Patterns Not Merged

- GoatCitadel code is not copied from GoatCitadel.
- GoatCitadel packages are not imported.
- Runtime provider fan-out is not adopted as authority.
- Autonomous background dispatch is not adopted.
- Browser or connector execution is not adopted.
- Broad plugin/runtime import is not adopted.
- GoatCitadel product maturity claims are not treated as UAA implementation
  evidence.

## Blocked Authority Preserved

The following remain blocked outside separately accepted exact lanes:

- runtime model calls
- provider SDK calls
- live web fetching
- browser automation
- connector writes
- unrestricted shell/subprocess execution
- plugin runtime import
- remote execution
- public release claims
- production authority
- broad autonomy
- raw prompt persistence
- raw response persistence
- raw provider payload persistence
- raw local path persistence
- raw log persistence
- credential or secret-like value persistence

Existing local loopback/runtime and exact-approved provider experiments remain
their own governed, narrow, non-authoritative lanes. This scorecard does not
promote them into general runtime model calls, general provider authority, or
production authority.

## Evidence Rules

- Store safe refs, redacted summaries, bounded previews, hashes, and receipts
  only.
- Do not persist raw prompts, raw model responses, provider payloads, raw logs,
  sensitive paths, usernames, hostnames, credentials, or secret-like values.
- Model output, provider dry-run output, memory recall, and preview output are
  proposal/evidence only, not truth or authority.
- Control Center may display and initiate backend-owned envelopes, but it must not mint authority.

## Phase 01 Acceptance Result

Phase 01 is documentation/verifier work only. It defines the runtime parity
baseline, target scores, blocked authorities, and implementation lane map. It
adds no backend route, no provider/model call, no live web fetch, no browser
automation, no connector write, no shell/subprocess authority, no plugin runtime
import, no remote execution, no public beta/public release claim, no production
authority, and no broad autonomy.
