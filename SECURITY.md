# Security Policy

Status: active public security posture for v0.104.0
Program task: UAA-P0-003

Ultimate AI Agent is a public MIT-licensed source repository and a local-first
alpha foundation, not a production service or supported binary distribution.
This policy explains how to report vulnerabilities and what security
invariants maintainers use while triaging reports.

## Supported Versions

| Line | Support status | Notes |
|---|---|---|
| `main` / v0.104.0 / package `0.104.0` | Supported for security review and fixes | Current active baseline plus accepted checkpoint-m169 and local model checkpoint-m166/checkpoint-m167 context. |
| Historical release and checkpoint tags | Audit history only | Historical tags are not moved. Fixes land on current `main` unless a scoped maintenance decision says otherwise. |

No supported public distribution is claimed by this policy. This policy does
not claim public beta, a supported signed release, external audit completion,
production deployment, a managed service, or production readiness.

## Reporting A Vulnerability

Preferred private path: use GitHub private vulnerability reporting for this
repository when it is available.

If private vulnerability reporting is unavailable, open a minimal public issue
asking maintainers to enable a private reporting channel. Do not include
sensitive details, exploit steps, secret-like values, private workspace data, or
unredacted screenshots in a public issue.

## Unsafe Disclosure Guidance

Use a private channel for any report that includes exploit details, unsafe
runtime behavior, authority bypass, raw private data, secret-like output,
workspace-specific identifiers, or reproduction details that could help another
party trigger the issue.

Public issues and release-facing comments should contain only a safe summary,
affected area, expected invariant, and requested private follow-up path. Do not
post raw prompt content, raw response content, raw provider payload content, raw
local path content, raw log content, usernames, hostnames, serials, environment
dumps, credentials, secret-like values, screenshots with private data, or
copyable exploit payloads.

Useful report shape:

- affected component or documentation area
- safe summary of impact
- severity estimate using the definitions below
- minimal safe reproduction summary
- whether any secret-like value, private data, or unsafe output was observed
- suggested safe contact path for follow-up

## Severity Definitions

| Severity | Definition |
|---|---|
| Critical | A vulnerability that could enable unapproved execution, authority bypass, secret exposure, credential handling, durable sensitive-data exposure, or public unsafe release claims. |
| High | A vulnerability that could bypass PolicyEngine, LocalApprovalAuthority, route side-effect classification, OpenAPI checks, Foundation Gate checks, redaction, or exact approval boundaries. |
| Medium | A vulnerability that weakens local-only, preview-only, safe-ref-only, idempotency, audit, rollback, or no-secret-output guarantees without direct authority bypass. |
| Low | A documentation, test, or hardening gap that could confuse operators or maintainers but does not expose authority, private data, or unsafe release claims by itself. |

## Response Targets

These are maintainer targets, not service-level guarantees:

| Step | Target |
|---|---|
| Acknowledge private report | Within 3 business days |
| Initial severity assessment | Within 7 business days |
| High or Critical mitigation plan | Before public detail disclosure |
| Documentation-only clarification | In the next security or documentation patch when verified |

Reports may remain private longer when disclosure could expose users,
workspaces, credentials, or vulnerable local-dev configurations.

## Security Invariants

Maintainers treat these as non-negotiable:

- No production authority is added unless an accepted scoped milestone grants
  exact authority with tests, verifier updates, and rollback.
- No unrestricted shell/subprocess execution, unrestricted network/browser
  automation, connector writes, plugin runtime import, mobile control, or broad
  autonomy is accepted by default.
- PolicyEngine, LocalApprovalAuthority, route side-effect classification,
  OpenAPI checks, and Foundation Gate checks remain required boundaries.
- Mutating paths must be idempotent, audited, rollback-aware, and tested.
- AuthorityDispatcher adapters must be exact, explicitly injected, lease- and
  approval-bound, budget-reserved before start, and settled with safe evidence.
  A durable `started` dispatch must never be replayed automatically after an
  interrupted or unknown outcome.
- Portable mission-evidence Ed25519 seeds may exist only inside the dedicated
  non-synchronizing, device-only macOS Keychain helper boundary. Python, API,
  CLI, receipts, logs, fixtures, and durable state may contain public keys,
  signatures, fingerprints, and safe refs only. UAA does not claim Secure
  Enclave Ed25519, signer identity, non-repudiation, or external anchoring.
- Durable evidence, reports, release docs, tests, and logs must not contain raw
  prompt content, raw response content, raw provider payload content, raw local
  path content, raw log content, usernames, hostnames, serials, environment
  dumps, credentials, or secret-like values.
- Knowledge Workbench source chunks are plaintext at the application layer and
  must remain in an owner-only local store on an operator-controlled encrypted
  volume. Plans, approvals, receipts, audit rows, and removal tombstones must
  remain content-free. Archived, rights-ineligible, and OCR-pending sources
  must not enter search or cited context.
- User-facing claims must match implementation evidence.

## Local Control Center Browser Threat Model

The local API bearer is development protection, not a distribution-grade user
identity. It is no longer compiled through a `VITE_` environment value. The
launcher places it in the URL fragment, the Control Center consumes it into
process memory before rendering, and the fragment is removed from browser
history. URL fragments are not sent in the HTTP request. Production builds use
strict backend mode so an unavailable backend fails visibly instead of showing
mock data.

The boundary also depends on exact loopback CORS origins, no wildcard CORS, a
protected-route bearer check, CSP/security headers, and explicit route
classification. These controls reduce exposure to an unrelated local webpage,
but they do not protect against a compromised browser extension, same-user
process inspection, debugging access, or a compromised local account. Native
IPC or a short-lived origin-bound session bootstrapped from an appropriate
Keychain boundary remains required before supported binary distribution.

## macOS Installer And Update Threat Model

The first-class macOS updater is an exact product-distribution transport, not
agent-facing web access. It may read only Ultimate AI Agent GitHub Release
metadata and release assets for the configured repository. A release is
installable only when its active-product-line descriptor, channel, exact tag
commit, architecture, byte size, SHA-256, per-file manifest, and code-signing
posture agree.

Legacy static scans exempt only the three reviewed distribution adapter files.
`distribution/macos/static_policy.py` separately fails closed if their fixed
command, GitHub-only network, or loopback-supervisor capability shape broadens.

Archive traversal, links, special files, unexpected files, checksum drift,
signature drift, unmanaged Applications bundles, and unrelated CLI entries
fail closed. Promotion uses a single-writer lock and staged verification; the
prior managed version remains available for rollback. A failed Applications,
CLI, or receipt promotion compensates the managed pointers and entry points
back to their prior state. Install/update receipts contain safe refs only.
Runtime inspection retains the existing managed Applications location even
when the inspecting process has less write authority than the installer; it
does not silently redirect an established install into a second user-local app.

For a private fork, an optional repository token may come from an explicit
updater environment slot or authenticated `gh`; UAA holds it in memory and
excludes it from commands, durable state, status, receipts, and logs. The
public upstream catalog does not require that token. Neither posture protects
against compromise of the same user account or GitHub credential store.

Ad-hoc signing supports local/private verification only. Public distribution
remains blocked until Developer ID hardened-runtime signing, notarization,
stapling, Gatekeeper assessment, release publishing, and independent
distribution review are completed.

The global idempotency middleware validates only header presence and shape.
`/api/manifest` now reports that as `header_shape_gate_only`; it must never be
treated as durable deduplication or exactly-once execution. An exact route may
report `route_owned_durable_replay` only when it names its durable receipt-store
owner. All routes remain blocked from production by the current API contract.

Independent property, mutation, recovery fault-injection, packaged-app, SBOM,
vulnerability-scan, blocked CodeQL, and external-review expectations are documented in
`docs/verification/PRODUCT_HARDENING_EVIDENCE_GATE.md`.

Maintainer triage steps live in
`docs/security/SECURITY_TRIAGE_RUNBOOK.md`.
