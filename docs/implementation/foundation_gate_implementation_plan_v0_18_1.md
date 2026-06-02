# Foundation Gate Implementation Plan v0.18.1

Status: Active for M14 Web Control Center Local Backend Connection Safety hardening.

v0.18.1 does not add runtime capability or backend API authority. It hardens Foundation Gate coverage for local-only Web Control Center backend connection behavior.

M14 hardening criteria:

- `VERSION.md`, `pyproject.toml`, and `src/ultimate_ai_agent/__init__.py` agree on `0.18.1`.
- README points to `README_IMPORT_v0_18_1.md` and `ultimate_ai_agent_master_plan_v0_18_1.md`.
- active import, master plan, release notes, and Foundation Gate implementation plan exist for v0.18.1.
- Web Control Center API base URL policy allows only relative paths, localhost, 127.0.0.1, and loopback IPv6.
- external absolute API URLs are blocked.
- public IPs, private LAN IPs, non-loopback hostnames, and URL credentials are blocked.
- secret-like API base URL strings and broad secret-like query parameter names are rejected without exposing secret-like values.
- unknown, checking, backend online, degraded, offline-safe, and mock fallback states are visible.
- mock fallback remains non-authoritative.
- backend OpenAPI path count remains `74`.
- M15 Approval Queue + Receipt/Event Viewer UI is not added.

The gate must continue to fail if a release adds execution routes, provider/model SDKs, tokenizer/billing APIs, remote dispatch, plugin enablement, mobile sensors, native build workflows, browser automation, Chrome authenticated profile control, Computer Use automation, broad filesystem scanning, shell execution in runtime source, production truth integrations, real secret material, unsafe frontend generated artifacts, committed smoke screenshots/reports containing secrets, external API hosts, credential handling, cookies, Authorization headers, API keys, analytics/SaaS SDKs, or production Control Center authority.

## Skill Package Security Rule

All skills are untrusted packages by default until a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities exist.

v0.18.1 does not change the Skill Package Security Rule. The web shell may display plugin governance summaries only; it cannot install, enable, configure, or execute plugins or skills.
