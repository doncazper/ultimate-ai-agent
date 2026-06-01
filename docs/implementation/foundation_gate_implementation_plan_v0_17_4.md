# Foundation Gate Implementation Plan v0.17.4

Status: Active for Web Control Center local browser smoke polish.

v0.17.4 does not add new runtime capability. It keeps the v0.17.2 Web Control Center CI, static safety, and local browser smoke readiness criteria active while extending browser smoke readiness verification to require safe local browser smoke reporting documentation.

Documentation and frontend criteria:

- `VERSION.md`, `pyproject.toml`, and `src/ultimate_ai_agent/__init__.py` agree on `0.17.4`.
- `apps/control-center/package.json` and `package-lock.json` agree on `0.17.4`.
- README points to `README_IMPORT_v0_17_4.md` and `ultimate_ai_agent_master_plan_v0_17_4.md`.
- active import, master plan, release notes, and Foundation Gate implementation plan exist for v0.17.4.
- `docs/DOCUMENTATION_INDEX.md` points its current release notes entry to `docs/release_notes/v0_17_4.md`.
- `docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md` exists and documents local-only, non-authoritative, secret-free reporting.
- Web Control Center pages expose clear route headings for local browser smoke review.
- loading and empty states remain accessible and read-only.
- action preview risk level remains preview metadata only.
- frontend safety and browser-smoke-readiness verifiers continue to run.

The gate must continue to fail if a release adds execution routes, provider/model SDKs, tokenizer/billing APIs, remote dispatch, plugin enablement, mobile sensors, native build workflows, browser automation, Chrome authenticated profile control, Computer Use automation, broad filesystem scanning, shell execution in runtime source, production truth integrations, real secret material, unsafe frontend generated artifacts, or committed smoke screenshots/reports containing secrets.

## Skill Package Security Rule

All skills are untrusted packages by default until a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities exist.

v0.17.4 does not change the Skill Package Security Rule. The web shell may display plugin governance summaries only; it cannot install, enable, configure, or execute plugins or skills.
