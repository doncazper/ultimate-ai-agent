# Product Loop 009 Chat To Loop Handoff

Status: implemented as a backend-owned local read model over existing Chat receipts and handoff receipts.

Product Loop 009 adds `chat_to_loop_handoff_read_model` to existing Founder
Loop read payloads for Today, Action Inbox, and Morning Briefing:

```text
contract-ref:product-loop-009-chat-to-loop-handoff:v1
```

The read model classifies safe Chat-to-loop proposals into canonical review
outcomes:

- remember-this
- create-action
- add-to-plan
- defer
- ask-human
- blocked

`remember-this` is a reviewed memory-intake proposal only. It is not a memory
write, memory truth, context injection, prompt stuffing, model authority, or an
instruction to act. `create-action` and `add-to-plan` are proposal refs only.
`defer`, `ask-human`, and `blocked` make uncertain or unsafe handoffs visible
without creating execution authority.

This lane reuses durable Chat receipt and handoff storage. It adds a
backend-owned read-model grouping for Chat turn refs, handoff receipt refs,
created proposal refs, evidence refs, idempotency refs, outcome refs, and
blocked authority refs. The model output remains non-authoritative, and all
claims are safe refs or bounded labels. No raw prompt content, raw response
content, provider exchange content, raw logs, raw local paths, usernames,
hostnames, credentials, secrets, cookies, tokens, account identifiers, or
provider payloads are allowed in the read model.

No model output authority. No direct memory writes. No automatic memory writes.
No context injection. No tool execution. No connector writes. No action
execution. No plan execution. No provider/model calls. No live web. No
shell/subprocess execution. No browser execution. No production authority.

The companion CLI inspection path is:

```bash
PYTHONPATH=src .venv/bin/python scripts/inspect_chat_to_loop_handoff.py
```

Inspection is read-only and redacted. It emits `state_not_found_no_write` for
missing local Founder Loop state and must not create storage while inspecting.
Control Center renders the read model only when backend-owned payloads validate;
unsafe payloads and mock-only fallback fail closed. Any immediate Chat handoff
receipt shown after a POST is labeled as pending backend refresh until the
backend read model is visible again.

No-authority phrases: No model output authority; No direct memory writes; No automatic memory writes; No context injection; No tool execution; No connector writes; No action execution; No plan execution; No provider/model calls; No live web; No shell/subprocess execution; No browser execution; No production authority.

## Verification Lane

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_chat_to_loop_handoff_v1.py tests/test_fcc_v1_004_chat_durable_receipt_handoff.py tests/test_control_center_founder_loop_api.py
PYTHONPATH=src .venv/bin/python scripts/verify_product_loop_009_chat_to_loop_handoff.py
```

## Still Blocked

This lane adds no direct memory writes, no automatic memory writes, no hard
delete, no export, no context injection, no hidden memory use, no action
execution, no plan execution, no tool execution, no workflow execution, no
connector writes, no connector runtime, no provider/model calls, no live web,
no browser execution, no shell/subprocess execution, no public beta, no
distribution, and no production authority.
