# Product Loop 011 Settings And Kill-Switch Clarity

Status: implemented read-only posture contract
Scope: Settings surface authority labels, kill-switch posture, feature-flag
posture, backend-owned safe refs, and CLI inspection parity.

Product Loop 011 makes Settings clearer without adding authority. The
`GET /control-center/settings/status` read model now exposes blocked/degraded/partial
labels for web, providers, connectors, memory context use, model runtime, local
model lifecycle, and platform capabilities.

Settings and kill-switch clarity remains status-only:

- no toggles that grant authority
- no provider configuration
- no installer behavior
- no runtime activation
- no feature-flag writes
- no kill-switch execution
- no revocation execution
- no connector runtime
- no connector writes
- no model calls
- no provider SDK calls
- no live web
- no shell/browser execution
- no public beta
- no production readiness claims
- no production authority

The read model cites `/api/manifest`, runtime readiness, the runtime capability
matrix, local model status, source readiness, and the PlatformCapabilityRegistry
snapshot as visibility metadata only. Catalog, manifest, provider, platform, or
Settings visibility does not make a capability callable.

CLI inspection is available through:

```bash
PYTHONPATH=src .venv/bin/python scripts/inspect_settings_authority_posture.py --pretty
```

Verification is available through:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_product_loop_011_settings_kill_switch_clarity.py
```

The Control Center Settings UI renders backend-owned posture rows first and
keeps mutation controls absent. The next safe step after this lane is the
Private product loop trial script.
