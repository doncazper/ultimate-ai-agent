# Ultimate AI Agent Master Plan v0.7.0

Status: Active project baseline after implementing Milestone M3 (Consent Ledger and Tool Broker Policy Engine).

## v0.7.0 change log

v0.7.0 implements Milestone M3, adding consent ledgers, Pydantic permission contracts, local policy evaluations, risk checking, dry-run calculations, untrusted tool firewalls, Foundation Gate blocks, and validation API routes.

Added:

```text
src/ultimate_ai_agent/core/consent/__init__.py
src/ultimate_ai_agent/core/consent/enums.py
src/ultimate_ai_agent/core/consent/grants.py
src/ultimate_ai_agent/core/consent/policies.py
src/ultimate_ai_agent/core/consent/ledger.py
src/ultimate_ai_agent/core/consent/decisions.py
src/ultimate_ai_agent/core/consent/validation.py
src/ultimate_ai_agent/core/tools/__init__.py
src/ultimate_ai_agent/core/tools/enums.py
src/ultimate_ai_agent/core/tools/manifests.py
src/ultimate_ai_agent/core/tools/requests.py
src/ultimate_ai_agent/core/tools/decisions.py
src/ultimate_ai_agent/core/tools/broker.py
src/ultimate_ai_agent/core/tools/registry.py
src/ultimate_ai_agent/core/tools/capability_firewall.py
src/ultimate_ai_agent/core/tools/validation.py
tests/test_consent_grants.py
tests/test_consent_ledger.py
tests/test_consent_policy_decisions.py
tests/test_tool_manifests.py
tests/test_tool_broker_authorization.py
tests/test_tool_broker_risk_policy.py
tests/test_capability_firewall.py
tests/test_tool_broker_foundation_gate.py
tests/test_tool_broker_redaction_and_receipts.py
tests/test_m3_api_routes.py
docs/release_notes/v0_7_0.md
docs/implementation/foundation_gate_implementation_plan_v0_7_0.md
```

Updated:

```text
README.md
VERSION.md
pyproject.toml
src/ultimate_ai_agent/__init__.py
src/ultimate_ai_agent/api/app.py
tests/__init__.py
scripts/verify_current_baseline.py
```

## Rule

Consent validation separates credentials from access permissions (having a credential does not imply consent). The Tool Broker risk calculator strictly enforces human approval requirements on high-risk or external mutating actions, and blocks all Skill/MCP/A2A/SDK categories via the Foundation Gate.

## Roadmap pointer

The active roadmap lives at `docs/canonical/09_roadmap.md`. Versioned master plans are historical context. If this master plan and a canonical file disagree, the active canonical file wins.
