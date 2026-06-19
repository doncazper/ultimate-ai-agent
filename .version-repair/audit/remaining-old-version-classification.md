# Remaining Version Reference Classification

Status: final repair classification
Date: 2026-06-19

## Current Version

- `VERSION` contains `0.100.0`.
- Current package metadata uses `0.100.0`.
- Current human-facing baseline docs use `v0.100.0`.
- Current tag to create for the repaired local snapshot: `v0.100.0`.

## `v2.0.0` / `2.0.0`

Classification:

- Historical mistake in old tags and repair ledger only.
- Third-party dependency or engine constraint where it appears without a `v`
  prefix.
- Not current project version truth.

Disposition:

- Do not rewrite or delete remote tags without the explicit remote rewrite gate.
- Do not alter dependency constraints merely because they contain `2.0.0`.
- Keep old `v2.0.0` references in repair audit files as evidence of the
  corrected mistake.

## `v1.2.0-alpha`

Classification:

- Historical M150 alpha-target contract label.
- Preserved by existing M150/M101-M150 tests and verifiers as audit context.
- Not the active package baseline, not a current release target, and not final
  stable approval under the repaired SemVer policy.

Disposition:

- Keep historical M150 alpha-target docs and tests intact unless a later scoped
  roadmap patch retires or remaps the M150 contract label.
- Current docs must describe `v1.2.0-alpha` as historical/audit context, not as
  the active baseline.

## `v1.0.0` Through `v1.7.2`

Classification:

- Historical internal milestone labels and already-pushed tags from the old
  line.
- Not current release truth after this repair.

Disposition:

- Preserve locally and remotely by default.
- Proposed deletion or replacement remains blocked unless the remote rewrite
  gate is explicitly satisfied.

## Dependency Versions

Dependency versions such as `pydantic>=2.0.0`, npm package versions, and Node
engine ranges are not project release claims. They are intentionally excluded
from current-version repair.

## Uncertain References

No unclassified current-version references remain. The remaining old labels are
historical, dependency, or repair-audit context.
