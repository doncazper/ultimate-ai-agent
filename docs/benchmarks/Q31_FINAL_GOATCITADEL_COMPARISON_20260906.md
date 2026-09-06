# Q31 Final UAA / GoatCitadel Comparison

Status: final comparison candidate for Queue V2 Q31, pending protected merge,
post-merge qualification, and the canonical Queue V2 terminal receipt.
Comparison only; no repair, provider call, model call, competitor-code import,
runtime mutation, production claim, or automatic authority grant is included.

Queue truth: this is the final comparison candidate; Q31 remains pending until protected merge, post-merge qualification, and the Queue V2 terminal receipt complete. Q32 remains blocked until that terminal receipt exists.

## Scope and exact baselines

This comparison evaluates the two repositories as governed agent/operator
systems. It does not score base-model intelligence because the same model,
provider, prompts, environment, and repeated task protocol were not run in both
systems.

| System | Exact source | Version truth | Checkout used |
|---|---|---|---|
| UAA | `git-sha:817d84d8f0e4660de5dfcff9cb215e5330d8714c` (`main`) | package `0.104.0`; the historical `v0.104.0` tag is not this commit | clean isolated worktree |
| GoatCitadel | `git-sha:41d0f2e52910c60c39fa0b788042638eddf302e5` (`origin/main`) | root `0.1.0-rc.1`, Mission Control `1.0.0`; `v1.0.0` is an older ancestor | clean isolated worktree |

Report binding: UAA `git-sha:817d84d8f0e4660de5dfcff9cb215e5330d8714c`; GoatCitadel `git-sha:41d0f2e52910c60c39fa0b788042638eddf302e5`; scores `UAA=70` and `GoatCitadel=73`; independent validation `not_performed`; controlled model task trials `not_measured`; residual owners `Q33,Q36`; Q31 repair authority `denied`.

The July comparison is a longitudinal reference only. Its decimal rubric and
older commits are not carried forward as verified scores. Current values are
calculated from
`docs/benchmarks/q31_goat_maturity_input_20260906.json` with the
repository-local `goat-comparison-maturity.v2` compatibility scorer whose exact
file digest is bound in that ledger. All independent-validation gates remain
zero; self-tests are not acceptance. Every GoatCitadel repository path used as
score evidence is also bound to its exact file SHA-256 in
`docs/benchmarks/q31_goat_evidence_manifest_20260906.json`, derived from the
pinned GoatCitadel checkout.

## Executive profile

The evidence-gated repository maturity score is **GoatCitadel 73, UAA 70**.
Both are in the rubric's **Strong system** band. The three-point reported gap
(3.6290 raw) is a slight GoatCitadel lead, driven by its visible chat shell,
code workflow, provider surface, and extension breadth. It is not a controlled
task-performance, raw-intelligence, production-readiness, or general UX winner.

The most useful current product in the one directly observed clean-start,
no-provider scenario was GoatCitadel: it offered a safe demo, full chat shell,
thread switching, persistent drafts, and a truthful disabled Send state. UAA's
ordinary chat was command-palette discoverable but remained hidden behind
incomplete backend-truth evidence, and Setup later degraded to unavailable.
This is a formative observation by one evaluator, not a comparative usability
experiment.

For a 12-month governed founder/operator foundation, UAA retains the stronger
strategic spine: exact request-bound authority, fail-closed backend-truth
binding, content-free evidence, CLI/API contracts, and the accepted Q22 local
Qwen lane. GoatCitadel shows the stronger product-surface reference. The best
direction is to preserve UAA's Python-core authority model while making its
first loop as legible and recoverable as GoatCitadel's safe demo—not to merge
the projects or copy competitor implementation.

## Gate scorecard

Scores are out of 10. `Medium` confidence means code and focused test evidence
exist, but independent acceptance does not. The scorer caps partial status at 6
and unaccepted evidence at 8.

| Component (weight) | UAA | GoatCitadel | Skeptical gap |
|---|---:|---:|---|
| Reasoning (8) | 6 · Usable · partial · Medium | 6 · Usable · partial · Medium | Neither ran shared model tasks or recovery trials. |
| Planning (8) | 8 · Strong · implemented · Medium | 8 · Strong · implemented · Medium | Both have durable, tested orchestration; neither is independently accepted here. |
| Learning (8) | 6 · Usable · partial · Medium | 6 · Usable · partial · Medium | Reviewed adaptation was not observed through either direct chat. |
| Memory (9) | 8 · Strong · implemented · Medium | 8 · Strong · implemented · Medium | Both have provenance-oriented memory code and focused tests. |
| Communication (7) | 6 · Usable · partial · Medium | 8 · Strong · implemented · Medium | Goat exposed the clearer clean-start conversation shell. |
| Action/tool calling (9) | 8 · Strong · implemented · Medium | 6 · Usable · partial · Medium | Goat's current policy tests contradict legitimate approved/read actions. |
| Authority (10) | 8 · Strong · implemented · Medium | 8 · Strong · implemented · Medium | Both fail closed in inspected paths; no independent validation. |
| Code assistance (6) | 6 · Usable · partial · Medium | 8 · Strong · implemented · Medium | Goat exposes a code workbench; UAA's full code loop was not observed. |
| Research/web (5) | 6 · Usable · partial · Medium | 7 · Strong · implemented · Medium | No live web authority or controlled research task was granted. |
| Model/providers (6) | 6 · Usable · partial · Medium | 7 · Strong · implemented · Medium | Goat exposes a richer setup shell; Q31 made no provider call. |
| Evidence/audit (9) | 8 · Strong · implemented · Medium | 8 · Strong · implemented · Medium | Both have durable evidence designs; only UAA has the bound Q22 receipt here. |
| Safety/failure (10) | 8 · Strong · implemented · Medium | 8 · Strong · implemented · Medium | Goat's false-positive guard hurts action utility but remains fail closed. |
| Cockpit UX (7) | 6 · Usable · partial · Medium | 8 · Strong · implemented · Medium | UAA has a mobile overlap and clean-start chat gate; Goat's composer falls below the initial mobile fold. |
| CLI/API parity (6) | 8 · Strong · implemented · Medium | 8 · Strong · implemented · Medium | Both expose inspectable contracts; full surface parity was not revalidated. |
| Extensibility (6) | 6 · Usable · partial · Medium | 8 · Strong · implemented · Medium | Goat has a broader runtime SDK surface; UAA intentionally withholds plugin runtime authority. |
| Productized loop (10) | 6 · Usable · partial · Medium | 6 · Usable · partial · Medium | Neither produced a useful model result in the allowed no-provider run. |

Weighted raw totals are 69.8387 for UAA and 73.4677 for GoatCitadel. Rounded
reported totals are 70 and 73. The component gates, holds, evidence refs, and
blockers are machine-reproducible in the JSON ledger.

## Component analysis

1. **Reasoning.** UAA separates facts, assumptions, unknowns, and questions in
   `src/ultimate_ai_agent/core/intent/reasoning_truth.py`. GoatCitadel routes
   observable intent classes in
   `apps/gateway/src/services/model-router-decision-service.ts#L60-L126`.
   Neither result proves reasoning quality without the shared model-task run.
2. **Planning.** UAA's mission orchestrator binds budgets, approvals, and
   recovery. GoatCitadel's orchestration engine and durable boot-recovery tests
   cover long-running state. This is the strongest shared capability.
3. **Learning.** Both repositories have governed improvement/review machinery,
   but neither direct no-provider observation reached a reviewed learning
   outcome. Status remains partial.
4. **Memory.** UAA separates recall from truth and retains review requirements.
   GoatCitadel has a context composer and lifecycle service. Focused UAA tests
   and 38 Goat memory/contract tests passed.
5. **Communication.** UAA's chat contract explicitly blocks model output from
   minting tool, memory, web, connector, shell, action, approval, or production
   authority (`src/ultimate_ai_agent/core/chat/operator_surface.py#L23-L59`).
   Goat's threaded surface presents planning, tools, approvals, and code context
   inline (`apps/mission-control-next/src/features/threaded-surface/ThreadedModeControl.tsx#L23-L57`).
   The latter was more legible in the clean-start observation.
6. **Actions.** UAA's accepted Q22 evidence and current exact-head CI support
   the score of 8. GoatCitadel's tool coordinator is substantial, but 9 current
   policy tests fail because legitimate filesystem/presentation arguments are
   rejected as `structured_secret`. The rejecting guard is
   `packages/policy-engine/src/tool-executor.ts#L258-L270`; the approved replay
   expectation is `packages/policy-engine/src/engine.test.ts#L4761-L4775`.
7. **Authority.** UAA rechecks reservation fingerprints and persists denial on
   invalid budget state
   (`src/ultimate_ai_agent/core/authority/dispatcher.py#L1225-L1265`).
   GoatCitadel revalidates a stored pending approval before execution
   (`packages/policy-engine/src/engine.ts#L702-L765`). Both are strong but not
   independently accepted by this packet.
8. **Code assistance.** GoatCitadel includes visible Code mode/workbench and
   backend execution abstractions. UAA has exact code-action contracts, but Q31
   did not exercise an end-to-end code outcome, so its status remains partial.
9. **Research/web.** UAA's hybrid request is typed, two-attempt bounded, and
   exact-ref validated
   (`src/ultimate_ai_agent/core/web_access/hybrid_execution.py#L51-L80`).
   GoatCitadel has research and browser policy layers. No live network task was
   allowed, so neither receives empirical research credit.
10. **Models/providers.** GoatCitadel's route decision distinguishes tools,
    freshness, code, vision, and confirmation before direct chat
    (`apps/gateway/src/services/model-router-decision-service.ts#L60-L126`). UAA
    has an accepted Q22 founder-private Qwen 3.8 27B lane, but its direct Setup
    flow did not stay available. Q31 performed no model calls.
11. **Evidence.** UAA has content-free signed lifecycle evidence and a Q22
    terminal receipt. GoatCitadel can assemble and offline-verify signed run
    receipts (`apps/gateway/src/services/evidence-receipt-service.ts#L165-L220`).
12. **Safety.** Both deny uncertain execution. GoatCitadel's current
    overblocking defect is a reliability contradiction, not evidence of unsafe
    execution; it is therefore charged to Action rather than used to inflate or
    erase Safety.
13. **Cockpit UX.** GoatCitadel's safe demo, thread rail, readiness cards,
    route-block explanation, and responsive collapse are stronger today. UAA's
    truthful backend gate is valuable but its clean-start state prevents the
    ordinary first loop, and the 390x844 layout visibly overlaps one card.
14. **CLI/API.** UAA's route side-effect manifest classifies sensitive and
    external mutations (for example
    `src/ultimate_ai_agent/api/manifest.py#L965-L1009`). GoatCitadel exposes
    gateway routes, docs, and TUI tooling. Both are strong; exhaustive parity is
    outside this read-only comparison.
15. **Extensibility.** GoatCitadel provides a wider extension SDK and tool
    override surface. UAA's narrower extension catalog is deliberate: it does
    not grant plugin runtime import or broad connector authority.
16. **Product loop.** UAA has a typed proposal → approval → orchestration →
    completion → review-only memory contract; its result keeps raw operator
    input/path out of evidence
    (`src/ultimate_ai_agent/core/control_center/founder_loop_mission.py#L478-L549`).
    The direct clean start could not reach it. GoatCitadel's demo reached chat
    but could not produce a model outcome without a provider and returned to
    onboarding after refresh. Both remain partial.

## Direct product observation

The observation used desktop and real 390x844 viewports, keyboard navigation,
route transitions, a content-free draft, thread switching, and refresh. It did
not send prompts, call models/providers, invoke tools, grant approvals, or
perform external writes.

| Behavior | UAA | GoatCitadel |
|---|---|---|
| Clean start | Truthfully hid unverified state; ordinary chat remained evidence-incomplete | Offered safe local demo and then a full blocked chat shell |
| Chat discovery | Absent from primary navigation; found through command palette | Primary product surface after demo entry |
| Composer | Not rendered in the evidence-incomplete state | Rendered; content-free draft accepted; Send disabled |
| Draft/thread persistence | Not measurable because chat was gated | Persisted per thread across switching and refresh |
| Refresh recovery | Setup later degraded to unavailable | Returned to onboarding; one extra demo-open step restored the draft |
| Progress/actions | Messenger fixture disclosed that messages/actions were synthetic and blocked | Readiness, runtime, policy, context, thread, build, and activity areas visible |
| Mobile | Responsive columns, but runtime card overlapped work content | Collapsed navigation and stacked cards; composer below initial fold |
| Truthfulness | Strong exact-revision and evidence gating | Strong explicit no-provider route block |

The following required interaction dimensions were not silently omitted. They
remain explicit missing evidence for both systems because this comparison did
not grant provider/model send or active-run authority:

| Unexercised dimension | UAA | GoatCitadel | Reason |
|---|---|---|---|
| Streaming | not measured | not measured | No response stream existed. |
| Cancel/retry | not measured | not measured | No active execution existed to cancel or retry. |
| Interruption | not measured | not measured | No active execution existed to interrupt. |
| Steering | not measured | not measured | No active execution existed to steer. |
| Resumption | not measured | not measured | Draft recovery is not active-run resumption. |
| Restart | not measured | not measured | Process restart was not performed. |
| Accessibility | not measured | not measured | Keyboard navigation was observed, but no formal accessibility audit was performed. |
| Steps/time to useful outcome | not measured | not measured | No provider or model outcome was authorized. |

These missing states prevent the direct-surface observation from being read as
a complete usability, recovery, accessibility, or task-success evaluation.

Visual refs are content-free hashes:

- UAA desktop: `sha256:a1a9d01008d2ef9b6674f768bdf0df221f174ffb5a5583f89af69c3284a83a6a`
- UAA mobile: `sha256:f065dc43b29dba59d76a117fe5fd725da53447b251d0848c34535c5849fd741e`
- GoatCitadel desktop: `sha256:97fa42f14cd36287e23f590ab193f55d649ca864c889b812caaf78bd7e64cda6`
- GoatCitadel mobile: `sha256:af5d307012e375cfbe205fecdbbcc2acb03eb89962ba88396051007f1634d381`

No empirical product-experience winner is declared: the required repeated
identical tasks, multiple evaluators, accessibility measurements, and useful
outcome timings were not run. The one-evaluator formative result favors
GoatCitadel for clean-start chat legibility.

## Feature parity matrix

| Capability | UAA | GoatCitadel | Current evidence boundary |
|---|---|---|---|
| Intent/fact separation | implemented contract, partial product reach | implemented router, partial task proof | shared model trials absent |
| Decomposition | implemented mission planning | implemented orchestration | independent run absent |
| Plan revision | implemented and receipt-bound | implemented durable plans | no cross-system task |
| Ordinary chat | partial; clean start gated | implemented shell | no model send |
| Proposals | exact typed action proposal | tool/workflow proposals | no mutation allowed |
| Approvals | exact local authority | approval inbox/inline controls | no approval granted |
| Tool catalog | implemented | implemented | code/test inspection |
| Tool selection | governed eligibility | routed coordinator/policy | no tool call |
| Execution | accepted exact UAA slices | partial; policy regression present | Goat 9 focused failures |
| Code workflow | partial operator proof | visible Code workbench | no code task |
| Memory intake | governed and review-bound | implemented lifecycle | no live content intake |
| Memory correction | implemented contracts | implemented lifecycle | no direct correction trial |
| Evidence | signed/content-free receipts | signed/offline-verifiable receipts | self-validation only |
| Model routing | capability/readiness plane | richer visible router | no same-model trials |
| Local models | accepted Qwen 3.8 27B Q22 lane | configurable provider shell | no Q31 call |
| Web/research | governed bounded adapters | research/browser services | live authority withheld |
| Connectors/plugins | contracts/catalog, runtime blocked | broader SDK/runtime surface | no external write |
| Cockpit | founder surfaces, partial clean start | broad chat/operator shell | formative observation |
| CLI | first-class inspection paths | TUI/admin/tool commands | exhaustive parity absent |
| API/OpenAPI | typed manifest and classified routes | gateway routes/docs | source/test inspection |
| Safety | exact authority, fail closed | policy/auth, fail closed | independent review absent |
| Redaction | content-free evidence posture | structured secret redaction | Goat false positive present |
| Verification | full exact-head hosted CI plus focused tests | focused local suites | Goat policy suite non-green |

## Strengths, weaknesses, and missing capabilities

| System | Strongest evidence | Most important weakness | Missing proof |
|---|---|---|---|
| UAA | authority, evidence, safety, planning, CLI/API | clean-start chat and Setup are not currently a readable first loop | repeated independent founder tasks through the rendered shell |
| GoatCitadel | chat UX, surface breadth, code/provider/extension discoverability | secret guard falsely blocks legitimate approved/read actions; refresh returns demo to onboarding | independent controlled tasks and a green exact-head policy suite |

The Goat regression is reproducible at exact current main: one engine slice
reported 124 pass / 1 fail and a broader tool-executor slice reported 142 pass /
8 fail. All nine failures share the `structured_secret` false-positive family.
Chat UI (118 tests), gateway (75 tests), and memory/contracts (38 tests) passed.
UAA's focused comparison foundation reported 136 tests passed, and current
exact-head hosted CI is `github-actions:34021920751`.

## Reciprocal learning

| Direction | Pattern | Transfer | Disposition | Boundary / exit test |
|---|---|---:|---|---|
| Goat → UAA | safe demo onboarding with truthful route block | 9 | adapt in Q33 | Clean install reaches a useful explanation without credentials; Send stays disabled until exact readiness. |
| Goat → UAA | per-thread draft persistence and readable thread rail | 9 | adapt in Q33 | Content-free draft survives switching/refresh with an explicit recovery state. |
| Goat → UAA | collapsed mobile navigation and stacked readiness | 8 | adapt in Q36 | At 390x844 no status element overlaps the work surface. |
| Goat → UAA | very dense capability palette | 5 | study only in Q36 | Keep frequent founder actions fast without unavailable-capability noise. |
| UAA → Goat | exact backend revision/truth binding | 9 | adapt externally | Shell cannot assert readiness against an unbound backend. |
| UAA → Goat | exact authority plus content-free receipts | 9 | adapt externally | Receipts bind scope without prompt, response, credential, or local-path content. |
| Either direction | source code, branding, broad unsafe defaults | 0 | do not borrow | No copied competitor implementation or authority expansion. |

Do not merge the systems. Do not borrow GoatCitadel's broad runtime surface or
its current secret-argument heuristic. Defer live-provider, live-web,
connector-write, shell, and production comparisons until separately authorized
exact lanes exist.

## Recommendations and owners

| Rank | Recommendation | Impact | Effort | Risk | Owner | First step |
|---:|---|---|---|---|---|---|
| 1 | Make the UAA clean-start chat/setup loop readable without weakening backend truth | high | medium | medium | Q33 | Reproduce the evidence-incomplete → unavailable transition as a deterministic fixture. |
| 2 | Add original UAA per-thread content-free draft recovery | high | medium | low | Q33 | Define Python/API-owned persistence contract and UI-only presentation state. |
| 3 | Remove the 390x844 status-card overlap and reduce header density | medium | small | low | Q36 | Add a visual viewport regression at 390x844. |
| 4 | Keep equal Qwen/API controlled tasks blocked until a separate evaluation item is admitted | high | medium | medium | not admitted | Do not assign this work to Q32 or make calls under Q31. |
| 5 | Keep Goat's current tool-policy regression visible; do not compensate UAA scores for it | medium | external | low | external only | Upstream should narrow the false-positive detector and re-run exact focused tests. |

No Q31 finding authorizes its own repair. Q33 owns the clean-start loop, Setup
degradation, chat discoverability, and draft recovery. Q36 owns responsive and
interaction polish. Controlled performance evaluation has no queue owner and
remains blocked pending a separately admitted exact milestone. Q32 remains CRM
functional adoption only. Q34/Q35 receive no artificial work from this
comparison; news and vertical modules remain dependency-driven.

## Bounded 30-day plan

1. **Days 1–7, Q32:** only after Q31 has its protected merge, post-merge
   qualification, and Queue V2 terminal receipt, complete the accepted CRM
   adoption slice and its real founder-private lifecycle/recovery proof. Do not
   add model evaluation work.
2. **Days 8–14, Q33:** after Q32 is terminal, reproduce and repair the
   clean-start backend-truth/Setup transition, then add content-free draft and
   thread recovery without provider calls or new authority.
3. **Days 15–21, Q34:** after Q33 is terminal, complete the authorized-source
   News adoption loop. Reconcile Q26 in parallel only through its accepted
   queue contract so Q35 can become dependency-ready.
4. **Days 22–30, Q35 then Q36:** complete Q35 only after Q26 and Q34, then begin
   Q36 only after Q32 through Q35 are terminal. If those gates are not closed,
   defer Q36 rather than violating dependency order. Controlled model trials
   remain unmeasured pending a separately admitted evaluation item.

Stop after these finite owners. Do not turn the comparison into an open-ended
parity chase.

## Final verdict

GoatCitadel has a slight current repository-maturity lead, **73 to 70**, and a
clearly stronger formative clean-start chat presentation. UAA has the more
compelling governed founder-private foundation for the stated product direction
because its accepted authority/evidence spine is stricter and already bound to
the user's local Qwen target. Neither system is proven production-ready by this
packet, neither wins controlled task performance, and neither has independent
Q31 acceptance evidence.

Q31 can close only after its verifier confirms the exact baselines, scorer
output, redaction posture, direct-observation refs, residual owners, and
finite-scope language; the protected PR merges; post-merge qualification is
green; and the canonical Queue V2 terminal receipt is recorded. The next work
then belongs to the queue owners above—not to an unbounded comparison repair
loop.
