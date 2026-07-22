# Exact-Head CI Evidence DAG

Status: implemented CI architecture contract. This is repository verification
infrastructure only. It grants no runtime, provider, browser, network, shell,
connector, model, production, or standing authority.

## Old/new inventory

The previous topology placed the required backend release lanes after complete
pytest and serialized Control Center behind static plus all backend lanes. That
made the post-pytest critical path contain work with no proof dependency on
pytest. Only five source receipts reached the Foundation prerequisite builder.

The current `ci-architecture:exact-head-evidence-dag-v1` topology preserves all
visible check contexts and commands while changing only scheduling and proof
transport:

| Stage | Declared budget | Work |
| --- | ---: | --- |
| bootstrap | 1/4 | canonical manifest attestation |
| pre-suite pool | at most 4/4 | lint, exact-base affected preflight, required backend release lanes |
| pytest exclusive | 4/4 | eight logical shards, four workers, one installed environment |
| post-suite pool | at most 4/4 | static 2/4, Control Center 2/4, then dependent frontend/visual/packaging lanes |
| performance exclusive | 4/4 | isolated latency measurement after functional work |
| Foundation exclusive | 4/4 | terminal exact-evidence validation and Foundation report |

The canonical inventory contains every job identity, display/check name,
command lane, real prerequisite, resource class, resource stage, CPU and memory
units, timeout, evidence posture, eight-shard count, four-worker count, four
runner services, and required check context. Static validation rejects an
unknown stage, an over-budget job, an under-declared exclusive job, or any
declared concurrency set above the fixed machine budget.

## Exact proof chain

`UAA_CI_EXACT_SHA` binds the event head and checkout. The comparison base is an
exact commit and affected preflight preserves its local ref. Manifest
attestation resolves one bounded exact-diff visual scope and publishes it as a
job output through a descriptor-relative, owner/root-controlled parent chain;
every later plan and the visual execution decision consume that
same value, so affected-path proof cannot diverge between lanes. Every required command job
emits a content-bound GitHub job-output envelope from the canonical lane runner.
The envelope binds:

- repository SHA and exact selected-unit definition;
- canonical command manifest and verifier definition fingerprints;
- dependency lock-set, platform, test collection, shard plan, and TypeScript
  project/runtime fingerprints where applicable;
- terminal receipt, command/result membership, redaction posture, and proof
  equivalence;
- the derived pytest run manifest for the commandless `pytest` context.

The terminal validator accepts one ordered result and envelope per upstream
job. It rejects arity or order drift, duplicate bindings, cross-operation or
cross-head substitution, wrapper/content-fingerprint tampering, non-success job
results, unexpected receipt status, dependency chronology drift, or an
aggregate whose exact receipt bindings and missing-unit posture do not match
its point in the DAG. The commandless pytest receipt is also bound to the exact
dependency receipt refs from which it was derived. Typed-optional lanes remain
in the ordered result set but emit envelopes only when their optional execution
runs; a missing required envelope is never accepted. The frontend release lane
must reuse the exact passing `command:frontend.check` receipt emitted by its
declared Control Center dependency; a fresh or substituted proof is rejected.
Foundation also reconstructs the legacy prerequisite manifest from the
expanded pre-suite, pytest, and static receipt chain, preserving the existing
report contract. That content-bound manifest persists the exact visual scope,
so standalone Foundation loading does not depend on ambient process state.
Before accepting any TypeScript-executing receipt, the terminal job installs
the frozen frontend dependencies and independently resolves the bounded
version-only runtime binding; it does not repeat typechecking.

The validator writes one owner-only, non-symlink, content-free local manifest
through a descriptor-relative parent chain that rejects untrusted writable
directories.
No raw output, path, environment, prompt, response, credential, provider
payload, or host identity is durable evidence.

## Failure and cancellation matrix

- A required lane failure, cancellation, timeout, or skip prevents its envelope
  or yields a non-success result; the `always()` terminal job runs and rejects
  the incomplete set.
- A superseding SHA cancels the prior workflow through the existing concurrency
  key. Receipts from that SHA cannot satisfy the replacement plan.
- Missing required, duplicated, reordered, oversized, malformed, or cross-job envelopes
  fail before Foundation starts.
- A comparison-base, lockfile, manifest, checkout, or verifier change produces
  a different plan and rejects prior envelopes even if a wrapper hash is
  recomputed.
- Typed-optional visual or packaging execution may be inapplicable only through
  its declared lane posture; its check must still succeed. An exact envelope is
  required whenever that optional execution runs.

Focused tests inject every result terminal state and the membership, ordering,
same-plan/cross-plan substitution, chronology, visual-scope, and frontend reuse
failures above. The hosted run is not duplicated for benchmarking or diagnosis.

## Timing acceptance

The goal is a post-pytest critical path below five minutes on the private Mac.
Use the first ordinary pull request after this architecture lands as the first
natural sample and the next ordinary queue pull request as the second. Record
job start/completion timestamps from their existing Actions run only; do not
dispatch benchmark-only or duplicate workflows. Compare:

1. completion of `pytest / sharded suite`;
2. completion of `foundation-gate-report`;
3. overlap of static and Control Center jobs;
4. isolation of performance and Foundation;
5. total queue delay separately from execution time.

A sample above five minutes is an optimization finding, not permission to skip,
weaken, or rename a gate. Test-corpus modernization begins only after the CI PR
is green and this architecture has been exercised naturally by one or two
subsequent ordinary queue PRs.
