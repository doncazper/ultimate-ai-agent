# v1.6.0 Master Plan

Milestone: M102 Location Sensor, Off by Default.

Scope:

- Add contract-only location sensor policy and scope contracts.
- Keep location off by default.
- Require foreground-only review, separate precise-location approval, consent,
  revocation, and audit.
- Add tests, docs, static verification, documentation-integrity checks, and
  Foundation Gate coverage.

Non-goals:

- no runtime location access.
- no native permission prompt.
- no background location.
- no raw coordinates.
- no location history.
- no geofence behavior.
- no location export.
- no backend route.
- no Control Center control.
- no dependency.
- no memory write.
- no context injection.
- no execution.
- no M103 work.
- no production authority.
