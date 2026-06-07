# M102 Location Sensor Policy

The M102 policy is contract-only and off by default. A valid policy requires:

- location sensor default off.
- location permission scope.
- foreground-only review.
- separate precise-location approval requirement.
- consent.
- revocation.
- audit.

The policy denies runtime location access, native permission prompt, background
location, raw coordinates, location history, geofence behavior, location export,
backend routes, Control Center controls, dependency changes, memory writes,
context injection, execution, and production authority.
