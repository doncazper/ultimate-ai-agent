# 21 — Consent and Permissions Ledger

Status: Foundation specification, v0.4.8
Owner: Trust / Permissions
Layer: Layer 1 Truth, Memory, and Data Ownership; Layer 2 Tools
Blocking: Required before scanners, email/message access, external actions, companion memory, proactive notifications, Skill Factory, and self-improving code.

## Purpose

The Consent and Permissions Ledger records what the user has authorized the agent to access, remember, monitor, suggest, draft, or execute.

Approval is per action. Consent is durable policy.

Examples:

```text
The agent may read newsletters in Gmail daily.
The agent may not read family emails.
The agent may summarize Slack channels but not DMs.
The agent may draft replies but not send them without approval.
The agent may monitor Reddit for AI-agent topics.
The agent may use cloud models for project docs but local-only models for private notes.
```

## Core rule

> The agent may not access data, use tools, write memory, route sensitive content, or perform external actions unless permitted by the Consent Ledger and current Execution Contract.

## Consent dimensions

Consent grants must specify:

```text
who: user/workspace/project/account
what: data/tool/action/memory/model/scope
where: source/account/channel/location
why: purpose
how: allowed operations
limits: denied operations, content boundaries, rate limits, cost limits
when: schedule/expiration/quiet hours
risk: approval requirements
revocation: how to disable/delete
```

## Permission scopes

```text
memory.read
memory.write
memory.delete
file.read
file.write
file.delete
code.generate
code.patch
code.execute
web.search
web.read
scanner.read
scanner.monitor
email.read
email.draft
email.send
message.read
message.draft
message.send
calendar.read
calendar.write
external.publish
external.modify
credential.read
permission.modify
model.cloud_route
model.local_route
notification.digest
notification.interrupt
self_improve.patch
self_improve.merge
```

## Consent states

```text
requested
active
denied
expired
revoked
suspended
superseded
```

## Content boundaries

Permissions should support inclusion and exclusion rules.

Example:

```json
{
  "source": "gmail_personal",
  "allowed_content": ["newsletters", "receipts", "project_related"],
  "excluded_content": ["family", "medical", "legal", "financial_accounts"],
  "allowed_actions": ["read", "summarize", "extract_tasks"],
  "denied_actions": ["send", "delete", "forward"]
}
```

## Approval layering

A consent grant may allow preparation but still require approval to execute.

Example:

```text
Can read email newsletters -> no per-email approval.
Can draft a reply -> no send approval required for draft.
Can send an email -> always requires approval unless a narrow recurring workflow is explicitly granted.
```

## Privacy and model routing

Consent controls whether content can be routed to cloud or local models.

```text
cloud_allowed
local_only
summaries_only
embeddings_allowed
raw_content_forbidden
```

The Model Router must consult this ledger before routing sensitive content.

## Revocation

Revocation must be immediate for future actions. It should trigger cleanup workflows where applicable:

```text
stop scanner
remove credentials
block tool scope
mark memory source as revoked
delete or archive derived memories if requested
stop notifications
log revocation event
```

## User controls

The User Control Center must expose:

```text
Active grants
Pending approval requests
Connected accounts
Scanner permissions
Notification permissions
Memory permissions
Model/cloud routing permissions
Revocation controls
Export/delete controls
```

## Contract tests

```text
consent_blocks_missing_scope
consent_blocks_expired_grant
consent_blocks_revoked_grant
consent_allows_draft_but_blocks_send
consent_excludes_private_content_category
consent_enforces_local_only_model_route
consent_requires_reapproval_for_new_tool_scope
consent_revocation_stops_scanner
```

## MVP implementation notes

Start with:

```text
Postgres consent_grants table
permission_policies table
approval_requests table
policy evaluator library
User Control Center shell for viewing grants
Tool Broker integration
Model Router integration
Event Ledger logging
```

Do not connect email/message scanners until this ledger can enforce content boundaries and revocation.


## v0.5.3 remediation note

Consent is separate from credentials. A credential only proves the system can access a provider; consent proves the user has authorized a specific use. Standing approvals must map to autonomy levels and cannot authorize high/critical actions.
