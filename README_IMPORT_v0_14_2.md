# README Import v0.14.2

Status: Active baseline after M10.5 Remote Worker Policy Contract Hardening.

Import these files first:

```text
README.md
VERSION.md
ultimate_ai_agent_master_plan_v0_14_2.md
docs/remote/REMOTE_WORKER_FOUNDATION.md
docs/remote/REMOTE_NODE_SECURITY_MODEL.md
docs/remote/REMOTE_JOB_ENVELOPE.md
docs/remote/TAILNET_TRANSPORT_POLICY.md
docs/decisions/remote_worker_tailnet_foundation.md
docs/api/README.md
docs/api/route_inventory.md
docs/implementation/foundation_gate_implementation_plan_v0_14_2.md
```

v0.14.2 is a targeted patch to the M10.5 REMOTE-01 foundation. It rejects unsupported `remote_tailnet_enabled=true` and `remote_personal_data_enabled=true` policy inputs, forbids unexpected top-level fields on remote-worker API wrapper payloads, and extends the Foundation Gate to cover those contract checks.

No live networking exists in this patch.
No job dispatch exists in this patch.
No remote approvals exist in this patch.

It does not add mesh networking, tailnet execution, remote execution, remote Tool Broker execution, remote subagents, file transfer, shell execution, background services, personal-data access, write/send actions, or critical remote work.
