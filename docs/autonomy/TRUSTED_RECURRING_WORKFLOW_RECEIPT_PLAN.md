# Trusted Recurring Workflow Receipt Plan

M132 receipt plans are no-effect receipts. They store safe summaries and safe
refs only.

Receipt plans bind:

- trusted workflow ref
- scope ref
- M131 scoped work-session decision ref
- M97 recurring contract ref
- M98 scoped low-risk recurring ref
- cadence ref
- approval bundle ref
- approval renewal ref
- expiration ref
- audit ref
- replay ref
- revocation ref
- kill-switch ref

Receipt plans must not store raw prompts, raw provider payloads, secrets, raw
recurring workflow payloads, workflow execution output, or scheduler output.
They must record no workflow start, no recurring runtime start, no scheduler
start, no execution, and no side effects.
