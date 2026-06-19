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
./scripts/dev/uaa ui
./scripts/dev/uaa status
./scripts/dev/uaa logs
./scripts/dev/uaa stop
```

The launcher starts the existing FastAPI backend and CCC Web Control Center
development server:

| Service | URL | Command family |
|---|---|---|
| Backend API | `http://127.0.0.1:8000` | `.venv/bin/python -m uvicorn ultimate_ai_agent.api.app:app` |
| Control Center | `http://127.0.0.1:5173` | `npm run dev` inside `apps/control-center/` |

Both services bind to localhost only. The launcher refuses non-loopback hosts
and never binds to `0.0.0.0`.

## Commands

| Command | Purpose |
|---|---|
| `uaa doctor` | Checks local prerequisites, package scripts, and port state. |
| `uaa start` | Starts the backend and Control Center if they are not already running. |
| `uaa ui` | Opens the Control Center URL in the default browser. |
| `uaa status` | Prints service status, PIDs, URLs, and log locations. |
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
2. Starts local backend and Control Center services if needed.
3. Opens the Control Center in the default browser.
4. Prints status and log locations.
5. Keeps the terminal window open until a key is pressed.

The generated `.command` file is not a signed app, launch daemon, installer, or
background service. Remove it like any ordinary local file.

## Safety Boundary

The launcher adds no agent capability and no production authority.

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
or stop the unrelated process manually if it is not launcher-owned.

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
