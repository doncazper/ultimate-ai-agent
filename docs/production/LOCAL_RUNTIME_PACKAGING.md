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
separate M151-M167 gates and runbooks. The Setup Assistant may reference this
lane as local package proof, but that does not turn the proof into signed
installer, public distribution, app launch, or production authority.

GitHub-hosted bootstrap installer authority is defined separately in
`docs/production/M167_GITHUB_BOOTSTRAP_LOCAL_INSTALLER.md`. That milestone is
definition-only until a later implementation slice adds pinned release,
checksum/signature verification, approval, receipt, PATH rollback, and static
unsafe-pattern tests.

## Safe Defaults

| Control | Default |
|---|---|
| API host exposure | Host-loopback only: defaults to `127.0.0.1:8000`; local proof runs may override with `UAA_LOCAL_RUNTIME_API_PORT`. |
| Control Center exposure | Host-loopback only: defaults to `127.0.0.1:5173`; local proof runs may override with `UAA_LOCAL_RUNTIME_CONTROL_CENTER_PORT`. |
| Container internal bind | Internal container bind only so Docker host-loopback publishing works; not a remote support claim. |
| API access posture | Existing UAA route policy and side-effect classification only; no new auth or execution authority. |
| Local OpenWebUI test gateway | Disabled by default. |
| Access logs | API container starts with access logs disabled to avoid raw path-oriented request logs. |
| File API safe root | Container-local `/app` only. |
| Container scratch state | API runtime scratch state uses container-local tmpfs, including `/app/.uaa`; it is not release evidence. |
| Local state | Ignored `.uaa/local-runtime/` state only. |
| Secret material | Generated local secret material, stored under ignored `.uaa/local-runtime/`, and never committed. |

## Local Secret Generation

Before starting the package manually, create the local secret file:

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

The automated proof script performs the same local-only pattern: it writes
ignored secret material with `token_urlsafe`, calls `chmod(0o600)`, and keeps
the generated value out of the proof summary. The verifier rejects static proof
material and non-safe summary shapes.

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

If either default loopback port is already in use, set
`UAA_LOCAL_RUNTIME_API_PORT` or `UAA_LOCAL_RUNTIME_CONTROL_CENTER_PORT` to an
available local port before starting compose. The package must remain bound to
`127.0.0.1`.

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

## Local Unsigned macOS App Bundle Proof

The packaging lane also has a repeatable local unsigned `.app` bundle proof:

```bash
.venv/bin/python scripts/build_local_macos_app_bundle_proof.py
```

The proof writes an ignored local bundle under UAA local state and emits a
safe-ref summary only. The generated `Ultimate AI Agent Local.app` wraps the
existing `./scripts/dev/uaa trial-boot` launcher entrypoint. The verifier checks
the app bundle, `Info.plist`, launcher entrypoint, and boundary note without
launching the app or starting services:

```bash
.venv/bin/python scripts/verify_local_macos_app_bundle_proof.py
```

This proof is local-only and unsigned. It is not signed, not notarized, not a
DMG, not a public installer, not an auto-updater, not a LaunchAgent or daemon,
and not production distribution authority. It is also distinct from successful
daily-loop execution proof: the `.app` proof confirms the local launcher
artifact shape without launching the app, while runtime launch evidence remains
the Docker/local-runtime proof or a separately scoped trial-boot smoke receipt.

## Rollback

To stop the local package:

```bash
docker compose -f packaging/local-runtime/compose.yaml down --remove-orphans
```

To remove local generated state after confirming no evidence is needed:

```bash
rm -rf .uaa/local-runtime
```

To remove the local unsigned `.app` proof bundle, delete the ignored local proof
state created by `scripts/build_local_macos_app_bundle_proof.py`.

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
