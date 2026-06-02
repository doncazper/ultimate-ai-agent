# Local Runtime M22 To M23 Boundary

Status: Active M22 contract documentation for v0.26.0. Contract-only.

M22 is the Local Model Runtime Activation Contract. It defines metadata-only profiles, endpoint policy, activation policy, activation request/decision validation, health probe planning, tests, verifiers, docs, and Foundation Gate criteria.

M22 stops before runtime behavior:

- no model was called.
- no runtime was activated.
- no endpoint was contacted.
- no prompt was processed.
- no tool call was executed.
- no memory write occurred.

M23 remains future. M23 is the first possible milestone for a reviewed, bounded, local-only, non-tool, non-authoritative local model call. M23 must not inherit authority from M22 metadata. It needs its own prompt, review, tests, redaction policy, approval policy, receipt policy, timeout policy, local-only guard, and Foundation Gate criteria.
