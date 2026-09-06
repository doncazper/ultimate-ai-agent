# Foundation Gate Implementation Plan v0.14.0

M10 extends the Foundation Gate with manual local loopback smoke-readiness checks.

## Skill Package Security Rule

All skills are untrusted packages by default. Before any skill package can become an executable or high-trust capability it must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

Required checks:

- M10 manual smoke policy, request, result, transport, script, and tests exist.
- The stdlib HTTP transport is isolated to manual local smoke code.
- `requests`, `httpx`, provider SDKs, tokenizers, billing APIs, shell execution, and broad network imports remain blocked.
- Tests, CI, `verify_all.py`, and Foundation Gate do not call the manual smoke script.
- Foundation Gate uses fake smoke transport only.
- Public API exposes smoke validation only and no smoke execute route.
- The smoke prompt is fixed and non-sensitive.
- User prompts, files, memory, context packs, secrets, and task content cannot be passed into smoke execution.
- Remote, private LAN, public IP, credential-bearing, and secret-query endpoints are denied.
- Scoped local approval is required.
- Arbitrary approval refs are denied.
- Smoke responses are non-authoritative and secret-scanned.
- Simulated fallback remains available.

Verification commands:

```bash
PYTHONPATH=src python -m pytest
python scripts/verify_current_baseline.py
python scripts/verify_skill_package_security_rule.py
python scripts/verify_all.py
python -I -B -S scripts/run_foundation_gate.py
python scripts/verify_openapi_contract.py
python -m ruff check .
```
