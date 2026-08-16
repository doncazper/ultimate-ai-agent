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
./scripts/dev/uaa setup
./scripts/dev/uaa setup install --target openwebui
./scripts/dev/uaa trial-boot
./scripts/dev/uaa launch-ui
.venv/bin/python scripts/dev/uaa_founder_loop.py inspect
.venv/bin/python scripts/dev/uaa_founder_loop.py promote-action-envelope --today-item-ref briefing:storage-state-first-loop --idempotency-ref idempotency-ref:local-review
.venv/bin/python scripts/dev/uaa_developer_queue.py catalog --pretty
.venv/bin/python scripts/dev/uaa_developer_queue.py scout --pretty
```

`uaa_founder_loop.py` is a repo-local FCC-V1-003 inspection helper. It prints
safe refs for Today, Actions, receipts, and Evidence Timeline state, and can
create a review-only Today-to-Action envelope receipt. It does not execute
actions, call providers, write connectors, run shell/subprocess work, write
memory, or echo raw local paths.

## Local Developer Work Coordinator

`uaa_developer_queue.py` is a separate local developer coordination plane for
the existing long-running UAA planning queue. It indexes canonical planning
sources, requires explicit branch/worktree/verifier/merge-gate triage plus a
registered, heartbeating node before a Mac or Beast worker can claim a task,
uses a recoverable snapshot/receipt transaction journal, prevents active
branch/worktree collisions, and exposes exact completion or cancellation plus
a terminal scope-packet archive gate. It provides fixed read-only local Git
hygiene scouting; GitHub queries remain outside coordinator v1.
It neither runs developer agents nor mutates Git, worktrees, pull requests, or
UAA product-runtime authority. See
`docs/developer/LOCAL_DEVELOPER_WORK_COORDINATOR.md` for the shared-ledger and
handoff workflow.

## First-Run Setup Doctor

Run the local setup doctor before starting OpenWebUI:

```bash
uaa setup --profile local-llama --write-env
```

The setup doctor scans the local developer profile at a safe summary level.
Use `--profile minimal`, `--profile frontend-only`, `--profile openwebui-smoke`,
or `--profile local-llama` to avoid checks that do not apply to the first-run
path you are trying to prepare.

Depending on the selected profile, it checks Python, Control Center
dependencies, the `uaa` shell command, Docker readiness, OpenWebUI image/port
status, backend/frontend port identity, `llama-server` readiness, local
gateway env, the UAA `/v1/models` gateway status when the backend is already
running, OpenWebUI local data state, and the selected model alias expected by
UAA. It prints grouped blocked/manual steps plus an ordered repair plan so
first-run setup is diagnosis-first.

It writes `.uaa/dev/local-llama.env` only when `--write-env` is provided. That
file is gitignored, local-dev-only, and contains the M164 local loopback
gateway values used by the launcher. If the file already exists, `--write-env`
keeps it in place and prints a safe diff summary; use `--overwrite-env` only
when you intentionally want to replace the local template.

Useful diagnostic-only variants:

```bash
uaa setup --profile minimal --plan
uaa setup --profile local-llama --explain
uaa setup --profile local-llama --check-env .uaa/dev/local-llama.env
uaa setup --profile local-llama --write-report
uaa setup --profile openwebui-smoke --json
```

The setup doctor deliberately does not install packages, download models, pull
Docker images, collect provider credentials, configure frontier-provider API
keys, mutate OpenWebUI internals, or enable model/provider output as authority.
Frontier provider setup is reported as not scoped until a reviewed milestone
defines credential handling, policy, approval, redaction, audit, rollback, and
verifier coverage.

## Scoped OpenWebUI Image Install

The explicit M167 local-dev installer slice is limited to the configured
OpenWebUI Docker image:

```bash
uaa setup install --target openwebui
uaa setup install --target openwebui --receipt "$HOME/.local/state/uaa/openwebui-install-receipt.json"
```

That command prints the exact `docker pull` command, asks you to type
`install openwebui` before running it, and writes a redacted receipt (default:
`.uaa/dev/setup-install-receipts/`, or a custom path with `--receipt`). A custom
path must be under your home directory, must not already exist or cross a
symlink, and must not cross a world-writable directory. Reusing the same custom
receipt path fails closed with exit code 2.

The receipt destination is bound into the preview hash. Unattended approval is
disabled: bare `--yes` and the deprecated `--approval-token` and
`--write-approval-token` inputs fail closed before Docker is resolved, and no
token path is read or written. Rerun without those options and type the exact
interactive confirmation. Denial receipts label approval authority as `none`
and the decision source as `pre-authority-input-guard` because the approval
stack is never constructed for unattended input.

It does not install Python, Node/npm dependencies, Homebrew packages,
llama.cpp, models, providers, plugins, browser tooling, credentials, or system
services. It does not start OpenWebUI. Roll back the image with:

```bash
docker image rm ghcr.io/open-webui/open-webui@sha256:7f1b0a1a50cfbac23da3b16f96bc968fd757b26dc9e54e93813d61768ea9184e
```

## Designated UI Launcher

Use the private operator trial boot for the dual-surface local path. It opens
the first-party Control Center first, then opens OpenWebUI as a secondary local
shell only when prerequisites are ready:

```bash
uaa trial-boot
```

Use the one-command launcher for the designated UI. The current default target
is Control Center:

```bash
uaa launch-ui
```

`uaa launch-ui` starts or reuses the local backend and Control Center, verifies
that the occupied ports are UAA-owned, opens the configured Control Center URL
(defaults to `http://127.0.0.1:5173` and can be overridden with
`UAA_LAUNCHER_*` variables), and keeps
the launch localhost-only. It does not install packages, download models, pull
Docker images, or collect credentials.

OpenWebUI can still be launched explicitly as the secondary local shell:

```bash
uaa launch-ui --target openwebui
```

That path verifies the local `/v1` gateway, opens the configured OpenWebUI URL
(default `http://127.0.0.1:3000`, overridable with
`UAA_LAUNCHER_OPENWEBUI_*`), and
fails closed if the OpenWebUI image is not already present locally. It points to
`uaa setup install --target openwebui` for the separate approval-bound image
pull path.

Launcher ports can be switched per run:

```bash
UAA_LAUNCHER_FRONTEND_PORT=5174 UAA_LAUNCHER_OPENWEBUI_PORT=3001 ./scripts/dev/uaa launch-ui --target openwebui
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

Optional M164 llama.cpp-backed OpenWebUI shell commands:

```bash
source .uaa/dev/local-llama.env

llama-server \
  --host 127.0.0.1 \
  --port 8080 \
  --hf-repo ggml-org/gemma-3-1b-it-GGUF \
  --hf-file gemma-3-1b-it-Q4_K_M.gguf \
  --alias "${UAA_LLAMA_CPP_MODEL_ID:-uaa-llama-cpp-local}" \
  --api-key "${UAA_LLAMA_CPP_API_KEY:-uaa-llama-backend-dev}"
```

Direct GGUF launchers can set `UAA_LLAMA_CPP_MODEL_PATH` under
`$HOME/Models/llama.cpp/model-cache`; `.uaa/model-cache` remains a compatibility
link for existing local-dev tooling. Leave that `llama-server` terminal open.
In a second terminal:

```bash
UAA_LLAMA_CPP_GATEWAY_ENABLED=1 \
UAA_LLAMA_CPP_GATEWAY_KEY=uaa-local-llama-cpp-dev \
UAA_LLAMA_CPP_BASE_URL=http://127.0.0.1:8080 \
UAA_LLAMA_CPP_MODEL_ID=uaa-llama-cpp-local \
UAA_LLAMA_CPP_API_KEY=uaa-llama-backend-dev \
uaa start
```

Then start or restart OpenWebUI with the same local gateway model:

```bash
UAA_LLAMA_CPP_GATEWAY_ENABLED=1 \
UAA_LLAMA_CPP_GATEWAY_KEY=uaa-local-llama-cpp-dev \
UAA_LLAMA_CPP_MODEL_ID=uaa-llama-cpp-local \
uaa openwebui start
```

In this path, OpenWebUI selects `uaa-llama-cpp-local`, UAA validates that exact
model ID and forwards to loopback `llama-server`, and llama.cpp runs the
reviewed local GGUF. The launcher does not print the M164 bearer value in
OpenWebUI status output or Docker command metadata. Streaming, tools,
functions, memory writes, context injection, raw prompt logging, and
provider/model output as authority remain denied.

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
closing. The generated desktop launcher enables
`UAA_LAUNCHER_AUTO_SWITCH_ON_PORT_BLOCK=1` so if a requested launcher port is
already occupied by an unverified local process, it transparently switches to a
nearby free port and continues. Later status and stop commands reuse that
endpoint only when its running PID and existing launcher metadata still match
the exact reconstructed service command.

## Safety Boundary

- localhost-only: backend default `127.0.0.1:8000`, frontend default
  `127.0.0.1:5173`. Both can be overridden via `UAA_LAUNCHER_*` environment
  variables. Host overrides accept only `127.0.0.1` or `localhost`; IPv6
  loopback is not implemented. Setup probes and the Control Center proxy use
  the same validated endpoints.
- optional OpenWebUI test shell is localhost-only at default
  `127.0.0.1:3000` and can also be overridden with
  `UAA_LAUNCHER_OPENWEBUI_*`.
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
