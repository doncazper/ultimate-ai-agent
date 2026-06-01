# 51 — Redaction and Safe Debugging

Status: Active foundation contract, v0/provisional until Foundation Gate.

## Purpose

The Event Ledger, receipts, debug bundles, provider errors, prompt logs, and traces are only safe if secrets and sensitive data are redacted before they are persisted or displayed.

## Core rule

> Raw secrets and sensitive payloads must never enter prompts, memory, logs, receipts, canonical files, debug bundles, or Git.

## Redaction surfaces

```text
prompts
model outputs
tool inputs
tool outputs
provider requests
provider responses
error messages
event ledger payloads
receipts
debug bundles
file previews
memory snippets
```

## Never-log examples

```text
API keys
OAuth tokens
refresh tokens
cookies
private keys
passwords
authorization headers
session IDs
.env values
full personal message bodies unless explicitly needed and consented
```

## Redaction actions

```text
omit
mask
hash
summarize
store_by_reference
classify_only
quarantine
```

## Safe debug bundle policy

A debug bundle may include:

```text
run_id
step_ids
event types
safe messages
redacted payload previews
schema validation errors
file paths within allowed workspace
cost totals
model classes, not secret credentials
```

A debug bundle must not include:

```text
raw credentials
raw private messages by default
raw emails by default
unredacted provider request headers
secrets from environment variables
full prompt context containing sensitive data
```

## Rules

1. Redaction happens before event persistence, not merely before display.
2. Receipts are user-facing and must be redaction-safe.
3. Error envelopes include `details_redacted` and should expose `safe_message`.
4. Secret detection failures are security bugs.
5. The redaction policy is part of the Trusted Computing Base.

## Future Mobile Redaction

Future mobile capture logs and validation errors must never expose raw location, microphone audio, camera media, contacts, calendar data, photos, health-adjacent data, device identifiers, credentials, tokens, or secrets.

Debug output should use safe summaries, evidence refs, redaction markers, and receipt IDs. Sensor data is untrusted evidence until verified and must not be copied into prompts, memory, logs, receipts, provider envelopes, or user-visible output without redaction and user review.
