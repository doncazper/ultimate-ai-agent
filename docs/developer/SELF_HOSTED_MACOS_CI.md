# Self-Hosted macOS CI

Status: implemented repository workflow and provisioning contract; runner
registration remains local operator setup until the dedicated account is
created and the provisioner completes.

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
- Fork pull requests fail closed before a job is scheduled on the Mac.
- The workflow token has `contents: read` only, and checkout does not persist
  its token.
- No GitHub Actions cache or artifact upload/download action is used. Job logs
  and safe step summaries remain subject to GitHub's normal Actions retention.
- Four isolated runner processes are the default so the existing pytest shard
  contract can make progress concurrently. Set `UAA_RUNNER_COUNT=1` through
  `4` before provisioning to choose a smaller bounded count.
- Python 3.12 and Node 22 are shared, pre-provisioned Homebrew toolchains. CI
  does not use the setup actions because their macOS installers require
  host-level installation privileges that the non-admin runner must not gain.
- Runner work roots contain `.metadata_never_index` markers so Spotlight does
  not amplify I/O while four large repository checkouts are materialized.
- Pytest shard basetemps, performance reports, and static-verification timings
  use each job's private `RUNNER_TEMP`. The shared-Mac CI budget keeps a
  180-second stretch goal, reports a 360-second target, and enforces a
  480-second hard timeout. The wider ceiling absorbs measured whole-machine
  contention from the release matrix without hiding it; only the hard timeout
  terminates a shard.
- The performance release lane waits for the rest of the CI matrix before it
  measures latency. This keeps the four-runner pool useful for functional
  checks without treating whole-machine contention as product latency.
- CPU- and I/O-heavy job classes are staged: lint, pytest shards, backend and
  release checks, Control Center verification, visual regression, performance,
  then the aggregate Foundation Gate. Jobs within a stage still use the four
  runners concurrently. This prevents unrelated scans from exhausting pytest
  and Vitest per-test deadlines on one physical Mac.
- Release lanes disable Bash's immediate-exit behavior only inside their
  bounded command wrappers so failures produce safe summaries and still end
  the job unsuccessfully.
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
repository registration tokens without printing them, registers each runner,
and installs root-owned LaunchDaemons that execute as `uaa-ci`. Each service
receives a private writable tool-cache path, while jobs use the pre-provisioned
Python and Node binaries without granting the runner `sudo`.

The provisioning script never changes GitHub billing, spending limits,
payment methods, repository visibility, workflow permissions, or paid runner
settings.

## Verify

Run the static contract and inspect GitHub's live runner state:

```bash
.venv/bin/python scripts/verify_self_hosted_macos_ci.py
gh api repos/doncazper/ultimate-ai-agent/actions/runners \
  --jq '.runners[] | [.name, .status, .busy, [.labels[].name]]'
```

Expected names are `uaa-ci-mac-arm64-01` through the configured count. Each
must be `online` and advertise `self-hosted`, `macOS`, `ARM64`, and `uaa-ci`.

Open a same-repository pull request only after at least one runner is online.
All named release lanes remain present. With fewer than four local runner
instances they queue and serialize rather than consume GitHub-hosted minutes.

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
