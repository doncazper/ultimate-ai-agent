# v0.40.0 Master Plan

Status: historical release packet.
Release: **v0.40.0 / M36 - CCC File Review Surface, Review-Only**.

## Objective

Implement the M36 CCC File Review Surface as a frontend-only, review-only
display surface for already-redacted review packet data.

## Scope

- add `/files/review` to the Control Center shell.
- display redacted preview text.
- display redaction summary text.
- display exact binding refs.
- display review-only decision status.
- display approval gate contract status.
- display receipt plan metadata.
- use mock and non-authoritative fallback data.
- add tests, docs, verifier coverage, and Foundation Gate criteria.

## Validation Expectations

- pytest passes.
- frontend tests pass.
- documentation integrity passes.
- static verification passes.
- Foundation Gate passes.
- OpenAPI version is v0.40.0 with path count unchanged at 74.
- forbidden raw-file, review approval capture, context, memory, export, and
  execute routes remain absent.

M37 remains planned/provisional. M38 remains planned/provisional.
