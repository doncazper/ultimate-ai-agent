# M102 Location Sensor, Off by Default

M102 defines a contract-only location sensor boundary for future mobile review.
Location remains off by default. The milestone records safe refs for a future
foreground review candidate, exact scope, consent, revocation, and audit
requirements.

M102 adds no runtime location access, no native permission prompt, no background
location, no raw coordinates, no location history, no geofence behavior, no
location export, no backend route, no Control Center control, no dependency, no
memory write, no context injection, no execution, and no production authority.

Safety shorthand: no background location and no location export.

The location contract is non-authoritative. Approval refs, context refs, memory
refs, model output, runtime output, and Control Center refs cannot authorize
location access. M103 remains future.
