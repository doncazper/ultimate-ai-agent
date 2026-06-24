# FCC-HEALTH-001 Self-Healing Recommendations To Inbox

Status: Implemented for first backend-owned recommendation read-model and
Action Inbox projection slice; broader signal adapters, decision receipts,
Evidence lifecycle events, CLI inspection, and conversion paths remain planned
or blocked until separately scoped.
Baseline: v0.104.0 / 0.104.0.
Primary surfaces: `/actions`, `/briefing`, `/evidence`, and local CLI
inspection.

## Purpose

FCC-HEALTH-001 turns system-health and product-friction signals into
reviewable recommendations in Action Inbox. It borrows the useful part of a
Hermes-style self-improving loop: the system can notice drift, missing proof,
broken checks, blocked-state confusion, and repeated friction. It does not
borrow hidden repair authority.

The product behavior is:

1. Detect a bounded signal from repo-local proof, private dogfood, route
   metadata, source readiness, UI friction, or memory quality posture.
2. Convert the signal into a safe recommendation candidate with refs,
   severity, scope, owner, missing proof, validation plan, rollback or
   safe-disable posture, and blocked authority.
3. Show the candidate in Action Inbox as `self_heal_recommendation`.
4. Let the operator approve, edit, reject, or defer the recommendation as
   review state only.
5. Convert an approved recommendation into a task candidate or patch-proposal
   candidate only through a later exact scoped lane.
6. Record every step in Evidence Timeline without changing code
   automatically.

## Current Implemented Slice

The current implementation adds a backend-owned `RecommendationCandidate`
contract in
`src/ultimate_ai_agent/core/control_center/health_recommendations.py` and
projects safe recommendation refs into Action Inbox as
`self_heal_recommendation` items. Those items are review material only. They
use `recommendation_review_only_no_execution_path`,
`proposal_only_no_execution_path`, blocked-authority refs, validation-plan
refs, missing-proof refs, expected-receipt refs, and conversion-option refs to
show what might be reviewed next.

The first bounded signals are source-readiness gaps, documentation currentness
drift, operational maturity proof gaps, and optional private dogfood friction
refs when supplied by a later harness. The current slice does not add
recommendation review routes, Evidence recommendation lifecycle events,
automatic task creation, patch proposal generation, CLI queue inspection, or
Morning Briefing health counters.

Current non-goals are explicit: no autonomous coding, no auto-apply patches,
no background self-repair, no scheduler authority, no provider/model calls, no
connector reads or writes, no shell execution, no browser automation, no hidden
context injection, no action execution, and no production authority.

## Dependencies

FCC-HEALTH-001 should stay behind:

- `FCC-BRIEFING-001` Morning Briefing and Today Plan V1.
- `FCC-INBOX-001` Action Inbox and Approval Envelope UX.
- `FCC-SOURCES-001` Source Readiness and Draft-only Inputs.
- `FCC-MEMORY-CRM-001` Professional Memory and CRM-lite Binding.
- `FCC-REVIEW-001` Evidence Narrative and Weekly CEO Review, if the first
  implementation needs weekly carry-forward copy.

The first implementation should reuse:

- Action Inbox lanes and approval-envelope read model.
- Evidence Timeline event grouping.
- Founder Loop storage/read model patterns.
- Operational maturity manifest rank language.
- Product language rules and raw-content denial checks.
- Existing verifier and documentation-integrity conventions.

## Implementation Readiness

The desired end state is close to implemented product behavior, not a vague
future roadmap. The safe near-term implementation target is a backend-owned
recommendation lane that detects bounded repo/product signals, creates
reviewable Action Inbox items, records receipts, and shows Evidence history.

The lane can start now if these prerequisites are treated as the hard floor:

- Action Inbox remains the review surface and already supports backend-owned
  envelopes, receipt visibility, and approve/edit/reject/defer decisions.
- Evidence Timeline remains the history surface and can add
  recommendation-created and recommendation-reviewed event groups.
- Morning Briefing can display counts and review links without adding
  background repair.
- Source readiness, Memory Review, route manifests, product-language checks,
  documentation integrity, and operational maturity outputs are consumed only
  as safe refs and bounded summaries.
- Governed Code patch proposals remain a separate later lane. FCC-HEALTH-001
  may create a patch-proposal candidate only after review, but it must not
  apply or generate code in the same step.

Prerequisites that may need to be completed before claiming FCC-HEALTH-001
done:

- Stable Action Inbox decision receipt storage for the new
  `self_heal_recommendation` kind.
- Evidence Timeline event support for recommendation lifecycle events.
- A safe signal-normalization layer that can summarize verifier/docs/UI/source
  issues without storing raw command output, raw logs, raw paths, or private
  content.
- Frontend card support for missing backend fields so mock/degraded data stays
  visibly non-authoritative.
- CLI or repo-local inspection parity for the recommendation queue and
  receipts.
- A focused verifier proving denied authority flags, raw-content denial,
  Action Inbox binding, Evidence binding, and docs/index alignment.

Do not wait for broad self-healing, provider/model calls, scheduler support,
connector runtime, or patch apply authority. Those are not prerequisites for
this lane and remain explicitly out of scope.

## Authority Boundary

FCC-HEALTH-001 has no autonomous coding, no auto-apply patches, and does not
add unrestricted
shell/subprocess execution, browser automation, connector reads or writes,
account sync, external task or CRM writes, provider/model calls, hidden context
injection, automatic memory writes, production authority, public beta,
distribution claims, scheduler authority, background repair, or plugin runtime
execution.

Recommendations are review material. Approval of a recommendation does not by
itself authorize a patch, command, connector action, task execution, memory
write, source fetch, or route mutation.

## Planned Contract Tasks

1. Add a `RecommendationCandidate` contract.
   - Suggested module:
     `src/ultimate_ai_agent/core/control_center/health_recommendations.py`.
   - Required fields:
     `contract_ref`, `recommendation_ref`, `kind`, `severity`,
     `lifecycle_state`, `safe_title`, `safe_summary`, `source_signal_refs`,
     `source_surface_refs`, `source_doc_refs`, `source_route_refs`,
     `source_test_refs`, `source_verifier_refs`, `evidence_refs`,
     `missing_proof_refs`, `blocked_authority_refs`, `owner_ref`,
     `scope_ref`, `impact_ref`, `validation_plan_refs`,
     `rollback_or_safe_disable_refs`, `expected_receipt_refs`,
     `conversion_option_refs`, `next_safe_action`, `created_at`,
     `updated_at`, `redaction_status`, and denied-authority flags.
   - `safe_title`, `safe_summary`, and `next_safe_action` are bounded and must
     not include raw logs, raw paths, raw prompts, raw responses, raw provider
     payloads, raw source bodies, usernames, hostnames, credentials, tokens,
     secrets, or environment dumps. `evidence_refs` must remain safe refs, not
     slash paths.

2. Define recommendation kinds.
   - `verifier_failure`
   - `documentation_currentness_drift`
   - `route_manifest_mismatch`
   - `api_contract_mismatch`
   - `frontend_ui_friction`
   - `blocked_state_confusion`
   - `source_readiness_gap`
   - `private_dogfood_feedback`
   - `memory_quality_issue`
   - `product_language_issue`
   - `operational_maturity_gap`
   - `release_truth_gap`

3. Define lifecycle states.
   - `detected`
   - `queued_for_review`
   - `reviewed_accepted`
   - `reviewed_edited`
   - `reviewed_rejected`
   - `reviewed_deferred`
   - `converted_to_task_candidate`
   - `converted_to_patch_proposal_candidate`
   - `stale`
   - `resolved_by_external_evidence`

4. Define severity and prioritization.
   - `info`: informative gap, no user-facing confusion.
   - `low`: minor copy, docs, or polish issue.
   - `medium`: repeated friction, stale proof, blocked-state confusion, or
     route/doc mismatch that affects operator trust.
   - `high`: safety boundary, product-language, route-manifest, or evidence
     mismatch that could cause unsupported claims.
   - No severity level grants execution or patch authority.

5. Define denied authority flags.
   - Required false flags:
     `auto_code_authorized`, `auto_apply_authorized`,
     `shell_execution_authorized`, `browser_automation_authorized`,
     `connector_write_authorized`, `connector_read_authorized`,
     `memory_write_authorized`, `context_injection_authorized`,
     `provider_model_call_authorized`, `task_execution_authorized`,
     `external_side_effect_authorized`, `production_authority_enabled`,
     and `public_release_claim_enabled`.

## Planned Signal Intake Tasks

6. Add verifier-failure signal conversion.
   - Input: safe refs to failed verifier/test lanes, not raw command output.
   - Output: one recommendation per stable verifier/test/scope tuple.
   - Required refs:
     `source_verifier_refs`, `source_test_refs`, `missing_proof_refs`,
     `validation_plan_refs`, and `evidence_refs`.
   - Example next safe action:
     "Review the failing verifier refs and decide whether to create a scoped
     fix task or patch proposal."

7. Add documentation-currentness drift conversion.
   - Input: safe refs to docs index drift, stale status language, missing
     cross-links, or product-truth mismatch.
   - Output: `documentation_currentness_drift` recommendation.
   - Required refs:
     currentness doc refs, product-truth refs, docs-index refs, and a
     validation plan that names documentation integrity.
   - Raw diff bodies and raw local paths remain blocked.

8. Add route/API manifest mismatch conversion.
   - Input: route inventory, OpenAPI, API manifest, route-status manifest, or
     release-surface inconsistency refs.
   - Output: `route_manifest_mismatch` or `api_contract_mismatch`
     recommendation.
   - Required refs:
     route refs, operation-id refs, manifest refs, verifier refs, and
     blocked authority refs.
   - The recommendation can ask for an API contract task; it cannot mutate a
     route.

9. Add frontend/UI-friction conversion.
   - Input: private dogfood friction refs, accepted UI tuning refs,
     accessibility issue refs, or local browser-smoke refs.
   - Output: `frontend_ui_friction` recommendation.
   - Required refs:
     surface refs, screenshot or visual-baseline refs where safe, dogfood refs,
     and next safe action.
   - The recommendation cannot edit UI directly.

10. Add blocked-state confusion conversion.
    - Input: mismatched blocked-state refs, missing denied-authority copy,
      unsupported completion labels, or mock/degraded state ambiguity.
    - Output: `blocked_state_confusion` or `product_language_issue`
      recommendation.
    - Required refs:
      product-language rule refs, route-status refs, UI surface refs, and
      expected blocked-state refs.

11. Add source-readiness gap conversion.
    - Input: source readiness read model states such as `blocked`, `missing`,
      `metadata_only`, `unavailable`, or `not_configured`.
    - Output: `source_readiness_gap` recommendation.
    - Required refs:
      source lane refs, missing contract refs, blocked authority refs, and
      source readiness evidence refs.
    - No connector runtime, account auth, polling, message fetch, or raw source
      import is authorized.

12. Add memory-quality issue conversion.
    - Input: reviewed memory quality refs for duplicate, conflict,
      stale/expired, low-confidence, missing evidence, or missing source.
    - Output: `memory_quality_issue` recommendation.
    - Required refs:
      memory candidate refs, reviewed recall refs where available, evidence
      refs, quality refs, stale/conflict refs, and next safe action.
    - The recommendation can point to Memory Review. It cannot write memory,
      delete memory, export memory, or inject context.

13. Add operational-maturity gap conversion.
    - Input: operational maturity manifest gaps, rank mismatch refs, missing
      proof refs, or maturity scorecard review refs.
    - Output: `operational_maturity_gap` recommendation.
    - Required refs:
      maturity item refs, current rank refs, missing proof refs, and validation
      plan refs.
    - No rank promotion occurs from the recommendation itself.

## Planned Queue And Storage Tasks

14. Add deterministic recommendation refs.
    - Generate refs from `kind`, `scope_ref`, `owner_ref`, and stable signal
      refs.
    - Do not include raw source text or raw local paths in refs.
    - Duplicate signals should replay the same recommendation ref where the
      scope and evidence are unchanged.

15. Add recommendation deduping.
    - Group repeat failures by stable signal refs.
    - Preserve first-seen and latest-seen timestamps.
    - Preserve each supporting evidence ref.
    - Do not collapse distinct authority-boundary problems into one generic
      recommendation.

16. Add ranking and grouping.
    - Rank by severity, operator impact, safety risk, stale age, missing proof,
      repeated occurrence count, and loop relevance.
    - Group for Action Inbox by:
      `needs_review`, `safety_or_claim_risk`, `proof_gap`, `ui_friction`,
      `source_readiness`, `memory_quality`, `deferred`, and `rejected`.
    - Every group needs a safe count and a next safe action.

17. Add storage/read model.
    - Reuse Founder Loop local storage patterns unless a narrower existing
      store is a better fit during implementation.
    - Persist recommendation envelopes, decision receipts, replay posture, and
      Evidence Timeline refs.
    - Store safe summaries and refs only.

## Planned Action Inbox Tasks

18. Add Action Inbox kind `self_heal_recommendation`.
    - The item must render as proposal/review state, not execution state.
    - Required approval-envelope fields:
      kind, exact scope, risk, side-effect class, owner, severity, evidence
      refs, expected receipt refs, blocked authority refs, validation plan refs,
      rollback or safe-disable refs, expiry/staleness, idempotency ref, and
      next safe action.

19. Add review decisions.
    - Supported decisions:
      `accept`, `edit`, `reject`, and `defer`.
    - Mutating decision routes must use the repo idempotency pattern.
    - Decision receipts must state what changed:
      recommendation review state only.
    - Decision receipts must state what did not change:
      no code, connector, memory, route, shell, browser, task, or external
      system changed.

20. Add conversion posture.
    - Accepted recommendations may expose conversion options:
      `create_local_task_candidate` and `create_patch_proposal_candidate`.
    - Conversion requires a later exact scoped lane and cannot happen
      automatically.
    - A patch proposal candidate must bind to governed Code workbench refs and
      validation-plan refs before any later apply lane exists.

21. Add stale and replay posture.
    - Recommendations need expiry or recheck posture.
    - If the underlying signal is resolved, mark the recommendation stale or
      resolved by evidence instead of silently deleting it.
    - Idempotency replay must return the prior receipt for the same payload and
      reject conflicting payloads.

## Planned Evidence Tasks

22. Add Evidence Timeline events.
    - `self_heal_recommendation_created`
    - `self_heal_recommendation_reviewed`
    - `self_heal_recommendation_deferred`
    - `self_heal_recommendation_rejected`
    - `self_heal_recommendation_marked_stale`
    - `self_heal_recommendation_converted_to_task_candidate`
    - `self_heal_recommendation_converted_to_patch_proposal_candidate`

23. Add readable Evidence answers.
    - What signal was detected?
    - What recommendation was created?
    - What evidence and missing proof refs supported it?
    - What decision was recorded?
    - What receipt was created?
    - What changed?
    - What did not change?
    - What remains blocked?
    - What is the next safe action?

24. Add weekly carry-forward posture.
    - Deferred or stale recommendations may be summarized in Weekly Review as
      safe refs only.
    - Weekly Review must distinguish accepted, edited, rejected, deferred,
      stale, resolved, blocked, and missing-proof states.

## Planned UI Tasks

25. Action Inbox card.
    - Show severity, kind, surface, owner, scope, evidence refs, missing proof,
      validation plan, blocked authority, expected receipt, and next safe
      action.
    - Use the existing approval-envelope and receipt-visibility cards.
    - Do not show auto-fix, run, apply, fetch, sync, or repair controls.

26. Morning Briefing health summary.
    - Show counts for high-risk recommendations, proof gaps, UI friction,
      source-readiness gaps, and memory-quality issues.
    - Each count links to Action Inbox review state, not execution.

27. Evidence view.
    - Add grouped recommendation history with safe refs and receipts.
    - Do not render raw verifier output or raw logs.

28. Mock/degraded fallback behavior.
    - If backend recommendation fields are missing, UI must mark the card
      non-authoritative and hide decision/conversion controls.
    - Fallback data must not claim backend ownership, review eligibility,
      task conversion readiness, patch readiness, or receipt-recorded state.

## Planned CLI Tasks

29. Add CLI or repo-local script inspection.
    - Planned command or script should inspect recommendation queue, decision
      receipts, and Evidence refs without using the UI.
    - Output must be safe-ref and bounded-summary only.
    - CLI parity must prove the UI is not the only operator surface.

30. Add local verification command.
    - Planned verifier:
      `scripts/verify_fcc_health_001_self_healing_recommendations.py`.
    - It should check contracts, docs links, denied authority flags, route
      posture if routes exist, Evidence event names, Action Inbox envelope
      kind, frontend non-authority copy, and raw-content denial.

## Planned Tests

31. Contract tests.
    - Validate required fields for `RecommendationCandidate`.
    - Reject raw/private markers in refs and summaries.
    - Reject true denied-authority flags.
    - Require evidence refs, missing-proof refs or explicit none refs,
      validation-plan refs, expected receipt refs, and blocked authority refs.

32. Signal conversion tests.
    - Verifier failure converts to safe recommendation without raw logs.
    - Docs drift converts to currentness recommendation.
    - Route/API mismatch converts to manifest recommendation.
    - UI friction converts to review recommendation.
    - Source readiness gap converts without connector authority.
    - Memory quality issue converts without memory write or context injection.

33. Queue tests.
    - Duplicate signal refs dedupe.
    - Distinct authority-boundary issues remain separate.
    - Ranking is deterministic.
    - Stale/resolved posture does not delete audit history.

34. Action Inbox tests.
    - `self_heal_recommendation` appears in the expected review lane.
    - Approval envelope includes severity, scope, evidence, validation,
      rollback/safe-disable, expected receipt, and blocked authority refs.
    - Accept/edit/reject/defer are idempotent and receipt-backed.
    - Accept does not execute a task or patch.
    - Conversion options remain disabled unless the exact later lane exists.

35. Evidence tests.
    - Recommendation creation and review events appear in Evidence Timeline.
    - Evidence answers what changed and what remained blocked.
    - Raw logs, raw paths, raw prompts, raw provider payloads, credentials,
      tokens, usernames, hostnames, and environment dumps are denied.

36. Frontend tests.
    - Action Inbox card renders recommendation fields and blocked authority.
    - Morning Briefing renders health counts as review links only.
    - Missing backend ownership hides controls.
    - No copy says auto-fix, self-repair completed, code changed, patch
      applied, connector synced, or production ready.

37. Verifier and broader checks.
    - Add the focused milestone verifier.
    - Update documentation integrity only where links change.
    - Run OpenAPI/API manifest checks if routes are added.
    - Run frontend checks if UI changes.
    - Run `git diff --check`.

## Suggested Implementation Slices

1. Contract-only recommendation model and tests.
2. Storage/read-model queue over static safe signals.
3. Evidence Timeline event refs for created/reviewed recommendations.
4. Action Inbox read-model item and approval envelope kind.
5. Decision receipt routes for accept/edit/reject/defer.
6. Morning Briefing and Evidence UI display.
7. Signal converters for verifier/docs/route/UI/source/memory inputs.
8. Conversion posture to task candidate or patch-proposal candidate.
9. CLI inspection.
10. Verifier, docs, product-truth, and release-surface alignment.

## Current Slice Gate

The first implemented slice is done when:

- `RecommendationCandidate` denies every authority flag and rejects unsafe
  payload content.
- Source-readiness, documentation currentness, operational maturity, and
  optional private-friction refs can become safe recommendation candidates.
- Action Inbox includes backend-owned `self_heal_recommendation` items with no
  approval requirement and no execution path.
- Health recommendation fields are typed for the Control Center as optional
  display/read-model fields.
- `scripts/verify_fcc_health_001_self_healing_recommendations_to_inbox.py`
  and
  `tests/test_fcc_health_001_self_healing_recommendations_to_inbox.py` prove
  the boundary.

## Full Done Gate

FCC-HEALTH-001 is done only when:

- Recommendations can be generated from safe verifier, docs-currentness,
  route/API, UI-friction, source-readiness, private-feedback, and
  memory-quality signals.
- Recommendations appear in Action Inbox as backend-owned
  `self_heal_recommendation` envelopes.
- Review decisions are idempotent, receipt-backed, and visible in Evidence.
- Recommendations can be converted only to task or patch-proposal candidates
  after review, with no automatic code or patch behavior.
- Morning Briefing and Evidence summarize recommendation state using safe refs.
- CLI or repo-local inspection can show the same recommendation state.
- Tests and verifiers prove raw-content denial and denied authority posture.
- Docs distinguish implemented, planned, blocked, stale, missing-proof,
  deferred, rejected, and proposal-only states.

## Verification Commands

Current slice checks:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_health_001_self_healing_recommendations_to_inbox.py -q
.venv/bin/python scripts/verify_fcc_health_001_self_healing_recommendations_to_inbox.py
.venv/bin/python scripts/verify_operational_maturity.py
.venv/bin/python scripts/verify_documentation_integrity.py
make frontend-check
git diff --check
```

OpenAPI checks are only required if a later slice adds or changes routes.
