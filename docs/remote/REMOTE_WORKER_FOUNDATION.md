# Remote Worker Foundation

M10.5 is foundation-only. It defines local schemas, mock registries, static status metadata, and dry-run result contracts for future remote workers.

No live networking exists in this milestone.
No job dispatch exists in this milestone.
No remote approvals exist in this milestone.
No remote subagents, remote tools, listeners, background services, file transfer, shell execution, write/send actions, personal-data access, or critical actions are enabled.

Remote worker output is always untrusted remote output. It is never trusted control input, never truth authority, and never approval authority.

v0.14.2 hardens the M10.5 policy contract: `remote_tailnet_enabled=true` and `remote_personal_data_enabled=true` are rejected as unsupported in M10.5. Remote-worker API wrapper payloads reject unexpected top-level fields, and validation errors remain sanitized.
