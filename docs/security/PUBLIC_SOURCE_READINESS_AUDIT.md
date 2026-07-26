# Public Source Readiness Audit

Status: pre-visibility audit complete; hosted CI and repository settings proof
remain required.

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
- External contributors require approval before their first workflow runs.
- Pushed tags verify macOS packaging but do not automatically publish a binary
  release.

## Remaining visibility gate

Before changing repository visibility:

1. land the MIT/hosted-runner migration through exact-head review and CI;
2. confirm the merge on exact `main`;
3. change visibility to public;
4. require approval for workflows from every external contributor;
5. enable private vulnerability reporting and public-repository secret
   scanning where available;
6. apply branch/ruleset protection to `main` with the existing required check
   contexts;
7. verify one ordinary public pull request and one `main` push on standard
   hosted runners; and
8. only then stop and unregister the four local runner services.

Any secret alert, unexpected workflow permission, unapproved runner class,
missing required context, or hosted exact-head disagreement blocks visibility
or runner retirement until repaired.
