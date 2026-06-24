# FCC-HEALTH-001 Self-Healing Recommendations To Inbox

You are working in the `doncazper/ultimate-ai-agent` repo.

Your task is to implement `FCC-HEALTH-001 Self-Healing Recommendations To
Inbox` as a close-to-real product lane with safety preserved. Do not stop at
documentation. Build the safe implementation path as far as the current repo
can support, and clearly report any prerequisite that blocks a later slice.

This is the governed version of Hermes-style self-healing: the system may
detect issues and propose recommendations, but it must not auto-code,
auto-apply, run broad shell commands, fetch connectors, write memory, inject
context, or silently repair itself.

## First Read

Before editing, read:

- `AGENTS.md`
- `docs/control_center/FCC_HEALTH_001_SELF_HEALING_RECOMMENDATIONS_TO_INBOX.md`
- `docs/control_center/FCC_INBOX_001_APPROVAL_ENVELOPE_UX.md`
- `docs/control_center/FCC_V1_002_ACTION_INBOX_STATE_MACHINE.md`
- `docs/control_center/FCC_BRIEFING_001_MORNING_BRIEFING_TODAY_PLAN.md`
- `docs/control_center/FCC_SOURCES_001_SOURCE_READINESS_DRAFT_ONLY_INPUTS.md`
- `docs/control_center/FCC_MEMORY_CRM_001_PROFESSIONAL_MEMORY_CRM_LITE_BINDING.md`
- `docs/control_center/FCC_V1_006_EVIDENCE_TIMELINE_PRODUCTIZATION.md`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
- `docs/kanban/founder_command_center_board.md`
- `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`

Then inspect the current implementation patterns for:

- Founder Loop storage/read models:
  `src/ultimate_ai_agent/core/storage/founder_loop.py`
- Founder Loop API routes:
  `src/ultimate_ai_agent/api/founder_loop.py`
- Action Inbox contracts and decisions:
  `src/ultimate_ai_agent/core/control_center/actions.py`
  and related planning/action decision modules.
- Morning Briefing and Today summaries.
- Evidence Timeline grouping.
- API manifest/route status/OpenAPI conventions.
- Existing tests for Action Inbox, Morning Briefing, Evidence Timeline,
  product language, operational maturity, and Founder Loop storage.

## Product Goal

Make system-health and product-friction signals become backend-owned
`self_heal_recommendation` review items in Action Inbox. Each recommendation
must include safe refs, severity, scope, owner, evidence, missing proof,
validation plan refs, rollback or safe-disable posture, expected receipt refs,
blocked authority refs, and a next safe action.

The user should be able to inspect recommendations in Action Inbox, review
them with backend-owned accept/edit/reject/defer decisions, see receipts and
Evidence Timeline history, and inspect the same state through a CLI or
repo-local script.

Approved recommendations may expose conversion posture for a local task
candidate or governed patch-proposal candidate, but conversion must remain
review-gated and must not apply code automatically.

## Non-Negotiable Boundaries

Do not implement:

- autonomous coding by the product runtime
- automatic patch generation/application
- background self-repair
- scheduler-driven repair
- broad shell/subprocess execution
- browser automation
- connector reads or writes
- account auth or account sync
- external task or CRM writes
- provider/model calls
- hidden context injection
- automatic memory writes
- memory delete/export execution
- plugin runtime execution
- public beta, public distribution, production readiness, or production
  authority claims

The implementation work may edit repo code in this Codex session. The product
behavior being implemented must not give UAA runtime authority to edit/apply
code automatically.

## Stage 0 - Prerequisite Audit

Produce a short implementation audit before coding:

1. Confirm whether Action Inbox decision receipt storage can support a new
   `self_heal_recommendation` kind.
2. Confirm whether Evidence Timeline can add recommendation lifecycle events.
3. Confirm where a safe signal-normalization layer should live.
4. Confirm which API routes can be reused and whether new routes are needed.
5. Confirm which frontend components can reuse approval-envelope and
   receipt-visibility cards.
6. Confirm the CLI or repo-local script pattern to use for inspection parity.
7. List exact files to modify first.

If a prerequisite is missing but small and directly required for
FCC-HEALTH-001, build it. If a prerequisite would require broad authority or a
separate milestone, keep it blocked and implement the safe smaller slice.

## Stage 1 - Contract And Safe Signal Model

Implement a `RecommendationCandidate` contract, likely in:

`src/ultimate_ai_agent/core/control_center/health_recommendations.py`

Required fields:

- `contract_ref`
- `recommendation_ref`
- `kind`
- `severity`
- `lifecycle_state`
- `safe_title`
- `safe_summary`
- `source_signal_refs`
- `source_surface_refs`
- `source_doc_refs`
- `source_route_refs`
- `source_test_refs`
- `source_verifier_refs`
- `evidence_refs`
- `missing_proof_refs`
- `blocked_authority_refs`
- `owner_ref`
- `scope_ref`
- `impact_ref`
- `validation_plan_refs`
- `rollback_or_safe_disable_refs`
- `expected_receipt_refs`
- `conversion_option_refs`
- `next_safe_action`
- `created_at`
- `updated_at`
- `redaction_status`
- denied-authority flags

Supported recommendation kinds:

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

Supported lifecycle states:

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

Denied-authority flags must exist and remain false:

- `auto_code_authorized`
- `auto_apply_authorized`
- `shell_execution_authorized`
- `browser_automation_authorized`
- `connector_write_authorized`
- `connector_read_authorized`
- `memory_write_authorized`
- `context_injection_authorized`
- `provider_model_call_authorized`
- `task_execution_authorized`
- `external_side_effect_authorized`
- `production_authority_enabled`
- `public_release_claim_enabled`

Validation must reject raw/private markers including raw logs, raw local paths,
raw prompts, raw responses, raw provider payloads, raw source bodies,
usernames, hostnames, credentials, tokens, secrets, environment dumps,
unredacted transcripts, and full command output.

## Stage 2 - Signal Converters

Add deterministic safe signal conversion helpers for:

1. verifier/test failures
2. documentation currentness drift
3. route/API manifest mismatch
4. frontend/UI friction
5. blocked-state confusion
6. source-readiness gaps
7. private dogfood feedback
8. memory-quality issues
9. operational-maturity gaps
10. release-truth gaps

Converters must use safe refs and bounded summaries only. They must not store
raw command output, raw diffs, raw logs, raw paths, source bodies, account
identifiers, or private content.

Each converter should produce deterministic refs from stable safe inputs so
duplicate signals can be deduped.

## Stage 3 - Queue, Dedupe, Ranking, And Storage

Add a backend-owned recommendation queue/read model.

Requirements:

- deterministic recommendation refs
- dedupe by stable signal refs
- first-seen and latest-seen timestamps
- repeated occurrence count
- severity ranking
- missing-proof grouping
- stale/resolved posture without silent deletion
- safe summaries and refs only
- blocked authority refs on every item
- conversion posture only, no execution

Expected groups:

- `needs_review`
- `safety_or_claim_risk`
- `proof_gap`
- `ui_friction`
- `source_readiness`
- `memory_quality`
- `deferred`
- `rejected`

Prefer existing Founder Loop storage patterns. If routes are added, update
route metadata, OpenAPI/API manifest, route status, side-effect class, auth,
idempotency posture, release surface, and tests.

## Stage 4 - Action Inbox Binding

Add Action Inbox kind:

`self_heal_recommendation`

The item must render as proposal/review state, not execution state.

Each Action Inbox item must expose:

- recommendation kind
- severity
- exact scope
- owner
- risk class
- side-effect class
- approval requirement
- evidence refs
- missing proof refs
- validation-plan refs
- rollback or safe-disable refs
- expected receipt refs
- blocked authority refs
- stale/recheck posture
- idempotency ref
- next safe action

Add backend-owned review decisions if they are not already covered by existing
Action Inbox decision routes:

- accept
- edit
- reject
- defer

Mutating decisions must require idempotency. Same key + same payload replays
the prior receipt. Same key + different payload is rejected.

Decision receipts must state:

- what recommendation was reviewed
- what decision was recorded
- what evidence/missing-proof refs were used
- what receipt was created
- what changed: recommendation review state only
- what did not change: no code, patch, connector, memory, route, shell,
  browser, task execution, or external system changed
- what remains blocked

## Stage 5 - Evidence Timeline

Add Evidence Timeline event support for:

- `self_heal_recommendation_created`
- `self_heal_recommendation_reviewed`
- `self_heal_recommendation_deferred`
- `self_heal_recommendation_rejected`
- `self_heal_recommendation_marked_stale`
- `self_heal_recommendation_converted_to_task_candidate`
- `self_heal_recommendation_converted_to_patch_proposal_candidate`

Evidence must answer:

- what signal was detected
- what recommendation was created
- what evidence and missing proof supported it
- what decision was recorded
- what receipt was created
- what changed
- what did not change
- what remains blocked
- what the next safe action is

Do not include raw verifier logs, raw command output, raw paths, raw diffs, or
private content in durable Evidence.

## Stage 6 - Morning Briefing, Action Inbox, Evidence UI

Wire frontend UI only after backend/read-model fields exist.

Action Inbox:

- Render `self_heal_recommendation` cards using existing approval-envelope and
  receipt-visibility grammar.
- Show severity, kind, source surface, owner, scope, evidence refs, missing
  proof, validation plan, blocked authority, expected receipt, and next safe
  action.
- Do not show auto-fix, repair, run, apply, fetch, sync, or execute controls.

Morning Briefing:

- Show counts for high-risk recommendations, proof gaps, UI friction,
  source-readiness gaps, and memory-quality issues.
- Counts must link to review posture, not execution.

Evidence:

- Show recommendation history grouped with safe refs and receipts.
- Do not render raw command output or logs.

Mock/degraded fallback:

- If backend ownership or required fields are missing, mark data
  non-authoritative.
- Hide decision/conversion controls.
- Do not claim review eligibility, task conversion readiness, patch readiness,
  receipt-recorded state, or backend proof.

## Stage 7 - Conversion Posture

Approved recommendations may expose conversion options:

- `create_local_task_candidate`
- `create_patch_proposal_candidate`

Conversion must remain a candidate/proposal posture unless a separate exact
lane already exists. Do not add patch apply, code generation, shell execution,
or task execution.

Patch-proposal candidates must bind to governed Code workbench refs,
validation-plan refs, expected receipt refs, and rollback/safe-disable posture.

## Stage 8 - CLI / Repo-Local Inspection

Add CLI or repo-local script inspection parity for:

- recommendation queue
- recommendation details
- decision receipts
- Evidence refs
- stale/resolved posture

Output must be safe-ref and bounded-summary only.

The UI must not be the only operator surface.

## Stage 9 - Verifier, Tests, Docs

Add focused verifier:

`scripts/verify_fcc_health_001_self_healing_recommendations.py`

Add focused tests, likely:

`tests/test_fcc_health_001_self_healing_recommendations.py`

Test coverage must include:

- contract required fields
- raw/private marker denial
- denied-authority flags remain false
- each signal converter creates a safe recommendation
- duplicate signal refs dedupe
- ranking is deterministic
- Action Inbox item appears in the expected review lane
- approval envelope contains severity/scope/evidence/validation/rollback/
  expected receipt/blocked authority refs
- accept/edit/reject/defer are idempotent and receipt-backed
- accept does not execute a task or patch
- conversion options remain proposal-only
- Evidence events are recorded
- Morning Briefing shows review counts only
- frontend missing-backend fallback is non-authoritative
- product copy makes no auto-fix, self-repair completed, patch applied,
  connector synced, public beta, or production-ready claims

Update only the smallest necessary docs and indexes:

- `docs/control_center/FCC_HEALTH_001_SELF_HEALING_RECOMMENDATIONS_TO_INBOX.md`
- `docs/kanban/founder_command_center_board.md`
- `docs/DOCUMENTATION_INDEX.md`
- `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`, if implementation truth
  changes
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`, if routes/UI behavior
  changes
- route/OpenAPI/API manifest docs if routes are added

## Done Gate

Do not call FCC-HEALTH-001 implemented until all of this is true:

- Safe signal converters exist for verifier, docs-currentness, route/API,
  UI-friction, source-readiness, private-feedback, and memory-quality signals.
- Recommendations are backend-owned `self_heal_recommendation` Action Inbox
  envelopes.
- Review decisions are idempotent, receipt-backed, and visible in Evidence.
- Recommendations can become task or patch-proposal candidates only after
  review.
- No automatic code generation, patch apply, shell execution, connector
  runtime, memory write, context injection, provider/model call, or external
  side effect exists.
- Morning Briefing and Evidence summarize recommendation state using safe refs.
- CLI or repo-local inspection shows the same recommendation state.
- Tests and verifiers prove raw-content denial and denied authority posture.
- Docs distinguish implemented, planned, blocked, stale, missing-proof,
  deferred, rejected, and proposal-only states.

If some done-gate item cannot be safely completed in the current pass, still
implement the earlier safe slices and leave the remaining work explicitly
blocked with file-level evidence and next safe actions.

## Verification Commands

Run focused checks first:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_health_001_self_healing_recommendations.py -q
.venv/bin/python scripts/verify_fcc_health_001_self_healing_recommendations.py
```

Then run the affected existing lanes:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_inbox_001_approval_envelope_ux.py tests/test_founder_loop_storage_actions.py tests/test_founder_loop_storage_briefing.py tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/verify_operational_maturity.py
.venv/bin/python scripts/verify_documentation_integrity.py
```

If routes are added:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
```

If frontend changes:

```bash
make frontend-check
.venv/bin/python scripts/verify_control_center_frontend.py
```

Always finish with:

```bash
git diff --check
```

## Final Response Format

Report:

1. Summary of implemented behavior.
2. Files changed.
3. Routes/models/storage/UI/CLI added or updated.
4. Tests and verifiers run, with results.
5. Prerequisites satisfied.
6. Remaining blocked prerequisites, if any.
7. Authority boundaries preserved.
8. Capabilities still blocked.
9. Next safe follow-up.
