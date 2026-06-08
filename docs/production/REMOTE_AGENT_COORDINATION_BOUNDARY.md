# Remote Agent Coordination Boundary

M117 is a contract-only and review-only remote agent coordination boundary. It
defines safe refs for future remote agent coordination review, but those refs
are identifiers only. They are not authority, connection strings, URLs,
credentials, live channels, dispatch handles, or execution handles.

The boundary is actor-bound, baseline-bound,
source-role-authority-model-bound, user-bound, workspace-bound,
remote-agent-bound, coordination-scope-bound, trust-boundary-bound, and
handoff-protocol-bound. Audit and replay are required, and every receipt is a
no-effect receipt plan.

M117 permits no production authority, no remote agent runtime, no remote
dispatch, no remote execution, no live connection, no network access, no agent
spawn, no background worker, no credential handling, no account action, no
model call, no memory write, no context injection, no execution, no tool
execution, no shell execution, no browser automation, no plugin execution, no
mobile sensor, no backend route, no Control Center control, no dependency, and
no M118 implementation.

M118 remains future. M150 remains the planned v1.0.0-alpha target.
