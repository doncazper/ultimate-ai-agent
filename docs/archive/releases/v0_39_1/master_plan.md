# v0.39.1 Master Plan

Status: historical release packet.
Release: **v0.39.1 / M35 hardening - File Review Exact File/Path Binding**.

## Objective

Harden M35 Safe File Review Workflow Contracts so review approvals bind to the
exact reviewed file and safe path refs, while preserving review-only,
contract-only behavior.

## Scope

- require approval `file_ref` and `safe_path_ref`.
- require gate expected `file_ref` and `safe_path_ref`.
- deny mismatched approval file/path refs.
- deny `model_copy`-mutated packet file/path refs at evaluator boundaries.
- strengthen tests, static verification, documentation integrity, docs, and
  Foundation Gate coverage.

## Validation Expectations

- pytest passes.
- documentation integrity passes.
- static verification passes.
- Foundation Gate passes.
- OpenAPI version is v0.39.1 with path count unchanged at 74.
- forbidden raw-file, review approval capture, context, memory, export, and
  execute routes remain absent.

M36 remains planned/provisional. M37 remains planned/provisional. M38 remains
planned/provisional.
