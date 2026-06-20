# Local Runtime Packaging

Status: active UAA-P1-014 Docker/local runtime packaging

Scope: reproducible loopback-first local runtime packaging for release-readiness
testing. This package is local-only evidence scaffolding. It is not a public
distribution, hosted production deployment, signed installer, or production
runtime authority.

## Package Contents

| Artifact | Role | Safety boundary |
|---|---|---|
| `packaging/local-runtime/compose.yaml` | Starts the local UAA API and Control Center containers for release-candidate testing. | Publishes only `127.0.0.1:8000` and `127.0.0.1:5173`; no remote host binding. |
| `packaging/local-runtime/Dockerfile.api` | Builds the local API image from repo source and project metadata. | Uses the existing FastAPI route contract; no new route or runtime authority. |
| `packaging/local-runtime/Dockerfile.control-center` | Builds the local Control Center image from `apps/control-center/package-lock.json`. | Uses the existing local Control Center shell; no execute controls. |
| `.dockerignore` | Keeps local state and private material out of image build context. | Excludes `.uaa`, env files, generated reports, dependency caches, and key-like files. |
| `.env.example` | Documents safe local environment defaults. | Contains no checked-in secret value; local secrets are generated under ignored `.uaa/` state. |

The package intentionally excludes OpenWebUI, `llama-server`, model download,
model runtime launch, connector writes, plugin runtime import, browser
automation, mobile control, remote execution, and autonomous background
execution. Local model and OpenWebUI readiness remain governed by their
separate M151-M167 gates and runbooks.

GitHub-hosted bootstrap installer authority is defined separately in
`docs/production/M167_GITHUB_BOOTSTRAP_LOCAL_INSTALLER.md`. That milestone is
definition-only until a later implementation slice adds pinned release,
checksum/signature verification, approval, receipt, PATH rollback, and static
unsafe-pattern tests.

## Safe Defaults

| Control | Default |
|---|---|
| API host exposure | Host-loopback only: `127.0.0.1:8000`. |
| Control Center exposure | Host-loopback only: `127.0.0.1:5173`. |
| Container internal bind | Internal container bind only so Docker host-loopback publishing works; not a remote support claim. |
| API access posture | Existing UAA route policy and side-effect classification only; no new auth or execution authority. |
| Local OpenWebUI test gateway | Disabled by default. |
| Access logs | API container starts with access logs disabled to avoid raw path-oriented request logs. |
| File API safe root | Container-local `/app` only. |
| Local state | Ignored `.uaa/local-runtime/` state only. |
| Secret material | Generated local secret material, stored under ignored `.uaa/local-runtime/`, and never committed. |

## Local Secret Generation

Before starting the package, create the local secret file:

```bash
mkdir -p .uaa/local-runtime
.venv/bin/python - <<'PY'
from pathlib import Path
from secrets import token_urlsafe

target = Path(".uaa/local-runtime/uaa_local_runtime_secret")
target.write_text(token_urlsafe(48) + "\n", encoding="utf-8")
target.chmod(0o600)
print("created local runtime secret ref")
PY
```

The secret file is a local packaging secret reference only. It is not a
credential vault, not a production auth mechanism, and not release evidence.
Do not paste the generated value into docs, reports, logs, commits, tickets, or
chat transcripts.

## Local Start

After generating the local secret file:

```bash
docker compose -f packaging/local-runtime/compose.yaml up --build
```

Then inspect:

```bash
curl http://127.0.0.1:8000/health
open http://127.0.0.1:5173
```

These commands are operator-run local packaging commands. The repository does
not execute them as part of documentation verification, and this package does
not add shell/subprocess authority to UAA runtime code.

## Configuration Boundaries

- Do not change published host bindings to `0.0.0.0`, LAN addresses, public
  IPs, or hostnames.
- Do not add provider API keys, connector credentials, cookies, environment
  dumps, raw prompts, raw responses, raw provider payloads, raw paths, or raw
  logs to images, compose files, reports, or docs.
- Do not add OpenWebUI, `llama-server`, model download, model runtime launch,
  connector writes, plugin runtime import, browser automation, mobile control,
  or autonomous background execution to this package.
- Do not claim public distribution, hosted production support, signed release
  readiness, broad production packaging, or enterprise support from this
  local package.

## Rollback

To stop the local package:

```bash
docker compose -f packaging/local-runtime/compose.yaml down --remove-orphans
```

To remove local generated state after confirming no evidence is needed:

```bash
rm -rf .uaa/local-runtime
```

To roll back UAA-P1-014, revert this document, the
`packaging/local-runtime/` configs, `.dockerignore`, `.env.example` changes,
docs index links, Kanban/roadmap/product-truth updates, and documentation
integrity verifier checks.

For local state categories outside the packaging files, use
`docs/production/LOCAL_STATE_ROLLBACK_RUNBOOK.md` and keep backup restore,
safe-disable, rollback, and unsupported recovery states distinct.

## Known Gaps

- Base image digest pinning is not yet a release-blocking gate.
- GitHub bootstrap installer implementation remains future-scoped by
  `docs/production/M167_GITHUB_BOOTSTRAP_LOCAL_INSTALLER.md`.
- Live restore, hosted production deployment, signed installers, and public
  distribution remain future-scoped.
- Local model runtime proof still depends on M166/M167 evidence and UAA local
  model verification lanes.
