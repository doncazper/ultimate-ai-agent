# M79 Plugin Install Review Authority Boundary

Plugin Install Review is non-authoritative. A review-ready decision means the
install candidate metadata has passed review while remaining disabled by
default. It does not authorize plugin install, plugin enablement, plugin
execution, runtime import, network access, model/provider call, browser
automation, shell execution, mobile device access, remote execution,
credentials or cookies, raw manifest content, raw package content, raw prompt,
raw provider payload, backend route, Control Center control, dependency, or
production authority.

Exact approval binding is required for review. The approval must bind to the
install review request ref, M78 manifest security decision ref, manifest ref,
plugin ref, version pin, and actor. Expired, revoked, replayed, mismatched, and
`approval_test_*` approvals are denied.

Evaluator boundaries revalidate safety-critical fields and cannot trust
constructor validation alone. M80 remains future.
