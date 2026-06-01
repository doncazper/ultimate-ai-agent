# Ultimate AI Agent Workspace Standards

Active baseline: v0.14.3.

This repository is the Ultimate AI Agent foundation workspace. Treat it as a contract-first Python core, not a production runtime integration layer.

## API Boundary

- `/api/manifest` is the typed metadata endpoint for the current API boundary.
- OpenAPI is the public route contract. Keep operation IDs stable, unique, and generated from method plus path.
- API routes may validate, preview, evaluate policy, or expose metadata. They must not perform production provider calls or autonomous external actions.
- Do not add runtime model calls.
- Do not add web fetching.
- Do not add provider SDK calls, browser automation, production persistence, scanner runtimes, or runtime agent config loading.
- M8 model runtime endpoints are simulated/dry-run only. Do not add live runtime URLs, tokenizers, billing APIs, network calls, or provider SDK calls.
- M8.5 approval endpoints are local/dev validation-only. Do not treat arbitrary approval strings as authority, and do not add production auth, OAuth, persistence, or external actions.
- M9 local loopback runtime support is dev-only, loopback-only, approval-gated, and must default to validation or simulated fallback. Caller policy cannot disable the loopback-only guard or use allowed host lists to authorize remote hosts; hostile policy inputs should fail validation before adapter execution. Tests and Foundation Gate must use fake transport and must not make real network/model calls.
- M10 manual local loopback smoke support is manual-only, disabled by default, approval-gated, loopback-only, and restricted to a fixed non-sensitive smoke prompt. Do not pass user prompts, files, memory, context packs, secrets, or task content into smoke execution. Do not add a public smoke execute API route.
- M10.5 remote worker support is foundation-only, disabled by default, mock/local metadata only, and dry-run only. Do not add live mesh networking, tailnet execution, listeners, network calls, job dispatch, remote subagents, remote Tool Broker execution, remote approvals, personal-data access, write/send actions, critical remote work, background services, or private transport configuration.
- v0.14.3 keeps private mesh/tailnet terms vendor-neutral and open-source-first. Headscale, generic WireGuard, Tailscale, private mesh, tailnet, and LAN transports are planned/disabled metadata only. Do not install, call, configure, or integrate Headscale, Tailscale, tailscaled, WireGuard, or `wg`; do not commit tailnet names, hostnames, private IPs, node keys, auth keys, OAuth data, credentials, or tokens.
- v0.14.4 mobile companion work is planning-only. Phone/mobile is a future control, approval, capture, receipt, and status surface, not the agent brain. Do not add a mobile app, iOS/Android/native package, React Native, Expo, Flutter, Swift, Kotlin, Capacitor, Ionic, sensor access, OS permission integration, device pairing, background service, notification runtime, network call, autonomous mobile action, or runtime Device Capability Broker.
- v0.14.5 documentation integrity work may update docs, release notes, verifier scripts, and gate documentation checks only. Keep active docs aligned with `VERSION.md`, `pyproject.toml`, package `__version__`, README import docs, release notes, API docs, roadmap, and Foundation Gate plan.
- API validation errors must be sanitized and must never echo raw invalid input values or secret-like field values.

## Workspace

- Keep milestone changes small and release-gated.
- Prefer typed contracts, deterministic tests, and metadata-only verification before implementation work.
- Before release, run `PYTHONPATH=src python -m pytest`, `python scripts/verify_current_baseline.py`, `python scripts/verify_documentation_integrity.py`, `python scripts/verify_skill_package_security_rule.py`, `python scripts/verify_all.py`, `python scripts/run_foundation_gate.py`, `python scripts/verify_openapi_contract.py`, and `python -m ruff check .`.
- Update `scripts/verify_openapi_contract.py` and the Foundation Gate when the API boundary changes.
- Keep generated OpenAPI JSON out of git unless a release explicitly asks for a versioned schema snapshot.
- Never move existing release tags or force-push release history. Create the next release tag only after verification passes and the remote tag is confirmed absent.
