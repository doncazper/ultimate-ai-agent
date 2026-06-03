Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Module Readiness Audit v0.5.2

## Ready for M0 build

```text
Repo/canonical import
Python Agent Core skeleton
Schema validation
Prompt validation
Agent API Boundary placeholder
Docker Compose scaffold
OpenWebUI optional shell config
```

## Ready for M1-M2 build

```text
Execution Contract
Context Pack
Event Ledger
Receipt generator
API boundary logging rules
```

## Needs detail soon, but should not block M0-M2

```text
Cost Governor
Rollback and Recovery
Security Threat Model implementation
Data Lifecycle implementation
Code Workspace / sandboxing
Web Research V1
Source Credibility and Rumor Protocol
```

## Blocked until Foundation Gate

```text
Scanners
Companion Proactivity
Skill Factory
Self-Improving Coding Framework
Autopilot Workflows
External high-autonomy execution
```

## Stack-specific warning

OpenWebUI is useful for speed, but dangerous if it becomes a backdoor around Agent Core policy. Keep durable state, permissions, memory, tools, and execution inside Agent Core.
