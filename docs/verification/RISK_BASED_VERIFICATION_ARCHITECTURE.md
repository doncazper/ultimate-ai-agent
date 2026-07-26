# Risk-Based Verification Architecture

Status: Phase 05 canonical cutover. Local selectors, private diagnosis, GitHub
CI, release verification, and Foundation Gate project or consume one canonical
typed DAG. Exact resource-attempt fencing, measured verifier value, and the
bounded legacy-selector comparison are active; the final repository-scoped
GitHub run remains the merge authority.

This document defines UAA's canonical repository-verification architecture. It
does not grant runtime authority, relax a merge gate, or treat a local result as
a GitHub merge-gate result. The phased cutover added typed vocabulary,
fail-closed risk selection, exact receipts, and measured consolidation without
removing unique defect coverage.

## Scope and invariants

The target architecture is one versioned verification directed acyclic graph
(DAG) shared by:

- local and affected-path checks;
- private CI diagnosis;
- standard ephemeral GitHub-hosted CI;
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
- larger/paid runners, billing changes, and CI-policy bypasses are out of scope;
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

The plan records a deterministic test inventory and labels it
`inventory_bound`; it does not mislabel that digest as execution. Complete
pytest runs now derive a separate `collected` fingerprint and count from the
actual shard processes without a second collection pass. Raw node IDs exist
only transiently and are hashed before bounded owner-only sidecars are
published. Missing, duplicate, unsafe, malformed, or collection-error evidence
fails closed.

Each exact pytest shard-reproduction command is also represented by one
canonical diagnostic DAG unit. These units are local/private only, serialized,
excluded from the default and GitHub merge graphs, and explicitly non-gating.
When a complete suite fails, its bounded summary may expose untrusted,
diagnostic, code-metadata-only `pytest-test-ref` hints alongside the failed
shard ref; raw test output and failure payloads remain transient. These hints
are not collection-bound proof. A diagnostic reproduction can locate a
failure, but it cannot satisfy a complete-pytest receipt or a merge gate.

The Control Center TypeScript declaration is bound to the exact TypeScript 7
version, package and lock state, project-reference graph, configured commands,
and macOS arm64 platform package. A runtime binding is accepted only after the
installed launcher, compiler intermediaries, native platform binary, package
metadata, safe Node identity, and bounded `--version` probe agree before and
after the verified command. This proof does not execute an additional
typecheck. The combined frontend lane now carries an observed Vitest collection
fingerprint and count derived from transient reporter output. Raw reporter data
is deleted after bounded validation and never enters the receipt.

The target cutover policy permits at most one complete pytest execution and one
matching TypeScript typecheck for an exact commit and dependency state. The
complete pytest and canonical installed frontend jobs both use durable
exact-identity fences. The frontend command runs one `tsc -b`, treats the
identical `lint` declaration as already satisfied, runs Vitest once with
observed collection proof, and invokes Vite directly so the production build
does not run a second `tsc -b`. The downstream frontend release lane must reuse
the exact passing dependency receipt; synthetic dependency satisfaction is
rejected. Private CI may run affected checks and one exact failed-shard
diagnostic, but it cannot run a non-diagnostic canonical lane or label private
evidence as a GitHub check.

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

## Bounded shadow comparison and cutover

Before cutover, Phase 00 captured the legacy selector as a frozen lower-bound
baseline. Phase 05 now compares that baseline with the canonical selection
across eleven bounded representative cases. The comparison rejects missing
legacy commands, a less conservative risk tier, changed baseline fingerprints,
or malformed cases. The checked-in baseline is comparison evidence only; it is
not a second command registry and cannot select or execute verification.

`make verify-fast`, `make verify-affected`, private fallback, and CI manifest
planning now consume the same canonical selection. The compatibility commands
remain stable operator entry points. Release lanes and Foundation Gate consume
the same unit definitions and exact receipts without treating local evidence as
a GitHub merge result. No branch-protection or runner-policy rule changed.

Operators can inspect the active canonical selection for a clean checked-out
exact commit:

```bash
PYTHONPATH=src .venv/bin/python \
  scripts/verification/plan_affected_verification.py \
  --base-sha <exact-base-sha> \
  --head-sha <exact-head-sha>
```

The command refuses a dirty or mismatched worktree. `--json` emits the same
redacted backend-owned plan; it does not execute checks or satisfy a gate. The
bounded old-versus-new comparison remains available through
`scripts/verification/verification_shadow_comparison.py`; it cannot become an
alternate selector.

## Redacted evidence posture

Plans and receipts use safe refs, hashes, counts, timestamps, and bounded
durations. Command output remains transient and bounded; durable evidence may
retain only its count and digest. Repository-relative paths may be used where
the plan requires affected-path binding, but absolute paths and machine
identity are excluded. Verification evidence cannot mint runtime authority,
approve an action, or satisfy an AuthorityLease.

## Phase 01 proof and scheduling boundary

Phase 01 adds content-bound v2 unit receipts, partial run manifests, and a typed
GitHub-gate proof shape. The legacy boolean GitHub posture remains permanently
non-authoritative. Structural hashes prove internal consistency, not GitHub
provenance, so the Phase 01 evaluator remains blocked even when every receipt
and run binding agrees. A later trusted GitHub API attestation loader must
recompute the canonical repository state and validate the exact workflow run
before the typed decision may satisfy a merge gate.

The pure scheduler partitions only dependency-ready units into deterministic
resource-disjoint waves. Nonparallel units remain singletons, complete pytest
and TypeScript resources cannot overlap, failed or unknown dependencies block
all descendants, and independent work remains distinguishable. Scheduling is
execution mechanics only: it cannot generate a receipt or authorize a merge.

CI lanes can emit typed receipt and run-fragment sidecars in addition to the
unchanged legacy receipt. A fragment is explicitly blocked until the later
aggregator validates complete DAG membership; it cannot be presented as a
complete run. GitHub, private CI, release verification, and Foundation Gate do
not consume these new sidecars until the next measured cutover phase.

## Phase 02 immutable proof and whole-run boundary

Phase 02 adds v3 unit receipts, exact execution identities, a durable start
fence, an immutable content-addressed proof store, and deterministic whole-run
aggregation. These contracts are evidence mechanics only; they cannot satisfy
GitHub, merge, runtime, approval, policy, or AuthorityLease gates.

The execution identity binds one unit to the exact commit, plan, dependency
locks and state, platform/toolchain posture, command and verifier definitions,
test inventory and observed collection posture, pytest shard plan, TypeScript
project/runtime where applicable, execution surface, the ordered DAG
fingerprint, and the complete selected-unit definition. Changing dependencies,
kind, timeout, commands, surfaces, or scheduling posture invalidates proof. An
identical durable start can occur at most once inside one fence store. An
unsettled durable start becomes `recovery_required`; a terminal proof is reused;
and only a canonically classified, evidence-bound deterministic code failure is
not automatically rerun. The fence is available
for the later consumer cutover but does not yet change existing CI execution.
Its owner-only lock inode is pinned, total state is bounded, incomplete
pre-publication stages are reclaimed, and an exact same-inode post-link crash is
reconciled before another start decision is made.
Typed command execution rebuilds and compares the full plan, TypeScript runtime
where relevant, and execution identity immediately before each process start.
The suite-attempt fence is recorded only after that check. A post-run comparison
remains a second boundary, not a substitute for pre-start denial.

The receipt store walks and creates every path component descriptor-relative,
rejects links and non-regular substitutions, publishes owner-only canonical
JSON immutably, and detects root or artifact replacement. Stored objects are
bounded and content-addressed. Readers reject duplicate keys, non-finite
numbers, non-canonical bytes, unknown fields, invalid contracts, and digest
mismatches without reflecting supplied data in errors. Publication recovery is
serialized and bounded: abandoned internal stages are removed safely, while an
exact crash-after-link publication is settled without accepting arbitrary
hardlinks. Historical v2 fingerprints and wire shapes remain byte-stable.
Receipt wall-clock spans are bounded and reconciled against monotonic duration
within a narrow clock-skew allowance; run and unsettled-start spans also fail
when they exceed the bounded verification window.

Whole-run aggregation revalidates every v3 receipt against the canonical plan,
normalizes input to DAG order, rejects extra, duplicate, stale, cross-surface,
or cross-binding evidence, and derives only commandless aggregate units from
their exact dependencies. Audit units are never fabricated. A passing run must
bind exactly one receipt to every selected unit; missing or non-passing evidence
remains blocked or failed. Dependency command reuse is accepted only when an
exact passed dependency receipt proves the command actually executed.
Dependent evidence is rejected unless every prerequisite is present, passed,
and terminal before the dependent begins. Dynamic result, reuse, receipt, and
execution refs are digest-bound rather than merely syntactically safe.
The canonical DAG must be topologically ordered, and selected lanes, commands,
and gate-resource postures must derive exactly from selected unit definitions.
A failed multi-command unit may bind only its actually executed command prefix;
it cannot fabricate evidence for commands never started.

CI lanes may opt into this immutable store and emit a v3 incomplete whole-run
manifest. A lane that still represents dependency satisfaction with a synthetic
legacy result, skip, or not-applicable command remains v2 and blocked rather
than claiming reusable v3 proof. Visual-scope decisions are plan-bound, and a
frontend or visual test without observed collection evidence remains blocked.
GitHub output transport, private-CI narrowing, and Foundation receipt
consumption are Phase 03 work. Trusted GitHub API attestation remains separate,
so the final GitHub run continues to be the sole authoritative merge gate.

## Phase 03 bounded consumer cutover

Five GitHub source jobs emit compact, content-free, repository-constructed
envelopes through owner-only job outputs: manifest attestation, lint, affected
preflight, complete pytest, and static verification. An envelope contains the
exact v3 unit receipt and compact plan binding, including the event-derived
comparison-base SHA used by affected preflight, but no gate, authorization, or
merge boolean. A changed or mismatched base invalidates the chain. The codec is
bounded and canonical; malformed, oversized,
non-canonical, unsafe, stale, foreign-plan, or substituted output fails closed.
No raw logs or uploaded artifacts are used for this transport.

The stable `pytest` job derives its commandless aggregate only after rebuilding
the canonical plan and validating the four exact prerequisite envelopes. The
Foundation job independently rebuilds that same plan from the checked-out SHA,
revalidates all five source envelopes, derives only the permitted aggregate
chain, and writes an owner-only prerequisite manifest. Foundation Gate accepts
that manifest only in `ci-parallel` mode and reports
`satisfied_by_exact_receipts`; a missing file, changed SHA, changed plan,
changed dependency state, changed verifier definition, incomplete source, or
standalone receipt ref is rejected. This reuse avoids repeating lint, pytest,
or static commands inside Foundation Gate. It does not make the constructed
envelopes authoritative outside the enclosing required GitHub run.

Complete pytest and the matching frontend TypeScript resource are declared
GitHub/local only. In Phase 03, the complete pytest source records its atomic
start in the durable exact-identity fence immediately before process spawn and
settles the fence with its exact terminal receipt. An unsettled start remains
recovery required; deterministic failure, cancellation, or a duplicate
identity cannot silently start another suite. Superseded workflow cancellation
still reaches the complete subprocess group. The frontend singleton continues
to run once per ordinary workflow invocation until Phase 04 binds its observed
Vitest/Playwright collection and activates the same exact-identity fence.
The complete pytest lane also checks its exact fixed Matrix loopback test
resource inside the locked atomic pre-start boundary and immediately before
recording a start. A busy endpoint is an explicit pre-start infrastructure
block, while the fixed-port fixture owners remain in one shard affinity group
and tolerate only bounded transient bind contention. Tests that copy, probe,
or execute the same bounded Matrix Node runtime join that exact resource group.
The explicit loopback and Node-runtime markers make the owning shard a
serialized preflight: it must finish before the eight ordinary timing-balanced
shards enter their parallel worker wave. The serialized posture is part of the
exact shard-plan fingerprint, not an unbound runner option. Direct single-shard
diagnosis remains available because it does not claim a complete-suite start.
Only contention observed at this pre-start boundary receives the infrastructure
reason; a collision after durable start remains a deterministic test failure.
Phase 03 includes the strict transient Vitest/Playwright JSON consumers needed
for that next cutover: they derive only bounded counts and identity hashes and
delete raw reporter output on both success and rejection. They are tested but
are not yet a gating workflow source.

The private fallback now has a deliberately narrower role. It verifies the
exact pushed SHA against the live exact head of the current branch, binds the
live `main` base and a hashed branch ref into its canonical plan, runs affected
or focused commands, and may reproduce one named failed pytest shard. The
canonical changed-path selector owns focused test selection; a full-gate or
unclassified result blocks ordinary private verification instead of silently
running too little. Private execution excludes complete pytest, matching
TypeScript, commandless aggregates, and audit units. Private green therefore
means only that bounded diagnosis is stable enough to return the exact SHA to
GitHub; it never satisfies branch protection, Foundation prerequisites, or
merge. Post-start faults settle as content-free recovery-required evidence and
the operator CLI never reflects the underlying traceback or local path.

## Phase 04 frontend proof cutover

The canonical installed Control Center job now owns the complete frontend
proof for one exact commit and dependency state. `make frontend-check` invokes
one repository-owned runner that validates the package-script declarations,
runs exactly one TypeScript project build, one Vitest execution, and one direct
Vite production build from the exact pinned installed binary. No package
acquisition is permitted during execution. The duplicate `lint` script is
accepted only while it is byte-for-byte identical to the declared typecheck
command; any package script drift blocks before execution.

Vitest writes transient JSON under an owner-only temporary directory. The
consumer validates bounded structure, repository-relative test identity,
counts, outcomes, retries, and status agreement, hashes the identities, emits
only a content-free aggregate, and deletes the raw report. A missing, malformed,
unsafe, stale, duplicated, substituted, or status-mismatched aggregate converts
an otherwise passing command into failure. The exact TypeScript runtime binding
and observed collection fingerprint are both attached to the v3 receipt.

The installed frontend job uses the same durable exact-execution fence as the
complete pytest job. Its compact GitHub output envelope is the only acceptable
proof for the downstream `frontend` release lane. The release lane validates
the exact plan, commit, comparison base, dependency state, definitions,
TypeScript runtime, collection proof, direct dependency edge, and source
receipt before recording `reused_exact_receipt`. It does not invoke TypeScript,
Vitest, or Vite again. A missing or synthetic dependency result fails closed.

Affected visual regression still executes as a separate exact lane. Its
repository-owned Playwright wrapper consumes and deletes transient JSON and
publishes the same content-free collection shape. Trace, screenshot, and other
non-reporter output is confined to the same owner-only temporary boundary and
removed after the command. A plan-bound
`not_affected` decision remains a non-executed, blocked v2 posture rather than
an invented passing visual receipt. Browser installation and screenshot
comparison remain visible prerequisites.

Phase 04 consolidates only the measured duplicate frontend execution already
represented by the exact installed-job receipt. It removes no unique test,
typecheck, build, safety, or visual coverage. The final verifier-value,
cold/warm timing, selector cutover, and bounded old-versus-new shadow
comparison remain Phase 05 work.

## Phase 05 canonical cutover and measured endpoint

Phase 05 makes `verification_selection.py` the one path-to-risk and
path-to-command decision source. The legacy selector CLI is a compatibility
projection over that source, the CI command manifest derives plan membership
from it, and private diagnosis narrows the same selection. API contracts,
governed memory/provider/extension contracts, and unknown or unsafe path
postures fail closed to Tier 3. The frozen legacy baseline passed all eleven
bounded comparison cases before cutover.

Exact resource-attempt identity is now global across execution surfaces for the
two exclusive resources: complete pytest and the matching TypeScript
declaration. The key binds the repository SHA, dependency state, canonical
resource ref, and TypeScript runtime/version where applicable. A second plan or
surface cannot start the same resource attempt; execution scope is audit
metadata rather than part of the availability key. The host-wide attempt ledger
enforces that cross-surface rule, while the separate owner-only execution fence
binds exact pre-start and terminal settlement. A changed dependency state
creates a distinct attempt; an unsettled exact attempt remains recovery
required. The execution fence store uses the versioned
`/private/tmp/uaa-verification-execution-fence-v2` boundary for the
repository-scoped runner and an owner-scoped
`/private/tmp/uaa-verification-execution-fence-v2-<uid>` boundary for local
entry points. Cross-account duplicate prevention remains in the shared attempt
ledger rather than either owner-only store. Private diagnosis still cannot
execute either exclusive merge-gate resource.

The stable `make test-sharded`, `make test-sharded-profile`, and
`make frontend-check` entry points now invoke the same canonical lane runner
with the `local` execution surface. They validate a clean exact SHA and consume
that SHA and dependency state's one durable resource attempt before process
spawn. A local complete run therefore cannot be repeated by GitHub for the same
state. Normal pull-request work uses `verify-fast`, `verify-affected`, and
focused tests locally, then reserves the complete pytest and TypeScript
attempts for the authoritative repository-scoped GitHub run. The profile target
may publish only the bounded content-free pytest timing artifact after the
canonical run succeeds.

Canonical affected execution also distinguishes an exact committed tree from a
changing worktree. On a clean exact SHA it defers the matching TypeScript
resource and its dependent Vite build to the installed frontend lane while
still running selected frontend unit tests and safety checks. On a dirty
worktree the direct typecheck and dependent build are advisory feedback for
uncommitted content and are not accepted as exact-SHA evidence. Affected
preflight therefore cannot consume or duplicate the later merge-gate
TypeScript attempt or violate the canonical dependency edge.

Verifier value is recorded by four fixed synthetic mutations in an owner-only
temporary boundary. Product-truth, redaction, API-contract, and frontend
declaration probes all killed their expected mutation on the exact source SHA;
zero probes survived or were blocked. The content-free v2 artifact binds the
repository, dependency state, platform, command manifest, verifier definitions,
test collection, probe definitions, result refs, and same-machine timing
comparisons. A surviving, blocked, stale, or tampered record prohibits
consolidation.

The only execution removed by this program is measured duplication:

- the downstream frontend release lane reuses the exact installed frontend
  receipt instead of repeating TypeScript, Vitest, and Vite; and
- selector rule and command declarations were consolidated into the canonical
  source without removing any selected verifier.

API, redaction, product-truth, visual, durability, web-hybrid, packaging,
local-model, and all other unique or unmeasured coverage remain retained.
Same-machine measurements are advisory, record warnings above 15 percent, and
support no universal speed claim. The final required GitHub run on the exact
eligible SHA remains the sole merge authority.
