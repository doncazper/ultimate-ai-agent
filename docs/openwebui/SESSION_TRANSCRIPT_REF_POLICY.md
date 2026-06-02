# Session Transcript Ref Policy

Status: Active M21 contract documentation for v0.25.0. Contract-only.

OpenWebUI session refs, message refs, and transcript refs are identifiers only. Refs are not authority. Refs cannot approve actions, execute tools, write memory, call runtimes, call providers, access credentials, or bypass Python Agent Core.

M21 refs carry safe metadata:

- session refs identify a future OpenWebUI chat shell session.
- message refs identify planned message metadata.
- transcript refs identify planned transcript metadata.
- event refs and receipt refs point to governed records.
- safe summaries are redacted and user-visible.

Refs must not contain secrets, cookies, API keys, admin tokens, browser profile paths, private user data, raw prompts, raw transcript content, raw file content, raw memory content, raw provider payloads, or raw tool arguments.

Transcript raw content is not stored in M21. Future transcript handling must be explicitly reviewed, redacted, receipt-backed, and routed through Python Agent Core. Future transcript handling must preserve Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, Redaction, and Foundation Gate boundaries.

This patch adds no OpenWebUI integration, no storage backend, no browser profile access, no OpenWebUI admin/session token handling, no memory provider implementation, and no backend API route.
