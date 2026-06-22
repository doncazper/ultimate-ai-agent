# UAA-P1-087.1 Local Launcher Dual-Surface Boot Readiness

Status: Implemented.

UAA-P1-087.1 hardens the existing repo-local launcher and clickable macOS
`.command` path for the first private operator trial. Control Center is the
first-party product surface. OpenWebUI is the secondary local shell and may
remain blocked until local prerequisites are ready.

## Contract

The private trial boot command is:

```bash
./scripts/dev/uaa trial-boot
```

The inline command ref is `./scripts/dev/uaa trial-boot`.

It:

- starts the existing backend and Control Center localhost services;
- opens Control Center first;
- starts and opens OpenWebUI only when Docker, the pinned local image, and the
  UAA local gateway are ready;
- prints readiness status for backend, Control Center, and OpenWebUI;
- reports safe launcher log refs such as `launcher-log:backend`,
  `launcher-log:frontend`, and `launcher-log:openwebui`;
- preserves `./scripts/dev/uaa stop` as the stop path for all trial services.

The generated `Ultimate AI Agent.command` file now calls `trial-boot`, then
prints `status` and `openwebui status` so a double-clicked boot ends with the
same readiness and blocked-state guidance as the CLI path.

## Blocked States

OpenWebUI remains blocked or degraded when Docker is missing, Docker Desktop is
not ready, the pinned image is absent, or the UAA local gateway is not ready.
When Control Center is ready but the secondary shell is blocked, the CLI names
the state `primary_ready_secondary_blocked`.
No packages are installed and no images are pulled by `uaa trial-boot`; the
existing approval-bound setup path remains separate.

## Safety

No new runtime authority.

This milestone does not add backend routes, OpenAPI operations, middleware,
auth, CORS, security headers, rate limits, provider/model calls, connector
writes, action execution, memory writes, shell payload execution, Docker
installation, image pulls, LaunchAgents, daemons, signing, notarization, public
beta, public distribution, production readiness, or production authority.

## Verification

```bash
.venv/bin/python scripts/verify_uaa_p1_087_1_local_launcher_boot_readiness.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_dev_launcher.py tests/test_uaa_p1_087_1_local_launcher_boot_readiness.py
```
