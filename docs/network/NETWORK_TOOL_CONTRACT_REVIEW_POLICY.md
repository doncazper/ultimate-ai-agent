# Network Tool Contract Review Policy

The M71 policy is contract-only, review-only, deterministic, and disabled by
default. It may describe a future allowlisted read-only HTTP fetch candidate,
but it does not enable the capability.

Required policy invariants:

- contract-only
- review-only
- disabled by default
- deterministic
- M72 candidate only
- no network call
- no HTTP fetch
- no unrestricted network tool
- no authenticated network action
- no credentials or cookies
- no request body
- no non-GET method
- no download or export
- no raw response body
- no browser automation
- no provider/model call
- no tool execution
- no memory write
- no context injection
- no backend route
- no Control Center control
- no dependency
- no production authority

All request and decision models are revalidated at evaluator boundaries.
Model-copy mutations that request network calls, HTTP fetches, credentials,
request bodies, non-GET methods, raw response bodies, backend routes,
dependencies, or production authority are denied.

M72 remains future.
