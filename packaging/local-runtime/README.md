# Local Runtime Packaging Configs

Status: active UAA-P1-014 local-runtime packaging configs

These files define a reproducible loopback-first local stack for release
candidate testing. They do not claim public distribution, hosted production
support, signed installer readiness, or broad runtime authority.

Canonical operator guidance lives in
`docs/production/LOCAL_RUNTIME_PACKAGING.md`.

## Files

| File | Purpose |
|---|---|
| `../../scripts/dev/uaa_local_runtime.py` | Supported clean-source-gated start/stop entry with local bearer handoff. |
| `packaging/local-runtime/compose.yaml` | Local Docker Compose stack for the UAA API and Control Center only. |
| `packaging/local-runtime/Dockerfile.api` | Local API image build recipe. |
| `packaging/local-runtime/Dockerfile.control-center` | Local Control Center image build recipe. |
| `.dockerignore` | Excludes ignored runtime state, env files, reports, dependency caches, and generated artifacts from build context. |

## Boundary

- Host ports are bound only to `127.0.0.1`.
- Host ports default to `8000` for the API and `5173` for Control Center, and
  can be overridden with `UAA_LOCAL_RUNTIME_API_PORT` and
  `UAA_LOCAL_RUNTIME_CONTROL_CENTER_PORT` for local proof runs.
- The API receives the exact selected loopback Control Center origin through
  `UAA_CONTROL_CENTER_CORS_ORIGIN`; fallback ports remain exact-scoped and do
  not broaden the CORS policy.
- Docker containers bind internally so host-loopback publishing can reach them.
- API runtime scratch state uses container-local tmpfs, including `/app/.uaa`.
- The package does not include OpenWebUI, `llama-server`, connector writes,
  plugin runtime import, browser automation, mobile control, or autonomous
  background execution.
- A generated local secret file is mounted from ignored `.uaa/` state. It is
  not a checked-in credential and not a production auth claim.
- Compose requires `UAA_BUILD_COMMIT` and the wrapper admission marker from
  `scripts/dev/uaa_local_runtime.py`; the wrapper verifies a clean exact
  checkout before starting and binds that revision into the API image and
  runtime environment.
