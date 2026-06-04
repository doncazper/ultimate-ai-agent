# M35 Safe File Review Workflow Readiness

Status: active M34 readiness documentation.
Current through: **v0.38.1**.

M35 is the first implementation milestone after M34. It must implement Safe File
Review Workflow Contracts only.

M35 remains planned/provisional until a dedicated reviewed v0.39.0 / M35
release implements those contracts.

## Exact M35 Scope

M35 may add:

- review workflow contract models.
- review packet contracts derived from existing redacted preview results.
- redaction verification requirements.
- review-only decision envelopes.
- file review receipt plans with no raw content.
- evaluator revalidation for safety-critical packet fields.
- tests, docs, static verifier coverage, and Foundation Gate coverage.

## Required Tests

M35 tests must prove:

- valid redacted preview results can produce review packet contracts.
- review packets include redacted preview only.
- review packets require redaction summary and redaction verification.
- raw_content, full_file_content, unredacted_preview, raw absolute paths, and
  secret-like metadata are denied.
- model_copy-mutated raw/content/context/memory/export/execution flags are
  denied at evaluator boundaries.
- review decisions are non-authoritative.
- receipt plans store no raw content.
- no backend routes are added and OpenAPI path count remains unchanged.

## Required Verifiers And Gate Checks

M35 must add documentation integrity, static verifier, and Foundation Gate
checks for:

- M35 docs and contracts exist.
- M35 remains contract-only.
- no raw file reads or full-file output.
- no file review UI.
- no approval persistence.
- no context proposal or context injection.
- no memory writes.
- no export.
- no execution.
- no backend routes.
- no dependencies.
- M36 remains planned/provisional.

## Strict Non-Goals

M35 must not add:

- CCC File Review Surface.
- Review Approval Capture.
- approval persistence.
- Safe Context Proposal.
- Context Proposal Surface.
- Context Handoff Approval.
- raw file access.
- context injection.
- memory writes.
- export/download/copy-raw.
- file mutation.
- backend routes.
- frontend runtime features.
- production authority.

## Release Review Focus

The M35 release review should stop on any raw-content ambiguity,
redaction-verification weakness, approval-authority ambiguity, route drift,
context-injection ambiguity, memory-write ambiguity, export ambiguity,
execution ambiguity, dependency drift, or M36/M37/M38 leakage.
