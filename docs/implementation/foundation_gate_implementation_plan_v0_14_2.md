# Foundation Gate Implementation Plan v0.14.2

v0.14.2 extends the M10.5 Foundation Gate checks for remote-worker policy contract hardening.

Skill Package Security Rule:

All skills are untrusted packages by default. Before any skill package can become an executable or high-trust capability it must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

Gate additions:

- `remote_tailnet_enabled=true` is rejected as unsupported in M10.5
- `remote_personal_data_enabled=true` is rejected as unsupported in M10.5
- remote-worker API wrapper payloads reject unexpected top-level fields
- secret-like top-level extras do not leak in validation responses

Gate continuations:

- remote worker files exist
- risky remote capabilities default false
- unknown nodes and transports are denied
- planned tailnet/LAN transports remain disabled
- dry-runs dispatch nothing
- remote worker source has no live network, process, listener, private transport call, or background runtime imports
- remote subagents, remote tool execution, remote approvals, personal-data access, write/send actions, and critical actions remain denied
- remote output is untrusted
- API exposes validation/status/dry-run only
- docs say foundation-only

No live networking exists in this patch.
No job dispatch exists in this patch.
No remote approvals exist in this patch.
