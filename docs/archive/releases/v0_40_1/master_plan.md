# v0.40.1 Master Plan

Status: historical release packet.
Release: **v0.40.1 / M36 hardening - CCC File Review Surface Read-Only Safety**.

## Objective

Harden the M36 CCC File Review Surface so it remains safe-ref-only, local
read-only, non-mutating, non-authoritative, and free of private/raw path drift.

## Scope

- strengthen visible safe-ref-only UI boundary copy.
- keep packet selection and expansion as local read-only UI state.
- add mock markers for safe refs and no mutating requests.
- add frontend tests for safe refs and private/raw path absence.
- strengthen frontend static verification.
- strengthen Foundation Gate coverage.
- strengthen documentation-integrity checks.
- update release metadata to v0.40.1.

## Validation Expectations

- pytest passes.
- frontend tests pass.
- documentation integrity passes.
- static verification passes.
- Foundation Gate passes.
- OpenAPI version is v0.40.1 with path count unchanged at 74.
- forbidden raw-file, review approval capture, context, memory, export, and
  execute routes remain absent.

M37 remains planned/provisional. M38 remains planned/provisional.
