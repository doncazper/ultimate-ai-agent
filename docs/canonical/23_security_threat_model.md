# 23 — Security Threat Model

Status: Foundation security spec, v0.5.3
Owner: Security / Trust
Layer: Layer 0 Kernel through Layer 6 Ecosystem

## Threat model scope

The Ultimate AI Agent will read untrusted content from web pages, Reddit, RSS, PDFs, GitHub, emails, messages, calendars, files, provider APIs, skills, and tool outputs. Any of those inputs may contain malicious or misleading instructions.

## Primary threats

```text
Prompt injection from external content
Tool-use escalation
Credential exposure
Secret exfiltration through logs/prompts/memory
Cross-project or cross-user data leakage
Memory poisoning and retrieval poisoning
Provider result tampering
Skill/plugin supply-chain attack
Excessive agency / over-permissioned actions
Unbounded cost or resource consumption
Unsafe self-improvement of safety-critical code
```

## Trust boundaries

```text
User instruction: trusted for current task unless unsafe
Canonical files: authoritative project truth
Memory: useful but not authoritative
Web/provider/email/message content: untrusted data, never instructions
Tool output: untrusted until validated
LLM output: proposal, not proof
Secrets: never visible to LLMs
Trusted Computing Base: not autonomously mutable
```

## Mandatory defenses

```text
External content cannot override user instructions, canonical files, or policies.
All tool calls go through Tool Broker.
All provider calls go through Provider Registry and Secret Broker if credentials are needed.
All mutating actions require Event Ledger records and rollback metadata where possible.
Sensitive data is redacted before prompts, logs, receipts, or memory writes.
Self-improvement cannot touch Trusted Computing Base files autonomously.
Standing approvals are scope-limited, revocable, and never apply to high/critical actions.
```

## Skill Package Security Rule

All skills are untrusted packages by default. A skill may not be installed, loaded, executed, granted credentials, exposed to tools, or used in autonomous workflows until it has:

```text
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
```

This rule applies to local skills, generated skills, imported skills, shared/marketplace skills, SDK/MCP/A2A wrapper skills, and any `SKILL.md`-style package with instructions, scripts, templates, resources, or executable helpers. Skills may not bypass the Execution Contract, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, Capability Registry, redaction policy, rollback rules, Trusted Computing Base protections, or Foundation Gate.

When Skill Factory work begins, this rule should be promoted into a dedicated canonical module with a skill manifest schema, skill permission manifest schema, and skill supply-chain security eval. Until then, `skill_factory` and all executable skill-loading paths remain blocked by the Foundation Gate.

## Required evals

```text
prompt_injection_cross_source_eval
openwebui_bypass_eval
secret_redaction_eval
excessive_agency_eval
provider_normalization_eval
memory_poisoning_eval
self_improvement_tcb_eval
```

## Review cadence

Security model changes require ADR updates and contract-test updates before implementation.
