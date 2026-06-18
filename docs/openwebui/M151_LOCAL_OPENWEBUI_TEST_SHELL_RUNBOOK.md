# M151 Local OpenWebUI Test Shell Runbook

This runbook starts a local test shell using Docker and the UAA developer
launcher. It does not install OpenWebUI into the Python package and does not
add OpenWebUI as a repository dependency.

## Start UAA

From the repo root:

```bash
UAA_OPENWEBUI_TEST_GATEWAY_ENABLED=1 ./scripts/dev/uaa start
```

Confirm the backend is ready:

```bash
curl -H "Authorization: Bearer uaa-local-test" http://127.0.0.1:8000/v1/models
```

## Check OpenWebUI Readiness

```bash
./scripts/dev/uaa openwebui doctor
```

The doctor checks Docker, the UAA backend, the M151 local gateway, and the local
OpenWebUI port.

## Start OpenWebUI

```bash
./scripts/dev/uaa openwebui start
```

Open:

```text
http://127.0.0.1:3000
```

The launcher starts OpenWebUI with:

- base URL for the container: `http://host.docker.internal:8000/v1`
- local bearer value: `uaa-local-test`
- model: `uaa-safe-local`
- OpenAI-compatible streaming disabled
- Ollama adapter disabled for the local smoke path

M151 denies streaming requests, so OpenWebUI must send ordinary non-streaming
chat completions to the local gateway.

If OpenWebUI is run directly on the host instead of Docker, use this shape:

```bash
mkdir -p .uaa/dev
test -f .uaa/dev/openwebui_secret_key || \
  (umask 077 && openssl rand -hex 32 > .uaa/dev/openwebui_secret_key)

DATA_DIR="$PWD/.uaa/dev/openwebui-data" \
WEBUI_SECRET_KEY="$(cat "$PWD/.uaa/dev/openwebui_secret_key")" \
WEBUI_AUTH="False" \
OPENAI_API_BASE_URL="http://127.0.0.1:8000/v1" \
OPENAI_API_BASE_URLS="http://127.0.0.1:8000/v1" \
OPENAI_API_KEY="uaa-local-test" \
OPENAI_API_KEYS="uaa-local-test" \
ENABLE_OPENAI_API="True" \
ENABLE_OLLAMA_API="False" \
ENABLE_PERSISTENT_CONFIG="False" \
DEFAULT_MODELS="uaa-safe-local" \
DEFAULT_MODEL_PARAMS='{"stream_response":false}' \
WEBUI_URL="http://127.0.0.1:3000" \
uvx --python 3.11 open-webui@latest serve --host 127.0.0.1 --port 3000
```

This direct-host fallback uses OpenWebUI outside the UAA package. It does not
add OpenWebUI as a repository dependency.

## Status, Logs, Stop

```bash
./scripts/dev/uaa openwebui status
./scripts/dev/uaa openwebui logs
./scripts/dev/uaa openwebui logs --follow
./scripts/dev/uaa openwebui stop
```

Logs are written under:

```text
.uaa/dev/logs/
```

## Manual Smoke Prompt

Select `uaa-safe-local` and send:

```text
hello from openwebui smoke test
```

Expected response:

```text
UAA safe local test gateway is online.
```

The response must not echo raw prompt content. The response safety receipt must
show no provider call, no tool execution, no memory write, no context injection,
no external network, no raw prompt logging, and no production authority.

## Troubleshooting

If Docker is missing, install Docker Desktop and rerun:

```bash
./scripts/dev/uaa openwebui doctor
```

If Docker Desktop is installed but still in first-run setup, open Docker
Desktop, finish the local setup prompts, and rerun the doctor command. The
doctor uses a bounded Docker engine probe and should fail quickly when Docker
is installed but not ready.

If the UAA gateway is disabled, stop and restart the backend with:

```bash
./scripts/dev/uaa stop
UAA_OPENWEBUI_TEST_GATEWAY_ENABLED=1 ./scripts/dev/uaa start
```

If the OpenWebUI port is already occupied, stop the other local process or use
the status command to see whether the launcher already owns it.

If the OpenWebUI chat displays `None`, streaming is probably still enabled in
OpenWebUI. Confirm that `DEFAULT_MODEL_PARAMS='{"stream_response":false}'` is
set for direct-host runs, or restart OpenWebUI through the developer launcher.
