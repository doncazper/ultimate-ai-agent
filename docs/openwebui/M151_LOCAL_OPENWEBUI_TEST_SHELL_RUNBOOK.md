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

If OpenWebUI is run directly on the host instead of Docker, use this base URL:

```text
http://127.0.0.1:8000/v1
```

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

If the UAA gateway is disabled, stop and restart the backend with:

```bash
./scripts/dev/uaa stop
UAA_OPENWEBUI_TEST_GATEWAY_ENABLED=1 ./scripts/dev/uaa start
```

If the OpenWebUI port is already occupied, stop the other local process or use
the status command to see whether the launcher already owns it.
