# Foundation Gate Implementation Plan v0.17.1

Status: Active for Web Control Center safety polish.

v0.17.1 extends the Foundation Gate and verifier boundary for the M13 Web Control Center shell.

M13 safety criteria:

- frontend shell files remain present under `apps/control-center`.
- frontend dependencies remain limited to local React/Vite/TypeScript/Vitest/Testing Library tooling.
- frontend source remains read-only/preview-only.
- the only frontend POST target is `/control-center/actions/preview`.
- action preview controls are visibly preview-only and do not expose execute/run/send/deploy/enable/approve buttons.
- frontend endpoint allowlists contain no execute, plugin enablement, remote dispatch, runtime execution, or mobile sensor targets.
- frontend source uses no local storage, session storage, cookies, browser credential APIs, service workers, IndexedDB, CacheStorage, clipboard writes, notifications, push APIs, camera, microphone, or location APIs.
- mock data is visibly mock, non-authoritative, and keeps runtime, remote, private mesh, mobile, plugin, and native capabilities disabled or blocked.
- generated artifacts and native/mobile project files are not release artifacts.
- `scripts/verify_control_center_frontend.py` passes and is run by `scripts/verify_all.py`.
- backend API path count remains `74` with no new execution route.

The gate must continue to fail if a release adds execution routes, provider/model SDKs, tokenizer/billing APIs, remote dispatch, plugin enablement, mobile sensors, native build workflows, browser automation, broad filesystem scanning, shell execution in runtime source, production truth integrations, or real secret material.

## Skill Package Security Rule

All skills are untrusted packages by default until a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities exist.

v0.17.1 does not change the Skill Package Security Rule. The web shell may display plugin governance summaries only; it cannot install, enable, configure, or execute plugins or skills.
