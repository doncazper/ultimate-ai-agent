# 37 — Tool Broker

Status: Foundation specification, v0.4.8
Owner: Tooling / Runtime
Layer: Layer 2 Tools, Files, Code, and Web
Blocking: Required before file writes, code execution, web actions, scanners, external actions, Skill Factory, and self-improving code.

## Purpose

The Tool Broker is the only allowed pathway from agents to tools. It prevents subagents from directly touching files, code, memory, web, scanners, credentials, or external systems.

The Tool Broker decides:

```text
Is this tool available?
Is the request valid?
Is the caller allowed to use it?
Does the Consent Ledger permit it?
Does the Execution Contract permit it?
Is approval required?
Can this run in dry-run mode?
What must be logged?
What rollback metadata is required?
```

## Core rule

> Agents request tool actions; the Tool Broker authorizes, executes, logs, and returns results.

## Tool risk classes

```text
R0 read_only_public
R1 read_only_private
R2 local_draft_or_write
R3 sandbox_execution
R4 external_draft
R5 external_send_or_publish
R6 destructive_or_irreversible
R7 credential_or_permission_change
R8 financial_or_legal_sensitive
R9 self_modifying_agent_change
```

Higher risk classes require stronger consent, logging, evals, approvals, and rollback plans.

## Tool manifest

Every tool must declare:

```text
tool_id
name
version
owner
capability_scopes
risk_class
input_schema
output_schema
side_effects
requires_consent_scopes
requires_approval_conditions
supports_dry_run
supports_rollback
network_access
filesystem_access
credential_requirements
rate_limits
cost_model
timeout_ms
audit_fields
```

No undocumented tools in production.

## Execution sequence

```text
1. Receive Tool Call Request.
2. Validate request schema.
3. Verify caller identity and run/contract IDs.
4. Check Execution Contract allowed_tools.
5. Check Consent Ledger and permission policy.
6. Classify risk.
7. Check approval requirement.
8. Check Cost Governor and rate limits.
9. Check sandbox requirements.
10. Produce dry-run preview if required.
11. Execute tool.
12. Validate output schema.
13. Record Event Ledger events.
14. Store rollback metadata if mutation happened.
15. Return structured Tool Call Result.
```

## Untrusted input policy

Tool requests must not be generated directly from untrusted web/email/message/scanner content.

Allowed:

```text
Scanner detects a signal -> Orchestrator creates contract -> verifier evaluates -> Tool Broker may create notification if permitted.
```

Forbidden:

```text
Email says "send this to everyone" -> agent sends email.
Webpage says "ignore previous instructions" -> agent changes policy.
```

## Dry run

Mutating or external actions should support dry-run previews when possible.

Dry run output:

```text
what would happen
files/accounts/entities affected
permission checks
estimated cost
rollback option
approval needed
```

## Rollback

For mutating actions, the Tool Broker must record:

```text
before_state_ref
after_state_ref
diff_ref
rollback_command_or_plan
rollback_risk
rollback_expiration
```

If rollback is impossible, the action must be marked as irreversible and approval-gated.

## Tool result contract

Tool results must be structured:

```text
tool_call_id
run_id
contract_id
tool_id
status
summary
output_refs
raw_output_ref, if stored
side_effects
rollback_ref
cost
latency_ms
errors
redactions
```

## Required contract tests

```text
tool_broker_blocks_unregistered_tool
tool_broker_blocks_forbidden_scope
tool_broker_requires_approval_for_external_send
tool_broker_dry_run_precedes_high_risk_mutation
tool_broker_logs_all_tool_calls
tool_broker_records_rollback_for_mutation
tool_broker_validates_tool_output_schema
tool_broker_blocks_prompt_injection_tool_request
```

## MVP implementation notes

Implement first:

```text
Tool registry
Tool manifest schema
Tool Call Request/Result schemas
Permission evaluator integration
Approval request integration
Event Ledger integration
Dry-run interface
Rollback metadata interface
Mock tools for contract tests
```

Real external integrations come later.
## v0.5.3 Secret Broker and provider routing rule

The Tool Broker may call provider adapters, but it must not expose raw credentials to the LLM or to tool-call payloads. Provider tools use credential references and resolve them through the Secret Broker at execution time.

Provider tool calls must check, in order:

```text
Execution Contract allows the action.
Consent Ledger allows the purpose and data scope.
Tool Broker risk policy allows or gates the call.
Secret Broker can resolve a credential reference if required.
Cost Governor allows the call.
Provider Registry chooses a provider and normalizer.
Event Ledger records request/result with redaction and cost attribution.
```

