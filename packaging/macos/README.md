# First-Class macOS Distribution

Status: implemented and locally verified for private arm64 use

This directory contains the long-lived installer entry point for a
self-contained Ultimate AI Agent macOS app. The installed app does not depend
on a repository checkout, `.venv`, Node, npm, Vite, or developer launcher.
The app and `uaa` shell command execute the same packaged Python CLI.

The working app-icon placeholder lives in `packaging/macos/assets/` as a
transparent 1024px master plus the generated `UltimateAI-Agent.icns`. The
release builder copies the ICNS into the signed bundle and binds it through
`CFBundleIconFile`.

Public distribution is not claimed. Current builds are ad-hoc signed until a
Developer ID Application identity and notarization profile are configured.

## Operator Install

For a locally built release:

```bash
packaging/macos/install.sh \
  --local-archive BUILD_DIR/uaa-macos-arm64.tar.gz \
  --local-descriptor BUILD_DIR/uaa-macos-arm64.release.json
```

For a published private GitHub Release:

```bash
gh auth login
packaging/macos/install.sh --channel newest --launch
```

Remote install requires two published release surfaces:

1. the long-lived `uaa-installer-v1` bootstrap assets; and
2. at least one app GitHub Release with a valid
   `uaa-macos-arm64.release.json` descriptor and matching artifact.

The repository currently has no GitHub Releases. The remote command becomes
active after this implementation is accepted, a new eligible tag is created,
and `.github/workflows/macos-release.yml` publishes both surfaces. Arbitrary
tags are never downloaded directly.

## Installed Layout

```text
/Applications/Ultimate AI Agent.app
~/Library/Application Support/Ultimate AI Agent/
  current -> versions/<release-id>
  previous -> versions/<release-id>
  versions/
  state/
  receipts/
~/.local/bin/uaa
```

The Applications bundle is a real signed app directory. Versioned copies under
Application Support provide atomic promotion and rollback. The CLI wrapper has
no checkout-specific path and resolves the managed `current` version.

## CLI

```bash
uaa launch
uaa status
uaa doctor
uaa update --check
uaa update
uaa update --channel stable
uaa update --channel dev
uaa rollback
uaa stop
uaa uninstall
```

Opening the app is equivalent to `uaa launch`. It checks the selected channel
before boot. If GitHub is unavailable or private-repository authentication is
missing, it keeps the verified installed version and does not replace it.

## Release Selection

`newest` compares the newest valid stable descriptor with the newest valid dev
descriptor by the immutable tag commit timestamp. GitHub publication time is a
tie-breaker only, so backfilling an older release cannot make it appear newer.

`packaging/macos/release-policy.json` owns the active tag grammar. Historical
`v1.*` and `v2.*` audit tags are explicitly retired from the current product
line. A release without the active product-line descriptor, matching
architecture, exact size, and SHA-256 is ignored.

## Private GitHub Authentication

The updater first checks `UAA_UPDATER_GITHUB_TOKEN`, then the authenticated
GitHub CLI. Tokens are held in memory only and are excluded from commands,
receipts, status, and logs. The environment variable is intended for
non-interactive build/repair use; `gh auth login` is the normal private
operator path.

## Build

```bash
npm ci --prefix apps/control-center
npm run build --prefix apps/control-center

PYTHON_RUNTIME="$(
  scripts/macos/prepare_python_runtime.sh arm64 \
    .uaa/macos-build/python-runtime
)"

PYTHONPATH=src .venv/bin/python scripts/macos/build_release_bundle.py \
  --python-runtime "$PYTHON_RUNTIME" \
  --output-dir .uaa/macos-build/release \
  --tag TAG \
  --channel stable-or-dev \
  --source-commit EXACT_COMMIT_SHA \
  --source-timestamp TAG_COMMIT_TIMESTAMP \
  --architecture arm64
```

The build uses a pinned, SHA-256-verified relocatable CPython runtime, the
frozen Python dependency lock, a hash-pinned setuptools backend in a disposable
build-only environment, a wheel of the tagged source, and the production
Control Center. Build tooling is not copied into the shipped runtime. The
builder removes non-runtime metadata and bytecode, scans text metadata for local
build paths, signs nested Mach-O files, inventories every installed file, and
emits:

- `uaa-macos-arm64.tar.gz`
- `uaa-macos-arm64.tar.gz.sha256`
- `uaa-macos-arm64.release.json`
- `build-receipt.json`

## Signing And Notarization

Ad-hoc signing is the local/private default. For Developer ID:

```bash
PYTHONPATH=src .venv/bin/python scripts/macos/build_release_bundle.py \
  ... \
  --signing-identity "Developer ID Application: ORGANIZATION (TEAMID)" \
  --notary-profile UAA_NOTARY_PROFILE
```

The builder signs nested Mach-O code before the app, enables hardened runtime
for Developer ID, submits with `notarytool`, staples the ticket, runs strict
`codesign` verification, and evaluates notarized builds with `spctl`.
No entitlements are added by default.

## Release Automation

`.github/workflows/macos-release.yml` runs on a standard GitHub-hosted
`macos-15` runner. Tag pushes use a read-only, secret-free verification job.
An explicit manual dispatch must request publication before a separate
write-scoped job can rebuild, verify, and publish the GitHub Release.

The reusable fail-closed lifecycle verifier is:

```bash
PYTHONPATH=src .venv/bin/python scripts/macos/verify_installer_e2e.py \
  --archive BUILD_DIR/uaa-macos-arm64.tar.gz \
  --descriptor BUILD_DIR/uaa-macos-arm64.release.json
```

For a local two-version recovery proof, also pass `--previous-archive` and
`--previous-descriptor`. The verifier uses an isolated home and install root,
checks the native Applications executable, icon/plist, signature, CLI parity,
idempotent reinstall, production HTML, protected API manifest, security
headers, stop/cleanup, default uninstall plus repair reinstall, bytecode
immutability, redacted receipts, and optional two-way rollback. It emits safe
summary refs only.

The bootstrap is published separately and rarely:

```bash
gh workflow run macos-release.yml \
  -f release_tag=NEW_ELIGIBLE_TAG \
  -f channel=auto \
  -f publish_release=true \
  -f publish_installer_bootstrap=true
```

Do not move or reuse a historical tag. The first publishable tag must contain
this installer implementation; pre-installer tags cannot truthfully produce a
self-contained app from their source alone.
