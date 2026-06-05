# Master Plan - v0.47.0

Status: Historical release plan for v0.47.0.

## Objective

Implement M43 Mobile API Boundary, Read-Only as a contract, documentation,
verifier, and Foundation Gate milestone only.

## Scope

- Define planned endpoint refs for future mobile read-only summaries.
- Require read-only, GET-only, redacted summary only endpoint contracts.
- Deny raw data, raw payload exposure, raw absolute path exposure, mutation,
  approval capture, approval execution, sensors, credentials, cookies, context
  injection, memory write, export, execution, and production authority.
- Keep OpenAPI route count stable.
- Keep M44 CCC iOS Skeleton, No Authority future.
- Add tests for unsafe model_copy mutations.
- Add verifier and Foundation Gate coverage.
- Update active baseline, release notes, and roadmap currentness.

## Non-Goals

- No mobile app.
- No iOS app.
- No Android app.
- No native package.
- No native build workflow.
- No backend route.
- No mobile API route runtime.
- No approval capture or approval execution.
- No mobile sensor access.
- No OS permission integration.
- No background collection.
- No raw data, raw payload exposure, or raw absolute path exposure.
- No credential or cookie handling.
- No memory write, context injection, export, or execution.
- No dependency, M44 implementation, or production authority.
