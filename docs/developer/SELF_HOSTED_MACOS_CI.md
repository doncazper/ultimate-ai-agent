# Self-Hosted macOS CI

Status: implemented repository workflow and provisioning contract. Runner
registration is local operator-managed infrastructure and must remain
repository-scoped, bounded, and independently revocable.

UAA uses repository-scoped self-hosted Apple Silicon runners so normal CI can
continue without GitHub-hosted runner minutes. GitHub still coordinates jobs,
checks, pull requests, and logs. The local Mac supplies the compute.

This is CI infrastructure only. It grants no UAA runtime, shell, browser,
provider, connector, production, or AuthorityLease capability.

## Security boundary

- The repository must remain private while these runners are registered.
- Runner processes execute as the dedicated standard account `uaa-ci`, never
  the everyday operator account and never root.
- The runner account must contain no SSH keys, cloud credentials, package
  registry credentials, browser profiles, or personal Keychain material.
- Each runner is scoped only to `doncazper/ultimate-ai-agent` and carries the
  custom label `uaa-ci` plus GitHub's `self-hosted`, `macOS`, and `ARM64`
  labels.
- Fork pull requests never reach the normal CI workflow. A separate
  base-controlled `pull_request_target` policy job checks only repository-name
  metadata, uses no checkout, action, secret, PR ref, or head SHA, and fails the
  pull request. No fork-controlled repository content or command reaches the
  Mac. Keep `fork-policy` among the repository's required merge checks.
- The workflow token has `contents: read` only, and checkout does not persist
  its token.
- No GitHub Actions cache or artifact upload/download action is used. Job logs
  and safe step summaries remain subject to GitHub's normal Actions retention.
- Four isolated runner processes are the default so the existing pytest shard
  contract can make progress concurrently. Set `UAA_RUNNER_COUNT=1` through
  `4` before provisioning to choose a smaller bounded count.
- Runner LaunchDaemons use macOS `ProcessType=Standard`. Background process
  classification is intentionally rejected because it constrains CI children
  to background scheduling and makes the bounded test budget non-representative;
  interactive scheduling is not granted.
- Every workflow command uses exact `taskpolicy -c utility` scheduling so an
  older installed runner cannot silently inherit background QoS. The pytest
  command keeps the same exact wrapper for explicit contract verification. The
  wrapper execs the existing command and grants no administrator access.
- Python 3.12 and Node 22 are shared, pre-provisioned Homebrew toolchains. CI
  does not use the setup actions because their macOS installers require
  host-level installation privileges that the non-admin runner must not gain.
- Runner work roots contain `.metadata_never_index` markers so Spotlight does
  not amplify I/O while four large repository checkouts are materialized.
- Pytest shard basetemps, performance reports, and static-verification timings
  use each job's private `RUNNER_TEMP`. The shared-Mac CI budget keeps a
  900-second stretch goal, reports a 1200-second target, and enforces an
  1800-second hard timeout for the complete nine-shard suite. The wider suite
  ceiling absorbs measured single-host variance without hiding it; only the
  hard timeout terminates the sharded run.
- The performance release lane waits for the rest of the CI matrix before it
  measures latency. This keeps the four-runner pool useful for functional
  checks without treating whole-machine contention as product latency.
- CPU- and I/O-heavy job classes are staged: lint, pytest shards, backend and
  release checks, Control Center verification, visual regression, performance,
  then the aggregate Foundation Gate. Jobs within a stage still use the four
  runners concurrently. This prevents unrelated scans from exhausting pytest
  and Vitest per-test deadlines on one physical Mac.
- After manifest attestation, lint and a canonical fast affected-path preflight
  run in parallel. The preflight binds the exact pull-request base or prior push
  SHA and can fail quickly on focused Python, documentation, or frontend-safety
  regressions. It never replaces or satisfies the complete pytest and release
  gates; critical CI/topology changes fail closed to those full gates.
- Pull-request and main-push visual screenshots use the exact GitHub event
  range and run only when it changes the Control Center, its visual/product-language documentation,
  or its visual contract verifiers. The visual-contract verifier still runs on
  every CI invocation, and missing Git history fails closed to the full browser
  lane. This preserves the macOS image gate for affected UI changes without
  making unrelated integration work inherit stale image drift.
- Pytest keeps nine deterministic logical shards inside one job and one
  installed environment: one serialized Matrix resource preflight followed by
  eight timing-balanced shards. Fixed-port owners and tests that copy, probe,
  or execute the bounded Matrix Node runtime stay in that preflight instead of
  competing with the parallel wave. Four isolated workers overlap other
  subprocess-heavy shard waits while avoiding the lock starvation and repeated
  dependency installation caused by multiple runner jobs on one physical Mac.
  Every logical shard receives its own bounded `HOME`, `TEMP`, `TMP`, and
  `TMPDIR` below the run basetemp, so child processes cannot share runner-home
  caches, state, or credential configuration.
- Fixed-port Matrix fixture owners remain in one shard affinity group. Before
  the complete suite records its atomic start, the canonical lane verifies,
  while holding the host-wide full-suite lock, that the exact loopback fixture
  endpoint is free. Existing ownership fails as
  `reason-ref:ci:pytest-loopback-resource-unavailable`, not as a deterministic
  test failure; bounded bind waiting tolerates only a short release race.
  The explicitly marked resource-owning shard then finishes before the
  parallel shard wave starts, preventing another repository test from taking
  the endpoint during those integration checks.
  Contention that begins after this probe and durable start remains an ordinary
  test failure and is never relabeled as infrastructure.
- The complete pytest lane reads only the bounded, content-free shard rows from
  its transient performance report. GitHub's safe step summary retains failed
  shard refs and the fixed `make ci-reproduce-shard CI_SHARD_INDEX=<index>`
  command shape without uploading or retaining raw shard output as durable
  evidence. Transient shard logs remain only under the job-private runner temp
  directory until runner cleanup. Malformed, oversized, group/other-writable,
  stale, assignment-mismatched, or symlink-substituted reports are rejected and
  never become test evidence.
- Checkout remains on the repository-allowlisted `actions/checkout@v4` action;
  changing the repository Actions allow-policy is outside this provisioner's
  authority. Checkout tokens remain non-persistent.
- GitHub cancellation is forwarded by the Bash step and handled inside the
  shard runner for `SIGINT`, `SIGTERM`, and `SIGHUP`. Active shard process groups
  close with a bounded grace period; the wrapper escalates after a bounded wait
  so superseded runs do not leave an indefinitely waiting job on the dedicated
  account.
- GitHub jobs and the private fallback select from the same fixed command and
  lane definitions in `scripts/verification/ci_command_manifest.py`. GitHub
  executes the gating lanes; private fallback is limited to affected/focused
  checks and exact failed-shard diagnosis. The lane runner captures raw output
  only in a bounded transient file, persists only hashes, counts, durations,
  refs, and statuses, forwards cancellation to the entire child process group,
  and still ends the job unsuccessfully on a command failure.
- The dedicated account is not granted access to the everyday account's Docker
  Desktop socket. The desktop-packaging lane reports its permitted explicit
  `self-hosted-runner-docker-unavailable` skipped posture and still runs the
  packaging contract verifier. Live packaging proof remains available through
  the separate local operator verification lane.

Same-repository branches can execute their checked-in workflow commands on the
runner. Keep repository write access narrow and review workflow changes as
machine-execution changes.

## Provision once

From an administrator account with authenticated `gh`, on the intended Apple
Silicon Mac:

```bash
brew install python@3.12 node@22
./scripts/ci/provision_self_hosted_macos_runners.sh
```

The script uses secure `sudo` and `sysadminctl` prompts to create `uaa-ci` as a
standard user when it does not exist. It downloads the exact GitHub runner
archive `2.335.1`, verifies the published SHA-256 checksum, requests short-lived
repository registration tokens without printing them, and passes each token to
the upstream runner through its masked `ACTIONS_RUNNER_INPUT_TOKEN` input rather
than a process argument. It then registers each runner and installs root-owned
LaunchDaemons that execute as `uaa-ci`. Each service receives a private writable
tool-cache path, while jobs use the pre-provisioned Python and Node binaries
without granting the runner `sudo`.

An existing local `.runner` record is reused only when GitHub still reports the
exact runner name and the local record matches the expected repository, work
folder, and runner name. The record must be a regular non-symlink file. A local
record without a matching remote registration fails closed. Remove that stale
registration with an exact short-lived GitHub removal token before
reprovisioning; the bootstrap helper never silently trusts or overwrites
ambiguous runner state.

The provisioning script never changes GitHub billing, spending limits,
payment methods, repository visibility, workflow permissions, or paid runner
settings.

The provisioner tolerates one transient macOS `launchctl` bootstrap race after
unloading an existing service. It waits two seconds, retries exactly once, and
then verifies that the system-domain service is loaded. A second failure remains
fatal and requires inspection rather than an unbounded retry loop.

## Verify

Run the static contract and inspect GitHub's live runner state:

```bash
.venv/bin/python scripts/verify_self_hosted_macos_ci.py
.venv/bin/python scripts/verification/ci_command_manifest.py
gh api repos/doncazper/ultimate-ai-agent/actions/runners \
  --jq '.runners[] | [.name, .status, .busy, [.labels[].name]]'
```

Expected names are `uaa-ci-mac-arm64-01` through the configured count. Each
must be `online` and advertise `self-hosted`, `macOS`, `ARM64`, and `uaa-ci`.

Open a same-repository pull request only after at least one runner is online.
All named release lanes remain present. With fewer than four local runner
instances they queue and serialize rather than consume GitHub-hosted minutes.

## GitHub-first private fallback

GitHub Actions remains the authoritative merge gate. Normal flow is an affected
local preflight, push of one exact SHA, and one required GitHub run on the
repository-scoped runners. Pull requests explicitly check out and attest the
pushed head SHA instead of GitHub's synthetic merge ref. The required
`manifest-attestation` job validates the exact repository-owned plan before
parallel lint and fast affected preflight can start. Complete pytest waits for
both. The workflow concurrency key cancels superseded
SHAs, and the shared host guard plus exact resource-attempt fence permit only
one complete pytest attempt for that SHA and dependency state across GitHub and
local execution surfaces.
Private verification cannot execute the complete suite or matching TypeScript
resource, so the required GitHub run remains the sole full-gate execution.
Explicit local complete execution is a separate diagnostic/operator choice:
`make test-sharded`, `make test-sharded-profile`, and `make frontend-check`
enter the canonical lanes through the `local` surface and consume the same
one-attempt resource key. They never satisfy GitHub branch protection. Normal
pull-request cadence therefore uses affected and focused local checks and
reserves both exclusive resources for the final GitHub SHA.
The installed `control-center-frontend` job executes the canonical direct
frontend runner behind the same exact-identity fence used for complete pytest;
the local `make frontend-check` target enters that same lane through the local
wrapper rather than recursively invoking itself. The frontend runner executes
one `tsc -b`, one Vitest suite with
content-free observed collection proof, and one direct Vite build. The
identical package `lint` declaration is satisfied by the one typecheck rather
than executed again. The downstream frontend release job validates and reuses
the exact passing job envelope; it cannot substitute an unbound success or
repeat the frontend suite. Vite and Playwright resolve only the exact pinned
installed executables; package acquisition is forbidden during verification.

The two exclusive resource identities are `resource-ref:complete-pytest` and
`resource-ref:typescript-typecheck`. Their attempt keys bind the exact repository
SHA, dependency state, resource ref, and TypeScript runtime/version where
applicable—not a workflow surface or plan ref—so the host-wide shared attempt
ledger rejects a different GitHub or local consumer for the same state.
Private policy forbids both resources. A changed dependency fingerprint creates
a distinct attempt. Separate owner-only exact start/settlement state lives under
versioned real macOS paths: the repository-scoped runner uses
`/private/tmp/uaa-verification-execution-fence-v2`, while local entry points use
`/private/tmp/uaa-verification-execution-fence-v2-<uid>`. The shared attempt
ledger, not either owner-only store, fences duplicate work across accounts.
Symlinked path components, foreign identities, and cross-identity settlement
are rejected.

When the GitHub control plane is unavailable, a run fails before any repository
command starts, runner capacity exceeds the bounded queue budget, runner contact
is lost before checkout, or superseded-run churn reaches its cap, the operator
may use the one-shot local controller:

```bash
.venv/bin/python scripts/ci/verify_with_fallback.py \
  --repo . \
  --sha "$(git rev-parse HEAD)" \
  --mode github-first

.venv/bin/python scripts/ci/verify_with_fallback.py \
  --repo . \
  --sha "$(git rev-parse HEAD)" \
  --mode status
```

The controller uses only read-only `gh run list` and `gh run view` observations.
It cannot dispatch, rerun, cancel, approve, merge, push, tag, or change Actions
or billing settings. A code/test/install failure after a repository command has
started is `github_code_failure` and never enters private fallback.

An operator can reproduce one exact deterministic failed shard without rerunning
the complete suite by using `make ci-reproduce-shard CI_SHARD_INDEX=0` (indices
0 through 8). These fixed reproduction lanes come from the same canonical
manifest and do not satisfy the GitHub merge gate.

Eligible private fallback creates a standalone credential-free local clone at
the exact pushed SHA only after a live, bounded remote-head query proves that
SHA is the exact head of the current local branch. The branch name is transient;
durable scope records retain only its content-bound ref. The live `main` head is
bound separately as the comparison base. A deleted, superseded, detached,
unadvertised, malformed, or locally unverifiable branch fails closed. The
isolated clone pins that validated base object to an immutable local ref,
removes its remote, and never shares refs, config, or hooks with the developer
repository. It verifies lock fingerprints and regular repository paths and
installs only through the existing lockfile policy. After dependency setup it
captures a bounded content fingerprint of every ignored setup artifact under
the exact `.ci-bootstrap`, `.venv`, Control Center `node_modules`, and pinned
Matrix client adapter `node_modules` roots, including file type and permissions.
Every selected command revalidates tracked files plus that exact setup
fingerprint immediately before and after execution. Any other untracked file,
module-shadowing path, dependency mutation, FIFO, or special file fails closed.
Python bytecode, pytest cache, and Ruff cache output are redirected outside the
checkout. The one canonical Vitest command disables its results cache, and the
one canonical Vite build command writes to the run's bounded temporary root,
so frontend verification cannot create import-visible or generated checkout
state.
It derives an exact
affected/focused command scope from the canonical changed-path selector and
excludes full pytest, the matching TypeScript resource, aggregate units, and
audit units. If selection requires a full gate, private fallback reports that
posture instead of claiming a focused pass; an explicitly named deterministic
failed shard may still run through one exact diagnostic lane. Private fallback
never invokes a non-diagnostic canonical CI lane.
A new versioned coordination directory avoids dependence on legacy lock-file
ownership and holds one bounded exact-SHA attempt ledger shared by all four
runners and private CI. The bounded controller ledger records only safe refs,
hashes, timestamps, duration buckets, and terminal states. Raw command output,
paths, environment values, runner identity, credentials, and host details are
not durable evidence. A crash after `private_start` becomes
`recovery_required`; the same SHA is never started a second time.

The GitHub pytest job reserves bounded time for at most ten minutes of shared-Mac
lock contention, fifteen minutes of setup, and the canonical 1,830-second suite
command inside its 60-minute job timeout. The attempt is recorded only after
all locked pre-start validation succeeds and immediately before process spawn.
A spawn failure conservatively consumes the one-attempt allowance so a hard
termination cannot leave an unrecorded full-suite process. Empty or partial
GitHub job evidence fails closed as a
code/evidence failure rather than being relabeled as an infrastructure outage.
An attempted duplicate is rejected before process spawn with the content-free
`reason-ref:ci:full-suite-attempt-recorded`; local coordination details and
tracebacks are not emitted to the operator surface.
The execution fence uses the real owner-only `/private/tmp` macOS directory;
the `/tmp` alias is intentionally rejected because the fence refuses symlinked
path components.
The canonical shard command loads a tiny repo-owned pytest plugin that writes
only an exclusive-created, bounded list of content-free test refs under a fresh
private run directory. Failed shards expose at most eight refs derived from
parameter-free module and test-function metadata; parameter values, failure
bodies, captured output, logs, and local paths never enter the file, safe
summary, or durable receipts.

Vitest and Playwright use matching content-free collection consumers. Reporter
JSON exists only in a fresh owner-only job directory and is unlinked after
bounded validation on success or rejection. Durable frontend receipts contain
only safe runner refs, hashed collection identity, counts, terminal posture,
TypeScript binding refs where applicable, and redaction status. A missing,
unsafe, malformed, or command-status-mismatched report fails the job.
Playwright traces, screenshots, and other non-reporter output stay in that
temporary boundary and are removed rather than written into the checkout.

CLI exit code `0` means only `github_green` on the exact live, attested SHA.
Pending/running states return `2`; code failure, private failure, and external
blocking return `1`. Injected observation files are simulation-only and can
never satisfy the merge gate.

Private `pass` is reported as `private_green_pending_github`; it means only that
bounded diagnosis is stable enough to return to GitHub. It never satisfies
branch protection, complete-suite proof, Foundation prerequisites, or merge.
The exact privately checked SHA must be pushed and receive one final green
GitHub merge-gate run using the same manifest fingerprint. Capacity gets one
three-minute cooldown, a repair series gets at
most two private SHA attempts, and private green gets at most one final GitHub
retry. Exhaustion ends as `externally_blocked`.

## Stop and incident response

The LaunchDaemon labels are `com.github.actions.runner.uaa-ci-01` through
`-04`. Stop an instance immediately with:

```bash
sudo launchctl bootout system/com.github.actions.runner.uaa-ci-01
```

Then remove the runner registration in GitHub repository Settings → Actions →
Runners. If a branch executes unexpected code, stop every instance, rotate any
credential that was mistakenly placed in the runner account, remove the
runner registration, and inspect the runner `_diag` directory locally. Do not
upload raw runner diagnostics because they may contain paths or command output.

## Cost posture

Self-hosted runner compute does not consume GitHub-hosted runner minutes. This
does not make every Actions feature unmetered: GitHub-hosted runners and excess
Actions storage remain separate billing surfaces. UAA therefore keeps caches
and uploaded artifacts out of this workflow and makes no paid-usage claim.
