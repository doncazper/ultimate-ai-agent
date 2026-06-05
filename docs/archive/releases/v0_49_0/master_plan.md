# v0.49.0 Master Plan

M45 implements CCC iOS Local Read-Only Connection as contract/status work only.

Scope:

- Add local-only read-only CCC iOS connection contracts.
- Add loopback-only API base refs.
- Add redacted summary endpoint refs.
- Add source-only Swift status display.
- Add tests, static verifier coverage, documentation-integrity checks, and
  Foundation Gate criteria.
- Keep OpenAPI route count unchanged.

Non-goals:

- No runtime network call.
- No backend route.
- No approval capture or approval execution.
- No raw data.
- No context injection, memory write, file mutation, export, or execution.
- No background collection or mobile sensor access.
- No credentials or cookies.
- No Xcode project, Swift package, signing, store, or TestFlight workflow.
- No production authority.
- No M46 implementation.
