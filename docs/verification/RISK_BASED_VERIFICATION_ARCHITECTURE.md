# Risk-Based Verification Architecture

Status: Phase 00 contract and shadow-model foundation. Existing verification
commands, CI jobs, release lanes, and Foundation Gate behavior remain the
authoritative execution and merge evidence until a later measured cutover.

This document defines UAA's canonical repository-verification architecture. It
does not grant runtime authority, relax a merge gate, or treat a local result as
a GitHub merge-gate result. Phase 00 adds the typed vocabulary and a
fail-closed risk model so later phases can consolidate measured duplication
without removing unique defect coverage.

## Scope and invariants

The target architecture is one versioned verification directed acyclic graph
(DAG) shared by:

- local and affected-path checks;
- private CI diagnosis;
- repository-scoped self-hosted GitHub CI;
- release verification; and
- Foundation Gate receipt validation.

Python-owned definitions are canonical. GitHub workflow YAML, Make targets,
and operator commands are verified projections or entry points; they must not
become independent command registries. The final GitHub run on the exact
eligible commit remains the authoritative merge gate wherever branch
protection requires it.

These rules are permanent:

- unknown, malformed, renamed, deleted, overlapping, or unclassified changes
  escalate fail-closed;
- test failures cannot be reclassified as infrastructure failures;
- branch protection and required checks cannot be weakened;
- paid runners, billing changes, and CI-policy bypasses are out of scope;
- no verifier or test may be removed solely because another command appears
  similar;
- no file is split, frozen, moved, renamed, or reorganized solely because of
  size, line count, complexity, or a maintainability threshold; and
- redacted verification evidence cannot contain raw logs, environment values,
  credentials, usernames, hostnames, or absolute local paths.

## Canonical typed DAG

The graph is a bounded immutable set of verification units and dependency
edges. Its definition is adapted from the existing command manifest, release
lanes, and CI job graph rather than introduced as a competing registry.

| Contract | Purpose |
|---|---|
| `VerificationUnit` | One command, aggregate, or audit node with exact dependencies, minimum risk tier, execution surfaces, timeout, exclusive resources, and proof-equivalence posture. |
| `VerificationPlan` | Immutable selection for one exact commit and dependency state, including the complete selected unit membership and graph bindings. |
| `VerificationReceipt` | Content-free terminal proof for one unit, bound to the plan, commit, dependencies, platform, definitions, and test collection. |
| `VerificationRunManifest` | Bounded content-free summary of a run and its receipt refs; it is evidence, not repository or runtime authority. |
| `VerificationGateDecision` | Fail-closed decision over required units and exact validated receipts, including missing or invalid proof and the GitHub-gate posture. |
| `VerificationValueRecord` | Measured verifier value from a safe synthetic mutation, including expected defect class, observed detection, overlap, timing, and redaction posture. |

Every unit ref and dependency edge is stable and safe-ref-only. Validation
rejects duplicate units, missing dependencies, self-dependencies, cycles,
unbounded plans, invalid refs, and unit definitions that do not match their
declared execution kind. A lower-risk selection cannot omit a required
higher-risk dependency.

Graph scheduling may eventually run genuinely independent units concurrently.
Two units are not independent when their dependency edges, test state, ports,
temporary directories, process trees, or exclusive resource refs overlap.
Complete pytest, matching TypeScript typecheck, visual, and other shared-machine
resources remain serialized until isolation is proven.

## Risk tiers

The repository verification tier is distinct from UAA runtime authority modes
and from the current `fast` versus `affected` selection mode.

| Tier | Change posture | Minimum interpretation |
|---:|---|---|
| 0 | Documentation and inert planning | Text or inert bundle metadata only, with no executable, contract, security, release, or product-truth effect. Documentation integrity, product truth, redaction, and diff integrity still apply as selected. |
| 1 | Isolated presentation/UI | Presentation-only desktop changes with no backend authority, API, persistence, dependency, tooling, or route-contract effect. Focused frontend checks apply. |
| 2 | Bounded non-authority core behavior | Bounded Python, API, frontend contract, or test behavior that does not change an authority, security, persistence, dependency, execution, CI, or release-critical boundary. Focused regression and boundary checks apply. |
| 3 | Authority, security, persistence, dependencies, execution, CI, or release-critical behavior | Full fail-closed posture with all affected boundary and release evidence. Unknown or unsafe classifications land here. |

Tier selection takes the highest applicable tier across every changed path and
change kind. A path may legitimately match more than one compatible rule; an
ambiguous or contradictory overlap escalates rather than selecting the least
expensive result. Both sides of a rename or copy are classified. Deletes,
type changes, unsafe path forms, missing classification, malformed Git diff
records, and forced-full invocations select Tier 3.

Risk classification chooses verification; it never grants permission to
modify a product or execute an agent capability.

## Exact proof bindings

A reusable proof is valid only when all relevant bindings match:

- exact repository and base commit SHAs;
- normalized change-set fingerprint and risk-manifest version;
- dependency-lock and dependency-state fingerprints;
- safe platform and toolchain fingerprint, without machine identity;
- command-manifest and verifier-definition fingerprints;
- immutable unit membership, dependency edges, and plan fingerprint;
- deterministic test inventory, pytest shard plan, and exact test-collection
  fingerprint where applicable;
- frontend and desktop visual scope;
- bounded start, completion, and duration values; and
- content-free result, receipt, and redaction refs.

Changing any binding invalidates the old proof. A skipped unit, stale receipt,
foreign commit, incomplete collection, unknown terminal result, or missing
required receipt fails closed. Foundation Gate may consume an equivalent prior
receipt only after validating every exact binding; a generic assertion that CI
ran is not equivalent proof.

Phase 00 records a deterministic test inventory and labels it
`inventory_bound`; it does not mislabel that digest as an executed pytest
collection. Gate evaluation rejects receipt reuse for every test-executing unit
until a later phase records the exact `collected` fingerprint.

The eventual execution policy permits at most one complete pytest execution
and one matching TypeScript typecheck for an exact commit and dependency state.
That limit is not activated in Phase 00. Cross-surface proof reuse must preserve
GitHub's authoritative final gate and may never label private execution as a
GitHub-run check.

## Verifier value and consolidation

Verifier value is measured, not inferred from names or command similarity. A
safe synthetic mutation is created only in an isolated fixture or temporary
copy and is identified by a safe ref. Its value record captures whether the
expected verifier detected the defect, which other units overlap, bounded
timing evidence, and the content-free receipt ref.

A surviving, blocked, unknown, or unmeasured mutation prohibits removal of the
associated coverage. Consolidation is allowed only after measurements prove
that the replacement retains every unique defect class. Performance work must
compare same-machine cold and warm samples with equivalent dependency state;
regressions greater than 15 percent produce an explicit warning and review.

Deterministic code failures are not automatically rerun. Superseded work may
be cancelled, but cancellation cannot convert an incomplete result into a
passing receipt.

## Phase 00 shadow boundary

Phase 00 is deliberately non-disruptive:

1. Define and validate the typed contracts and risk tiers.
2. Adapt the current command manifest and job graph into the typed DAG.
3. Produce a deterministic shadow plan for representative changed-path sets.
4. Compare the shadow plan with the currently authoritative selection.
5. Fail tests when the shadow graph is malformed or less conservative.

Phase 00 does **not**:

- replace `make verify-fast`, `make verify-affected`, `make verify`, release
  lanes, private CI, GitHub CI, or Foundation Gate;
- consume shadow receipts as release or merge evidence;
- remove, skip, deduplicate, or reorder existing verification execution;
- change branch protection, runner policy, or workflow authority; or
- claim timing improvements before comparable measurements exist.

The existing paths remain authoritative throughout the bounded shadow period.
Later phases may cut one surface over at a time only after focused tests,
repository-scoped self-hosted CI, and the old-versus-new comparison prove the
new graph is equal or more conservative. No recursively generated prompt pack
or open-ended verification program follows this architecture.

Operators can inspect the shadow selection for a clean checked-out exact commit:

```bash
PYTHONPATH=src .venv/bin/python \
  scripts/verification/plan_affected_verification.py \
  --base-sha <exact-base-sha> \
  --head-sha <exact-head-sha>
```

The command refuses a dirty or mismatched worktree. `--json` emits the same
redacted backend-owned plan; it does not execute checks or satisfy a gate.

## Redacted evidence posture

Plans and receipts use safe refs, hashes, counts, timestamps, and bounded
durations. Command output remains transient and bounded; durable evidence may
retain only its count and digest. Repository-relative paths may be used where
the plan requires affected-path binding, but absolute paths and machine
identity are excluded. Verification evidence cannot mint runtime authority,
approve an action, or satisfy an AuthorityLease.
