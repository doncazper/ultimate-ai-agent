# Autonomy Mode 4 Scoped Work Session Receipt Plan

M131 receipt metadata is no-effect, safe-summary-only, and safe-ref-only.

A compliant M131 receipt plan may store:

- work-session ref
- scope ref
- policy decision ref
- approval bundle ref
- risk decision ref
- audit ref
- replay ref
- revocation ref
- kill-switch ref
- no-effect receipt plan ref
- safe summary

It must not store raw prompts, raw provider payloads, secrets, credentials,
cookies, raw connector content, raw files, session output, execution output, or
tool/browser/network/plugin/shell results. It must not indicate session start,
autonomous actions, execution, background workers, scheduler activity, beta
release, or production authority.
