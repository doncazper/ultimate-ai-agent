# M111 to M112 Boundary

Checkpoint M111 implements Production Threat Model as a contract-only,
review-only checkpoint over the M110 Mobile Sensor Hardening Freeze.

M112 User/Workspace Identity Model remains future. M111 must not implement M112
identity records, user/workspace runtime identity, account authority,
credential handling, production authority, production runtime, external
distribution, deployment, backend routes, Control Center controls,
dependencies, broad autonomy, memory write, context injection, or execution.

The current product baseline remains v1.7.2 through M111 checkpoint work.
M150 remains the v1.0.0-alpha target. Beta begins later after the alpha UI and
supporting safety/product work are reviewed and promoted.
