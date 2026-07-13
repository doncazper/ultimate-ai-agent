# Fast Local Verification

Status: implemented local-development feedback; not merge or release evidence.

UAA has two stable changed-path commands:

```bash
make verify-fast
make verify-affected
```

`verify-fast` runs the smallest useful checks for normalized changed paths.
`verify-affected` adds boundary-level checks such as the full frontend contract,
OpenAPI, product truth, and redaction where those surfaces are affected. Both
commands use a fixed command registry, deterministic sorted paths, the merge-base
diff, both sides of renames, staged and unstaged changes, and untracked files.
Advanced direct CLI use may add repeated `--path` values, but those values are
always unioned with Git state and can never hide it.

Unknown paths, verification topology, CI configuration, dependency manifests,
gate architecture, and shared test setup fail closed to `make
verify-dev-sharded`. Neither selector caches a prior result, grants authority,
or counts as release evidence. `make verify` remains the release-grade local
gate.

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
| Sharded pytest | 126.87 | 111.48 | eight shards; cold run had one isolated-worktree environment failure, warm run green |
| Control Center frontend | 58.66 | 56.73 | typecheck, lint, 257 tests, production build |

The cold pytest value is diagnostic only because one shard could not find the
worktree-local virtual environment. It is not a passing baseline. The warm
measurement is the comparable green baseline. `make verify-value-audit`
records the unique defect class and overlap posture for the main active lanes.
That audit is registry-bound to every selector command and release lane and
verifies the fingerprint on
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
between 96.72s and 100.44s. Compared with the 111.48s green warm baseline, the
seed-only confirmation is 9.9% faster. This is same-machine scheduling evidence,
not a universal performance claim.
