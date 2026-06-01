# Foundation Gate Implementation Plan v0.13.2

M9.5 extends the Foundation Gate with stricter loopback policy model checks and approval API cleanup checks.

## Skill Package Security Rule

All skills are untrusted packages by default. Before any skill package can become an executable or high-trust capability it must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

Required checks:

- M9 loopback runtime files exist.
- Remote hosts are denied.
- URL credentials are denied.
- Secret-like query parameters are denied.
- `deny_non_loopback=false` is rejected by loopback policy validation.
- Non-loopback `allowed_hosts` entries are rejected by loopback policy validation.
- Private LAN endpoints are denied.
- Public IP endpoints are denied.
- Caller-supplied policy cannot authorize non-loopback endpoints.
- Arbitrary approval refs cannot authorize local loopback execution.
- Approval API loads validation grants through a public LocalApprovalAuthority helper.
- Local/dev approval validation is required for real execution decisions.
- Foundation Gate uses fake transport only.
- M9 runtime code has no provider SDK, tokenizer, billing, shell, or broad network imports.
- Simulated fallback remains available.
- Model output remains non-authoritative.
- M8 simulated runtime behavior remains valid.

Verification commands:

```bash
PYTHONPATH=src python -m pytest
python scripts/verify_current_baseline.py
python scripts/verify_skill_package_security_rule.py
python scripts/verify_all.py
python scripts/run_foundation_gate.py
python scripts/verify_openapi_contract.py
python -m ruff check .
```
