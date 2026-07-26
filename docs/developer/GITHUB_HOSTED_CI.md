# GitHub-Hosted CI

Status: implemented standard hosted-runner contract.

UAA uses standard GitHub-hosted runners for repository verification. The
public repository receives these runners without metered Actions minutes; UAA
does not use larger runners. Every job starts on a fresh virtual machine, uses
a read-only workflow token, checks out the exact event head, and does not
persist checkout credentials.

This is CI infrastructure only. It grants no UAA runtime, shell, browser,
provider, connector, production, billing, or AuthorityLease capability.

## Runner boundary

- The 19 canonical CI contexts run on the standard arm64 `macos-15` image.
- The base-controlled, metadata-only `fork-policy` job runs on
  `ubuntu-24.04`.
- Supply-chain jobs run on standard `macos-15`.
- macOS tag verification and explicitly requested packaging run on standard
  `macos-15`.
- `macos-15-xlarge`, `macos-latest-xlarge`, and every self-hosted selector are
  rejected by the static CI contract.
- Python 3.12.13 and Node 22.23.1 are installed through exact
  repository-allowlisted revisions of `actions/setup-python` and
  `actions/setup-node`.
- Frozen `uv` and npm locks remain mandatory. Actions cache and artifact
  upload/download services are not used.

Standard macOS hosted runners do not provide nested virtualization. The
desktop-packaging lane therefore records the existing exact typed-optional
`reason-ref:github-hosted-macos-docker-unavailable` posture and still executes
its required static packaging contract. The separate local operator packaging
proof remains available when Docker evidence is needed. This does not create a
binary distribution claim.

## Public pull requests

The primary CI and supply-chain workflows use `pull_request`, never
`pull_request_target`. They execute untrusted contribution code only on fresh
hosted virtual machines with:

- `contents: read`;
- no repository secrets;
- no persistent checkout credential;
- no self-hosted network or hardware access; and
- GitHub's repository setting requiring approval for every external
  contributor before a workflow starts.

`fork-pr-policy.yml` uses `pull_request_target` only for a metadata-only check
from the trusted base branch. It has `permissions: {}`, performs no checkout,
uses no action, consumes no secret, and never references the pull request head
SHA or ref.

## Exact-head evidence DAG

The hosted migration preserves every existing check name, canonical command,
dependency edge, exact-head binding, eight-shard/four-worker pytest budget,
typed receipt, and Foundation Gate assertion. It changes the runner profile,
not the verification standard.

Cross-job plan identity binds to the declared
`github-hosted-macos-15-python-3.12.13-node-22.23.1` profile rather than an
individual VM image patch. Every generated receipt separately records a
content-free fingerprint of its observed OS, architecture, and Python patch,
so image drift remains auditable without making independent hosted VMs reject
one another's otherwise equivalent evidence.

The hosted performance lane keeps the existing 45-second Foundation Gate
best/mean budgets. It performs one untimed cold-start warmup before the timed
sample so ephemeral image import/cache initialization is not mislabeled as
steady-state evaluator latency.

Every command-bearing job emits a bounded job-output envelope containing safe
refs, hashes, counts, timestamps, statuses, and exact plan bindings only. The
terminal `foundation-gate-report` job uses `if: always()` and rejects failed,
cancelled, unexpectedly skipped, missing, extra, duplicated, reordered,
cross-head, cross-operation, or recomputed-wrapper evidence.

The execution fences for complete pytest and the Control Center lane live
under the job-specific `RUNNER_TEMP`. Ephemeral hosted jobs do not share a
machine-level fence, home directory, cache, or credential store.

The machine-verifiable inventory lives in
`ci_architecture_inventory()` in
`scripts/verification/ci_command_manifest.py`. Detailed proof transport and
failure behavior live in
`docs/developer/CI_EVIDENCE_DAG_ARCHITECTURE.md`.

## Binary release boundary

A pushed tag verifies the macOS package in a read-only, secret-free job and
does not automatically publish a GitHub Release. Binary publication requires
a maintainer-triggered `workflow_dispatch` with an explicit publish input. A
separate write-scoped job runs only after read-only verification succeeds,
then rebuilds and verifies the immutable tag before publication. Public source
visibility and MIT licensing do not imply notarized binaries, public beta,
production readiness, support guarantees, or runtime authority.

## Verification

Run the static contracts locally:

```bash
.venv/bin/python scripts/verify_github_hosted_ci.py
.venv/bin/python scripts/verification/ci_command_manifest.py
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_github_hosted_ci.py \
  tests/test_ci_workflow.py \
  tests/test_supply_chain_workflow.py \
  tests/test_macos_first_class_installer.py
```

The final merge gate is one non-duplicated GitHub Actions run on the exact
eligible commit. Local verification is proportional pre-push evidence and
cannot substitute for required hosted checks.

## Self-hosted retirement

The former `uaa-ci-mac-arm64-*` services must remain available until the hosted
migration pull request completes exact-head CI and lands. After the public
repository settings and hosted main-branch confirmation are accepted:

1. stop the four local runner services;
2. remove their repository registrations;
3. verify that no workflow contains a self-hosted selector;
4. confirm an ordinary pull request and `main` push complete on hosted
   runners; and
5. retain historical tags and receipts unchanged.

The old provisioning scripts remain historical source evidence only. They are
not invoked by any active workflow or canonical verifier.
