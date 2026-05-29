# 45 — Trusted Computing Base

Status: Foundation safety boundary, v0.5.3
Owner: Security / Runtime

## Purpose

Define the parts of the system autonomous self-improvement cannot modify.

## Trusted Computing Base components

```text
Agent Constitution
autonomy and approval policy
Consent Ledger logic
Tool Broker risk classification
Secret Broker and credential handling
Event Ledger append/redaction logic
security threat model
prompt-injection defenses
model routing privacy rules
cost governor hard limits
rollback policy
TCB policy itself
CI/security checks enforcing this boundary
```

## Self-improvement rule

Autonomous self-improvement may propose changes to TCB files, but it cannot apply, merge, deploy, or activate those changes. TCB changes require explicit human review and a dedicated ADR.

## File/path examples

```text
docs/canonical/30_agent_constitution.md
docs/canonical/42_autonomy_levels_and_standing_approvals.md
docs/canonical/45_trusted_computing_base.md
docs/canonical/23_security_threat_model.md
docs/canonical/40_credentials_secret_broker_and_provider_registry.md
future runtime files for consent, tool broker, secret broker, event redaction, risk classification
```

## Required controls

```text
TCB file registry
CI check that detects TCB edits
human approval requirement
Event Ledger record for TCB change proposal
contract tests for TCB policy
```
