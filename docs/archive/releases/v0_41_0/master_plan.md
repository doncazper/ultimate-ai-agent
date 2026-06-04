# v0.41.0 Master Plan

Status: historical release packet after acceptance.
Release: **v0.41.0 / M37 - Review Approval Capture, Review-Only Persistence**.

## Objective

Implement review-only approval capture for already-redacted file review packets
without granting raw access, context, memory, export, execution, or production
authority.

## Scope

- add review approval capture contracts.
- add safe review-only approval and denial records.
- add idempotency/replay protection.
- add safe-ref-only local approval store.
- add `POST /files/review/approvals/capture`.
- add Control Center review-only capture controls.
- add tests, documentation, static verification, and Foundation Gate coverage.
- update version metadata to v0.41.0.

## Validation Expectations

- pytest passes.
- frontend tests pass.
- documentation integrity passes.
- static verification passes.
- Foundation Gate passes.
- OpenAPI version is v0.41.0 with path count 75.
- only `/files/review/approvals/capture` is added; raw-file, context, memory,
  export, and execute routes remain absent.

M38 remains planned/provisional.
