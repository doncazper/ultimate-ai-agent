# README Import v0.24.1

Status: Current import README for v0.24.1 / M20 hardening.

v0.24.1 hardens M20 Device Capability Broker Contract safety. It strengthens
contract validators, tests, documentation, static verification, and Foundation
Gate coverage while keeping M20 contract-only.

Start with:

- `VERSION.md`
- `ultimate_ai_agent_master_plan_v0_24_1.md`
- `docs/release_notes/v0_24_1.md`
- `docs/implementation/foundation_gate_implementation_plan_v0_24_1.md`
- `docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md`
- `docs/device_capabilities/CAPABILITY_MANIFEST_SCHEMA.md`
- `docs/device_capabilities/DEVICE_PERMISSION_LIFECYCLE.md`
- `docs/device_capabilities/CAPTURE_INTENT_CONTRACT.md`
- `docs/device_capabilities/SENSOR_BOUNDARY_AND_NON_GOALS.md`
- `docs/device_capabilities/DEVICE_TRUST_AND_REVOCATION_CONTRACT.md`
- `docs/device_capabilities/DEVICE_RECEIPT_AND_REDACTION_POLICY.md`
- `docs/device_capabilities/DEVICE_CAPABILITY_SECURITY_MODEL.md`
- `docs/device_capabilities/DEVICE_CAPABILITY_BROKER_NON_GOALS.md`
- `docs/canonical/09_roadmap.md`
- `docs/canonical/64_mobile_companion_and_device_capability_broker.md`
- `docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md`
- `docs/roadmap/NEXT_SEQUENCE_v0_17_5.md`

M20 remains contract-only. No device capability is enabled or implemented.
All enabled and implemented capability flags are rejected. Raw payloads,
silent/passive/background/continuous capture, automatic memory writes,
external sends, OS permission runtime claims, notification push runtime claims,
background service runtime claims, device pairing runtime claims, device
identity runtime claims, raw payload-like metadata, private local paths, and
secret-like metadata are blocked.

This patch adds no M21 OpenWebUI Bridge, Device Capability Broker runtime
implementation, mobile app, Android app, iOS app, macOS app, native build
workflow, sensor API, OS permission code, backend API route, runtime
execution, model/provider call, remote execution, plugin enablement,
dependency, architecture behavior change, or production authority.
