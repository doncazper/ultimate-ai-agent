# M71 to M72 Boundary

M71 is the Network Tool Contract Review milestone. It defines safe contracts for
reviewing future network tool categories only.

M72 is the future Read-Only HTTP Fetch Tool, Allowlisted milestone. M72 may
introduce the first bounded allowlisted fetch implementation if it passes its own
review, tests, static verifier, Foundation Gate, and pushed-release review.

The boundary is strict:

- M71 may define a future allowlisted read-only HTTP fetch candidate.
- M71 performs no network call.
- M71 performs no HTTP fetch.
- M71 adds no unrestricted network tool.
- M71 adds no authenticated network action.
- M71 handles no credentials or cookies.
- M71 sends no request body.
- M71 uses no non-GET method.
- M71 performs no download or export.
- M71 stores no raw response body.
- M71 adds no backend route.
- M71 adds no Control Center control.
- M71 adds no dependency.
- M71 grants no production authority.

Evaluator boundaries revalidate current object fields, including model-copy
mutated request, policy, decision, and receipt fields.

M72 remains future.
