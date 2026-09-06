# TAW-00 Fail-Closed Evaluation Scaffold

Status: bounded implementation evidence; independent promotion evidence pending

Acceptance-state role: `non-owner`.
Canonical mutable-state owner: `docs/evals/TOOL_AWARE_COGNITION_TAW08_ACCEPTANCE.md`.
This document records implementation evidence only; it cannot assert or
reconcile mutable founder-private status. Only that owner may perform bounded
active-truth reconciliation. Independent promotion remains a separate gate.

Baseline: v0.104.0 / 0.104.0

Protocol: `docs/evals/tool_aware_cognition_taw00_protocol_v1.json`

Convergence ledger: `docs/evals/tool_aware_cognition_taw00_convergence_ledger_v1.json`

Source projection: `docs/evals/tool_aware_cognition_taw00_source_projection_v1.json`

Founder profile: `docs/evals/tool_aware_cognition_q22_founder_dogfood_v1.json`

## Boundary

This slice implements two separate gates without changing
the Turn Contract Router, chat path, prompts, policy, model-visible formatting,
model/provider behavior, or runtime authority. Capability Evaluation Lab V1
remains the deterministic capability-task contract. TAW-00 scaffolds separate
contracts for paired ordinary-chat quality and future routing measurements; the
two forms of evidence are not interchangeable.

The bounded implementation gate covers English-first Q22
implementation for one explicitly selected local profile, Qwen 3.8 27B with a
128K context window, plus separately identified ChatGPT and Codex OpenAI API
profiles. Exact local artifact/tokenizer/runtime digests and exact OpenAI API
model IDs remain required before measurements for those profiles. Mac and
Windows hardware are recorded per run; quality and latency comparisons use the
same host rather than pretending unlike computers form one latency class.

The independent-promotion gate remains fail-closed. It still requires external
custody, blind scoring, identity authority, and the complete acceptance bundle
before public, multi-user, production, or independently validated quality
claims. The bounded implementation gate does not represent independent
acceptance.

The checked-in independent-promotion protocol remains deliberately
`pending_configuration_freeze`.
Repository evidence does not identify a complete authoritative set of supported
product languages, local-model configurations, or hardware/backend classes, so
the scaffold leaves those arrays empty and reports exact blockers. Convenience
defaults would narrow the acceptance population without authority.

## Implemented Evidence Contracts

- deterministic synthetic development-corpus manifests store generator/version,
  safe parameter/category/rubric refs, immutable case refs, and generated-content
  digests; the generator reconstructs the exact transient synthetic system/user
  payload locally without storing that text in durable evidence;
- the independent custodian tool creates only an HMAC-SHA-256 public commitment,
  rejects private material inside the candidate tree, reads its key from an
  environment-only handoff, validates a strict private holdout manifest, binds
  cycle/custodian/generator/order/attestation fields into the keyed envelope,
  and never prints the key or private location;
- baseline receipt shapes record evaluator Git revision, environment, catalog,
  model, tokenizer, inference, baseline/candidate payload digests, denominators,
  prompt format, TTFT ordering, cache state, pair/source manifests, estimates,
  one-sided bounds, failures, artifact census, and a self-verifying receipt
  digest;
- each metric requirement records its acceptance bound and threshold; internal
  consistency checks apply the plan's `-5` quality margin, 2% false-positive,
  false-block, and unsupported-support bounds, 1% unsafe-authority bound, 5%
  candidate-error-disagreement bound, and both the 50 ms and 5%-of-baseline
  paired p95 TTFT bounds. Binomial metrics require an event numerator, exact
  one-sided Clopper-Pearson upper bound with a 10,000-observation verification
  ceiling, and a zero-event, strictly-below-1%
  unsafe-authority result;
- blind-score receipt shapes record separately scored blinded A/B payload digests,
  randomization refs, cycle/configuration/language, the four plan
  dimensions (`helpfulness`, `instruction_following`, `tone`, and
  `response_relevance`), exactly two distinct evaluators per canonical pair,
  and a distinct adjudicator for every disagreement. Typed randomization
  receipts bind every pair, label/order decision, payload digest, and exact
  candidate manifest;
- selected pure-Python paired and clustered bootstrap helpers, Holm step-down
  thresholds, ordinal Krippendorff alpha, exact binomial tails, and deterministic
  normal-bound power calculations provide reproducible statistics. Computed
  power receipts bind preregistered effect, variance, alpha, target-power, and
  recomputed denominator values to the complete metric/stratum census;
- an exact evaluation-matrix census binds the full reviewed
  language/configuration/hardware/stratum cross product and every canonical pair;
- an exhaustive observation census binds every pair/metric observation, enforces
  estimand-specific shapes, and deterministically derives every baseline metric;
- a Holm-family receipt recomputes ordering probabilities, adjusted one-sided
  alphas, and exact Clopper-Pearson bounds from that observation census;
- a content-addressed candidate lock records named-revision bytes and keeps
  evidence-only deltas disjoint. Pair manifests bind its exact candidate ref,
  Git revision, and manifest digest;
- a revision-bound partial source-root inventory records router/chat/classifier/harness,
  preparation/preflight/fence, capability, approval, prompt, dependency, and
  API boundary roots and verifies those bytes from its exact Git revision. A
  separate typed closure contract parses local Python imports, requires every
  reachable node and exact edge, and rejects missing, unreachable, or
  non-literal dynamic-import nodes. The
  checked-in historical projection remains explicitly partial and cannot pass
  that closure gate;
- one complete acceptance-evidence binding digest links the frozen protocol, power
  receipt, source projection and closure, candidate lock, pair manifest,
  baseline, randomization, score, adjudication, verified holdout opening,
  matrix, observation, familywise-bound, and exhaustive recursive-safe artifact
  census so any changed link stales the result;
- repository CLI and verifier surfaces operate on content-safe JSON only. Their
  only subprocess is fixed-argument, read-only `git show` for revision-bound
  verification; they add no model, provider, network, browser, mutation, or
  execution authority.

## Commands

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_tool_aware_cognition_taw00.py
PYTHONPATH=src .venv/bin/python scripts/run_tool_aware_baseline.py validate-protocol
PYTHONPATH=src .venv/bin/python scripts/run_tool_aware_baseline.py report-founder-dogfood-readiness
```

`report-readiness` requires explicit paths for the commitment, development
corpus, pair manifest, power analysis, baseline receipt, source projection,
source closure, candidate lock, randomization bundle, score/adjudication
bundles, acceptance bindings, holdout opening, matrix census, computed power,
observation census, familywise bounds, and artifact census. It exits 2 while any external trust input is
absent. The facility has no reachable `ready` state. Acceptance-oriented
subcommands report only structure or receipt consistency and exit 2; those
results are not external acceptance evidence. The development-manifest command
produces a reconstructible synthetic manifest from a strict local spec.

The custodian command belongs on the independent machine. Its private manifest
and HMAC key must stay outside the repository and any shared or synced
filesystem. Only the public commitment and opening-receipt JSON may return to
the candidate-building environment.

Key possession and a safe custodian/evaluator ref do not prove independent human
identity. Promotion is deliberately fail-closed until separately reviewed,
externally anchored custodian, evaluator, and baseline-acceptance identity
authorities exist. Candidate-generated attestations cannot open those gates.

## Founder Private-Dogfood Gate

The bounded implementation profile fixes the
initial product scope to English, Qwen 3.8 27B / 128K locally, configured
ChatGPT and Codex OpenAI API profiles, and observed Mac/Windows runs. It requires
the zero-extra-model-call ordinary-chat path, same-host baseline comparisons,
safe-disable, rollback, redacted evidence, and no new authority in this
rebaseline slice. It does not activate a local model or provider, call an API,
select exact OpenAI model IDs, or claim cross-host latency comparability.

TAW-01 capability evidence, TAW-02 familiarity assessment, and TAW-03 bounded
progressive retrieval are now present as non-authorizing contracts. The next
safe implementation step is TAW-04 evidence-only shadow chat integration and
clarification behavior. Each later behavior slice still needs deterministic development-corpus tests,
before/after evidence, and rollback. Founder feedback may refine the private
dogfood candidate through ordinary reviewed PRs.

## Remaining Independent-Promotion Evidence

The six formerly code-owned gaps are now typed, digest-bound, recursively
content-safe, and covered by tamper tests. `verify-complete-evidence` can prove
internal consistency, but deliberately exits 2 and does not claim human
acceptance. The supported matrix still needs truthful independent freeze; the
custodian/evaluator/baseline-acceptance identity authorities remain external;
and no actual baseline or blind-score evidence has been collected.

## Remaining Independent-Promotion Gate

Before independent or public promotion:

1. independently review this complete code-owned evidence contract;
2. freeze the truthful supported language, model-configuration, and
   hardware/backend sets through review;
3. configure externally anchored custodian/evaluator/baseline-acceptance identity
   authority and have an independent custodian create the public commitment
   before the candidate is built;
4. collect the accepted-current same-model behavior-preserving baseline with
   transient raw prompts/responses and redacted durable receipts;
5. obtain two independent language-qualified blind scores per pair and a third
   independent qualified adjudicator for disagreements;
6. lock and verify the complete candidate manifest before any one-time holdout
   release.

Until those steps pass, independent promotion remains blocked.

Those steps do not narrow bounded founder-private-dogfood implementation under
the checked-in founder profile.

This rebaseline opens Q22 implementation but does not complete TAW-00 through
TAW-08 and does not grant runtime model/provider authority.
