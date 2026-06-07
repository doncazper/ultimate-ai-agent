# M102 Location Authority Boundary

M102 does not grant location authority. It defines safe contract records only.

Review records must not be treated as permission to read location, request a
native permission prompt, collect background location, store coordinates, export
location data, write memory, inject context, execute tools, or claim production
authority.

Approval refs are identifiers only. `approval_test_*` refs are never runtime
authority. Model, memory, context, tool-intent, runtime, and Control Center refs
cannot authorize location access.
