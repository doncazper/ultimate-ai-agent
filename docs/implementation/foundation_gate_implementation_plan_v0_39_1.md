# Foundation Gate Implementation Plan v0.39.1

Status: active Foundation Gate plan for v0.39.1.

v0.39.1 hardens M35 Safe File Review Workflow Contracts as review-only,
contract-only logic.

## Gate Coverage

Foundation Gate must cover:

- M35 file review workflow module exists.
- M35 file review docs exist.
- redacted review packets only.
- exact approval binding across actor, review packet, preview result,
  redaction summary, `file_ref`, and `safe_path_ref`.
- `review_packet_ref` alone is not authority.
- `approval_ref` alone denied.
- `approval_test_*` denied.
- expired, revoked, replayed, and mismatched approvals denied.
- evaluator revalidation catches `model_copy` raw content, unredacted preview,
  context injection, memory write, export, execution, packet `file_ref`, and
  packet `safe_path_ref` mutations.
- review decisions authorize no raw file access, context proposal, context
  injection, memory writes, export, or execution.
- receipt plans store no raw content.
- no backend routes are added.
- OpenAPI path count remains 74.
- M36 remains planned/provisional.
- M37 remains planned/provisional.
- M38 remains planned/provisional.

## Blocked Drift

Gate must fail on raw content, full-file content, unredacted preview, raw
absolute path storage, missing redaction verification, approval mismatch,
file/path mismatch, approval capture, approval persistence, context proposal,
context injection, memory writes, export, execution, backend routes, route
count drift, M36 work, M37 work, M38 work, dependency drift, or production
authority.

## No New Authority

M35 adds no Control Center UI, approval capture, approval persistence, raw file
access, raw content, full-file reads, context proposal, context injection,
memory writes, export, execution, file mutation, backend routes, dependencies,
or production authority.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package requires
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be trusted by a runtime boundary.
