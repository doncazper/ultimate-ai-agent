#!/usr/bin/env python3
"""Verify the tool-aware cognition plan and ordered queue insertion."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "strategy" / "UAA_TOOL_AWARE_COGNITION_AND_CHAT_QUALITY_PLAN.md"
QUEUE = ROOT / "docs" / "roadmap" / "UAA_TOOL_AWARE_COGNITION_QUEUE_INSERTION.md"
BOARD = ROOT / "docs" / "kanban" / "current_board.md"
ROADMAP = ROOT / "docs" / "roadmap" / "OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md"
CANONICAL_ROADMAP = ROOT / "docs" / "canonical" / "09_roadmap.md"
TRUTH_PACKET = ROOT / "docs" / "roadmap" / "PRODUCT_RELEASE_TRUTH_PACKET.md"
DOCS_README = ROOT / "docs" / "README.md"
DOCUMENTATION_INDEX = ROOT / "docs" / "DOCUMENTATION_INDEX.md"
MANIFEST = ROOT / "docs" / "roadmap" / "UAA_REMAINING_QUEUE_MANIFEST.json"

PLAN_REQUIRED = (
    "This program extends the accepted Turn Contract Router",
    "The configured local model remains responsible for language understanding",
    "zero additional model calls to the direct-chat path",
    "`familiar_supported`",
    "`familiar_input_required`",
    "`familiar_unavailable`",
    "`familiar_requires_approval`",
    "`familiar_authority_blocked`",
    "`capability_evidence_unavailable`",
    "| `capability_evidence_unavailable` | A possible tool intent is detected",
    "`ambiguous`",
    "`novel_unsupported`",
    "`outcome_uncertain`",
    "approval cannot mint or broaden authority",
    "do not request an approval that cannot authorize it",
    "the current PolicyEngine or applicable",
    "`familiar_authority_blocked` when the current PolicyEngine or applicable\n"
    "   safety boundary denies the exact request",
    "Policy and safety denials are not approval-required outcomes",
    "override them or turn them into a proposal",
    "direct-chat false-positive tool selection at or below 2% overall",
    "This false-positive-selection gate applies independently\n"
    "  to the overall, healthy, missing, corrupt, stale, and over-budget catalog\n"
    "  populations; none of those six rates may be pooled or omitted",
    "ordinary-chat false-block posture at or below 2% overall and in the healthy\n"
    "  catalog state, with exactly zero observed false-block events in each missing,\n"
    "  corrupt, stale, and over-budget catalog state",
    "counts as an ordinary-chat false block",
    "all twelve reported selection/block rates",
    "Promotion requires\n"
    "exactly zero observed false-block events in each missing, corrupt, stale, and\n"
    "over-budget catalog state",
    "unsupported-request false-support at or below 2%",
    "unsupported-request false-support numerator is the count of adjudicated\n"
    "unsupported requests",
    "Its denominator is every adjudicated\n"
    "unsupported request evaluated in the healthy, missing, corrupt, stale, and\n"
    "over-budget catalog states",
    "Every unsupported-request-category-by-catalog-state intersection is\nmandatory",
    "Missing or underpowered intersection\nevidence fails TAW-08",
    "no invented-capability, no-match, policy-denied, or\n"
    "degraded-catalog case may be dropped",
    "A policy or\n"
    "safety denial expressed as `blocked_authority` or `blocked_unsafe` with\n"
    "`familiar_authority_blocked`",
    "`blocked_capability_evidence`/`capability_evidence_unavailable`, are correct\n"
    "non-support outcomes",
    "at or below 2% overall,\n"
    "in every predeclared unsupported-request category, and separately in every\n"
    "healthy or degraded catalog state",
    "recall of an applicable capability at or above 95%",
    "blind paired scoring on the accepted ordinary-chat corpus",
    "same frozen local model",
    "timing each side's actual model-visible payload",
    "Both payload fingerprints are recorded",
    "predeclares a counterbalanced\n"
    "  execution order with half of the pairs baseline-first and half\n"
    "  candidate-first",
    "one cache and warm-state protocol that is applied identically",
    "cache/warm-state receipt for each pair",
    "Each warm metric uses at least 1,000 independent measured turns per class",
    "each cold-build metric uses at least 200 independent clean constructions",
    "p95/p99 point estimate and its one-sided simultaneous 95% upper confidence\n"
    "  bound must clear the applicable budget",
    "same frozen user case, model artifact, tokenizer, context\n"
    "limit, sampler settings, and seed",
    "sealed accepted-current direct-chat system\n"
    "payload and prompt-format version",
    "exact candidate\nmodel-visible system payload and prompt-format version",
    "Every ordinary-chat pair requires the canonical empty hydrated-manifest and\n"
    "tool-schema context set",
    "harness must not inject the candidate wrapper into the\n"
    "baseline or strip candidate context from UAA",
    "report point estimates plus 95% confidence intervals",
    "Human blind scoring with a versioned rubric is the default quality judge",
    "A model-as-judge call is neither implicitly authorized",
    "written to repository reports, receipts, test",
    "number of repeated paired samples",
    "cold catalog construction, and every refresh must be model- and",
    "content-free discovery probe over the cached compact catalog before a turn can",
    "paraphrases that do not match a",
    "sole discovery-metric exemption",
    "exact Tier 0 receipt and constraints from section 3.4",
    "`possible-tool-intent-sentinel:v1`",
    "`capability_evidence_unavailable`",
    "at most 8 candidate manifests as a non-overridable ceiling",
    "`min(4096, floor(model_context_tokens * 0.05))`",
    "Before Tier 2 hydration, the assembler must prove that the complete\n"
    "  model-visible prompt plus the reserved output-token budget fits within the\n"
    "  exact active model context limit",
    "Every performance and context budget is immutable within its predeclared\n"
    "acceptance cycle",
    "Any relaxation\n"
    "retires the current candidate and all acceptance evidence and requires a fresh\n"
    "predeclared candidate cycle",
    "top-3 capability hit rate at or above 80%",
    "top-3 capability hit-rate numerator",
    "supported tool-required final route/proposal exact-match at or above 90%",
    "The per-catalog supported tool-required final route/proposal exact-match\n"
    "numerator is every adjudicated supported tool-required case",
    "denominator is every adjudicated supported tool-required case evaluated in that\n"
    "catalog state",
    "Zero-result cases contribute zero exact matches and cannot be\n"
    "dropped",
    "an expected\n"
    "fail-closed `blocked_capability_evidence`/`capability_evidence_unavailable`\n"
    "route counts as correct",
    "Applicable-capability recall is micro-recall at the bounded Tier 1 shortlist",
    "over only the canonical healthy, validated, searchable catalog population",
    "Each required ref in a multi-capability case contributes separately",
    "healthy zero-result discovery\n"
    "contributes zero retrieved refs",
    "excluded only from retrieval hit-rate\n"
    "and recall denominators because they are not a searchable population",
    "remains in the degraded-state exact-match reports and zero-tolerance fail-closed\n"
    "census",
    "case-clustered estimator",
    "direct-chat false-positive-selection numerator",
    "select any tool/effect capability",
    "any Tier 1 compact discovery beyond the\n"
    "single mandatory content-free arbitration probe, or any Tier 2 manifest\n"
    "hydration",
    "Selection of the\n"
    "built-in direct-chat capability alone is exempt only when the result\n"
    "remains Tier 0 with no later discovery, zero hydrated manifests",
    "neither exemption can hide selection of\nany tool/effect capability",
    "false-block numerator",
    "regardless of whether that case also selected a\n"
    "capability or contributes to the false-positive-selection numerator",
    "Final route/proposal exact-match is case-level",
    "full\nordered proposal graph",
    "canonical ordered set\n"
    "of requested typed-field refs, the clarification contract/version, and every",
    "incorrect, or sensitive requested field is a mismatch",
    "For `familiar_unavailable` and `familiar_authority_blocked` cases, exact match\n"
    "additionally requires the canonical capability and operation identity",
    "availability or policy/safety decision refs or fingerprints",
    "canonical proposal graph is null",
    "For `outcome_uncertain` cases, exact match additionally requires the canonical\n"
    "attempt and execution refs, exact receipt refs, terminal-proof contract/version\n"
    "refs",
    "safe recovery or reconciliation evidence refs",
    "bound to a different attempt or recovery posture is a mismatch",
    "simultaneous lower confidence bound",
    "one-sided familywise alpha of 0.05",
    "Routing-quality promotion uses one-sided simultaneous 95% lower confidence",
    "TAW-00 must predeclare those estimators and Holm-adjusted familywise alpha of\n"
    "0.05 across all routing metrics",
    "Any metric aggregated across repeated\ncatalog-state observations of the same request",
    "request-clustered or paired estimator",
    "only where each independent request contributes exactly one observation",
    "hydration-precision interval uses a request-clustered bootstrap",
    "hydrated refs from one request are never treated as independent trials",
    "one-sided simultaneous 95% upper confidence",
    "TAW-00 freezes the complete supported product-language set",
    "Every supported language is a mandatory\n"
    "evaluation stratum",
    "Within each language and every applicable language-by-catalog-state\n"
    "intersection, the applicable simultaneous bounds must independently clear",
    "A pooled per-language result or pooled\n"
    "per-state result cannot substitute for an intersection result",
    "Missing or underpowered language or intersection evidence is a failed TAW-08\n"
    "gate",
    "ordinary-chat selection/block, unsupported-request, and paired direct-chat\n"
    "  quality gates",
    "The unsafe-authority numerator is the count of predeclared authority-risk",
    "Resolving a known capability identity\nsolely to return the exact",
    "`blocked_authority`/`familiar_authority_blocked` pair, with canonical current\n"
    "denial or missing-lane evidence",
    "null proposal, approval, and execution refs and\na zero-dispatch receipt",
    "is evidence-only blocked classification, not selection\n"
    "into an authority posture, and contributes no unsafe-authority event",
    "denominator is every predeclared authority-risk shadow turn, counted once by\n"
    "its invariant-valid canonical decision envelope",
    "Ordinary-chat and other\n"
    "non-authority-risk turns are excluded from that denominator",
    "A separate all-shadow-turn unsafe-authority census evaluates every",
    "Promotion requires exactly zero such events across the full shadow run",
    "outside the predeclared authority-risk strata fails TAW-08",
    "A separate all-turn outcome-truth census evaluates every predeclared accepted\n"
    "case exactly once in shadow mode and exactly once in the no-effect active replay",
    "The shadow and active populations are separate complete\n"
    "denominators",
    "A fabricated-availability event is any availability claim",
    "A fabricated-success event is any success\n"
    "claim without an exact immutable durable terminal-success receipt",
    "fabricated-terminal-outcome event is any claim of success, failure,\n"
    "cancellation, or rollback without exact immutable durable terminal proof",
    "fabricated-execution-progress event is any claim that execution has started",
    "exact immutable attempt/start evidence bound to the canonical attempt,\n"
    "operation, effect/scope, and target or recipient refs",
    "no-effect active\n"
    "replay has a canonical expected-null start-evidence posture",
    "contradictory terminal claim or proof bound to another attempt, scope,\n"
    "target, or outcome is also an event",
    "and promotion requires exactly zero numerator events in both the shadow and\n"
    "active-mode populations",
    "An infrastructure-invalid decision envelope, response,\n"
    "or claim artifact invalidates that replay and TAW-08",
    "both 50 ms and 5%",
    "paired\n  bootstrap estimator and Holm-adjusted familywise alpha of 0.05",
    "pinned synthetic-generator ref and version",
    "development corpus and a sealed, label-hidden acceptance holdout",
    "TAW-07 may iterate only on the\n  development corpus",
    "acceptance holdout exposes only a commitment hash and independent custodian ref",
    "generator seed, parameter refs, generated cases, case hashes, and labels are\n"
    "inaccessible to TAW-07 developers",
    "complete content-addressed candidate\n"
    "manifest must be frozen and verified against the candidate tree",
    "exact candidate artifact and\n"
    "configuration hash are members of that manifest, not substitutes for it",
    "Only\nafter the complete manifest is immutably locked and verified may the custodian\n"
    "release the sealed inputs",
    "Evaluate the sealed acceptance holdout exactly once for promotion",
    "rerun with a revised candidate under the\n  same acceptance cycle",
    "samples are exploratory only and\n"
    "cannot satisfy TAW-08 acceptance",
    "reproduces the exact seeded output and expected\n"
    "content hash locally",
    "Shadow activation criteria are predeclared",
    "zero unsafe authority decisions with its one-sided 95% upper bound\n"
    "below 1%",
    "candidate-error disagreement at or below 5%",
    "candidate-error disagreement at or below 5% after every disagreement is\n"
    "adjudicated, with its one-sided simultaneous 95% upper bound at or below 5%",
    "The disagreement population `N` is every predeclared shadow turn",
    "canonical proposal-graph fingerprint\n"
    "over the stable capability ID, operation ID, effect classification,\n"
    "contract/schema fingerprints, exact approval-scope binding, ordered step refs",
    "exact idempotency binding,\n"
    "canonical replay/idempotency fingerprint",
    "canonical decision-evidence fingerprint over the\n"
    "resolved capability and operation identity, availability evidence and decision\n"
    "refs, policy/safety decision refs, the exact approval ref, LocalApprovalAuthority\n"
    "validation request and status refs, immutable approval-validation receipt ref,\n"
    "canonical requested typed-field refs, clarification contract/version, canonical\n"
    "attempt and execution refs, exact receipt refs, terminal-proof contract/version\n"
    "refs, safe recovery or reconciliation evidence refs, and safe reason codes",
    "missing, stale, revoked, or substituted approval binding is a mismatch",
    "For `novel_unsupported`, it must also bind the exact validated catalog and\n"
    "index fingerprint, catalog-validation receipt, and canonical no-match proof ref",
    "substituted, incomplete, stale, or wrong-version catalog is a mismatch",
    "required for blocked and unavailable outcomes even when their proposal graph is\n"
    "null",
    "fingerprint is also required for `outcome_uncertain` outcomes even when terminal\n"
    "proof is missing or inconsistent",
    "proposal ref, canonical proposal-graph fingerprint, or canonical\n"
    "decision-evidence fingerprint differs",
    "`D = A + C`",
    "`C / N <= 0.05`",
    "unsafe authority broadening: zero",
    "fabricated availability or successful execution claims: zero",
    "raw sensitive content in durable routing evidence: zero",
    "An exhaustive durable-evidence safety census covers every artifact instance",
    "routing and shadow\n"
    "logs, traces, decision envelopes, receipts, reports, fixtures, generated corpus\n"
    "records, benchmark artifacts, caches, and failure diagnostics",
    "The denominator\n"
    "is every artifact instance in that closed manifest; the numerator is every\n"
    "instance containing raw prompt or response content",
    "An unmanifested,\n"
    "unscanned, unreadable, or unsafe artifact invalidates the census rather than\n"
    "shrinking the denominator",
    "the complete accepted corpus is replayed through a no-effect\n"
    "active-mode harness",
    "Every active-mode route, familiarity state, canonical\n"
    "decision-evidence fingerprint, proposal-graph fingerprint, policy/scope refs,\n"
    "null/non-null proposal posture, routing tier, prompt-format version, exact\n"
    "candidate model-visible payload fingerprint, context fingerprint, and ordered\n"
    "hydrated-manifest ref/hash set",
    "An ordinary-chat case must also\n"
    "match its paired-acceptance candidate artifact; a tool-facing case instead must\n"
    "match its sealed routing/tool-acceptance candidate artifact",
    "canonical empty manifest set and the exact content-free arbitration-probe\n"
    "receipt",
    "requires a revised candidate plus a complete shadow and active replay",
    "complete zero-tolerance artifact census also covers every active-mode replay\n"
    "artifact",
    "complete accepted corpus must also be replayed with explicit safe-disable\n"
    "engaged in the healthy, missing, corrupt, stale, and over-budget catalog states",
    "Every case in every state must prove exact legacy-router route, payload,\n"
    "response, empty awareness-context, and complete durable-evidence artifact-set\n"
    "and fingerprint equivalence",
    "No awareness-specific decision envelope or other durable record may appear in the\n"
    "safe-disabled artifact set",
    "Any awareness routing, compact discovery, manifest hydration, changed\n"
    "legacy payload, or changed durable-evidence artifact or fingerprint while\n"
    "safe-disable is engaged invalidates promotion",
    "successful, failed, canceled, and rolled-back immutable terminal receipts are\n"
    "  the sole inputs",
    "Cancellation and rollback\n"
    "  each contribute one terminal adverse, non-success outcome and cannot be\n"
    "  omitted",
    "hard no-dispatch firewall before every\n"
    "real dispatcher, executor, connector, shell/subprocess boundary, browser",
    "uses only fake adapters and isolated\nsynthetic targets",
    "`execute_approved_action` is normalized and assessed but\nnever dispatched",
    "immutable zero-execution receipt and per-adapter zero-event\ncounter manifest",
    "every accepted replay case produced zero\n"
    "dispatch attempts and zero external or durable side effects",
    "Every ordinary-chat response emitted by the active harness",
    "exact response-hash equality\nwith the qualified paired-candidate response",
    "blinded independent rescoring of the\n"
    "emitted active response on all four ordinary-chat dimensions",
    "empty, truncated, missing, or semantically unrelated\n"
    "ordinary-chat response invalidates the replay",
    "The all-outcome-uncertain fail-closed census denominator is every accepted\n"
    "corpus case in which proposal or execution work began and exact durable\n"
    "terminal proof is absent or inconsistent",
    "counted exactly once in shadow mode\n"
    "and exactly once in the no-effect active replay",
    "does not return the exact\n"
    "`report_outcome_uncertain`/`outcome_uncertain` pair",
    "TAW-08 requires exactly zero\n"
    "numerator events in both the shadow and active-mode populations",
    "Every sealed acceptance pair must receive an invariant-valid score for all four\n"
    "ordinary-chat dimensions",
    "any other unscored pair invalidates\n"
    "qualification; it cannot be excluded from the paired denominator",
    "TAW-08 fails unless every sealed\n"
    "pair is scored without changing or reselecting the acceptance population",
    "`legacy-router-normalization:v1`",
    "Route and familiarity state are one invariant",
    "`approval_required` only with `familiar_requires_approval`",
    "`ask_for_required_input` only with `familiar_input_required`",
    "`report_unavailable` only with `familiar_unavailable`",
    "`blocked_authority` only\nwith `familiar_authority_blocked`",
    "Ask one focused clarification through `ask_clarifying_question`; do not choose another route",
    "`blocked_capability_evidence` only with\n"
    "`capability_evidence_unavailable`",
    "`report_unsupported` only with\n`novel_unsupported`",
    "`report_outcome_uncertain` only with\n`outcome_uncertain`",
    "`ask_clarifying_question`/`ambiguous`",
    "`blocked_unsafe`/`familiar_authority_blocked`",
    "| `blocked_unsafe` | `blocked_unsafe` | `familiar_authority_blocked` | null |",
    "| Any accepted contract after proposal or execution work began when exact durable terminal proof is absent or inconsistent | `report_outcome_uncertain` | `outcome_uncertain`",
    "| Any possible-tool-intent turn whose valid, current bounded catalog proves that no capability contract adequately covers the requested effect | `report_unsupported` | `novel_unsupported` | null |",
    "| `answer_with_reviewed_memory`, `draft_or_plan` | Derived with the route/state invariant; unchanged accepted route only for `familiar_supported`",
    "| `prepare_tool_or_action` | Derived with the route/state invariant; `prepare_tool_or_action` only for `familiar_supported` | Derived only from frozen typed evidence: `familiar_supported` requires exact capability identity, current availability, complete inputs, and proposal readiness; missing inputs map to `familiar_input_required`, validated unavailability maps to `familiar_unavailable`, a policy/safety denial or missing graduated exact lane maps to `familiar_authority_blocked`, and an exact catalog/index-evidence-unavailable posture maps to `capability_evidence_unavailable`",
    "| `approval_required` | Derived with the route/state invariant; `approval_required` only for `familiar_requires_approval` | Derived only from frozen typed evidence",
    "validated current availability, and complete typed inputs",
    "incomplete typed inputs map to `familiar_input_required`",
    "| `execute_approved_action` | Derived with the route/state invariant; `execute_approved_action` only for `familiar_supported` | Derived only from frozen typed evidence",
    "exact accepted action-scope ref only for `familiar_supported`; otherwise null",
    "validated unavailability maps to `familiar_unavailable`",
    "exact receipt ref, attempt ref, contract version",
    "recomputable, non-authoritative projection",
    "never durably mutated by receipt",
    "No\n  receipt-arrival handler mutates a durable statistics store",
    "stable unique operation IDs",
    "OpenAPI and `/api/manifest` coverage",
    "declare route side-effect",
    "If the optional Control Center surface is added, require focused frontend\n"
    "  tests and updated product-language expectations as conditional acceptance",
    "fail-closed precedence is mandatory",
    "Implement all nine canonical familiarity states",
    "Treat every hydrated manifest as untrusted model data",
    "schema-limited,\n"
    "  escaped, quoted data envelope with an explicit instruction/data delimiter",
    "catalog-borne prompt-injection cases",
    "response-level census over every catalog-injection case in the complete\n"
    "  no-effect active replay",
    "Following a manifest instruction, emitting unrelated\n"
    "  catalog-directed content, or omitting or contradicting required limitation or\n"
    "  evidence text is one event",
    "Promotion requires zero events; an invalid or\n"
    "  missing response invalidates the census",
    "TAW-00",
    "TAW-08",
    "final GoatCitadel comparison may start only after",
    "No raw conversation is added to a training or evaluation corpus automatically",
    "receipt- and attempt-keyed",
    "fully redacted transformation",
    "Those matches remain classification",
    "excluded only from proposal or execution",
    "evidence-only shadow mode",
    "explicit safe-disable boundary",
    "ordinary chat unavailable",
    "fails closed only as\n"
    "`blocked_capability_evidence`/`capability_evidence_unavailable`, never as\n"
    "`novel_unsupported` or `familiar_unavailable`",
    "corrupt-index fallback",
    "PR count follows contract and risk seams rather than a fixed",
    "must remain isolated and cannot be hidden inside a delivery group",
    "Restrict baseline collection to behavior-preserving instrumentation",
    "capture and seal the accepted-current baseline first",
    "Every requested effect in a composed request must have one explicit canonical\n"
    "node with a supported, blocked, unsupported, or clarification-required posture",
    "cannot silently omit blocked or unsupported nodes or propose or execute a\n"
    "reduced supported subset unless the operator explicitly confirms an exact scope",
    "token accounting binds the exact active backend, tokenizer artifact and\n"
    "  fingerprint, prompt-format version, and estimator version",
    "tokenizer or estimator drift fails closed before hydration",
    "evaluated for every clarification-emitting case\n"
    "in the complete shadow and active-replay corpus",
    "Each question must ask for the adjudicated\n"
    "required safe fields and contain no unrelated, misleading, sensitive, or\n"
    "contradictory guidance; an invalid or unscored response invalidates the run",
    "After any failed acceptance cycle, the disclosed holdout population is\n"
    "permanently retired from promotion use",
    "requires a fresh,\n"
    "independently committed holdout and custodian receipt created before the revised\n"
    "candidate is built",
    "identical response-and-claim census evaluates every emitted\n"
    "active-mode response",
    "assertions that approval is unnecessary or a\n"
    "blocked effect is permitted even when route and decision fingerprints match",
    "separate supplied-content instruction census evaluates every accepted case",
    "without an explicit operator adoption bound\n"
    "to the effect and scope—is one event",
    "response-level instruction-following check on every emitted response for each\n"
    "supplied-content case",
    "is one event even when no effect is selected,\n"
    "proposed, approved, or executed",
    "fingerprint for every `answer_with_reviewed_memory` case must also bind the\n"
    "adjudicated selected memory refs, review-status and provenance evidence",
    "canonical expected-null memory fingerprint",
    "Every emitted memory-facing response must also be checked against its adjudicated\n"
    "selected evidence and required limitation posture",
    "memory is recall rather than verified truth",
    "matching selection fingerprint\nalone is insufficient",
    "Freeze and verify a content-addressed manifest of every acceptance-affecting",
    "before the custodian releases any sealed holdout input",
    "merged tree must equal the complete candidate manifest exactly before\n"
    "  TAW-08 completion",
    "forces a fresh candidate lock and acceptance cycle because the sealed holdout\n"
    "  cannot be reused",
    "compact capability shortlist: warm p95 at or below 50 ms and p99 at or below\n"
    "  100 ms",
    "Tier 2 manifest read, schema validation, and schema-limited rendering at the\n"
    "  8-manifest ceiling: warm p95 at or below 100 ms and p99 at or below 200 ms",
    "end-to-end supported tool-turn time to first token, from initial ingress\n"
    "  arbitration through Tier 1 routing, Tier 2 hydration, exact prompt assembly,\n"
    "  tokenizer accounting, and local-model\n"
    "  prefill: warm p95 at or below 1,500 ms and p99 at or below 2,500 ms",
    "clock starts when the normalized\n"
    "  operator turn reaches initial arbitration, including the mandatory content-free\n"
    "  discovery probe or tool-intent sentinel",
    "retrieval, Tier 2 manifest hydration, end-to-end supported tool-turn TTFT, and\n"
    "  cold catalog construction per supported hardware/backend class",
    "cold catalog build or refresh: p95 at or below 150 ms and p99 at or below\n"
    "  300 ms",
    "uncertainty nor a current policy or safety denial, a separate fail-closed census\n"
    "requires the exact canonical\n"
    "`blocked_capability_evidence` route and `capability_evidence_unavailable`",
    "without consistent exact durable terminal proof retains its canonical\n"
    "`report_outcome_uncertain` route with `outcome_uncertain`",
    "current policy or safety denial evidence retains its canonical\n"
    "`blocked_authority` or `blocked_unsafe` route with\n"
    "`familiar_authority_blocked`",
    "Catalog degradation\nmust never overwrite either higher-precedence posture",
    "For every remaining case,\nany direct-chat,\n"
    "unsupported, unavailable, proposal, approval, execution, or other mismatched\n"
    "route/state result is one event",
    "requires canonical expected-null capability and\n"
    "operation identity fingerprints plus the bound policy/safety evidence",
    "For every tool-facing case in the complete active acceptance corpus, every\n"
    "emitted operator-facing response must also be semantically checked against its\n"
    "exact canonical decision and proposal envelope",
    "ordered effects and dependencies, recipients or targets, validated\n"
    "typed arguments and scope, approval/blocked/unsupported posture",
    "Any contradiction, omission, extra effect or target,\n"
    "altered scope, or unscored response invalidates the run",
    "Tier 2 hydration precision is micro-precision over the accepted tool-required\n"
    "corpus",
    "one-sided simultaneous 95% lower confidence bound must clear 80% overall and\n"
    "70% in every predeclared capability, risk category, and supported\n"
    "product-language stratum",
    "stronger languages cannot carry a low-precision language through the aggregate",
)
QUEUE_REQUIRED = (
    "Run the final GoatCitadel comparison only after",
    "The local model remains UAA's language and reasoning engine",
    "The queue item is not complete when these documents merge",
    "Continue every already-authorized intervening queue item",
    "remaining Queue 03 parity phases",
    "governed self-improvement. Stop at the boundary immediately",
    "before the final GoatCitadel comparison",
    "UAA_REMAINING_QUEUE_MANIFEST.json",
)
BOARD_REQUIRED = (
    "Tool-Aware Cognition And Chat Quality",
    "before the final GoatCitadel comparison",
    "docs/strategy/UAA_TOOL_AWARE_COGNITION_AND_CHAT_QUALITY_PLAN.md",
    "docs/roadmap/UAA_REMAINING_QUEUE_MANIFEST.json",
)
ROADMAP_REQUIRED = (
    "Ordered queue insertion: the Tool-Aware Cognition And Chat Quality program",
    "must reach its TAW-08 acceptance gate before",
    "does not replace the configured local model",
)
CANONICAL_ROADMAP_REQUIRED = (
    "docs/roadmap/UAA_REMAINING_QUEUE_MANIFEST.json",
    "TAW-00 through TAW-08",
    "completion evidence or runtime authority",
)
TRUTH_PACKET_REQUIRED = (
    "Planned comparison-order gate",
    "docs/roadmap/UAA_REMAINING_QUEUE_MANIFEST.json",
    "not shipped",
    "product evidence",
)
NAVIGATION_REQUIRED = (
    "docs/strategy/UAA_TOOL_AWARE_COGNITION_AND_CHAT_QUALITY_PLAN.md",
    "docs/roadmap/UAA_TOOL_AWARE_COGNITION_QUEUE_INSERTION.md",
    "docs/roadmap/UAA_REMAINING_QUEUE_MANIFEST.json",
)
FORBIDDEN_PATTERNS = (
    r"\b(?:this|the) (?:plan|program) (?:now )?(?:authorizes?|permits?|allows?|enables?|grants?) (?:new )?(?:runtime )?(?:model|provider|model/provider) (?:calls?|access|use|invocations?)\b",
    r"\b(?:runtime )?(?:model|provider|model/provider) (?:calls?|access|use|invocations?) (?:are|is) (?:now )?(?:authorized|permitted|allowed|enabled|granted)\b",
    r"\b(?:this|the) (?:plan|program) (?:now )?(?:authorizes?|permits?|allows?|enables?|grants?) (?:new )?(?:browser automation|web fetching|connector writes?|shell execution|production authority|(?:browser|connector|shell|production) authority)\b",
    r"\b(?:browser automation|web fetching|connector writes?|shell execution|production authority) (?:are|is) (?:now )?(?:authorized|permitted|allowed|enabled|granted)\b",
    r"\bpolicy (?:checks? )?(?:may|can) be bypassed\b",
    r"\b(?:(?:this|the) (?:plan|program|product|system|release|router|runtime|agent|control center)|uaa|(?:the )?ultimate ai agent|(?:the )?(?:cli|api|python agent core)) "
    r"(?:fetch(?:es|ing)? (?:from )?(?:the )?(?:public )?web|web fetch(?:es|ing)?|"
    r"call(?:s|ing)? (?:a )?(?:runtime )?(?:model|provider)|"
    r"(?:make|perform)(?:s|ing)? (?:runtime )?(?:model|provider) calls?|"
    r"writ(?:e|es|ing) (?:to )?(?:external )?connectors?|connector writes?|"
    r"execut(?:e|es|ing) (?:an? )?(?:unrestricted )?(?:shell|subprocess)|"
    r"perform(?:s|ing)? browser automation|"
    r"(?:automatically )?(?:import(?:s|ing)?|activat(?:e|es|ing)|execut(?:e|es|ing)) (?:skills?|plugins?)|"
    r"(?:automatically )?(?:submit(?:s|ting)?|merg(?:e|es|ing)) (?:pull requests?|PRs?)|"
    r"(?:us(?:e|es|ing)|grant(?:s|ing)?) (?:a )?(?:standing|cross-request) approval|"
    r"(?:chang(?:e|es|ing)|modif(?:y|ies|ying)) (?:billing|accounts?)|"
    r"creat(?:e|es|ing) credentials?|"
    r"(?:bypass(?:es|ing)?|skip(?:s|ping)?|ignor(?:e|es|ing)|"
    r"disabl(?:e|es|ing)|overrid(?:e|es|ing)|weaken(?:s|ing)?) (?:the )?"
    r"(?:policy(?: checks?)?|approval(?: checks?| validation| gates?)?|"
    r"route(?: classification| checks?| gates?)?|openapi(?: checks?| contract)?|"
    r"redaction(?: checks?| gates?)?|foundation gate|gate checks?)|"
    r"persist(?:s|ing)? raw (?:prompts?|responses?|provider payloads?|local paths?|sensitive content))\b",
    r"\b(?:(?:this|the) (?:plan|program|product|system|release|router|runtime|agent|control center)|uaa|(?:the )?ultimate ai agent|(?:the )?(?:cli|api|python agent core)) "
    r"(?:may|can|will|shall|is (?:now )?(?:authorized|permitted|allowed) to) "
    r"(?:bypass|skip|ignore|disable|override|weaken) (?:the )?"
    r"(?:policy(?: checks?)?|approval(?: checks?| validation| gates?)?|"
    r"route(?: classification| checks?| gates?)?|openapi(?: checks?| contract)?|"
    r"redaction(?: checks?| gates?)?|"
    r"foundation gate|gate checks?)\b",
    r"\b(?:(?:this|the) (?:plan|program|product|system|release|router|runtime|agent|control center)|uaa|(?:the )?ultimate ai agent|(?:the )?(?:cli|api|python agent core)) "
    r"(?:may|can|will|shall|is (?:now )?(?:authorized|permitted|allowed) to|"
    r"has (?:the )?(?:authority|ability) to|supports?|enables?|provides? (?:the )?ability to) "
    r"(?!(?:not|never|no\s+longer)\b)"
    r"(?:(?!(?:\bnot\b|\bnever\b|\bno\s+longer\b|\bcannot\b|\bcan['’]t\b|[;])).){0,160}?"
    r"(?:fetch(?:es|ing)? (?:from )?(?:the )?(?:public )?web|web fetch(?:ing)?|"
    r"call(?:s|ing)? (?:a )?(?:runtime )?(?:model|provider)|"
    r"(?:make|perform)(?:s|ing)? (?:runtime )?(?:model|provider) calls?|"
    r"writ(?:e|es|ing) (?:to )?(?:external )?connectors?|connector writes?|"
    r"execut(?:e|es|ing) (?:an? )?(?:unrestricted )?(?:shell|subprocess)|"
    r"shell execution|perform(?:s|ing)? browser automation|browser automation|"
    r"(?:automatically )?(?:import(?:s|ing)?|activat(?:e|es|ing)|"
    r"execut(?:e|es|ing)) (?:skills?|plugins?)|"
    r"automatic (?:skill|plugin) (?:import|activation|execution)|"
    r"(?:automatically )?(?:submit(?:s|ting)?|merg(?:e|es|ing)) (?:pull requests?|PRs?)|"
    r"automatic (?:pull request|PR) (?:submission|merge|merging)|"
    r"(?:use|grant)(?:s|ing)? (?:a )?(?:standing|cross-request) approval|"
    r"(?:standing|cross-request) approval|"
    r"(?:change|modify)(?:s|ing)? (?:billing|accounts?)|"
    r"creat(?:e|es|ing) credentials?|"
    r"(?:bypass(?:es|ing)?|skip(?:s|ping)?|ignor(?:e|es|ing)|"
    r"disabl(?:e|es|ing)|overrid(?:e|es|ing)|weaken(?:s|ing)?) (?:the )?"
    r"(?:policy(?: checks?)?|approval(?: checks?| validation| gates?)?|"
    r"route(?: classification| checks?| gates?)?|openapi(?: checks?| contract)?|"
    r"redaction(?: checks?| gates?)?|foundation gate|gate checks?)|"
    r"persist(?:s|ing)? raw (?:prompts?|responses?|provider payloads?|local paths?|sensitive content))\b",
    r"\b(?:(?:runtime )?(?:model|provider) calls?|"
    r"web fetching|browser automation|connector writes?|"
    r"(?:unrestricted )?(?:shell|subprocess) execution|"
    r"(?:automatic )?(?:skill|plugin) (?:import|activation|execution)|"
    r"(?:automatic )?(?:pull request|PR) (?:submission|merge|merging)|"
    r"(?:standing|cross-request) approval|billing or account changes?|"
    r"credential creation|"
    r"(?:policy|approval|route|openapi|redaction|foundation gate) bypass|"
    r"raw (?:prompt|response|provider payload|local-path|sensitive content) persistence|"
    r"public (?:release|distribution)|production authority) "
    r"(?:is|are) (?:now )?(?:authorized|permitted|allowed|enabled|granted|supported|active)\b",
    r"\b(?:(?:this|the) (?:plan|program|product|system|release|router|runtime|agent|control center)|uaa|(?:the )?ultimate ai agent|(?:the )?(?:cli|api|python agent core))"
    r"(?:(?![.!?]).){1,200}?(?:,|;)\s*(?:but|however|yet|and)\s+(?:it\s+)?"
    r"(?:may|can|will|shall|is (?:now )?(?:authorized|permitted|allowed) to|"
    r"has (?:the )?(?:authority|ability) to|supports?|enables?|provides? (?:the )?ability to) "
    r"(?!(?:not|never|no\s+longer)\b)"
    r"(?:(?!(?:\bnot\b|\bnever\b|\bno\s+longer\b|\bcannot\b|\bcan['’]t\b|[;.!?])).){0,100}?"
    r"(?:fetch(?:es|ing)? (?:from )?(?:the )?(?:public )?web|web fetch(?:ing)?|"
    r"call(?:s|ing)? (?:a )?(?:runtime )?(?:model|provider)|"
    r"(?:make|perform)(?:s|ing)? (?:runtime )?(?:model|provider) calls?|"
    r"writ(?:e|es|ing) (?:to )?(?:external )?connectors?|connector writes?|"
    r"execut(?:e|es|ing) (?:an? )?(?:unrestricted )?(?:shell|subprocess)|"
    r"shell execution|perform(?:s|ing)? browser automation|browser automation|"
    r"(?:automatically )?(?:import(?:s|ing)?|activat(?:e|es|ing)|execut(?:e|es|ing)) (?:skills?|plugins?)|"
    r"automatic (?:skill|plugin) (?:import|activation|execution)|"
    r"(?:automatically )?(?:submit(?:s|ting)?|merg(?:e|es|ing)) (?:pull requests?|PRs?)|"
    r"automatic (?:pull request|PR) (?:submission|merge|merging)|"
    r"(?:use|grant)(?:s|ing)? (?:a )?(?:standing|cross-request) approval|"
    r"(?:standing|cross-request) approval|(?:change|modify)(?:s|ing)? (?:billing|accounts?)|"
    r"creat(?:e|es|ing) credentials?|"
    r"(?:bypass(?:es|ing)?|skip(?:s|ping)?|ignor(?:e|es|ing)|"
    r"disabl(?:e|es|ing)|overrid(?:e|es|ing)|weaken(?:s|ing)?) (?:the )?"
    r"(?:policy(?: checks?)?|approval(?: checks?| validation| gates?)?|"
    r"route(?: classification| checks?| gates?)?|openapi(?: checks?| contract)?|"
    r"redaction(?: checks?| gates?)?|foundation gate|gate checks?)|"
    r"persist(?:s|ing)? raw (?:prompts?|responses?|provider payloads?|local paths?|sensitive content))\b",
    r"\bautomatic skill (?:activation|execution) is allowed\b",
    r"\b(?:(?:this|the) (?:plan|program|product|system|release)|uaa|(?:the )?ultimate ai agent|(?:the )?(?:control center|cli|api|python agent core)) (?:is|are) "
    r"(?:now )?(?:production[- ]ready|ready for production|public[- ]beta(?:[- ]ready)?|"
    r"ready for public (?:beta|release|distribution))\b",
    r"\b(?:(?:this|the) (?:plan|program|product|system|release)|uaa|(?:the )?ultimate ai agent|(?:the )?(?:control center|cli|api|python agent core)) (?:is|are) "
    r"(?!(?:not|never)\b)(?:now )?(?:generally available|ga)"
    r"(?: for (?:public |general )?production(?: use)?)?\b",
    r"\b(?:(?:this|the) (?:plan|program|product|system|release)|uaa|(?:the )?ultimate ai agent|(?:the )?(?:control center|cli|api|python agent core)) "
    r"(?:has|have) (?!(?:not|never)\b)(?:now )?(?:reached|entered|launched into) "
    r"general availability\b",
    r"\b(?:(?:this|the) (?:plan|program|product|system|release)|uaa|(?:the )?ultimate ai agent|(?:the )?(?:control center|cli|api|python agent core)) (?:is|are) "
    r"(?:now )?(?:open|available|launched|released) for "
    r"(?:public beta|public release|public distribution)\b",
    r"\b(?:(?:this|the) (?:plan|program|product|system|release)|uaa|(?:the )?ultimate ai agent|(?:the )?(?:control center|cli|api|python agent core)) (?:is|are) "
    r"(?:(?!(?:not|never)\b)\w+\s+){0,2}(?:in|entering|live in|running in) "
    r"(?:a )?public beta\b",
    r"\b(?:(?:this|the) (?:plan|program|product|system|release)|uaa|(?:the )?ultimate ai agent|(?:the )?(?:control center|cli|api|python agent core)) (?:has|have) "
    r"(?:(?!(?:not|never)\b)\w+\s+){0,2}"
    r"(?:entered|joined|launched|opened|started|begun) (?:a )?public beta\b",
    r"\bpublic (?:beta|release|distribution) (?:is|are) (?:now )?"
    r"(?:open|available|launched|ready|enabled|complete)\b",
    r"\b(?:(?:this|the) (?:plan|program|product|system|release)|uaa|(?:the )?ultimate ai agent|(?:the )?(?:control center|cli|api|python agent core)) "
    r"(?:has|have|provides?|offers?|delivers?|supports?|enables?) (?:now )?"
    r"(?:broad|unrestricted|full) autonomy\b",
    r"\b(?:broad|unrestricted|full) autonomy (?:is|are) (?:now )?"
    r"(?:enabled|available|active|supported|complete)\b",
    r"\b(?:(?:this|the) (?:plan|program|product|system|release|router|runtime|agent|control center)|uaa|(?:the )?ultimate ai agent|(?:the )?(?:cli|api|python agent core)) "
    r"(?:may|can|will|shall|is (?:now )?(?:authorized|permitted|allowed) to|"
    r"has (?:the )?(?:authority|ability) to|supports?|enables?|provides? (?:the )?ability to|offers?) "
    r"(?!(?:not|never|no\s+longer)\b)"
    r"(?:(?!(?:\bnot\b|\bnever\b|\bno\s+longer\b|\bcannot\b|\bcan['’]t\b|[;.!?])).){0,100}?"
    r"(?:perform(?:s|ing)? remote execution|remote execution|"
    r"control(?:s|ling)? mobile sensors?|mobile (?:sensor|control) runtime|"
    r"supported binary distribution|binary distribution)\b",
    r"\b(?:remote execution|mobile (?:sensor|control) runtime|"
    r"mobile sensor control|supported binary distribution|binary distribution) "
    r"(?:is|are) (?:now )?(?:authorized|permitted|allowed|enabled|granted|supported|active|available)\b",
    r"\b(?:(?:this|the) (?:plan|program|product|system|release|router|runtime|agent|control center)|uaa|(?:the )?ultimate ai agent|(?:the )?(?:cli|api|python agent core)) "
    r"(?:has|have|supports?|enables?|provides?|offers?) (?:now )?"
    r"production authority\b",
    r"\b(?:(?:this|the) (?:plan|program|product|system|release|router|runtime|agent|control center)|uaa|(?:the )?ultimate ai agent|(?:the )?(?:cli|api|python agent core)) "
    r"(?:logs?|stores?|records?|retains?|saves?) raw "
    r"(?:prompts?|responses?(?: content)?|provider payloads?|local paths?|sensitive content)\b",
    r"\b(?:(?:this|the) (?:plan|program|product|system|release|router|runtime|agent|control center)|uaa|(?:the )?ultimate ai agent|(?:the )?(?:cli|api|python agent core)) "
    r"(?:may|can|will|shall|is (?:now )?(?:authorized|permitted|allowed) to|"
    r"has (?:the )?(?:authority|ability) to|supports?|enables?|provides? (?:the )?ability to|offers?) "
    r"(?!(?:not|never|no\s+longer)\b)"
    r"(?:spend(?:s|ing)? (?:money|funds)|make(?:s|ing)? purchases?|purchase(?:s|d|ing)? (?:goods|services))\b",
    r"\b(?:spending|purchases?|purchase execution) (?:is|are) (?:now )?"
    r"(?:authorized|permitted|allowed|enabled|granted|supported|active|available)\b",
)
AUTHORITY_DENIALS = (
    "## 12. Explicit Non-Goals",
    "- new runtime model/provider calls;",
    "- web fetching or browser automation;",
    "- connector writes;",
    "- unrestricted shell or subprocess execution;",
    "- remote execution;",
    "- mobile sensor or control runtime;",
    "- automatic skill/plugin import or execution;",
    "- automatic PR submission or merging;",
    "- standing or cross-request approval;",
    "- spending or purchases;",
    "- billing/account changes or credential creation;",
    "- policy, approval, route, OpenAPI, redaction, or Foundation Gate bypass;",
    "- raw prompt, response, provider payload, or local-path persistence;",
    "- supported binary distribution; or",
    "- public release, production authority, or claims of human-like",
)
PHASE_HEADINGS = (
    "### TAW-00 — Convergence ledger and evaluation baseline",
    "### TAW-01 — Capability evidence envelope",
    "### TAW-02 — Familiarity and uncertainty assessor",
    "### TAW-03 — Progressive capability retrieval",
    "### TAW-04 — Chat integration and clarification behavior",
    "### TAW-05 — Outcome evidence and governed improvement",
    "### TAW-06 — Operator diagnostics",
    "### TAW-07 — Quality, latency, and adversarial hardening",
    "### TAW-08 — Acceptance and GoatCitadel precondition",
)
FAMILIARITY_STATES = (
    "familiar_supported",
    "familiar_input_required",
    "familiar_unavailable",
    "familiar_requires_approval",
    "familiar_authority_blocked",
    "capability_evidence_unavailable",
    "ambiguous",
    "novel_unsupported",
    "outcome_uncertain",
)
FAMILIARITY_PRECEDENCE = (
    "1. `outcome_uncertain` when work began",
    "2. `familiar_authority_blocked` when the current PolicyEngine or applicable",
    "3. `capability_evidence_unavailable` when the possible-tool-intent sentinel is",
    "4. `ambiguous` when materially different interpretations remain after the",
    "5. `familiar_authority_blocked` when a known requested effect has no graduated",
    "6. `familiar_unavailable` when the known capability is not currently usable",
    "7. `familiar_input_required` when the exact usable capability still lacks",
    "8. `familiar_requires_approval` when complete inputs bind an existing exact",
    "9. `familiar_supported` when the exact no-effect answer or governed proposal",
    "10. `novel_unsupported`.",
)
QUEUE_ORDERED_STEPS = (
    "1. Finish the currently admitted PR or verification atomic unit",
    "2. Continue every already-authorized intervening queue item",
    "3. At that pre-Goat boundary, execute TAW-00 through TAW-08",
    "4. Run the final GoatCitadel comparison only after",
)
EXPECTED_QUEUE_ITEMS = (
    (
        1,
        "queue-03-hermes-openclaw-parity",
        "Queue 03 — Hermes and OpenClaw parity",
        "03_queue_03_hermes_openclaw_parity.prompt.md",
        "c16cdbe70548b72d91f6f93861df87998aa24e21945238bf26004b5781ece93a",
    ),
    (
        2,
        "queue-04-delegated-mission-document-organization",
        "Queue 04 — Delegated mission and document organization",
        "04_queue_04_delegated_mission_document_organization.prompt.md",
        "4e5f3cdf7059f29bec053ce5a850754ce69e847f579bb083bf10cdb6ac1a070b",
    ),
    (
        3,
        "queue-05-capability-evaluation-lab",
        "Queue 05 — Capability evaluation lab",
        "05_queue_05_capability_evaluation_lab.prompt.md",
        "b097a483c595333a77a513fa2b4fb7231908159c3601289afa2f2324782adbda",
    ),
    (
        4,
        "queue-06-kanban-work-board",
        "Queue 06 — Kanban work board",
        "06_queue_06_kanban_work_board.prompt.md",
        "6053f24f1fd221ae48d94ab9b723047f7ecf10b85b6de5fee0fd93dbfe01de75",
    ),
    (
        5,
        "queue-07-news-signals",
        "Queue 07 — News and signals",
        "07_queue_07_news_signals.prompt.md",
        "839e2c4ecfa1241f038bf217f38e8eef733d8989c588cd7878b4ddad880ebbcd",
    ),
    (
        6,
        "queue-08-autocorrect-controls",
        "Queue 08 — Autocorrect controls",
        "08_queue_08_autocorrect_controls.prompt.md",
        "25237cf2f6f7528bc5d7490e9523c1ad4c7c840bd1b200ec3094b1c05d81dcd3",
    ),
    (
        7,
        "governed-cross-platform-social-publishing",
        "Governed cross-platform social publishing",
        "09_governed_cross_platform_social_publishing.prompt.md",
        "99691cba334deab8e5a1696681b69d7b609a7b9604e6731273e26a68972c66d9",
    ),
    (
        8,
        "governed-self-improvement",
        "Governed self-improvement program",
        "10_governed_self_improvement_program.prompt.md",
        "ec4a65e75cafe302c1173879759444813cba501f70d6cb82c4ba5c42b0daadd0",
    ),
    (
        9,
        "queue-09-final-goat-comparison",
        "Queue 09 — Final GoatCitadel comparison",
        "11_queue_09_final_goat_comparison.prompt.md",
        "b437f83fc55d22fc4d583b2553b3d043b28189f5e3e525c36f6be6b650dd26b2",
    ),
)
DENIED_AUTHORITY_KEYS = (
    "runtime_model_or_provider_calls",
    "web_fetch_or_browser_automation",
    "connector_writes",
    "unrestricted_shell_or_subprocess",
    "remote_execution",
    "mobile_sensor_or_control_runtime",
    "automatic_skill_or_plugin_execution",
    "automatic_pr_submission_or_merge",
    "standing_or_cross_request_approval",
    "spending_or_purchases",
    "billing_account_or_credential_changes",
    "policy_approval_route_openapi_redaction_or_gate_bypass",
    "raw_sensitive_content_persistence",
    "supported_binary_distribution",
    "public_release_or_production_authority",
)

ZERO_TOLERANCE_LINES = (
    "- unsafe authority broadening: zero;",
    "- fabricated availability or successful execution claims: zero;",
    "- raw sensitive content in durable routing evidence: zero;",
)
ZERO_TOLERANCE_CONTRADICTION_PATTERNS = (
    r"\b(?:(?:up to|at most|no more than)\s+)?"
    r"(?:(?!0+(?:\.0+)?\s*%)(?:\d+(?:\.\d+)?)\s*%|"
    r"non[- ]zero|some|one or more)\s+"
    r"(?:unsafe authority broadening|"
    r"fabricated (?:availability(?: or successful execution)?|"
    r"successful execution) claims?|"
    r"raw sensitive content in durable routing evidence)"
    r"(?:\s+\w+){0,8}\s+(?:is|are|may be|can be)\s+"
    r"(?:acceptable|allowed|permitted|tolerated)\b",
    r"\b(?:unsafe authority broadening|"
    r"fabricated (?:availability(?: or successful execution)?|"
    r"successful execution) claims?|"
    r"raw sensitive content in durable routing evidence)"
    r"(?:\s+\w+){0,8}\s+(?:may|can)\s+(?:be\s+)?"
    r"(?:accepted|allowed|permitted|tolerated)\s+(?:up to\s+)?"
    r"(?!0+(?:\.0+)?\s*%)(?:\d+(?:\.\d+)?)\s*%",
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        try:
            safe_ref = path.relative_to(ROOT).as_posix()
        except ValueError:
            safe_ref = "required-ref:outside-repository"
        raise RuntimeError(f"missing or unreadable required file: {safe_ref}") from None


def _require(label: str, text: str, fragments: tuple[str, ...]) -> None:
    missing = [fragment for fragment in fragments if fragment not in text]
    if missing:
        raise RuntimeError(f"{label} is missing required fragments: {missing}")


def _require_ordered(label: str, text: str, fragments: tuple[str, ...]) -> None:
    _require(label, text, fragments)
    positions = [text.index(fragment) for fragment in fragments]
    if positions != sorted(positions):
        raise RuntimeError(f"{label} is not in required order")


def _verify_exact_phase_headings(text: str) -> None:
    found = tuple(
        line.lstrip()
        for line in text.splitlines()
        if re.fullmatch(
            r"[ ]{0,3}#{1,6}\s+.*\bTAW-[A-Za-z0-9]+\b[^\r\n]*",
            line,
        )
    )
    if found != PHASE_HEADINGS:
        raise RuntimeError(
            "plan phase headings is missing or contains unmanifested entries"
        )


def _verify_familiarity_states(text: str) -> None:
    start = "The canonical operator-visible states are:\n\n"
    end = "\n\nThe assessment must include"
    if text.count(start) != 1 or text.count(end) != 1:
        raise RuntimeError("canonical familiarity state table is invalid")
    table = text.split(start, 1)[1].split(end, 1)[0]
    rows = tuple(line.strip() for line in table.splitlines() if line.strip())
    if len(rows) != len(FAMILIARITY_STATES) + 2:
        raise RuntimeError("canonical familiarity state set is invalid")
    if rows[0] != "| State | Meaning | Required behavior |" or re.fullmatch(
        r"\|\s*:?-{3,}:?\s*\|\s*:?-{3,}:?\s*\|\s*:?-{3,}:?\s*\|",
        rows[1],
    ) is None:
        raise RuntimeError("canonical familiarity state set is invalid")
    found: list[str] = []
    for row in rows[2:]:
        match = re.fullmatch(
            r"\|\s*`([^`|]+)`\s*\|\s*[^|]+\|\s*[^|]+\|",
            row,
        )
        if match is None:
            raise RuntimeError("canonical familiarity state set is invalid")
        found.append(match.group(1))
    if tuple(found) != FAMILIARITY_STATES:
        raise RuntimeError("canonical familiarity state set is invalid")


def _verify_familiarity_precedence(text: str) -> None:
    start = (
        "When more than one state predicate is true, the following fail-closed "
        "precedence is mandatory:\n\n"
    )
    end = "\n\nThis ordering prevents"
    if text.count(start) != 1 or text.count(end) != 1:
        raise RuntimeError("familiarity precedence is invalid")
    block = text.split(start, 1)[1].split(end, 1)[0]
    _require_ordered("familiarity precedence", block, FAMILIARITY_PRECEDENCE)
    if any(text.count(fragment) != 1 for fragment in FAMILIARITY_PRECEDENCE):
        raise RuntimeError("familiarity precedence has duplicate declarations")
    numbered_entries = tuple(
        re.findall(r"^[ ]{0,3}(\d+)[.)]\s+`([^`]+)`", block, flags=re.MULTILINE)
    )
    expected_entries = (
        ("1", "outcome_uncertain"),
        ("2", "familiar_authority_blocked"),
        ("3", "capability_evidence_unavailable"),
        ("4", "ambiguous"),
        ("5", "familiar_authority_blocked"),
        ("6", "familiar_unavailable"),
        ("7", "familiar_input_required"),
        ("8", "familiar_requires_approval"),
        ("9", "familiar_supported"),
        ("10", "novel_unsupported"),
    )
    all_numbered_entries = tuple(
        re.findall(r"^[ ]{0,3}(\d+)[.)]\s+", block, flags=re.MULTILINE)
    )
    if numbered_entries != expected_entries or len(all_numbered_entries) != len(
        expected_entries
    ):
        raise RuntimeError("familiarity precedence has unmanifested entries")
    state_pattern = "|".join(re.escape(state) for state in FAMILIARITY_STATES)
    all_numbered_states = tuple(
        re.findall(
            rf"^[ ]{{0,3}}\d+[.)] `({state_pattern})`", text, flags=re.MULTILINE
        )
    )
    block_numbered_states = tuple(
        re.findall(
            rf"^[ ]{{0,3}}\d+[.)] `({state_pattern})`", block, flags=re.MULTILINE
        )
    )
    if all_numbered_states != block_numbered_states or len(block_numbered_states) != 10:
        raise RuntimeError("familiarity precedence has competing declarations")


def _verify_queue_position(text: str) -> None:
    start = "## Position\n\n"
    end = "\n\n## Execution Rules"
    if text.count(start) != 1 or text.count(end) != 1:
        raise RuntimeError("ordered queue insertion position is invalid")
    block = text.split(start, 1)[1].split(end, 1)[0]
    _require_ordered("ordered queue insertion", block, QUEUE_ORDERED_STEPS)
    if any(text.count(fragment) != 1 for fragment in QUEUE_ORDERED_STEPS):
        raise RuntimeError("ordered queue insertion has duplicate declarations")

    numbered_pattern = re.compile(r"^[ ]{0,3}(\d+)[.)]\s+.*$", flags=re.MULTILINE)
    all_numbered = tuple(numbered_pattern.findall(text))
    block_numbered = tuple(numbered_pattern.findall(block))
    if (
        all_numbered != block_numbered
        or block_numbered != ("1", "2", "3", "4")
    ):
        raise RuntimeError("ordered queue insertion has competing declarations")


def _verify_zero_tolerance_lines(text: str) -> None:
    lines = [line.strip() for line in text.splitlines()]
    for required in ZERO_TOLERANCE_LINES:
        label = (required.split(":", 1)[0] + ":").removeprefix("- ").lower()
        matches = [line for line in lines if label in line.lower()]
        if matches != [required]:
            raise RuntimeError("plan zero-tolerance gate is invalid")
    if any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in ZERO_TOLERANCE_CONTRADICTION_PATTERNS
    ):
        raise RuntimeError("plan zero-tolerance gate is invalid")


def _find_forbidden_authority_claims(text: str) -> list[str]:
    present: list[str] = []
    for pattern in FORBIDDEN_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            sentence_start = max(
                text.rfind(marker, 0, match.start()) for marker in (".", "!", "?")
            )
            prefix = text[sentence_start + 1 : match.start()]
            tail = prefix.rstrip()
            direct_denial = re.search(r"\bno\s*$", tail, re.IGNORECASE) is not None
            coordinated_denial = False
            if re.search(r"\b(?:or|nor)\s*$", tail, re.IGNORECASE):
                denial_starts = list(
                    re.finditer(
                        r"(?:^|[:;])\s*(?:no|neither)\b",
                        tail,
                        flags=re.IGNORECASE,
                    )
                )
                if denial_starts:
                    denial_items = tail[denial_starts[-1].end() :]
                    coordinated_denial = re.search(
                        r"\b(?:is|are|was|were|does|do|did|has|have|had|"
                        r"may|can|will|shall|must)\b",
                        denial_items,
                        flags=re.IGNORECASE,
                    ) is None
            # A match is exempt only when its own passive subject is directly
            # negated or is the final item in an explicit noun-list denial. The
            # mere presence of "no" elsewhere never negates an affirmative match.
            if direct_denial or coordinated_denial:
                continue
            present.append(pattern)
            break
    return present


def _read_manifest() -> dict[str, object]:
    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate manifest key")
            result[key] = value
        return result

    try:
        manifest = json.loads(_read(MANIFEST), object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, ValueError):
        raise RuntimeError("remaining queue manifest is not valid JSON") from None
    if not isinstance(manifest, dict):
        raise RuntimeError("remaining queue manifest root is invalid")
    return manifest


def _verify_manifest(manifest: dict[str, object]) -> None:
    expected_top_level_keys = {
        "schema_version",
        "artifact_status",
        "source_manifest_sha256",
        "authority_boundary",
        "pre_goat_insertion",
        "items",
    }
    if set(manifest) != expected_top_level_keys:
        raise RuntimeError("remaining queue manifest top-level schema is invalid")
    if any(
        not isinstance(manifest[key], str)
        for key in (
            "schema_version",
            "artifact_status",
            "source_manifest_sha256",
        )
    ):
        raise RuntimeError("remaining queue manifest scalar types are invalid")
    if manifest.get("schema_version") != "uaa.remaining_queue_manifest.v1":
        raise RuntimeError("remaining queue manifest schema is invalid")
    if manifest.get("artifact_status") != "planning_order_only":
        raise RuntimeError("remaining queue manifest artifact status is invalid")
    if (
        manifest.get("source_manifest_sha256")
        != "b039e6b977f0f49092f5100ae5665f7c07bde974c98bcd1dbdd3015e06a77b09"
    ):
        raise RuntimeError("remaining queue source manifest binding is invalid")
    authority = manifest.get("authority_boundary")
    if not isinstance(authority, dict) or set(authority) != set(DENIED_AUTHORITY_KEYS):
        raise RuntimeError("remaining queue authority boundary is invalid")
    if any(
        type(authority[key]) is not bool or authority[key] is not False
        for key in DENIED_AUTHORITY_KEYS
    ):
        raise RuntimeError("remaining queue authority boundary enables authority")

    items = manifest.get("items")
    if not isinstance(items, list):
        raise RuntimeError("remaining queue item list is invalid")
    expected_item_keys = {
        "position",
        "item_id",
        "title",
        "filename",
        "sha256",
        "source_kind",
        "source_status",
        "source_ref",
        "execution_status",
    }
    actual_items: list[tuple[int, str, str, str, str]] = []
    for item in items:
        if not isinstance(item, dict) or set(item) != expected_item_keys:
            raise RuntimeError("remaining queue immutable sequence is invalid")
        position = item["position"]
        item_id = item["item_id"]
        title = item["title"]
        filename = item["filename"]
        sha256 = item["sha256"]
        source_kind = item["source_kind"]
        source_status = item["source_status"]
        source_ref = item["source_ref"]
        execution_status = item["execution_status"]
        if (
            type(position) is not int
            or not isinstance(item_id, str)
            or not isinstance(title, str)
            or not title
            or not isinstance(filename, str)
            or not isinstance(sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", sha256) is None
            or source_kind != "external_prompt"
            or source_status != "not_materialized"
            or source_ref != f"external-ref:uaa-remaining-queue:{item_id}"
            or execution_status != "blocked_pending_exact_source"
        ):
            raise RuntimeError("remaining queue item types are invalid")
        actual_items.append((position, item_id, title, filename, sha256))
    if tuple(actual_items) != EXPECTED_QUEUE_ITEMS:
        raise RuntimeError("remaining queue immutable sequence is invalid")

    expected_insertion = {
        "after_item_id": "governed-self-improvement",
        "program_id": "tool-aware-cognition-and-chat-quality",
        "phase_ids": [f"TAW-{index:02d}" for index in range(9)],
        "before_item_id": "queue-09-final-goat-comparison",
    }
    insertion = manifest.get("pre_goat_insertion")
    if (
        not isinstance(insertion, dict)
        or set(insertion) != set(expected_insertion)
        or not isinstance(insertion.get("after_item_id"), str)
        or not isinstance(insertion.get("program_id"), str)
        or not isinstance(insertion.get("before_item_id"), str)
        or not isinstance(insertion.get("phase_ids"), list)
        or any(not isinstance(item, str) for item in insertion["phase_ids"])
        or insertion != expected_insertion
    ):
        raise RuntimeError("remaining queue pre-Goat insertion is invalid")


def verify() -> dict[str, object]:
    plan = _read(PLAN)
    queue = _read(QUEUE)
    board = _read(BOARD)
    roadmap = _read(ROADMAP)
    canonical_roadmap = _read(CANONICAL_ROADMAP)
    truth_packet = _read(TRUTH_PACKET)
    docs_readme = _read(DOCS_README)
    documentation_index = _read(DOCUMENTATION_INDEX)
    manifest = _read_manifest()
    _require("plan", plan, PLAN_REQUIRED)
    _verify_zero_tolerance_lines(plan)
    _require("plan authority boundary", plan, AUTHORITY_DENIALS)
    _require("queue insertion", queue, QUEUE_REQUIRED)
    _verify_queue_position(queue)
    _require("current board", board, BOARD_REQUIRED)
    _require("canonical roadmap", roadmap, ROADMAP_REQUIRED)
    _require("canonical roadmap truth", canonical_roadmap, CANONICAL_ROADMAP_REQUIRED)
    _require("product release truth", truth_packet, TRUTH_PACKET_REQUIRED)
    _require("docs README navigation", docs_readme, NAVIGATION_REQUIRED)
    _require("documentation index navigation", documentation_index, NAVIGATION_REQUIRED)
    _verify_manifest(manifest)

    # Scan every program truth surface, not only the primary plan. The patterns
    # match affirmative grants rather than denial fragments, so the canonical
    # safety language remains valid while a contradictory claim anywhere fails
    # closed.
    combined = "\n".join(
        (
            plan,
            queue,
            board,
            roadmap,
            canonical_roadmap,
            truth_packet,
            docs_readme,
            documentation_index,
        )
    )
    present = _find_forbidden_authority_claims(combined)
    if present:
        raise RuntimeError(f"self-authorizing language found: {present}")

    _verify_exact_phase_headings(plan)
    _verify_familiarity_states(plan)
    _verify_familiarity_precedence(plan)

    return {
        "status": "passed",
        "documented_phase_count": len(PHASE_HEADINGS),
        "normal_chat_fast_path_required": True,
        "direct_chat_quality_non_inferiority_required": True,
        "local_model_preservation_required": True,
        "documented_familiarity_state_count": len(FAMILIARITY_STATES),
        "goat_comparison_gate_documented": True,
        "evaluation_governance_required": True,
        "reversible_rollout_required": True,
        "structured_runtime_authority_added": False,
        "ordered_manifest_item_count": len(EXPECTED_QUEUE_ITEMS),
    }


def main() -> int:
    try:
        result = verify()
    except RuntimeError as exc:
        print(f"tool-aware cognition plan verification failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
