# Ultimate AI Agent Version

Current active baseline: **v0.14.2**

v0.14.2 hardens the M10.5 Remote Worker and Tailnet Transport Foundation policy contract. It rejects unsupported `remote_tailnet_enabled=true` and `remote_personal_data_enabled=true` policy inputs, forbids unexpected top-level fields on remote-worker API wrapper payloads, and extends the Foundation Gate to cover these policy-contract checks. It adds no live networking, Tailscale calls, job dispatch, remote execution, remote subagent launch, remote Tool Broker execution, personal-data access, write/send action, remote approval, or background service.
