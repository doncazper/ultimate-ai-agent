# SemVer Policy

Status: active local maintenance policy for the v0.102.0 version-repair baseline.

## Source Of Truth

- `VERSION` is the proposed machine-readable source of truth.
- `VERSION` should contain only the bare SemVer value, such as `0.102.0`.
- Git tags, when later approved, should use the `v` prefix, such as `v0.102.0`.
- Package metadata should use the bare version, such as `0.102.0`.
- Human documentation may mention both forms when useful.

## Version Stages

- `v0.0.x` is reserved for documentation-only pre-implementation releases.
- `v0.1.0` is the first code-bearing implementation release.
- `v0.x.y` remains pre-1.0 development.
- Patch bumps are for bug fixes, hardening, tests, documentation tied to existing behavior, cleanup, and non-feature repair.
- Minor bumps are for new capabilities, new product surfaces, new runtime subsystems, new integrations, or meaningful project milestones.
- `v1.0.0-rc.N` is the release-candidate sequence.
- `v1.0.0` is reserved for explicit stable-release promotion.
- `v2.x.x` is forbidden until the project has a real accepted `v1.x` stable history and an explicit major-version break.

## Current Repair Position

The v0.102.0 repair preserves all existing tags as immutable history, classifies
`v2.0.0` as a superseded internal mislabel, and continues from the existing
pre-1.0 repair lane.

## Non-Goals

- This policy does not authorize tag deletion, tag retargeting, force-push, history rewrite, GitHub release mutation, or remote repair.
- This policy does not claim public release, beta release, stable release, or production authority.
- This policy does not change safety or authority boundaries.
