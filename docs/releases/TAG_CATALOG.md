# Tag Catalog

Status: active tag-history catalog
Baseline: v0.104.0 / 0.104.0
Scope: documentation-only tag history summary

Ultimate AI Agent has a dense internal milestone tag history. Existing tags are
immutable audit records: do not delete, move, retarget, replace, force-push, or
reinterpret them as current authority. Current product/package truth comes from
`VERSION.md`, `docs/release_notes/v0_104_0.md`, `docs/README.md`, and
`docs/DOCUMENTATION_INDEX.md`.

This document explains the tag story for portfolio reviewers without rewriting
history or creating GitHub Releases.

## Read-Only Tag Audit

A local read-only inspection found:

| Metric | Count |
|---|---:|
| Total tags | 447 |
| Annotated tag objects | 54 |
| Lightweight tags pointing directly to commits | 393 |

The inspection used read-only `git for-each-ref` and `git tag --list`
commands. No tags were created, deleted, moved, retargeted, rewritten, or
pushed.

## Tag Families

| Family | Meaning |
|---|---|
| `vX.Y.Z` and prerelease tags | Product/package baselines and older internal milestones. Some early tags are lightweight historical markers. |
| `checkpoint-mNNN` and named `checkpoint-*` tags | Accepted milestone or audit checkpoints. |
| `baseline-vX.Y.Z-YYYYMMDD` tags | Currentness baselines for recent package states. |
| `operator-runtime-*` and dated named tags | Focused audit lanes for Operator Runtime Excellence work. |
| `backup/version-repair-original-v*` tags | Preservation refs from version-repair work. They exist to retain historical audit points. |

Older `v1.x` tags and the historical `v2.0.0` tag are audit records, not the
current active baseline. The current baseline is the `v0.104.0` line.

## Current Anchors

| Anchor | Meaning |
|---|---|
| `v0.104.0` | Current product/package baseline tag. |
| `baseline-v0.104.0-20260623` | Currentness baseline for `v0.104.0` / `0.104.0`. |
| `checkpoint-m169` | Latest accepted repository checkpoint in active docs. |
| `checkpoint-m166`, `checkpoint-m167` | Latest accepted local model lane checkpoints in active docs. |
| `fcc-operational-maturity-20260623` | Operational maturity gate audit tag. |

## Future Convention

Future approved release and baseline tags should be annotated tags with concise
messages. Use the `v` prefix for product versions, keep the tag subject short,
and include scope, status, and verification pointers in the annotation message.

Future tags should not be created for planning-only work unless an accepted
release or checkpoint task explicitly grants that exact action. Stale
currentness claims should be corrected through reviewed commits and later
approved tags, not through history rewrite.

## Portfolio Interpretation

The tag history is intentionally preserved as evidence of iteration. It shows
the project moving from early exploratory milestones into a more disciplined
contract-first baseline with active version truth, release notes, product
truth, and documentation integrity checks.

For current evaluation, prefer:

- `README.md`
- `VERSION.md`
- `docs/release_notes/v0_104_0.md`
- `docs/portfolio/CURRENT_STATUS.md`
- `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
- `docs/maintenance/RELEASE_PROCESS.md`

Historical release packets under `docs/archive/releases/` remain useful for
audit review, but they are not current implementation claims.
