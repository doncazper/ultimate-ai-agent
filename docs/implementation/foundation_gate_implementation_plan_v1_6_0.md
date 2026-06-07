# Foundation Gate Implementation Plan v1.6.0

v1.6.0 adds M102 Foundation Gate checks for Location Sensor, Off by Default.

Coverage:

- M102 location contracts exist and validate.
- location remains off by default.
- foreground-only review scope is required.
- separate precise-location approval requirement is present.
- runtime location access is denied.
- native permission prompts are denied.
- background location is denied.
- raw coordinates, location history, geofence behavior, and location export are
  denied.
- backend route and Control Center control drift are denied.
- dependency drift, memory writes, context injection, execution, and production
  authority are denied.
- active roadmap docs mark M102 implemented/released and keep M103-M150
  planned/provisional.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be considered for later reviewed milestones.

M102 does not add skill package execution, plugin execution, external plugins,
runtime imports, backend routes, Control Center controls, dependencies, or
production authority.
