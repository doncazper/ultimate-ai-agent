# Dependency Graph v0.4.1

## Foundation path

```text
Execution Contract
  -> Event Ledger
  -> Consent/Permission Ledger
  -> Tool Broker

Context Pack
  -> Memory Service
  -> Orchestrator

Event Ledger
  -> Memory Service
  -> File Manager
  -> Tool Broker
  -> Rollback
  -> Contract Tests

Memory Service + File Manager + Tool Broker
  -> Orchestrator MVP
  -> Spec SDLC Engine
```

## Advanced path

```text
Tool Broker + Consent Ledger + Event Ledger + Source Credibility + Notification Policy
  -> Scanners
  -> Proactive Intelligence

Memory Service + User Control Center + Data Lifecycle + Companion Safety Evals
  -> Companion Layer

Capability Registry + Tool Broker + Code Workspace + Skill Trust Pipeline
  -> Skill Factory

Code Workspace + Contract Tests + Event Ledger + Rollback + Approval Policy
  -> Self-Improving Coding Framework
```

## Blocked by Foundation Gate

```text
Scanners
Companion Proactivity
Skill Factory
Self-Improving Coding Framework
Autopilot Workflows
High-autonomy External Execution
```
