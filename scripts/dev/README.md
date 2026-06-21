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
./scripts/dev/uaa launch-ui
```

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
```

That command prints the exact `docker pull` command, asks you to type
`install openwebui` before running it, and writes a redacted receipt under
`.uaa/dev/setup-install-receipts/`. For noninteractive automation, first write
a preview-bound approval token after typed approval:

```bash
uaa setup install --target openwebui --write-approval-token "$HOME/.local/state/uaa/openwebui-install-approval.json"
uaa setup install --target openwebui --yes --approval-token "$HOME/.local/state/uaa/openwebui-install-approval.json"
```

Bare `--yes` fails closed before Docker is resolved.

It does not install Python, Node/npm dependencies, Homebrew packages,
llama.cpp, models, providers, plugins, browser tooling, credentials, or system
services. It does not start OpenWebUI. Roll back the image with:

```bash
docker image rm ghcr.io/open-webui/open-webui@sha256:7f1b0a1a50cfbac23da3b16f96bc968fd757b26dc9e54e93813d61768ea9184e
```

## Designated UI Launcher

Use the one-command launcher for the designated UI. The current target is
OpenWebUI:

```bash
uaa launch-ui
```

`uaa launch-ui` starts or reuses the local backend and OpenWebUI, verifies the
local `/v1` gateway, opens `http://127.0.0.1:3000`, and keeps the launch
localhost-only. It does not install packages, download models, pull Docker
images, or collect credentials; if the OpenWebUI image is not already present
locally, it fails closed and points you to
`uaa setup install --target openwebui`.

The Control Center can still be launched explicitly:

```bash
uaa launch-ui --target control-center
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
