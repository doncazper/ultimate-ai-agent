# Phase 01: Baseline Scoreboard And Gap Truth

Goal: establish a code-evidenced runtime parity baseline before implementation.
This phase prevents vague "external runtime parity" claims and defines the exact score
movement required by the end-to-end run.

## Required Work

1. Inspect UAA's existing turn router, runtime gateway, model router,
   execution, durable run, approval, evidence, CLI, API, and Control Center
   surfaces.
2. Inspect external comparison runtime read-only for the five reference areas named in the
   bundle README.
3. Create or update a UAA runtime parity scorecard, preferably
   `docs/runtime/UAA_RUNTIME_PARITY_SCORECARD.md`.
4. Score the eight dimensions from the screenshot:
   - turn-contract clarity;
   - authority/safety boundary;
   - execution readiness;
   - durable runtime integration;
   - model/provider routing;
   - operator inspectability;
   - product usefulness today;
   - long-term safe foundation.
5. For each dimension, include current score, target score, confidence, status,
   strongest evidence, missing evidence, and exact implementation lane.
6. Mark external runtime references as architectural evidence only. Do not infer
   UAA readiness from external runtime code.
7. Add tests or a verifier that fails if the scorecard overclaims implemented
   capability without naming evidence and blocked authority.

## Acceptance Criteria

- The scorecard distinguishes implemented, partial, planned, blocked,
  mock-only, contradicted, deprecated, and unknown states.
- The scorecard names UAA files/tests as stronger evidence than docs.
- The scorecard contains no raw local paths, raw prompts, raw payloads, raw
  logs, usernames, hostnames, credentials, or secret-like values.
- The scorecard defines what "parity by today" means without promising broad
  runtime authority.
- A verifier or focused test protects the scorecard from unsupported parity
  claims.

## Verification

Run focused docs/verifier tests plus:

```bash
git diff --check
.venv/bin/python scripts/verify_documentation_integrity.py
```
