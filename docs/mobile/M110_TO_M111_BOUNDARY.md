# M110 to M111 Boundary

Checkpoint M110 implements Mobile Sensor Hardening Freeze as a contract-only,
review-only, freeze-only checkpoint over the M109 Mobile Sensor Audit Ledger.

M111 Production Threat Model remains future. M110 must not implement M111
production threat model records, production authority, production runtime,
external distribution, backend routes, Control Center controls, dependencies,
mobile sensor runtime, broad autonomy, memory write, context injection, or
execution.

The current product baseline remains v1.7.2 through M110 checkpoint work.
M150 remains the v1.2.0-alpha target. Beta begins later after the alpha UI and
supporting safety/product work are reviewed and promoted.
