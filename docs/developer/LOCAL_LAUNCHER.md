# Local Developer Launcher

Status: active developer tooling
Baseline: v0.37.2

The local developer launcher makes the Ultimate AI Agent prototype easier to
start, inspect, and stop from a terminal or a double-clickable macOS command
file. It is a developer convenience only. It is not a production installer,
does not run as a daemon, and does not add execution authority.

## Quick Start

From the repository root:

```bash
./scripts/dev/uaa doctor
./scripts/dev/uaa start
./scripts/dev/uaa trial-boot
./scripts/dev/uaa ui
./scripts/dev/uaa status
./scripts/dev/uaa logs
./scripts/dev/uaa stop
```

The launcher starts the existing FastAPI backend and CCC Web Control Center
development server. For private operator trial boot, Control Center is the
first-party product surface and OpenWebUI is the secondary local shell.

| Service | URL | Command family |
|---|---|---|
| Backend API | `http://127.0.0.1:8000` (default, configurable) | `.venv/bin/python -m uvicorn ultimate_ai_agent.api.app:app` |
| Control Center | `http://127.0.0.1:5173` (default, configurable) | `npm run dev` inside `apps/control-center/` |
| OpenWebUI local shell | `http://127.0.0.1:3000` (default, configurable) | pinned Docker image, started only when already present locally |

Both services bind to localhost only. The launcher refuses non-loopback hosts
and never binds to `0.0.0.0`.

You can switch all launcher ports at runtime with environment overrides:

- `UAA_LAUNCHER_BACKEND_HOST` / `UAA_LAUNCHER_BACKEND_PORT`
- `UAA_LAUNCHER_FRONTEND_HOST` / `UAA_LAUNCHER_FRONTEND_PORT`
- `UAA_LAUNCHER_OPENWEBUI_HOST` / `UAA_LAUNCHER_OPENWEBUI_PORT`
- `UAA_LAUNCHER_AUTO_SWITCH_ON_PORT_BLOCK` (set to `1`, `true`, `on`, or `yes`)

Example:

```bash
UAA_LAUNCHER_FRONTEND_PORT=5174 UAA_LAUNCHER_OPENWEBUI_PORT=3001 ./scripts/dev/uaa trial-boot
```

The macOS `.command` launcher enables `UAA_LAUNCHER_AUTO_SWITCH_ON_PORT_BLOCK=1` so it automatically tries a nearby free port for any service when the requested port is occupied by an unverified local process.
Host overrides are limited to `127.0.0.1` and `localhost`; accepted `localhost`
variants are canonicalized to `127.0.0.1`, and `::1` is rejected because this
launcher does not implement IPv6 URL or socket handling. Setup probes and the
Control Center proxy use the same validated endpoints. A later
`status` or `stop` process reloads an auto-selected endpoint only while the PID
is running and the existing launcher metadata matches the exact reconstructed
service command.

## Commands

| Command | Purpose |
|---|---|
| `uaa doctor` | Checks local prerequisites, package scripts, and port state. |
| `uaa start` | Starts the backend and Control Center if they are not already running. |
| `uaa trial-boot` | Opens Control Center first, then opens OpenWebUI as the secondary local shell when prerequisites are ready. |
| `uaa ui` | Opens the Control Center URL in the default browser. |
| `uaa status` | Prints backend, Control Center, and OpenWebUI service status, PIDs, URLs, safe log refs, and log locations. |
| `uaa logs` | Prints recent launcher logs. |
| `uaa logs --follow` | Follows launcher logs until Ctrl-C. |
| `uaa stop` | Stops only processes whose PID files were created by this launcher. |
| `uaa restart` | Runs stop, then start. |

Runtime state lives under ignored local files:

```text
.uaa/dev/pids/
.uaa/dev/logs/
.uaa/dev/*.json
```

These files are local launcher state only and must not be committed.

## Optional Shell Command

To use `uaa` directly:

```bash
mkdir -p ~/.local/bin
ln -s "$(pwd)/scripts/dev/uaa" ~/.local/bin/uaa
```

Then ensure `~/.local/bin` is on your `PATH`.

Remove the shell shortcut with:

```bash
rm ~/.local/bin/uaa
```

No `sudo`, `/usr/local/bin` write, global package install, or production
installer is required.

## macOS Double-Click Launcher

Create a repo-local clickable command file:

```bash
.venv/bin/python scripts/dev/create_macos_launcher.py --target repo
```

Or create one on the current user's Desktop:

```bash
.venv/bin/python scripts/dev/create_macos_launcher.py --target desktop
```

Double-click behavior:

1. Runs `./scripts/dev/uaa doctor`.
2. Runs `./scripts/dev/uaa trial-boot`.
3. Opens Control Center first as the first-party product surface.
4. Opens OpenWebUI as the secondary local shell when Docker, the pinned local
   image, and the UAA local gateway are ready.
5. Prints status, OpenWebUI status, safe log refs, blocked-state guidance, and
   log locations.
6. Keeps the terminal window open until a key is pressed.

The generated `.command` file is not a signed app, launch daemon, installer, or
background service. Remove it like any ordinary local file.

## Safety Boundary

The launcher adds no agent capability and no production authority.

No packages are installed and no images are pulled by `uaa trial-boot`.
If Control Center is ready but OpenWebUI is blocked, the launcher reports the
state `primary_ready_secondary_blocked`.

It does not add:

- backend API routes
- action execution
- tool execution
- task execution
- shell or subprocess execution beyond starting the existing local dev servers
- file mutation beyond launcher-local PID/log files under `.uaa/dev/`
- memory writes
- model/provider calls
- network calls beyond localhost health checks and local dev-server traffic
- Control Center execute controls
- dependencies
- launch daemon or background worker behavior

The launcher does not print environment variables, secrets, `.env` content,
raw prompts, raw model output, raw file content, cookies, tokens, or provider
payloads.

## Troubleshooting

If `doctor` reports a missing Python environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

If `doctor` reports missing Control Center packages:

```bash
cd apps/control-center
npm install
```

If a port is already in use, `uaa start` will not start a duplicate launcher
process on that port. Use `uaa status`, inspect the reported process/log state,
or stop the unrelated process manually if it is not launcher-owned. You can also
switch to free ports using the env vars above and relaunch.

Always stop launcher-owned services with:

```bash
./scripts/dev/uaa stop
```

Future production app packaging, signed macOS apps, managed installers,
background services, and broader local capability work belong to later reviewed
milestones.

For UAA-P1-014 loopback-first Docker/local runtime packaging, use
`docs/production/LOCAL_RUNTIME_PACKAGING.md`. That package is a local
release-readiness test stack only; it does not replace this launcher and does
not claim public distribution, hosted production support, or signed installer
readiness.
