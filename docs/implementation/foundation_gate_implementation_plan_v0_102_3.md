# Foundation Gate Implementation Plan v0.102.3

v0.102.3 keeps Foundation Gate coverage aligned with the Founder Command Center
product-spine hardening baseline while preserving the existing contract-first,
local-first, review-gated, and disabled-by-default posture.

## Required Currentness Checks

- Active docs must preserve the current v0.102.3 / 0.102.3 baseline.
- Active docs must preserve checkpoint-m168 as the latest accepted repository
  checkpoint.
- Active docs must preserve checkpoint-m166 and checkpoint-m167 as accepted
  local model lane checkpoints.
- Product release truth, public security posture, API docs, Control Center
  route/status docs, release evidence docs, Founder Loop docs, and version
  metadata must agree on the current baseline.
- Historical v0.102.0, v0.102.1, v0.102.2, v1.x, and v2.0.0 tags remain
  immutable audit records and must not be treated as current release authority.

## Required Commands

```bash
.venv/bin/python scripts/release/check_version_truth.py
PYTHONPATH=src .venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
PYTHONPATH=src .venv/bin/python -m pytest tests/test_gate_evaluator_characterization.py tests/test_gate_architecture_guard.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py tests/test_openapi_contract.py
make frontend-check
```

## Founder Command Center Product-Spine Rule

The Founder Command Center surfaces may expose storage-backed summaries,
command-palette navigation, visual regression proof, and local packaging proof
only when they keep safe refs, bounded summaries, explicit blocked states, and
reviewable backend/API contracts visible. They do not grant mutation authority
unless a later scoped milestone defines the exact approval, idempotency,
rollback, evidence, and test contract.

## Foundation Gate Modularity Rule

`core/gate/evaluators.py` remains the public compatibility facade. Extracted
route-boundary evaluator data may be exempted from static-safety source scans
only by exact file path and only as evaluator data. Route-boundary checks,
OpenAPI checks, side-effect classification, redaction checks, approval checks,
PolicyEngine checks, and LocalApprovalAuthority checks remain release-blocking.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before any installation, loading, execution, credential access, tool exposure,
or autonomous workflow use.

## Denials

v0.102.3 does not allow production authority, public distribution, public beta,
signed installer readiness, notarization, hosted deployment, runtime
model/provider calls, unrestricted network/browser automation, shell/subprocess
authority, connector runtime, connector writes, account auth, email/calendar
reads, arbitrary plugin execution, mobile control, memory writes, context
injection, raw prompt export, raw provider payload export, credential handling,
or raw private-content persistence.
