# Foundation Gate Implementation Plan v0.17.3

Status: Active for documentation current-release label cleanup.

v0.17.3 does not add new Foundation Gate runtime criteria. It keeps the v0.17.2 Web Control Center CI, static safety, and local browser smoke readiness criteria active while strengthening documentation integrity checks for release-label drift.

Documentation integrity criteria:

- `VERSION.md`, `pyproject.toml`, and `src/ultimate_ai_agent/__init__.py` agree on `0.17.3`.
- README points to `README_IMPORT_v0_17_3.md` and `ultimate_ai_agent_master_plan_v0_17_3.md`.
- active import, master plan, release notes, and Foundation Gate implementation plan exist for v0.17.3.
- `docs/DOCUMENTATION_INDEX.md` points its current release notes entry to `docs/release_notes/v0_17_3.md`.
- non-active release notes under `docs/release_notes/` do not claim to be current release notes.
- historical release notes remain available as audit records.
- the v0.17.2 M13 frontend CI, browser-smoke-readiness, static safety, and no-execution checks continue to run.

The gate must continue to fail if a release adds execution routes, provider/model SDKs, tokenizer/billing APIs, remote dispatch, plugin enablement, mobile sensors, native build workflows, browser automation, Chrome authenticated profile control, Computer Use automation, broad filesystem scanning, shell execution in runtime source, production truth integrations, real secret material, or unsafe frontend generated artifacts.

## Skill Package Security Rule

All skills are untrusted packages by default until a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities exist.

v0.17.3 does not change the Skill Package Security Rule. The web shell may display plugin governance summaries only; it cannot install, enable, configure, or execute plugins or skills.
