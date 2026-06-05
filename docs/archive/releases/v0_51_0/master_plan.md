# v0.51.0 Master Plan

Milestone: M47 - TestFlight Pipeline, Internal Only.

Scope:

- Add internal-only TestFlight pipeline contracts.
- Add checklist stages for source snapshot, build/archive plan, signing asset
  presence check, internal distribution review, rollback, and redacted audit
  receipt planning.
- Add validators, tests, static verification, documentation-integrity coverage,
  and Foundation Gate criteria.
- Update currentness docs and version metadata.

Non-goals:

- no build execution
- no upload execution
- no App Store Connect API call
- no signing asset storage
- no provisioning profile storage
- no certificate or private key storage
- no Fastlane lane
- no CI upload workflow
- no external beta
- no public distribution
- no production authority
- no M48 implementation
