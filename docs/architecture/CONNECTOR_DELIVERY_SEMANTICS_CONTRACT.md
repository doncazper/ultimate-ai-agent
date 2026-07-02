# Connector Delivery Semantics Contract

Status: contract-only foundation.

This document defines how future connector delivery proposals must be represented before any connector write or send authority can exist. The Python Agent Core owns the contract. Control Center may later display the posture, but presentation does not grant delivery authority.

## Scope

The contract adds:

- connector delivery envelopes bound to durable run refs
- target-session refs as identifiers only
- origin cleanup posture refs
- outbound approval refs as identifiers only
- idempotency key refs
- redacted subject and body-summary refs
- attachment refs, evidence refs, expected receipt refs
- rollback and safe-disable posture refs
- delivery timeline metadata states
- read-only CLI inspection through task decomposition

The contract does not send, write, sync, authenticate, or connect accounts.

## Delivery States

- `draft_created_metadata_only`
- `pending_approval`
- `approval_denied`
- `delivery_blocked`
- `delivery_ready_not_sent`
- `retry_scheduled_metadata_only`
- `failed_metadata_only`
- `canceled_metadata_only`
- `sent_not_supported`

`delivery_ready_not_sent` means the metadata contract has enough refs for review. It does not mean a message, event, CRM update, or connector write was delivered.

## Required Gates

Every envelope requires:

- `source_connector_safety_freeze_ref`
- `run_ref`
- `delivery_ref`
- `connector_ref`
- `channel_ref`
- `target_session_ref`
- `origin_ref`
- `origin_cleanup_posture_ref`
- `outbound_approval_ref`
- `idempotency_key_ref`
- `redacted_subject_ref`
- `redacted_body_summary_ref`
- `expected_receipt_refs`
- `rollback_posture_ref`
- `safe_disable_posture_ref`
- `audit_ref`
- `replay_ref`

Unknown connector refs and unknown channel refs block. `approval_test` refs, wildcard approvals, and source-freeze drift block. Target/session refs remain identifiers only and cannot encode raw contact data, account identity, credentials, cookies, tokens, usernames, hostnames, local paths, or raw message content.

## Blocked Authority

This lane explicitly blocks:

- connector writes
- email, calendar, CRM, or message sends
- account sync
- OAuth or credential collection
- cookie/session handling
- attachment download
- provider/model calls
- live web or browser runtime
- shell execution
- background delivery workers
- schedulers
- production, public beta, or public release claims
- raw body, prompt, response, provider payload, file content, contact data, local path, credential, cookie, token, username, hostname, or secret-like persistence

## Inspection

Repo-local inspection is read-only:

```bash
PYTHONPATH=src .venv/bin/python -m ultimate_ai_agent.core.task_decomposition.cli inspect-connector-deliveries
```

The command returns safe refs, blocked state, no-send posture, and denied authority flags only. It does not approve, send, deliver, retry, schedule, revoke, or connect anything.

## Future Promotion

A later connector delivery implementation would need a separate accepted milestone with exact LocalApprovalAuthority scope, PolicyEngine gates, idempotency, audit/replay, redacted receipts, rollback/safe-disable posture, UI/CLI/API parity, red-team coverage, and explicit route/product-language updates.
