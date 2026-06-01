# Foundation Gate Implementation Plan v0.17.0

Status: Active for M13.

v0.17.0 extends the Foundation Gate with M13 Web Control Center frontend shell checks.

M13 criteria:

- frontend shell files are present under `apps/control-center`.
- frontend dependencies remain limited to local React/Vite/TypeScript/Vitest/Testing Library tooling.
- frontend source is read-only/preview-only.
- the only frontend POST target is `/control-center/actions/preview`.
- mock data is visibly mock, non-authoritative, and keeps runtime, remote, private mesh, mobile, plugin, and native capabilities disabled or blocked.
- generated artifacts and native/mobile project files are not release artifacts.
- backend API path count remains `74` with no new execution route.

The gate must continue to fail if a release adds execution routes, provider/model SDKs, tokenizer/billing APIs, remote dispatch, plugin enablement, mobile sensors, native build workflows, browser automation, broad filesystem scanning, shell execution in runtime source, production truth integrations, or real secret material.

## Skill Package Security Rule

All skills are untrusted packages by default until a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities exist.

M13 does not change the Skill Package Security Rule. The web shell may display plugin governance summaries only; it cannot install, enable, configure, or execute plugins or skills.
