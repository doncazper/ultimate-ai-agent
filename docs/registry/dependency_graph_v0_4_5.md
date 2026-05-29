# Dependency Graph v0.4.5

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
  -> Model Router
  -> Cost Governor
  -> Rollback
  -> Contract Tests

Capability Registry
  -> Tool Broker
  -> Model Capability Registry
  -> Skill Factory later

Consent/Permission Ledger + Cost Governor + Capability Registry + Event Ledger
  -> Model Router
  -> Orchestrator
  -> Scanners later
  -> Proactive Intelligence later
  -> Skill Factory later
  -> Self-Improving Coding Framework later

Memory Service + File Manager + Tool Broker + Model Router
  -> Orchestrator MVP
  -> Spec SDLC Engine
```

## Advanced path

```text
Tool Broker + Consent Ledger + Event Ledger + Source Credibility + Notification Policy + Model Router + Cost Governor
  -> Scanners
  -> Proactive Intelligence

Memory Service + User Control Center + Data Lifecycle + Companion Safety Evals + Model Router
  -> Companion Layer

Capability Registry + Tool Broker + Code Workspace + Skill Trust Pipeline + Model Router + Cost Governor
  -> Skill Factory

Code Workspace + Contract Tests + Event Ledger + Rollback + Approval Policy + Model Router
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

## New v0.4.5 dependency rule

High-volume or high-risk modules must not begin implementation until model routing is operational. This means Model Router V1, model capability registry, Cost Governor integration, privacy routing policy, Event Ledger route logs, fallback behavior, and routing evals must pass.
