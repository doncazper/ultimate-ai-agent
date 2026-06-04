# README Import v0.37.2

Status: active release packet.
Current active baseline: **v0.37.2**

v0.37.2 adds a local developer launcher for prototype testing. It is a
developer-experience/tooling patch after v0.37.1 and does not start M34.

The launcher provides:

- `./scripts/dev/uaa doctor`
- `./scripts/dev/uaa start`
- `./scripts/dev/uaa ui`
- `./scripts/dev/uaa status`
- `./scripts/dev/uaa logs`
- `./scripts/dev/uaa stop`
- `./scripts/dev/uaa restart`
- a macOS `.command` launcher generator for opening the local Control Center

The backend startup path is the existing FastAPI app via uvicorn on
`127.0.0.1:8000`. The frontend startup path is the existing CCC Web Vite dev
server on `127.0.0.1:5173`.

Launcher state lives under ignored `.uaa/dev/` PID/log files.

The patch adds no production installer, launch daemon, backend route, Control
Center execute control, task/action/tool execution, model/provider call, memory
write, filesystem mutation beyond launcher-local PID/log files, dependency,
M34 work, or production authority.

OpenAPI path count remains `74`. M34-M40 remain planned/provisional.
