<!--
PR title: type(area): concrete behavior or prevented failure

Examples:
- fix(runtime): preserve unknown dispatch outcomes during replay
- feat(goals): recover interrupted durable goal mutations
- ci(verify): isolate resource locks between local verification lanes

Avoid phase-only titles such as "close final gaps", "refresh provenance", or
"parity follow-up". Put milestone and phase details in the body instead.
-->

## Summary

<!-- What problem does this solve? Keep private data and raw logs out. -->

## Scope and approach

<!-- Describe the smallest relevant implementation and important boundaries. -->

## Risk and authority

- [ ] No runtime authority is added or broadened, or this PR implements only an
      accepted exact governed authority-graduation lane and documents its scope
      and safeguards below.
- [ ] Any mutation remains exact-scoped, approval-bound, idempotent, auditable,
      rollback-aware, redacted, and tested.
- [ ] Product language accurately distinguishes implemented, partial, planned,
      blocked, mock-only, skipped, and missing states.

## Verification

<!-- List exact commands and results. State why any relevant check was skipped. -->

## Contribution provenance

- [ ] I have the right to submit every part of this contribution.
- [ ] I identified third-party code, assets, data, and applicable licenses.
- [ ] I disclosed any material AI assistance and personally reviewed the result.
- [ ] This change contains no credentials, private data, raw prompts, raw model
      responses, raw provider payloads, raw logs, or machine-specific details.

## Documentation and compatibility

- [ ] Focused tests accompany behavior changes.
- [ ] Relevant docs and indexes are updated.
- [ ] Route changes update OpenAPI, API manifest, and side-effect classification.
- [ ] UI changes preserve backend ownership and include frontend verification.
