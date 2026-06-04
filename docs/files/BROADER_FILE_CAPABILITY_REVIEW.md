# Broader File Capability Review

Status: active M34 documentation.
Current through: **v0.38.1**.

M34 implements Broader File Capability Review as a planning, architecture
review, documentation, verifier, and Foundation Gate milestone only. It does
not add runtime file capability. It does not change the M33 redacted preview
tool, add backend routes, add frontend runtime features, or grant production
authority.

v0.38.1 hardens boundary clarity only: active docs and verifiers must not treat
M34 as Safe File Review Workflow Contracts, file review UI, approval
capture/persistence, context proposal, context injection, raw file access,
memory writes, export, execution, or runtime file authority.

## Purpose

M34 answers this question:

```text
What exact file-review capabilities should be allowed next, in what order,
under which safety boundaries, and with what tests, gates, and verifiers?
```

M34 does not answer whether the agent can now review files, whether CCC Web can
now display review packets, whether approvals can now be captured, whether
reviewed file content can become context, or whether anything can be injected
into a model, OpenWebUI, tool, runtime, or agent loop.

## Current Implemented File Capabilities

Implemented through M33:

- M32 safe filesystem metadata tool:
  `tool:filesystem_metadata.v1`.
- M33 bounded redacted file preview proposal tool:
  `tool:filesystem.redacted_preview.v1`.
- governed Tool Runtime Adapter allowlist with exactly:
  `tool:no_op.v1`, `tool:filesystem_metadata.v1`, and
  `tool:filesystem.redacted_preview.v1`.
- server-owned or explicit test fixture safe roots.
- relative path policy with traversal, hidden path, secret-like path, glob,
  symlink, caller-selected root, and mutation denial.
- bounded UTF-8 preview reads inside the redaction-before-return boundary.
- redacted preview result contracts and no-raw-content receipt plans.
- no backend public raw-file, review, context, memory-write, or tool execute
  routes.
- no CCC file review surface, raw preview control, approval capture control,
  export control, context-injection control, or execute control.

## Next Allowed Direction

The next allowed file-review direction is a staged, review-only path:

1. M35 creates Safe File Review Workflow Contracts.
2. M36 creates a CCC File Review Surface that is review-only.
3. M37 captures user review approvals as review-only persistence.
4. M38 creates Safe Context Proposal contracts from approved reviews, with no
   context injection.
5. M39 creates a CCC Context Proposal Surface.
6. M40 creates Context Handoff Approval, still with no injection.

Each step must preserve exact scope, actor binding, resource binding, replay
safety, non-transferability, redaction boundaries, and no-authority decision
envelopes.

## Explicit Non-Goals

M34 adds none of the following:

- raw file reads.
- full-file reads.
- unredacted preview.
- file review workflow implementation.
- review packet runtime implementation.
- file review UI.
- approval capture or approval persistence.
- context proposal.
- context injection.
- memory writes.
- raw file export, download, or copy-raw control.
- file writes, deletes, or filesystem mutation.
- directory listing, recursive traversal, symlink following, or arbitrary
  caller-selected roots.
- shell, subprocess, network, provider/model, browser, mobile, remote, plugin,
  or tool execution.
- backend routes.
- frontend runtime features.
- dependencies.
- production authority.

## M35 Readiness Conclusion

M35 may start only the Safe File Review Workflow Contracts milestone. It should
define review packet contracts, redaction verification, no-authority review
decisions, and no-raw-content receipt plans. It must not add CCC UI, approval
persistence, context proposal, context injection, raw file access, export,
memory writes, execution, or backend routes.

M35 release review should treat any raw content output/storage, approval
authority ambiguity, context-injection ambiguity, route drift, verifier
weakness, or M36/M37/M38 leakage as a blocking issue.
