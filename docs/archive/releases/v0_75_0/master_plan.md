# v0.75.0 Master Plan

Milestone: M71 Network Tool Contract Review.

Plan:

- Add contract-only network tool review models.
- Add disabled-by-default policy validation.
- Add allowlisted read-only HTTP fetch candidate review for M72 only.
- Deny unrestricted/authenticated network categories as future-only.
- Deny credentials or cookies, request bodies, non-GET methods, downloads,
  exports, raw response bodies, routes, controls, dependencies, and production
  authority.
- Revalidate safety-critical fields at evaluator boundaries.
- Add tests, docs, documentation integrity checks, static verification, and
  Foundation Gate coverage.

Non-goals:

- no network call
- no HTTP fetch
- no unrestricted network tool
- no authenticated network action
- no credentials or cookies
- no request body
- no non-GET method
- no download or export
- no raw response body
- no backend route
- no Control Center control
- no dependency
- no production authority

M72 remains future.
