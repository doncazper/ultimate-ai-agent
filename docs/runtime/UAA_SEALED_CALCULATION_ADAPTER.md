# UAA Sealed Deterministic Calculation Adapter

Status: exact macOS-first implementation; catalog posture remains
configuration-required until the current installation's local hostile proof passes

## Scope

`lane-ref:sealed-arithmetic-exact-lease` evaluates one bounded ASCII
arithmetic expression. It is not a general Python, CodeAct, shell, notebook, or
package runtime. The result is transient numeric evidence, never authority.
The earlier design placeholder
`lane-ref:codeact-sandbox-calculate-no-approval` is intentionally not a
compatibility alias: it remains blocked because this adapter cannot execute
general CodeAct or caller-supplied code. The narrower lane name is part of the
fail-closed product truth.

The exact execution path is:

```text
SealedCalculationMissionService
  -> SynchronousAuthorityMissionOrchestrator
  -> AuthorityMissionRunner
  -> AuthorityDispatcher
  -> SealedCalculationAuthorityDispatchAdapter
  -> DockerSealedCalculationBackend
```

No API or Control Center mutation route executes this lane. The existing
capability-availability and Action Inbox catalog routes expose backend-owned
read-only truth. `scripts/dev/uaa_runtime.py sealed-calculation inspect` is the
human-readable readiness surface. `sealed-calculation prepare` reads the
expression from stdin, emits only its hash and exact safe lease resource refs,
and performs no execution. `sealed-calculation run` reads the expression from
stdin again and requires caller-supplied exact request, plan, mission, run,
step, lease, owner, and immutable start-deadline refs.

## Authority

No per-invocation approval means only that a second approval is unnecessary
after `LocalApprovalAuthority` has validated issuance of an exact mission-scoped
`AuthorityLease`. The lease must bind `workspace/execute`, mission ref,
capability, adapter, fixed target, input ref, expression hash, grammar,
attestation, limit profile, and operation/cost ceilings. Policy, lease,
revocation, deadline, budget, kill switch, safe-disable, target, readiness,
idempotency, and input hash are re-evaluated immediately before the transient
input commit, after the container READY handshake.

The dispatcher first appends a durable start claim. While still inside its
locked pre-start authority boundary, the adapter verifies the exact container
configuration, receives the runner `READY` frame, commits the transient input,
and verifies the matching `INPUT_ACCEPTED` hash. Only then does it append the
runtime-start-confirmed receipt. A succeeded receipt requires runtime start,
input commitment, result collection, and verified absence of the exact owned
container. If the bounded removal or inspection command reports failure,
cleanup is accepted only when an immediate exact-name container inventory
proves that container absent; a still-present container or unavailable
inventory remains recovery-required. This reconciliation records only
content-free status and safe refs. Unknown execution or cleanup truth is never
automatically replayed.

## Isolation profile

The local image is built from an exact public base digest. Invocation uses the
exact locally discovered image ID with pulls disabled. Image labels bind the
reviewed runner and isolation-probe source hashes. The runtime then verifies:

- no network namespace;
- no host mounts, binds, volumes, ports, or devices;
- read-only root filesystem;
- bounded `noexec,nosuid,nodev` temporary storage;
- non-root UID/GID;
- all Linux capabilities dropped;
- no-new-privileges;
- default-deny seccomp allowlist;
- one-process, memory, CPU, file-size, descriptor, wall-time, and output bounds;
- fixed entrypoint, safe environment, no restart, and no container logs;
- the current Docker CLI, Docker Desktop daemon identity/security posture, and
  no-follow seccomp file identity at create and commit boundaries.

The image retains only the fixed Python 3.13 launcher under `/usr/local/bin` and
removes pip, ensurepip, setuptools, shell, and package-manager surfaces. A manually reviewed AST
interpreter accepts numeric constants, parentheses, unary plus/minus, and the
bounded operators `+`, `-`, `*`, `/`, `//`, `%`, and `**`. Numeric lexemes are
converted directly to bounded Decimal values; inexact division or power results
are denied, and floor/modulo follow explicit floor semantics. Character, byte,
node, nesting, exponent, magnitude, and result bounds apply before evidence is
returned. This semantic allowlist is the primary untrusted-input boundary; the
container is defense in depth.

## Data and evidence

Raw expressions remain only in a bounded process-local transient store and are
sent over container stdin. Durable plans and dispatch ledgers contain the input
ref, expression SHA-256, byte count, fixed target, grammar, limits, and
attestation refs. Raw expressions, numeric previews, environment values, Docker
payloads, local paths, logs, credentials, and stderr never enter durable state.

Terminal evidence binds the exact image, runner source, seccomp profile, limits,
dispatcher execution, output hash, lease, budget, and mission receipts. Replay
of the unchanged mission returns content-free durable evidence and never starts
a second container. The numeric preview is available only on the first transient
result path.

## Proven denials and limitations

The local hostile suite proves IPv4, IPv6, Unix sockets, host home/private
directories, root writes, subprocess creation, unsafe environment keys, shell
binaries, package managers, and credential paths are denied. It also proves the
only writable surface is the bounded disposable temporary filesystem.

The lane remains macOS-first and requires a current Docker Desktop daemon plus a
locally built source-bound image. The static availability snapshot intentionally
keeps compatibility, configuration, health, safe-disable, resources, and
freshness unknown. Linux and Windows are not product implementations. General
code execution, shell, network, host filesystem access, packages, background
execution, browser work, connector writes, production authority, and a global
callable switch remain denied.

Docker Desktop and the Docker CLI run with the local user's authority. A
malicious same-UID process or substituted daemon is outside this adapter's
isolation guarantee; current socket ownership, daemon identity, version,
architecture, cgroup, and seccomp posture are hash-bound and drift fails closed.

Build locally:

```bash
PYTHONPATH=src .venv/bin/python scripts/build_sealed_calculation_image.py
```

Run the required local hostile proof:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_sealed_calculation_backend.py
```

The build may use the network only if the exact base digest is not already in
the local Docker cache. Runtime invocation always uses `--pull never`.
