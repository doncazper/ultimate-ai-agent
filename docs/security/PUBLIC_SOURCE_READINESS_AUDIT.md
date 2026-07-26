# Public Source Readiness Audit

Status: repository public under MIT; exact hosted CI migration and local-runner
retirement remain in progress.

Audit baseline:
`76891d8f9e8c0de238e3c3e262aca79d2ee9bcf9` (`origin/main` at lane start).

This audit authorizes no runtime capability and makes no public beta,
production-readiness, binary-distribution, support, or security-certification
claim.

## License and community files

- Root license: MIT.
- Copyright notice: Sam Behdjou and Ultimate AI Agent contributors.
- Contribution boundary: `CONTRIBUTING.md`.
- Vulnerability reporting boundary: `SECURITY.md`.
- Historical tags remain immutable audit records.

## Secret and artifact audit

The exact `origin/main` history was scanned with checksum-verified Gitleaks
8.30.1 using full-history Git mode and 100% redaction.

The detector reported 80 candidate matches across 63 files and 52 commits:

- 79 generic API-key heuristic matches; and
- one curl authorization-header match.

Every candidate was classified as one of these non-credential test or evidence
classes:

- deliberately fake secret-like values used by redaction tests;
- fixed loopback-only development examples;
- safe-ref/idempotency/cache identifiers; or
- deterministic SHA-256 source-integrity fields.

No authentic credential, token, private key, certificate, signing material, or
account secret was identified. The tracked tree contains no private-key,
certificate, database, log, package archive, or signing-profile artifact. The
repository Actions secret inventory was empty at audit time.

The largest historical blob was approximately 6.2 MB and no blob met or
exceeded GitHub's 100 MB hard limit. Historical visual baselines make the Git
pack comparatively large; that is a clone-performance concern, not a
visibility blocker. Any later Git LFS or history-size work must preserve
immutable historical tags and requires its own scoped review.

## CI and fork boundary

- All canonical CI contexts retain their exact names and evidence DAG.
- CI and supply-chain jobs use standard `macos-15` hosted runners.
- The metadata-only fork policy uses standard `ubuntu-24.04`.
- No active workflow selects a self-hosted or larger runner.
- Pull request workflows use read-only tokens, do not persist checkout
  credentials, and receive no repository secrets.
- Every external contributor requires approval before a fork workflow runs.
- Pushed tags verify macOS packaging in a read-only, secret-free job and do not
  automatically publish a binary release.

## Applied public repository settings

- GitHub reports `visibility: public` and recognizes the root MIT license.
- Vulnerability alerts, automated security updates, private vulnerability
  reporting, secret scanning, and secret-scanning push protection are enabled.
- Actions keeps a read-only default token and a selected-action allowlist.
- Fork workflow approval is set to every external contributor.
- An unauthenticated clone and unauthenticated repository API lookup succeeded
  against exact public `main` after PR #350.

## Remaining retirement gate

1. land the hosted-runner migration through exact-head public CI and review;
2. confirm its exact merge on `main` using standard hosted runners; and
3. only then stop and unregister the four local runner services.

Branch/ruleset protection is a separate repository-policy decision. It is not
changed during this migration while an existing parent queue pull request is
active.

Any secret alert, unexpected workflow permission, unapproved runner class,
missing required context, or hosted exact-head disagreement blocks runner
retirement until repaired.
