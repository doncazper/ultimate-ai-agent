# macOS First-Class Installer And Updater

Status: implemented and locally verified; publication requires an accepted
immutable tag and its GitHub Release evidence
Baseline: v0.104.0 / 0.104.0

## Current Truth

The macOS distribution lane now builds a self-contained arm64 app with:

- a native Mach-O application bootstrap;
- a pinned relocatable CPython runtime and frozen Python dependencies;
- the Python Agent Core and FastAPI boundary;
- the production-built Control Center;
- one shared app/CLI command surface;
- exact GitHub stable/dev release selection;
- size, SHA-256, per-file inventory, and code-signature verification;
- compensated version/entry-point promotion, retained prior version, and
  rollback;
- a real `/Applications/Ultimate AI Agent.app` bundle;
- a checkout-independent `~/.local/bin/uaa` command;
- app-open update checking with safe fallback to the installed version; and
- a generated local API bearer handed to Control Center through the existing
  in-memory URL-fragment flow.

The local arm64 artifact has completed build, install, doctor, Finder launch,
protected `/api/manifest`, production HTML, status, stop, signature-preservation,
no-bytecode-write, idempotency, and rollback smoke checks.

`scripts/macos/verify_installer_e2e.py` is the reusable release lifecycle gate.
It creates an isolated home/install root and verifies the native Applications
executable, icon/plist, signature, CLI parity, idempotent reinstall, production
HTML, protected API manifest, security headers, stop/cleanup, no-bytecode
mutation, default uninstall plus repair reinstall, receipt redaction, and
optional two-version rollback. The hosted macOS workflow runs this verifier
with a read-only token and no secrets. It does not publish assets.

This is a product distribution transport, not agent-facing web authority.
Network access is exact-scoped to GitHub Release metadata and release-asset
hosts for `doncazper/ultimate-ai-agent`. It does not expose general fetching to
the Python Agent Core, providers, tools, prompts, or Control Center.
Legacy scanners exempt only the three reviewed distribution adapters; a
dedicated static policy rejects broadened command, network, or supervisor call
shapes.

## Release Selection Contract

An arbitrary Git tag is not installable. A candidate must be a non-draft
GitHub Release carrying a valid architecture-specific descriptor with:

- schema `uaa.macos.release.v1`;
- product line `ultimate-ai-agent.current`;
- stable or dev channel;
- exact tag and commit SHA;
- timezone-bound tag commit timestamp;
- platform and architecture;
- artifact name, exact byte size, and SHA-256;
- minimum macOS version; and
- truthful ad-hoc/Developer ID and notarization posture.

The default `newest` channel compares the newest valid stable and dev
candidates by tag commit timestamp. This satisfies the operator requirement to
take whichever line is actually newer while preventing a later backfill of an
older tag from winning. Historical `v1.*` and `v2.*` audit labels are blocked
by `packaging/macos/release-policy.json`.

## Mutation And Recovery Contract

Installation holds a single-writer file lock, rejects unsafe archive paths,
links, special files, unexpected files, duplicate manifest paths, invalid
modes, checksum drift, signature drift, unrelated Applications bundles, and
unrelated CLI entries.

The installer stages and verifies the complete release before promotion.
`current` changes only after validation. The prior version is retained as
`previous`; `uaa rollback` swaps the two exact managed versions and refreshes
the Applications app. If an Applications, CLI, or receipt step fails, the
installer compensates the managed links and entry points to their prior state.
Receipts contain safe refs and posture only—never raw paths, credentials,
release payloads, prompts, responses, or logs.

Applications-directory selection prefers an existing managed app location
before testing present write authority. A restricted process can therefore
still inspect and operate an app already installed in `/Applications`; write
authority is evaluated only when choosing a location for a new installation.

The only legacy CLI migration allowed is the exact old four-line wrapper that
executes a repository `scripts/dev/uaa` path. Any other pre-existing `uaa`
entry is refused.

## Authentication

The repository is private. Release reads use an explicit updater token or the
authenticated `gh` credential helper. The token is held in memory and is not
persisted by UAA. App API access uses a separate random local bearer stored
mode `0600`; the browser receives it through the existing fragment handoff and
removes it from browser history.

The app continues running the verified installed release if an automatic
update check cannot authenticate or reach GitHub. It never treats update
failure as permission to install an unverified archive.

## Evidence

- `src/ultimate_ai_agent/distribution/macos/`
- `packaging/macos/`
- `scripts/macos/build_release_bundle.py`
- `scripts/macos/build_installer_bootstrap.py`
- `scripts/macos/verify_installer_e2e.py`
- `scripts/macos/prepare_python_runtime.sh`
- `.github/workflows/macos-release.yml`
- `tests/test_macos_first_class_installer.py`

## Remaining Distribution Blocks

- No valid Developer ID Application identity is installed.
- No Apple notarization profile is configured.
- Hosted publication is fail-closed until an isolated publisher can consume
  commit-bound verified artifacts without executing tag code under write
  authority and can provision an ephemeral signing keychain/notary profile.
- Source implementation alone does not prove an app or `uaa-installer-v1`
  GitHub Release exists; inspect the repository release catalog and
  workflow receipts for current publication state.
- Intel contracts and pinned runtime exist, but the release workflow and local
  end-to-end proof are arm64-only.
- Public distribution, public beta, production readiness, and Mac App Store
  distribution remain unclaimed.

Any future publication must use a new eligible immutable tag containing the
installer code and pass the macOS verification workflow plus the separately
accepted publisher gate. Do not retarget an older tag or claim that a
pre-installer tag contains this app.
