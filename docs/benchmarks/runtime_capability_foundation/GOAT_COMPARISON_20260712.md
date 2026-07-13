# UAA and GoatCitadel Agent Capability Comparison — 2026-07-12

This is a bounded evidence-gate comparison, not a base-model intelligence score
or a production-readiness claim. The machine-readable ledger is
[`goat_comparison_20260712.json`](goat_comparison_20260712.json).

## Baselines and limitations

| Repository | Inspected state | Version truth | Limitation |
|---|---|---|---|
| UAA (historical comparison baseline) | `main` at `7f4230ac984177d44142330d7b4d3714874d0bd9` | `0.104.0` | Clean and synchronized before implementation; this SHA is intentionally not rewritten to the later integrated UI head. |
| GoatCitadel | `91775e6905c8ca6c5083444f64eb3457b2d0aaa0` | root package `0.1.0-rc.1`; gateway/UI `1.0.0` | Local branch tracks a removed upstream branch and has one pre-existing untracked report. It is not the expected clean `v1.0.0` release checkout. |

GoatCitadel remained read-only. Its focused existing test binary produced 209
passes in the independent evidence audit, while a separate five-file sample in
this run produced 93 passes and three current-head chat-orchestrator failures.
Confidence for GoatCitadel is therefore Medium.

## Numeric profile

| Dimension | UAA | GoatCitadel | Result | Confidence |
|---|---:|---:|---|---|
| Capability maturity before implementation | 88/100 | 86/100 | UAA leads on demonstrated repository maturity | UAA High; Goat Medium |
| Capability maturity after implementation | 88/100 | 86/100 | No score increase without a bound empirical result | UAA High; Goat Medium |
| Cross-repository empirical task performance | not measured | not measured | no winner | Low |
| Observed product experience | not measured | not measured | no winner | Low |
| Safety and authority component | 10/10 | 8/10 | UAA | High/Medium |
| Current cockpit implementation component | 8/10 | 10/10 | GoatCitadel | High/Medium |

The weighted scores were calculated mechanically with the `goat-comparison`
skill's seven integer evidence gates. They measure repository capability
maturity, not empirical task success or user satisfaction.

## Component scorecard

| Component | UAA before | UAA after | GoatCitadel | Leader |
|---|---:|---:|---:|---|
| Reasoning and task understanding | 8 | 8 | 8 | tie |
| Planning and orchestration | 10 | 10 | 9 | UAA |
| Learning and adaptation | 8 | 8 | 8 | tie |
| Memory and context | 9 | 9 | 9 | tie |
| Communication | 8 | 8 | 8 | tie |
| Action and tool calling | 9 | 9 | 9 | tie |
| Autonomy and authority | 10 | 10 | 8 | UAA |
| Code assistance | 8 | 8 | 8 | tie |
| Research and web | 10 | 10 | 8 | UAA |
| Model and provider management | 8 | 8 | 9 | GoatCitadel |
| Evidence and observability | 9 | 9 | 9 | tie |
| Safety and failure handling | 10 | 10 | 9 | UAA |
| AI cockpit implementation | 8 | 8 | 10 | GoatCitadel |
| CLI/API parity | 9 | 9 | 8 | UAA |
| Extensibility | 7 | 7 | 9 | GoatCitadel |
| Productized agent loop | 8 | 8 | 8 | tie |

## Gap selected and implemented

The highest user-facing gap is still exact founder-loop execution, but that
backend work already exists on preserved PR `#272`. The desktop operator shell
has since landed separately; reimplementing the backend here would duplicate
authority code. The sealed adapter and signed evidence similarly remain
preserved on PRs `#271` and `#275`; they remain outside this slice and require
their own merge-gate evidence.

This slice therefore closed the next independent P1 gap: complete component
verifier coverage with honest measurement posture. UAA now has a backend-owned
content-free report and a human-readable CLI covering all 16 components through
21 bounded scenario verifiers. It separates observed process/posture results
from correctness, recovery, evidence-completeness, replay, intervention,
false-completion, unsupported-claim, and policy-violation metrics that still lack
structured result envelopes. Those metrics remain `not measured`. Evaluation
grants no authority and every child process runs with a scrubbed environment and
macOS network denial.

The local result was:

- 21/21 verifier results matched their expected safe posture;
- 16/16 components covered;
- 20 passed, unblocked scenario verifiers and one truthfully blocked sandbox
  scenario;
- task completion: `not measured` because these bundles do not emit exact
  structured task-result envelopes;
- correctness, recovery, evidence completeness, replay correctness, operator
  interventions, false completion, unsupported claims, and policy violations:
  `not measured` pending structured scenario result envelopes;
- deterministic WEB-HYBRID preservation tests and contract verification passed
  without live provider or network access.

These are UAA-only controlled scenarios. They do not establish a cross-project
empirical winner.

The stored projection is bound to exact UAA source commit `9a76be7b4` and a
content digest covering the 49 evaluator, verifier, dependency-lock, and target
files used by the run. The default verifier is repository-local and does not
open a sibling benchmark checkout. GoatCitadel evidence-line revalidation is an
explicit opt-in operation requiring a caller-supplied read-only root. A fresh
bounded UAA runtime revalidation matched the stored projection after these
bindings were added.

## Reciprocal learning

UAA should adapt GoatCitadel's readable approval queue, Run Detail grouping,
provider-choice explanations, and bounded fanout presentation. Every adopted
behavior must continue to use UAA's exact request-scoped leases, dispatcher,
budget, target, kill-switch, safe-disable, idempotency, and content-free receipts.

GoatCitadel would benefit from UAA's deny-unknown authority, exact lease and
approval scope, stable CLI/API parity verifier, content-free portable evidence,
and web-content-as-non-authority boundary.

UAA should not borrow wildcard grants, approval-bypass profiles, content-bearing
research persistence, trusted host execution presented as sealed isolation, or
arbitrary runtime extension imports.

## Remaining bounded gaps

- Land the already-implemented exact founder-loop PR once its required safe CI
  gate is available.
- Preserve the sealed-calculation and signed-evidence branches until their
  separate isolation and key-lifecycle merge gates are satisfied.
- Query the existing safe FTS memory projection in a later focused preview-only
  retrieval slice.
- Add one configured provider lane with exact cost settlement before broad model
  routing.
- Keep cross-repository empirical performance and observed usability explicitly
  `not measured` until identical multi-trial protocols run on comparable releases.
