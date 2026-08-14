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

## AI-assisted contributions

AI assistance does not reduce the contributor's responsibility. Contributors
must personally review, understand, and test the submitted change; have the
right to submit every part of it; disclose material AI assistance; identify
known third-party sources or licenses; and avoid confidential, secret, copied,
or memorized material. Generated output is not evidence of originality,
correctness, security, or license compatibility.

## Commit and pull-request quality

- Use a concise, behavior-first pull-request title:

  ```text
  type(area): concrete behavior or prevented failure
  ```

- Prefer `feat`, `fix`, `perf`, `test`, `ci`, `docs`, `refactor`,
  or `chore` for `type`, and the smallest stable subsystem for `area`.
- Name the observable result rather than an internal phase. Put milestone
  identifiers, implementation phases, and detailed verification in the body.
- Keep each pull request focused on one outcome and do not mix unrelated
  refactors.
- Do not rewrite or remove historical release tags.
- Include tests run, skipped checks, and known limitations.
- Keep durable evidence redacted and use repository-safe references.

## Product language

Public source availability under the MIT License is not a public beta,
production-readiness claim, supported binary release, or grant of runtime
authority. Keep implemented, partial, planned, blocked, skipped, mock-only, and
missing states explicit.

By contributing, you agree that your contribution is licensed under the
repository's MIT License.
