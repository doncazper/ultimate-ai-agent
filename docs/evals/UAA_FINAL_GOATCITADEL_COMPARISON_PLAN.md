# UAA Final GoatCitadel Comparison Plan

Status: recovered final evaluation contract for Queue V2 Q31. Read-only unless
a separately scoped UAA-native repair is admitted.

This plan preserves the original comparison intent: evaluate the systems as AI
agent/operator platforms, not as base-model weight repositories. It grants no
provider/model call, competitor-code import, repository mutation, threshold
change, runtime authority, production claim, or automatic gap-fix authority.

## Entry Gate

Do not start the final comparison until:

- Q05 Capability Evaluation Lab has stable repeatable cases as the accepted
  evaluation foundation;
- the exact Queue V2 dependency set—Q10, Q21, Q22, Q24, Q25, Q28, Q29, and
  Q30—has terminal slice evidence or an explicit reviewed cancellation where
  the queue contract permits one;
- Finance/Q26 evidence is included when the comparison rubric explicitly binds
  it, but Q26 does not block core parity merely because it remains nonterminal;
- both repositories can be bound to exact current revisions;
- any uncommitted or unclassified repository state is excluded from scoring.

The final comparison is a closing measurement, not a mechanism for hiding
unfinished prerequisites inside one enormous repair cycle.

## Evidence Hierarchy

Score evidence in this order:

1. exact-revision runtime/evaluation results and accepted receipts;
2. focused tests and verifiers that exercise the claimed behavior;
3. implemented Python/TypeScript code and reachable CLI/API/UI surfaces;
4. stable contracts and configurations tied to implementation;
5. mock/fixture-only surfaces;
6. plans, roadmaps, screenshots, and claims.

Higher-ranked evidence can contradict lower-ranked evidence. Planning never
upgrades implementation status. If evidence is absent or conflicting, record
`unknown from available evidence` or `contradicted`; do not estimate upward.

## Status And Confidence

Every capability claim uses one status:

- `implemented`;
- `partial`;
- `planned`;
- `mock_only`;
- `blocked`;
- `deprecated`;
- `contradicted`;
- `unknown`.

Every numeric score includes `high`, `medium`, or `low` confidence with a short
reason. A polished UI with mock data can score well for visual design but not
for the underlying agent loop.

## Scoring Scale

| Score | Meaning |
|---:|---|
| 0 | no evidence |
| 1 | claim only |
| 2 | placeholder, mock, or roadmap only |
| 3 | thin partial implementation |
| 4 | partial implementation with weak integration |
| 5 | usable baseline with meaningful gaps |
| 6 | solid implementation with tests/docs |
| 7 | strong implementation with clear product surface and tests |
| 8 | very strong, coherent, tested, and operator-visible |
| 9 | excellent, mature, deeply integrated, and well governed |
| 10 | exceptional production-grade evidence across code, tests, UX, docs, and operations |

A score of 10 requires production-grade evidence; neither project receives it
from aspiration, local demos, or test-only adapters.

## Sixteen Components And Weights

| Component | Weight |
|---|---:|
| Reasoning and task understanding | 8 |
| Planning and orchestration | 8 |
| Learning and adaptation | 8 |
| Memory and context management | 9 |
| Communication and interaction quality | 7 |
| Action and tool calling | 9 |
| Autonomy and authority management | 10 |
| Code and implementation assistance | 6 |
| Research/web/external information handling | 5 |
| Model/provider management | 6 |
| Evidence, audit, and observability | 9 |
| Safety, security, and failure handling | 10 |
| UX as an AI cockpit | 7 |
| CLI/API parity | 6 |
| Extensibility and ecosystem | 6 |
| Productized agent loop | 10 |

Normalize the weighted total to 100. Do not score raw LLM intelligence unless
both systems have exact comparable model-evaluation evidence. Score how each
system uses models, prompts, memory, tools, approvals, orchestration, UI, APIs,
and evidence to produce intelligent operator behavior.

## Component Evaluation Questions

1. Reasoning: intent, ambiguity, decomposition, context, explanations, and
   separation of fact/assumption/unknown.
2. Planning: revision, durable workflow, task state, recovery, approvals, and
   long-running support.
3. Learning: intake, feedback, governed adaptation, provenance, correction,
   rejection, and reviewed outcomes.
4. Memory: short/long context, retrieval, provenance, quality, staleness,
   action binding, redaction, and deletion.
5. Communication: chat quality, readable status, blocked explanations,
   uncertainty, progressive disclosure, CLI/UI language.
6. Tools/actions: catalog, eligibility, selection, side-effect classification,
   approvals, idempotency, receipts, rollback, and results.
7. Authority: deny-by-default, exact scopes, escalation prevention, revocation,
   safe-disable, and explicit blocked states.
8. Code assistance: proposal/diff, validation, tests, hashes/receipts, sandbox
   controls, reviewability, and Git boundaries.
9. Research/web: gateway posture, source evidence, fetched-content trust,
   browser boundaries, and external-data influence on authority.
10. Models/providers: local support, abstraction, selection, cost/latency,
    truth posture, and separation of output from authority.
11. Evidence: timeline, audit, receipts, provenance, runtime visibility,
    redaction, inspection, and debugging.
12. Safety: auth/CORS/rate limits, secrets, shell/connector controls, bypass
    prevention, failures, reconciliation, and degradation.
13. Cockpit UX: readable knowledge/plans/actions/limits/approvals/memory/
    evidence; no raw JSON as the critical workflow.
14. CLI/API parity: inspectability, stable contracts, route classification,
    manifest/OpenAPI truth, and aligned tests.
15. Extensibility: plugins, connectors, skills/capabilities, catalogs, safety,
    developer experience, and ownership.
16. Productized loop: input -> understanding -> plan -> proposal -> approval ->
    result -> evidence -> memory, with honest usefulness today.

## Required Comparison Packet

The durable report must contain:

1. exact repository revision/baseline inventory;
2. executive ranking and normalized score;
3. 16-component scorecard with confidence/status/evidence/gap;
4. component-by-component skeptical analysis;
5. feature parity matrix covering at least intent, decomposition, plan
   revision, chat, proposals, approvals, tools, execution, code workflow,
   memory intake/review/correction, evidence, model routing, local models, web,
   connectors/plugins, cockpit, CLI, API, safety, redaction, and verification;
6. capability maturity table using None, Claimed, Mocked, Partial, Usable,
   Strong, and Mature;
7. direct strategic answers for current usefulness and 12-month foundation;
8. strengths, weaknesses, and missing-capability tables;
9. recommendations ranked by impact, effort, risk, owner, and first step;
10. explicit items each project should borrow, avoid, not merge, and defer;
11. residual gap ledger with exact UAA owner/queue destination;
12. final verdict and bounded 30-day improvement plan.

Important claims cite repository-relative files and line numbers in the report.
Durable evidence excludes raw prompts, responses, payloads, logs, credentials,
hostnames, usernames, and private local paths.

## Repair Policy

Comparison findings do not authorize fixes. A UAA repair must become a
separate child item with:

- one bounded native outcome;
- exact UAA owner and dependency;
- no competitor-code copy/import;
- tests/evals that prove the UAA contract;
- no test, verifier, threshold, or guardrail weakening;
- isolated branch/worktree and exact-head review evidence;
- explicit defer/intentional-exclusion option.

Run at most two finite repair/re-evaluation passes. Remaining gaps are routed
with evidence; Q31 must not become an endless parity chase.

## Final Acceptance

Q31 is complete when the exact-revision packet is reproducible, every score is
status/confidence/evidence bound, unknowns and intentional exclusions remain
visible, residual UAA gaps have owners, affected verifiers pass at exact head,
and the report makes no production or parity claim beyond evidence.

Q31 completion measures the current agent systems. It does not mean UAA's full
assistant-OS vision, Goat parity, or production readiness is complete.
