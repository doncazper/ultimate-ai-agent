# TAW-00 Fail-Closed Evaluation Scaffold

Status: scaffold implemented; acceptance evidence contracts and external inputs pending

Baseline: v0.104.0 / 0.104.0

Protocol: `docs/evals/tool_aware_cognition_taw00_protocol_v1.json`

Convergence ledger: `docs/evals/tool_aware_cognition_taw00_convergence_ledger_v1.json`

Source projection: `docs/evals/tool_aware_cognition_taw00_source_projection_v1.json`

## Boundary

This slice implements a fail-closed TAW-00 evaluation scaffold without changing
the Turn Contract Router, chat path, prompts, policy, model-visible formatting,
model/provider behavior, or runtime authority. Capability Evaluation Lab V1
remains the deterministic capability-task contract. TAW-00 scaffolds separate
contracts for paired ordinary-chat quality and future routing measurements; the
two forms of evidence are not interchangeable, and this slice cannot produce
acceptance or promotion proof.

The checked-in protocol is deliberately `pending_configuration_freeze`.
Repository evidence does not identify a complete authoritative set of supported
product languages, local-model configurations, or hardware/backend classes, so
the scaffold leaves those arrays empty and reports exact blockers. Convenience
defaults would narrow the acceptance population without authority.

## Implemented Scaffold

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
  digest; typed power proof and full cross-artifact acceptance binding remain
  pending;
- each metric requirement records its acceptance bound and threshold; internal
  consistency checks apply the plan's `-5` quality margin, 2% false-positive,
  false-block, and unsupported-support bounds, 1% unsafe-authority bound, 5%
  candidate-error-disagreement bound, and both the 50 ms and 5%-of-baseline
  paired p95 TTFT bounds, but this is not statistical acceptance proof;
- blind-score receipt shapes record separately scored blinded A/B payload digests,
  randomization refs, cycle/configuration/language, the four plan
  dimensions (`helpfulness`, `instruction_following`, `tone`, and
  `response_relevance`), exactly two distinct evaluators per canonical pair,
  and a distinct adjudicator for every disagreement; typed randomization proof
  and candidate/result cross-binding remain pending;
- selected pure-Python paired and clustered bootstrap helpers, Holm step-down
  thresholds, and ordinal Krippendorff alpha provide deterministic scaffold
  statistics; typed power proof and the binomial upper-bound estimator remain
  pending;
- a content-addressed candidate-lock scaffold records named-revision bytes and
  keeps evidence-only deltas disjoint; complete source closure and result
  cross-binding remain pending;
- a revision-bound partial source-root inventory records router/chat/classifier/harness,
  preparation/preflight/fence, capability, approval, prompt, dependency, and
  API boundary roots and verifies those bytes from its exact Git revision; it
  does not claim transitive dependency closure;
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
corpus, pair manifest, baseline receipt, source projection, candidate lock,
scores, and adjudications; it exits 2 while any binding or external trust input
is absent. The scaffold has no reachable `ready` state. Acceptance-oriented
subcommands report only structure or receipt consistency and exit 2; those
results are not acceptance evidence. The development-manifest command produces
a reconstructible synthetic manifest from a strict local spec.

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

1. finish and review typed power-analysis, binomial upper-bound, randomization,
   candidate/result cross-binding, and transitive source-closure contracts;
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

Until those steps pass, TAW-00 and Q22 remain blocked before behavior change.
This slice narrows the old facility-unavailable blocker to explicit acceptance-
contract and external-review inputs; it does not complete TAW-00 or Q22.
