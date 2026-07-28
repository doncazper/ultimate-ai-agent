# UAA Tool-Aware Cognition And Chat Quality Plan

Status: User-authorized implementation plan and ordered queue insertion.

Date: 2026-07-28.

Execution boundary: this plan must be implemented and accepted before the final
GoatCitadel comparison. The document and its queue entry grant no runtime
authority by themselves.

## 1. Outcome

UAA should converse naturally when the operator wants a chatbot and should
recognize, retrieve, and propose the right governed capability when a task
benefits from tools. It must distinguish familiar, supported work from
ambiguous, unavailable, or novel work using inspectable evidence rather than
model confidence or a brittle command list.

The intended product behavior is:

- ordinary chat feels comparable in responsiveness and conversational quality
  to a direct local-model chat;
- paired evaluation against the same frozen local model and inference settings
  proves that UAA's routing wrapper does not materially degrade ordinary-chat
  helpfulness, instruction following, tone, or response relevance;
- tool awareness is broad enough to understand capability descriptions,
  synonyms, paraphrases, and composed tasks rather than only exact commands;
- tool details are loaded progressively, so normal chat does not carry the
  entire tool catalog in its prompt;
- uncertainty causes an accurate direct answer, one focused clarification, or
  a safe unsupported result instead of a fabricated capability;
- approval, policy, availability, and execution truth remain separate from
  semantic tool relevance; and
- verified outcomes improve deterministic routing data and evaluations without
  turning UAA into a replacement language model or silently training on private
  conversations.

## 2. Existing Foundation And Required Convergence

This program extends the accepted Turn Contract Router; it does not replace or
duplicate it.

Current reusable foundation:

- `docs/architecture/TURN_CONTRACT_ROUTER.md` defines deterministic turn
  classification, direct-answer behavior, no-effect firewalls, and
  approval-aware routing.
- `src/ultimate_ai_agent/core/decision_router/` contains the typed classifier,
  harness binding, route binding, prepared-turn, parallel-preflight, and
  executor-fence contracts.
- `/v1/chat/completions` already obtains a governed chat-turn harness binding
  before using the configured local model surface.
- the capability registry already supports compact catalog search followed by
  full-manifest inspection.
- progressive skill disclosure is metadata-only and does not auto-load or
  execute skills.

The convergence gap is a proof-backed layer between coarse turn
classification and exact execution:

1. identify the smallest relevant capability set;
2. measure how well the request is supported by current schemas, availability,
   authority posture, evaluations, and prior verified outcomes;
3. expose only the required manifests to the local model;
4. preserve a zero-tool, zero-extra-model-call fast path for ordinary chat; and
5. produce redacted evidence explaining the decision without storing raw
   prompts.

## 3. Product And Architecture Principles

### 3.1 The local model remains the language engine

The configured local model remains responsible for language understanding,
reasoning, and response generation. UAA supplies governed context, capability
retrieval, state, evidence, and execution boundaries. This plan does not:

- replace the local model with rules;
- fine-tune, distill, or retrain the local model;
- add a second routing-model call to every message;
- treat registry metadata as a substitute for general reasoning; or
- grant model output authority to execute a tool.

Deterministic routing is a guardrail and context-selection layer, not the whole
of the agent's intelligence.

### 3.2 Chat remains normal by default

Direct conversation is a first-class product path. Greetings, explanation,
writing, brainstorming, summarization of supplied text, and other no-effect
requests must not hydrate tool schemas or wait on tool availability probes.
They pass through the existing local chat surface with only the bounded routing
metadata already required for safety.

### 3.3 Familiarity is evidence, not a feeling

UAA must not ask the model whether it is “confident.” A familiarity assessment
is derived from typed evidence:

- intent clarity and ambiguity signals;
- semantic and deterministic capability matches;
- required-input/schema completeness;
- current capability availability and catalog freshness;
- exact authority and approval posture;
- applicable evaluation coverage and known negative cases;
- prior terminal outcome evidence for the same capability contract version;
- dependency and environment readiness; and
- whether an execution result has actually reached a durable terminal state.

These dimensions remain separately inspectable. A high semantic match never
implies availability, approval, or successful execution.

### 3.4 Progressive disclosure controls latency and context

Capability awareness uses four bounded tiers:

| Tier | Behavior | Model/tool impact |
|---|---|---|
| 0 — direct chat | Existing deterministic classifier selects a no-effect response | No catalog hydration and no extra model call |
| 1 — compact discovery | Search a cached content-free catalog of capability names, summaries, risk, and schema fingerprints | No execution and no hidden import |
| 2 — manifest hydration | Load only the top relevant typed manifests and input schemas | Bounded local context; still no authority |
| 3 — governed proposal/execution | Build an exact proposal and use existing policy, approval, dispatcher, receipt, and rollback boundaries | Execution only when the exact lane is already authorized |

No tier may automatically load executable skill code, fetch the web, invoke a
provider, or broaden an approval.

### 3.5 Rollout is reversible and chat-survivable

The awareness layer must first run in evidence-only shadow mode against the
accepted router. Shadow decisions cannot change responses, hydrate model
context, request approval, or reach execution. Promotion requires the versioned
evaluation and latency thresholds in this plan on the exact candidate.

The promoted integration must retain one explicit safe-disable boundary that
returns routing to the accepted legacy Turn Contract Router without changing
the configured local model, chat payload, authority policy, or durable
evidence. A malformed, stale, over-budget, or unreadable awareness index must
never make ordinary chat unavailable: direct-chat classification falls back to
the accepted no-tool path, while any turn that would require capability
evidence fails closed as unsupported or unavailable. The fallback must not
silently construct a proposal, request approval, or execute a capability.

Safe-disable and rollback are operational recovery controls, not a global
autonomy flag and not new authority. Their state, reason code, catalog
fingerprint, and activation evidence must be redacted and inspectable through
the shared Python Core, CLI, and API contracts.

## 4. Familiarity And Uncertainty Contract

The canonical operator-visible states are:

| State | Meaning | Required behavior |
|---|---|---|
| `familiar_supported` | Intent is clear and the relevant capability contract, required inputs, and current availability are proven | Answer directly or produce the exact governed proposal |
| `familiar_input_required` | The exact capability is known and available, but one or more required typed inputs are missing or invalid | Ask only for the missing safe input fields; do not construct an executable proposal |
| `familiar_unavailable` | The capability is known but is disabled, unhealthy, stale, or absent in the current environment | Explain the bounded limitation and offer safe alternatives |
| `familiar_requires_approval` | Relevance and inputs are known, an exact graduated authority lane already exists, and execution requires its exact approval | Preview scope and request only that existing exact approval; approval cannot mint or broaden authority |
| `familiar_authority_blocked` | Relevance and inputs are known, but no currently graduated exact authority lane covers the requested effect | Keep the effect blocked and expose the exact future promotion prerequisite; do not request an approval that cannot authorize it |
| `ambiguous` | Multiple materially different interpretations or tools remain plausible | Ask one focused clarification or choose a reversible no-effect response |
| `novel_unsupported` | No current capability contract adequately covers the requested effect | Do not invent a tool; identify the unsupported need |
| `outcome_uncertain` | A proposal or execution began but durable terminal proof is missing or inconsistent | Fail closed, preserve evidence, and expose recovery posture |

The assessment must include a stable reason-code set and the fingerprints of
the catalog, selected manifests, policy snapshot, and applicable evaluation
set. It must not persist raw operator text, raw model text, secrets, local
paths, or provider payloads.

## 5. Capability Understanding

Each capability's awareness envelope should be generated from canonical typed
sources rather than a manually maintained command list. At minimum it includes:

- stable capability and operation IDs;
- short operator-language summaries and deterministic aliases;
- effect and risk class;
- required and optional input schema fingerprints;
- preconditions and incompatibilities;
- authority/approval classification;
- availability and health refs;
- safe-disable and rollback posture;
- expected terminal receipt/proof contract;
- supported composition/dependency edges; and
- relevant positive, negative, ambiguity, and adversarial eval refs.

Semantic retrieval may rank candidates, but familiarity assessment retains
plausible registered matches even when they are unavailable, policy-blocked,
or lack a graduated authority lane. Those matches remain classification
evidence for `familiar_unavailable` and `familiar_authority_blocked`; they are
excluded only from proposal or execution. Deterministic constraints reject
effect or schema incompatibility before proposal, and the exact operation
schema remains authoritative. Cross-capability composition is a proposal
graph; it is never standing authority.

Retrieval must not add a per-turn model or provider call. Any semantic index is
local, deterministic for a fixed catalog/evaluator version, and built only
from canonical content-free capability metadata. If that constraint cannot be
met at the accepted catalog scale, TAW-00 must select a deterministic lexical
or hybrid metadata index rather than silently adding another model.

## 6. Performance And Context Budgets

The implementation must meet explicit budgets on supported development Macs:

- routing adds zero additional model calls to the direct-chat path;
- direct-chat router overhead: warm p95 at or below 20 ms and p99 at or below
  50 ms;
- paired direct-chat time to first token is reported against the same local
  model, prompt payload, and frozen inference settings, with routing overhead
  measured separately from model generation;
- compact capability shortlist: warm p95 at or below 50 ms;
- cold catalog build or refresh: p95 at or below 150 ms for the accepted
  baseline catalog;
- Tier 0 exposes zero tool manifests;
- Tier 2 hydrates at most 8 candidate manifests by default;
- hydrated catalog material is bounded by a configurable byte budget and fails
  closed when it cannot be represented safely;
- cache keys bind the canonical catalog, capability schemas, policy version,
  availability epoch, and evaluator version; and
- no network call is required for routing or local catalog hydration.

Budgets may be tightened after measurement. They may not be relaxed silently
to hide regressions.

## 7. Quality And Safety Acceptance

An accepted, versioned evaluation corpus must include:

- natural chat that should never select a tool;
- direct and paraphrased tool requests;
- multi-turn ellipsis and corrections;
- ambiguous requests with materially different effects;
- unavailable and disabled tools;
- missing required inputs;
- unsupported or invented capability names;
- multi-capability composition;
- policy and approval mismatches;
- stale catalog/availability evidence;
- cross-operation and cross-session substitution attempts;
- multilingual and colloquial phrasing represented in the supported product
  languages;
- prompt injection embedded in supplied content; and
- interrupted executions without terminal evidence.

Minimum release thresholds:

- direct-chat false-positive tool selection at or below 2%;
- recall of an applicable capability at or above 95% on the accepted
  tool-required corpus;
- blind paired scoring on the accepted ordinary-chat corpus shows no more than
  a 5 percentage-point degradation from direct use of the same frozen local
  model in helpfulness, instruction following, tone, or response relevance;
- unsafe authority broadening: zero;
- fabricated availability or successful execution claims: zero;
- raw sensitive content in durable routing evidence: zero;
- all `outcome_uncertain` cases fail closed; and
- no statistically material chat latency regression outside the stated
  budgets.

Quality reporting must show the confusion matrix and per-category failures, not
only one aggregate score. It must also identify the exact model artifact,
inference settings, prompt-format version, sample counts, and paired scoring
rubric, and report point estimates plus 95% confidence intervals. A small
sample or wide interval is an unresolved measurement gap, not evidence of
non-inferiority.

### 7.1 Evaluation governance

The ordinary-chat comparison must be a true paired test. Baseline and UAA
outputs use the same model artifact, tokenizer, system/user payload, context
limit, sampler settings, and seed when the backend supports deterministic
seeding. Pair order and display labels are randomized for scoring. If the
backend cannot reproduce a seeded response, the benchmark uses a predeclared
number of repeated paired samples and reports the additional variance instead
of selecting favorable generations.

Human blind scoring with a versioned rubric is the default quality judge.
Evaluator identity is represented only by a safe ref; the report records
evaluator count, agreement, adjudication rules, exclusions, and missing scores.
Deterministic format, latency, safety, and task-specific assertions supplement
human scoring. A model-as-judge call is neither implicitly authorized nor
sufficient as the sole quality proof; using one would require a separately
accepted, cost-bounded evaluation lane with exact model/prompt identity,
calibration against human judgments, and redacted receipts.

Prompts and expected behaviors in the accepted corpus are synthetic or fully
redacted. Candidate responses may be viewed transiently by the scorer, but raw
prompt and response text is not written to repository reports, receipts, test
fixtures, logs, or benchmark artifacts. Durable evidence contains case refs,
category labels, blinded order, bounded numeric/rubric decisions, content
hashes, aggregate statistics, and safe failure reason codes. Any tooling that
cannot enforce that separation fails the acceptance gate.

## 8. Outcome Learning Without Replacing The Model

“Learning” in this program means improving governed data and tests:

- successful and failed terminal receipts update bounded capability outcome
  statistics keyed by contract version and safe environment class;
- operator corrections become safe-ref-only review candidates and must be
  transformed into synthetic or fully redacted fixtures before durable eval
  promotion; raw correction, prompt, and response content is rejected by the
  eval verifier;
- frequently missed paraphrases may be promoted into reviewed aliases or eval
  fixtures;
- changed schemas or policy fingerprints invalidate stale outcome priors; and
- offline evaluation determines whether a routing change is promoted.

No raw conversation is added to a training or evaluation corpus automatically
or manually. Durable evaluation fixtures must be synthetic or fully redacted
and pass the repository content-safety verifier. No online weight update,
reward loop, hidden prompt rewrite, or self-modifying policy is introduced.
Model fine-tuning, if ever desired, is a separate future program with explicit
privacy, dataset, evaluation, rollback, and authority decisions.

## 9. Operator Experience And Observability

CLI, API, and any later Control Center view must expose the same safe read
model:

- selected turn mode;
- familiarity state and reason codes;
- catalog and selected-manifest fingerprints;
- shortlist count, not raw hidden content;
- authority and availability posture;
- latency by routing tier;
- proposal, approval, execution, and terminal proof refs when applicable; and
- clarification, unsupported, or recovery guidance.

Ordinary chat should not show machinery unless the operator asks for details or
the state affects what UAA can safely do. Operator-critical output must be
human-readable rather than raw JSON alone.

## 10. Implementation Sequence

Every phase requires explicit, independently inspectable acceptance evidence,
but PR count follows contract and risk seams rather than a fixed
one-PR-per-phase rule. Adjacent phases may share one reviewable final candidate
when their dependencies are already fixed, the combined diff remains bounded,
and doing so avoids duplicate broad gates. A phase may be skipped only with
exact-current-main code, test, and verifier evidence. Runtime-authority
graduation, new external effects, or materially different rollback boundaries
must remain isolated and cannot be hidden inside a delivery group.

Independent work may be prepared and locally verified concurrently after its
dependencies are fixed, while shared contracts and merge admission follow the
evidence dependency order. Each final candidate uses targeted checks while
coding, one broad local qualification, exact-head hosted CI/review, merge,
proportional post-merge verification, and cleanup.

### TAW-00 — Convergence ledger and evaluation baseline

- Map every requirement in this plan to the existing Turn Contract Router,
  capability registry, skill disclosure, chat route, and authority system.
- Establish the versioned evaluation corpus and benchmark harness.
- Record baseline routing accuracy, paired same-model ordinary-chat quality,
  time to first token, routing latency, catalog scale, and current failure
  categories under frozen model, inference, and prompt-format identities.
- Do not change runtime behavior in this phase unless required to make
  measurement deterministic.

### TAW-01 — Capability evidence envelope

- Define the typed, content-free awareness envelope and canonical fingerprint.
- Generate envelopes from registered capabilities and operation schemas.
- Bind availability, policy, approval class, safe-disable, rollback, and
  terminal proof expectations without granting them.
- Reject stale, malformed, duplicate, or inconsistent envelopes.

### TAW-02 — Familiarity and uncertainty assessor

- Implement the eight canonical familiarity states and stable reason codes.
- Keep semantic relevance separate from availability, authority, input
  completeness, and terminal outcome truth.
- Add table-driven tamper, ambiguity, substitution, and stale-evidence tests.
- Make unsupported and inconsistent cases fail closed.

### TAW-03 — Progressive capability retrieval

- Add cached Tier 1 compact discovery and bounded Tier 2 manifest hydration.
- Rank by relevance while retaining unavailable, policy-blocked, and
  authority-blocked registered matches for familiarity classification.
- Deterministically filter effect and schema incompatibilities before proposal
  and prevent every blocked or unavailable match from proposal or execution.
- Bind cache entries to exact catalog and environment fingerprints.
- Enforce entry, byte, and latency budgets.

### TAW-04 — Chat integration and clarification behavior

- Preserve the existing direct-chat path and zero extra model-call rule.
- Introduce the awareness decision in evidence-only shadow mode before it can
  affect model context or operator-visible routing.
- Supply only selected typed manifests to the local model when needed.
- Add focused clarification for truly ambiguous material effects.
- Prove no hidden skill activation, execution, provider call, or web fetch.
- Add one explicit safe-disable back to the accepted legacy router; corrupt,
  stale, unreadable, or over-budget awareness state must preserve ordinary
  no-tool chat while blocking capability proposal and execution.
- Keep CLI/API inspection parity with the shared Python Core.

### TAW-05 — Outcome evidence and governed improvement

- Bind attempts to exact durable terminal receipts.
- Add versioned, redacted outcome statistics using receipt- and attempt-keyed
  idempotent updates that are auditable, rollback-aware, and immune to retry or
  recovery replay inflation.
- Accept operator corrections only as safe refs; require reviewed synthetic or
  fully redacted transformation and a content-safety verifier before an eval
  fixture can become durable.
- Invalidate stale priors on schema, policy, or evaluator change.
- Prove that missing terminal evidence produces `outcome_uncertain`.
- Do not add online training or automatic policy/alias promotion.

### TAW-06 — Operator diagnostics

- Add human-readable route/familiarity inspection to CLI and API.
- Add a Control Center surface only if it consumes the same backend read model.
- Hide routine machinery from ordinary chat while making limitations and
  required approvals clear when relevant.
- Validate redaction and bounded evidence.

### TAW-07 — Quality, latency, and adversarial hardening

- Run the full evaluation corpus, performance budgets, context-budget tests,
  fault injection, and stale-cache recovery.
- Run blind paired ordinary-chat scoring against the frozen direct-local-model
  baseline and report per-dimension non-inferiority with statistical
  uncertainty.
- Exercise shadow-to-active promotion, safe-disable, rollback, and corrupt-index
  recovery without changing the local model or broadening authority.
- Audit false positives, false negatives, ambiguity, authority separation, and
  multilingual/paraphrase behavior.
- Batch all findings into one final candidate and rerun broad qualification
  once.

### TAW-08 — Acceptance and GoatCitadel precondition

- Run end-to-end chat, tool discovery, proposal, approval-required, unavailable,
  unsupported, interrupted, and recovery journeys.
- Publish the exact acceptance report with thresholds, remaining gaps, and
  immutable evidence refs.
- Reconcile current product claims and relevant boards.
- The final GoatCitadel comparison may start only after TAW-00 through TAW-08
  are merged, post-merge verified, and represented accurately on current main.

## 11. Unknowns To Resolve During TAW-00

The implementation must measure rather than assume:

- actual catalog size and operation count after the remaining queue lands;
- supported-language scope and representative paraphrase coverage;
- the local models' tool-schema/context-format differences;
- warm and cold latency on each supported macOS hardware class;
- the right semantic-retrieval method at current catalog scale;
- whether existing availability signals are fresh enough for routing;
- how outcome priors should decay across environment and contract versions;
- which composed requests require clarification instead of a multi-step
  proposal; and
- whether the current chat UI can expose optional diagnostics without harming
  the normal conversational experience;
- the benchmark sample size required for stable per-category routing and paired
  chat-quality confidence intervals; and
- the human-evaluation staffing, agreement target, and adjudication procedure
  needed to make blind scoring credible without persisting raw conversations;
- which supported local-model backends provide reproducible seeding and how
  many repeated pairs are required when they do not; and
- how supported local-model prompt formats alter manifest presentation without
  changing the underlying capability or authority contract;
- the minimum shadow-observation sample and category coverage required before
  activation; and
- the operator-facing recovery language when awareness is safely disabled but
  ordinary chat remains available.

Unknowns are not authority. If a safe answer requires materially new runtime
authority, the phase must stop at the exact minimal proposal and evidence.

## 12. Explicit Non-Goals

This program does not authorize:

- new runtime model/provider calls;
- web fetching or browser automation;
- connector writes;
- unrestricted shell or subprocess execution;
- automatic skill/plugin import or execution;
- automatic PR submission or merging;
- standing or cross-request approval;
- billing/account changes or credential creation;
- policy, approval, route, OpenAPI, redaction, or Foundation Gate bypass;
- raw prompt, response, provider payload, or local-path persistence; or
- public release, production authority, or claims of human-like
  self-awareness.

## 13. Definition Of Done

The program is complete only when:

1. every phase is merged and verified on exact current main;
2. the quality and performance thresholds are met with an inspectable corpus;
3. ordinary chat retains the no-tool fast path and conversational behavior;
4. paired same-model evaluation proves ordinary-chat quality is non-inferior
   within the accepted threshold and reports its statistical uncertainty;
5. relevant tools can be discovered from meaning and typed capability evidence,
   not only exact commands;
6. familiarity, availability, authority, and outcome truth are distinct;
7. unsupported and uncertain states fail closed without fabricated capability;
8. the local model remains the language/reasoning engine;
9. no new authority was implied by the plan or implementation;
10. shadow promotion, safe-disable, corrupt-index fallback, and rollback are
    proven without replacing or reconfiguring the local model;
11. docs, CLI/API parity, redaction, and evidence are current; and
12. the queue may proceed to the final GoatCitadel comparison.
