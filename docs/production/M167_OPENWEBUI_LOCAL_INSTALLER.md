# M167 OpenWebUI Local Installer

Status: scoped local-dev installer/downloader milestone.

This M167 scoped productionization slice authorizes exactly one new setup
side effect: an explicit operator-approved pull of the configured OpenWebUI
Docker image for the local developer OpenWebUI path.

## Exact Capability

`uaa setup install --target openwebui` may run:

```bash
docker pull ghcr.io/open-webui/open-webui@sha256:7f1b0a1a50cfbac23da3b16f96bc968fd757b26dc9e54e93813d61768ea9184e
```

The command is local developer tooling only. It prepares the already-reviewed
OpenWebUI shell path to run through UAA's local `/v1` gateway. It does not make
OpenWebUI the agent brain.

## CLI And API Surface

The only new CLI surface is:

```bash
uaa setup install --target openwebui
uaa setup install --target openwebui --receipt "$HOME/.local/state/uaa/openwebui-install-receipt.json"
```

The legacy `--yes`, `--approval-token`, and `--write-approval-token` options
remain parseable only to produce a truthful redacted denial. They cannot
authorize the image pull, no token is read or written, and the operator must
rerun without them and type the exact interactive confirmation.

No API route, Control Center control, backend route, provider route, OpenWebUI
admin call, plugin path, browser automation path, or model runtime route is
added by this milestone.

## Authority Boundary

Allowed:

- verify Docker CLI and Docker engine readiness
- print the exact `docker pull` command before execution
- require explicit typed operator approval after the exact preview
- run the exact OpenWebUI image pull command
- write a redacted local receipt under `.uaa/dev/setup-install-receipts/` by
  default, or to an explicit safe user-scope `--receipt` path

Denied:

- install Python, Node/npm dependencies, Homebrew packages, llama.cpp, models,
  providers, plugins, browser tooling, credentials, or system services
- download GGUF files or provider SDKs
- execute arbitrary shell strings or caller-provided commands
- start OpenWebUI, start UAA, call `/v1/models`, call providers/models, use
  browser automation, write memory, mutate OpenWebUI admin settings, install
  OpenWebUI plugins, or grant tools/functions authority
- print environment values, provider keys, raw prompts, raw responses, raw
  provider payloads, raw logs, usernames, cookies, or credentials

## Risk Ceiling

Risk is limited to local Docker image acquisition from the configured
OpenWebUI digest ref and local receipt persistence. Mutable image tags such as
`main` are denied for this runtime install surface. The risk ceiling does not
cover remote installer bootstrapping, arbitrary GitHub script execution, broad
dependency installation, signed installers, launch daemons, model downloads,
or public distribution.

## Approval Model

Before any pull, the command prints the authority boundary, exact command,
rollback notes, and receipt location. Interactive runs require the operator to
type:

```text
install openwebui
```

Unattended setup approval is disabled. The deprecated `--yes`,
`--approval-token`, and `--write-approval-token` inputs always fail before
Docker is resolved, record `INTERACTIVE_OPERATOR_CONFIRMATION_REQUIRED`,
and cannot mint or validate a LocalApprovalAuthority grant. Structurally
valid, hash-matching, stale, replayed, forged, malformed, symlinked, and
arbitrary token paths are all non-authorizing because the token is never an
approval source. These pre-authority denials record approval authority `none`
and decision source `pre-authority-input-guard`; they do not attribute the
rejection to PolicyEngine or LocalApprovalAuthority.

Approved image-pull decisions are routed through the local PolicyEngine plus
LocalApprovalAuthority adapter, which records a chmod `0600` redacted approval
receipt with exact scope, actor, target, image ref, preview hash, revocation
notes, and replay notes. The receipt grants no reusable runtime authority.

## Persistence Model

The Docker image is stored in the local Docker image cache. Setup install
receipts are stored under `.uaa/dev/setup-install-receipts/` by default, which
is ignored local developer state. `--receipt` may instead select one exact
nonexistent path beneath the current user's home. Symlinked, outside-home, and
world-writable paths are denied; missing parents are created mode `0700`.
Control characters and paths that would occupy required setup evidence
directories are denied before preview. Missing custom-receipt parents are
prepared privately, and the exact custom destination is reserved before
interactive approval or Docker resolution. The command does not create
OpenWebUI data state; that state is created only by the launcher when OpenWebUI
is started.

## Redacted Receipt Model

Each receipt records safe summary fields only:

- schema
- target
- milestone ref
- action
- image ref
- preview hash
- approval mode
- approval authority, decision source, and decision ref
- safe receipt summary and hashed receipt scope ref
- exact command label
- status
- result summary
- allowed and denied side effects
- rollback steps
- timestamp

Receipts must not include command output, environment dumps, credentials,
provider keys, raw prompts, raw responses, raw provider payloads, raw logs,
cookies, or usernames.

## Test Plan

Focused tests must cover:

- approval refusal does not run Docker pull
- bare `--yes` and every deprecated token input fail before Docker is resolved
- structurally valid, forged, stale, mismatched, replayed, arbitrary-path, and
  token-writer inputs remain non-authorizing and are not read or written
- exact interactive confirmation runs only the expected OpenWebUI image pull
  argv
- Docker-not-ready path does not pull
- install and approval receipts are chmod `0600`, exact-scope, and redacted
- a custom receipt is preview-bound, safely reserved before Docker,
  no-follow/exclusive-created, and never printed as a raw home path
- control characters, internal evidence directory occupancy, and unsafe or
  reused custom receipt paths fail closed; missing parents remain private under
  a permissive umask on all receipt writes
- rollback text is present and names the selected safe receipt scope
- plain `uaa setup` remains diagnostic and does not run install paths
- launcher still refuses missing images and points to the setup install command

## Verifier And Foundation Gate

No OpenAPI or Foundation Gate route update is required because this milestone
adds no backend route, public API boundary, Control Center control, or runtime
authority. The guard is the local deterministic unit test coverage plus this
milestone document.

The scoped follow-on GitHub bootstrap milestone is defined in
`docs/production/M167_GITHUB_BOOTSTRAP_LOCAL_INSTALLER.md`.

## Rollback Plan

Stop OpenWebUI if it is running:

```bash
./scripts/dev/uaa openwebui stop
```

Remove the local Docker image:

```bash
docker image rm ghcr.io/open-webui/open-webui@sha256:7f1b0a1a50cfbac23da3b16f96bc968fd757b26dc9e54e93813d61768ea9184e
```

Review local OpenWebUI state only when intentionally resetting it. Setup
install does not remove `.uaa/dev/openwebui-data`; any state cleanup must be a
separate canonical-path review and must not be presented as part of the image
pull rollback.

Remove local setup install receipts only when no longer needed for support:

```bash
rm -rf .uaa/dev/setup-install-receipts
```
