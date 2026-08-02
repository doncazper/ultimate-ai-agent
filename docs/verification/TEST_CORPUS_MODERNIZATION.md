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
tests, parameterized titles, supported import aliases, and extended test APIs;
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

The assertion artifact binds the retired and replacement refs to one or more
bounded, typed, safe-summary-only assertion artifacts whose canonical JSON is
recomputed as an `assertion-ref:sha256:*`. The evidence artifact does the same
for passed verification artifacts and their `test-result-ref:sha256:*` values.
The nested artifacts and their enclosing artifacts are both content-bound;
arbitrary well-shaped hashes are insufficient. Records accepted
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
