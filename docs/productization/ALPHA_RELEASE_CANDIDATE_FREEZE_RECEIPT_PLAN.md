# M149 Alpha Release Candidate Freeze Receipt Plan

M149 receipt plans are no-effect receipt records. They may point to release
candidate refs, freeze checklist refs, alpha readiness refs, evidence index
refs, blocker summary refs, signoff review refs, M150 promotion gate refs,
audit refs, replay refs, revocation refs, and kill-switch refs.

Receipts must remain safe-ref-only and redacted-summary-only. They must not
contain raw private content, raw prompts, raw provider payloads, credentials,
cookies, release artifacts, build outputs, exported repositories, or release
automation payloads.

The receipt plan confirms no release publication, no release tag, no tag
creation, no artifact build, no artifact upload, no artifact export, no
external distribution, no beta release, no M150 release, and no production
authority. v1.2.0-alpha remains planned/provisional.
