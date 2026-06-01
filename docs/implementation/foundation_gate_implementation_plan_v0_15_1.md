# Foundation Gate Implementation Plan v0.15.1

Status: Active M11 gate clarification plan.

v0.15.1 keeps the v0.15.0 M11 Foundation Gate scope and clarifies runtime readiness taxonomy only.

Gate checks include:

- runtime readiness files and docs exist.
- runtime capability matrix surfaces are safe: simulated-only, manual-only, dry-run-only, planned-disabled, supported validation-only, or blocked.
- `local_loopback_policy` is supported validation-only policy support, not automated smoke execution or production runtime readiness.
- manual smoke report validation rejects raw prompts, secrets, remote endpoints, full bodies, execution claims, production runtime/readiness/evidence claims, live mesh/tailnet claims, mobile sensor claims, plugin/native build claims, and authoritative model output.
- `fake_manual_loopback_smoke` is allowed only as a fake/test report origin and is not production evidence.
- readiness report does not claim production readiness, real model readiness, remote execution readiness, mobile sensor readiness, plugin/native build readiness, or model-output authority.
- API exposes only `/runtime/readiness`, `/runtime/capability-matrix`, and `/runtime/smoke-reports/validate` for M11.
- gate and verification scripts do not execute `local_loopback_smoke.py`.
- runtime readiness source has no provider SDK, network, tokenizer, billing, shell, eval, or exec capability.
- M11 source/docs do not enable remote mesh, mobile sensor, plugin, native build, or computer-use automation.

The gate must remain deterministic and local. It must not inspect live Codex plugin state, keychains, signing identities, local runtime processes, mobile devices, remote hosts, or provider credentials.

## Skill Package Security Rule

All skills are untrusted packages by default until the repository has a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

v0.15.1 does not add Skill Factory, skill loading, plugin loading, installer behavior, marketplace behavior, or runtime execution through skills. The rule remains a release gate for future capability work.
