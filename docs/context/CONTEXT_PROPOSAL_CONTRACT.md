# Context Proposal Contract

Status: active M38 contract documentation.
Release: v0.42.0 / M38 - Safe Context Proposal From Approved Review.

The M38 contract defines:

- `SafeContextProposalPolicy`
- `SafeContextProposalRequest`
- `SafeContextProposalSource`
- `SafeContextProposalBinding`
- `SafeContextProposalRedactionVerification`
- `SafeContextProposalSection`
- `SafeContextProposal`
- `SafeContextProposalDecision`
- `SafeContextProposalReceiptPlan`

Default policy enables context proposal construction only. The policy disables
context surface, context handoff, context injection, OpenWebUI handoff, model
calls, memory writes, export, execution, raw file access, raw content, full-file
reads, unredacted preview, backend routes, Control Center surface, and
production authority.

Valid proposals must be non-authoritative, proposal-only, redacted-only, and
bounded. They must include exact approved-review binding, source-chain
provenance, redaction verification, and safe proposal sections. A proposal is
not context injection and does not write memory. It does not export. It does
not execute.

Evaluator boundaries revalidate current object fields. Constructor validation
alone is not trusted. `model_copy` mutations that add raw content, full file
content, unredacted preview, context injection, OpenWebUI handoff, model calls,
memory writes, export, execution, or mismatched refs are denied.

M39 remains planned/provisional.
