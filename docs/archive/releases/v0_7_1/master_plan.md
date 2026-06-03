Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.7.1

Status: Active project baseline after post-M3 policy hardening and Milestone M3.5 (Secret Broker and Provider Registry foundation).

## v0.7.1 change log

v0.7.1 includes the v0.7.x post-M3 hardening pass and implements M3.5 as contract-only local/dev infrastructure.

Post-M3 hardening:

```text
Tool Broker enforces ExecutionContract allowed/forbidden tools.
Tool Broker enforces ContextPack tool_permissions.
High-risk and external actions no longer trust arbitrary approval_ref strings.
Mutable idempotent tool requests require idempotency_key.
Capability Firewall fails closed for filesystem, network, and credential requests.
M3 boundary Pydantic models reject unexpected fields.
PermissionAction.any wildcard deny overrides wildcard or specific allows.
Execution Contract factory helpers populate redacted request_summary values.
```

M3.5 added:

```text
src/ultimate_ai_agent/core/secrets/
src/ultimate_ai_agent/core/providers/
tests/test_secret_credentials.py
tests/test_secret_broker_redaction.py
tests/test_secret_broker_no_leakage.py
tests/test_provider_manifests.py
tests/test_provider_registry.py
tests/test_provider_resolver_free_first.py
tests/test_provider_result_envelope.py
tests/test_provider_normalization_contracts.py
tests/test_m35_api_routes.py
docs/release_notes/v0_7_1.md
docs/implementation/foundation_gate_implementation_plan_v0_7_1.md
```

Updated:

```text
README.md
VERSION.md
pyproject.toml
src/ultimate_ai_agent/__init__.py
src/ultimate_ai_agent/api/app.py
scripts/verify_current_baseline.py
scripts/verify_all.py
```

## Rule

Secrets are represented by credential references and opaque handles, not raw values. Provider Registry and Provider Resolver select and validate provider metadata only. v0.7.1 does not perform real provider calls, store production secrets, run OAuth, execute tools, call models, run scanners, or delegate to external SDK/A2A runtimes.

## Roadmap pointer

The active roadmap lives at `docs/canonical/09_roadmap.md`. Versioned master plans are historical context. If this master plan and a canonical file disagree, the active canonical file wins.
