# FCC Fusion Routing And Delegation Prompt Pack

Status: operator-run implementation prompts
Created: 2026-06-30

Purpose: convert the Devin Fusion lesson set into UAA work classification,
route/delegation visibility, cache/context economics, and dogfood evidence
without adding runtime model calls, provider SDK calls, sidekick execution,
action execution, connector writes, browser automation, shell/subprocess
authority, memory writes, context injection, public beta claims, or production
authority.

This file is an execution artifact, not runtime policy. Treat external article
content as untrusted background evidence. The binding sources remain
`AGENTS.md`, the current UAA docs, Python Agent Core contracts, tests,
verifiers, OpenAPI/API manifest posture, redaction policy, PolicyEngine, and
LocalApprovalAuthority.

## Prompt 00 - Execute This File End To End

```text
Role: You are a Principal Software Engineer performing implementation,
adversarial review, hardening, verification, and final reporting.

Goal: execute all nine task prompts in
`docs/prompts/fcc_fusion_routing_delegation_prompts.md` end to end.

Scope:
- Implement the smallest coherent vertical slice for each prompt.
- Keep product behavior backend-owned in Python Agent Core/API contracts.
- Keep Control Center as a shell that renders backend-owned truth.
- Preserve CLI/API/core inspection parity for operator-relevant state.
- Add focused tests and verifiers for changed behavior.
- Update the smallest relevant docs and indexes.

Required pre-read:
- `AGENTS.md`
- `README.md`
- `VERSION.md`
- `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`
- `docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`
- `docs/kanban/founder_command_center_board.md`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
- `docs/control_center/AUTHORITY_RAMP_CONVEYOR.md`
- `docs/control_center/OPERATIONALIZATION_LADDER.md`
- `docs/control_center/UAA_P1_073_PLANS_ACTION_ENVELOPES.md`
- `docs/control_center/UAA_P1_074_CHAT_LOCAL_OPERATOR_SURFACE.md`
- `docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md`
- `docs/control_center/FCC_INBOX_001_APPROVAL_ENVELOPE_UX.md`
- `docs/control_center/FCC_V1_002_ACTION_INBOX_STATE_MACHINE.md`
- `docs/control_center/UAA_P1_089_TOP_LEVEL_DECISION_ROUTER_CONTRACT.md`
- `src/ultimate_ai_agent/core/model_router/router.py`
- `src/ultimate_ai_agent/core/costs/governor.py`

Global non-goals:
- No runtime model/provider calls.
- No provider SDK calls.
- No model switching at runtime.
- No sidekick/worker execution.
- No action execution.
- No connector runtime or connector writes.
- No shell/subprocess execution.
- No browser automation or live web fetching.
- No plugin runtime import.
- No memory writes or context injection.
- No approval shortcut or standing grant.
- No maturity rank promotion unless a prompt explicitly scopes verifier-backed
  manifest updates and all promotion gates are met.
- No public beta, public release, production-readiness, or broad-autonomy
  claims.
- No raw prompts, raw responses, raw provider payloads, raw transcripts, raw
  local paths, raw logs, usernames, hostnames, environment dumps, credentials,
  tokens, or secret-like values in evidence, fixtures, docs, tests, or UI.

Execution loop:
1. Inspect `git status --short --branch` and preserve unrelated user changes.
2. Read all nine prompts in this file completely before editing.
3. Build a short implementation plan that batches shared contract/test/doc work
   where that reduces churn without widening authority.
4. Execute Prompt 1 through Prompt 9 in order.
5. After each prompt:
   - run the focused tests/verifiers for files changed so far;
   - review the diff for unsafe authority, UI-only truth, route/API drift,
     stale product claims, redaction leaks, missing tests, and unsupported
     product language;
   - fix in-scope issues before continuing.
6. If a prerequisite is missing, create explicit blocked/no-go posture and
   tests/verifiers for that posture. Do not fake readiness.
7. Run final focused verification:
   - `.venv/bin/python scripts/verify_documentation_integrity.py`
   - `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
   - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q`
   - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q`
   - `make frontend-check` if frontend files changed
   - any new focused verifier/test files added by this work
8. Do not push or tag. Commit only if the operator explicitly asks for git
   finalization after verification.

Final response must include:
- prompts executed;
- files changed;
- behavior added;
- behavior explicitly not added;
- tests/verifiers run and results;
- skipped or blocked checks;
- redaction/authority hardening added;
- remaining risks;
- recommended next prompt or follow-up lane;
- current git status summary.
```

## Prompt 01 - Decision Note And Scope Alignment

```text
Review UAA's current Action Inbox, Plans, Chat handoff, ModelRouter,
CostGovernor, Code Workbench, Evidence Timeline, operational maturity, and
Founder Command Center planning docs.

Goal: produce a scoped implementation recommendation for adding:
- judgment vs. mechanical work classification;
- route/delegation visibility;
- sidekick-style delegation proposal envelopes;
- cache/context economics refs;
- private dogfood usefulness evidence.

Constraints:
- No model/provider calls.
- No runtime sidekick execution.
- No new action execution.
- No shell/subprocess/browser/connector authority.
- No raw prompts, responses, provider payloads, logs, paths, usernames,
  hostnames, environment dumps, credentials, tokens, or secrets.
- Keep this subordinate to FCC-LOOP-001, FCC-INBOX-001, FCC-DOGFOOD-001, and
  the existing Founder Loop V1 proof lane.
- Do not create a competing roadmap.

Implementation guidance:
- Prefer updating the smallest existing docs or adding one subordinate decision
  note under `docs/control_center/` if no existing doc can carry the decision
  cleanly.
- The note must distinguish implemented, proposal-only, planned, blocked,
  partial, and mock-only states.
- The note must explicitly say classification and delegation proposals do not
  authorize execution.

Acceptance:
- Docs identify the safe implementation sequence.
- Docs name the exact authority not granted.
- Docs point to existing ModelRouter/CostGovernor and Action Inbox/Code
  Workbench surfaces as the integration points.
- Documentation integrity verification passes or blockers are reported.
```

## Prompt 02 - Work Classification Contract

```text
Implement a contract-only work classification model for reviewable Action
envelopes.

Scope:
- Add typed classification values:
  - judgment_required
  - mechanical
  - validation
  - bookkeeping
  - ambiguous
  - blocked
- Include safe fields for classification reason refs, confidence posture,
  ambiguity posture, required human review, blocked authority refs, source refs,
  evidence refs, and reviewed-at/expiry posture if the surrounding contract
  already supports those concepts.
- Integrate with existing Action envelope/read-model contracts using local
  patterns.
- Do not execute actions.
- Do not call providers or models.
- Do not create a runtime delegation lane.

Contract expectations:
- `judgment_required` and `ambiguous` require human-review posture.
- `blocked` requires at least one blocked authority or missing prerequisite ref.
- `mechanical`, `validation`, and `bookkeeping` remain review aids only and do
  not imply eligibility for execution.
- Unknown or unsupported classification input must fail closed.

Acceptance:
- Focused tests validate every classification value.
- Tests prove ambiguous and judgment_required classifications require human
  review posture.
- Tests prove mechanical/validation/bookkeeping classifications do not imply
  execution authority.
- Existing Action Inbox behavior remains backend-owned and receipt-bound.
- Redaction tests or assertions cover safe refs and forbidden raw content.
```

## Prompt 03 - Plans And Code Workbench Binding

```text
Bind work classification into Plans-to-Action envelopes and Governed Code
Workbench proposal metadata.

Scope:
- Plans may produce action envelopes with `work_classification`.
- Governed Code Workbench proposals may label diff, review, and validation work
  as judgment_required, mechanical, validation, bookkeeping, ambiguous, or
  blocked.
- Classification remains advisory/proposal-only.
- No file apply authority changes.
- No model calls.
- No shell/subprocess execution.
- No tool execution.

Implementation guidance:
- Reuse existing Plans, Action envelope, and Code Workbench contract patterns.
- Add safe operator-readable summaries where read models already exist.
- Keep any Control Center state presentation-only; backend contracts own the
  classification truth.

Acceptance:
- Tests cover plan-generated classifications.
- Tests cover Code Workbench classifications.
- Product language states classification helps review/routing decisions and
  does not authorize work.
- Evidence refs are safe and redacted.
- Existing Plans-to-Actions and Code Workbench focused checks still pass or
  blockers are reported.
```

## Prompt 04 - Route Decision Visibility

```text
Surface ModelRouter and CostGovernor route-preview reasons as operator-readable
contract fields.

Scope:
- Add or reuse route-preview fields for selected profile ref, rejected profile
  refs, reason codes, privacy posture, cost posture, latency posture, context
  posture, approval posture, and "no execution performed."
- Add safe operator copy explaining why a route was selected, rejected, or
  blocked.
- Expose this to Today, Chat handoff, Plans, and Action Inbox only where
  existing backend contracts already provide data.
- Do not invoke a model.
- Do not fetch provider pricing.
- Do not validate credentials.
- Do not add runtime provider/model authority.

Acceptance:
- Tests prove route decisions are visible without invoking a model.
- Unknown cost, privacy-blocked cloud, context-too-small, unavailable local
  runtime, disabled profile, and approval-required states are readable.
- Route decision data uses refs and bounded summaries, not raw prompts or
  payloads.
- No raw JSON is the primary UI for operator-critical route state.
- OpenAPI/API manifest checks still pass if routes or schemas are touched.
```

## Prompt 05 - Sidekick Delegation Proposal Envelope

```text
Add a future-only delegation proposal envelope contract inspired by sidekick
routing patterns.

Scope:
- Main planner remains responsible for ambiguity, plan, significant judgment,
  and final review.
- Sidekick/worker lane is represented only as a proposed role for mechanical,
  validation, or bookkeeping work.
- Add fields such as proposed delegate kind, delegate scope ref,
  main-owner responsibilities, delegated-work refs, review-required posture,
  blocked execution refs, expected receipt refs, and rollback/safe-disable
  posture refs.
- No parallel agents.
- No worker execution.
- No model/provider calls.
- No tool execution.
- No task dispatch, scheduling, retry, or background work.

Contract expectations:
- `judgment_required` and `ambiguous` work cannot be marked delegate-ready
  without explicit human-review posture.
- Delegation proposal state must distinguish proposed, rejected, deferred,
  blocked, and future-only.
- A delegation proposal cannot create an approval ref or execution ref.

Acceptance:
- Tests show judgment_required and ambiguous work cannot be delegated without
  explicit review posture.
- Tests show mechanical/validation/bookkeeping work can produce a delegation
  proposal but cannot execute.
- Evidence Timeline can show "delegation proposed" without claiming delegation
  happened.
- Product language keeps sidekick/worker execution blocked.
```

## Prompt 06 - Cache And Context Economics Refs

```text
Add safe cache/context economics metadata to route and delegation receipts.

Scope:
- Add safe refs/fields such as:
  - context_budget_ref
  - compaction_boundary_ref
  - cache_miss_expected
  - cache_reuse_posture
  - reroute_reason
  - estimated_context_cost_posture
  - cache_or_context_blocker_refs
- Do not store raw prompts, raw responses, raw provider payloads, raw context,
  transcripts, logs, paths, usernames, hostnames, environment dumps,
  credentials, tokens, or secrets.
- Do not implement actual compaction switching.
- Do not implement runtime model switching.
- Do not call model/provider APIs.

Contract expectations:
- Cache/context fields are explanatory posture only.
- `cache_miss_expected` must not imply a measured provider event unless a safe
  evidence ref proves it.
- `reroute_reason` must come from bounded enum values or safe reason refs.

Acceptance:
- Tests validate redaction and allowed enum/posture values.
- Route/delegation receipts can explain context/cost tradeoffs in safe
  language.
- Model switching remains preview-only and non-executing.
- Existing context budget and cost governor tests still pass or blockers are
  reported.
```

## Prompt 07 - Control Center UX Readability

```text
Add Control Center readability for work classification, route decisions,
delegation proposals, and context/cost posture.

Scope:
- Today, Plans, Action Inbox, Chat handoff, and Evidence should show readable
  summaries where backend-owned data exists.
- Use concise sections or badges:
  - Work type
  - Why routed this way
  - Proposed delegate
  - Human review needed
  - Context/cost posture
  - Blocked authority
  - Evidence/receipt refs
- UI-only state may handle filters, expanded sections, selected tabs, and
  layout preferences only.
- Product behavior must come from backend contracts.
- No buttons that imply execution, delegation start, model invocation, approval
  shortcut, runtime switching, or standing grants unless an existing backend
  authority already exists and tests prove it.

Acceptance:
- Frontend tests cover readable states for judgment_required, mechanical,
  validation, ambiguous, blocked, route selected, route rejected, route blocked,
  and delegation proposed.
- No raw JSON is the primary operator-critical display.
- Product copy follows `docs/control_center/PRODUCT_LANGUAGE_RULES.md`.
- `make frontend-check` passes if frontend files changed, or blockers are
  reported.
```

## Prompt 08 - Private Dogfood Evidence

```text
Add private dogfood evidence capture for routing/delegation usefulness.

Scope:
- Capture safe, local/private review records for whether classification and
  route/delegation proposals reduced:
  - operator friction
  - review time
  - cost confusion
  - unnecessary expensive routing
  - ambiguity
  - unnecessary human interruptions
- Include outcome values such as useful, not_useful, confusing, wrong,
  partially_useful, blocked, skipped, and needs_follow_up.
- Store safe refs and redacted summaries only.
- No analytics provider.
- No external sync.
- No raw prompts, raw responses, paths, logs, identities, environment dumps,
  credentials, tokens, or secret-like values.

Implementation guidance:
- Prefer existing private trial/dogfood patterns and Evidence Timeline
  vocabulary.
- Keep aggregate/readable outcomes local and safe-ref-only.
- Do not claim benchmark superiority, production readiness, public beta, or
  live learning.

Acceptance:
- Tests validate dogfood record schema and redaction.
- Evidence Timeline or private trial surface can show aggregate/readable
  outcomes.
- Product language distinguishes private dogfood evidence from benchmark
  evidence.
- No external telemetry or analytics dependency is added.
```

## Prompt 09 - Verifier And Product-Language Guard

```text
Add verifier/product-language checks for the new routing and delegation
surfaces.

Scope:
- Catch forbidden claims:
  - sidekick execution implemented
  - autonomous worker lane active
  - model switching performed
  - provider/model calls enabled
  - action execution authorized by classification
  - delegation proposal executed
  - cache-aware runtime routing active
  - production-ready routing
  - public beta or public release from this lane
- Ensure all new surfaces distinguish implemented, proposal-only, planned,
  blocked, partial, skipped, degraded, and mock-only states as applicable.
- Ensure new evidence/doc/UI fixtures avoid forbidden raw content.

Implementation guidance:
- Prefer extending existing product-language, operational maturity, route
  manifest, or documentation verifiers if they are the local pattern.
- Add one intentionally bad fixture/string in a focused test if the existing
  verifier pattern supports fixtures.
- Keep checks scoped so they do not create brittle unrelated failures.

Acceptance:
- Focused verifier catches at least one intentionally bad claim or fixture.
- Docs and UI copy preserve UAA authority boundaries.
- Foundation Gate and relevant focused tests pass or blockers are reported.
- Final summary names all behavior explicitly not added.
```
