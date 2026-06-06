# M71 Network Tool Contract Review

v0.75.0 implements M71 Network Tool Contract Review as contract-only and
review-only validation for future network tool contracts. The first allowed
candidate category is an allowlisted read-only HTTP fetch contract proposal for
M72, but M71 performs no network call and no HTTP fetch.

The M71 contract records safe refs for a proposed tool, actor, allowed-host
policy, and risk review. It can decide that an allowlisted read-only HTTP fetch
candidate is ready for future review, or that effectful network categories
require a future milestone. Every decision remains disabled by default and
non-authoritative.

M71 explicitly provides no unrestricted network tool, no authenticated network
action, no credentials or cookies, no request body, no non-get method, no
download or export, no raw response body, no backend route, no Control Center
control, no dependency, and no production authority.

Evaluator boundaries revalidate current object fields so constructor validation
alone is never trusted. Approval refs remain identifiers only, and
approval_test_* refs are denied as runtime authority.

M72 remains future.
