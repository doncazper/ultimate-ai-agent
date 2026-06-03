# 50 — Data Classification Policy

Status: Active foundation contract, v0/provisional until Foundation Gate.

## Purpose

Model routing, consent, logging, redaction, memory, file access, prompt construction, debugging, and provider calls all need a shared language for data sensitivity.

## Core rule

> Every durable memory, file reference, event, provider result, prompt input, tool result, and debug artifact should carry a data classification.

## Classification labels

```text
public
user_private
project_private
sensitive_personal
credential_secret
regulated
third_party_confidential
system_internal
tcb_protected
```

## Label meanings

- `public`: safe to cite or display broadly.
- `user_private`: personal user data not intended for public sharing.
- `project_private`: internal project information.
- `sensitive_personal`: health, finances, private messages, family, identity, or other sensitive personal data.
- `credential_secret`: API keys, tokens, cookies, passwords, private keys.
- `regulated`: legal, medical, financial, or compliance-bound data.
- `third_party_confidential`: client/customer/vendor confidential information.
- `system_internal`: internal traces, policies, implementation details.
- `tcb_protected`: Trusted Computing Base artifacts that autonomous self-improvement cannot modify.

## Classification effects

| Classification | Prompt use | Logging | Memory | Model routing |
|---|---|---|---|---|
| public | allowed | allowed | allowed | any allowed provider |
| user_private | minimize | redacted summaries | consent required | privacy-aware routing |
| sensitive_personal | only if necessary | highly redacted | explicit consent | local/private preferred |
| credential_secret | never | never | never | never to model |
| tcb_protected | policy context only | references only | immutable by self-improvement | high-reliability review |

## Rules

1. Secrets are not data to summarize; they are values to isolate.
2. External content is untrusted even when public.
3. Data classification must travel with the object through result envelopes and events.
4. If classification is unknown, default to the safer higher classification until resolved.

## Future Mobile Data Classification

Mobile sensor data is classified conservatively by default.

```text
manual typed note: user-provided, low unless content indicates otherwise
selected photo/document import: private or sensitive until reviewed
camera capture: sensitive by default
microphone clip: sensitive by default
precise location: sensitive by default
contacts/calendar/photos: private or sensitive by default
device identifiers: sensitive by default
```

Future mobile capture must classify before storage, memory write, provider routing, or external send.

## M24 Memory Classification

M24 memory records use local `public`, `internal`, `personal`, `sensitive`,
`regulated`, and `forbidden` classification values. `forbidden` memory is
rejected. Credential-like or secret-like content is rejected before storage.

Memory is recall, not authority. Memory is not ground truth. Canonical files,
evidence manifests, receipts, Event Ledger records, and user-reviewed sources
outrank memory. M24 adds no automatic writes, model-output writes, local LLM
output writes, OpenWebUI chat memory writes, mobile capture writes, tool output
writes, vector DB, embeddings, cloud memory, raw session history, or context
injection.

## M25 Truth/Evidence Classification

M25 claim, evidence, source, receipt, and verification refs use classification
metadata for safe review only. The Truth Source Router and Evidence Claim
Checker may classify refs, safe summaries, status, staleness, revocation,
conflict, and decision metadata, but they must not expose raw prompts, raw
files, raw memory contents, raw provider payloads, raw credentials, or raw
session history.

M25 adds no web search, external verification, source fetching, model/provider
calls, memory writes, evidence mutation, backend routes, vector DB, embeddings,
context injection, or production authority.
