# Codex Plugin Risk Policy

Status: Active tooling governance policy, v0.14.6

This policy classifies Codex plugins and external build tools before future milestone use. It is guidance-only and does not enable plugins or grant runtime capability.

## Risk Categories

Low:

- process guidance,
- read-only local documentation inspection,
- local methodology helpers that do not execute external actions.

Medium:

- artifact generation,
- local document rendering,
- unauthenticated browser inspection,
- generated image or report creation.

High:

- authenticated browser profile control,
- GitHub write or release actions,
- external code review that shares source/diffs,
- cloud service connectors,
- dependency or package installation,
- database/payment-provider workflows,
- plugin or skill installation.

Critical:

- native iOS/macOS build systems,
- signing identities,
- provisioning profiles,
- keychains,
- App Store Connect,
- simulator/device workflows,
- local desktop UI automation,
- cloud training/jobs/uploads,
- deployment/publishing workflows.

## Default Policy

All plugins are disabled unless a milestone, review prompt, or direct user instruction explicitly allows them.

Build, deploy, signing, simulator, device, and native app tooling is high or critical risk until proven otherwise. Browser authenticated profile control is high risk. Computer Use is critical risk. Plugin and skill installers are high supply-chain risk. GitHub write/release actions require explicit approval or direct-push rules. Read-only review tools can be approved per review prompt.

Shell commands are allowed narrowly for local verifier, test, grep, git, and script workflows. Shell commands must not be used to access secrets, keychains, signing profiles, App Store Connect, browser profiles, plugin credentials, or cloud tokens unless a future prompt explicitly authorizes that scope.

## Explicit Allow-Later Rules

- Browser + Build Web Apps may be used for future Web Control Center work after approval.
- Build iOS Apps / XcodeBuildMCP may be used only for a future Mobile Companion implementation milestone after signing, simulator, device, and sensor boundaries are defined.
- Build macOS Apps may be used only for a future Desktop/macOS Companion milestone after signing, entitlement, keychain, and notarization boundaries are defined.
- CodeRabbit and GitHub read-only review may be used for release readiness reviews with explicit review prompts.
- Documents, Presentations, and Spreadsheets may be used for artifacts when explicitly requested.
- Superpowers/process tools may be used as methodology, not runtime capability.

## Explicit Do-Not-Enable-Yet List

- Build iOS Apps / XcodeBuildMCP.
- Build macOS Apps.
- Computer Use.
- Chrome authenticated profile control.
- Hugging Face Jobs, uploads, training, or Spaces deployment.
- Plugin/skill installers.
- Stripe/Supabase credential workflows.
- Any signing, keychain, provisioning profile, App Store Connect, browser-cookie, SSH-key, `.env`, token, or credential-store flow.

## Approval Template

Before enabling any high-risk or critical plugin, record:

```text
purpose
milestone
scope
files affected
permissions
network access
credential/keychain/signing access
artifact outputs
test plan
rollback plan
approver
expiration or revocation condition
```

No approval exists merely because a plugin appears available in Codex.
