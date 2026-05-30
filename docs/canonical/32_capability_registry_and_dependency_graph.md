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
## v0.5.3 dependency additions

Foundation dependencies now include:

```text
Verification Contract before verified status.
Secret Broker before credentialed providers.
Provider Registry before provider-specific integrations.
Cost Attribution before scanners or high-volume model routing.
Trusted Computing Base before self-improvement.
Contract provisional policy before M1 schema freezing.
```



## Capability flags

Every runtime capability should have a flag record that declares:

```text
capability_id
enabled
stage
requires_foundation_gate
required_contracts
required_permissions
required_evals
kill_switch
owner
```

Capabilities blocked by the Foundation Gate must be disabled by default in code, not only in documentation. The Capability Registry is the source of truth for which advanced modules are allowed to load.


## Skill package capability requirements

Any capability that installs, loads, executes, grants credentials to, exposes tools through, or autonomously invokes a skill must remain blocked until the Skill Package Security Rule is satisfied. Skills are untrusted packages by default.

Skill-related capability records must include or reference:

```text
skill_manifest_ref
declared_permissions
source_provenance
static_review_status
sandbox_test_status
tool_broker_permission_mapping
event_ledger_logging_required
version_pin
revocation_supported
high_risk_human_approval_required
```

The Capability Registry must be able to disable a single skill, a skill source, a skill version, or the entire Skill Factory without disabling unrelated foundation capabilities. No skill may move from `blocked_by_foundation_gate` to `ready_for_build` unless its dependencies include Tool Broker, Consent Ledger, Event Ledger, Secret Broker where credentials are involved, redaction, rollback, and contract tests.

## Skill Package Security Rule

All skills are untrusted packages by default. A skill may not be installed, loaded, executed, granted credentials, exposed to tools, or used in autonomous workflows until it has:

1. a manifest,
2. declared permissions,
3. source/provenance metadata,
4. static review where applicable,
5. sandbox test execution,
6. Tool Broker permission mapping,
7. Event Ledger logging,
8. version pinning,
9. revocation/disable support,
10. human approval for high-risk capabilities.


A Skill Factory capability must remain `blocked_by_foundation_gate` until the registry can express skill manifests, permission mappings, provenance, sandbox status, version pins, revocation state, and approval requirements.
