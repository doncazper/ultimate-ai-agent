# Autonomous Tool Execution Contract

M91 defines an autonomous tool execution contract as contract-only,
review-only, deterministic, local-only metadata. It records the exact safe refs
that a future low-risk tool autonomy milestone would need, but it performs no
real tool execution.

The contract is bound to an exact M90 Shell/Subprocess Hardening Freeze
decision. Evaluator boundaries revalidate the M90 decision and the current M91
fields before any decision is valid for review. Approval refs are identifiers
only and are not authority.

M91 is safe refs only and dry-run plan only. It adds no real tool execution, no
autonomous execution, no autonomous session start, no command execution, no shell execution, no
subprocess execution, no filesystem mutation, no network access, no browser
automation, no plugin execution, no remote execution, no model call, no memory
write, no context injection, no background worker, no backend route, no Control
Center control, no dependency, and no production authority.

M92 remains future.
