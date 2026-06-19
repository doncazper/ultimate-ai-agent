# SemVer Policy

Status: active versioning policy
Source of truth: `VERSION`

Ultimate AI Agent uses pre-1.0 SemVer until the project is explicitly promoted
to a final stable release. The mistaken `v2.0.0` line is superseded by this
policy and must not be used as the current project version.

## Version Rules

- `v0.0.x` is for documentation-only stage releases before implementation code
  exists.
- `v0.1.0` is the first code-bearing implementation release.
- `v0.x.patch` is for incremental repair, polish, hardening, tests, docs tied
  to existing features, and other non-feature changes.
- `v0.next.0` is for new features, capabilities, product surfaces, runtime
  subsystems, integrations, or meaningful project milestones.
- `v1.0.0-rc.N` is the release-candidate sequence.
- `v1.0.0` is reserved for final stable release only after explicit approval.
- `v2.x.x` is forbidden until the project has a real `v1.x` stable history and
  an explicitly justified major-version break.

## Formatting

- `VERSION` contains the bare SemVer value, for example `0.100.0`.
- Git tags use a `v` prefix, for example `v0.100.0`.
- Package metadata uses bare SemVer, for example `0.100.0`.
- Human docs may mention both forms, for example `v0.100.0 / 0.100.0`.

## Protected Labels

Do not rewrite or reinterpret checkpoint IDs, milestone IDs, task IDs, route
counts, dependency versions, API schema versions, or historical audit refs as
project release versions.

Release candidates must be tagged as `v1.0.0-rc.N`; never tag a release
candidate as `v1.0.0`.

## Historical Alpha Labels

Earlier docs and tags may mention `v1.2.0-alpha` as an M150 alpha-target
contract label. Under this repaired policy, that label is historical audit
context only. It is not the active package baseline, not a current release
target, and not evidence of final stable approval. Future release candidates
must use `v1.0.0-rc.N`.
