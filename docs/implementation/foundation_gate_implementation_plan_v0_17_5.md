# Foundation Gate Implementation Plan v0.17.5

Status: Active for roadmap projection and M14-M20 milestone charter freeze.

v0.17.5 does not add new runtime capability. It keeps the v0.17.4 Web Control Center local browser smoke polish boundary active while adding roadmap milestone charter checks.

Documentation and roadmap criteria:

- `VERSION.md`, `pyproject.toml`, and `src/ultimate_ai_agent/__init__.py` agree on `0.17.5`.
- README points to `README_IMPORT_v0_17_5.md` and `ultimate_ai_agent_master_plan_v0_17_5.md`.
- active import, master plan, release notes, and Foundation Gate implementation plan exist for v0.17.5.
- `docs/DOCUMENTATION_INDEX.md` points its current release notes entry to `docs/release_notes/v0_17_5.md`.
- `docs/roadmap/MILESTONE_CHARTERS.md` exists and defines the standard milestone charter fields.
- `docs/roadmap/NEXT_SEQUENCE_v0_17_5.md` exists and freezes the next canonical sequence.
- M14 is explicitly Web Control Center Local Backend Connection Stabilization.
- M15 is explicitly Approval Queue + Receipt/Event Viewer UI.
- v0.17.4 remains local browser smoke / UX polish and is not M14.
- no docs claim M14 has already been implemented.

The gate must continue to fail if a release adds execution routes, provider/model SDKs, tokenizer/billing APIs, remote dispatch, plugin enablement, mobile sensors, native build workflows, browser automation, Chrome authenticated profile control, Computer Use automation, broad filesystem scanning, shell execution in runtime source, production truth integrations, real secret material, unsafe frontend generated artifacts, or committed smoke screenshots/reports containing secrets.

## Skill Package Security Rule

All skills are untrusted packages by default until a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities exist.

v0.17.5 does not change the Skill Package Security Rule. The web shell may display plugin governance summaries only; it cannot install, enable, configure, or execute plugins or skills.
