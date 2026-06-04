# Master Plan v0.37.2

Status: active release packet.
Current active baseline: **v0.37.2**

v0.37.2 adds local developer launcher tooling for prototype testing without
adding agent capability or starting M34.

## Scope

- Add a repo-local `./scripts/dev/uaa` launcher.
- Support `doctor`, `start`, `ui`, `status`, `logs`, `stop`, and `restart`.
- Start the existing FastAPI backend on `127.0.0.1:8000`.
- Start the existing CCC Web Vite dev server on `127.0.0.1:5173`.
- Store local PID/log state under ignored `.uaa/dev/`.
- Add a macOS `.command` launcher generator.
- Add launcher docs, tests, documentation-integrity checks, and static safety
  verification.

## Non-Goals

- production installer behavior.
- launch daemon, background service, or system-wide privileged install.
- backend routes.
- Control Center execute controls.
- task execution.
- action execution.
- tool execution.
- arbitrary shell execution beyond starting existing local dev servers.
- file mutation beyond launcher-local PID/log files.
- memory writes.
- network/provider/model calls.
- dependencies.
- M34 work.
- production authority.

M34-M40 remain planned/provisional.
