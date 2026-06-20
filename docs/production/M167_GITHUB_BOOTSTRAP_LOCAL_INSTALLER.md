# M167 GitHub Bootstrap Local Installer

Status: scoped implementation slice; downloader available only through
`uaa setup bootstrap` with a pinned release tag, exact asset name, explicit
SHA-256, signature/provenance manifest, typed approval or preview-bound
approval token, and fail-closed provenance mode.

This scoped M167+ milestone defines the authority boundary for a
GitHub-hosted bootstrap installer that can prepare a local developer
OpenWebUI shell with one reviewed bootstrap flow. The implementation slice is
narrow: it may download only a pinned UAA GitHub Release artifact from the
approved repository, verify it, unpack it into a temporary installer
directory, and run only the verified local OpenWebUI installer argv.

## Exact Capability

This implementation may let an operator download a pinned, verified bootstrap
artifact from the UAA GitHub release page, run the verified installer locally,
install only approved user-scope UAA local-dev assets, add a `uaa` launcher
command to the user's PATH, and then run:

```bash
uaa launch-ui
```

The designated UI remains OpenWebUI. OpenWebUI remains a shell pointed at
UAA's local `/v1` gateway; it does not become the agent brain.

## GitHub Source And Ref Policy

The only allowed source repository is:

```text
https://github.com/doncazper/ultimate-ai-agent
```

Allowed source form:

- a GitHub Release artifact attached to an explicitly named release tag
- an exact release asset name for the operator platform
- a signed checksum manifest for that exact asset
- a repository-pinned public signing key or equivalent provenance root

Denied source form:

- mutable branch names; `main` is denied
- pull request refs, branch refs, `refs/heads/*`, or moving aliases
- `raw.githubusercontent.com` script execution
- arbitrary GitHub repositories, forks, gists, snippets, or caller-provided
  script URLs
- `latest` is denied; an explicit release tag is required before download,
  verification, approval, execution, and receipt writing

## Required Verification

The bootstrap flow must verify before execution:

- release tag matches the approved milestone/version policy
- release asset name matches the supported platform matrix
- SHA-256 digest matches the signed checksum manifest
- signature/provenance verification passes against the repo-pinned trust root
- unpacked installer path is inside a temporary installer directory
- installer manifest declares only approved assets and side effects

The first implementation adds the repo-owned trust-root document
`docs/production/UAA_BOOTSTRAP_TRUST_ROOT.md`, which names the allowed
provenance schema, issuer/source identity, verification rules, and fail-closed
behavior for trust-root drift.

Checksum mismatch, signature mismatch, missing manifest, unsupported platform,
unexpected file path, unexpected executable, or provenance failure must abort
before any installer code runs.

## Exact Installer Command Surface

The public setup command is:

```bash
uaa setup bootstrap --release-tag v0.102.0-m167 --asset uaa-bootstrap-darwin-arm64.tar.gz --sha256 "<64-hex-digest>" --signature uaa-bootstrap-darwin-arm64.tar.gz.provenance.json --target openwebui --provenance-mode local-dev-json
```

After approval and verification, the verified local installer command is:

```bash
./uaa-bootstrap install --target openwebui --bin-dir "$HOME/.local/bin"
```

Allowed options:

- `--target openwebui`
- `--bin-dir PATH`, defaulting to `$HOME/.local/bin`, only after
  canonicalized user-scope path validation
- `--install-dir PATH`, defaulting to a user-scope UAA install directory, only
  after canonicalized user-scope path validation
- `--receipt PATH`, defaulting to ignored local UAA state, only after
  canonicalized user-scope path validation
- `--approval-token PATH`, required for noninteractive `--yes`
- `--write-approval-token PATH`, which writes a preview-bound approval token
  after typed approval and exits without downloading
- `--provenance-mode minisign|local-dev-json`; `minisign` is public
  bootstrap mode and fails closed until the repo-pinned key/verifier is
  configured, while `local-dev-json` is explicit local-dev/test-only
- `--yes`, only with a matching preview-bound approval token
- `--no-profile-edit`, to skip shell profile PATH changes

All path options must reject symlink escapes, path traversal, world-writable
directories, system directories, and unrelated existing files.

The setup doctor remains separate and diagnostic-only. Existing
`uaa setup install --target openwebui` remains the explicit pre-bootstrap
OpenWebUI image downloader and is not triggered by plain `uaa setup`.

## Installable Assets

Allowed first-slice assets:

- the verified UAA bootstrap artifact from the approved GitHub Release
- versioned UAA local launcher files under a user-scope install directory
- a `uaa` launcher shim or symlink under the approved user `--bin-dir`
- release-bundled, hash-checked Python wheels/assets needed by the local UAA
  backend
- local state directories under ignored UAA state
- the configured OpenWebUI Docker image through the existing scoped
  OpenWebUI image install boundary

Denied assets:

- Docker Desktop installer
- Homebrew packages or taps
- system Python, system Node, npm global packages, or privileged system files
- live PyPI/npm/Homebrew dependency resolution, source builds, postinstall
  hooks, or downloader fallbacks
- llama.cpp binaries or GGUF/model files
- provider SDK credential setup
- browser drivers, plugins, mobile tooling, remote workers, or daemons
- OpenWebUI plugins, OpenWebUI admin settings, or OpenWebUI internal database
  mutations
- UAA tool/function authority, memory writes, context injection, autonomous
  background sessions, or model/provider output as authority

If a supported host lacks Docker, Python, or another base prerequisite, the
bootstrapper must abort with manual guidance unless a later milestone
separately approves that dependency installation.

The OpenWebUI image ref inherited from
`docs/production/M167_OPENWEBUI_LOCAL_INSTALLER.md` is digest-pinned:

```text
ghcr.io/open-webui/open-webui@sha256:7f1b0a1a50cfbac23da3b16f96bc968fd757b26dc9e54e93813d61768ea9184e
```

Digest updates must be a reviewed source change that records the old digest,
new digest, registry inspection date, test evidence, rollback command, and
release-note rationale. Mutable tags such as `main` are not accepted for the
runtime install or launch surfaces.

## PATH Mutation Scope

Allowed:

- create or update a user-scope launcher shim at `$HOME/.local/bin/uaa`
- refuse to overwrite an unrelated existing `uaa` file
- add an idempotent, clearly marked PATH block to the user's shell profile
  only after explicit approval
- write a timestamped backup before editing a shell profile
- remove or replace only receipt-bound or marker-matched installer-owned PATH
  blocks and shim files

Denied:

- `sudo`
- `/usr/local/bin`, `/opt/homebrew/bin`, `/usr/bin`, or system-wide PATH
  mutation
- launch agents, daemons, login items, background services, or auto-start
  behavior
- shell profile edits without backup and explicit consent

Rollback must remove the shim, restore the backed-up profile block, and leave
unrelated user shell content untouched.

## Approval And Consent Copy

Before any installer side effect, the bootstrapper must print:

- exact release tag, asset name, checksum ref, and signature/provenance status
- exact install directory and bin directory
- exact PATH mutation plan
- exact local commands it may run
- allowed and denied side effects
- rollback steps

The operator must approve with:

```text
install uaa openwebui bootstrap
```

`--yes` may be accepted only with a chmod `0600`, single-use, unexpired
approval token whose preview hash matches the current preview. The preview hash
is computed over safe canonical fields: milestone ref, approved repo, release
tag, asset, SHA-256, signature/provenance reference, provenance mode, target,
safe path summaries, and the pinned OpenWebUI image ref. Tokens expire after
15 minutes, are marked used before any download, and must fail closed when
missing, expired, replayed, or mismatched.

## Cryptographic Verification Policy

Public bootstrap mode is `--provenance-mode minisign`. It requires a
repo-pinned minisign or equivalent Sigstore trust root, detached signature,
artifact digest binding, and deterministic verifier before installer code may
run. Until that key and verifier are configured, public mode fails closed
before extraction or execution.

`--provenance-mode local-dev-json` accepts the existing JSON provenance
manifest only for local-dev/test bootstrap exercises. It is not public
distribution provenance and must not be treated as cryptographic signing.

## Redacted Receipt Model

The bootstrapper must write a chmod `0600` receipt with safe summaries
only:

- schema
- milestone ref
- release tag
- asset name
- checksum status
- signature/provenance status
- target
- install directory summary
- bin directory summary
- PATH mutation status
- installed asset names
- OpenWebUI image install status
- result status
- timestamp
- rollback hints

Receipts must not include provider keys, credentials, cookies, environment
dumps, raw prompts, raw responses, raw provider payloads, raw logs, usernames,
home-directory expansions beyond safe summaries, or shell history.

## Persistence Model

Allowed persistence:

- versioned user-scope UAA install directory
- user-scope launcher shim
- optional shell profile backup and idempotent PATH block
- ignored local UAA state and receipts
- local Docker image cache for the configured OpenWebUI image

Denied persistence:

- system services
- LaunchAgents or daemons
- credential stores
- provider secrets
- raw OpenWebUI database edits
- model caches or GGUF files
- background jobs

## Platform Support Matrix

First supported platform:

| Platform | Status | Base prerequisites |
|---|---|---|
| macOS arm64 | supported first | Docker Desktop manually installed and running, Python 3.10+, POSIX shell, writable `$HOME/.local/bin` |
| macOS x86_64 | planned after arm64 proof | Same as macOS arm64 |
| Linux | future milestone | Not approved in this slice |
| Windows | future milestone | Not approved in this slice |

The first implementation must abort on unsupported platforms before download
or execution.

## Failure Modes And Safe Abort

The bootstrapper must fail closed for:

- unsupported platform
- missing Docker engine
- missing Python baseline
- missing checksum or signature
- checksum/signature/provenance mismatch
- missing, expired, replayed, or mismatched approval token for `--yes`
- cryptographic verifier missing or unavailable in public provenance mode
- mutable branch, `main`, or `latest` source
- arbitrary URL input
- PATH conflict
- profile backup failure
- install directory conflict
- port conflict during final launch readiness check
- OpenWebUI image pull failure

Safe abort means no unverified installer code runs, no PATH mutation happens
after a verification failure, receipts remain redacted, and rollback guidance
is printed.

## Test Plan

Tests or verifier checks must reject:

- `curl | bash`
- pipe-to-shell execution
- execution from mutable `main`
- execution from `latest`
- `raw.githubusercontent.com` script execution
- arbitrary GitHub repo or script URL execution
- unverified script execution
- missing checksum/signature/provenance verification
- secret or environment dumping
- broad system install claims
- `sudo`, launch agents, daemons, or system-wide PATH mutation
- OpenWebUI plugin/admin mutation
- model/provider authority
- UAA tool/function authority, memory writes, context injection, and
  autonomous background authority

Tests must also prove:

- the milestone doc is linked from local runtime and M167 docs
- the existing setup doctor remains non-installing
- `uaa setup install --target openwebui` remains the separate pre-bootstrap
  OpenWebUI image downloader
- `uaa setup bootstrap` rejects mutable refs, arbitrary URLs, missing
  verification material, unsafe paths, unsupported platforms, refusal, and
  verification failure before any installer code runs
- digest-pinned OpenWebUI image appears in setup install preview, receipt, and
  launch command
- `--yes` fails without a matching preview-bound approval token
- stale, mismatched, and replayed approval tokens fail before download
- JSON provenance is accepted only under explicit `local-dev-json` mode
- public `minisign` mode rejects JSON-only provenance before extraction

## Verifier And Foundation Gate Impact

This CLI-only milestone adds no backend route, OpenAPI path, Control Center
control, model call, provider call, browser automation, plugin runtime, mobile
authority, remote execution, or production authority. No Foundation Gate or
OpenAPI update is required for this slice.

The implementation slice adds static tests and focused CLI coverage before
the downloader code. The CLI is covered by parser tests, refusal tests,
verification failure tests, approval tests, receipt tests, rollback tests, and
no-secret-output tests.

## Rollback Plan

Rollback for the bootstrapper must first verify receipt ownership and
installer markers, then remove only installer-owned files such as:

```bash
rm -f "$HOME/.local/bin/uaa"
```

It must restore only shell profile backups created by the installer and remove
only the installer-owned PATH block.

It may remove the user-scope UAA install directory only after printing the
exact canonical path, proving receipt ownership, and receiving explicit
approval.

OpenWebUI image rollback remains digest-bound:

```bash
docker image rm ghcr.io/open-webui/open-webui@sha256:7f1b0a1a50cfbac23da3b16f96bc968fd757b26dc9e54e93813d61768ea9184e
```

OpenWebUI local state rollback remains explicit and separate. The future
bootstrapper must print the exact canonical path, prove receipt ownership or
operator-selected reset intent, and receive explicit approval before removal:

```bash
rm -rf .uaa/dev/openwebui-data
```

## Current Implementation Slice

This milestone implements only the bounded GitHub bootstrap command:

```bash
uaa setup bootstrap --release-tag v0.102.0-m167 --asset uaa-bootstrap-darwin-arm64.tar.gz --sha256 "<64-hex-digest>" --signature uaa-bootstrap-darwin-arm64.tar.gz.provenance.json --target openwebui --provenance-mode local-dev-json
```

Plain setup remains diagnostic-only. The existing local repo launcher and
scoped image installer remain available:

```bash
uaa setup install --target openwebui
uaa launch-ui
```
