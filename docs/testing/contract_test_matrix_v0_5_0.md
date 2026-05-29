# Contract Test Matrix v0.5.0

| Area | Test | Blocks release? |
|---|---|---|
| Execution Contract | Missing acceptance criteria fails validation | yes |
| Execution Contract | Critical action requires approval policy | yes |
| Context Pack | Truth hierarchy applied | yes |
| Context Pack | Untrusted content marked evidence-only | yes |
| Event Ledger | Run reconstructable from events | yes |
| Event Ledger | Secrets redacted | yes |
| Consent Ledger | Revoked consent blocks future action | yes |
| Tool Broker | Unregistered/forbidden tool blocked | yes |
| Tool Broker | Mutating action has rollback metadata | yes |
| Model Router | Privacy route respected | yes |
| Cost Governor | Budget breach blocked or approval-gated | yes |
| Memory Service | Memory write requires source event | yes |
| Memory Service | Superseded memory excluded | yes |
| File Manager | Hash-guarded patch prevents overwrite | yes |
| File Manager | Canonical update logged and rollback-ready | yes |
| Shadow Replay | Changed foundation decision detected | yes |
| Kanban Gate | Blocked advanced modules stay blocked | yes |
