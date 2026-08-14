# Fast Local Verification

Status: implemented local-development feedback; not merge or release evidence.

The canonical cutover architecture is documented in
[`RISK_BASED_VERIFICATION_ARCHITECTURE.md`](RISK_BASED_VERIFICATION_ARCHITECTURE.md).
The stable local commands are compatibility entry points over the same
backend-owned Tier 0-3 selection used by private diagnosis and CI planning.
They do not maintain a second rule or command registry and do not produce
merge authority.

UAA has two stable changed-path commands:

```bash
make verify-fast
make verify-affected
```

`verify-fast` runs the smallest useful checks for normalized changed paths.
`verify-affected` adds boundary-level checks such as the full frontend contract,
OpenAPI, product truth, and redaction where those surfaces are affected. Both
commands use the canonical fixed command registry, deterministic sorted paths,
the merge-base diff, both sides of renames, staged and unstaged changes, and
untracked files.
Advanced direct CLI use may add repeated `--path` values, but those values are
always unioned with Git state and can never hide it.

Unknown paths, verification topology, CI configuration, dependency manifests,
gate architecture, and shared test setup fail closed to Tier 3 and `make
verify-dev-sharded`. Neither selector caches a prior result, grants authority,
or counts as release evidence. GitHub affected preflight reports a Tier 3 full
gate without starting a duplicate complete suite; the repository-scoped GitHub
jobs normally own that exact-SHA resource.

### Static scan process scheduler

`make verify-static` preserves the canonical `SCAN_SEQUENCE` but may execute
reviewed entries in four process-isolated workers. It uses a dedicated local
verification entry point so the current v4 hosted CI command and its outer
exact-head execution fence remain unchanged. The scheduler binds worker plans
and structured results to the repository HEAD, the exact scan-registry
fingerprint, and a per-shard context ref. Any registry addition or rename that
has not updated the reviewed fingerprint fails closed to one serial lane; it
is never assumed parallel-safe.

Every declared scan must return exactly one identity-matching result. Missing,
duplicate, substituted, failed, and timed-out results fail the run. The worker
count is capped by `UAA_VERIFY_CPU_BUDGET` and the detected logical CPU count;
`STATIC_SCAN_WORKERS=1 make verify-static` remains the serial diagnostic path.
Worker state lives in a private ephemeral directory and is removed after
aggregation. Raw worker output is not retained; failure reporting uses bounded
safe refs. This local scheduler does not change hosted CI command authority,
create a second command registry, or grant merge evidence on its own.

`make test-sharded`, `make test-sharded-profile`, and `make frontend-check`
remain available for intentional local complete verification. They execute the
canonical pytest or frontend lane on a clean exact SHA through the host-wide
attempt ledger and owner-only exact-execution fence; they are not separate
command definitions. Local entry points use an owner-scoped
`/private/tmp/uaa-verification-execution-fence-v2-<uid>` store so the
repository-scoped runner's owner-only fence cannot block a different local
account. Complete pytest and TypeScript verification use separate host-wide
locks and separate attempt ledgers, so those independent resource classes may
run concurrently while duplicate work within either class still fails closed.
During the compatibility window, both current resource locks also hold a
shared lease on the legacy `active.lock`; pre-change runners require that lease
exclusively, so an already-running legacy command drains before current work
starts and a later legacy command cannot overlap it. Current pytest and
TypeScript commands can still overlap because both use the shared legacy lease
plus distinct exclusive resource locks. TypeScript admission checks and mirrors
its exact start into the legacy `attempts.json` under a separate migration lock
before writing its resource-bound ledger, while complete-pytest records retain
the legacy four-field hash shape. Exact retries are therefore visible in both
directions without letting the two current resource classes overwrite one
another.
Starting one consumes the single attempt for its own resource class, SHA, and
dependency state inside its execution plane. Local and GitHub planes may each
produce one independently bound attempt for the same tree; the shared physical
resource lock still prevents conflicting concurrent use, and a second attempt
within either plane fails closed. Private diagnostics retain their separate
non-gating reproduction lock and cannot consume either exclusive merge-gate
resource. This preserves the same candidate SHA across proportional local
qualification and authoritative hosted evidence instead of requiring a
content-free commit rotation. `make
verify`, `make verify-dev-fast`, `make verify-dev-sharded`, and `make
verify-local` also include the canonical complete-pytest lane and consume that
attempt. `test-sharded-profile` is an alternative first and only complete run
for the state, not a second refresh after `test-sharded`.

Before durable admission, an exclusive local lane checks writable temporary
capacity and every runtime it requires. Complete pytest requires the installed
Python test runtime, Node, npm, and the frozen Matrix adapter runtime; Control
Center requires Node, npm, and the installed TypeScript, Vitest, and Vite tool
targets. A missing prerequisite fails before consuming the exact-state attempt.
Prepare a new isolated worktree once with:

```bash
make verification-bootstrap
```

The bootstrap installs the frozen Python, Matrix, and Control Center dependency
sets. It is explicit and reusable rather than hidden inside each verification
attempt.

Failed local exclusive lanes retain at most five owner-only, metadata-only
diagnostic envelopes in one bounded insertion-ordered journal outside the
repository and print only a content-free
`diagnostic-ref:local-verification:*`. Raw command output is erased through the
original open descriptor; the resulting empty transient inode is left for the
outer private temporary-root cleanup, so no pathname scan or deletion is part
of the security boundary. Each retained envelope is allowlisted to command
refs, terminal states, byte counts, output digests, and validated safe failure
refs. Retention pins and validates the owner-only root descriptor, locks that
inode with a bounded deadline, and writes the next journal to a fixed
owner-validated staging inode. Only after those bytes are synced and
identity-validated is the staging inode atomically published over the committed
journal and the root synced. A crash or interruption before publication leaves
the previous journal intact, and a later attempt safely overwrites abandoned
staging state. Retention does not enumerate, timestamp-sort, prune, or delete
individual paths. Before a ref is published, both the exact committed journal
bytes and its named inode are revalidated while the lock is still held.
Terminal diagnostics preserve timeout and cancellation causes.

Admission also validates the complete offline npm dependency trees for the
Control Center and Matrix adapter with scripts disabled. Missing or invalid
transitive dependencies therefore fail before a durable verification attempt
is consumed.

Prefer focused tests plus `verify-fast` or `verify-affected` while stabilizing a
branch, and reserve complete resources for the final GitHub-hosted merge
gate. For a dirty worktree, a selected frontend typecheck is advisory feedback
for content that is not yet an exact SHA. On a clean committed tree the affected
executor defers that exclusive command to the canonical installed frontend
lane together with its dependent Vite build, while retaining selected unit
tests and safety checks. `make verify` remains the release-grade local
composition when a deliberate local-only full gate is required, but it does
not satisfy branch protection.

## Canonical API snapshot

`tests/fixtures/api_route_inventory_133.json` is the canonical generated static
API declaration snapshot. It is built from FastAPI OpenAPI and `/api/manifest`,
checks unique route keys and operation IDs, carries a deterministic content
fingerprint, enforces a separate hand-reviewed route-security policy floor, and
explicitly excludes runtime authority. Use:

```bash
PYTHONPATH=src .venv/bin/python scripts/verification/api_contract_snapshot.py --check
PYTHONPATH=src .venv/bin/python scripts/verification/api_contract_snapshot.py --refresh
```

Refresh updates the snapshot and the marked active count blocks in the three
canonical API documents. Historical release records remain immutable.

## Measured baseline

Same-machine local measurements before this refactor, in seconds:

| Lane | Cold | Warm | Notes |
|---|---:|---:|---|
| Focused API-verifier tests | 7.37 | 5.89 | 11 tests |
| OpenAPI contract verifier | 3.09 | 3.03 | process startup included |
| Documentation integrity | 0.28 | 0.22 | static |
| Product truth | 3.31 | 3.48 | static plus imports |
| Foundation Gate | 23.46 | 23.11 | 627 checks |
| Sharded pytest | 126.87 | 111.48 | eight shards; historical cold run had one isolated-worktree environment failure before fail-fast admission, warm run green |
| Control Center frontend | 58.66 | 56.73 | typecheck, lint, 257 tests, production build |

The cold pytest value is diagnostic only because one shard could not find the
worktree-local virtual environment. It is not a passing baseline. The warm
measurement is the comparable green baseline. The current preflight prevents
that class of missing-runtime failure from consuming an attempt. `make
verify-value-audit`
records the unique defect class and overlap posture for the main active lanes.
That audit is registry-bound to every selector command and release lane and
validates the exact-SHA synthetic run and timing derivations in
`docs/verification/verifier_value_measurements.json`; unmeasured lanes remain
explicit instead of inheriting timing claims.

The selector targets under 60 seconds for typical fast changes and under two
minutes for typical affected changes. These are latency targets, not permission
to skip a required full gate. After-change timings must be measured on the same
machine before claiming an improvement.

Same-machine warm selector measurements after the refactor:

| Representative change | `verify-fast` | `verify-affected` |
|---|---:|---:|
| Active documentation | 0.31s | 4.49s |
| API application boundary | 14.94s | 18.07s |

These measurements prove the typical latency targets for two representative
surfaces only. Frontend changes retain the complete frontend contract in the
affected tier and may approach the two-minute budget. Critical and unknown
changes intentionally exceed the fast targets because they fall back to the
complete local/dev gate.

The first complete green profile after residual-attribution repair completed in
104.77s. A seed-only confirmation completed in 100.48s with all shard durations
between 96.72s and 100.44s. Their median is 102.63s, 7.94% below the 111.48s
green warm baseline. The post-cutover frontend sample was 50.13s, 11.63% below
the 56.73s warm baseline. Product-truth warm versus cold was 5.14% slower;
documentation, Foundation Gate, and frontend cold/warm comparisons were below
their cold samples. No comparable same-machine result regressed by more than
15%, so the artifact records no warning. This is advisory scheduling evidence,
not a universal performance claim.

The frozen eleven-case legacy-selector comparison passed before cutover and is
kept as a lower-bound regression check. It does not preserve a second active
selector. Only the measured duplicate downstream frontend execution was
removed; unique and unmeasured verifiers remain in their original gates.
