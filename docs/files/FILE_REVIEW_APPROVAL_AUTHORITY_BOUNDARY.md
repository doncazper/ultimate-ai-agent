# File Review Approval Authority Boundary

Status: active M37 authority-boundary documentation.
Release: v0.41.0 / M37 - Review Approval Capture, Review-Only Persistence.

Review approval capture is not raw access authority and is not execution
authority. A review-only approval record cannot authorize:

- raw file reads
- full-file reads
- unredacted preview
- file export or download
- context proposal
- context injection
- memory writes
- tool/action/task execution
- filesystem mutation
- approval refs as authority

Approval must bind to the exact reviewed packet refs. Mismatched packet, preview
result, redaction summary, file, safe path, or actor refs are denied. Expired,
revoked, replayed, and `approval_test_` approvals are denied.

Review decisions and review approval records are non-authoritative audit
records. M38 can consume exact-scope approved review records as evidence for a
safe, non-authoritative context proposal, but the review approval record itself
still grants no context injection, OpenWebUI handoff, memory write, export, raw
file access, execution, or truth authority.
