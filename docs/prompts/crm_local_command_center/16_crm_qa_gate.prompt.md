# Phase 16: CRM QA Gate

Branch: `codex/crm-16-qa-gate`

Commit: `Add CRM local command center QA gate`

Goal: Add one verifier for CRM local command center readiness.

Implement:

- `scripts/verify_crm_local_command_center.py`
- `make verify-crm-local` if the Makefile pattern supports scoped verifiers.

Verifier checks:

- docs truth.
- CRM read model.
- routes/OpenAPI when routes exist.
- CLI parity.
- frontend route.
- no raw sensitive data.
- blocked sends/writes/provider/browser/production.
- local mutation receipts if implemented.
- product language.

Tests:

- verifier passes.
- verifier fails on authority creep fixture.
- verifier catches raw-data persistence.

Verification:

- CRM QA verifier.
- documentation integrity.
- product truth verifier.
- operational maturity verifier.
- OpenAPI verifier if routes exist.
- frontend check if frontend changed.
- `git diff --check`
