# v0.44.0 Master Plan

Status: historical release packet after acceptance.
Release: **v0.44.0 / M40 - Context Handoff Approval, No Injection**.

## Goal

Add contract-only context handoff approval decisions that bind exactly to safe
context proposal refs and preserve no-injection, no-execution, and
non-authoritative boundaries.

## Scope

- context handoff approval policy, request, decision, and receipt contracts.
- exact proposal binding validation.
- approval_ref and approval_test_ denial.
- expired, revoked, replayed, mismatched approval denial.
- evaluator revalidation for model_copy-mutated proposal and request fields.
- no-injection and no-authority decision invariants.
- tests, docs, static verifier coverage, documentation-integrity checks, and
  Foundation Gate coverage.

## Non-Goals

No automatic context injection, OpenWebUI handoff execution, runtime
integration, model/provider calls, memory writes, export/download/copy-raw,
execution/tool/action/task controls, approval mutation controls, backend
routes, raw file reads, raw content display/storage, full-file content,
unredacted preview, raw absolute paths, arbitrary file reads, file picker,
browser, upload, root selector, directory traversal/listing, file mutation,
shell/subprocess, network calls, mobile/native work, plugins, dependencies,
M41 work, or production authority.
