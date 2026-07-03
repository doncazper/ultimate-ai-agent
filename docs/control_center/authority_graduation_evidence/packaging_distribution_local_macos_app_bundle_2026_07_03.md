# Packaging / Distribution Local macOS App Bundle Evidence

Status: verified local unsigned app bundle proof, not distribution authority
Lane: Packaging / Distribution
Promotion level: Level 1 local packaging proof
Date: 2026-07-03

## Evidence

`scripts/build_local_macos_app_bundle_proof.py` creates a repo-local ignored
`Ultimate AI Agent Local.app` proof bundle under UAA local state. The bundle
contains an `Info.plist`, a launcher entrypoint that targets the existing
`./scripts/dev/uaa trial-boot` local launcher, and a boundary note.

The proof summary uses safe refs and hashes only. It does not print or persist
raw local paths in the summary, raw logs, credentials, cookies, provider
payloads, prompts, responses, or environment dumps.

Verified posture:

- app bundle created: `true`
- launcher entrypoint created: `true`
- launch executed by verifier: `false`
- signed: `false`
- notarized: `false`
- public installer created: `false`
- auto-update enabled: `false`
- daemon or LaunchAgent created: `false`
- provider/model authority added: `false`
- connector write authority added: `false`
- browser automation added: `false`
- runtime shell authority added: `false`
- distribution claims allowed: `false`

## Boundary

This evidence verifies only a repeatable local unsigned `.app` bundle artifact
around the existing local launcher. It does not launch the app in CI, does not
start services, does not sign or notarize the bundle, does not create a DMG,
does not install a LaunchAgent or daemon, does not add auto-update behavior, and
does not claim public beta, public release, production readiness, or production
distribution authority.

Removing the ignored local bundle disables this packaging artifact.
