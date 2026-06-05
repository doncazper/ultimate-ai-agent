# Context Handoff Approval Boundary

Status: active M40 authority-boundary documentation.
Release: **v0.44.0 / M40 - Context Handoff Approval, No Injection**.

Context Handoff Approval is a policy decision over already-safe context
proposal refs. It is review-only and non-authoritative. It cannot be used to
perform context injection, OpenWebUI handoff execution, model/provider calls,
memory writes, export, task/action/tool execution, raw file reads, backend route
mutation, or production authority.

## Exact Proposal Binding

M40 requires exact proposal binding. The approval request must match the safe
context proposal's actor, proposal, approval record, review packet, preview
result, redaction summary, file, and safe path refs. A mismatch in any of those
refs is denied.

approval_ref alone is not authority. approval_test_ is not runtime authority.
Context packs, memory refs, model output, OpenWebUI output, Control
Center refs, tool intent refs, task refs, and approval refs can explain review
provenance, but they cannot authorize handoff execution or injection.

## No Runtime Boundary

M40 adds no backend routes, no Control Center mutation controls, no context
handoff execution endpoint, no context injection endpoint, no OpenWebUI handoff
endpoint, no memory write endpoint, no export endpoint, and no execution
endpoint.

M41 remains future.
