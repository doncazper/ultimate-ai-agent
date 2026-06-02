# Foundation Gate Implementation Plan v0.18.3

Status: Active for OpenWebUI and CCC Client Strategy clarification.

v0.18.3 does not add runtime capability, frontend behavior, backend API authority, OpenWebUI integration, native CCC implementation, mobile sensor access, or native build workflows. It adds Foundation Gate coverage for OpenWebUI/CCC strategy docs.

OpenWebUI/CCC strategy criteria:

- `VERSION.md`, `pyproject.toml`, and `src/ultimate_ai_agent/__init__.py` agree on `0.18.3`.
- README points to `README_IMPORT_v0_18_3.md` and `ultimate_ai_agent_master_plan_v0_18_3.md`.
- active import, master plan, release notes, and Foundation Gate implementation plan exist for v0.18.3.
- required `docs/ui/*` strategy files exist.
- UI strategy docs say OpenWebUI is the preferred conversational web shell.
- UI strategy docs say OpenWebUI is not the agent brain.
- UI strategy docs say CCC is the governance/control layer.
- UI strategy docs say Open Design does not replace OpenWebUI.
- UI strategy docs define CCC Web, CCC iOS, CCC Android, and CCC macOS.
- UI strategy docs say no OpenWebUI integration is implemented.
- UI strategy docs say no CCC native implementation, native build workflow, mobile sensor access, or OS permission integration is added.

The gate must continue to fail if a release adds execution routes, provider/model SDKs, tokenizer/billing APIs, remote dispatch, plugin enablement, mobile sensors, native build workflows, browser automation, Chrome authenticated profile control, Computer Use automation, broad filesystem scanning, shell execution in runtime source, production truth integrations, real secret material, unsafe frontend generated artifacts, committed smoke screenshots/reports containing secrets, external API hosts, credential handling, cookies, Authorization headers, API keys, analytics/SaaS SDKs, design tool enablement, OpenWebUI integration/deployment, native CCC implementation, Android/iOS/macOS app implementation, OS permission integration, signing/keystore/provisioning/App Store/Play Store workflow, or production Control Center authority.

## Skill Package Security Rule

All skills are untrusted packages by default until a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities exist.

v0.18.3 does not change the Skill Package Security Rule. OpenWebUI plugins, functions, pipelines, tools, deployment helpers, and native build plugins remain disabled until dedicated future milestones explicitly approve them.
