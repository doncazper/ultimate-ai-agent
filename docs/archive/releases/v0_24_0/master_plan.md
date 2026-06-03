Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.24.0

Status: Current master plan for v0.24.0 / M20.

v0.24.0 implements M20 Device Capability Broker Contract only.

Implemented:

- contract-only device capability enums and Pydantic boundary models.
- default manifest for future CCC iOS, CCC Android, CCC macOS, and mobile
  web/PWA device capability planning.
- validation helpers that reject enabled sensor access, OS permission
  integration, silent capture, background capture, passive capture, continuous
  capture, raw payloads, automatic memory writes, external sends, background
  services, runtime pairing claims, device-client authority claims, and
  secret-like metadata.
- Device Capability Broker docs under `docs/device_capabilities/`.
- Foundation Gate criterion `m20_device_capability_broker_contract_safe`.
- documentation and static verifier coverage for the M20 boundary.

Still not implemented:

- M21 OpenWebUI Bridge + Chat Shell Integration Contract.
- Device Capability Broker runtime implementation.
- Android app.
- iOS app.
- macOS app.
- native build workflow.
- mobile sensor access.
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
