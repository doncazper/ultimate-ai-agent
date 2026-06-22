# Foundation Gate Implementation Plan v0.103.0

v0.103.0 keeps Foundation Gate coverage aligned with the Founder Loop V1
currentness, branch-hygiene, and baseline consolidation release while
preserving the existing contract-first, local-first, review-gated, and
disabled-by-default posture.

## Required Currentness Checks

- Active docs must preserve the current v0.103.0 / 0.103.0 baseline.
- Active docs must preserve checkpoint-m169 as the latest accepted repository
  checkpoint.
- Active docs must preserve checkpoint-m166 and checkpoint-m167 as accepted
  local model lane checkpoints.
- Product release truth, public security posture, API docs, Control Center
  route/status docs, release evidence docs, Founder Loop docs, and version
  metadata must agree on the current baseline.
- Historical v0.102.0 through v0.102.3, v1.x, and v2.0.0 tags remain immutable
  audit records and must not be treated as current release authority.

## Required Commands

```bash
.venv/bin/python scripts/release/check_version_truth.py
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
.venv/bin/python scripts/verify_control_center_frontend.py
PYTHONPATH=src .venv/bin/python -m pytest --collect-only -q
.venv/bin/python scripts/verify_all.py --skip-pytest
```

## Founder Loop V1 Currentness Rule

The bounded FCC-V1 proof-lane conveyor is complete through FCC-V1-007 for
release-surface truth, API perimeter, backend-owned Action/Chat/Memory
decisions, Evidence Timeline productization, and proofed `/actions`, `/chat`,
`/memory`, and `/evidence` route surfaces only. `/today` remains partial, and
`/inbox`, `/settings`, model lifecycle, full private UI functional tuning,
public beta, public distribution, and production authority remain outside this
baseline.

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

v0.103.0 does not allow production authority, public distribution, public beta,
signed installer readiness, notarization, hosted deployment, runtime
model/provider calls, unrestricted network/browser automation, shell/subprocess
authority, connector runtime, connector writes, account auth, email/calendar
reads, arbitrary plugin execution, mobile control, memory writes, context
injection, raw prompt export, raw provider payload export, credential handling,
or raw private-content persistence.
