# 32 Capability Registry and Dependency Graph

Status: Canonical draft, v0.4.1

## Purpose

Track what capabilities exist, what they depend on, what permissions they need, what risks they carry, and whether they are allowed to move forward.

## Why this matters

The Ultimate AI Agent will have many modules. Without a dependency graph, foundation changes can silently break higher layers.

## Capability manifest fields

```json
{
  "id": "scanner.reddit.v1",
  "name": "Reddit Scanner V1",
  "layer": 5,
  "status": "blocked_by_foundation_gate",
  "dependencies": [
    "kernel.execution_contract.v1",
    "ledger.event.v1",
    "consent.ledger.v1",
    "tool_broker.v1",
    "source_credibility.v1",
    "notification_policy.v1"
  ],
  "permissions_required": ["web.read", "scanner.run", "notification.create"],
  "risk_level": "medium",
  "rollback_required": true,
  "contract_tests_required": true
}
```

## Status values

```text
idea
shaping
spec_draft
spec_review
ready_for_build
building
qa_evals
release_candidate
done
parking_lot
blocked
blocked_by_foundation_gate
deprecated
```

## Foundation Gate enforcement

Capabilities with these tags must remain blocked until the Foundation Gate passes:

```text
scanner
companion_proactivity
skill_factory
self_improving_code
autopilot
high_autonomy_external_execution
```

## Required registry outputs

- Capability inventory.
- Dependency graph.
- Permission map.
- Risk map.
- Contract test list.
- Foundation Gate blocked list.
- Blast-radius report before foundation changes.

## Current blocked capabilities

```text
scanner.reddit.v1
scanner.news.v1
scanner.weather.v1
scanner.email.v1
scanner.messages.v1
proactive_intelligence.v1
companion_layer.v1
skill_factory.v1
self_improving_code.v1
autopilot_workflows.v1
```
