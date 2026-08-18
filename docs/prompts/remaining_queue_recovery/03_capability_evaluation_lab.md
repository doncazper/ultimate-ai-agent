# Capability Evaluation Lab Recovery Contract

Status: triage-ready recovery source. Evaluation output is evidence, not
execution or product authority.

## Outcome

Build a deterministic local evaluation lab that measures UAA capability gaps,
regressions, and parity claims using bounded, content-free receipts.

## In Scope

- Versioned evaluation cases, manifests, provenance, and repeatable scoring.
- Failure attribution with safe test refs and explicit unknown states.
- Regression gates for accepted Hermes, OpenClaw, GoatCitadel, and UAA-native
  capability claims.

## Out Of Scope

- Live provider benchmarking, unrestricted network access, automatic model
  judgment, hidden training, or authority promotion from a score.

## Acceptance

- Evaluations are deterministic or label bounded variance explicitly.
- Every result binds source revision, evaluator revision, and evidence digest.
- False precision, missing-case pooling, and raw payload persistence fail
  closed.
