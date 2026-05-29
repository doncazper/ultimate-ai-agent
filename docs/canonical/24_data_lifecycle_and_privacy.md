# 24 — Data Lifecycle and Privacy

Status: Foundation privacy spec, v0.5.3
Owner: Trust / Data Governance

## Purpose

Define how user data, project data, scanned content, memories, traces, files, and provider results are stored, retained, exported, deleted, and minimized.

## Data classes

```text
User profile memory
Project memory
Relationship memory
Canonical files
Uploaded files
Generated artifacts
Event ledger records
Tool results
Provider result envelopes
Raw provider responses
Scanner-derived items
Credential references
Raw secrets
Model prompts and completions
```

## Retention rules

```text
Canonical files: retained until project deletion or explicit archive.
Project memories: retained while active; superseded rather than silently overwritten.
Raw provider responses: store only when necessary; prefer normalized envelopes.
Secrets: stored only in Secret Broker / vault / keychain; never in memory/logs/git.
Scanner-derived private data: default shorter retention and user-visible controls.
Event ledger: append-only, but payloads may be redacted/minimized with retained receipt metadata.
```

## User controls

The user must be able to:

```text
Show what you know about me
Forget this
Forget everything about this project
Export memory
Export receipts
Delete scanner-derived data
Pause learning
Pause provider access
Pause proactive notifications
Revoke credentials
```

## Privacy routing

Sensitive/private data should prefer local/private models when available. Cloud model routing requires explicit policy allowance and Event Ledger recording.

## Non-negotiable rules

```text
Do not store secrets in memory.
Do not store raw email/message content as long-term memory by default.
Do not mix private content across projects/workspaces.
Do not use old memory over current user instruction or canonical files.
```
