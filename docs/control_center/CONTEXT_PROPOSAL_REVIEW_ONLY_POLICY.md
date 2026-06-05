# Context Proposal Review-Only Policy

Status: active for **v0.43.0 / M39 - CCC Context Proposal Surface**.

The Context Proposal Surface is read-only and proposal-only. It may select a
mock proposal for display, but local selection is not approval capture,
approval persistence, context handoff, context injection, OpenWebUI handoff,
memory write, export, execution, model/provider call, or production authority.

Control Center output is not authority. Python Agent Core remains the brain and
the policy authority. Context packs are not authority. Memory is recall, not
authority. Model output is not authority. Runtime output is not authority.
`approval_ref` alone is not authority, and `approval_test_` refs are never
runtime authority.

The surface must keep exact binding refs visible so reviewers can see which
approved review packet, redacted preview result, redaction summary, file ref,
safe path/path ref, actor ref, and approval record produced the proposal.

M39 adds no context handoff approval. M40 remains future.
