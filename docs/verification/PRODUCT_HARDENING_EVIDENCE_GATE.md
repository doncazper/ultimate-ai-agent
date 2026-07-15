# Product Hardening Evidence Gate

Status: implemented internal gate; independent review pending

This gate separates evidence that can fail independently from the code it
checks. A green repository verifier is necessary, but it is not sufficient for
distribution or production readiness.

## Independent automated evidence

| Evidence | Implementation | Failure signal |
|---|---|---|
| Property tests | Hypothesis exercises bearer comparison, unsafe build identity input, and durable storage idempotency. | A generated counterexample fails pytest. |
| Mutation tests | `mutmut` targets the local-auth and build-identity boundaries on the weekly/manual supply-chain lane, records killed and surviving mutants, and enforces a 60% no-incomplete-results floor. | An incomplete run or score regression below the floor fails the mutation job. |
| Storage fault injection | Real SQLite and Founder Loop JSONL artifacts are backed up, verified, corrupted, interrupted, and restored in temporary state roots. | Hash, JSONL, SQLite integrity, low-disk, schema, or atomic-publish checks fail closed. |
| Packaged-app golden journey | The generated macOS launcher is executed from an isolated bundle with a fake backend/frontend handoff. | Bundle layout, executable permissions, or handoff failure fails pytest. |
| Supply-chain evidence | Frozen `uv.lock` installation, Python and npm audit, and CycloneDX SBOM generation run on repository-scoped self-hosted macOS runners. The content-free CodeQL SARIF severity verifier is implemented, but CodeQL analysis remains externally blocked by the repository action allow-policy. | Audit or SBOM validation fails the workflow; supplied SARIF with a high-severity finding fails the local verifier. |
| Dependency compatibility | Repository-scoped self-hosted macOS runners install the bounded lowest-direct and highest dependency resolutions and run the identity, API, recovery, and property boundaries. | Either supported edge fails its focused pytest lane. |

Historical Goat comparison evidence is checked against source bytes from its
recorded Git commit, not against the moving worktree. Pytest CI retains Git
history for this fail-closed binding check.

The full repository verifier, documentation verifier, OpenAPI verifier, and
Foundation Gate remain required. These independent lanes supplement them; they
do not replace them.

## Recovery operator journey

Run backup and restore offline. The destination must not already exist, and the
commands emit safe receipts without raw paths or database contents.

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_founder_loop_recovery.py backup \
  --state-dir STATE_DIR --backup-dir BACKUP_DIR --confirm-offline
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_founder_loop_recovery.py verify \
  --backup-dir BACKUP_DIR
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_founder_loop_recovery.py restore \
  --backup-dir BACKUP_DIR --target-state-dir RESTORE_DIR \
  --confirm-offline-restore
```

Backup uses SQLite's backup API, validates SQLite with `PRAGMA quick_check`,
validates each JSONL record, records content hashes and sizes, checks available
space, and publishes atomically. Restore verifies before writing, stages all
artifacts, checks space, and publishes atomically. Unknown storage schema
versions require an explicit migration and are never overwritten in place.

This first recovery lane is offline and local. Encrypted backups, scheduled
backup UX, in-place rollback, cross-version migrations, remote destinations,
and automatic recovery are not claimed.

## External review packet

An independent security and product reviewer should receive:

- the immutable build identity from `scripts/inspect_build_identity.py`;
- the SBOM hashes and vulnerability-scan results from the supply-chain job;
- mutation score and surviving-mutant report;
- packaged-app golden-journey results;
- one successful backup/verify/restore drill and one corruption rejection;
- `/api/manifest` route auth, approval, and idempotency enforcement inventory;
- the local-browser threat model in `SECURITY.md`;
- a strict-mode screenshot showing a backend failure without mock fallback.

Acceptance requires zero unresolved Critical or High security findings, no
operator-critical product flow that silently uses mock data, successful restore
from the reviewed artifact, and explicit disposition of Medium findings.
Maintainers must record reviewer identity by safe organization/ref, review
date, reviewed build and commit refs, finding refs, dispositions, and retest
refs. Until that external record exists, external review remains pending and no
distribution or production-readiness claim is allowed.

## Honest remaining boundaries

- The launcher keeps the local bearer out of the Vite build and transfers it in
  a scrubbed URL fragment to memory. Native IPC or a distribution-grade
  Keychain session bootstrap is still required before distribution.
- Global idempotency middleware validates header shape only. The API manifest
  labels that posture explicitly. Durable replay may be claimed only by an
  exact route with a route-owned receipt store and owner ref.
- Build identity is available in API, Control Center Settings, and the CLI
  inspector. A dedicated redacted support-export bundle remains future work.
- The oversized generated/legacy client, type, fixture, verifier, and storage
  files remain maintainability debt. New behavior in this change is placed in
  focused modules; this gate does not claim those hotspots are partitioned.
