# Foundation Gate Implementation Plan v0.18.2

Status: Active for Open Design System and UI Design Governance.

v0.18.2 does not add runtime capability, frontend behavior, backend API authority, design-tool integration, or design SaaS authority. It adds Foundation Gate coverage for repo-owned design governance docs.

Design governance criteria:

- `VERSION.md`, `pyproject.toml`, and `src/ultimate_ai_agent/__init__.py` agree on `0.18.2`.
- README points to `README_IMPORT_v0_18_2.md` and `ultimate_ai_agent_master_plan_v0_18_2.md`.
- active import, master plan, release notes, and Foundation Gate implementation plan exist for v0.18.2.
- required `docs/design/*` files exist.
- design docs say no design tools are enabled.
- design docs say the design source of truth is repo-owned.
- design docs say screenshots and design artifacts must not contain secrets.
- design docs say no design SaaS is authority.
- design docs say no automatic design-to-code or automatic design sync is enabled.
- Control Center docs link the design governance docs.
- M15 Approval Queue + Receipt/Event Viewer UI is not added.

The gate must continue to fail if a release adds execution routes, provider/model SDKs, tokenizer/billing APIs, remote dispatch, plugin enablement, mobile sensors, native build workflows, browser automation, Chrome authenticated profile control, Computer Use automation, broad filesystem scanning, shell execution in runtime source, production truth integrations, real secret material, unsafe frontend generated artifacts, committed smoke screenshots/reports containing secrets, external API hosts, credential handling, cookies, Authorization headers, API keys, analytics/SaaS SDKs, design tool enablement, automatic design sync, automatic design-to-code, or production Control Center authority.

## Skill Package Security Rule

All skills are untrusted packages by default until a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities exist.

v0.18.2 does not change the Skill Package Security Rule. The web shell may display plugin governance summaries only; it cannot install, enable, configure, or execute plugins or skills.
