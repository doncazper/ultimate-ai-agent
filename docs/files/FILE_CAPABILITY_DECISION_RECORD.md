# File Capability Decision Record

Status: active M34 documentation.
Current through: **v0.39.1**.

M34 records the staged decision for broader file capability work. It is not an
implementation milestone.

## Decisions

1. M35 is Safe File Review Workflow Contracts only.
   M35 may define redacted review packet contracts, redaction verification,
   review-only decision envelopes, and no-raw-content receipt plans. M35 must
   not add CCC UI, approval persistence, context proposal, context injection,
   memory writes, export, execution, backend routes, or raw file access.

2. M36 is CCC File Review Surface, Review-Only.
   M36 may display redacted review packets and safe metadata. It must not add
   raw preview, file browser, file picker, upload, export/download/copy-raw,
   approve/deny persistence, context proposal, context injection, or execute
   controls.

3. M37 is Review Approval Capture, Review-Only Persistence.
   M37 may capture review-only approval metadata bound to exact review packet
   refs, actor, resource, scope, expiry, revocation, and replay protections. It
   must not grant raw file access, context injection, memory write, export, or
   execution authority.

4. M38 is Safe Context Proposal From Approved Review.
   M38 may create proposal contracts from approved redacted review metadata. It
   must not inject context into a model, OpenWebUI, runtime, tool, or agent
   loop.

5. M39 is CCC Context Proposal Surface.
   M39 may display context proposals for review. It must not inject, export,
   execute, write memory, or bypass approval boundaries.

6. M40 is Context Handoff Approval, No Injection.
   M40 may define handoff approval boundaries. It still must not implement
   automatic context injection.

## Not Allowed Before M40

- raw file reads or full-file reads.
- raw file export, download, or copy-raw behavior.
- context injection.
- memory writes.
- execution or tool/action execution.
- file mutation.
- backend raw-file/review/context/memory/execute routes.
- approvals that become transferable execution authority.

## Not Allowed Before M60

- arbitrary raw file browsing.
- arbitrary caller-selected filesystem roots.
- arbitrary shell/subprocess.
- unrestricted network tools.
- provider/model calls as authority.
- background workers.
- mobile sensors.
- plugin enablement.
- production authority.
- browser automation execution.
- approval refs as authority.
