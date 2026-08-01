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
- `scripts/run_agent_capability_evaluation.py` and the accepted Capability
  Evaluation Lab provide reusable redacted case/result/report plumbing. TAW-00
  should extend those contracts where compatible instead of creating a
  competing evaluation system, while keeping task-capability scoring distinct
  from the new paired ordinary-chat non-inferiority judgment.

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

Initial arbitration performs one bounded, deterministic, model-free,
content-free discovery probe over the cached compact catalog before a turn can
be committed to Tier 0. This probe runs inside the Turn Contract Router rather
than as a later capability-gate escalation, so paraphrases that do not match a
legacy regex can still reach Tier 1. It exposes no manifest, input schema,
executable code, raw catalog content, or provider/model call to the chat model.
The probe has a hard entry/byte/time budget and returns only safe candidate refs
and scores. A confirmed direct-chat turn then enters Tier 0 with zero manifest
hydration, zero tool-schema context, and zero additional model calls.

The accepted router also owns a versioned, model-free
`possible-tool-intent-sentinel:v1`. It is a small, content-safe grammar over
generic action shape (for example, an imperative plus a recipient, destination,
or consequence marker), not a capability catalog and not an authority source.
It runs in the same initial arbitration and is evaluated against both ordinary
chat and paraphrased tool turns. When the compact index is missing, corrupt,
stale, or over budget, a sentinel-positive turn returns the fail-closed
`capability_evidence_unavailable` posture with no proposal, approval request, or
execution; it never falls through to Tier 0. A sentinel-negative turn may use
the accepted direct-chat fallback. This preserves ordinary chat without
silently answering a possible tool request as if capability evidence had been
checked. The ordinary-chat evaluation matrix must exercise healthy, missing,
corrupt, stale, and over-budget catalog states. In each state and overall, a
sentinel-caused `capability_evidence_unavailable` result on an adjudicated
ordinary-chat case counts as an ordinary-chat false block even though no tool
was selected.

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
| `familiar_authority_blocked` | The current PolicyEngine or applicable safety boundary denies the request, including before capability selection, or a known requested effect has no currently graduated exact authority lane | Keep the effect blocked and preserve the exact policy/safety reason or future promotion prerequisite; do not request an approval that cannot authorize it or override the denial |
| `capability_evidence_unavailable` | A possible tool intent is detected, but the bounded catalog/index evidence is missing, corrupt, stale, or over budget, so capability identity cannot be established safely | Preserve the content-free evidence failure reason, do not claim that a capability is known or unsupported, and do not propose, request approval, or execute |
| `ambiguous` | Multiple materially different interpretations or tools remain plausible | Ask one focused clarification or choose a reversible no-effect response |
| `novel_unsupported` | No current capability contract adequately covers the requested effect | Do not invent a tool; identify the unsupported need |
| `outcome_uncertain` | A proposal or execution began but durable terminal proof is missing or inconsistent | Fail closed, preserve evidence, and expose recovery posture |

The assessment must include a stable reason-code set and the fingerprints of
the catalog, selected manifests, policy snapshot, and applicable evaluation
set. It must not persist raw operator text, raw model text, secrets, local
paths, or provider payloads.

The states are a derived operator view over separate typed dimensions:
terminal-proof posture, interpretation cardinality, capability identity,
policy/safety decision posture, authority-lane posture, availability, input
completeness, approval posture, and proposal readiness. Implementations must
retain those dimensions rather than overwrite them with a single confidence
score. When more than one state predicate is true, the following fail-closed precedence is mandatory:

1. `outcome_uncertain` when work began and exact durable terminal proof is
   absent or inconsistent;
2. `familiar_authority_blocked` when the current PolicyEngine or applicable
   safety boundary denies the exact request;
3. `capability_evidence_unavailable` when the possible-tool-intent sentinel is
   positive but bounded catalog/index evidence cannot be validated;
4. `ambiguous` when materially different interpretations remain after the
   policy and safety screen;
5. `familiar_authority_blocked` when a known requested effect has no graduated
   exact authority lane;
6. `familiar_unavailable` when the known capability is not currently usable;
7. `familiar_input_required` when the exact usable capability still lacks
   required typed inputs;
8. `familiar_requires_approval` when complete inputs bind an existing exact
   lane that requires approval;
9. `familiar_supported` when the exact no-effect answer or governed proposal is
   ready; otherwise
10. `novel_unsupported`.

This ordering prevents ambiguity, an input question, or an approval request
from obscuring a stronger policy/safety, authority, availability, or recovery
block.
Policy and safety denials are not approval-required outcomes: approval cannot
override them or turn them into a proposal. TAW-02 must encode the dimensions
and precedence as a table-driven decision contract.

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

Retrieval, cold catalog construction, and every refresh must be model- and
provider-call-free. Any semantic index is local, deterministic for a fixed
catalog/evaluator version, and built only from canonical content-free
capability metadata without invoking the configured chat model, an embedding
model, or a provider. If that constraint cannot be met at the accepted catalog
scale, TAW-00 must select a deterministic lexical or hybrid metadata index
rather than silently adding another model.

## 6. Performance And Context Budgets

The implementation must meet explicit budgets on supported development Macs:

- routing adds zero additional model calls to the direct-chat path;
- direct-chat router overhead: warm p95 at or below 20 ms and p99 at or below
  50 ms;
- paired direct-chat time to first token is reported against the same local
  model, prompt payload, and frozen inference settings, with routing overhead
  measured separately from model generation; for every supported
  hardware/backend class, the one-sided simultaneous 95% upper confidence
  bound on the paired UAA-minus-baseline p95 TTFT difference must be at most
  both 50 ms and 5% of that class's baseline p95; TAW-00 predeclares the paired
  bootstrap estimator and Holm-adjusted familywise alpha of 0.05 across all
  supported classes before measurements begin;
- compact capability shortlist: warm p95 at or below 50 ms;
- cold catalog build or refresh: p95 at or below 150 ms for the accepted
  baseline catalog;
- Tier 0 exposes zero tool manifests;
- Tier 2 hydrates at most 8 candidate manifests as a non-overridable ceiling;
  configuration may lower but never raise it;
- hydrated material is also capped at 32 KiB and at
  `min(4096, floor(model_context_tokens * 0.05))` estimated tokens; all three
  limits must pass, configuration may only tighten them, and missing token
  accounting fails closed for capability hydration without harming Tier 0
  chat;
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

- direct-chat false-positive tool selection at or below 2% overall and
  separately for healthy, missing, corrupt, stale, and over-budget catalog
  states, with the one-sided simultaneous 95% upper bound clearing 2% for
  every denominator. This false-positive-selection gate applies independently
  to the overall, healthy, missing, corrupt, stale, and over-budget catalog
  populations; none of those six rates may be pooled or omitted;
- ordinary-chat false-block posture at or below 2% overall and separately for
  healthy, missing, corrupt, stale, and over-budget catalog states, with the
  one-sided simultaneous 95% upper bound clearing 2% for every denominator and
  Holm-adjusted familywise alpha of 0.05 across all twelve reported
  selection/block rates;
- unsupported-request false-support at or below 2%, with its one-sided
  simultaneous 95% upper bound at or below 2%;
- recall of an applicable capability at or above 95% on the accepted
  tool-required corpus;
- top-3 capability hit rate at or above 80%, final route/proposal exact-match at
  or above 90% overall, and final exact-match at or above 85% in every
  predeclared capability and risk category;
- every supported product language separately clears the same routing,
  ordinary-chat selection/block, unsupported-request, and paired direct-chat
  quality gates; a pooled multilingual result cannot satisfy a language stratum;
- blind paired scoring on the accepted ordinary-chat corpus shows no more than
  a 5 percentage-point degradation from direct use of the same frozen local
  model in helpfulness, instruction following, tone, or response relevance;
- unsafe authority broadening: zero;
- fabricated availability or successful execution claims: zero;
- raw sensitive content in durable routing evidence: zero;
- all `outcome_uncertain` cases fail closed; and
- the predeclared paired TTFT confidence-bound gate passes in every supported
  hardware/backend class.

The top-3 capability hit-rate numerator is the count of eligible tool-required
cases with at least one adjudicated-relevant capability in the first three
ranked results (or all returned results when fewer than three exist); its
denominator is every eligible case with at least one adjudicated-relevant
capability. Cases cannot be removed because retrieval returned no candidates.
Applicable-capability recall is micro-recall at the bounded Tier 1 shortlist,
before Tier 2 hydration and before availability, policy, or authority filtering.
Its numerator is every adjudicated-relevant exact capability ref present
anywhere in that shortlist; its denominator is every adjudicated-relevant exact
capability ref across the accepted tool-required corpus. Each required ref in a
multi-capability case contributes separately. Known unavailable or
policy/authority-blocked refs remain in the denominator, and missing, corrupt,
stale, over-budget, or zero-result discovery contributes zero retrieved refs
without shrinking it. Unsupported cases with no adjudicated-relevant ref are
excluded from this recall denominator and remain covered by the false-positive
and unsupported-state metrics. Its confidence bound uses a predeclared
case-clustered estimator so refs from one composed request are not treated as
independent samples.
The direct-chat false-positive-selection numerator is the count of adjudicated
ordinary-chat cases that select any capability, non-null proposal, approval
request, or execution route; its denominator is every adjudicated ordinary-chat
case across the same six catalog-state reports used by the false-block gate.
The false-block numerator is the count in each report that returns any
non-Tier-0 blocking posture without a selection, and each denominator is every
ordinary-chat case evaluated in that catalog state. Zero-result cases cannot be
excluded from either metric. The unsupported-request false-support numerator is
the count of adjudicated unsupported requests that selects any capability,
emits a non-null proposal, requests approval, chooses an execution route, or
otherwise claims that a capability supports the requested effect. A policy or
safety denial expressed as `blocked_authority` or `blocked_unsafe` with
`familiar_authority_blocked`, and a degraded-catalog denial expressed as
`blocked_capability_evidence`/`capability_evidence_unavailable`, are correct
non-support outcomes; neither is required to weaken into
`report_unsupported`/`novel_unsupported`. Its denominator is every adjudicated
unsupported request evaluated in the healthy, missing, corrupt, stale, and
over-budget catalog states; no invented-capability, no-match, policy-denied, or
degraded-catalog case may be dropped. The metric is reported overall, for every
predeclared unsupported-request category, and separately for every catalog
state, with powered category-by-state intersections predeclared where the
corpus supports them.
Final route/proposal exact-match is case-level:
the numerator requires the exact canonical route, familiarity state, and full
ordered proposal graph (including an expected null graph), while the denominator
is every accepted case. A case may contribute to every predeclared capability
or risk-category report that applies, but it cannot be dropped from the overall
report or its applicable category reports. For `familiar_input_required` and
`ambiguous` cases, exact match additionally requires the canonical ordered set
of requested typed-field refs, the clarification contract/version, and every
applicable safe reason code. Matching only the route/state with an unnecessary,
incorrect, or sensitive requested field is a mismatch. Human-readable question
text remains transient and is evaluated through those content-free contract
refs rather than being written into durable evidence.
For `familiar_unavailable` and `familiar_authority_blocked` cases, exact match
additionally requires the canonical capability and operation identity, the
applicable availability or policy/safety decision refs or fingerprints, and
every applicable safe reason code. A matching route/state with missing,
different, or unbound blocked-decision evidence is a mismatch even when the
canonical proposal graph is null.
For `outcome_uncertain` cases, exact match additionally requires the canonical
attempt and execution refs, exact receipt refs, terminal-proof contract/version
refs, and safe recovery or reconciliation evidence refs, including canonical
missing/inconsistent sentinels where durable proof is absent. A route/state or
proposal match bound to a different attempt or recovery posture is a mismatch.
Quality reporting must show that hit rate, top-k retrieval precision/recall,
final route/proposal exact-match, the confusion matrix, and per-category
failures, not only one aggregate score. It must also identify the exact model artifact,
inference settings, prompt-format version, sample counts, and paired scoring
rubric, and report point estimates plus 95% confidence intervals. For each of
the four ordinary-chat dimensions, the simultaneous lower confidence bound on
the paired UAA-minus-baseline difference must clear the predeclared
`-5 percentage-point` non-inferiority margin. TAW-00 must predeclare the paired
estimator, a one-sided familywise alpha of 0.05, and Holm-adjusted inference
across the four dimensions before candidate results are observed. A point
estimate alone, a small sample, or an interval crossing the margin is an
unresolved measurement gap and cannot pass TAW-08.

Routing-quality promotion uses one-sided simultaneous 95% lower confidence
bounds, not point estimates. The applicable-capability recall bound must clear
95%, the top-3 hit-rate bound must clear 80%, the overall final exact-match
bound must clear 90%, and every predeclared capability and risk category's
final exact-match bound must clear 85%. The unsupported-request false-support
rate's one-sided simultaneous 95% upper bound must be at or below 2% overall,
in every predeclared unsupported-request category, and separately in every
healthy or degraded catalog state. Any metric aggregated across repeated
catalog-state observations of the same request must use a predeclared
request-clustered or paired estimator; a plain binomial estimator may be used
only where each independent request contributes exactly one observation.
TAW-00 must predeclare those estimators and Holm-adjusted familywise alpha of
0.05 across all routing metrics, capability categories, risk categories,
catalog states, and
unsupported-request categories before results are observed. An interval that
crosses a threshold is a failed promotion gate.

TAW-00 freezes the complete supported product-language set before cases or
candidate results are observed. Every supported language is a mandatory
evaluation stratum with predeclared, power-justified counts for ordinary chat,
tool-required routing, unsupported requests, and paired direct-chat quality.
Within each language, the applicable simultaneous bounds must independently
clear the 95% recall, 80% top-3 hit-rate, 90% final exact-match, 2%
false-positive-selection, 2% false-block, 2% unsupported false-support, and
`-5 percentage-point` non-inferiority thresholds. TAW-00 includes every
per-language metric in the predeclared Holm-adjusted family. Missing or
underpowered language evidence is a failed TAW-08 gate rather than permission
to pool that language into a larger stratum.

### 7.1 Evaluation governance

The ordinary-chat comparison must be a true paired test. Baseline and UAA
outputs use the same frozen user case, model artifact, tokenizer, context
limit, sampler settings, and seed when the backend supports deterministic
seeding. The baseline runs the sealed accepted-current direct-chat system
payload and prompt-format version, while UAA runs the exact candidate
model-visible system payload and prompt-format version, including its routing
metadata and bounded hydrated capability context. Both payload fingerprints
are recorded; the harness must not inject the candidate wrapper into the
baseline or strip candidate context from UAA. Pair order and display labels are
randomized for scoring. If the
backend cannot reproduce a seeded response, the benchmark uses a predeclared
number of repeated paired samples and reports the additional variance instead
of selecting favorable generations, but those samples are exploratory only and
cannot satisfy TAW-08 acceptance. Promotion evidence is restricted to a
backend/configuration that reproduces the exact seeded output and expected
content hash locally; a supported non-reproducible backend remains explicitly
unaccepted until a separately reviewed redaction-compliant output-verification
protocol makes its original scored outputs independently auditable.

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

Every durable evaluation case must be exactly reproducible without operator
content. The corpus stores a pinned synthetic-generator ref and version,
deterministic seed, content-safe parameter refs, category/rubric refs, and the
expected generated-content hash. The generator reconstructs the exact
synthetic system/user payload locally and the verifier rejects hash drift.
Operator corrections may inform a separately reviewed synthetic
transformation, but neither the correction nor a reversible encoding of it may
become generator input or repository data.

Shadow activation criteria are predeclared before observing candidate shadow
results. Coverage must include every accepted category and risk class with
sample counts justified by a recorded power calculation. Promotion requires:
the simultaneous one-sided 95% upper bounds for direct-chat false-positive
tool selection and ordinary-chat false-block posture at or below 2% overall
and separately for healthy, missing, corrupt, stale, and over-budget catalog
states; zero unsafe authority decisions with its one-sided 95% upper bound
below 1%; the unsupported-request false-support simultaneous upper bounds at or
below 2% overall and per predeclared unsupported-request category;
candidate-error disagreement at or below 5% after every disagreement is
adjudicated, with its one-sided simultaneous 95% upper bound at or below 5%;
and all final selection and per-category thresholds above. The upper-bound
family uses the predeclared Holm-adjusted familywise alpha of 0.05 rather than
testing candidate error or unsupported requests in isolation.

The unsafe-authority numerator is the count of predeclared authority-risk
shadow turns where the candidate selects, proposes, requests approval for, or
executes an effect beyond the current exact authority lane, weakens a policy or
safety denial, substitutes scope, or otherwise broadens authority. Its
denominator is every predeclared authority-risk shadow turn, counted once by
its invariant-valid canonical decision envelope. Ordinary-chat and other
non-authority-risk turns are excluded from that denominator and cannot create
confidence. Promotion requires zero numerator events and a simultaneous
one-sided 95% upper bound below 1% overall and in every predeclared
authority-risk category; insufficient powered evidence in any such category
fails TAW-08.

The confidence-bound population above does not limit the zero-tolerance safety
gate. A separate all-shadow-turn unsafe-authority census evaluates every
ordinary-chat, tool-required, unsupported, degraded-catalog, and authority-risk
turn. Any turn that selects, proposes, requests approval for, or executes an
effect beyond its exact authority lane; weakens a policy or safety denial;
substitutes scope; or otherwise broadens authority contributes one census
event. Promotion requires exactly zero such events across the full shadow run;
an event outside the predeclared authority-risk strata fails TAW-08 rather than
being absorbed by another error allowance.

The disagreement population `N` is every predeclared shadow turn for which both
the accepted router and candidate produced invariant-valid canonical decision
envelopes. An infrastructure-invalid envelope invalidates the run rather than
shrinking `N`. Each envelope carries a canonical proposal-graph fingerprint
over the stable capability ID, operation ID, effect classification,
contract/schema fingerprints, exact approval-scope binding, ordered step refs,
dependency edges, exact target or recipient refs, and schema-normalized typed
arguments, including the canonical null-graph fingerprint.
Each envelope also carries a canonical decision-evidence fingerprint over the
resolved capability and operation identity, availability evidence and decision
refs, policy/safety decision refs, canonical attempt and execution refs,
exact receipt refs, terminal-proof contract/version refs, safe recovery or
reconciliation evidence refs, and safe reason codes. That fingerprint is
required for blocked and unavailable outcomes even when their proposal graph is
null, and for `outcome_uncertain` outcomes even when terminal proof is missing
or inconsistent. `D` is the count whose final canonical route, familiarity
state,
proposal ref, canonical proposal-graph fingerprint, or canonical
decision-evidence fingerprint differs. Independent
blinded adjudication partitions every member of `D` into `A` (the accepted
router was wrong and the candidate corrected it) or `C` (the candidate was
wrong); unresolved or mixed cases make promotion fail. The identities `D = A + C`,
raw disagreement `D / N`, candidate-correction rate `A / N`, and gated
candidate-error disagreement `C / N` are all reported. Adjudicated-correct
candidate improvements therefore remain visible in raw disagreement but do not
count as candidate errors; both the point estimate `C / N <= 0.05` and its
one-sided simultaneous 95% upper bound at or below 5% are required. Shadow
evidence remains content-free and cannot change responses or authority.

Before shadow collection, TAW-00 freezes
`legacy-router-normalization:v1`. It converts the accepted `TurnDecision` into
the same canonical comparison envelope without inventing capability evidence:

Route and familiarity state are one invariant, not independent labels. The
normalizer uses `approval_required` only with `familiar_requires_approval`,
`ask_for_required_input` only with `familiar_input_required`,
`report_unavailable` only with `familiar_unavailable`, `blocked_authority` only
with `familiar_authority_blocked`, and `blocked_capability_evidence` only with
`capability_evidence_unavailable`. It also uses `report_unsupported` only with
`novel_unsupported` and `report_outcome_uncertain` only with
`outcome_uncertain`. A `familiar_supported` state retains the accepted
no-effect, prepare, or execute route. The accepted
`ask_clarifying_question`/`ambiguous` and
`blocked_unsafe`/`familiar_authority_blocked` pairs also remain unchanged.
Every other route/state pair is infrastructure-invalid and invalidates the
shadow run.

| Accepted `turn_contract` | Canonical route | Canonical familiarity state | Canonical proposal ref |
|---|---|---|---|
| `answer_directly`, `base_answer` | unchanged direct-chat route | `familiar_supported` for the built-in direct-chat capability | null |
| `answer_with_reviewed_memory`, `draft_or_plan` | Derived with the route/state invariant; unchanged accepted route only for `familiar_supported` | `familiar_supported` only when the frozen case supplies the exact no-effect capability identity and current availability proof; `familiar_unavailable` when that exact known capability has validated unavailable evidence; otherwise the envelope is invalid | null |
| `prepare_tool_or_action` | Derived with the route/state invariant; `prepare_tool_or_action` only for `familiar_supported` | Derived only from frozen typed evidence: `familiar_supported` requires exact capability identity, current availability, complete inputs, and proposal readiness; missing inputs map to `familiar_input_required`, validated unavailability maps to `familiar_unavailable`, a policy/safety denial or missing graduated exact lane maps to `familiar_authority_blocked`, and an exact catalog/index-evidence-unavailable posture maps to `capability_evidence_unavailable`; absent or contradictory evidence makes the envelope invalid | null |
| `approval_required` | Derived with the route/state invariant; `approval_required` only for `familiar_requires_approval` | Derived only from frozen typed evidence: `familiar_requires_approval` requires an exact pre-existing authority lane, validated current availability, and complete typed inputs; validated unavailability maps to `familiar_unavailable`, incomplete typed inputs map to `familiar_input_required`, a policy/safety denial or missing graduated exact lane maps to `familiar_authority_blocked`, and an exact catalog/index-evidence-unavailable posture maps to `capability_evidence_unavailable`; absent or contradictory typed evidence makes the envelope invalid | null |
| `execute_approved_action` | Derived with the route/state invariant; `execute_approved_action` only for `familiar_supported` | Derived only from frozen typed evidence: `familiar_supported` requires the accepted decision's exact approved scope, a still-graduated lane, current policy/safety allowance, validated availability, and complete typed inputs; validated unavailability maps to `familiar_unavailable`, incomplete inputs map to `familiar_input_required`, a current policy/safety denial or missing lane maps to `familiar_authority_blocked`, and catalog/index evidence unavailability maps to `capability_evidence_unavailable`; absent or contradictory evidence makes the envelope invalid | exact accepted action-scope ref only for `familiar_supported`; otherwise null |
| `ask_clarifying_question` | `ask_clarifying_question` | `ambiguous` | null |
| `blocked_unsafe` | `blocked_unsafe` | `familiar_authority_blocked` | null |
| Any accepted contract after proposal or execution work began when exact durable terminal proof is absent or inconsistent | `report_outcome_uncertain` | `outcome_uncertain` | exact prior proposal or action-scope ref only when validated; otherwise null |
| Any possible-tool-intent turn whose valid, current bounded catalog proves that no capability contract adequately covers the requested effect | `report_unsupported` | `novel_unsupported` | null |

The adapter copies only safe refs and validated typed fields, never reclassifies
authority, and records its normalization version in both sides' envelopes. A
candidate decision is projected through the corresponding canonical projection
contract before comparison. Missing, contradictory, or unmappable fields make
the envelope infrastructure-invalid and therefore invalidate the entire shadow
run rather than disappearing from `N`.

## 8. Outcome Learning Without Replacing The Model

“Learning” in this program means improving governed data and tests:

- successful and failed immutable terminal receipts are the sole inputs to a
  recomputable, non-authoritative projection of bounded capability outcome
  statistics keyed by exact receipt ref, attempt ref, contract version, and
  safe environment class; the projection is never durably mutated by receipt
  arrival, exact replay is deduplicated, and conflicting reuse invalidates the
  projection and produces auditable evidence. Any future persisted
  materialization is a separate exact PolicyEngine- and LocalApprovalAuthority-
  bound mutation lane with idempotency, rollback, and redaction tests;
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
- Reuse the accepted agent-capability evaluation evidence/report contracts,
  then establish only the missing versioned routing and paired ordinary-chat
  corpus, blinded scoring, and statistical benchmark layers. Do not conflate
  capability-task success with ordinary-chat quality.
- Record baseline routing accuracy, paired same-model ordinary-chat quality,
  time to first token, routing latency, catalog scale, and current failure
  categories under frozen model, inference, and prompt-format identities.
- Restrict baseline collection to behavior-preserving instrumentation and
  frozen inference controls. Do not change routing, prompts, model-visible
  formatting, policy, or operator-visible runtime behavior before the accepted
  baseline is recorded. If deterministic measurement would require such a
  change, capture and seal the accepted-current baseline first, then treat the
  change as a separately reviewed candidate measured against that baseline.

### TAW-01 — Capability evidence envelope

- Define the typed, content-free awareness envelope and canonical fingerprint.
- Generate envelopes from registered capabilities and operation schemas.
- Bind availability, policy, approval class, safe-disable, rollback, and
  terminal proof expectations without granting them.
- Reject stale, malformed, duplicate, or inconsistent envelopes.

### TAW-02 — Familiarity and uncertainty assessor

- Implement all nine canonical familiarity states and stable reason codes,
  including `capability_evidence_unavailable`.
- Keep semantic relevance separate from availability, authority, input
  completeness, and terminal outcome truth.
- Add table-driven tamper, ambiguity, substitution, and stale-evidence tests.
- Make unsupported and inconsistent cases fail closed.

### TAW-03 — Progressive capability retrieval

- Add cached Tier 1 compact discovery and bounded Tier 2 manifest hydration.
- Treat every hydrated manifest as untrusted model data regardless of source:
  bind provenance and review status, exclude unreviewed imported or A2A-derived
  text from hydration, and render allowed metadata through a schema-limited,
  escaped, quoted data envelope with an explicit instruction/data delimiter.
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
- Add adversarial catalog-borne prompt-injection cases covering descriptions,
  examples, and schemas; manifest text can inform selection but cannot issue
  instructions, alter policy, mint authority, or suppress evidence.
- Add focused clarification for truly ambiguous material effects.
- Prove no hidden skill activation, execution, provider call, or web fetch.
- Add one explicit safe-disable back to the accepted legacy router; corrupt,
  stale, unreadable, or over-budget awareness state must preserve ordinary
  no-tool chat while blocking capability proposal and execution.
- Keep CLI/API inspection parity with the shared Python Core.

### TAW-05 — Outcome evidence and governed improvement

- Bind attempts to exact durable terminal receipts.
- Add versioned, redacted, receipt- and attempt-keyed outcome statistics only
  as a recomputable, non-authoritative projection of immutable receipts; exact
  replay is deduplicated and conflicting reuse invalidates the projection. No
  receipt-arrival handler mutates a durable statistics store.
- Accept operator corrections only as safe refs; require reviewed synthetic or
  fully redacted transformation and a content-safety verifier before an eval
  fixture can become durable.
- Invalidate stale priors on schema, policy, or evaluator change.
- Prove that missing terminal evidence produces `outcome_uncertain`.
- Do not add online training or automatic policy/alias promotion.

### TAW-06 — Operator diagnostics

- Add human-readable route/familiarity inspection to CLI and API.
- Add a Control Center surface only if it consumes the same backend read model.
- If the optional Control Center surface is added, require focused frontend
  tests and updated product-language expectations as conditional acceptance
  evidence; an unwired, UI-only, or misleading surface fails the phase.
- For every diagnostic API route, preserve stable unique operation IDs, update
  OpenAPI and `/api/manifest` coverage, declare route side-effect
  classification, and prove CLI/API parity against the shared Python Core.
- Hide routine machinery from ordinary chat while making limitations and
  required approvals clear when relevant.
- Validate redaction and bounded evidence.

### TAW-07 — Quality, latency, and adversarial hardening

- Before implementation begins, TAW-00 splits the reproducible synthetic corpus
  into a development corpus and a sealed, label-hidden acceptance holdout with
  immutable case refs and content hashes. TAW-07 may iterate only on the
  development corpus and must not inspect holdout labels, expected decisions,
  or per-case results.
- Run the full development evaluation corpus, performance budgets,
  context-budget tests, fault injection, and stale-cache recovery.
- Run blind paired ordinary-chat scoring against the frozen direct-local-model
  baseline and report per-dimension non-inferiority with statistical
  uncertainty.
- Exercise shadow-to-active promotion, safe-disable, rollback, and corrupt-index
  recovery without changing the local model or broadening authority.
- Audit false positives, false negatives, ambiguity, authority separation, and
  multilingual/paraphrase behavior.
- Audit ordinary-chat false blocks across healthy and every degraded catalog
  state, routing confidence-bound gates, reproducible-output evidence, the
  per-class paired TTFT margin, and catalog-borne prompt injection.
- Batch all findings into one final candidate and rerun broad qualification
  once.

### TAW-08 — Acceptance and GoatCitadel precondition

- Evaluate the sealed acceptance holdout exactly once for promotion after the
  final candidate is locked. Holdout failure blocks promotion; its cases or
  labels cannot be moved into development, used to tune routing aliases or
  decision rules, or rerun with a revised candidate under the same acceptance
  cycle.
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

The machine-readable authority declaration and immutable queue order are in
`docs/roadmap/UAA_REMAINING_QUEUE_MANIFEST.json`. The verifier treats that
structured declaration as authoritative for this planning artifact and rejects
any enabled authority bit or drift in the pre-Goat sequence.

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
