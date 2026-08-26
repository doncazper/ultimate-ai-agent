# TAW-00 Fail-Closed Evaluation Acceptance Contracts

Status: acceptance contracts implemented; external configuration and evidence pending

Baseline: v0.104.0 / 0.104.0

Protocol: `docs/evals/tool_aware_cognition_taw00_protocol_v1.json`

Convergence ledger: `docs/evals/tool_aware_cognition_taw00_convergence_ledger_v1.json`

Source projection: `docs/evals/tool_aware_cognition_taw00_source_projection_v1.json`

## Boundary

This slice implements fail-closed TAW-00 evaluation acceptance contracts without changing
the Turn Contract Router, chat path, prompts, policy, model-visible formatting,
model/provider behavior, or runtime authority. Capability Evaluation Lab V1
remains the deterministic capability-task contract. TAW-00 scaffolds separate
contracts for paired ordinary-chat quality and future routing measurements; the
two forms of evidence are not interchangeable, and this slice cannot produce
acceptance or promotion proof without the separately anchored external inputs.

The checked-in protocol is deliberately `pending_configuration_freeze`.
Repository evidence does not identify a complete authoritative set of supported
product languages, local-model configurations, or hardware/backend classes, so
the scaffold leaves those arrays empty and reports exact blockers. Convenience
defaults would narrow the acceptance population without authority.

## Implemented Acceptance Contracts

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
  thresholds, and ordinal Krippendorff alpha provide deterministic scaffold
  statistics. Typed power receipts must cover the exact metric/stratum census,
  bind the frozen protocol, and prove the pair census meets every denominator;
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
- one acceptance-evidence binding digest links the frozen protocol, power
  receipt, source projection and closure, candidate lock, pair manifest,
  baseline, randomization, score, and adjudication bundles so any changed link
  stales the result;
- repository CLI and verifier surfaces operate on content-safe JSON only. Their
  only subprocess is fixed-argument, read-only `git show` for revision-bound
  verification; they add no model, provider, network, browser, mutation, or
  execution authority.

## Commands

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_tool_aware_cognition_taw00.py
PYTHONPATH=src .venv/bin/python scripts/run_tool_aware_baseline.py validate-protocol
```

`report-readiness` requires explicit paths for the commitment, development
corpus, pair manifest, power analysis, baseline receipt, source projection,
source closure, candidate lock, randomization bundle, score/adjudication
bundles, and acceptance binding. It exits 2 while any external trust input is
absent. The facility has no reachable `ready` state. Acceptance-oriented
subcommands report only structure or receipt consistency and exit 2; those
results are not external acceptance evidence. The development-manifest command
produces a reconstructible synthetic manifest from a strict local spec.

The custodian command belongs on the independent machine. Its private manifest
and HMAC key must stay outside the repository and any shared or synced
filesystem. Only the public commitment JSON may return to the candidate-building
environment.

Key possession and a safe custodian/evaluator ref do not prove independent human
identity. Promotion is deliberately fail-closed until separately reviewed,
externally anchored custodian, evaluator, and baseline-acceptance identity
authorities exist. Candidate-generated attestations cannot open those gates.

## Remaining TAW-00 Gate

Before any routing or prompt change:

1. freeze the truthful supported language, model-configuration, and
   hardware/backend sets through review;
2. configure externally anchored custodian/evaluator/baseline-acceptance identity
   authority and have an independent custodian create the public commitment
   before the candidate is built;
3. collect the accepted-current same-model behavior-preserving baseline with
   transient raw prompts/responses and redacted durable receipts;
4. obtain two independent language-qualified blind scores per pair and a third
   independent qualified adjudicator for disagreements;
5. lock and verify the complete candidate manifest before any one-time holdout
   release.

Until those steps pass, TAW-00 and Q22 remain blocked before behavior change.
This slice removes the code-owned acceptance-contract blocker and narrows the
old facility-unavailable blocker to external configuration, identity,
measurement, and review inputs; it does not complete TAW-00 or Q22.
