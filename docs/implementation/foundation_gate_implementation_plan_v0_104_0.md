# Foundation Gate Implementation Plan v0.104.0

v0.104.0 keeps Foundation Gate coverage aligned with the Founder Command
Center functioning-units and truth-binding hardening baseline.

## Currentness Requirements

- Active docs must preserve the current v0.104.0 / 0.104.0 baseline.
- Active docs must preserve checkpoint-m169 as the latest accepted repository
  checkpoint until a later checkpoint tag is explicitly accepted.
- The Control Center remains a shell. Python Agent Core remains the authority
  boundary.
- Operational maturity, OpenAPI, route metadata, redaction, documentation
  integrity, and frontend truth-binding checks remain hard gates.

## No New Authority

v0.104.0 does not allow production authority, public distribution, public beta,
runtime model/provider calls, unrestricted network access, browser automation,
shell/subprocess execution, connector writes, live email/calendar runtime,
plugin runtime import, memory writes, context injection, generic action
execution, or raw private-content persistence.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities before any enablement. v0.104.0 does not grant plugin runtime import or skill execution authority.

## Verification

- `.venv/bin/python scripts/verify_current_baseline.py --skip-static-scans`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
- `make frontend-check`
