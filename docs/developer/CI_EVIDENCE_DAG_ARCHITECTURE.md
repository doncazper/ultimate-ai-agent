# Exact-Head CI Evidence DAG

Status: implemented CI architecture contract. This is repository verification
infrastructure only. It grants no runtime, provider, browser, network, shell,
connector, model, production, or standing authority.

## Old/new inventory

The previous topology placed the required backend release lanes after complete
pytest and serialized Control Center behind static plus all backend lanes. That
made the post-pytest critical path contain work with no proof dependency on
pytest. Only five source receipts reached the Foundation prerequisite builder.

The current
`ci-architecture:exact-head-evidence-dag-v3-parallel-hosted` topology preserves
all visible check contexts and commands while removing false dependencies
between fresh GitHub-hosted machines. It uses dependency-aware parallelism
under `ci-execution-policy:bounded-cost-parallel-v1`; cost is bounded rather
than required to be zero.

| Stage | Declared budget | Work |
| --- | ---: | --- |
| bootstrap | 1/4 | canonical manifest attestation |
| parallel validation | exact canonical DAG width of 13 hosted jobs | lint, exact-base affected preflight, required backend lanes, complete pytest, static verification, and Control Center start as soon as their real dependencies are met |
| pytest exclusive | 4/4 on its machine | eight logical shards, four workers, one installed environment |
| frontend/static branches | up to 4/4 on each machine | static and Control Center run independently; frontend, visual, and packaging retain only their actual upstream edges |
| performance exclusive | 4/4 | isolated latency measurement after functional work |
| Foundation exclusive | 4/4 | terminal exact-evidence validation and Foundation report |

The canonical inventory contains every job identity, display/check name,
command lane, real prerequisite, resource class, resource stage, CPU and memory
units, timeout, evidence posture, eight-shard count, four-worker count, four
logical per-machine resource-budget units, permitted hosted runner classes,
the proven 13-job DAG-width cap, the 870 job-minute worst-case timeout cap, superseded-run
cancellation, hosted runner labels, and required check context. Static
validation recomputes the graph's exact maximum antichain and rejects an
unknown stage, an over-budget job, an under-declared exclusive job, or any
disagreement with the bounded-cost execution limits.

The terminal Foundation command receives both the exact head SHA and the exact
comparison-base SHA explicitly. It reconstructs the same plan and fails closed
if either ref disagrees with the prerequisite manifest.

The checked-in workflow currently selects standard hosted machines. The policy
also permits a repository-configured larger hosted runner class when available
and cost-capped. It does not authorize changing account billing, spending
limits, credentials, branch protection, or repository policy. Independent
implementation and review work may overlap in isolated worktrees; dependent
merges, shared-state mutations, authority changes, migrations, releases, and
tags remain ordered by their real dependency edges.

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
- dependency lock-set, stable declared runner profile, test collection, shard
  plan, and TypeScript project/runtime fingerprints where applicable, plus a
  separate observed platform fingerprint on each receipt;
- terminal receipt, command/result membership, redaction posture, and proof
  equivalence;
- the derived pytest run manifest for the commandless `pytest` context; that
  derived receipt spans and content-binds the complete transitive pre-suite
  dependency closure rather than only the final shard edge.

The terminal validator accepts one ordered result and envelope per upstream
job. It rejects arity or order drift, duplicate bindings, cross-operation or
cross-head substitution, wrapper/content-fingerprint tampering, non-success job
results, unexpected receipt status, dependency chronology drift, or an
aggregate whose exact receipt bindings, dependency-span timestamps, duration,
and missing-unit posture do not match its point in the DAG. The commandless
pytest receipt is also bound to the exact dependency receipt refs from which it
was derived. Typed-optional lanes always emit a v3 envelope. Their required
contract commands remain exact executed evidence, while a declared optional
command that does not run is separately bound to a content-free reason ref and
the receipt remains blocked. The terminal validator re-derives the only allowed
reason and result refs from the exact head, command, and affected scope, so a
recomputed wrapper cannot substitute nonexecution provenance; classifying a
required command as optional nonexecution is rejected. The frontend release lane
must reuse the exact passing `command:frontend.check` receipt emitted by its
declared Control Center dependency; a fresh or substituted proof is rejected.
After all upstream envelopes validate, the terminal validator constructs a
formal whole-plan run manifest that binds every exact terminal receipt ref
(and therefore each receipt's output digest). The Foundation lane consumes the
same complete ordered dependency envelope set, independently re-derives the
pytest aggregate, adds its own receipt, requires a fully passing whole-plan run,
and emits that final run manifest in its exact GitHub output envelope. This is
the durable downstream seal for static, frontend, visual, packaging,
performance, and Foundation proof.
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
  its declared command posture; its required contract command and exact blocked
  envelope must still be present, and its check must still succeed.

Focused tests inject every result terminal state and the membership, ordering,
same-plan/cross-plan substitution, chronology, visual-scope, and frontend reuse
failures above. The hosted run is not duplicated for benchmarking or diagnosis.

## Timing acceptance

Use the migration pull request as the first hosted sample and the next ordinary
queue pull request as the second. Record job start/completion timestamps from
their existing Actions run only; do not dispatch benchmark-only or duplicate
workflows. Compare:

1. completion of `pytest / sharded suite`;
2. completion of `foundation-gate-report`;
3. overlap of pytest, static, Control Center, and independent release lanes;
4. isolation of performance and Foundation;
5. total queue delay separately from execution time.

A slow sample is an optimization finding, not permission to skip, weaken, or
rename a gate. Queue work adopts the hosted profile only after the migration PR
is green and the exact `main` result is accepted.
