# Local Developer Launcher

Status: local developer tooling only.

The `uaa` launcher starts the existing Ultimate AI Agent FastAPI API boundary
and the existing Control Center Vite development server for local prototype
testing. It is not a production installer, not a daemon, and not execution
authority.

## Commands

```bash
./scripts/dev/uaa doctor
./scripts/dev/uaa start
./scripts/dev/uaa ui
./scripts/dev/uaa status
./scripts/dev/uaa logs
./scripts/dev/uaa stop
./scripts/dev/uaa restart
```

Optional M151 local OpenWebUI test shell commands:

```bash
UAA_OPENWEBUI_TEST_GATEWAY_ENABLED=1 ./scripts/dev/uaa start
./scripts/dev/uaa openwebui doctor
./scripts/dev/uaa openwebui start
./scripts/dev/uaa openwebui status
./scripts/dev/uaa openwebui logs
./scripts/dev/uaa openwebui stop
```

The OpenWebUI path is local-dev-only, disabled by default, localhost-only, and
uses the deterministic `uaa-safe-local` model through UAA's `/v1` local test
gateway. OpenWebUI is a shell, not the agent brain. The M151 path adds no
provider call, tool execution, memory write, context injection, external
network, raw prompt logging, or production authority.

Optional shell command:

```bash
mkdir -p ~/.local/bin
ln -s "$(pwd)/scripts/dev/uaa" ~/.local/bin/uaa
```

Then:

```bash
uaa doctor
uaa start
uaa ui
uaa status
uaa logs
uaa stop
uaa restart
```

The launcher stores local PID and log files under `.uaa/dev/`, which is ignored
by git.

## macOS Launcher

Create a repo-local clickable launcher:

```bash
.venv/bin/python scripts/dev/create_macos_launcher.py --target repo
```

Or create one on the Desktop:

```bash
.venv/bin/python scripts/dev/create_macos_launcher.py --target desktop
```

Double-clicking `Ultimate AI Agent.command` runs doctor checks, starts the
local backend and Control Center if needed, opens the Control Center in the
default browser, prints status and log locations, and waits for a key before
closing.

## Safety Boundary

- localhost-only: backend `127.0.0.1:8000`, frontend `127.0.0.1:5173`.
- optional OpenWebUI test shell is localhost-only at `127.0.0.1:3000`.
- no `0.0.0.0` binding.
- no tool, action, task, shell, browser, mobile, remote, plugin, model/provider,
  or production execution authority.
- no backend routes are added.
- no dependencies are added.
- no memory writes are added.
- no production installer, service manager, launch daemon, signed app, or
  system-wide privileged install is added.

If `doctor` reports missing frontend dependencies, install them explicitly:

```bash
cd apps/control-center
npm install
```

Remove the optional shell symlink with:

```bash
rm ~/.local/bin/uaa
```

Remove a generated repo-local macOS launcher with:

```bash
rm "Ultimate AI Agent.command"
```

For the UAA-P1-014 loopback-first Docker/local runtime package, see
`docs/production/LOCAL_RUNTIME_PACKAGING.md`. The package is local
release-readiness scaffolding only and does not add public distribution,
hosted production support, signed installer readiness, or broader runtime
authority.
