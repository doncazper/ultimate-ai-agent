# Security Policy

Status: active public security posture for v0.103.0
Program task: UAA-P0-003

Ultimate AI Agent is a local-first alpha foundation, not a production service
or public distribution. This policy explains how to report vulnerabilities and
what security invariants maintainers use while triaging reports.

## Supported Versions

| Line | Support status | Notes |
|---|---|---|
| `main` / v0.103.0 / package `0.103.0` | Supported for security review and fixes | Current active baseline plus accepted checkpoint-m169 and local model checkpoint-m166/checkpoint-m167 context. |
| Historical release and checkpoint tags | Audit history only | Historical tags are not moved. Fixes land on current `main` unless a scoped maintenance decision says otherwise. |

No public beta, signed release, external audit completion, production
deployment, managed service, or public distribution is claimed by this policy.

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
- Durable evidence, reports, release docs, tests, and logs must not contain raw
  prompt content, raw response content, raw provider payload content, raw local
  path content, raw log content, usernames, hostnames, serials, environment
  dumps, credentials, or secret-like values.
- User-facing claims must match implementation evidence.

Maintainer triage steps live in
`docs/security/SECURITY_TRIAGE_RUNBOOK.md`.
