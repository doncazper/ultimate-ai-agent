# Test Corpus Modernization

Status: Phase 01 inventory and retirement/replacement guardrails implemented.

Tracking source: GitHub issue 341.

## Goal

Reduce verification latency and maintenance cost without reducing the defect
classes, safety assertions, exact-head evidence, or operator-visible quality
that the test corpus proves.

The modernization sequence is:

1. deterministic inventory and retirement/replacement guardrails;
2. deterministic fixture foundations;
3. subsystem-by-subsystem setup deduplication with assertion equivalence;
4. slow-test optimization without weaker coverage; and
5. deterministic shard rebalancing after final timing measurement.

Independent subsystem work may be prepared concurrently when fixtures, files,
and contracts do not overlap. Merge admission remains dependency- and
evidence-aware rather than globally one-task-at-a-time.

## Phase 01 Contract

`scripts/verification/test_corpus_guard.py` inventories stable Python and
Control Center `.test`/`.spec` declarations, including inherited pytest class
tests, Python parameterization bound to resolvable decorator syntax, ordered
pre-declaration parameter-data bindings, and in-place mutations visible at
collection time, parameter-data-bound frontend titles, supported runner import
aliases, and extended test APIs. Changes to a parameter set change its stable
declaration ref, so removing a collected case cannot retain the prior inventory
identity.
Identifier-backed frontend parameter sets bind to the preceding static `const`
initializer or to a relative import's exported static `const` initializer.
Nested spread and supported collection expressions bind to the same sources.
Supported static frontend registration loops emit one declaration identity per
collection item, preserving unchanged item identities as neighboring rows change;
unresolved or dynamic loops fail closed. Python imported parameter data is
bound to the exact referenced declaration and its recursively resolvable local
dependencies. Changes to an imported initializer, including one in another test
module, recheck the dependent test file. Dynamic, mutated, ambiguous, or
unresolved parameter bindings and collection-changing `conftest.py` hooks fail
closed. Frontend files also fail closed when `it` or `test` is shadowed by a
local declaration or non-runner import;
`scripts/verify_test_corpus_guard.py`
provides the direct inspection command. For a pull request the guard compares
every changed test file with the exact CI comparison base. A removed or renamed
declaration must have one durable entry in
`docs/verification/test_corpus_retirements.json`.
Git rename collapsing is disabled for this comparison, so moving a test file
explicitly retires its old path-bound stable refs even when its declarations
are otherwise unchanged.

Each retirement entry must identify:

- the exact retired test ref;
- one or more replacements that are present in the current corpus;
- a substantive reason;
- a typed assertion-equivalence artifact plus the SHA-256 ref recomputed from
  its canonical JSON; and
- a typed verification-evidence artifact plus the SHA-256 ref recomputed from
  its canonical JSON.

The assertion artifact binds every replacement ref to an independently derived
`test-source-ref:sha256:*` over only that exact inventoried function or frontend
call expression. Unrelated imports, helpers, or neighboring tests do not
invalidate an accepted historical source ref, while changes to the replacement
declaration do; prose cannot stand in for preserved assertion evidence. The
verification artifact has a
bounded field reserved for independently attested exact-head GitHub evidence.
The repository-constructed GitHub transport envelope is explicitly
non-authoritative and is rejected even when its internally reported receipt and
Foundation Gate run are passed. Phase 01 does not add live GitHub fetching, a
credentialed status client, or a new attestation trust root. Until a later
accepted scope provides an independently verifiable immutable GitHub run or
artifact identity, real test retirements therefore fail closed. Schema tests
inject a bounded validator only to exercise the retirement contract; that test
seam does not grant repository verification authority. The nested artifacts
and their enclosing artifacts are
content-bound as `assertion-ref:sha256:*` and `test-result-ref:sha256:*` values;
arbitrary summaries, status strings, or well-shaped hashes are insufficient.
Records accepted
on the exact comparison commit are immutable: later candidates must preserve
the complete typed record field-for-field. If a historical replacement is later
retired, its own new record must preserve the replacement chain and retain at
least one active replacement.
Every newly added retirement record must correspond to a declaration removed
relative to the bound comparison commit. When a local comparison commit is
unavailable, existing multi-hop replacement chains remain valid only when they
terminate at an active test.

Missing or malformed canonical CI base commits, malformed inventories,
duplicate refs, missing replacements, weak reasons, modified historical
records, or unaccounted removals fail closed. Base-to-HEAD, index, worktree,
and untracked test paths are unioned under fixed byte and path-count budgets,
and the exact base commit supplies both the path comparison and prior content.
A local checkout without a comparison ref reports an explicit local-only
unavailable state; hosted verification may not use that fallback. Adding this
guard does not retire any test.
Worktree test files and the retirement ledger are read as bounded,
single-link regular-file identities by walking every repository-relative path
component through pinned no-follow directory descriptors; substitutions,
symlinked parents, or mid-read identity changes fail closed.
Historical source refs are used only when the replacement file or declaration
is absent; unsafe, oversized, mutated, or undecodable worktree content never
falls back to historical evidence.

Retirement reasons are bounded and rejected when repository redaction rules
detect credential-like values, raw prompt/response/log/path markers, local user
paths, usernames, hostnames, serials, or environment dumps. The verifier
envelope applies its own content-free transport validation before acceptance.
The durable result stores only repository code metadata, counts, and hashes.
It does not store raw test output, application payloads, prompts, responses,
credentials, host identity, or local paths.

## Later Phase Rules

- Fixture deduplication must preserve assertion and failure-mode equivalence.
- A surviving, blocked, unknown, or unmeasured mutation prevents retirement.
- Slow-test optimization must compare equivalent cold and warm runs.
- Timeouts and skips are not performance fixes.
- Shard rebalancing happens after behavior-preserving changes and keeps the
  canonical shard/worker budget unless a separately accepted architecture
  change proves a better budget.
- No phase weakens Foundation Gate, OpenAPI, policy, approval, redaction,
  supply-chain, or exact-head checks.

## Authority

This is verification infrastructure only. It grants no model, provider,
network, browser, connector, shell, plugin, production, or release authority.
