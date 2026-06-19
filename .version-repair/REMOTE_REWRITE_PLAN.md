# Remote Rewrite Plan

Status: dry-run plan only
Date: 2026-06-19

No remote rewrite is approved or performed by this repair.

## Current Local Repair

- Repair branch: `version-repair/semver-reset`
- Original repair base: `df496f3`
- Corrected local snapshot tag target: `v0.100.0`
- Current version source: `VERSION` -> `0.100.0`

## Remote Safety Gate

Remote tag deletion, replacement, or force-push is forbidden unless both are
true in a later explicit request:

1. `ALLOW_REMOTE_TAG_REWRITE=YES_I_UNDERSTAND` is set.
2. The user explicitly says `APPROVE_REMOTE_VERSION_REPAIR`.

Without both conditions, the only permitted remote action after review is a
normal push of a new commit and a new non-conflicting corrected tag.

## Candidate Remote Actions If Later Approved

Dry-run only:

```bash
git push origin version-repair/semver-reset
git push origin v0.100.0
```

Candidate old SemVer tags for later review, not deletion in this repair:

- `v1.0.0`
- `v1.1.0`
- `v1.2.0`
- `v1.2.0-alpha`
- `v1.3.0`
- `v1.4.0`
- `v1.4.1`
- `v1.5.0`
- `v1.6.0`
- `v1.7.0`
- `v1.7.1`
- `v1.7.2`
- `v2.0.0`

## No-Action Decision

This repair does not delete remote tags, move existing tags, force-push, create
a public release, upload artifacts, publish packages, or claim stable release.
