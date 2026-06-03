Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.24.1

Status: Current master plan for v0.24.1 / M20 hardening.

v0.24.1 hardens M20 Device Capability Broker Contract safety only.

Implemented:

- validator hardening for permission runtime claims, notification push runtime
  claims, background service runtime claims, validation decisions, redacted
  receipt requirements, contract-only revocation plans, raw payload-like
  metadata, geolocation coordinates, private local paths, and secret-like
  metadata.
- expanded tests for every major device capability rejecting `allowed_now=true`
  and `implemented_now=true`.
- static verifier coverage for expanded device/mobile route drift, sensitive
  browser/native API fragments, and native/mobile frontend dependencies.
- Foundation Gate M20 coverage for expanded capability kinds and forbidden
  route drift.
- documentation hardening that states no device capability is enabled or
  implemented, user gesture is future contract metadata only, raw payloads are
  blocked, receipts remain redacted, and M21 remains planned/provisional.

Still not implemented:

- M21 OpenWebUI Bridge + Chat Shell Integration Contract.
- Device Capability Broker runtime implementation.
- Android app.
- iOS app.
- macOS app.
- native build workflow.
- mobile sensor access.
- sensor API.
- OS permission integration.
- background service.
- notification runtime.
- device pairing runtime.
- backend API route additions.
- approval execution.
- runtime execution.
- model/provider calls.
- remote execution.
- plugin enablement.
- OpenWebUI integration.

OpenAPI path count remains `74`. M21 remains planned/provisional.
