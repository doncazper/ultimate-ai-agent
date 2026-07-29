# Contributing to Ultimate AI Agent

Thanks for improving UAA. Contributions are welcome when they preserve the
project's local-first, contract-first, fail-closed boundaries.

## Before opening a pull request

1. Read `AGENTS.md` and the relevant architecture or product-truth docs.
2. Keep the change focused and avoid unrelated refactors.
3. Add focused tests for behavior changes.
4. Update the smallest relevant documentation and indexes.
5. Run the focused tests, then the proportional repository verification.
6. Do not include credentials, raw private data, environment dumps, local
   paths, raw logs, prompts, responses, provider payloads, or screenshots with
   private information.

## Review convergence

Follow
[`docs/verification/REVIEW_CONVERGENCE_POLICY.md`](docs/verification/REVIEW_CONVERGENCE_POLICY.md).
Scope a pull request to one durable contract, authority boundary, or
independently reviewable product slice. Record the applicable authority,
provenance, recovery, concurrency, tampering, capacity, failure-truth, and
cross-surface invariants before implementation.

Use targeted checks while coding, batch known findings, perform one structural
adversarial audit before publishing, and run one broad local qualification on
the final candidate. Publish once per candidate and request one exact-head CI
and review cycle. Repeated architectural findings should become the smallest
isolated prerequisite repair instead of another field-specific patch.

This cadence does not weaken required review, CI, policy, approval, redaction,
OpenAPI, Foundation Gate, or post-merge checks.

## Pull request safety

External pull request workflows require maintainer approval before they run.
Approved workflows execute on fresh standard GitHub-hosted machines with a
read-only token and no repository secrets. A contribution must not attempt to
access secrets, expand workflow permissions, introduce a self-hosted runner,
or bypass policy, approval, redaction, OpenAPI, route, review, or Foundation
Gate checks.

## Verification

Useful local entry points include:

```bash
make doctor
make test
make verify
make frontend-check
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
```

If a required environment or dependency is unavailable, report the blocker
truthfully instead of weakening or skipping the assertion.

## Product language

Public source availability under the MIT License is not a public beta,
production-readiness claim, supported binary release, or grant of runtime
authority. Keep implemented, partial, planned, blocked, skipped, mock-only, and
missing states explicit.

By contributing, you agree that your contribution is licensed under the
repository's MIT License.
